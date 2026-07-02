"""Tests for data catalog API, schema, and download feature.

Spec reference: spec/002_C_myimagery_api.md
"""
import json
from unittest.mock import MagicMock
from datetime import datetime, timedelta


from mapflow.schema.data_catalog import (
    ImageReturnSchema,
    ImageStatusSchema,
    MosaicReturnSchema,
    MosaicStatusResponse,
    MosaicStatusSummary,
    PreprocessingStatus,
)


# ====== Test data ====== #

def _mosaic_data(**overrides):
    """Minimal valid MosaicReturnSchema dict."""
    base = {
        "id": "11111111-2222-3333-4444-555555555555",
        "rasterLayer": {
            "tileUrl": "https://example.com/{z}/{x}/{y}.png",
            "tileJsonUrl": "https://example.com/tiles.json",
        },
        "name": "Test mosaic",
        "created_at": "2025-01-15T10:30:00Z",
        "footprint": "MULTIPOLYGON (((0 0, 1 0, 1 1, 0 1, 0 0)))",
        "sizeInBytes": 1048576,
        "tags": ["survey"],
    }
    base.update(overrides)
    return base


def _status_image(**overrides):
    """A per-image entry of GET /mosaic/{id}/status."""
    base = {
        "image_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "filename": "pending.tif",
        "preprocessing_status": "PENDING",
        "preprocessing_error": None,
        "data_available": False,
        "tiles_ready": False,
        "uploaded_at": "2025-01-15T10:30:00Z",
    }
    base.update(overrides)
    return base

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


# ====== Preprocessing status semantics (spec 002_C: Status Summary) ====== #

class TestPreprocessingStatus:
    def test_ready_states(self):
        assert PreprocessingStatus.none.is_ready
        assert PreprocessingStatus.completed.is_ready
        assert not PreprocessingStatus.pending.is_ready

    def test_pending_states(self):
        assert PreprocessingStatus.pending.is_pending
        assert PreprocessingStatus.in_progress.is_pending
        assert not PreprocessingStatus.completed.is_pending

    def test_failed_state(self):
        assert PreprocessingStatus.failed.is_failed
        assert not PreprocessingStatus.completed.is_failed

    def test_unknown_status_falls_back_to_ready(self):
        """Non-breaking API changes: an unknown status must not crash and is treated as ready."""
        assert PreprocessingStatus("SOMETHING_NEW") is PreprocessingStatus.none


# ====== Status summary (mosaic-level counts) ====== #

class TestMosaicStatusSummary:
    def test_parsed_from_dict(self):
        s = MosaicStatusSummary.from_dict(
            {"total": 5, "ready": 3, "pending": 1, "in_progress": 1, "failed": 0})
        assert s.ready == 3
        assert s.preprocessing == 2  # pending + in_progress
        assert s.failed == 0
        assert s.has_activity is True

    def test_no_activity_when_nothing_pending(self):
        s = MosaicStatusSummary.from_dict(
            {"total": 3, "ready": 3, "pending": 0, "in_progress": 0, "failed": 0})
        assert s.has_activity is False
        assert s.preprocessing == 0

    def test_defaults_are_zero(self):
        # SkipDataClass.from_dict({}) is None by design; the dataclass itself defaults to zeros.
        s = MosaicStatusSummary()
        assert (s.total, s.ready, s.pending, s.in_progress, s.failed) == (0, 0, 0, 0, 0)


class TestMosaicReturnSchemaStatusSummary:
    def test_status_summary_parsed(self):
        data = _mosaic_data(status_summary={"total": 2, "ready": 1, "pending": 1,
                                            "in_progress": 0, "failed": 0})
        mosaic = MosaicReturnSchema.from_dict(data)
        assert isinstance(mosaic.status_summary, MosaicStatusSummary)
        assert mosaic.status_summary.ready == 1
        assert mosaic.status_summary.preprocessing == 1

    def test_status_summary_absent_is_none(self):
        data = _mosaic_data()
        assert "status_summary" not in data
        mosaic = MosaicReturnSchema.from_dict(data)
        assert mosaic.status_summary is None


# ====== Per-image status (mosaic /status endpoint) ====== #

class TestImageStatusSchema:
    def test_status_enum_parsed(self):
        st = ImageStatusSchema.from_dict(_status_image(preprocessing_status="FAILED",
                                                       preprocessing_error="boom"))
        assert st.preprocessing_status is PreprocessingStatus.failed
        assert st.is_failed
        assert st.preprocessing_error == "boom"

    def test_id_alias_matches_image_id(self):
        """Status rows expose .id so they share the selection/delete contract with full images."""
        st = ImageStatusSchema.from_dict(_status_image())
        assert st.id == st.image_id
        assert hasattr(st, "filename")

    def test_uploaded_at_parsed(self):
        st = ImageStatusSchema.from_dict(_status_image())
        assert isinstance(st.uploaded_at, datetime)


class TestMosaicStatusResponse:
    def test_non_ready_images_flags_by_status(self):
        """non_ready is keyed on preprocessing_status (matching the mosaic badge buckets)."""
        data = {
            "mosaic_id": "11111111-2222-3333-4444-555555555555",
            "total_images": 4,
            "ready_images": 2, "pending_images": 1, "in_progress_images": 0,
            "failed_images": 1, "tiles_ready_images": 2,
            "images": [
                _status_image(image_id="1", preprocessing_status="NONE", data_available=True),
                _status_image(image_id="2", preprocessing_status="COMPLETED", data_available=True),
                _status_image(image_id="3", preprocessing_status="PENDING", data_available=False),
                _status_image(image_id="4", preprocessing_status="FAILED", data_available=False),
            ],
        }
        resp = MosaicStatusResponse.from_dict(data)
        ids = {s.id for s in resp.non_ready_images()}
        assert ids == {"3", "4"}  # NONE and COMPLETED are ready

    def test_empty_images(self):
        resp = MosaicStatusResponse.from_dict(
            {"mosaic_id": "11111111-2222-3333-4444-555555555555"})
        assert resp.images == []
        assert resp.non_ready_images() == []


# ====== Selection/delete contract (both row types) ====== #

class TestRowContract:
    def test_full_and_status_rows_share_id_and_filename(self):
        full = ImageReturnSchema.from_dict(_image_data())
        status = ImageStatusSchema.from_dict(_status_image())
        for row in (full, status):
            assert hasattr(row, "id")
            assert hasattr(row, "filename")


# ====== Status API URLs ====== #

class TestStatusApiUrls:
    def _api(self, http_mock):
        from mapflow.functional.api.data_catalog_api import DataCatalogApi
        return DataCatalogApi(
            http=http_mock,
            server="https://whitemaps.mapflow.ai/rest",
            dlg=MagicMock(),
            iface=MagicMock(),
            result_loader=MagicMock(),
            plugin_version="1.0.0",
        )

    def test_get_mosaic_status_url(self, http_mock):
        api = self._api(http_mock)
        mosaic_id = "11111111-2222-3333-4444-555555555555"
        api.get_mosaic_status(mosaic_id=mosaic_id, callback=MagicMock(), error_handler=MagicMock())
        http_mock.get.assert_called_once()
        url = http_mock.get.call_args.kwargs.get("url", "")
        assert f"/rasters/mosaic/{mosaic_id}/status" in url

    def test_delete_failed_images_url(self, http_mock):
        api = self._api(http_mock)
        mosaic_id = "11111111-2222-3333-4444-555555555555"
        api.delete_failed_images(mosaic_id=mosaic_id, callback=MagicMock())
        http_mock.delete.assert_called_once()
        url = http_mock.delete.call_args.kwargs.get("url", "")
        assert f"/rasters/mosaic/{mosaic_id}/failed" in url


# ====== Mosaic status counts → pictogram text ====== #

class TestStatusSummaryText:
    def _text(self, summary):
        # _status_summary_text does not use instance state; call it unbound with a dummy self.
        from mapflow.functional.view.data_catalog_view import DataCatalogView
        return DataCatalogView._status_summary_text(object(), summary)

    def test_none_summary_is_blank(self):
        assert self._text(None) == ""

    def test_ready_only_hides_pending_and_failed(self):
        from mapflow.functional.view import data_catalog_view as v
        s = MosaicStatusSummary.from_dict({"ready": 7, "pending": 0, "in_progress": 0, "failed": 0})
        text = self._text(s)
        assert "7" in text
        assert v.STATUS_OK_ICON in text
        # No pending/failed segments when their counts are zero
        assert v.STATUS_PENDING_ICON not in text
        assert v.STATUS_FAILED_ICON not in text

    def test_shows_pending_and_failed_when_present(self):
        s = MosaicStatusSummary.from_dict({"ready": 7, "pending": 1, "in_progress": 0, "failed": 2})
        text = self._text(s)
        assert "7" in text and "1" in text and "2" in text


# ====== Image list signature (poll change detection) ====== #

class TestImageSignature:
    def test_signature_stable_when_unchanged(self):
        from mapflow.functional.service.data_catalog import DataCatalogService
        images = [ImageReturnSchema.from_dict(_image_data(id="a"))]
        statuses = [ImageStatusSchema.from_dict(_status_image(image_id="b"))]
        sig1 = DataCatalogService._image_signature("m1", images, statuses)
        sig2 = DataCatalogService._image_signature("m1", list(images), list(statuses))
        assert sig1 == sig2

    def test_signature_changes_when_status_changes(self):
        from mapflow.functional.service.data_catalog import DataCatalogService
        images = [ImageReturnSchema.from_dict(_image_data(id="a"))]
        pending = [ImageStatusSchema.from_dict(_status_image(image_id="b", preprocessing_status="PENDING"))]
        failed = [ImageStatusSchema.from_dict(_status_image(image_id="b", preprocessing_status="FAILED"))]
        sig_pending = DataCatalogService._image_signature("m1", images, pending)
        sig_failed = DataCatalogService._image_signature("m1", images, failed)
        assert sig_pending != sig_failed


# ====== Full load chain: /image then /status, statuses reach the view ====== #

def _bare_service():
    """A DataCatalogService with __init__ bypassed and collaborators mocked."""
    from mapflow.functional.service.data_catalog import DataCatalogService
    svc = DataCatalogService.__new__(DataCatalogService)
    svc.api = MagicMock()
    svc.view = MagicMock()
    svc.view.mosaic_table_visible = False  # skip the preview branch
    svc.app_context = MagicMock()
    svc.dlg = MagicMock()
    svc.dlg.settings.value.return_value = "false"  # hideUnprocessedImages off
    svc._status_poll_timer = MagicMock()
    svc._polling_mosaic_id = None
    svc._last_image_signature = None
    svc.images = []
    svc.image_statuses = []
    svc.preview_idx = 0
    return svc


def _response(payload):
    resp = MagicMock()
    resp.readAll.return_value.data.return_value = json.dumps(payload).encode()
    return resp


class TestLoadChain:
    def test_status_request_is_sent_after_images(self):
        svc = _bare_service()
        image_list = [_image_data(id="ready-1"), _image_data(id="ready-2")]
        svc._on_mosaic_images_loaded(_response(image_list), mosaic_id="m1", is_poll=False)
        # The /image callback must chain a /status request for the same mosaic.
        svc.api.get_mosaic_status.assert_called_once()
        assert svc.api.get_mosaic_status.call_args.kwargs["mosaic_id"] == "m1"

    def test_non_ready_rows_reach_the_view(self):
        svc = _bare_service()
        image_list = [_image_data(id="ready-1")]  # /image returns only the ready one
        svc._on_mosaic_images_loaded(_response(image_list), mosaic_id="m1", is_poll=False)
        status_callback = svc.api.get_mosaic_status.call_args.kwargs["callback"]

        status_payload = {
            "mosaic_id": "m1",
            "total_images": 2,
            "ready_images": 1, "pending_images": 1, "in_progress_images": 0,
            "failed_images": 0, "tiles_ready_images": 1,
            "images": [
                _status_image(image_id="ready-1", preprocessing_status="COMPLETED",
                              data_available=True),
                _status_image(image_id="pending-1", filename="pending.tif",
                              preprocessing_status="PENDING", data_available=False),
            ],
        }
        status_callback(_response(status_payload))

        svc.view.display_images.assert_called_once()
        rendered_images, rendered_statuses = svc.view.display_images.call_args.args
        assert [i.id for i in rendered_images] == ["ready-1"]
        assert [s.filename for s in rendered_statuses] == ["pending.tif"]

    def test_available_but_pending_image_is_not_duplicated(self):
        """A data_available image that is still PENDING appears once (flagged), not twice."""
        svc = _bare_service()
        # /image returns both the ready one and the still-pending-but-available one
        image_list = [_image_data(id="ready-1"), _image_data(id="dup-pending")]
        svc._on_mosaic_images_loaded(_response(image_list), mosaic_id="m1", is_poll=False)
        status_callback = svc.api.get_mosaic_status.call_args.kwargs["callback"]
        status_payload = {
            "mosaic_id": "m1",
            "total_images": 2,
            "ready_images": 1, "pending_images": 1, "in_progress_images": 0,
            "failed_images": 0, "tiles_ready_images": 1,
            "images": [
                _status_image(image_id="ready-1", preprocessing_status="COMPLETED", data_available=True),
                _status_image(image_id="dup-pending", filename="dup.tif",
                              preprocessing_status="PENDING", data_available=True),
            ],
        }
        status_callback(_response(status_payload))
        rendered_images, rendered_statuses = svc.view.display_images.call_args.args
        assert [i.id for i in rendered_images] == ["ready-1"]        # dup removed from ready list
        assert [s.id for s in rendered_statuses] == ["dup-pending"]  # shown once, flagged

    def test_status_failure_falls_back_to_ready_only(self):
        svc = _bare_service()
        image_list = [_image_data(id="ready-1")]
        svc._on_mosaic_images_loaded(_response(image_list), mosaic_id="m1", is_poll=False)
        error_handler = svc.api.get_mosaic_status.call_args.kwargs["error_handler"]
        error_handler(_response({"detail": "not found"}))
        svc.view.display_images.assert_called_once()
        _, rendered_statuses = svc.view.display_images.call_args.args
        assert rendered_statuses == []


def _open_mosaic(image_list, status_images):
    """Drive the full open-mosaic chain (/image then /status) and return the service."""
    svc = _bare_service()
    svc._on_mosaic_images_loaded(_response(image_list), mosaic_id="m1", is_poll=False)
    callback = svc.api.get_mosaic_status.call_args.kwargs["callback"]
    payload = {
        "mosaic_id": "m1", "total_images": len(status_images),
        "ready_images": 0, "pending_images": 0, "in_progress_images": 0,
        "failed_images": 0, "tiles_ready_images": 0, "images": status_images,
    }
    callback(_response(payload))
    return svc


class TestOpenMosaicStates:
    """Opening a mosaic must not crash and must flag rows for edge compositions."""

    def test_only_failed(self):
        svc = _open_mosaic(
            image_list=[],  # no ready images
            status_images=[_status_image(image_id="f1", filename="f1.tif",
                                         preprocessing_status="FAILED", data_available=False)],
        )
        rendered_images, rendered_statuses = svc.view.display_images.call_args.args
        assert rendered_images == []
        assert [s.id for s in rendered_statuses] == ["f1"]
        svc.view.set_failed_images_present.assert_called_with(True)

    def test_only_in_progress(self):
        svc = _open_mosaic(
            image_list=[],
            status_images=[_status_image(image_id="p1", filename="p1.tif",
                                         preprocessing_status="IN_PROGRESS", data_available=False)],
        )
        rendered_images, rendered_statuses = svc.view.display_images.call_args.args
        assert rendered_images == []
        assert [s.id for s in rendered_statuses] == ["p1"]
        svc.view.set_failed_images_present.assert_called_with(False)  # no failed → no bulk button

    def test_mix_ready_pending_failed(self):
        svc = _open_mosaic(
            image_list=[_image_data(id="r1")],
            status_images=[
                _status_image(image_id="r1", preprocessing_status="COMPLETED", data_available=True),
                _status_image(image_id="p1", preprocessing_status="PENDING", data_available=False),
                _status_image(image_id="ip1", preprocessing_status="IN_PROGRESS", data_available=False),
                _status_image(image_id="f1", preprocessing_status="FAILED", data_available=False),
            ],
        )
        rendered_images, rendered_statuses = svc.view.display_images.call_args.args
        assert [i.id for i in rendered_images] == ["r1"]
        assert {s.id for s in rendered_statuses} == {"p1", "ip1", "f1"}
        svc.view.set_failed_images_present.assert_called_with(True)

    def test_empty_mosaic(self):
        svc = _open_mosaic(image_list=[], status_images=[])
        rendered_images, rendered_statuses = svc.view.display_images.call_args.args
        assert rendered_images == []
        assert rendered_statuses == []
        svc.view.set_failed_images_present.assert_called_with(False)


class TestSelectedReadyImage:
    def test_non_ready_selection_is_ignored(self):
        """A selected preprocessing/failed image must not be treated as usable imagery
        (guards area/AOI code that reads .footprint)."""
        svc = _bare_service()
        ready = ImageReturnSchema.from_dict(_image_data(id="r"))
        failed = ImageStatusSchema.from_dict(_status_image(image_id="f", preprocessing_status="FAILED"))
        svc.images = [ready]
        svc.image_statuses = [failed]

        svc.view.selected_images_indecies.return_value = ["f"]  # only the failed row selected
        assert svc.selected_ready_image() is None

        svc.view.selected_images_indecies.return_value = ["r"]
        assert svc.selected_ready_image() is ready
