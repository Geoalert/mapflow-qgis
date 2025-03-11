import json
import os.path
import shutil
from base64 import b64encode, b64decode
from configparser import ConfigParser  # parse metadata.txt -> QGIS version check (compatibility)
from datetime import datetime  # processing creation datetime formatting
from pathlib import Path
from typing import List, Optional, Union, Callable, Tuple

from PyQt5.QtCore import (
    QDate, QObject, QCoreApplication, QTimer, QTranslator, Qt, QFile, QIODevice, QTextStream, QByteArray, QTemporaryDir, QVariant
)
from PyQt5.QtGui import QColor
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest, QHttpMultiPart, QHttpPart
from PyQt5.QtWidgets import (
    QApplication, QMessageBox, QFileDialog, QPushButton, QTableWidgetItem, QAbstractItemView, QMenu, QAction, QWidget
)
from PyQt5.QtXml import QDomDocument
from osgeo import gdal
from qgis.core import (
    QgsProject, QgsSettings, QgsMapLayer, QgsVectorLayer, QgsRasterLayer, QgsFeature, Qgis,
    QgsCoordinateReferenceSystem, QgsDistanceArea, QgsGeometry, QgsWkbTypes, QgsPoint, QgsMapLayerType, QgsRectangle
)
from qgis.gui import QgsMessageBarItem

from . import constants
from .dialogs import (MainDialog,
                      MapflowLoginDialog,
                      ErrorMessageWidget,
                      ProviderDialog,
                      ReviewDialog,
                      CreateProjectDialog,
                      UpdateProjectDialog,
                      UpdateProcessingDialog,
                      )
from .dialogs.icons import plugin_icon
from .functional.controller.data_catalog_controller import DataCatalogController
from .config import Config, ConfigSearchColumns
from .entity.billing import BillingType
from .entity.processing import parse_processings_request, Processing, ProcessingHistory, updated_processings
from .entity.provider import (UsersProvider,
                              MaxarProvider,
                              ProvidersList,
                              SentinelProvider,
                              create_provider,
                              DefaultProvider,
                              ImagerySearchProvider,
                              MyImageryProvider,
                              ProviderInterface)
from .entity.workflow_def import WorkflowDef
from .errors import (ProcessingInputDataMissing,
                     BadProcessingInput,
                     PluginError,
                     ImageIdRequired,
                     AoiNotIntersectsImage,
                     ProxyIsAlreadySet)
from .functional import layer_utils, helpers
from .functional.auth import get_auth_id
from .functional.geometry import clip_aoi_to_image_extent
from .functional.processing import ProcessingService
from .functional.project import ProjectService
from .functional.service.data_catalog import DataCatalogService
from .http import (Http,
                   get_error_report_body,
                   data_catalog_message_parser,
                   securewatch_message_parser,
                   api_message_parser,
                   )
from .schema import (PostSourceSchema,
                     PostProcessingSchema,
                     ProviderReturnSchema,
                     ImageCatalogRequestSchema,
                     ImageCatalogResponseSchema)
from .schema.catalog import PreviewType, ProductType
from .schema.project import MapflowProject
from .schema.project import UserRole


class Mapflow(QObject):
    """This class represents the plugin. It is instantiated by QGIS."""

    def __init__(self, iface) -> None:
        """Initialize the plugin.

        :param iface: an instance of the QGIS interface.
        """
        # init configs
        self.search_footprints = dict()
        self.config = Config()
        # init empty params
        self.max_aois_per_processing = self.config.MAX_AOIS_PER_PROCESSING
        self.aoi_size = None
        self.aoi = None
        self.metadata_aoi = None
        self.metadata_layer = None
        self.search_provider = None
        self.is_admin = False
        self.aoi_area_limit = 0.0
        self.username = self.password = ''
        self.version_ok = True
        self.remaining_limit = 0
        self.remaining_credits = 0
        self.billing_type = BillingType.area
        self.review_workflow_enabled = False
        self.processing_cost = 0
        # Save refs to key variables used throughout the plugin
        self.iface = iface
        self.main_window = self.iface.mainWindow()
        self.workflow_defs = {}
        self.current_project = None
        self.user_role = UserRole.owner
        self.aoi_layers = []
        self.preview_dict = {}
        self.project_connection = None
        super().__init__(self.main_window)
        self.project = QgsProject.instance()
        self.message_bar = self.iface.messageBar()
        self.plugin_dir = os.path.dirname(__file__)
        self.plugin_name = self.config.PLUGIN_NAME  # aliased here to be overloaded in submodules
        # Settings will be used to store credentials and various UI customizations
        self.settings = QgsSettings()
        # Get the server environment to connect to (for admins)
        self.server = self.config.SERVER
        self.layer_tree_root = self.project.layerTreeRoot()
        # Set up authentication flags
        self.logged_in = False
        # Init toolbar and toolbar buttons
        self.toolbar = self.iface.addToolBar(self.plugin_name)
        self.toolbar.setObjectName(self.plugin_name)
        # Init project
        # Translation
        locale = self.settings.value('locale/userLocale', 'en_US')[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n', f'mapflow_{locale}.qm')
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)
        # Translate native Qt texts; doesn't work in a cycle for some reason
        QCoreApplication.translate('QPlatformTheme', 'Cancel')
        QCoreApplication.translate('QPlatformTheme', '&Yes')
        QCoreApplication.translate('QPlatformTheme', '&No')
        # Create a namespace for the plugin settings
        self.settings.beginGroup(self.plugin_name.lower())
        if self.settings.value('processings') is None:
            self.settings.setValue('processings', {})
        # If no project id is set, use "default"
        self.project_id = self.settings.value("project_id", "default")
        self.projects = {}
        # Store user's current processing
        self.processing_history = ProcessingHistory.from_settings(
            self.settings.value('processings', {})
            .get(self.config.MAPFLOW_ENV, {})
            .get(self.username, {})
            .get(self.project_id, {}))
        self.processings = []
        # Imagery search pagination
        self.search_page_offset = 0
        self.search_page_limit = self.config.SEARCH_RESULTS_PAGE_LIMIT

        # Init dialogs
        self.use_oauth = (self.settings.value('use_oauth', 'false').lower() == 'true')
        self.plugin_icon = plugin_icon
        self.dlg = MainDialog(self.main_window, self.settings)
        self.dlg_login = self.set_up_login_dialog()
        self.review_dialog = ReviewDialog(self.dlg)
        self.dlg_provider = ProviderDialog(self.dlg)

        self.dlg_provider.accepted.connect(self.edit_provider_callback)
        # Display the plugin's version
        # todo: Move to Maindialog
        metadata_parser = ConfigParser()
        metadata_parser.read(os.path.join(self.plugin_dir, 'metadata.txt'))
        self.plugin_version = metadata_parser.get('general', 'version')
        self.dlg.help.setText(
            self.dlg.help.text().replace('Mapflow', f'{self.plugin_name} {self.plugin_version}', 1)
        )
        # Initialize HTTP request sender
        self.http = Http(self.plugin_version, self.default_error_handler)
        self.calculator = QgsDistanceArea()
        # RESTORE LATEST FIELD VALUES & OTHER ELEMENTS STATE
        self.dlg.outputDirectory.setText(self.settings.value('outputDir'))

        # Setup temporary directory from setting or skip for now
        self.temp_dir = None
        self.setup_tempdir()

        # Initialize services
        self.result_loader = layer_utils.ResultsLoader(iface=self.iface,
                                                       maindialog=self.dlg,
                                                       http=self.http,
                                                       server=self.server,
                                                       project=self.project,
                                                       settings=self.settings,
                                                       plugin_name=self.plugin_name,
                                                       temp_dir=self.temp_dir
                                                       )

        self.data_catalog_service = DataCatalogService(self.http, self.server, self.dlg, self.iface, self.result_loader, self.plugin_version, self.temp_dir)
        self.data_catalog_controller = DataCatalogController(self.dlg, self.data_catalog_service)

        self.project_service = ProjectService(self.http, self.server)
        self.project_service.projectsUpdated.connect(self.update_projects)

        self.processing_service = ProcessingService(self.http, self.server)
        self.processing_service.processingUpdated.connect(lambda: self.http.get(
                url=f'{self.server}/projects/{self.project_id}/processings',
                callback=self.get_processings_callback,
                use_default_error_handler=False  # ignore errors to prevent repetitive alerts
            ))
        # load providers from settings
        errors = []
        try:
            self.user_providers, errors = ProvidersList.from_settings(settings=self.settings)
            self.sentinel_providers = ProvidersList([SentinelProvider(proxy=self.server)])
            self.default_providers = ProvidersList([])
            self.providers = ProvidersList([])
        except Exception as e:
            self.alert(self.tr("Error during loading the data providers: {e}").format(str(e)), icon=Qgis.Warning)
        if errors:
            self.alert(self.tr('We failed to import providers from the settings. Please add them again'),
                       icon=Qgis.Warning)
        self.update_providers()
        self.dlg.minIntersection.setValue(int(self.settings.value('metadataMinIntersection', 0)))
        self.dlg.maxCloudCover.setValue(int(self.settings.value('metadataMaxCloudCover', 100)))
        # Set default metadata dates
        today = QDate.currentDate()
        self.dlg.metadataFrom.setDate(self.settings.value('metadataFrom', today.addMonths(-6)))
        self.dlg.metadataTo.setDate(self.settings.value('metadataTo', today))
        # SET UP SIGNALS & SLOTS
        self.dlg.modelCombo.activated.connect(self.on_model_change)
        self.dlg.modelOptionsChanged.connect(self.on_options_change)
        # Memorize dialog element sizes & positioning
        self.dlg.finished.connect(self.save_dialog_state)
        # Connect buttons
        self.dlg.logoutButton.clicked.connect(self.logout)
        self.dlg.selectOutputDirectory.clicked.connect(self.select_output_directory)
        self.dlg.downloadResultsButton.clicked.connect(self.load_results)
        # (Dis)allow the user to use raster extent as AOI
        self.dlg.useImageExtentAsAoi.toggled.connect(self.toggle_polygon_combos)
        self.dlg.startProcessing.clicked.connect(self.create_processing)
        # Calculate AOI size
        self.dlg.polygonCombo.layerChanged.connect(self.calculate_aoi_area_polygon_layer)
        self.dlg.useImageExtentAsAoi.toggled.connect(self.calculate_aoi_area_use_image_extent)
        self.dlg.mosaicTable.itemSelectionChanged.connect(self.calculate_aoi_area_catalog)
        self.dlg.imageTable.itemSelectionChanged.connect(self.calculate_aoi_area_catalog)
        self.monitor_polygon_layer_feature_selection([
            self.project.mapLayer(layer_id) for layer_id in self.project.mapLayers(validOnly=True)
        ])
        self.project.layersAdded.connect(self.setup_layers_context_menu)
        self.project.layersAdded.connect(self.monitor_polygon_layer_feature_selection)
        # Processings
        self.dlg.processingsTable.cellDoubleClicked.connect(self.load_results)
        self.dlg.deleteProcessings.clicked.connect(self.delete_processings)
        self.dlg.filterProcessings.textChanged.connect(self.dlg.filter_processings_table)
        # Processings ratings
        self.dlg.processingsTable.itemSelectionChanged.connect(self.enable_feedback)
        self.dlg.ratingSubmitButton.clicked.connect(self.submit_processing_rating)
        self.dlg.enable_rating(False, False)  # by default disabled
        self.dlg.enable_review(False)
        # processing feedback fields
        self.dlg.ratingComboBox.activated.connect(self.enable_feedback)
        self.dlg.processingsTable.cellClicked.connect(self.update_processing_current_rating)
        # processing review
        self.dlg.acceptButton.clicked.connect(self.accept_processing)
        self.dlg.reviewButton.clicked.connect(self.show_review_dialog)
        self.review_dialog.accepted.connect(self.submit_review)

        # Providers
        self.dlg.minIntersectionSpinBox.valueChanged.connect(self.filter_metadata)
        self.dlg.maxCloudCoverSpinBox.valueChanged.connect(self.filter_metadata)
        self.dlg.metadataFrom.dateChanged.connect(self.filter_metadata)
        self.dlg.metadataTo.dateChanged.connect(self.filter_metadata)
        self.dlg.searchImageryButton.clicked.connect(self.preview_or_search)

        self.dlg.addProvider.clicked.connect(self.add_provider)
        self.dlg.editProvider.clicked.connect(self.edit_provider)
        self.dlg.removeProvider.clicked.connect(self.remove_provider)

        # Projects
        self.dlg.createProject.clicked.connect(self.create_project)
        self.dlg.deleteProject.clicked.connect(self.delete_project)
        self.dlg.updateProject.clicked.connect(self.update_project)
        self.dlg.filterProject.textChanged.connect(self.filter_projects)

        # Maxar
        self.config_search_columns = ConfigSearchColumns()
        self.meta_table_layer_connection = self.dlg.metadataTable.itemSelectionChanged.connect(
            self.sync_table_selection_with_image_id_and_layer)
        self.meta_layer_table_connection = None
        self.dlg.getMetadata.clicked.connect(self.get_metadata)
        self.dlg.metadataTable.cellDoubleClicked.connect(self.preview)
        self.dlg.rasterSourceChanged.connect(self.on_provider_change)
        self.dlg.clearSearch.clicked.connect(self.clear_metadata)
        self.dlg.metadataTableFilled.connect(self.filter_metadata)
        self.dlg.searchRightButton.clicked.connect(self.show_search_next_page)
        self.dlg.searchLeftButton.clicked.connect(self.show_search_previous_page)
        # Poll processings
        self.processing_fetch_timer = QTimer(self.dlg)
        self.processing_fetch_timer.setInterval(self.config.PROCESSING_TABLE_REFRESH_INTERVAL * 1000)
        self.processing_fetch_timer.timeout.connect(
            lambda: self.http.get(
                url=f'{self.server}/projects/{self.project_id}/processings',
                callback=self.get_processings_callback,
                use_default_error_handler=False  # ignore errors to prevent repetitive alerts
            )
        )
        # Poll user status to get limits
        self.user_status_update_timer = QTimer(self.dlg)
        self.user_status_update_timer.setInterval(self.config.USER_STATUS_UPDATE_INTERVAL * 1000)
        self.user_status_update_timer.timeout.connect(self.refresh_status)
        # timer for user update at startup, in case get_processings request takes too long
        # stopped as soon as first /user/status request is made
        self.app_startup_user_update_timer = QTimer(self.dlg)
        self.app_startup_user_update_timer.setInterval(500)
        self.app_startup_user_update_timer.timeout.connect(self.first_status_request)
        # Add layer menu
        self.add_layer_menu = QMenu()
        self.create_aoi_from_map_action = QAction(self.tr("Create new AOI layer from map extent"))
        self.add_aoi_from_file_action = QAction(self.tr("Add AOI from vector file"))
        self.draw_aoi = QAction(self.tr("Draw AOI at the map"))
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

        # Zoom selection for data source
        self.zoom_selector = (self.config.ZOOM_SELECTOR.lower() == "true")
        self.zoom = None
        if self.zoom_selector:
            self.dlg.zoomCombo.currentIndexChanged.connect(self.on_zoom_change)
            saved_zoom = self.settings.value('zoom')
            if saved_zoom is None:
                self.dlg.zoomCombo.setCurrentIndex(0)
            else:
                zoom_index = self.dlg.zoomCombo.findText(saved_zoom)
                if zoom_index == -1:
                    # Fallback for situation if the settings contain value not available in the list
                    self.dlg.zoomCombo.setCurrentIndex(0)
                    self.settings.setValue('zoom', None)
                else:
                    self.dlg.zoomCombo.setCurrentIndex(zoom_index)

    def setup_layers_context_menu(self, layers: List[QgsMapLayer]):
        for layer in filter(layer_utils.is_polygon_layer, layers):
            self.iface.addCustomActionForLayer(self.add_layer_action, layer)
        self.dlg.polygonCombo.setExceptedLayerList(self.filter_aoi_layers())

    def add_to_layers(self, layer=None):
        if not layer:
            layer = self.iface.layerTreeView().currentLayer()
        if layer not in self.aoi_layers:
            self.aoi_layers.append(layer)
            self.iface.addCustomActionForLayer(self.remove_layer_action, layer)
        self.dlg.polygonCombo.setExceptedLayerList(self.filter_aoi_layers())
        self.dlg.polygonCombo.setLayer(layer)

    def remove_from_layers(self, layer=None):
        if not layer:
            layer = self.iface.layerTreeView().currentLayer()
        try:
            self.aoi_layers.remove(layer)
        except ValueError:
            pass
            # it can be easly already removed as I can't remove action from contextmenu of a single layer
        self.dlg.polygonCombo.setExceptedLayerList(self.filter_aoi_layers())

    def toggle_all_layers(self, state: bool):
        self.dlg.polygonCombo.setExceptedLayerList(self.filter_aoi_layers())
        self.settings.setValue('useAllVectorLayers', str(self.dlg.useAllVectorLayers.isChecked()))

    def refresh_status(self):
        self.http.get(
            url=f'{self.server}/user/status',
            callback=self.set_processing_limit,
            use_default_error_handler=False  # ignore errors to prevent repetitive alerts
        )

    def first_status_request(self):
        self.http.get(
            url=f'{self.server}/user/status',
            callback=self.set_processing_limit,
            callback_kwargs={'app_startup_request': True},
            use_default_error_handler=False
        )
        self.data_catalog_service.get_user_limit()
    
    def get_project_callback(self, response: QNetworkReply):
        self.current_project = MapflowProject.from_dict(json.loads(response.readAll().data()))
        if self.current_project:
            self.project_id = self.current_project.id
        self.setup_processings_table()
        self.get_project_sharing(self.current_project)
        self.setup_project_change_rights()
        self.settings.setValue("project_id", self.project_id)
        self.setup_workflow_defs(self.current_project.workflowDefs)
        # Manually toggle function to avoid race condition
        self.calculate_aoi_area_use_image_extent(self.dlg.useImageExtentAsAoi.isChecked())

    def setup_add_layer_menu(self):
        self.add_layer_menu.addAction(self.create_aoi_from_map_action)
        self.add_layer_menu.addAction(self.add_aoi_from_file_action)
        self.add_layer_menu.addAction(self.draw_aoi)

        self.create_aoi_from_map_action.triggered.connect(self.create_aoi_layer_from_map)
        self.add_aoi_from_file_action.triggered.connect(self.open_vector_file)
        self.draw_aoi.triggered.connect(self.create_editable_aoi_layer)
        self.dlg.addAoiButton.setMenu(self.add_layer_menu)

    def setup_options_menu_connections(self):
        self.dlg.save_result_action.triggered.connect(self.download_results_file)
        self.dlg.download_aoi_action.triggered.connect(self.download_aoi_file)
        self.dlg.see_details_action.triggered.connect(self.show_details)
        self.dlg.processing_update_action.triggered.connect(self.update_processing)
        self.dlg.saveOptionsButton.setMenu(self.dlg.options_menu)

    def create_aoi_layer_from_map(self, action: QAction):
        aoi_geometry = helpers.to_wgs84(
            QgsGeometry.fromRect(self.iface.mapCanvas().extent()),
            self.project.crs()
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

    def open_vector_file(self):
        """Open a file selection dialog for the user to select a vector file as AOI
        Is called by clicking the 'Open vector file menu' button in the main dialog.
        """
        dlg = QFileDialog(QApplication.activeWindow(), self.tr('Select vector file'))
        dlg.setFileMode(QFileDialog.ExistingFile)
        if dlg.exec():
            path = dlg.selectedFiles()[0]
            aoi_layer = QgsVectorLayer(path, os.path.splitext(os.path.basename(path))[0])
            aoi_layer.loadNamedStyle(os.path.join(self.plugin_dir, 'static', 'styles', 'aoi.qml'))
            if aoi_layer.isValid():
                self.result_loader.add_layer(aoi_layer)
                self.add_to_layers(aoi_layer)
                self.iface.setActiveLayer(aoi_layer)
                self.iface.zoomToActiveLayer()
            else:
                self.alert(self.tr(f'Your file is not valid vector data source!'))

    def filter_aoi_layers(self):
        if self.dlg.useAllVectorLayers.isChecked():
            # We exclude search metadata layers from AOI layers list because they are big, crowded
            # and lead to topology errors
            if self.search_provider:
                return [layer for layer in self.project.mapLayers().values()
                             if self.search_provider.name + ' metadata' == layer.name()]
            else:
                return []
        else:
            return [layer for layer in self.project.mapLayers().values() if layer not in self.aoi_layers]

    def on_options_change(self):
        wd_name = self.dlg.modelCombo.currentText()
        wd = self.workflow_defs.get(wd_name)
        if not wd:
            return
        enabled_blocks = self.dlg.enabled_blocks()
        self.dlg.show_wd_price(wd_price=wd.get_price(enable_blocks=enabled_blocks),
                               wd_description=wd.description,
                               display_price=self.billing_type == BillingType.credits)
        self.save_options_settings(wd, enabled_blocks)
        if self.billing_type == BillingType.credits:
            self.update_processing_cost()

    def on_model_change(self, index: Optional[int] = None) -> None:
        wd_name = self.dlg.modelCombo.currentText()
        wd = self.workflow_defs.get(wd_name)
        self.set_available_imagery_sources(wd_name)
        if not wd:
            return
        self.show_wd_options(wd)
        self.dlg.show_wd_price(wd_price=wd.get_price(enable_blocks=self.dlg.enabled_blocks()),
                               wd_description=wd.description,
                               display_price=self.billing_type == BillingType.credits)
        if self.billing_type == BillingType.credits:
            self.update_processing_cost()

    def show_wd_options(self, wd: WorkflowDef):
        self.dlg.clear_model_options()
        for block in wd.optional_blocks:
            self.dlg.add_model_option(block.displayName, checked=bool(self.settings.value(f"wd/{wd.id}/{block.name}", False)))
        # Other wigets are disabled before the appearence of these checkboxes, so we do it here separately after adding them
        self.dlg.enable_model_options(self.user_role.can_start_processing)

    def save_options_settings(self, wd: WorkflowDef, enabled_blocks: List[bool]):
        enabled_blocks_dict = wd.get_enabled_blocks(enabled_blocks)
        for block in enabled_blocks_dict:
            name = block["name"]
            enabled = block["enabled"]
            self.settings.setValue(f"wd/{wd.id}/{name}", enabled)

    def set_available_imagery_sources(self, wd: str) -> None:
        """Restrict the list of imagery sources according to the selected model."""
        if self.config.SENTINEL_WD_NAME_PATTERN in wd and self.providers != self.sentinel_providers:
            self.providers = self.sentinel_providers
        elif not self.providers == self.basemap_providers:
            self.providers = self.basemap_providers
        else:
            # Providers did not change
            return
        provider_names = [p.name for p in self.providers]
        self.dlg.set_raster_sources(provider_names=provider_names,
                                    default_provider_names=['Mapbox', '🌍 Mapbox Satellite'])

    def filter_metadata(self, *_, min_intersection=None, max_cloud_cover=None) -> None:
        """Filter out the metadata table and layer every time user changes a filter."""
        try:
            crs = self.metadata_layer.crs()
        except (RuntimeError, AttributeError):  # no metadata layer
            return
        if max_cloud_cover is None:
            max_cloud_cover = self.dlg.maxCloudCover.value()
        if min_intersection is None:
            min_intersection = self.dlg.minIntersection.value()
        from_ = self.dlg.metadataFrom.date().toString(Qt.ISODate)
        to = self.dlg.metadataTo.date().toString(Qt.ISODate)
        filter_ = (
            f"acquisitionDate >= '{from_}'"
            f" and acquisitionDate <= '{to}'"
            f' and (cloudCover is null or cloudCover <= {max_cloud_cover})'
        )
        aoi = helpers.from_wgs84(self.metadata_aoi, crs)
        if not aoi:
            if self.dlg.polygonCombo.currentLayer():
                geom = layer_utils.collect_geometry_from_layer(self.dlg.polygonCombo.currentLayer())
                aoi = helpers.from_wgs84(geom, crs)
        self.calculator.setEllipsoid(crs.ellipsoidAcronym())
        self.calculator.setSourceCrs(crs, self.project.transformContext())
        min_intersection_size = self.calculator.measureArea(aoi) * (min_intersection / 100)
        aoi = QgsGeometry.createGeometryEngine(aoi.constGet())
        aoi.prepareGeometry()
        # Get attributes
        if self.dlg.sourceCombo.currentText() == constants.SENTINEL_OPTION_NAME:
            id_column_index = self.config.SENTINEL_ID_COLUMN_INDEX
            datetime_column_index = self.config.SENTINEL_DATETIME_COLUMN_INDEX
            cloud_cover_column_index = self.config.SENTINEL_CLOUD_COLUMN_INDEX
        else:  # Maxar
            id_column_index = self.config.MAXAR_ID_COLUMN_INDEX
            datetime_column_index = self.config.MAXAR_DATETIME_COLUMN_INDEX
            cloud_cover_column_index = self.config.MAXAR_CLOUD_COLUMN_INDEX
        self.metadata_layer.setSubsetString('')  # clear any existing filters
        filtered_ids = []
        for feature in self.metadata_layer.getFeatures():
            area = self.calculator.measureArea(QgsGeometry(aoi.intersection(feature.geometry().constGet())))
            if area < min_intersection_size:
                filtered_ids.append(feature['id'])
        if filtered_ids:
            filter_ += f' and id not in (' + ', '.join((f"'{id_}'" for id_ in filtered_ids)) + ')'
        self.metadata_layer.setSubsetString(filter_)
        to = QDate.fromString(to, Qt.ISODate).addDays(1).toString(Qt.ISODate)
        # Show/hide table rows
        for row in range(self.dlg.metadataTable.rowCount()):
            id_ = self.dlg.metadataTable.item(row, id_column_index).data(Qt.DisplayRole)
            datetime_ = self.dlg.metadataTable.item(row, datetime_column_index).data(Qt.DisplayRole)
            cloud_cover = self.dlg.metadataTable.item(row, cloud_cover_column_index).data(Qt.DisplayRole)
            is_unfit = from_ > datetime_ or to < datetime_ or id_ in filtered_ids
            if cloud_cover is not None:  # may be undefined
                is_unfit = is_unfit or cloud_cover > max_cloud_cover
            self.dlg.metadataTable.setRowHidden(row, is_unfit)

    def set_up_login_dialog(self) -> MapflowLoginDialog:
        """Create a login dialog, set its title and signal-slot connections."""
        dlg_login = MapflowLoginDialog(self.main_window, self.use_oauth, self.settings.value("token", ""))
        dlg_login.setWindowTitle(helpers.generate_plugin_header(self.tr("Log in ") + self.plugin_name,
                                                                     self.config.MAPFLOW_ENV,
                                                                     None, None, None))
        dlg_login.logIn.clicked.connect(self.read_mapflow_token)
        dlg_login.useOauth.toggled.connect(self.set_auth_type)
        return dlg_login

    def set_auth_type(self, use_oauth: bool = False):
        self.use_oauth = use_oauth
        self.settings.setValue("use_oauth", str(use_oauth).lower())
        self.dlg_login.set_auth_type(use_oauth=use_oauth, token = self.settings.value('token', ""))

    def toggle_polygon_combos(self, use_image_extent: bool) -> None:
        """Disable polygon combos when Use image extent is checked.

        :param use_image_extent: Whether the corresponding checkbox is checked
        """
        self.dlg.polygonCombo.setEnabled(not use_image_extent)

    def on_provider_change(self) -> None:
        """Adjust max and current zoom, and update the metadata table when user selects another
        provider.

        :param index: The currently selected provider index
        """
        # This is done after area calculation, because there the provider list is updated?
        provider_index = self.dlg.providerIndex()
        provider = self.providers[provider_index]
        # Changes in search tab
        self.toggle_imagery_search(provider)
        # Changes in case provider is raster layer
        self.toggle_processing_checkboxes()
        # re-calculate AOI because it may change due to intersection of image/area
        polygon_layer = self.dlg.polygonCombo.currentLayer()
        if isinstance(provider, MyImageryProvider):
            my_imagery_tab = self.dlg.tabWidget.findChild(QWidget, "catalogTab") 
            self.dlg.tabWidget.setCurrentWidget(my_imagery_tab)
            self.calculate_aoi_area_catalog()
            self.create_processing_request()
        else:
            self.calculate_aoi_area_polygon_layer(polygon_layer)
        if provider.requires_image_id:
            imagery_search_tab = self.dlg.tabWidget.findChild(QWidget, "providersTab")
            self.dlg.tabWidget.setCurrentWidget(imagery_search_tab)
    
    def on_zoom_change(self):
        """ Set chosen zoom and update cost (if it depends on zoom for provider).
        """
        if self.dlg.zoomCombo.currentIndex() != 0:
            self.settings.setValue('zoom', str(self.dlg.zoomCombo.currentText())) 
        else:
            self.settings.setValue('zoom', None)
        self.update_processing_cost()

    def setup_workflow_defs(self, workflow_defs: List[WorkflowDef]):
        self.workflow_defs = {wd.name: wd for wd in workflow_defs}
        self.dlg.modelCombo.clear()
        # We skip SENTINEL WDs if sentinel is not enabled (normally, it should be not)
        # wds along with ids in the format: {'model_name': 'workflow_def_id'}
        self.dlg.modelCombo.addItems(name for name in self.workflow_defs
                                     if self.config.ENABLE_SENTINEL or self.config.SENTINEL_WD_NAME_PATTERN not in name)
        self.dlg.modelCombo.setCurrentText(self.config.DEFAULT_MODEL)
        self.on_model_change()

    def save_dialog_state(self):
        """Memorize dialog element sizes & positioning to allow user to customize the look."""
        # Save main dialog size & position
        self.settings.setValue('mainDialogState', self.dlg.saveGeometry())

    # ========== Projects ========== #

    def on_project_change(self):
        selected_id = self.dlg.selected_project_id()
        if selected_id is not None and selected_id == self.project_id and self.workflow_defs:
            # we look at workflow defs because if they are NOT initialized, it means that the project
            # is not initialized yet (at plugin's startup) and we still need to set it up
            # otherwise, if the WDs are set, we assume that the project hasn't changed and skip further setup
            return
        if selected_id is None:
            self.project_service.get_project("default", self.get_project_callback)
        else:
            self.project_service.get_project(selected_id, self.get_project_callback)

    def setup_project_change_rights(self):
        project_editable = True
        if not self.current_project:
            project_editable = False
            reason = self.tr("No project selected")
        elif self.current_project.isDefault:
            reason = self.tr("You can't remove or modify default project")
            project_editable = False
        elif not self.user_role.can_delete_rename_project:
            reason = self.tr('Not enough rights to delete or update shared project ({})').format(self.user_role.value)
        else:
            reason = ""
        self.dlg.enable_project_change(reason, project_editable and self.user_role.can_delete_rename_project)

    def create_project(self):
        dialog = CreateProjectDialog(self.dlg)
        dialog.accepted.connect(lambda: self.project_service.create_project(dialog.project()))
        dialog.setup()
        dialog.deleteLater()

    def update_project(self):
        dialog = UpdateProjectDialog(self.dlg)
        dialog.accepted.connect(lambda: self.project_service.update_project(self.current_project.id,
                                                                                              dialog.project()))
        dialog.setup(self.current_project)
        dialog.deleteLater()

    def delete_project(self):
        if self.alert(self.tr('Do you really want to remove project {}? '
                              'This action cannot be undone, all processings will be lost!').format(self.current_project.name),
                        icon=QMessageBox.Question):
            # Unload current project as we are deleting it
            to_delete = self.project_id
            self.project_id = None
            self.current_project = None
            self.project_service.delete_project(to_delete)

    # ========= Providers ============ #
    def remove_provider(self) -> None:
        """Delete a web tile provider from the list of registered providers.

        Is called by clicking the red minus button near the provider dropdown list.
        """
        provider_index = self.dlg.providerCombo.currentIndex()
        provider = self.providers[provider_index]
        if provider.is_default:
            # We want to protect built in providers!
            self.alert(self.tr("This provider is default and cannot be removed"),
                       icon=QMessageBox.Warning)
            return
        # Ask for confirmation
        elif self.alert(self.tr('Permanently remove {}?').format(provider.name),
                        icon=QMessageBox.Question):
            self.user_providers.remove(provider)
            self.update_providers()

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
            if new_provider.name in self.providers:
                self.alert(self.tr("Provider name must be unique. {name} already exists, "
                                   "select another or delete/edit existing").format(name=new_provider.name),
                           icon=QMessageBox.Warning)
                self.dlg_provider.show()
                return
            else:
                self.user_providers.append(new_provider)
                provider_index = len(self.providers)
        else:
            # we replace old provider with a new one
            # if self.dlg_provider.property('mode') == 'edit':  #
            provider_index = self.providers.index(old_provider)
            user_provider_index = self.user_providers.index(old_provider)
            if new_provider.name != old_provider.name and new_provider.name in self.providers:
                # we do not want user to replace another provider when editing this one
                self.alert(self.tr("Provider name must be unique. {name} already exists,"
                                   " select another or delete/edit existing").format(name=new_provider.name),
                           icon=QMessageBox.Warning)
                self.dlg_provider.show()
                return
            else:
                self.user_providers[user_provider_index] = new_provider

        self.update_providers()
        self.dlg.setProviderIndex(provider_index)

    def add_provider(self) -> None:
        self.dlg_provider.setup(None, self.tr("Add new provider"))

    def edit_provider(self) -> None:
        """Prepare and show the provider edit dialog.
        Is called by the corresponding button.
        """
        provider = self.providers[self.dlg.providerIndex()]
        if provider.is_default:
            self.alert(self.tr("This is a default provider, it cannot be edited"),
                       icon=QMessageBox.Warning)
        else:
            self.dlg_provider.setup(provider)

    def update_providers(self) -> None:
        """Update imagery & providers dropdown list after edit/add/remove
        It works both ways: if providers is specified, it updates the settings;
        otherwise loads providers list from settings
        """
        self.user_providers.to_settings(self.settings)
        self.dlg.providerCombo.addItems(provider.name for provider in self.providers)
        self.set_available_imagery_sources(self.dlg.modelCombo.currentText())

    def monitor_polygon_layer_feature_selection(self, layers: List[QgsMapLayer]) -> None:
        """Set up connection between feature selection in polygon layers and AOI area calculation.

        Since the plugin allows using a single feature withing a polygon layer as an AOI for processing,
        its area should then also be calculated and displayed in the UI, just as with a single-featured layer.
        For every polygon layer added to the project, this function sets up a signal-slot connection for
        monitoring its feature selection by passing the changes to calculate_aoi_area().

        :param layers: A list of layers of any type (all non-polygon layers will be skipped)
        """
        for layer in filter(layer_utils.is_polygon_layer, layers):
            layer.selectionChanged.connect(self.calculate_aoi_area_selection)
            layer.geometryChanged.connect(self.calculate_aoi_area_layer_edited)
            layer.featureAdded.connect(self.calculate_aoi_area_layer_edited)
            layer.featuresDeleted.connect(self.calculate_aoi_area_layer_edited)

    def toggle_processing_checkboxes(self) -> None:
        """Toggle 'Use image extent' depending on the item in the imagery combo box.

        :param raster_source: Provider name or None, depending on the signal, if one of the
            tile providers, otherwise the selected raster layer
        """
        provider = self.providers[self.dlg.providerIndex()]
        enabled = isinstance(provider, MyImageryProvider)
        self.dlg.useImageExtentAsAoi.setEnabled(enabled)
        self.dlg.useImageExtentAsAoi.setChecked(enabled)

    def toggle_imagery_search(self,
                              provider):
        """
        Get necessary attributes from config and send them to MainDialogo to setup Imagery Search tab
        """
        provider_changed = self.replace_search_provider(provider)
        if not provider_changed:
            return
        # No need to re-set imagery search if the provider is not set,
        # or if search provider did not change
        if isinstance(self.search_provider, SentinelProvider):
            columns = self.config.SENTINEL_ATTRIBUTES
            hidden_columns = (len(columns) - 1,)
            sort_by = self.config.SENTINEL_DATETIME_COLUMN_INDEX
            current_zoom = max_zoom = None
            image_id_tooltip = self.tr(
                'If you already know which {provider_name} image you want to process,\n'
                'simply paste its ID here. Otherwise, search suitable images in the catalog below.'
            ).format(provider_name=self.search_provider.name)
            image_id_placeholder = self.tr('e.g. S2B_OPER_MSI_L1C_TL_VGS4_20220209T091044_A025744_T36SXA_N04_00')
            geoms = None
        else:  # any non-sentinel provider: setup table as for ImagerySearch provider
            columns = self.config_search_columns.METADATA_TABLE_ATTRIBUTES
            hidden_columns = (len(columns) - 1,)
            sort_by = self.config.MAXAR_DATETIME_COLUMN_INDEX
            max_zoom = self.config.MAX_ZOOM
            current_zoom = int(self.settings.value('maxZoom', self.config.DEFAULT_ZOOM))
            image_id_tooltip = self.tr(
                'If you already know which {provider_name} image you want to process,\n'
                'simply paste its ID here. Otherwise, search suitable images in the catalog below.'
            ).format(provider_name=self.search_provider.name)
            image_id_placeholder = self.tr('e.g. a3b154c40cc74f3b934c0ffc9b34ecd1')

            # If we have searched with current provider previously, we want to restore the search results as it were
            # We store the results in a temp folder, separate file for each provider
            geoms = self.search_provider.load_search_layer(self.temp_dir)
            if geoms:
                self.display_metadata_geojson_layer(
                    os.path.join(self.temp_dir, self.search_provider.metadata_layer_name),
                    f"{self.search_provider.name} metadata")
            else:
                self.clear_metadata()

        # override max zoom for proxy maxar provider
        self.dlg.setup_imagery_search(provider=self.search_provider,
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
            self.settings.setValue('outputDir', path)
            self.setup_tempdir()
            self.data_catalog_service.temp_dir = self.temp_dir
            return path

    def check_if_output_directory_is_selected(self) -> bool:
        """Check if the user specified an existing output dir.

        Returns True if an existing directory is specified or a new directory has been selected, else False.
        """
        if os.path.exists(self.dlg.outputDirectory.text()) or self.select_output_directory():
            return True
        self.alert(self.tr('Please, specify an existing output directory'))
        return False

    @property
    def imagery_search_provider_index(self):
        for index, provider in enumerate(self.providers):
            if isinstance(provider, ImagerySearchProvider):
                return index
        return -1

    @property
    def imagery_search_provider(self):
        for provider in self.providers:
            if isinstance(provider, ImagerySearchProvider):
                return provider
        return None

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
        if provider != self.search_provider:
            self.search_provider = provider
            provider_changed = True
        return provider_changed

    def replace_search_provider_index(self):
        try:
            provider_supports_search = self.providers[self.dlg.providerIndex()].meta_url is not None
        except (NotImplementedError, AttributeError):
            provider_supports_search = False

        if not provider_supports_search:
            self.dlg.setProviderIndex(self.imagery_search_provider_index)

    def get_metadata(self, _: Optional[bool] = False, offset: Optional[int] = 0) -> None:
        """Metadata is image footprints with attributes like acquisition date or cloud cover."""
        # If current provider does not support search, we should select ImagerySearchProvider to be able to search
        self.replace_search_provider_index()

        self.dlg.metadataTable.clearContents()
        self.dlg.metadataTable.setRowCount(0)
        more_button = self.dlg.findChild(QPushButton, self.config.METADATA_MORE_BUTTON_OBJECT_NAME)
        if more_button:
            self.dlg.layoutMetadataTable.removeWidget(more_button)
            more_button.deleteLater()
        provider = self.providers[self.dlg.providerIndex()]
        # Check if the AOI is defined
        if self.aoi:
            aoi = self.aoi
        else:
            self.alert(self.tr('Please, select a valid area of interest'))
            return

        from_ = self.dlg.metadataFrom.date().toString(Qt.ISODate)
        to = self.dlg.metadataTo.date().toString(Qt.ISODate)

        from_time = self.dlg.metadataFrom.dateTime().toTimeSpec(Qt.UTC).toString(Qt.ISODate)
        to_time = self.dlg.metadataTo.dateTime().toTimeSpec(Qt.UTC).toString(Qt.ISODate)

        max_cloud_cover = self.dlg.maxCloudCover.value()
        min_intersection = self.dlg.minIntersection.value()

        hide_unavailable = self.dlg.hideUnavailableResults.isChecked()
        product_types = self.selected_search_product_types()

        if isinstance(provider, MaxarProvider):
            self.get_maxar_metadata(aoi=aoi,
                                    provider=provider,
                                    from_=from_,
                                    to=to,
                                    max_cloud_cover=max_cloud_cover,
                                    min_intersection=min_intersection)
        elif isinstance(provider, SentinelProvider):
            self.request_skywatch_metadata(aoi, from_, to, max_cloud_cover, min_intersection)
        else:
            self.request_mapflow_metadata(aoi=aoi,
                                          provider=provider,
                                          from_=from_time,
                                          to=to_time,
                                          offset=offset,
                                          hide_unavailable=hide_unavailable,
                                          product_types=product_types)
            # HEAD API does not work properly with intersection percent, so not sending it yet (filtering after)
            # max_cloud_cover=max_cloud_cover,
            # min_intersection=min_intersection)

    def clear_metadata(self):
        try:
            self.project.removeMapLayer(self.metadata_layer)
        except (AttributeError, RuntimeError):  # metadata layer has been deleted
            pass

        self.dlg.metadataTable.clearContents()
        self.dlg.metadataTable.setRowCount(0)
        #provider = self.providers[self.dlg.providerIndex()]
        self.search_provider.clear_saved_search(self.temp_dir)

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
                                 product_types: Optional[List[ProductType]] = None):
        if not self.check_if_output_directory_is_selected():
            return # only when outputDirectory is empty AND user closed selection dialog
        self.metadata_aoi = aoi
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
                                                    productTypes=product_types)
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
            self.project.removeMapLayer(self.metadata_layer)
        except (AttributeError, RuntimeError):  # metadata layer has been deleted
            pass
        self.metadata_layer = QgsVectorLayer(filename, layer_name, 'ogr')
        self.project.addMapLayer(self.metadata_layer)
        self.metadata_layer.loadNamedStyle(os.path.join(self.plugin_dir, 'static', 'styles', 'metadata.qml'))
        self.meta_layer_table_connection = self.metadata_layer.selectionChanged.connect(
            self.sync_layer_selection_with_table)
        self.search_footprints = {
            feature['local_index']: feature
            for feature in self.metadata_layer.getFeatures()
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
        try:
            filename = provider.save_search_layer(self.temp_dir, geoms)
        except:
            self.alert(self.tr("<b>Results could not be loaded </b><br>Please, make sure you chose the right output folder in the Settings tab \
                                and you have access rights to this folder"))
            return
        self.display_metadata_geojson_layer(filename, f"{provider.name} metadata")
        self.dlg.fill_metadata_table(geoms)

        if response_data.total > response_data.limit:
            self.search_page_offset = response_data.offset
            self.search_page_limit = response_data.limit
            quotient, remainder = divmod(response_data.total, response_data.limit)
            search_total_pages = quotient + (remainder > 0)            
            search_page_number = int(response_data.offset/response_data.limit) + 1
            self.dlg.enable_search_pages(True, search_page_number, search_total_pages)
            # Disable next arrow for the last page
            if search_page_number == search_total_pages:
                self.dlg.searchRightButton.setEnabled(False)
            else:
                self.dlg.searchRightButton.setEnabled(True)
            # Disable previous arrow for the first page
            if search_page_number == 1:
                self.dlg.searchLeftButton.setEnabled(False)
            else:
                self.dlg.searchLeftButton.setEnabled(True)
        else:
            self.dlg.enable_search_pages(False)

    def request_skywatch_metadata(
            self,
            aoi: QgsGeometry,
            from_: str,
            to: str,
            max_cloud_cover: int,
            min_intersection: int,
    ) -> None:
        """Sumbit a request to SkyWatch to get metadata."""
        self.metadata_aoi = aoi
        callback_kwargs = {'max_cloud_cover': max_cloud_cover, 'min_intersection': min_intersection}
        # Check if the AOI is too large
        self.calculator.setEllipsoid(helpers.WGS84_ELLIPSOID)
        self.calculator.setSourceCrs(helpers.WGS84, self.project.transformContext())
        aoi_bbox = aoi.boundingBox()
        aoi_bbox_geom = QgsGeometry.fromRect(aoi_bbox)
        # Check the area
        aoi_too_large_message = self.tr('Your area of interest is too large.')
        if self.calculator.measureArea(aoi_bbox_geom) > self.config.SKYWATCH_METADATA_MAX_AREA:
            self.alert(aoi_too_large_message)
            return
        # Check the side length
        x_min, x_max, y_min, y_max = (
            aoi_bbox.xMinimum(),
            aoi_bbox.xMaximum(),
            aoi_bbox.yMinimum(),
            aoi_bbox.yMaximum()
        )
        north_west = QgsPoint(x_min, y_max)
        width = QgsGeometry.fromPolyline((north_west, QgsPoint(x_max, y_max)))
        height = QgsGeometry.fromPolyline((north_west, QgsPoint(x_min, y_min)))
        if (
                self.calculator.measureLength(width) > self.config.SKYWATCH_METADATA_MAX_SIDE_LENGTH
                or self.calculator.measureLength(height) > self.config.SKYWATCH_METADATA_MAX_SIDE_LENGTH
        ):
            self.alert(aoi_too_large_message)
            return
        # Handle the multipolygon case
        if aoi.wkbType() == QgsWkbTypes.MultiPolygon:
            if len(aoi.asMultiPolygon()) == 1:
                aoi.convertToSingleType()
            else:  # use the BBOX of the parts
                aoi = aoi_bbox_geom
        url = self.server + '/meta/skywatch/id'
        headers = {}
        self.http.post(
            url=url,
            body=json.dumps({
                'location': json.loads(aoi.asJson()),
                'resolution': 'low',
                'coverage': min_intersection,
                'start_date': from_,
                'end_date': to,
                'order_by': ['-date']
            }).encode(),
            headers=headers,
            callback=self.request_skywatch_metadata_callback,
            callback_kwargs=callback_kwargs,
            error_handler=self.request_skywatch_metadata_error_handler,
            use_default_error_handler=False
        )
        self.dlg.getMetadata.setDown(True)
        self.dlg.getMetadata.blockSignals(True)

    def request_skywatch_metadata_callback(
            self,
            response: QNetworkReply,
            max_cloud_cover: int,
            min_intersection: int
    ):
        """Start polling SkyWatch for metadata upon a successful request submission

        :param response: The HTTP response.
        :param max_cloud_cover: Passed on to fetch_skywatch_metadata().
        """
        request_id = json.loads(response.readAll().data())['data']['id']
        self.sentinel_metadata_coords = {}
        # Delete previous search
        try:
            self.project.removeMapLayer(self.metadata_layer)
        except (AttributeError, RuntimeError):  # metadata layer has been deleted
            pass
        # Prepare a layer
        self.metadata_layer = QgsVectorLayer(
            'polygon?crs=epsg:4326&index=yes&' +
            '&'.join(f'field={name}:{type_}' for name, type_ in {
                'id': 'string',
                'preview': 'string',
                'cloudCover': 'int',
                'acquisitionDate': 'datetime'
            }.items()),
            constants.SENTINEL_OPTION_NAME + ' metadata',
            'memory'
        )
        self.metadata_layer.loadNamedStyle(os.path.join(self.plugin_dir, 'static', 'styles', 'metadata.qml'))
        self.meta_layer_table_connection = self.metadata_layer.selectionChanged.connect(
            self.sync_layer_selection_with_table)
        # Poll processings
        metadata_fetch_timer = QTimer(self.dlg)
        metadata_fetch_timer.setInterval(self.config.SKYWATCH_POLL_INTERVAL * 1000)
        metadata_fetch_timer.timeout.connect(
            lambda: self.fetch_skywatch_metadata(
                'mapflow' in response.request().url().authority(),
                request_id,
                max_cloud_cover,
                min_intersection,
                metadata_fetch_timer
            )
        )
        metadata_fetch_timer.start()

    def request_skywatch_metadata_error_handler(self, response: QNetworkReply) -> None:
        """Error handler for Sentinel metadata requests.

        :param response: The HTTP response.
        """
        self.dlg.getMetadata.blockSignals(False)
        self.dlg.getMetadata.setDown(False)
        error = response.error()
        if error == QNetworkReply.ContentAccessDenied:
            self.alert(self.tr('Please, check your credentials'))
        else:
            self.report_http_error(response, self.tr("We couldn't fetch Sentinel metadata"))

    def fetch_skywatch_metadata(
            self,
            is_proxied: bool,
            request_id: str,
            max_cloud_cover: int = None,
            min_intersection: int = None,
            timer: QTimer = None,
            start_index: int = 0
    ) -> None:
        """Check if the metadata is ready.

        :param request_id: The UUID of the submitted SkyWatch request.
        :param max_cloud_cover: All metadata with a higher cloud cover % will be discarded.
        """
        url = f'{self.server}/meta/skywatch/page?id={request_id}&cursor={start_index}'
        headers = {}
        self.http.get(
            url=url,
            headers=headers,
            callback=self.fetch_skywatch_metadata_callback,
            callback_kwargs={
                'max_cloud_cover': max_cloud_cover,
                'min_intersection': min_intersection,
                'request_id': request_id,
                'timer': timer,
            },
            error_handler=self.fetch_skywatch_metadata_error_handler,
            error_handler_kwargs={'timer': timer},
            use_default_error_handler=False
        )

    def fetch_skywatch_metadata_callback(
            self,
            response: QNetworkReply,
            request_id: str,
            max_cloud_cover: int = None,
            min_intersection: int = None,
            timer: QTimer = None,
    ):
        """Parse the returned metadata page and fill out the table and the layer."""
        is_proxied = 'mapflow' in response.request().url().authority()
        if response.attribute(QNetworkRequest.HttpStatusCodeAttribute) == 202:
            return  # not ready yet
        if timer:
            timer.stop()
        if min_intersection is None:
            min_intersection = self.dlg.minIntersection.value()
        if max_cloud_cover is None:
            max_cloud_cover = self.dlg.maxCloudCover.value()
        response = json.loads(response.readAll().data())
        metadata = {'type': 'FeatureCollection', 'features': []}
        for feature in response['data']:
            if round(feature['result_cloud_cover_percentage']) > max_cloud_cover:
                continue
            id_ = feature['product_name'].split('tiles')[-1].split('metadata')[0]
            formatted_feature = {
                'id': id_,
                'type': 'Feature',
                'geometry': feature['location'],
                'properties': {
                    'preview': feature['preview_uri'],
                    'cloudCover': round(feature['result_cloud_cover_percentage']),
                }
            }
            try:
                datetime_ = datetime.strptime(feature['start_time'], '%Y-%m-%dT%H:%M:%S.%f%z')
            except ValueError:  # non-standard time format (missing milliseconds)
                datetime_ = datetime.strptime(feature['start_time'], '%Y-%m-%dT%H:%M:%S%z')
            formatted_feature['properties']['acquisitionDate'] = datetime_.astimezone().strftime('%Y-%m-%d %H:%M')
            metadata['features'].append(formatted_feature)
        self.sentinel_metadata_coords.update({
            feature['id']: feature['geometry']['bbox']
            for feature in metadata['features']
        })
        # Create a temporary layer for the current page of metadata
        output_file_name = os.path.join(self.temp_dir, os.urandom(32).hex())
        with open(output_file_name, 'w') as file:
            json.dump(metadata, file)
        metadata_layer = QgsVectorLayer(output_file_name, '', 'ogr')
        # Add the new features to the displayed metadata layer
        self.metadata_layer.dataProvider().addFeatures(metadata_layer.getFeatures())
        if timer:  # first page
            self.result_loader.add_layer(self.metadata_layer)
        current_row_count = self.dlg.metadataTable.rowCount()
        self.dlg.metadataTable.setRowCount(current_row_count + metadata_layer.featureCount())
        self.dlg.metadataTable.setSortingEnabled(False)
        for row, feature in enumerate(metadata['features'], start=current_row_count):
            table_items = [QTableWidgetItem() for _ in range(len(self.config.SENTINEL_ATTRIBUTES))]
            table_items[0].setData(Qt.DisplayRole, feature['properties']['acquisitionDate'])
            table_items[1].setData(Qt.DisplayRole, round(feature['properties']['cloudCover']))
            table_items[2].setData(Qt.DisplayRole, feature['id'])
            table_items[3].setData(Qt.DisplayRole, feature['properties']['preview'])
            for col, table_item in enumerate(table_items):
                self.dlg.metadataTable.setItem(row, col, table_item)
        self.filter_metadata(min_intersection=min_intersection, max_cloud_cover=max_cloud_cover)
        self.dlg.metadataTable.setSortingEnabled(True)
        # Handle pagination
        try:
            next_page_start_index = response['pagination']['cursor']['next']
        except TypeError:  # {"data": [], "pagination": None}
            try:
                self.project.removeMapLayer(self.metadata_layer)
            except (AttributeError, RuntimeError):  # metadata layer has been deleted
                pass
            self.alert(
                self.tr('No images match your criteria. Try relaxing the filters.'),
                QMessageBox.Information
            )
            self.dlg.getMetadata.blockSignals(False)
            self.dlg.getMetadata.setDown(False)
            return
        if next_page_start_index is not None:
            # Create a 'More' button
            more_button = QPushButton(self.tr('More'))
            more_button.setObjectName(self.config.METADATA_MORE_BUTTON_OBJECT_NAME)
            self.dlg.layoutMetadataTable.addWidget(more_button)

            # Set the button to fetch more metadata on click

            def fetch_skywatch_metadata_next_page(**kwargs):
                self.fetch_skywatch_metadata(**kwargs)
                # more_button = self.dlg.findChild(QPushButton, config.METADATA_MORE_BUTTON_OBJECT_NAME)
                self.dlg.layoutMetadataTable.removeWidget(more_button)
                more_button.deleteLater()

            more_button.clicked.connect(
                lambda: fetch_skywatch_metadata_next_page(
                    is_proxied=is_proxied,
                    request_id=request_id,
                    start_index=next_page_start_index
                )
            )
        if timer:
            self.dlg.getMetadata.blockSignals(False)
            self.dlg.getMetadata.setDown(False)

    def fetch_skywatch_metadata_error_handler(self, response: QNetworkReply, timer: QTimer) -> None:
        """Error handler for Sentinel metadata requests.

        :param response: The HTTP response.
        """
        try:
            timer.stop()
            timer.deleteLater()
        except (RuntimeError, AttributeError):  # None or has been destroyed
            pass
        self.report_http_error(response, self.tr("We couldn't fetch Sentinel metadata"))

    def get_maxar_metadata(
            self,
            aoi: QgsGeometry,
            provider: UsersProvider,
            from_: str,
            to: str,
            max_cloud_cover: int,
            min_intersection: int
    ) -> None:
        """Get SecureWatch image metadata."""
        self.metadata_aoi = aoi
        callback_kwargs = {
            'provider': provider,
            'min_intersection': min_intersection,
            'max_cloud_cover': max_cloud_cover
        }
        byte_array = QByteArray(b'')
        stream = QTextStream(byte_array)
        elem = aoi.get().asGml3(QDomDocument(), precision=5, ns="http://www.opengis.net/gml")
        elem.save(stream, 0)  # 0 = no indentation (minimize request size)
        stream.seek(0)  # rewind to the start
        request_body = provider.meta_request(from_=from_,
                                             to=to,
                                             max_cloud_cover=max_cloud_cover / 100,
                                             geometry=stream.readAll())
        encoded_credentials = b64encode(':'.join((
            provider.credentials.login,
            provider.credentials.password
        )).encode())
        self.http.post(
            url=provider.meta_url,
            body=request_body,
            auth=f'Basic {encoded_credentials.decode()}'.encode(),
            callback=self.get_maxar_metadata_callback,
            callback_kwargs=callback_kwargs,
            use_default_error_handler=False,
            error_handler=self.get_maxar_metadata_error_handler
        )

    def get_maxar_metadata_callback(
            self,
            response: QNetworkReply,
            provider: UsersProvider,
            min_intersection: int,
            max_cloud_cover: int
    ) -> None:
        """Format, save and load Maxar metadata.

        :param response: The HTTP response.
        :param product: Maxar product whose metadata was requested.
        """
        self.dlg.metadataTable.clearContents()
        response_data = response.readAll().data()
        metadata = json.loads(response_data)
        if metadata['totalFeatures'] == 0:
            self.alert(
                self.tr('No images match your criteria. Try relaxing the filters.'),
                QMessageBox.Information
            )
            return
        # Format decimals and dates
        for feature in metadata['features']:
            # Parse, localize & format the datetime
            feature['properties']['acquisitionDate'] = datetime.strptime(
                feature['properties']['acquisitionDate'] + '+0000', '%Y-%m-%d %H:%M:%S%z'
            ).astimezone().strftime('%Y-%m-%d %H:%M')
            # Round values for display
            if feature['properties']['offNadirAngle']:
                feature['properties']['offNadirAngle'] = round(feature['properties']['offNadirAngle'])
            if feature['properties']['cloudCover']:
                feature['properties']['cloudCover'] = round(feature['properties']['cloudCover'] * 100)
        # Save metadata to file to return to previous search
        filename = provider.save_search_layer(self.temp_dir, metadata)
        self.display_metadata_geojson_layer(filename, f'{provider.name} metadata')
        # Memorize IDs and extents to be able to clip the user's AOI to image on processing creation
        self.dlg.fill_metadata_table(metadata)

    def get_maxar_metadata_error_handler(self, response: QNetworkReply) -> None:
        """Error handler for metadata requests.

        :param response: The HTTP response.
        """
        error = response.error()
        if error in [QNetworkReply.ContentAccessDenied]:  # , QNetworkReply.AuthenticationRequiredError):
            self.alert(self.tr('Please, check your Maxar credentials'))
        else:
            self.report_http_error(response,
                                   self.tr("We couldn't get metadata from Maxar, "
                                           "error {error}").format(
                                       error=response.attribute(QNetworkRequest.HttpStatusCodeAttribute)),
                                   error_message_parser=securewatch_message_parser)

    def sync_table_selection_with_image_id_and_layer(self) -> None:
        """
        Every time user selects a row in the metadata table, select the
        corresponding feature in the metadata layer and put the selected image's
        id into the "Image ID" field.
        """
        if self.dlg.sourceCombo.currentText() == constants.SENTINEL_OPTION_NAME:
            id_column_index = self.config.SENTINEL_ID_COLUMN_INDEX
            # sentinel is indexed by the image ID
            local_index_column = id_column_index
            key = 'id'
        else:
            id_column_index = self.config.MAXAR_ID_COLUMN_INDEX
            local_index_column = self.config.LOCAL_INDEX_COLUMN
            key = 'local_index'

        selected_cells = self.dlg.metadataTable.selectedItems()
        if not selected_cells:
            local_indices = []
        else:
            selected_rows = [cell.row() for cell in selected_cells]
            local_indices = [self.dlg.metadataTable.item(row, local_index_column).text() for row in selected_rows]
        try:
            self.metadata_layer.selectionChanged.disconnect(self.meta_layer_table_connection)
            # disconnect to prevent loop of signals
        except (RuntimeError, AttributeError):
            # metadata layer was removed or not initialized
            return
        self.replace_search_provider_index()

        try:
            self.metadata_layer.selectByExpression(f"{key} in {tuple(local_indices)}")
        except RuntimeError:  # layer has been deleted
            pass
        except Exception as e:
            self.meta_layer_table_connection = self.metadata_layer.selectionChanged.connect(
                self.sync_layer_selection_with_table)
            raise e
        self.calculate_aoi_area_polygon_layer(self.dlg.polygonCombo.currentLayer())
        self.meta_layer_table_connection = self.metadata_layer.selectionChanged.connect(
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
        key = 'id' if self.dlg.sourceCombo.currentText() == constants.SENTINEL_OPTION_NAME else 'local_index'
        id_column_index = self.config.SENTINEL_ID_COLUMN_INDEX \
            if self.dlg.sourceCombo.currentText() == constants.SENTINEL_OPTION_NAME \
            else self.config.LOCAL_INDEX_COLUMN

        self.dlg.metadataTable.itemSelectionChanged.disconnect(self.meta_table_layer_connection)

        try:
            if not selected_ids:
                self.dlg.metadataTable.clearSelection()
                return
            found_items = []
            for selected_id in selected_ids:
                selected_local_index = self.metadata_layer.getFeature(selected_id)[key]
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
        provider = self.providers[self.dlg.providerIndex()]

        if isinstance(provider, SentinelProvider):
            if not ((
                            helpers.SENTINEL_DATETIME_REGEX.search(image_id)
                            and helpers.SENTINEL_COORDINATE_REGEX.search(image_id)
                    ) or (helpers.SENTINEL_PRODUCT_NAME_REGEX.search(image_id)
                    )):
                self.alert(self.tr(
                    'A Sentinel image ID should look like '
                    'S2B_OPER_MSI_L1C_TL_VGS4_20220209T091044_A025744_T36SXA_N04_00 '
                    'or /36/S/XA/2022/02/09/0/'
                ))
                return
        elif isinstance(provider, MaxarProvider):
            if not helpers.UUID_REGEX.match(image_id):
                self.alert(self.tr('A Maxar image ID should look like a3b154c40cc74f3b934c0ffc9b34ecd1'))
                return
        items = self.dlg.metadataTable.findItems(image_id, Qt.MatchExactly)
        if not items:
            self.dlg.metadataTable.clearSelection()
            return
        #if items[0] not in self.dlg.metadataTable.selectedItems():
            #self.dlg.metadataTable.selectRow(items[0].row())
        # Redundant since imageId is temorary removed

    def get_aoi_area_polygon_layer(self, layer: Union[QgsVectorLayer, None]) -> None:
        if not layer or layer.featureCount() == 0:
            if not self.user_role.can_start_processing:
                reason = self.tr('Not enough rights to start processing in a shared project ({})').format(self.user_role.value)
            else:
                reason = self.tr('Set AOI to start processing')
            self.dlg.disable_processing_start(reason, clear_area=True)
            self.aoi = self.aoi_size = None
            return

        features = list(layer.getSelectedFeatures()) or list(layer.getFeatures())
        if QgsWkbTypes.flatType(layer.wkbType()) == QgsWkbTypes.Polygon:
            geoms_count = len(features)
        elif QgsWkbTypes.flatType(layer.wkbType()) == QgsWkbTypes.MultiPolygon:
            geoms_count = layer_utils.count_polygons_in_layer(features)
        else: # type of layer is not supported
            # (but it shouldn't be the case, because point and line layers will not appear in AOI-combo,
            # and collections are devided by QGIS into separate layers with different types)
            raise ValueError("Only polygon and multipolyon layers supported for this operation")
        if self.max_aois_per_processing >= geoms_count:
            if len(features) == 1:
                aoi = features[0].geometry()
            else:
                aoi = QgsGeometry.collectGeometry([feature.geometry() for feature in features])
            self.calculate_aoi_area(aoi, layer.crs())
            return aoi
        else:  # self.max_aois_per_processing < number of polygons (as features and as parts of multipolygons):
            if not self.user_role.can_start_processing:
                reason = self.tr('Not enough rights to start processing in a shared project ({})').format(self.user_role.value)
            else:
                reason = self.tr('AOI must contain not more than {} polygons').format(self.max_aois_per_processing)
            self.dlg.disable_processing_start(reason, clear_area=True)
            self.aoi = self.aoi_size = None

    def calculate_aoi_area_polygon_layer(self, layer: Union[QgsVectorLayer, None]) -> None:
        """Get the AOI size total when polygon another layer is chosen,
        current layer's selection is changed or the layer's features are modified.

        :param layer: The current polygon layer
        """
        if self.dlg.useImageExtentAsAoi.isChecked():  # GeoTIFF extent used; no difference
            return
        provider = self.providers[self.dlg.providerIndex()]
        if isinstance(provider, MyImageryProvider):
            self.calculate_aoi_area_catalog()
        else:
            self.get_aoi_area_polygon_layer(layer)

    def calculate_aoi_area_raster(self, layer: Optional[QgsRasterLayer]) -> None:
        """Get the AOI size when a new entry in the raster combo box is selected.

        :param layer: The current raster layer
        """
        provider = self.providers[self.dlg.providerIndex()]
        if layer:
            geometry = QgsGeometry.collectGeometry([QgsGeometry.fromRect(layer.extent())])
            self.calculate_aoi_area(geometry, layer.crs())
        elif isinstance(provider, MyImageryProvider):
            self.calculate_aoi_area_catalog()
        else:
            self.calculate_aoi_area_polygon_layer(self.dlg.polygonCombo.currentLayer())

    def calculate_aoi_area_use_image_extent(self, use_image_extent: bool) -> None:
        """Get the AOI size when the Use image extent checkbox is toggled.

        :param use_image_extent: The current state of the checkbox
        """
        provider = self.providers[self.dlg.providerIndex()]
        if isinstance(provider, MyImageryProvider):
            self.calculate_aoi_area_catalog()
        else:
            self.calculate_aoi_area_polygon_layer(self.dlg.polygonCombo.currentLayer())
    
    def calculate_aoi_area_catalog(self) -> None:
        """Get the AOI size when a new mosaic or image in 'My imagery' is selected.
        """
        provider = self.providers[self.dlg.providerIndex()]
        if isinstance(provider, MyImageryProvider):
            image = self.data_catalog_service.selected_image()
            mosaic = self.data_catalog_service.selected_mosaic()
            if self.dlg.useImageExtentAsAoi.isChecked():
                if image or mosaic:
                    if image:
                        aoi = QgsGeometry().fromWkt(image.footprint)
                    else:
                        aoi = QgsGeometry().fromWkt(mosaic.footprint)
                else:
                    self.dlg.disable_processing_start(reason=self.tr('Choose mosaic or image to start processing'),
                                                      clear_area=True)
                    aoi = self.aoi = self.aoi_size = None
            else:
                # Get polygon AOI to set self.aoi for intersection check later
                aoi_layer = self.get_aoi_area_polygon_layer(self.dlg.polygonCombo.currentLayer())
                if image or mosaic:
                    if image:
                        catalog_aoi = QgsGeometry().fromWkt(image.footprint)
                    else:
                        catalog_aoi = QgsGeometry().fromWkt(mosaic.footprint)
                    aoi = layer_utils.get_catalog_aoi(catalog_aoi=catalog_aoi,
                                                      selected_aoi=self.aoi,
                                                      use_image_extent_as_aoi=False)
                else:
                    aoi = aoi_layer
                if not self.aoi: # other error message is already shown
                    pass 
                elif not aoi: # error after intersection
                    self.dlg.disable_processing_start(reason=self.tr("Selected AOI does not intersect the selected imagery"),
                                                      clear_area=True)
                    return
            # Don't recalculate AOI if first selected mosaic/image didn't change
            selected_mosaics = self.dlg.mosaicTable.selectedIndexes()
            selected_images = self.dlg.imageTable.selectedIndexes()
            if len(selected_mosaics) > 1 and self.dlg.selected_mosaic_cell == selected_mosaics[0] \
            or len(selected_images) > 1 and self.dlg.selected_image_cell == selected_images[0]:
                return
            self.calculate_aoi_area(aoi, helpers.WGS84)
        else:
            self.calculate_aoi_area_polygon_layer(self.dlg.polygonCombo.currentLayer())
        # If different provider is chosen, set it to My imagery
        self.data_catalog_service.set_catalog_provider(self.providers)

    def calculate_aoi_area_selection(self, _: List[QgsFeature]) -> None:
        """Get the AOI size when the selection changed on a polygon layer.

        :param _: A list of currently selected features
        """
        layer = self.dlg.polygonCombo.currentLayer()
        if layer == self.iface.activeLayer():
            self.calculate_aoi_area_polygon_layer(layer)

    def calculate_aoi_area_layer_edited(self) -> None:
        """Get the AOI size when a feature is added or remove from a layer."""
        layer = self.sender()
        if layer == self.dlg.polygonCombo.currentLayer():
            self.calculate_aoi_area_polygon_layer(layer)

    def calculate_aoi_area(self, aoi: QgsGeometry, crs: QgsCoordinateReferenceSystem) -> None:
        """Display the AOI size in sq.km.
            This is the only place where self.aoi is changed! This is important because it is the place where we
            send request to update processing cost!
        :param aoi: the processing area.
        :param crs: the CRS of the processing area.
        """
        if crs != helpers.WGS84:
            aoi = helpers.to_wgs84(aoi, crs)

        self.aoi = aoi  # save for reuse in processing creation or metadata requests
        # fetch UI data
        provider_index = self.dlg.providerIndex()
        use_image_extent_as_aoi = self.dlg.useImageExtentAsAoi.isChecked()
        selected_images = self.dlg.metadataTable.selectedItems()
        if selected_images:
            rows = list(set(image.row() for image in selected_images))
            local_image_indices = [int(self.dlg.metadataTable.item(row, self.config.LOCAL_INDEX_COLUMN).text()) 
                                   for row in rows]
        else:
            local_image_indices = []
        # This is AOI with respect to selected Maxar images and raster image extent
        try:
            real_aoi = self.get_aoi(provider_index=provider_index,
                                    use_image_extent_as_aoi=use_image_extent_as_aoi,
                                    local_image_indices=local_image_indices,
                                    selected_aoi=self.aoi)
        except ImageIdRequired:
            # AOI is OK, but image ID is not selected,
            # in this case we should use selected AOI without cut by AOI
            real_aoi = self.aoi
        except Exception as e:
            # Could not calculate AOI size
            real_aoi = QgsGeometry()
        try:
            self.aoi_size = layer_utils.calculate_aoi_area(real_aoi, self.project.transformContext())
        except Exception as e:
            self.aoi_size = 0
        
        self.dlg.labelAoiArea.setText(self.tr('Area: {:.2f} sq.km').format(self.aoi_size))
        self.update_processing_cost()

    def update_processing_cost(self):
        if not self.aoi:
            # Here the button must already be disabled, and the warning text set
            if self.dlg.startProcessing.isEnabled():
                if not self.user_role.can_start_processing:
                    reason = self.tr('Not enough rights to start processing in a shared project ({})').format(self.user_role.value)
                else:
                    reason = self.tr("Set AOI to start processing")
                self.dlg.disable_processing_start(reason, clear_area=False)
        elif not self.workflow_defs:
            self.dlg.disable_processing_start(reason=self.tr("Error! Models are not initialized"),
                                              clear_area=True)
        elif self.billing_type != BillingType.credits:
            self.dlg.startProcessing.setEnabled(True)
            self.dlg.processingProblemsLabel.clear()
            request_body, error = self.create_processing_request(allow_empty_name=True)
        else:  # self.billing_type == BillingType.credits: f
            provider = self.providers[self.dlg.providerIndex()]
            request_body, error = self.create_processing_request(allow_empty_name=True)
            if not request_body:
                self.dlg.disable_processing_start(self.tr("Processing cost is not available:\n"
                                                          "{error}").format(error=error))
            elif isinstance(provider, ImagerySearchProvider) and\
                not self.dlg.metadataTable.selectionModel().hasSelection():
                    self.dlg.disable_processing_start(self.tr("This provider requires image ID. "
                                                              "Use search tab to find imagery for you requirements, "
                                                              "and select image in the table."))
            elif isinstance(provider, MyImageryProvider) and\
                not self.dlg.mosaicTable.selectionModel().hasSelection():
                    self.dlg.disable_processing_start(reason=self.tr('Choose mosaic or image to start processing'))
            else:
                if self.user_role.can_start_processing:
                    self.http.post(
                        url=f"{self.server}/processing/cost",
                        callback=self.calculate_processing_cost_callback,
                        body=request_body.as_json().encode(),
                        use_default_error_handler=False,
                        error_handler=self.clear_processing_cost
                    )

    def clear_processing_cost(self, response: QNetworkReply):
        """
        We do not display the result in case of error,
        the errors are also not displayed to not confuse the user.

        If the user tries to start the processing, he will see the errors
        """
        response_text = response.readAll().data().decode()
        if response_text is not None:
            message = api_message_parser(response_text)
            if not self.user_role.can_start_processing:
                reason = self.tr('Not enough rights to start processing in a shared project ({})').format(self.user_role.value)
            else:
                reason = self.tr('Processing cost is not available:\n{message}').format(message=message)
            self.dlg.disable_processing_start(reason, clear_area=False)

    def calculate_processing_cost_callback(self, response: QNetworkReply):
        response_data = response.readAll().data().decode()
        self.processing_cost = int(response_data)
        self.dlg.processingProblemsLabel.setPalette(self.dlg.default_palette)
        self.dlg.processingProblemsLabel.setText(self.tr("Processsing cost: {cost} credits").format(cost=response_data))
        self.dlg.startProcessing.setEnabled(True)

    def delete_processings(self) -> None:
        """Delete one or more processings from the server.

        Asks for confirmation in a pop-up dialog. Multiple processings can be selected.
        Is called by clicking the deleteProcessings ('Delete') button.
        """
        # Pause refreshing processings table to avoid conflicts
        self.processing_fetch_timer.stop()
        selected_ids = self.selected_processing_ids()
        # Ask for confirmation if there are selected rows
        if selected_ids and self.alert(
                self.tr('Delete selected processings?'), QMessageBox.Question
        ):
            for id_ in selected_ids:
                self.http.delete(
                    url=f'{self.server}/processings/{id_}',
                    callback=self.delete_processings_callback,
                    callback_kwargs={'id_': id_},
                    error_handler=self.delete_processings_error_handler
                )

    def delete_processings_callback(self, _: QNetworkReply, id_: str) -> None:
        """Delete processings from the table after they've been deleted from the server.

        :param id_: ID of the deleted processing.
        """
        row = self.dlg.processingsTable.findItems(id_, Qt.MatchExactly)[0].row()
        self.dlg.processingsTable.removeRow(row)
        self.processing_fetch_timer.start()

    def delete_processings_error_handler(self,
                                         response: QNetworkReply) -> None:
        """Error handler for processing deletion request.

        :param response: The HTTP response.
        """
        self.report_http_error(response, self.tr("Error deleting a processing"))

    def check_processing_ui(self, allow_empty_name=False):
        processing_name = self.dlg.processingName.text()

        if not processing_name and not allow_empty_name:
            raise ProcessingInputDataMissing(self.tr('Please, specify a name for your processing'))
        use_image_extent_as_aoi = self.dlg.useImageExtentAsAoi.isChecked()
        if not self.aoi:
            if use_image_extent_as_aoi:
                raise BadProcessingInput(self.tr('GeoTIFF is corrupted or has invalid projection'))
            elif self.dlg.polygonCombo.currentLayer():
                raise BadProcessingInput(self.tr('Processing area layer is corrupted or has invalid projection'))
            else:
                raise BadProcessingInput(self.tr('Please, select a valid area of interest'))
        if self.aoi_area_limit < self.aoi_size:
            raise BadProcessingInput(self.tr(
                'Up to {} sq km can be processed at a time. '
                'Try splitting your area(s) into several processings.').format(self.aoi_area_limit))

        return True

    def crop_aoi_with_maxar_image_footprint(self,
                                            aoi: QgsFeature,
                                            local_image_indices: List[int]):
        extents = [self.search_footprints[local_image_index] for local_image_index in local_image_indices]
        try:
            clipped_aoi_features = clip_aoi_to_image_extent(aoi, extents)
            aoi = QgsGeometry.fromWkt('GEOMETRYCOLLECTION()')
            for feature in clipped_aoi_features:
                geom = feature.geometry()
                aoi = aoi.combine(geom)
        except StopIteration:
            raise AoiNotIntersectsImage()
        return aoi

    def get_processing_params(self,
                              provider_index: Optional[int],
                              s3_uri: str = "",
                              zoom: Optional[str] = None,
                              image_id: Optional[str] = None,
                              provider_name: Optional[str] = None,
                              requires_id: Optional[bool] = False):
        provider = self.providers[provider_index]
        meta = {'source-app': 'qgis',
                'version': self.plugin_version,
                'source': provider.name.lower()}
        if not provider:
            raise PluginError(self.tr('Providers are not initialized'))
        provider_params, provider_meta = provider.to_processing_params(image_id=image_id,
                                                                       provider_name=provider_name,
                                                                       url=s3_uri,
                                                                       zoom=zoom,
                                                                       requires_id=requires_id)
        meta.update(**provider_meta)
        return provider_params, meta

    def get_aoi(self,
                provider_index: Optional[int],
                use_image_extent_as_aoi: bool,
                selected_aoi: QgsGeometry,
                local_image_indices: Optional[List[int]]) -> QgsGeometry:
        if not helpers.check_aoi(selected_aoi):
            raise BadProcessingInput(self.tr('Bad AOI. AOI must be inside boundaries:'
                                             ' \n[-180, 180] by longitude, [-90, 90] by latitude'))
        else:
            provider = self.providers[provider_index]
            if not provider:
                raise PluginError(self.tr('Providers are not initialized'))
            if len(local_image_indices) != 0:
                if isinstance(provider, (MaxarProvider, ImagerySearchProvider)):
                    aoi = self.crop_aoi_with_maxar_image_footprint(selected_aoi, local_image_indices)
                    if not aoi:
                        raise AoiNotIntersectsImage()
                elif isinstance(provider, SentinelProvider):
                    # todo: crop sentinel aoi with image footprint?
                    aoi = selected_aoi
                else:
                    aoi = selected_aoi
                    # We ignore image ID if the provider does not support it
                    # raise PluginError(self.tr("Selection is not available for  {}").format(provider.name))
            elif provider.requires_image_id:
                aoi = selected_aoi
                # raise PluginError(self.tr("Please select image in Search table for {}").format(provider.name))
            elif isinstance(provider, MyImageryProvider):
                image = self.data_catalog_service.selected_image()
                mosaic = self.data_catalog_service.selected_mosaic()
                if image:
                    catalog_aoi = QgsGeometry().fromWkt(image.footprint)
                elif mosaic:
                    catalog_aoi = QgsGeometry().fromWkt(mosaic.footprint)
                if image or mosaic:
                    aoi = layer_utils.get_catalog_aoi(catalog_aoi=catalog_aoi,
                                                      selected_aoi=selected_aoi,
                                                      use_image_extent_as_aoi=use_image_extent_as_aoi)
                    if not aoi:
                        raise AoiNotIntersectsImage()
                    aoi = selected_aoi
                else:
                    aoi = selected_aoi
            else:
                aoi = selected_aoi
        return aoi

    def create_processing_request(self,
                                  allow_empty_name: bool = False) -> Tuple[Optional[PostProcessingSchema], str]:
        processing_name = self.dlg.processingName.text()
        wd_name = self.dlg.modelCombo.currentText()
        wd = self.workflow_defs.get(wd_name)
        provider_index = self.dlg.providerIndex()
        provider = self.providers[provider_index]
        s3_uri = self.get_s3_uri(provider)

        selected_images = self.dlg.metadataTable.selectedItems()
        if selected_images:
            local_image_indices = self.get_local_image_indices(selected_images) 
            provider_names, product_types = self.get_search_providers(local_image_indices)
            image_id, requires_id, selection_error = self.get_search_images_ids(local_image_indices, provider_names, product_types)
            if selection_error:
                return None, selection_error
        else:
            local_image_indices = []
            provider_names, product_types = [], []
            image_id, requires_id, selection_error = None, False, ""
        provider_name = provider_names[0] if provider_names else None # the same for all [i] if there was no 'selection_error'

        zoom, zoom_error = self.get_zoom(provider, local_image_indices, product_types)
        if zoom_error:
            return None, zoom_error
        
        try:
            self.check_processing_ui(allow_empty_name=allow_empty_name)
            provider_params, processing_meta = self.get_processing_params(provider_index=provider_index,
                                                                          s3_uri=s3_uri,
                                                                          zoom=zoom,
                                                                          image_id=image_id,
                                                                          provider_name=provider_name,
                                                                          requires_id=requires_id)
            
            if self.zoom_selector:
                if isinstance(provider_params, PostSourceSchema): # no zoom for tifs
                    if provider_params.source_type == 'tif':
                        provider_params.zoom = None

            use_image_extent_as_aoi = self.dlg.useImageExtentAsAoi.isChecked()
            aoi = self.get_aoi(provider_index=provider_index,
                               use_image_extent_as_aoi=use_image_extent_as_aoi,
                               local_image_indices=local_image_indices,
                               selected_aoi=self.aoi)
        except AoiNotIntersectsImage:
            return None, self.tr("Selected AOI does not intersect the selected imagery")
        except ImageIdRequired:
            return None, self.tr("This provider requires image ID. Use search tab to find imagery for you requirements, "
                                 "and select image in the table.")
        except PluginError as e:
            return None, str(e)
        processing_params = PostProcessingSchema(
            name=processing_name,
            wdId=wd.id,
            blocks=wd.get_enabled_blocks(self.dlg.enabled_blocks()),
            meta=processing_meta,
            params=provider_params,
            geometry=json.loads(aoi.asJson()))
        return processing_params, ""

    def create_processing(self) -> None:
        """Create and start a processing on the server.

        Is called by clicking the 'Create processing' button.
        """
        # get the data from UI
        processing_params, error = self.create_processing_request()
        if not processing_params:
            self.alert(error, icon=QMessageBox.Warning)
            return
        if not helpers.check_processing_limit(billing_type=self.billing_type,
                                              remaining_limit=self.remaining_limit,
                                              remaining_credits=self.remaining_credits,
                                              aoi_size=self.aoi_size,
                                              processing_cost=self.processing_cost):
            self.alert(self.tr('Processing limit exceeded. '
                               'Visit "<a href=\"https://app.mapflow.ai/account/balance\">Mapflow</a>" '
                               'to top up your balance'),
                       icon=QMessageBox.Warning)
            return
        self.message_bar.pushInfo(self.plugin_name, self.tr('Starting the processing...'))
        try:
            self.dlg.startProcessing.setEnabled(False)
            self.post_processing(processing_params)
        except Exception as e:
            self.alert(self.tr("Could not launch processing! Error: {}.").format(str(e)))
        return

    def upload_tif_callback(self,
                            response: QNetworkReply,
                            processing_params: PostProcessingSchema) -> None:
        """Start processing upon a successful GeoTIFF upload.

        :param response: The HTTP response.
        :param processing_params: A dictionary with the processing parameters.
        """
        processing_params.params.url = json.loads(response.readAll().data())['url']
        self.post_processing(processing_params)

    def upload_tif_error_handler(self, response: QNetworkReply) -> None:
        """Error handler for GeoTIFF upload request, made for data-catalog API

        """
        self.report_http_error(response=response,
                               title=self.tr("We couldn't upload your GeoTIFF"),
                               error_message_parser=data_catalog_message_parser)

    def post_processing(self, request_body: PostProcessingSchema) -> None:
        """Submit a processing to Mapflow.

        :param request_body: Processing parameters.
        """
        if self.project_id != 'default':
            request_body.projectId = self.project_id
        self.http.post(
            url=f'{self.server}/processings',
            callback=self.post_processing_callback,
            callback_kwargs={'processing_name': request_body.name},
            error_handler=self.post_processing_error_handler,
            use_default_error_handler=False,
            body=request_body.as_json().encode()
        )

    def post_processing_callback(self, _: QNetworkReply, processing_name: str) -> None:
        """Display a success message and clear the processing name field."""
        self.alert(
            self.tr("Success! We'll notify you when the processing has finished."),
            QMessageBox.Information
        )
        if self.dlg.processingName.text() == processing_name:
            self.dlg.processingName.clear()
        self.processing_fetch_timer.start()  # start monitoring
        # Do an extra fetch immediately
        self.http.get(
            url=f'{self.server}/projects/{self.project_id}/processings',
            callback=self.get_processings_callback
        )
        self.dlg.startProcessing.setEnabled(True)

    def post_processing_error_handler(self, response: QNetworkReply) -> None:
        """Error handler for processing creation requests.

        :param response: The HTTP response.
        """
        error = response.error()
        response_body = response.readAll().data().decode()
        if error == QNetworkReply.ContentAccessDenied \
                and "data provider" in response_body.lower():
            self.alert(self.tr('The selected data provider is unavailable on your plan. \n '
                               'Upgrade your subscription to get access to the data. \n'
                               'See pricing at <a href=\"https://mapflow.ai/pricing\">mapflow.ai</a>'),
                       QMessageBox.Information)
            # provider ID is the last "word" in the message.
            # In this case, when "data provider" is in the message, there can't be index error
        else:
            error_summary, email_body = get_error_report_body(response=response,
                                                              response_body=response_body,
                                                              plugin_version=self.plugin_version,
                                                              error_message_parser=api_message_parser)
            ErrorMessageWidget(parent=QApplication.activeWindow(),
                               text= error_summary,
                               title=self.tr('Processing creation failed'),
                               email_body=email_body).show()
        self.dlg.startProcessing.setEnabled(True)

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
            self.billing_type = BillingType.none
        else:
            # get billing type, by default it is area
            self.billing_type = BillingType(response_data.get('billingType', 'AREA').upper())
        # get limits
        self.remaining_limit = int(response_data.get('remainingArea', 0)) / 1e6  # convert into sq.km
        self.remaining_credits = int(response_data.get('remainingCredits', 0))
        self.max_aois_per_processing = int(response_data.get("maxAoisPerProcessing",
                                                             self.config.MAX_AOIS_PER_PROCESSING))
        if self.billing_type == BillingType.credits:
            balance_str = self.tr("Your balance: {} credits").format(self.remaining_credits)
        elif self.billing_type == BillingType.area:  # area
            balance_str = self.tr('Remaining limit: {:.2f} sq.km').format(self.remaining_limit)
        else:  # BillingType.none
            balance_str = ''

        self.review_workflow_enabled = response_data.get('reviewWorkflowEnabled', False)
        self.dlg.balanceLabel.setText(balance_str)

        if app_startup_request:
            self.update_processing_cost()
            self.app_startup_user_update_timer.stop()
            self.dlg.setup_for_billing(self.billing_type)
            self.dlg.setup_for_review(self.review_workflow_enabled)
            self.dlg.modelCombo.activated.emit(self.dlg.modelCombo.currentIndex())
            self.setup_providers(response_data.get("dataProviders") or [])
            self.on_provider_change()

    def setup_providers(self, providers_data):
        self.default_providers = ProvidersList([ImagerySearchProvider(proxy=self.server)] +
                                               [MyImageryProvider()] +
                                               [DefaultProvider.from_response(ProviderReturnSchema.from_dict(data))
                                                for data in providers_data])
        self.set_available_imagery_sources(self.dlg.modelCombo.currentText())
        # We want to clear the data from previous lauunch to avoid confusion
        for provider in self.providers:
            provider.clear_saved_search(self.temp_dir)

    def preview_sentinel_callback(self, response: QNetworkReply, datetime_: str, image_id: str) -> None:
        """Save and open the preview image as a layer."""
        with open(self.temp_dir/os.urandom(32).hex(), mode='wb') as f:
            f.write(response.readAll().data())
        # Some previews aren't georef-ed
        preview = gdal.Open(f.name)
        try:
            image_metadata = self.sentinel_metadata_coords[image_id]
        except (AttributeError, KeyError):
            image_metadata = None
        if image_metadata and not preview.GetProjection():
            lon_wgs84, *_, lat_wgs84 = image_metadata
            utm_zone = int((180 + lon_wgs84) // 6 + 1)
            crs = QgsCoordinateReferenceSystem(f'epsg:32{6 if lat_wgs84 > 0 else 7}{utm_zone}')
            preview.SetProjection(crs.toWkt())
            nw = helpers.from_wgs84(QgsGeometry(QgsPoint(lon_wgs84, lat_wgs84)), crs).asPoint()
            preview.SetGeoTransform([
                nw.x(),  # north-west corner x (lon, in case of UTM)
                320,  # pixel horizontal resolution (m)
                0,  # x-axis rotation
                nw.y(),  # north-west corner y (lat, in case of UTM)
                0,  # y-axis rotation
                -320  # pixel vertical resolution (m)
            ])
            preview.FlushCache()
        layer = QgsRasterLayer(f.name, f'{constants.SENTINEL_OPTION_NAME} {datetime_}', 'gdal')
        # Set the no-data value if undefined
        layer_provider = layer.dataProvider()
        for band in range(1, layer.bandCount() + 1):  # bands are 1-based (!)
            if not layer_provider.sourceHasNoDataValue(band):
                layer_provider.setNoDataValue(band, 0)
        layer.renderer().setNodataColor(QColor(Qt.transparent))
        self.result_loader.add_layer(layer)

    def preview_sentinel_error_handler(self,
                                       response: QNetworkReply,
                                       guess_format=False,
                                       **kwargs) -> None:
        """Error handler for requesting a Sentinel preview from SkyWatch."""
        if guess_format:
            alternative_url = response.request().url().toDisplayString().replace('jp2', 'jpg')
            self.http.get(
                url=alternative_url,
                callback=self.preview_sentinel_callback,
                callback_kwargs=kwargs,
                error_handler=self.preview_sentinel_error_handler
            )
            return
        self.alert(self.tr("Sorry, we couldn't load the image"))
        self.report_http_error(response, self.tr('Error previewing Sentinel imagery'))

    def preview_catalog(self, image_id):
        feature = self.metadata_feature(image_id)
        if not feature:
            self.alert(self.tr("Preview is unavailable when metadata layer is removed"))
            return
        footprint = self.metadata_footprint(feature=feature)
        url = feature.attribute('previewUrl')
        preview_type = feature.attribute('previewType')
        self.iface.mapCanvas().zoomToSelected()
        self.iface.mapCanvas().refresh()
        if preview_type == PreviewType.png:
            self.preview_png(url, footprint, image_id)
        else:
            self.alert(self.tr("Only PNG preview type is supported"))

    def preview_png(self,
                    url: str,
                    footprint: QgsGeometry,
                    image_id: str = ""):
        self.http.get(url=url,
                      timeout=30,
                      auth='null'.encode(),
                      callback=self.display_png_preview_gcp,
                      use_default_error_handler=False,
                      error_handler=self.preview_png_error_handler,
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
        with open(self.temp_dir/os.urandom(32).hex(), mode='wb') as f:
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
        self.project.addMapLayer(layer)

    def display_png_preview_gcp(self,
                                response: QNetworkReply,
                                footprint: QgsGeometry,
                                crs: QgsCoordinateReferenceSystem = QgsCoordinateReferenceSystem("EPSG:3857"),
                                image_id: str = ""):
        """
        We take corner points of a polygon that represents image footprint
        and put their coordinates as GCPs (ground control points)
        """
        # Return a list of coordinate pairs
        corners = []
        footprint = footprint.asPolygon()
        if len(footprint[0]) != 5:
            self.message_bar.pushInfo(self.plugin_name, self.tr('Preview is unavailable'))
            return
        for point in range(4):
            pt = footprint[0][point]
            coords = (pt.x(), pt.y())
            corners.append(coords)
        # Get non-referenced raster and set its projection
        with open(self.temp_dir/os.urandom(32).hex(), mode='wb') as f:
            f.write(response.readAll().data())
        preview = gdal.Open(f.name)
        preview.SetProjection(crs.toWkt())
        # Specify (inter)cardinal directions
            # Right now it is implemented just by points order in a list
            # We assume that points go from NE in clockwise direcrtion
            # If we won't find a different and more accurate solution
            # I would suggest creating a dictionary, storing x and y coordinates as values
            # Then we can check min and max coords from bounding box
            # And scecify that the point that has the same x as xmin is SW, xmax - NE,
            # Same y as ymin - SE, ymax - NW
        # Assuming raster is n*m size, where n is width and m is height, we get:
            # NW is a 1 point in a list (clockwise) and 0,0 - in our image
            # NE - 2 and n,0
            # SW - 4 and 0,m
            # SE - 3 and n,m
        # Create a list of GCPS
        # Where each GCP is (x, y, z, pixel(n or width), line(m or height))
        gcp_list = [
        gdal.GCP(corners[0][0], corners[0][1], 0, 0, 0),
        gdal.GCP(corners[1][0], corners[1][1], 0, preview.RasterXSize-1, 0),
        gdal.GCP(corners[3][0], corners[3][1], 0, 0, preview.RasterYSize-1),
        gdal.GCP(corners[2][0], corners[2][1], 0, preview.RasterXSize-1, preview.RasterYSize-1)
        ]
        # Set control points, clear cache, add preview layer
        preview.SetGCPs(gcp_list, crs.toWkt())
        preview.FlushCache()
        layer = QgsRasterLayer(f.name, f"{image_id} preview", 'gdal')
        # If (for some reason) transparent band is not set automatically, but it exists, set it
        if layer.bandCount() == 4:
            if layer.renderer().alphaBand() != 4:
                layer.renderer().setAlphaBand(4)
        # Otherwise, for each band set "0" as No Data value
        else:
            for band in range(layer.bandCount()):
                layer.dataProvider().setNoDataValue(band, 0)
        self.project.addMapLayer(layer)

    def preview_png_error_handler(self, response: QNetworkReply):
        self.report_http_error(response, self.tr("Could not display preview"))

    def preview_sentinel(self, image_id):
        selected_cells = self.dlg.metadataTable.selectedItems()
        if selected_cells:
            datetime_ = selected_cells[self.config.SENTINEL_DATETIME_COLUMN_INDEX]
            url = self.dlg.metadataTable.item(datetime_.row(), self.config.SENTINEL_PREVIEW_COLUMN_INDEX).text()
            if not url:
                self.alert(self.tr("Sorry, there's no preview for this image"), QMessageBox.Information)
                return
            datetime_ = datetime_.text()
            guess_format = False
        elif image_id:
            datetime_ = helpers.SENTINEL_DATETIME_REGEX.search(image_id)
            if datetime_ and helpers.SENTINEL_COORDINATE_REGEX.search(image_id):
                url = f'https://preview.skywatch.com/esa/sentinel-2/{image_id}.jp2'
                datetime_ = datetime.strptime(datetime_.group(0), '%Y%m%dT%H%M%S') \
                    .astimezone().strftime('%Y-%m-%d %H:%M')
            else:
                self.alert(self.tr("We couldn't load a preview for this image"))
                return
            guess_format = True
        else:
            self.alert(self.tr('Please, select an image to preview'), QMessageBox.Information)
            return
        callback_kwargs = {'datetime_': datetime_, 'image_id': image_id}
        self.http.get(
            url=url,
            callback=self.preview_sentinel_callback,
            callback_kwargs=callback_kwargs,
            error_handler=self.preview_sentinel_error_handler,
            error_handler_kwargs={'guess_format': guess_format, **callback_kwargs}
        )
        return

    def maxar_layer_name(self, layer_name, image_id):
        row = self.dlg.metadataTable.currentRow()
        attrs = tuple(self.config_search_columns.METADATA_TABLE_ATTRIBUTES.values())
        try:
            layer_name = ' '.join((
                layer_name,
                self.dlg.metadataTable.item(row, attrs.index('acquisitionDate')).text(),
                self.dlg.metadataTable.item(row, attrs.index('productType')).text()
            ))
        except AttributeError:  # the table is empty
            layer_name = f'{layer_name} {image_id}'
        return layer_name

    def metadata_extent(self,
                        image_id=None,
                        feature=None,
                        crs: QgsCoordinateReferenceSystem = helpers.WEB_MERCATOR):
        if not feature:
            feature = self.metadata_feature(image_id)
        if not feature:
            return None
        return helpers.from_wgs84(feature.geometry(), crs).boundingBox()

    def metadata_footprint(self,
                           image_id=None,
                           feature=None,
                           crs: QgsCoordinateReferenceSystem = helpers.WEB_MERCATOR):
        if not feature:
            feature = self.metadata_feature(image_id)
        if not feature:
            return None
        return helpers.from_wgs84(feature.geometry(), crs)

    def metadata_feature(self, image_id):
        if not image_id:
            return None
        try:  # Get the image extent to set the correct extent on the raster layer
            return next(self.metadata_layer.getFeatures(f"id = '{image_id}'"))
        except (RuntimeError, AttributeError, StopIteration):  # layer doesn't exist or has been deleted, or empty
            return None

    def preview_xyz(self, provider, image_id):
        max_zoom = self.config.MAX_ZOOM
        layer_name = provider.name
        try:
            url = provider.preview_url(image_id=image_id)
        except ImageIdRequired as e:
            self.alert(self.tr("Provider {name} requires image id for preview!").format(name=provider.name),
                       QMessageBox.Warning)
            return
        except NotImplementedError as e:            
            self.alert(self.tr("Preview is unavailable for the provider {}. \nOSM layer will be added instead.").format(provider.name), QMessageBox.Information)
            # Add OSM instaed of preview, if it is unavailable (for Mapbox)
            osm = constants.OSM
            layer = QgsRasterLayer(osm, 'OpenStreetMap', 'wms')
            self.result_loader.add_preview_layer(preview_layer=layer, preview_dict=self.preview_dict)
            return
        except Exception as e:
            self.alert(str(e), QMessageBox.Warning)
            return         
        uri = layer_utils.generate_xyz_layer_definition(url,
                                                        provider.credentials.login,
                                                        provider.credentials.password,
                                                        max_zoom,
                                                        provider.source_type)
        layer = QgsRasterLayer(uri, layer_name, 'wms')
        layer.setCrs(QgsCoordinateReferenceSystem(provider.crs))
        if layer.isValid():
            if isinstance(provider, MaxarProvider) and image_id:
                layer_name = self.maxar_layer_name(layer_name, image_id)
                layer.setName(layer_name)
                extent = self.metadata_extent(image_id)
                if extent:
                    layer.setExtent(extent)
            self.result_loader.add_preview_layer(preview_layer=layer, preview_dict=self.preview_dict)            
        else:
            self.alert(self.tr("We couldn't load a preview for this image"))

    def preview(self) -> None:
        """Display raster tiles served over the Web."""
        selected_cells = self.dlg.metadataTable.selectedItems()
        if not selected_cells:
            image_id = None
        else:
            id_column_index = self.config.MAXAR_ID_COLUMN_INDEX
            image_id = self.dlg.metadataTable.item(selected_cells[0].row(), id_column_index).text()
        provider = self.providers[self.dlg.providerIndex()]
        if provider.requires_image_id and not image_id:
            self.alert(self.tr("This provider requires image ID!"), QMessageBox.Warning)
            return
        if isinstance(provider, SentinelProvider):
            self.preview_sentinel(image_id=image_id)
        elif isinstance(provider, ImagerySearchProvider):
            self.preview_catalog(image_id=image_id)
        else:  # XYZ providers
            self.preview_xyz(provider=provider, image_id=image_id)

    def preview_or_search(self, provider) -> None:
        provider_index = self.dlg.providerIndex()
        provider = self.providers[provider_index]
        if provider.requires_image_id:
            imagery_search_tab = self.dlg.tabWidget.findChild(QWidget, "providersTab")
            self.dlg.tabWidget.setCurrentWidget(imagery_search_tab)
        else:
            self.preview()

    def update_processing_current_rating(self) -> None:
        # reset labels:
        processing = self.selected_processing()
        if not processing:
            return
        pid = processing.id_
        p_name = processing.name

        self.dlg.set_processing_rating_labels(processing_name=p_name)
        self.http.get(
            url=f'{self.server}/processings/{pid}',
            callback=self.update_processing_current_rating_callback
        )

    def update_processing_current_rating_callback(self, response: QNetworkReply) -> None:
        response_data = json.loads(response.readAll().data())
        processing = Processing.from_response(response_data)
        p_name = response_data.get('name')
        rating_json = response_data.get('rating')
        if not rating_json:
            return
        rating = int(rating_json.get('rating'))
        feedback = rating_json.get('feedback')
        self.dlg.set_processing_rating_labels(processing_name=p_name,
                                              current_rating=rating,
                                              current_feedback=feedback)

    def selected_processing_ids(self, limit=None):
        # add unique selected rows
        selected_rows = list(set(index.row() for index in self.dlg.processingsTable.selectionModel().selectedIndexes()))
        if not selected_rows:
            return []
        pids = [self.dlg.processingsTable.item(row,
                                               self.config.PROCESSING_TABLE_ID_COLUMN_INDEX).text()
                for row in selected_rows[:limit]]
        return pids

    def selected_processings(self, limit=None) -> List[Processing]:
        pids = self.selected_processing_ids(limit=limit)
        # limit None will give full selection
        selected_processings = [p for p in filter(lambda p: p.id_ in pids, self.processings)]
        return selected_processings

    def selected_processing(self) -> Optional[Processing]:
        first = self.selected_processings(limit=1)
        if not first:
            return None
        return first[0]

    def submit_processing_rating(self) -> None:
        processing = self.selected_processing()
        if not processing:
            return
        pid = processing.id_
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
        processing = self.selected_processing()
        if not processing:
            return
        pid = processing.id_
        if not processing.status.is_ok:
            self.alert(self.tr('Only finished processings can be rated'))
            return
        elif not processing.review_status.is_in_review:
            self.alert(self.tr("Processing must be in `Review required` status"))
            return
        self.http.put(
            url=f'{self.server}/processings/{pid}/acceptation',
            callback=self.review_processing_callback
        )

    def review_processing_callback(self, response: QNetworkReply):
        # Clear successfully uploaded review
        self.review_dialog.reviewComment.setText("")
        self.processing_fetch_timer.start()
        self.http.get(url=f'{self.server}/projects/{self.project_id}/processings',
                      callback=self.get_processings_callback,
                      use_default_error_handler=False)

    def show_review_dialog(self):
        processing = self.selected_processing()
        if not processing:
            return
        if not processing.status.is_ok:
            self.alert(self.tr('Only finished processings can be rated'))
            return
        elif not processing.review_status.is_in_review:
            self.alert(self.tr("Processing must be in `Review required` status"))
            return
        self.review_dialog.setup(processing)
        self.review_dialog.show()

    def submit_review(self):
        body = {"comment": self.review_dialog.reviewComment.toPlainText(),
                "features": layer_utils.export_as_geojson(self.review_dialog.reviewLayerCombo.currentLayer())}
        self.http.put(
            url=f'{self.server}/processings/{self.review_dialog.processing.id_}/rejection',
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
                               self.tr("Only correctly finished processings (status OK) can be reviewed"))

    def enable_rating_submit(self, status_ok: bool) -> None:
        rating_selected = 5 >= self.dlg.ratingComboBox.currentIndex() > 0
        if not self.user_role.can_delete_rename_review_processing:
            reason = self.tr('Not enough rights to rate processing in a shared project ({})').format(self.user_role.value)
        elif not status_ok:
            if not self.selected_processing():
                reason = self.tr('Please select processing')
            else:
                reason = self.tr("Only correctly finished processings (status OK) can be rated")
        elif not rating_selected and self.user_role.can_delete_rename_review_processing:
            reason = self.tr("Please select rating to submit")
        else:
            reason = ""
        self.dlg.enable_rating(can_interact=(status_ok and self.user_role.can_delete_rename_review_processing),
                               can_send=rating_selected,
                               reason=reason)

    def enable_feedback(self) -> None:
        """
        By feedback we mean either rating (1-5 stars + message) for regular users
        or review for users which have review workflow enabled
        """
        processing = self.selected_processing()
        if not processing:
            if self.review_workflow_enabled:
                self.enable_review_submit(False)
            else:
                self.enable_rating_submit(False)
            return
        if self.review_workflow_enabled:
            self.enable_review_submit(processing.status.is_ok and processing.review_status.is_in_review)
        else:
            self.enable_rating_submit(processing.status.is_ok)

    # =================== Results management ==================== #
    def load_results(self):
        processing = self.selected_processing()
        if not processing:
            return
        if processing.id_ not in self.processing_history.finished:
            self.alert(self.tr("Only the results of correctly finished processing can be loaded"))
            return

        if self.dlg.viewAsTiles.isChecked():
            self.result_loader.load_result_tiles(processing=processing)
        elif self.dlg.viewAsLocal.isChecked():
            if not self.check_if_output_directory_is_selected():
                return
            self.result_loader.download_results(processing=processing)

    def download_results_file(self) -> None:
        """
        Download result and save directly to a geojson file
        It is the most reliable way to get results, applicable if everything else failed
        """
        processing = self.selected_processing()
        if not processing:
            return
        if processing.id_ not in self.processing_history.finished:
            self.alert(self.tr("Only the results of correctly finished processing can be loaded"))
            return
        self.result_loader.download_results_file(pid=processing.id_)

    def download_aoi_file(self) -> None:
        """
        Download area of interest and save to a geojson file
        """
        processing = self.selected_processing()
        if not processing:
            return
        self.result_loader.download_aoi_file(pid=processing.id_)

    def alert(self, message: str, icon: QMessageBox.Icon = QMessageBox.Critical, blocking=True) -> None:
        """Display a minimalistic modal dialog with some info or a question.

        :param message: A text to display
        :param icon: Info/Warning/Critical/Question
        :param blocking: Opened as modal - code below will only be executed when the alert is closed
        """
        box = QMessageBox(icon, self.plugin_name, message, parent=QApplication.activeWindow())
        box.setTextFormat(Qt.RichText)
        if icon == QMessageBox.Question:  # by default, only OK is added
            box.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        return box.exec() == QMessageBox.Ok if blocking else box.open()

    def get_processings_callback(self, response: QNetworkReply, caller=None) -> None:
        """Update the processing table and user limit.

        :param response: The HTTP response.
        """
        response_data = json.loads(response.readAll().data())
        processings = parse_processings_request(response_data)
        if response_data:
            current_project_id = response_data[0]['projectId']
        else:
            current_project_id = None
        if all(not p.status.is_in_progress
               and p.review_status.is_not_accepted
               for p in processings):
            # We do not re-fetch the processings, if nothing is going to change.
            # What can change from server-side: processing can finish if IN_PROGRESS
            # or review can be accepted if NOT_ACCEPTED.
            # Any other processings can change only from client-side
            self.processing_fetch_timer.stop()
        env = self.config.MAPFLOW_ENV
        processing_history = self.settings.value('processings')
        self.processing_history = ProcessingHistory.from_settings(
            processing_history.get(env, {})
            .get(self.username, {})
            .get(self.project_id, {}))
        # get updated processings (newly failed and newly finished) and updated user processing history
        failed_processings, finished_processings, self.processing_history = updated_processings(processings,
                                                                                                self.processing_history)

        # update processing limit of user
        self.update_processing_limit()
        self.alert_failed_processings(failed_processings)
        self.alert_finished_processings(finished_processings)
        self.update_processing_table(processings)
        self.processings = processings
        try:  # use try-except bc this will only error once
            processing_history[env][self.username][self.project_id] = self.processing_history.asdict()
        except KeyError:  # history for the current env hasn't been initialized yet
            try:
                processing_history[env][self.username] = {self.project_id: self.processing_history.asdict()}
            except KeyError:
                processing_history[env] = {self.username: {self.project_id: self.processing_history.asdict()}}
        self.settings.setValue('processings', processing_history)

    def alert_failed_processings(self, failed_processings):
        if not failed_processings:
            return
            # this means that some of processings have failed since last update and the limit must have been returned
        if len(failed_processings) == 1:
            proc = failed_processings[0]
            self.alert(
                proc.name +
                self.tr(' failed with error:\n') + proc.error_message(self.config.SHOW_RAW_ERROR),
                QMessageBox.Critical,
                blocking=False)
        elif 1 < len(failed_processings) < 10:
            # If there are more than one failed processing, we will not
            self.alert(self.tr('{} processings failed: \n {} \n '
                               'See tooltip over the processings table'
                               ' for error details').format(len(failed_processings),
                                                            '\n'.join((proc.name for proc in failed_processings))),
                       QMessageBox.Critical,
                       blocking=False)
        else:  # >= 10
            self.alert(self.tr(
                '{} processings failed: \n '
                'See tooltip over the processings table for error details').format(len(failed_processings)),
                       QMessageBox.Critical,
                       blocking=False)

    def alert_finished_processings(self, finished_processings):
        if not finished_processings:
            return
        if len(finished_processings) == 1:
            # Print error message from first failed processing
            proc = finished_processings[0]
            self.alert(
                proc.name +
                self.tr(' finished. Double-click it in the table to download the results.'),
                QMessageBox.Information,
                blocking=False  # don't repeat if user doesn't close the alert
            )
        elif 1 < len(finished_processings) < 10:
            # If there are more than one failed processing, we will not
            self.alert(self.tr(
                '{} processings finished: \n {} \n '
                'Double-click it in the table '
                'to download the results').format(len(finished_processings),
                                                  '\n'.join((proc.name for proc in finished_processings))),
                       QMessageBox.Information,
                       blocking=False)
        else:  # >= 10
            self.alert(self.tr(
                '{} processings finished. \n '
                'Double-click it in the table to download the results').format(len(finished_processings)),
                       QMessageBox.Information,
                       blocking=False)

    def update_processing_table(self, processings: List[Processing]):
        # UPDATE THE TABLE
        # Memorize the selection to restore it after table update
        selected_processings = self.selected_processing_ids()
        # Explicitly clear selection since resetting row count won't do it
        self.dlg.processingsTable.clearSelection()
        # Temporarily enable multi selection so that selectRow won't clear previous selection
        self.dlg.processingsTable.setSelectionMode(QAbstractItemView.MultiSelection)
        # Row insertion triggers sorting -> row indexes shift -> duplicate rows, so turn sorting off
        self.dlg.processingsTable.setSortingEnabled(False)
        self.dlg.processingsTable.setRowCount(len(processings))
        # Fill out the table
        for row, proc in enumerate(processings):
            processing_dict = proc.asdict()
            set_color = False
            if proc.status.is_ok and proc.review_expires:
                # setting color for close review
                set_color = True
                color = QColor(255, 220, 200)
            for col, attr in enumerate(self.config.PROCESSING_TABLE_COLUMNS):
                table_item = QTableWidgetItem()
                table_item.setData(Qt.DisplayRole, processing_dict[attr])
                if proc.status.is_failed:
                    table_item.setToolTip(proc.error_message(raw=self.config.SHOW_RAW_ERROR))
                elif proc.in_review_until:
                    table_item.setToolTip(self.tr("Please review or accept this processing until {}."
                                                  " Double click to add results"
                                                  " to the map").format(
                        proc.in_review_until.strftime('%Y-%m-%d %H:%M') if proc.in_review_until else ""))
                elif proc.status.is_ok:
                    table_item.setToolTip(self.tr("Double click to add results to the map."
                                                  ))
                if set_color:
                    table_item.setBackground(color)
                self.dlg.processingsTable.setItem(row, col, table_item)
            if proc.id_ in selected_processings:
                self.dlg.processingsTable.selectRow(row)
        self.dlg.processingsTable.setSortingEnabled(True)
        # Restore extended selection and filtering
        self.dlg.processingsTable.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.dlg.filter_processings_table(self.dlg.filterProcessings.text())

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
        self.project.readProject.connect(self.set_layer_group)
        self.dlg.processingsTable.sortByColumn(self.config.PROCESSING_TABLE_SORT_COLUMN_INDEX, Qt.DescendingOrder)

    def set_layer_group(self) -> None:
        """Setup a legend group where all layers created by the plugin will be added."""
        self.layer_group = self.layer_tree_root.findGroup(self.settings.value('layerGroup'))
        if self.layer_group:
            # If the group has been deleted, assume user wants to add layers to root, memorize it
            self.layer_group.destroyed.connect(lambda: setattr(self, 'add_layers_to_group', False))
            # Let user rename the group, memorize the new name
            self.layer_group.nameChanged.connect(lambda _, name: self.settings.setValue('layerGroup', name))

    def unload(self) -> None:
        """Remove the plugin icon & toolbar from QGIS GUI."""
        self.processing_fetch_timer.stop()
        self.processing_fetch_timer.deleteLater()
        self.user_status_update_timer.stop()
        self.iface.removeCustomActionForLayerType(self.add_layer_action)
        self.iface.removeCustomActionForLayerType(self.remove_layer_action)
        for dlg in self.dlg, self.dlg_login, self.dlg_provider:
            if dlg:
                dlg.close()
        del self.toolbar
        self.settings.setValue('metadataMinIntersection', self.dlg.minIntersection.value())
        self.settings.setValue('metadataMaxCloudCover', self.dlg.maxCloudCover.value())
        self.settings.setValue('metadataFrom', self.dlg.metadataFrom.date())
        self.settings.setValue('metadataTo', self.dlg.metadataTo.date())

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
        self.settings.setValue('token', token)
        # keep login/password from token
        try:
            self.username, self.password = b64decode(token).decode().split(':')
        except:
            self.username = self.password = ''
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
        self.settings.setValue('token', '')
        self.processing_fetch_timer.stop()
        self.user_status_update_timer.stop()
        self.logged_in = False
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
        service = 'Mapflow' if 'mapflow' in response.request().url().authority() else 'SecureWatch'
        parser = api_message_parser if 'mapflow' in response.request().url().authority() else securewatch_message_parser
        if error == QNetworkReply.AuthenticationRequiredError:  # invalid/empty credentials
            # Prevent deadlocks
            if self.logged_in:  # token re-issued during a plugin session
                self.logout()
            elif self.settings.value('token'):  # env changed w/out logging out (admin)
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
            if not self.user_role.can_delete_rename_project:
                self.report_http_error(response,
                                       self.tr("Not enough rights for this action\n"+
                                                "in a shared project '{project_name}' ({user_role})").format(project_name=self.current_project.name, 
                                                                                                            user_role=self.user_role.value),
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
                                                          plugin_version=self.plugin_version,
                                                          error_message_parser=error_message_parser)
        ErrorMessageWidget(parent=QApplication.activeWindow(),
                           text= error_summary,
                           title=title,
                           email_body=email_body).show()

    def setup_processings_table(self):
        table_item = QTableWidgetItem("Loading...")
        table_item.setToolTip('Fetching your processings from server, please wait')
        self.dlg.processingsTable.setRowCount(1)
        self.dlg.processingsTable.setItem(0, 0, table_item)
        for column in range(1, self.dlg.processingsTable.columnCount()):
            empty_item = QTableWidgetItem("")
            self.dlg.processingsTable.setItem(0, column, empty_item)
        # Fetch processings at startup and start the timer to keep fetching them afterwards
        self.http.get(url=f'{self.server}/projects/{self.project_id}/processings',
                      callback=self.get_processings_callback,
                      callback_kwargs={"caller": f"setup_table_{self.project_id}"},
                      use_default_error_handler=False)
        self.processing_fetch_timer.start()

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

        self.update_processing_limit()
        self.aoi_area_limit = userinfo['aoiAreaLimit'] * 1e-6
        # We have different behavior for admin as he has access to all processings
        self.is_admin = userinfo.get("role") == "ADMIN"

        self.dlg.restoreGeometry(self.settings.value('mainDialogState', b''))
        # Authenticate and keep user logged in
        self.logged_in = True
        self.dlg_login.close()

        # Get all projects & setup processings table (see callback)
        if self.is_admin:
            self.project_id = Config.PROJECT_ID
            self.setup_workflow_defs(default_project.workflowDefs)
            self.setup_processings_table()
        else:
            self.project_service.get_projects(current_project_id=self.project_id)
            self.data_catalog_service.get_mosaics()
        self.dlg.setup_for_billing(self.billing_type)
        self.dlg.show()
        self.user_status_update_timer.start()
        self.app_startup_user_update_timer.start()

    def update_projects(self):
        self.projects = {pr.id: pr for pr in self.project_service.projects}
        if not self.projects:
            self.alert(self.tr("No projects found! Contact us to resolve the issue"))
            return
        self.filter_projects(self.dlg.filterProject.text())

    def setup_projects_combo(self, projects: dict[str, MapflowProject]):
        if self.project_connection is not None:
            self.dlg.projectsCombo.currentIndexChanged.disconnect(self.project_connection)
            self.project_connection = None
        self.dlg.setup_project_combo(projects, self.project_id)
        self.on_project_change()
        self.project_connection = self.dlg.projectsCombo.currentIndexChanged.connect(self.on_project_change)

    def filter_projects(self, name_filter):
        if not name_filter:
            filtered_projects = self.projects
        else:
            filtered_projects = {pid: p for pid, p in self.projects.items() if name_filter.lower() in p.name.lower()}
        if self.project_id in self.projects \
                and self.project_id not in filtered_projects:
            # We maintain the current project in the combo even if it not found to prevent over-requesting
            # until it is changed explicitly
            filtered_projects.update({self.project_id: self.projects[self.project_id]})
        self.setup_projects_combo(filtered_projects)

    def check_plugin_version_callback(self, response: QNetworkReply) -> None:
        """Inspect the plugin version backend expects and show a warning if it is incompatible w/ the plugin.

        If the major version differs, we force the user to reinstall and exit the plugin
        If the minor/patch differs, we recommend the user to reinstall, and if do it only once for the version,
         so in case user dismisses the recommendation, w save the "last recommended version" in settings
         and do not show the reminder until the even newer version is released
        :param response: The HTTP response.
        """

        server_version = response.readAll().data().decode('utf-8')
        latest_reported_version = self.settings.value('latest_reported_version', self.plugin_version)

        force_upgrade, recommend_upgrade = helpers.check_version(local_version=self.plugin_version,
                                                                 server_version=server_version,
                                                                 latest_reported_version=latest_reported_version)
        if force_upgrade:
            self.alert(self.tr("You must upgrade your plugin version to continue work with Mapflow. \n"
                               "The server requires version {server_version}, your plugin is {local_version}\n"
                               "Go to Plugins -> Manage and Install Plugins -> Upgradable").format(
                server_version=server_version,
                local_version=self.plugin_version,
                icon=QMessageBox.Warning))
            self.version_ok = False
            self.dlg.close()

        elif recommend_upgrade:
            self.alert(self.tr("A new version of Mapflow plugin {server_version} is released \n"
                               "We recommend you to upgrade to get all the latest features\n"
                               "Go to Plugins -> Manage and Install Plugins -> Upgradable").format(
                server_version=server_version,
                local_version=self.plugin_version,
                icon=QMessageBox.Information))
            # saving the requested version to not bother the user next time, if he decides not to upgrade
            self.settings.setValue('latest_reported_version', server_version)
            self.version_ok = True
        else:
            # it is if the upgrade is not needed, we want to save it
            self.settings.setValue('latest_reported_version', server_version)
            self.version_ok = True

    def show_details(self):
        processing = self.selected_processing()
        if not processing:
            return
        message = self.tr("<b>Name</b>: {name}"
                          "<br><b>Status</b></br>: {status}"
                          "<br><b>Model</b></br>: {model}").format(name=processing.name,
                                                                   model=processing.workflow_def,
                                                                   status=processing.status.value)
        if processing.description:
            message += self.tr("<br><b>Description</b></br>: {description}").format(description=processing.description)
        if processing.blocks: 
            if any([block.enabled for block in processing.blocks]):
                message += self.tr("<br><b>Model options:</b></br>"
                                    " {options}").format(options=", ".join(block.name
                                                                      for block in processing.blocks
                                                                           if block.enabled))
            else:
                message += self.tr("<br><b>Model options:</b></br>" " No options selected")
                
        if processing.params.data_provider:
            message += self.tr("<br><b>Data provider</b></br>: {provider}").format(provider=processing.params.data_provider)
        elif (processing.params.source_type and processing.params.source_type.lower() in ("local", "tif", "tiff")) \
                or (processing.params.url and processing.params.url.startswith("s3://")):
            # case of user's raster file; we do not want to display internal file address
            message += self.tr("<br><b>Data source</b></br>: uploaded file")
        elif processing.params.url:
            message += self.tr("<br><b>Data source link</b></br> {url}").format(url=processing.params.url)

        if processing.errors:
            message += "<br><b>Errors</b>:</br>" + "<br></br>" + processing.error_message(raw=self.config.SHOW_RAW_ERROR)
        self.alert(message=message,
                   icon=QMessageBox.Information,
                   blocking=False)

    def update_processing(self):
        processing = self.selected_processing()
        if not processing:
            return
        dialog = UpdateProcessingDialog(self.dlg)
        dialog.accepted.connect(lambda: self.processing_service.update_processing(processing.id_,
                                                                                  dialog.processing()))
        dialog.setup(processing)
        dialog.deleteLater()

    def create_project(self):
        dialog = CreateProjectDialog(self.dlg)
        dialog.accepted.connect(lambda: self.project_service.create_project(dialog.project()))
        dialog.setup()
        dialog.deleteLater()

    def get_project_sharing(self, project):
        if not project:
            return
        if project.shareProject:
            # Get user role, if project is shared
            users = project.shareProject.users
            for user in users:
                if user.email == self.username:
                    self.user_role = UserRole(user.role)
            # Get project owner
            owners = project.shareProject.owners
            for owner in owners:
                if owner.email == self.username:
                    self.user_role = UserRole.owner
            project_owner = owners[0].email
            # Disable buttons
            self.dlg.enable_shared_project(self.user_role)
        # Specify new main window header
        self.dlg.setWindowTitle(helpers.generate_plugin_header(self.plugin_name,
                                                               env=self.config.MAPFLOW_ENV,
                                                               project_name=project.name,
                                                               user_role=self.user_role,
                                                               project_owner=project_owner))
        
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
            provider_names = [self.search_footprints[local_image_index].attribute("providerName")
                              for local_image_index in local_image_indices]
        except KeyError:
            provider_names = []
        try:
            product_types = [self.search_footprints[local_image_index].attribute("productType")
                             for local_image_index in local_image_indices]
        except KeyError:
            product_types = []
        return provider_names, product_types
    
    def get_search_images_ids(self, local_image_indices, provider_names, product_types):
        image_id = self.dlg.imageId.text()
        requires_id = False
        selection_error = ""
        try:
            if len(local_image_indices) == 1:
                if product_types[0] == "Mosaic":
                    image_id = None # remove image_id for mosaic providers
                else:
                    requires_id = True # require image_id for single images
            else:
                # When multiple images is selected, check if selected images have mosaic product type and the same provider
                if set(product_types) == set(["Mosaic"]) and len(set(provider_names)) == 1:
                    image_id = None
                # Forbid multiselection for regular images and for different mosaics
                else:
                    selection_error = self.tr("You can launch multiple image processing only if it has the same provider of mosaic type")
        except:
            return image_id, requires_id, selection_error
        return image_id, requires_id, selection_error
    
    def get_zoom(self, provider, local_image_indices, product_types):
        zoom = None
        zoom_error = ""
        if isinstance(provider, ImagerySearchProvider):
            if local_image_indices:
                try:
                    zooms = [self.search_footprints[local_image_index].attribute("zoom")
                            for local_image_index in local_image_indices]
                except KeyError:
                    zooms = []
                # Allow zooms only for mosaics
                if set(product_types) == set(["Mosaic"]):
                    # No specified zoom if NULL is returned or it's None
                    unique_zooms = set(filter(lambda x: (x is not None and x != QVariant()), zooms))
                    # Forbid multiselection for results with different zooms
                    if len(unique_zooms) > 1:
                        zoom_error = self.tr("Selected search results must have the same zoom level")
                    elif len(unique_zooms) == 1: # get unique zoom as a parameter
                        zoom = str(int(list(unique_zooms)[0]))
            self.dlg.enable_zoom_selector(False, zoom)
        elif isinstance(provider, MyImageryProvider):
            self.dlg.enable_zoom_selector(False, zoom)
        else:
            if self.zoom_selector:
                self.zoom = self.settings.value('zoom')
                zoom = self.zoom
            self.dlg.enable_zoom_selector(True, zoom)
        return zoom, zoom_error
    
    def get_s3_uri(self, provider):
        s3_uri = None
        if isinstance(provider, MyImageryProvider):
            image = self.data_catalog_service.selected_image()
            mosaic = self.data_catalog_service.selected_mosaic()
            if image:
                s3_uri = image.image_url
            elif mosaic:
                try:
                    image_uri = self.data_catalog_service.images[0].image_url
                    # to launch for the whole mosaic we need to use minio path without the filename
                    s3_uri = image_uri.rsplit('/',1)[0]+'/'
                except:
                    s3_uri = None
        return s3_uri
    
    def show_search_next_page(self):
        self.get_metadata(offset=self.search_page_offset + self.search_page_limit)

    def show_search_previous_page(self):
        self.get_metadata(offset=self.search_page_offset - self.search_page_limit)
    
    def selected_search_product_types(self):
        product_types = []
        if self.dlg.searchMosaicCheckBox.isChecked():
            product_types.append(ProductType.mosaic.upper())
        if self.dlg.searchImageCheckBox.isChecked():
            product_types.append(ProductType.image.upper())
        if len(product_types) == 0:
            product_types = [ProductType.mosaic.upper(), ProductType.image.upper()]
        return product_types

    def setup_tempdir(self):
        if not self.settings.value('outputDir'):
            return # don't ask to specify tempdir at the plugin start
        self.temp_dir = Path(self.settings.value('outputDir'), "Temp")
        try:
            shutil.rmtree(self.temp_dir) # remove old tempdir
        except:
            pass
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    @property
    def basemap_providers(self):
        return ProvidersList(self.default_providers + self.user_providers)

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

        if self.logged_in:
            # with any auth method
            self.dlg.show()
            self.dlg.raise_()
            self.update_processing_limit()
            self.user_status_update_timer.start()
            return

        token = self.settings.value('token')
        if not self.use_oauth and token:
            # Saved token for basic auth
            self.login_basic(token)
        else:
            self.dlg_login.show()
