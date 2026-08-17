"""QGIS-tier tests: intersecting AOIs are merged before they are sent as ``aoiDetails``, and the
user is asked first when the merge would discard AOI names (spec 002_F).

Merging is what stops the shared area from being searched (and billed) twice; the prompt exists
because a merged AOI cannot keep two different names.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from PyQt5.QtCore import QVariant
from qgis.core import QgsFeature, QgsField, QgsGeometry, QgsVectorLayer

from mapflow.errors import AoiMergeDeclined
from mapflow.mapflow import Mapflow

LEFT = "POLYGON((0 0,0 1,1 1,1 0,0 0))"
RIGHT = "POLYGON((0.75 0,0.75 1,1.75 1,1.75 0,0.75 0))"  # overlaps LEFT
FAR = "POLYGON((5 5,5 6,6 6,6 5,5 5))"


def _layer_with(features, with_name_field=True):
    layer = QgsVectorLayer("Polygon?crs=epsg:4326", "aois", "memory")
    provider = layer.dataProvider()
    if with_name_field:
        provider.addAttributes([QgsField("name", QVariant.String)])
        layer.updateFields()
    qgs_features = []
    for wkt, name in features:
        feature = QgsFeature(layer.fields())
        feature.setGeometry(QgsGeometry.fromWkt(wkt))
        if with_name_field:
            feature.setAttribute("name", name)
        qgs_features.append(feature)
    provider.addFeatures(qgs_features)
    layer.updateExtents()
    return layer


def _plugin(layer, confirmed=True):
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda text: text
    plugin.dlg = MagicMock()
    plugin.dlg.polygonCombo.currentLayer.return_value = layer
    plugin.alert = MagicMock(return_value=confirmed)
    return plugin


def test_intersecting_aois_with_different_names_ask_before_merging():
    plugin = _plugin(_layer_with([(LEFT, "North"), (RIGHT, "South")]))

    fc = plugin._build_template_aoi_details()

    plugin.alert.assert_called_once()
    assert "merged" in plugin.alert.call_args[0][0]
    # One merged AOI, and the ambiguous name is dropped rather than picked arbitrarily.
    assert len(fc["features"]) == 1
    assert fc["features"][0]["properties"]["name"] is None


def test_declined_merge_aborts_the_details_build():
    plugin = _plugin(_layer_with([(LEFT, "North"), (RIGHT, "South")]), confirmed=False)

    with pytest.raises(AoiMergeDeclined):
        plugin._build_template_aoi_details()


def test_declined_merge_does_not_create_the_template():
    layer = _layer_with([(LEFT, "North"), (RIGHT, "South")])
    plugin = _plugin(layer, confirmed=False)
    plugin.replace_search_provider_index = MagicMock()
    plugin._build_search_params = MagicMock()
    plugin.app_context = SimpleNamespace(current_project=object(),
                                         aoi=QgsGeometry.fromWkt(LEFT),
                                         aoi_size=1.0,
                                         template_area_limit=0)

    plugin.create_search_template()

    plugin._build_search_params.assert_not_called()


def test_intersecting_aois_sharing_one_name_merge_silently():
    """Only *conflicting* names are worth a prompt: an unnamed neighbour loses nothing."""
    plugin = _plugin(_layer_with([(LEFT, "North"), (RIGHT, None)]))

    fc = plugin._build_template_aoi_details()

    plugin.alert.assert_not_called()
    assert len(fc["features"]) == 1
    assert fc["features"][0]["properties"]["name"] == "North"


def test_disjoint_named_aois_are_untouched():
    plugin = _plugin(_layer_with([(LEFT, "North"), (FAR, "South")]))

    fc = plugin._build_template_aoi_details()

    plugin.alert.assert_not_called()
    assert [f["properties"]["name"] for f in fc["features"]] == ["North", "South"]


def test_merged_aoi_is_a_single_part_polygon_spanning_both_sources():
    plugin = _plugin(_layer_with([(LEFT, "North"), (RIGHT, "South")]))

    geometry = plugin._build_template_aoi_details()["features"][0]["geometry"]

    # Single-part Polygon: the backend ignores MultiPolygon features in aoiDetails.
    assert geometry["type"] == "Polygon"
    xs = [point[0] for point in geometry["coordinates"][0]]
    assert min(xs) == pytest.approx(0.0)   # left edge of LEFT
    assert max(xs) == pytest.approx(1.75)  # right edge of RIGHT


def test_drawn_overlapping_aois_are_added_as_one():
    """The draw-AOI session has no name field, so overlapping sketches merge without a prompt."""
    plugin = _plugin(None)
    plugin.iface = MagicMock()
    plugin.processing_service = MagicMock()
    plugin.processing_service.active_template = SimpleNamespace(id="t-1")
    layer = _layer_with([(LEFT, None), (RIGHT, None)], with_name_field=False)

    with patch("mapflow.mapflow.QInputDialog.getText", return_value=("Drawn", True)):
        assert plugin._commit_aoi_draw(layer) is True

    plugin.alert.assert_not_called()
    data = plugin.processing_service.api.add_aois.call_args.kwargs["data"]
    assert len(data.aois) == 1
    assert data.aois[0].name == "Drawn"
