"""QGIS-tier test: previewing a My Imagery result (no acquisition date) must not raise.

A NULL ``acquisitionDate`` attribute comes back as Python ``None``, so the historic
``feature.attribute('acquisitionDate').toString(...)`` raised ``AttributeError`` — which the
surrounding ``except KeyError`` (there for duplicated processings) did not catch.

Owned by `PreviewService` since the preview extraction. `alert` is patched rather than mocked
on the object: the service reaches the message tier through a module-level function, the way
every other service does.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from qgis.core import QgsVectorLayer, QgsFeature

from mapflow.functional.service.preview_service import PreviewService


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
    service = _preview_service(_null_date_feature())

    service.preview_catalog("img-1")  # must not raise

    # The PNG branch is reached (no exception aborted it before dispatch).
    service.preview_png.assert_called_once()


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


def _preview_service(feature):
    app_context = SimpleNamespace(project=MagicMock(), metadata_layer=MagicMock())
    app_context.project.mapLayersByName.return_value = []
    service = PreviewService(iface=MagicMock(),
                             app_context=app_context,
                             http=MagicMock(),
                             plugin_dir="",
                             config=MagicMock(),
                             result_loader=MagicMock(),
                             processing_service=SimpleNamespace(in_template_mode=False,
                                                                active_template=None))
    service.metadata_feature = MagicMock(return_value=feature)
    service.metadata_footprint = MagicMock(return_value=MagicMock())
    service.preview_png = MagicMock()
    service.preview_mosaic = MagicMock()
    return service


@pytest.fixture
def alerts(monkeypatch):
    """What the service told the user. Empty is the assertion in both tests below."""
    shown = []
    monkeypatch.setattr("mapflow.functional.service.preview_service.alert",
                        lambda *args, **kwargs: shown.append(args[0] if args else ""))
    return shown


def test_mosaic_previews_when_acquisition_date_field_is_absent(alerts):
    # The reported bug: a mosaic (valid xyz preview) reported "Selected imagery has no preview"
    # because a KeyError on the missing acquisitionDate column blanked out preview_type.
    feature = _feature_without_acquisition_date_field(
        "xyz", "https://host/api/v0/cogs/tiles/{z}/{x}/{y}.png?uri=s3://bucket/cog",
        "my_imagery_mosaics")
    service = _preview_service(feature)

    service.preview_catalog("mosaic-1")

    service.preview_mosaic.assert_called_once()
    service.preview_png.assert_not_called()
    assert alerts == []  # no "Selected imagery has no preview"


def test_image_dispatches_to_png_when_acquisition_date_field_is_absent(alerts):
    # An image reaches the PNG branch too (its own failure, if any, is the broken URL download —
    # not the false "no preview").
    feature = _feature_without_acquisition_date_field(
        "png", "https://host/rest/rasters/image/x/preview/l", "my_imagery_images")
    service = _preview_service(feature)

    service.preview_catalog("img-1")

    service.preview_png.assert_called_once()
    assert alerts == []
