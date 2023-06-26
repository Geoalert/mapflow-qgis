import json
from pathlib import Path
import os.path
import tempfile
from base64 import b64encode, b64decode
from typing import List, Optional, Union, Callable, Tuple
from datetime import datetime  # processing creation datetime formatting
from configparser import ConfigParser  # parse metadata.txt -> QGIS version check (compatibility)

from osgeo import gdal
from PyQt5.QtXml import QDomDocument
from PyQt5.QtGui import QColor
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest, QHttpMultiPart, QHttpPart
from PyQt5.QtCore import (
    QDate, QObject, QCoreApplication, QTimer, QTranslator, Qt, QFile, QIODevice, QTextStream, QByteArray
)
from PyQt5.QtWidgets import (
    QApplication, QMessageBox, QFileDialog, QPushButton, QTableWidgetItem, QAction,
    QAbstractItemView, QLabel, QProgressBar, QMenu
)

from qgis.gui import QgsMessageBarItem
from qgis.core import (
    QgsProject, QgsSettings, QgsMapLayer, QgsVectorLayer, QgsRasterLayer, QgsFeature, Qgis,
    QgsCoordinateReferenceSystem, QgsDistanceArea, QgsGeometry, QgsVectorFileWriter,
    QgsWkbTypes, QgsPoint, QgsMapLayerType
)

from .functional import layer_utils, helpers
from .dialogs import MainDialog, LoginDialog, ErrorMessageWidget, ProviderDialog
from .dialogs.icons import plugin_icon
from .http import (Http,
                   get_error_report_body,
                   data_catalog_message_parser,
                   securewatch_message_parser,
                   api_message_parser)
from .config import Config
from .entity.processing import parse_processings_request, Processing, ProcessingHistory, updated_processings
from .entity.provider import (Provider,
                              MaxarProvider,
                              MaxarProxyProvider,
                              ProvidersDict,
                              SentinelProvider,
                              create_provider)
from .entity.billing import BillingType
from .entity.workflow_def import WorkflowDef
from .entity.processing_params import ProcessingParams, PostProcessingSchema
from .errors import ProcessingInputDataMissing, BadProcessingInput, PluginError, ImageIdRequired, AoiNotIntersectsImage
from .functional.geometry import clip_aoi_to_image_extent
from . import constants


class Mapflow(QObject):
    """This class represents the plugin. It is instantiated by QGIS."""

    def __init__(self, iface) -> None:
        """Initialize the plugin.

        :param iface: an instance of the QGIS interface.
        """
        # init configs
        self.maxar_metadata_footprints = dict()
        self.config = Config()
        # init empty params
        self.max_aois_per_processing = self.config.MAX_AOIS_PER_PROCESSING
        self.aoi_size = None
        self.aoi = None
        self.is_premium_user = False
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
        self.dlg_login = LoginDialog(self.main_window)
        self.workflow_defs = {}

        super().__init__(self.main_window)
        self.project = QgsProject.instance()
        self.message_bar = self.iface.messageBar()
        self.plugin_dir = os.path.dirname(__file__)
        self.temp_dir = tempfile.gettempdir()
        self.plugin_name = self.config.PLUGIN_NAME  # aliased here to be overloaded in submodules
        # Settings will be used to store credentials and various UI customizations
        self.settings = QgsSettings()
        # Get the server environment to connect to (for admins)
        self.server = self.config.SERVER
        # By default, plugin adds layers to a group unless user explicitly deletes it
        self.add_layers_to_group = True
        self.layer_tree_root = self.project.layerTreeRoot()
        # Set up authentication flags
        self.logged_in = False
        # Store user's current processing
        self.processing_history = ProcessingHistory.from_settings(
            self.settings.value('processings', {}).get(self.config.MAPFLOW_ENV, {}).get(self.username, {}))
        self.processings = []
        # Init toolbar and toolbar buttons
        self.toolbar = self.iface.addToolBar(self.plugin_name)
        self.toolbar.setObjectName(self.plugin_name)
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

        # Init dialogs
        self.dlg = MainDialog(self.main_window)
        self.set_up_login_dialog()
        self.dlg_provider = ProviderDialog(self.dlg)
        self.dlg_provider.accepted.connect(self.edit_provider_callback)
        # Display the plugin's version
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
        self.dlg.maxZoom.setValue(int(self.settings.value('maxZoom') or self.config.DEFAULT_ZOOM))

        # load providers from settings
        errors = []
        try:
            self.providers, errors = ProvidersDict.from_settings(settings=self.settings, server=self.config.SERVER)
        except Exception as e:
            self.alert(self.tr("Error during loading the data providers: {e}").format(str(e)), icon=Qgis.Warning)
        if errors:
            self.alert(
                self.tr('We failed to import providers {errors} from the settings. Please add them again').format(
                    errors), icon=Qgis.Warning)
        self.update_providers()
        self.dlg.rasterCombo.setCurrentText('Mapbox')  # otherwise SW will be set due to combo sync
        self.dlg.minIntersection.setValue(int(self.settings.value('metadataMinIntersection', 0)))
        self.dlg.maxCloudCover.setValue(int(self.settings.value('metadataMaxCloudCover', 100)))
        # Set default metadata dates
        today = QDate.currentDate()
        self.dlg.metadataFrom.setDate(self.settings.value('metadataFrom', today.addMonths(-6)))
        self.dlg.metadataTo.setDate(self.settings.value('metadataTo', today))
        # Hide the ID columns as only needed for table operations, not the user
        self.dlg.processingsTable.setColumnHidden(self.config.PROCESSING_TABLE_ID_COLUMN_INDEX, True)
        # SET UP SIGNALS & SLOTS
        self.filter_bad_rasters()
        self.dlg.modelCombo.activated.connect(self.on_model_change)
        # Memorize dialog element sizes & positioning
        self.dlg.finished.connect(self.save_dialog_state)
        # Connect buttons
        self.dlg.logoutButton.clicked.connect(self.logout)
        self.dlg.selectOutputDirectory.clicked.connect(self.select_output_directory)
        self.dlg.downloadResultsButton.clicked.connect(self.download_results)
        # (Dis)allow the user to use raster extent as AOI
        self.dlg.useImageExtentAsAoi.toggled.connect(self.toggle_polygon_combos)
        self.dlg.startProcessing.clicked.connect(self.create_processing)
        # Calculate AOI size
        self.dlg.polygonCombo.layerChanged.connect(self.calculate_aoi_area_polygon_layer)
        self.dlg.useImageExtentAsAoi.toggled.connect(self.calculate_aoi_area_use_image_extent)
        self.monitor_polygon_layer_feature_selection([
            self.project.mapLayer(layer_id) for layer_id in self.project.mapLayers(validOnly=True)
        ])
        self.project.layersAdded.connect(self.monitor_polygon_layer_feature_selection)
        self.project.layersAdded.connect(self.filter_bad_rasters)
        # Processings
        self.dlg.processingsTable.cellDoubleClicked.connect(self.download_results)
        self.dlg.deleteProcessings.clicked.connect(self.delete_processings)
        # Processings ratings
        self.dlg.processingsTable.cellClicked.connect(self.update_processing_current_rating)
        self.dlg.processingsTable.cellClicked.connect(self.enable_feedback)
        self.dlg.ratingSubmitButton.clicked.connect(self.submit_processing_rating)
        self.dlg.enable_rating(False, False)  # by default disabled
        self.dlg.enable_review(False, False)
        # connect radio buttons signals
        self.dlg.ratingComboBox.activated.connect(self.enable_feedback)
        self.dlg.processingRatingFeedbackText.textChanged.connect(self.enable_feedback)
        # Providers
        self.dlg.minIntersectionSpinBox.valueChanged.connect(self.filter_metadata)
        self.dlg.maxCloudCoverSpinBox.valueChanged.connect(self.filter_metadata)
        self.dlg.metadataFrom.dateChanged.connect(self.filter_metadata)
        self.dlg.metadataTo.dateChanged.connect(self.filter_metadata)
        self.dlg.preview.clicked.connect(self.preview)
        self.dlg.addProvider.clicked.connect(self.add_provider)
        self.dlg.editProvider.clicked.connect(self.edit_provider)
        self.dlg.removeProvider.clicked.connect(self.remove_provider)
        self.dlg.maxZoom.valueChanged.connect(lambda value: self.settings.setValue('maxZoom', value))
        # Maxar
        self.dlg.imageId.textChanged.connect(self.sync_image_id_with_table_and_layer)
        self.dlg.imageId.textChanged.connect(self.update_processing_cost)
        self.dlg.metadataTable.itemSelectionChanged.connect(self.sync_table_selection_with_image_id_and_layer)
        self.dlg.getMetadata.clicked.connect(self.get_metadata)
        self.dlg.metadataTable.cellDoubleClicked.connect(self.preview)
        self.dlg.rasterCombo.currentIndexChanged.connect(self.on_provider_change)
        # Poll processings
        self.processing_fetch_timer = QTimer(self.dlg)
        self.processing_fetch_timer.setInterval(self.config.PROCESSING_TABLE_REFRESH_INTERVAL * 1000)
        self.processing_fetch_timer.timeout.connect(
            lambda: self.http.get(
                url=f'{self.server}/projects/{self.config.PROJECT_ID}/processings',
                callback=self.get_processings_callback,
                use_default_error_handler=False  # ignore errors to prevent repetitive alerts
            )
        )
        # Poll user status to get limits
        self.user_status_update_timer = QTimer(self.dlg)
        self.user_status_update_timer.setInterval(self.config.USER_STATUS_UPDATE_INTERVAL * 1000)
        self.user_status_update_timer.timeout.connect(
            lambda: self.http.get(
                url=f'{self.server}/user/status',
                callback=self.set_processing_limit,
                use_default_error_handler=False  # ignore errors to prevent repetitive alerts
            )
        )
        # timer for user update at startup, in case get_processings request takes too long
        # stopped as soon as first /user/status request is made
        self.app_startup_user_update_timer = QTimer(self.dlg)
        self.app_startup_user_update_timer.setInterval(500)
        self.app_startup_user_update_timer.timeout.connect(
            lambda: self.http.get(
                url=f'{self.server}/user/status',
                callback=self.set_processing_limit,
                callback_kwargs={'app_startup_request': True},
                use_default_error_handler=False
            )
        )
        # Add layer menu
        self.add_layer_menu = QMenu()
        self.create_aoi_from_map_action = QAction(self.tr("Create new AOI layer from map extent"))
        self.add_aoi_from_file_action = QAction(self.tr("Add AOI from vector file"))
        self.aoi_layer_counter = 0
        self.setup_add_layer_menu()

    def setup_add_layer_menu(self):
        self.add_layer_menu.addAction(self.create_aoi_from_map_action)
        self.add_layer_menu.addAction(self.add_aoi_from_file_action)

        self.create_aoi_from_map_action.triggered.connect(self.create_aoi_layer_from_map)
        self.add_aoi_from_file_action.triggered.connect(self.open_vector_file)
        self.dlg.toolButton.setMenu(self.add_layer_menu)

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
        self.add_layer(aoi_layer)
        self.iface.setActiveLayer(aoi_layer)
        self.dlg.polygonCombo.setLayer(aoi_layer)

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
                self.add_layer(aoi_layer)
                self.iface.setActiveLayer(aoi_layer)
                self.iface.zoomToActiveLayer()
                self.dlg.polygonCombo.setLayer(aoi_layer)
            else:
                self.alert(self.tr(f'Your file is not valid vector data source!'))

    def filter_bad_rasters(self, changed_layers: Optional[List[QgsRasterLayer]] = None) -> None:
        """Leave only GeoTIFF layers in the Imagery Source combo box."""
        # (!) Instead of going thru all project layers each time
        # it'd be better to filter the new layers, then add them to
        # the already filtered ones like rasterCombo.exceptedLayerList() + new_layers
        # but calling exceptedLayerList() crashes when it contains deleted layers

        # so we will need to add new function like "remove_filtered_layers" to handle this.
        # However, current implementation takes 4 ms when 100 files are opened, which is OK

        raster_layers = (layer for layer in self.project.mapLayers().values()
                         if layer.type() == QgsMapLayerType.RasterLayer)
        if self.dlg.modelCombo.currentText() in self.config.SENTINEL_WD_NAMES:
            filtered_raster_layers = raster_layers
        else:
            try:
                filtered_raster_layers = [
                    layer for layer in raster_layers
                    if not helpers.raster_layer_is_allowed(layer)
                ]
            except Exception as e:
                self.alert(f"Error checking raster layers validity: {e}")
        self.dlg.rasterCombo.setExceptedLayerList(filtered_raster_layers)

    def on_model_change(self, index: int) -> None:
        wd_name = self.dlg.modelCombo.currentText()
        wd = self.workflow_defs.get(wd_name)
        self.set_available_imagery_sources(wd_name)
        if not wd:
            return
        self.dlg.show_wd_price(wd_price=wd.pricePerSqKm,
                               wd_description=wd.description,
                               display_price=self.billing_type == BillingType.credits)
        if self.billing_type == BillingType.credits:
            self.update_processing_cost()

    def set_available_imagery_sources(self, wd: str) -> None:
        """Restrict the list of imagery sources according to the selected model."""
        sentinel_providers = [provider.name for provider in self.providers.values() if
                              isinstance(provider, SentinelProvider)]
        web_providers = [provider.name for provider in self.providers.values() if
                         not isinstance(provider, SentinelProvider)]
        current_sources = self.dlg.rasterCombo.additionalItems()
        if wd in self.config.SENTINEL_WD_NAMES and not set(current_sources) == set(sentinel_providers):
            self.dlg.rasterCombo.setAdditionalItems(sentinel_providers)
            if sentinel_providers:
                self.dlg.rasterCombo.setCurrentText(sentinel_providers[0])
            self.dlg.providerCombo.clear()
            self.dlg.providerCombo.addItems(sentinel_providers)
            self.filter_bad_rasters()  # filter rasters for sentinel
        elif not set(current_sources) == set(web_providers):
            # skip update in case source list did not change.
            # This prevents the current selected item from being discarded
            self.dlg.rasterCombo.setAdditionalItems(web_providers)
            self.dlg.providerCombo.clear()
            self.dlg.providerCombo.addItems(web_providers)
            self.filter_bad_rasters()

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
            f' and cloudCover is null or cloudCover <= {max_cloud_cover}'
        )
        aoi = helpers.from_wgs84(self.metadata_aoi, crs)
        self.calculator.setEllipsoid(crs.ellipsoidAcronym())
        self.calculator.setSourceCrs(crs, self.project.transformContext())
        min_intersection_size = self.calculator.measureArea(aoi) * (min_intersection / 100)
        aoi = QgsGeometry.createGeometryEngine(aoi.constGet())
        aoi.prepareGeometry()
        # Get attributes
        if self.dlg.rasterCombo.currentText() == constants.SENTINEL_OPTION_NAME:
            id_column_index = self.config.SENTINEL_ID_COLUMN_INDEX
            datetime_column_index = self.config.SENTINEL_DATETIME_COLUMN_INDEX
            cloud_cover_column_index = self.config.SENTINEL_CLOUD_COLUMN_INDEX
        else:  # Maxar
            id_column_index = self.config.MAXAR_ID_COLUMN_INDEX
            datetime_column_index = self.config.MAXAR_DATETIME_COLUMN_INDEX
            cloud_cover_column_index = self.config.MAXAR_CLOUD_COLUMN_INDEX
        self.metadata_layer.setSubsetString('')  # clear any existing filters
        filtered_ids = [
            feature['id'] for feature in self.metadata_layer.getFeatures()
            if self.calculator.measureArea(
                QgsGeometry(aoi.intersection(feature.geometry().constGet()))
            ) < min_intersection_size
        ]
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

    def set_up_login_dialog(self) -> None:
        """Create a login dialog, set its title and signal-slot connections."""
        self.dlg_login.setWindowTitle(helpers.generate_plugin_header(self.tr("Log in ") + self.plugin_name,
                                                                     self.config.MAPFLOW_ENV,
                                                                     None))
        self.dlg_login.logIn.clicked.connect(self.read_mapflow_token)

    def toggle_polygon_combos(self, use_image_extent: bool) -> None:
        """Disable polygon combos when Use image extent is checked.

        :param use_image_extent: Whether the corresponding checkbox is checked
        """
        self.dlg.polygonCombo.setEnabled(not use_image_extent)

    def on_provider_change(self, index: int) -> None:
        """Adjust max and current zoom, and update the metadata table when user selects another
        provider.

        :param index: The currently selected provider index
        """
        provider_name = self.dlg.rasterCombo.currentText()
        provider_layer = self.dlg.rasterCombo.currentLayer()
        provider = self.providers.get(provider_name, None)
        # Changes in case provider is raster layer
        self.toggle_processing_checkboxes(provider_layer)
        # Changes in search tab
        self.toggle_imagery_search(provider_name,
                                   provider)
        # re-calculate AOI because it may change due to intersection of image/area
        polygon_layer = self.dlg.polygonCombo.currentLayer()
        if provider_layer:
            self.calculate_aoi_area_raster(provider_layer)
        else:
            self.calculate_aoi_area_polygon_layer(polygon_layer)

        self.update_processing_cost()

    def save_dialog_state(self):
        """Memorize dialog element sizes & positioning to allow user to customize the look."""
        # Save main dialog size & position
        self.settings.setValue('mainDialogState', self.dlg.saveGeometry())

    def add_layer(self, layer: QgsMapLayer) -> None:
        """Add layers created by the plugin to the legend.

        By default, layers are added to a group with the same name as the plugin.
        If the group has been deleted by the user, assume they prefer to not use
        the group, and add layers to the legend root.

        :param layer: A vector or raster layer to be added.
        """
        self.layer_group = self.layer_tree_root.findGroup(self.settings.value('layerGroup'))
        if self.add_layers_to_group:
            if not self.layer_group:  # сreate a layer group
                self.layer_group = self.layer_tree_root.insertGroup(0, self.plugin_name)
                # A bug fix, - gotta collapse first to be able to expand it
                # Or else it'll ignore the setExpanded(True) calls
                self.layer_group.setExpanded(False)
                self.settings.setValue('layerGroup', self.plugin_name)
                # If the group has been deleted, assume user wants to add layers to root, memorize it
                self.layer_group.destroyed.connect(lambda: setattr(self, 'add_layers_to_group', False))
                # Let user rename the group, memorize the new name
                self.layer_group.nameChanged.connect(lambda _, name: self.settings.setValue('layerGroup', name))
            # To be added to group, layer has to be added to project first
            self.project.addMapLayer(layer, addToLegend=False)
            # Explcitly add layer to the position 0 or else it adds it to bottom
            self.layer_group.insertLayer(0, layer)
            self.layer_group.setExpanded(True)
        else:  # assume user opted to not use a group, add layers as usual
            self.project.addMapLayer(layer)

    def remove_provider(self) -> None:
        """Delete a web tile provider from the list of registered providers.

        Is called by clicking the red minus button near the provider dropdown list.
        """
        provider_name = self.dlg.providerCombo.currentText()
        provider = self.providers[provider_name]
        if provider.is_default:
            # We want to protect built in providers!
            self.alert(self.tr("This provider is default and cannot be removed"),
                       icon=QMessageBox.Warning)
            return
        # Ask for confirmation
        elif self.alert(self.tr('Permanently remove {}?').format(provider.name),
                        icon=QMessageBox.Question):
            self.providers.pop(provider_name)
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
                self.providers.update({new_provider.name: new_provider})
        else:
            # we replace old provider with a new one
            # if self.dlg_provider.property('mode') == 'edit':  #
            if new_provider.name != old_provider.name and new_provider.name in self.providers:
                # we do not want user to replace another provider when editing this one
                self.alert(self.tr("Provider name must be unique. {name} already exists,"
                                   " select another or delete/edit existing").format(name=new_provider.name),
                           icon=QMessageBox.Warning)
                self.dlg_provider.show()
                return
            else:
                self.providers.pop(old_provider.name)
                self.providers.update({new_provider.name: new_provider})

        self.update_providers()
        self.dlg.providerCombo.setCurrentText(new_provider.name)

    def add_provider(self) -> None:
        self.dlg_provider.setup(None, self.tr("Add new provider"))

    def edit_provider(self) -> None:
        """Prepare and show the provider edit dialog.
        Is called by the corresponding button.
        """
        name = self.dlg.providerCombo.currentText()
        if self.providers[name].is_default:
            self.alert(self.tr("This is a default provider, it cannot be edited"),
                       icon=QMessageBox.Warning)
        else:
            self.show_provider_edit_dialog(name)

    def update_providers(self) -> None:
        """Update imagery & providers dropdown list after edit/add/remove
        It works both ways: if providers is specified, it updates the settings;
        otherwise loads providers list from settings

        args:
         providers: optional ProvidersDict to update settings with
        """
        self.providers.to_settings(self.settings)
        self.dlg.providerCombo.clear()
        self.dlg.providerCombo.addItems(self.providers.keys())

    def show_provider_edit_dialog(self, name) -> None:
        provider = self.providers.get(name, None)
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
            layer.selectionChanged.connect(self.calculate_aoi_area_selection)
            layer.editingStopped.connect(self.calculate_aoi_area_layer_edited)

    def toggle_processing_checkboxes(self, raster_source: Union[QgsRasterLayer, str, None]) -> None:
        """Toggle 'Use image extent' depending on the item in the imagery combo box.

        :param raster_source: Provider name or None, depending on the signal, if one of the
            tile providers, otherwise the selected raster layer
        """
        enabled = isinstance(raster_source, QgsRasterLayer)
        self.dlg.useImageExtentAsAoi.setEnabled(enabled)
        self.dlg.useImageExtentAsAoi.setChecked(enabled)

    def toggle_imagery_search(self,
                              provider_name: str,
                              provider: Optional[Provider]):
        """
        Get necessary attributes from config and send them to MainDialogo to setup Imagery Search tab
        """
        if isinstance(provider, SentinelProvider):
            columns = self.config.SENTINEL_ATTRIBUTES
            hidden_columns = (len(columns) - 1,)
            sort_by = self.config.SENTINEL_DATETIME_COLUMN_INDEX
            current_zoom = max_zoom = None
            image_id_tooltip = self.tr(
                'If you already know which {provider_name} image you want to process,\n'
                'simply paste its ID here. Otherwise, search suitable images in the catalog below.'
            ).format(provider_name=provider_name)
            image_id_placeholder = self.tr('e.g. S2B_OPER_MSI_L1C_TL_VGS4_20220209T091044_A025744_T36SXA_N04_00')
        elif isinstance(provider, (MaxarProvider, MaxarProxyProvider)):
            columns = self.config.MAXAR_METADATA_ATTRIBUTES
            hidden_columns = tuple()
            sort_by = self.config.MAXAR_DATETIME_COLUMN_INDEX
            max_zoom = self.config.MAX_ZOOM
            current_zoom = int(self.settings.value('maxZoom', self.config.DEFAULT_ZOOM))
            image_id_tooltip = self.tr(
                'If you already know which {provider_name} image you want to process,\n'
                'simply paste its ID here. Otherwise, search suitable images in the catalog below.'
            ).format(provider_name=provider_name)
            image_id_placeholder = self.tr('e.g. a3b154c40cc74f3b934c0ffc9b34ecd1')
        else:
            # other providers do not support imagery search,
            # tear down the table and deactivate the panel
            columns = tuple()  # empty
            hidden_columns = tuple()
            sort_by = None
            max_zoom = self.config.MAX_ZOOM
            # Forced to int bc somehow used to be stored as str, so for backward compatability
            current_zoom = int(self.settings.value('maxZoom', self.config.DEFAULT_ZOOM))
            image_id_placeholder = ""
            image_id_tooltip = self.tr("{} doesn't allow processing single images.").format(provider_name)

        # override max zoom for proxy maxar provider
        if isinstance(provider, MaxarProxyProvider):
            max_zoom = self.config.MAXAR_MAX_FREE_ZOOM
            current_zoom = max_zoom
        self.dlg.setup_imagery_search(provider_name=provider_name,
                                      provider=provider,
                                      columns=columns,
                                      hidden_columns=hidden_columns,
                                      sort_by=sort_by,
                                      preview_zoom=current_zoom,
                                      max_preview_zoom=max_zoom,
                                      more_button_name=self.config.METADATA_MORE_BUTTON_OBJECT_NAME,
                                      image_id_placeholder=image_id_placeholder,
                                      image_id_tooltip=image_id_tooltip)

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
            return path

    def check_if_output_directory_is_selected(self) -> bool:
        """Check if the user specified an existing output dir.

        Returns True if an existing directory is specified or a new directory has been selected, else False.
        """
        if os.path.exists(self.dlg.outputDirectory.text()) or self.select_output_directory():
            return True
        self.alert(self.tr('Please, specify an existing output directory'))
        return False

    def get_metadata(self) -> None:
        """Metadata is image footprints with attributes like acquisition date or cloud cover."""
        self.dlg.metadataTable.clearContents()
        self.dlg.metadataTable.setRowCount(0)
        more_button = self.dlg.findChild(QPushButton, self.config.METADATA_MORE_BUTTON_OBJECT_NAME)
        if more_button:
            self.dlg.layoutMetadataTable.removeWidget(more_button)
            more_button.deleteLater()
        provider = self.providers[self.dlg.rasterCombo.currentText()]
        # Check if the AOI is defined
        if self.dlg.metadataUseCanvasExtent.isChecked():
            aoi = helpers.to_wgs84(
                QgsGeometry.fromRect(self.iface.mapCanvas().extent()),
                self.project.crs()
            )
        elif self.aoi:
            aoi = self.aoi
        else:
            self.alert(self.tr('Please, select an area of interest'))
            return

        from_ = self.dlg.metadataFrom.date().toString(Qt.ISODate)
        to = self.dlg.metadataTo.date().toString(Qt.ISODate)
        max_cloud_cover = self.dlg.maxCloudCover.value()
        min_intersection = self.dlg.minIntersection.value()
        if isinstance(provider, (MaxarProxyProvider, MaxarProvider)):
            self.get_maxar_metadata(aoi, provider, from_, to, max_cloud_cover, min_intersection)
        elif isinstance(provider, SentinelProvider):
            self.request_skywatch_metadata(aoi, from_, to, max_cloud_cover, min_intersection)
        else:
            self.alert(self.tr("Provider {name} does not support metadata requests").format(name=provider.name))

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
        self.metadata_layer.selectionChanged.connect(self.sync_layer_selection_with_table)
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
            self.add_layer(self.metadata_layer)
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
            provider: Provider,
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
        if provider.is_proxy:  # assume user wants to use our account, proxy thru Mapflow
            self.http.post(
                url=provider.meta_url,
                body=request_body,
                callback=self.get_maxar_metadata_callback,
                callback_kwargs=callback_kwargs,
                timeout=7
            )
        else:  # user's own account
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
                error_handler=self.get_maxar_metadata_error_handler,
                use_default_error_handler=False
            )

    def get_maxar_metadata_callback(
            self,
            response: QNetworkReply,
            provider: Provider,
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

        # Delete previous search
        try:
            self.project.removeMapLayer(self.metadata_layer)
        except (AttributeError, RuntimeError):  # metadata layer has been deleted
            pass
        with open(os.path.join(self.temp_dir, os.urandom(32).hex()) + '.geojson', 'w') as file:
            json.dump(metadata, file)
            file.seek(0)
            self.metadata_layer = QgsVectorLayer(file.name, f'{provider.name} metadata', 'ogr')

        self.metadata_layer.loadNamedStyle(os.path.join(self.plugin_dir, 'static', 'styles', 'metadata.qml'))
        self.metadata_layer.selectionChanged.connect(self.sync_layer_selection_with_table)
        self.add_layer(self.metadata_layer)
        # Memorize IDs and extents to be able to clip the user's AOI to image on processing creation
        self.maxar_metadata_footprints = {
            feature['id']: feature
            for feature in self.metadata_layer.getFeatures()
        }
        # Fill out the table
        self.dlg.metadataTable.setRowCount(metadata['totalFeatures'])
        # Row insertion triggers sorting -> row indexes shift -> duplicate rows, so turn sorting off
        self.dlg.metadataTable.setSortingEnabled(False)
        for row, feature in enumerate(metadata['features']):
            feature['properties']['id'] = feature['id']  # for uniformity
            for col, attr in enumerate(self.config.MAXAR_METADATA_ATTRIBUTES.values()):
                try:
                    value = feature['properties'][attr]
                except KeyError:  # e.g. <colorBandOrder/> for pachromatic images
                    value = ''
                table_item = QTableWidgetItem()
                table_item.setData(Qt.DisplayRole, value)
                self.dlg.metadataTable.setItem(row, col, table_item)
        # Turn sorting on again
        self.dlg.metadataTable.setSortingEnabled(True)
        self.filter_metadata(min_intersection=min_intersection, max_cloud_cover=max_cloud_cover)

    def get_maxar_metadata_error_handler(self, response: QNetworkReply) -> None:
        """Error handler for metadata requests.

        :param response: The HTTP response.
        """
        error = response.error()
        if error in [QNetworkReply.ContentAccessDenied]:  # , QNetworkReply.AuthenticationRequiredError):
            self.alert(self.tr('Please, check your credentials'))
        else:
            self.report_http_error(response,
                                   self.tr("We couldn't get metadata from Maxar, "
                                           "error {error}").format(
                                       error=response.attribute(QNetworkRequest.HttpStatusCodeAttribute)),
                                   error_message_parser=securewatch_message_parser)

    def sync_table_selection_with_image_id_and_layer(self) -> str:
        """
        Every time user selects a row in the metadata table, select the
        corresponding feature in the metadata layer and put the selected image's
        id into the "Image ID" field.
        """
        selected_cells = self.dlg.metadataTable.selectedItems()
        if not selected_cells:
            self.dlg.imageId.setText('')
            try:
                self.metadata_layer.removeSelection()
            except RuntimeError:  # layer has been deleted
                pass
            return
        id_column_index = (
            self.config.SENTINEL_ID_COLUMN_INDEX
            if self.dlg.rasterCombo.currentText() == constants.SENTINEL_OPTION_NAME
            else self.config.MAXAR_ID_COLUMN_INDEX
        )
        image_id = next(cell for cell in selected_cells if cell.column() == id_column_index).text()
        try:
            already_selected = [feature['id'] for feature in self.metadata_layer.selectedFeatures()]
            if (len(already_selected) != 1 or already_selected[0] != image_id):
                self.metadata_layer.selectByExpression(f"id='{image_id}'")
        except RuntimeError:  # layer has been deleted
            pass
        if self.dlg.imageId.text() != image_id:
            self.dlg.imageId.setText(image_id)
        self.calculate_aoi_area_polygon_layer(self.dlg.polygonCombo.currentLayer())

    def sync_layer_selection_with_table(self, selected_ids: List[int]) -> None:
        """
        Every time user selects an image in the metadata layer, select the corresponding
        row in the table and fill out the image id in the providers tab.

        :param selected_ids: The selected feature IDs. These aren't the image IDs, but rather
            the primary keys of the features.
        """
        if not selected_ids:
            self.dlg.metadataTable.clearSelection()
            return
        selected_id = self.metadata_layer.getFeature(selected_ids[-1])['id']
        id_column_index = [
            self.config.SENTINEL_ID_COLUMN_INDEX
            if self.dlg.rasterCombo.currentText() == constants.SENTINEL_OPTION_NAME
            else self.config.MAXAR_ID_COLUMN_INDEX
        ]
        already_selected = [
            item.text() for item in self.dlg.metadataTable.selectedItems()
            if item.column() == id_column_index
        ]
        if selected_id not in already_selected:
            self.dlg.metadataTable.selectRow(
                self.dlg.metadataTable.findItems(selected_id, Qt.MatchExactly)[0].row()
            )

    def sync_image_id_with_table_and_layer(self, image_id: str) -> None:
        """
        Select a footprint in the current metadata layer when user selects it in the table.

        :param image_id: The new image ID.
        """
        if not image_id:
            self.dlg.metadataTable.clearSelection()
            return
        provider = self.providers.get(self.dlg.rasterCombo.currentText())

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
                self.dlg.imageId.clear()
                return
        elif isinstance(provider, (MaxarProvider, MaxarProxyProvider)):
            if not helpers.UUID_REGEX.match(image_id):
                self.dlg.imageId.clear()
                self.alert('A Maxar image ID should look like a3b154c40cc74f3b934c0ffc9b34ecd1')
                return
        items = self.dlg.metadataTable.findItems(image_id, Qt.MatchExactly)
        if not items:
            self.dlg.metadataTable.clearSelection()
            return
        if items[0] not in self.dlg.metadataTable.selectedItems():
            self.dlg.metadataTable.selectRow(items[0].row())

    def calculate_aoi_area_polygon_layer(self, layer: Union[QgsVectorLayer, None]) -> None:
        """Get the AOI size total when polygon another layer is chosen,
        current layer's selection is changed or the layer's features are modified.

        :param layer: The current polygon layer
        """
        if self.dlg.useImageExtentAsAoi.isChecked():  # GeoTIFF extent used; no difference
            return
        if layer and self.max_aois_per_processing >= layer.featureCount() > 0:
            features = list(layer.getSelectedFeatures()) or list(layer.getFeatures())
            if len(features) == 1:
                aoi = features[0].geometry()
            else:
                aoi = QgsGeometry.collectGeometry([feature.geometry() for feature in features])
            self.calculate_aoi_area(aoi, layer.crs())
        elif layer and self.max_aois_per_processing < layer.featureCount():
            self.dlg.labelAoiArea.clear()
            self.dlg.processingProblemsLabel.setPalette(self.dlg.alert_palette)
            self.dlg.processingProblemsLabel.setText(self.tr('AOI must contain not more than'
                                                        ' {} polygons').format(self.max_aois_per_processing))
            self.dlg.startProcessing.setDisabled(True)
            self.aoi = self.aoi_size = None
        else:  # empty layer or combo's itself is empty
            self.dlg.labelAoiArea.clear()
            self.dlg.processingProblemsLabel.setPalette(self.dlg.alert_palette)
            self.dlg.processingProblemsLabel.setText(self.tr('Set AOI to start processing'))
            self.dlg.startProcessing.setDisabled(True)
            self.aoi = self.aoi_size = None

    def calculate_aoi_area_raster(self, layer: Optional[QgsRasterLayer]) -> None:
        """Get the AOI size when a new entry in the raster combo box is selected.

        :param layer: The current raster layer
        """
        if layer:
            geometry = QgsGeometry.collectGeometry([QgsGeometry.fromRect(layer.extent())])
            self.calculate_aoi_area(geometry, layer.crs())
        else:
            self.calculate_aoi_area_polygon_layer(self.dlg.polygonCombo.currentLayer())

    def calculate_aoi_area_use_image_extent(self, use_image_extent: bool) -> None:
        """Get the AOI size when the Use image extent checkbox is toggled.

        :param use_image_extent: The current state of the checkbox
        """
        if use_image_extent:
            self.calculate_aoi_area_raster(self.dlg.rasterCombo.currentLayer())
        else:
            self.calculate_aoi_area_polygon_layer(self.dlg.polygonCombo.currentLayer())

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
        raster_option = self.dlg.rasterCombo.currentText()
        imagery = self.dlg.rasterCombo.currentLayer()
        use_image_extent_as_aoi = self.dlg.useImageExtentAsAoi.isChecked()
        selected_image = self.dlg.metadataTable.selectedItems()
        # This is AOI with respect to selected Maxar images and raster image extent
        try:
            real_aoi = self.get_aoi(raster_option=raster_option,
                                    raster_layer=imagery,
                                    use_image_extent_as_aoi=use_image_extent_as_aoi,
                                    selected_image=selected_image,
                                    selected_aoi=self.aoi)
            self.aoi_size = layer_utils.calculate_aoi_area(real_aoi, self.project.transformContext())
        except:
            # Could not calculate AOI size
            self.aoi_size = 0
        self.dlg.labelAoiArea.setText(self.tr('Area: {:.2f} sq.km').format(self.aoi_size))
        self.update_processing_cost()

    def update_processing_cost(self):
        if not self.aoi:
            # Here the button must already be disabled, and the warning text set
            if self.dlg.startProcessing.isEnabled():
                self.dlg.startProcessing.setDisabled(True)
                self.dlg.processingProblemsLabel.setPalette(self.dlg.alert_palette)
                self.dlg.processingProblemsLabel.setText(self.tr("Set AOI to start processing"))
        elif not self.workflow_defs:
            self.dlg.startProcessing.setDisabled(True)
            self.dlg.processingProblemsLabel.setPalette(self.dlg.alert_palette)
            self.dlg.processingProblemsLabel.setText("Error! Models are not initialized")
        elif self.billing_type != BillingType.credits:
            self.dlg.startProcessing.setEnabled(True)
            self.dlg.processingProblemsLabel.clear()
        else:  # self.billing_type == BillingType.credits: f
            request_body, error = self.create_processing_request(allow_empty_name=True)
            if not request_body:
                self.dlg.processingProblemsLabel.setPalette(self.dlg.alert_palette)
                self.dlg.processingProblemsLabel.setText(self.tr("Processing cost is not available:\n"
                                                                 "{error}").format(error=error))

            else:
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
        message = api_message_parser(response_text)
        self.dlg.processingProblemsLabel.setPalette(self.dlg.alert_palette)
        self.dlg.processingProblemsLabel.setText(self.tr('Processing cost is not available:\n'
                                                         '{message}').format(message=message))
        self.dlg.startProcessing.setEnabled(True)

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
        selected_ids = [
            self.dlg.processingsTable.item(index.row(), self.config.PROCESSING_TABLE_ID_COLUMN_INDEX).text()
            for index in self.dlg.processingsTable.selectionModel().selectedRows()
        ]
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

    def delete_processings_error_handler(self, response: QNetworkReply) -> None:
        """Error handler for processing deletion request.

        :param response: The HTTP response.
        """
        self.report_http_error(response, self.tr("Error deleting a processing"))

    def upload_image(self, layer,
                     processing_params: Optional[PostProcessingSchema] = None,
                     mosaic=None):
        """
        if processing_params are None, we do not call processing after upload;
        this is a stub for further data-catalog usage
        Also, mosaic can be specified to upload to specific mosaic
        """
        body = QHttpMultiPart(QHttpMultiPart.FormDataType)
        tif = QHttpPart()
        tif.setHeader(QNetworkRequest.ContentTypeHeader, 'image/tiff')
        filename = Path(layer.dataProvider().dataSourceUri()).name
        tif.setHeader(QNetworkRequest.ContentDispositionHeader, f'form-data; name="file"; filename="{filename}"')
        image = QFile(layer.dataProvider().dataSourceUri(), body)
        image.open(QIODevice.ReadOnly)
        tif.setBodyDevice(image)
        body.append(tif)
        if processing_params:
            callback = self.upload_tif_callback
            callback_kwargs = {'processing_params': processing_params}
        else:
            # uploading without processing creation
            callback = None
            callback_kwargs = None
        if mosaic:
            url = f'{self.server}/mosaic/{mosaic}/image'
        else:
            url = f'{self.server}/rasters'
        response = self.http.post(
            url=url,
            callback=callback,
            callback_kwargs=callback_kwargs,
            error_handler=self.upload_tif_error_handler,
            use_default_error_handler=False,
            body=body,
            timeout=3600  # one hour
        )
        body.setParent(response)
        progress_message = QgsMessageBarItem(
            self.plugin_name,
            self.tr('Uploading image to Mapflow...'),
            QProgressBar(self.message_bar),
            parent=self.message_bar
        )
        self.message_bar.pushItem(progress_message)

        def display_upload_progress(bytes_sent: int, bytes_total: int):
            try:
                progress_message.widget().setValue(round(bytes_sent / bytes_total * 100))
            except ZeroDivisionError:  # may happen for some reason
                return
            if bytes_sent == bytes_total:
                self.message_bar.popWidget(progress_message)

        connection = response.uploadProgress.connect(display_upload_progress)
        # Tear this connection if the user closes the progress message
        progress_message.destroyed.connect(lambda: response.uploadProgress.disconnect(connection))

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
                raise BadProcessingInput(self.tr('Please, select an area of interest'))
        if self.aoi_area_limit < self.aoi_size:
            raise BadProcessingInput(self.tr(
                'Up to {} sq km can be processed at a time. '
                'Try splitting your area(s) into several processings.').format(self.aoi_area_limit))
        return True

    def crop_aoi_with_maxar_image_footprint(self,
                                            aoi: QgsFeature,
                                            image_id: str):
        extent = self.maxar_metadata_footprints[image_id[self.config.MAXAR_ID_COLUMN_INDEX].text()]
        try:
            aoi = next(clip_aoi_to_image_extent(aoi, extent)).geometry()
        except StopIteration:
            raise AoiNotIntersectsImage()
        return aoi

    def get_processing_params(self,
                              raster_option: str,
                              raster_layer: Optional[QgsRasterLayer],
                              s3_uri: str = "",
                              image_id: Optional[str] = None):
        meta = {'source-app': 'qgis',
                'version': self.plugin_version,
                'source': raster_option.lower()}
        if raster_layer is not None:
            # We cannot set URL yet if we do not know it before the image is uploaded
            return ProcessingParams(source_type='tif', url=s3_uri), meta
        provider = self.providers.get(raster_option)
        if not provider:
            raise PluginError(self.tr('Providers are not initialized'))
        provider_params, provider_meta = provider.to_processing_params(image_id=image_id)
        meta.update(**provider_meta)
        return provider_params, meta

    def get_aoi(self,
                raster_option: Optional[str],
                raster_layer: Optional[QgsRasterLayer],
                use_image_extent_as_aoi: bool,
                selected_aoi: QgsGeometry,
                selected_image: Optional[str] = None) -> QgsGeometry:
        if not helpers.check_aoi(selected_aoi):
            raise BadProcessingInput(self.tr('Bad AOI. AOI must be inside boundaries:'
                                             ' \n[-180, 180] by longitude, [-90, 90] by latitude'))

        if raster_layer is not None:
            # selected raster source is a layer
            aoi = layer_utils.get_raster_aoi(raster_layer=raster_layer,
                                              selected_aoi=selected_aoi,
                                              use_image_extent_as_aoi=use_image_extent_as_aoi)
            if not aoi:
                raise AoiNotIntersectsImage()
            return aoi
        else:
            provider = self.providers.get(raster_option)
            if not provider:
                raise PluginError(self.tr('Providers are not initialized'))
            if selected_image:
                if isinstance(provider, (MaxarProvider, MaxarProxyProvider)):
                    aoi = self.crop_aoi_with_maxar_image_footprint(selected_aoi, selected_image)
                elif isinstance(provider, SentinelProvider):
                    # todo: crop sentinel aoi with image footprint?
                    aoi = selected_aoi
            elif provider.requires_image_id:
                raise PluginError(self.tr("Please select image in Search table for {}").format(provider.name))
            else:
                aoi = selected_aoi
        return aoi

    def create_processing_request(self,
                                  allow_empty_name: bool = False) -> Tuple[Optional[PostProcessingSchema], str]:
        processing_name = self.dlg.processingName.text()
        raster_option = self.dlg.rasterCombo.currentText()
        imagery = self.dlg.rasterCombo.currentLayer()
        use_image_extent_as_aoi = self.dlg.useImageExtentAsAoi.isChecked()
        image_id = self.dlg.imageId.text()
        selected_image = self.dlg.metadataTable.selectedItems()
        wd_name = self.dlg.modelCombo.currentText()
        wd_id = self.workflow_defs.get(wd_name).id
        try:
            self.check_processing_ui(allow_empty_name=allow_empty_name)
            provider_params, processing_meta = self.get_processing_params(raster_option=raster_option,
                                                                          raster_layer=imagery,
                                                                          image_id=image_id)
            aoi = self.get_aoi(raster_option=raster_option,
                               raster_layer=imagery,
                               use_image_extent_as_aoi=use_image_extent_as_aoi,
                               selected_image=selected_image,
                               selected_aoi=self.aoi)
        except AoiNotIntersectsImage:
            return None, self.tr("Selected AOI does not intestect the selected image")
        except ImageIdRequired:
            return None, self.tr("This provider requires image ID!")
        except PluginError as e:
            return None, str(e)
        processing_params = PostProcessingSchema(
            name=processing_name,
            wdId=wd_id,
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

        raster_option = self.dlg.rasterCombo.currentText()
        imagery = self.dlg.rasterCombo.currentLayer()

        self.message_bar.pushInfo(self.plugin_name, self.tr('Starting the processing...'))
        if imagery:
            try:
                self.upload_image(layer=imagery, processing_params=processing_params)
            except Exception as e:
                self.alert(self.tr("Could not launch processing! Error: {}.").format(str(e)))
            return
        else:
            provider = self.providers[raster_option]
            if isinstance(provider, MaxarProxyProvider) and not self.is_premium_user:
                ErrorMessageWidget(
                    parent=self.dlg,
                    text=self.tr('Click on the link below to send us an email'),
                    title=self.tr('Upgrade your subscription to process Maxar imagery'),
                    email_body=self.tr(
                        "I'd like to upgrade my subscription to Mapflow Processing API "
                        'to be able to process Maxar imagery.'
                    )
                ).show()
                return
            try:
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
        if self.config.PROJECT_ID != 'default':
            request_body.projectId = self.config.PROJECT_ID
        self.http.post(
            url=f'{self.server}/processings',
            callback=self.post_processing_callback,
            callback_kwargs={'processing_name': request_body.name},
            error_handler=self.post_processing_error_handler,
            use_default_error_handler=False,
            body=request_body.as_json().encode()
        )

    def post_processing_error_handler(self, response: QNetworkReply) -> None:
        """Error handler for processing creation requests.

        :param response: The HTTP response.
        """
        self.report_http_error(response,
                               self.tr('Processing creation failed'),
                               error_message_parser=api_message_parser)

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
            url=f'{self.server}/projects/{self.config.PROJECT_ID}/processings',
            callback=self.get_processings_callback
        )

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

    def preview_sentinel_callback(self, response: QNetworkReply, datetime_: str, image_id: str) -> None:
        """Save and open the preview image as a layer."""
        with open(os.path.join(self.temp_dir, os.urandom(32).hex()), mode='wb') as f:
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
        self.add_layer(layer)

    def preview_sentinel_error_handler(self, response: QNetworkReply, guess_format=False, **kwargs) -> None:
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
        attrs = tuple(self.config.MAXAR_METADATA_ATTRIBUTES.values())
        try:
            layer_name = ' '.join((
                layer_name,
                self.dlg.metadataTable.item(row, attrs.index('acquisitionDate')).text(),
                self.dlg.metadataTable.item(row, attrs.index('productType')).text()
            ))
        except AttributeError:  # the table is empty
            layer_name = f'{layer_name} {image_id}'
        return layer_name

    def maxar_extent(self, image_id):
        if not image_id:
            return None
        try:  # Get the image extent to set the correct extent on the raster layer
            footprint = next(self.metadata_layer.getFeatures(f"id = '{image_id}'"))
        except (RuntimeError, AttributeError, StopIteration):  # layer doesn't exist or has been deleted, or empty
            extent = None
        else:
            extent = helpers.from_wgs84(footprint.geometry(), helpers.WEB_MERCATOR).boundingBox()
        return extent

    def preview_xyz(self, provider, image_id):
        max_zoom = self.dlg.maxZoom.value()
        layer_name = provider.name
        try:
            url = provider.preview_url(image_id=image_id)
        except ImageIdRequired as e:
            self.alert(self.tr("Provider {name} requires image id for preview!").format(name=provider.name),
                       QMessageBox.Warning)
            return
        except NotImplementedError as e:
            self.alert(self.tr("Preview is unavailable for the provider {}").format(provider.name))
        except Exception as e:
            self.alert(str(e), QMessageBox.Warning)
        if provider.is_proxy:
            uri = layer_utils.generate_xyz_layer_definition(url,
                                                            self.username,
                                                            self.password,
                                                            max_zoom, image_id)
            extent = self.maxar_extent(image_id)
            layer_name = self.maxar_layer_name(layer_name, image_id)
        else:
            uri = layer_utils.generate_xyz_layer_definition(url,
                                                            provider.credentials.login,
                                                            provider.credentials.password,
                                                            max_zoom, provider.source_type)
            extent = None
        layer = QgsRasterLayer(uri, layer_name, 'wms')
        if layer.isValid():
            if isinstance(provider, (MaxarProvider, MaxarProxyProvider)) and image_id and extent:
                layer.setExtent(extent)
            self.add_layer(layer)
        else:
            self.alert(self.tr("We couldn't load a preview for this image"))

    def preview(self) -> None:
        """Display raster tiles served over the Web."""
        if self.dlg.rasterCombo.currentLayer() is not None:
            self.iface.setActiveLayer(self.dlg.rasterCombo.currentLayer())
            self.iface.zoomToActiveLayer()
            return
        provider_name = self.dlg.rasterCombo.currentText()
        image_id = self.dlg.imageId.text()
        provider = self.providers[provider_name]
        if isinstance(provider, SentinelProvider):
            self.preview_sentinel(image_id=image_id)
        else:  # XYZ providers
            self.preview_xyz(provider=provider, image_id=image_id)

    def update_processing_current_rating(self) -> None:
        # reset labels:
        row = self.dlg.processingsTable.currentRow()
        pid = self.dlg.processingsTable.item(row, self.config.PROCESSING_TABLE_ID_COLUMN_INDEX).text()
        p_name = self.dlg.processingsTable.item(row, 0).text()

        self.dlg.set_processing_rating_labels(processing_name=p_name)
        self.http.get(
            url=f'{self.server}/processings/{pid}',
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
        row = self.dlg.processingsTable.currentRow()
        if not row and (row != 0):
            return
        pid = self.dlg.processingsTable.item(row, self.config.PROCESSING_TABLE_ID_COLUMN_INDEX).text()
        processing = next(filter(lambda p: p.id_ == pid, self.processings))
        if processing.status != 'OK':
            self.alert(self.tr('Only finished processings can be rated'))
            return
        pid = self.dlg.processingsTable.item(row, self.config.PROCESSING_TABLE_ID_COLUMN_INDEX).text()
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
        review_text_present = self.dlg.processingRatingFeedbackText.toPlainText() != ""
        if not status_ok:
            reason = self.tr("Only correctly finished processings (status OK) can be reviewed")
        elif not review_text_present:
            reason = self.tr("Please fill review text form to submit review")
        else:
            reason = ""
        self.dlg.enable_review(status_ok,
                               review_text_present,
                               reason)

    def enable_rating_submit(self, status_ok: bool) -> None:
        rating_selected = 5 >= self.dlg.ratingComboBox.currentIndex() > 0
        if not status_ok:
            reason = self.tr("Only correctly finished processings (status OK) can be rated")
        elif not rating_selected:
            reason = self.tr("Please select rating to submit")
        else:
            reason = ""
        self.dlg.enable_rating(status_ok,
                               rating_selected,
                               reason)

    def enable_feedback(self) -> None:
        row = self.dlg.processingsTable.currentRow()
        if not row >= 0:
            return
        pid = self.dlg.processingsTable.item(row, self.config.PROCESSING_TABLE_ID_COLUMN_INDEX).text()
        processing = next(filter(lambda p: p.id_ == pid, self.processings))
        status_ok = (processing.status == 'OK')

        if self.review_workflow_enabled:
            self.enable_review_submit(status_ok)
        else:
            self.enable_rating_submit(status_ok)

    def download_results(self) -> None:
        """Download and display processing results along with the source raster, if available.

        Results will be downloaded into the user's output directory.
        If it's unset, the user will be prompted to select one.
        Unfinished or failed processings yield partial or no results.

        Is called by double-clicking on a row in the processings table.

        :param row: int Row number in the processings table (0-based)
        """
        if not self.check_if_output_directory_is_selected():
            return
        row = self.dlg.processingsTable.currentRow()
        if row < 0:  # for some reason, if nothing is selected, returns -1
            return
        pid = self.dlg.processingsTable.item(row, self.config.PROCESSING_TABLE_ID_COLUMN_INDEX).text()
        if not pid in self.processing_history.finished:
            self.alert(self.tr("Only the results of correctly finished processing can be loaded"))
            return
        self.dlg.processingsTable.setEnabled(False)
        self.http.get(
            url=f'{self.server}/processings/{pid}/result',
            callback=self.download_results_callback,
            callback_kwargs={'pid': pid},
            error_handler=self.download_results_error_handler,
            timeout=300
        )

    def download_results_callback(self, response: QNetworkReply, pid: str) -> None:
        """Display processing results upon their successful fetch.

        :param response: The HTTP response.
        :param pid: ID of the inspected processing.
        """
        self.dlg.processingsTable.setEnabled(True)
        processing = next(filter(lambda p: p.id_ == pid, self.processings))
        # Avoid overwriting existing files by adding (n) to their names
        output_path = os.path.join(self.dlg.outputDirectory.text(), processing.id_)
        extension = '.gpkg'
        if os.path.exists(output_path + extension):
            count = 1
            while os.path.exists(output_path + f'({count})' + extension):
                count += 1
            output_path += f'({count})' + extension
        else:
            output_path += extension
        transform = self.project.transformContext()
        # Layer creation options for QGIS 3.10.3+
        write_options = QgsVectorFileWriter.SaveVectorOptions()
        write_options.layerOptions = ['fid=id']
        with open(os.path.join(self.temp_dir, os.urandom(32).hex()), mode='wb+') as f:
            f.write(response.readAll().data())
            f.seek(0)  # rewind the cursor to the start of the file
            layer = QgsVectorLayer(f.name, '', 'ogr')
            # writeAsVectorFormat keeps changing with versions so gotta check the version :-(
            if Qgis.QGIS_VERSION_INT < 31003:
                error, msg = QgsVectorFileWriter.writeAsVectorFormat(
                    layer,
                    output_path,
                    'utf8',
                    layerOptions=['fid=id']
                )
            elif Qgis.QGIS_VERSION_INT >= 32000:
                # V3 returns two additional str values but they're not documented, so just discard them
                error, msg, *_ = QgsVectorFileWriter.writeAsVectorFormatV3(
                    layer,
                    output_path,
                    transform,
                    write_options
                )
            else:
                error, msg = QgsVectorFileWriter.writeAsVectorFormatV2(
                    layer,
                    output_path,
                    transform,
                    write_options
                )
        if error:
            self.alert(self.tr('Error loading results. Error code: ' + str(error)))
            return
        # Load the results into QGIS
        results_layer = QgsVectorLayer(output_path, processing.name, 'ogr')
        results_layer.loadNamedStyle(os.path.join(
            self.plugin_dir,
            'static',
            'styles',
            self.config.STYLES.get(processing.workflow_def, 'default') + '.qml'
        ))
        # Add the source raster (COG) if it has been created
        raster_url = processing.raster_layer.get('tileUrl')
        tile_json_url = processing.raster_layer.get("tileJsonUrl")
        if raster_url:
            params = {
                'type': 'xyz',
                'url': raster_url,
                'zmin': 0,
                'zmax': 18,
                'username': self.username,
                'password': self.password
            }
            raster = QgsRasterLayer(
                '&'.join(f'{key}={val}' for key, val in params.items()),  # don't URL-encode it
                processing.name + ' image',
                'wms'
            )
            self.http.get(
                url=tile_json_url,
                callback=self.set_raster_extent,
                callback_kwargs={
                    'vector': results_layer,
                    'raster': raster
                },
                use_default_error_handler=False,
                error_handler=self.set_raster_extent_error_handler,
                error_handler_kwargs={
                    'vector': results_layer,
                }
            )
        else:
            self.set_raster_extent_error_handler(response=None, vector=results_layer)

    def download_results_error_handler(self, response: QNetworkReply) -> None:
        """Error handler for downloading processing results.

        :param response: The HTTP response.
        """
        self.dlg.processingsTable.setEnabled(True)
        self.report_http_error(response,
                               self.tr('Error downloading results'),
                               error_message_parser=api_message_parser())

    def set_raster_extent(
            self,
            response: QNetworkReply,
            vector: QgsVectorLayer,
            raster: QgsRasterLayer
    ) -> None:
        """Set processing raster extent upon successfully requesting the processing's AOI.

        :param response: The HTTP response.
        :param vector: The downloaded feature layer.
        :param raster: The downloaded raster which was used for processing.
        """
        bounding_box = layer_utils.get_bounding_box_from_tile_json(response=response)
        raster.setExtent(rect=bounding_box)
        self.add_layer(raster)
        self.add_layer(vector)
        self.iface.zoomToActiveLayer()

    def set_raster_extent_error_handler(self,
                                        response: QNetworkReply,
                                        vector: Optional[QgsVectorLayer]):

        """Error handler for processing AOI requests. If tilejson can't be loaded, we do not add raster layer, and
        """
        self.add_layer(vector)

    def alert(self, message: str, icon: QMessageBox.Icon = QMessageBox.Critical, blocking=True) -> None:
        """Display a minimalistic modal dialog with some info or a question.

        :param message: A text to display
        :param icon: Info/Warning/Critical/Question
        :param blocking: Opened as modal - code below will only be executed when the alert is closed
        """
        box = QMessageBox(icon, self.plugin_name, message, parent=QApplication.activeWindow())
        if icon == QMessageBox.Question:  # by default, only OK is added
            box.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        return box.exec() == QMessageBox.Ok if blocking else box.open()

    def get_processings_callback(self, response: QNetworkReply) -> None:
        """Update the processing table and user limit.

        :param response: The HTTP response.
        """
        raw_processings: list[dict] = json.loads(response.readAll().data())
        if all([p['status'] != 'IN_PROGRESS' for p in raw_processings]):  # stop polling
            self.processing_fetch_timer.stop()

        processings = parse_processings_request(raw_processings)

        env = self.config.MAPFLOW_ENV
        processing_history = self.settings.value('processings')
        self.processing_history = ProcessingHistory.from_settings(
            processing_history.get(env, {}).get(self.username, {}))
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
            processing_history[env][self.username] = self.processing_history.asdict()
        except KeyError:  # history for the current env hasn't been initialized yet
            processing_history[env] = {self.username: self.processing_history.asdict()}
        self.settings.setValue('processings', processing_history)

    def alert_failed_processings(self, failed_processings):
        if not failed_processings:
            return
            # this means that some of processings have failed since last update and the limit must have been returned
        if len(failed_processings) == 1:
            # Print error message from first failed processing
            proc = failed_processings[0]
            self.alert(
                proc.name +
                self.tr(' failed with error:\n') + proc.error_message(),
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
        selected_processings = [
            index.data() for index in self.dlg.processingsTable.selectionModel().selectedIndexes()
            if index.column() == self.config.PROCESSING_TABLE_ID_COLUMN_INDEX
        ]
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
            for col, attr in enumerate(self.config.PROCESSING_ATTRIBUTES):
                table_item = QTableWidgetItem()
                table_item.setData(Qt.DisplayRole, processing_dict[attr])
                if proc.status == 'FAILED':
                    table_item.setToolTip(proc.error_message())
                elif proc.status == 'OK':
                    table_item.setToolTip(self.tr("Double click to add results to the map"))
                self.dlg.processingsTable.setItem(row, col, table_item)
            if proc.id_ in selected_processings:
                self.dlg.processingsTable.selectRow(row)
        self.dlg.processingsTable.setSortingEnabled(True)
        # Restore extended selection
        self.dlg.processingsTable.setSelectionMode(QAbstractItemView.ExtendedSelection)

    def initGui(self) -> None:
        """Create the menu entries and toolbar icons inside the QGIS GUI.

        This function is referenced by the QGIS plugin loading system, so it can't be renamed.
        Since there are submodules, the various UI texts are set dynamically.
        """
        # Set main dialog title dynamically so it could be overridden when used as a submodule
        if self.config.MAPFLOW_ENV == 'production':
            self.dlg.setWindowTitle(self.plugin_name)
        else:
            self.dlg.setWindowTitle(self.plugin_name + f' {self.config.MAPFLOW_ENV}')
        # Display plugin icon in own toolbar
        plugin_button = QAction(plugin_icon, self.plugin_name, self.main_window)
        plugin_button.triggered.connect(self.main)
        self.toolbar.addAction(plugin_button)
        self.project.readProject.connect(self.set_layer_group)
        self.project.readProject.connect(self.filter_bad_rasters)
        # list(filter(bool, [self.dlg.rasterCombo.layer(index) for index in range(self.dlg.rasterCombo.count())]))
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
        for dlg in self.dlg, self.dlg_login, self.dlg_provider:
            dlg.close()
        del self.toolbar
        self.settings.setValue('metadataMinIntersection', self.dlg.minIntersection.value())
        self.settings.setValue('metadataMaxCloudCover', self.dlg.maxCloudCover.value())
        self.settings.setValue('metadataFrom', self.dlg.metadataFrom.date())
        self.settings.setValue('metadataTo', self.dlg.metadataTo.date())

    def read_mapflow_token(self) -> None:
        """Compose and memorize the user's credentils as Basic Auth."""
        token = self.dlg_login.token.text().strip()
        if token:
            # to add paddind for the token len to be multiple of 4
            token += "=" * ((4 - len(token) % 4) % 4)
            self.log_in(token)

    def log_in(self, token) -> None:
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
            return
        self.http.basic_auth = f'Basic {token}'
        self.http.get(
            url=f'{self.config.SERVER}/projects/{self.config.PROJECT_ID}',
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
        self.dlg.close()
        self.set_up_login_dialog()  # recreate the login dialog
        self.dlg_login.show()  # assume user wants to log into another account

    def default_error_handler(self, response: QNetworkReply) -> bool:
        """Handle general networking errors: offline, timeout, server errors.

        :param response: The HTTP response.
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
            # Wrong token entered - display a message
            elif not self.dlg_login.findChild(QLabel, self.config.INVALID_TOKEN_WARNING_OBJECT_NAME):
                invalid_token_label = QLabel(self.tr('Invalid token'), self.dlg_login)
                invalid_token_label.setObjectName(self.config.INVALID_TOKEN_WARNING_OBJECT_NAME)
                invalid_token_label.setStyleSheet('color: rgb(239, 41, 41);')
                self.dlg_login.layout().insertWidget(1, invalid_token_label, alignment=Qt.AlignCenter)
                new_size = self.dlg_login.width(), self.dlg_login.height() + invalid_token_label.height()
                self.dlg_login.setMaximumSize(*new_size)
                self.dlg_login.setMinimumSize(*new_size)
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
                          'If you are behind a proxy or firewall,\ncheck your QGIS proxy settings.\n'
            ))
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
        error_summary, email_body = get_error_report_body(response=response,
                                                          plugin_version=self.plugin_version,
                                                          error_message_parser=error_message_parser)
        ErrorMessageWidget(parent=QApplication.activeWindow(),
                           text=error_summary,
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
        self.http.get(url=f'{self.server}/projects/{self.config.PROJECT_ID}/processings',
                      callback=self.get_processings_callback,
                      use_default_error_handler=False)
        self.processing_fetch_timer.start()

    def log_in_callback(self, response: QNetworkReply) -> None:
        """Fetch user info, models and processings.

        :param response: The HTTP response.
        """
        # Show history of processings at startup to get non-empty table immediately, and setup the table update
        self.setup_processings_table()
        # Set up the UI with the received data
        response = json.loads(response.readAll().data())
        self.update_processing_limit()
        self.is_premium_user = response['user']['isPremium']
        self.on_provider_change(self.dlg.rasterCombo.currentText())
        self.aoi_area_limit = response['user']['aoiAreaLimit'] * 1e-6
        # We skip SENTINEL WDs if sentinel is not enabled (normally, it should be not)
        # wds along with ids in the format: {'model_name': 'workflow_def_id'}
        self.workflow_defs = {
            workflow['name']: WorkflowDef(**workflow)
            for workflow in response['workflowDefs']
        }
        self.dlg.modelCombo.clear()
        self.dlg.modelCombo.addItems(name for name in self.workflow_defs
                                     if self.config.ENABLE_SENTINEL or name not in self.config.SENTINEL_WD_NAMES)
        self.dlg.modelCombo.setCurrentText(self.config.DEFAULT_MODEL)
        self.dlg.rasterCombo.setCurrentText('Mapbox')
        self.calculate_aoi_area_use_image_extent(self.dlg.useImageExtentAsAoi.isChecked())
        self.dlg.processingsTable.setColumnHidden(self.config.PROCESSING_TABLE_ID_COLUMN_INDEX, True)
        self.dlg.restoreGeometry(self.settings.value('mainDialogState', b''))
        # Authenticate and keep user logged in
        self.logged_in = True
        self.dlg_login.close()

        # setup window title for different envs and project
        self.dlg.setWindowTitle(helpers.generate_plugin_header(self.plugin_name,
                                                               self.config.MAPFLOW_ENV,
                                                               response.get("name", "")))
        self.dlg.setup_for_billing(self.billing_type)
        self.dlg.show()
        self.user_status_update_timer.start()
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
        token = self.settings.value('token')
        if self.logged_in:
            self.dlg.show()
            self.update_processing_limit()
            self.user_status_update_timer.start()
            self.app_startup_user_update_timer.start()
        elif token:  # token saved
            self.http.basic_auth = f'Basic {token}'
            self.log_in(token)
        else:
            self.set_up_login_dialog()
            self.dlg_login.show()
