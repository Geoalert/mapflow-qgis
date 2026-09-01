"""QGIS-tier tests: template edit/control rights (rename, pause / resume / restart).

Maintainers and owners may control any template. A contributor may control only their OWN
templates (``template.userId == user_id``); readonly may control none. This mirrors
``AppContext.can_edit_template``."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.mapflow import Mapflow
from mapflow.functional.app_context import AppContext
from mapflow.schema.project import UserRole

OWNER_ID = "user-1"
OTHER_ID = "user-2"


def _plugin_with_template(user_role, is_active=True, status="READY",
                          template_user_id=OWNER_ID, user_id=OWNER_ID):
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda text: text
    plugin.dlg = MagicMock()
    plugin.processing_service = MagicMock()
    plugin.template_service = MagicMock()
    plugin.template_service.in_template_mode = False
    plugin.processing_service.selected_template.return_value = SimpleNamespace(
        isActive=is_active, status=status, userId=template_user_id,
        is_failed=(status or "").upper() == "FAILED",
    )
    plugin.processing_service.selected_processing.return_value = None
    # Selecting a template row happens in the processings list, not inside a template.
    plugin.template_service.in_template_mode = False
    app_context = AppContext()
    app_context.user_role = user_role
    app_context.user_id = user_id
    plugin.app_context = app_context
    return plugin


def test_pause_disabled_for_contributor_on_others_template():
    plugin = _plugin_with_template(UserRole.contributor, is_active=True,
                                   template_user_id=OTHER_ID)

    plugin.update_processing_options_menu()

    plugin.dlg.template_pause_action.setEnabled.assert_called_once_with(False)


def test_pause_enabled_for_contributor_on_own_template():
    plugin = _plugin_with_template(UserRole.contributor, is_active=True,
                                   template_user_id=OWNER_ID)

    plugin.update_processing_options_menu()

    plugin.dlg.template_pause_action.setEnabled.assert_called_once_with(True)


def test_pause_enabled_for_maintainer():
    plugin = _plugin_with_template(UserRole.maintainer, is_active=True,
                                   template_user_id=OTHER_ID)

    plugin.update_processing_options_menu()

    plugin.dlg.template_pause_action.setEnabled.assert_called_once_with(True)


def test_resume_disabled_for_contributor_on_others_template():
    plugin = _plugin_with_template(UserRole.contributor, is_active=False, status="READY",
                                   template_user_id=OTHER_ID)

    plugin.update_processing_options_menu()

    plugin.dlg.template_resume_action.setEnabled.assert_called_once_with(False)


def test_resume_enabled_for_contributor_on_own_template():
    plugin = _plugin_with_template(UserRole.contributor, is_active=False, status="READY",
                                   template_user_id=OWNER_ID)

    plugin.update_processing_options_menu()

    plugin.dlg.template_resume_action.setEnabled.assert_called_once_with(True)


def test_resume_enabled_for_owner():
    plugin = _plugin_with_template(UserRole.owner, is_active=False, status="READY",
                                   template_user_id=OTHER_ID)

    plugin.update_processing_options_menu()

    plugin.dlg.template_resume_action.setEnabled.assert_called_once_with(True)


def test_restart_disabled_for_contributor_on_others_template():
    plugin = _plugin_with_template(UserRole.contributor, is_active=False, status="FAILED",
                                   template_user_id=OTHER_ID)

    plugin.update_processing_options_menu()

    plugin.dlg.template_restart_action.setEnabled.assert_called_once_with(False)


def test_restart_enabled_for_contributor_on_own_template():
    plugin = _plugin_with_template(UserRole.contributor, is_active=False, status="FAILED",
                                   template_user_id=OWNER_ID)

    plugin.update_processing_options_menu()

    plugin.dlg.template_restart_action.setEnabled.assert_called_once_with(True)


def test_failed_but_active_template_offers_restart_not_pause():
    # A FAILED template can still be isActive; it must offer Restart (not Pause), matching
    # table_status which prioritises FAILED over isActive.
    plugin = _plugin_with_template(UserRole.owner, is_active=True, status="FAILED")

    plugin.update_processing_options_menu()

    plugin.dlg.template_restart_action.setEnabled.assert_called_once_with(True)
    plugin.dlg.template_pause_action.setEnabled.assert_not_called()
    actions = [c.args[0] for c in plugin.dlg.options_menu.addAction.call_args_list]
    assert plugin.dlg.template_restart_action in actions
    assert plugin.dlg.template_pause_action not in actions


def test_rename_shown_for_contributor_on_own_template_only():
    own = _plugin_with_template(UserRole.contributor, template_user_id=OWNER_ID)
    own.update_processing_options_menu()
    own_actions = [c.args[0] for c in own.dlg.options_menu.addAction.call_args_list]
    assert own.dlg.template_rename_action in own_actions

    other = _plugin_with_template(UserRole.contributor, template_user_id=OTHER_ID)
    other.update_processing_options_menu()
    other_actions = [c.args[0] for c in other.dlg.options_menu.addAction.call_args_list]
    assert other.dlg.template_rename_action not in other_actions
