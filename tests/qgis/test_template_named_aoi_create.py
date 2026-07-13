"""QGIS-tier tests for sending AOI names when creating a template (spec 002_F).

When the source layer has a ``name`` attribute, each AOI feature in
``searchParams.aoiDetails`` carries that name; otherwise the name is ``None``.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsField
from PyQt5.QtCore import QVariant

from mapflow.mapflow import Mapflow
from mapflow.schema.template import AOI_NAME_MAX_LENGTH


def _layer_with(features, with_name_field=True):
    layer = QgsVectorLayer("Polygon?crs=epsg:4326", "aois", "memory")
    provider = layer.dataProvider()
    if with_name_field:
        provider.addAttributes([QgsField("name", QVariant.String)])
        layer.updateFields()
    qgs_features = []
    for wkt, name in features:
        feat = QgsFeature(layer.fields())
        feat.setGeometry(QgsGeometry.fromWkt(wkt))
        if with_name_field:
            feat.setAttribute("name", name)
        qgs_features.append(feat)
    provider.addFeatures(qgs_features)
    layer.updateExtents()
    return layer


def _plugin_with_layer(layer):
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda text: text
    plugin.dlg = MagicMock()
    plugin.dlg.polygonCombo.currentLayer.return_value = layer
    return plugin


def test_aoi_details_carry_names_from_layer_attribute():
    layer = _layer_with([
        ("POLYGON((0 0,0 1,1 1,1 0,0 0))", "North"),
        ("POLYGON((2 2,2 3,3 3,3 2,2 2))", "South"),
    ])
    plugin = _plugin_with_layer(layer)

    fc = plugin._build_template_aoi_details()

    assert fc["type"] == "FeatureCollection"
    names = [f["properties"]["name"] for f in fc["features"]]
    assert names == ["North", "South"]


def test_aoi_details_null_name_without_attribute():
    layer = _layer_with([("POLYGON((0 0,0 1,1 1,1 0,0 0))", None)], with_name_field=False)
    plugin = _plugin_with_layer(layer)

    fc = plugin._build_template_aoi_details()

    assert fc["features"][0]["properties"]["name"] is None


def test_aoi_details_rejects_overlong_name():
    layer = _layer_with([("POLYGON((0 0,0 1,1 1,1 0,0 0))", "x" * (AOI_NAME_MAX_LENGTH + 1))])
    plugin = _plugin_with_layer(layer)

    with pytest.raises(ValueError):
        plugin._build_template_aoi_details()


def test_no_layer_falls_back_to_aoi_as_one_unnamed_feature():
    """Without a polygon layer (e.g. an image extent) aoiDetails is still built from the
    combined AOI as a single unnamed feature — the deprecated plain `aoi` is never sent."""
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda text: text
    plugin.dlg = MagicMock()
    plugin.dlg.polygonCombo.currentLayer.return_value = None
    plugin.app_context = SimpleNamespace(aoi=QgsGeometry.fromWkt("POLYGON((0 0,0 1,1 1,1 0,0 0))"))

    fc = plugin._build_template_aoi_details()

    assert fc["type"] == "FeatureCollection"
    assert len(fc["features"]) == 1
    assert fc["features"][0]["properties"]["name"] is None


def test_no_layer_no_aoi_returns_none():
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda text: text
    plugin.dlg = MagicMock()
    plugin.dlg.polygonCombo.currentLayer.return_value = None
    plugin.app_context = SimpleNamespace(aoi=None)

    assert plugin._build_template_aoi_details() is None


def test_multipolygon_feature_is_exploded_into_polygons():
    """The backend ignores MultiPolygon features in aoiDetails (feedback 10), so a
    MultiPolygon AOI is split into one Polygon feature per part, each keeping the name."""
    layer = _layer_with([
        ("MULTIPOLYGON(((0 0,0 1,1 1,1 0,0 0)),((2 2,2 3,3 3,3 2,2 2)))", "Combo"),
    ])
    plugin = _plugin_with_layer(layer)

    fc = plugin._build_template_aoi_details()

    assert len(fc["features"]) == 2
    assert [f["geometry"]["type"] for f in fc["features"]] == ["Polygon", "Polygon"]
    assert [f["properties"]["name"] for f in fc["features"]] == ["Combo", "Combo"]


def test_mixed_polygon_and_multipolygon_features_all_become_polygons():
    layer = _layer_with([
        ("POLYGON((0 0,0 1,1 1,1 0,0 0))", "Single"),
        ("MULTIPOLYGON(((2 2,2 3,3 3,3 2,2 2)),((4 4,4 5,5 5,5 4,4 4)))", "Double"),
    ])
    plugin = _plugin_with_layer(layer)

    fc = plugin._build_template_aoi_details()

    assert [f["geometry"]["type"] for f in fc["features"]] == ["Polygon", "Polygon", "Polygon"]
    assert [f["properties"]["name"] for f in fc["features"]] == ["Single", "Double", "Double"]


def test_fallback_multipolygon_aoi_is_exploded():
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda text: text
    plugin.dlg = MagicMock()
    plugin.dlg.polygonCombo.currentLayer.return_value = None
    plugin.app_context = SimpleNamespace(
        aoi=QgsGeometry.fromWkt(
            "MULTIPOLYGON(((0 0,0 1,1 1,1 0,0 0)),((2 2,2 3,3 3,3 2,2 2)))"
        )
    )

    fc = plugin._build_template_aoi_details()

    assert len(fc["features"]) == 2
    assert all(f["geometry"]["type"] == "Polygon" for f in fc["features"])
    assert all(f["properties"]["name"] is None for f in fc["features"])
