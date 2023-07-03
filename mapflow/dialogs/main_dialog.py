from pathlib import Path
from typing import Iterable, Optional

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QStandardItemModel
from PyQt5.QtWidgets import QWidget, QPushButton, QComboBox
from qgis.core import QgsMapLayerProxyModel

from ..entity.billing import BillingType
from ..entity.provider import Provider
from ..functional import helpers
from ..config import config
from . import icons

ui_path = Path(__file__).parent/'static'/'ui'


class MainDialog(*uic.loadUiType(ui_path/'main_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        """Plugin's main dialog."""
        super().__init__(parent)
        self.setupUi(self)
        # Restrict combos to relevant layer types; QGIS 3.10-3.20 (at least) bugs up if set in .ui
        self.polygonCombo.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.rasterCombo.setFilters(QgsMapLayerProxyModel.RasterLayer)
        # Set icons (can be done in .ui but brings about the resources_rc import bug)
        self.setWindowIcon(icons.plugin_icon)
        self.addProvider.setIcon(icons.plus_icon)
        self.removeProvider.setIcon(icons.minus_icon)
        self.editProvider.setIcon(icons.edit_icon)
        self.toolButton.setIcon(icons.plus_icon)
        self.billingHistoryButton.setIcon(icons.chart_icon)
        self.logoutButton.setIcon(icons.logout_icon)
        self.modelInfo.setIcon(icons.info_icon)
        self.tabWidget.setTabIcon(1, icons.lens_icon)
        self.tabWidget.setTabIcon(2, icons.user_gear_icon)
        self.tabWidget.setTabIcon(3, icons.info_icon)

        coin_pixmap = icons.coins_icon.pixmap(16, 16)
        self.labelCoins_1.setPixmap(coin_pixmap)

        self.modelInfo.clicked.connect(lambda: helpers.open_model_info(model_name=self.modelCombo.currentText()))
        self.topUpBalanceButton.clicked.connect(lambda: helpers.open_url(config.TOP_UP_URL))
        self.billingHistoryButton.clicked.connect(lambda: helpers.open_url(config.BILLING_HISTORY_URL))

        self.alert_palette = QPalette()
        self.default_palette = QPalette()
        self.alert_palette.setColor(QPalette.WindowText, Qt.red)
        # self.processingProblemsLabel.setPalette(self.alert_palette)

        # not show review/rating at first, to avoid showing non-appropriate buttons
        self.show_feedback_controls(False)
        self.show_review_controls(False)

        # setup hidden/visible columns
        # table.setHorizontalHeaderLabels(labels)
        self.set_column_visibility()
        self.connect_column_checkboxes()

    def connect_column_checkboxes(self):
        self.showNameColumn.toggled.connect(self.set_column_visibility)
        self.showModelColumn.toggled.connect(self.set_column_visibility)
        self.showStatusColumn.toggled.connect(self.set_column_visibility)
        self.showProgressColumn.toggled.connect(self.set_column_visibility)
        self.showAreaColumn.toggled.connect(self.set_column_visibility)
        self.showCostColumn.toggled.connect(self.set_column_visibility)
        self.showCreatedColumn.toggled.connect(self.set_column_visibility)
        self.showReviewColumn.toggled.connect(self.set_column_visibility)
        self.showIdColumn.toggled.connect(self.set_column_visibility)

    def set_column_visibility(self):
        """
        todo: rewrite it as a checkable comboBox or something, which will be filled from code
        """
        column_flags = (self.showNameColumn.isChecked(),
                        self.showModelColumn.isChecked(),
                        self.showStatusColumn.isChecked(),
                        self.showProgressColumn.isChecked(),
                        self.showAreaColumn.isChecked(),
                        self.showCostColumn.isChecked(),
                        self.showCreatedColumn.isChecked(),
                        self.showReviewColumn.isChecked(),
                        self.showIdColumn.isChecked())

        for idx, flag in enumerate(column_flags):
            # A VERY ugly solution, depends on correspondence between Config, main_dialog.ui and this file
            self.processingsTable.setColumnHidden(idx, not flag)

    # ========= SHOW =========== #
    def setup_for_billing(self, billing_type: BillingType):
        """
        set the UI elements according to user's billing type
        """
        credits_used = billing_type == billing_type.credits
        balance_visible = billing_type != billing_type.none

        self.topUpBalanceButton.setVisible(credits_used)
        self.labelCoins_1.setVisible(False)  # credits_used
        self.labelWdPrice.setVisible(False)  # credits_used
        self.balanceLabel.setVisible(balance_visible)

    def setup_for_review(self, review_workflow_enabled: bool):
        self.show_review_controls(review_workflow_enabled)
        self.show_feedback_controls(not review_workflow_enabled)

    def show_feedback_controls(self, enable: bool):
        self.ratingComboBox.setVisible(enable)
        self.rateProcessingLabel.setVisible(enable)
        self.ratingSubmitButton.setVisible(enable)
        self.processingRatingFeedbackText.setVisible(enable)

    def show_review_controls(self, enable: bool):
        self.acceptButton.setVisible(enable)
        self.reviewButton.setVisible(enable)

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

        imagery_search_tab = self.tabWidget.findChild(QWidget, "providersTab")
        self.searchImageryButton.clicked.connect(lambda: self.tabWidget.setCurrentWidget(imagery_search_tab))
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
        if not current_rating:
            position = 0
        else:
            # rating is reversed in the combobox; 1st line is placeholder
            position = 6 - current_rating
        self.ratingComboBox.setCurrentIndex(position)
        self.processingRatingFeedbackText.setText(current_feedback or "")

    def enable_rating(self,
                      can_interact: bool = True,
                      can_send: bool = True,
                      reason: str = ""):
        """
        Toggle the whole group of controls about user's feedback
        """
        self.ratingComboBox.setEnabled(can_interact)
        self.rateProcessingLabel.setEnabled(can_interact)
        self.processingRatingFeedbackText.setEnabled(can_interact)
        self.ratingSubmitButton.setEnabled(can_interact and can_send)

        if can_interact and can_send:
            self.ratingSubmitButton.setToolTip("")
        elif not can_interact:
            self.ratingSubmitButton.setToolTip(reason)
        else:
            self.ratingSubmitButton.setToolTip(self.tr("Please select processing and rating to submit"))

    def enable_review(self,
                      can_interact: bool = True,
                      reason: str = ""):
        """
        Toggle the whole group of controls about user's feedback

        reason is displayed tooltip on `why the buttons are disabled`
        """
        self.acceptButton.setEnabled(can_interact)
        self.reviewButton.setEnabled(can_interact)

        if can_interact:
            self.reviewButton.setToolTip("")
            self.acceptButton.setToolTip("")
        elif not can_interact:
            self.reviewButton.setToolTip(reason)
            self.acceptButton.setToolTip(reason)

    def disable_processing_start(self,
                                 reason: str,
                                 clear_area: bool = False):
        if clear_area:
            self.labelAoiArea.clear()
        self.processingProblemsLabel.setPalette(self.alert_palette)
        self.processingProblemsLabel.setText(reason)
        self.startProcessing.setDisabled(True)
