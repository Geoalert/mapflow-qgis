"""Tests for data catalog API, schema, and download feature.

Spec reference: spec/002_C_myimagery_api.md
"""
import gc
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import MagicMock
from datetime import datetime, timedelta

import pytest
from PyQt5.QtCore import QCoreApplication
from qgis.core import QgsNetworkAccessManager

from mapflow.functional.app_context import AppContext
from mapflow.functional.service import data_catalog
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


# ====== Image download to disk (spec/002_C § Client-side download) ====== #

FIRST_CHUNK = 256 * 1024
PAYLOAD = bytes(range(256)) * 4096  # 1 MiB; position-dependent, so a lost or reordered chunk shows


class _ImageServer:
    """A local stand-in for the presigned S3 URL, serving PAYLOAD in one of several modes."""

    def __init__(self, mode):
        self.mode = mode
        self.requests = 0
        self.release = threading.Event()  # 'hold' mode sends the rest of the body once this is set
        server = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                server.requests += 1
                if server.mode == "forbidden":
                    body = b"<Error><Code>AccessDenied</Code></Error>"
                    self.send_response(403)
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
                self.send_response(200)
                self.send_header("Content-Length", str(len(PAYLOAD)))
                self.end_headers()
                if server.mode == "ok":
                    self.wfile.write(PAYLOAD)
                    return
                self.wfile.write(PAYLOAD[:FIRST_CHUNK])
                self.wfile.flush()
                if server.mode == "hold":
                    server.release.wait(10)
                    self.wfile.write(PAYLOAD[FIRST_CHUNK:])
                # 'drop' returns with the body incomplete, and the connection closes

            def log_message(self, *args):
                pass

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_port}/image.tif"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self):
        self.release.set()
        self.httpd.shutdown()
        self.httpd.server_close()


@pytest.fixture()
def image_server():
    servers = []

    def start(mode):
        servers.append(_ImageServer(mode))
        return servers[-1]

    yield start
    for server in servers:
        server.close()


@pytest.fixture()
def service(monkeypatch):
    """A DataCatalogService built by its real constructor, downloading through QGIS's network manager."""
    monkeypatch.setattr(data_catalog, "DataCatalogApi", MagicMock())
    monkeypatch.setattr(data_catalog, "DataCatalogView", MagicMock())  # the real alert() blocks on a modal box
    svc = data_catalog.DataCatalogService(http=MagicMock(), server="https://example.com", dlg=MagicMock(),
                                          iface=MagicMock(), result_loader=MagicMock(), plugin_version="test",
                                          app_context=AppContext())
    svc.api.http.nam = QgsNetworkAccessManager.instance()
    return svc


def _wait_until(condition, timeout=10.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        QCoreApplication.processEvents()
        if condition():
            return True
        time.sleep(0.01)
    return False


def _finished(svc):
    return svc.view.alert.called or svc.iface.messageBar().pushMessage.called


def _bytes_on_disk(directory):
    return sum(path.stat().st_size for path in directory.iterdir() if path.is_file())


class TestImageDownloadToDisk:
    def test_saves_the_served_bytes_and_reports_the_path(self, service, image_server, tmp_path):
        server = image_server("ok")
        target = tmp_path / "image.tif"

        service._download_file_from_url(server.url, str(target))

        assert _wait_until(lambda: _finished(service)), "the download never completed"
        service.view.alert.assert_not_called()
        assert target.read_bytes() == PAYLOAD
        assert str(target) in service.iface.messageBar().pushMessage.call_args.args[1]
        assert [path.name for path in tmp_path.iterdir()] == ["image.tif"]  # no temporary file left behind

    def test_streams_to_disk_while_downloading(self, service, image_server, tmp_path):
        server = image_server("hold")  # sends FIRST_CHUNK of the body, then waits for release
        target = tmp_path / "image.tif"

        service._download_file_from_url(server.url, str(target))

        # Mid-download, what has arrived is already on disk rather than held in memory, and the
        # target itself is not there yet: it is only replaced once the download succeeds.
        assert _wait_until(lambda: _bytes_on_disk(tmp_path) >= FIRST_CHUNK // 2), \
            "no data reached the disk while the download was in flight"
        assert not target.exists()

        server.release.set()
        assert _wait_until(lambda: _finished(service)), "the download never completed"
        assert target.read_bytes() == PAYLOAD

    def test_completes_when_garbage_collection_runs_mid_download(self, service, image_server, tmp_path):
        # Regression: the `finished` slot was a lambda capturing its own reply. PyQt lets the cyclic GC
        # see that as a reply <-> lambda cycle with nothing else holding it, so a GC pass mid-download
        # tore the slot down: the image was silently never saved, or QGIS crashed when it finished.
        server = image_server("hold")
        target = tmp_path / "image.tif"

        service._download_file_from_url(server.url, str(target))
        assert _wait_until(lambda: server.requests == 1)
        gc.collect()
        server.release.set()

        assert _wait_until(lambda: _finished(service)), "the download's completion was lost"
        assert target.read_bytes() == PAYLOAD

    def test_http_error_keeps_the_existing_file(self, service, image_server, tmp_path):
        server = image_server("forbidden")  # e.g. an expired presigned URL
        target = tmp_path / "image.tif"
        target.write_bytes(b"previous image")

        service._download_file_from_url(server.url, str(target))

        assert _wait_until(lambda: _finished(service))
        service.iface.messageBar().pushMessage.assert_not_called()
        assert "Failed to download image" in service.view.alert.call_args.args[0]
        assert target.read_bytes() == b"previous image"
        assert [path.name for path in tmp_path.iterdir()] == ["image.tif"]

    def test_interrupted_download_leaves_no_partial_file(self, service, image_server, tmp_path):
        server = image_server("drop")  # closes the connection after FIRST_CHUNK of the body
        target = tmp_path / "image.tif"

        service._download_file_from_url(server.url, str(target))

        assert _wait_until(lambda: _finished(service))
        service.iface.messageBar().pushMessage.assert_not_called()
        assert "Failed to download image" in service.view.alert.call_args.args[0]
        assert list(tmp_path.iterdir()) == []

    def test_unwritable_target_is_reported_without_downloading(self, service, image_server, tmp_path):
        server = image_server("ok")
        target = tmp_path / "no-such-dir" / "image.tif"

        service._download_file_from_url(server.url, str(target))
        _wait_until(lambda: server.requests > 0, timeout=1.0)

        assert server.requests == 0, "a download was started for a target that cannot be written"
        assert "Failed to save file" in service.view.alert.call_args.args[0]
