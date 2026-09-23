"""QGIS-tier tests for filtering template search results by multiple selected AOIs
(round-2 feedback 11; spec 002_F: selecting one or more AOI rows sends all their ids as
``aoiIds`` on the template images request; deselecting all restores the full results).

Owners after the search extraction: `TemplateController` guards on being inside a template,
`TemplateService` holds the current scope and decides whether it actually changed.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.functional.controller.template_controller import TemplateController
from mapflow.functional.service.template_service import TemplateService


def _service(selected_aois):
    template = SimpleNamespace(id="tpl-1", name="T1")
    service = TemplateService(app_context=MagicMock(), processing_service=MagicMock())
    service.in_template_mode = True
    service.active_template = template
    service.selected_aois = lambda: selected_aois
    service.load_search = MagicMock()
    return service, template


def _aoi(aoi_id):
    return SimpleNamespace(id=aoi_id)


def test_multiple_selected_aois_are_all_sent():
    service, template = _service([_aoi("a1"), _aoi("a2")])

    service.filter_search_by_selected_aois()

    service.load_search.assert_called_once()
    _, kwargs = service.load_search.call_args
    assert set(kwargs["aoi_ids"]) == {"a1", "a2"}
    assert service.search_aoi_filter == frozenset({"a1", "a2"})


def test_no_selection_restores_full_results():
    service, template = _service([])
    service.search_aoi_filter = frozenset({"a1"})

    service.filter_search_by_selected_aois()

    service.load_search.assert_called_once_with(template, aoi_ids=None)
    assert service.search_aoi_filter is None


def test_unchanged_selection_does_not_reload():
    service, _ = _service([_aoi("a1"), _aoi("a2")])
    service.search_aoi_filter = frozenset({"a1", "a2"})

    service.filter_search_by_selected_aois()

    service.load_search.assert_not_called()


def test_reselection_order_independent():
    """Selecting the same AOIs in a different order must not trigger a reload."""
    service, _ = _service([_aoi("a2"), _aoi("a1")])
    service.search_aoi_filter = frozenset({"a1", "a2"})

    service.filter_search_by_selected_aois()

    service.load_search.assert_not_called()


def test_no_active_template_is_noop():
    service, _ = _service([_aoi("a1")])
    service.active_template = None

    service.filter_search_by_selected_aois()

    service.load_search.assert_not_called()


def test_not_in_template_mode_is_noop():
    """The in-template check stays with the caller: the service has no view of navigation."""
    controller = TemplateController.__new__(TemplateController)
    controller.template_service = MagicMock()
    controller.template_service.in_template_mode = False

    controller.filter_search_by_selected_aoi()

    controller.template_service.filter_search_by_selected_aois.assert_not_called()


def test_in_template_mode_delegates_to_the_service():
    controller = TemplateController.__new__(TemplateController)
    controller.template_service = MagicMock()
    controller.template_service.in_template_mode = True

    controller.filter_search_by_selected_aoi()

    controller.template_service.filter_search_by_selected_aois.assert_called_once()
