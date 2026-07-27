"""QGIS-tier tests for parsing /catalog/meta responses with optional metadata.

My Imagery search results (``my_imagery_images`` / ``my_imagery_mosaics``) come back with
``acquisitionDate: null``. ``ImageSchema.__post_init__`` used to raise ``TypeError`` on that,
which aborted the whole ``ImageCatalogResponseSchema`` parse and killed the search response
(spec 002_D "Response and missing metadata"). A null date must now parse and stay ``None``.
"""
from datetime import datetime

import pytest

from mapflow.schema.catalog import ImageSchema, ImageCatalogResponseSchema


def _image(acquisition_date):
    return {
        "id": "img-1",
        "footprint": {"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 1], [0, 0]]]},
        "pixelResolution": None,
        "acquisitionDate": acquisition_date,
        "productType": "Image",
        "sensor": None,
        "colorBandOrder": None,
        "cloudCover": None,
        "offNadirAngle": None,
        "previews": [],
    }


def test_image_schema_allows_null_acquisition_date():
    image = ImageSchema.from_dict(_image(None))  # must not raise
    assert image.acquisitionDate is None


def test_image_schema_parses_iso_acquisition_date():
    image = ImageSchema.from_dict(_image("2026-01-02T03:04:05.000Z"))
    assert isinstance(image.acquisitionDate, datetime)


def test_image_schema_rejects_non_date_type():
    # A genuinely wrong type is still an error — only null is tolerated.
    with pytest.raises(TypeError):
        ImageSchema.from_dict(_image(12345))


def test_catalog_response_parses_mixed_null_and_dated_images():
    response = ImageCatalogResponseSchema(
        images=[_image(None), _image("2026-01-02T03:04:05Z")], total=2)

    assert response.images[0].acquisitionDate is None
    assert isinstance(response.images[1].acquisitionDate, datetime)
    # The GeoJSON conversion the search callback relies on still works for the whole page.
    geojson = response.as_geojson()
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == 2
