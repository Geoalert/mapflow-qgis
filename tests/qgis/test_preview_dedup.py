"""QGIS-tier tests for search-preview de-duplication.

A preview layer is added only in the async HTTP callback, so a rapid second click / double-click
on the Preview cell used to start several downloads (the on-map dedupe guard saw nothing yet) and
add several duplicate preview layers. An in-flight guard (``_pending_preview_ids``) prevents a
second download for an image whose preview is already being fetched; it is cleared on success and
on error so the image can be previewed again afterwards."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.mapflow import Mapflow


def _plugin():
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda t: t
    plugin.app_context = SimpleNamespace(project=MagicMock())
    plugin.app_context.project.mapLayersByName.return_value = []  # nothing on the map yet
    plugin.metadata_feature = MagicMock(return_value=MagicMock())  # feature exists
    plugin.preview_png = MagicMock()
    plugin._pending_preview_ids = set()
    return plugin


def test_preview_catalog_skips_when_download_in_flight():
    plugin = _plugin()
    plugin._pending_preview_ids = {"IMG-1"}  # a download for this image is already running

    plugin.preview_catalog("IMG-1")

    plugin.preview_png.assert_not_called()  # no second download started


def test_display_png_preview_gcp_clears_in_flight_flag():
    plugin = _plugin()
    plugin._pending_preview_ids = {"IMG-1"}
    plugin.result_loader = MagicMock()
    plugin.result_loader.display_preview_with_gcp.return_value = None
    plugin.processing_service = SimpleNamespace(in_template_mode=False)
    plugin._relocate_preview_to_template_group = MagicMock()

    plugin.display_png_preview_gcp(response=MagicMock(), footprint=MagicMock(), image_id="IMG-1")

    assert "IMG-1" not in plugin._pending_preview_ids  # cleared -> image can be previewed again


def test_error_handler_clears_in_flight_flag():
    plugin = _plugin()
    plugin._pending_preview_ids = {"IMG-1"}
    plugin.report_http_error = MagicMock()

    plugin.preview_png_error_handler(MagicMock(), image_id="IMG-1")

    assert "IMG-1" not in plugin._pending_preview_ids
    plugin.report_http_error.assert_called_once()


# ---------- My Imagery preview auth (§2.3): forward the token to the Mapflow host only ----------

def _auth_plugin():
    plugin = Mapflow.__new__(Mapflow)
    plugin.app_context = SimpleNamespace(server="https://whitemaps-v2.mapflow.ai/rest")
    return plugin


def test_preview_auth_forwards_token_for_same_host_url():
    plugin = _auth_plugin()
    # My Imagery preview lives on the Mapflow host -> None lets Http.authorize apply the real token.
    url = "https://whitemaps-v2.mapflow.ai/rest/rasters/image/abc/preview/l"

    assert plugin._preview_auth_override(url) is None


def test_preview_auth_uses_dummy_header_for_external_host():
    plugin = _auth_plugin()
    # External pre-signed preview host -> must NOT leak Mapflow credentials.
    url = "https://api.sdstream.net/preview/comm/abc123"

    assert plugin._preview_auth_override(url) == b'null'


def test_preview_auth_defaults_to_no_credentials_on_bad_url():
    plugin = _auth_plugin()

    assert plugin._preview_auth_override("::not a url::") == b'null'
