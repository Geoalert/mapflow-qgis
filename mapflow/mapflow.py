import json
import logging
import os.path
import shutil
from base64 import b64decode
from configparser import ConfigParser  # parse metadata.txt -> QGIS version check (compatibility)
from datetime import datetime, timedelta  # processing creation datetime formatting
from pathlib import Path
from typing import List, Optional, Callable, Tuple
from osgeo import gdal, ogr

from PyQt5.QtCore import (
    QCoreApplication, QDate, QDateTime, QObject, Qt,
    QTimer, QTranslator
)
from PyQt5.QtGui import QBrush, QColor, QIcon
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest
from PyQt5.QtWidgets import (
    QAbstractItemView, QAction, QApplication, QFileDialog, QHBoxLayout,
    QInputDialog, QLabel, QMenu, QMessageBox, QPushButton, QWidget, QToolButton
)
from qgis.core import (
    Qgis, QgsCoordinateReferenceSystem, QgsDistanceArea, QgsFeature, QgsGeometry,
    QgsLayerTreeGroup, QgsLayerTreeLayer, QgsMapLayer, QgsMapLayerType,
    QgsProject, QgsRasterLayer, QgsRectangle, QgsVectorLayer
)

from .config import OSM, Config, ConfigColumns
from .errors import (BadProcessingInput,
                     ErrorMessage,
                     ImageIdRequired,
                     PluginError,
                     ProcessingInputDataMissing,
                     ProxyIsAlreadySet)
# Functional
from .functional import helpers, layer_utils
from .functional.app_context import AppContext
from .functional.auth import get_auth_id
from .functional.controller.data_catalog_controller import DataCatalogController
from .functional.controller.processing_controller import ProjectProcessingController
from .functional.service import (DataCatalogService,
                                 ProcessingService,
                                 ProjectService,
                                 ProviderService)
from .functional.service.alert_service import AlertService, alert
from .functional.service.area_calculator_service import AreaCalculatorService
# HTTP
from .http import (Http,
                   api_message_parser,
                   get_error_report_body)
# Schema
from .schema import (BillingType,
                     ImageCatalogRequestSchema,
                     ImageCatalogResponseSchema,
                     ImagerySearchParams,
                     MyImageryParams,
                     ProviderReturnSchema,
                     UserDefinedParams)
from .schema.catalog import (MultiPreviewList,
                             PreviewType,
                             ProductType)
from .schema.project import MapflowProject, UserRole
from .schema.template import (AOI_NAME_MAX_LENGTH,
                              AddAoisSchema,
                              AddSingleAoiSchema,
                              CreateProcessingTemplateSchema,
                              DeleteAoisSchema,
                              SearchParams,
                              UpdateAoiSchema,
                              UpdateProcessingTemplateSchema)
from .schema.workflow_def import WorkflowDef
# Dialogs
from .dialogs import (ErrorMessageWidget,
                      MainDialog,
                      MapflowLoginDialog,
                      ProviderDialog,
                      ReviewDialog)
from .dialogs.icons import plugin_icon, new_image_icon
from .dialogs.processing_details_dialog import ProcessingDetailsDialog
from .dialogs.select_aoi_layers_dialog import SelectAoiLayersDialog
# Providers
from .model.provider import (create_provider,
                              DefaultProvider,
                              ImagerySearchProvider,
                              MyImageryProvider,
                              ProviderInterface,
                              ProvidersList)

logger = logging.getLogger(__name__)


class Mapflow(QObject):
    """This class represents the plugin. It is instantiated by QGIS."""

    # The AOI id the in-template search results are currently filtered by (None = all).
    # Class-level default so the check is safe before on_template_opened sets it.
    _template_search_aoi_filter = None
    # Guards against the ``metadataTableFilled`` -> ``apply_local_filter`` -> ``fill_metadata_table``
    # -> ``metadataTableFilled`` re-entrancy: the local filter re-fills the table itself, so the
    # nested fill must not trigger another filter pass.
    _suppress_local_filter = False
    # Last local-filter outcome, so a slider drag that doesn't flip any image skips the re-fill.
    _last_unfit_set = None
    _last_filtered_geoms = None
    # Server-side sort of the search results (regular search AND template results). Default:
    # newest first by acquisition date; a header click changes/flips it and re-runs the search.
    _search_sort_by = "ACQUISITION_DATE"
    _search_sort_order = "DESC"
    # Cached widen-warning messages backing the (!) indicator's click handler.
    _widen_details = None
    # The AOI ids the processing Area is currently derived from, so a repeated selection signal
    # doesn't rebuild it. ``_selected_aois_layer_id`` is the visible "Selected AOIs" layer built
    # for a MULTI-AOI selection (a single selection uses that AOI's own layer).
    _processing_area_aoi_filter = None
    _selected_aois_layer_id = None
    # Id of the currently shown mosaic-preview boundary layer, so it can be removed when the
    # next preview is shown (its name varies by acquisition date, so name-match alone misses it).
    _mosaic_preview_footprint_id = None
    # State of an in-progress on-map AOI edit/draw session (None = no session). While a session
    # is active the plugin panel is hidden and a Save/Cancel bar is shown over the map.
    _aoi_session = None
    _aoi_edit_bar_item = None

    def __init__(self, iface) -> None:
        """Initialize the plugin.

        :param iface: an instance of the QGIS interface.
        """
        # ========== 1. BASIC CONFIGURATION ==========
        # Init configs
        self.config = Config()
        self.app_context = AppContext(self.config)
        self.version_ok = True
        # Save refs to key variables used throughout the plugin
        self.iface = iface
        self.main_window = self.iface.mainWindow()
        self.project_connection = None
        super().__init__(self.main_window)
        self.message_bar = self.iface.messageBar()
        self.plugin_dir = os.path.dirname(__file__)
        self.plugin_name = self.config.PLUGIN_NAME  # aliased here to be overloaded in submodules
        # Get the server environment to connect to
        self.server = self.config.SERVER
        
        # ========== 2. APP_CONTEXT ==========
        # Populate infrastructure in app_context
        self.app_context.server = self.server
        self.app_context.config = self.config
        self.app_context.max_aois_per_processing = self.config.MAX_AOIS_PER_PROCESSING
        self.app_context.project = QgsProject.instance()
        self.app_context.plugin_name = self.plugin_name
        # Get the layer tree root from app context
        self.layer_tree_root = self.app_context.project.layerTreeRoot()
        # Init toolbar and toolbar buttons
        self.toolbar = self.iface.addToolBar(self.plugin_name)
        self.toolbar.setObjectName(self.plugin_name)
        # Translation
        locale = self.app_context.settings.value('locale/userLocale', 'en_US')[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n', f'mapflow_{locale}.qm')
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)
        # Translate native Qt texts
        QCoreApplication.translate('QPlatformTheme', 'Cancel')
        QCoreApplication.translate('QPlatformTheme', '&Yes')
        QCoreApplication.translate('QPlatformTheme', '&No')
        # Create a namespace for the plugin settings
        self.app_context.settings.beginGroup(self.plugin_name.lower())
        if self.app_context.settings.value('processings') is None:
            self.app_context.settings.setValue('processings', {})
        # Set projects from settings if it was opened before
        self.app_context.project_id = self.app_context.settings.value("project_id")
        # Imagery search pagination
        self.search_page_offset = 0
        self.search_page_limit = self.config.SEARCH_RESULTS_PAGE_LIMIT

        # ========== 3. INIT DIALOGS ==========
        # Init dialogs before creating timers that need them as parent
        self.use_oauth = (self.app_context.settings.value('use_oauth', 'false').lower() == 'true')
        self.plugin_icon = plugin_icon
        self.dlg = MainDialog(self.main_window, self.app_context.settings)
        self.dlg_login = self.set_up_login_dialog()
        self.review_dialog = ReviewDialog(self.dlg)
        self.dlg_provider = ProviderDialog(self.dlg)
        self.dlg_provider.accepted.connect(self.edit_provider_callback)
        # todo: Move to Maindialog
        metadata_parser = ConfigParser()
        metadata_parser.read(os.path.join(self.plugin_dir, 'metadata.txt'))
        self.app_context.plugin_version = metadata_parser.get('general', 'version')
        self.dlg.help.setText(
            self.dlg.help.text().replace('Mapflow', f'{self.plugin_name} {self.app_context.plugin_version}', 1)
        )
        # Initialize HTTP request sender
        self.http = Http(self.app_context.server,
                         self.app_context.plugin_version,
                         self.default_error_handler)
        self.calculator = QgsDistanceArea()
        # Restore directory from settings
        self.dlg.outputDirectory.setText(self.app_context.settings.value('outputDir'))

        # ========== 4. CREATE TIMERS ==========
        # Poll user status to get limits
        self.user_status_update_timer = QTimer(self.dlg)
        self.user_status_update_timer.setInterval(self.config.USER_STATUS_UPDATE_INTERVAL * 1000)
        self.user_status_update_timer.timeout.connect(self.refresh_status)
        # Retries /user/status until the response that configures the plugin arrives.
        # A tick is skipped while a request is still in flight, so a slow or unreachable
        # server produces one outstanding request rather than two per second.
        self.app_startup_user_update_timer = QTimer(self.dlg)
        self.app_startup_user_update_timer.setInterval(self.config.STARTUP_STATUS_RETRY_INTERVAL)
        self.app_startup_user_update_timer.timeout.connect(self.first_status_request)
        self._startup_status_attempts = 0
        self._startup_status_pending = False
        self._startup_status_given_up = False

        # ========== 5. SETUP TEMP DIRECTORY ==========
        # AlertService must exist before setup_tempdir: an unavailable working directory below (and
        # select_output_directory on a bad pick) shows a modal, and both run before section 6.
        AlertService(self.plugin_name)
        tempdir_error = self.setup_tempdir()
        if tempdir_error:
            # Working directory is configured but unavailable (e.g. an unmounted external drive).
            # It's only needed to save results locally, so let the user fix it now or postpone —
            # a modal with an action beats a transient status-bar line for a blocking problem.
            self.prompt_output_directory(
                self.tr("The working directory '{dir}' is unavailable:<br>{error}<br><br>"
                        "It is needed to save processing results on your computer.").format(
                            dir=self.app_context.settings.value('outputDir'), error=tempdir_error))

        # ========== 6. INITIALIZE INDEPENDENT SERVICES ==========
        self.result_loader = layer_utils.ResultsLoader(iface=self.iface,
                                                       maindialog=self.dlg,
                                                       http=self.http,
                                                       settings=self.app_context.settings,
                                                       context=self.app_context
                                                    )
        self.result_loader.check_tempdir_func = self.check_if_output_directory_is_selected

        self.data_catalog_service = DataCatalogService(self.http,
                                                    self.server,
                                                    self.dlg,
                                                    self.iface,
                                                    self.result_loader,
                                                    self.app_context.plugin_version,
                                                    app_context=self.app_context)
        self.data_catalog_controller = DataCatalogController(self.dlg, self.data_catalog_service)

        # ========== 7. INITIALIZE PROJECT AND PROCESSING SERVICES ==========
        self.project_service = ProjectService(http=self.http,
                                            app_context=self.app_context,
                                            dlg=self.dlg,
                                            config=self.config)
        
        self.provider_service = ProviderService.get_instance(providers=ProvidersList([]),
                                                            dlg=self.dlg,
                                                            app_context=self.app_context,
                                                            config=self.config,
                                                            data_catalog_service=self.data_catalog_service)
        self.provider_service.selection_sync_callback = self.sync_layer_selection_with_table

        self.processing_service = ProcessingService(http=self.http,
                                                    dlg=self.dlg,
                                                    iface=self.iface,
                                                    result_loader=self.result_loader,
                                                    app_context=self.app_context,
                                                    timer_interval=self.config.PROCESSING_TABLE_REFRESH_INTERVAL * 1000)
        
        self.project_processing_controller = ProjectProcessingController(dlg=self.dlg,
                                                                        processing_service=self.processing_service,
                                                                        project_service=self.project_service,
                                                                        app_context=self.app_context)
        
        # ========== 8. LOAD PROVIDERS FROM SETTINGS ==========
        # load providers from settings before initializing area calculator service
        errors = []
        try:
            self.provider_service.user_providers, errors = ProvidersList.from_settings(settings=self.app_context.settings)
            self.provider_service.default_providers = ProvidersList([])
        except Exception as e:
            self.alert(self.tr("Error during loading the data providers: {e}").format(e=str(e)),
                       icon=QMessageBox.Warning)
        if errors:
            self.alert(self.tr('We failed to import providers from the settings. Please add them again'),
                    icon=QMessageBox.Warning)
        self.provider_service.update_providers()

        # ========== 9. ADD LAYER MENU ==========
        self.add_layer_menu = QMenu()
        self.draw_aoi = QAction(self.tr("Draw AOI at the map"))
        self.use_imagery_extent = QAction(self.tr("Use imagery extent"))
        self.use_imagery_extent.setEnabled(False)
        self.create_aoi_from_map_action = QAction(self.tr("Create AOI from map extent"))
        self.aoi_layer_counter = 0
        self.setup_add_layer_menu()
        # Add options menu functionality
        self.setup_options_menu_connections()
        # Layer actions
        self.add_layer_action = QAction(u"Use as AOI in Mapflow")
        self.add_layer_action.setIcon(plugin_icon)
        self.add_layer_action.triggered.connect(self.add_to_layers)
        iface.addCustomActionForLayerType(self.add_layer_action, None, QgsMapLayerType.VectorLayer, True)
        self.remove_layer_action = QAction(u"Remove AOI from Mapflow")
        self.remove_layer_action.setIcon(plugin_icon)
        self.remove_layer_action.triggered.connect(self.remove_from_layers)
        iface.addCustomActionForLayerType(self.remove_layer_action, None, QgsMapLayerType.VectorLayer, False)
        self.dlg.useAllVectorLayers.stateChanged.connect(self.toggle_all_layers)
        self.dlg.polygonCombo.setExceptedLayerList(self.filter_aoi_layers())

        # ========== 10. INITIALIZE AREA CALCULATOR SERVICE ==========
        self.area_calculator_service = AreaCalculatorService(iface=self.iface,
                                                             app_context=self.app_context,
                                                             dlg=self.dlg,
                                                             config=self.config,
                                                             data_catalog_service=self.data_catalog_service,
                                                             processing_service=self.processing_service,
                                                             provider_service=self.provider_service,
                                                             use_imagery_extent=self.use_imagery_extent)
        self.project_service.area_calculator_service = self.area_calculator_service
        
        # ========== 11. SETUP METADATA FILTERS ==========
        self.dlg.minIntersection.setValue(int(self.app_context.settings.value('metadataMinIntersection', 0)))
        self.dlg.maxCloudCover.setValue(int(self.app_context.settings.value('metadataMaxCloudCover', 100)))
        self.dlg.set_off_nadir_range(
            int(self.app_context.settings.value('metadataMinOffNadir', self.dlg.OFF_NADIR_MIN)),
            int(self.app_context.settings.value('metadataMaxOffNadir', self.dlg.OFF_NADIR_MAX)))
        # Set default metadata dates
        today = QDate.currentDate()
        self.dlg.metadataFrom.setDate(self.app_context.settings.value('metadataFrom', today.addMonths(-6)))
        self.dlg.metadataTo.setDate(self.app_context.settings.value('metadataTo', today))

        # ========== 12. SET UP SIGNALS & SLOTS ==========
        self.dlg.modelCombo.currentIndexChanged.connect(self.on_model_change)
        self.dlg.modelOptionsChanged.connect(self.on_options_change)
        # Memorize dialog element sizes & positioning
        self.dlg.finished.connect(self.save_dialog_state)
        # Connect buttons
        self.dlg.logoutButton.clicked.connect(self.logout)
        self.dlg.selectOutputDirectory.clicked.connect(self.select_output_directory)
        self.dlg.downloadResultsButton.clicked.connect(self.load_results)
        # Calculate AOI size
        self.dlg.polygonCombo.layerChanged.connect(self.area_calculator_service.calculate_aoi_area_polygon_layer)
        self.dlg.mosaicTable.itemSelectionChanged.connect(self.area_calculator_service.calculate_aoi_area_catalog)
        self.dlg.imageTable.itemSelectionChanged.connect(self.area_calculator_service.calculate_aoi_area_catalog)
        self.monitor_polygon_layer_feature_selection([
            self.app_context.project.mapLayer(layer_id) for layer_id in self.app_context.project.mapLayers(validOnly=True)
        ])
        self.app_context.project.layersAdded.connect(self.setup_layers_context_menu)
        self.app_context.project.layersAdded.connect(self.monitor_polygon_layer_feature_selection)
        # Processings
        self.dlg.processingsTable.cellDoubleClicked.connect(self.load_results)
        self.dlg.deleteProcessings.clicked.connect(self.processing_service.confirm_delete_processings)
        self.processing_service.connect_processings_pagination()
        # In-template navigation: map side-effects on enter/leave a template.
        self.processing_service.templateOpened.connect(self.on_template_opened)
        self.processing_service.templateClosed.connect(self.on_template_closed)
        self.processing_service.templateAoisChanged.connect(self.on_template_aois_changed)
        self.processing_service.templateProcessingsLoaded.connect(self.on_template_processings_loaded)
        self.dlg.processingsTable.itemSelectionChanged.connect(self.filter_search_by_selected_aoi)
        self.dlg.processingsTable.itemSelectionChanged.connect(self.sync_processing_area_to_selected_aois)
        # Processings ratings
        self.dlg.processingsTable.itemSelectionChanged.connect(self.enable_feedback)
        self.dlg.processingsTable.itemSelectionChanged.connect(self.on_processings_selection_changed)
        self.dlg.ratingSubmitButton.clicked.connect(self.submit_processing_rating)
        self.dlg.enable_rating(False, False)  # by default disabled
        self.dlg.enable_review(False)
        # Processing feedback
        self.dlg.ratingComboBox.activated.connect(self.enable_feedback)
        self.dlg.processingsTable.cellClicked.connect(self.update_processing_current_rating)
        # In a template, single-clicking a 'No AOI' processing row adds its AOI to the map
        # (double-click still loads results).
        self.dlg.processingsTable.cellClicked.connect(self.on_no_aoi_processing_clicked)
        # Processing review
        self.dlg.acceptButton.clicked.connect(self.accept_processing)
        self.dlg.reviewButton.clicked.connect(self.show_review_dialog)
        self.review_dialog.accepted.connect(self.submit_review)

        # ========== 13. PROVIDERS ==========
        # Search filters (intersection, cloud, dates) are applied server-side on the next
        # Search; there is no offline re-filtering on widget change anymore.
        self.dlg.searchImageryButton.clicked.connect(self.preview_or_search)

        self.dlg.addProvider.clicked.connect(self.add_provider)
        self.dlg.editProvider.clicked.connect(self.edit_provider)
        self.dlg.removeProvider.clicked.connect(self.remove_provider)

        self.config_search_columns = ConfigColumns()
        # Image ids whose preview is currently being downloaded (async). Guards against the
        # dedupe-on-map check missing duplicates, since the preview layer is only added in the
        # HTTP callback — a second click/double-click fired several downloads before the first
        # landed, producing duplicate preview layers.
        self._pending_preview_ids = set()
        # Processing ids whose 'No AOI' AOI request is in flight (guards rapid re-clicks).
        self._pending_no_aoi_ids = set()
        self.meta_table_layer_connection = self.dlg.metadataTable.itemSelectionChanged.connect(
            self.sync_table_selection_with_image_id_and_layer)
        self.dlg.metadataTable.itemSelectionChanged.connect(self.update_start_processing_button_state)
        self.app_context.meta_layer_table_connection = None
        self.dlg.getMetadata.clicked.connect(self.handle_metadata_button_click)
        self.dlg.metadataTable.cellDoubleClicked.connect(self.preview)
        self.dlg.metadataTable.cellClicked.connect(self.on_metadata_table_cell_clicked)
        self.dlg.metadataTable.horizontalHeader().sectionClicked.connect(self.on_metadata_header_clicked)
        self.dlg.rasterSourceChanged.connect(self.on_provider_change)
        self.dlg.clearSearch.clicked.connect(self.clear_metadata)
        self.dlg.metadataTableFilled.connect(self.apply_local_filter)
        # Instant local filtering: changing a filter widget re-filters the already-fetched
        # results in place (no server request), for both regular search and templates.
        self.dlg.minIntersection.valueChanged.connect(self.apply_local_filter)
        self.dlg.maxCloudCover.valueChanged.connect(self.apply_local_filter)
        self.dlg.offNadirSlider.rangeChanged.connect(self.apply_local_filter)
        self.dlg.metadataFrom.dateChanged.connect(self.apply_local_filter)
        self.dlg.metadataTo.dateChanged.connect(self.apply_local_filter)
        # Provider selection/availability and product type (Mosaic/Image) are local filters too;
        # re-filter when any of them change.
        self.dlg.searchProvidersCombo.checkedItemsChanged.connect(self.apply_local_filter)
        self.dlg.hideUnavailableResults.toggled.connect(self.apply_local_filter)
        self.dlg.searchMosaicCheckBox.toggled.connect(self.apply_local_filter)
        self.dlg.searchImageCheckBox.toggled.connect(self.apply_local_filter)
        self.dlg.resetSearchFilters.clicked.connect(self.reset_filters)
        self.dlg.searchRightButton.clicked.connect(self.show_search_next_page)
        self.dlg.searchLeftButton.clicked.connect(self.show_search_previous_page)
        # Repurposed Filter button: now the widen-warning (!) indicator (shown only when the
        # current filters are wider than what was fetched); clicking it explains what won't apply.
        self.dlg.searchWidenWarning.clicked.connect(self.show_widen_details)
        self.dlg.updateTemplateSearch.clicked.connect(self.update_template_search_params)
        self.setup_metadata_search_dropdown()
        self.setup_metadata_seen_dropdown()

        # ========== 14. ZOOM SELECTOR CONFIGURATION ==========
        self.dlg.zoomCombo.currentIndexChanged.connect(self.on_zoom_change)
        saved_zoom = self.app_context.settings.value('zoom')
        if saved_zoom is None:
            self.dlg.zoomCombo.setCurrentIndex(0)
        else:
            zoom_index = self.dlg.zoomCombo.findText(saved_zoom)
            if zoom_index == -1:
                # Fallback for situation if the settings contain value not available in the list
                self.dlg.zoomCombo.setCurrentIndex(0)
                self.app_context.settings.setValue('zoom', None)
            else:
                self.dlg.zoomCombo.setCurrentIndex(zoom_index)
    
    def setup_layers_context_menu(self, layers: List[QgsMapLayer]):
        for layer in filter(layer_utils.is_polygon_layer, layers):
            self.iface.addCustomActionForLayer(self.add_layer_action, layer)
        self.dlg.polygonCombo.setExceptedLayerList(self.filter_aoi_layers())

    def add_to_layers(self, layer=None, recompute_cost: bool = True, set_current: bool = True):
        if not layer:
            layer = self.iface.layerTreeView().currentLayer()
        if layer not in self.app_context.aoi_layers:
            self.app_context.aoi_layers.append(layer)
            self.iface.addCustomActionForLayer(self.remove_layer_action, layer)
        self.dlg.polygonCombo.setExceptedLayerList(self.filter_aoi_layers())
        # ``set_current=False`` for template AOI *display* layers added in bulk: they must not
        # hijack the processing Area (the last one used to stick as the Area — feedback 8.1);
        # the Area is driven by the AOI table selection instead.
        if not set_current:
            return
        # When adding template AOI layers in bulk (recompute_cost=False), don't let each
        # setLayer fire polygonCombo.layerChanged -> a cost request: no image is selected yet,
        # and the user's click will compute the cost once afterwards.
        self.dlg.polygonCombo.blockSignals(not recompute_cost)
        self.dlg.polygonCombo.setLayer(layer)
        self.dlg.polygonCombo.blockSignals(False)

    def remove_from_layers(self, layer=None):
        if not layer:
            layer = self.iface.layerTreeView().currentLayer()
        try:
            self.app_context.aoi_layers.remove(layer)
        except ValueError:
            pass
            # it can be easly already removed as I can't remove action from contextmenu of a single layer
        self.dlg.polygonCombo.setExceptedLayerList(self.filter_aoi_layers())

    def toggle_all_layers(self, state: bool):
        self.dlg.polygonCombo.setExceptedLayerList(self.filter_aoi_layers())
        self.app_context.settings.setValue('useAllVectorLayers', str(self.dlg.useAllVectorLayers.isChecked()))

    def refresh_status(self):
        self.http.get(
            url=f'{self.server}/user/status',
            callback=self.set_processing_limit,
            use_default_error_handler=False  # ignore errors to prevent repetitive alerts
        )

    def first_status_request(self):
        if self._startup_status_given_up or self._startup_status_pending:
            return
        if self._startup_status_attempts >= self.config.STARTUP_STATUS_MAX_ATTEMPTS:
            # Latched rather than left to the stopped timer: giving up must be a terminal
            # state, so a stray call cannot turn one warning into a modal per invocation.
            self._startup_status_given_up = True
            self.stop_startup_status_polling()
            self.alert(self.tr('Could not load your account status from Mapflow.\n\n'
                               'Some features stay unavailable until you reconnect and '
                               'reopen the plugin.'),
                       icon=QMessageBox.Warning)
            return
        self._startup_status_attempts += 1
        self._startup_status_pending = True
        self.http.get(
            url=f'{self.server}/user/status',
            callback=self.first_status_callback,
            error_handler=self.first_status_error_handler,
            use_default_error_handler=False
        )

    def stop_startup_status_polling(self):
        self.app_startup_user_update_timer.stop()
        self._startup_status_pending = False

    def first_status_callback(self, response: QNetworkReply) -> None:
        """Apply the startup configuration carried by the first /user/status response.

        The timer is stopped *before* the configuration runs, not after it. `set_processing_limit`
        is invoked through the error guard, which swallows an exception and skips the rest of the
        callback — so a stop placed after the configuration would never run on a bad response, and
        the plugin would re-attempt the whole setup twice a second for the rest of the session.
        See spec/006_error_reporting.md § Consequences for new code.
        """
        self.stop_startup_status_polling()
        self.set_processing_limit(response, app_startup_request=True)
        # Storage quota for My Imagery: needed once at startup, and refreshed later by
        # mosaicsUpdated. Issuing it per retry would mean a second endpoint polled at the
        # retry interval, with its own error dialog on every failed tick.
        self.data_catalog_service.get_user_limit()

    def first_status_error_handler(self, response: QNetworkReply) -> None:
        """Let the next tick retry, and surface the failure once the attempts run out."""
        self._startup_status_pending = False
        logger.warning("Startup /user/status attempt %s failed with Qt error %s",
                       self._startup_status_attempts, response.error())

    def setup_add_layer_menu(self):
        self.add_layer_menu.addAction(self.draw_aoi)
        self.add_layer_menu.addAction(self.use_imagery_extent)
        self.add_layer_menu.addAction(self.create_aoi_from_map_action)
        
        self.draw_aoi.triggered.connect(self.create_editable_aoi_layer)
        self.use_imagery_extent.triggered.connect(self.create_aoi_layer_from_imagery)
        self.create_aoi_from_map_action.triggered.connect(self.create_aoi_layer_from_map)
        self.dlg.addAoiButton.setMenu(self.add_layer_menu)

    def setup_options_menu_connections(self):
        self.dlg.save_result_action.triggered.connect(self.download_results_file)
        self.dlg.download_aoi_action.triggered.connect(self.download_aoi_file)
        self.dlg.see_details_action.triggered.connect(self.show_selected_details)
        self.dlg.see_processings_action.triggered.connect(self.select_template_processings)
        self.dlg.see_search_results_action.triggered.connect(self.show_template_search_results)
        self.dlg.processing_update_action.triggered.connect(self.processing_service.update_processing)
        self.dlg.processing_restart_action.triggered.connect(self.processing_service.restart_processing)
        self.dlg.processing_duplicate_action.triggered.connect(self.check_dir_and_duplicate_processing)
        # Template-specific actions
        self.dlg.template_rename_action.triggered.connect(self.processing_service.update_template)
        self.dlg.template_pause_action.triggered.connect(self.processing_service.pause_template)
        self.dlg.template_resume_action.triggered.connect(self.processing_service.resume_template)
        self.dlg.template_restart_action.triggered.connect(self.processing_service.restart_template)
        # AOI actions (in-template view)
        self.dlg.aoi_rename_action.triggered.connect(self.processing_service.rename_aoi)
        self.dlg.aoi_delete_action.triggered.connect(self.processing_service.delete_aoi)
        self.dlg.aoi_add_action.triggered.connect(self.add_aoi_from_layer_dialog)
        self.dlg.aoi_update_geometry_action.triggered.connect(self.start_update_aoi_session)
        self.dlg.aoi_draw_action.triggered.connect(self.start_draw_aoi_session)
        self.dlg.exclude_from_search_action.triggered.connect(self.exclude_processing_from_search)
        self.dlg.options_menu.aboutToShow.connect(self.update_processing_options_menu)
        self.dlg.saveOptionsButton.setMenu(self.dlg.options_menu)

    def update_processing_options_menu(self):
        """Render processing options menu depending on selected row type."""
        menu = self.dlg.options_menu
        menu.clear()

        selected_template = self.processing_service.selected_template()
        selected_processing = self.processing_service.selected_processing()

        # In-template view: AOI add/rename/delete (only for AOI rows / empty selection;
        # a selected processing row falls through to the normal processing actions below).
        if self.processing_service.in_template_mode and not selected_processing:
            can_edit = self.app_context.can_edit_template(self.processing_service.active_template)
            selected_aoi = self.processing_service.selected_aoi()
            # No AOI action can start while another edit/draw session is running.
            no_session = self._aoi_session is None
            if selected_aoi:
                self.dlg.aoi_rename_action.setEnabled(can_edit and selected_aoi.can_rename)
                menu.addAction(self.dlg.aoi_rename_action)
                self.dlg.aoi_delete_action.setEnabled(can_edit and selected_aoi.can_rename)
                menu.addAction(self.dlg.aoi_delete_action)
                # Edit the selected AOI's geometry on the map (vertex editing, in place).
                self.dlg.aoi_update_geometry_action.setEnabled(
                    can_edit and selected_aoi.can_rename and no_session)
                menu.addAction(self.dlg.aoi_update_geometry_action)
            self.dlg.aoi_add_action.setEnabled(can_edit and no_session)
            menu.addAction(self.dlg.aoi_add_action)
            self.dlg.aoi_draw_action.setEnabled(can_edit and no_session)
            menu.addAction(self.dlg.aoi_draw_action)
            return

        # In-template view, a processing row is backed by the v1 TemplateProcessingSchema
        # (flat params, no ProcessingParams) — offer only the read-only result actions, not
        # restart/duplicate which need v2 source params.
        if self.processing_service.in_template_mode and selected_processing:
            menu.addAction(self.dlg.save_result_action)
            menu.addAction(self.dlg.see_details_action)
            # Subtract this processing's already-processed area from the template's AOIs (feature 3).
            # This edits the open template's geometry, so it follows template-edit rights.
            if self.app_context.can_edit_template(self.processing_service.active_template):
                menu.addAction(self.dlg.exclude_from_search_action)
            return

        # Template selection: only template details action.
        if selected_template and not selected_processing:
            menu.addAction(self.dlg.see_details_action)
            menu.addAction(self.dlg.see_search_results_action)
            menu.addAction(self.dlg.see_processings_action)
            # A contributor may edit/control their OWN templates; maintainer+ may edit any.
            can_edit_template = self.app_context.can_edit_template(selected_template)
            if can_edit_template:
                menu.addAction(self.dlg.template_rename_action)
                # NB: "Update search parameters" is offered only from *inside* the template
                # (below), where the filter widgets reflect the template (populated on open).
                # In this project-list selection they hold unrelated values, so it is not shown.
            # Add pause/resume/restart based on template status. Run-state control follows the
            # same template-edit rights (maintainer+, or a contributor on their own template).
            can_control = can_edit_template
            # A FAILED template can still be isActive, so check FAILED first (mirrors
            # ProcessingTemplateDTO.table_status precedence): it offers Restart, not Pause.
            if selected_template.is_failed:
                self.dlg.template_restart_action.setEnabled(can_control)
                menu.addAction(self.dlg.template_restart_action)
            elif selected_template.isActive:
                self.dlg.template_pause_action.setEnabled(can_control)
                menu.addAction(self.dlg.template_pause_action)
            else:
                self.dlg.template_resume_action.setEnabled(can_control)
                menu.addAction(self.dlg.template_resume_action)
            return

        # Processing selection: show processing-related actions.
        if not selected_processing:
            return

        menu.addAction(self.dlg.save_result_action)
        menu.addAction(self.dlg.download_aoi_action)
        menu.addAction(self.dlg.see_details_action)

        if self.app_context.user_role.can_delete_rename_review_processing:
            menu.addAction(self.dlg.processing_update_action)

        if self.app_context.user_role.can_start_processing:
            menu.addAction(self.dlg.processing_restart_action)
            menu.addAction(self.dlg.processing_duplicate_action)

    def show_selected_details(self):
        """Open details based on selected entity type."""
        template = self.processing_service.selected_template()
        if template and not self.processing_service.selected_processing():
            self.show_template_details_and_navigation(template)
            return
        self.show_details()

    def on_processings_selection_changed(self):
        """Refresh the Start button for the new processings-table selection (it resolves the
        selected template/processing itself)."""
        self.update_start_processing_button_state()
        self.update_delete_button_state()

    def update_delete_button_state(self):
        """Contributor-only: the Delete button follows the selection — enabled only when every
        selected row is a template the contributor owns (they may delete their own templates but
        never a processing). Other roles keep the fixed, role-based state from
        ``enable_shared_project``, so this leaves them untouched."""
        if self.app_context.user_role != UserRole.contributor:
            return
        can_delete = self.processing_service.all_selected_templates_editable()
        self.dlg.deleteProcessings.setEnabled(can_delete)
        self.dlg.deleteProcessings.setToolTip(
            "" if can_delete
            else self.tr("Contributors can only delete their own planned processings"))

    def update_start_processing_button_text(self):
        # Mirror what the start action actually does: "Start planned processing" only when a
        # template run would happen (template selected + imagery-search source + its results open).
        if self.processing_service.template_to_run():
            self.dlg.startProcessing.setText(self.tr("Start planned processing"))
        else:
            self.dlg.startProcessing.setText(self.tr("Start processing"))

    def update_start_processing_button_state(self):
        """Render start button text and enforce planned-processing image selection gate."""
        self.update_start_processing_button_text()
        error = self.processing_service.planned_processing_selection_error()
        if error:
            self.dlg.disable_processing_start(reason=error, clear_area=False)
            return

        # No gate error: re-enable the button and clear any planned-processing reason label.
        self.dlg.startProcessing.setEnabled(True)
        planned_reason = self.tr("Select one or more images in search results to start planned processing")
        if self.dlg.processingProblemsLabel.text() == planned_reason:
            self.dlg.processingProblemsLabel.clear()

    def _template_single_data_provider(self, template) -> Optional[str]:
        """The template's sole search data provider, used to backfill an image's providerName
        when the backend returns it null. ``None`` when the template searches zero or several
        providers (then we cannot attribute an image to one)."""
        if not template:
            return None
        search_params = getattr(template, "searchParams", None)
        if isinstance(search_params, SearchParams):
            providers = search_params.dataProviders
        elif isinstance(search_params, dict):
            providers = search_params.get("dataProviders")
        else:
            providers = None
        providers = [p for p in (providers or []) if p]
        return providers[0] if len(providers) == 1 else None

    def get_selected_template_callback(self, response: QNetworkReply, template=None):
        """Render a template's search results in the search table.

        ``template`` is passed explicitly because inside the in-template view the table
        selection points at AOIs/processings, not the template row.
        """
        response_json = json.loads(response.readAll().data())
        if not response_json.get("images"):
            self.dlg.metadataTable.clearContents()
            self.dlg.metadataTable.setRowCount(0)
            self.app_context.open_template_results_id = None
            self.alert(self.tr("No images was found"), QMessageBox.Information)
            return
        if template is None:
            template = self.processing_service.selected_template()
        template_group_name = str(template.name) if template else None
        # Mark these results as belonging to this template, so a "Start" runs a planned processing.
        self.app_context.open_template_results_id = str(template.id) if template else None
        response_data = ImageCatalogResponseSchema(**response_json)
        images = response_data.images
        geoms = response_data.as_geojson()
        # Template search images may omit per-image providerName; without it a planned
        # processing (and its cost) cannot resolve `dataProvider` and the backend rejects the
        # request. Backfill from the template's own searchParams.dataProviders when it searches
        # a single provider (multi-provider templates rely on the backend providing it).
        template_provider = self._template_single_data_provider(template)
        for position, feature in enumerate(geoms.get("features", ())):
            props = feature.setdefault("properties", {})
            props["local_index"] = position
            if not props.get("providerName") and template_provider:
                props["providerName"] = template_provider
        # Footprints must keep the real providerName/productType so that a planned
        # processing started from these results can resolve its source params (dataProvider).
        self._store_template_search_footprints(geoms, template_group_name=template_group_name)
        # Retain the raw results (for the instant local filter) and the template's own params as
        # the widen (!) baseline; template results are filtered client-side, not server-side.
        self.app_context.search_result_geojson = geoms
        self.app_context.search_baseline_filters = self._template_filter_baseline(template)
        # Built-in Qt column sorting stays OFF: search order is server-driven (regular search) or
        # local-filter-driven (templates); only SEARCH_SORT_FIELDS headers re-sort, server-side.
        self.dlg.fill_metadata_table(geoms, sort=False)
        # Keep the image DTOs (they carry isNew) keyed by id so mark-seen reads truth.
        self.template_search_images = {str(image.id): image for image in images}
        # New images are flagged with an icon in the leftmost column (not by editing text).
        self._apply_new_image_markers()
        # Toggle/wire the search pager for the template results (T6).
        self._update_search_pager(response_data.total, response_data.limit, response_data.offset)

    def _store_template_search_footprints(self,
                                          geoms: dict,
                                          template_group_name: Optional[str] = None) -> None:
        """Build the template search-results footprint layer.

        Two responsibilities, mirroring a regular imagery search:
        * populate ``app_context.search_footprints`` (QgsFeatures keyed by ``local_index``)
          so a planned processing started from these results resolves its source params
          (``dataProvider`` comes from the footprint ``providerName``; otherwise the
          backend rejects creation with HTTP 400);
        * add the styled footprint layer to the map under the template's group so the
          user can preview image footprints and request imagery previews.
        """
        self.app_context.search_footprints = {}
        provider = self.imagery_search_provider
        if not provider:
            return
        filename = provider.save_search_layer(self.app_context.temp_dir, geoms)
        if not filename:
            return
        # Drop the previous footprint layer so repeated searches don't stack duplicates.
        if getattr(self.app_context, 'metadata_layer', None) is not None:
            try:
                self.app_context.project.removeMapLayer(self.app_context.metadata_layer)
            except (AttributeError, RuntimeError):
                pass
        layer = QgsVectorLayer(filename, f"{provider.name} metadata", "ogr")
        if not layer.isValid():
            self.app_context.metadata_layer = None
            return
        layer.loadNamedStyle(os.path.join(self.plugin_dir, 'static', 'styles', 'metadata.qml'))
        # Register as the current search-metadata layer BEFORE adding it to the project, so
        # the AOI-area monitor (which reacts to layersAdded) recognizes and skips it.
        self.app_context.metadata_layer = layer
        if template_group_name:
            target_group = self._template_group_target(template_group_name)
            self.app_context.project.addMapLayer(layer, addToLegend=False)
            # Append (bottom) so the search-results footprints sit below the AOI/processing
            # subgroups rather than on top of them.
            target_group.addLayer(layer)
        else:
            self.result_loader.add_layer(layer=layer)
        # Selecting a footprint on the map selects the matching table row (and triggers preview).
        self.app_context.meta_layer_table_connection = layer.selectionChanged.connect(
            self.sync_layer_selection_with_table)
        self.app_context.search_footprints = {
            feature["local_index"]: feature for feature in layer.getFeatures()
        }

    def _aoi_ids_from_template(self, template) -> List[str]:
        """Extract AOI IDs from template searchParams.aoiDetails features."""
        search_params = template.searchParams or {}
        if isinstance(search_params, dict):
            aoi_details = search_params.get("aoiDetails", {})
        else:
            aoi_details = search_params.aoiDetails

        if not aoi_details:
            return []

        ids = []
        for feature in aoi_details.get("features", []):
            aoi_id = feature.get("id") or feature.get("properties", {}).get("id")
            if aoi_id:
                ids.append(str(aoi_id))
        return ids

    def show_template_details_and_navigation(self, template):
        """Show template summary. The processings count is fetched from the
        ``/processings`` endpoint (aoiDetails links are not always populated)."""
        self.processing_service.api.get_template_processings(
            template_id=template.id,
            callback=lambda response: self._show_template_details_callback(template, response),
        )

    def _show_template_details_callback(self, template, response: QNetworkReply):
        try:
            data = json.loads(response.readAll().data())
            items = data.get("results") if isinstance(data, dict) else data
            linked_count = len([i for i in (items or []) if isinstance(i, dict)])
        except Exception:
            linked_count = 0
        new_images = template.newImagesCount or 0
        local_created_at = template.createdAt.astimezone()
        local_active_until = template.activeUntil.astimezone()

        details = self.tr(
            "<b>{name}</b><br/>"
            "<b>Status:</b> {status}<br/>"
            "<b>Created:</b> {created}<br/>"
            "<b>Active Until:</b> {active_until}<br/>"
            "<b>Linked processings:</b> {linked}<br/>"
            "<b>New images:</b> {new_images}"
        ).format(
            name=template.name,
            status=template.status,
            created=local_created_at.strftime('%Y-%m-%d %H:%M'),
            active_until=local_active_until.strftime('%Y-%m-%d %H:%M'),
            linked=linked_count,
            new_images=new_images,
        )

        alert(details, QMessageBox.Information)

    def select_template_processings(self):
        """Menu action: load AOI/processing layers for the selected template."""
        template = self.processing_service.selected_template()
        if not template or self.processing_service.selected_processing():
            return
        # Hydrate first (the list view's template omits aoiDetails), then draw layers.
        self.processing_service.hydrate_template(template, self._load_template_layers)

    def _load_template_layers(self, template):
        """Draw, per AOI, a subgroup named after the AOI containing the AOI polygon (blue)
        and each of its processings' footprints (green), all from the template's
        ``aoiDetails`` (no extra requests)."""
        if not template:
            return
        template_group_name = str(template.name)
        for aoi in template.aoi_dtos():
            subgroup_name = self.tr("AOI: {name}").format(name=aoi.display_name)
            if aoi.geometry:
                self._add_geojson_aoi_layer(
                    features=[{"type": "Feature", "geometry": aoi.geometry, "properties": {}}],
                    layer_name=aoi.display_name,
                    style_name='aoi_template_blue.qml',
                    template_group_name=template_group_name,
                    subgroup_name=subgroup_name,
                    aoi_id=aoi.id,
                )
            for link in aoi.processings:
                if not link.geometry:
                    continue
                self._add_geojson_aoi_layer(
                    features=[{"type": "Feature", "geometry": link.geometry, "properties": {}}],
                    layer_name=link.processingName or str(link.processingId),
                    style_name='aoi_template_processing_green.qml',
                    template_group_name=template_group_name,
                    subgroup_name=subgroup_name,
                )

    def _no_aoi_subgroup_name(self) -> str:
        return self.tr("No AOI")

    def on_template_processings_loaded(self, template) -> None:
        """Once a template's processings load, create the (initially empty) 'No AOI' group if any
        processing is not bound to an AOI. Each such AOI is fetched and added lazily when the user
        single-clicks its row (see on_no_aoi_processing_clicked) — no bulk requests on open."""
        if not template or not self.processing_service.no_aoi_processing_ids():
            return
        self._template_group_target(str(template.name), self._no_aoi_subgroup_name())

    def on_no_aoi_processing_clicked(self, *args) -> None:
        """Single-click on a 'No AOI' processing row: fetch that processing's AOI and add it to the
        'No AOI' group. No-op outside a template, for AOI/bound-processing rows, or when the AOI is
        already on the map or its request is already in flight (double-click still loads results)."""
        if not self.processing_service.in_template_mode:
            return
        processing = self.processing_service.selected_processing()
        if not processing:
            return
        pid = str(processing.id)
        if not self.processing_service.is_no_aoi_processing(pid):
            return
        if pid in self._pending_no_aoi_ids or self._no_aoi_aoi_on_map(pid):
            return
        self._pending_no_aoi_ids.add(pid)
        self.http.get(
            url=f'{self.server}/processings/{pid}/aois',
            callback=self._add_no_aoi_processing_aoi_callback,
            callback_kwargs={'pid': pid, 'name': processing.name},
            error_handler=self._add_no_aoi_processing_aoi_error,
            error_handler_kwargs={'pid': pid},
            use_default_error_handler=False,
            timeout=30,
        )

    def _add_no_aoi_processing_aoi_callback(self, response: QNetworkReply, pid: str, name: str) -> None:
        self._pending_no_aoi_ids.discard(pid)
        template = self.processing_service.active_template
        if not template or not self.processing_service.in_template_mode or self._no_aoi_aoi_on_map(pid):
            return
        # GET /processings/{id}/aois returns a JSON list of AOI objects (each with a `geometry`),
        # not a FeatureCollection — wrap each geometry into a feature the layer builder understands.
        try:
            aois = json.loads(response.readAll().data())
        except Exception:
            return
        if isinstance(aois, dict):
            aois = aois.get('aois', [])
        features = [{"type": "Feature", "geometry": aoi.get("geometry"), "properties": {}}
                    for aoi in aois if isinstance(aoi, dict) and aoi.get("geometry")]
        if not features:
            return
        layer = self._add_geojson_aoi_layer(
            features=features,
            layer_name=name or pid,
            style_name='aoi_template_processing_green.qml',
            template_group_name=str(template.name),
            subgroup_name=self._no_aoi_subgroup_name(),
        )
        if layer is not None:
            layer.setCustomProperty('mapflow/no_aoi_processing_id', str(pid))

    def _add_no_aoi_processing_aoi_error(self, response: QNetworkReply, pid: str = None) -> None:
        self._pending_no_aoi_ids.discard(pid)

    def _no_aoi_aoi_on_map(self, pid) -> bool:
        """Whether a 'No AOI' processing's AOI layer (tagged with its id) is already on the map."""
        return any(layer.customProperty('mapflow/no_aoi_processing_id') == str(pid)
                   for layer in self.app_context.project.mapLayers().values())

    def _add_aoi_to_preview_if_needed(self) -> None:
        """Overlay the search AOI on a preview — but not inside a template, where the AOI is
        already drawn as its own layer, so the clone would just duplicate it (feedback 1)."""
        if self.processing_service.in_template_mode:
            return
        self.result_loader.add_aoi_to_preview()

    def _relocate_preview_to_template_group(self, layer) -> None:
        """In the in-template view, move a freshly added preview layer into the template's
        map group, above the search-results footprints and below the AOI subgroups, so the
        precedence is AOIs (top) > previews > search results (bottom)."""
        service = self.processing_service
        if not layer or not service.in_template_mode or not service.active_template:
            return
        try:
            template_group = self._template_group_target(str(service.active_template.name))
            root = self.app_context.project.layerTreeRoot()
            node = root.findLayer(layer.id())
            if node is None or template_group is None:
                return
            footprints_layer = getattr(self.app_context, 'metadata_layer', None)
            footprints_id = footprints_layer.id() if footprints_layer else None
            children = template_group.children()
            # Default to the bottom; otherwise insert directly above the footprints layer
            # (which itself sits below the AOI/processing subgroups).
            insert_index = len(children)
            for i, child in enumerate(children):
                if isinstance(child, QgsLayerTreeLayer) and child.layerId() == footprints_id:
                    insert_index = i
                    break
            template_group.insertChildNode(insert_index, node.clone())
            (node.parent() or root).removeChildNode(node)
        except (AttributeError, RuntimeError):
            return

    def _add_geojson_aoi_layer(self,
                               features: list,
                               layer_name: str,
                               style_name: str,
                               template_group_name: Optional[str] = None,
                               subgroup_name: Optional[str] = None,
                               reference_layer_id: Optional[str] = None,
                               aoi_id: Optional[str] = None) -> Optional[QgsVectorLayer]:
        if not features:
            return None
        aoi_layer = QgsVectorLayer('Polygon?crs=epsg:4326', layer_name, 'memory')
        # Tag the AOI's own polygon layer with its id so "Update selected AOI" can find and edit
        # this exact layer in place (processing-footprint layers are left untagged).
        if aoi_id is not None:
            aoi_layer.setCustomProperty('mapflow/aoi_id', str(aoi_id))
        provider = aoi_layer.dataProvider()
        qgs_features = []
        for feature in features:
            geom_dict = feature.get("geometry")
            if not geom_dict:
                continue
            try:
                ogr_geom = ogr.CreateGeometryFromJson(json.dumps(geom_dict))
                if not ogr_geom:
                    continue
                qgs_geom = QgsGeometry.fromWkt(ogr_geom.ExportToWkt())
                qgs_feat = QgsFeature()
                qgs_feat.setGeometry(qgs_geom)
                qgs_features.append(qgs_feat)
            except Exception as e:
                # Per-feature, inside a loop: no traceback, or one malformed response
                # buries the panel in near-identical stack dumps.
                logger.warning("Skipping a search feature that failed to parse: %s", e)
                continue
        if not qgs_features:
            return None
        provider.addFeatures(qgs_features)
        aoi_layer.updateExtents()

        root = self.app_context.project.layerTreeRoot()
        if template_group_name:
            target_group = self._template_group_target(template_group_name, subgroup_name)
            self.app_context.project.addMapLayer(aoi_layer, addToLegend=False)
            target_group.insertLayer(0, aoi_layer)
        elif reference_layer_id:
            root = self.app_context.project.layerTreeRoot()
            ref_node = root.findLayer(reference_layer_id)
            if ref_node and ref_node.parent():
                self.app_context.project.addMapLayer(aoi_layer, addToLegend=False)
                ref_node.parent().insertLayer(0, aoi_layer)
            else:
                self.app_context.project.addMapLayer(aoi_layer)
        else:
            self.app_context.project.addMapLayer(aoi_layer)

        aoi_layer.loadNamedStyle(os.path.join(self.plugin_dir, 'static', 'styles', style_name))
        # Template AOI layers are added in bulk on open; don't fire a cost request per layer,
        # and don't let them become the current processing Area (feedback 8.1) — the Area is
        # set from the AOI table selection (see sync_processing_area_to_selected_aois).
        self.add_to_layers(aoi_layer, recompute_cost=False, set_current=False)
        return aoi_layer

    def _template_group_target(self,
                               template_group_name: str,
                               subgroup_name: Optional[str] = None):
        """Find or create the ``Mapflow > <template name> [> <subgroup>]`` layer-tree group
        and return the node new layers should be inserted into.

        The Mapflow group is created here when missing so the template group is nested under it
        from the very first (template-open) call. Previously the open path fell back to the root
        because the Mapflow group did not exist yet, and a later preview — by which point the
        group had been created — added a SECOND template group under it (feedback 4.1). If the
        user has deleted the Mapflow group (the result loader then adds to root), respect that
        and place template groups at the root too, keeping a single path."""
        root = self.app_context.project.layerTreeRoot()
        mapflow_group_name = self.app_context.settings.value('layerGroup') or self.app_context.plugin_name
        mapflow_group = root.findGroup(mapflow_group_name)
        if mapflow_group is None and getattr(self.result_loader, 'add_layers_to_group', True):
            mapflow_group = root.insertGroup(0, mapflow_group_name)
            self.app_context.settings.setValue('layerGroup', mapflow_group_name)
        parent_group = mapflow_group if mapflow_group else root
        template_group = parent_group.findGroup(template_group_name)
        if not template_group:
            template_group = parent_group.insertGroup(0, template_group_name)
        if subgroup_name:
            subgroup = template_group.findGroup(subgroup_name)
            if not subgroup:
                subgroup = template_group.insertGroup(0, subgroup_name)
            return subgroup
        return template_group

    def show_template_search_results(self):
        """Menu action: fill the imagery-search table with the selected template's results."""
        template = self.processing_service.selected_template()
        if not template or self.processing_service.selected_processing():
            return
        # Explicit "See search results" action: bring the imagery-search tab to front.
        self._load_template_search(template, switch_tab=True)

    def _load_template_search(self, template, aoi_ids=None, switch_tab=False, offset=0):
        """Fill the imagery-search table with the template's search results.

        ``aoi_ids`` restricts the results to specific AOIs (S7: filter by selected AOI);
        when ``None`` all of the template's AOIs are used. ``switch_tab`` brings the
        imagery-search tab to front — only the explicit menu action does so; entering a
        template or filtering by AOI must not steal focus from the processings tab.
        ``offset`` selects the results page: entering a template or changing the AOI filter
        resets to the first page (offset 0); the search pager passes a page offset (T6).
        """
        if not template:
            return
        if switch_tab:
            imagery_search_tab = self.dlg.tabWidget.findChild(QWidget, "providersTab")
            if imagery_search_tab:
                self.dlg.tabWidget.setCurrentWidget(imagery_search_tab)

        self.search_page_offset = max(0, offset)
        if aoi_ids is None:
            aoi_ids = self._aoi_ids_from_template(template)
        # Template results are fetched WITHOUT date/cloud server-side filters: those (and the
        # intersection %) are applied instantly on the client (apply_local_filter). Persisting
        # them to the template is done separately via the "Update template" button. Only the
        # selected-AOI scoping (aoi_ids) stays server-side (it decides which AOIs to search).
        self.processing_service.api.get_template_images(
            template_id=template.id,
            callback=lambda response: self.get_selected_template_callback(response, template),
            limit=self.search_page_limit,
            offset=self.search_page_offset,
            aoi_ids=aoi_ids or None,
            sort_by=self._search_sort_by,
            sort_order=self._search_sort_order,
        )

    def _load_template_search_page(self, offset: int):
        """Re-fetch the active template's search results at ``offset``, preserving the current
        AOI filter — the search pager's next/prev inside a template (T6)."""
        template = self.processing_service.active_template
        if not template:
            return
        aoi_ids = list(self._template_search_aoi_filter) if self._template_search_aoi_filter else None
        self._load_template_search(template, aoi_ids=aoi_ids, offset=offset)

    # ==================== AOI edit/draw/add sessions ==================== #
    def add_aoi_from_layer_dialog(self):
        """Add AOI(s) from existing polygon layer(s) chosen in a multi-select dialog."""
        template = self.processing_service.active_template
        if not template or self._aoi_session is not None:
            return
        layers = self._selectable_aoi_layers()
        if not layers:
            self.alert(self.tr("There are no polygon layers to add as AOIs. Draw one on the map "
                               "or load a vector layer first."), QMessageBox.Information)
            return
        dialog = SelectAoiLayersDialog(self.dlg)
        dialog.setup(layers)
        if not dialog.exec():
            return
        selected_ids = dialog.selected_layer_ids()
        if not selected_ids:
            return
        try:
            features = []
            for layer_id in selected_ids:
                layer = self.app_context.project.mapLayer(layer_id)
                if layer is not None:
                    features.extend(self._aoi_features_from_layer(layer))
        except ValueError as e:
            self.alert(str(e), QMessageBox.Warning)
            return
        if not features:
            self.alert(self.tr("The selected layer(s) have no polygon features to add."),
                       QMessageBox.Warning)
            return
        aois = [AddSingleAoiSchema(geometry=f["geometry"], name=f["properties"].get("name"))
                for f in features]
        self.processing_service.api.add_aois(
            template_id=template.id,
            data=AddAoisSchema(aois=aois),
            callback=self.processing_service.aoi_changed_callback,
            error_handler=self.processing_service.aoi_change_error_handler,
        )

    def _selectable_aoi_layers(self) -> List[QgsVectorLayer]:
        """Polygon vector layers the user can add as AOIs.

        Only the plugin's own *display* layers are hidden: the active template's group (the AOI
        polygons + processing footprints + template search metadata), the current search-metadata
        layer, preview layers, and the active draw session's temp layer. The user's own AOI layers
        (which live directly under the Mapflow group after "Use as AOI") stay selectable — hiding
        the whole Mapflow group is what left only the stray root layer visible before."""
        project = self.app_context.project
        excluded = set()
        # Layers inside the active template's group (Mapflow > <template name> > …).
        root = project.layerTreeRoot()
        mapflow_group = root.findGroup(self.app_context.settings.value('layerGroup')
                                       or self.app_context.plugin_name)
        template = self.processing_service.active_template
        if template is not None and mapflow_group is not None:
            template_group = mapflow_group.findGroup(str(template.name))
            if template_group is not None:
                excluded |= {node.layerId() for node in template_group.findLayers()}
        meta_layer = getattr(self.app_context, 'metadata_layer', None)
        if meta_layer is not None:
            try:
                excluded.add(meta_layer.id())
            except (RuntimeError, AttributeError):
                pass
        session_layer = self._aoi_session.get('layer') if self._aoi_session else None
        if session_layer is not None:
            excluded.add(session_layer.id())

        result = []
        for layer in project.mapLayers().values():
            if layer.id() in excluded:
                continue
            name = layer.name() or ''
            if name.endswith(' preview') or name.endswith(' metadata'):
                continue
            # Template AOI display layers are tagged; never offer them as sources.
            if layer.customProperty('mapflow/aoi_id'):
                continue
            if isinstance(layer, QgsVectorLayer) and layer_utils.is_polygon_layer(layer):
                result.append(layer)
        return result

    def start_update_aoi_session(self):
        """'Update selected AOI': edit the selected AOI's polygon on the map (in place)."""
        if self._aoi_session is not None:
            return
        aoi = self.processing_service.selected_aoi()
        template = self.processing_service.active_template
        if not aoi or not template:
            return
        if not aoi.can_rename:  # a persisted AOI id is required to update it
            self.alert(self.tr("This AOI has no id yet and cannot be updated. "
                               "Reopen the template and try again."), QMessageBox.Information)
            return
        layer = self._find_aoi_layer(aoi.id)
        if layer is None:
            self.alert(self.tr("Could not find this AOI's layer on the map. "
                               "Reopen the template and try again."), QMessageBox.Warning)
            return
        self._begin_aoi_session(
            mode="update", layer=layer, aoi=aoi, is_temp=False, tool="vertex",
            message=self.tr("Editing AOI '{name}': move its vertices on the map, then Save AOI.")
            .format(name=aoi.display_name))

    def start_draw_aoi_session(self):
        """'Draw AOI on the map': draw a new polygon, name it on Save, then add it as an AOI."""
        if self._aoi_session is not None:
            return
        if not self.processing_service.active_template:
            return
        layer = QgsVectorLayer('Polygon?crs=epsg:4326', self.tr('New AOI'), 'memory')
        layer.loadNamedStyle(os.path.join(self.plugin_dir, 'static', 'styles', 'aoi.qml'))
        self.app_context.project.addMapLayer(layer)
        self._begin_aoi_session(
            mode="draw", layer=layer, aoi=None, is_temp=True, tool="add",
            message=self.tr("Draw the AOI polygon on the map, then Save AOI."))

    def _find_aoi_layer(self, aoi_id) -> Optional[QgsVectorLayer]:
        """The on-map AOI layer tagged with ``aoi_id`` (see ``_add_geojson_aoi_layer``)."""
        for layer in self.app_context.project.mapLayers().values():
            if layer.customProperty('mapflow/aoi_id') == str(aoi_id):
                return layer
        return None

    def _begin_aoi_session(self, mode: str, layer: QgsVectorLayer, aoi, is_temp: bool,
                           tool: str, message: str):
        """Enter an on-map AOI edit session: pause the poll, hide the panel, make ``layer``
        active + editable with the right map tool, and show the Save/Cancel bar."""
        self.processing_service.processing_fetch_timer.stop()
        self._aoi_session = {"mode": mode, "layer": layer, "aoi": aoi, "is_temp": is_temp,
                             "prev_active_layer": self.iface.activeLayer()}
        self.dlg.hide()
        self.iface.setActiveLayer(layer)
        if not layer.isEditable():
            layer.startEditing()
        if tool == "add":
            self.iface.actionAddFeature().trigger()
        else:
            vertex_action = (getattr(self.iface, "actionVertexTool", None)
                             or getattr(self.iface, "actionNodeTool", None))
            if vertex_action is not None:
                vertex_action().trigger()
        self._show_aoi_edit_bar(message)

    def _show_aoi_edit_bar(self, message: str):
        """Persistent Save AOI / Cancel bar over the map canvas (the panel is hidden)."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel(message))
        layout.addStretch(1)
        save_button = QPushButton(self.tr("Save AOI"))
        cancel_button = QPushButton(self.tr("Cancel"))
        save_button.clicked.connect(self._save_aoi_session)
        cancel_button.clicked.connect(self._cancel_aoi_session)
        layout.addWidget(save_button)
        layout.addWidget(cancel_button)
        self._aoi_edit_bar_item = self.iface.messageBar().pushWidget(widget, Qgis.Info)

    def _save_aoi_session(self):
        session = self._aoi_session
        if not session:
            return
        try:
            if session["mode"] == "update":
                ok = self._commit_aoi_update(session["layer"], session["aoi"])
            else:
                ok = self._commit_aoi_draw(session["layer"])
        except ValueError as e:  # e.g. name too long
            self.alert(str(e), QMessageBox.Warning)
            return
        if ok:  # keep the session open on validation failure so the user can fix it
            self._end_aoi_session()

    def _cancel_aoi_session(self):
        session = self._aoi_session
        if not session:
            return
        layer = session["layer"]
        if not session["is_temp"]:
            try:
                if layer.isEditable():
                    layer.rollBack()  # discard the in-place edits
            except (RuntimeError, AttributeError):
                pass
        self._end_aoi_session()

    def _end_aoi_session(self):
        """Tear down a session: remove the bar, restore the panel/poll/tool; drop a temp layer."""
        session = self._aoi_session
        self._aoi_session = None
        if self._aoi_edit_bar_item is not None:
            try:
                self.iface.messageBar().popWidget(self._aoi_edit_bar_item)
            except (RuntimeError, AttributeError):
                pass
            self._aoi_edit_bar_item = None
        self.iface.actionPan().trigger()  # leave the add-feature/vertex tool
        if session and session.get("is_temp"):
            try:
                self.app_context.project.removeMapLayer(session["layer"].id())
            except (RuntimeError, AttributeError):
                pass
        self.dlg.show()
        self.processing_service.processing_fetch_timer.start()
        prev = session.get("prev_active_layer") if session else None
        if prev is not None:
            try:
                self.iface.setActiveLayer(prev)
            except (RuntimeError, AttributeError):
                pass

    def _commit_aoi_update(self, layer: QgsVectorLayer, aoi) -> bool:
        """POST the edited AOI geometry (as-is, single or multi-part — the per-AOI update
        endpoint accepts a generic geometry). Returns False (keeping the session open) if the
        edit left no usable geometry."""
        template = self.processing_service.active_template
        if not template or not aoi or not aoi.id:
            return False
        feats = [f for f in layer.getFeatures() if f.geometry() and not f.geometry().isEmpty()]
        if not feats:
            self.alert(self.tr("The AOI has no geometry — draw or keep at least one polygon."),
                       QMessageBox.Warning)
            return False
        geom = (feats[0].geometry() if len(feats) == 1
                else QgsGeometry.collectGeometry([f.geometry() for f in feats]))
        wgs = helpers.to_wgs84(QgsGeometry(geom), layer.crs())
        if wgs is None or wgs.isEmpty():
            self.alert(self.tr("The edited AOI has no valid geometry."), QMessageBox.Warning)
            return False
        if layer.isEditable():
            layer.commitChanges()  # reflect the edit on the map until the server refresh arrives
        self.processing_service.api.update_aoi(
            template_id=template.id,
            aoi_id=aoi.id,
            data=UpdateAoiSchema(geometry=json.loads(wgs.asJson())),
            callback=self.processing_service.aoi_changed_callback,
            error_handler=self.processing_service.aoi_change_error_handler,
        )
        return True

    def _commit_aoi_draw(self, layer: QgsVectorLayer) -> bool:
        """Name the drawn polygon(s) and add them as AOI(s). Returns False if nothing was drawn."""
        template = self.processing_service.active_template
        if not template:
            return False
        if layer.isEditable():
            layer.commitChanges()  # move drawn features from the edit buffer into the provider
        features = self._aoi_features_from_layer(layer)
        if not features:
            self.alert(self.tr("Draw at least one polygon before saving."), QMessageBox.Warning)
            return False
        name, ok = QInputDialog.getText(self.iface.mainWindow(),
                                        self.tr("Name the AOI"), self.tr("AOI name:"))
        if not ok:
            return False  # keep the session open so the drawing is not lost
        name = (name or "").strip()
        if name and len(name) > AOI_NAME_MAX_LENGTH:
            self.alert(self.tr("AOI name must not exceed {limit} characters.").format(
                limit=AOI_NAME_MAX_LENGTH), QMessageBox.Warning)
            return False
        aois = [AddSingleAoiSchema(geometry=f["geometry"], name=(name or None)) for f in features]
        self.processing_service.api.add_aois(
            template_id=template.id,
            data=AddAoisSchema(aois=aois),
            callback=self.processing_service.aoi_changed_callback,
            error_handler=self.processing_service.aoi_change_error_handler,
        )
        return True

    def filter_search_by_selected_aoi(self):
        """S7: inside a template, selecting one or more AOIs filters the imagery-search
        results (table and footprint layer) to images intersecting any of the selected AOIs;
        de-selecting all AOIs (or selecting a processing) restores all of the template's
        results."""
        if not self.processing_service.in_template_mode:
            return
        template = self.processing_service.active_template
        if not template:
            return
        selected_ids = frozenset(
            str(aoi.id) for aoi in self.processing_service.selected_aois() if aoi and aoi.id
        )
        # Only reload when the effective filter actually changes (selection fires often).
        current = self._template_search_aoi_filter or frozenset()
        if selected_ids == current:
            return
        self._template_search_aoi_filter = selected_ids or None
        self._load_template_search(template, aoi_ids=list(selected_ids) or None)

    def sync_processing_area_to_selected_aois(self):
        """Inside a template, point the Area combo at the selected AOI(s), so the Area shown in
        the combo IS the one a processing will use — one place to look, no silent override.

        A single selection points at that AOI's own (already visible) layer; a multi-selection
        points at a visible "Selected AOIs" layer holding one feature per AOI. No-op when no AOI
        is selected, keeping the current Area (e.g. while a processing row is selected)."""
        if not self.processing_service.in_template_mode:
            return
        aois = [aoi for aoi in self.processing_service.selected_aois() if aoi and aoi.id]
        selected_ids = frozenset(str(aoi.id) for aoi in aois)
        # Selection signals fire often; only rebuild when the set actually changes.
        if selected_ids == (self._processing_area_aoi_filter or frozenset()):
            return
        layer = self._layer_for_selected_aois(aois)
        if layer is None:
            return
        self._processing_area_aoi_filter = selected_ids or None
        # layerChanged -> calculate_aoi_area_polygon_layer recomputes Area/cost from this layer.
        self.dlg.polygonCombo.setLayer(layer)

    def _layer_for_selected_aois(self, aois) -> Optional[QgsVectorLayer]:
        """The layer the Area combo should show for the current AOI selection."""
        if not aois:
            return None
        if len(aois) == 1:
            return self._find_aoi_layer(aois[0].id)
        geometries = [geom for geom in
                      (self._geometry_from_geojson(getattr(aoi, "geometry", None)) for aoi in aois)
                      if geom is not None]
        return self._rebuild_selected_aois_layer(geometries) if geometries else None

    def _rebuild_selected_aois_layer(self, geometries: List[QgsGeometry]) -> QgsVectorLayer:
        """(Re)build the visible "Selected AOIs" layer in the template group — one feature per
        selected AOI, so a processing covers exactly them and the per-processing AOI limit still
        applies. Visible on the map and in the tree (unlike the old hidden 'Selected AOI')."""
        self._remove_selected_aois_layer()
        layer = QgsVectorLayer('Polygon?crs=epsg:4326', self.tr('Selected AOIs'), 'memory')
        features = []
        for geom in geometries:
            feature = QgsFeature()
            feature.setGeometry(geom)
            features.append(feature)
        layer.dataProvider().addFeatures(features)
        layer.updateExtents()
        layer.loadNamedStyle(os.path.join(self.plugin_dir, 'static', 'styles', 'aoi.qml'))
        template = self.processing_service.active_template
        group = self._template_group_target(str(template.name)) if template else None
        if group is not None:
            self.app_context.project.addMapLayer(layer, addToLegend=False)
            group.insertLayer(0, layer)
        else:
            self.app_context.project.addMapLayer(layer)
        # Register it as an AOI layer so it is selectable in the combo (not excepted).
        self.add_to_layers(layer, recompute_cost=False, set_current=False)
        self._selected_aois_layer_id = layer.id()
        return layer

    @staticmethod
    def _geometry_from_geojson(geom_dict) -> Optional[QgsGeometry]:
        """Build a QgsGeometry from a GeoJSON geometry mapping (as carried in aoiDetails)."""
        if not geom_dict:
            return None
        try:
            ogr_geom = ogr.CreateGeometryFromJson(json.dumps(geom_dict))
        except Exception:
            return None
        if not ogr_geom:
            return None
        geom = QgsGeometry.fromWkt(ogr_geom.ExportToWkt())
        return geom if not geom.isEmpty() else None

    def _remove_selected_aois_layer(self):
        """Drop the multi-selection "Selected AOIs" layer (on a new selection or on leaving the
        template). Single-AOI selections point at the AOI's own layer, so there is nothing to
        clean up for them."""
        layer_id = self._selected_aois_layer_id
        self._selected_aois_layer_id = None
        if not layer_id:
            return
        try:
            layer = self.app_context.project.mapLayer(layer_id)
            if layer is not None:
                self.remove_from_layers(layer)
            self.app_context.project.removeMapLayer(layer_id)
        except (RuntimeError, KeyError, AttributeError):
            pass

    def select_processing_in_table(self, processing_id: str):
        """Select processing row by ID and open processing details."""
        id_column_index = self.config.PROCESSING_TABLE_ID_COLUMN_INDEX
        id_items = self.dlg.processingsTable.findItems(str(processing_id), Qt.MatchExactly)

        for item in id_items:
            if item.column() != id_column_index:
                continue
            row = item.row()
            self.dlg.processingsTable.clearSelection()
            self.dlg.processingsTable.selectRow(row)
            self.dlg.processingsTable.scrollToItem(item)
            self.show_details()
            return

    def create_aoi_layer_from_map(self, action: QAction):
        aoi_geometry = helpers.to_wgs84(
            QgsGeometry.fromRect(self.iface.mapCanvas().extent()),
            self.app_context.project.crs()
        )
        aoi_layer = QgsVectorLayer('Polygon?crs=epsg:4326',
                                   f'AOI_{self.aoi_layer_counter}',
                                   'memory')
        aoi = QgsFeature()
        aoi.setGeometry(aoi_geometry)
        aoi_layer.dataProvider().addFeatures([aoi])
        aoi_layer.updateExtents()
        aoi_layer.loadNamedStyle(os.path.join(self.plugin_dir, 'static', 'styles', 'aoi.qml'))
        self.aoi_layer_counter += 1
        self.result_loader.add_layer(aoi_layer)
        self.add_to_layers(aoi_layer)
        self.iface.setActiveLayer(aoi_layer)
    
    def create_aoi_layer_from_imagery(self, action: QAction):
        image = self.data_catalog_service.selected_image()
        mosaic = self.data_catalog_service.selected_mosaic()
        if image:
            aoi_geometry = QgsGeometry().fromWkt(image.footprint)
        elif mosaic:
            aoi_geometry = QgsGeometry().fromWkt(mosaic.footprint)
        else:
            self.dlg.disable_processing_start(reason=self.tr('Choose imagery collection or image to start processing'),
                                              clear_area=True)
            aoi_geometry = None
            return
        aoi_layer = QgsVectorLayer('Polygon?crs=epsg:4326',
                                   f'AOI_{self.aoi_layer_counter}',
                                   'memory')
        aoi = QgsFeature()
        aoi.setGeometry(aoi_geometry)
        aoi_layer.dataProvider().addFeatures([aoi])
        aoi_layer.updateExtents()
        aoi_layer.loadNamedStyle(os.path.join(self.plugin_dir, 'static', 'styles', 'aoi.qml'))
        self.aoi_layer_counter += 1
        self.result_loader.add_layer(aoi_layer)
        self.add_to_layers(aoi_layer)
        self.iface.setActiveLayer(aoi_layer)

    def create_editable_aoi_layer(self, action: QAction):
        aoi_layer = QgsVectorLayer('Polygon?crs=epsg:4326',
                                   f'AOI_{self.aoi_layer_counter}',
                                   'memory')
        aoi_layer.startEditing()
        aoi_layer.loadNamedStyle(os.path.join(self.plugin_dir, 'static', 'styles', 'aoi.qml'))
        self.aoi_layer_counter += 1
        self.result_loader.add_layer(aoi_layer)
        self.add_to_layers(aoi_layer)
        self.iface.setActiveLayer(aoi_layer)
        self.iface.actionAddFeature().trigger()

    def filter_aoi_layers(self):
        if self.dlg.useAllVectorLayers.isChecked():
            # We exclude search metadata layers from AOI layers list because they are big, crowded
            # and lead to topology errors
            if self.app_context.search_provider:
                return [layer for layer in self.app_context.project.mapLayers().values()
                             if self.app_context.search_provider.name + ' metadata' == layer.name()]
            else:
                return []
        else:
            return [layer for layer in self.app_context.project.mapLayers().values() if layer not in self.app_context.aoi_layers]

    def on_options_change(self):
        wd_name = self.dlg.modelCombo.currentText()
        wd = self.app_context.get_workflow_def(wd_name)
        if not wd:
            return
        enabled_blocks = self.dlg.enabled_blocks()
        self.dlg.show_wd_price(wd_price=wd.get_price(enable_blocks=enabled_blocks),
                               wd_description=wd.description,
                               display_price=self.app_context.billing_type == BillingType.credits)
        self.save_options_settings(wd, enabled_blocks)
        if self.app_context.billing_type == BillingType.credits:
            self.processing_service.update_processing_cost()

    def on_model_change(self, 
                        index: Optional[int] = None) -> None:
        wd_name = self.dlg.modelCombo.currentText()
        wd = self.app_context.get_workflow_def(wd_name)
        self.provider_service.set_available_imagery_sources(wd_name)
        if not wd:
            return
        self.show_wd_options(wd)
        self.dlg.show_wd_price(wd_price=wd.get_price(enable_blocks=self.dlg.enabled_blocks()),
                               wd_description=wd.description,
                               display_price=self.app_context.billing_type == BillingType.credits)
        if len(wd.blocks) == 0: # and for wd with options it will update cost later
            if self.app_context.billing_type == BillingType.credits:
                # todo: here was a toggle to not call if from setup_workflow_defs, but maybe not so important?
                self.processing_service.update_processing_cost()

    def show_wd_options(self, wd: WorkflowDef):
        self.dlg.clear_model_options()
        for block in wd.optional_blocks:
            self.dlg.add_model_option(block.displayName, checked=bool(self.app_context.settings.value(f"wd/{wd.id}/{block.name}", False)))
        # Other wigets are disabled before the appearence of these checkboxes, so we do it here separately after adding them
        can_start_processing = True
        if self.app_context.user_role:
            can_start_processing = self.app_context.user_role.can_start_processing
        self.dlg.enable_model_options(can_start_processing)

    def save_options_settings(self, wd: WorkflowDef, enabled_blocks: List[bool]):
        enabled_blocks_dict = wd.get_enabled_blocks(enabled_blocks)
        for block in enabled_blocks_dict:
            name = block["name"]
            enabled = block["enabled"]
            self.app_context.settings.setValue(f"wd/{wd.id}/{name}", enabled)

    def apply_local_filter(self, *_) -> None:
        """Instantly filter the current search/template results by the filter widgets
        (intersection %, cloud cover, date range) without a server request.

        Unfit rows are NOT removed: they are greyed-out, made non-selectable and sorted to the
        bottom of the page (so pages keep their expected size and the user can see that some
        images were filtered), and their footprints are hidden from the result layer. Runs on
        every filter-widget change and after each table (re)fill, and refreshes the widen (!)
        indicator. Applies to both regular search and template results — templates no longer
        filter server-side; only "Update template" persists filter values."""
        if self._suppress_local_filter:
            return
        geoms = self.app_context.search_result_geojson
        if not geoms or not geoms.get("features"):
            self._reconnect_cell_preview()
            self._update_widen_indicator()
            return
        features = geoms["features"]
        # Compute fit/unfit from the SAME GeoJSON properties that fill the table, so the greyed
        # rows always match the values shown in the Cloud %/Date columns (reading the OGR layer
        # instead risked field-type mismatches, greying rows that looked fine).
        unfit = self._unfit_local_indices(features)
        # Skip the (heavier) re-fill/re-mark when the outcome is unchanged — e.g. dragging a
        # slider through a range where no image flips fit<->unfit. Invalidated automatically when
        # a new search replaces ``search_result_geojson`` (a different object).
        if unfit == self._last_unfit_set and geoms is self._last_filtered_geoms:
            self._update_widen_indicator()
            return
        self._last_unfit_set = set(unfit)
        self._last_filtered_geoms = geoms
        # Order: fit rows first, unfit rows last. WITHIN each group keep the incoming order — the
        # server sort (sortBy/sortOrder) for both regular AND template search — so header-click
        # sorting actually shows in the table. Built-in column sorting is OFF so the order sticks
        # (otherwise the table would re-sort and the unfit rows jump back up).
        fit_features = [
            f for f in features if f.get("properties", {}).get("local_index") not in unfit]
        unfit_features = [
            f for f in features if f.get("properties", {}).get("local_index") in unfit]
        reordered = dict(geoms)
        reordered["features"] = fit_features + unfit_features
        # Re-fill in the new order. Preview cells are generic and ``local_index`` stays bound to
        # each feature, so table<->layer selection and footprint mapping are preserved. The
        # nested ``metadataTableFilled`` is swallowed by the re-entrancy guard.
        self._suppress_local_filter = True
        try:
            self.dlg.fill_metadata_table(reordered, sort=False)
        finally:
            self._suppress_local_filter = False
        # Re-filling drops the per-row 'new image' icons; restore them for template results.
        if getattr(self.processing_service, "in_template_mode", False):
            self._apply_new_image_markers()
        self._mark_unfit_rows(unfit)
        self._hide_unfit_footprints(getattr(self.app_context, "metadata_layer", None), unfit)
        self._reconnect_cell_preview()
        self._update_widen_indicator()
        # The fill above hid the sort arrow (setSortingEnabled(False)); put it back so it persists.
        self._restore_search_sort_indicator()

    def _unfit_local_indices(self, features: list) -> set:
        """``local_index`` of every result (GeoJSON feature) that FAILS the active filter
        widgets: date range, cloud cover, off-nadir angle range, provider selection / availability,
        product type (Mosaic vs Image), and (where an intersection reference exists) min intersection %. A
        per-feature parsing error never hides the row (treated as fit)."""
        from_ = self.dlg.metadataFrom.date()
        to = self.dlg.metadataTo.date()
        max_cloud_cover = self.dlg.maxCloudCover.value()
        min_intersection = self.dlg.minIntersection.value()
        min_off_nadir, max_off_nadir = self.dlg.off_nadir_range()
        off_nadir_filtered = not self.dlg.off_nadir_is_full_range()  # full 0-30 range = no filter
        provider_set = self._allowed_provider_set()  # None = show all
        product_filter = self._product_category_filter()  # None = show all
        unfit = set()
        for feature in features:
            props = feature.get("properties", {})
            local_index = props.get("local_index")
            if local_index is None:
                continue
            try:
                # Missing metadata matches any condition: user imagery (My Imagery search) has no
                # acquisition date / cloud cover, and the server already treats a NULL column as
                # satisfying every predicate — the local filter must not then demote those rows.
                acquisition_date = self._utc_date_from_iso(props.get("acquisitionDate"))
                date_ok = self._passes_optional(acquisition_date, lambda d: from_ <= d <= to)
                cloud_cover = self._to_float(props.get("cloudCover"))
                # 100% = don't filter by cloud at all.
                cloud_ok = max_cloud_cover >= 100 or self._passes_optional(
                    cloud_cover, lambda c: c <= max_cloud_cover)
                off_nadir = self._to_float(props.get("offNadirAngle"))
                # Full 0-30 range = don't filter; a missing angle passes the range check.
                off_nadir_ok = not off_nadir_filtered or self._passes_optional(
                    off_nadir, lambda a: min_off_nadir <= a <= max_off_nadir)
                if provider_set is None:
                    provider_ok = True
                else:
                    provider_name = props.get("providerName")
                    provider_ok = (provider_name is not None
                                   and str(provider_name).lower() in provider_set)
                product_ok = (product_filter is None
                              or self._product_category(props.get("productType")) in product_filter)
                # Intersection % comes from the backend (aoiIntersectionPercent, computed against
                # the searched AOI / the template's AOIs), not recomputed locally against a
                # sub-selection. 0 = don't filter; a missing value passes (like other metadata).
                if min_intersection <= 0:
                    intersection_ok = True
                else:
                    aoi_intersection = self._to_float(props.get("aoiIntersectionPercent"))
                    intersection_ok = self._passes_optional(
                        aoi_intersection, lambda pct: pct >= min_intersection)
                fit = (date_ok and cloud_ok and off_nadir_ok and provider_ok
                       and product_ok and intersection_ok)
            except Exception:
                fit = True  # never hide a row because of a parsing error
            if not fit:
                unfit.add(local_index)
        return unfit

    def _allowed_provider_set(self) -> Optional[set]:
        """Lowercased provider api-names a result may come from for the LOCAL filter, or ``None``
        for no provider filtering (show all).

        - "Search only through available providers" OFF -> ``None`` (show all).
        - ON with specific providers checked -> just those.
        - ON with none checked -> all providers available to the user
          (``app_context.search_data_providers``), so results from providers the user cannot use
          are dropped."""
        if not self.dlg.hideUnavailableResults.isChecked():
            return None
        checked = self.dlg.searchProvidersCombo.checkedItemsData()
        if checked:
            return {str(p).lower() for p in checked}
        available = self.app_context.search_data_providers or []
        return {str(p).lower() for p in available} if available else None

    def _product_category_filter(self) -> Optional[set]:
        """The product categories to KEEP ({'MOSAIC'} or {'IMAGE'}), or ``None`` when both or
        neither Mosaic/Image is checked (= all, no filter)."""
        mosaic = self.dlg.searchMosaicCheckBox.isChecked()
        image = self.dlg.searchImageCheckBox.isChecked()
        if mosaic == image:  # both or neither -> show all
            return None
        return {ProductType.mosaic.upper()} if mosaic else {ProductType.image.upper()}

    @staticmethod
    def _product_category(product_type) -> str:
        """Map a result's ``productType`` to a Mosaic/Image category: 'Mosaic' -> MOSAIC, anything
        else -> IMAGE.
        #WARNING: ``productType`` is free text (e.g. 'OPTICAL', 'Image', ''); this
        Mosaic-vs-everything-else split is a product decision and may misclassify some providers."""
        if str(product_type).strip().lower() == ProductType.mosaic.lower():
            return ProductType.mosaic.upper()
        return ProductType.image.upper()

    @staticmethod
    def _to_float(value) -> Optional[float]:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _passes_optional(value, predicate) -> bool:
        """A metadata filter clause where a missing value matches any condition: ``None`` passes,
        otherwise the row must satisfy ``predicate``. My Imagery results carry mostly-empty
        metadata (no date/cloud), which the server counts as matching every filter; the local
        filter follows the same rule so user imagery is not hidden when a filter is set."""
        return value is None or predicate(value)

    def _mark_unfit_rows(self, unfit: set) -> None:
        """Grey-out and disable (non-selectable) the rows whose image was filtered out; restore
        fit rows to normal. The row order already places the unfit rows last."""
        grey_text = QBrush(QColor(150, 150, 150))
        grey_bg = QBrush(QColor(235, 235, 235))
        table = self.dlg.metadataTable
        local_col = self.config.LOCAL_INDEX_COLUMN
        for row in range(table.rowCount()):
            key = table.item(row, local_col)
            if key is None:
                continue
            try:
                is_unfit = int(key.text()) in unfit
            except (TypeError, ValueError):
                continue
            for col in range(table.columnCount()):
                item = table.item(row, col)
                if item is None:
                    continue
                if is_unfit:
                    item.setForeground(grey_text)
                    item.setBackground(grey_bg)
                    item.setFlags(item.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsEnabled)
                else:
                    item.setForeground(QBrush())
                    item.setBackground(QBrush())
                    item.setFlags(item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)

    def _hide_unfit_footprints(self, layer: QgsVectorLayer, unfit: set) -> None:
        """Hide the filtered-out images' footprints from the result layer (subset filter),
        matching the previous behaviour where filtered geometries disappear from the map."""
        try:
            if unfit:
                ids = ', '.join(str(i) for i in sorted(unfit))
                layer.setSubsetString(f'local_index NOT IN ({ids})')
            else:
                layer.setSubsetString('')
        except (RuntimeError, AttributeError):
            pass

    def _update_widen_indicator(self) -> None:
        """Show the (!) indicator when the current filter widgets are WIDER than the filters
        that fetched the current results (relaxing them cannot surface more images without a new
        search); hide it otherwise. Its tooltip lists exactly which settings will not apply."""
        widened = self._widened_filter_messages()
        button = self.dlg.searchWidenWarning
        self._widen_details = widened
        if widened:
            button.setToolTip(self._format_widen_message(widened))
            button.setVisible(True)
        else:
            button.setToolTip("")
            button.setVisible(False)

    def _widened_filter_messages(self) -> List[str]:
        """Human-readable list of the ways the current filter widgets are wider than the
        baseline that fetched the current results (empty when none / no baseline)."""
        baseline = self.app_context.search_baseline_filters
        if not baseline:
            return []
        messages = []
        cur_from = self.dlg.metadataFrom.date()
        cur_to = self.dlg.metadataTo.date()
        base_from = baseline.get("date_from")
        base_to = baseline.get("date_to")
        if base_from is not None and cur_from < base_from:
            messages.append(self.tr("Start date {cur} is earlier than searched ({base})").format(
                cur=cur_from.toString("yyyy-MM-dd"), base=base_from.toString("yyyy-MM-dd")))
        if base_to is not None and cur_to > base_to:
            messages.append(self.tr("End date {cur} is later than searched ({base})").format(
                cur=cur_to.toString("yyyy-MM-dd"), base=base_to.toString("yyyy-MM-dd")))
        cur_cloud = self.dlg.maxCloudCover.value()
        base_cloud = baseline.get("max_cloud_cover")
        if base_cloud is not None and cur_cloud > base_cloud:
            messages.append(self.tr("Max cloud cover {cur}% is higher than searched ({base}%)").format(
                cur=cur_cloud, base=int(base_cloud)))
        cur_int = self.dlg.minIntersection.value()
        base_int = baseline.get("min_intersection")
        if base_int is not None and cur_int < base_int:
            messages.append(self.tr("Min intersection {cur}% is lower than searched ({base}%)").format(
                cur=cur_int, base=int(base_int)))
        cur_off_lo, cur_off_hi = self.dlg.off_nadir_range()
        base_off_lo = baseline.get("min_off_nadir")
        base_off_hi = baseline.get("max_off_nadir")
        if base_off_lo is not None and base_off_hi is not None \
                and (cur_off_lo < base_off_lo or cur_off_hi > base_off_hi):
            messages.append(self.tr("Off-nadir range {lo}-{hi}° is wider than searched ({blo}-{bhi}°)").format(
                lo=cur_off_lo, hi=cur_off_hi, blo=int(base_off_lo), bhi=int(base_off_hi)))
        base_products = baseline.get("product_types")
        if base_products:
            extra = [p for p in (str(pt).upper() for pt in self.selected_search_product_types())
                     if p not in base_products]
            if extra:
                messages.append(self.tr("Product type(s) not searched: {extra}").format(
                    extra=", ".join(extra)))
        base_providers = baseline.get("data_providers")
        if base_providers:
            cur_providers = self.selected_search_providers() or []
            if not cur_providers:
                messages.append(self.tr("Showing all providers, but search was limited to: {base}").format(
                    base=", ".join(base_providers)))
            else:
                extra = [p for p in cur_providers if p not in base_providers]
                if extra:
                    messages.append(self.tr("Provider(s) not searched: {extra}").format(
                        extra=", ".join(extra)))
        return messages

    @staticmethod
    def _format_widen_message(messages: List[str]) -> str:
        header = QCoreApplication.translate(
            "Mapflow",
            "These filters are wider than the last search, so they will not bring more images. "
            "Run a new Search to fetch them:")
        return header + "\n• " + "\n• ".join(messages)

    def show_widen_details(self):
        """On click of the (!) indicator, explain which filters are wider than the fetched
        results and therefore have no effect until a new search is run."""
        messages = self._widen_details or self._widened_filter_messages()
        if not messages:
            return
        self.alert(self._format_widen_message(messages), QMessageBox.Information)

    def _current_filter_baseline(self) -> dict:
        """Snapshot of the filter widgets at search time, stored as the baseline the widen (!)
        indicator compares later widget edits against."""
        off_nadir_lo, off_nadir_hi = self.dlg.off_nadir_range()
        return {
            "date_from": self.dlg.metadataFrom.date(),
            "date_to": self.dlg.metadataTo.date(),
            "max_cloud_cover": self.dlg.maxCloudCover.value(),
            "min_intersection": self.dlg.minIntersection.value(),
            "min_off_nadir": off_nadir_lo,
            "max_off_nadir": off_nadir_hi,
            "product_types": [str(pt).upper() for pt in self.selected_search_product_types()],
            "data_providers": self.selected_search_providers() or [],
            "hide_unavailable": self.dlg.hideUnavailableResults.isChecked(),
        }

    def _template_filter_baseline(self, template) -> Optional[dict]:
        """Baseline (widen indicator + Reset filters) from a template's stored searchParams. A
        field the template does not carry stays ``None`` so Reset leaves that widget untouched."""
        sp = getattr(template, "searchParams", None)
        if not sp:
            return None
        if isinstance(sp, dict):
            sp = SearchParams.from_dict(sp)
        return {
            "date_from": self._utc_date_from_iso(sp.acquisitionDateFrom),
            "date_to": self._utc_date_from_iso(sp.acquisitionDateTo),
            "max_cloud_cover": sp.maxCloudCover,
            "min_intersection": sp.minAoiIntersectionPercent,
            "min_off_nadir": sp.minOffNadirAngle,
            "max_off_nadir": sp.maxOffNadirAngle,
            "product_types": ([str(pt).upper() for pt in sp.productTypes]
                              if sp.productTypes is not None else None),
            "data_providers": list(sp.dataProviders) if sp.dataProviders is not None else None,
            "hide_unavailable": sp.hideUnavailable,
        }

    def reset_filters(self):
        """Reset the filter widgets to the parameters the current results were fetched with — a
        regular search's request params, or the open template's search params. Only params that
        were part of that request are restored; params it did not carry are left untouched. The
        local filter is re-applied afterwards (so the greying/order returns to the fetched set)."""
        self._apply_baseline_to_widgets(self.app_context.search_baseline_filters)

    def _apply_baseline_to_widgets(self, baseline: Optional[dict]) -> None:
        if not baseline:
            return
        if baseline.get("date_from") is not None:
            self.dlg.metadataFrom.setDate(baseline["date_from"])
        if baseline.get("date_to") is not None:
            self.dlg.metadataTo.setDate(baseline["date_to"])
        if baseline.get("max_cloud_cover") is not None:
            self.dlg.maxCloudCover.setValue(int(round(baseline["max_cloud_cover"])))
        if baseline.get("min_intersection") is not None:
            self.dlg.minIntersection.setValue(int(round(baseline["min_intersection"])))
        base_off_lo = baseline.get("min_off_nadir")
        base_off_hi = baseline.get("max_off_nadir")
        if base_off_lo is not None and base_off_hi is not None:
            self.dlg.set_off_nadir_range(int(round(base_off_lo)), int(round(base_off_hi)))
        products = baseline.get("product_types")
        if products is not None:
            self.dlg.searchMosaicCheckBox.setChecked(ProductType.mosaic.upper() in products)
            self.dlg.searchImageCheckBox.setChecked(ProductType.image.upper() in products)
        if baseline.get("hide_unavailable") is not None:
            self.dlg.hideUnavailableResults.setChecked(bool(baseline["hide_unavailable"]))
        providers = baseline.get("data_providers")
        if providers is not None:
            self._apply_search_providers_to_combo(providers)
        # Re-filter once against the restored widgets (some setters above may not have changed a
        # value, so their change-signal would not have fired the filter).
        self.apply_local_filter()

    def _reconnect_cell_preview(self):
        """Rewire the search table's 'Preview' cell click to a single handler.
        ``apply_local_filter`` runs on every table refill; connecting without disconnecting
        first stacks the connections, so one click fires the preview several times and adds
        several preview layers at once (feedback 4.2). Disconnect the previous connection first."""
        try:
            self.dlg.metadataTable.disconnect(self.cell_preview_connection)
        except (AttributeError, TypeError, RuntimeError):
            # no previous connection, or its underlying C++ object is gone
            pass
        self.cell_preview_connection = self.dlg.metadataTable.cellClicked.connect(
            self.preview_search_from_cell)

    def set_up_login_dialog(self) -> MapflowLoginDialog:
        """Create a login dialog, set its title and signal-slot connections."""
        dlg_login = MapflowLoginDialog(self.main_window, self.use_oauth, self.app_context.settings.value("token", ""))
        dlg_login.setWindowTitle(helpers.generate_plugin_header(self.tr("Log in ") + self.plugin_name,
                                                                     self.config.MAPFLOW_ENV,
                                                                     None, None, None))
        dlg_login.logIn.clicked.connect(self.read_mapflow_token)
        dlg_login.useOauth.toggled.connect(self.set_auth_type)
        return dlg_login

    def set_auth_type(self, use_oauth: bool = False):
        self.use_oauth = use_oauth
        self.app_context.settings.setValue("use_oauth", str(use_oauth).lower())
        self.dlg_login.set_auth_type(use_oauth=use_oauth, token = self.app_context.settings.value('token', ""))

    def on_provider_change(self) -> None:
        """Adjust max and current zoom, and update the metadata table when user selects another
        provider.

        :param index: The currently selected provider index
        """
        # This is done after area calculation, because there the provider list is updated?
        provider_index = self.dlg.providerIndex()
        provider = self.provider_service.providers[provider_index]
        self.app_context.data_provider = provider
        # Changes in search tab
        self.toggle_imagery_search(provider)
        # re-calculate AOI because it may change due to intersection of image/area
        polygon_layer = self.dlg.polygonCombo.currentLayer()
        if isinstance(provider, MyImageryProvider):
            my_imagery_tab = self.dlg.tabWidget.findChild(QWidget, "catalogTab") 
            self.dlg.tabWidget.setCurrentWidget(my_imagery_tab)
            self.area_calculator_service.calculate_aoi_area_catalog()
            self.processing_service.validate_all_processing_params(allow_empty_name=True)
            self.dlg.zoomCombo.setEnabled(False)
            self.dlg.zoomCombo.setCurrentIndex(0)
        else:
            if isinstance(provider, ImagerySearchProvider):
                self.dlg.zoomCombo.setEnabled(False)
            else:
                self.dlg.zoomCombo.setEnabled(True)
            self.area_calculator_service.calculate_aoi_area_polygon_layer(polygon_layer)
        if provider.requires_image_id:
            imagery_search_tab = self.dlg.tabWidget.findChild(QWidget, "providersTab")
            self.dlg.tabWidget.setCurrentWidget(imagery_search_tab)
        # A planned (template) start only applies with the imagery-search source, so the Start
        # button label depends on the data source: refresh it here (e.g. switching an open template
        # to My imagery must drop the "planned" wording). Text only — the enabled state is managed
        # by the validation above.
        self.update_start_processing_button_text()
    
    def on_zoom_change(self):
        """ Set chosen zoom and update cost (if it depends on zoom for provider).
        """
        if self.dlg.zoomCombo.currentIndex() != 0:
            self.app_context.settings.setValue('zoom', str(self.dlg.zoomCombo.currentText()))
        else:
            self.app_context.settings.setValue('zoom', None)
        self.processing_service.update_processing_cost()

    def save_dialog_state(self):
        """Memorize dialog element sizes & positioning to allow user to customize the look."""
        # Save main dialog size & position
        self.app_context.settings.setValue('mainDialogState', self.dlg.saveGeometry())

    # ========= Providers ============ #
    def remove_provider(self) -> None:
        """Delete a web tile provider from the list of registered providers.

        Is called by clicking the red minus button near the provider dropdown list.
        """
        provider_index = self.dlg.providerCombo.currentIndex()
        provider = self.provider_service.providers[provider_index]
        if provider.is_default:
            # We want to protect built in providers!
            self.alert(self.tr("This provider is default and cannot be removed"),
                       icon=QMessageBox.Warning)
            return
        # Ask for confirmation
        elif self.alert(self.tr('Permanently remove {}?').format(provider.name),
                        icon=QMessageBox.Question):
            self.provider_service.user_providers.remove(provider)
            self.provider_service.update_providers()

    def edit_provider_callback(self) -> None:
        """Add a web imagery provider or commit edits to an existing one."""
        old_provider = self.dlg_provider.current_provider
        if self.dlg_provider.result:
            new_provider = create_provider(**self.dlg_provider.result)
        else:
            # returned empty provider - i.e. nothing was changed
            return

        if not old_provider:
            # we have added new one - without current one
            if new_provider.name in self.provider_service.providers:
                self.alert(self.tr("Provider name must be unique. {name} already exists, "
                                   "select another or delete/edit existing").format(name=new_provider.name),
                           icon=QMessageBox.Warning)
                self.dlg_provider.show()
                return
            else:
                self.provider_service.user_providers.append(new_provider)
                provider_index = len(self.provider_service.providers)
        else:
            # we replace old provider with a new one
            # if self.dlg_provider.property('mode') == 'edit':  #
            provider_index = self.provider_service.providers.index(old_provider)
            user_provider_index = self.provider_service.user_providers.index(old_provider)
            if new_provider.name != old_provider.name and new_provider.name in self.provider_service.providers:
                # we do not want user to replace another provider when editing this one
                self.alert(self.tr("Provider name must be unique. {name} already exists,"
                                   " select another or delete/edit existing").format(name=new_provider.name),
                           icon=QMessageBox.Warning)
                self.dlg_provider.show()
                return
            else:
                self.provider_service.user_providers[user_provider_index] = new_provider
        self.provider_service.update_providers()
        self.dlg.setProviderIndex(provider_index)

    def add_provider(self) -> None:
        self.dlg_provider.setup(None, self.tr("Add new provider"))

    def edit_provider(self) -> None:
        """Prepare and show the provider edit dialog.
        Is called by the corresponding button.
        """
        provider = self.provider_service.providers[self.dlg.providerIndex()]
        if provider.is_default:
            self.alert(self.tr("This is a default provider, it cannot be edited"),
                       icon=QMessageBox.Warning)
        else:
            self.dlg_provider.setup(provider)

    def monitor_polygon_layer_feature_selection(self, layers: List[QgsMapLayer]) -> None:
        """Set up connection between feature selection in polygon layers and AOI area calculation.

        Since the plugin allows using a single feature withing a polygon layer as an AOI for processing,
        its area should then also be calculated and displayed in the UI, just as with a single-featured layer.
        For every polygon layer added to the project, this function sets up a signal-slot connection for
        monitoring its feature selection by passing the changes to calculate_aoi_area().

        :param layers: A list of layers of any type (all non-polygon layers will be skipped)
        """
        for layer in filter(layer_utils.is_polygon_layer, layers):
            # The current search-results footprint layer is a polygon too, but it is NOT an
            # AOI. Wiring its selection to the area calc would recompute (and re-request) the
            # processing cost a second time on every image click — skip it.
            if self._is_search_metadata_layer(layer):
                continue
            layer.selectionChanged.connect(self.area_calculator_service.calculate_aoi_area_selection)
            layer.geometryChanged.connect(self.area_calculator_service.calculate_aoi_area_layer_edited)
            layer.featureAdded.connect(self.area_calculator_service.calculate_aoi_area_layer_edited)
            layer.featuresDeleted.connect(self.area_calculator_service.calculate_aoi_area_layer_edited)

    def _is_search_metadata_layer(self, layer) -> bool:
        """True if `layer` is the current imagery-search footprints layer.

        Metadata-layer creators assign ``app_context.metadata_layer`` before adding the
        layer to the project, so this is reliable at ``layersAdded`` time.
        """
        metadata_layer = self.app_context.metadata_layer
        if metadata_layer is None:
            return False
        try:
            return layer.id() == metadata_layer.id()
        except RuntimeError:  # metadata layer was deleted
            return False

    def toggle_imagery_search(self,
                              provider):
        """
        Get necessary attributes from config and send them to MainDialogo to setup Imagery Search tab
        """
        provider_changed = self.replace_search_provider(provider)
        if not provider_changed:
            return
        # No need to re-set imagery search if the provider is not set,
        # or if search provider did not change. All search goes through the Mapflow catalog.
        columns = self.config_search_columns.METADATA_TABLE_ATTRIBUTES
        hidden_columns = (len(columns) - 1,)
        sort_by = self.config.SEARCH_DATETIME_COLUMN_INDEX
        max_zoom = self.config.MAX_ZOOM
        current_zoom = int(self.app_context.settings.value('maxZoom', self.config.DEFAULT_ZOOM))
        image_id_tooltip = self.tr(
            'If you already know which {provider_name} image you want to process,\n'
            'simply paste its ID here. Otherwise, search suitable images in the catalog below.'
        ).format(provider_name=self.app_context.search_provider.name)
        image_id_placeholder = self.tr('e.g. a3b154c40cc74f3b934c0ffc9b34ecd1')

        # If we have searched with current provider previously, we want to restore the search results as it were
        # We store the results in a temp folder, separate file for each provider
        geoms = self.app_context.search_provider.load_search_layer(self.app_context.temp_dir)
        if geoms:
            self.display_metadata_geojson_layer(
                os.path.join(self.app_context.temp_dir, self.app_context.search_provider.metadata_layer_name),
                f"{self.app_context.search_provider.name} metadata")
            # Keep the restored results available to the instant local filter (fill below emits
            # metadataTableFilled -> apply_local_filter), so switching back to a provider re-applies
            # the current filter widgets instead of showing a stale/unfiltered view.
            self.app_context.search_result_geojson = geoms
        else:
            self.clear_metadata()

        self.dlg.setup_imagery_search(provider=self.app_context.search_provider,
                                      columns=columns,
                                      hidden_columns=hidden_columns,
                                      sort_by=sort_by,
                                      preview_zoom=current_zoom,
                                      max_preview_zoom=max_zoom,
                                      more_button_name=self.config.METADATA_MORE_BUTTON_OBJECT_NAME,
                                      image_id_placeholder=image_id_placeholder,
                                      image_id_tooltip=image_id_tooltip,
                                      fill=geoms)

    def select_output_directory(self) -> str:
        """Open a file dialog for the user to select a directory where plugin files will be stored.

        Returns the selected path, or None if user closed the dialog.
        """
        path = QFileDialog.getExistingDirectory(
            QApplication.activeWindow(),
            self.tr('Select output directory')
        )
        if path:
            self.dlg.outputDirectory.setText(path)
            self.app_context.settings.setValue('outputDir', path)
            error = self.setup_tempdir()
            if error:
                # The chosen directory exists but is not usable (e.g. no write permission, or it
                # lives on an unmounted volume). Tell the user exactly why and let them pick another.
                self.alert(self.tr("Cannot use '{dir}' as the working directory:\n{error}\n\n"
                                   "Please choose another directory.").format(dir=path, error=error),
                           QMessageBox.Warning)
            return path

    def check_if_output_directory_is_selected(self) -> bool:
        """Check if the user specified an existing output dir.

        Returns True if an existing directory is specified or a new directory has been selected, else False.
        """
        if os.path.exists(self.dlg.outputDirectory.text()) or self.select_output_directory():
            return True
        self.alert(self.tr('Please, specify an existing output directory'))
        return False

    def prompt_output_directory(self, message: str) -> bool:
        """Modal prompt to set the working directory, explaining why it is needed.

        Shows `message` with 'Select directory…' / 'Later' buttons. Returns True if the user picked
        a usable directory (``temp_dir`` is now set), False if they postponed or the pick failed.
        Used both at startup (a configured directory turned out unavailable) and before any action
        that needs the directory (so 'Later' cancels that action)."""
        box = QMessageBox(QMessageBox.Warning, self.plugin_name, message, parent=self.main_window)
        box.setTextFormat(Qt.RichText)
        select_button = box.addButton(self.tr("Select directory…"), QMessageBox.AcceptRole)
        box.addButton(self.tr("Later"), QMessageBox.RejectRole)
        box.exec()
        if box.clickedButton() is not select_button:
            return False
        self.select_output_directory()  # alerts by itself if the newly picked directory is unusable
        return self.app_context.temp_dir is not None

    def ensure_output_directory(self, reason: str) -> bool:
        """Ensure a usable working directory exists before an action that writes to it.

        Returns True if results can be saved (directory set and present); if not, prompts the user
        with `reason` and returns whether they selected a usable directory (False = postponed)."""
        temp_dir = self.app_context.temp_dir
        if temp_dir is not None and temp_dir.exists():
            return True
        return self.prompt_output_directory(reason)

    def replace_search_provider(self, provider: ProviderInterface):
        if not provider:
            return False
        provider_changed = False
        try:
            provider_supports_search = provider.meta_url is not None
        except (NotImplementedError, AttributeError):
            provider_supports_search = False
        if not provider_supports_search:
            provider = self.imagery_search_provider
            # we need to deselect table to be able to use the non-search provider
        if provider != self.app_context.search_provider:
            self.app_context.search_provider = provider
            provider_changed = True
        return provider_changed

    def replace_search_provider_index(self):
        try:
            provider_supports_search = self.provider_service.providers[self.dlg.providerIndex()].meta_url is not None
        except (NotImplementedError, AttributeError):
            provider_supports_search = False

        if not provider_supports_search:
            self.dlg.setProviderIndex(self.provider_service.imagery_search_provider_index)

    def setup_metadata_search_dropdown(self):
        """Set Search button as dropdown with Search and Plan search modes."""
        self.metadata_search_mode = "search"
        self.metadata_search_menu = QMenu(self.dlg.getMetadata)
        search_action = self.metadata_search_menu.addAction(self.tr("Search"))
        plan_action = self.metadata_search_menu.addAction(self.tr("Plan search"))
        search_action.triggered.connect(lambda: self.set_metadata_search_mode("search"))
        plan_action.triggered.connect(lambda: self.set_metadata_search_mode("plan"))
        self.dlg.getMetadata.setPopupMode(QToolButton.MenuButtonPopup)
        self.dlg.getMetadata.setMenu(self.metadata_search_menu)
        self.set_metadata_search_mode("search")

    def setup_metadata_seen_dropdown(self):
        """Set Seen button as dropdown with Seen and Seen all actions."""
        self.metadata_seen_menu = QMenu(self.dlg.markSeenButton)
        self.metadata_seen_action = self.metadata_seen_menu.addAction(self.tr("Seen"))
        self.metadata_seen_all_action = self.metadata_seen_menu.addAction(self.tr("Seen all"))
        self.metadata_seen_action.triggered.connect(self.mark_selected_template_images_seen)
        self.metadata_seen_all_action.triggered.connect(self.mark_all_template_images_seen)
        self.dlg.markSeenButton.setPopupMode(QToolButton.MenuButtonPopup)
        self.dlg.markSeenButton.setMenu(self.metadata_seen_menu)
        self.dlg.markSeenButton.setDefaultAction(self.metadata_seen_action)

    def set_metadata_search_mode(self, mode: str):
        self.metadata_search_mode = mode
        self.dlg.getMetadata.setText(self.tr("Plan search") if mode == "plan" else self.tr("Search"))
        self.update_plan_search_message()

    def _select_project_for_template_message(self) -> str:
        return self.tr("Select a project to create a template")

    def update_plan_search_message(self) -> None:
        """A template must belong to a project. In plan mode without one, prompt the user in
        the cost/message label (the immediate search is never blocked, so the button stays usable)."""
        message = self._select_project_for_template_message()
        if getattr(self, "metadata_search_mode", "search") == "plan" and not self.app_context.current_project:
            self.dlg.processingProblemsLabel.setPalette(self.dlg.alert_palette)
            self.dlg.processingProblemsLabel.setText(message)
        elif self.dlg.processingProblemsLabel.text() == message:
            # Only clear our own message, never the cost / other reasons.
            self.dlg.processingProblemsLabel.clear()

    def handle_metadata_button_click(self):
        if getattr(self, "metadata_search_mode", "search") == "plan":
            self.create_search_template()
            return
        # An immediate search over a too-large AOI is offered as a Planned Search instead (T8).
        if self._search_area_exceeds_limit():
            self._prompt_plan_search()
            return
        self.get_metadata()

    def _search_area_exceeds_limit(self) -> bool:
        """Whether the current AOI is too large for an immediate search (T8). Zero/unknown
        ``searchAreaLimit`` disables the check and lets the search proceed."""
        limit = self.app_context.search_area_limit
        return bool(limit and self.app_context.aoi_size and self.app_context.aoi_size > limit)

    def _planned_search_default_name(self) -> str:
        """Auto-name for a Planned Search created from the too-large-AOI prompt (T8)."""
        return self.tr("Searching {datetime}").format(
            datetime=datetime.now().strftime("%Y-%m-%d %H:%M"))

    def _prompt_plan_search(self) -> None:
        """Offer to create a Planned Search when the AOI exceeds the immediate-search limit
        (T8). On confirmation, create a template with an auto-generated name; the existing
        template-area-limit check inside ``create_search_template`` still applies."""
        box = QMessageBox(
            QMessageBox.Question,
            self.plugin_name,
            self.tr("The search area is too large for immediate processing. The Planned Search "
                    "will be created and run in the background. You will be notified when "
                    "results are available."),
            parent=self.main_window,
        )
        box.addButton(QMessageBox.Cancel)
        plan_button = box.addButton(self.tr("Plan Search"), QMessageBox.AcceptRole)
        box.setDefaultButton(plan_button)
        box.exec()
        if box.clickedButton() is not plan_button:
            return
        self.create_search_template(name_override=self._planned_search_default_name())

    def _build_template_aoi_details(self) -> Optional[dict]:
        """Build the ``searchParams.aoiDetails`` FeatureCollection for template creation.

        Each feature carries ``properties.name`` from the layer's ``name`` attribute (when
        present), so the backend persists named AOIs (parsed as ``InputAoiProperties``; the
        name is optional). When the AOI does not come from a polygon layer (e.g. an
        image/mosaic extent), a single unnamed feature is built from ``app_context.aoi``.

        ``aoiDetails`` is always used — the legacy plain ``aoi`` field is deprecated because
        names cannot be attached to it. Returns ``None`` only when there is no AOI at all.
        Raises ``ValueError`` if a name exceeds the limit.
        """
        features = self._aoi_features_from_layer(self.dlg.polygonCombo.currentLayer())
        # Fall back to the combined AOI (e.g. image/mosaic extent) as one unnamed feature,
        # so we still send aoiDetails rather than the deprecated plain `aoi`.
        if not features and self.app_context.aoi:
            features.extend(self._polygon_aoi_features(self.app_context.aoi, None))
        if not features:
            return None
        return {"type": "FeatureCollection", "features": features}

    def _aoi_features_from_layer(self, layer: Optional[QgsVectorLayer]) -> List[dict]:
        """Exploded single-Polygon GeoJSON AOI features from a polygon layer (selected features
        if any, else all). Each feature's ``properties.name`` comes from a ``name`` attribute
        when present. MultiPolygons are split into separate Polygon features (the create path
        requires single-part polygons). Raises ``ValueError`` if a name exceeds the limit."""
        if layer is None or not layer.featureCount():
            return []
        source_features = list(layer.getSelectedFeatures()) or list(layer.getFeatures())
        has_name_field = layer.fields().indexFromName("name") != -1
        features = []
        for feature in source_features:
            geom = feature.geometry()
            if geom is None or geom.isEmpty():
                continue
            wgs_geom = helpers.to_wgs84(QgsGeometry(geom), layer.crs())
            name = None
            if has_name_field:
                raw = feature.attribute("name")
                # QGIS NULL attributes are not None; normalize to a real None.
                if raw not in (None, "") and str(raw).upper() != "NULL":
                    name = str(raw).strip()
            if name and len(name) > AOI_NAME_MAX_LENGTH:
                raise ValueError(
                    self.tr("AOI name '{name}' exceeds {limit} characters").format(
                        name=name, limit=AOI_NAME_MAX_LENGTH
                    )
                )
            features.extend(self._polygon_aoi_features(wgs_geom, name))
        return features

    @staticmethod
    def _polygon_aoi_features(wgs_geom: QgsGeometry, name: Optional[str]) -> List[dict]:
        """Split a (possibly multi-)polygon into one GeoJSON *Polygon* Feature per part.

        The backend ignores ``MultiPolygon`` features in ``aoiDetails`` — an all-MultiPolygon
        upload would create an empty, Failed template (feedback 10) — so mirror the web client
        and explode each MultiPolygon into separate single-part Polygon features. Parts share
        the source feature's ``name``. ``asGeometryCollection`` returns one element for a plain
        Polygon and one per part for a MultiPolygon."""
        features = []
        for part in wgs_geom.asGeometryCollection() or [wgs_geom]:
            if part is None or part.isEmpty():
                continue
            features.append({
                "type": "Feature",
                "geometry": json.loads(part.asJson()),
                "properties": {"name": name},
            })
        return features

    def create_search_template(self, name_override: Optional[str] = None):
        """Create planned search template using current AOI and imagery-search filters.

        ``name_override`` supplies the template name for the Planned Search auto-created from
        the too-large-AOI prompt (T8); otherwise the name comes from the search name field."""
        self.replace_search_provider_index()
        # A template always belongs to a project — block creation (but not the immediate search)
        # and tell the user, instead of sending a request that the backend would reject.
        if not self.app_context.current_project:
            self.dlg.processingProblemsLabel.setPalette(self.dlg.alert_palette)
            self.dlg.processingProblemsLabel.setText(self._select_project_for_template_message())
            self.alert(self._select_project_for_template_message(), QMessageBox.Warning)
            return
        if not self.app_context.aoi:
            self.alert(self.tr('Please, select a valid area of interest'))
            return

        # Forbid creation client-side when the AOI exceeds the planned-processing area cap (mirrors processing creation).
        # A zero/unknown limit disables the check and lets the backend be the source of truth.
        if self.app_context.template_area_limit and self.app_context.aoi_size \
                and self.app_context.aoi_size > self.app_context.template_area_limit:
            self.alert(ErrorMessage(
                code="TEMPLATE_AREA_LIMIT_EXCEEDED",
                parameters={"templateAreaLimit": round(self.app_context.template_area_limit, 2)},
            ).to_str())
            return

        try:
            aoi_details = self._build_template_aoi_details()
        except ValueError as e:
            self.alert(str(e), QMessageBox.Warning)
            return
        if not aoi_details:
            self.alert(self.tr('Please, select a valid area of interest'))
            return

        # Always send aoiDetails (FeatureCollection); the plain `aoi` field is deprecated
        # because per-AOI names cannot be attached to it.
        search_params = self._build_search_params(aoi_details=aoi_details)

        template_name = (name_override or self.dlg.processingName.text()).strip()
        if not template_name:
            self.alert(self.tr('Please, specify a name for your search'))
            return

        now_utc = datetime.utcnow()
        # Backend validates activeUntil against a strict 0-6m window.
        # Use a duration cap to avoid edge-case rejections around month-length differences.
        active_until = now_utc + timedelta(days=180) - timedelta(minutes=1)

        template_payload = CreateProcessingTemplateSchema(
            name=template_name,
            searchParams=search_params,
            projectId=str(self.app_context.project_id),
            activeUntil=active_until.strftime('%Y-%m-%dT%H:%M:%S.0Z'),
        )

        self.dlg.getMetadata.setEnabled(False)
        self.iface.messageBar().pushInfo(self.app_context.plugin_name, self.tr('Creating planned search...'))
        self.processing_service.api.create_template(
            data=template_payload,
            callback=self.create_search_template_callback,
            error_handler=self.create_search_template_error_handler,
        )

    def create_search_template_callback(self, response: QNetworkReply):
        # TODO (architecture): the create-template stack (create_search_template, this callback and
        # its error handler) belongs in ProcessingService — reaching into its private
        # _parse_template_response below is the tell. It stays here for now because the request
        # builder is tightly coupled to Mapflow's imagery-search helpers (_build_search_params /
        # _build_template_aoi_details, off-nadir + product/provider selection, report_http_error);
        # moving it is a larger refactor.
        self.dlg.getMetadata.setEnabled(True)
        # A created template is normally active; isActive comes back False when the active-templates
        # limit is reached (the template is created but inactivated).
        template = self.processing_service._parse_template_response(response)
        if template is not None and not template.isActive:
            alert(self.tr(
                "The template has been created, but is inactive.\n\n"
                "You have reached the maximum number of active planned processings. "
                "Pause or delete another one before activating this template."),
                QMessageBox.Warning)
        self.processing_service.get_processings()

    def create_search_template_error_handler(self, response: QNetworkReply):
        self.dlg.getMetadata.setEnabled(True)
        self.report_http_error(
            response,
            self.tr("Template creation failed"),
            error_message_parser=api_message_parser,
        )

    def _build_search_params(self, aoi_details=None) -> SearchParams:
        """Build ``SearchParams`` from the current imagery-search filter widgets. When
        ``aoi_details`` is ``None`` the geometry is omitted — used to update a template's
        non-geometry search params (which the backend merges); geometry updates go through
        the per-AOI endpoints instead (the PUT template endpoint rejects geometry)."""
        off_nadir_min, off_nadir_max = self._off_nadir_request_bounds()
        return SearchParams(
            aoiDetails=aoi_details,
            acquisitionDateFrom=self.dlg.metadataFrom.dateTime().toUTC().toString("yyyy-MM-ddTHH:mm:ss.zzz'Z'"),
            acquisitionDateTo=self.dlg.metadataTo.dateTime().toUTC().toString("yyyy-MM-ddTHH:mm:ss.zzz'Z'"),
            maxCloudCover=self.dlg.maxCloudCover.value(),
            minAoiIntersectionPercent=self.dlg.minIntersection.value(),
            minOffNadirAngle=off_nadir_min,
            maxOffNadirAngle=off_nadir_max,
            hideUnavailable=self.dlg.hideUnavailableResults.isChecked(),
            productTypes=self.selected_search_product_types() or [],
            dataProviders=self.selected_search_providers(),
        )

    def update_template_search_params(self):
        """Feature 1: save the current imagery-search filter widgets to the open template's
        stored ``searchParams`` (non-geometry params only — the backend merges them and
        preserves the geometry). Triggered by the "Update template" button on the Imagery
        Search tab, which is shown only while a template is open (so the widgets reflect it)."""
        template = self.processing_service.active_template or self.processing_service.selected_template()
        if not template:
            return
        # Only name + searchParams are changed. processingParams and activeUntil are omitted
        # so the backend preserves them (sending processingParams={} would fail its required
        # ``rest`` field; a partial update leaves the stored value untouched).
        payload = UpdateProcessingTemplateSchema(
            name=template.name,
            searchParams=self._build_search_params(aoi_details=None),
        )
        self.iface.messageBar().pushInfo(self.app_context.plugin_name,
                                         self.tr('Updating template search parameters...'))
        self.processing_service.api.update_template(
            template_id=template.id,
            data=payload,
            callback=self._template_updated_callback,
            error_handler=self._template_update_error_handler,
        )

    def _template_updated_callback(self, response: QNetworkReply):
        alert(self.tr("Template updated."), QMessageBox.Information)
        # Re-hydrate so the open template / list reflects the new params.
        self.processing_service.aoi_changed_callback(response)
        self.processing_service.get_processings()

    def _template_update_error_handler(self, response: QNetworkReply):
        self.report_http_error(response, self.tr("Template update failed"),
                               error_message_parser=api_message_parser)

    def _processing_footprints_by_aoi(self, template, processing_id: str):
        """For each of the template's AOIs, the QgsGeometry footprints of the given processing
        that were run over it (a processing can intersect several AOIs, so it may appear under
        more than one). Returns ``[(aoi, [footprint, ...]), ...]`` for AOIs it touches."""
        result = []
        for aoi in template.aoi_dtos():
            if not aoi.id or not aoi.geometry:
                continue
            footprints = [
                self._geometry_from_geojson(link.geometry)
                for link in aoi.processings
                if str(link.processingId) == str(processing_id) and link.geometry
            ]
            footprints = [g for g in footprints if g is not None]
            if footprints:
                result.append((aoi, footprints))
        return result

    def exclude_processing_from_search(self):
        """Feature 3: 'Exclude from search' — subtract a processing's footprint from the AOIs
        it was run over, so the template stops searching an area that was already processed.
        A processing is linked to every AOI it intersects, so subtract from each parent AOI;
        an AOI fully consumed by the subtraction is deleted."""
        template = self.processing_service.active_template
        processing = self.processing_service.selected_processing()
        if not template or not processing:
            return
        affected = self._processing_footprints_by_aoi(template, str(processing.id))
        updates = []      # (aoi_id, new_geometry_dict)
        deletions = []    # aoi_id fully consumed
        for aoi, footprints in affected:
            aoi_geom = self._geometry_from_geojson(aoi.geometry)
            if aoi_geom is None:
                continue
            footprint = footprints[0] if len(footprints) == 1 else QgsGeometry.unaryUnion(footprints)
            new_geom = aoi_geom.difference(footprint)
            if new_geom is None or new_geom.isEmpty() or new_geom.area() == 0:
                deletions.append(aoi.id)
            else:
                updates.append((aoi.id, json.loads(new_geom.asJson())))
        if not updates and not deletions:
            self.alert(self.tr("This processing is not linked to any AOI geometry."),
                       QMessageBox.Information)
            return
        if not self.alert(self.tr("Exclude this processing's area from the template's search? "
                                  "The already-processed area will be removed from the AOI(s)."),
                          QMessageBox.Question):
            return
        for aoi_id, geom in updates:
            self.processing_service.api.update_aoi(
                template_id=template.id,
                aoi_id=aoi_id,
                data=UpdateAoiSchema(geometry=geom),
                callback=self.processing_service.aoi_changed_callback,
                error_handler=self.processing_service.aoi_change_error_handler,
            )
        if deletions:
            self.processing_service.api.delete_aois(
                template_id=template.id,
                data=DeleteAoisSchema(aoiIds=deletions),
                callback=self.processing_service.aoi_changed_callback,
                error_handler=self.processing_service.aoi_change_error_handler,
            )

    def on_metadata_header_clicked(self, column: int) -> None:
        """Clicking a *sortable* search column header re-runs the search sorted server-side by that
        column, toggling ASC/DESC on repeat clicks. Only the columns the API can sort on
        (config.SEARCH_SORT_FIELDS) react; the rest (preview, product type, band order, image id)
        do nothing. Applies to both regular search (/catalog/meta) and template results (the
        template-images endpoint accepts the same sortBy/sortOrder)."""
        if self.dlg.metadataTable.rowCount() == 0:
            return  # nothing searched yet
        attributes = tuple(self.config_search_columns.METADATA_TABLE_ATTRIBUTES.values())
        if not 0 <= column < len(attributes):
            return
        sort_field = self.config.SEARCH_SORT_FIELDS.get(attributes[column])
        if not sort_field:
            return  # column is not server-sortable
        if self._search_sort_by == sort_field:
            self._search_sort_order = "ASC" if self._search_sort_order == "DESC" else "DESC"
        else:
            self._search_sort_by = sort_field
            self._search_sort_order = "DESC"
        self._update_search_sort_indicator(column)
        # Re-request the first page with the new sort — the template-images endpoint and
        # /catalog/meta take the same sort params, so both re-sort server-side.
        if self.processing_service.in_template_mode:
            self._load_template_search_page(0)
        else:
            self.get_metadata()

    def _update_search_sort_indicator(self, column: int) -> None:
        header = self.dlg.metadataTable.horizontalHeader()
        header.setSortIndicatorShown(True)
        order = Qt.DescendingOrder if self._search_sort_order == "DESC" else Qt.AscendingOrder
        header.setSortIndicator(column, order)

    def _restore_search_sort_indicator(self) -> None:
        """Re-show the sort arrow on the active sort column. Every table (re)fill calls
        setSortingEnabled(False), which Qt implements as hiding the sort indicator, so it must be
        restored after each fill (otherwise the arrow flashes on click and immediately vanishes)."""
        if not self._search_sort_by:
            return
        attribute = next((attr for attr, token in self.config.SEARCH_SORT_FIELDS.items()
                          if token == self._search_sort_by), None)
        attributes = tuple(self.config_search_columns.METADATA_TABLE_ATTRIBUTES.values())
        if attribute in attributes:
            self._update_search_sort_indicator(attributes.index(attribute))

    def get_metadata(self, _: Optional[bool] = False, offset: Optional[int] = 0) -> None:
        """Metadata is image footprints with attributes like acquisition date or cloud cover."""
        try: # disconnect to prevent adding mutliple previews if table was refilled (multiple searches)
            self.dlg.metadataTable.disconnect(self.cell_preview_connection)
        except AttributeError: # if no previous connection (first search after start)
            pass
        # If current provider does not support search, we should select ImagerySearchProvider to be able to search
        self.replace_search_provider_index()
        # A regular search replaces any template results, so a "Start" is no longer planned.
        self.app_context.open_template_results_id = None

        self.dlg.metadataTable.clearContents()
        self.dlg.metadataTable.setRowCount(0)
        more_button = self.dlg.findChild(QPushButton, self.config.METADATA_MORE_BUTTON_OBJECT_NAME)
        if more_button:
            self.dlg.layoutMetadataTable.removeWidget(more_button)
            more_button.deleteLater()
        provider = self.provider_service.providers[self.dlg.providerIndex()]
        # Check if the AOI is defined
        if self.app_context.aoi:
            aoi = self.app_context.aoi
        else:
            self.alert(self.tr('Please, select a valid area of interest'))
            return

        from_time = self.dlg.metadataFrom.dateTime().toTimeSpec(Qt.UTC).toString(Qt.ISODate)
        to_time = self.dlg.metadataTo.dateTime().toTimeSpec(Qt.UTC).toString(Qt.ISODate)

        max_cloud_cover = self.dlg.maxCloudCover.value()
        min_intersection = self.dlg.minIntersection.value()

        hide_unavailable = self.dlg.hideUnavailableResults.isChecked()
        product_types = self.selected_search_product_types()
        search_providers = self.selected_search_providers()
        min_off_nadir, max_off_nadir = self._off_nadir_request_bounds()

        # All imagery search goes through the Mapflow catalog API, which filters server-side.
        self.request_mapflow_metadata(aoi=aoi,
                                      provider=provider,
                                      from_=from_time,
                                      to=to_time,
                                      offset=offset,
                                      max_cloud_cover=max_cloud_cover,
                                      min_intersection=min_intersection,
                                      min_off_nadir_angle=min_off_nadir,
                                      max_off_nadir_angle=max_off_nadir,
                                      hide_unavailable=hide_unavailable,
                                      product_types=product_types,
                                      search_providers=search_providers,
                                      sort_by=self._search_sort_by,
                                      sort_order=self._search_sort_order)

    def _off_nadir_request_bounds(self):
        """(min, max) off-nadir angle to send to the API, or (None, None) at the full 0-30 range
        (no off-nadir filtering — leaving it out avoids excluding images beyond the slider)."""
        if self.dlg.off_nadir_is_full_range():
            return None, None
        return self.dlg.off_nadir_range()

    def clear_metadata(self):
        try:
            self.app_context.project.removeMapLayer(self.app_context.metadata_layer)
        except (AttributeError, RuntimeError):  # metadata layer has been deleted
            pass

        self.app_context.open_template_results_id = None
        self.dlg.metadataTable.clearContents()
        self.dlg.metadataTable.setRowCount(0)
        # Drop the retained results/baseline so a stale widen (!) indicator does not linger.
        self.app_context.search_result_geojson = None
        self.app_context.search_baseline_filters = None
        self.dlg.searchWidenWarning.setVisible(False)
        #provider = self.provider_service.providers[self.dlg.providerIndex()]
        self.app_context.search_provider.clear_saved_search(self.app_context.temp_dir)

    def request_mapflow_metadata(self,
                                 aoi: QgsGeometry,
                                 provider: ProviderInterface,
                                 from_: Optional[str] = None,
                                 to: Optional[str] = None,
                                 min_resolution: Optional[float] = None,
                                 max_resolution: Optional[float] = None,
                                 max_cloud_cover: Optional[float] = None,
                                 min_off_nadir_angle: Optional[float] = None,
                                 max_off_nadir_angle: Optional[float] = None,
                                 min_intersection: Optional[float] = None,
                                 offset: Optional[int] = 0,
                                 hide_unavailable: Optional[bool] = False,
                                 product_types: Optional[List[ProductType]] = None,
                                 search_providers: Optional[List[str]] = None,
                                 sort_by: Optional[str] = None,
                                 sort_order: Optional[str] = None):
        if not self.check_if_output_directory_is_selected():
            return # only when outputDirectory is empty AND user closed selection dialog
        self.app_context.metadata_aoi = aoi
        # Remember what this search actually asks the server for, so the widen (!) indicator can
        # flag later widget edits that ask for MORE than was fetched (which local filtering can't
        # surface without a fresh Search).
        self.app_context.search_baseline_filters = self._current_filter_baseline()
        request_payload = ImageCatalogRequestSchema(aoi=json.loads(aoi.asJson()),
                                                    acquisitionDateFrom=from_,
                                                    acquisitionDateTo=to,
                                                    minResolution=min_resolution,
                                                    maxResolution=max_resolution,
                                                    maxCloudCover=max_cloud_cover,
                                                    minOffNadirAngle=min_off_nadir_angle,
                                                    maxOffNadirAngle=max_off_nadir_angle,
                                                    minAoiIntersectionPercent=min_intersection,
                                                    limit=self.search_page_limit,
                                                    offset=offset,
                                                    hideUnavailable=hide_unavailable,
                                                    productTypes=product_types,
                                                    dataProviders=search_providers,
                                                    sortBy=sort_by,
                                                    sortOrder=sort_order)
        self.http.post(url=provider.meta_url,
                       body=request_payload.as_json().encode(),
                       headers={},
                       callback=self.request_mapflow_metadata_callback,
                       callback_kwargs={"min_intersection": min_intersection,
                                        "max_cloud_cover": max_cloud_cover},
                       error_handler=self.request_mapflow_metadata_error_handler,
                       use_default_error_handler=False,
                       timeout=60)

    def request_mapflow_metadata_error_handler(self, response: QNetworkReply):
        title = self.tr("We couldn't get metadata from the Mapflow Imagery Catalog")
        error = response.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if error is not None:
            title += self.tr(". Error {error}").format(error=error)
        self.report_http_error(response, title, error_message_parser=api_message_parser)

    def display_metadata_geojson_layer(self, filename, layer_name):
        try:
            self.app_context.project.removeMapLayer(self.app_context.metadata_layer)
        except (AttributeError, RuntimeError):  # metadata layer has been deleted
            pass
        # Assigned (before add_layer) so the AOI-area monitor recognizes and skips it.
        self.app_context.metadata_layer = QgsVectorLayer(filename, layer_name, 'ogr')
        self.app_context.metadata_layer.loadNamedStyle(os.path.join(self.plugin_dir, 'static', 'styles', 'metadata.qml'))
        # Place search results just under the AOI layer, if that layer has a legend node.
        # (A layer added with addToLegend=False has no tree node -> findLayer returns None;
        # fall back to a plain add instead of dereferencing a missing parent.)
        aoi_layer = self.dlg.polygonCombo.currentLayer()
        aoi_layer_tree = (self.app_context.project.layerTreeRoot().findLayer(aoi_layer.id())
                          if aoi_layer else None)
        if aoi_layer_tree is not None and aoi_layer_tree.parent() is not None:
            index = aoi_layer_tree.parent().children().index(aoi_layer_tree)
            self.result_loader.add_layer(layer=self.app_context.metadata_layer, order=index + 1)
        else:
            self.result_loader.add_layer(layer=self.app_context.metadata_layer)
        # Connect layer with metadata table
        self.app_context.meta_layer_table_connection = self.app_context.metadata_layer.selectionChanged.connect(
            self.sync_layer_selection_with_table)
        self.app_context.search_footprints = {
            feature['local_index']: feature
            for feature in self.app_context.metadata_layer.getFeatures()
        }

    def request_mapflow_metadata_callback(self, response: QNetworkReply,
                                          min_intersection: int = 0,
                                          max_cloud_cover: int = 90):
        response_json = json.loads(response.readAll().data())
        if not response_json.get("images"):
            self.alert(
                self.tr('No images match your criteria. Try relaxing the filters.'),
                QMessageBox.Information
            )
            return
        response_data = ImageCatalogResponseSchema(**response_json)
        geoms = response_data.as_geojson()
        # Add index to map table and layer
        for position, feature in enumerate(geoms.get("features", ())):
            feature['properties']['local_index'] = position

        # Save the current search results to load later
        provider = self.imagery_search_provider
        save_failed_message = self.tr("<b>Results could not be loaded </b><br>Please, make sure you chose the right output folder in the Settings tab \
                                and you have access rights to this folder")
        try:
            filename = provider.save_search_layer(self.app_context.temp_dir, geoms)
        except OSError:
            # The case the message describes: missing/unwritable output folder.
            self.alert(save_failed_message)
            return
        except Exception:
            logger.exception("Unexpected error saving the search layer")
            self.alert(save_failed_message)
            return
        self.display_metadata_geojson_layer(filename, f"{provider.name} metadata")
        # Retain the raw results so the instant local filter can reorder/re-render them without
        # a new request (fill emits metadataTableFilled -> apply_local_filter).
        self.app_context.search_result_geojson = geoms
        # Built-in Qt sorting stays OFF; the results already arrive in the server sort order and
        # header clicks re-request with sortBy/sortOrder (see on_metadata_header_clicked).
        self.dlg.fill_metadata_table(geoms, sort=False)

        self._update_search_pager(response_data.total, response_data.limit, response_data.offset)

    def sync_table_selection_with_image_id_and_layer(self) -> None:
        """
        Every time user selects a row in the metadata table, select the
        corresponding feature in the metadata layer and put the selected image's
        id into the "Image ID" field.
        """
        local_index_column = self.config.LOCAL_INDEX_COLUMN
        key = 'local_index'

        selected_cells = self.dlg.metadataTable.selectedItems()
        if not selected_cells:
            selected_rows = local_indices = []
        else:
            selected_rows = [cell.row() for cell in selected_cells]
            local_indices = [self.dlg.metadataTable.item(row, local_index_column).text() for row in selected_rows]
        try:
            self.app_context.metadata_layer.selectionChanged.disconnect(self.app_context.meta_layer_table_connection)
            # disconnect to prevent loop of signals
        except (RuntimeError, AttributeError, TypeError):
            # metadata layer was removed or not initialized
            return
        self.replace_search_provider_index()

        try:
            self.app_context.metadata_layer.selectByExpression(f"{key} in {tuple(local_indices)}")
        except RuntimeError:  # layer has been deleted
            pass
        except Exception as e:
            self.app_context.meta_layer_table_connection = self.app_context.metadata_layer.selectionChanged.connect(
                self.sync_layer_selection_with_table)
            raise e
        # Set the zoom from the selected image BEFORE recomputing cost, with the combo's
        # signals blocked. Otherwise zoomCombo.currentIndexChanged -> on_zoom_change fires a
        # SECOND, duplicate cost request (and the first one below would use the stale zoom).
        if selected_rows:
            zooms = [self.dlg.metadataTable.item(row, self.config.ZOOM_COLUMN_INDEX).text() for row in selected_rows]
            zoom_index = self.dlg.zoomCombo.findText(zooms[0])  # different zooms are not allowed
        else:
            zoom_index = -1
        self.dlg.zoomCombo.blockSignals(True)
        self.dlg.zoomCombo.setCurrentIndex(0 if zoom_index == -1 else zoom_index)
        self.dlg.zoomCombo.blockSignals(False)
        self.area_calculator_service.calculate_aoi_area_polygon_layer(self.dlg.polygonCombo.currentLayer())
        self.app_context.meta_layer_table_connection = self.app_context.metadata_layer.selectionChanged.connect(
            self.sync_layer_selection_with_table)

    def sync_layer_selection_with_table(self, selected_ids: List[int]) -> None:
        """
        Every time user selects an image in the metadata layer, select the corresponding
        row in the table and fill out the image id in the providers tab.

        :param selected_ids: The selected feature IDs. These aren't the image IDs, but rather
            the primary keys of the features.
        """
        self.dlg.metadataTable.setSelectionMode(QAbstractItemView.MultiSelection)
        # Disconnect to avoid backwards signal and possible infinite loop;
        # connection is restored before return
        key = 'local_index'
        id_column_index = self.config.LOCAL_INDEX_COLUMN

        self.dlg.metadataTable.itemSelectionChanged.disconnect(self.meta_table_layer_connection)

        try:
            if not selected_ids:
                self.dlg.metadataTable.clearSelection()
                return
            found_items = []
            for selected_id in selected_ids:
                selected_local_index = self.app_context.metadata_layer.getFeature(selected_id)[key]
                for item in self.dlg.metadataTable.findItems(str(selected_local_index), Qt.MatchExactly):
                    if item.column() == id_column_index:
                        found_items.append(item)
            self.dlg.metadataTable.clearSelection()
            if not found_items:
                return
            for item in found_items:
                self.dlg.metadataTable.selectRow(item.row())
        finally:
            self.dlg.metadataTable.setSelectionMode(QAbstractItemView.ExtendedSelection)
            self.meta_table_layer_connection = self.dlg.metadataTable.itemSelectionChanged.connect(
                self.sync_table_selection_with_image_id_and_layer)

    def sync_image_id_with_table_and_layer(self, image_id: str) -> None:
        """
        Select a footprint in the current metadata layer when user selects it in the table.

        :param image_id: The new image ID.
        """

        if not image_id:
            self.dlg.metadataTable.clearSelection()
            return
        items = self.dlg.metadataTable.findItems(image_id, Qt.MatchExactly)
        if not items:
            self.dlg.metadataTable.clearSelection()
            return
        #if items[0] not in self.dlg.metadataTable.selectedItems():
            #self.dlg.metadataTable.selectRow(items[0].row())
        # Redundant since imageId is temorary removed

    def check_processing_ui(self, allow_empty_name=False):
        processing_name = self.dlg.processingName.text()

        if not processing_name and not allow_empty_name:
            raise ProcessingInputDataMissing(self.tr('Please, specify a name for your processing'))
        if not self.app_context.aoi:
            if self.dlg.polygonCombo.currentLayer():
                raise BadProcessingInput(self.tr('Processing area layer is corrupted or has invalid projection'))
            else:
                raise BadProcessingInput(self.tr('Please, select a valid area of interest'))
        if self.app_context.aoi_area_limit < self.app_context.aoi_size:
            raise BadProcessingInput(self.tr(
                'Up to {} sq km can be processed at a time. '
                'Try splitting your area(s) into several processings.').format(self.app_context.aoi_area_limit))

        return True

    def get_processing_params(self,
                              provider_index: Optional[int],
                              s3_uri: str = "",
                              zoom: Optional[str] = None,
                              provider_name: Optional[str] = None):
        provider = self.provider_service.providers[provider_index]
        meta = {'source-app': 'qgis',
                'version': self.app_context.plugin_version,
                'source': provider.name.lower()}
        if not provider:
            raise PluginError(self.tr('Providers are not initialized'))
        provider_params, provider_meta = provider.to_processing_params(provider_name=provider_name,
                                                                       zoom=zoom)
        meta.update(**provider_meta)
        return provider_params, meta

    def update_processing_limit(self) -> None:
        """Set the user's processing limit as reported by Mapflow."""
        self.http.get(
            url=f'{self.server}/user/status',
            callback=self.set_processing_limit,
            use_default_error_handler=False  # it is done by timer, so we ignore errors to avoid stacking
        )

    def set_processing_limit(self, response: QNetworkReply,
                             app_startup_request: Optional[bool] = False) -> None:
        response_data = json.loads(response.readAll().data())
        if self.plugin_name != 'Mapflow':
            # In custom plugins, we don't show the remaining limit and do not check it for the processing
            self.app_context.billing_type = BillingType.none
        else:
            # get billing type, by default it is area
            self.app_context.billing_type = BillingType(response_data.get('billingType', 'AREA').upper())
        # get limits
        self.app_context.remaining_limit = int(response_data.get('remainingArea', 0)) / 1e6  # convert into sq.km
        self.app_context.remaining_credits = int(response_data.get('remainingCredits', 0))
        # Planned-processing (template) area cap; absent/zero means "unknown" and disables the client-side check
        self.app_context.template_area_limit = int(response_data.get('templateAreaLimit', 0)) / 1e6  # convert into sq.km
        # Immediate-search area cap; above it the user is offered a Planned Search (T8). Zero = unknown/disabled.
        self.app_context.search_area_limit = int(response_data.get('searchAreaLimit', 0)) / 1e6  # convert into sq.km
        self.app_context.max_aois_per_processing = int(response_data.get("maxAoisPerProcessing",
                                                             self.config.MAX_AOIS_PER_PROCESSING))
        if self.app_context.billing_type == BillingType.credits:
            balance_str = self.tr("Your balance: {} credits").format(self.app_context.remaining_credits)
        elif self.app_context.billing_type == BillingType.area:  # area
            balance_str = self.tr('Remaining limit: {:.2f} sq.km').format(self.app_context.remaining_limit)
        else:  # BillingType.none
            balance_str = ''

        self.app_context.review_workflow_enabled = response_data.get('reviewWorkflowEnabled', False)
        self.dlg.balanceLabel.setText(balance_str)

        if app_startup_request:
            self.processing_service.update_processing_cost()
            self.dlg.setup_for_billing(self.app_context.billing_type)
            self.dlg.setup_for_review(self.app_context.review_workflow_enabled)
            self.dlg.modelCombo.activated.emit(self.dlg.modelCombo.currentIndex())
            self.setup_providers(response_data.get("dataProviders") or [])
            self.setup_search_providers(response_data.get("searchDataProviders") or [])
            self.on_provider_change()
            # Open processings or projects table
            if self.app_context.current_project:
                self.project_processing_controller.show_processings()
            else:
                self.project_processing_controller.show_projects()
                self.project_service.setup_project_change_rights()

    def _register_provider_min_areas(self, providers_data):
        """Map provider name -> minimum AOI area (sq km) from /user/status provider data.

        Keyed by both the api name and the display name (lowercased) so it matches whatever
        the search results report as the image's ``providerName``.
        """
        for data in providers_data or []:
            min_area = data.get("minAreaSqKm", data.get("minAreaSqkm"))
            if min_area is None:
                continue
            try:
                min_area = float(min_area)
            except (TypeError, ValueError):
                continue
            for key in (data.get("name"), data.get("displayName")):
                if key:
                    self.app_context.provider_min_areas[str(key).lower()] = min_area

    def setup_providers(self, providers_data):
        self._register_provider_min_areas(providers_data)
        self.provider_service.imagery_search_provider_instance = ImagerySearchProvider(proxy=self.server)
        self.provider_service.my_imagery_provider_instance = MyImageryProvider()
        # Get only unique providers to avoid index shifting in souceCombo when one provider is sent multiple times
        unique_providers = list({provider.name: provider for provider in
                                 [DefaultProvider.from_response(ProviderReturnSchema.from_dict(data))
                                  for data in providers_data]}.values())
        self.provider_service.default_providers = ProvidersList([self.provider_service.imagery_search_provider_instance] +
                                               [self.provider_service.my_imagery_provider_instance] +
                                               unique_providers)
        self.provider_service.set_available_imagery_sources(self.dlg.modelCombo.currentText())
        # We want to clear the data from previous lauunch to avoid confusion
        for provider in self.provider_service.providers:
            provider.clear_saved_search(self.app_context.temp_dir)
    
    def setup_search_providers(self, providers_data):
        self._register_provider_min_areas(providers_data)
        search_providers = ProvidersList([DefaultProvider.from_response(ProviderReturnSchema.from_dict(data))
                                          for data in providers_data])
        # Remember the api-names of the available providers so the local filter can drop results
        # from providers not available to the user ("Search only through available providers").
        self.app_context.search_data_providers = [pr.api_name for pr in search_providers]
        self.dlg.enable_search_providers_filter(len(search_providers))
        if len(search_providers) == 0:
            return
        for pr in search_providers:
            self.dlg.searchProvidersCombo.addItemWithCheckState(pr.name, Qt.Unchecked, pr.api_name)
        self.dlg.searchProvidersCombo.setDefaultText(self.tr("Show all"))

    def _move_layer_to_top(self, layer_id: str) -> bool:
        """Move an existing layer's tree node to the top of its parent group."""
        root = self.app_context.project.layerTreeRoot()
        node = root.findLayer(layer_id)
        if not node:
            return False
        parent = node.parent() or root
        parent.insertChildNode(0, node.clone())
        parent.removeChildNode(node)
        return True

    def preview_catalog(self, image_id):
        feature = self.metadata_feature(image_id)
        if not feature:
            self.alert(self.tr("Preview is unavailable when metadata layer is removed"))
            return
        # If this image's preview is already on the map (layers are named "<image_id> preview"),
        # just bring it to the top instead of downloading and adding a duplicate.
        existing_preview = self.app_context.project.mapLayersByName(f"{image_id} preview")
        if existing_preview:
            self._move_layer_to_top(existing_preview[0].id())
            self.iface.setActiveLayer(existing_preview[0])
            self.iface.mapCanvas().refresh()
            return
        # A preview for this image is already being downloaded (async): a rapid second click /
        # double-click must not start another download. The preview layer is only added in the
        # HTTP callback, so the on-map guard above cannot catch these — hence this in-flight set.
        if image_id in self._pending_preview_ids:
            return
        footprint = self.metadata_footprint(feature=feature)
        url = feature.attribute('previewUrl')
        preview_type = feature.attribute('previewType')
        self.iface.mapCanvas().zoomToSelected(self.app_context.metadata_layer)
        self.iface.mapCanvas().refresh()
        # Get multi-image preview (e.g. Roscosmos)
        try:
            previews_list = MultiPreviewList.from_dict_or_string(feature['previews'])
        except KeyError: # duplicated processings don't have this field
            previews_list = MultiPreviewList([])
        if len(previews_list.previews) != 0:
            previews = []
            for p in previews_list.previews:
                # Create QgsGeometry from GeoJSON through ogr and wkt
                ogr_geom = ogr.CreateGeometryFromJson(str(p.geometry))
                wkt_geom = ogr_geom.ExportToWkt()
                geom = QgsGeometry.fromWkt(wkt_geom)
                previews.append((p.url, geom))
            self._pending_preview_ids.add(image_id)  # in-flight until the VRT is added / errors
            self.preview_multiple_png(response=None,
                                      previews=previews,
                                      footprint=previews[0][1],
                                      image_id=image_id,
                                      georeferenced_previews_list=[])
            return
        # Get single image preview. Read each attribute independently: a My Imagery result may
        # lack whole metadata columns — an all-null acquisitionDate is dropped by the OGR GeoJSON
        # reader, so feature.attribute('acquisitionDate') raises KeyError. A single missing field
        # must not blank out the others (a shared try/except previously reset preview_type to '',
        # so even mosaics with a valid xyz preview reported "no preview"). Duplicated processings
        # likewise lack these fields, and get '' the same way.
        url = self._feature_attribute(feature, 'previewUrl') or ''
        preview_type = self._feature_attribute(feature, 'previewType') or ''
        provider_name = self._feature_attribute(feature, 'providerName') or ''
        raw_date = self._feature_attribute(feature, 'acquisitionDate')
        image_date = raw_date.toString("dd.MM.yyyy") if raw_date else ''
        if not preview_type:
            self.alert(self.tr("Selected imagery has no preview"))
            return
        # Display image preview
        if preview_type in (PreviewType.png, PreviewType.jpg):
            if not url:
                self.alert(self.tr("Preview with such URL is unavailable"))
                return
            self._pending_preview_ids.add(image_id)  # in-flight until the preview is added / errors
            self.preview_png(url, footprint, image_id)
        # Display mosaic preview
        elif preview_type in (PreviewType.xyz, PreviewType.tms, PreviewType.wms):
            self.preview_mosaic(feature, url, preview_type, provider_name, image_date)
        else:
            self.alert(self.tr("Preview for '{iid}' is unavailable").format(iid=image_id))
            return

    def preview_png(self,
                    url: str,
                    footprint: QgsGeometry,
                    image_id: str = ""):
        # previewUrl is always a self-authenticating (pre-signed) URL — for every provider,
        # including My Imagery — so we send a dummy Authorization header and never leak the
        # Mapflow credentials to the (often third-party) preview host.
        self.http.get(url=url,
                      timeout=30,
                      auth='null'.encode(),
                      callback=self.display_png_preview_gcp,
                      use_default_error_handler=False,
                      error_handler=self.preview_png_error_handler,
                      error_handler_kwargs={"image_id": image_id},
                      callback_kwargs={"footprint": footprint,
                                       "image_id": image_id})

    def display_png_preview(self,
                            response: QNetworkReply,
                            extent: QgsRectangle,
                            crs: QgsCoordinateReferenceSystem = QgsCoordinateReferenceSystem("EPSG:3857"),
                            image_id: str = ""):
        """
        We assume that png preview is not internally georeferenced,
        but the footprint specified in the metadata has the same extent, so we generate georef for the image
        """
        with open(self.app_context.temp_dir/os.urandom(32).hex(), mode='wb') as f:
            f.write(response.readAll().data())
        preview = gdal.Open(f.name)
        pixel_xsize = extent.width() / preview.RasterXSize
        pixel_ysize = extent.height() / preview.RasterYSize
        preview.SetProjection(crs.toWkt())
        preview.SetGeoTransform([
            extent.xMinimum(),  # north-west corner x
            pixel_xsize,  # pixel horizontal resolution (m)
            0,  # x-axis rotation
            extent.yMaximum(),  # north-west corner y
            0,  # y-axis rotation
            -pixel_ysize  # pixel vertical resolution (m)
        ])
        preview.FlushCache()
        layer = QgsRasterLayer(f.name, f"{image_id} preview", 'gdal')
        layer.setExtent(extent)
        self.app_context.project.addMapLayer(layer)

    def display_png_preview_gcp(self,
                                response: QNetworkReply,
                                footprint: QgsGeometry,
                                crs: QgsCoordinateReferenceSystem = QgsCoordinateReferenceSystem("EPSG:3857"),
                                image_id: str = ""):
        """
        Display image preview using Ground Control Points from footprint corners.
        Delegates to ResultsLoader.display_preview_with_gcp().
        """
        layer = self.result_loader.display_preview_with_gcp(
            response=response,
            footprint=footprint,
            crs=crs,
            image_name=image_id,
            # Don't clone the AOI over the preview inside a template: the AOI is already drawn
            # as its own layer there, so the "Search area" clone just duplicates it (feedback 1).
            add_aoi=not self.processing_service.in_template_mode,
        )
        self._pending_preview_ids.discard(image_id)  # download finished
        self._relocate_preview_to_template_group(layer)

    def preview_multiple_png(self,
                             response: QNetworkReply,
                             previews: List[Tuple[str, QgsGeometry]],
                             footprint: QgsGeometry,
                             image_id: str = "",
                             georeferenced_previews_list: List[str] = []):
        " Add preview for multi-part images (e.g. Roscosmos). "
        # Callback part: collect response images into a list
        if response:
            georeferenced_preview = self.result_loader.georeference_preview_part(response=response,
                                                                                 footprint=footprint,
                                                                                 crs=helpers.WGS84)
            georeferenced_previews_list.append(georeferenced_preview)
        # Final part: merge all coolected images into one VRT
        if len(previews) == 0:
            vrt_path = os.path.join(self.app_context.temp_dir, os.urandom(32).hex())
            vrt = gdal.BuildVRT(vrt_path, georeferenced_previews_list)
            vrt.FlushCache()
            vrt = None
            vrt_layer = QgsRasterLayer(vrt_path, "{image_id} preview".format(image_id=image_id), 'gdal')
            self._pending_preview_ids.discard(image_id)  # multi-part download finished
            self.result_loader.add_layer(vrt_layer)
            self._add_aoi_to_preview_if_needed()
            self._relocate_preview_to_template_group(vrt_layer)
            return
        # Requset part: remove first image from the list and get its preview
        image_to_preview = previews.pop(0)
        self.http.get(url=image_to_preview[0],
                      timeout=30,
                      auth='null'.encode(),
                      callback=self.preview_multiple_png,
                      use_default_error_handler=False,
                      error_handler=self.preview_png_error_handler,
                      error_handler_kwargs={"image_id": image_id},
                      callback_kwargs={"previews": previews,
                                       "footprint": image_to_preview[1],
                                       "image_id": image_id,
                                       "georeferenced_previews_list":georeferenced_previews_list})

    def preview_png_error_handler(self, response: QNetworkReply, image_id: str = ""):
        # Clear the in-flight flag so the user can retry this image's preview after a failure.
        self._pending_preview_ids.discard(image_id)
        self.report_http_error(response, self.tr("Could not display preview"))
    
    def preview_mosaic(self,
                       feature: QgsFeature,
                       url: str,
                       preview_type: str,
                       provider_name: str,
                       image_date: str):
        uri = layer_utils.generate_xyz_layer_definition(url=url, source_type=preview_type)
        tile_layer = QgsRasterLayer(uri, provider_name, "wms")
        tiles_to_delete = [layer.id() for layer in self.app_context.project.mapLayers().values()
                            if layer.dataProvider().dataSourceUri() == tile_layer.dataProvider().dataSourceUri()]
        self.app_context.project.removeMapLayers(tiles_to_delete)
        self.result_loader.add_layer(layer=tile_layer, order=0)
        self._relocate_preview_to_template_group(tile_layer)
        # Add footprint layer
        if feature:
            footprint_layer = QgsVectorLayer("Polygon?crs=EPSG:4326",
                                                f"{provider_name}_{image_date}",
                                                "memory")
            footprint_layer.dataProvider().addFeatures([feature])
            footprint_layer.updateExtents()
            footprint_layer.loadNamedStyle(os.path.join(self.plugin_dir, 'static', 'styles', 'metadata_footprint.qml'))
            # Remove same-named boundaries AND the previously shown one (its name varies by
            # acquisition date, so a name match alone leaves the old boundary on the map).
            footprints_to_delete = [layer.id() for layer in self.app_context.project.mapLayers().values()
                                    if layer.name() == footprint_layer.name()]
            if self._mosaic_preview_footprint_id:
                footprints_to_delete.append(self._mosaic_preview_footprint_id)
            self.app_context.project.removeMapLayers(footprints_to_delete)
            self.result_loader.add_layer(layer=footprint_layer, order=0)
            self._mosaic_preview_footprint_id = footprint_layer.id()
            self._relocate_preview_to_template_group(footprint_layer)
        self._add_aoi_to_preview_if_needed()

    def metadata_footprint(self,
                           image_id=None,
                           feature=None,
                           crs: QgsCoordinateReferenceSystem = helpers.WEB_MERCATOR):
        if not feature:
            feature = self.metadata_feature(image_id)
        if not feature:
            return None
        return helpers.from_wgs84(feature.geometry(), crs)

    @staticmethod
    def _feature_attribute(feature, name):
        """``feature.attribute(name)``, or ``None`` when that field does not exist on the layer.

        The OGR GeoJSON reader omits a property that is null in every feature, so My Imagery
        results (all-null ``acquisitionDate`` etc.) lack those columns and a plain
        ``feature.attribute(name)`` would raise ``KeyError``. A NULL value on an existing field
        already comes back as Python ``None``."""
        try:
            return feature.attribute(name)
        except KeyError:
            return None

    def metadata_feature(self, image_id):
        if not image_id:
            return None
        try:  # Get the image extent to set the correct extent on the raster layer
            return next(self.app_context.metadata_layer.getFeatures(f"id = '{image_id}'"))
        except (RuntimeError, AttributeError, StopIteration):  # layer doesn't exist or has been deleted, or empty
            return None

    def preview_xyz(self, provider, image_id):
        max_zoom = self.config.MAX_ZOOM
        layer_name = provider.name
        try:
            url = provider.preview_url(image_id=image_id)
            preview_max_zoom = provider.preview_max_zoom
        except ImageIdRequired:
            self.alert(self.tr("Provider {name} requires image id for preview!").format(name=provider.name),
                       QMessageBox.Warning)
            return
        except NotImplementedError:            
            self.alert(self.tr("Preview is unavailable for the provider {}. \nOSM layer will be added instead.").format(provider.name), QMessageBox.Information)
            # Add OSM instaed of preview, if it is unavailable (for Mapbox)
            layer = QgsRasterLayer(OSM, 'OpenStreetMap', 'wms')
            self.result_loader.add_preview_layer(preview_layer=layer)
            return
        except Exception as e:
            self.alert(str(e), QMessageBox.Warning)
            return         
        uri = layer_utils.generate_xyz_layer_definition(url,
                                                        provider.source_type,
                                                        preview_max_zoom or max_zoom,
                                                        provider.credentials.login,
                                                        provider.credentials.password)
        layer = QgsRasterLayer(uri, layer_name, 'wms')
        layer.setCrs(QgsCoordinateReferenceSystem(provider.crs))
        if layer.isValid():
            self.result_loader.add_preview_layer(preview_layer=layer)
        else:
            self.alert(self.tr("We couldn't load a preview for this image"))

    def preview(self) -> None:
        """Display raster tiles served over the Web."""
        selected_cells = self.dlg.metadataTable.selectedItems()
        if not selected_cells:
            image_id = None
        else:
            id_column_index = self.config.SEARCH_ID_COLUMN_INDEX
            image_id = self.dlg.metadataTable.item(selected_cells[0].row(), id_column_index).text()
        provider = self.provider_service.providers[self.dlg.providerIndex()]
        if provider.requires_image_id and not image_id:
            self.alert(self.tr("This provider requires image ID!"), QMessageBox.Warning)
            return
        if isinstance(provider, ImagerySearchProvider):
            self.preview_catalog(image_id=image_id)
        else:  # XYZ providers
            self.preview_xyz(provider=provider, image_id=image_id)
    
    def on_metadata_table_cell_clicked(self, row: int, column: int):
        """Keep click behavior passive; marking seen is handled by Seen actions only."""
        return

    def _seen_template_id(self) -> Optional[str]:
        """Id of the template whose search results are currently in the table.

        This must NOT come from the processings-table selection: inside the in-template view the
        selected rows are AOIs/processings, so a selection-derived id is None there and both Seen
        actions silently sent no request. ``open_template_results_id`` is set whenever template
        results are loaded (entering a template and "See search results" alike)."""
        open_id = getattr(self.app_context, "open_template_results_id", None)
        if open_id:
            return str(open_id)
        template = self.processing_service.active_template
        return str(template.id) if template else None

    def _mark_template_image_seen_by_row(self, row: int) -> None:
        """Request 'seen' for one row's image, only if its DTO is still new.

        The row marker and the new-images counter are updated from the success
        callback (``_on_template_image_seen``) — never optimistically.
        """
        template_id = self._seen_template_id()
        if not template_id:
            return
        image = self._template_image_at_row(row)
        if image is None or not image.isNew:
            return
        self.processing_service.api.mark_template_image_seen(
            template_id=template_id,
            image_id=str(image.id),
            callback=lambda _response, r=row, img=image, tid=template_id:
                self._on_template_image_seen(r, img, tid),
            error_handler=self._mark_seen_error_handler,
        )

    def mark_selected_template_images_seen(self):
        """Mark selected metadata rows as seen for the template whose results are shown."""
        if not self._seen_template_id():
            return
        for row in sorted({item.row() for item in self.dlg.metadataTable.selectedItems()}):
            self._mark_template_image_seen_by_row(row)

    def mark_all_template_images_seen(self):
        """Mark every image of the shown template as seen with a single request."""
        template_id = self._seen_template_id()
        if not template_id:
            return
        self.processing_service.api.mark_all_template_images_seen(
            template_id=template_id,
            callback=lambda _response, tid=template_id: self._on_all_template_images_seen(tid),
            error_handler=self._mark_seen_error_handler,
        )

    def _template_image_at_row(self, row: int):
        """Return the stored image DTO for a metadata-table row, or None."""
        id_item = self.dlg.metadataTable.item(row, self.config.SEARCH_ID_COLUMN_INDEX)
        if not id_item:
            return None
        return getattr(self, "template_search_images", {}).get(id_item.text())

    def _on_template_image_seen(self, row: int, image, template_id: str) -> None:
        """Success: clear the row marker and decrement the new-images counter."""
        image.isNew = False
        self._set_new_image_marker(row, False)
        self._decrement_template_new_images_count(template_id)

    def _on_all_template_images_seen(self, template_id: str) -> None:
        """Success: clear every visible marker and zero the new-images counter."""
        for row in range(self.dlg.metadataTable.rowCount()):
            image = self._template_image_at_row(row)
            if image is not None and image.isNew:
                image.isNew = False
                self._set_new_image_marker(row, False)
        self._reset_template_new_images_count(template_id)

    def _mark_seen_error_handler(self, response: QNetworkReply) -> None:
        """Leave markers/counter untouched and tell the user the request failed."""
        self.iface.messageBar().pushWarning(
            self.app_context.plugin_name,
            self.tr("Could not mark image(s) as seen, please try again."),
        )

    def _new_image_marker_column(self) -> int:
        """Leftmost visible column — where the 'new image' icon is shown.

        Starts at the configured leftmost index (0) and skips columns the user hid via
        the search-column checkboxes, so the marker never lands on a hidden column.
        """
        start = self.config.NEW_IMAGE_MARKER_COLUMN_INDEX
        table = self.dlg.metadataTable
        for col in range(start, table.columnCount()):
            if not table.isColumnHidden(col):
                return col
        return start

    def _apply_new_image_markers(self) -> None:
        """Show the 'new image' icon on every row whose image DTO is still new."""
        for row in range(self.dlg.metadataTable.rowCount()):
            image = self._template_image_at_row(row)
            self._set_new_image_marker(row, bool(image is not None and image.isNew))

    def _set_new_image_marker(self, row: int, is_new: bool) -> None:
        """Set or clear the 'new image' icon on a row's leftmost-visible cell."""
        cell = self.dlg.metadataTable.item(row, self._new_image_marker_column())
        if cell is not None:
            cell.setIcon(new_image_icon if is_new else QIcon())

    def _find_template(self, template_id: str):
        template_map = getattr(self.processing_service, "templates", {}) or {}
        for key, value in template_map.items():
            if str(key) == str(template_id):
                return value
        return None

    def _decrement_template_new_images_count(self, template_id: str):
        """Decrement newImagesCount on the in-memory template DTO and refresh its status cell."""
        template = self._find_template(template_id)
        if template is None:
            return
        if template.newImagesCount and template.newImagesCount > 0:
            template.newImagesCount -= 1
        self._refresh_template_status_cell(template_id, template)

    def _reset_template_new_images_count(self, template_id: str):
        """Zero newImagesCount on the in-memory template DTO and refresh its status cell."""
        template = self._find_template(template_id)
        if template is None:
            return
        template.newImagesCount = 0
        self._refresh_template_status_cell(template_id, template)

    def _refresh_template_status_cell(self, template_id: str, template) -> None:
        """Update the template's status cell text + tooltip in the processings table."""
        id_col = self.config.PROCESSING_TABLE_ID_COLUMN_INDEX
        status_col = list(self.config.PROCESSING_TABLE_COLUMNS).index('status')
        table = self.dlg.processingsTable
        for row in range(table.rowCount()):
            id_item = table.item(row, id_col)
            if id_item and id_item.text() == str(template_id):
                status_item = table.item(row, status_col)
                if status_item:
                    status_item.setData(Qt.DisplayRole, template.table_status)
                    tip = self.tr("Planned processing")
                    if template.newImagesCount and template.newImagesCount > 0:
                        tip = self.tr("Planned processing. New images: {count}").format(
                            count=template.newImagesCount
                        )
                    status_item.setToolTip(tip)
                break

    def preview_search_from_cell (self, row, column):
        if column == self.config.PPRVIEW_INDEX_COLUMN:
            id_column_index = self.config.SEARCH_ID_COLUMN_INDEX
            image_id = self.dlg.metadataTable.item(row, id_column_index).text()
            self.preview_catalog(image_id)

    def preview_or_search(self, provider) -> None:
        provider_index = self.dlg.providerIndex()
        provider = self.provider_service.providers[provider_index]
        if provider.requires_image_id:
            imagery_search_tab = self.dlg.tabWidget.findChild(QWidget, "providersTab")
            self.dlg.tabWidget.setCurrentWidget(imagery_search_tab)
        else:
            self.preview()

    def update_processing_current_rating(self) -> None:
        # reset labels:
        processing = self.processing_service.selected_processing()
        if not processing:
            return
        pid = processing.id
        p_name = processing.name

        self.dlg.set_processing_rating_labels(processing_name=p_name)
        self.http.get(
            url=f'{self.server}/processings/{pid}/v2',
            callback=self.update_processing_current_rating_callback
        )

    def update_processing_current_rating_callback(self, response: QNetworkReply) -> None:
        response_data = json.loads(response.readAll().data())
        p_name = response_data.get('name')
        rating_json = response_data.get('rating')
        if not rating_json:
            return
        rating = int(rating_json.get('rating'))
        feedback = rating_json.get('feedback')
        self.dlg.set_processing_rating_labels(processing_name=p_name,
                                              current_rating=rating,
                                              current_feedback=feedback)

    def submit_processing_rating(self) -> None:
        processing = self.processing_service.selected_processing()
        if not processing:
            return
        pid = processing.id
        if not processing.status.is_ok:
            self.alert(self.tr('Only finished processings can be rated'))
            return
        # Rating is descending: None-5-4-3-2-1
        rating = 6 - self.dlg.ratingComboBox.currentIndex()
        if not 0 < rating <= 5:
            return
        feedback_text = self.dlg.processingRatingFeedbackText.toPlainText()
        body = {
            'rating': rating,
            'feedback': feedback_text
        }
        self.http.put(
            url=f'{self.server}/processings/{pid}/rate',
            body=json.dumps(body).encode(),
            callback=self.submit_processing_rating_callback,
            callback_kwargs={'feedback': feedback_text}
        )

    def accept_processing(self):
        processing = self.processing_service.selected_processing()
        if not processing:
            return
        pid = processing.id
        if not processing.status.is_ok:
            self.alert(self.tr('Only finished processings can be rated'))
            return
        elif not processing.reviewStatus.is_in_review:
            self.alert(self.tr("Processing must be in `Review required` status"))
            return
        self.http.put(
            url=f'{self.server}/processings/{pid}/acceptation',
            callback=self.review_processing_callback
        )

    def review_processing_callback(self, response: QNetworkReply):
        # Clear successfully uploaded review
        self.review_dialog.reviewComment.setText("")
        self.processing_service.processing_fetch_timer.start()
        self.processing_service.get_processings()

    def show_review_dialog(self):
        processing = self.processing_service.selected_processing()
        if not processing:
            return
        if not processing.status.is_ok:
            self.alert(self.tr('Only finished processings can be rated'))
            return
        elif not processing.reviewStatus.is_in_review:
            self.alert(self.tr("Processing must be in `Review required` status"))
            return
        self.review_dialog.setup(processing)
        self.review_dialog.show()

    def submit_review(self):
        body = {"comment": self.review_dialog.reviewComment.toPlainText(),
                "features": layer_utils.export_as_geojson(self.review_dialog.reviewLayerCombo.currentLayer())}
        self.http.put(
            url=f'{self.server}/processings/{self.review_dialog.processing.id}/rejection',
            body=json.dumps(body).encode(),
            callback=self.review_processing_callback
        )

    def submit_processing_rating_callback(self, response: QNetworkReply, feedback: str) -> None:
        if not feedback:
            self.alert(
                self.tr(
                    "Thank you! Your rating is submitted!\nWe would appreciate if you add feedback as well."
                ),
                QMessageBox.Information
            )
        else:
            self.alert(
                self.tr(
                    "Thank you! Your rating and feedback are submitted!"
                ),
                QMessageBox.Information
            )
        self.update_processing_current_rating()

    def enable_review_submit(self, status_ok: bool) -> None:
        self.dlg.enable_review(status_ok,
                               self.tr("Only correctly finished processings with 'Review required' status can be reviewed"))

    def enable_rating_submit(self, status_ok: bool) -> None:
        rating_selected = 5 >= self.dlg.ratingComboBox.currentIndex() > 0
        if not self.app_context.user_role.can_delete_rename_review_processing:
            reason = self.tr('Not enough rights to rate processing in a shared project ({})').format(self.app_context.user_role.value)
        elif not status_ok:
            if not self.processing_service.selected_processing():
                reason = self.tr('Please select processing')
            else:
                reason = self.tr("Only correctly finished processings (status OK) can be rated")
        elif not rating_selected and self.app_context.user_role.can_delete_rename_review_processing:
            reason = self.tr("Please select rating to submit")
        else:
            reason = ""
        self.dlg.enable_rating(can_interact=(status_ok and self.app_context.user_role.can_delete_rename_review_processing),
                               can_send=rating_selected,
                               reason=reason)

    def enable_feedback(self) -> None:
        """
        By feedback we mean either rating (1-5 stars + message) for regular users
        or review for users which have review workflow enabled
        """
        processing = self.processing_service.selected_processing()
        if not processing:
            if self.app_context.review_workflow_enabled:
                self.enable_review_submit(False)
            else:
                self.enable_rating_submit(False)
            return
        if self.app_context.review_workflow_enabled:
            self.enable_review_submit(processing.status.is_ok and processing.reviewStatus.is_in_review)
        else:
            self.enable_rating_submit(processing.status.is_ok)
        self.enable_restart_action(self.app_context.user_role.can_start_processing 
                                   and (processing.status.is_failed 
                                        or processing.status.is_cancelled))
    
    def enable_restart_action(self, enabled: bool):
        self.dlg.enable_restart_action(enabled)
            

    # =================== Results management ==================== #
    def _open_template(self, template):
        """Navigate into a template ('one step right').

        The actual hydration (the poll omits ``searchParams``) and state switch happen in
        the service; map side-effects are handled by ``on_template_opened`` via signal.
        """
        self.project_processing_controller.enter_template(template)

    def on_template_opened(self, template):
        """React to entering a template: fill search results and load AOI/processing layers."""
        # Initial results are the whole template (no AOI filter applied yet).
        self._template_search_aoi_filter = None
        # Drop the previous view's results/baseline first, so the widget updates below (which
        # fire the local filter) don't briefly compare against a stale baseline. The template's
        # own results + baseline are set when its search response arrives.
        self.app_context.search_result_geojson = None
        self.app_context.search_baseline_filters = None
        # "Update template" (save the current filters into the template) only makes sense while
        # viewing a template. The widen (!) indicator manages its own visibility. Template
        # results are filtered client-side now (no server-side Filter button).
        self.dlg.updateTemplateSearch.setVisible(True)
        self.apply_search_params_to_ui(getattr(template, "searchParams", None))
        self._load_template_search(template)
        self._load_template_layers(template)

    def on_template_closed(self, template):
        """React to leaving a template: drop its map group and clear the search table."""
        if template is not None:
            self._remove_template_group(str(template.name))
        self.app_context.open_template_results_id = None
        self._template_search_aoi_filter = None
        self.app_context.search_result_geojson = None
        self.app_context.search_baseline_filters = None
        self.dlg.searchWidenWarning.setVisible(False)
        self.dlg.updateTemplateSearch.setVisible(False)
        # Drop the AOI-selection processing Area so it doesn't leak to the project view.
        self._remove_selected_aois_layer()
        self._processing_area_aoi_filter = None
        self.dlg.metadataTable.clearContents()
        self.dlg.metadataTable.setRowCount(0)
        # Clear the template search-results pagination so it is not preserved on re-open.
        self.search_page_offset = 0
        self.dlg.enable_search_pages(False)

    def on_template_aois_changed(self, template):
        """Redraw the template's AOI/processing map layers after its AOIs change (add / rename
        / delete / geometry update / exclude-from-search), so the layer tree stays in sync
        without re-entering the template."""
        if not template:
            return
        self._remove_template_aoi_subgroups(str(template.name))
        self._load_template_layers(template)

    def _remove_template_aoi_subgroups(self, template_group_name: str):
        """Remove the per-AOI subgroups (and their layers) under the template group, keeping
        the search-results footprint layer that sits directly in the template group."""
        if not template_group_name:
            return
        root = self.app_context.project.layerTreeRoot()
        mapflow_group_name = self.app_context.settings.value('layerGroup') or self.app_context.plugin_name
        mapflow_group = root.findGroup(mapflow_group_name)
        parent_group = mapflow_group if mapflow_group else root
        template_group = parent_group.findGroup(template_group_name)
        if template_group is None:
            return
        for child in list(template_group.children()):
            # AOI subgroups are groups; the search-footprints node is a layer — leave it.
            if isinstance(child, QgsLayerTreeGroup):
                for layer in child.findLayers():
                    layer_id = layer.layerId()
                    if layer_id:
                        try:
                            self.app_context.project.removeMapLayer(layer_id)
                        except (RuntimeError, KeyError):
                            pass
                template_group.removeChildNode(child)

    def apply_search_params_to_ui(self, search_params):
        """Populate the Imagery Search filters from a template's stored ``searchParams``
        (web parity: the user can see what the template searches for). The widgets stay
        editable — changing them affects the current search view only, never the template.
        Fields the template does not carry leave the corresponding widgets untouched."""
        if not search_params:
            return
        if isinstance(search_params, dict):
            search_params = SearchParams.from_dict(search_params)

        date_from = self._utc_date_from_iso(search_params.acquisitionDateFrom)
        if date_from is not None:
            self.dlg.metadataFrom.setDate(date_from)
        date_to = self._utc_date_from_iso(search_params.acquisitionDateTo)
        if date_to is not None:
            self.dlg.metadataTo.setDate(date_to)
        if search_params.maxCloudCover is not None:
            self.dlg.maxCloudCover.setValue(int(round(search_params.maxCloudCover)))
        if search_params.minAoiIntersectionPercent is not None:
            self.dlg.minIntersection.setValue(int(round(search_params.minAoiIntersectionPercent)))
        if search_params.minOffNadirAngle is not None and search_params.maxOffNadirAngle is not None:
            self.dlg.set_off_nadir_range(int(round(search_params.minOffNadirAngle)),
                                         int(round(search_params.maxOffNadirAngle)))
        if search_params.hideUnavailable is not None:
            self.dlg.hideUnavailableResults.setChecked(bool(search_params.hideUnavailable))
        product_types = [str(pt).upper() for pt in (search_params.productTypes or [])]
        if product_types:
            self.dlg.searchMosaicCheckBox.setChecked(ProductType.mosaic.upper() in product_types)
            self.dlg.searchImageCheckBox.setChecked(ProductType.image.upper() in product_types)
        self._apply_search_providers_to_combo(search_params.dataProviders)

    @staticmethod
    def _utc_date_from_iso(value: Optional[str]) -> Optional[QDate]:
        """Parse an ISO-8601 timestamp (as stored in ``searchParams``) into a UTC QDate."""
        if not value:
            return None
        parsed = QDateTime.fromString(value, Qt.ISODateWithMs)
        if not parsed.isValid():
            parsed = QDateTime.fromString(value, Qt.ISODate)
        return parsed.toUTC().date() if parsed.isValid() else None

    def _apply_search_providers_to_combo(self, data_providers: Optional[List[str]]):
        """Mirror ``selected_search_providers``: check the combo items whose api-name is in
        the template's ``dataProviders``; ``None``/empty means the template searched all
        providers, shown as no checked items ("Show all")."""
        combo = self.dlg.searchProvidersCombo
        combo.deselectAllOptions()
        if not data_providers:
            return
        wanted = set(data_providers)
        for index in range(combo.count()):
            if combo.itemData(index) in wanted:
                combo.setItemCheckState(index, Qt.Checked)

    def _remove_template_group(self, template_group_name: str):
        """Remove the template's layer-tree group (and its layers) from the map."""
        if not template_group_name:
            return
        root = self.app_context.project.layerTreeRoot()
        mapflow_group_name = self.app_context.settings.value('layerGroup') or self.app_context.plugin_name
        mapflow_group = root.findGroup(mapflow_group_name)
        parent_group = mapflow_group if mapflow_group else root
        template_group = parent_group.findGroup(template_group_name)
        if template_group is None:
            return
        for layer in template_group.findLayers():
            layer_id = layer.layerId()
            if layer_id:
                try:
                    self.app_context.project.removeMapLayer(layer_id)
                except (RuntimeError, KeyError):
                    pass
        parent_group.removeChildNode(template_group)

    def load_results(self):
        # Check if it's a template first
        template = self.processing_service.selected_template()
        if template:
            self._open_template(template)
            return

        # Otherwise, it's a processing
        processing = self.processing_service.selected_processing()
        if not processing:
            return
        if not processing.status.is_ok:
            self.alert(self.tr("Only the results of correctly finished processing can be loaded"))
            return

        if self.dlg.viewAsTiles.isChecked():
            self.result_loader.load_result_tiles(processing=processing)
        elif self.dlg.viewAsLocal.isChecked():
            if not self.ensure_output_directory(
                    self.tr("A working directory is required to save the processing results "
                            "on your computer.")):
                return  # user chose 'Later' — cancel the action that needs the directory
            self.result_loader.download_results(processing=processing)

    def download_results_file(self) -> None:
        """
        Download result and save directly to a geojson file
        It is the most reliable way to get results, applicable if everything else failed
        """
        processing = self.processing_service.selected_processing()
        if not processing:
            return
        if not processing.status.is_ok:
            self.alert(self.tr("Only the results of correctly finished processing can be loaded"))
            return
        self.result_loader.download_results_file(pid=processing.id)

    def download_aoi_file(self) -> None:
        """
        Download area of interest and save to a geojson file
        """
        processing = self.processing_service.selected_processing()
        if not processing:
            return
        if not self.ensure_output_directory(
                self.tr("A working directory is required to save the area of interest "
                        "on your computer.")):
            return  # user chose 'Later' — cancel the action that needs the directory
        self.result_loader.download_aoi_file(pid=processing.id, callback=self.result_loader.download_aoi_file_callback)

    def alert(self, message: str, icon: QMessageBox.Icon = QMessageBox.Critical, blocking=True) -> None:
        return alert(message, icon, blocking)

    def initGui(self) -> None:
        """Create the menu entries and toolbar icons inside the QGIS GUI.

        This function is referenced by the QGIS plugin loading system, so it can't be renamed.
        Since there are submodules, the various UI texts are set dynamically.
        """
        # Set main dialog title dynamically so it could be overridden when used as a submodule
        self.dlg.setWindowTitle(helpers.generate_plugin_header(self.plugin_name,
                                                               env=self.config.MAPFLOW_ENV,
                                                               project_name=None,
                                                               user_role=None,
                                                               project_owner=None))
        # Display plugin icon in own toolbar
        plugin_button = QAction(self.plugin_icon, self.plugin_name, self.main_window)
        plugin_button.triggered.connect(self.main)
        self.toolbar.addAction(plugin_button)
        self.app_context.project.readProject.connect(self.set_layer_group)
        self.dlg.processingsTable.sortByColumn(self.config.PROCESSING_TABLE_SORT_COLUMN_INDEX, Qt.DescendingOrder)

    def set_layer_group(self) -> None:
        """Setup a legend group where all layers created by the plugin will be added."""
        self.layer_group = self.layer_tree_root.findGroup(self.app_context.settings.value('layerGroup'))
        if self.layer_group:
            # If the group has been deleted, assume user wants to add layers to root, memorize it
            self.layer_group.destroyed.connect(lambda: setattr(self, 'add_layers_to_group', False))
            # Let user rename the group, memorize the new name
            self.layer_group.nameChanged.connect(lambda _, name: self.app_context.settings.setValue('layerGroup', name))

    def unload(self) -> None:
        """Remove the plugin icon & toolbar from QGIS GUI."""
        self.processing_service.stop()
        self.user_status_update_timer.stop()
        self.iface.removeCustomActionForLayerType(self.add_layer_action)
        self.iface.removeCustomActionForLayerType(self.remove_layer_action)
        for dlg in self.dlg, self.dlg_login, self.dlg_provider:
            if dlg:
                dlg.close()
        del self.toolbar
        self.app_context.settings.setValue('metadataMinIntersection', self.dlg.minIntersection.value())
        self.app_context.settings.setValue('metadataMaxCloudCover', self.dlg.maxCloudCover.value())
        off_nadir_min, off_nadir_max = self.dlg.off_nadir_range()
        self.app_context.settings.setValue('metadataMinOffNadir', off_nadir_min)
        self.app_context.settings.setValue('metadataMaxOffNadir', off_nadir_max)
        self.app_context.settings.setValue('metadataFrom', self.dlg.metadataFrom.date())
        self.app_context.settings.setValue('metadataTo', self.dlg.metadataTo.date())

    def read_mapflow_token(self) -> None:
        """Compose and memorize the user's credentils as Basic Auth."""
        if self.use_oauth:
            auth_id, new_auth = get_auth_id(self.config.AUTH_CONFIG_NAME,
                                             self.config.AUTH_CONFIG_MAP)
            if new_auth:
                self.alert(self.tr("We have just set the authentication config for you. \n"
                                       " You may need to restart QGIS to apply it so you could log in"),
                           icon=QMessageBox.Information)
            if not auth_id:
                self.dlg_login.invalidToken.setVisible(True)
            else:
                self.dlg_login.invalidToken.setVisible(False)
                self.login_oauth(auth_id)
        else:
            auth_data = self.dlg_login.token_value()
            if not auth_data:
                return
            # to add paddind for the token len to be multiple of 4
            token = auth_data + "=" * ((4 - len(auth_data) % 4) % 4)
            self.login_basic(token)

    def login_oauth(self, oauth_id):
        try:
            self.http.setup_auth(oauth_id=oauth_id)
            self.http.get(
                url=f'{self.config.SERVER}/projects/default',
                callback=self.log_in_callback,
                use_default_error_handler=True
            )
        except ProxyIsAlreadySet:
            self.alert(self.tr("Please restart QGIS before using OAuth2 login."),
                       icon=QMessageBox.Warning)
        except Exception as e:
            self.alert(f"Error while trying to send authorization request: {e}."
                       f"It is possible that your auth config is corrupted. "
                       f"Remove auth config named {self.config.AUTH_CONFIG_NAME} and restart QGis"
                       f"for the plugin to recreate it. "
                       f"If it does not help, contact us",
                       icon=QMessageBox.Warning)

    def login_basic(self, token) -> None:
        """Log into Mapflow."""
        # save new token to settings immediately to overwrite old one, if any
        self.app_context.settings.setValue('token', token)
        # keep login/password from token
        try:
            self.app_context.username, self.app_context.password = b64decode(token).decode().split(':')
        except (ValueError, TypeError):
            # A malformed token, which is the whole point of this handler. ValueError covers
            # all three ways it can be malformed: binascii.Error (not base64) and
            # UnicodeDecodeError (not utf-8) both subclass it, and so does the unpack when
            # the decoded text has no ':'. TypeError covers a non-str/bytes token.
            self.app_context.username = self.app_context.password = ''  # nosec B105  # clearing creds, not a secret
            self.dlg_login.show()
            self.alert(self.tr('Wrong token. '
                               'Visit "<a href=\"https://app.mapflow.ai/account/api\">mapflow.ai</a>" '
                               'to get a new one'),
                       icon=QMessageBox.Warning)
            self.dlg_login.invalidToken.setVisible(True)
            return
        self.http.setup_auth(basic_auth_token=f'Basic {token}')
        self.http.get(
            url=f'{self.config.SERVER}/projects/default',
            callback=self.log_in_callback,
            use_default_error_handler=True
        )

    def logout(self) -> None:
        """Close the plugin and clear credentials from cache."""
        # set token to empty to delete it from settings
        self.app_context.settings.setValue('token', '')
        self.processing_service.processing_fetch_timer.stop()
        self.user_status_update_timer.stop()
        self.stop_startup_status_polling()
        self.app_context.logged_in = False
        self.http.logout()
        self.dlg.close()
        # self.dlg_login = self.set_up_login_dialog()  # recreate the login dialog
        self.dlg_login.show()  # assume user wants to log into another account

    def default_error_handler(self,
                              response: QNetworkReply,
                              ) -> bool:
        """Handle general networking errors: offline, timeout, server errors.

        :param response: The HTTP response.
        :param: error_message_parser: function to parse the message from the particular API
        Returns True if the error has been handled, otherwise returns False.
        """
        error = response.error()
        service = 'Mapflow'
        parser = api_message_parser
        if error == QNetworkReply.AuthenticationRequiredError:  # invalid/empty credentials
            # Prevent deadlocks
            if self.app_context.logged_in:  # token re-issued during a plugin session
                self.logout()
            elif self.app_context.settings.value('token'):  # env changed w/out logging out (admin)
                self.alert(self.tr('Wrong token. '
                                   'Visit "<a href=\"https://app.mapflow.ai/account/api\">mapflow.ai</a>" '
                                   'to get a new one'),
                           icon=QMessageBox.Warning)
                self.dlg_login.show()

            self.dlg_login.invalidToken.setVisible(True)
            return True
        elif error in (
                QNetworkReply.OperationCanceledError,  # timeout
                QNetworkReply.ServiceUnavailableError,  # HTTP 503
                QNetworkReply.InternalServerError,  # HTTP 500
                QNetworkReply.ConnectionRefusedError,
                QNetworkReply.RemoteHostClosedError,
                QNetworkReply.NetworkSessionFailedError,
        ):
            self.report_http_error(response, self.tr(
                service + ' is not responding. Please, try again.\n\n'
                          'If you are behind a proxy or firewall,\ncheck your QGIS proxy settings.\n'),
                                   error_message_parser=parser)
            return True
        elif error == QNetworkReply.HostNotFoundError:  # offline
            self.alert(self.tr(service + ' not found. Check your Internet connection'))
            return True
        elif error in (
                QNetworkReply.UnknownNetworkError,
                QNetworkReply.ProxyConnectionRefusedError,
                QNetworkReply.ProxyConnectionClosedError,
                QNetworkReply.ProxyNotFoundError,
                QNetworkReply.ProxyTimeoutError,
                QNetworkReply.ProxyAuthenticationRequiredError,
        ):
            self.report_http_error(response, self.tr('Proxy error. Please, check your proxy settings.'))
            return True
        elif error == QNetworkReply.ContentAccessDenied:
            if not self.app_context.user_role.can_delete_rename_project:
                self.report_http_error(response,
                                       self.tr("Not enough rights for this action\n"+
                                                "in a shared project '{project_name}' ({user_role})").format(project_name=self.app_context.current_project.name, 
                                                                                                            user_role=self.app_context.user_role.value),
                                       error_message_parser=parser)
            else:
                self.report_http_error(response,
                                       self.tr("This operation is forbidden for your account, contact us"),
                                       error_message_parser=parser)
            return True
        else:
            self.report_http_error(response, self.tr("Error"), error_message_parser=parser)
        return False

    def report_http_error(self,
                          response: QNetworkReply,
                          title: str = None,
                          error_message_parser: Optional[Callable] = None):
        """Prepare and show an error message for the supplied response.

        :param response: The HTTP response.
        :param title: The error message's title.
        :param error_message_parser: function to parse error message, depends on server which is requested.
            Default parser (if None) searches for 'message' section in response json
        """
        response_body = response.readAll().data().decode()
        error_summary, email_body = get_error_report_body(response=response,
                                                          response_body=response_body,
                                                          plugin_version=self.app_context.plugin_version,
                                                          error_message_parser=error_message_parser)
        ErrorMessageWidget(parent=QApplication.activeWindow(),
                           text= error_summary,
                           title=title,
                           email_body=email_body).show()


    def find_project(self, projects: List[MapflowProject], project_id: str):
        # first, try to find by ID
        default_index = -1
        for idx, project in enumerate(projects):
            if project.id == project_id:
                return idx
            if project.name == "Default":
                default_index = idx

        # report if id is not found
        if default_index >= 0:
            if project_id.lower() != "default":
                self.alert(message=f"Selected project {project_id} is not found. Setting project to default",
                           icon=QMessageBox.Information)
            return default_index

        # if there is NO default project, but some projects are present - we will use the first
        self.alert(message=f"Default project is not found. Using existing project {projects[0].name}",
                   icon=QMessageBox.Information)
        return 0

    def log_in_callback(self, response: QNetworkReply) -> None:
        """Fetch user info, models and processings.
        :param response: The HTTP response.
        """
        # Show history of processings at startup to get non-empty table immediately, and setup the table update
        self.dlg_login.invalidToken.setVisible(False)
        # Set up the UI with the received data
        response = json.loads(response.readAll().data())
        # User info is stored inside user's Default project - will change it in the future API versions
        userinfo = response['user']
        default_project = MapflowProject.from_dict(response)
        # Remember the logged-in user's id (template ownership check for contributors).
        if default_project.user is not None:
            self.app_context.user_id = default_project.user.id

        self.update_processing_limit()
        # We have different behavior for admin as he has access to all processings
        self.is_admin = userinfo.get("role") == "ADMIN"

        self.dlg.restoreGeometry(self.app_context.settings.value('mainDialogState', b''))
        # Authenticate and keep user logged in
        self.app_context.logged_in = True
        self.dlg_login.close()

        # Get all projects & setup processings table (see callback)
        if self.is_admin:
            self.app_context.project_id = Config.PROJECT_ID
            self.project_service.view.setup_workflow_defs(default_project.workflowDefs, 
                                                          self.config.DEFAULT_MODEL)
            self.processing_service.setup_processings_table()
        else:
            if self.app_context.project_id:
                self.app_context.current_project = self.project_service.get_project(
                    project_id=self.app_context.project_id,
                    callback=self.project_service.get_project_callback,
                    error_handler=self.project_service.get_project_error_handler,
                    error_handler_kwargs={'default_error_handler': self.default_error_handler,
                                          'show_projects': self.project_processing_controller.show_projects}
                )
            self.data_catalog_service.get_mosaics()
        self.dlg.setup_for_billing(self.app_context.billing_type)
        self.dlg.show()
        self.user_status_update_timer.start()
        # Logging in again after a failed startup must get a full budget of retries.
        self._startup_status_attempts = 0
        self._startup_status_pending = False
        self._startup_status_given_up = False
        self.app_startup_user_update_timer.start()

    def check_plugin_version_callback(self, response: QNetworkReply) -> None:
        """Inspect the plugin version backend expects and show a warning if it is incompatible w/ the plugin.

        If the major version differs, we force the user to reinstall and exit the plugin
        If the minor/patch differs, we recommend the user to reinstall, and if do it only once for the version,
         so in case user dismisses the recommendation, w save the "last recommended version" in settings
         and do not show the reminder until the even newer version is released
        :param response: The HTTP response.
        """

        server_version = response.readAll().data().decode('utf-8')
        latest_reported_version = self.app_context.settings.value('latest_reported_version', self.app_context.plugin_version)

        force_upgrade, recommend_upgrade = helpers.check_version(local_version=self.app_context.plugin_version,
                                                                 server_version=server_version,
                                                                 latest_reported_version=latest_reported_version)
        if force_upgrade:
            self.alert(self.tr("You must upgrade your plugin version to continue work with Mapflow. \n"
                               "The server requires version {server_version}, your plugin is {local_version}\n"
                               "Go to Plugins -> Manage and Install Plugins -> Upgradable").format(
                server_version=server_version,
                local_version=self.app_context.plugin_version,
                icon=QMessageBox.Warning))
            self.version_ok = False
            self.dlg.close()

        elif recommend_upgrade:
            self.alert(self.tr("A new version of Mapflow plugin {server_version} is released \n"
                               "We recommend you to upgrade to get all the latest features\n"
                               "Go to Plugins -> Manage and Install Plugins -> Upgradable").format(
                server_version=server_version,
                local_version=self.app_context.plugin_version,
                icon=QMessageBox.Information))
            # saving the requested version to not bother the user next time, if he decides not to upgrade
            self.app_context.settings.setValue('latest_reported_version', server_version)
            self.version_ok = True
        else:
            # it is if the upgrade is not needed, we want to save it
            self.app_context.settings.setValue('latest_reported_version', server_version)
            self.version_ok = True

    def show_details(self):
        processing = self.processing_service.selected_processing()
        if not processing:
            return
        error = None
        if processing.messages:
            error = processing.error_message(raw=self.config.SHOW_RAW_ERROR)
        dialog = ProcessingDetailsDialog(self.dlg)
        dialog.toSourceButton.clicked.connect(lambda: self.show_processing_source(
                                                           processing=processing,
                                                           window=dialog))
        dialog.setup(processing, error or None)
        dialog.deleteLater()
    
    def show_processing_source(self,
                               processing,
                               window):
        source_params = processing.params.sourceParams
        if isinstance(source_params, ImagerySearchParams):
            # Download AOI and only then fill search table
            self.result_loader.download_aoi_file(pid=processing.id, callback=self.processing_service.duplicate_aoi_callback)
        elif isinstance(source_params, MyImageryParams):
            self.data_catalog_service.show_my_imagery_source(source_params)
        elif isinstance(source_params, UserDefinedParams):
            text = self.dlg.show_user_provider_info(source_params)
            self.alert(message=text, icon=QMessageBox.Information)
        window.close()

    def get_local_image_indices(self, selected_images):
        try:
            rows = list(set(image.row() for image in selected_images))
            local_image_indices = [int(self.dlg.metadataTable.item(row, self.config.LOCAL_INDEX_COLUMN).text()) 
                                   for row in rows]
        except (AttributeError, KeyError):
            local_image_indices = []
        return local_image_indices

    def get_search_providers(self, local_image_indices):
        try:
            provider_names = [self.app_context.search_footprints[local_image_index].attribute("providerName")
                              for local_image_index in local_image_indices]
        except KeyError:
            provider_names = []
        try:
            product_types = [self.app_context.search_footprints[local_image_index].attribute("productType")
                             for local_image_index in local_image_indices]
        except KeyError:
            product_types = []
        return provider_names, product_types
    
    def _update_search_pager(self, total: int, limit: int, offset: int):
        """Show/hide and wire the imagery-search page navigation from a search response's
        ``total``/``limit``/``offset``. Shared by regular search and template search (T6):
        template results used to fill the table but never toggle the pager."""
        if limit and total > limit:
            self.search_page_offset = offset
            self.search_page_limit = limit
            quotient, remainder = divmod(total, limit)
            total_pages = quotient + (remainder > 0)
            page_number = int(offset / limit) + 1
            self.dlg.enable_search_pages(True, page_number, total_pages)
            self.dlg.searchRightButton.setEnabled(page_number != total_pages)
            self.dlg.searchLeftButton.setEnabled(page_number != 1)
        else:
            self.dlg.enable_search_pages(False)

    def show_search_next_page(self):
        offset = self.search_page_offset + self.search_page_limit
        if self.processing_service.in_template_mode:
            self._load_template_search_page(offset)
        else:
            self.get_metadata(offset=offset)

    def show_search_previous_page(self):
        offset = self.search_page_offset - self.search_page_limit
        if self.processing_service.in_template_mode:
            self._load_template_search_page(offset)
        else:
            self.get_metadata(offset=offset)
    
    def selected_search_product_types(self):
        product_types = []
        if self.dlg.searchMosaicCheckBox.isChecked():
            product_types.append(ProductType.mosaic.upper())
        if self.dlg.searchImageCheckBox.isChecked():
            product_types.append(ProductType.image.upper())
        if len(product_types) == 0:
            product_types = [ProductType.mosaic.upper(), ProductType.image.upper()]
        return product_types

    def selected_search_providers(self):
        """Provider filter to send with a search/template request.

        Only meaningful while the search is limited to available providers; when
        "Search only through available providers" is off, the (hidden) provider selection
        must NOT be sent — the search runs across all providers. An empty selection is
        also omitted (None), since the backend reads ``[]`` as "search no providers".
        """
        if not self.dlg.hideUnavailableResults.isChecked():
            return None
        return self.dlg.searchProvidersCombo.checkedItemsData() or None

    def setup_tempdir(self) -> Optional[str]:
        """Create the working ``Temp`` directory under the configured output directory.

        Returns ``None`` on success (or when no output directory is configured), or a human-readable
        error string when the directory is unavailable. Never raises: this runs during plugin startup
        (``classFactory``), and any failure here must not abort the whole plugin. The directory can be
        unusable for several reasons — an external drive that is not mounted (its ``/Volumes/<name>``
        stub is left root-owned and unwritable -> ``PermissionError``), a deleted parent
        (``FileNotFoundError``), a read-only or full filesystem, etc. — so we catch broadly and fall
        back to "no working directory", letting the user pick another one.
        """
        output_dir = self.app_context.settings.value('outputDir')
        if not output_dir:
            return None # don't ask to specify tempdir at the plugin start
        temp_dir = Path(output_dir, "Temp")
        try:
            shutil.rmtree(temp_dir) # remove old tempdir
        except Exception as e:
            # Best-effort cleanup of a stale directory; the run continues either way.
            logger.warning("Could not remove old temp dir '%s': %s", temp_dir, e)
        try:
            temp_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.app_context.temp_dir = None
            logger.exception("Working directory '%s' is unavailable", output_dir)
            return str(e)
        self.app_context.temp_dir = temp_dir
        return None

    def check_dir_and_duplicate_processing(self):
        if not self.check_if_output_directory_is_selected():
            return # only when outputDirectory is empty AND user closed selection dialog
        self.processing_service.duplicate_processing()

    def tr(self, message: str) -> str:
        """Localize a UI element text.
        :param message: A text to translate
        """
        # Don't use self.plugin_name as context since it'll be overriden in supermodules
        return QCoreApplication.translate(self.config.PLUGIN_NAME, message)

    def main(self) -> None:
        """Plugin entrypoint."""
        self.config = Config()
        # check plugin version first
        self.http.get(
            url=f'{self.server}/version',
            callback=self.check_plugin_version_callback,
            use_default_error_handler=False  # ignore errors
        )
        if not self.version_ok:
            self.dlg.close()
            return

        if self.app_context.logged_in:
            # with any auth method
            self.dlg.show()
            self.dlg.raise_()
            self.update_processing_limit()
            self.user_status_update_timer.start()
            return

        token = self.app_context.settings.value('token')
        if not self.use_oauth and token:
            # Saved token for basic auth
            self.login_basic(token)
        else:
            self.dlg_login.show()

    @property
    def imagery_search_provider(self):
        for provider in self.provider_service.providers:
            if isinstance(provider, ImagerySearchProvider):
                return provider
        return None
