from pathlib import Path

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QDialogButtonBox
from qgis.core import QgsMapLayerProxyModel
from .icons import plugin_icon

ui_path = Path(__file__).parent/'static'/'ui'


class LoginDialog(*uic.loadUiType(ui_path/'login_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        """Auth dialog."""
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(plugin_icon)


class ErrorMessageWidget(*uic.loadUiType(ui_path / 'error_message.ui')):
    def __init__(self, parent: QWidget, text: str, title: str = None, email_body: str = '') -> None:
        """A message box notifying user about a plugin error, with a 'Send a report' button."""
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(plugin_icon)
        self.text.setText(text)
        if title:
            self.title.setText(title)
        self.mailTo.setText(
            '<html><head/><body><p><a href="mailto:help@geoalert.io?subject=Mapflow-QGIS&body=' +
            email_body +
            '"><span style=" text-decoration: underline; color:#0057ae;">Let us know</span></a></p></body></html>'
        )


class ReviewDialog(*uic.loadUiType(ui_path/'review_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        """Auth dialog."""
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(plugin_icon)
        self.reviewLayerCombo.setFilters(QgsMapLayerProxyModel.HasGeometry)
        self.reviewLayerCombo.setAllowEmptyLayer(True)

        self.processing = None

    def setup(self, processing):
        self.processing = processing
        self.setWindowTitle(self.tr("Review {processing}").format(processing=processing.name))
        self.reviewLayerCombo.setCurrentIndex(0)
        ok = self.buttonBox.button(QDialogButtonBox.Ok)
        ok.setEnabled(self.review_submit_allowed())
        # Enabled only if the text is entered
        self.reviewComment.textChanged.connect(lambda: ok.setEnabled(self.review_submit_allowed()))
        self.reviewLayerCombo.layerChanged.connect(lambda: ok.setEnabled(self.review_submit_allowed()))

    def review_submit_allowed(self):
        text_ok = self.reviewComment.toPlainText() != ""
        # Not check geometry yet
        geometry_ok = True
        return text_ok and geometry_ok