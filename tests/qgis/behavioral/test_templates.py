"""Planned processings — listing templates and opening one.

A template is a standing search: it keeps looking for imagery and launches processings as
matches arrive. It shares the processings table with ordinary processings, and opening one
switches that table into an in-template view, so the two must stay tellable apart.

The largest domain in the plugin and the biggest Phase C extraction, which is why it gets a
journey before any of it moves.
"""
from conftest import open_first_project, settle
from fake_network import fixture


def _template_names():
    return [template["name"] for template in fixture("templates_by_project")]


def _templates_of_the_open_project():
    """The captured templates, re-pointed at the project this journey opens.

    The plugin discards templates whose `projectId` is not the open project — a real guard
    against a slow response from a project the user has since left. The captured templates
    come from a different project than the captured processings, because no project on the
    account that was captured had both, so without this the guard (correctly) hides them all.

    Only the id is rewritten; every other field is the payload the server actually sent.
    """
    project_id = fixture("projects_page")["results"][0]["id"]
    return [dict(template, projectId=project_id)
            for template in fixture("templates_by_project")]


def _open_project_showing_templates(plugin, network):
    network.respond_with("processings/template/project/*", 200,
                         _templates_of_the_open_project())
    open_first_project(plugin, network)


def _row_showing(table, text):
    for row in range(table.rowCount()):
        for column in range(table.columnCount()):
            item = table.item(row, column)
            if item and item.text() == text:
                return row
    return None


def _open_template(plugin, network, name):
    """Select a template row and press the 'enter template' arrow, as a user does."""
    table = plugin.dlg.processingsTable
    row = _row_showing(table, name)
    assert row is not None, f"template {name!r} is not listed; cannot open it"
    table.selectRow(row)
    plugin.dlg.switchProcessingsFakeButton.click()
    settle(network)
    return row


def test_the_projects_templates_are_listed_with_its_processings(logged_in, network):
    _open_project_showing_templates(logged_in, network)
    table = logged_in.dlg.processingsTable
    shown = [table.item(row, col).text()
             for row in range(table.rowCount())
             for col in range(table.columnCount())
             if table.item(row, col)]

    missing = [name for name in _template_names() if name not in shown]
    assert not missing, f"templates {missing} are not listed alongside the processings"


def test_opening_a_template_asks_for_its_details_and_processings(logged_in, network):
    _open_project_showing_templates(logged_in, network)
    before = len(network.sent_to("processings/template/"))
    _open_template(logged_in, network, _template_names()[0])

    after = network.sent_to("processings/template/")
    assert len(after) > before, (
        f"opening a template issued no request for it; sent: {network.paths()}")
    assert any(request.path.endswith("/processings") for request in after), (
        f"the template's own processings were never fetched; asked for: "
        f"{[r.path for r in after]}")


def test_the_open_template_is_named_in_the_breadcrumb(logged_in, network):
    """How the user knows which template they are inside, and that they are inside one."""
    _open_project_showing_templates(logged_in, network)
    name = _template_names()[0]
    _open_template(logged_in, network, name)

    tabs = logged_in.dlg.tabWidget
    labels = [tabs.tabText(index) for index in range(tabs.count())]
    tooltips = [tabs.tabToolTip(index) for index in range(tabs.count())]
    assert name in tooltips or any(name.startswith(label.rstrip("…")) and label != ""
                                   for label in labels), (
        f"the open template is not named anywhere in the tabs; labels={labels}")


def test_the_templates_own_processings_replace_the_project_list(logged_in, network):
    """Entering a template changes what the table is showing, not just what was fetched.

    Matched on ids, not names. One of the template's processings shares the template's own
    name, so a name check passes on the template row alone and stays green even when the
    processings are never fetched — an id can only have come from that response.
    """
    _open_project_showing_templates(logged_in, network)
    _open_template(logged_in, network, _template_names()[0])

    table = logged_in.dlg.processingsTable
    shown = [table.item(row, col).text()
             for row in range(table.rowCount())
             for col in range(table.columnCount())
             if table.item(row, col)]
    expected = [p["id"] for p in fixture("template_processings")]
    missing = [pid for pid in expected if pid not in shown]
    assert not missing, (
        f"the template's processings {missing} are not shown in its view; table has {shown}")


def test_leaving_a_template_returns_to_the_project(logged_in, network):
    _open_project_showing_templates(logged_in, network)
    _open_template(logged_in, network, _template_names()[0])

    logged_in.dlg.switchProjectsButton.click()
    settle(network)

    table = logged_in.dlg.processingsTable
    shown = [table.item(row, col).text()
             for row in range(table.rowCount())
             for col in range(table.columnCount())
             if table.item(row, col)]
    missing = [name for name in _template_names() if name not in shown]
    assert not missing, (
        f"going back did not restore the project's list; templates {missing} are gone")


def test_every_request_in_this_journey_has_a_fixture(logged_in, network):
    _open_project_showing_templates(logged_in, network)
    _open_template(logged_in, network, _template_names()[0])
    assert network.unmatched == [], f"no fixture for: {sorted(set(network.unmatched))}"
