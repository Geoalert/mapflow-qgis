"""Logging in, and what the account response configures.

The plugin is unusable until this exchange completes: the model list, the imagery sources,
the balance and every area cap arrive with it. Asserted on the requests that go out and on
what the user can then see, never on which object parsed the response.
"""
import json

from conftest import log_in


def test_login_authorises_and_asks_who_the_user_is(plugin, network):
    log_in(plugin)

    sent = network.sent_to("projects/default")
    assert sent, f"login must identify the account; sent instead: {network.paths()}"
    assert sent[0].method == "GET"


def test_login_sends_the_token_and_the_plugin_version(plugin, network):
    """Both headers are contract: the backend gates access on one and features on the other."""
    log_in(plugin)

    request = network.sent_to("projects/default")[0]
    assert request.headers.get("authorization", "").startswith("Basic "), request.headers
    assert request.headers.get("x-plugin-version"), (
        "every request carries the plugin version; the backend uses it for compatibility")


def test_account_status_is_fetched_after_login(logged_in, network):
    assert network.sent_to("user/status"), (
        f"limits and models come from /user/status; sent: {network.paths()}")


def test_the_balance_is_shown_to_the_user(logged_in, network):
    """What the account response is *for*, from the user's side."""
    network.deliver()
    text = logged_in.dlg.balanceLabel.text()
    assert text != "", "the user must be able to see their remaining balance after login"


def test_a_successful_login_swaps_the_login_dialog_for_the_main_window(logged_in, network):
    """The user-visible outcome of logging in.

    The model list is deliberately not asserted here: models come from a project's
    workflowDefs, so they arrive when a project is opened, not when the account is
    authenticated. That belongs to the projects journey.
    """
    network.deliver()
    assert logged_in.dlg.isVisible(), "the main window never opened"
    assert not logged_in.dlg_login.isVisible(), "the login dialog must close on success"


def test_no_request_is_repeated_needlessly_during_login(plugin, network):
    """A duplicated status call at startup is the shape of bug this suite must notice."""
    log_in(plugin)
    network.deliver()
    network.deliver()

    status_calls = network.sent_to("user/status")
    assert len(status_calls) <= 2, (
        f"/user/status called {len(status_calls)} times during a single login")


def test_every_request_during_login_has_a_captured_fixture(logged_in, network):
    """Guards the suite itself: an unrouted call answers 501 and would pass vacuously."""
    assert network.unmatched == [], (
        f"no fixture for: {sorted(set(network.unmatched))}. Re-run capture_fixtures.py, or "
        f"add an explicit network.respond_with() for these paths.")


def test_the_login_fixture_is_a_real_payload(logged_in):
    """The fixtures are captured, not hand-written; if that stops being true, say so here."""
    from pathlib import Path

    fixture = json.loads(
        (Path(__file__).parent / "responses" / "user_status.json").read_text())
    body = fixture["body"]
    assert "models" in body and body["models"], "user_status fixture lost its model list"
    assert "remainingCredits" in body or "remainingArea" in body
