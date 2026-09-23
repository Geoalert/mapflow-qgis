"""Loading a finished processing's results onto the map.

The payoff of the whole workflow: the user gets their extracted features as QGIS layers. Two
layers arrive per processing — the imagery it ran on and the vector result — and each is
positioned from a tilejson the plugin fetches for its bounds.

Only the tiles path is covered here. The "save to disk" alternative writes files through
QFileDialog, which is a different journey.

Result *styling* is deliberately not asserted. `loadNamedStyle` fails silently on a missing
file, so it is worth covering — but every way of checking it from here reaches into the style
helpers, and a behavioral test that names internals stops surviving the refactoring, which is
the only reason this suite exists. Recorded as a gap in WAL instead.
"""
from urllib.parse import urlparse

from qgis.core import QgsProject

from conftest import open_first_project, settle
from fake_network import fixture

#: Bounds a tile server would report, in EPSG:4326 as the plugin expects.
TILE_JSON = {"bounds": [27.5, 53.8, 27.6, 53.9]}


def _finished_processing():
    """The first processing the account reports as finished."""
    for processing in fixture("processings_page")["results"]:
        if processing["status"] == "OK":
            return processing
    raise AssertionError("no finished processing in the fixture to load results from")


def _load_results(plugin, network, processing):
    """Select a processing and open it, which is how results are loaded."""
    # Routing matches on path segments, so hand it the path — a full URL would add the scheme
    # and host as segments and never line up with an incoming request.
    for url in (processing["rasterLayer"]["tileJsonUrl"],
                processing["vectorLayer"]["tileJsonUrl"]):
        network.respond_with(urlparse(url).path, 200, TILE_JSON)

    table = plugin.dlg.processingsTable
    row = next((r for r in range(table.rowCount())
                if any(table.item(r, c) and table.item(r, c).text() == processing["name"]
                       for c in range(table.columnCount()))), None)
    assert row is not None, f"{processing['name']} is not in the processings table"

    plugin.dlg.viewAsTiles.setChecked(True)
    table.setCurrentCell(row, 0)
    table.cellDoubleClicked.emit(row, 0)
    settle(network)


def _layer_names():
    return [layer.name() for layer in QgsProject.instance().mapLayers().values()]


def test_loading_results_adds_the_imagery_and_the_result(logged_in, network):
    processing = _finished_processing()
    open_first_project(logged_in, network)
    _load_results(logged_in, network, processing)

    names = _layer_names()
    assert processing["name"] in names, f"the result layer is missing; layers are {names}"
    assert f"{processing['name']} raster" in names, (
        f"the imagery the processing ran on is missing; layers are {names}")


def test_the_layers_point_at_the_tiles_the_server_named(logged_in, network):
    """Names alone would pass on empty layers pointing nowhere."""
    processing = _finished_processing()
    open_first_project(logged_in, network)
    _load_results(logged_in, network, processing)

    layers = {layer.name(): layer for layer in QgsProject.instance().mapLayers().values()}
    vector_source = layers[processing["name"]].source()
    raster_source = layers[f"{processing['name']} raster"].source()

    assert processing["vectorLayer"]["tileUrl"] in vector_source, (
        f"result layer points at {vector_source}")
    assert processing["rasterLayer"]["tileUrl"] in raster_source, (
        f"imagery layer points at {raster_source}")


def test_the_layers_are_positioned_from_the_tilejson(logged_in, network):
    """Without the bounds the layers land at the origin and the user sees nothing."""
    processing = _finished_processing()
    open_first_project(logged_in, network)
    _load_results(logged_in, network, processing)

    layers = {layer.name(): layer for layer in QgsProject.instance().mapLayers().values()}
    extent = layers[processing["name"]].extent()
    assert not extent.isEmpty(), "the result layer has no extent"
    # The tilejson is EPSG:4326 and the layers are Web Mercator, so compare after projecting
    # the requested bounds rather than against the raw degrees.
    assert extent.xMinimum() > 3_000_000, (
        f"extent {extent.toString()} does not match the bounds the tile server reported")


def test_results_of_an_unfinished_processing_are_refused(logged_in, network, alerts):
    """Loading a failed processing would add empty layers and look like a plugin bug."""
    page = fixture("processings_page_failed")
    network.respond_with("projects/*/processings/v2/page", 200, page)
    open_first_project(logged_in, network)

    failed = next(p for p in page["results"] if p["status"] == "FAILED")
    table = logged_in.dlg.processingsTable
    row = next((r for r in range(table.rowCount())
                if any(table.item(r, c) and table.item(r, c).text() == failed["name"]
                       for c in range(table.columnCount()))), None)
    assert row is not None, f"{failed['name']} is not in the processings table"

    before = set(_layer_names())
    table.setCurrentCell(row, 0)
    table.cellDoubleClicked.emit(row, 0)
    settle(network)

    assert set(_layer_names()) == before, "layers were added for a processing that failed"
    assert any("finished" in message.lower() for message in alerts), (
        f"the user was not told why nothing loaded; alerts were {alerts}")


def test_every_request_in_this_journey_has_a_fixture(logged_in, network):
    processing = _finished_processing()
    open_first_project(logged_in, network)
    _load_results(logged_in, network, processing)
    assert network.unmatched == [], f"no fixture for: {sorted(set(network.unmatched))}"
