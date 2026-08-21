"""QGIS-tier tests: logging in records WHO is logged in.

``/projects/default`` is the user's own project, so its ``user`` section describes the logged-in
user. Its email is what ``ShareProject.get_user_role`` matches on, and under OAuth2 it is the only
source for it — there is no Basic token to decode. Losing it left every shared project resolving
to ``readonly`` while the header still named the real owner ("readonly, owner: <email>").
"""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.functional.app_context import AppContext
from mapflow.mapflow import Mapflow
from mapflow.schema.project import ShareProject, UserRole

USER_ID = "dac29386-df51-470c-a81b-5b1410f555b5"
USER_EMAIL = "a.trekin@geoalert.io"
PROJECT_ID = "f08c84ef-821a-4c50-ba96-1e83e1183c38"

# The reported payload, trimmed to the sections the callback reads.
LOGIN_RESPONSE = {
    "id": PROJECT_ID,
    "name": "Default",
    "isDefault": True,
    "description": None,
    "user": {
        "id": USER_ID,
        "email": USER_EMAIL,
        "role": "USER",
        "areaLimit": 25000000000,
        "aoiAreaLimit": 350000000000,
        "templateAreaLimit": 350000000000,
        "processedArea": 112036872,
        "isPremium": True,
        "reviewWorkflowEnabled": True,
        "isCustomer": True,
    },
    "shareProject": {
        "owners": [{"projectId": PROJECT_ID, "role": "owner",
                    "userId": USER_ID, "email": USER_EMAIL}],
        "users": [],
        "isCustomer": True,
    },
}


def _response(payload):
    reply = MagicMock()
    reply.readAll.return_value.data.return_value = json.dumps(payload).encode()
    return reply


def _plugin():
    """A Mapflow with a real AppContext; only the UI/network plumbing after the identity
    extraction is stubbed."""
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda text: text
    plugin.app_context = AppContext()
    plugin.app_context.settings = MagicMock()
    plugin.app_context.project_id = None
    plugin.config = SimpleNamespace(DEFAULT_MODEL="Buildings")
    for attribute in ("dlg", "dlg_login", "project_service", "processing_service",
                      "data_catalog_service", "project_processing_controller",
                      "user_status_update_timer", "app_startup_user_update_timer",
                      "update_processing_limit"):
        setattr(plugin, attribute, MagicMock())
    return plugin


def test_login_records_the_logged_in_users_email():
    """The regression: without this, ``username`` stayed empty under OAuth2."""
    plugin = _plugin()

    plugin.log_in_callback(_response(LOGIN_RESPONSE))

    assert plugin.app_context.username == USER_EMAIL


def test_login_records_the_logged_in_users_id():
    plugin = _plugin()

    plugin.log_in_callback(_response(LOGIN_RESPONSE))

    assert plugin.app_context.user_id == USER_ID


def test_the_recorded_email_resolves_the_owner_role():
    """End to end for the report: the same payload that showed "readonly, owner: <email>" must
    resolve to owner once the login remembers who logged in."""
    plugin = _plugin()

    plugin.log_in_callback(_response(LOGIN_RESPONSE))
    share = ShareProject.from_dict(LOGIN_RESPONSE["shareProject"])

    assert share.get_user_role(plugin.app_context.username) == UserRole.owner


def test_login_without_an_email_leaves_the_previous_one():
    """A payload with no email must not wipe an identity Basic auth already decoded."""
    plugin = _plugin()
    plugin.app_context.username = "typed@example.com"
    payload = json.loads(json.dumps(LOGIN_RESPONSE))
    payload["user"]["email"] = None

    plugin.log_in_callback(_response(payload))

    assert plugin.app_context.username == "typed@example.com"
