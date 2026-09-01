"""QGIS-tier tests for the in-template navigation level (spec 002_F):
Projects -> Processings -> Template, with left/right buttons and signals."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from PyQt5.QtCore import QObject

from mapflow.functional.controller.project_processing_controller import ProjectProcessingController
from mapflow.functional.service.processing_service import ProcessingService
from mapflow.functional.service.template_service import TemplateService


def _bare_service():
    """A ProcessingService with only its QObject base initialised (so signals work)."""
    service = ProcessingService.__new__(ProcessingService)
    QObject.__init__(service)
    return service


def _bare_template_service():
    """A TemplateService with the in-template view's collaborators mocked. It owns the
    navigation state and its signals since the templates step."""
    service = TemplateService(app_context=MagicMock(), processing_service=MagicMock())
    return service


def _controller():
    controller = ProjectProcessingController.__new__(ProjectProcessingController)
    # Initialise the QObject base so Qt signal->slot delivery works (the controller connects
    # its own methods to service signals in _setup_navigation).
    QObject.__init__(controller)
    controller.tr = lambda text: text
    controller.dlg = MagicMock()
    controller.processing_service = MagicMock()
    controller.template_service = MagicMock()
    controller.template_service.in_template_mode = False
    controller.project_service = MagicMock()
    controller.app_context = SimpleNamespace()
    return controller


def test_navigate_back_exits_template_when_inside():
    controller = _controller()
    controller.template_service.in_template_mode = True
    controller.exit_template = MagicMock()
    controller.show_projects = MagicMock()

    controller.navigate_back()

    controller.exit_template.assert_called_once()
    controller.show_projects.assert_not_called()


def test_navigate_back_goes_to_projects_when_in_processings():
    controller = _controller()
    controller.template_service.in_template_mode = False
    controller.exit_template = MagicMock()
    controller.show_projects = MagicMock()

    controller.navigate_back()

    controller.show_projects.assert_called_once()
    controller.exit_template.assert_not_called()


def test_navigate_into_template_requires_single_template():
    controller = _controller()
    controller.template_service.in_template_mode = False
    template = SimpleNamespace(id="t-1", name="T1")
    controller.processing_service.selected_template.return_value = template
    controller.processing_service.is_only_templates_selected.return_value = True
    controller.enter_template = MagicMock()

    controller.navigate_into_template()

    controller.enter_template.assert_called_once_with(template)


def test_navigate_into_template_noop_when_processing_selected():
    controller = _controller()
    controller.template_service.in_template_mode = False
    controller.processing_service.selected_template.return_value = SimpleNamespace(id="t-1")
    controller.processing_service.is_only_templates_selected.return_value = False
    controller.enter_template = MagicMock()

    controller.navigate_into_template()

    controller.enter_template.assert_not_called()


def test_enter_template_view_emits_opened_signal():
    service = _bare_template_service()
    received = []
    service.templateOpened.connect(lambda t: received.append(t))
    template = SimpleNamespace(id="t-1", name="T1", aoi_dtos=lambda: [])

    service._do_enter_template(template)

    assert service.in_template_mode is True
    assert service.active_template is template
    assert received == [template]


def test_enter_arrow_disables_on_template_opened_signal():
    """Entering a template is async when aoiDetails must be fetched, so `in_template_mode`
    flips only after the controller's synchronous `_update_nav_buttons` has run. The arrow must
    therefore be refreshed on the `templateOpened` signal — not only on the next selection
    change (the reported bug: the '>' stayed enabled until an AOI/processing was selected)."""
    controller = _controller()
    service = _bare_template_service()  # real signals
    service.in_template_mode = False
    controller.template_service = service
    controller.processing_service.is_only_templates_selected = MagicMock(return_value=True)
    controller.processing_service.selected_template = MagicMock(
        return_value=SimpleNamespace(id="t-1"))

    controller._setup_navigation()  # wires templateOpened/Closed -> _update_nav_buttons
    # A single template is selected in the processings view -> arrow enabled.
    assert controller.dlg.switchProcessingsFakeButton.setEnabled.call_args.args == (True,)

    # Async enter completes: in_template_mode flips, then templateOpened fires.
    service.in_template_mode = True
    service.templateOpened.emit(SimpleNamespace(id="t-1"))

    # Arrow is now disabled without any selection change.
    assert controller.dlg.switchProcessingsFakeButton.setEnabled.call_args.args == (False,)


def test_exit_template_view_emits_closed_signal_and_clears_state():
    service = _bare_template_service()
    service.in_template_mode = True
    template = SimpleNamespace(id="t-1", name="T1")
    service.active_template = template
    service.template_processings = {"p": object()}
    service.template_aois = {"a": object()}
    received = []
    service.templateClosed.connect(lambda t: received.append(t))

    service.exit_template_view()

    assert service.in_template_mode is False
    assert service.active_template is None
    assert service.template_processings == {}
    assert received == [template]


def test_processings_tab_text_truncates_long_template_name():
    controller = _controller()
    controller.dlg.tabWidget.findChild.return_value = object()  # processingsTab exists
    controller.dlg.tabWidget.indexOf.return_value = 1
    long_name = "1233333333333321 213 123 12213 2121 312 312"

    controller._set_processings_tab_text(long_name)

    label = controller.dlg.tabWidget.setTabText.call_args.args[1]
    assert len(label) == ProjectProcessingController.MAX_TAB_TEXT_LENGTH
    assert label.endswith("…")
    controller.dlg.tabWidget.setTabToolTip.assert_called_once_with(1, long_name)  # full name kept


def test_processings_tab_text_keeps_short_name():
    controller = _controller()
    controller.dlg.tabWidget.findChild.return_value = object()
    controller.dlg.tabWidget.indexOf.return_value = 1

    controller._set_processings_tab_text("Processing")

    assert controller.dlg.tabWidget.setTabText.call_args.args[1] == "Processing"
