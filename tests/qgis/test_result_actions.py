"""QGIS-tier tests for loading and saving a processing's results.

`tests/qgis/behavioral/test_results_loading.py` drives the happy path end to end. These cover the
guards in front of it, which that journey never reaches: a selection that is a template rather
than a processing, a run that did not finish cleanly, and the working-directory prompt that any
action writing to disk has to pass first.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from PyQt5.QtCore import QObject

from mapflow.functional.controller import project_processing_controller as ppc_mod
from mapflow.functional.controller.project_processing_controller import ProjectProcessingController


@pytest.fixture(autouse=True)
def alerts(monkeypatch):
    """Autouse: an unstubbed `alert` opens a modal that never closes in the test container."""
    said = []
    monkeypatch.setattr(ppc_mod, "alert", lambda message, *a, **k: said.append(message))
    return said


def _processing(is_ok=True):
    return SimpleNamespace(id="p-1", status=SimpleNamespace(is_ok=is_ok))


def _controller(processing=None, template=None, as_tiles=True, output_dir_ok=True):
    controller = ProjectProcessingController.__new__(ProjectProcessingController)
    QObject.__init__(controller)
    controller.tr = lambda text: text
    controller.processing_service = MagicMock()
    controller.processing_service.selected_template.return_value = template
    controller.processing_service.selected_processing.return_value = processing
    controller.processing_view = MagicMock()
    controller.processing_view.results_as_tiles.return_value = as_tiles
    controller.processing_view.results_as_local_file.return_value = not as_tiles
    controller.result_loader = MagicMock()
    controller.enter_template = MagicMock()
    controller.ensure_output_directory = lambda reason: output_dir_ok
    return controller


# ---------- load_results ----------

def test_a_template_row_is_opened_rather_than_loaded():
    template = SimpleNamespace(id="t-1")
    controller = _controller(template=template)

    controller.load_results()

    controller.enter_template.assert_called_once_with(template)
    controller.result_loader.load_result_tiles.assert_not_called()


def test_tiles_are_streamed_without_touching_the_working_directory():
    """The tile route adds a remote layer, so it must not demand a directory."""
    processing = _processing()
    controller = _controller(processing=processing, as_tiles=True, output_dir_ok=False)

    controller.load_results()

    controller.result_loader.load_result_tiles.assert_called_once_with(processing=processing)


def test_the_local_route_downloads_after_the_directory_is_confirmed():
    processing = _processing()
    controller = _controller(processing=processing, as_tiles=False)

    controller.load_results()

    controller.result_loader.download_results.assert_called_once_with(processing=processing)


def test_declining_the_directory_prompt_cancels_the_download():
    controller = _controller(processing=_processing(), as_tiles=False, output_dir_ok=False)

    controller.load_results()

    controller.result_loader.download_results.assert_not_called()


def test_an_unfinished_processing_has_no_results_to_load(alerts):
    controller = _controller(processing=_processing(is_ok=False))

    controller.load_results()

    controller.result_loader.load_result_tiles.assert_not_called()
    assert "correctly finished" in alerts[0]


def test_no_selection_loads_nothing():
    controller = _controller(processing=None)

    controller.load_results()

    controller.result_loader.load_result_tiles.assert_not_called()


# ---------- save result / download AOI ----------

def test_saving_the_result_file_needs_a_finished_processing(alerts):
    controller = _controller(processing=_processing(is_ok=False))

    controller.download_results_file()

    controller.result_loader.download_results_file.assert_not_called()
    assert "correctly finished" in alerts[0]


def test_saving_the_result_file_sends_the_processing_id():
    controller = _controller(processing=_processing())

    controller.download_results_file()

    assert controller.result_loader.download_results_file.call_args.kwargs["pid"] == "p-1"


def test_the_aoi_can_be_downloaded_for_a_failed_processing():
    """Deliberately not gated on status, unlike the result: the AOI exists as soon as the
    processing does, and is most wanted when the run failed."""
    controller = _controller(processing=_processing(is_ok=False))

    controller.download_aoi_file()

    assert controller.result_loader.download_aoi_file.call_args.kwargs["pid"] == "p-1"


def test_downloading_the_aoi_still_needs_a_working_directory():
    controller = _controller(processing=_processing(), output_dir_ok=False)

    controller.download_aoi_file()

    controller.result_loader.download_aoi_file.assert_not_called()


def test_downloading_the_aoi_without_a_selection_does_nothing():
    controller = _controller(processing=None)

    controller.download_aoi_file()

    controller.result_loader.download_aoi_file.assert_not_called()
