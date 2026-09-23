"""QGIS-tier tests for the processing-cost pre-checks.

* The AOI∩image area must be compared against the provider's minimum BEFORE the
  cost request is sent — when it is too small the request is skipped (and start
  is blocked) with the ProviderMinAreaError message.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

from qgis.core import QgsGeometry, QgsProject
from PyQt5.QtCore import QObject

from mapflow.model.provider.default import ImagerySearchProvider, MyImageryProvider
from mapflow.functional.service.processing_service import ProcessingService
from mapflow.mapflow import Mapflow


def _small_aoi():
    """A ~0.001° square (~0.01 sq km bounding box) — well under any sane aoiAreaLimit,
    so the per-AOI bbox pre-check passes and these tests exercise the provider-min logic."""
    return QgsGeometry.fromWkt("POLYGON((0 0, 0.001 0, 0.001 0.001, 0 0.001, 0 0))")


def _search_provider():
    return ImagerySearchProvider(proxy="https://example.com/rest")


def _footprint(provider=None):
    feature = MagicMock()
    feature.attribute.side_effect = lambda name: {"providerName": provider}.get(name)
    return feature


def test_register_provider_min_areas_maps_name_and_display_name():
    plugin = Mapflow.__new__(Mapflow)
    plugin.app_context = SimpleNamespace(provider_min_areas={})

    plugin._register_provider_min_areas([
        {"name": "arcgis_world_imagery", "displayName": "ArcGIS", "minAreaSqKm": 5.0},
        {"name": "orbview", "displayName": "OrbView"},          # no minimum -> skipped
        {"name": "maxar", "displayName": "Maxar", "minAreaSqkm": 7.5},  # lowercase-k variant
    ])

    mapping = plugin.app_context.provider_min_areas
    assert mapping["arcgis_world_imagery"] == 5.0
    assert mapping["arcgis"] == 5.0      # keyed by display name too
    assert "orbview" not in mapping
    assert mapping["maxar"] == 7.5       # both field spellings accepted


def test_selected_search_min_area_returns_most_restrictive_and_provider():
    service = ProcessingService.__new__(ProcessingService)
    service.app_context = SimpleNamespace(
        data_provider=_search_provider(),
        search_footprints={
            0: _footprint(provider="orbview"),
            2: _footprint(provider="arcgis_world_imagery"),
        },
        provider_min_areas={"orbview": 3.0, "arcgis_world_imagery": 5.0},
        selected_search_indices=["0", "2"],
    )

    min_area, provider = service._selected_search_min_area()

    # The binding (largest) minimum and the provider it belongs to.
    assert min_area == 5.0
    assert provider == "arcgis_world_imagery"


def test_selected_search_min_area_lookup_is_case_insensitive():
    service = ProcessingService.__new__(ProcessingService)
    service.app_context = SimpleNamespace(
        data_provider=_search_provider(),
        search_footprints={0: _footprint(provider="ArcGIS_World_Imagery")},
        provider_min_areas={"arcgis_world_imagery": 5.0},
        selected_search_indices=["0"],
    )

    assert service._selected_search_min_area() == (5.0, "ArcGIS_World_Imagery")


def test_selected_search_min_area_is_none_without_selection():
    service = ProcessingService.__new__(ProcessingService)
    service.app_context = SimpleNamespace(data_provider=_search_provider(),
                                          selected_search_indices=[])

    assert service._selected_search_min_area() == (None, None)


def test_selected_search_min_area_skips_non_search_provider():
    service = ProcessingService.__new__(ProcessingService)
    # Even with a (stale) selection present, a non-search provider short-circuits to (None, None).
    service.app_context = SimpleNamespace(data_provider=MyImageryProvider(),
                                          selected_search_indices=["0"],
                                          search_footprints={0: _footprint(provider="orbview")},
                                          provider_min_areas={"orbview": 3.0})

    assert service._selected_search_min_area() == (None, None)


def test_validate_processing_params_blocks_below_provider_min_area():
    service = ProcessingService.__new__(ProcessingService)
    service.tr = lambda text: text
    service.dlg = MagicMock()
    service.app_context = SimpleNamespace(aoi=_small_aoi(), processing_aoi=_small_aoi(),
                                          project=QgsProject.instance(),
                                          aoi_size=0.1, aoi_area_limit=1000.0)
    service._selected_search_min_area = MagicMock(return_value=(5.0, "orbview"))

    error, _ = service.validate_processing_params(SimpleNamespace(name="Run 1"), allow_empty_name=False)

    assert error is not None
    assert "orbview" in error
    assert "0.1" in error and "5.0" in error


def test_validate_processing_params_passes_when_area_meets_provider_min():
    service = ProcessingService.__new__(ProcessingService)
    service.tr = lambda text: text
    service.dlg = MagicMock()
    service.app_context = SimpleNamespace(aoi=_small_aoi(), processing_aoi=_small_aoi(),
                                          project=QgsProject.instance(),
                                          aoi_size=12.0, aoi_area_limit=1000.0)
    service._selected_search_min_area = MagicMock(return_value=(5.0, "orbview"))

    error, _ = service.validate_processing_params(SimpleNamespace(name="Run 1"), allow_empty_name=False)

    assert error is None


def test_update_processing_cost_skips_request_when_below_provider_min_area():
    service = ProcessingService.__new__(ProcessingService)
    QObject.__init__(service)  # the disable is announced as a signal
    service.tr = lambda text: text
    service.api = MagicMock()
    # Reach validate_processing_params with a too-small AOI∩image area.
    service.validate_context_params = MagicMock(return_value=None)
    service.set_start_panel(SimpleNamespace())
    service.app_context = SimpleNamespace(
        aoi=_small_aoi(), processing_aoi=_small_aoi(), project=QgsProject.instance(),
        aoi_size=0.1, aoi_area_limit=1000.0, data_provider=object(),
    )
    service.get_processing_schema = MagicMock(return_value=SimpleNamespace(name="Run 1"))
    service._selected_search_min_area = MagicMock(return_value=(5.0, "orbview"))
    disabled = []
    service.startDisabled.connect(lambda *a: disabled.append(a))

    service.update_processing_cost()

    service.api.get_cost.assert_not_called()
    # The AOI size is known, so a blocking validation error must NOT clear the area label.
    assert len(disabled) == 1 and disabled[0][1] is False
