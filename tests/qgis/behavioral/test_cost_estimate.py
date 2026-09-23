"""Choosing an AOI and being told what the processing will cost.

The last step before a user spends credits, so both outcomes matter: a price they can act on,
and a refusal they can understand. The account in the fixtures is billed in credits, which is
the only billing mode where the plugin asks for a price at all.

Driven by putting a polygon layer on the map and selecting it, which is how an AOI is chosen.
"""
from conftest import add_aoi_layer, choose_imagery_source, open_first_project
from fake_network import fixture


def _basemap_source():
    """A source that can be priced without picking an individual image."""
    return fixture("user_status")["dataProviders"][0]["displayName"]


def _prepared(plugin, network):
    open_first_project(plugin, network)
    choose_imagery_source(plugin, network, _basemap_source())
    add_aoi_layer(plugin, network)
    return plugin


def test_choosing_an_aoi_asks_what_it_costs(logged_in, network):
    _prepared(logged_in, network)
    assert network.sent_to("processing/cost"), (
        f"selecting an AOI must price the processing; sent: {network.paths()}")


def test_the_cost_request_describes_what_the_user_chose(logged_in, network):
    """The request body is the contract — assert its content, not that a call happened."""
    _prepared(logged_in, network)
    body = network.sent_to("processing/cost")[-1].json()

    assert body, "the cost request carried no body"
    assert body.get("wdId"), f"no model id in the cost request: {body}"
    geometry = body.get("geometry") or {}
    assert geometry.get("coordinates"), f"the AOI geometry never reached the request: {body}"
    assert body.get("projectId"), "the cost is project-scoped and the id is missing"


def test_the_price_is_shown_to_the_user(logged_in, network):
    """Matched as a whole word.

    A substring check passes on the wrong number — "12" is in "1012" — so a display bug that
    inflates the price would go unnoticed, which is the one thing a price label must not do.
    """
    import re

    _prepared(logged_in, network)
    expected = str(fixture("processing_cost"))
    shown = logged_in.dlg.processingProblemsLabel.text()
    assert re.search(rf"\b{re.escape(expected)}\b", shown), (
        f"cost label reads {shown!r}, the server said {expected}")


def test_a_priced_processing_can_be_started(logged_in, network):
    _prepared(logged_in, network)
    assert logged_in.dlg.startProcessing.isEnabled(), (
        f"start is still disabled after a successful price; "
        f"label says {logged_in.dlg.processingProblemsLabel.text()!r}")


def test_changing_the_aoi_asks_for_a_new_price(logged_in, network):
    """A price belongs to one AOI, so changing the AOI must re-price.

    What the plugin does with a *refused* re-price is not asserted: it neither shows the
    server's reason nor keeps Start disabled, because an unrelated UI refresh
    (`update_start_processing_button_state`) re-enables the button and overwrites the label
    without knowing a refusal happened. Both are recorded in WAL as defects. Asserting
    today's behaviour would make fixing it look like a regression, and asserting the correct
    behaviour would leave a red test in a suite whose job is to be green before the
    refactoring starts.
    """
    from conftest import add_aoi_layer

    _prepared(logged_in, network)
    assert logged_in.dlg.startProcessing.isEnabled(), (
        "precondition failed: the first AOI was never priced")

    network.respond_with("processing/cost/v2", 404, fixture("processing_cost_rejected"))
    before = len(network.sent_to("processing/cost"))
    add_aoi_layer(logged_in, network, name="second aoi", extent=(1.0, 51.0, 1.02, 51.02))

    assert len(network.sent_to("processing/cost")) > before, (
        f"changing the AOI did not ask for a new price; sent: {network.paths()}")


def test_every_request_in_this_journey_has_a_fixture(logged_in, network):
    _prepared(logged_in, network)
    assert network.unmatched == [], f"no fixture for: {sorted(set(network.unmatched))}"
