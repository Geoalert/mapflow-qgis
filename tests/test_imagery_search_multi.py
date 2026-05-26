"""Tests for multi-image Imagery Search selection handling.

Spec reference: spec/002_B_processing_api.md (ImagerySearchSchema.imageIds: List[str])
and spec/002_D_search_api.md (orbview_* family is dispatched by the backend
via OrbviewService.isValidRequest -> startsWith("orbview")).

Covers three bugs from plan_fix_search_bug.md:
1. get_search_images_ids returns ALL selected rows' image IDs (not just row 0).
2. orbview_* providers (e.g. orbview_msi + orbview_pan) may be combined when
   product type is Image.
3. duplicate_imagery_search recreates one row per imageId.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


# ---------- helpers ----------

def _make_cell(text):
    cell = MagicMock()
    cell.text.return_value = text
    return cell


def _make_table(rows):
    """rows: list[list[str]] — table[r][c] = cell text. Returns a mock metadataTable."""
    table = MagicMock()

    def item(row, col):
        try:
            return _make_cell(rows[row][col])
        except IndexError:
            return None

    table.item.side_effect = item

    def selected_items():
        selected = []
        for r, row_cells in enumerate(rows):
            for c, _ in enumerate(row_cells):
                cell = MagicMock()
                cell.row.return_value = r
                cell.column.return_value = c
                selected.append(cell)
        return selected

    table.selectedItems.side_effect = selected_items
    return table


def _make_service(rows, provider_names, product_types, zooms=None):
    """Build the minimum ProviderService surface needed by the methods under test."""
    from mapflow.functional.service.provider_service import ProviderService
    from mapflow.config import Config

    config = Config()

    # Reset singleton state so each test starts fresh.
    ProviderService._instance = None
    ProviderService._initialized = False

    dlg = MagicMock()
    dlg.metadataTable = _make_table(rows)

    app_context = SimpleNamespace()
    footprints = {}
    zooms = zooms or [None] * len(provider_names)
    for idx, (pname, ptype, zoom) in enumerate(zip(provider_names, product_types, zooms)):
        feature = MagicMock()

        def attribute(name, _p=pname, _t=ptype, _z=zoom):
            return {"providerName": _p, "productType": _t, "zoom": _z}[name]

        feature.attribute.side_effect = attribute
        footprints[idx] = feature
    app_context.search_footprints = footprints

    service = ProviderService.__new__(ProviderService)
    service.dlg = dlg
    service.app_context = app_context
    service.config = config
    service.imagery_search_provider_instance = SimpleNamespace(requires_id=None, image_ids=None)
    service.my_imagery_provider_instance = SimpleNamespace(mosaic_id=None, image_ids=None)
    # tr() is a Qt method; in unit tests just echo the input.
    service.tr = lambda msg: msg
    return service


# ---------- orbview-family detection ----------

class TestOrbviewFamily:
    def test_all_orbview_variants(self):
        from mapflow.functional.service.provider_service import ProviderService
        assert ProviderService._is_orbview_family(["orbview_msi", "orbview_pan"]) is True

    def test_case_insensitive(self):
        from mapflow.functional.service.provider_service import ProviderService
        assert ProviderService._is_orbview_family(["ORBVIEW_MSI", "OrbView_pan"]) is True

    def test_mixed_with_non_orbview(self):
        from mapflow.functional.service.provider_service import ProviderService
        assert ProviderService._is_orbview_family(["orbview_msi", "maxar"]) is False

    def test_empty(self):
        from mapflow.functional.service.provider_service import ProviderService
        assert ProviderService._is_orbview_family([]) is False

    def test_none_value(self):
        from mapflow.functional.service.provider_service import ProviderService
        assert ProviderService._is_orbview_family([None, "orbview_msi"]) is False


# ---------- Bug 1: all selected IDs returned ----------

class TestSearchImagesIdsCollectsAllRows:
    def test_same_provider_all_ids(self):
        from mapflow.config import Config
        config = Config()
        # Build rows wide enough that MAXAR_ID_COLUMN_INDEX is a valid column.
        width = config.MAXAR_ID_COLUMN_INDEX + 1
        rows = []
        for image_id in ("img-1", "img-2", "img-3"):
            row = [""] * width
            row[config.MAXAR_ID_COLUMN_INDEX] = image_id
            rows.append(row)
        service = _make_service(rows,
                                provider_names=["orbview_msi"] * 3,
                                product_types=["Image"] * 3)
        image_ids, err = service.get_search_images_ids(["orbview_msi"] * 3, ["Image"] * 3)
        assert image_ids == ["img-1", "img-2", "img-3"]
        assert err == ""
        assert service.imagery_search_provider_instance.image_ids == ["img-1", "img-2", "img-3"]
        assert service.imagery_search_provider_instance.requires_id is True

    def test_single_row_unchanged(self):
        from mapflow.config import Config
        config = Config()
        width = config.MAXAR_ID_COLUMN_INDEX + 1
        row = [""] * width
        row[config.MAXAR_ID_COLUMN_INDEX] = "only-one"
        service = _make_service([row],
                                provider_names=["maxar"],
                                product_types=["Image"])
        image_ids, err = service.get_search_images_ids(["maxar"], ["Image"])
        assert image_ids == ["only-one"]
        assert err == ""

    def test_empty_selection(self):
        service = _make_service([],
                                provider_names=[],
                                product_types=[])
        image_ids, err = service.get_search_images_ids([], [])
        assert image_ids is None
        assert err == ""
        assert service.imagery_search_provider_instance.requires_id is False


# ---------- Bug 2: orbview-family multi-provider mix ----------

class TestOrbviewMixIsAllowed:
    def _rows(self, ids):
        from mapflow.config import Config
        config = Config()
        width = config.MAXAR_ID_COLUMN_INDEX + 1
        rows = []
        for image_id in ids:
            row = [""] * width
            row[config.MAXAR_ID_COLUMN_INDEX] = image_id
            rows.append(row)
        return rows

    def test_orbview_msi_plus_pan_allowed(self):
        rows = self._rows(["a", "b"])
        provider_names = ["orbview_msi", "orbview_pan"]
        product_types = ["Image", "Image"]
        service = _make_service(rows, provider_names, product_types)
        image_ids, err = service.get_search_images_ids(provider_names, product_types)
        assert err == ""
        assert image_ids == ["a", "b"]

    def test_orbview_mosaic_mix_blocked(self):
        rows = self._rows(["a", "b"])
        provider_names = ["orbview_msi", "orbview_pan"]
        product_types = ["Image", "Mosaic"]  # mismatched product types
        service = _make_service(rows, provider_names, product_types)
        _, err = service.get_search_images_ids(provider_names, product_types)
        # different provider names + non-mosaic-only + not pure-Image-orbview → blocked
        assert err != ""

    def test_orbview_plus_non_orbview_blocked(self):
        rows = self._rows(["a", "b"])
        provider_names = ["orbview_msi", "maxar"]
        product_types = ["Image", "Image"]
        service = _make_service(rows, provider_names, product_types)
        _, err = service.get_search_images_ids(provider_names, product_types)
        assert err != ""

    def test_pure_mosaic_mix_still_allowed(self):
        rows = self._rows(["a", "b"])
        provider_names = ["foo", "bar"]
        product_types = ["Mosaic", "Mosaic"]
        service = _make_service(rows, provider_names, product_types)
        _, err = service.get_search_images_ids(provider_names, product_types)
        assert err == ""


# ---------- Bug 2: validate_provider_params mirrors the rule ----------

class TestValidateProviderParamsOrbviewMix:
    def _make_service_with_provider(self, rows, provider_names, product_types, zooms=None):
        service = _make_service(rows, provider_names, product_types, zooms=zooms)
        # Pre-populate image_ids so the "must have image ID" branch doesn't fire.
        service.imagery_search_provider_instance.image_ids = [r[-1] for r in rows] or []
        return service

    def test_orbview_image_mix_no_error(self):
        from mapflow.config import Config
        from mapflow.entity.provider import ImagerySearchProvider
        config = Config()
        width = config.MAXAR_ID_COLUMN_INDEX + 1
        rows = []
        for image_id in ("a", "b"):
            row = [""] * width
            row[config.MAXAR_ID_COLUMN_INDEX] = image_id
            rows.append(row)
        provider_names = ["orbview_msi", "orbview_pan"]
        product_types = ["Image", "Image"]
        service = self._make_service_with_provider(rows, provider_names, product_types)
        provider = ImagerySearchProvider(proxy="http://example")
        # Service's imagery_search_provider_instance must already have ids set.
        service.imagery_search_provider_instance.image_ids = ["a", "b"]
        assert service.validate_provider_params(provider) is None

    def test_non_orbview_mixed_providers_error(self):
        from mapflow.config import Config
        from mapflow.entity.provider import ImagerySearchProvider
        config = Config()
        width = config.MAXAR_ID_COLUMN_INDEX + 1
        rows = []
        for image_id in ("a", "b"):
            row = [""] * width
            row[config.MAXAR_ID_COLUMN_INDEX] = image_id
            rows.append(row)
        provider_names = ["foo", "bar"]
        product_types = ["Image", "Image"]
        service = self._make_service_with_provider(rows, provider_names, product_types)
        provider = ImagerySearchProvider(proxy="http://example")
        service.imagery_search_provider_instance.image_ids = ["a", "b"]
        # Different non-orbview providers with Image type → error.
        err = service.validate_provider_params(provider)
        assert err is not None and err != ""


# ---------- Bug 3: duplicate_imagery_search expands all rows ----------

class TestDuplicateImagerySearchMultiRow:
    def test_n_rows_one_per_image_id(self):
        from mapflow.config import Config
        from mapflow.schema import ImagerySearchParams, ImagerySearchSchema
        from mapflow.functional.service.provider_service import ProviderService
        from PyQt5.QtCore import QObject

        ProviderService._instance = None
        ProviderService._initialized = False

        config = Config()
        service = ProviderService.__new__(ProviderService)
        service.config = config
        service.config_search_columns = {
            k: v for k, v in __import__("mapflow.config", fromlist=["ConfigColumns"]).ConfigColumns().METADATA_TABLE_ATTRIBUTES.items()
        }
        service.tr = lambda msg: msg
        service.app_context = SimpleNamespace(metadata_layer=None,
                                              search_footprints={},
                                              meta_layer_table_connection=None)
        service.selection_sync_callback = lambda *_a, **_kw: None

        dlg = MagicMock()
        dlg.metadataTable = MagicMock()
        row_count_holder = {"n": 0}
        dlg.metadataTable.setRowCount.side_effect = lambda n: row_count_holder.__setitem__("n", n)
        dlg.metadataTable.rowCount.side_effect = lambda: row_count_holder["n"]
        set_items = []
        dlg.metadataTable.setItem.side_effect = lambda r, c, item: set_items.append((r, c, item))
        # polygonCombo returns a layer with no features so getFeatures() returns []
        # → duplicate_imagery_search will still create rows from image_ids but no features
        # because aoi_features is empty. To exercise the per-row layer population we
        # provide a stub layer with a single getFeatures() entry.
        aoi_feature = MagicMock()
        aoi_feature.geometry.return_value = MagicMock()
        layer = MagicMock()
        layer.getFeatures.return_value = [aoi_feature]
        dlg.polygonCombo.currentLayer.return_value = layer
        dlg.tabWidget.findChild.return_value = MagicMock()
        dlg.sourceCombo = MagicMock()
        dlg.metadataTableFilled = MagicMock()
        service.dlg = dlg
        # imagery_search_provider_index needs providers; stub via attribute.
        type(service).imagery_search_provider_index = property(lambda self: 0)
        service.providers = []

        image_ids = ["img-1", "img-2", "img-3"]
        params = ImagerySearchParams(
            ImagerySearchSchema(dataProvider="orbview_msi",
                                imageIds=image_ids,
                                zoom=18)
        )
        service.duplicate_imagery_search(params)

        assert row_count_holder["n"] == 3, "Should create one table row per imageId"

        # Every imageId should have a setItem at MAXAR_ID_COLUMN_INDEX
        id_col = config.MAXAR_ID_COLUMN_INDEX
        id_items = [(r, item) for (r, c, item) in set_items if c == id_col]
        # We have 3 rows × set 4 columns = 12 setItem calls; 3 of them are at id_col.
        assert len(id_items) == 3
        # The item.setData receiver was called with each image_id once.
        seen_ids = set()
        for _r, item in id_items:
            for call in item.setData.call_args_list:
                args = call.args
                if len(args) >= 2:
                    seen_ids.add(args[1])
        assert seen_ids == set(image_ids)

        # And footprints dict should be keyed by local_index 0..2
        # (the metadata layer is real QGIS so we rely on attribute() returning the row index)
        # local_indices we set are 0..2.
        assert set(service.app_context.search_footprints.keys()) == {0, 1, 2}
