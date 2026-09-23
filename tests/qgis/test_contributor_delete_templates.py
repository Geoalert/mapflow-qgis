"""QGIS-tier tests: a CONTRIBUTOR may delete their OWN templates but never processings.

The Delete button is recomputed on processings-table selection change and enabled only when
every selected row is a template the contributor owns (``all_selected_templates_editable`` +
``ProjectProcessingController.update_delete_button_state``). Other roles keep their fixed
role-based state.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

from PyQt5.QtCore import QObject

from mapflow.functional.app_context import AppContext
from mapflow.functional.controller.project_processing_controller import ProjectProcessingController
from mapflow.functional.service.processing_service import ProcessingService
from mapflow.schema.project import UserRole

OWNER = "user-1"
OTHER = "user-2"


def _service(user_role, user_id, selected_ids, templates):
    service = ProcessingService.__new__(ProcessingService)
    service.set_selected_ids(selected_ids)
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


# ---- ProjectProcessingController.update_delete_button_state --------------------------------

def _controller(user_role, editable):
    controller = ProjectProcessingController.__new__(ProjectProcessingController)
    QObject.__init__(controller)
    controller.tr = lambda text: text
    controller.dlg = MagicMock()
    controller.processing_service = MagicMock()
    controller.template_service = MagicMock()
    controller.template_service.in_template_mode = False
    controller.processing_service.all_selected_templates_editable.return_value = editable
    controller.app_context = SimpleNamespace(user_role=user_role)
    return controller


def test_delete_enabled_for_contributor_on_own_templates():
    controller = _controller(UserRole.contributor, editable=True)
    controller.update_delete_button_state()
    controller.dlg.deleteProcessings.setEnabled.assert_called_once_with(True)
    controller.dlg.deleteProcessings.setToolTip.assert_called_once_with("")


def test_delete_disabled_for_contributor_on_processing_or_others_template():
    controller = _controller(UserRole.contributor, editable=False)
    controller.update_delete_button_state()
    controller.dlg.deleteProcessings.setEnabled.assert_called_once_with(False)
    # A non-empty explanatory tooltip is set.
    (tip,), _ = controller.dlg.deleteProcessings.setToolTip.call_args
    assert tip


def test_delete_button_untouched_for_non_contributor():
    for role in (UserRole.maintainer, UserRole.owner, UserRole.readonly):
        controller = _controller(role, editable=True)
        controller.update_delete_button_state()
        controller.dlg.deleteProcessings.setEnabled.assert_not_called()
        controller.dlg.deleteProcessings.setToolTip.assert_not_called()
