"""Tests for data catalog API, schema, and download feature.

Spec reference: spec/002_C_myimagery_api.md
"""
from unittest.mock import MagicMock
from datetime import datetime, timedelta


from mapflow.schema.data_catalog import ImageReturnSchema


# ====== Test data ====== #

def _image_data(**overrides):
    """Minimal valid ImageReturnSchema dict."""
    base = {
        "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "mosaic_id": "11111111-2222-3333-4444-555555555555",
        "image_url": "https://example.com/image.tif",
        "preview_url_l": "https://example.com/preview_l.png",
        "preview_url_s": "https://example.com/preview_s.png",
        "uploaded_at": "2025-01-15T10:30:00Z",
        "file_size": 1048576,
        "footprint": "POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))",
        "filename": "test_image.tif",
        "checksum": "abc123",
        "meta_data": {
            "crs": "EPSG:4326",
            "count": 3,
            "width": 1024,
            "height": 1024,
            "dtypes": ["uint8", "uint8", "uint8"],
            "nodata": 0.0,
            "pixel_size": [0.0001, 0.0001],
        },
        "cog_link": None,
    }
    base.update(overrides)
    return base


# ====== Schema tests ====== #

class TestImageReturnSchema:
    def test_available_for_download_present_true(self):
        """When API returns available_for_download=True, schema has True."""
        data = _image_data(available_for_download=True)
        image = ImageReturnSchema.from_dict(data)
        assert image.available_for_download is True

    def test_available_for_download_present_false(self):
        """When API returns available_for_download=False, schema has False."""
        data = _image_data(available_for_download=False)
        image = ImageReturnSchema.from_dict(data)
        assert image.available_for_download is False

    def test_available_for_download_absent_defaults_true(self):
        """When API omits available_for_download, schema defaults to True."""
        data = _image_data()
        assert "available_for_download" not in data
        image = ImageReturnSchema.from_dict(data)
        assert image.available_for_download is True

    def test_uploaded_at_parsed(self):
        """uploaded_at string is parsed into datetime."""
        data = _image_data()
        image = ImageReturnSchema.from_dict(data)
        assert isinstance(image.uploaded_at, datetime)
        assert image.uploaded_at.utcoffset() == timedelta(0)

    def test_meta_data_parsed(self):
        """meta_data dict is parsed into ImageMetadataSchema."""
        from mapflow.schema.data_catalog import ImageMetadataSchema
        data = _image_data()
        image = ImageReturnSchema.from_dict(data)
        assert isinstance(image.meta_data, ImageMetadataSchema)
        assert image.meta_data.crs == "EPSG:4326"


# ====== API URL construction tests ====== #

class TestDownloadApiUrl:
    def test_download_url_construction(self, http_mock):
        """API client constructs correct download URL."""
        from mapflow.functional.api.data_catalog_api import DataCatalogApi

        dlg_mock = MagicMock()
        api = DataCatalogApi(
            http=http_mock,
            server="https://whitemaps.mapflow.ai/rest",
            dlg=dlg_mock,
            iface=MagicMock(),
            result_loader=MagicMock(),
            plugin_version="1.0.0",
        )
        callback = MagicMock()
        error_handler = MagicMock()
        image_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

        api.download_image(image_id=image_id, callback=callback, error_handler=error_handler)

        http_mock.get.assert_called_once()
        call_kwargs = http_mock.get.call_args
        assert f"/rasters/image/{image_id}/download" in call_kwargs.kwargs.get("url", call_kwargs[1].get("url", ""))
