"""Startup configures the plugin only once both of its inputs are in.

Two responses decide what a returning user sees after logging in: the first account status, which
starts the configuration, and the project remembered from the last session, which decides whether
that configuration opens the project's processings or the projects list — and carries the model
list the imagery sources are filtered by. They arrive in either order. Configuring on the status
alone made the table depend on which landed first, and the login code also stored the lookup's
return value (always None) as the open project.

These drive the composition root's startup slots and `ProjectService`'s lookup directly; the
behavioral journeys cannot hold one reply back while delivering the other.
"""
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from PyQt5.QtCore import QObject

from mapflow.config import Config
from mapflow.functional.service import project_service as project_service_module
from mapflow.functional.service.project_service import ProjectService
from mapflow.http import RequestMode
from mapflow.mapflow import Mapflow

LOGIN_RESPONSE = Path(__file__).parent / "behavioral" / "responses" / "login_projects_default.json"


def _root(saved_project_pending: bool):
    plugin = Mapflow.__new__(Mapflow)
    plugin._saved_project_pending = saved_project_pending
    plugin._deferred_startup_status = None
    plugin._configure_from_status = MagicMock()
    return plugin


# ---------- the order the two responses arrive in ----------

def test_a_status_that_arrives_first_waits_for_the_saved_project():
    plugin = _root(saved_project_pending=True)

    plugin.on_account_status({"status": "first"}, app_startup_request=True)
    plugin._configure_from_status.assert_not_called()

    plugin.on_saved_project_resolved()
    plugin._configure_from_status.assert_called_once_with({"status": "first"})


def test_a_saved_project_that_arrives_first_lets_the_status_configure_at_once():
    plugin = _root(saved_project_pending=True)

    plugin.on_saved_project_resolved()
    plugin._configure_from_status.assert_not_called()  # nothing to configure from yet

    plugin.on_account_status({"status": "second"}, app_startup_request=True)
    plugin._configure_from_status.assert_called_once_with({"status": "second"})


def test_without_a_saved_project_the_status_configures_at_once():
    plugin = _root(saved_project_pending=False)

    plugin.on_account_status({"status": "only"}, app_startup_request=True)

    plugin._configure_from_status.assert_called_once_with({"status": "only"})


def test_a_later_status_refresh_configures_nothing():
    plugin = _root(saved_project_pending=False)

    plugin.on_account_status({"status": "refresh"}, app_startup_request=False)
    plugin.on_saved_project_resolved()

    plugin._configure_from_status.assert_not_called()


@pytest.mark.parametrize("project, opens", [
    (SimpleNamespace(id="saved-1"), "show_processings"),
    (None, "show_projects"),
])
def test_the_configuration_opens_the_table_for_what_the_lookup_found(project, opens):
    plugin = Mapflow.__new__(Mapflow)
    plugin.data_catalog_service = MagicMock()
    plugin.processing_service = MagicMock()
    plugin.project_service = MagicMock()
    plugin.project_processing_controller = MagicMock()
    plugin.dlg = MagicMock()
    plugin.setup_providers = MagicMock()
    plugin.setup_search_providers = MagicMock()
    plugin.on_provider_change = MagicMock()
    plugin.app_context = SimpleNamespace(billing_type=None, review_workflow_enabled=False,
                                         current_project=project)

    plugin._configure_from_status({})

    # Startup opened it, not a click: nobody is waiting on this particular request.
    getattr(plugin.project_processing_controller, opens).assert_called_once_with(
        mode=RequestMode.BACKGROUND)


# ---------- logging in ----------

def _logged_in_root():
    plugin = Mapflow.__new__(Mapflow)
    plugin.config = Config
    plugin.dlg = MagicMock()
    plugin.dlg_login = MagicMock()
    plugin.account_service = MagicMock()
    plugin.project_service = MagicMock()
    plugin.data_catalog_service = MagicMock()
    plugin.project_view = MagicMock()
    plugin.project_processing_controller = MagicMock()
    plugin._saved_project_pending = False
    plugin._deferred_startup_status = None
    return plugin


def _login_response():
    response = MagicMock()
    body = json.loads(LOGIN_RESPONSE.read_text())["body"]
    response.readAll.return_value.data.return_value = json.dumps(body).encode()
    return response


def test_login_looks_up_the_saved_project_without_keeping_a_stale_one():
    plugin = _logged_in_root()
    plugin.app_context = SimpleNamespace(settings=MagicMock(), project_id="saved-1",
                                         current_project=SimpleNamespace(id="from-an-earlier-login"),
                                         billing_type=None, user_id=None, logged_in=False)

    plugin.log_in_callback(_login_response())

    assert plugin.app_context.current_project is None, (
        "until the lookup answers, no project is open — a leftover one would choose the table")
    assert plugin._saved_project_pending is True
    plugin.project_service.open_saved_project.assert_called_once_with("saved-1")


def test_login_without_a_saved_project_waits_for_nothing_and_keeps_nothing():
    """Clearing the project filter forgets the saved id but not the open project, so a leftover can
    exist without a saved id — and it would still choose the processings table, for no project."""
    plugin = _logged_in_root()
    plugin.app_context = SimpleNamespace(settings=MagicMock(), project_id=None,
                                         current_project=SimpleNamespace(id="from-an-earlier-login"),
                                         billing_type=None, user_id=None, logged_in=False)

    plugin.log_in_callback(_login_response())

    assert plugin._saved_project_pending is False
    assert plugin.app_context.current_project is None
    plugin.project_service.open_saved_project.assert_not_called()


def test_login_asks_for_the_account_status_once():
    """The startup poll fetches and applies the status; a second request from the login callback
    fetched the same response again and configured nothing."""
    plugin = _logged_in_root()
    plugin.app_context = SimpleNamespace(settings=MagicMock(), project_id=None, current_project=None,
                                         billing_type=None, user_id=None, logged_in=False)

    plugin.log_in_callback(_login_response())

    plugin.account_service.request_status.assert_not_called()
    plugin.account_service.begin_startup_polling.assert_called_once()


# ---------- the lookup always announces that it is over ----------

@pytest.fixture
def projects():
    service = ProjectService.__new__(ProjectService)
    QObject.__init__(service)
    service.api = MagicMock()
    service.app_context = SimpleNamespace(settings=MagicMock(), project_id="saved-1",
                                          current_project=None)
    service.area_calculator_service = MagicMock()
    service.apply_project_aoi_area_limit = MagicMock()
    service.get_project_sharing = MagicMock()
    service.setup_project_change_rights = MagicMock()
    resolved = []
    service.savedProjectResolved.connect(lambda: resolved.append(True))
    return service, resolved


def test_the_lookup_is_a_background_request(projects):
    service, _resolved = projects

    service.open_saved_project("saved-1")

    assert service.api.get_project.call_args.kwargs["mode"] is RequestMode.BACKGROUND


def _project_response():
    response = MagicMock()
    response.readAll.return_value.data.return_value = b'{"id": "saved-1"}'
    return response


def test_a_found_project_is_announced(projects):
    service, resolved = projects

    with patch.object(project_service_module.MapflowProject, "from_dict",
                      return_value=SimpleNamespace(id="saved-1")):
        service.get_project_callback(_project_response())

    assert resolved == [True]


def test_a_project_that_fails_to_apply_is_still_announced(projects):
    """The callback runs behind the error guard, so an emit after a raise would never happen and
    startup would wait forever."""
    service, resolved = projects

    with patch.object(project_service_module.MapflowProject, "from_dict",
                      side_effect=KeyError("drifted payload")):
        with pytest.raises(KeyError):
            service.get_project_callback(_project_response())

    assert resolved == [True]


def test_a_project_that_cannot_be_opened_is_announced(projects):
    service, resolved = projects

    service.get_project_error_handler(MagicMock())

    assert resolved == [True]
