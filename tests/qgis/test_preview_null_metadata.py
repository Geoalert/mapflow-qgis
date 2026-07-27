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


def _feature_without_acquisition_date_field(preview_type, preview_url, provider_name):
    """A layer whose acquisitionDate column is *absent* — the case OGR produces when every My
    Imagery result has a null acquisitionDate (an all-null property is dropped from the schema),
    so ``feature.attribute('acquisitionDate')`` raises ``KeyError``."""
    layer = QgsVectorLayer(
        "Point?crs=epsg:4326&field=id:string&field=previewUrl:string"
        "&field=previewType:string&field=providerName:string",  # note: no acquisitionDate
        "m", "memory")
    feat = QgsFeature(layer.fields())
    feat.setAttribute("id", "x")
    feat.setAttribute("previewUrl", preview_url)
    feat.setAttribute("previewType", preview_type)
    feat.setAttribute("providerName", provider_name)
    layer.dataProvider().addFeatures([feat])
    return next(layer.getFeatures())


def _preview_plugin(feature):
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda t: t
    plugin.iface = MagicMock()
    plugin.alert = MagicMock()
    plugin.metadata_feature = MagicMock(return_value=feature)
    plugin.metadata_footprint = MagicMock(return_value=MagicMock())
    plugin.preview_png = MagicMock()
    plugin.preview_mosaic = MagicMock()
    plugin._pending_preview_ids = set()
    plugin.app_context = SimpleNamespace(project=MagicMock(), metadata_layer=MagicMock())
    plugin.app_context.project.mapLayersByName.return_value = []
    return plugin


def test_mosaic_previews_when_acquisition_date_field_is_absent():
    # The reported bug: a mosaic (valid xyz preview) reported "Selected imagery has no preview"
    # because a KeyError on the missing acquisitionDate column blanked out preview_type.
    feature = _feature_without_acquisition_date_field(
        "xyz", "https://host/api/v0/cogs/tiles/{z}/{x}/{y}.png?uri=s3://bucket/cog",
        "my_imagery_mosaics")
    plugin = _preview_plugin(feature)

    plugin.preview_catalog("mosaic-1")

    plugin.preview_mosaic.assert_called_once()
    plugin.preview_png.assert_not_called()
    plugin.alert.assert_not_called()  # no "Selected imagery has no preview"


def test_image_dispatches_to_png_when_acquisition_date_field_is_absent():
    # An image reaches the PNG branch too (its own failure, if any, is the broken URL download —
    # not the false "no preview").
    feature = _feature_without_acquisition_date_field(
        "png", "https://host/rest/rasters/image/x/preview/l", "my_imagery_images")
    plugin = _preview_plugin(feature)

    plugin.preview_catalog("img-1")

    plugin.preview_png.assert_called_once()
    plugin.alert.assert_not_called()
