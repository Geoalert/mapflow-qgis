"""QGIS-tier tests: DataCatalogApi reports and shows progress without holding a widget (error-
reporting phase, MR-3).

The api built `ErrorMessageWidget` in six places and a `QProgressBar` in two — the last widget
construction below the controller layer. The error handlers now call `show_error_report` in
`mapflow.infra`; the upload progress is delegated to an injected view-layer reporter. With no
QtWidgets or dialog imports left, the api's two allowlist entries clear and `ALLOWED` is empty.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from PyQt5.QtCore import QObject
from PyQt5.QtNetwork import QNetworkRequest

from mapflow.functional.api import data_catalog_api as api_module
from mapflow.functional.api.data_catalog_api import DataCatalogApi


def _api():
    api = DataCatalogApi.__new__(DataCatalogApi)
    QObject.__init__(api)
    api.tr = lambda text: text
    api.plugin_version = "9.9.9"
    api.progress_reporter = None
    return api


# ---------- the error handlers report through infra, not a dialog ----------

def test_a_delete_failure_is_reported_with_its_message():
    api = _api()

    with patch.object(api_module, "show_error_report") as report:
        api.delete_mosaic_error_handler(["North field"])

    report.assert_called_once()
    assert "North field" in report.call_args.kwargs["text"]


def test_a_download_404_reports_the_not_found_message():
    api = _api()
    response = MagicMock()
    response.readAll.return_value.data.return_value = b"{}"
    response.attribute.return_value = 404  # HttpStatusCodeAttribute

    with patch.object(api_module, "show_error_report") as report:
        api.download_image_error_handler(response)

    assert "don't have access" in report.call_args.kwargs["text"]
    assert report.call_args.kwargs["title"] == "Download error"


def test_a_mosaic_extent_failure_reports_and_carries_the_collection_id():
    api = _api()
    api.iface = MagicMock()
    api.result_loader = MagicMock()
    response = MagicMock()
    response.error.return_value = 99  # not NoError

    with patch.object(api_module, "show_error_report") as report:
        api.add_mosaic_with_extent(response, layer=MagicMock(), errors=False, mosaic_id="m-1")

    assert "m-1" in report.call_args.kwargs["email_body"]


# ---------- upload progress is delegated to the injected reporter ----------

def test_an_upload_delegates_progress_to_the_reporter():
    api = _api()
    api.server = "https://example.com/rest"
    response = MagicMock()
    api.http = MagicMock()
    api.http.post.return_value = response
    api.progress_reporter = MagicMock()

    with patch.object(api_module.DataCatalogApi, "create_upload_image_body", return_value=MagicMock()):
        api.upload_image(mosaic_id="m-1", image_path="/tmp/x.tif",
                         image_number=2, image_count=5)

    api.progress_reporter.track.assert_called_once()
    assert api.progress_reporter.track.call_args.args[0] is response
    assert "2/5" in api.progress_reporter.track.call_args.args[1]


def test_an_upload_without_a_reporter_still_uploads():
    """The reporter is injected after construction; an upload before it exists must not crash."""
    api = _api()
    api.server = "https://example.com/rest"
    api.http = MagicMock()
    api.progress_reporter = None

    with patch.object(api_module.DataCatalogApi, "create_upload_image_body", return_value=MagicMock()):
        api.upload_image(mosaic_id="m-1", image_path="/tmp/x.tif")

    api.http.post.assert_called_once()
