"""Browsing My Imagery: the user's own uploaded rasters.

Mosaics are fetched as part of logging in, so the list is already there; opening one asks for
its images. The storage figures matter as much as the lists — an upload is refused when there
is no room, and the quota is the only place the user can see that coming.
"""
from conftest import settle
from fake_network import fixture


def _table_text(table):
    return [table.item(row, col).text()
            for row in range(table.rowCount())
            for col in range(table.columnCount())
            if table.item(row, col)]


def _open_first_mosaic(plugin, network):
    """Select a mosaic and open it, the way a double-click does.

    Selection first: the images request is built from the *selected* mosaic, so activating a
    row without selecting it asks for nothing.
    """
    table = plugin.dlg.mosaicTable
    assert table.rowCount(), "no mosaics listed; the journey cannot start"
    table.setCurrentCell(0, 1)
    table.cellDoubleClicked.emit(0, 1)
    settle(network)


def test_the_mosaics_are_listed(logged_in):
    shown = _table_text(logged_in.dlg.mosaicTable)
    expected = [mosaic["name"] for mosaic in fixture("mosaics")]
    missing = [name for name in expected if name not in shown]
    assert not missing, f"mosaics {missing} are missing from the table; it shows {shown}"


def test_the_storage_quota_is_shown(logged_in):
    """Both figures, computed independently of the formatter under test.

    Arithmetic here rather than a call to the plugin's own size helper: reusing it would make
    the assertion agree with the code by construction, including when both are wrong.
    """
    memory = fixture("rasters_memory")
    used = round(memory["memoryUsed"] / 1024 ** 3, 1)
    free = round(memory["memoryFree"] / 1024 ** 3, 1)

    shown = logged_in.dlg.dataLimit.text()
    assert str(used) in shown, f"used storage {used} GB not in {shown!r}"
    assert str(free) in shown, f"free storage {free} GB not in {shown!r}"


def test_opening_a_mosaic_asks_for_its_images(logged_in, network):
    _open_first_mosaic(logged_in, network)
    assert network.sent_to("/image"), (
        f"opening a mosaic must load its images; sent: {network.paths()}")


def test_the_images_of_the_opened_mosaic_are_listed(logged_in, network):
    _open_first_mosaic(logged_in, network)
    shown = _table_text(logged_in.dlg.imageTable)

    expected = [image["filename"] for image in fixture("mosaic_images")]
    missing = [name for name in expected if name not in shown]
    assert not missing, f"images {missing} are missing from the table; it shows {shown}"


def test_every_request_in_this_journey_has_a_fixture(logged_in, network):
    _open_first_mosaic(logged_in, network)
    assert network.unmatched == [], f"no fixture for: {sorted(set(network.unmatched))}"
