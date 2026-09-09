"""Every Qt-source entry point is guarded (spec/007 § Entry points, § Enforcement).

A slot connected to a Qt-owned signal (a widget, action, timer, layer, project or dialog) begins a
fresh call stack from Qt's event loop; an unexpected failure there escapes to QGIS's raw
unhandled-exception dialog unless it is guarded. The guard is `error_guard.guarded_connect`, used at
the connection site instead of a raw `signal.connect(slot)`.

A slot on a plugin `pyqtSignal` is NOT an entry point of its own: it emits synchronously inside some
other entry point's stack, so it is covered transitively and is not flagged here.

`ALLOWED_UNGUARDED` records the Qt-source connections not yet routed through `guarded_connect`. It
only shrinks — each entry-point PR removes its rows, and a row that no longer corresponds to a raw
Qt-source connect fails the stale-entry test. Same discipline as `test_layering.py` /
`test_silent_opt_outs.py`.
"""
import ast
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[2] / "mapflow"

#: Signals owned by Qt/QGIS — a connection to one of these begins a fresh stack from the event loop
#: (spec/007 § Entry points). Classified by attribute name, since AST cannot resolve the receiver's
#: type. Plugin `pyqtSignal`s (domain signals like `refreshRequested`) are deliberately absent.
QT_SIGNALS = {
    # widgets
    "clicked", "triggered", "itemSelectionChanged", "cellClicked", "cellDoubleClicked",
    "doubleClicked", "currentIndexChanged", "currentTextChanged", "activated", "textChanged",
    "textEdited", "stateChanged", "toggled", "valueChanged", "sectionClicked", "layerChanged",
    "aboutToShow",
    # QTimer
    "timeout",
    # QgsVectorLayer
    "selectionChanged", "geometryChanged", "featureAdded", "featuresDeleted",
    # QgsProject
    "layersAdded", "readProject",
    # QDialog / QNetworkReply completion
    "finished", "accepted", "rejected",
    # custom dialog signals emitted from inside a Qt event handler (fresh stack — see spec § Entry points)
    "rasterSourceChanged", "metadataTableFilled",
}

#: (path relative to repo root, enclosing function, signal name) for each Qt-source connection still
#: made with a raw `.connect`. Only shrinks — see the module docstring. It began as every Qt-source
#: connection in the plugin and is now down to one, which is not a gap:
#:
#: `send_request` wires the finished signal to `response_dispatcher`, which IS the guard (it wraps
#: every callback in `call_guarded`). It is the one `.connect` that need not go through the helper —
#: routing the guard through itself would be circular.
#:
#: So a new row here is a regression, not a step: every other Qt entry point in the plugin reaches
#: plugin code through `guarded_connect`.
ALLOWED_UNGUARDED = {
    ('mapflow/http.py', 'send_request', 'finished'),
}


def _signal_name(call: ast.Call):
    """The signal a `.connect(...)` call attaches to, e.g. 'clicked' for `btn.clicked.connect(x)`.

    Returns None when the receiver of `.connect` is not an attribute access (e.g. a bare `signal`
    parameter inside the helper itself), which cannot be a Qt-source connection to classify.
    """
    if not (isinstance(call.func, ast.Attribute) and call.func.attr == "connect"):
        return None
    receiver = call.func.value
    return receiver.attr if isinstance(receiver, ast.Attribute) else None


class _ConnectVisitor(ast.NodeVisitor):
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
        name = _signal_name(node)
        if name in QT_SIGNALS:
            func = self.func_stack[-1] if self.func_stack else "<module>"
            self.sites.add((self.rel_path, func, name))
        self.generic_visit(node)


def _qt_source_connects():
    sites = set()
    for path in sorted(PLUGIN.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        visitor = _ConnectVisitor(path.relative_to(PLUGIN.parent).as_posix())
        visitor.visit(tree)
        sites |= visitor.sites
    return sites


def test_every_qt_source_connection_is_guarded_or_allowlisted():
    sites = _qt_source_connects()
    unguarded = sites - ALLOWED_UNGUARDED
    assert not unguarded, (
        "these Qt-source signals are connected with a raw `.connect` — route them through "
        "`guarded_connect`, or (for a genuine Qt->Qt passthrough) add to ALLOWED_UNGUARDED with a "
        f"reason:\n{chr(10).join(repr(s) for s in sorted(unguarded))}")


def test_the_allowlist_has_no_stale_entries():
    sites = _qt_source_connects()
    stale = ALLOWED_UNGUARDED - sites
    assert not stale, (
        f"these are allowlisted but no longer raw Qt-source connects — drop them from "
        f"ALLOWED_UNGUARDED:\n{chr(10).join(repr(s) for s in sorted(stale))}")
