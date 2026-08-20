"""A handler that catches `Exception` must surface what it caught.

The rule, and why it is this one rather than "don't catch `Exception`":

A broad handler that logs a traceback hides nothing — the failure is in the log, with the
stack, and a refactor that breaks the code underneath it is still visible. A *narrow*
`except ValueError: pass` hides plenty. So the property worth enforcing is whether the failure
leaves a trace, not how wide the except clause is. Counting `except Exception` would have
called `except ValueError: pass` an improvement.

This matters most during the Phase C extraction (`spec/007_architecture.md`): code moves past
these sites constantly, and a handler that swallows everything turns a broken move into a
feature that quietly does nothing.

flake8 has no rule for this — `BLE001` is a flake8-bugbear/ruff check, and neither is in the
toolchain (`spec/004_stack.md` § Static analysis pins flake8, bandit and detect-secrets to
match what plugins.qgis.org runs). bandit's `B110`/`B112` only catch `except: pass` and
`except: continue`, which is a strict subset. Hence a test.

Same shape and the same argument as `tests/functional/test_layering.py`: parse with `ast`,
never import, and keep an allowlist that only shrinks.
"""
import ast
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[2] / "mapflow"

#: Handlers allowed to swallow silently, with the reason. Only ever shrinks — a stale entry
#: fails `test_the_allowlist_has_no_stale_entries`.
ALLOWED_SILENT = {
    # A logging handler must not raise into the code that logged, and must not log its own
    # failure either — that is what recursed in the first place. See the comment at the site.
    ("mapflow/log_config.py", "QgisMessageLogHandler.emit"),
}


def is_broad(handler: ast.ExceptHandler) -> bool:
    """A bare `except:`, or one naming Exception/BaseException among its types."""
    if handler.type is None:
        return True
    types = handler.type.elts if isinstance(handler.type, ast.Tuple) else [handler.type]
    return any(isinstance(t, ast.Name) and t.id in ("Exception", "BaseException") for t in types)


def surfaces(handler: ast.ExceptHandler) -> bool:
    """Does the handler body leave a trace of the failure?

    Three ways, and the third is why this is not a list of approved function names:

    * ``raise`` — the caller still sees it;
    * ``logger.exception(...)`` — records the traceback whether or not the exception is bound;
    * binding with ``as`` and *using* that name — the exception reaches a message, a log line
      or a report either way, so `alert(str(e))`, `pushWarning(...)` with the text, and
      `report_unexpected_error(exception, ...)` all pass without being enumerated here.

    The failure mode it rejects is the handler that discards the exception object and says
    nothing: `except Exception: return None`.
    """
    for node in ast.walk(handler):
        if isinstance(node, ast.Raise):
            return True
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "exception"):
            return True
    if handler.name:
        return any(isinstance(node, ast.Name) and node.id == handler.name
                   for node in ast.walk(handler))
    return False


def _handlers_with_scope(tree: ast.AST):
    """(handler, dotted class/function path) for every handler in the file.

    Allowlist entries key off this name rather than a line number, so an unrelated edit above
    the handler does not turn an exemption stale.
    """
    found = []

    def visit(node, scope):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ExceptHandler):
                found.append((child, ".".join(scope) or "<module>"))
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                visit(child, scope + [child.name])
            else:
                visit(child, scope)

    visit(tree, [])
    return found


def _silent_handlers():
    """(file, qualified name, lineno) for every broad handler that surfaces nothing."""
    found = []
    for path in sorted(PLUGIN.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        relative = str(path.relative_to(PLUGIN.parent))
        for handler, scope in _handlers_with_scope(tree):
            if is_broad(handler) and not surfaces(handler):
                found.append((relative, scope, handler.lineno))
    return found


def test_the_detector_recognises_each_way_of_surfacing():
    """Everything below trusts `surfaces`, so it is tested before it is used.

    A detector that returned True too readily would pass the whole tree while measuring
    nothing — the failure mode `test_layering.py`'s resolver test exists for.
    """
    def handler(source: str) -> ast.ExceptHandler:
        return ast.parse(source).body[0].handlers[0]

    assert surfaces(handler("try:\n    f()\nexcept Exception:\n    raise"))
    assert surfaces(handler("try:\n    f()\nexcept Exception:\n    logger.exception('x')"))
    assert surfaces(handler("try:\n    f()\nexcept Exception as e:\n    alert(str(e))"))
    assert surfaces(handler("try:\n    f()\nexcept Exception as e:\n    report(e, ctx)"))

    # Silent: the exception object is discarded and nothing records it.
    assert not surfaces(handler("try:\n    f()\nexcept Exception:\n    return None"))
    assert not surfaces(handler("try:\n    f()\nexcept Exception:\n    pass"))
    # Bound but unused is still silent — `as e` alone tells the reader nothing.
    assert not surfaces(handler("try:\n    f()\nexcept Exception as e:\n    return None"))
    # A message with no reference to the exception loses which failure happened.
    assert not surfaces(handler("try:\n    f()\nexcept Exception:\n    alert('failed')"))


def test_is_broad_covers_bare_and_tuple_forms():
    def handler(source: str) -> ast.ExceptHandler:
        return ast.parse(source).body[0].handlers[0]

    assert is_broad(handler("try:\n    f()\nexcept:\n    pass"))
    assert is_broad(handler("try:\n    f()\nexcept Exception:\n    pass"))
    assert is_broad(handler("try:\n    f()\nexcept BaseException:\n    pass"))
    assert is_broad(handler("try:\n    f()\nexcept (ValueError, Exception):\n    pass"))

    assert not is_broad(handler("try:\n    f()\nexcept ValueError:\n    pass"))
    assert not is_broad(handler("try:\n    f()\nexcept (ValueError, TypeError):\n    pass"))


def test_no_broad_handler_swallows_silently():
    breaches = [(file, name, line) for file, name, line in _silent_handlers()
                if (file, name) not in ALLOWED_SILENT]
    assert not breaches, (
        "these catch Exception and leave no trace of what they caught — name the exceptions "
        "you expect, or log/re-raise/report it:\n"
        + "\n".join(f"  {file}:{line} in {name}" for file, name, line in breaches))


def test_the_allowlist_has_no_stale_entries():
    """An exemption outliving its handler quietly re-permits what it recorded."""
    live = {(file, name) for file, name, _line in _silent_handlers()}
    stale = sorted(entry for entry in ALLOWED_SILENT if entry not in live)
    assert not stale, (
        f"these no longer correspond to a silent handler and must be deleted from "
        f"ALLOWED_SILENT: {stale}")
