"""What a fresh install shows after logging in.

Fresh means no saved project, which is the state a first-time user is in and the state the
test profile is in. The plugin issues one /user/status on login and a second from a 500 ms
timer; only the second carries the flag that configures the UI, so this journey needs real
time to pass rather than replies to be delivered.

The model and provider combos are deliberately not asserted here. Both are populated from a
*project's* workflowDefs, so on a fresh profile they are legitimately empty until a project
is opened — that belongs to the projects journey.
"""
from conftest import settle


def test_the_balance_is_shown(logged_in):
    assert logged_in.dlg.balanceLabel.text() != "", (
        "the remaining balance is how the user knows whether they can run anything")


def test_the_main_window_replaces_the_login_dialog(logged_in):
    assert not logged_in.dlg_login.isVisible()


def test_startup_configuration_runs_to_completion(logged_in, network):
    """The whole point of the second /user/status.

    Asserted through the projects table because that is the last thing the configuration
    does, so it is only populated if nothing threw on the way. An exception midway is
    absorbed by the error guard and leaves the plugin looking healthy but half-set-up —
    which is exactly the failure this journey exists to notice.
    """
    assert network.sent_to("projects/page"), (
        f"the project list is fetched at the end of startup configuration; "
        f"sent: {network.paths()}")


def test_the_startup_poll_stops_once_it_has_answered(logged_in, network):
    """It runs at 500 ms. If it does not stop, the plugin hammers two endpoints forever."""
    before = len(network.sent_to("user/status"))
    settle(network, rounds=4)
    after = len(network.sent_to("user/status"))
    assert after == before, (
        f"/user/status kept being requested after configuration completed: {before} -> {after}")


def test_the_storage_quota_is_not_requested_per_poll_tick(logged_in, network):
    """It used to be issued from every retry tick of the startup poll.

    Asserted as "does not keep growing" rather than a fixed count: it is legitimately
    requested more than once during startup — once with the account status and again when the
    mosaic list updates — and pinning the exact number would make this test fail on a
    perfectly good change to either path.
    """
    before = len(network.sent_to("rasters/memory"))
    settle(network, rounds=6)
    after = len(network.sent_to("rasters/memory"))
    assert after == before, (
        f"/rasters/memory is still being requested after startup: {before} -> {after}")


def test_every_startup_request_has_a_captured_fixture(logged_in, network):
    assert network.unmatched == [], f"no fixture for: {sorted(set(network.unmatched))}"
