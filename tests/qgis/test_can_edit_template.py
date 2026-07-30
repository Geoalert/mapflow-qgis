"""QGIS-tier tests: AppContext.can_edit_template — a contributor may edit only their OWN
templates (template.userId == user_id); maintainer/owner may edit any; readonly none."""
from types import SimpleNamespace

from mapflow.functional.app_context import AppContext
from mapflow.schema.project import UserRole


def _ctx(user_role, user_id="user-1"):
    ctx = AppContext()
    ctx.user_role = user_role
    ctx.user_id = user_id
    return ctx


def _template(user_id):
    return SimpleNamespace(userId=user_id)


def test_owner_can_edit_any_template():
    assert _ctx(UserRole.owner).can_edit_template(_template("someone-else")) is True


def test_maintainer_can_edit_any_template():
    assert _ctx(UserRole.maintainer).can_edit_template(_template("someone-else")) is True


def test_readonly_cannot_edit_any_template():
    assert _ctx(UserRole.readonly).can_edit_template(_template("user-1")) is False


def test_contributor_can_edit_own_template():
    assert _ctx(UserRole.contributor, "user-1").can_edit_template(_template("user-1")) is True


def test_contributor_cannot_edit_others_template():
    assert _ctx(UserRole.contributor, "user-1").can_edit_template(_template("user-2")) is False


def test_contributor_ownership_compares_as_strings():
    # userId may arrive as a UUID object while user_id is a string (or vice-versa).
    assert _ctx(UserRole.contributor, "abc-123").can_edit_template(_template("abc-123")) is True


def test_contributor_without_user_id_cannot_edit():
    assert _ctx(UserRole.contributor, None).can_edit_template(_template("user-1")) is False


def test_none_role_allows_edit():
    # Personal/default project or admin: no shared-project role, full rights.
    assert _ctx(None).can_edit_template(_template("whoever")) is True
