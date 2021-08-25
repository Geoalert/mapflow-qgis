import json
import os.path
from uuid import UUID
from configparser import ConfigParser
from typing import Callable, List, Dict, Optional, Union

import requests
from dateutil.parser import parse as parse_datetime  # can't be imported otherwise
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from qgis.core import *
from qgis.gui import *
from qgis import processing

from .dialogs import MainDialog, LoginDialog, ConnectIdDialog, CustomProviderDialog
from .workers import ProcessingFetcher, ProcessingCreator
from . import helpers, config


MAXAR_METADATA_ATTRIBUTES = ('featureId', 'sourceUnit', 'productType', 'colorBandOrder', 'cloudCover', 'formattedDate')
MAXAR_METADATA_FEATURE_ID_COLUMN_INDEX = MAXAR_METADATA_ATTRIBUTES.index('featureId')
ID_COLUMN_INDEX: int = 5  # processings table


class Mapflow:
    """This class represents the plugin.

    It is instantiated by QGIS and shouldn't be used directly.

    Instance attributes:
    iface: an instance of the QGIS interface used for various UI ops
    main_window: QGIS main window; all icons, widgets and threads will have it as their parent
    dlg: the main dialog
    dlg_login: the login dialog
    dlg_connect_id: a tiny dialog for editing Maxar's connect IDs
    server: the Mapflow URL
    logged_in: a flag used to bypass the login dialog
    toolbar: the plugin uses its own toolbar
    project: current QGIS project
    settings: QGIS settings used for storing credentials and user preferences
    actions: the plugin's toolbar buttons
    translator: a translator used to localize the UI
    plugin_dir: the plugin's top-level directory
    """

    def __init__(self, iface: QgisInterface) -> None:
        """Initialize the plugin.

        :param iface: an instance of the QGIS interface.
        """
        # Save refs to key variables used throughout the plugin
        self.iface = iface
        self.main_window = iface.mainWindow()
        self.project = QgsProject.instance()
        self.plugin_dir = os.path.dirname(__file__)
        self.plugin_name = config.PLUGIN_NAME  # aliased here to be overloaded in submodules
        # Init toolbar and toolbar buttons
        self.actions = []
        self.toolbar = self.iface.addToolBar(self.plugin_name)
        self.toolbar.setObjectName(self.plugin_name)
        # QGIS Settings will be used to store user credentials and various UI element state
        self.settings = QgsSettings()
        # Create a namespace for the plugin settings
        self.settings.beginGroup(self.plugin_name.lower())
        # Translation
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n', f'mapflow_{locale}.qm')
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)
        # Init dialogs
        self.dlg = MainDialog(self.main_window)
        self.dlg_login = LoginDialog(self.main_window)
        self.dlg_connect_id = ConnectIdDialog(self.main_window)
        self.dlg_custom_provider = CustomProviderDialog(self.main_window)
        self.red_border_style = 'border-color: rgb(239, 41, 41);'  # used to highlight invalid inputs
        self.timeout_alert = QMessageBox(
            QMessageBox.Warning, self.plugin_name,
            self.tr("Sorry, we couldn't connect to Mapflow. Please try again later."
                    "If the problem remains, please, send us an email to help@geoalert.io."),
            parent=self.main_window
        )
        self.offline_alert = QMessageBox(
            QMessageBox.Information,
            self.plugin_name,
            self.tr("Mapflow requires Internet connection"),
            parent=self.main_window
        )
        # Tweak URL's considering the user's locale
        if locale == 'ru':
            help_text = self.dlg.helpText.text()
            new_text = help_text.replace('docs.mapflow', 'ru.docs.mapflow').replace('http://mapflow.ai', 'http://mapflow.ai/ru')
            self.dlg.helpText.setText(new_text)
        # Display the plugin's version in the Help tab
        metadata_parser = ConfigParser()
        metadata_parser.read(os.path.join(self.plugin_dir, 'metadata.txt'))
        plugin_version = metadata_parser.get('general', 'version')
        self.dlg.pluginVersion.setText(self.dlg.pluginVersion.text() + plugin_version)
        # RESTORE LATEST FIELD VALUES & OTHER ELEMENTS STATE
        # Check if there are stored credentials
        self.logged_in = self.settings.value("serverLogin") and self.settings.value("serverPassword")
        if self.settings.value('serverRememberMe'):
            self.server = self.settings.value('server')
            self.dlg_login.loginField.setText(self.settings.value('serverLogin'))
            self.dlg_login.passwordField.setText(self.settings.value('serverPassword'))
        self.dlg.outputDirectory.setText(self.settings.value('outputDir'))
        self.dlg.maxarProduct.setCurrentText(self.settings.value('maxarProduct'))
        if self.settings.value("customProviderSaveAuth"):
            self.dlg.customProviderSaveAuth.setChecked(True)
            self.dlg.customProviderLogin.setText(self.settings.value("customProviderLogin"))
            self.dlg.customProviderPassword.setText(self.settings.value("customProviderPassword"))
        # Restore Maxar Connect IDs
        for product in config.CONNECT_IDS:
            setting_key = f'connectId{product}'
            self.settings.setValue(setting_key, self.settings.value(setting_key) or config.CONNECT_IDS[product])
        # Restore custom providers
        self.custom_provider_config = os.path.join(self.plugin_dir, 'custom_providers.json')
        with open(self.custom_provider_config) as f:
            self.custom_providers = json.load(f)
        self.dlg.rasterCombo.setAdditionalItems(self.custom_providers)
        self.dlg.customProviderCombo.addItems(self.custom_providers)
        # Store processings selected in the table
        self.selected_processings: List[Dict[str, Union[str, int]]] = []
        # Hide the ID columns as only needed for table operations, not the user
        self.dlg.processingsTable.setColumnHidden(ID_COLUMN_INDEX, True)
        self.dlg.maxarMetadataTable.setColumnHidden(MAXAR_METADATA_FEATURE_ID_COLUMN_INDEX, True)
        # SET UP SIGNALS & SLOTS
        # Connect buttons
        self.dlg.logoutButton.clicked.connect(self.logout)
        self.dlg.selectOutputDirectory.clicked.connect(self.select_output_directory)
        self.dlg.selectTif.clicked.connect(self.select_tif)
        # (Dis)allow the user to use raster extent as AOI
        self.dlg.rasterCombo.layerChanged.connect(self.toggle_use_image_extent_as_aoi)
        self.dlg.useImageExtentAsAOI.stateChanged.connect(lambda is_checked: self.dlg.polygonCombo.setEnabled(not is_checked))
        self.dlg.startProcessing.clicked.connect(self.create_processing)
        # Calculate AOI area
        self.dlg.polygonCombo.layerChanged.connect(self.calculate_aoi_area)
        self.dlg.rasterCombo.layerChanged.connect(self.calculate_aoi_area)
        self.dlg.useImageExtentAsAOI.toggled.connect(self.calculate_aoi_area)
        self.project.layersAdded.connect(self.monitor_polygon_layer_feature_selection)
        # Processings
        self.dlg.processingsTable.itemSelectionChanged.connect(self.memorize_selected_processings)
        self.dlg.processingsTable.cellDoubleClicked.connect(self.download_processing_results)
        self.dlg.deleteProcessings.clicked.connect(self.delete_processings)
        # Custom provider
        self.dlg.preview.clicked.connect(self.preview)
        self.dlg.addCustomProvider.clicked.connect(self.dlg_custom_provider.show)
        self.dlg.removeCustomProvider.clicked.connect(self.remove_custom_provider)
        self.dlg_custom_provider.buttonBox.accepted.connect(self.add_custom_provider)
        # Maxar
        self.dlg.getImageMetadata.clicked.connect(self.get_maxar_metadata)
        self.dlg.editConnectID.clicked.connect(self.dlg_connect_id.show)
        self.dlg_connect_id.buttonBox.accepted.connect(self.edit_connect_id)

    def remove_custom_provider(self) -> None:
        """"""
        del self.custom_providers[self.dlg.customProviderCombo.currentText()]
        with open(self.custom_provider_config, 'w') as f:
            json.dump(self.custom_providers, f)
        self.dlg.customProviderCombo.removeItem(self.dlg.customProviderCombo.currentIndex())

    def add_custom_provider(self) -> None:
        """"""
        name = self.dlg_custom_provider.name.text()
        url = self.dlg_custom_provider.url.text()
        if not name:
            self.dlg_custom_provider.name.setStyleSheet(self.red_border_style)
        elif not url:
            self.dlg_custom_provider.url.setStyleSheet(self.red_border_style)
        else:
            self.custom_providers[name] = {"url": url, "type": self.dlg_custom_provider.type.currentText()}
            with open(self.custom_provider_config, 'w') as f:
                json.dump(self.custom_providers, f)
            self.dlg.rasterCombo.setAdditionalItems(self.custom_providers)
            self.dlg.customProviderCombo.addItem(name)
            self.dlg_custom_provider.close()

    def edit_connect_id(self) -> None:
        """Open up a dialog to enter a new Maxar Connect ID.

        Opens up self.dlg_connect_id with a single line edit to enter the value.
        Validates the input and stores it in the settings if valid, otherwise keeps the dialog open
        and outlines the input field with red to signal the error.

        Is called by clicking the "Edit Connect ID" button.
        """
        product_name = self.dlg.maxarProduct.currentText()
        try:
            uuid_ = self.dlg_connect_id.connectID.text()
            UUID(uuid_)
            self.settings.setValue(f'connectId{product_name}', uuid_)
            self.dlg_connect_id.connectID.setStyleSheet('')  # default
            self.dlg_connect_id.close()
        except ValueError:
            self.dlg_connect_id.connectID.setStyleSheet(self.red_border_style)

    def monitor_polygon_layer_feature_selection(self, layers: List[QgsMapLayer]) -> None:
        """Set up connection between feature selection in polygon layers and AOI area calculation.

        Since the plugin allows using a single feature withing a polygon layer as an AOI for processing,
        its area should then also be calculated and displayed in the UI, just as with a single-featured layer.
        For every polygon layer added to the project, this function sets up a signal-slot connection for
        monitoring its feature selection by passing the changes to calculate_aoi_area().

        :param layers: A list of layers of any type (all non-polygon layers will be skipped) 
        """
        for layer in [layer for layer in layers if helpers.is_polygon_layer(layer)]:
            layer.selectionChanged.connect(self.calculate_aoi_area)

    def toggle_use_image_extent_as_aoi(self, layer: Optional[QgsRasterLayer]) -> None:
        """Toggle the 'Use image extent' checkbox depending on the item in the 'Imagery source' combo box.

        If it's a GeoTIFF layer, then 'Use image extent' is enabled and checked since it's presumed that when a user
        processes their own image, they would often like to process only within its extent.
        'Update cache' is toggled reversely: if a local GeoTIFF is passed, cache can't be updated.

        :param layer: A raster layer
        """
        # False if imagery source is 'Mapbox Satellite' or 'Custom provider', i.e. a 'virtual' layer
        enabled = bool(layer)
        # If a 'virtual layer', it's extent can't be used
        self.dlg.useImageExtentAsAOI.setEnabled(enabled)
        self.dlg.useImageExtentAsAOI.setChecked(enabled)
        # Raster can't be cached for user GeoTIFFs
        self.dlg.updateCache.setEnabled(not enabled)

    def select_output_directory(self) -> str:
        """Open a file dialog for the user to select a directory where plugin files will be stored.

        Is called by clicking the 'selectOutputDirectory' button or when other functions that use file storage
        are called (get_maxar_metadata(), download_processing_results()).

        Returns the selected path, or None if the user closed the dialog.
        """
        path: str = QFileDialog.getExistingDirectory(self.main_window, self.tr('Select output directory'))
        if path:
            self.dlg.outputDirectory.setText(path)
            # Save to settings to set it automatically at next plugin start
            self.settings.setValue("outputDir", path)
            return path

    def check_if_output_directory_is_selected(self) -> bool:
        """Check if the user specified an existing output dir.

        The 'outputDirectory' field in the Settings tab is checked. If it doesn't contain a path to an
        existing directory, prompt the user to select one by opening a modal file selection dialog.

        Returns True if an existing directory is specified or a new directory has been selected, else False.
        """
        if os.path.exists(self.dlg.outputDirectory.text()):
            return True
        elif self.select_output_directory():
            return True
        else:
            self.alert(self.tr('Please, specify an existing output directory'))
            return False

    def select_tif(self) -> None:
        """Open a file selection dialog for the user to select a GeoTIFF for processing.

        Is called by clicking the 'selectTif' button in the main dialog.
        """
        dlg = QFileDialog(self.main_window, self.tr("Select GeoTIFF"))
        dlg.setMimeTypeFilters(['image/tiff'])
        if dlg.exec():
            path: str = dlg.selectedFiles()[0]
            layer = QgsRasterLayer(path, os.path.splitext(os.path.basename(path))[0])
            self.project.addMapLayer(layer)
            self.dlg.rasterCombo.setLayer(layer)

    def get_maxar_metadata(self) -> None:
        """Get SecureWatch image footprints and metadata.

        SecureWatch provides 'metadata': image footprints (polygonal boundaries of images) and the relevant attributes
        such as capture date, cloud cover, etc. The data is requested via WFS, loaded as a layer named 'Maxar metadata'
        and a selection of the attributes is further represented in the maxarMetadataTable. The user can select an image
        of their interest in the table and click 'Get URL' to preview the image or submit it for processing.

        Is called by clicking the 'getMaxarMetadata' button in the main dialog.
        """
        self.save_custom_provider_auth()
        if not self.check_if_output_directory_is_selected():
            return
        aoi_layer = self.dlg.maxarAOICombo.currentLayer()
        if not aoi_layer:
            self.alert(self.tr('Please, select an area of interest'))
            return
        # Get the AOI feature within the layer
        if aoi_layer.featureCount() == 1:
            aoi_feature = next(aoi_layer.getFeatures())
        elif len(list(aoi_layer.getSelectedFeatures())) == 1:
            aoi_feature = next(aoi_layer.getSelectedFeatures())
        elif aoi_layer.featureCount() == 0:
            self.alert(self.tr('Your AOI layer is empty'))
            return
        else:
            self.alert(self.tr('Please, select a single feature in your AOI layer'))
            return
        connect_id = self.settings.value(f'connectId{self.dlg.maxarProduct.currentText()}')
        aoi = aoi_feature.geometry()
        # Reproject to WGS84, if necessary
        layer_crs: QgsCoordinateReferenceSystem = aoi_layer.crs()
        if layer_crs != helpers.WGS84:
            aoi = helpers.to_wgs84(aoi, layer_crs, self.project.transformContext())
        # Get the '{min_lon},{min_lat} : {max_lon},{max_lat}' (SW-NE) representation of the AOI's bbox
        extent = aoi.boundingBox().toString()
        # Change lon,lat to lat,lon for Maxar
        coords = [reversed(position.split(',')) for position in extent.split(':')]
        bbox = ','.join([coord.strip() for position in coords for coord in position])
        # Read credentials
        login = self.dlg.customProviderLogin.text()
        password = self.dlg.customProviderPassword.text()
        url = "https://securewatch.digitalglobe.com/catalogservice/wfsaccess"
        params = {
            "REQUEST": "GetFeature",
            "TYPENAME": "DigitalGlobe:FinishedFeature",
            "SERVICE": "WFS",
            "VERSION": "2.0.0",
            "CONNECTID": connect_id,
            "BBOX": bbox,
            "SRSNAME": "EPSG:4326",
            "FEATUREPROFILE": "Default_Profile",
            "WIDTH": 3000,
            "HEIGHT": 3000
        }
        try:
            r = requests.get(url, params=params, auth=(login, password), timeout=5)
            r.raise_for_status()
        except requests.Timeout:
            self.alert(self.tr("SecureWatch is not responding. Please, try again later."))
            return
        except requests.HTTPError:
            if r.status_code == 401:
                self.alert(self.tr('Please, check your credentials'), kind='warning')
                return
        # Save metadata to a GeoJSON; I couldn't get WFS to work otherwise no file would be necessary
        output_file_name = os.path.join(self.dlg.outputDirectory.text(), 'maxar_metadata.geojson')
        with open(output_file_name, 'wb') as f:
            f.write(r.content)
        metadata_layer = QgsVectorLayer(output_file_name, 'Maxar metadata', 'ogr')
        self.project.addMapLayer(metadata_layer)
        # Add style
        metadata_layer.loadNamedStyle(os.path.join(self.plugin_dir, 'styles', 'wfs.qml'))
        # Get the list of features (don't use the generator itself, otherwise it'll get exhausted)
        features = list(metadata_layer.getFeatures())
        # Memorize IDs and extents to be able to clip the user's AOI to image on processing creation
        self.maxar_metadata_extents: List[QgsFeature] = {feature['featureId']: feature for feature in features}
        # Fill out the table
        self.dlg.maxarMetadataTable.setRowCount(len(features))
        # Round up cloud cover to two decimal numbers
        for feature in features:
            # Use 'or 0' to handle NULL values that don't have a __round__ method
            feature['cloudCover'] = round(feature['cloudCover'] or 0, 2)
        for row, feature in enumerate(features):
            for col, attr in enumerate(MAXAR_METADATA_ATTRIBUTES):
                self.dlg.maxarMetadataTable.setItem(row, col, QTableWidgetItem(str(feature[attr])))

    def get_maxar_url(self) -> str:
        """Construct a Maxar SecureWatch URL with the given connect ID and Feature ID, if present.

        To rid the user of the necessity to remember the URL, the fixed part of the URL is supplied by the plugin.
        The user only needs to select the Maxar product and select a row in the metadata table, if they'd like to 
        preview or process a single image. 
        """
        connect_id = self.settings.value(f'connectId{self.dlg.maxarProduct.currentText()}')
        # Check if the user selected a specific image
        selected_row = self.dlg.maxarMetadataTable.currentRow()
        feature_id = '' if selected_row == -1 else self.dlg.maxarMetadataTable.item(selected_row, 0).text()
        # Build the Maxar URL
        url = 'https://securewatch.digitalglobe.com/earthservice/wmtsaccess'
        # URL must be constructed manually to prevent URL-encoding which otherwise breaks the request
        params = '&'.join(f'{key}={value}' for key, value in {
            'CONNECTID': connect_id,
            'SERVICE': 'WMTS',
            'VERSION': '1.0.0',
            'STYLE': '',  # required even if empty
            'REQUEST': 'GetTile',
            'LAYER': 'DigitalGlobe:ImageryTileService',
            'FORMAT': 'image/jpeg',
            'TileRow': '{y}',
            'TileCol': '{x}',
            'TileMatrixSet': 'EPSG:3857',
            'TileMatrix': 'EPSG:3857:{z}',
            'CQL_FILTER': f"feature_id=%27{feature_id}%27" if feature_id else ''  # must use %27 instead of '
        }.items())
        return f'{url}?{params}'

    def calculate_aoi_area(self, arg: Optional[Union[bool, QgsMapLayer, List[QgsFeature]]]) -> None:
        """Display the area of the processing AOI in sq. km above the processings table.

        Users are charged by area and various usage limits are defined with respect to area too.
        So it's important for the user how much area they're going submit for processing.
        An AOI must be a single feature, or the extent of a GeoTIFF layer, so the area is only displayed when either:
            a) the layer in the polygon combo has a single feature, or, if more, a single feature is selected in it
            b) 'Use image extent' is checked and the current raster combo entry is a GeoTIFF layer
        The area is calculated on the sphere if the CRS is geographical.

        Is called when the current layer has been changed in either of the combos in the processings tab.

        :param arg: A list of selected polygons (layer selection changed),
            a polygon or raster layer (combo item changed),
            or the state of the 'Use image extent' checkbox
        """
        layer: QgsMapLayer
        if arg is None:  # Mapbox Satellite or Custom provider
            layer = self.dlg.polygonCombo.currentLayer()
            if not layer:
                return
        elif isinstance(arg, list) and not self.dlg.useImageExtentAsAOI.isChecked():  # feature selection changed
            layer = self.dlg.polygonCombo.currentLayer()
            # All project layers are monitored for selection, so have to check if it's the same layer as in the combo
            if layer != self.iface.activeLayer() or self.dlg.useImageExtentAsAOI.isChecked():
                return
        elif isinstance(arg, bool):  # checkbox state changed
            combo = self.dlg.rasterCombo if arg else self.dlg.polygonCombo
            layer = combo.currentLayer()
        else:  # A new layer has been selected
            layer = arg
        # Layer identified, now let's extract the geometry
        aoi: QgsGeometry
        if layer.type() == QgsMapLayerType.RasterLayer:
            aoi = QgsGeometry.fromRect(layer.extent())
        elif layer.featureCount() == 1:
            aoi = next(layer.getFeatures()).geometry()
        elif len(list(layer.getSelectedFeatures())) == 1:
            aoi = next(layer.getSelectedFeatures()).geometry()
        else:
            self.dlg.labelAOIArea.setText('')
            return
        # Now, do the math
        layer_crs: QgsCoordinateReferenceSystem = layer.crs()
        calculator = QgsDistanceArea()
        # Set ellipsoid to use spherical calculations for geographic CRSs
        calculator.setEllipsoid(layer_crs.ellipsoidAcronym() or 'EPSG:7030')  # 7030=WGS84 => makes a sensible default
        calculator.setSourceCrs(layer_crs, self.project.transformContext())
        area = calculator.measureArea(aoi) / 10**6  # sq. m to sq. km
        label = self.tr('Area: {:.2f} sq.km').format(area)
        self.dlg.labelAOIArea.setText(label)

    def memorize_selected_processings(self) -> None:
        """Memorize the currently selected processings by ID.

        Is used to restore selection in the processings table after refill. 
        IDs are saved to an instance attribute 'selected_processings'.

        Is called when a row in processings table is selected/deselected. 
        """
        selected_rows: List[int] = [row.row() for row in self.dlg.processingsTable.selectionModel().selectedRows()]
        self.selected_processings: List[Dict[str, Union[str, int]]] = [{
            'id': self.dlg.processingsTable.item(row, ID_COLUMN_INDEX).text(),
            'name': self.dlg.processingsTable.item(row, 0).text(),
            'row': row
        } for row in selected_rows]

    def delete_processings(self) -> None:
        """Delete one or more processings on the server.

        Asks for confirmation in a pop-up dialog. Multiple processings can be selected.
        Selected processings are immediately deleted from the table.

        Is called by clicking the deleteProcessings ('Delete') button.
        """
        selected_rows: List[QModelIndex] = self.dlg.processingsTable.selectionModel().selectedRows()
        if not selected_rows:
            return
        # Ask for confirmation
        if self.alert(self.tr('Delete {} processing(s)?').format(len(selected_rows)), 'question') == QMessageBox.No:
            return
        # QPersistentModel index allows deleting rows sequentially while preserving their original indexes
        for index in [QPersistentModelIndex(row) for row in selected_rows]:
            row = index.row()
            pid = self.dlg.processingsTable.item(row, ID_COLUMN_INDEX).text()
            name = self.dlg.processingsTable.item(row, 0).text()
            try:
                r = requests.delete(url=f'{self.server}/rest/processings/{pid}', auth=self.server_basic_auth, timeout=5)
            except requests.ConnectionError:
                self.offline_alert.show()
                return
            except requests.Timeout:
                self.timeout_alert.show()
                return
            r.raise_for_status()
            self.dlg.processingsTable.removeRow(row)
            self.processing_names.remove(name)

    def create_processing(self) -> None:
        """Create and start a processing on the server.

        The UI inputs are read, validated, and if valid, passed to a worker in a separate thread.
        This worker then post a requests to Mapflow and executes a callback based on the request outcome.

        Is called by clicking the 'createProcessing' ('Create processing') button.
        """
        processing_name = self.dlg.processingName.text()
        if not processing_name:
            self.alert(self.tr('Please, specify a name for your processing'))
            return
        elif processing_name in self.processing_names:
            self.alert(self.tr('Processing name taken. Please, choose a different name.'))
            return
        if not (self.dlg.polygonCombo.currentLayer() or self.dlg.useImageExtentAsAOI.isChecked()):
            self.alert(self.tr('Please, select an area of interest'))
            return
        auth_fields = (self.dlg.customProviderLogin.text(), self.dlg.customProviderPassword.text())
        if any(auth_fields) and not all(auth_fields):
            self.alert(self.tr('Invalid custom provider credentials'), kind='warning')
        update_cache = str(self.dlg.updateCache.isChecked())  # server current fails if bool
        worker_kwargs = {
            'processing_name': processing_name,
            'server': self.server,
            'auth': self.server_basic_auth,
            'wd': self.dlg.workflowDefinitionCombo.currentText(),
            'meta': {'source-app': 'qgis'}  # optional metadata
        }
        params = {}  # processing parameters
        current_raster_layer: QgsRasterLayer = self.dlg.rasterCombo.currentLayer()
        # Local GeoTIFF
        if current_raster_layer:
            if not os.path.splitext(current_raster_layer.dataProvider().dataSourceUri())[-1] in ('.tif', '.tiff'):
                self.alert(self.tr('Please, select a GeoTIFF layer'))
                return
            # Upload the image to the server
            worker_kwargs['tif'] = current_raster_layer
            worker_kwargs['aoi'] = helpers.get_layer_extent(current_raster_layer, self.project.transformContext())
            params['source_type'] = 'tif'
        else:  # custom provider or Mapbox
            raster_option = self.dlg.rasterCombo.currentText()
            if raster_option == 'Mapbox':
                worker_kwargs['meta']['source'] = 'mapbox'
                params['cache_raster_update'] = update_cache
            elif raster_option == 'Maxar':
                params['url'] = self.get_maxar_url()
                if not params['url']:
                    return
                worker_kwargs['meta']['source'] = 'maxar'
            else:
                params['source_type'] = self.custom_providers[raster_option]['type']
                params['url'] = self.custom_providers[raster_option]['url']
            self.alert(self.tr('Please, be aware that you may be charged by the imagery provider!'))
            self.save_custom_provider_auth()
            params['raster_login'] = self.dlg.customProviderLogin.text()
            params['raster_password'] = self.dlg.customProviderPassword.text()
            params['cache_raster_update'] = update_cache
            if params.get('source_type') == 'wms':
                params['target_resolution'] = 0.000005  # for the 18th zoom
        worker_kwargs['params'] = params
        if not self.dlg.useImageExtentAsAOI.isChecked():
            aoi_layer = self.dlg.polygonCombo.currentLayer()
            if aoi_layer.featureCount() == 1:
                aoi_feature = next(aoi_layer.getFeatures())
            elif len(list(aoi_layer.getSelectedFeatures())) == 1:
                aoi_feature = next(aoi_layer.getSelectedFeatures())
            elif aoi_layer.featureCount() == 0:
                self.alert(self.tr('Your AOI layer is empty'))
                return
            else:
                self.alert(self.tr('Please, select a single feature in your AOI layer'))
                return
            # Reproject it to WGS84 if the layer has another CRS
            layer_crs: QgsCoordinateReferenceSystem = aoi_layer.crs()
            if layer_crs != helpers.WGS84:
                worker_kwargs['aoi'] = helpers.to_wgs84(aoi_feature.geometry(), layer_crs, self.project.transformContext())
            else:
                worker_kwargs['aoi'] = aoi_feature.geometry()
            # Clip AOI to image if a single Maxar image is requested
            selected_row = self.dlg.maxarMetadataTable.currentRow()
            if raster_option != 'Mapbox Satellite' and self.dlg.maxar.isChecked() and selected_row != -1:
                # Recreate AOI layer; shall we change helpers.to_wgs84 to return layer, not geometry?
                aoi_layer = QgsVectorLayer('Polygon?crs=epsg:4326', 'aoi', 'memory')
                aoi = QgsFeature()
                aoi.setGeometry(worker_kwargs['aoi'])
                aoi_layer.dataProvider().addFeatures([aoi])
                aoi_layer.updateExtents()
                # Create a temp layer for the image extent
                feature_id = self.dlg.maxarMetadataTable.item(selected_row, 0).text()
                image_extent_layer = QgsVectorLayer('Polygon?crs=epsg:4326', 'image extent', 'memory')
                extent = self.maxar_metadata_extents[feature_id]
                image_extent_layer.dataProvider().addFeatures([extent])
                aoi_layer.updateExtents()
                # Find the intersection and pass it to the worker
                intersection = processing.run(
                    'qgis:intersection',
                    {'INPUT': aoi_layer, 'OVERLAY': image_extent_layer, 'OUTPUT': 'memory:'}
                )['OUTPUT']
                worker_kwargs['aoi'] = next(intersection.getFeatures()).geometry()
        # Spin up a worker, a thread, and move the worker to the thread
        thread = QThread(self.main_window)
        worker = ProcessingCreator(**worker_kwargs)
        worker.moveToThread(thread)
        thread.started.connect(worker.create_processing)
        worker.finished.connect(thread.quit)
        worker.finished.connect(self.processing_created)
        worker.tif_uploaded.connect(lambda url: self.log(self.tr(f'Your image was uploaded to: ') + url, Qgis.Success))
        worker.error.connect(lambda error: self.log(error))
        worker.error.connect(lambda: self.alert(self.tr('Processing creation failed, see the QGIS log for details'), kind='critical'))
        self.dlg.finished.connect(thread.requestInterruption)
        thread.start()
        self.push_message(self.tr('Starting the processing...'))

    def processing_created(self) -> None:
        """Display a success message and start polling Mapflow for processing progress.

        This is a callback executed after a successful create processing request.
        """
        self.alert(self.tr("Success! Processing may take up to several minutes"))
        # Restart the thread with a worker that monitors processing progress
        self.worker.thread().start()
        self.dlg.processingName.clear()

    def save_custom_provider_auth(self) -> None:
        """Save custom provider login and password to settings if user checked the save option.

        Is called at three occasions: preview, processing creation and metadata request.
        """
        # Save the checkbox state itself
        self.settings.setValue("customProviderSaveAuth", self.dlg.customProviderSaveAuth.isChecked())
        # If checked, save the credentials
        if self.dlg.customProviderSaveAuth.isChecked():
            self.settings.setValue("customProviderLogin", self.dlg.customProviderLogin.text())
            self.settings.setValue("customProviderPassword", self.dlg.customProviderPassword.text())

    def preview(self) -> None:
        """Download and display the custom provider raster data.

        The data is defined by the custom imagery provider URL.

        Is called by clicking the preview button.
        """
        self.save_custom_provider_auth()
        raster_option = self.dlg.rasterCombo.currentText()
        if raster_option == 'Mapbox':
            return
        url = self.get_maxar_url() if raster_option == 'Maxar' else self.custom_providers[raster_option]['url']
        # Complete escaping via libs like urllib3 or requests somehow invalidates the request
        # Requesting JPEG for Maxar won't work with some of their layers so use PNG instead
        url_escaped = url.replace('&', '%26').replace('=', '%3D').replace('jpeg', 'png')
        params = {
            'type': self.custom_providers[raster_option]['type'],
            'url': url_escaped,
            'zmax': self.dlg.zoomLimit.value(),
            'zmin': 0,
            'username': self.dlg.customProviderLogin.text(),
            'password': self.dlg.customProviderPassword.text()
        }
        uri = '&'.join(f'{key}={val}' for key, val in params.items())
        layer = QgsRasterLayer(uri, self.tr('Custom tileset'), 'wms')
        if not layer.isValid():
            self.alert(self.tr('Invalid custom imagery provider:') + url_escaped)
        else:
            self.project.addMapLayer(layer)

    def download_processing_results(self, row: int) -> None:
        """Download and display processing results along with the source raster, if available.

        Features will be downloaded into the user's output directory. If it's not set, a prompt will appear
        telling the user to select one. 
        If the processing hasn't finished yet or has failed, the resulting feature layer will be empty (no geometry).

        Is called by double-clicking on a row in the processings table.

        :param int: Row number in the processings table (0-based)
        """
        if not self.check_if_output_directory_is_selected():
            return
        processing_name = self.dlg.processingsTable.item(row, 0).text()  # 0th column is Name
        pid = self.dlg.processingsTable.item(row, ID_COLUMN_INDEX).text()
        try:
            r = requests.get(f'{self.server}/rest/processings/{pid}/result', auth=self.server_basic_auth)
        except requests.ConnectionError:
            self.offline_alert.show()
            return
        r.raise_for_status()
        # Add the source raster (COG) if it has been created
        tif_url = [processing['rasterLayer']['tileUrl'] for processing in self.processings if processing['id'] == pid]
        if tif_url:
            params = {
                'type': 'xyz',
                'url': tif_url[0],
                'zmin': 0,
                'zmax': 18,
                'username': self.dlg_login.loginField.text(),
                'password': self.dlg_login.passwordField.text()
            }
            # URI-encoding will invalidate the request so requests.prepare() or the like can't be used
            uri = '&'.join(f'{key}={val}' for key, val in params.items())
            tif_layer = QgsRasterLayer(uri, f'{processing_name}_image', 'wms')
        # First, save the features as GeoJSON
        geojson_file_name = os.path.join(self.dlg.outputDirectory.text(), f'{processing_name}.geojson')
        with open(geojson_file_name, 'wb') as f:
            f.write(r.content)
        # Export to Geopackage to prevent QGIS from hanging if the GeoJSON is heavy
        output_path = os.path.join(self.dlg.outputDirectory.text(), f'{processing_name}.gpkg')
        layer = QgsVectorLayer(geojson_file_name, 'temp', 'ogr')
        transform = self.project.transformContext()
        # Layer creation options for QGIS 3.10.3+
        write_options = QgsVectorFileWriter.SaveVectorOptions()
        write_options.layerOptions = ['fid=id']
        # writeAsVectorFormat keeps changing between version so gotta check the version :-(
        if Qgis.QGIS_VERSION_INT < 31003:
            error, msg = QgsVectorFileWriter.writeAsVectorFormat(layer, output_path, 'utf8', layerOptions=['fid=id'])
        elif Qgis.QGIS_VERSION_INT >= 32000:
            # V3 returns two additional str values but they're not documented, so just discard them
            error, msg, *_ = QgsVectorFileWriter.writeAsVectorFormatV3(layer, output_path, transform, write_options)
        else:
            error, msg = QgsVectorFileWriter.writeAsVectorFormatV2(layer, output_path, transform, write_options)
        if error:
            self.push_message(self.tr('Error saving results! See QGIS logs.'), Qgis.Warning)
            self.log(msg)
            return
        # Try to delete the GeoJSON file. Fails on Windows
        try:
            os.remove(geojson_file_name)
        except:
            pass
        # Load the results into QGIS
        results_layer = QgsVectorLayer(output_path, processing_name, "ogr")
        if not results_layer:
            self.push_message(self.tr("Could not load the results"), Qgis.Warning)
            return
        # Add a style
        styles = {
            'Buildings Detection': 'buildings',
            'Buildings Detection With Heights': 'buildings',
            'Forest Detection': 'forest',
            'Forest Detection With Heights': 'forest_with_heights',
            'Roads Detection': 'roads'
        }
        wd = self.dlg.processingsTable.item(row, 1).text()
        style_path = os.path.join(self.plugin_dir, 'styles', f'{styles.get(wd, "default")}.qml')
        results_layer.loadNamedStyle(style_path)
        if tif_layer.isValid():
            self.project.addMapLayer(tif_layer)
        self.project.addMapLayer(results_layer)
        self.iface.zoomToActiveLayer()

    def alert(self, message: str, kind: str = 'information') -> None:
        """Display an interactive modal pop up.

        :param message: A text to display
        :param kind: The type of a pop-up to display; it is translated into a class method name of QMessageBox,
            so must be one of https://doc.qt.io/qt-5/qmessagebox.html#static-public-members
        """
        return getattr(QMessageBox, kind)(self.dlg, self.plugin_name, message)

    def push_message(self, message: str, level: Qgis.MessageLevel = Qgis.Info, duration: int = 5) -> None:
        """Display a message on the message bar.

        :param message: A text to display
        :param level: The type of a message to display
        :param duration: For how long the message will be displayed
        """
        self.iface.messageBar().pushMessage(self.plugin_name, message, level, duration)

    def log(self, message: str, level: Qgis.MessageLevel = Qgis.Warning) -> None:
        """Log a message to the QGIS Message Log.

        :param message: A text to display
        :param level: The type of a message to display
        """
        QgsMessageLog.logMessage(message, self.plugin_name, level=level)

    def fill_out_processings_table(self, processings: List[Dict[str, Union[str, int]]]) -> None:
        """Fill out the processings table with the processings in the user's default project.

        Is called by the FetchProcessings worker running in a separate thread upon successful fetch.

        :param processings: A list of JSON-like dictionaries containing information about the user's processings.
        """
        # Inform the user about the finished processings
        try:
            finished_processings = [i['name'] for i in processings if i['percentCompleted'] == 100]
            previously_finished_processings = [i['name'] for i in self.processings if i['percentCompleted'] == '100%']
            for processing in set(finished_processings) - set(previously_finished_processings):
                self.alert(processing + self.tr(' finished. Double-click it in the table to download the results.'))
        except AttributeError:  # On plugin start, there's no self.processings, just ignore the exception
            pass
        # Save as an instance attribute to reuse elsewhere
        self.processings = processings
        # Save ref to check name uniqueness at processing creation
        self.processing_names: List[str] = [processing['name'] for processing in self.processings]
        self.dlg.processingsTable.setRowCount(len(self.processings))
        for processing in self.processings:
            # Add % signs to progress column for clarity
            processing['percentCompleted'] = f'{processing["percentCompleted"]}%'
            # Localize creation datetime
            local_datetime = parse_datetime(processing['created']).astimezone()
            # Format as ISO without seconds to save a bit of space
            processing['created'] = local_datetime.strftime('%Y-%m-%d %H:%M')
            # Extract WD names from WD objects
            processing['workflowDef'] = processing['workflowDef']['name']
        # Fill out the table and restore selection
        columns = ('name', 'workflowDef', 'status', 'percentCompleted', 'created', 'id')
        selected_processing_names = [processing['name'] for processing in self.selected_processings]
        # Row insertion triggers sorting -> row indexes shift -> duplicate rows, so turn sorting off while inserting
        self.dlg.processingsTable.setSortingEnabled(False)
        for row, processing in enumerate(self.processings):
            for col, attr in enumerate(columns):
                self.dlg.processingsTable.setItem(row, col, QTableWidgetItem(processing[attr]))
            if processing['name'] in selected_processing_names:
                self.dlg.processingsTable.selectRow(row)
        # Turn sorting on again
        self.dlg.processingsTable.setSortingEnabled(True)
        # Sort by creation date (4th column) descending
        self.dlg.processingsTable.sortItems(4, Qt.DescendingOrder)

    def tr(self, message: str) -> str:
        """Localize a UI element text.

        :param message: A text to translate
        """
        # From config, not self.plugin_name bc the latter is overloaded in submodules which break translation
        return QCoreApplication.translate(config.PLUGIN_NAME, message)

    def add_action(self, icon_path: str, text: str, callback: Callable, enabled_flag: bool = True) -> QAction:
        """Adds actionable icons to the toolbar.

        :param icon_path: The path to an image file that 'll be used for the icon
        :param text: The name of the button (displayed on hover)
        :param callback: A function or method to run when the button's clicked
        :param enabled_flag: Whether the button is enabled by default
        """
        icon = QIcon(icon_path)
        action = QAction(icon, text, self.main_window)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        self.toolbar.addAction(action)
        self.actions.append(action)
        return action

    def initGui(self) -> None:
        """Create the menu entries and toolbar icons inside the QGIS GUI.

        This function is referenced by the QGIS plugin loading system, so it can't be renamed.
        Since there are submodules, the various UI texts are set dynamically.
        """
        self.dlg.setWindowTitle(self.plugin_name)
        self.dlg_login.setWindowTitle(self.plugin_name + ' - ' + self.tr('Log in'))
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        self.add_action(icon_path, text=self.plugin_name, callback=self.run)

    def unload(self) -> None:
        """Remove the plugin menu item and icon from QGIS GUI."""
        self.dlg.close()
        self.dlg_login.close()
        for action in self.actions:
            self.iface.removePluginVectorMenu(self.plugin_name, action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar

    def connect_to_server(self) -> None:
        """Log into Mapflow.

        Is called at plugin startup.
        """
        server_name = self.dlg_login.serverCombo.currentText()
        self.server = f'https://whitemaps-{server_name}.mapflow.ai'
        login = self.dlg_login.loginField.text()
        password = self.dlg_login.passwordField.text()
        remember_me = self.dlg_login.rememberMe.isChecked()
        self.settings.setValue("serverRememberMe", remember_me)
        self.server_basic_auth = requests.auth.HTTPBasicAuth(login, password)
        try:
            # There's no separate auth endpoint so requesting the default project is the way to auth the user
            res = requests.get(f'{self.server}/rest/projects/default', auth=self.server_basic_auth, timeout=5)
            res.raise_for_status()
        except requests.ConnectionError:
            self.offline_alert.show()
        except requests.Timeout:
            self.timeout_alert.show()
        except requests.HTTPError:
            if res.status_code == 401:  # Unauthorized
                self.dlg_login.invalidCredentialsMessage.setVisible(True)
        else:  # Success!
            self.logged_in = True  # this var allows skipping auth if the user's remembered
            self.dlg_login.invalidCredentialsMessage.hide()
            if remember_me:
                self.settings.setValue('server', self.server)
                self.settings.setValue('serverLogin', login)
                self.settings.setValue('serverPassword', password)

    def logout(self) -> None:
        """Close the plugin and clear credentials from cache."""
        self.dlg.close()
        if not self.settings.value('serverRememberMe'):
            # Erase stored credentials
            for setting in ('serverLogin', 'serverPassword', 'serverRememberMe'):
                self.settings.remove(setting)
            # Clear the login form
            for field in (self.dlg_login.loginField, self.dlg_login.passwordField):
                field.clear()
        self.logged_in = False
        # Assume user wants to log into another account or to another server
        self.run()

    def run(self) -> None:
        """Plugin entrypoint.

        Is called by clicking the plugin icon.
        """
        # If not logged in, show the login form
        while not self.logged_in:
            # If the user closes the dialog
            if self.dlg_login.exec():
                self.connect_to_server()
            else:
                # Refresh the form & quit
                self.dlg_login.invalidCredentialsMessage.hide()
                return
        # Refresh the list of workflow definitions
        self.login = self.dlg_login.loginField.text()
        self.password = self.dlg_login.passwordField.text()
        self.server_basic_auth = requests.auth.HTTPBasicAuth(self.login, self.password)
        self.dlg.username.setText(self.login)
        try:
            res = requests.get(f'{self.server}/rest/projects/default', auth=self.server_basic_auth, timeout=5)
            res.raise_for_status()
        except requests.ConnectionError:
            self.offline_alert.show()
            return
        except requests.Timeout:
            self.timeout_alert.show()
            return
        except requests.HTTPError:
            if res.status_code == 401:  # Unauthorized - credentials aren't valid anymore
                self.dlg_login.invalidCredentialsMessage.setVisible(True)
                self.dlg_login.show()
                return
        wds: List[str] = [wd['name'] for wd in res.json()['workflowDefs']]
        self.dlg.workflowDefinitionCombo.clear()
        self.dlg.workflowDefinitionCombo.addItems(wds)
        # Fetch processings
        thread = QThread(self.main_window)
        self.worker = ProcessingFetcher(f'{self.server}/rest/processings', self.server_basic_auth)
        self.worker.moveToThread(thread)
        thread.started.connect(self.worker.fetch_processings)
        self.worker.fetched.connect(self.fill_out_processings_table)
        self.worker.error.connect(lambda error: self.log(error))
        self.worker.finished.connect(thread.quit)
        self.dlg.finished.connect(thread.requestInterruption)
        thread.start()
        # Enable/disable the use of image extent as AOI based on the current raster combo layer
        self.toggle_use_image_extent_as_aoi(self.dlg.rasterCombo.currentLayer())
        # Calculate area of the current AOI layer or feature
        combo = self.dlg.rasterCombo if self.dlg.useImageExtentAsAOI.isChecked() else self.dlg.polygonCombo
        self.calculate_aoi_area(combo.currentLayer())
        # Show main dialog
        self.dlg.show()
