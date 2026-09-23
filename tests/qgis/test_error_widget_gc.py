"""C3.4: the error-report dialog must outlive the callback that built it.

`ErrorMessageWidget` is often shown parentless (a report can fire from a network callback while
`QApplication.activeWindow()` is None), and a top-level widget shown with `.show()` is then owned
only by the local that built it. The reporter returns, the local goes out of scope, and Qt could
collect the dialog before it was ever painted. The widget now retains itself in a class-level set
until closed; this pins that it survives collection while open and leaves the set once closed.
"""
import gc
import weakref

from PyQt5.QtCore import QEvent
from PyQt5.QtWidgets import QApplication

from mapflow.dialogs.error_message_widget import ErrorMessageWidget


def test_the_dialog_is_not_collected_while_open():
    """Without the self-retention, dropping the last local and collecting would take the dialog
    with it — the C3.4 bug. With it, the class holds a reference and the dialog survives."""
    ref = weakref.ref(ErrorMessageWidget(parent=None, text="something failed"))

    gc.collect()

    assert ref() is not None, "the dialog was collected before it could be shown (C3.4)"


def test_closing_the_dialog_releases_it_from_the_retention_set():
    """The other half of the mechanism: retention must end on close, or every reported error would
    leak for the session. Asserted on set membership (what the code controls) rather than Python GC
    of the wrapper."""
    baseline = len(ErrorMessageWidget._alive)
    widget = ErrorMessageWidget(parent=None, text="something failed")
    assert len(ErrorMessageWidget._alive) == baseline + 1, "an open dialog must be retained"

    widget.close()
    # WA_DeleteOnClose posts a deferred-delete; flush it so `destroyed` fires and discards the
    # dialog from the set (processEvents does not reliably run DeferredDelete in a headless test).
    QApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    assert len(ErrorMessageWidget._alive) == baseline, "a closed dialog must leave the retention set"
