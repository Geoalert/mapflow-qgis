import sys
from pathlib import Path
from typing import Iterable, Optional, List
from datetime import datetime

from PyQt5 import uic
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import (QWidget, QPushButton, QCheckBox, QTableWidgetItem, QStackedLayout, QLabel, QToolButton, 
                             QAction, QMenu, QAbstractItemView, QHeaderView, QVBoxLayout, QButtonGroup, QTableWidget)
from qgis.core import QgsMapLayerProxyModel, QgsSettings

from . import icons
from ..config import config, ConfigColumns
from ..entity.billing import BillingType
from ..entity.provider import ProviderInterface
from ..functional import helpers
from ..schema.project import MapflowProject, UserRole
from ..schema.catalog import ProductType

ui_path = Path(__file__).parent/'static'/'ui'

# To allow to import widgets
sys.path.append(str(Path(__file__).parent/'widgets'))


class MainDialog(*uic.loadUiType(ui_path/'main_dialog.ui')):
    # SIGNALS
    modelOptionsChanged = pyqtSignal()
    rasterSourceChanged = pyqtSignal()
    metadataTableFilled = pyqtSignal()

    def __init__(self, parent: QWidget, settings: QgsSettings) -> None:
        """Plugin's main dialog."""
        super().__init__(parent)
        self.settings = settings
        self.setupUi(self)
        # Restrict combos to relevant layer types; QGIS 3.10-3.20 (at least) bugs up if set in .ui
        self.polygonCombo.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        # Don't allow to change path directly (without ... and selection in file dialog) to avoid errors
        self.outputDirectory.setReadOnly(True)
        # Set icons (can be done in .ui but brings about the resources_rc import bug)
        self.setWindowIcon(icons.plugin_icon)
        self.addProvider.setIcon(icons.plus_icon)
        self.removeProvider.setIcon(icons.minus_icon)
        self.editProvider.setIcon(icons.edit_icon)
        self.addAoiButton.setIcon(icons.plus_icon)
        self.billingHistoryButton.setIcon(icons.chart_icon)
        self.logoutButton.setIcon(icons.logout_icon)
        self.modelInfo.setIcon(icons.info_icon)
        self.tabWidget.setTabIcon(0, icons.processing_icon)
        self.tabWidget.setTabIcon(1, icons.lens_icon)
        self.tabWidget.setTabIcon(2, icons.images_icon)
        self.tabWidget.setTabIcon(3, icons.user_gear_icon)
        self.tabWidget.setTabIcon(4, icons.info_icon)
        self.saveOptionsButton.setIcon(icons.options_icon)
        self.createProject.setIcon(icons.plus_icon)
        self.deleteProject.setIcon(icons.minus_icon)
        self.updateProject.setIcon(icons.edit_icon)

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
        self.set_processing_visible_columns()
        self.connect_processing_column_checkboxes()
        self.set_search_visible_columns()
        self.connect_search_column_checkboxes()
        # current state to compare with on change
        self.current_raster_source = self.sourceCombo.currentText()
        # connect raster/provider combos
        self.raster_provider_connection = self.sourceCombo.currentTextChanged.connect(self.switch_provider_combo)
        self.provider_raster_connection = self.providerCombo.currentTextChanged.connect(self.switch_raster_combo)

        self.modelOptions = []
        # Save on toggle
        self.buttonGroup.buttonClicked.connect(self.save_view_results_mode)

        # Restored saved state
        self.set_state_from_settings()

        # Store latest cell selections from data catalog tables
        self.selected_mosaic_cell = None
        self.selected_image_cell = None
        # Create data catalog table wigets
        self.stackedLayout = QStackedLayout()
        self.stackedLayout.addWidget(self.mosaicTable)
        self.stackedLayout.addWidget(self.imageTable)
        self.catalogTableLayout.addLayout(self.stackedLayout)
        # Add buttons for catalog table cells
        self.addImageButton = QToolButton()
        self.showImagesButton = QPushButton()
        self.previewMosaicButton = QPushButton()
        self.editMosaicButton = QPushButton()
        self.previewImageButton = QPushButton()
        self.imageInfoButton = QPushButton()
        # Create colored spacers for tables' cell widgets (so long names won't be seen inbetween buttons)
        self.imageSpacer = QLabel()
        self.mosaicSpacers = [QLabel(), QLabel(), QLabel()]
        for spacer in self.mosaicSpacers+[self.imageSpacer]:
            spacer.setFixedSize(3,26)
            highlight_color = self.mosaicTable.palette().highlight().color().name() 
            spacer.setStyleSheet("background-color:" + highlight_color + ";")
        
        # Hide zoom spinbox
        if config.ZOOM_SELECTOR.lower() == "true":
            pass
        else:
            self.zoomCombo.hide()
        
        # Add options menu
        self.options_menu = QMenu()
        self.save_result_action = QAction(self.tr("Save results"))
        self.download_aoi_action = QAction(self.tr("Download AOI"))
        self.see_details_action = QAction(self.tr("See details"))
        self.processing_update_action = QAction(self.tr("Rename"))
        self.setup_options_menu()

        # Imagery Search
        self.metadataTable.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.enable_search_pages(False)

    # ===== Settings management ===== #
    def save_view_results_mode(self):
        if self.viewAsTiles.isChecked():
            self.settings.setValue("viewResultsMode", "tile")
        elif self.viewAsLocal.isChecked():
            self.settings.setValue("viewResultsMode", "file")

    def set_state_from_settings(self):
        viewResultsMode = self.settings.value('viewResultsMode', "tile")
        if viewResultsMode == "tile":
            self.viewAsTiles.setChecked(True)
        elif viewResultsMode == "file":
            self.viewAsLocal.setChecked(True)
        self.useAllVectorLayers.setChecked(str(self.settings.value('useAllVectorLayers', "true")).lower() == "true")
        self.cornfirmProcessingStart.setChecked(str(self.settings.value('confirmProcessingStart', "true")).lower() == "true")
        self.cornfirmProcessingStart.toggled.connect(lambda: self.settings.setValue("confirmProcessingStart", 
                                                                                    self.cornfirmProcessingStart.isChecked()))

    # connect raster/provider combos funcs
    def switch_provider_combo(self, text):
        # We want to skip the signal emission if the actual text and layer did not change
        # Separate check on layer is needed in case two layers have the same name
        if self.current_raster_source == text:
            return
        self.current_raster_source = text

        self.providerCombo.currentTextChanged.disconnect(self.provider_raster_connection)
        self.providerCombo.setCurrentText(text)
        self.rasterSourceChanged.emit()
        self.provider_raster_connection = self.providerCombo.currentTextChanged.connect(self.switch_raster_combo)

    def switch_raster_combo(self, text):
        # We want to skip the signal emission if the actual text did not change
        if self.current_raster_source == text:
            return
        self.current_raster_source = text
        self.sourceCombo.currentTextChanged.disconnect(self.raster_provider_connection)
        self.sourceCombo.setCurrentText(text)
        self.rasterSourceChanged.emit()
        self.raster_provider_connection = self.sourceCombo.currentTextChanged.connect(self.switch_provider_combo)

    def set_raster_sources(self,
                           provider_names: List[str],
                           default_provider_names: List[str]):
        """
        args:
            provider_names: strings to be added to providers and raster combos
            default_provider_names: will try to set the current text to this value, if available
                The first of available names is set, so the first is preferable
        """
        # Disconnect so that rasterSourceChanged would not be emitted while changing comboBoxes
        self.providerCombo.currentTextChanged.disconnect(self.provider_raster_connection)
        self.sourceCombo.currentTextChanged.disconnect(self.raster_provider_connection)

        self.sourceCombo.clear()
        self.sourceCombo.addItems(provider_names)
        self.providerCombo.clear()
        self.providerCombo.addItems(provider_names)

        for name in default_provider_names:
            if name in provider_names:
                self.sourceCombo.setCurrentText(name)
                self.providerCombo.setCurrentText(name)
        self.current_raster_source = self.sourceCombo.currentText()

        # Now, after all is set, we can unblock the signals and emit a new one
        self.provider_raster_connection = self.providerCombo.currentTextChanged.connect(self.switch_raster_combo)
        self.raster_provider_connection = self.sourceCombo.currentTextChanged.connect(self.switch_provider_combo)
        self.rasterSourceChanged.emit()

    def set_processing_visible_columns(self):
        processing_columns_numbers = [str(x) for x in range(len(self.processing_columns))] # 9 columns in total: 0-8
        # When settings are empty OR filled with something except 0-8
        if not self.settings.value("visibleProcessingColumns") or \
        not list(set(self.settings.value("visibleProcessingColumns")) & set(processing_columns_numbers)):
            # Set only 0-4 and 6 columns (and checkboxes) as checked by default 
            self.settings.setValue("visibleProcessingColumns", [str(x) for x in range(5)] + ["6"])
        # Or check previous columns from settings
        for idx, column in enumerate(self.processing_columns):
            if str(idx) in self.settings.value("visibleProcessingColumns"):
                column.setChecked(True)
        self.set_processing_column_visibility()

    def connect_processing_column_checkboxes(self):
        for checkbox in self.processing_columns:
            checkbox.toggled.connect(self.set_processing_column_visibility)

    def set_processing_column_visibility(self):
        """
        todo: rewrite it as a checkable comboBox or something, which will be filled from code
        """
        new_visible_columns = []
        # Show / hide newly checked / unchecked columns
        for idx, column in enumerate(self.processing_columns):
            self.processingsTable.setColumnHidden(idx, not column.isChecked())
            if column.isChecked():
                new_visible_columns.append(str(idx))
        # Save new checked state in settings
        self.settings.setValue("visibleProcessingColumns", new_visible_columns)

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
                             provider: ProviderInterface,
                             columns: Iterable,
                             hidden_columns: [Iterable[int]],
                             sort_by: str,
                             preview_zoom: int,
                             max_preview_zoom: int,
                             more_button_name: str,
                             image_id_placeholder: str,
                             image_id_tooltip: str,
                             fill: Optional[dict] = None
                             ):
        self.metadataTable.clear()

        more_button = self.findChild(QPushButton, more_button_name)
        if more_button:
            self.layoutMetadataTable.removeWidget(more_button)
            more_button.deleteLater()

        # If the provider does not support search,
        # we substitute it with default search provider (which is ImagerySearchProvider)

        self.metadataFilters.setEnabled(True)
        self.metadataTable.setRowCount(0)
        self.metadataTable.setColumnCount(len(columns))
        self.metadataTable.setHorizontalHeaderLabels(columns)
        for col in range(len(columns)):  # reveal any previously hidden columns
            self.metadataTable.setColumnHidden(col, False)
        for col in hidden_columns:
            self.metadataTable.setColumnHidden(col, True)
        if sort_by is not None:
            self.metadataTable.sortByColumn(sort_by, Qt.DescendingOrder)
        self.metadata.setTitle(self.tr("Search ") + provider.name)

        if fill:
            self.fill_metadata_table(fill)

        self.set_search_column_visibility()

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
            self.ratingComboBox.setToolTip("")
        elif not can_interact:
            self.ratingSubmitButton.setToolTip(reason)
            self.ratingComboBox.setToolTip(reason)
        else:
            self.ratingSubmitButton.setToolTip(self.tr("Please select processing and rating to submit"))
            self.ratingComboBox.setToolTip("")

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

    def clear_model_options(self):
        for checkbox_ in self.modelOptions:
            checkbox_.deleteLater()
            checkbox_ = None
        self.modelOptions.clear()

    def add_model_option(self, name: str, checked: bool = False):
        checkbox = QCheckBox(name, self)
        self.modelOptionsLayout.addWidget(checkbox)
        self.modelOptions.append(checkbox)
        checkbox.setChecked(checked)
        checkbox.toggled.connect(lambda: self.modelOptionsChanged.emit())

    def enabled_blocks(self):
        """
        A simple ordered list of options. It preserve the order,
        but is WD's responsibility to translate the order into option names
        """
        return [box.isChecked() for box in self.modelOptions]

    def providerIndex(self):
        """
        We store proviers in a List, so we need to discard
        """
        return self.providerCombo.currentIndex()

    def setProviderIndex(self, index):
        self.providerCombo.setCurrentIndex(index)

    def fill_metadata_table(self, metadata):
        # Fill out the table
        self.metadataTable.setRowCount(metadata.get('totalFeatures') or len(metadata['features']))
        # Row insertion triggers sorting -> row indexes shift -> duplicate rows, so turn sorting off
        self.metadataTable.setSortingEnabled(False)
        for row, feature in enumerate(metadata['features']):
            if feature.get('id'):
                feature['properties']['id'] = feature.get('id') # for uniformity
            for col, attr in enumerate(ConfigColumns().METADATA_TABLE_ATTRIBUTES.values()):
                value = feature['properties'].get(attr)  # None in case of empty/non-existent field
                table_item = QTableWidgetItem()
                table_item.setData(Qt.DisplayRole, value)
                self.metadataTable.setItem(row, col, table_item)
        # Turn sorting on again
        self.metadataTable.setSortingEnabled(True)
        self.metadataTable.resizeColumnsToContents()
        self.add_preview_cell()
        self.metadataTableFilled.emit()
        
    def setup_options_menu(self):
        self.options_menu.addAction(self.save_result_action)
        self.options_menu.addAction(self.download_aoi_action)
        self.options_menu.addAction(self.see_details_action)
        self.options_menu.addAction(self.processing_update_action)

    def enable_shared_project(self, user_role: UserRole):
        """Disable buttons depending on user role in a shared project.

        :param user_role: current user's role in a project (from ShareProject schema).
        """
        if not user_role:
            user_role = UserRole.owner
        # Disable processing panel
        if not user_role.can_start_processing:
            reason = self.tr('Not enough rights to start processing in a shared project ({})').format(user_role)
        else:
            reason = ""
        self.disable_processing_start(reason, clear_area=True)
        for control in self.project_controls:
            control.setEnabled(user_role.can_start_processing)
        # Disable processing rating
        for control in self.rating_controls:
            control.setEnabled(user_role.can_delete_rename_review_processing)
            self.deleteProcessings.setEnabled(user_role.can_delete_rename_review_processing)
        self.rateProcessingLabel.setText(self.tr('Rate processing:'))
        self.ratingComboBox.setCurrentIndex(0)
        if not user_role.can_delete_rename_review_processing:
            self.enable_rating(False, False, self.tr('Not enough rights to rate processing in a shared project ({})').format(user_role))
        else:
            self.enable_rating(False, True, self.tr('Please select processing'))
        # Disable processing deletion
        self.deleteProcessings.setEnabled(user_role.can_delete_rename_review_processing)
        if not user_role.can_delete_rename_review_processing:
            self.deleteProcessings.setToolTip(self.tr('Not enough rights to delete processing in a shared project ({})').format(user_role))
        else:
            self.deleteProcessings.setToolTip('')
        # And remove/add back renaming option from save options menu
        self.enable_rename_processing(user_role.can_delete_rename_review_processing)

    def enable_model_options(self, can_start_processing: bool = True):
        """
        Set the whole group of checkboxes for model options disabled depending on user role property.
        Is called from 'show_wd_options' in 'mapflow.py'.
        """
        if not can_start_processing:
            can_start_processing = True
        for i in range(self.modelOptionsLayout.count()):
            widget = self.modelOptionsLayout.itemAt(i).widget()
            widget.setEnabled(can_start_processing)
            widget.setChecked(can_start_processing)
    
    def enable_project_change(self, reason: str, can_delete_rename_project: bool = True):
        """
        Disable project controls in a 'Settings' tab depending on user role property.
        Is called from 'on_project_change' in 'mapflow.py'.
        """
        if can_delete_rename_project is None:
            can_delete_rename_project = True
        self.deleteProject.setEnabled(can_delete_rename_project)
        self.updateProject.setEnabled(can_delete_rename_project)
        if can_delete_rename_project is False:
            self.deleteProject.setToolTip(reason)
            self.updateProject.setToolTip(reason)
        else:
            self.deleteProject.setToolTip(self.tr("Delete project"))
            self.updateProject.setToolTip(self.tr("Edit project"))

    def enable_rename_processing(self, can_delete_rename_review_processing: bool = True):
        """
        Remove processing's renaming option from '...' menu near 'View results' button depending on user role property.
        """
        if can_delete_rename_review_processing is False:
            self.options_menu.removeAction(self.processing_update_action)
        else:
            self.options_menu.addAction(self.processing_update_action)

    def enable_zoom_selector(self, enable: bool = True, zoom: str = None):
        self.zoomCombo.setEnabled(enable)
        if enable is False:
            if zoom:
                self.zoomCombo.setCurrentText(zoom)
                self.zoomCombo.setToolTip(self.tr("Zoom is derived from found imagery resolution"))
            else:
                self.zoomCombo.setCurrentIndex(0)
                self.zoomCombo.setToolTip(self.tr("Zoom"))
        else:
            self.zoomCombo.setToolTip(self.tr("Zoom"))

    def enable_search_pages(self, enable: bool = False, page_number: int = 1, total_pages: int = 1):
        self.searchLeftButton.setVisible(enable)
        self.searchRightButton.setVisible(enable)
        self.searchPageLabel.setVisible(enable)
        if enable is False:
            return
        self.searchLeftButton.setIcon(icons.arrow_left_icon)
        self.searchRightButton.setIcon(icons.arrow_right_icon)
        self.searchLeftButton.setToolTip(self.tr("Previous page"))
        self.searchRightButton.setToolTip(self.tr("Next page"))
        self.searchPageLabel.setToolTip(self.tr("Page"))
        self.searchPageLabel.setText(f"{page_number}/{total_pages}")
    
    def enable_search_providers_filter(self, search_provides_count: int):
        if search_provides_count == 0:
            self.searchProvidersCombo.setVisible(False)
            self.searchProvidersLabel.setVisible(False)
        else:
            self.searchProvidersCombo.setVisible(True)
            self.searchProvidersLabel.setVisible(True)

    def enable_projects_pages(self, enable: bool = False, page_number: int = 1, total_pages: int = 1):
        self.projectsPreviousPageButton.setVisible(enable)
        self.projectsNextPageButton.setVisible(enable)
        self.projectsPageLabel.setVisible(enable)
        if enable is True:
            self.projectsPageLabel.setText(f"{page_number}/{total_pages}")
    
    def selected_project_id(self):
        selected_idx = self.projectsTable.selectionModel().selectedIndexes()
        if selected_idx:
            pid = selected_idx[0].data()
        else:
            pid = None
        return (pid)
    
    def set_search_visible_columns(self):
        search_columns_numbers = [str(x) for x in range(len(self.search_columns))] # 11 columns in total: 0-10
        # When settings are empty OR filled with something except 0-10
        if not self.settings.value("visibleSearchColumns") or \
        not list(set(self.settings.value("visibleSearchColumns")) & set(search_columns_numbers)):
            # Set only 0-6 columns (and checkboxes) as checked by default 
            self.settings.setValue("visibleSearchColumns", [str(x) for x in range(8)])
        # Or check previous columns from settings
        for idx, column in enumerate(self.search_columns):
            if str(idx) in self.settings.value("visibleSearchColumns"):
                column.setChecked(True)
    
    def connect_search_column_checkboxes(self):
        for checkbox in self.search_columns:
            checkbox.toggled.connect(self.set_search_column_visibility)
    
    def set_search_column_visibility(self):
        new_visible_columns = []
        # Show / hide newly checked / unchecked columns
        for idx, column in enumerate(self.search_columns):
            self.metadataTable.setColumnHidden(idx, not column.isChecked())
            if column.isChecked():
                new_visible_columns.append(str(idx))
        # Save new checked state in settings
        self.settings.setValue("visibleSearchColumns", new_visible_columns)

    def filter_processings_table(self, name_filter: str = None):
        for row in range(self.processingsTable.rowCount()):
            processing_name = self.processingsTable.item(row, 0).data(Qt.DisplayRole)
            hide = bool(name_filter) and (name_filter.lower() not in processing_name.lower())
            self.processingsTable.setRowHidden(row, hide)
    
    def add_preview_cell(self):
        preview_column_index = config.PPRVIEW_INDEX_COLUMN
        for row in range(self.metadataTable.rowCount()):
            preview_label = QLabel()
            preview_label.setPixmap(icons.lens_icon.pixmap(16, 16))
            preview_label.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
            self.metadataTable.setCellWidget(row, preview_column_index, preview_label)

    @property
    def project_controls(self):
        return [self.labelProcessingName, self.processingName,
                self.labelAoiLayer, self.polygonCombo, self.addAoiButton,
                self.labelImagerySource, self.sourceCombo, self.zoomCombo, self.searchImageryButton,
                self.labelAiModel, self.labelCoins_1, self.labelWdPrice, self.modelCombo, self.modelInfo,
                self.modelOptionsLabel,
                self.startProcessing]
    
    @property
    def rating_controls(self):
        return [self.rateProcessingLabel, self.ratingComboBox,
                self.processingRatingFeedbackText,
                self.acceptButton, self.reviewButton,
                self.ratingSubmitButton]
    
    @property
    def processing_columns(self):
        return [self.showNameColumn,
                self.showModelColumn,
                self.showStatusColumn,
                self.showProgressColumn,
                self.showAreaColumn,
                self.showCostColumn,
                self.showCreatedColumn,
                self.showReviewColumn,
                self.showIdColumn]

    @property
    def search_columns(self):
        return [self.showProductTypeColumn,
                self.showProviderNameColumn,
                self.showPreviewColumn,
                self.showSensorColumn,
                self.showBandsColumn,
                self.showCloudsColumn,
                self.showOffNadirColumn,
                self.showDateTimeColumn,
                self.showZoomColumn,
                self.showResolutionColumn,
                self.showImageIdColumn]
