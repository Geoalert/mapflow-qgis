"""QGIS-tier tests: controlling a template's run state (pause / resume / restart) is a
maintainer+ action, so it is disabled for contributors (and readonly) in shared projects."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.mapflow import Mapflow
from mapflow.schema.project import UserRole


def test_can_pause_resume_template_requires_maintainer_or_owner():
    assert UserRole.readonly.can_pause_resume_template is False
    assert UserRole.contributor.can_pause_resume_template is False
    assert UserRole.maintainer.can_pause_resume_template is True
    assert UserRole.owner.can_pause_resume_template is True


def _plugin_with_template(user_role, is_active=True, status="READY"):
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda text: text
    plugin.dlg = MagicMock()
    plugin.processing_service = MagicMock()
    plugin.processing_service.selected_template.return_value = SimpleNamespace(
        isActive=is_active, status=status,
    )
    plugin.processing_service.selected_processing.return_value = None
    # Selecting a template row happens in the processings list, not inside a template.
    plugin.processing_service.in_template_mode = False
    plugin.app_context = SimpleNamespace(user_role=user_role)
    return plugin


def test_pause_disabled_for_contributor():
    plugin = _plugin_with_template(UserRole.contributor, is_active=True)

    plugin.update_processing_options_menu()

    plugin.dlg.template_pause_action.setEnabled.assert_called_once_with(False)


def test_pause_enabled_for_maintainer():
    plugin = _plugin_with_template(UserRole.maintainer, is_active=True)

    plugin.update_processing_options_menu()

    plugin.dlg.template_pause_action.setEnabled.assert_called_once_with(True)


def test_resume_disabled_for_contributor():
    plugin = _plugin_with_template(UserRole.contributor, is_active=False, status="READY")

    plugin.update_processing_options_menu()

    plugin.dlg.template_resume_action.setEnabled.assert_called_once_with(False)


def test_resume_enabled_for_owner():
    plugin = _plugin_with_template(UserRole.owner, is_active=False, status="READY")

    plugin.update_processing_options_menu()

    plugin.dlg.template_resume_action.setEnabled.assert_called_once_with(True)


def test_restart_disabled_for_contributor():
    plugin = _plugin_with_template(UserRole.contributor, is_active=False, status="FAILED")

    plugin.update_processing_options_menu()

    # The restart action is created inline via menu.addAction(...).
    plugin.dlg.options_menu.addAction.return_value.setEnabled.assert_called_with(False)
