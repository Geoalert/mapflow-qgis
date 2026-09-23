"""QGIS-tier test for the upload-progress reporter that left DataCatalogApi (error-reporting MR-3).

The api may hold no widget, so the message-bar progress bar moved to this view-layer helper, injected
into the api. It shows a bar for an upload and removes it when the bytes complete.
"""
from unittest.mock import MagicMock

from mapflow.functional.view.upload_progress import UploadProgressReporter


def test_track_pushes_a_progress_bar_and_wires_the_reply():
    iface = MagicMock()
    reporter = UploadProgressReporter(iface)
    response = MagicMock()

    reporter.track(response, "Uploading image 1/3:")

    iface.messageBar().createMessage.assert_called_once_with("Uploading image 1/3:")
    iface.messageBar().pushWidget.assert_called_once()
    response.uploadProgress.connect.assert_called_once()


def test_the_bar_is_removed_when_the_upload_completes():
    iface = MagicMock()
    reporter = UploadProgressReporter(iface)
    response = MagicMock()

    reporter.track(response, "Uploading image 1/1:")
    on_progress = response.uploadProgress.connect.call_args.args[0]

    on_progress(50, 100)     # mid-upload: bar stays
    iface.messageBar().popWidget.assert_not_called()

    on_progress(100, 100)    # complete: bar removed
    iface.messageBar().popWidget.assert_called_once()


def test_zero_total_does_not_divide_by_zero():
    reporter = UploadProgressReporter(MagicMock())
    response = MagicMock()
    reporter.track(response, "Uploading:")
    on_progress = response.uploadProgress.connect.call_args.args[0]

    on_progress(0, 0)  # must not raise
