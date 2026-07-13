"""QGIS-tier tests for refreshing the in-template view after starting a processing
(round-2 feedback 8.2). A template-started processing is grouped under its AOI via the
template's aoiDetails, which the create response does not carry; the callback must
re-hydrate the template (not do a flat optimistic add) so the new processing is bound to
its AOI instead of showing under the 'No AOI' separator."""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from mapflow.functional.service import processing_service as processing_service_module
from mapflow.functional.service.processing_service import ProcessingService


def _response(payload):
    reply = MagicMock()
    reply.readAll.return_value.data.return_value = json.dumps(payload).encode()
    return reply


def _service(in_template_mode):
    service = ProcessingService.__new__(ProcessingService)
    service.tr = lambda text: text
    service.dlg = MagicMock()
    service.api = MagicMock()
    service.view = MagicMock()
    service.processing_fetch_timer = MagicMock()
    service.in_template_mode = in_template_mode
    service.active_template = SimpleNamespace(id="tpl-1") if in_template_mode else None
    service.processings = {}
    service.processings_history = MagicMock()
    service.get_processings = MagicMock()
    service._fetch_template_processings = MagicMock()
    service._reopen_template_callback = MagicMock()
    return service


_PROCESSING = {"id": "p-1", "name": "Run 1", "status": "IN_PROGRESS"}


def test_template_start_rehydrates_template_and_skips_flat_add():
    service = _service(in_template_mode=True)

    with patch.object(processing_service_module, "alert"):
        service.start_processing_callback(_response(_PROCESSING))

    # Re-hydrate aoiDetails (binds the new processing to its AOI) + refetch processings.
    service.api.get_template.assert_called_once()
    assert service.api.get_template.call_args.kwargs["template_id"] == "tpl-1"
    service._fetch_template_processings.assert_called_once()
    # No flat optimistic add / regular-list refresh in template mode.
    service.view.add_new_processing.assert_not_called()
    service.get_processings.assert_not_called()
    service.dlg.startProcessing.setEnabled.assert_called_once_with(True)


def test_regular_start_does_flat_add_and_no_template_refresh():
    service = _service(in_template_mode=False)
    fake_dto = SimpleNamespace(id="p-1", name="Run 1", status="IN_PROGRESS")

    with patch.object(processing_service_module, "alert"), \
            patch.object(processing_service_module.ProcessingDTO, "from_dict", return_value=fake_dto):
        service.start_processing_callback(_response(_PROCESSING))

    service.view.add_new_processing.assert_called_once_with(fake_dto)
    service.get_processings.assert_called_once()
    service.api.get_template.assert_not_called()
    service._fetch_template_processings.assert_not_called()


def test_refresh_active_template_noop_without_active_template():
    service = _service(in_template_mode=True)
    service.active_template = None

    service._refresh_active_template()

    service.api.get_template.assert_not_called()
    service._fetch_template_processings.assert_not_called()
