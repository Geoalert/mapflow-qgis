"""QGIS-tier tests for the processings poll-loop rendering.

Regression: with templates present, each poll rendered the table twice — first with
processings only (templates momentarily gone), then with the combined rows once the
templates request returned. The changing row count between the two renders made the
table flash. The poll must render the table once, with the combined rows.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

from PyQt5.QtCore import QObject

from mapflow.functional.service.processing_service import ProcessingService


def _rendered(service):
    """The row sets the service asked the controller to draw."""
    rendered = []
    service.rowsChanged.connect(rendered.append)
    return rendered


def test_update_local_processings_does_not_render_table():
    service = ProcessingService.__new__(ProcessingService)
    QObject.__init__(service)  # the rows are announced as a signal
    service.tr = lambda text: text
    service.iface = MagicMock()
    service.app_context = SimpleNamespace(settings=MagicMock())
    history = MagicMock()
    history.update.return_value = {}
    service.processings_history = history
    rendered = _rendered(service)

    service.update_local_processings([SimpleNamespace(id="proc-1", name="Run 1")])

    # History is still updated, but rendering is deferred to the combined render.
    history.update.assert_called_once()
    assert rendered == []


def test_update_local_processings_noop_without_history():
    service = ProcessingService.__new__(ProcessingService)
    QObject.__init__(service)
    service.tr = lambda text: text
    service.processings_history = None
    rendered = _rendered(service)

    service.update_local_processings([SimpleNamespace(id="proc-1", name="Run 1")])

    assert rendered == []
