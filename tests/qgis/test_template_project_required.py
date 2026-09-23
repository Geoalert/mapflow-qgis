"""QGIS-tier tests: a template requires a project.

Creating a planned search (template) is blocked without a selected project — the user is
prompted in the cost/message label — but the immediate (non-template) search is never blocked.
`TemplateService` emits `projectRequired` (the label) and alerts;
`TemplateController.on_search_mode_changed` drives the label through `TemplateView` when the
Search button switches mode. The rule is the template region's, so the search tab announces the
mode rather than deciding what it means.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.functional.controller.template_controller import TemplateController
from mapflow.functional.service.template_service import TemplateService
from mapflow.functional.view.template_view import TemplateView

PROMPT = "Select a project to create a template"


def _service(current_project, aoi=None):
    return TemplateService(
        app_context=SimpleNamespace(current_project=current_project, aoi=aoi,
                                    aoi_size=None, template_area_limit=0,
                                    project_id=None, plugin_version="1.0"),
        processing_service=MagicMock())


def _plugin(mode, current_project):
    """The controller, plus the mode the search tab would have announced."""
    controller = TemplateController.__new__(TemplateController)
    controller.dlg = MagicMock()
    controller.template_view = TemplateView(dlg=controller.dlg, iface=MagicMock(),
                                            config=MagicMock())
    controller.template_service = _service(current_project)
    controller.app_context = SimpleNamespace(current_project=current_project)
    controller._mode = mode
    return controller


def test_create_search_template_blocks_without_project(monkeypatch):
    warnings = []
    monkeypatch.setattr("mapflow.functional.service.template_service.alert_warning",
                        lambda m, *a, **k: warnings.append(m))
    service = _service(current_project=None, aoi=MagicMock())
    prompts = []
    service.projectRequired.connect(prompts.append)

    service.create_search_template("Name", aoi_details={"features": [1]},
                                   search_params=MagicMock())

    service.processing_service.api.create_template.assert_not_called()
    assert prompts and "project" in prompts[0].lower()   # the persistent label
    assert warnings and "project" in warnings[0].lower()  # and the pop-up


def test_on_search_mode_changed_prompts_in_plan_mode_without_project():
    plugin = _plugin(mode="plan", current_project=None)

    plugin.on_search_mode_changed(plugin._mode)

    plugin.dlg.processingProblemsLabel.setText.assert_called_once_with(PROMPT)


def test_on_search_mode_changed_clears_prompt_when_project_selected():
    plugin = _plugin(mode="plan", current_project=SimpleNamespace(id="p-1"))
    plugin.dlg.processingProblemsLabel.text.return_value = PROMPT

    plugin.on_search_mode_changed(plugin._mode)

    plugin.dlg.processingProblemsLabel.clear.assert_called_once()
    plugin.dlg.processingProblemsLabel.setText.assert_not_called()


def test_on_search_mode_changed_clears_prompt_in_search_mode():
    plugin = _plugin(mode="search", current_project=None)
    plugin.dlg.processingProblemsLabel.text.return_value = PROMPT

    plugin.on_search_mode_changed(plugin._mode)

    plugin.dlg.processingProblemsLabel.clear.assert_called_once()


def test_on_search_mode_changed_leaves_other_label_text_untouched():
    plugin = _plugin(mode="search", current_project=None)
    plugin.dlg.processingProblemsLabel.text.return_value = "Processing cost: 42 credits"

    plugin.on_search_mode_changed(plugin._mode)

    plugin.dlg.processingProblemsLabel.clear.assert_not_called()
    plugin.dlg.processingProblemsLabel.setText.assert_not_called()
