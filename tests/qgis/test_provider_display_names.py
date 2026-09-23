"""QGIS-tier tests: My Imagery search results show a readable provider name.

The catalog returns the user's own imagery under the internal names ``my_imagery_images`` and
``my_imagery_mosaics``. Those belong in requests and lookups, not in front of a user, so the
search-results table shows "My Image" / "My Collection" instead. The mapping is display-only:
the GeoJSON properties, the footprint attributes and everything matching on them are untouched.
"""
from unittest.mock import MagicMock

import pytest
from PyQt5.QtWidgets import QTableWidget

from mapflow.config import Config, ConfigColumns, provider_display_name
from mapflow.dialogs.main_dialog import MainDialog

_ATTRS = list(ConfigColumns().METADATA_TABLE_ATTRIBUTES.values())
_PROVIDER_COLUMN = _ATTRS.index('providerName')
_ID_COLUMN = _ATTRS.index('id')


def _dialog():
    """A MainDialog stub with a real table: fill_metadata_table only touches these three."""
    dialog = MainDialog.__new__(MainDialog)
    dialog.metadataTable = QTableWidget(0, len(_ATTRS))
    dialog.add_preview_cell = MagicMock()
    dialog.metadataTableFilled = MagicMock()
    return dialog


def _metadata(*provider_names):
    return {"features": [{"id": f"image-{i}",
                          "properties": {"providerName": name, "id": f"image-{i}"}}
                         for i, name in enumerate(provider_names)]}


@pytest.mark.parametrize("raw, shown", [("my_imagery_images", "My Image"),
                                        ("my_imagery_mosaics", "My Collection")])
def test_my_imagery_provider_names_are_shown_readably(raw, shown):
    dialog = _dialog()

    dialog.fill_metadata_table(_metadata(raw))

    assert dialog.metadataTable.item(0, _PROVIDER_COLUMN).text() == shown


def test_other_providers_are_shown_as_they_come():
    dialog = _dialog()

    dialog.fill_metadata_table(_metadata("Maxar", "Airbus"))

    assert [dialog.metadataTable.item(row, _PROVIDER_COLUMN).text() for row in range(2)] \
        == ["Maxar", "Airbus"]


def test_a_missing_provider_name_stays_empty():
    dialog = _dialog()

    dialog.fill_metadata_table(_metadata(None))

    assert dialog.metadataTable.item(0, _PROVIDER_COLUMN).text() == ""


def test_only_the_provider_column_is_remapped():
    """A guard against remapping by value instead of by column: an image id that happens to
    equal a provider name must be shown untouched."""
    dialog = _dialog()

    dialog.fill_metadata_table({"features": [{"properties": {"providerName": "my_imagery_images",
                                                             "id": "my_imagery_images"}}]})

    assert dialog.metadataTable.item(0, _PROVIDER_COLUMN).text() == "My Image"
    assert dialog.metadataTable.item(0, _ID_COLUMN).text() == "my_imagery_images"


def test_display_name_helper_passes_unknown_values_through():
    assert provider_display_name("my_imagery_images") == "My Image"
    assert provider_display_name("my_imagery_mosaics") == "My Collection"
    assert provider_display_name("Maxar") == "Maxar"
    assert provider_display_name(None) is None


def test_provider_column_index_matches_the_config():
    """The remap is keyed on the attribute name, but the duplicate path keys on this index."""
    assert Config.NAME_COLUMN_INDEX == _PROVIDER_COLUMN
