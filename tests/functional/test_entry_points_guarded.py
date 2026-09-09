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


#: `.connect(...)` sites whose receiver is a bare name, so no signal can be named for them. One
#: entry, and it is the helper itself: `guarded_connect` connects its wrapper to whatever signal it
#: was handed, which is the entire point of it. Anything else appearing here is a connection the
#: rule above cannot see — make the receiver an attribute access, or route it through
#: `guarded_connect`. Do not add rows to silence it.
ALLOWED_UNCLASSIFIED = {
    # The helper itself: `guarded_connect` connects its wrapper to whatever signal it was handed,
    # which is the entire point of it.
    ('mapflow/error_guard.py', 'guarded_connect'),
    # `model_options_changed` is `MainDialog.modelOptionsChanged` — a plugin pyqtSignal injected as
    # a constructor argument, so the receiver is a parameter name and nothing can be read off it.
    # Plugin-signal connections stay raw because they emit inside an already-guarded stack, and this
    # one's Qt boundary is the model-option checkbox's `toggled`, guarded in `main_dialog`.
    ('mapflow/functional/controller/processing_controller.py', '__init__'),
}


def _is_connect_call(call: ast.Call) -> bool:
    return isinstance(call.func, ast.Attribute) and call.func.attr == "connect"


def _signal_name(call: ast.Call):
    """The signal a `.connect(...)` call attaches to, e.g. 'clicked' for `btn.clicked.connect(x)`.

    Returns None when the receiver of `.connect` is not an attribute access — a bare name, as in
    `for signal in (...): signal.connect(...)`. Such a call is NOT thereby safe: it is invisible to
    the classification, which is why `test_no_connection_is_invisible_to_the_classifier` fails on it
    separately rather than letting it pass as "not a Qt signal".
    """
    if not _is_connect_call(call):
        return None
    receiver = call.func.value
    return receiver.attr if isinstance(receiver, ast.Attribute) else None


class _ConnectVisitor(ast.NodeVisitor):
    def __init__(self, rel_path: str):
        self.rel_path = rel_path
        self.func_stack = []
        self.sites = set()
        self.unclassified = set()

    def visit_FunctionDef(self, node):
        self.func_stack.append(node.name)
        self.generic_visit(node)
        self.func_stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Call(self, node):
        if _is_connect_call(node):
            func = self.func_stack[-1] if self.func_stack else "<module>"
            name = _signal_name(node)
            if name is None:
                self.unclassified.add((self.rel_path, func))
            elif name in QT_SIGNALS:
                self.sites.add((self.rel_path, func, name))
        self.generic_visit(node)


def _visit_plugin():
    sites, unclassified = set(), set()
    for path in sorted(PLUGIN.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        visitor = _ConnectVisitor(path.relative_to(PLUGIN.parent).as_posix())
        visitor.visit(tree)
        sites |= visitor.sites
        unclassified |= visitor.unclassified
    return sites, unclassified


def _qt_source_connects():
    return _visit_plugin()[0]


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


def test_no_connection_is_invisible_to_the_classifier():
    """Fail closed: a `.connect` the classifier cannot name is a hole, not an absence.

    The rule above reads the signal off an attribute access, so `for signal in (...):
    signal.connect(...)` names nothing and simply never appears — it is neither guarded nor
    allowlisted nor reported. `mapflow.py` held exactly that shape (nine Qt widget signals wired in
    a loop) through the whole rollout, and they were guarded only because a human happened to read
    the block. An enforcement test that depends on someone reading the code is not enforcing
    anything, so an unnameable receiver now has to be justified like any other exemption.
    """
    _sites, unclassified = _visit_plugin()
    invisible = unclassified - ALLOWED_UNCLASSIFIED
    assert not invisible, (
        "these `.connect(...)` calls have a receiver the classifier cannot name, so the guard rule "
        "cannot see them. Give the receiver an attribute access (`widget.signal.connect(...)`) or "
        "route it through `guarded_connect`:\n"
        + "\n".join(repr(s) for s in sorted(invisible)))


def test_the_unclassified_allowlist_has_no_stale_entries():
    _sites, unclassified = _visit_plugin()
    stale = ALLOWED_UNCLASSIFIED - unclassified
    assert not stale, (
        f"these are allowlisted as unclassifiable but no longer are — drop them from "
        f"ALLOWED_UNCLASSIFIED:\n{chr(10).join(repr(s) for s in sorted(stale))}")
