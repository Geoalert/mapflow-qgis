"""QGIS-tier tests for sending AOI names when creating a template (spec 002_F).

When the source layer has a ``name`` attribute, each AOI feature in
``searchParams.aoiDetails`` carries that name; otherwise the name is ``None``.
"""
from unittest.mock import MagicMock

import pytest
from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsField
from PyQt5.QtCore import QVariant

from mapflow.mapflow import Mapflow
from mapflow.schema.processing import AOI_NAME_MAX_LENGTH


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


def test_no_layer_returns_none():
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda text: text
    plugin.dlg = MagicMock()
    plugin.dlg.polygonCombo.currentLayer.return_value = None

    assert plugin._build_template_aoi_details() is None
