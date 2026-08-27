"""QGIS-tier tests: a template requires a project.

Creating a planned search (template) is blocked without a selected project — the user is
prompted in the cost/message label — but the immediate (non-template) search is never blocked.
`TemplateService` emits `projectRequired` (the label) and alerts; `Mapflow.update_plan_search_message`
drives the label through `TemplateView` based on the search/plan mode.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.functional.service.template_service import TemplateService
from mapflow.functional.view.template_view import TemplateView
from mapflow.mapflow import Mapflow

PROMPT = "Select a project to create a template"


def _service(current_project, aoi=None):
    return TemplateService(
        app_context=SimpleNamespace(current_project=current_project, aoi=aoi,
                                    aoi_size=None, template_area_limit=0,
                                    project_id=None, plugin_version="1.0"),
        processing_service=MagicMock())


def _plugin(mode, current_project):
    plugin = Mapflow.__new__(Mapflow)
    plugin.metadata_search_mode = mode
    plugin.dlg = MagicMock()
    plugin.template_view = TemplateView(dlg=plugin.dlg, iface=MagicMock(), config=MagicMock())
    plugin.template_service = _service(current_project)
    plugin.app_context = SimpleNamespace(current_project=current_project)
    return plugin


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


def test_update_plan_search_message_prompts_in_plan_mode_without_project():
    plugin = _plugin(mode="plan", current_project=None)

    plugin.update_plan_search_message()

    plugin.dlg.processingProblemsLabel.setText.assert_called_once_with(PROMPT)


def test_update_plan_search_message_clears_prompt_when_project_selected():
    plugin = _plugin(mode="plan", current_project=SimpleNamespace(id="p-1"))
    plugin.dlg.processingProblemsLabel.text.return_value = PROMPT

    plugin.update_plan_search_message()

    plugin.dlg.processingProblemsLabel.clear.assert_called_once()
    plugin.dlg.processingProblemsLabel.setText.assert_not_called()


def test_update_plan_search_message_clears_prompt_in_search_mode():
    plugin = _plugin(mode="search", current_project=None)
    plugin.dlg.processingProblemsLabel.text.return_value = PROMPT

    plugin.update_plan_search_message()

    plugin.dlg.processingProblemsLabel.clear.assert_called_once()


def test_update_plan_search_message_leaves_other_label_text_untouched():
    plugin = _plugin(mode="search", current_project=None)
    plugin.dlg.processingProblemsLabel.text.return_value = "Processing cost: 42 credits"

    plugin.update_plan_search_message()

    plugin.dlg.processingProblemsLabel.clear.assert_not_called()
    plugin.dlg.processingProblemsLabel.setText.assert_not_called()
