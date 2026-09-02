"""The startup /user/status retry loop, now `AccountService`'s.

The loop exists because the plugin cannot configure itself until that response arrives, so
it re-asks every 500 ms. What it must never do is re-ask forever: each tick issues a
request, and nothing else in the plugin bounds it. Two ways it used to run away —

* the response arrived but applying it raised part-way through, so the stop that sat at the
  end of that callback never ran (the error guard swallows the exception, and everything
  after the raise point is skipped);
* the response never arrived at all, because the error branch had no handler.

Both left the plugin polling /user/status and /rasters/memory twice a second for the rest
of the session, while looking healthy on screen.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from PyQt5.QtNetwork import QNetworkReply

from mapflow.config import Config
from mapflow.functional.service.account_service import AccountService
from mapflow.mapflow import Mapflow


@pytest.fixture
def service():
    instance = AccountService(http=MagicMock(),
                              app_context=SimpleNamespace(),
                              config=Config,
                              server="https://example.invalid/api",
                              plugin_name="Mapflow")
    instance.tr = lambda text: text
    instance.begin_startup_polling()
    return instance


def _failed_response():
    response = MagicMock()
    response.error.return_value = QNetworkReply.HostNotFoundError
    return response


def test_a_tick_is_skipped_while_a_request_is_in_flight(service):
    """Ticks are not synchronised with responses, so without this a slow server would
    accumulate one outstanding request per 500 ms."""
    service.request_startup_status()
    service.request_startup_status()
    service.request_startup_status()

    assert service.http.get.call_count == 1


def test_the_next_tick_retries_once_the_previous_request_failed(service):
    service.request_startup_status()
    service.startup_status_error_handler(_failed_response())
    service.request_startup_status()

    assert service.http.get.call_count == 2
    assert service.startup_timer.isActive(), "a single failure is not fatal"


def test_polling_stops_and_the_user_is_told_after_the_attempt_budget(service):
    warnings = []
    service.startupGaveUp.connect(warnings.append)

    for _ in range(Config.STARTUP_STATUS_MAX_ATTEMPTS):
        service.request_startup_status()
        service.startup_status_error_handler(_failed_response())

    assert service.http.get.call_count == Config.STARTUP_STATUS_MAX_ATTEMPTS
    assert service.startup_timer.isActive(), "the budget is not spent yet"

    service.request_startup_status()

    assert not service.startup_timer.isActive()
    assert service.http.get.call_count == Config.STARTUP_STATUS_MAX_ATTEMPTS, "no further requests"
    assert len(warnings) == 1


def test_no_further_requests_after_the_budget_is_spent(service):
    warnings = []
    service.startupGaveUp.connect(warnings.append)

    for _ in range(Config.STARTUP_STATUS_MAX_ATTEMPTS + 5):
        service.request_startup_status()
        service.startup_status_error_handler(_failed_response())

    assert service.http.get.call_count == Config.STARTUP_STATUS_MAX_ATTEMPTS
    assert len(warnings) == 1, "give up once, not once per tick"


def test_a_raising_configuration_still_stops_the_poll(service):
    """The regression: the stop must not depend on the configuration succeeding."""
    service.apply_status = MagicMock(side_effect=TimeoutError("injected"))

    with pytest.raises(TimeoutError):
        service.startup_status_callback(MagicMock())

    assert not service.startup_timer.isActive()


def test_a_successful_startup_stops_the_poll(service):
    service.apply_status = MagicMock()

    service.startup_status_callback(MagicMock())

    assert not service.startup_timer.isActive()
    service.apply_status.assert_called_once()
    assert service.apply_status.call_args.kwargs == {"app_startup_request": True}


def test_logging_in_again_after_giving_up_gets_a_full_budget(service):
    for _ in range(Config.STARTUP_STATUS_MAX_ATTEMPTS + 1):
        service.request_startup_status()
        service.startup_status_error_handler(_failed_response())
    assert not service.startup_timer.isActive()

    service.begin_startup_polling()
    service.request_startup_status()

    assert service.http.get.call_count == Config.STARTUP_STATUS_MAX_ATTEMPTS + 1
    assert service.startup_timer.isActive()


def test_the_storage_quota_is_requested_once_on_success_not_per_retry():
    """/rasters/memory used to be issued from every tick, doubling the runaway traffic. It now
    hangs off `statusApplied`, which only a real response emits."""
    plugin = Mapflow.__new__(Mapflow)
    plugin.data_catalog_service = MagicMock()
    plugin.processing_service = MagicMock()
    plugin.dlg = MagicMock()
    plugin.app_context = SimpleNamespace(billing_type=None, review_workflow_enabled=False,
                                         current_project=None)
    plugin.project_processing_controller = MagicMock()
    plugin.project_service = MagicMock()
    plugin.setup_providers = MagicMock()
    plugin.setup_search_providers = MagicMock()
    plugin.on_provider_change = MagicMock()

    plugin.on_account_status({}, app_startup_request=False)
    plugin.data_catalog_service.get_user_limit.assert_not_called()

    plugin.on_account_status({}, app_startup_request=True)
    plugin.data_catalog_service.get_user_limit.assert_called_once()


def test_logout_stops_a_startup_poll_that_never_finished(service):
    """Otherwise a failed startup keeps polling the account endpoint after logging out."""
    plugin = Mapflow.__new__(Mapflow)
    plugin.account_service = service
    plugin.app_context = SimpleNamespace(settings=MagicMock(), logged_in=True)
    plugin.processing_service = MagicMock()
    plugin.http = MagicMock()
    plugin.dlg = MagicMock()
    plugin.dlg_login = MagicMock()

    plugin.logout()

    assert not service.startup_timer.isActive()
    assert not service.refresh_timer.isActive()
