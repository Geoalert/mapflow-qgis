"""QGIS-tier tests: a template requires a project.

Creating a planned search (template) is blocked without a selected project — the user is
prompted in the cost/message label — but the immediate (non-template) search is never blocked.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.mapflow import Mapflow

PROMPT = "Select a project to create a template"


def _plugin(mode, current_project):
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda text: text
    plugin.metadata_search_mode = mode
    plugin.dlg = MagicMock()
    plugin.app_context = SimpleNamespace(current_project=current_project)
    return plugin


def test_create_search_template_blocks_without_project():
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda text: text
    plugin.replace_search_provider_index = MagicMock()
    plugin.alert = MagicMock()
    plugin.dlg = MagicMock()
    plugin.processing_service = MagicMock()
    plugin.app_context = SimpleNamespace(current_project=None, aoi=MagicMock())

    plugin.create_search_template()

    plugin.processing_service.api.create_template.assert_not_called()
    # Inline label message...
    plugin.dlg.processingProblemsLabel.setText.assert_called_once()
    assert "project" in plugin.dlg.processingProblemsLabel.setText.call_args.args[0].lower()
    # ...and a pop-up so it's obvious.
    plugin.alert.assert_called_once()
    assert "project" in plugin.alert.call_args.args[0].lower()


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
