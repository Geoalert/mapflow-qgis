from PyQt5.QtWidgets import QProgressBar


class UploadProgressReporter:
    """Shows a raster upload's progress in the QGIS message bar.

    This is the widget half of `DataCatalogApi`'s uploads. It lives in the view layer, which may
    hold Qt widgets, and is injected into the api (which may not) as a plain collaborator — the api
    hands over the reply and a label, and this attaches a progress bar to it. Uploads run one at a
    time (the service recurses through the images), so one bar is tracked at a time.
    """

    def __init__(self, iface):
        self.iface = iface

    def track(self, response, message: str) -> None:
        """Attach a progress bar to `response`'s upload, labelled `message`."""
        message_bar = self.iface.messageBar().createMessage(message)
        progress = QProgressBar()
        message_bar.layout().addWidget(progress)
        self.iface.messageBar().pushWidget(message_bar)

        def on_progress(bytes_sent: int, bytes_total: int):
            try:
                progress.setValue(round(bytes_sent / bytes_total * 100))
            except ZeroDivisionError:
                return
            if bytes_total > 0 and bytes_sent == bytes_total:
                self.iface.messageBar().popWidget(message_bar)

        connection = response.uploadProgress.connect(on_progress)
        message_bar.destroyed.connect(lambda: response.uploadProgress.disconnect(connection))
