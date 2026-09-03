"""QGIS-tier tests for the start panel after it left ProcessingService.

The service used to read the model combo, the option checkboxes, the AOI combo and the search
selection, and drive the Start button and the confirmation dialog directly. A service may do none
of that (`spec/007_architecture.md` § Services). It now *announces* what the panel must show and
is *told* what the panel says, and `ProcessingController` is the only thing that touches widgets.

The wiring is built in the real `ProcessingController.__init__`, and these run it — not a
hand-rolled set of connections. A test that makes the connection it checks cannot fail when the
production code stops making it (the bug that survived 866 tests in C2.2a).
"""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from PyQt5.QtCore import QObject, pyqtSignal

from mapflow.functional.controller.processing_controller import ProcessingController
from mapflow.functional.service import processing_service as processing_service_module
from mapflow.functional.service.processing_service import ProcessingService


class _AoiServiceStub(QObject):
    """The three AOI signals `ProcessingController.__init__` connects unconditionally."""
    aoiLayerRegistered = pyqtSignal(object)
    aoiLayersChanged = pyqtSignal()
    currentAoiLayerChanged = pyqtSignal(object)


class _Button(QObject):
    clicked = pyqtSignal()


def _service():
    service = ProcessingService.__new__(ProcessingService)
    QObject.__init__(service)  # it is the panel's signals we are testing
    service.tr = lambda text: text
    return service


def _controller(service, start_button=None):
    """A real `ProcessingController`, wired by its own `__init__` against a real service."""
    return ProcessingController(
        iface=MagicMock(),
        aoi_service=_AoiServiceStub(),
        aoi_view=MagicMock(),
        add_layer_action=MagicMock(),
        remove_layer_action=MagicMock(),
        processing_service=service,
        processing_view=MagicMock(),
        app_context=MagicMock(),
        start_button=start_button)


# ---------- the service announces, the controller renders ----------

def test_a_blocked_start_reaches_the_view():
    service = _service()
    controller = _controller(service)

    service.startDisabled.emit("too big", True)

    controller.processing_view.disable_processing_start.assert_called_once_with("too big", True)


def test_an_unblocked_start_clears_the_problem_and_enables():
    service = _service()
    controller = _controller(service)

    service.startUnblocked.emit()

    controller.processing_view.clear_problem_and_enable_start.assert_called_once()


def test_a_submission_in_flight_disables_the_button_and_returning_re_enables():
    service = _service()
    controller = _controller(service)

    service.submissionInFlight.emit(True)
    controller.processing_view.set_start_enabled.assert_called_with(False)

    service.submissionInFlight.emit(False)
    controller.processing_view.set_start_enabled.assert_called_with(True)


def test_a_quoted_cost_reaches_the_view():
    service = _service()
    controller = _controller(service)

    service.costQuoted.emit(42)

    controller.processing_view.set_processing_cost.assert_called_once_with(42)


def test_the_name_box_is_cleared_and_prefilled_on_request():
    service = _service()
    controller = _controller(service)

    service.processingNameCleared.emit("Run 1")
    controller.processing_view.clear_processing_name.assert_called_once_with("Run 1")

    service.processingNameSet.emit("Copy of Run 1")
    controller.processing_view.set_processing_name.assert_called_once_with("Copy of Run 1")


# ---------- the synchronous panel round trip ----------

def test_reading_the_panel_fills_it_before_returning():
    """`startPanelNeeded` is emitted and answered synchronously: by the time the service's own
    `_read_start_panel` returns, the controller has already pushed the panel back. This is the
    whole reason the inversion works instead of a stored copy going stale."""
    service = _service()
    controller = _controller(service)
    params = SimpleNamespace(wd_name="Buildings")
    controller.processing_view.read_processing_start_params.return_value = params
    controller.processing_view.enabled_blocks.return_value = [True, False]
    controller.processing_view.has_option_widgets.return_value = True
    controller.processing_view.aoi_layer_chosen.return_value = True

    returned = service._read_start_panel()

    assert returned is params
    assert service._start_params is params
    assert service._enabled_blocks == (True, False)
    assert service._has_option_widgets is True
    assert service._aoi_layer_chosen is True


def test_with_no_controller_listening_the_panel_reads_empty():
    """Tests and early startup have no controller yet; the service must answer "no parameters"
    rather than raise, so the ordinary "specify parameters" path handles it."""
    service = _service()

    assert service._read_start_panel() is None


# ---------- starting, and confirmation ----------

def test_the_start_button_starts_a_processing():
    service = _service()
    service.start_processing = MagicMock()
    button = _Button()
    # Keep the controller referenced: if it is collected, Qt drops the connection and the click
    # reaches nothing.
    controller = _controller(service, start_button=button)
    assert controller is not None

    button.clicked.emit()

    service.start_processing.assert_called_once()


def test_confirmation_is_asked_for_only_when_the_setting_says_so():
    service = _service()
    service.app_context = SimpleNamespace(settings=MagicMock())
    service.submit_processing = MagicMock()
    asked = []
    service.confirmationRequested.connect(asked.append)
    params = SimpleNamespace(name="Run 1")

    service.app_context.settings.value.return_value = "false"
    service.handle_processing_submission(params)
    assert asked == [] and service.submit_processing.call_count == 1

    service.app_context.settings.value.return_value = "true"
    service.handle_processing_submission(params)
    assert asked == [params] and service.submit_processing.call_count == 1  # not submitted again


def test_confirmation_raises_the_dialog_and_submits_on_accept():
    service = _service()
    service.submit_processing = MagicMock()
    service.confirmation_details = MagicMock(return_value={"price": None})
    controller = _controller(service)
    params = SimpleNamespace(name="Run 1")

    service.confirmationRequested.emit(params)

    call = controller.processing_view.confirm_processing_start.call_args
    assert call.kwargs["name"] == "Run 1"
    # The dialog is handed an on_accept that submits the very params it is confirming.
    call.kwargs["on_accept"]()
    service.submit_processing.assert_called_once_with(params)


def test_submit_sends_the_run_and_marks_it_in_flight():
    service = _service()
    service.iface = MagicMock()
    service.api = MagicMock()
    service.app_context = SimpleNamespace(plugin_name="Mapflow")
    service.template_to_run = MagicMock(return_value=None)
    service.start_processing_callback = MagicMock()
    service.start_processing_error_handler = MagicMock()
    in_flight = []
    service.submissionInFlight.connect(in_flight.append)
    params = SimpleNamespace(name="Run 1")

    with patch.object(processing_service_module, "alert"):
        service.submit_processing(params)

    service.api.create_processing.assert_called_once()
    assert in_flight == [True]  # re-enable is the callback's job, not this method's
