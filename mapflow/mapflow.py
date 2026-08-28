import json
import logging
import os.path
import shutil
from base64 import b64decode
from configparser import ConfigParser  # parse metadata.txt -> QGIS version check (compatibility)
from pathlib import Path
from typing import List, Optional, Callable

from PyQt5.QtCore import (
    QCoreApplication, QDate, QObject, Qt,
    QTimer, QTranslator
)
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtNetwork import QNetworkReply
from PyQt5.QtWidgets import (
    QAbstractItemView, QAction, QApplication, QFileDialog,
    QMenu, QMessageBox, QWidget, QToolButton
)
from qgis.core import (
    QgsDistanceArea, QgsMapLayer, QgsMapLayerType,
    QgsProject, QgsVectorLayer
)

from .config import Config, ConfigColumns
from .errors import (BadProcessingInput,
                     PluginError,
                     ProcessingInputDataMissing,
                     ProxyIsAlreadySet)
# Functional
from .functional import helpers, layer_utils
from .functional.app_context import AppContext
from .functional.auth import get_auth_id
from .functional.controller.data_catalog_controller import DataCatalogController
from .functional.controller.project_processing_controller import ProjectProcessingController
from .functional.controller.processing_controller import ProcessingController
from .functional.controller.search_controller import SearchController
from .functional.controller.template_controller import TemplateController
from .functional.service.template_service import TemplateService
from .functional.view.template_view import TemplateView
from .functional.service.aoi_service import AoiService
from .functional.service.local_filter_service import FilterCriteria, LocalFilterService
from .functional.service.preview_service import PreviewService
from .functional.service.search_service import SearchService
from .functional.view.aoi_view import AoiView
from .functional.view.search_view import SearchView
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
                     ImagerySearchParams,
                     MyImageryParams,
                     ProviderReturnSchema,
                     UserDefinedParams)
from .schema.catalog import ProductType
from .schema.project import MapflowProject, UserRole
from .schema.workflow_def import WorkflowDef
# Dialogs
from .dialogs import (ErrorMessageWidget,
                      MainDialog,
                      MapflowLoginDialog,
                      ProviderDialog,
                      ReviewDialog)
from .dialogs.icons import plugin_icon
from .dialogs.processing_details_dialog import ProcessingDetailsDialog
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

    # Guards against the ``metadataTableFilled`` -> ``apply_local_filter`` -> ``fill_metadata_table``
    # -> ``metadataTableFilled`` re-entrancy: the local filter re-fills the table itself, so the
    # nested fill must not trigger another filter pass.
    _suppress_local_filter = False
    # Last local-filter outcome, so a slider drag that doesn't flip any image skips the re-fill.
    _last_unfit_set = None
    _last_filtered_geoms = None
    # Cached widen-warning messages backing the (!) indicator's click handler.
    _widen_details = None

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
        # DataCatalogController is built after PreviewService (below): its two preview buttons
        # wire to that service, which in turn needs processing_service for the in-template
        # placement rules.

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
        self.add_layer_action = QAction(u"Use as AOI in Mapflow")
        self.add_layer_action.setIcon(plugin_icon)
        self.remove_layer_action = QAction(u"Remove AOI from Mapflow")
        self.remove_layer_action.setIcon(plugin_icon)

        # Before setup_add_layer_menu(), which connects these actions to the controller.
        self.aoi_service = AoiService(iface=self.iface,
                                      app_context=self.app_context,
                                      plugin_dir=self.plugin_dir,
                                      result_loader=self.result_loader,
                                      data_catalog_service=self.data_catalog_service,
                                      processing_service=self.processing_service)
        self.preview_service = PreviewService(iface=self.iface,
                                              app_context=self.app_context,
                                              http=self.http,
                                              plugin_dir=self.plugin_dir,
                                              config=self.config,
                                              result_loader=self.result_loader,
                                              processing_service=self.processing_service,
                                              data_catalog_service=self.data_catalog_service)
        self.data_catalog_controller = DataCatalogController(self.dlg,
                                                             self.data_catalog_service,
                                                             self.preview_service)
        # Before SearchService, which resolves sortable columns through it. Was created further
        # down with the provider-dialog wiring; construction order is load-bearing here.
        self.config_search_columns = ConfigColumns()
        self.search_view = SearchView(dlg=self.dlg, config=self.config)
        self.local_filter_service = LocalFilterService()
        self.search_service = SearchService(iface=self.iface,
                                            app_context=self.app_context,
                                            http=self.http,
                                            plugin_dir=self.plugin_dir,
                                            config=self.config,
                                            config_search_columns=self.config_search_columns,
                                            result_loader=self.result_loader,
                                            provider_service=self.provider_service)
        # Search wiring. Results/pager signals stay here for now — the run and pagination
        # handlers they end at are still mapflow.py slots (see SearchController's docstring).
        self.search_service.resultsReceived.connect(self._on_search_results)
        self.search_service.metadataLayerReady.connect(self._on_metadata_layer_ready)
        self.search_service.pagerChanged.connect(self.search_view.show_pages)
        self.search_service.pagerHidden.connect(self.search_view.hide_pages)
        # Owns the preview-dispatch handlers (search button, cell/double click) and their wiring.
        self.search_controller = SearchController(search_service=self.search_service,
                                                  search_view=self.search_view,
                                                  preview_service=self.preview_service,
                                                  provider_service=self.provider_service,
                                                  search_button=self.dlg.searchImageryButton,
                                                  metadata_table=self.dlg.metadataTable)
        self.aoi_view = AoiView(dlg=self.dlg, iface=self.iface)
        # Template-AOI session wiring. It belongs to TemplateController, which the templates
        # step creates; until then mapflow.py holds the connects (the spec allows wiring here,
        # not domain logic).
        self.aoi_service.editSessionStarted.connect(self.aoi_view.enter_edit_session)
        self.aoi_service.editSessionEnded.connect(self.aoi_view.leave_edit_session)
        self.aoi_view.saveRequested.connect(self.aoi_service.save_session)
        self.aoi_view.cancelRequested.connect(self.aoi_service.cancel_session)
        self.processing_controller = ProcessingController(
            iface=self.iface,
            aoi_service=self.aoi_service,
            aoi_view=self.aoi_view,
            add_layer_action=self.add_layer_action,
            remove_layer_action=self.remove_layer_action)

        # Templates (MR-1): create / update-search-params / exclude-from-search.
        self.template_service = TemplateService(app_context=self.app_context,
                                                processing_service=self.processing_service,
                                                plugin_dir=self.plugin_dir,
                                                aoi_service=self.aoi_service,
                                                result_loader=self.result_loader,
                                                search_service=self.search_service)
        self.template_view = TemplateView(dlg=self.dlg, iface=self.iface, config=self.config)
        self.template_controller = TemplateController(
            template_service=self.template_service,
            template_view=self.template_view,
            search_view=self.search_view,
            aoi_view=self.aoi_view,
            aoi_service=self.aoi_service,
            provider_service=self.provider_service,
            processing_service=self.processing_service,
            app_context=self.app_context,
            iface=self.iface,
            update_search_button=self.dlg.updateTemplateSearch,
            exclude_action=self.dlg.exclude_from_search_action,
            processings_table=self.dlg.processingsTable,
            see_processings_action=self.dlg.see_processings_action,
            see_search_results_action=self.dlg.see_search_results_action,
            selection_sync=self.sync_layer_selection_with_table)

        self.setup_add_layer_menu()
        # Add options menu functionality
        self.setup_options_menu_connections()
        # Layer actions
        iface.addCustomActionForLayerType(self.add_layer_action, None, QgsMapLayerType.VectorLayer, True)
        iface.addCustomActionForLayerType(self.remove_layer_action, None, QgsMapLayerType.VectorLayer, False)
        self.add_layer_action.triggered.connect(self.processing_controller.use_current_layer_as_aoi)
        self.remove_layer_action.triggered.connect(
            self.processing_controller.stop_using_current_layer_as_aoi)
        self.dlg.useAllVectorLayers.stateChanged.connect(self.toggle_all_layers)
        self.processing_controller.refresh_excepted_layers()

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
        # Entering and leaving a template is TemplateController's entirely — it owns the layers,
        # the search results and the view state they drive.
        # Processings ratings
        self.dlg.processingsTable.itemSelectionChanged.connect(self.enable_feedback)
        self.dlg.processingsTable.itemSelectionChanged.connect(self.on_processings_selection_changed)
        self.dlg.ratingSubmitButton.clicked.connect(self.submit_processing_rating)
        self.dlg.enable_rating(False, False)  # by default disabled
        self.dlg.enable_review(False)
        # Processing feedback
        self.dlg.ratingComboBox.activated.connect(self.enable_feedback)
        self.dlg.processingsTable.cellClicked.connect(self.update_processing_current_rating)
        # Processing review
        self.dlg.acceptButton.clicked.connect(self.accept_processing)
        self.dlg.reviewButton.clicked.connect(self.show_review_dialog)
        self.review_dialog.accepted.connect(self.submit_review)

        # ========== 13. PROVIDERS ==========
        # searchImageryButton and the metadata table's double/cell-click previews are wired by
        # SearchController (constructed above).
        self.dlg.addProvider.clicked.connect(self.add_provider)
        self.dlg.editProvider.clicked.connect(self.edit_provider)
        self.dlg.removeProvider.clicked.connect(self.remove_provider)

        self.meta_table_layer_connection = self.dlg.metadataTable.itemSelectionChanged.connect(
            self.sync_table_selection_with_image_id_and_layer)
        self.dlg.metadataTable.itemSelectionChanged.connect(self.update_start_processing_button_state)
        self.app_context.meta_layer_table_connection = None
        self.dlg.getMetadata.clicked.connect(self.handle_metadata_button_click)
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
        self.processing_controller.refresh_excepted_layers()

    def toggle_all_layers(self, state: bool):
        self.processing_controller.refresh_excepted_layers()
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
        
        self.draw_aoi.triggered.connect(self.processing_controller.draw_aoi)
        self.use_imagery_extent.triggered.connect(self.processing_controller.create_aoi_from_imagery)
        self.create_aoi_from_map_action.triggered.connect(
            self.processing_controller.create_aoi_from_map_extent)
        self.dlg.addAoiButton.setMenu(self.add_layer_menu)

    def setup_options_menu_connections(self):
        self.dlg.save_result_action.triggered.connect(self.download_results_file)
        self.dlg.download_aoi_action.triggered.connect(self.download_aoi_file)
        self.dlg.see_details_action.triggered.connect(self.show_selected_details)
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
        self.dlg.aoi_update_geometry_action.triggered.connect(
            self.aoi_service.start_update_session)
        self.dlg.aoi_draw_action.triggered.connect(self.aoi_service.start_draw_session)
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
            no_session = not self.aoi_service.session_active
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
            self.template_service.show_template_details(template)
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

    # ==================== AOI edit/draw/add sessions ==================== #
    def add_aoi_from_layer_dialog(self):
        """Add AOI(s) from existing polygon layer(s) chosen in a multi-select dialog."""
        if not self.processing_service.active_template or self.aoi_service.session_active:
            return
        layers = self.aoi_service.selectable_layers()
        if not layers:
            self.alert(self.tr("There are no polygon layers to add as AOIs. Draw one on the map "
                               "or load a vector layer first."), QMessageBox.Information)
            return
        selected_ids = self.aoi_view.pick_aoi_layers(layers)
        if not selected_ids:
            return
        self.aoi_service.add_aois_from_layers(selected_ids)

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
            self.search_controller.reconnect_cell_preview()
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
            self.template_controller.apply_new_image_markers()
        self._mark_unfit_rows(unfit)
        self._hide_unfit_footprints(getattr(self.app_context, "metadata_layer", None), unfit)
        self.search_controller.reconnect_cell_preview()
        self._update_widen_indicator()
        # The fill above hid the sort arrow (setSortingEnabled(False)); put it back so it persists.
        self._restore_search_sort_indicator()

    def _unfit_local_indices(self, features: list) -> set:
        """Which results fail the current filter, computed by `LocalFilterService`. This wrapper
        assembles the criteria from the widgets and `app_context`; the computation itself is
        widget-free and functional-tier tested."""
        return self.local_filter_service.unfit_indices(features, self._filter_criteria())

    def _filter_criteria(self) -> FilterCriteria:
        """The filter widgets + available-provider context, resolved to a `FilterCriteria`."""
        min_off_nadir, max_off_nadir = self.dlg.off_nadir_range()
        return FilterCriteria(
            date_from=self.dlg.metadataFrom.date(),
            date_to=self.dlg.metadataTo.date(),
            max_cloud_cover=self.dlg.maxCloudCover.value(),
            min_intersection=self.dlg.minIntersection.value(),
            off_nadir_filtered=not self.dlg.off_nadir_is_full_range(),  # full 0-30 = no filter
            min_off_nadir=min_off_nadir,
            max_off_nadir=max_off_nadir,
            provider_set=self._allowed_provider_set(),
            product_filter=self._product_category_filter(),
        )

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
        """The ways the current filter widgets are wider than the baseline that fetched the
        current results. The comparison is `LocalFilterService`; this passes the current widget
        values (as a baseline snapshot) and the fetched baseline."""
        return self.local_filter_service.widen_messages(
            self._current_filter_baseline(), self.app_context.search_baseline_filters)

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
            self.search_view.apply_providers_to_combo(providers)
        # Re-filter once against the restored widgets (some setters above may not have changed a
        # value, so their change-signal would not have fired the filter).
        self.apply_local_filter()

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
            if self.search_service.is_search_metadata_layer(layer):
                continue
            layer.selectionChanged.connect(self.area_calculator_service.calculate_aoi_area_selection)
            layer.geometryChanged.connect(self.area_calculator_service.calculate_aoi_area_layer_edited)
            layer.featureAdded.connect(self.area_calculator_service.calculate_aoi_area_layer_edited)
            layer.featuresDeleted.connect(self.area_calculator_service.calculate_aoi_area_layer_edited)

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
            self.search_service.display_metadata_geojson_layer(
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
            provider = self.search_service.imagery_search_provider
            # we need to deselect table to be able to use the non-search provider
        if provider != self.app_context.search_provider:
            self.app_context.search_provider = provider
            provider_changed = True
        return provider_changed

    def replace_search_provider_index(self):
        # The logic moved to SearchView; the regular-search paths still call this until they move
        # to SearchController.
        self.search_view.ensure_search_provider(self.provider_service)

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
        self.metadata_seen_action.triggered.connect(
            self.template_controller.mark_selected_images_seen)
        self.metadata_seen_all_action.triggered.connect(
            self.template_controller.mark_all_images_seen)
        self.dlg.markSeenButton.setPopupMode(QToolButton.MenuButtonPopup)
        self.dlg.markSeenButton.setMenu(self.metadata_seen_menu)
        self.dlg.markSeenButton.setDefaultAction(self.metadata_seen_action)

    def set_metadata_search_mode(self, mode: str):
        self.metadata_search_mode = mode
        self.dlg.getMetadata.setText(self.tr("Plan search") if mode == "plan" else self.tr("Search"))
        self.update_plan_search_message()

    def update_plan_search_message(self) -> None:
        """A template must belong to a project. In plan mode without one, prompt the user in
        the cost/message label (the immediate search is never blocked, so the button stays usable)."""
        message = self.template_service.project_required_message
        if getattr(self, "metadata_search_mode", "search") == "plan" and not self.app_context.current_project:
            self.template_view.show_project_required(message)
        else:
            self.template_view.clear_project_required(message)

    def handle_metadata_button_click(self):
        if getattr(self, "metadata_search_mode", "search") == "plan":
            self.template_controller.create_search_template()
            return
        # An immediate search over a too-large AOI is offered as a Planned Search instead (T8).
        if self.template_service.search_area_exceeds_limit():
            self.template_controller.prompt_plan_search()
            return
        self.get_metadata()

    def on_metadata_header_clicked(self, column: int) -> None:
        """Clicking a *sortable* search column header re-runs the search sorted server-side by that
        column, toggling ASC/DESC on repeat clicks. Only the columns the API can sort on
        (config.SEARCH_SORT_FIELDS) react; the rest (preview, product type, band order, image id)
        do nothing. Applies to both regular search (/catalog/meta) and template results (the
        template-images endpoint accepts the same sortBy/sortOrder)."""
        if self.dlg.metadataTable.rowCount() == 0:
            return  # nothing searched yet
        sort_field = self.search_service.sort_column_field(column)
        if not sort_field:
            return  # column is not server-sortable
        self.search_service.toggle_sort(sort_field)
        self._update_search_sort_indicator(column)
        # Re-request the first page with the new sort — the template-images endpoint and
        # /catalog/meta take the same sort params, so both re-sort server-side.
        if self.processing_service.in_template_mode:
            self.template_controller.load_search_page(0)
        else:
            self.get_metadata()

    def _update_search_sort_indicator(self, column: int) -> None:
        header = self.dlg.metadataTable.horizontalHeader()
        header.setSortIndicatorShown(True)
        order = Qt.DescendingOrder if self.search_service.sort_order == "DESC" else Qt.AscendingOrder
        header.setSortIndicator(column, order)

    def _restore_search_sort_indicator(self) -> None:
        """Re-show the sort arrow on the active sort column. Every table (re)fill calls
        setSortingEnabled(False), which Qt implements as hiding the sort indicator, so it must be
        restored after each fill (otherwise the arrow flashes on click and immediately vanishes)."""
        column = self.search_service.active_sort_column()
        if column is not None:
            self._update_search_sort_indicator(column)

    def get_metadata(self, _: Optional[bool] = False, offset: Optional[int] = 0) -> None:
        """Metadata is image footprints with attributes like acquisition date or cloud cover."""
        # Drop the previous Preview-cell connection so a refill does not stack it (multiple
        # searches would otherwise fire the preview several times per click).
        self.search_view.disconnect_cell_preview()
        # If current provider does not support search, we should select ImagerySearchProvider to be able to search
        self.replace_search_provider_index()
        # A regular search replaces any template results, so a "Start" is no longer planned.
        self.app_context.open_template_results_id = None

        self.search_view.clear_table()
        self.search_view.remove_more_button()
        provider = self.provider_service.providers[self.search_view.provider_index()]
        # Check if the AOI is defined
        if self.app_context.aoi:
            aoi = self.app_context.aoi
        else:
            self.alert(self.tr('Please, select a valid area of interest'))
            return

        if not self.check_if_output_directory_is_selected():
            return  # only when outputDirectory is empty AND user closed selection dialog
        # All imagery search goes through the Mapflow catalog API, which filters server-side.
        # Every filter widget is read once, here, so the request is built from what the widgets
        # said when Search was pressed rather than from whatever they say by the time it is sent.
        self.search_service.search(aoi=aoi,
                                   provider=provider,
                                   aoi_layer=self.aoi_view.current_layer(),
                                   baseline_filters=self._current_filter_baseline(),
                                   offset=offset,
                                   **self.search_view.search_parameters())

    def clear_metadata(self):
        """Drop the search results. The service owns the results and the layer; the table and the
        widen (!) indicator are widgets, so they are cleared here until `SearchController` lands."""
        self.search_service.clear()
        self.search_view.clear_table()
        self.search_view.set_widen_warning_visible(False)

    def _on_search_results(self, geoms) -> None:
        """Built-in Qt sorting stays OFF: results already arrive in the server's sort order, and
        a header click re-requests rather than sorting locally."""
        self.search_view.fill_table(geoms, sort=False)

    def _on_metadata_layer_ready(self, layer) -> None:
        """Selecting a footprint on the map selects the matching table row (and triggers preview)."""
        self.app_context.meta_layer_table_connection = layer.selectionChanged.connect(
            self.sync_layer_selection_with_table)

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

    def on_metadata_table_cell_clicked(self, row: int, column: int):
        """Keep click behavior passive; marking seen is handled by Seen actions only."""
        return

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
        the service; the layers, results and view state follow from ``templateOpened``, which
        `TemplateController` listens to.
        """
        self.project_processing_controller.enter_template(template)

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
    
    def show_search_next_page(self):
        self._show_search_page(self.search_service.next_page_offset())

    def show_search_previous_page(self):
        self._show_search_page(self.search_service.previous_page_offset())

    def _show_search_page(self, offset: int):
        """Which endpoint serves the page depends on where the results came from, so the branch
        stays out of `SearchService` — it is coordination between two regions, and moves to
        `SearchController` / `TemplateController` rather than into either service."""
        if self.processing_service.in_template_mode:
            self.template_controller.load_search_page(offset)
        else:
            self.get_metadata(offset=offset)
    
    def selected_search_product_types(self):
        """Kept as a forwarder: template creation reads the same widgets, and that code moves in
        the templates step."""
        return self.search_view.product_types()

    def selected_search_providers(self):
        return self.search_view.search_providers()

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

