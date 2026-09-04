"""Tests for multi-image Imagery Search selection handling.

Spec reference: spec/002_B_processing_api.md (ImagerySearchSchema.imageIds: List[str]).

Tier: qgis. Most cases here are mock-driven and would sit happily in the functional
tier, but ``duplicate_imagery_search`` builds a real in-memory ``QgsVectorLayer`` and
real ``QgsFeature``s, which is real QGIS state per spec/004_stack.md. The suite is kept
together rather than split across tiers — both run in the same image, so the split would
buy nothing and separate tests that belong side by side.

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


def _make_service(rows, provider_names, product_types, zooms=None,
                  min_areas=None, aoi_size=None):
    """Build the minimum ProviderService surface needed by the methods under test.

    The service reads no table now — the search selection is pushed to `app_context`
    (`selected_search_indices` + `selected_search_image_ids`), so the fixture pushes there.
    """
    from mapflow.functional.service.provider_service import ProviderService
    from mapflow.config import Config

    config = Config()

    ProviderService._instance = None
    ProviderService._initialized = False

    footprints = {}
    zooms = zooms or [None] * len(provider_names)
    # `min_areas=None` means the field is absent — feature.attribute("minAreaSqkm")
    # raises KeyError, matching how a layer without that field behaves.
    min_areas = min_areas if min_areas is not None else [None] * len(provider_names)
    for idx, (pname, ptype, zoom, min_area) in enumerate(
            zip(provider_names, product_types, zooms, min_areas)):
        feature = MagicMock()

        def attribute(name, _p=pname, _t=ptype, _z=zoom, _m=min_area):
            values = {"providerName": _p, "productType": _t, "zoom": _z}
            if _m is not None:
                values["minAreaSqkm"] = _m
            return values[name]  # KeyError for absent fields, as a real layer would

        feature.attribute.side_effect = attribute
        footprints[idx] = feature
    # The local index of each selected row is its position; the image id is the ID column.
    selected_indices = [str(i) for i in range(len(provider_names))]
    selected_image_ids = [row[config.SEARCH_ID_COLUMN_INDEX] for row in rows]
    app_context = SimpleNamespace(search_footprints=footprints, aoi_size=aoi_size,
                                  selected_search_indices=selected_indices,
                                  selected_search_image_ids=selected_image_ids)

    service = ProviderService.__new__(ProviderService)
    service.app_context = app_context
    service.config = config
    service.imagery_search_provider_instance = SimpleNamespace(requires_id=None, image_ids=None)
    service.my_imagery_provider_instance = SimpleNamespace(mosaic_id=None, image_ids=None)
    service.tr = lambda msg: msg
    return service


def _rows_with_ids(ids):
    from mapflow.config import Config
    config = Config()
    # Must be wide enough for LOCAL_INDEX_COLUMN, not just the ID column:
    # get_local_image_indices() reads the local_index cell, and a short row makes
    # metadataTable.item() return None -> AttributeError -> the service swallows it
    # and returns [], silently skipping every provider/zoom/min-area validation.
    width = max(config.SEARCH_ID_COLUMN_INDEX, config.LOCAL_INDEX_COLUMN) + 1
    rows = []
    for row_index, image_id in enumerate(ids):
        row = [""] * width
        row[config.SEARCH_ID_COLUMN_INDEX] = image_id
        row[config.LOCAL_INDEX_COLUMN] = str(row_index)
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
        from mapflow.model.provider import ImagerySearchProvider
        rows = _rows_with_ids(["a", "b"])
        provider_names = ["orbview_msi", "orbview_pan"]
        product_types = ["Image", "Image"]
        service = _make_service(rows, provider_names, product_types)
        service.imagery_search_provider_instance.image_ids = ["a", "b"]
        provider = ImagerySearchProvider(proxy="http://example")
        err = service.validate_provider_params(provider)
        assert err is not None and err != ""

    def test_same_image_provider_no_error(self):
        from mapflow.model.provider import ImagerySearchProvider
        rows = _rows_with_ids(["a", "b"])
        provider_names = ["orbview_msi", "orbview_msi"]
        product_types = ["Image", "Image"]
        service = _make_service(rows, provider_names, product_types)
        service.imagery_search_provider_instance.image_ids = ["a", "b"]
        provider = ImagerySearchProvider(proxy="http://example")
        assert service.validate_provider_params(provider) is None

    def test_mixed_mosaics_no_error(self):
        from mapflow.model.provider import ImagerySearchProvider
        rows = _rows_with_ids(["a", "b"])
        provider_names = ["foo", "bar"]
        product_types = ["Mosaic", "Mosaic"]
        service = _make_service(rows, provider_names, product_types,
                                zooms=["18", "18"])
        service.imagery_search_provider_instance.image_ids = ["a", "b"]
        provider = ImagerySearchProvider(proxy="http://example")
        assert service.validate_provider_params(provider) is None


# ---------- Provider minimum-area check (AREA billing & any change) ----------

class TestMinAreaCheck:
    def test_aoi_below_min_area_errors(self):
        from mapflow.model.provider import ImagerySearchProvider
        rows = _rows_with_ids(["a"])
        service = _make_service(rows,
                                provider_names=["maxar"],
                                product_types=["Image"],
                                min_areas=[25.0],
                                aoi_size=10.0)
        service.imagery_search_provider_instance.image_ids = ["a"]
        provider = ImagerySearchProvider(proxy="http://example")
        err = service.validate_provider_params(provider)
        assert err is not None and "minimum required area" in err

    def test_aoi_above_min_area_no_error(self):
        from mapflow.model.provider import ImagerySearchProvider
        rows = _rows_with_ids(["a"])
        service = _make_service(rows,
                                provider_names=["maxar"],
                                product_types=["Image"],
                                min_areas=[25.0],
                                aoi_size=30.0)
        service.imagery_search_provider_instance.image_ids = ["a"]
        provider = ImagerySearchProvider(proxy="http://example")
        assert service.validate_provider_params(provider) is None

    def test_multiple_images_use_max_min_area(self):
        from mapflow.model.provider import ImagerySearchProvider
        rows = _rows_with_ids(["a", "b"])
        service = _make_service(rows,
                                provider_names=["orbview_msi", "orbview_msi"],
                                product_types=["Image", "Image"],
                                min_areas=[10.0, 25.0],
                                aoi_size=20.0)  # below the max (25)
        service.imagery_search_provider_instance.image_ids = ["a", "b"]
        provider = ImagerySearchProvider(proxy="http://example")
        err = service.validate_provider_params(provider)
        assert err is not None and "minimum required area" in err

    def test_missing_min_area_field_no_error(self):
        """Duplicated search layers don't carry minAreaSqkm; absence must not crash
        or block."""
        from mapflow.model.provider import ImagerySearchProvider
        rows = _rows_with_ids(["a"])
        service = _make_service(rows,
                                provider_names=["maxar"],
                                product_types=["Image"],
                                min_areas=None,  # field absent
                                aoi_size=1.0)
        service.imagery_search_provider_instance.image_ids = ["a"]
        provider = ImagerySearchProvider(proxy="http://example")
        assert service.validate_provider_params(provider) is None

    def test_no_aoi_size_no_error(self):
        from mapflow.model.provider import ImagerySearchProvider
        rows = _rows_with_ids(["a"])
        service = _make_service(rows,
                                provider_names=["maxar"],
                                product_types=["Image"],
                                min_areas=[25.0],
                                aoi_size=None)  # AOI not measured yet
        service.imagery_search_provider_instance.image_ids = ["a"]
        provider = ImagerySearchProvider(proxy="http://example")
        assert service.validate_provider_params(provider) is None


# ---------- Bug 3: duplicate_imagery_search expands all rows ----------

class TestDuplicateImagerySearchMultiRow:
    def test_n_rows_one_per_image_id(self):
        from mapflow.config import Config
        from mapflow.schema import ImagerySearchParams, ImagerySearchSchema
        from mapflow.functional.service.provider_service import ProviderService
        from mapflow.config import ConfigColumns

        from PyQt5.QtCore import QObject

        ProviderService._instance = None
        ProviderService._initialized = False

        config = Config()
        service = ProviderService.__new__(ProviderService)
        QObject.__init__(service)  # imagerySearchDuplicated is a signal now
        service.config = config
        service.config_search_columns = ConfigColumns().METADATA_TABLE_ATTRIBUTES
        service.tr = lambda msg: msg
        # A real QgsGeometry, not a MagicMock: duplicate_imagery_search builds a real
        # in-memory QgsVectorLayer and calls QgsFeature.setGeometry(), which rejects
        # anything that is not a genuine geometry. This is why the file sits in the
        # qgis tier — see the module docstring. The AOI layer is pushed to app_context now.
        from qgis.core import QgsGeometry
        aoi_feature = MagicMock()
        aoi_feature.geometry.return_value = QgsGeometry.fromWkt("POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))")
        aoi_layer = MagicMock()
        aoi_layer.getFeatures.return_value = [aoi_feature]
        service.app_context = SimpleNamespace(metadata_layer=None,
                                              search_footprints={},
                                              meta_layer_table_connection=None,
                                              aoi_layer=aoi_layer)
        service.selection_sync_callback = lambda *_a, **_kw: None
        type(service).imagery_search_provider_index = property(lambda self: 0)
        service.providers = []

        # The table fill is announced as a signal for SearchView to draw; capture what it carries.
        duplicated_rows = []
        service.imagerySearchDuplicated.connect(duplicated_rows.append)

        image_ids = ["img-1", "img-2", "img-3"]
        params = ImagerySearchParams(
            ImagerySearchSchema(dataProvider="orbview_msi",
                                imageIds=image_ids,
                                zoom=18)
        )
        service.duplicate_imagery_search(params)

        assert len(duplicated_rows) == 1
        rows = duplicated_rows[0]
        assert len(rows) == 3, "Should hand over one row per imageId"

        id_col = config.SEARCH_ID_COLUMN_INDEX
        seen_ids = {row[id_col] for row in rows}
        assert seen_ids == set(image_ids)
        # Keys must be ints — `get_local_image_indices` casts the local index via int(),
        # so a string-keyed dict would KeyError downstream and leave the request without dataProvider.
        keys = list(service.app_context.search_footprints.keys())
        assert all(isinstance(k, int) for k in keys)
        assert set(keys) == {0, 1, 2}


# ---------- confirmation dialog summary ----------

class TestSetupProviderInfoMultiImage:
    def test_multiple_rows_show_count(self):
        from mapflow.model.provider import ImagerySearchProvider
        rows = _rows_with_ids(["a", "b", "c"])
        service = _make_service(rows,
                                provider_names=["orbview_msi"] * 3,
                                product_types=["Image"] * 3)
        provider = ImagerySearchProvider(proxy="http://example")
        text = service.setup_provider_info(provider)
        assert "3 images selected" in text

    def test_single_row_shows_id(self):
        from mapflow.model.provider import ImagerySearchProvider
        rows = _rows_with_ids(["only-one"])
        service = _make_service(rows,
                                provider_names=["orbview_msi"],
                                product_types=["Image"])
        provider = ImagerySearchProvider(proxy="http://example")
        text = service.setup_provider_info(provider)
        assert "only-one" in text
        assert "images selected" not in text


# ---------- billing-aware /cost skip ----------

class TestUpdateProcessingCostSkipsNonCredits:
    def _service(self, billing_type):
        from mapflow.functional.service.processing_service import ProcessingService
        from PyQt5.QtCore import QObject
        service = ProcessingService.__new__(ProcessingService)
        QObject.__init__(service)  # a disabled start is announced as a signal
        service.app_context = SimpleNamespace(billing_type=billing_type)
        service.api = MagicMock()
        # Tag validate_all_processing_params so we can detect whether we got past the billing gate.
        service.validate_all_processing_params = MagicMock(return_value=(MagicMock(), None))
        return service

    def test_validation_runs_but_cost_skipped_for_area(self):
        """Validation must still drive the UI label / start-button state for
        AREA billing — only the network call is skipped."""
        from mapflow.schema import BillingType
        service = self._service(BillingType.area)
        service.update_processing_cost()
        service.validate_all_processing_params.assert_called_once()
        service.api.get_cost.assert_not_called()

    def test_validation_runs_but_cost_skipped_for_none(self):
        from mapflow.schema import BillingType
        service = self._service(BillingType.none)
        service.update_processing_cost()
        service.validate_all_processing_params.assert_called_once()
        service.api.get_cost.assert_not_called()

    def test_validation_error_short_circuits_for_area(self):
        """A validation error surfaced by the chain must disable the start
        button even when /cost is not called, so issues like mixed-provider
        selection and missing project are visible immediately."""
        from mapflow.schema import BillingType
        service = self._service(BillingType.area)
        service.validate_all_processing_params = MagicMock(
            return_value=(None, "Models are not initialized"))
        disabled = []
        service.startDisabled.connect(lambda *a: disabled.append(a))
        service.update_processing_cost()
        assert len(disabled) == 1
        service.api.get_cost.assert_not_called()

    def test_runs_when_billing_is_credits(self):
        from mapflow.schema import BillingType
        service = self._service(BillingType.credits)
        service.update_processing_cost()
        service.validate_all_processing_params.assert_called_once()
        service.api.get_cost.assert_called_once()


# ---------- Clearing the imagery search selection ----------

class TestSelectionClearedResetsState:
    def test_get_provider_params_drops_stale_image_ids(self):
        """When the user deselects all rows, get_provider_params must wipe the
        cached image_ids so the next /cost call isn't dispatched with a stale
        imageId and a missing dataProvider (backend 400)."""
        from mapflow.model.provider import ImagerySearchProvider
        service = _make_service(rows=[],
                                provider_names=[],
                                product_types=[])
        # Simulate residual state from a previous selection.
        service.imagery_search_provider_instance.image_ids = ["stale-id"]
        service.imagery_search_provider_instance.requires_id = True
        # Avoid touching the real provider's to_processing_params; we only care
        # about side effects on imagery_search_provider_instance.
        provider = MagicMock(spec=ImagerySearchProvider)
        provider.name = "imagery_search"
        provider.to_processing_params.return_value = (MagicMock(), {})

        service.app_context.plugin_version = "test"
        service.get_provider_params(provider, zoom=None)

        assert service.imagery_search_provider_instance.image_ids is None
        assert service.imagery_search_provider_instance.requires_id is None

    def test_validate_blocks_when_image_ids_is_empty_list(self):
        """get_search_images_ids writes [] (not None) when its inner branch
        runs with no rows. validate_provider_params must treat [] the same as
        None and surface the error so /cost is short-circuited."""
        from mapflow.model.provider import ImagerySearchProvider
        service = _make_service(rows=[],
                                provider_names=[],
                                product_types=[])
        service.imagery_search_provider_instance.image_ids = []
        provider = ImagerySearchProvider(proxy="http://example")
        err = service.validate_provider_params(provider)
        assert err is not None and err != ""
