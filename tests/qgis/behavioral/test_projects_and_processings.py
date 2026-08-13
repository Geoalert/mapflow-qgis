"""Browsing projects and opening one.

The plugin's spine: nothing else is reachable until the user has picked a project. Opening
one is also what populates the model list and the imagery sources, since those come from the
project's workflowDefs rather than from the account.

Driven by double-clicking a row, which is how a user opens a project.
"""
from conftest import open_first_project, settle
from fake_network import fixture


def test_the_projects_the_account_has_are_listed(logged_in):
    table = logged_in.dlg.projectsTable
    expected = [p["name"] for p in fixture("projects_page")["results"]]
    shown = [table.item(row, 1).text() for row in range(table.rowCount())
             if table.item(row, 1)]
    assert shown == expected, f"projects table shows {shown}, response carried {expected}"


def test_opening_a_project_asks_for_its_processings(logged_in, network):
    open_first_project(logged_in, network)
    assert network.sent_to("processings/v2/page"), (
        f"opening a project must load its processings; sent: {network.paths()}")


def _table_text(table):
    return [table.item(row, col).text()
            for row in range(table.rowCount())
            for col in range(table.columnCount())
            if table.item(row, col)]


def test_the_processings_of_the_opened_project_are_listed(logged_in, network):
    """Asserts the rows carry the response's processings, not merely that rows exist.

    `rowCount() > 0` is not enough: the table is given a single "Loading..." placeholder row
    before the request goes out, so a callback that never renders anything still leaves a
    non-empty table. This assertion has to name what the response said.
    """
    open_first_project(logged_in, network)
    shown = _table_text(logged_in.dlg.processingsTable)

    expected = [p["name"] for p in fixture("processings_page")["results"]]
    missing = [name for name in expected if name not in shown]
    assert not missing, f"processings {missing} never reached the table; it shows {shown}"
    assert not any("Loading" in cell for cell in shown), (
        "the loading placeholder is still there — the results never rendered")


def test_opening_a_project_populates_the_model_list(logged_in, network):
    """Models arrive with the project, not with the account — see the startup journey."""
    open_first_project(logged_in, network)
    combo = logged_in.dlg.modelCombo
    shown = [combo.itemText(i) for i in range(combo.count())]

    expected = [wd["name"] for wd in fixture("project_detail")["workflowDefs"]]
    assert sorted(shown) == sorted(expected), (
        f"model list is {shown}, the project's workflowDefs are {expected}")


def test_opening_a_project_populates_the_imagery_sources(logged_in, network):
    """The named providers must arrive, not just some entries.

    Checked by display name from the account response, because that is what the user picks
    from — an entry count would pass on a list of the two built-in sources alone.
    """
    open_first_project(logged_in, network)
    combo = logged_in.dlg.providerCombo
    shown = [combo.itemText(i) for i in range(combo.count())]

    expected = [p["displayName"] for p in fixture("user_status")["dataProviders"]]
    missing = [name for name in expected if name not in shown]
    assert not missing, f"imagery sources {missing} missing; combo shows {shown}"


def test_a_failed_processing_is_shown_with_its_status(logged_in, network):
    """The failure path that matters most: the user has to be able to see it failed.

    Routed to the captured page that actually contains a FAILED row, rather than asserting
    against whichever project the fixture set happened to record first.
    """
    page = fixture("processings_page_failed")
    network.respond_with("projects/*/processings/v2/page", 200, page)
    open_first_project(logged_in, network)

    shown = _table_text(logged_in.dlg.processingsTable)
    failed_names = [p["name"] for p in page["results"] if p["status"] == "FAILED"]
    assert failed_names, "the fixture no longer contains a FAILED processing to check"
    missing = [name for name in failed_names if name not in shown]
    assert not missing, f"failed processings {missing} are not listed; table shows {shown}"
    assert any("fail" in cell.lower() for cell in shown), (
        f"the failure is not visible as a status anywhere in the row; table shows {shown}")


def test_every_request_in_this_journey_has_a_fixture(logged_in, network):
    open_first_project(logged_in, network)
    settle(network, rounds=3)
    assert network.unmatched == [], f"no fixture for: {sorted(set(network.unmatched))}"
