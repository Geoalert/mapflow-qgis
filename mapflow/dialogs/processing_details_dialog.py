from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QWidget

from .processing_dialog import plugin_icon, ui_path
from .icons import options_icon
from ..schema import DataProviderParams, MyImageryParams, ImagerySearchParams, UserDefinedParams

class ProcessingDetailsDialog(*uic.loadUiType(ui_path / 'processing_details.ui')):
    def __init__(self, parent: QWidget) -> None:
        """A dialog with processing infromation and the ability to switch to provider or my imagery."""
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(plugin_icon)
        self.setWindowTitle(self.tr("Processing details"))
    
    def setup(self, processing, zoom_selector, error) -> None:
        self.toSourceButton.setIcon(options_icon)
        # Hide zoom
        self.zoomLabel.setVisible(False)
        self.zoomInfo.setVisible(False)
        # Set name
        self.nameInfo.setText(processing.name)
        # Set id
        self.idInfo.setText(processing.id_)
        # Set description 
        if processing.description:
            self.descriptionLabel.setVisible(True)
            self.descriptionInfo.setVisible(True)
            self.descriptionInfo.setText(processing.description)
        else:
            self.descriptionLabel.setVisible(False)
            self.descriptionInfo.setVisible(False)
        # Set status
        self.statusInfo.setText(processing.status.value)
        # Set data provider
        source_params = processing.params.sourceParams
        if isinstance(source_params, DataProviderParams):
            provider = source_params.dataProvider.providerName # display name
            if zoom_selector:
                self.show_zoom(source_params.dataProvider.zoom)
            self.toSourceButton.setVisible(False)
        elif isinstance(source_params, ImagerySearchParams):
            provider = source_params.imagerySearch.dataProvider # display name
            self.toSourceButton.setVisible(False)
            if zoom_selector:
                self.show_zoom(source_params.imagerySearch.zoom)
        elif isinstance(source_params, MyImageryParams):
            provider = self.tr("My imagery") # display 'My imagery' + button
            if zoom_selector:
                self.show_zoom(0)
            self.toSourceButton.setVisible(True)
        elif isinstance(source_params, UserDefinedParams):
            provider = source_params.userDefined.url # display url + button
            if zoom_selector:
                self.show_zoom(source_params.userDefined.zoom)
            self.toSourceButton.setVisible(True)
        else:
            provider = source_params # display "Unidentified"
        self.providerInfo.setText(str(provider))
        self.providerInfo.setFixedWidth(self.providerInfo.sizeHint().width())
        # Set model
        self.modelInfo.setText(processing.workflow_def)
        # Set model options
        if processing.blocks: 
            blocks = ", \n".join(block.name for block in processing.blocks if block.enabled)
            if blocks:
                self.optionsLabel.setVisible(True)
                self.optionsInfo.setVisible(True)
                self.optionsInfo.setText(blocks)
            else:
                self.optionsLabel.setVisible(False)
                self.optionsInfo.setVisible(False)
        else:
            self.optionsLabel.setVisible(False)
            self.optionsInfo.setVisible(False)
        # Set error
        if error:
            self.errorLabel.setVisible(True)
            self.errorInfo.setVisible(True)
            self.errorInfo.setText(error)
        else:
            self.errorLabel.setVisible(False)
            self.errorInfo.setVisible(False)
        widgets = [self.gridLayout.itemAt(i).widget() for i in range(self.gridLayout.count())]
        for widget in widgets:
            if isinstance(widget, QLabel):
                widget.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.adjustSize()
        self.exec()

    def show_zoom(self, zoom):
        if zoom:
            self.zoomLabel.setVisible(True)
            self.zoomInfo.setVisible(True)
            self.zoomInfo.setText(str(zoom))
