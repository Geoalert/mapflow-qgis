"""QGIS-tier tests for what the processings table offers, and for the pool it resolves against.

Two things moved into `ProjectProcessingController` here: the details dialog (with the "go to
source" fork that reopens a processing's imagery), and the answer to "which view is the table
showing", which `ProcessingService` used to reach into `TemplateService` for.

That reach is what these pin. `ProcessingService` is now *told* — `set_open_template` and
`set_visible_processings` — and the push comes from `TemplateService`'s own signals, so the tests
below drive the real services and check that the selection resolves against the right pool.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from PyQt5.QtCore import QObject

from mapflow.functional.controller import project_processing_controller as ppc_mod
from mapflow.functional.controller.project_processing_controller import ProjectProcessingController
from mapflow.functional.service.processing_service import ProcessingService
from mapflow.functional.service.template_service import TemplateService
from mapflow.schema import ImagerySearchParams, MyImageryParams, UserDefinedParams


def _controller():
    controller = ProjectProcessingController.__new__(ProjectProcessingController)
    QObject.__init__(controller)
    controller.tr = lambda text: text
    controller.dlg = MagicMock()
    controller.processing_service = MagicMock()
    controller.template_service = MagicMock()
    controller.template_service.in_template_mode = False
    controller.aoi_service = MagicMock()
    controller.data_catalog_service = MagicMock()
    controller.result_loader = MagicMock()
    controller.processing_view = MagicMock()
    controller.app_context = SimpleNamespace(user_role=None)
    return controller


def _processing(source_params):
    return SimpleNamespace(id="p-1", params=SimpleNamespace(sourceParams=source_params))


# ---------- reopening the imagery a processing ran on ----------

def test_a_search_based_processing_downloads_its_aoi_first():
    """The search table is filled from the AOI, so the source cannot be shown before it lands."""
    controller = _controller()
    window = MagicMock()

    controller.show_processing_source(_processing(ImagerySearchParams(imagerySearch=None)), window)

    kwargs = controller.result_loader.download_aoi_file.call_args.kwargs
    assert kwargs["pid"] == "p-1"
    assert kwargs["callback"] is controller.processing_service.duplicate_aoi_callback
    window.close.assert_called_once()


def test_a_my_imagery_processing_is_handed_to_the_catalog():
    controller = _controller()
    source_params = MyImageryParams(myImagery=None)

    controller.show_processing_source(_processing(source_params), MagicMock())

    controller.data_catalog_service.show_my_imagery_source.assert_called_once_with(source_params)


def test_a_user_defined_source_is_described_in_a_message(monkeypatch):
    said = []
    monkeypatch.setattr(ppc_mod, "alert", lambda message, *a, **k: said.append(message))
    controller = _controller()
    controller.processing_view.show_user_provider_info.return_value = "XYZ tiles at zoom 18"

    controller.show_processing_source(_processing(UserDefinedParams(userDefined=None)), MagicMock())

    assert said == ["XYZ tiles at zoom 18"]


@pytest.mark.parametrize("source_params", [
    ImagerySearchParams(imagerySearch=None),
    MyImageryParams(myImagery=None),
    UserDefinedParams(userDefined=None),
    None,  # a provider-based processing: nothing to reopen
])
def test_the_details_window_always_closes(source_params, monkeypatch):
    monkeypatch.setattr(ppc_mod, "alert", lambda *a, **k: None)
    controller = _controller()
    window = MagicMock()

    controller.show_processing_source(_processing(source_params), window)

    window.close.assert_called_once()


# ---------- which entity 'See details' opens ----------

def test_a_selected_template_row_opens_the_template_details():
    controller = _controller()
    template = SimpleNamespace(id="t-1")
    controller.processing_service.selected_template.return_value = template
    controller.processing_service.selected_processing.return_value = None

    controller.show_selected_details()

    controller.template_service.show_template_details.assert_called_once_with(template)


def test_a_processing_row_inside_a_template_opens_the_processing_details():
    """Both are selected in the in-template view — the processing wins, or a processing's details
    would be unreachable there."""
    controller = _controller()
    controller.processing_service.selected_template.return_value = SimpleNamespace(id="t-1")
    controller.processing_service.selected_processing.return_value = None
    controller.show_details = MagicMock()

    controller.processing_service.selected_processing.return_value = SimpleNamespace(id="p-1")
    controller.show_selected_details()

    controller.show_details.assert_called_once()
    controller.template_service.show_template_details.assert_not_called()


# ---------- the pool a table row resolves against ----------

def _processing_service(processings):
    service = ProcessingService.__new__(ProcessingService)
    # Required, not decoration: a signal connected to a bound method of an uninitialised QObject
    # silently never fires, and every assertion below would then pass for the wrong reason.
    QObject.__init__(service)
    service.processings = processings
    return service


def _template_service():
    service = TemplateService(app_context=MagicMock(), processing_service=MagicMock())
    return service


def _push(template_service, processing_service):
    """The wiring `ProjectProcessingController` sets up, without the rest of the controller."""
    template_service.templateOpened.connect(processing_service.set_open_template)
    template_service.templateClosed.connect(lambda *_: processing_service.set_open_template(None))
    template_service.visibleProcessingsChanged.connect(processing_service.set_visible_processings)


def test_without_a_template_the_selection_resolves_against_the_projects_processings():
    service = _processing_service({"p-1": "project processing"})
    service.set_selected_ids(["p-1"])

    assert service.selected_processings() == ["project processing"]


def test_an_open_template_switches_the_pool_the_selection_resolves_against():
    processing_service = _processing_service({"p-1": "project processing"})
    processing_service.set_selected_ids(["p-2"])
    template_service = _template_service()
    _push(template_service, processing_service)

    template_service.in_template_mode = True
    template_service.template_processings = {"p-2": "template processing"}

    assert processing_service.selected_processings() == ["template processing"]


def test_leaving_the_template_puts_the_pool_back():
    processing_service = _processing_service({"p-1": "project processing"})
    template_service = _template_service()
    _push(template_service, processing_service)
    template_service.in_template_mode = True
    template_service.template_processings = {"p-2": "template processing"}

    template_service.in_template_mode = False
    template_service.template_processings = {}

    processing_service.set_selected_ids(["p-1"])
    assert processing_service.selected_processings() == ["project processing"]


def test_processings_arriving_after_the_template_was_left_do_not_come_back_as_the_pool():
    """The fetch is in flight when the user steps out; its callback still assigns. Announcing the
    template's processings then would leave the project list resolving against them."""
    processing_service = _processing_service({"p-1": "project processing"})
    template_service = _template_service()
    _push(template_service, processing_service)

    template_service.in_template_mode = False  # already left
    template_service.template_processings = {"p-2": "late arrival"}

    processing_service.set_selected_ids(["p-1"])
    assert processing_service.selected_processings() == ["project processing"]


def test_opening_and_closing_a_template_tells_the_processing_service_which_one():
    processing_service = _processing_service({})
    template_service = _template_service()
    _push(template_service, processing_service)
    template = SimpleNamespace(id="t-1")

    template_service.templateOpened.emit(template)
    assert processing_service._open_template is template

    template_service.templateClosed.emit(template)
    assert processing_service._open_template is None


def test_a_service_built_without_init_reports_no_open_template():
    """The class-level defaults matter: plenty of callers (and tests) skip __init__."""
    service = ProcessingService.__new__(ProcessingService)

    assert service._open_template is None
    assert service._visible_processings is None
