import os.path
from typing import Callable, List, Dict, Optional, Union

import requests
from dateutil.parser import parse as parse_datetime  # can't be imported otherwise
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from qgis.core import *
from qgis.gui import *

from .resources_rc import *
from .geoalert_dialog import MainDialog, LoginDialog
from .workers import ProcessingFetcher, ProcessingCreator
from . import helpers


PLUGIN_NAME: str = 'Geoalert'
PROCESSING_LIST_REFRESH_INTERVAL: int = 5  # in seconds
RASTER_COMBO_VIRTUAL_LAYER_COUNT: int = 2  # Mapbox Satellite, Custom provider
MAXAR_METADATA_ATTRIBUTES = ('featureId', 'sourceUnit', 'productType', 'colorBandOrder', 'cloudCover', 'formattedDate')
MAXAR_METADATA_FEATURE_ID_COLUMN_INDEX = MAXAR_METADATA_ATTRIBUTES.index('featureId')
ID_COLUMN_INDEX: int = 5  # processings table


class Geoalert:
    """This class represents the plugin.

    It is instantiated by QGIS and shouldn't be used directly.

    Instance attributes:
    iface: an instance of the QGIS interface used for various UI ops 
    main_window: QGIS main window; all icons, widgets and threads will have it as their parent
    dlg: the main dialog
    dlg_login: the login dialog
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
        # Init toolbar and toolbar buttons
        self.actions = []
        self.toolbar = self.iface.addToolBar(PLUGIN_NAME)
        self.toolbar.setObjectName(PLUGIN_NAME)
        # QGIS Settings will be used to store user credentials and various UI element state
        self.settings = QgsSettings()
        # Create a namespace for the plugin settings
        self.settings.beginGroup(PLUGIN_NAME.lower())
        # Translation
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n', f'geoalert_{locale}.qm')
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)
        # Init dialogs
        self.dlg = MainDialog()
        self.dlg_login = LoginDialog()
        # RESTORE LATEST FIELD VALUES & OTHER ELEMENTS STATE
        # Check if there are stored credentials
        self.logged_in = self.settings.value("serverLogin") and self.settings.value("serverPassword")
        if self.settings.value('serverRememberMe'):
            self.server = self.settings.value('server')
            self.dlg_login.loginField.setText(self.settings.value('serverLogin'))
            self.dlg_login.passwordField.setText(self.settings.value('serverPassword'))
        self.dlg.outputDirectory.setText(self.settings.value('outputDir'))
        self.dlg.maxarConnectID.setText(self.settings.value('connectID'))
        self.dlg.customProviderURL.setText(self.settings.value('customProviderURL'))
        self.dlg.customProviderType.setCurrentText(self.settings.value('customProviderType') or 'xyz')
        if self.settings.value("customProviderSaveAuth"):
            self.dlg.customProviderSaveAuth.setChecked(True)
            self.dlg.customProviderLogin.setText(self.settings.value("customProviderLogin"))
            self.dlg.customProviderPassword.setText(self.settings.value("customProviderPassword"))
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
        self.dlg.customProviderURL.textChanged.connect(lambda text: self.settings.setValue('customProviderURL', text))
        self.dlg.customProviderType.currentTextChanged.connect(lambda text: self.settings.setValue('customProviderType', text))
        self.dlg.preview.clicked.connect(self.preview)
        # Maxar
        self.dlg.getMaxarURL.clicked.connect(self.get_maxar_url)
        self.dlg.getImageMetadata.clicked.connect(self.get_maxar_metadata)
        self.dlg.maxarMetadataTable.clicked.connect(self.set_maxar_feature_id)

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

    def select_output_directory(self) -> None:
        """Open a file dialog for the user to select a directory where all plugin files will be stored.

        Is called by clicking the 'selectOutputDirectory' button in the main dialog.
        """
        path: str = QFileDialog.getExistingDirectory(self.main_window)
        if path:
            self.dlg.outputDirectory.setText(path)
            # Save to settings to set it automatically at next plugin start
            self.settings.setValue("outputDir", path)

    def select_tif(self) -> None:
        """Open a file selection dialog for the user to select a GeoTIFF for processing.

        Is called by clicking the 'selectTif' button in the main dialog.
        """
        dlg = QFileDialog(self.main_window, self.tr("Select GeoTIFF"))
        dlg.setMimeTypeFilters(['image/tiff'])
        if dlg.exec():
            path: List[str] = dlg.selectedFiles()
            layer = QgsRasterLayer(path, os.path.splitext(path[0])[0])
            self.project.addMapLayer(layer)
            self.dlg.rasterCombo.setLayer(layer)

    def set_maxar_feature_id(self) -> None:
        """Fill the Maxar FeatureID field out with the currently selected feature ID."""
        row = self.dlg.maxarMetadataTable.currentRow()
        feature_id = self.dlg.maxarMetadataTable.model().index(row, MAXAR_METADATA_FEATURE_ID_COLUMN_INDEX).data()
        self.dlg.maxarFeatureID.setText(str(feature_id))

    def get_maxar_metadata(self) -> None:
        """Get SecureWatch image footprints and metadata.

        SecureWatch provides 'metadata': image footprints (polygonal boundaries of images) and the relevant attributes
        such as capture date, cloud cover, etc. The data is requested via WFS, loaded as a layer named 'Maxar metadata'
        and a selection of the attributes is further represented in the maxarMetadataTable. The user can select an image
        of their interest in the table and click 'Get URL' to preview the image or submit it for processing.

        Is called by clicking the 'getMaxarMetadata' button in the main dialog.
        """
        self.save_custom_provider_auth()
        # Check if the user specified an existing output dir
        if not os.path.exists(self.dlg.outputDirectory.text()):
            self.alert(self.tr('Please, specify an existing output directory'))
            return
        aoi_layer = self.dlg.maxarAOICombo.currentLayer()
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
        # Read other form inputs
        connectID = self.dlg.maxarConnectID.text()
        login = self.dlg.customProviderLogin.text()
        password = self.dlg.customProviderPassword.text()
        # Save the connect ID to restore it at next plugin startup
        self.settings.setValue('connectID', connectID)
        url = "https://securewatch.digitalglobe.com/catalogservice/wfsaccess"
        params = {
            "REQUEST": "GetFeature",
            "TYPENAME": "DigitalGlobe:FinishedFeature",
            "SERVICE": "WFS",
            "VERSION": "2.0.0",
            "CONNECTID": connectID,
            "BBOX": bbox,
            "SRSNAME": "EPSG:4326",
            "FEATUREPROFILE": "Default_Profile",
            "WIDTH": 3000,
            "HEIGHT": 3000
        }
        r = requests.get(url, params=params, auth=(login, password))
        r.raise_for_status()
        # Save metadata to a GeoJSON; I couldn't get WFS to work otherwise no file would be necessary
        output_file_name = os.path.join(self.dlg.outputDirectory.text(), 'maxar_metadata.geojson')
        with open(output_file_name, 'wb') as f:
            f.write(r.content)
        metadata_layer = QgsVectorLayer(output_file_name, 'Maxar metadata', 'ogr')
        self.project.addMapLayer(metadata_layer)
        # Add style
        style_path = os.path.join(self.plugin_dir, 'styles/style_wfs.qml')
        style_manager = metadata_layer.styleManager()
        # read valid style from layer
        style = QgsMapLayerStyle()
        style.readFromLayer(metadata_layer)
        # get style name from file
        style_name = os.path.basename(style_path).strip('.qml')
        # add style with new name
        style_manager.addStyle(style_name, style)
        # set new style as current
        style_manager.setCurrentStyle(style_name)
        # load qml to current style
        message: str
        success: bool
        message, success = metadata_layer.loadNamedStyle(style_path)
        if not success:  # if style not loaded remove it
            style_manager.removeStyle(style_name)
            self.alert(message)
        # Fill out the table
        features = list(metadata_layer.getFeatures())
        self.dlg.maxarMetadataTable.setRowCount(len(features))
        # Round up cloud cover to two decimal numbers
        for feature in features:
            # Use 'or 0' to handle NULL values that don't have a __round__ method
            feature['cloudCover'] = round(feature['cloudCover'] or 0, 2)
        for row, feature in enumerate(features):
            for col, attr in enumerate(MAXAR_METADATA_ATTRIBUTES):
                self.dlg.maxarMetadataTable.setItem(row, col, QTableWidgetItem(str(feature[attr])))

    def get_maxar_url(self) -> None:
        """Construct a Maxar SecureWatch URL with the given connect ID and Feature ID, if present.

        To rid the user of the necessity to remember the URL, the fixed part of the URL is supplied by the plugin.
        The user only needs to put the Connect ID in the corresponding field and to select a row in the metadata table,
        if they would like to preview or process a single image. 

        Is called by clicking the getMaxarURL ('Get URL') button.
        """
        connectID = self.dlg.maxarConnectID.text()
        featureID = self.dlg.maxarFeatureID.text()
        url = 'https://securewatch.digitalglobe.com/earthservice/wmtsaccess'
        # URL must be constructed manually to prevent URL-encoding which otherwise breaks the request
        params = '&'.join(f'{key}={value}' for key, value in {
            'CONNECTID': connectID,
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
            # %27 instead of ' is mandatory for the URL to work
            'CQL_FILTER': f"feature_id=%27{featureID}%27" if featureID else ''
        }.items())
        self.dlg.customProviderURL.setText(f'{url}?{params}')
        # WMTS is converted to XYZ in Mapflow so set the provider type accordingly
        self.dlg.customProviderType.setCurrentIndex(0)
        # Memorize the connect ID to restore it when the plugin's next started
        self.settings.setValue('connectID', connectID)

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
        label = self.tr('Area: ') + str(round(area, 2)) + self.tr(' sq.km')
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
        if self.alert(self.tr('Delete ') + str(len(selected_rows)) + self.tr(' processings?'), 'question') == QMessageBox.No:
            return
        # QPersistentModel index allows deleting rows sequentially while preserving their original indexes
        for index in [QPersistentModelIndex(row) for row in selected_rows]:
            row = index.row()
            pid = self.dlg.processingsTable.item(row, ID_COLUMN_INDEX).text()
            name = self.dlg.processingsTable.item(row, 0).text()
            r = requests.delete(url=f'{self.server}/rest/processings/{pid}', auth=self.server_basic_auth)
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
        update_cache = str(self.dlg.updateCache.isChecked())  # server current fails if bool
        worker_kwargs = {
            'processing_name': processing_name,
            'server': self.server,
            'auth': self.server_basic_auth,
            'wd': self.dlg.workflowDefinitionCombo.currentText(),
            'params': {},  # workflow definition parameters
            'meta': {'source-app': 'qgis'}  # optional metadata
        }
        current_raster_layer: QgsRasterLayer = self.dlg.rasterCombo.currentLayer()
        # Local GeoTIFF
        if current_raster_layer:
            # Can use dataProvider().htmlMetadata() instead but gotta parse it for GDAL Driver Metadata ('GeoTIFF')
            if not os.path.splitext(current_raster_layer.dataProvider().dataSourceUri())[-1] in ('.tif', '.tiff'):
                self.alert(self.tr('Please, select a GeoTIFF layer'))
                return
            # Upload the image to the server
            worker_kwargs['tif'] = current_raster_layer
            worker_kwargs['aoi'] = helpers.get_layer_extent(current_raster_layer, self.project.transformContext())
            worker_kwargs['params']['source_type'] = 'tif'
        else:  # basemap
            raster_option = self.dlg.rasterCombo.currentText()
            if raster_option == 'Mapbox Satellite':
                worker_kwargs['meta']['source'] = 'mapbox'
                worker_kwargs['params']["cache_raster_update"] = update_cache
            else:  # custom provider
                url = self.dlg.customProviderURL.text()
                if not url:
                    self.alert(self.tr('Please, specify the imagery provider URL in Settings'))
                    return
                self.alert(self.tr("Please, be aware that you may be charged by the imagery provider!"))
                self.save_custom_provider_auth()
                worker_kwargs['params']["url"] = url
                worker_kwargs['params']["source_type"] = self.dlg.customProviderType.currentText()
                worker_kwargs['params']["raster_login"] = self.dlg.customProviderLogin.text()
                worker_kwargs['params']["raster_password"] = self.dlg.customProviderPassword.text()
                worker_kwargs['params']["cache_raster_update"] = update_cache
                if worker_kwargs['params']["source_type"] == 'wms':
                    worker_kwargs['params']['target_resolution'] = 0.000005  # for the 18th zoom
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
        url = self.dlg.customProviderURL.text()
        # Complete escaping via libs like urllib3 or requests somehow invalidates the request
        # Requesting JPEG for Maxar won't work with some of their layers so use PNG instead
        url_escaped = url.replace('&', '%26').replace('=', '%3D').replace('jpeg', 'png')
        params = {
            'type': self.dlg.customProviderType.currentText(),
            'url': url_escaped,
            'zmax': 14 if self.dlg.zoomLimit.isChecked() else 18,
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
        # Check if user specified an existing output dir
        if not os.path.exists(self.dlg.outputDirectory.text()):
            self.alert(self.tr('Please, specify an existing output directory'))
            return
        processing_name = self.dlg.processingsTable.item(row, 0).text()  # 0th column is Name
        pid = self.dlg.processingsTable.item(row, ID_COLUMN_INDEX).text()
        r = requests.get(f'{self.server}/rest/processings/{pid}/result', auth=self.server_basic_auth)
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
        write_options = QgsVectorFileWriter.SaveVectorOptions()
        write_options.layerOptions = ['fid=id']
        error, msg = QgsVectorFileWriter.writeAsVectorFormatV2(
            QgsVectorLayer(geojson_file_name, 'temp', 'ogr'),
            output_path,
            self.project.transformContext(),
            write_options
        )
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
        wd = self.dlg.processingsTable.item(row, 1).text()
        if wd in ('Buildings Detection', 'Buildings Detection With Heights'):
            style = 'buildings'
        elif wd == 'Forest Detection':
            style = 'forest'
        elif wd == 'Forest Detection With Heights':
            style = 'forest_with_heights'
        elif wd == 'Roads Detection':
            style = 'roads'
        else:
            style = 'default'
        style_path = os.path.join(self.plugin_dir, 'styles', f'style_{style}.qml')
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
        return getattr(QMessageBox, kind)(self.dlg, PLUGIN_NAME, message)

    def push_message(self, message: str, level: Qgis.MessageLevel = Qgis.Info, duration: int = 5) -> None:
        """Display a message on the message bar.

        :param message: A text to display
        :param level: The type of a message to display
        :param duration: For how long the message will be displayed
        """
        self.iface.messageBar().pushMessage(PLUGIN_NAME, message, level, duration)

    def log(self, message: str, level: Qgis.MessageLevel = Qgis.Warning) -> None:
        """Log a message to the QGIS Message Log.

        :param message: A text to display
        :param level: The type of a message to display
        """
        QgsMessageLog.logMessage(message, PLUGIN_NAME, level=level)

    def fill_out_processings_table(self, processings: List[Dict[str, Union[str, int]]]) -> None:
        """Fill out the processings table with the processings in the user's default project.

        Is called by the FetchProcessings worker running in a separate thread upon successful fetch.

        :param processings: A list of JSON-like dictionaries containing information about the user's processings.
        """
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
        return QCoreApplication.translate(PLUGIN_NAME, message)

    def add_action(
        self, icon_path: str, text: str, callback: Callable, enabled_flag: bool = True, add_to_menu: bool = False,
        add_to_toolbar: bool = True, whats_this: str = None, parent: QObject = None
    ) -> QAction:
        """Adds actionable icons to the toolbar.

        :param icon_path: The path to an image file that 'll be used for the icon
        :param text: The name of the button (displayed on hover)
        :param callback: A function or method to run when the button's clicked
        :param enabled_flag: Whether the button is enabled by default
        :param add_to_menu: Whether the button will be added to the Vector menu
        :param add_to_toolbar: Whether to add the button to the toolbar referenced by self.toolbar
        :param whats_this: A text describing the button when clicked on with the "What's this" tool
        :param parent: An GUI element the button will belong to
        """
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        if whats_this:
            action.setWhatsThis(whats_this)
        if add_to_toolbar:
            self.toolbar.addAction(action)
        if add_to_menu:
            self.iface.addPluginToVectorMenu(self.menu, action)
        self.actions.append(action)
        return action

    def initGui(self) -> None:
        """Create the menu entries and toolbar icons inside the QGIS GUI.

        This function is referenced by the QGIS plugin loading system, so it can't be renamed.
        """
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        self.add_action(icon_path, text=PLUGIN_NAME, callback=self.run, parent=self.main_window)

    def unload(self) -> None:
        """Remove the plugin menu item and icon from QGIS GUI."""
        self.dlg.close()
        self.dlg_login.close()
        for action in self.actions:
            self.iface.removePluginVectorMenu(PLUGIN_NAME, action)
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
            # Log in by requesting the user's default project
            res = requests.get(f'{self.server}/rest/projects/default', auth=self.server_basic_auth)
            res.raise_for_status()
            # Success!
            self.logged_in = True  # this var allows skipping auth if the user's remembered
            self.dlg_login.invalidCredentialsMessage.hide()
            if remember_me:
                self.settings.setValue('server', self.server)
                self.settings.setValue('serverLogin', login)
                self.settings.setValue('serverPassword', password)
        except requests.exceptions.HTTPError:
            if res.status_code == 401:  # Unauthorized
                self.dlg_login.invalidCredentialsMessage.setVisible(True)

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
        self.login = self.settings.value('serverLogin') or self.dlg_login.loginField.text()
        self.password = self.settings.value('serverPassword') or self.dlg_login.passwordField.text()
        self.server_basic_auth = requests.auth.HTTPBasicAuth(self.login, self.password)
        res = requests.get(f'{self.server}/rest/projects/default', auth=self.server_basic_auth)
        res.raise_for_status()
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
