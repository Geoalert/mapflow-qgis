"""QGIS-tier tests for refreshing the in-template view after starting a processing
(round-2 feedback 8.2). A template-started processing is grouped under its AOI via the
template's aoiDetails, which the create response does not carry; the callback must
re-hydrate the template (not do a flat optimistic add) so the new processing is bound to
its AOI instead of showing under the 'No AOI' separator.

The service no longer refreshes the table itself — it asks, and `ProjectProcessingController`
decides which of the table's two views to refresh. So "it refreshed" is asserted here as "it
asked", and the controller's own choice is covered in test_processings_table_refresh.py.
"""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from PyQt5.QtCore import QObject

from mapflow.functional.service import processing_service as processing_service_module
from mapflow.functional.service.processing_service import ProcessingService
from mapflow.functional.service.template_service import TemplateService


def _response(payload):
    reply = MagicMock()
    reply.readAll.return_value.data.return_value = json.dumps(payload).encode()
    return reply


def _service(in_template_mode):
    service = ProcessingService.__new__(ProcessingService)
    QObject.__init__(service)  # the refresh requests are signals now
    service.tr = lambda text: text
    service.dlg = MagicMock()
    service.api = MagicMock()
    service.view = MagicMock()
    service.processing_fetch_timer = MagicMock()
    service.template_state = SimpleNamespace(
        in_template_mode=in_template_mode,
        active_template=SimpleNamespace(id="tpl-1") if in_template_mode else None)
    service.processings = {}
    service.processings_history = MagicMock()
    return service


def _template_service(active_template=SimpleNamespace(id="tpl-1")):
    """The rehydrate itself is TemplateService's: it owns the open template."""
    service = TemplateService(app_context=MagicMock(), processing_service=MagicMock())
    service.active_template = active_template
    service._fetch_template_processings = MagicMock()
    return service


def _requests(service):
    """What the service asked the controller for, in order."""
    asked = []
    service.refreshRequested.connect(lambda: asked.append("refresh"))
    service.templateRehydrateRequested.connect(lambda: asked.append("rehydrate"))
    return asked


_PROCESSING = {"id": "p-1", "name": "Run 1", "status": "IN_PROGRESS"}


def test_template_start_asks_for_a_rehydrate_and_skips_flat_add():
    service = _service(in_template_mode=True)
    asked = _requests(service)

    with patch.object(processing_service_module, "alert"):
        service.start_processing_callback(_response(_PROCESSING))

    # A plain refresh would refetch the rows without rebinding the new processing to its AOI.
    assert asked == ["rehydrate"]
    # No flat optimistic add in template mode.
    service.view.add_new_processing.assert_not_called()
    service.dlg.startProcessing.setEnabled.assert_called_once_with(True)


def test_regular_start_does_flat_add_and_asks_for_a_plain_refresh():
    service = _service(in_template_mode=False)
    asked = _requests(service)
    fake_dto = SimpleNamespace(id="p-1", name="Run 1", status="IN_PROGRESS")

    with patch.object(processing_service_module, "alert"), \
            patch.object(processing_service_module.ProcessingDTO, "from_dict", return_value=fake_dto):
        service.start_processing_callback(_response(_PROCESSING))

    service.view.add_new_processing.assert_called_once_with(fake_dto)
    assert asked == ["refresh"]
    service.api.get_template.assert_not_called()


def test_rehydrate_re_fetches_the_template_and_its_processings():
    """What the controller runs when the rehydrate request arrives."""
    service = _template_service()

    service.refresh_active_template()

    api = service.processing_service.api
    api.get_template.assert_called_once()
    assert api.get_template.call_args.kwargs["template_id"] == "tpl-1"
    service._fetch_template_processings.assert_called_once()


def test_refresh_active_template_noop_without_active_template():
    service = _template_service(active_template=None)

    service.refresh_active_template()

    service.processing_service.api.get_template.assert_not_called()
    service._fetch_template_processings.assert_not_called()
