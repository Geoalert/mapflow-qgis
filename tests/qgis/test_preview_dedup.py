"""QGIS-tier tests for search-preview de-duplication.

A preview layer is added only in the async HTTP callback, so a rapid second click / double-click
on the Preview cell used to start several downloads (the on-map dedupe guard saw nothing yet) and
add several duplicate preview layers. An in-flight guard (``_pending_preview_ids``) prevents a
second download for an image whose preview is already being fetched; it is cleared on success and
on error so the image can be previewed again afterwards.

Owned by `PreviewService` since the preview extraction. The error path reports through the
message tier (`report_http_error`), which the service calls directly — `AlertService` owns the
report tier of `spec/006_error_reporting.md`, so a service does not need a dialog to reach it.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from mapflow.functional.service.preview_service import PreviewService


@pytest.fixture
def service():
    app_context = SimpleNamespace(project=MagicMock(), plugin_version="1.2.3")
    app_context.project.mapLayersByName.return_value = []  # nothing on the map yet
    service = PreviewService(iface=MagicMock(),
                             app_context=app_context,
                             http=MagicMock(),
                             plugin_dir="",
                             config=MagicMock(),
                             result_loader=MagicMock(),
                             processing_service=SimpleNamespace(in_template_mode=False,
                                                                active_template=None))
    service.metadata_feature = MagicMock(return_value=MagicMock())  # feature exists
    service.preview_png = MagicMock()
    return service


def test_preview_catalog_skips_when_download_in_flight(service):
    service._pending_preview_ids = {"IMG-1"}  # a download for this image is already running

    service.preview_catalog("IMG-1")

    service.preview_png.assert_not_called()  # no second download started


def test_display_png_preview_gcp_clears_in_flight_flag(service):
    service._pending_preview_ids = {"IMG-1"}
    service.result_loader.display_preview_with_gcp.return_value = None

    service.display_png_preview_gcp(response=MagicMock(), footprint=MagicMock(),
                                    image_id="IMG-1")

    assert "IMG-1" not in service._pending_preview_ids  # cleared -> previewable again


def test_error_handler_clears_in_flight_flag(service, monkeypatch):
    reported = MagicMock()
    monkeypatch.setattr("mapflow.functional.service.preview_service.report_http_error", reported)
    service._pending_preview_ids = {"IMG-1"}

    service.preview_png_error_handler(MagicMock(), image_id="IMG-1")

    assert "IMG-1" not in service._pending_preview_ids
    reported.assert_called_once()
