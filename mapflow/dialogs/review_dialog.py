from pathlib import Path

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QDialogButtonBox
from qgis.core import QgsMapLayerProxyModel

from .icons import plugin_icon

ui_path = Path(__file__).parent/'static'/'ui'


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