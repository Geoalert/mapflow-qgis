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


def test_the_processings_of_the_opened_project_are_listed(logged_in, network):
    open_first_project(logged_in, network)
    table = logged_in.dlg.processingsTable
    assert table.rowCount() > 0, "the processings table is empty after opening a project"


def test_opening_a_project_populates_the_model_list(logged_in, network):
    """Models arrive with the project, not with the account — see the startup journey."""
    open_first_project(logged_in, network)
    combo = logged_in.dlg.modelCombo
    names = [combo.itemText(i) for i in range(combo.count())]
    assert names, "no models after opening a project; nothing can be started"
    assert any("Buildings" in name for name in names), f"default model missing from {names}"


def test_opening_a_project_populates_the_imagery_sources(logged_in, network):
    open_first_project(logged_in, network)
    combo = logged_in.dlg.providerCombo
    names = [combo.itemText(i) for i in range(combo.count())]
    assert names, "no imagery sources after opening a project"


def test_a_failed_processing_is_shown_with_its_status(logged_in, network):
    """The failure path that matters most: the user has to be able to see it failed.

    Routed to the captured page that actually contains a FAILED row, rather than asserting
    against whichever project the fixture set happened to record first.
    """
    network.respond_with("projects/*/processings/v2/page", 200,
                         fixture("processings_page_failed"))
    open_first_project(logged_in, network)

    table = logged_in.dlg.processingsTable
    cells = [table.item(row, col).text()
             for row in range(table.rowCount())
             for col in range(table.columnCount())
             if table.item(row, col)]
    statuses = [s for s in cells if "fail" in s.lower()]
    assert statuses, (
        f"a FAILED processing must be visible as failed; table showed {cells}")


def test_every_request_in_this_journey_has_a_fixture(logged_in, network):
    open_first_project(logged_in, network)
    settle(network, rounds=3)
    assert network.unmatched == [], f"no fixture for: {sorted(set(network.unmatched))}"
