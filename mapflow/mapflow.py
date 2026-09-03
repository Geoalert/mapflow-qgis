import json
import logging
import os.path
import shutil
from configparser import ConfigParser  # parse metadata.txt -> QGIS version check (compatibility)
from pathlib import Path
from typing import List, Optional, Callable

from PyQt5.QtCore import (
    QCoreApplication, QDate, QObject, Qt,
    QTimer, QTranslator
)
from PyQt5.QtNetwork import QNetworkReply
from PyQt5.QtWidgets import (
    QAction, QApplication, QFileDialog,
    QMenu, QMessageBox
)
from qgis.core import (
    QgsDistanceArea, QgsMapLayer, QgsMapLayerType, QgsProject
)

from .config import Config, ConfigColumns
# Functional
from .functional import helpers, layer_utils
from .functional.app_context import AppContext
from .functional.controller.data_catalog_controller import DataCatalogController
from .functional.controller.project_processing_controller import ProjectProcessingController
from .functional.controller.processing_controller import ProcessingController
from .functional.controller.provider_controller import ProviderController
from .functional.view.provider_view import ProviderView
from .functional.controller.search_controller import SearchController
from .functional.controller.template_controller import TemplateController
from .functional.service.template_service import TemplateService
from .functional.view.template_view import TemplateView
from .functional.service.aoi_service import AoiService
from .functional.service.local_filter_service import LocalFilterService
from .functional.service.preview_service import PreviewService
from .functional.service.search_service import SearchService
from .functional.view.aoi_view import AoiView
from .functional.view.search_view import SearchView
from .functional.service import (DataCatalogService,
                                 ProcessingService,
                                 ProjectService,
                                 ProviderService)
from .functional.service.account_service import AccountService
from .functional.service.session_service import SessionService
from .functional.service.alert_service import AlertService, alert
from .functional.service.area_calculator_service import AreaCalculatorService
# HTTP
from .http import (Http,
                   api_message_parser,
                   get_error_report_body)
# Schema
from .schema import ProviderReturnSchema
from .schema.project import MapflowProject
# Dialogs
from .dialogs import (ErrorMessageWidget,
                      MainDialog,
                      MapflowLoginDialog,
                      ProviderDialog,
                      ReviewDialog)
from .dialogs.icons import plugin_icon
# Providers
from .model.provider import (DefaultProvider,
                              ImagerySearchProvider,
                              MyImageryProvider,
                              ProviderInterface,
                              ProvidersList)

logger = logging.getLogger(__name__)


class Mapflow(QObject):
    """This class represents the plugin. It is instantiated by QGIS."""

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
        self.plugin_icon = plugin_icon
        self.dlg = MainDialog(self.main_window, self.app_context.settings)
        self.review_dialog = ReviewDialog(self.dlg)
        self.dlg_provider = ProviderDialog(self.dlg)
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

        # ========== 3b. SESSION ==========
        # Owns the credentials and the auth method. Built after `Http` (it drives it) and before
        # the login dialog (which asks it which input to show).
        self.session_service = SessionService(http=self.http,
                                              app_context=self.app_context,
                                              config=self.config,
                                              on_authenticated=self.log_in_callback)
        self.dlg_login = self.set_up_login_dialog()
        self.session_service.tokenRejected.connect(self.dlg_login.invalidToken.setVisible)
        self.session_service.loginRequired.connect(self.dlg_login.show)
        self.session_service.authTypeChanged.connect(self.on_auth_type_changed)
        self.session_service.loggedOut.connect(self.on_logged_out)

        # ========== 4. ACCOUNT STATUS ==========
        # Owns both /user/status polls and their timers: the steady-state refresh for the limits
        # and balance, and the post-login retry that the startup configuration below waits for.
        self.account_service = AccountService(http=self.http,
                                              app_context=self.app_context,
                                              config=self.config,
                                              server=self.server,
                                              plugin_name=self.plugin_name)
        self.account_service.balanceChanged.connect(self.dlg.balanceLabel.setText)
        self.account_service.statusApplied.connect(self.on_account_status)
        self.account_service.startupGaveUp.connect(
            lambda message: self.alert(message, icon=QMessageBox.Warning))

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

        self.processing_service = ProcessingService(http=self.http,
                                                    dlg=self.dlg,
                                                    iface=self.iface,
                                                    result_loader=self.result_loader,
                                                    app_context=self.app_context,
                                                    timer_interval=self.config.PROCESSING_TABLE_REFRESH_INTERVAL * 1000)
        
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
        # The pager signals drive the view directly; the results land in SearchController, which
        # owns the run. Which endpoint a *page* comes from still forks on template mode below.
        self.search_service.pagerChanged.connect(self.search_view.show_pages)
        self.search_service.pagerHidden.connect(self.search_view.hide_pages)
        self.aoi_view = AoiView(dlg=self.dlg, iface=self.iface)
        # Owns the preview-dispatch handlers (search button, cell/double click), the local filter
        # over the fetched results, the two-way table<->footprint selection sync, and their wiring.
        self.search_controller = SearchController(search_service=self.search_service,
                                                  search_view=self.search_view,
                                                  preview_service=self.preview_service,
                                                  provider_service=self.provider_service,
                                                  search_button=self.dlg.searchImageryButton,
                                                  metadata_table=self.dlg.metadataTable,
                                                  local_filter_service=self.local_filter_service,
                                                  app_context=self.app_context,
                                                  widen_warning_button=self.dlg.searchWidenWarning,
                                                  reset_filters_button=self.dlg.resetSearchFilters,
                                                  clear_search_button=self.dlg.clearSearch,
                                                  aoi_view=self.aoi_view,
                                                  ensure_output_dir=self.check_if_output_directory_is_selected)
        self.search_service.metadataLayerReady.connect(self.search_controller.on_metadata_layer_ready)
        self.search_service.resultsReceived.connect(self.search_controller.on_search_results)
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
            remove_layer_action=self.remove_layer_action,
            processing_service=self.processing_service,
            processing_view=self.processing_service.view,
            app_context=self.app_context,
            review_dialog=self.review_dialog,
            rating_submit_button=self.dlg.ratingSubmitButton,
            rating_combo=self.dlg.ratingComboBox,
            accept_button=self.dlg.acceptButton,
            review_button=self.dlg.reviewButton,
            processings_table=self.dlg.processingsTable,
            provider_service=self.provider_service,
            model_combo=self.dlg.modelCombo,
            model_options_changed=self.dlg.modelOptionsChanged,
            metadata_table=self.dlg.metadataTable)

        # Templates (MR-1): create / update-search-params / exclude-from-search.
        self.template_service = TemplateService(app_context=self.app_context,
                                                processing_service=self.processing_service,
                                                plugin_dir=self.plugin_dir,
                                                aoi_service=self.aoi_service,
                                                result_loader=self.result_loader,
                                                search_service=self.search_service)
        # TemplateService owns the in-template view, but AoiService and PreviewService are built
        # before it (it takes AoiService as a collaborator), so their back-links are set here.
        self.aoi_service.template_service = self.template_service
        self.preview_service.template_service = self.template_service

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
            processing_view=self.processing_service.view,
            rename_action=self.dlg.template_rename_action,
            pause_action=self.dlg.template_pause_action,
            resume_action=self.dlg.template_resume_action,
            restart_action=self.dlg.template_restart_action)

        # After TemplateService: this controller owns the choice between the project list and the
        # in-template view, so it subscribes to both services' refresh signals.
        self.project_processing_controller = ProjectProcessingController(
            dlg=self.dlg,
            processing_service=self.processing_service,
            project_service=self.project_service,
            template_service=self.template_service,
            app_context=self.app_context,
            aoi_service=self.aoi_service,
            data_catalog_service=self.data_catalog_service,
            result_loader=self.result_loader,
            processing_view=self.processing_service.view,
            ensure_output_directory=self.ensure_output_directory)

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
        # SearchController is built well before this service (it is needed by the search wiring
        # above), so its cost-recompute collaborator is set here, as the other back-links are.
        self.search_controller.area_calculator_service = self.area_calculator_service
        # Restoring a provider's saved selection re-selects footprints, which must drive the table.
        self.provider_service.selection_sync_callback = \
            self.search_controller.sync_layer_selection_with_table

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
        # The model combo and its option checkboxes are wired by ProcessingController.
        # Memorize dialog element sizes & positioning
        self.dlg.finished.connect(self.save_dialog_state)
        # Connect buttons
        self.dlg.logoutButton.clicked.connect(self.session_service.logout)
        self.dlg.selectOutputDirectory.clicked.connect(self.select_output_directory)
        self.dlg.downloadResultsButton.clicked.connect(
            self.project_processing_controller.load_results)
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
        self.dlg.processingsTable.cellDoubleClicked.connect(
            self.project_processing_controller.load_results)
        self.dlg.deleteProcessings.clicked.connect(self.processing_service.confirm_delete_processings)
        self.processing_service.connect_processings_pagination()
        # Entering and leaving a template is TemplateController's entirely — it owns the layers,
        # the search results and the view state they drive. What the processings-table selection
        # enables is split between the two controllers that own those widgets: the Start button is
        # ProcessingController's, the Delete button and the context menu ProjectProcessingController's.
        # Review and rating are ProcessingController's — it owns those handlers now.
        self.dlg.enable_rating(False, False)  # by default disabled
        self.dlg.enable_review(False)

        # ========== 13. PROVIDERS ==========
        # searchImageryButton and the metadata table's double/cell-click previews are wired by
        # SearchController (constructed above); the add/edit/remove buttons and the zoom combo by
        # ProviderController, which owns those handlers.
        self.provider_view = ProviderView(dlg=self.dlg)
        self.provider_controller = ProviderController(
            provider_service=self.provider_service,
            provider_view=self.provider_view,
            provider_dialog=self.dlg_provider,
            app_context=self.app_context,
            processing_service=self.processing_service,
            add_button=self.dlg.addProvider,
            edit_button=self.dlg.editProvider,
            remove_button=self.dlg.removeProvider,
            zoom_combo=self.dlg.zoomCombo)

        self.search_controller.connect_table_selection()
        self.app_context.meta_layer_table_connection = None
        self.dlg.getMetadata.clicked.connect(self.handle_metadata_button_click)
        self.dlg.metadataTable.cellClicked.connect(self.on_metadata_table_cell_clicked)
        self.dlg.metadataTable.horizontalHeader().sectionClicked.connect(self.on_metadata_header_clicked)
        self.dlg.rasterSourceChanged.connect(self.on_provider_change)
        self.dlg.metadataTableFilled.connect(self.search_controller.apply_local_filter)
        # Instant local filtering: changing a filter widget re-filters the already-fetched
        # results in place (no server request), for both regular search and templates.
        # The handler and the Reset/(!) buttons are SearchController's; only these
        # widget-change connections stay here, because the widgets are the dialog's.
        for signal in (self.dlg.minIntersection.valueChanged,
                       self.dlg.maxCloudCover.valueChanged,
                       self.dlg.offNadirSlider.rangeChanged,
                       self.dlg.metadataFrom.dateChanged,
                       self.dlg.metadataTo.dateChanged,
                       # Provider selection/availability and product type (Mosaic/Image) are
                       # local filters too; re-filter when any of them change.
                       self.dlg.searchProvidersCombo.checkedItemsChanged,
                       self.dlg.hideUnavailableResults.toggled,
                       self.dlg.searchMosaicCheckBox.toggled,
                       self.dlg.searchImageCheckBox.toggled):
            signal.connect(self.search_controller.apply_local_filter)
        self.dlg.searchRightButton.clicked.connect(self.show_search_next_page)
        self.dlg.searchLeftButton.clicked.connect(self.show_search_previous_page)
        self.search_view.searchModeChanged.connect(self.template_controller.on_search_mode_changed)
        self.search_view.setup_search_mode_dropdown()
        self.search_view.setup_seen_dropdown(
            on_seen=self.template_controller.mark_selected_images_seen,
            on_seen_all=self.template_controller.mark_all_images_seen)

        # ========== 14. ZOOM SELECTOR CONFIGURATION ==========
        # currentIndexChanged is wired by ProviderController, which owns the handler.
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

    def on_account_status(self, response_data: dict, app_startup_request: bool) -> None:
        """Configure the plugin from an account-status response.

        Only the first response after login configures anything: everything below depends on the
        billing mode, the review workflow and the provider lists, none of which are known before
        it. Later refreshes only update the limits `AccountService` has already applied.
        """
        if not app_startup_request:
            return
        # Storage quota for My Imagery: needed once at startup, and refreshed later by
        # mosaicsUpdated. Issuing it per retry would mean a second endpoint polled at the
        # retry interval, with its own error dialog on every failed tick.
        self.data_catalog_service.get_user_limit()
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
        self.dlg.save_result_action.triggered.connect(
            self.project_processing_controller.download_results_file)
        self.dlg.download_aoi_action.triggered.connect(
            self.project_processing_controller.download_aoi_file)
        # 'See details' and the menu's own aboutToShow are wired by ProjectProcessingController,
        # which owns what the processings table offers for the current selection.
        self.dlg.processing_update_action.triggered.connect(self.processing_service.update_processing)
        self.dlg.processing_restart_action.triggered.connect(self.processing_service.restart_processing)
        self.dlg.processing_duplicate_action.triggered.connect(self.check_dir_and_duplicate_processing)
        # The template run-state actions are wired by TemplateController, which owns their handlers.
        # AOI actions (in-template view)
        self.dlg.aoi_rename_action.triggered.connect(self.template_service.rename_aoi)
        self.dlg.aoi_delete_action.triggered.connect(self.template_service.delete_aoi)
        self.dlg.aoi_add_action.triggered.connect(self.add_aoi_from_layer_dialog)
        self.dlg.aoi_update_geometry_action.triggered.connect(
            self.aoi_service.start_update_session)
        self.dlg.aoi_draw_action.triggered.connect(self.aoi_service.start_draw_session)
        self.dlg.saveOptionsButton.setMenu(self.dlg.options_menu)

    # ==================== AOI edit/draw/add sessions ==================== #
    def add_aoi_from_layer_dialog(self):
        """Add AOI(s) from existing polygon layer(s) chosen in a multi-select dialog."""
        if not self.template_service.active_template or self.aoi_service.session_active:
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

    def set_up_login_dialog(self) -> MapflowLoginDialog:
        """Create a login dialog, set its title and signal-slot connections."""
        dlg_login = MapflowLoginDialog(self.main_window,
                                       self.session_service.use_oauth,
                                       self.session_service.saved_token)
        dlg_login.setWindowTitle(helpers.generate_plugin_header(self.tr("Log in ") + self.plugin_name,
                                                                     self.config.MAPFLOW_ENV,
                                                                     None, None, None))
        dlg_login.logIn.clicked.connect(self.log_in)
        dlg_login.useOauth.toggled.connect(self.session_service.set_auth_type)
        return dlg_login

    def log_in(self) -> None:
        """The Log in button. What the user typed is a widget read, so it is taken here and handed
        over; which auth method applies is the service's own state."""
        self.session_service.authenticate(self.dlg_login.token_value())

    def on_auth_type_changed(self, use_oauth: bool, token: str) -> None:
        self.dlg_login.set_auth_type(use_oauth=use_oauth, token=token)

    def on_logged_out(self) -> None:
        """Everything that must stop when the session ends. The polls belong to other services,
        so they are stopped here rather than by `SessionService` reaching into them."""
        self.processing_service.processing_fetch_timer.stop()
        self.account_service.stop_refreshing()
        self.account_service.stop_startup_polling()
        self.dlg.close()

    def on_provider_change(self) -> None:
        """A different imagery source was picked.

        Stays in the composition root rather than moving to `ProviderController`: the effects land
        in the search, catalog and processing regions at once, and reaching into those controllers
        from one of them would be controller-to-controller (`spec/007_architecture.md`
        § Controllers). Everything it touches here is a view or a service.
        """
        provider = self.provider_service.providers[self.provider_view.provider_index()]
        self.app_context.data_provider = provider
        # Changes in search tab
        self.toggle_imagery_search(provider)
        if isinstance(provider, MyImageryProvider):
            self.provider_view.show_catalog_tab()
            self.area_calculator_service.calculate_aoi_area_catalog()
            self.processing_service.validate_all_processing_params(allow_empty_name=True)
            # Fixed-resolution source: no zoom to choose.
            self.provider_view.enable_zoom(False)
            self.provider_view.reset_zoom()
        else:
            self.provider_view.enable_zoom(not isinstance(provider, ImagerySearchProvider))
            # Re-calculate the AOI: it can change where an image and the area intersect.
            self.area_calculator_service.calculate_aoi_area_polygon_layer(
                self.aoi_view.current_layer())
        if provider.requires_image_id:
            self.provider_view.show_imagery_search_tab()
        # A planned (template) start only applies with the imagery-search source, so the Start
        # button label depends on the data source: switching an open template to My imagery must
        # drop the "planned" wording. Text only — the enabled state comes from the validation above.
        self.processing_controller.update_start_processing_button_text()

    def save_dialog_state(self):
        """Memorize dialog element sizes & positioning to allow user to customize the look."""
        # Save main dialog size & position
        self.app_context.settings.setValue('mainDialogState', self.dlg.saveGeometry())

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
            self.search_service.build_metadata_layer(
                os.path.join(self.app_context.temp_dir, self.app_context.search_provider.metadata_layer_name),
                f"{self.app_context.search_provider.name} metadata")
            # Keep the restored results available to the instant local filter (fill below emits
            # metadataTableFilled -> apply_local_filter), so switching back to a provider re-applies
            # the current filter widgets instead of showing a stale/unfiltered view.
            self.app_context.search_result_geojson = geoms
        else:
            self.search_controller.clear_results()

        self.search_view.setup_imagery_search(
            provider=self.app_context.search_provider,
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

    def handle_metadata_button_click(self):
        """Which of the three things the Search button does. The fork spans the search and
        template regions, so it stays here: in `SearchController` the two `template_controller`
        calls below would be controller-to-controller (`spec/007_architecture.md` § Controllers)."""
        if self.search_view.search_mode == "plan":
            self.template_controller.create_search_template()
            return
        # An immediate search over a too-large AOI is offered as a Planned Search instead (T8).
        if self.template_service.search_area_exceeds_limit():
            self.template_controller.prompt_plan_search()
            return
        self.search_controller.run_search()

    def on_metadata_header_clicked(self, column: int) -> None:
        """Clicking a *sortable* search column header re-runs the search sorted server-side by that
        column, toggling ASC/DESC on repeat clicks. Only the columns the API can sort on
        (config.SEARCH_SORT_FIELDS) react; the rest (preview, product type, band order, image id)
        do nothing. Applies to both regular search (/catalog/meta) and template results (the
        template-images endpoint accepts the same sortBy/sortOrder)."""
        if self.search_view.metadata_row_count() == 0:
            return  # nothing searched yet
        sort_field = self.search_service.sort_column_field(column)
        if not sort_field:
            return  # column is not server-sortable
        self.search_service.toggle_sort(sort_field)
        self.search_view.show_sort_indicator(
            column, descending=self.search_service.sort_order == "DESC")
        # Re-request the first page with the new sort — the template-images endpoint and
        # /catalog/meta take the same sort params, so both re-sort server-side.
        if self.template_service.in_template_mode:
            self.template_controller.load_search_page(0)
        else:
            self.search_controller.run_search()

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

    # =================== Results management ==================== #
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
        self.account_service.stop_refreshing()
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
                self.session_service.logout()
            elif self.session_service.saved_token:  # env changed w/out logging out (admin)
                self.session_service.reject_saved_token()

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

        self.account_service.request_status()
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
        self.account_service.start_refreshing()
        self.account_service.begin_startup_polling()

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

    def show_search_next_page(self):
        self._show_search_page(self.search_service.next_page_offset())

    def show_search_previous_page(self):
        self._show_search_page(self.search_service.previous_page_offset())

    def _show_search_page(self, offset: int):
        """Which endpoint serves the page depends on where the results came from, so the branch
        stays out of `SearchService` — it is coordination between two regions, and moves to
        `SearchController` / `TemplateController` rather than into either service."""
        if self.template_service.in_template_mode:
            self.template_controller.load_search_page(offset)
        else:
            self.search_controller.run_search(offset=offset)
    
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
            self.account_service.request_status()
            self.account_service.start_refreshing()
            return

        token = self.session_service.saved_token
        if not self.session_service.use_oauth and token:
            # Saved token for basic auth
            self.session_service.login_basic(token)
        else:
            self.dlg_login.show()

