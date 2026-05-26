"""Tests for multi-image Imagery Search selection handling.

Spec reference: spec/002_B_processing_api.md (ImagerySearchSchema.imageIds: List[str]).

Covers:
1. Bug #1 — get_search_images_ids returns every selected row's image ID, not just row 0.
2. Bug #3 — duplicate_imagery_search recreates one row per imageId so the
   selection-driven cost recalc fires on the full payload.
3. Bug #2 (lower-bound regression) — mixing different non-Mosaic providers
   still raises the selection error; backend currently does not accept mixed
   orbview_* providers in a single order.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock


def _make_table(rows):
    """rows: list[list[str]] — table[r][c] = cell text. Returns a mock metadataTable."""
    table = MagicMock()

    def item(row, col):
        try:
            text = rows[row][col]
        except IndexError:
            return None
        cell = MagicMock()
        cell.text.return_value = text
        return cell

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

    ProviderService._instance = None
    ProviderService._initialized = False

    dlg = MagicMock()
    dlg.metadataTable = _make_table(rows)

    footprints = {}
    zooms = zooms or [None] * len(provider_names)
    for idx, (pname, ptype, zoom) in enumerate(zip(provider_names, product_types, zooms)):
        feature = MagicMock()

        def attribute(name, _p=pname, _t=ptype, _z=zoom):
            return {"providerName": _p, "productType": _t, "zoom": _z}[name]

        feature.attribute.side_effect = attribute
        footprints[idx] = feature
    app_context = SimpleNamespace(search_footprints=footprints)

    service = ProviderService.__new__(ProviderService)
    service.dlg = dlg
    service.app_context = app_context
    service.config = config
    service.imagery_search_provider_instance = SimpleNamespace(requires_id=None, image_ids=None)
    service.my_imagery_provider_instance = SimpleNamespace(mosaic_id=None, image_ids=None)
    service.tr = lambda msg: msg
    return service


def _rows_with_ids(ids):
    from mapflow.config import Config
    config = Config()
    width = config.MAXAR_ID_COLUMN_INDEX + 1
    rows = []
    for image_id in ids:
        row = [""] * width
        row[config.MAXAR_ID_COLUMN_INDEX] = image_id
        rows.append(row)
    return rows


# ---------- Bug 1: all selected IDs returned ----------

class TestSearchImagesIdsCollectsAllRows:
    def test_same_provider_all_ids(self):
        rows = _rows_with_ids(["img-1", "img-2", "img-3"])
        service = _make_service(rows,
                                provider_names=["orbview_msi"] * 3,
                                product_types=["Image"] * 3)
        image_ids, err = service.get_search_images_ids(["orbview_msi"] * 3, ["Image"] * 3)
        assert image_ids == ["img-1", "img-2", "img-3"]
        assert err == ""
        assert service.imagery_search_provider_instance.image_ids == ["img-1", "img-2", "img-3"]
        assert service.imagery_search_provider_instance.requires_id is True

    def test_single_row_unchanged(self):
        rows = _rows_with_ids(["only-one"])
        service = _make_service(rows, provider_names=["maxar"], product_types=["Image"])
        image_ids, err = service.get_search_images_ids(["maxar"], ["Image"])
        assert image_ids == ["only-one"]
        assert err == ""

    def test_empty_selection(self):
        service = _make_service([], provider_names=[], product_types=[])
        image_ids, err = service.get_search_images_ids([], [])
        assert image_ids is None
        assert err == ""
        assert service.imagery_search_provider_instance.requires_id is False


# ---------- Mixed provider rules ----------

class TestMixedProvidersRules:
    def test_mixed_image_providers_blocked(self):
        """Different providers with product type Image — including orbview_msi + orbview_pan —
        are rejected client-side because the backend does not currently accept them together."""
        rows = _rows_with_ids(["a", "b"])
        provider_names = ["orbview_msi", "orbview_pan"]
        product_types = ["Image", "Image"]
        service = _make_service(rows, provider_names, product_types)
        _, err = service.get_search_images_ids(provider_names, product_types)
        assert err != ""

    def test_mixed_with_non_orbview_blocked(self):
        rows = _rows_with_ids(["a", "b"])
        provider_names = ["maxar", "skywatch"]
        product_types = ["Image", "Image"]
        service = _make_service(rows, provider_names, product_types)
        _, err = service.get_search_images_ids(provider_names, product_types)
        assert err != ""

    def test_pure_mosaic_mix_still_allowed(self):
        rows = _rows_with_ids(["a", "b"])
        provider_names = ["foo", "bar"]
        product_types = ["Mosaic", "Mosaic"]
        service = _make_service(rows, provider_names, product_types)
        _, err = service.get_search_images_ids(provider_names, product_types)
        assert err == ""


# ---------- validate_provider_params blocks the cost/create call on mixed providers ----------

class TestValidateBlocksMixedProviders:
    def test_mixed_image_providers_returns_error(self):
        """validate_provider_params must surface the mismatch so
        validate_all_processing_params propagates it and blocks the cost call."""
        from mapflow.entity.provider import ImagerySearchProvider
        rows = _rows_with_ids(["a", "b"])
        provider_names = ["orbview_msi", "orbview_pan"]
        product_types = ["Image", "Image"]
        service = _make_service(rows, provider_names, product_types)
        service.imagery_search_provider_instance.image_ids = ["a", "b"]
        provider = ImagerySearchProvider(proxy="http://example")
        err = service.validate_provider_params(provider)
        assert err is not None and err != ""

    def test_same_image_provider_no_error(self):
        from mapflow.entity.provider import ImagerySearchProvider
        rows = _rows_with_ids(["a", "b"])
        provider_names = ["orbview_msi", "orbview_msi"]
        product_types = ["Image", "Image"]
        service = _make_service(rows, provider_names, product_types)
        service.imagery_search_provider_instance.image_ids = ["a", "b"]
        provider = ImagerySearchProvider(proxy="http://example")
        assert service.validate_provider_params(provider) is None

    def test_mixed_mosaics_no_error(self):
        from mapflow.entity.provider import ImagerySearchProvider
        rows = _rows_with_ids(["a", "b"])
        provider_names = ["foo", "bar"]
        product_types = ["Mosaic", "Mosaic"]
        service = _make_service(rows, provider_names, product_types,
                                zooms=["18", "18"])
        service.imagery_search_provider_instance.image_ids = ["a", "b"]
        provider = ImagerySearchProvider(proxy="http://example")
        assert service.validate_provider_params(provider) is None


# ---------- Bug 3: duplicate_imagery_search expands all rows ----------

class TestDuplicateImagerySearchMultiRow:
    def test_n_rows_one_per_image_id(self):
        from mapflow.config import Config
        from mapflow.schema import ImagerySearchParams, ImagerySearchSchema
        from mapflow.functional.service.provider_service import ProviderService
        from mapflow.config import ConfigColumns

        ProviderService._instance = None
        ProviderService._initialized = False

        config = Config()
        service = ProviderService.__new__(ProviderService)
        service.config = config
        service.config_search_columns = ConfigColumns().METADATA_TABLE_ATTRIBUTES
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
        aoi_feature = MagicMock()
        aoi_feature.geometry.return_value = MagicMock()
        layer = MagicMock()
        layer.getFeatures.return_value = [aoi_feature]
        dlg.polygonCombo.currentLayer.return_value = layer
        dlg.tabWidget.findChild.return_value = MagicMock()
        dlg.sourceCombo = MagicMock()
        dlg.metadataTableFilled = MagicMock()
        service.dlg = dlg
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

        id_col = config.MAXAR_ID_COLUMN_INDEX
        id_items = [(r, item) for (r, c, item) in set_items if c == id_col]
        assert len(id_items) == 3
        seen_ids = set()
        for _r, item in id_items:
            for call in item.setData.call_args_list:
                args = call.args
                if len(args) >= 2:
                    seen_ids.add(args[1])
        assert seen_ids == set(image_ids)
        assert set(service.app_context.search_footprints.keys()) == {0, 1, 2}
