"""QGIS-tier tests for running an imagery search.

The guards in front of the request had no direct coverage while this was `Mapflow.get_metadata`:
each needed a plugin to reach. They matter because each one prevents a request that would fail
somewhere less legible — with no AOI the backend has nothing to intersect, without a working
directory the results have nowhere to land, and a provider that cannot search has no endpoint.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from PyQt5.QtCore import QObject

from mapflow.functional.controller import search_controller as sc_mod
from mapflow.functional.controller.search_controller import SearchController


@pytest.fixture(autouse=True)
def alerts(monkeypatch):
    """Autouse: an unstubbed `alert` opens a modal with nothing to close it in the test container
    (see tests/qgis/conftest.py)."""
    said = []
    monkeypatch.setattr(sc_mod, "alert", lambda message, *a, **k: said.append(message))
    return said


def _controller(aoi=object(), output_dir_ok=True):
    controller = SearchController.__new__(SearchController)
    QObject.__init__(controller)
    controller.tr = lambda text: text
    controller.search_service = MagicMock()
    controller.search_view = MagicMock()
    controller.search_view.provider_index.return_value = 0
    controller.search_view.search_parameters.return_value = {"max_cloud_cover": 30}
    controller.search_view.filter_baseline.return_value = {"baseline": True}
    controller.provider_service = MagicMock()
    controller.provider_service.providers = [MagicMock()]
    controller.aoi_view = MagicMock()
    controller.app_context = SimpleNamespace(aoi=aoi, open_template_results_id="t-1")
    controller.ensure_output_dir = lambda: output_dir_ok
    return controller


def test_a_search_sends_the_widget_values_read_once():
    controller = _controller()

    controller.run_search()

    kwargs = controller.search_service.search.call_args.kwargs
    assert kwargs["max_cloud_cover"] == 30
    assert kwargs["baseline_filters"] == {"baseline": True}
    assert kwargs["offset"] == 0


def test_a_page_request_passes_its_offset():
    controller = _controller()

    controller.run_search(offset=20)

    assert controller.search_service.search.call_args.kwargs["offset"] == 20


def test_a_regular_search_stops_the_results_belonging_to_a_template():
    """Otherwise Start would still read as a planned processing over results that have been
    replaced by an unrelated search."""
    controller = _controller()

    controller.run_search()

    assert controller.app_context.open_template_results_id is None


def test_the_table_is_cleared_before_the_request():
    controller = _controller()

    controller.run_search()

    controller.search_view.clear_table.assert_called_once()
    controller.search_view.remove_more_button.assert_called_once()


def test_the_preview_connection_is_dropped_before_a_refill():
    """A refill rewires it; connecting without dropping stacks them, so one click would fire
    several previews and add several layers."""
    controller = _controller()

    controller.run_search()

    controller.search_view.disconnect_cell_preview.assert_called_once()


def test_a_provider_that_cannot_search_is_swapped_first():
    controller = _controller()

    controller.run_search()

    controller.search_view.ensure_search_provider.assert_called_once_with(
        controller.provider_service)


def test_no_aoi_refuses_the_search(alerts):
    controller = _controller(aoi=None)

    controller.run_search()

    controller.search_service.search.assert_not_called()
    assert "area of interest" in alerts[0]


def test_no_working_directory_refuses_the_search():
    """The user was asked and declined; searching anyway would fetch results with nowhere to
    write them."""
    controller = _controller(output_dir_ok=False)

    controller.run_search()

    controller.search_service.search.assert_not_called()


def test_the_aoi_check_runs_before_the_directory_prompt(alerts):
    """Without an AOI there is nothing to search for, so prompting for a directory first would
    ask the user to fix the wrong thing."""
    controller = _controller(aoi=None, output_dir_ok=False)

    controller.run_search()

    assert "area of interest" in alerts[0]


def test_results_fill_the_table_without_local_sorting():
    controller = _controller()

    controller.on_search_results({"features": []})

    controller.search_view.fill_table.assert_called_once()
    assert controller.search_view.fill_table.call_args.kwargs["sort"] is False
