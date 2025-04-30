from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QDialogButtonBox, QAbstractItemView, QListWidgetItem
from qgis.core import QgsMapLayerProxyModel

from .icons import plugin_icon

ui_path = Path(__file__).parent/'static'/'ui'


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
            self.tr('"><span style=" text-decoration: underline; color:#0057ae;">Let us know</span></a></p></body></html>')
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


class UploadRasterLayersDialog(*uic.loadUiType(ui_path / 'raster_layers_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        """Dialog for choosing raster layer(s) when uploading image to mosaic."""
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(plugin_icon)
        
    def setup(self, layers):
        self.setWindowTitle(self.tr("Choose raster layers to upload to imagery collection"))
        for layer in layers:
            item_to_add = QListWidgetItem()
            item_to_add.setText(layer.name())
            item_to_add.setData(Qt.UserRole, layer.source()) 
            self.listWidget.addItem(item_to_add)
        self.listWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)    
        self.exec() 

    def get_selected_rasters_list(self, callback):
        # Get selected layers' paths
        layers_paths = []
        for item in self.listWidget.selectedItems():
            layers_paths.append(item.data(Qt.UserRole))
        # Run service.upload_raster_layers_to_mosaic
        callback(layers_paths)


class ConfirmProcessingStart(*uic.loadUiType(ui_path / 'processing_start_confirmation.ui')):
    def __init__(self, parent: QWidget) -> None:
        """A confirmation dialog for processing start with 'don't show again' checkbox, connected to Settings tab."""
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(plugin_icon)
        self.setWindowTitle(self.tr("Confirm processing start"))
    
    def setup(self, name, price, provider, zoom, area, model, blocks) -> None:
        elided_name = self.modelLabel.fontMetrics().elidedText(name, Qt.ElideRight, self.nameLabel.width() + 100)
        self.nameLabel.setText(elided_name)
        if price is not None:
            self.priceHeader.setVisible(True)
            self.priceLabel.setVisible(True)
            self.priceLabel.setText(price)
        else:
            self.priceHeader.setVisible(False)
            self.priceLabel.setVisible(False)
        elided_provider = self.dataSourceLabel.fontMetrics().elidedText(provider, Qt.ElideRight, self.modelLabel.width() + 150)
        self.dataSourceLabel.setText(elided_provider)
        if not zoom:
            zoom = "No zoom selected"
        self.zoomLabel.setText(zoom)
        self.areaLabel.setText(area)
        elided_model = self.modelLabel.fontMetrics().elidedText(model, Qt.ElideRight, self.modelLabel.width() + 100)
        self.modelLabel.setText(elided_model)
        if len(blocks) == 0:
            blocks = ["No options selected"]
        else:
            blocks = [block.text() for block in blocks if block.isChecked()]
        self.modelOptionsLabel.setText(', \n'.join(blocks))
        self.exec() 
