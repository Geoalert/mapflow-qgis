"""Logging out.

Two things have to happen and both are easy to get wrong: the credentials must stop being
usable, and the polling must stop. A logout that leaves a timer running keeps talking to the
backend as the previous user — and the user has no way to tell.
"""
import copy

from conftest import open_first_project, settle
from fake_network import fixture


def _log_out(plugin, network):
    plugin.dlg.logoutButton.click()
    settle(network)


def test_logging_out_shows_the_login_dialog_again(logged_in, network):
    _log_out(logged_in, network)
    assert logged_in.dlg_login.isVisible(), "the user has no way back in"
    assert not logged_in.dlg.isVisible(), "the main window stayed open after logging out"


def test_the_token_is_cleared(logged_in, network):
    """Left behind, it silently logs the next user in as the previous one."""
    _log_out(logged_in, network)
    assert not logged_in.app_context.settings.value("token"), (
        "the stored token survived logging out")


def test_polling_stops(logged_in, network):
    """The processings poll runs on a timer, so it outlives the session unless stopped.

    Two conditions have to be arranged or the test proves nothing, and both were wrong first
    time round. The poll stops itself once every processing has reached a final state, and all
    the captured ones are finished — so one is forced to IN_PROGRESS to keep it alive. And the
    wait has to exceed a whole poll interval: the default settle is about a second against a
    six-second poll, so a shorter wait sees no tick whether or not logout stopped anything.
    """
    from mapflow.config import Config

    page = copy.deepcopy(fixture("processings_page"))
    page["results"][0]["status"] = "IN_PROGRESS"
    page["results"][0]["percentCompleted"] = 40
    network.respond_with("projects/*/processings/v2/page", 200, page)

    poll_ms = Config.PROCESSING_TABLE_REFRESH_INTERVAL * 1000
    open_first_project(logged_in, network)
    settle(network, rounds=int(poll_ms / 100) + 25, wait_ms=100, min_wait_ms=poll_ms + 1500)
    polled_while_open = len(network.sent_to("processings/v2/page"))
    assert polled_while_open > 1, (
        "precondition failed: the processings poll was not running before logout, so "
        "stopping it cannot be observed")

    _log_out(logged_in, network)

    before = len(network.requests)
    settle(network, rounds=int(poll_ms / 100) + 25, wait_ms=100, min_wait_ms=poll_ms + 1500)
    assert len(network.requests) == before, (
        f"still talking to the backend after logout: "
        f"{[r.path for r in network.requests[before:]]}")


def test_the_session_is_marked_ended(logged_in, network):
    _log_out(logged_in, network)
    assert not logged_in.app_context.logged_in


def test_every_request_in_this_journey_has_a_fixture(logged_in, network):
    _log_out(logged_in, network)
    assert network.unmatched == [], f"no fixture for: {sorted(set(network.unmatched))}"
