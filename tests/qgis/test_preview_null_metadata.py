"""QGIS-tier test: previewing a My Imagery result (no acquisition date) must not raise.

A NULL ``acquisitionDate`` attribute comes back as Python ``None``, so the historic
``feature.attribute('acquisitionDate').toString(...)`` raised ``AttributeError`` — which the
surrounding ``except KeyError`` (there for duplicated processings) did not catch.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

from qgis.core import QgsVectorLayer, QgsFeature

from mapflow.mapflow import Mapflow


def _null_date_feature():
    layer = QgsVectorLayer(
        "Point?crs=epsg:4326&field=previewUrl:string&field=previewType:string"
        "&field=providerName:string&field=acquisitionDate:datetime",
        "m", "memory")
    feat = QgsFeature(layer.fields())
    feat.setAttribute("previewUrl", "https://whitemaps-v2.mapflow.ai/rest/rasters/image/x/preview/l")
    feat.setAttribute("previewType", "png")
    feat.setAttribute("providerName", "my_imagery_images")
    # acquisitionDate is left NULL (Python None) — the case this test guards.
    layer.dataProvider().addFeatures([feat])
    return next(layer.getFeatures())


def test_preview_catalog_handles_null_acquisition_date():
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda t: t
    plugin.iface = MagicMock()
    plugin.metadata_feature = MagicMock(return_value=_null_date_feature())
    plugin.metadata_footprint = MagicMock(return_value=MagicMock())
    plugin.preview_png = MagicMock()
    plugin._pending_preview_ids = set()
    plugin.app_context = SimpleNamespace(project=MagicMock(), metadata_layer=MagicMock())
    plugin.app_context.project.mapLayersByName.return_value = []

    plugin.preview_catalog("img-1")  # must not raise

    # The PNG branch is reached (no exception aborted it before dispatch).
    plugin.preview_png.assert_called_once()
