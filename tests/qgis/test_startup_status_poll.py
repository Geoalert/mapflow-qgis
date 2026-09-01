"""The startup /user/status retry loop.

The loop exists because the plugin cannot configure itself until that response arrives, so
it re-asks every 500 ms. What it must never do is re-ask forever: each tick issues a
request, and nothing else in the plugin bounds it. Two ways it used to run away —

* the response arrived but `set_processing_limit` raised part-way through, so the stop that
  sat at the end of that callback never ran (the error guard swallows the exception, and
  everything after the raise point is skipped);
* the response never arrived at all, because the error branch had no handler.

Both left the plugin polling /user/status and /rasters/memory twice a second for the rest
of the session, while looking healthy on screen.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from PyQt5.QtCore import QTimer
from PyQt5.QtNetwork import QNetworkReply

from mapflow.config import Config
from mapflow.mapflow import Mapflow


@pytest.fixture
def plugin():
    instance = Mapflow.__new__(Mapflow)
    instance.tr = lambda text: text
    instance.config = Config
    instance.server = "https://example.invalid/api"
    instance.http = MagicMock()
    instance.alert = MagicMock()
    instance.data_catalog_service = MagicMock()
    instance.app_startup_user_update_timer = QTimer()
    instance.app_startup_user_update_timer.setInterval(Config.STARTUP_STATUS_RETRY_INTERVAL)
    instance._startup_status_attempts = 0
    instance._startup_status_pending = False
    instance._startup_status_given_up = False
    instance.app_startup_user_update_timer.start()
    return instance


def _failed_response():
    response = MagicMock()
    response.error.return_value = QNetworkReply.HostNotFoundError
    return response


def test_a_tick_is_skipped_while_a_request_is_in_flight(plugin):
    """Ticks are not synchronised with responses, so without this a slow server would
    accumulate one outstanding request per 500 ms."""
    plugin.first_status_request()
    plugin.first_status_request()
    plugin.first_status_request()

    assert plugin.http.get.call_count == 1


def test_the_next_tick_retries_once_the_previous_request_failed(plugin):
    plugin.first_status_request()
    plugin.first_status_error_handler(_failed_response())
    plugin.first_status_request()

    assert plugin.http.get.call_count == 2
    assert plugin.app_startup_user_update_timer.isActive(), "a single failure is not fatal"


def test_polling_stops_and_the_user_is_told_after_the_attempt_budget(plugin):
    for _ in range(Config.STARTUP_STATUS_MAX_ATTEMPTS):
        plugin.first_status_request()
        plugin.first_status_error_handler(_failed_response())

    assert plugin.http.get.call_count == Config.STARTUP_STATUS_MAX_ATTEMPTS
    assert plugin.app_startup_user_update_timer.isActive(), "the budget is not spent yet"

    plugin.first_status_request()

    assert not plugin.app_startup_user_update_timer.isActive()
    assert plugin.http.get.call_count == Config.STARTUP_STATUS_MAX_ATTEMPTS, "no further requests"
    plugin.alert.assert_called_once()


def test_no_further_requests_after_the_budget_is_spent(plugin):
    for _ in range(Config.STARTUP_STATUS_MAX_ATTEMPTS + 5):
        plugin.first_status_request()
        plugin.first_status_error_handler(_failed_response())

    assert plugin.http.get.call_count == Config.STARTUP_STATUS_MAX_ATTEMPTS
    assert plugin.alert.call_count == 1, "give up once, not once per tick"


def test_a_raising_configuration_still_stops_the_poll(plugin):
    """The regression: the stop must not depend on the configuration succeeding."""
    plugin.set_processing_limit = MagicMock(side_effect=TimeoutError("injected"))

    with pytest.raises(TimeoutError):
        plugin.first_status_callback(MagicMock())

    assert not plugin.app_startup_user_update_timer.isActive()


def test_the_storage_quota_is_requested_once_on_success_not_per_retry(plugin):
    """/rasters/memory used to be issued from every tick, doubling the runaway traffic."""
    plugin.set_processing_limit = MagicMock()

    plugin.first_status_request()
    plugin.first_status_error_handler(_failed_response())
    plugin.first_status_request()
    plugin.data_catalog_service.get_user_limit.assert_not_called()

    plugin.first_status_callback(MagicMock())
    plugin.data_catalog_service.get_user_limit.assert_called_once()


def test_a_successful_startup_stops_the_poll(plugin):
    plugin.set_processing_limit = MagicMock()

    plugin.first_status_callback(MagicMock())

    assert not plugin.app_startup_user_update_timer.isActive()
    plugin.set_processing_limit.assert_called_once()
    assert plugin.set_processing_limit.call_args.kwargs == {"app_startup_request": True}


def test_logout_stops_a_startup_poll_that_never_finished(plugin):
    """Otherwise a failed startup keeps polling the account endpoint after logging out."""
    plugin.app_context = SimpleNamespace(settings=MagicMock(), logged_in=True)
    plugin.processing_service = MagicMock()
    plugin.template_service = MagicMock()
    plugin.template_service.in_template_mode = False
    plugin.user_status_update_timer = MagicMock()
    plugin.dlg = MagicMock()
    plugin.dlg_login = MagicMock()

    plugin.logout()

    assert not plugin.app_startup_user_update_timer.isActive()
