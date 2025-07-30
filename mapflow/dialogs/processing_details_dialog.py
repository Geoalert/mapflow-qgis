from PyQt5 import uic
from PyQt5.QtWidgets import QWidget

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
    
    def setup(self, processing, error) -> None:
        self.toSourceButton.setIcon(options_icon)
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
            provider = source_params.providerName # display name
            self.toSourceButton.setVisible(False)
        elif isinstance(source_params, ImagerySearchParams):
            provider = source_params.dataProvider # display name
            self.toSourceButton.setVisible(False)
        elif isinstance(source_params, MyImageryParams):
            provider = self.tr("My imagery") # display 'My imagery' + button
            self.toSourceButton.setVisible(True)
        elif isinstance(source_params, UserDefinedParams):
            provider = source_params.url # display url + button
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
        self.adjustSize()
        self.exec()
