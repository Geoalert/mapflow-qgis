"""QGIS-tier tests for keeping the project processings poll alive while a template is still
searching (round-2 feedback 9). A template created/searching while the user waits in the
project table must reach a terminal status without re-entering the project, so the poll's
stop decision considers template statuses, not only processings."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.functional.service.processing_service import ProcessingService
from mapflow.schema.template import ProcessingTemplateDTO


def _service(processings_all_final, templates, in_template_mode=False, timer_active=True):
    service = ProcessingService.__new__(ProcessingService)
    service.in_template_mode = in_template_mode
    service._processings_all_final = processings_all_final
    service.templates = templates
    service.processing_fetch_timer = MagicMock()
    service.processing_fetch_timer.isActive.return_value = timer_active
    return service


def _template(searching):
    return SimpleNamespace(is_search_in_progress=searching)


def test_is_search_in_progress_reads_status():
    tpl = ProcessingTemplateDTO.__new__(ProcessingTemplateDTO)
    tpl.status = "SEARCHING"
    assert tpl.is_search_in_progress is True
    tpl.status = "Searching"
    assert tpl.is_search_in_progress is True
    tpl.status = "UPDATED"
    assert tpl.is_search_in_progress is False
    tpl.status = None
    assert tpl.is_search_in_progress is False


def test_poll_stops_when_idle():
    service = _service(processings_all_final=True, templates={"t": _template(False)})

    service._apply_poll_timer_state()

    service.processing_fetch_timer.stop.assert_called_once()


def test_poll_kept_alive_by_searching_template():
    service = _service(
        processings_all_final=True, templates={"t": _template(True)}, timer_active=False
    )

    service._apply_poll_timer_state()

    service.processing_fetch_timer.stop.assert_not_called()
    service.processing_fetch_timer.start.assert_called_once()


def test_poll_kept_alive_by_running_processing():
    service = _service(processings_all_final=False, templates={}, timer_active=False)

    service._apply_poll_timer_state()

    service.processing_fetch_timer.stop.assert_not_called()
    service.processing_fetch_timer.start.assert_called_once()


def test_poll_not_restarted_when_already_active():
    service = _service(
        processings_all_final=True, templates={"t": _template(True)}, timer_active=True
    )

    service._apply_poll_timer_state()

    service.processing_fetch_timer.start.assert_not_called()
    service.processing_fetch_timer.stop.assert_not_called()


def test_in_template_mode_is_noop():
    service = _service(
        processings_all_final=True, templates={"t": _template(False)}, in_template_mode=True
    )

    service._apply_poll_timer_state()

    service.processing_fetch_timer.stop.assert_not_called()
    service.processing_fetch_timer.start.assert_not_called()
