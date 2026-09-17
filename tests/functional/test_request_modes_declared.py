"""Every request declares its mode, and nothing supplies one by default (spec/005 § Request modes).

`Http.send_request` already refuses a call without a mode — but only when that call runs, and most
request paths run only against a live server. This reads the source instead, so an unclassified
request fails the build rather than the first user who reaches it.

Two rules:
* every `http.get/post/put/delete(...)` passes `mode=`;
* no `mode` parameter has a default, in any module that deals in `RequestMode` — a default is how a
  timer caller added later silently inherits a click's mode.

"A `POLL` request takes no error handler" is not checked here: the mode reaches the call through a
variable (the timer's slot passes it down), which the source cannot resolve. `Http.send_request`
refuses that combination when it runs.
"""
import ast
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[2] / "mapflow"

HTTP_VERBS = {"get", "post", "put", "delete"}

#: Fewer Http call sites than this means the scan stopped recognising them — a rename of the `http`
#: attribute, say — and every rule below would pass vacuously.
MIN_EXPECTED_SITES = 50


def _is_http_call(node: ast.Call) -> bool:
    func = node.func
    if not isinstance(func, ast.Attribute) or func.attr not in HTTP_VERBS:
        return False
    receiver = func.value
    return (isinstance(receiver, ast.Attribute) and receiver.attr == "http") or \
        (isinstance(receiver, ast.Name) and receiver.id == "http")


def _declares_mode(node: ast.Call) -> bool:
    return any(kw.arg == "mode" for kw in node.keywords)


class _Visitor(ast.NodeVisitor):
    def __init__(self, rel_path: str, deals_in_modes: bool):
        self.rel_path = rel_path
        self.deals_in_modes = deals_in_modes
        self.func_stack = []
        self.sites = []
        self.undeclared = []
        self.defaulted = []

    def visit_FunctionDef(self, node):
        if self.deals_in_modes:
            args = node.args
            positional = args.posonlyargs + args.args
            defaults = dict(zip([a.arg for a in positional[len(positional) - len(args.defaults):]],
                                args.defaults))
            defaults.update({a.arg: d for a, d in zip(args.kwonlyargs, args.kw_defaults)
                             if d is not None})
            if "mode" in defaults:
                self.defaulted.append((self.rel_path, node.name))
        self.func_stack.append(node.name)
        self.generic_visit(node)
        self.func_stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Call(self, node):
        if _is_http_call(node):
            site = (self.rel_path, self.func_stack[-1] if self.func_stack else "<module>", node.lineno)
            self.sites.append(site)
            if not _declares_mode(node):
                self.undeclared.append(site)
        self.generic_visit(node)


def _scan():
    visitors = []
    for path in sorted(PLUGIN.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        source = path.read_text(encoding="utf-8")
        visitor = _Visitor(path.relative_to(PLUGIN.parent).as_posix(), "RequestMode" in source)
        visitor.visit(ast.parse(source, filename=str(path)))
        visitors.append(visitor)
    return visitors


def _collect(attribute):
    return sorted(item for visitor in _scan() for item in getattr(visitor, attribute))


def test_the_scan_still_sees_the_http_calls():
    sites = _collect("sites")
    assert len(sites) >= MIN_EXPECTED_SITES, (
        f"found only {len(sites)} Http call sites — the scan no longer recognises them, so the rules "
        f"below would pass on nothing")


def test_every_request_declares_its_mode():
    undeclared = _collect("undeclared")
    assert not undeclared, (
        "these requests declare no mode — pass mode=RequestMode.INTERACTIVE / BACKGROUND / POLL "
        "for what triggers them (spec/005 § Request modes):\n"
        + "\n".join(repr(site) for site in undeclared))


def test_no_mode_parameter_has_a_default():
    defaulted = _collect("defaulted")
    assert not defaulted, (
        "these functions give `mode` a default — the caller that knows the trigger must pass it:\n"
        + "\n".join(repr(site) for site in defaulted))
