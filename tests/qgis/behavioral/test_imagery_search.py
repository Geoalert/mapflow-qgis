"""Searching the imagery catalogue over an AOI.

How a user finds an image to process: set an area, press search, and get footprints on the map
alongside a table of what is available. The imagery-search source is the plugin's default
selection, so this journey needs no source switching — only an AOI.
"""
from qgis.core import QgsProject

from conftest import add_aoi_layer, open_first_project, settle
from fake_network import fixture


def _search(plugin, network):
    open_first_project(plugin, network)
    add_aoi_layer(plugin, network)
    plugin.dlg.getMetadata.click()
    settle(network)


def test_searching_asks_the_catalogue(logged_in, network):
    _search(logged_in, network)
    assert network.sent_to("catalog/meta"), (
        f"pressing search must query the catalogue; sent: {network.paths()}")


def test_the_search_describes_the_area_the_user_drew(logged_in, network):
    """The AOI is the whole point of the query, so it has to be in the body."""
    _search(logged_in, network)
    body = network.sent_to("catalog/meta")[-1].json()

    assert body, "the search request carried no body"
    aoi = body.get("aoi") or {}
    assert aoi.get("coordinates"), f"the AOI never reached the search request: {body}"


def test_the_results_are_listed(logged_in, network):
    """Every image the server returned must be shown — a count would miss a dropped row."""
    _search(logged_in, network)
    table = logged_in.dlg.metadataTable
    shown = [table.item(row, col).text()
             for row in range(table.rowCount())
             for col in range(table.columnCount())
             if table.item(row, col)]

    expected = [image["id"] for image in fixture("search_meta")["images"]]
    missing = [image_id for image_id in expected if image_id not in shown]
    assert not missing, f"images {missing} are missing from the results table"


def test_the_footprints_appear_on_the_map(logged_in, network):
    """Results are only useful if the user can see where they are."""
    _search(logged_in, network)
    names = [layer.name() for layer in QgsProject.instance().mapLayers().values()]
    assert any("metadata" in name for name in names), (
        f"no footprints layer was added to the map; layers are {names}")


def test_a_search_that_matches_nothing_says_so(logged_in, network, alerts):
    """Silence would read as a broken plugin rather than an empty result."""
    network.respond_with("catalog/meta", 200, {"images": [], "total": 0, "limit": 20,
                                               "offset": 0})
    _search(logged_in, network)

    assert any("no images" in message.lower() for message in alerts), (
        f"the user was not told the search matched nothing; alerts were {alerts}")


def test_searching_without_an_area_asks_for_one(logged_in, network, alerts):
    """The AOI is required, and the plugin must say which thing is missing."""
    open_first_project(logged_in, network)
    logged_in.dlg.getMetadata.click()
    settle(network)

    assert not network.sent_to("catalog/meta"), (
        "a search was sent although no area of interest was chosen")
    assert any("area of interest" in message.lower() for message in alerts), (
        f"the user was not told an AOI is needed; alerts were {alerts}")


def test_every_request_in_this_journey_has_a_fixture(logged_in, network):
    _search(logged_in, network)
    assert network.unmatched == [], f"no fixture for: {sorted(set(network.unmatched))}"
