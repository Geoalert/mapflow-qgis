"""Which HTTP requests are allowed to fail silently.

A request made with `use_default_error_handler=False` and no `error_handler=` reports its server
errors to nobody. Before the report throttle, several paths opted out that way to avoid a dialog
every poll tick — the throttle now bounds that, so opting out to dodge repeat alerts has no
justification left (`spec/006_error_reporting.md` § Consequences: "Opting out to dodge repeat alerts
is superseded by the throttle").

This enforces the one path that may still opt out: the `/version` probe, which fails open (the
plugin still starts when it is unreachable) and so must NOT pop a report on an offline start. Any
new silent request fails this test — restore the default handler, or add it to the allowlist with a
reason, the same discipline as `test_layering.py`.
"""
import ast
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[2] / "mapflow"

#: `Http` request methods. The `use_default_error_handler` keyword is unique to them, so matching on
#: it (below) cannot collide with an unrelated `.get`/`.put` such as `dict.get`.
HTTP_METHODS = {"get", "post", "put", "delete"}

#: (path relative to repo root, enclosing function) allowed to make a silent request. Only the
#: version probe: it fails open, so a report on an unreachable /version would be noise the user
#: cannot act on.
ALLOWED_SILENT = {("mapflow/mapflow.py", "main")}


def _is_silent_http_call(node: ast.Call) -> bool:
    if not isinstance(node.func, ast.Attribute) or node.func.attr not in HTTP_METHODS:
        return False
    if any(kw.arg == "error_handler" for kw in node.keywords):
        return False  # supplies its own handler — not silent
    return any(kw.arg == "use_default_error_handler"
               and isinstance(kw.value, ast.Constant) and kw.value.value is False
               for kw in node.keywords)


class _SilentSiteVisitor(ast.NodeVisitor):
    def __init__(self, rel_path: str):
        self.rel_path = rel_path
        self.func_stack = []
        self.sites = set()

    def visit_FunctionDef(self, node):
        self.func_stack.append(node.name)
        self.generic_visit(node)
        self.func_stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Call(self, node):
        if _is_silent_http_call(node):
            self.sites.add((self.rel_path, self.func_stack[-1] if self.func_stack else "<module>"))
        self.generic_visit(node)


def _silent_sites():
    sites = set()
    for path in sorted(PLUGIN.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        visitor = _SilentSiteVisitor(path.relative_to(PLUGIN.parent).as_posix())
        visitor.visit(tree)
        sites |= visitor.sites
    return sites


def test_only_the_version_probe_makes_a_silent_request():
    sites = _silent_sites()
    unexpected = sites - ALLOWED_SILENT
    assert not unexpected, (
        f"these requests fail silently — restore use_default_error_handler=True (the throttle now "
        f"bounds repeat dialogs), or allowlist with a reason: {sorted(unexpected)}")
    stale = ALLOWED_SILENT - sites
    assert not stale, (
        f"these are allowlisted as silent but no longer are — drop them from ALLOWED_SILENT: "
        f"{sorted(stale)}")
