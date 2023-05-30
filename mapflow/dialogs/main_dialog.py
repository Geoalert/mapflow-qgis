from pathlib import Path
from typing import Iterable, Optional

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QWidget, QPushButton
from qgis.core import QgsMapLayerProxyModel

from ..entity.billing import BillingType
from ..entity.provider import Provider
from ..functional import helpers
from .. import config

ui_path = Path(__file__).parent/'static'/'ui'
icon_path = Path(__file__).parent/'static'/'icons'
plugin_icon = QIcon(str(icon_path/'mapflow.png'))
coins_icon = QIcon(str(icon_path/'coins-solid.svg'))


class MainDialog(*uic.loadUiType(ui_path/'main_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        """Plugin's main dialog."""
        super().__init__(parent)
        self.setupUi(self)
        # Restrict combos to relevant layer types; QGIS 3.10-3.20 (at least) bugs up if set in .ui
        self.polygonCombo.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.rasterCombo.setFilters(QgsMapLayerProxyModel.RasterLayer)
        # Set icons (can be done in .ui but brings about the resources_rc import bug)
        self.setWindowIcon(plugin_icon)
        self.addProvider.setIcon(QIcon(str(icon_path/'add.svg')))
        self.removeProvider.setIcon(QIcon(str(icon_path/'remove_provider.svg')))
        self.editProvider.setIcon(QIcon(str(icon_path/'edit_provider.svg')))
        self.toolButton.setIcon(QIcon(str(icon_path/'add.svg')))
        self.billingHistoryButton.setIcon(QIcon(str(icon_path/'bar-chart-2.svg')))
        self.logoutButton.setIcon(QIcon(str(icon_path/'log-out.svg')))
        self.modelInfo.setIcon(QIcon(str(icon_path/'info.svg')))
        self.tabWidget.setTabIcon(1, QIcon(str(icon_path/'magnifying-glass-solid.svg')))
        self.tabWidget.setTabIcon(2, QIcon(str(icon_path/'user-gear-solid.svg')))
        self.tabWidget.setTabIcon(3, QIcon(str(icon_path/'info.svg')))

        coin_pixmap = QIcon(str(icon_path/'coins-solid.svg')).pixmap(16,16)
        self.labelCoins_1.setPixmap(coin_pixmap)

        self.modelInfo.clicked.connect(lambda: helpers.open_model_info(model_name=self.modelCombo.currentText()))
        self.topUpBalanceButton.clicked.connect(lambda: helpers.open_url(config.TOP_UP_URL))
        self.topUpBalanceButton_2.clicked.connect(lambda: helpers.open_url(config.TOP_UP_URL))
        self.billingHistoryButton.clicked.connect(lambda: helpers.open_url(config.BILLING_HISTORY_URL))


    # ========= SHOW =========== #
    def setup_for_billing(self, billing_type: BillingType):
        """
        set the UI elements according to user's billing type
        """
        if billing_type == billing_type.credits:
            self.balanceLabel.setVisible(True)
            self.labelWdPrice.setVisible(True)
            self.labelCoins_1.setVisible(True)
        elif billing_type == billing_type.area:
            self.balanceLabel.setVisible(True)
            self.labelCoins_1.setVisible(False)
            self.labelWdPrice.setVisible(False)
        else:  # None billing
            self.balanceLabel.setVisible(False)
            self.topUpBalanceButton.setVisible(False)
            self.labelCoins_1.setVisible(False)
            self.labelWdPrice.setVisible(False)

    def setup_imagery_search(self,
                             provider_name: str,
                             provider: Provider,
                             columns: Iterable,
                             hidden_columns: [Iterable[int]],
                             sort_by: str,
                             preview_zoom: int,
                             max_preview_zoom: int,
                             more_button_name: str,
                             image_id_placeholder: str,
                             image_id_tooltip: str):
        self.metadataTable.clear()
        self.imageId.clear()

        more_button = self.findChild(QPushButton, more_button_name)
        if more_button:
            self.layoutMetadataTable.removeWidget(more_button)
            more_button.deleteLater()

        try:
            enabled = provider.meta_url is not None
        except (NotImplementedError, AttributeError):
            enabled = False
        additional_filters_enabled = enabled

        preview_zoom_enabled = max_preview_zoom is not None and preview_zoom is not None
        self.maxZoom.setEnabled(preview_zoom_enabled)
        if preview_zoom_enabled:
            self.maxZoom.setMaximum(max_preview_zoom)
            self.maxZoom.setValue(preview_zoom)

        self.metadataFilters.setEnabled(additional_filters_enabled)
        self.metadataTable.setRowCount(0)
        self.metadataTable.setColumnCount(len(columns))
        self.metadataTable.setHorizontalHeaderLabels(columns)
        for col in range(len(columns)):  # reveal any previously hidden columns
            self.metadataTable.setColumnHidden(col, False)
        for col in hidden_columns:
            self.metadataTable.setColumnHidden(col, True)
        if sort_by is not None:
            self.metadataTable.sortByColumn(sort_by, Qt.DescendingOrder)
        self.metadata.setTitle(provider_name + self.tr(' Imagery Catalog'))
        self.metadata.setEnabled(enabled)
        self.imageId.setEnabled(enabled)
        self.imageId.setPlaceholderText(image_id_placeholder)
        self.labelImageId.setToolTip(image_id_tooltip)
        self.searchImageryButton.clicked.connect(lambda: self.tabWidget.setCurrentIndex(1))

        self.searchImageryButton.setEnabled(enabled)
        self.searchImageryButton.setToolTip(self.tr("Search imagery") if enabled
                                            else self.tr("Provider does not support imagery search"))

    def show_wd_price(self,
                      wd_price: float,
                      wd_description: str,
                      display_price: bool):
        if display_price:
            # We store the price as Float, but we want to display it as int if it's a whole number (as it usually is)
            _, d = divmod(wd_price,1)
            if d == 0:
                wd_price = int(wd_price)
            self.labelWdPrice.setText(str(wd_price))
            tooltip = wd_description + self.tr('\nPrice: {} credits per square km').format(wd_price)
        else:
            tooltip = wd_description

        self.modelCombo.setToolTip(tooltip)

    def set_processing_rating_labels(self,
                                     processing_name: Optional[str] = None,
                                     current_rating: Optional[int] = None,
                                     current_feedback: Optional[str] = None) -> None:

        self.rateProcessingLabel.setText(self.tr('Rate processing <b>{name}</b>:').format(name=processing_name or ""))
        self.ratingComboBox.setCurrentIndex(current_rating or 0)
        self.processingRatingFeedbackText.setText(current_feedback or "")