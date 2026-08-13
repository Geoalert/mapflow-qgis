"""Previewing a search result on the map.

How a user checks an image is the one they want before paying to process it. The preview is
fetched from the provider's own pre-signed URL, not from Mapflow, so this journey also pins
that the plugin does not send its credentials to a third-party host.

Deduplication is the behaviour worth guarding: a preview is a download, and both a rapid
second double-click and a re-preview of an image already on the map must not repeat it.
"""
import struct
import zlib
from urllib.parse import urlparse

from qgis.core import QgsProject

from conftest import add_aoi_layer, open_first_project, settle
from fake_network import fixture


def _png(width=16, height=16):
    """A real PNG, built rather than pasted as a blob.

    The preview path writes the response to disk, opens it with GDAL and georeferences it
    from the footprint, so the bytes have to be a genuine image. Generated because the size
    matters and a base64 constant hides it: a 1x1 raster is not something GDAL and QGIS will
    carry through georeferencing into a valid layer.
    """
    rows = b"".join(b"\x00" + b"\x80\x80\x80" * width for _ in range(height))

    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows))
            + chunk(b"IEND", b""))


PREVIEW_PNG = _png()

#: Images 0-2 in the capture carry a multi-part `previews` list, which takes a different
#: (VRT-building) path. Index 3 is a plain single preview, which is the common case.
SINGLE_PREVIEW_INDEX = 3


def _image():
    return fixture("search_meta")["images"][SINGLE_PREVIEW_INDEX]


def _searched(plugin, network):
    open_first_project(plugin, network)
    add_aoi_layer(plugin, network)
    plugin.dlg.getMetadata.click()
    settle(network)
    return plugin


def _double_click_result(plugin, image_id=None):
    """Find the row by image id and open it, the way a double-click does.

    By id rather than by position: the results table is re-rendered by the instant local
    filter, which orders unfit rows last, so a row index is not a stable handle on an image.

    `setCurrentCell` rather than `selectRow` because the plugin reads `selectedItems()` to
    learn which image was opened, and selectRow alone leaves that empty here.
    """
    table = plugin.dlg.metadataTable
    id_column = plugin.config.SEARCH_ID_COLUMN_INDEX
    target = image_id or _image()["id"]
    row = next((r for r in range(table.rowCount())
                if table.item(r, id_column) and table.item(r, id_column).text() == target), None)
    assert row is not None, (
        f"{target} is not in the results table; rows are "
        f"{[table.item(r, id_column).text() for r in range(table.rowCount()) if table.item(r, id_column)]}")
    table.setCurrentCell(row, id_column)
    table.cellDoubleClicked.emit(row, id_column)


def test_previewing_a_result_fetches_it_from_the_provider(logged_in, network, alerts):
    _searched(logged_in, network)
    before = len(network.requests)
    _double_click_result(logged_in)

    new = network.requests[before:]
    expected_path = urlparse(_image()["previewUrl"]).path
    assert any(request.path == expected_path for request in new), (
        f"no preview was fetched from {expected_path}; "
        f"sent {[r.path for r in new]}; alerts {alerts}")


def test_the_preview_request_does_not_carry_mapflow_credentials(logged_in, network):
    """The preview host is a third party and the URL is already self-authenticating."""
    _searched(logged_in, network)
    before = len(network.requests)
    _double_click_result(logged_in)

    expected_path = urlparse(_image()["previewUrl"]).path
    preview = [r for r in network.requests[before:] if r.path == expected_path]
    assert preview, "the preview request was never made"
    authorization = preview[0].headers.get("authorization", "")
    assert "Basic" not in authorization, (
        f"the account's credentials were sent to a third-party host: {authorization!r}")


def test_a_second_click_while_downloading_does_not_download_again(logged_in, network):
    """A preview is a download; double-clicking twice must not start two of them.

    The reply is deliberately left undelivered, which is exactly the window the guard exists
    for — the on-map check cannot help here because the layer only appears in the callback.
    """
    _searched(logged_in, network)
    before = len(network.requests)
    _double_click_result(logged_in)
    _double_click_result(logged_in)

    expected_path = urlparse(_image()["previewUrl"]).path
    downloads = [r for r in network.requests[before:] if r.path == expected_path]
    assert len(downloads) == 1, f"{len(downloads)} downloads started for one image"


def test_a_fetched_preview_appears_on_the_map(logged_in, network, alerts):
    image = _image()
    network.respond_with(urlparse(image["previewUrl"]).path, 200, PREVIEW_PNG)
    _searched(logged_in, network)
    _double_click_result(logged_in)
    settle(network)

    names = [layer.name() for layer in QgsProject.instance().mapLayers().values()]
    assert f"{image['id']} preview" in names, (
        f"no preview layer for the image; layers are {names}; alerts {alerts}")


def test_previewing_an_image_already_on_the_map_does_not_refetch(logged_in, network):
    """The user clicking twice on a result they already looked at costs nothing."""
    image = _image()
    network.respond_with(urlparse(image["previewUrl"]).path, 200, PREVIEW_PNG)
    _searched(logged_in, network)
    _double_click_result(logged_in)
    settle(network)

    expected_path = urlparse(image["previewUrl"]).path
    before = len([r for r in network.requests if r.path == expected_path])
    assert before == 1, "precondition failed: the first preview was not fetched exactly once"

    _double_click_result(logged_in)
    settle(network)
    after = len([r for r in network.requests if r.path == expected_path])
    assert after == before, f"the preview was downloaded again ({before} -> {after})"
