import json
import os.path
import tempfile
from base64 import b64encode, b64decode
from typing import List, Optional, Union
from datetime import datetime  # processing creation datetime formatting
from configparser import ConfigParser  # parse metadata.txt -> QGIS version check (compatibility)

from osgeo import gdal
from PyQt5.QtXml import QDomDocument
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest, QHttpMultiPart, QHttpPart
from PyQt5.QtCore import (
    QDate, QObject, QCoreApplication, QTimer, QTranslator, Qt, QFile, QIODevice, qVersion,
    QTextStream, QByteArray
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

from .dialogs.dialogs import MainDialog, LoginDialog, ErrorMessage
from .dialogs.provider_dialog import ProviderDialog
from .http import Http, update_processing_limit
from . import helpers, config
from .entity.processing import parse_processings_request, Processing, ProcessingHistory, updated_processings
from .entity.provider import (Provider,
                              MaxarProvider,
                              MaxarProxyProvider,
                              ProvidersDict,
                              SentinelProvider,
                              create_provider)

from .functional.geometry import clip_aoi_to_image_extent
from .errors import ErrorMessageList
from .layer_utils import generate_xyz_layer_definition


class Mapflow(QObject):

    """This class represents the plugin. It is instantiated by QGIS."""

    def __init__(self, iface) -> None:
        """Initialize the plugin.

        :param iface: an instance of the QGIS interface.
        """
        # Save refs to key variables used throughout the plugin
        self.iface = iface
        self.main_window = self.iface.mainWindow()
        super().__init__(self.main_window)
        self.project = QgsProject.instance()
        self.message_bar = self.iface.messageBar()
        self.plugin_dir = os.path.dirname(__file__)
        self.temp_dir = tempfile.gettempdir()
        self.plugin_name = config.PLUGIN_NAME  # aliased here to be overloaded in submodules
        # Settings will be used to store credentials and various UI customizations
        self.settings = QgsSettings()
        # Get the server environment to connect to (for admins)
        mapflow_env = self.settings.value('variables/mapflow_env') or 'production'
        self.server = config.SERVER.format(env=mapflow_env)
        # By default, plugin adds layers to a group unless user explicitly deletes it
        self.add_layers_to_group = True
        self.layer_tree_root = self.project.layerTreeRoot()
        # Set up authentication flags
        self.logged_in = False
        # Store user's current processing
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
        # Check plugin version for compatibility with Processing API
        self.http.get(
            url=f'{self.server}/version',
            callback=self.check_plugin_version_callback,
            use_default_error_handler=False  # ignore errors
        )
        self.calculator = QgsDistanceArea()
        # RESTORE LATEST FIELD VALUES & OTHER ELEMENTS STATE
        self.dlg.outputDirectory.setText(self.settings.value('outputDir'))
        self.dlg.maxZoom.setValue(int(self.settings.value('maxZoom') or config.DEFAULT_ZOOM))

        # load providers from settings
        try:
            self.providers, errors = ProvidersDict.from_settings(settings=self.settings, env=mapflow_env)
        except Exception as e:
            self.alert(self.tr("Error during loading the data providers: {e}").format(str(e)))
        if errors:
            self.alert(self.tr('We failed to import providers {errors} from the settings. Please add them again').format(errors))
        self.update_providers()
        self.dlg.rasterCombo.setCurrentText('Mapbox')  # otherwise SW will be set due to combo sync
        self.dlg.minIntersection.setValue(int(self.settings.value('metadataMinIntersection', 0)))
        self.dlg.maxCloudCover.setValue(int(self.settings.value('metadataMaxCloudCover', 100)))
        # Set default metadata dates
        today = QDate.currentDate()
        self.dlg.metadataFrom.setDate(self.settings.value('metadataFrom', today.addMonths(-6)))
        self.dlg.metadataTo.setDate(self.settings.value('metadataTo', today))
        # Hide the ID columns as only needed for table operations, not the user
        self.dlg.processingsTable.setColumnHidden(config.PROCESSING_TABLE_ID_COLUMN_INDEX, True)
        # SET UP SIGNALS & SLOTS
        imagery_sources = [
            self.dlg.rasterCombo.layer(index)
            for index in range(self.dlg.rasterCombo.count())
        ]
        self.filter_non_tif_rasters(list(filter(bool, imagery_sources)))
        self.dlg.modelCombo.currentTextChanged.connect(self.set_available_imagery_sources)
        # Memorize dialog element sizes & positioning
        self.dlg.finished.connect(self.save_dialog_state)
        # Connect buttons
        self.dlg.logoutButton.clicked.connect(self.logout)
        self.dlg.selectOutputDirectory.clicked.connect(self.select_output_directory)
        self.dlg.selectTif.clicked.connect(self.select_tif)
        # (Dis)allow the user to use raster extent as AOI
        self.dlg.rasterCombo.layerChanged.connect(self.toggle_processing_checkboxes)
        self.dlg.rasterCombo.layerChanged.connect(self.disallow_local_rasters_with_sentinel)
        self.dlg.rasterCombo.currentTextChanged.connect(self.toggle_processing_checkboxes)
        self.dlg.useImageExtentAsAoi.toggled.connect(self.toggle_polygon_combos)
        self.dlg.startProcessing.clicked.connect(self.create_processing)
        # Sync polygon layer combos
        self.dlg.polygonCombo.layerChanged.connect(self.dlg.maxarAoiCombo.setLayer)
        self.dlg.maxarAoiCombo.layerChanged.connect(self.dlg.polygonCombo.setLayer)
        # Calculate AOI size
        self.dlg.polygonCombo.layerChanged.connect(self.calculate_aoi_area_polygon_layer)
        self.dlg.rasterCombo.layerChanged.connect(self.calculate_aoi_area_raster)
        self.dlg.useImageExtentAsAoi.toggled.connect(self.calculate_aoi_area_use_image_extent)
        self.monitor_polygon_layer_feature_selection([
            self.project.mapLayer(layer_id) for layer_id in self.project.mapLayers(validOnly=True)
        ])
        self.project.layersAdded.connect(self.monitor_polygon_layer_feature_selection)
        self.project.layersAdded.connect(self.filter_non_tif_rasters)
        # Processings
        self.dlg.processingsTable.cellDoubleClicked.connect(self.download_results)
        self.dlg.deleteProcessings.clicked.connect(self.delete_processings)
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
        self.dlg.metadataTable.itemSelectionChanged.connect(self.sync_table_selection_with_image_id_and_layer)
        self.dlg.getMetadata.clicked.connect(self.get_metadata)
        self.dlg.metadataTable.cellDoubleClicked.connect(self.preview)
        self.dlg.providerCombo.currentTextChanged.connect(self.on_provider_change)
        # Poll processings
        self.processing_fetch_timer = QTimer(self.dlg)
        self.processing_fetch_timer.setInterval(config.PROCESSING_TABLE_REFRESH_INTERVAL * 1000)
        self.processing_fetch_timer.timeout.connect(
            lambda: self.http.get(
                url=f'{self.server}/processings',
                callback=self.get_processings_callback,
                use_default_error_handler=False  # ignore errors to prevent repetitive alerts
            )
        )
        self.error_messages = ErrorMessageList()
        # Add layer menu
        self.add_layer_menu = QMenu()
        self.create_aoi_from_map_action = QAction(self.tr("Create new AOI layer from map extent"))
        self.add_aoi_from_file_action = QAction(self.tr("Add AOI from vector file"))
        self.aoi_layer_counter = 0
        self.setup_add_layer_menu()
        self.dlg.imageId.textChanged.connect(self.set_image_id_label)

    def set_image_id_label(self, text):
        if text:
            self.dlg.imageId_label.setText(self.tr('Selected Image ID: {text}').format(text=text))
        else:
            self.dlg.imageId_label.setText("")

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

    def filter_non_tif_rasters(self, _: List[QgsMapLayer]) -> None:
        """Leave only GeoTIFF layers in the Imagery Source combo box."""
        # (!) Instead of going thru all project layers each time
        # it'd be better to filter the new layers, then add them to
        # the already filtered ones like rasterCombo.exceptedLayerList() + new_layers
        # but calling exceptedLayerList() crashes when it contains deleted layers
        self.dlg.rasterCombo.setExceptedLayerList([
            layer for layer in self.project.mapLayers().values() 
            if layer.type() == QgsMapLayerType.RasterLayer 
            and not (
                layer.crs().isValid()
                and os.path.splitext(layer.dataProvider().dataSourceUri())[-1] in ('.tif', '.tiff')
                and os.path.exists(layer.dataProvider().dataSourceUri())
                and os.path.getsize(layer.publicSource()) / 2**20 < config.MAX_TIF_SIZE
            )
        ])

    def disallow_local_rasters_with_sentinel(self, raster: QgsRasterLayer) -> None:
        """Override local raster selection if the model is Sentinel-2 Fields."""
        if raster and self.dlg.modelCombo.currentText() in config.SENTINEL_WD_NAMES:
            self.alert(self.tr(
                "Currently, Mapflow doesn't support uploading own Sentinel-2 imagery. "
                'To process Sentinel-2, go to the Providers tab andSENTINEL_WD_NAME either search for your image '
                'in the catalog or paste its ID in the Image ID field.'
            ))
            self.dlg.rasterCombo.setCurrentText(config.SENTINEL_OPTION_NAME)

    def set_available_imagery_sources(self, wd: str) -> None:
        """Restrict the list of imagery sources according to the selected model."""
        sentinel_providers = [provider.name for provider in self.providers.values() if
                              isinstance(provider, SentinelProvider)]
        web_providers = [provider.name for provider in self.providers.values() if
                         not isinstance(provider, SentinelProvider)]
        current_sources = self.dlg.rasterCombo.additionalItems()
        if wd in config.SENTINEL_WD_NAMES and not set(current_sources) == set(sentinel_providers):
            # Prevent disallow_local_rasters_with_sentinel() from being triggered
            self.dlg.rasterCombo.blockSignals(True)
            self.dlg.rasterCombo.setAdditionalItems(sentinel_providers)
            if sentinel_providers:
                self.dlg.rasterCombo.setCurrentText(sentinel_providers[0])
            self.dlg.providerCombo.clear()
            self.dlg.providerCombo.addItems(sentinel_providers)
            self.dlg.rasterCombo.blockSignals(False)
        elif not set(current_sources) == set(web_providers):
            # skip update in case source list did not change.
            # This prevents the current selected item from being discarded
            self.dlg.rasterCombo.setAdditionalItems(web_providers)
            self.dlg.providerCombo.clear()
            self.dlg.providerCombo.addItems(web_providers)

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
        min_intersection_size = self.calculator.measureArea(aoi) * (min_intersection/100)
        aoi = QgsGeometry.createGeometryEngine(aoi.constGet())
        aoi.prepareGeometry()
        # Get attributes
        if self.dlg.providerCombo.currentText() == config.SENTINEL_OPTION_NAME:
            id_column_index = config.SENTINEL_ID_COLUMN_INDEX
            datetime_column_index = config.SENTINEL_DATETIME_COLUMN_INDEX
            cloud_cover_column_index = config.SENTINEL_CLOUD_COLUMN_INDEX
        else:  # Maxar
            id_column_index = config.MAXAR_ID_COLUMN_INDEX
            datetime_column_index = config.MAXAR_DATETIME_COLUMN_INDEX
            cloud_cover_column_index = config.MAXAR_CLOUD_COLUMN_INDEX
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
        self.dlg_login = LoginDialog(self.main_window)
        env = QgsSettings().value('variables/mapflow_env') or 'production'
        if env == 'production':
            self.dlg_login.setWindowTitle(self.plugin_name + ' - ' + self.tr('Log in'))
        else:
            self.dlg_login.setWindowTitle(self.plugin_name + f' {env} - ' + self.tr('Log in'))
        self.dlg_login.logIn.clicked.connect(self.read_mapflow_token)

    def toggle_polygon_combos(self, use_image_extent: bool) -> None:
        """Disable polygon combos when Use image extent is checked.

        :param use_image_extent: Whether the corresponding checkbox is checked
        """
        self.dlg.polygonCombo.setEnabled(not use_image_extent)
        self.dlg.maxarAoiCombo.setEnabled(not use_image_extent)

    def limit_zoom_auth_toggled(self) -> None:
        """
        Limit zoom for Maxar when our account is to be used.
        """
        current_provider = self.providers.get(self.dlg.providerCombo.currentText())
        if isinstance(current_provider, MaxarProxyProvider):
            max_zoom = config.MAXAR_MAX_FREE_ZOOM
            value = max_zoom
        else:
            max_zoom = config.MAX_ZOOM
            # Forced to int bc somehow used to be stored as str, so for backward compatability
            value = int(self.settings.value('maxZoom', config.DEFAULT_ZOOM))
        self.dlg.maxZoom.setMaximum(max_zoom)
        self.dlg.maxZoom.setValue(value)

    def on_provider_change(self, provider_name: str) -> None:
        """Adjust max and current zoom, and update the metadata table when user selects another
        provider.

        :param provider: The currently selected provider
        """
        provider = self.providers.get(provider_name)

        self.dlg.metadataTable.clear()
        self.dlg.imageId.clear()

        more_button = self.dlg.findChild(QPushButton, config.METADATA_MORE_BUTTON_OBJECT_NAME)
        if more_button:
            self.dlg.layoutMetadataTable.removeWidget(more_button)
            more_button.deleteLater()
        image_id_tooltip = self.tr(
            'If you already know which {provider_name} image you want to process,\n'
            'simply paste its ID here. Otherwise, search suitable images in the catalog below.'
        ).format(provider_name=provider_name)

        if isinstance(provider, SentinelProvider):
            is_max_zoom_enabled = False
            columns = config.SENTINEL_ATTRIBUTES
            hidden_column_index = len(config.SENTINEL_ATTRIBUTES) - 1
            sort_by = config.SENTINEL_DATETIME_COLUMN_INDEX
            enabled = True
            image_id_placeholder = self.tr('e.g. S2B_OPER_MSI_L1C_TL_VGS4_20220209T091044_A025744_T36SXA_N04_00')
            additional_filters_enabled = True
        elif isinstance(provider, (MaxarProvider, MaxarProxyProvider)):
            is_max_zoom_enabled = True
            columns = config.MAXAR_METADATA_ATTRIBUTES
            hidden_column_index = None
            sort_by = config.MAXAR_DATETIME_COLUMN_INDEX
            enabled = True
            image_id_placeholder = self.tr('e.g. a3b154c40cc74f3b934c0ffc9b34ecd1')
            additional_filters_enabled = True
        else:
            # other providers do not support imagery search,
            # tear down the table and deactivate the panel
            is_max_zoom_enabled = True
            columns = tuple()  # empty
            hidden_column_index = None
            sort_by = None
            enabled = False
            image_id_placeholder = self.tr(f'Leave this field empty for ') + provider_name
            additional_filters_enabled = False
            image_id_tooltip = provider_name + self.tr(f" doesn't allow processing single images.")

        self.limit_zoom_auth_toggled()
        self.dlg.maxZoom.setEnabled(is_max_zoom_enabled)
        self.dlg.metadataFilters.setEnabled(additional_filters_enabled)
        self.dlg.metadataTable.setRowCount(0)
        self.dlg.metadataTable.setColumnCount(len(columns))
        self.dlg.metadataTable.setHorizontalHeaderLabels(columns)
        for col in range(len(columns)):  # reveal any previously hidden columns
            self.dlg.metadataTable.setColumnHidden(col, False)
        if hidden_column_index is not None:  # now hide the relevant ones
            self.dlg.metadataTable.setColumnHidden(hidden_column_index, True)
        if sort_by is not None:
            self.dlg.metadataTable.sortByColumn(sort_by, Qt.DescendingOrder)
        self.dlg.metadata.setTitle(provider_name + self.tr(' Imagery Catalog'))
        self.dlg.metadata.setEnabled(enabled)
        self.dlg.imageId.setPlaceholderText(image_id_placeholder)
        self.dlg.labelImageId.setToolTip(image_id_tooltip)

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
            self.alert(self.tr("This provider cannot be removed"), QMessageBox.Warning)
            return
        # Ask for confirmation
        elif self.alert(self.tr('Permanently remove {}?').format(provider.name), QMessageBox.Question):
            self.providers.pop(provider_name)
            self.update_providers()

    def edit_provider_callback(self) -> None:
        """Add a web imagery provider or commit edits to an existing one."""
        old_provider = self.dlg_provider.current_provider
        if self.dlg_provider.result:
            new_provider = create_provider(**self.dlg_provider.result)
        else:
            # returned empty provider - i.e nothing was changed
            return

        if not old_provider:
            # we have added new one - without current one
            if new_provider.name in self.providers:
                self.alert(self.tr("Provider name must be unique. {name} already exists, "
                                   "select another or delete/edit existing").format(name=new_provider.name))
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
                                   " select another or delete/edit existing").format(name=new_provider.name))
                self.dlg_provider.show()
                return
            else:
                self.providers.pop(old_provider.name)
                self.providers.update({new_provider.name: new_provider})

        self.update_providers()
        self.dlg.providerCombo.setCurrentText(new_provider.name)

    def add_provider(self) -> None:
        self.dlg_provider.setup(None)

    def edit_provider(self) -> None:
        """Prepare and show the provider edit dialog.
        Is called by the corresponding button.
        """
        name = self.dlg.providerCombo.currentText()
        if self.providers[name].is_default:
            self.alert("This is a default provider, it cannot be edited")
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
        self.dlg.modelCombo.currentTextChanged.emit(self.dlg.modelCombo.currentText())

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
        for layer in filter(helpers.is_polygon_layer, layers):
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
        self.dlg.imageId_label.setText("")

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

    def select_tif(self) -> None:
        """Open a file selection dialog for the user to select a GeoTIFF for processing.

        Is called by clicking the 'selectTif' button in the main dialog.
        """
        dlg = QFileDialog(QApplication.activeWindow(), self.tr('Select GeoTIFF'))
        dlg.setFileMode(QFileDialog.ExistingFile)
        dlg.setMimeTypeFilters(['image/tiff'])
        if dlg.exec():
            path = dlg.selectedFiles()[0]
            layer = QgsRasterLayer(path, os.path.splitext(os.path.basename(path))[0])
            self.add_layer(layer)
            self.dlg.rasterCombo.setLayer(layer)

    def get_metadata(self) -> None:
        """Metadata is image footprints with attributes like acquisition date or cloud cover."""
        self.dlg.metadataTable.clearContents()
        self.dlg.metadataTable.setRowCount(0)
        more_button = self.dlg.findChild(QPushButton, config.METADATA_MORE_BUTTON_OBJECT_NAME)
        if more_button:
            self.dlg.layoutMetadataTable.removeWidget(more_button)
            more_button.deleteLater()
        provider = self.providers[self.dlg.providerCombo.currentText()]
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
        if self.calculator.measureArea(aoi_bbox_geom) > config.SKYWATCH_METADATA_MAX_AREA:
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
            self.calculator.measureLength(width) > config.SKYWATCH_METADATA_MAX_SIDE_LENGTH
            or self.calculator.measureLength(height) > config.SKYWATCH_METADATA_MAX_SIDE_LENGTH
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
            config.SENTINEL_OPTION_NAME + ' metadata',
            'memory'
        )
        self.metadata_layer.loadNamedStyle(os.path.join(self.plugin_dir, 'static', 'styles', 'metadata.qml'))
        self.metadata_layer.selectionChanged.connect(self.sync_layer_selection_with_table)
        # Poll processings
        metadata_fetch_timer = QTimer(self.dlg)
        metadata_fetch_timer.setInterval(config.SKYWATCH_POLL_INTERVAL * 1000)
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
            self.report_error(response, self.tr("We couldn't fetch Sentinel metadata"))

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
            table_items = [QTableWidgetItem() for _ in range(len(config.SENTINEL_ATTRIBUTES))]
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
            more_button.setObjectName(config.METADATA_MORE_BUTTON_OBJECT_NAME)
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
        self.report_error(response, self.tr("We couldn't fetch Sentinel metadata"))

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
                                             max_cloud_cover=max_cloud_cover/100,
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
            for col, attr in enumerate(config.MAXAR_METADATA_ATTRIBUTES.values()):
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
        if error == QNetworkReply.ContentAccessDenied:
            self.alert(self.tr('Please, check your credentials'))
        else:
            self.report_error(response, self.tr("We couldn't get metadata from Maxar, error {error}").format(error=error))

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
            config.SENTINEL_ID_COLUMN_INDEX
            if self.dlg.providerCombo.currentText() == config.SENTINEL_OPTION_NAME
            else config.MAXAR_ID_COLUMN_INDEX
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
            config.SENTINEL_ID_COLUMN_INDEX
            if self.dlg.providerCombo.currentText() == config.SENTINEL_OPTION_NAME
            else config.MAXAR_ID_COLUMN_INDEX
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
        provider = self.providers.get(self.dlg.providerCombo.currentText())

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
        if layer and layer.featureCount() > 0:
            features = list(layer.getSelectedFeatures()) or list(layer.getFeatures())
            if len(features) == 1:
                aoi = features[0].geometry()
            else:
                aoi = QgsGeometry.collectGeometry([feature.geometry() for feature in features])
            self.calculate_aoi_area(aoi, layer.crs())
        else:  # empty layer or combo's itself is empty
            self.dlg.labelAoiArea.clear()
            self.aoi = self.aoi_size = None

    def calculate_aoi_area_raster(self, layer: Union[QgsRasterLayer, None]) -> None:
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

        :param aoi: the processing area.
        :param crs: the CRS of the processing area.
        """
        if crs != helpers.WGS84:
            aoi = helpers.to_wgs84(aoi, crs)
        self.aoi = aoi  # save for reuse in processing creation or metadata requests
        # Set ellipsoid to calculate on sphere if the CRS is geographic
        self.calculator.setEllipsoid(helpers.WGS84_ELLIPSOID)
        self.calculator.setSourceCrs(helpers.WGS84, self.project.transformContext())
        self.aoi_size = self.calculator.measureArea(aoi) / 10**6  # sq. m to sq.km
        self.dlg.labelAoiArea.setText(self.tr('Area: {:.2f} sq.km').format(self.aoi_size))

    def delete_processings(self) -> None:
        """Delete one or more processings from the server.

        Asks for confirmation in a pop-up dialog. Multiple processings can be selected.
        Is called by clicking the deleteProcessings ('Delete') button.
        """
        # Pause refreshing processings table to avoid conflicts
        self.processing_fetch_timer.stop()
        selected_ids = [
            self.dlg.processingsTable.item(index.row(), config.PROCESSING_TABLE_ID_COLUMN_INDEX).text()
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
        self.report_error(response, self.tr("Error deleting a processing"))

    def upload_image(self, layer, processing_params=None, mosaic=None):
        """
        if processing_params are None, we do not call processing after upload;
        this is a stub for further data-catalog usage
        Also, mosaic can be specified to upload to specific mosaic
        """
        body = QHttpMultiPart(QHttpMultiPart.FormDataType)
        tif = QHttpPart()
        tif.setHeader(QNetworkRequest.ContentTypeHeader, 'image/tiff')
        tif.setHeader(QNetworkRequest.ContentDispositionHeader, 'form-data; name="file"; filename=""')
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

    def create_processing_from_provider(self, provider, aoi, image_id, params, selected_image):
        provider_params, processing_meta = provider.to_processing_params(image_id=image_id)
        params.update(params=provider_params)
        params['meta'].update(**processing_meta)
        if selected_image:
            if isinstance(provider, (MaxarProvider, MaxarProxyProvider)):
                aoi = self.crop_aoi_with_maxar_image_footprint(aoi, selected_image)
            elif isinstance(provider, SentinelProvider):
                # todo: crop sentinel aoi with image footprint?
                pass
        elif provider.requires_image_id:
            self.alert(self.tr("Provider {} requires selected Image ID").format(provider.name))
        params.update(geometry=json.loads(aoi.asJson()))
        self.post_processing(params)

    def create_processing_from_local_file(self, imagery, aoi, params):
        params['meta'].update(source='tif')
        params['params'].update(source_type='tif')
        params.update(geometry=json.loads(aoi.asJson()))
        self.upload_image(layer=imagery, processing_params=params)

    def check_processing_ui(self):
        processing_name = self.dlg.processingName.text()

        if not processing_name:
            self.alert(self.tr('Please, specify a name for your processing'))
            return False
        use_image_extent_as_aoi = self.dlg.useImageExtentAsAoi.isChecked()
        if not self.aoi:
            if use_image_extent_as_aoi:
                self.alert(self.tr('GeoTIFF has invalid projection'))
            elif self.dlg.polygonCombo.currentLayer():
                self.alert(self.tr('Processing area has invalid projection'))
            else:
                self.alert(self.tr('Please, select an area of interest'))
            return False
        if self.remaining_limit < self.aoi_size:
            if self.plugin_name == 'Mapflow':  # don't alert in TechInspection
                self.alert(self.tr('Processing limit exceeded'))
            return False
        if self.aoi_area_limit < self.aoi_size:
            self.alert(self.tr(
                'Up to {} sq km can be processed at a time. '
                'Try splitting your area(s) into several processings.'
            ).format(self.aoi_area_limit))
            return False
        return True

    def crop_aoi_with_maxar_image_footprint(self, aoi, image_id):
        extent = self.maxar_metadata_footprints[image_id[config.MAXAR_ID_COLUMN_INDEX].text()]
        try:
            aoi = next(clip_aoi_to_image_extent(aoi, extent)).geometry()
        except StopIteration:
            raise ValueError('Image and processing area do not intersect')
        return aoi

    def create_processing(self) -> None:
        """Create and start a processing on the server.

        Is called by clicking the 'Create processing' button.
        """

        # get the data from UI
        processing_name = self.dlg.processingName.text()
        raster_option = self.dlg.rasterCombo.currentText()
        imagery = self.dlg.rasterCombo.currentLayer()
        use_image_extent_as_aoi = self.dlg.useImageExtentAsAoi.isChecked()
        image_id = self.dlg.imageId.text()
        selected_image = self.dlg.metadataTable.selectedItems()
        if not self.check_processing_ui():
            return

        processing_params = {
            'name': processing_name,
            'wdName': self.dlg.modelCombo.currentText(),
            'meta': {  # optional metadata
                'source-app': 'qgis',
                'version': self.plugin_version,
                'source': raster_option.lower()
            },
            'params': {}
        }
        self.message_bar.pushInfo(self.plugin_name, self.tr('Starting the processing...'))
        if imagery:
            layer_extent = QgsFeature()
            layer_extent.setGeometry(helpers.get_layer_extent(imagery))
            if not use_image_extent_as_aoi:
                # If we do not use the layer extent as aoi, we still create it and use it to crop the selected AOI
                try:
                    aoi = next(clip_aoi_to_image_extent(aoi_geometry=self.aoi, extent=layer_extent)).geometry()
                except StopIteration:
                    self.alert(self.tr('Image and processing area do not intersect'))
                    return
            else:
                aoi = self.aoi
            try:
                self.create_processing_from_local_file(imagery,
                                                       aoi=aoi,
                                                       params=processing_params)
            except Exception as e:
                self.alert(self.tr("Could not launch processing! Error: {}.").format(str(e)))
            return
        else:
            provider = self.providers[raster_option]
            if isinstance(provider, MaxarProxyProvider) and not self.is_premium_user:
                ErrorMessage(
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
                self.create_processing_from_provider(provider,
                                                     aoi=self.aoi,
                                                     image_id=image_id,
                                                     params=processing_params,
                                                     selected_image=selected_image)
            except Exception as e:
                self.alert(self.tr("Could not launch processing! Error: {}.").format(str(e)))
            return

    def upload_tif_callback(self, response: QNetworkReply, processing_params: dict) -> None:
        """Start processing upon a successful GeoTIFF upload.

        :param response: The HTTP response.
        :param processing_params: A dictionary with the processing parameters.
        """
        processing_params['params']['url'] = json.loads(response.readAll().data())['url']
        self.post_processing(processing_params)

    def upload_tif_error_handler(self, response: QNetworkReply) -> None:
        """Error handler for GeoTIFF upload request.

        :param response: The HTTP response.
        """
        self.report_error(response, self.tr("We couldn't upload your GeoTIFF"))

    def post_processing(self, request_body: dict) -> None:
        """Submit a processing to Mapflow.

        :param request_body: Processing parameters.
        """
        self.http.post(
            url=f'{self.server}/processings',
            callback=self.post_processing_callback,
            callback_kwargs={'processing_name': request_body['name']},
            error_handler=self.post_processing_error_handler,
            body=json.dumps(request_body).encode()
        )

    def post_processing_error_handler(self, response: QNetworkReply) -> None:
        """Error handler for processing creation requests.

        :param response: The HTTP response.
        """
        self.report_error(response, self.tr('Processing creation failed'))

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
            url=f'{self.server}/processings',
            callback=self.get_processings_callback
        )
        self.http.get(
            url=f'{self.server}/projects/default',
            callback=self.set_processing_limit
        )

    def set_processing_limit(
        self,
        response: Optional[QNetworkReply] = None,
        user: Optional[dict] = None
    ) -> None:
        """Set the user's processing limit as reported by Mapflow."""
        if response:
            user = json.loads(response.readAll().data())['user']
        if user['role'] == 'ADMIN':
            self.remaining_limit = 1e5  # 100K sq.km
        else:
            self.remaining_limit = (user['areaLimit'] - user['processedArea']) * 1e-6
        if self.plugin_name == 'Mapflow':
            self.dlg.remainingLimit.setText(
                self.tr('Processing limit: {} sq.km').format(round(self.remaining_limit, 2))
            )

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
        layer = QgsRasterLayer(f.name, f'{config.SENTINEL_OPTION_NAME} {datetime_}', 'gdal')
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
        self.report_error(response, self.tr('Error previewing Sentinel imagery'))

    def preview_sentinel(self, image_id):
        selected_cells = self.dlg.metadataTable.selectedItems()
        if selected_cells:
            datetime_ = selected_cells[config.SENTINEL_DATETIME_COLUMN_INDEX]
            url = self.dlg.metadataTable.item(datetime_.row(), config.SENTINEL_PREVIEW_COLUMN_INDEX).text()
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
        attrs = tuple(config.MAXAR_METADATA_ATTRIBUTES.values())
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
        username = provider.credentials.login
        password = provider.credentials.password
        max_zoom = self.dlg.maxZoom.value()
        layer_name = provider.name
        url = provider.preview_url(image_id=image_id)
        if not url:
            self.alert(f"Provider {provider.name} does not support previews!")
            return
        if provider.is_proxy:
            username = self.username
            password = self.password
            uri = generate_xyz_layer_definition(url,
                                                username, password,
                                                max_zoom, image_id)
            extent = self.maxar_extent(image_id)
            layer_name = self.maxar_layer_name(layer_name, image_id)
        else:
            uri = generate_xyz_layer_definition(url,
                                                username, password,
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
        provider_name = self.dlg.providerCombo.currentText()
        image_id = self.dlg.imageId.text()
        provider = self.providers[provider_name]
        if isinstance(provider, SentinelProvider):
            self.preview_sentinel(image_id=image_id)
        elif not provider.preview_url:
            self.alert(self.tr("Preview is unavailable for the provider {}").format(provider_name))
        else:  # XYZ providers
            self.preview_xyz(provider=provider, image_id=image_id)

    def download_results(self, row: int) -> None:
        """Download and display processing results along with the source raster, if available.

        Results will be downloaded into the user's output directory.
        If it's unset, the user will be prompted to select one.
        Unfinished or failed processings yield partial or no results.

        Is called by double-clicking on a row in the processings table.

        :param row: int Row number in the processings table (0-based)
        """
        if self.check_if_output_directory_is_selected():
            pid = self.dlg.processingsTable.item(row, config.PROCESSING_TABLE_ID_COLUMN_INDEX).text()
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
        processing = next(filter(lambda p: p.id_ == pid, self.processings))
        # Avoid overwriting existing files by adding (n) to their names
        output_path = os.path.join(self.dlg.outputDirectory.text(), processing.name)
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
            config.STYLES.get(processing.workflow_def, 'default') + '.qml'
        ))
        # Add the source raster (COG) if it has been created
        raster_url = processing.raster_layer.get('tileUrl')
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
        # Set image extent explicitly because as XYZ, it doesn't have one by default
        self.http.get(
            url=f'{self.server}/processings/{pid}/aois',
            callback=self.set_raster_extent,
            callback_kwargs={
                'vector': results_layer,
                'raster': raster
            },
            error_handler=self.set_raster_extent_error_handler
        )

    def download_results_error_handler(self, response: QNetworkReply) -> None:
        """Error handler for downloading processing results.

        :param response: The HTTP response.
        """
        self.report_error(response, self.tr('Error downloading results'))

    def set_raster_extent(
        self,
        response: QNetworkReply,
        vector: QgsVectorLayer,
        raster: QgsRasterLayer
    ) -> None:
        """Set processing raster extent upon successfully requesting the processing's AOI.

        :param response: The HTTP response.
        :param vector: The downloaded feature layer.
        :param response: The downloaded raster which was used for processing.
        """
        with open(os.path.join(self.temp_dir, os.urandom(32).hex()), 'w') as f:
            json.dump({
                'type': 'FeatureCollection',
                'features': json.loads(response.readAll().data())
            }, f)
        extent = QgsGeometry.fromRect(QgsVectorLayer(f.name, '', 'ogr').extent())
        raster.setExtent(helpers.from_wgs84(extent, raster.crs()).boundingBox())
        # Add the layers to the project
        self.add_layer(raster)
        self.add_layer(vector)
        self.iface.zoomToActiveLayer()

    def set_raster_extent_error_handler(self, response: QNetworkReply) -> None:
        """Error handler for processing AOI requests.

        :param response: The HTTP response.
        """
        self.report_error(response, self.tr('Error loading results'))

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

        env = QgsSettings().value('variables/mapflow_env') or 'production'
        processing_history = self.settings.value('processings')
        user_processing_history = ProcessingHistory.from_settings(processing_history.get(env, {}).get(self.username, {}))
        # get updated processings (newly failed and newly finished) and updated user processing history
        failed_processings, finished_processings, user_processing_history = updated_processings(processings, user_processing_history)

        if failed_processings:
            # this means that some of processings have failed since last update and the limit must have been returned
            update_processing_limit()
        self.alert_failed_processings(failed_processings)
        self.alert_finished_processings(finished_processings)

        self.update_processing_table(processings)
        self.processings = processings

        try:  # use try-except bc this will only error once
            processing_history[env][self.username] = user_processing_history.asdict()
        except KeyError:  # history for the current env hasn't been initialized yet
            processing_history[env] = {self.username: user_processing_history.asdict()}
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
                self.tr(' failed with error:\n') + proc.error_message(self.error_messages),
                QMessageBox.Critical)
        elif 1 < len(failed_processings) < 10:
            # If there are more than one failed processing, we will not
            self.alert(
                '{} processings failed: \n'.format(len(failed_processings)) +
                '\n'.join((proc.name for proc in failed_processings)) +
                'See tooltip over the processings table for error details',
                QMessageBox.Critical)
        else:  # >= 10
            self.alert(
                '{} processings failed: \n'.format(len(failed_processings)) +
                'See tooltip over the processings table for error details',
                QMessageBox.Critical)

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
            self.alert(
                '{} processings finished: \n'.format(len(finished_processings)) +
                '\n'.join((proc.name for proc in finished_processings)) +
                '\n Double-click it in the table to download the results',
                QMessageBox.Information,
                blocking=False)
        else:  # >= 10
            self.alert(
                '{} processings finished. \n '
                'Double-click it in the table to download the results'.format(len(finished_processings)),
                QMessageBox.Information,
                blocking=False)

    def update_processing_table(self, processings: List[Processing]):
        # UPDATE THE TABLE
        # Memorize the selection to restore it after table update
        selected_processings = [
            index.data() for index in self.dlg.processingsTable.selectionModel().selectedIndexes()
            if index.column() == config.PROCESSING_TABLE_ID_COLUMN_INDEX
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
            for col, attr in enumerate(config.PROCESSING_ATTRIBUTES):
                table_item = QTableWidgetItem()
                table_item.setData(Qt.DisplayRole, processing_dict[attr])
                if proc.status == 'FAILED':
                    table_item.setToolTip(proc.error_message(self.error_messages))
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
        mapflow_env = QgsSettings().value('variables/mapflow_env') or 'production'
        if mapflow_env == 'production':
            self.dlg.setWindowTitle(self.plugin_name)
        else:
            self.dlg.setWindowTitle(self.plugin_name + f' {mapflow_env}')
        # Display plugin icon in own toolbar
        icon = QIcon(os.path.join(self.plugin_dir, 'icon.png'))
        plugin_button = QAction(icon, self.plugin_name, self.main_window)
        plugin_button.triggered.connect(self.main)
        self.toolbar.addAction(plugin_button)
        self.project.readProject.connect(self.set_layer_group)
        self.project.readProject.connect(lambda: self.filter_non_tif_rasters(
            list(filter(bool, [self.dlg.rasterCombo.layer(index) for index in range(self.dlg.rasterCombo.count())]))
        ))
        self.dlg.processingsTable.sortByColumn(config.PROCESSING_TABLE_SORT_COLUMN_INDEX, Qt.DescendingOrder)

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
        for dlg in self.dlg, self.dlg_login, self.dlg_provider:
            dlg.close()
        del self.toolbar
        self.settings.setValue('metadataMinIntersection', self.dlg.minIntersection.value())
        self.settings.setValue('metadataMaxCloudCover', self.dlg.maxCloudCover.value())
        self.settings.setValue('metadataFrom', self.dlg.metadataFrom.date())
        self.settings.setValue('metadataTo', self.dlg.metadataTo.date())

    def read_mapflow_token(self) -> None:
        """Compose and memorize the user's credentils as Basic Auth."""
        self.mapflow_auth = f'Basic {self.dlg_login.token.text()}'
        self.http.basic_auth = self.mapflow_auth
        self.log_in()

    def log_in(self) -> None:
        """Log into Mapflow."""
        mapflow_env = QgsSettings().value('variables/mapflow_env') or 'production'
        self.server = config.SERVER.format(env=mapflow_env)
        self.http.get(
            url=f'{self.server}/projects/default',
            callback=self.log_in_callback,
            error_handler=self.log_in_error_handler
        )

    def logout(self) -> None:
        """Close the plugin and clear credentials from cache."""
        self.processing_fetch_timer.stop()
        self.logged_in = False
        self.dlg.close()
        self.set_up_login_dialog()  # recreate the login dialog
        self.dlg_login.show()  # assume user wants to log into another account

    def log_in_error_handler(self, response: QNetworkReply) -> None:
        """Error handler for the login request.

        :param response: The HTTP response.
        """
        self.report_error(response, self.tr("Can't log in to Mapflow"))

    def default_error_handler(self, response: QNetworkReply) -> bool:
        """Handle general networking errors: offline, timeout, server errors.

        :param response: The HTTP response.
        Returns True if the error has been handled, otherwise returns False.
        """
        error = response.error()
        service = 'Mapflow' if 'mapflow' in response.request().url().authority() else 'SecureWatch'
        if error == QNetworkReply.AuthenticationRequiredError:  # invalid/empty credentials
            # Prevent deadlocks
            if self.logged_in:  # token re-issued during a plugin session
                self.logout()
            elif self.settings.value('token'):  # env changed w/out logging out (admin)
                self.dlg_login.show()
            # Wrong token entered - display a message
            elif not self.dlg_login.findChild(QLabel, config.INVALID_TOKEN_WARNING_OBJECT_NAME):
                invalid_token_label = QLabel(self.tr('Invalid token'), self.dlg_login)
                invalid_token_label.setObjectName(config.INVALID_TOKEN_WARNING_OBJECT_NAME)
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
            self.report_error(response, self.tr(
                service + ' is not responding. Please, try again.\n\n'
                'If you are behind a proxy or firewall,\ncheck your QGIS proxy settings.\n'
            ))
            return True
        elif error == QNetworkReply.HostNotFoundError:  # offline
            self.alert(self.tr(service + ' requires Internet connection'))
            return True
        elif error in (
            QNetworkReply.UnknownNetworkError,
            QNetworkReply.ProxyConnectionRefusedError,
            QNetworkReply.ProxyConnectionClosedError,
            QNetworkReply.ProxyNotFoundError,
            QNetworkReply.ProxyTimeoutError,
            QNetworkReply.ProxyAuthenticationRequiredError,
        ):
            self.report_error(response, self.tr('Proxy error. Please, check your proxy settings.'))
            return True
        elif error == QNetworkReply.ContentAccessDenied:
            self.report_error(response, self.tr("This operation is forbidden for your account, contact us"))
            return True
        else:
            self.report_error(response, f"Unknown error: {error}")
        return False

    def report_error(self, response: QNetworkReply, title: str = None):
        """Prepare and show an error message for the supplied response.

        :param response: The HTTP response.
        :param title: The error message's title.
        """
        if response.error() == QNetworkReply.OperationCanceledError:
            error_summary = error_text = 'Request timed out'
        else:
            response_body = response.readAll().data().decode()
            try:  # handled standardized backend exception ({"code": <int>, "message": <str>})
                error_summary = error_text = json.loads(response_body)['message']
            except:  # unhandled error - plain text
                error_summary = self.tr('Unknown error')
                error_text = response_body
        report = {
            'Error summary': error_summary,
            'URL': response.request().url().toDisplayString(),
            'HTTP code': response.attribute(QNetworkRequest.HttpStatusCodeAttribute),
            'Qt code': response.error(),
            'Plugin version': self.plugin_version,
            'QGIS version': Qgis.QGIS_VERSION,
            'Qt version': qVersion(),
            'Error message': error_text[:5000]  # too long body => 400 (not sure what's the limit exactly)
        }
        email_body = '%0a'.join(f'{key}: {value}' for key, value in report.items())
        ErrorMessage(QApplication.activeWindow(), error_summary, title, email_body).show()

    def log_in_callback(self, response: QNetworkReply) -> None:
        """Fetch user info, models and processings.

        :param response: The HTTP response.
        """
        # Fetch processings at startup and start the timer to keep fetching them afterwards
        self.http.get(url=f'{self.server}/processings', callback=self.get_processings_callback)
        self.processing_fetch_timer.start()
        # Set up the UI with the received data
        response = json.loads(response.readAll().data())
        user = response['user']
        self.set_processing_limit(user=user)
        self.is_premium_user = user['isPremium']
        self.on_provider_change(self.dlg.providerCombo.currentText())
        self.aoi_area_limit = response['user']['aoiAreaLimit'] * 1e-6
        self.wds = [wd['name'] for wd in response['workflowDefs']]
        self.dlg.modelCombo.clear()
        self.dlg.modelCombo.addItems(self.wds)
        self.dlg.modelCombo.setCurrentText(config.DEFAULT_MODEL)
        self.dlg.rasterCombo.setCurrentText('Mapbox')
        self.calculate_aoi_area_use_image_extent(self.dlg.useImageExtentAsAoi.isChecked())
        self.dlg.processingsTable.setColumnHidden(config.PROCESSING_TABLE_ID_COLUMN_INDEX, True)
        self.dlg.restoreGeometry(self.settings.value('mainDialogState', b''))
        # Authenticate and keep user logged in
        self.logged_in = True
        token = self.mapflow_auth.split()[1]
        self.settings.setValue('token', token)
        try:
            self.username, self.password = b64decode(token).decode().split(':')
        except:  # incorrect padding
            self.username, self.password = b64decode(token + '==').decode().split(':')
        self.dlg_login.close()
        # setup window title for different envs
        mapflow_env = QgsSettings().value('variables/mapflow_env') or 'production'
        if mapflow_env == 'production':
            self.dlg.setWindowTitle(self.plugin_name)
        else:
            self.dlg.setWindowTitle(self.plugin_name + f' {mapflow_env}')

        self.dlg.show()

    def check_plugin_version_callback(self, response: QNetworkReply) -> None:
        """Inspect the backend version and show a warning if it is incompatible w/ the plugin.

        :param response: The HTTP response.
        """
        """
        
        server_version = str(response.readAll().data())
        if server_version == "1":
            # Old version, legacy check, all OK
            return
        
        
        server_version = server_version.split('.')
        if len(server_version) != 3:
            level = 'error'
            message = self.tr('Server returned version in unexpected format. Please upgrade your plugin version contact us')
        elif server_version == self.plugin_version:
            # New versioning, all OK
        """

        if int(response.readAll().data()) > 1:
            # Major version change
            self.alert(
                self.tr(
                    'There is a new version of Mapflow for QGIS available.\n'
                    'Please, upgrade to make sure everything works as expected. '
                    'Go to Plugins -> Manage and Install Plugins -> Upgradable.'
                ),
                QMessageBox.Warning
            )


    def tr(self, message: str) -> str:
        """Localize a UI element text.
        :param message: A text to translate
        """
        # Don't use self.plugin_name as context since it'll be overriden in supermodules
        return QCoreApplication.translate(config.PLUGIN_NAME, message)


    def main(self) -> None:
        """Plugin entrypoint."""
        token = self.settings.value('token')
        if self.logged_in:
            self.dlg.show()
        elif token:  # token saved
            self.mapflow_auth = f'Basic {token}'
            self.http.basic_auth = self.mapflow_auth
            self.log_in()
        else:
            self.set_up_login_dialog()
            self.dlg_login.show()




