"""QGIS-tier tests for the processings poll-loop rendering.

Regression: with templates present, each poll rendered the table twice — first with
processings only (templates momentarily gone), then with the combined rows once the
templates request returned. The changing row count between the two renders made the
table flash. The poll must render the table once, with the combined rows.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.functional.service.processing_service import ProcessingService


def test_update_local_processings_does_not_render_table():
    service = ProcessingService.__new__(ProcessingService)
    service.tr = lambda text: text
    service.view = MagicMock()
    service.iface = MagicMock()
    service.app_context = SimpleNamespace(settings=MagicMock())
    history = MagicMock()
    history.update.return_value = {}
    service.processings_history = history

    service.update_local_processings([SimpleNamespace(id="proc-1", name="Run 1")])

    # History is still updated, but rendering is deferred to the combined render.
    history.update.assert_called_once()
    service.view.update_processing_table.assert_not_called()


def test_update_local_processings_noop_without_history():
    service = ProcessingService.__new__(ProcessingService)
    service.tr = lambda text: text
    service.view = MagicMock()
    service.processings_history = None

    service.update_local_processings([SimpleNamespace(id="proc-1", name="Run 1")])

    service.view.update_processing_table.assert_not_called()
