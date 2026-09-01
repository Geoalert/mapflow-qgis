"""QGIS-tier tests: a CONTRIBUTOR may delete their OWN templates but never processings.

The Delete button is recomputed on processings-table selection change and enabled only when
every selected row is a template the contributor owns (``all_selected_templates_editable`` +
``Mapflow.update_delete_button_state``). Other roles keep their fixed role-based state.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.mapflow import Mapflow
from mapflow.functional.app_context import AppContext
from mapflow.functional.service.processing_service import ProcessingService
from mapflow.schema.project import UserRole

OWNER = "user-1"
OTHER = "user-2"


def _service(user_role, user_id, selected_ids, templates):
    service = ProcessingService.__new__(ProcessingService)
    service.view = MagicMock()
    service.view.selected_processing_ids.return_value = list(selected_ids)
    service.templates = templates
    ctx = AppContext()
    ctx.user_role = user_role
    ctx.user_id = user_id
    service.app_context = ctx
    return service


def _tpl(user_id):
    return SimpleNamespace(userId=user_id)


# ---- ProcessingService.all_selected_templates_editable -------------------------------------

def test_editable_true_when_contributor_owns_all_selected_templates():
    svc = _service(UserRole.contributor, OWNER, ["t1", "t2"],
                   {"t1": _tpl(OWNER), "t2": _tpl(OWNER)})
    assert svc.all_selected_templates_editable() is True


def test_editable_false_when_a_processing_is_also_selected():
    # "p1" is not in templates -> selection is not templates-only.
    svc = _service(UserRole.contributor, OWNER, ["t1", "p1"], {"t1": _tpl(OWNER)})
    assert svc.all_selected_templates_editable() is False


def test_editable_false_when_a_selected_template_is_not_owned():
    svc = _service(UserRole.contributor, OWNER, ["t1", "t2"],
                   {"t1": _tpl(OWNER), "t2": _tpl(OTHER)})
    assert svc.all_selected_templates_editable() is False


def test_editable_false_when_nothing_selected():
    svc = _service(UserRole.contributor, OWNER, [], {"t1": _tpl(OWNER)})
    assert svc.all_selected_templates_editable() is False


def test_editable_true_for_maintainer_even_on_others_template():
    svc = _service(UserRole.maintainer, OWNER, ["t1"], {"t1": _tpl(OTHER)})
    assert svc.all_selected_templates_editable() is True


# ---- Mapflow.update_delete_button_state ----------------------------------------------------

def _plugin(user_role, editable):
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda text: text
    plugin.dlg = MagicMock()
    plugin.processing_service = MagicMock()
    plugin.template_service = MagicMock()
    plugin.template_service.in_template_mode = False
    plugin.processing_service.all_selected_templates_editable.return_value = editable
    plugin.app_context = SimpleNamespace(user_role=user_role)
    return plugin


def test_delete_enabled_for_contributor_on_own_templates():
    plugin = _plugin(UserRole.contributor, editable=True)
    plugin.update_delete_button_state()
    plugin.dlg.deleteProcessings.setEnabled.assert_called_once_with(True)
    plugin.dlg.deleteProcessings.setToolTip.assert_called_once_with("")


def test_delete_disabled_for_contributor_on_processing_or_others_template():
    plugin = _plugin(UserRole.contributor, editable=False)
    plugin.update_delete_button_state()
    plugin.dlg.deleteProcessings.setEnabled.assert_called_once_with(False)
    # A non-empty explanatory tooltip is set.
    (tip,), _ = plugin.dlg.deleteProcessings.setToolTip.call_args
    assert tip


def test_delete_button_untouched_for_non_contributor():
    for role in (UserRole.maintainer, UserRole.owner, UserRole.readonly):
        plugin = _plugin(role, editable=True)
        plugin.update_delete_button_state()
        plugin.dlg.deleteProcessings.setEnabled.assert_not_called()
        plugin.dlg.deleteProcessings.setToolTip.assert_not_called()
