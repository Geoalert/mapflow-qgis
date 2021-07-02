import os.path

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


PLUGIN_NAME = 'Geoalert'
PROCESSING_LIST_REFRESH_INTERVAL = 5  # in seconds
RASTER_COMBO_VIRTUAL_LAYER_COUNT = 2  # Mapbox Satellite, Custom provider
ID_COLUMN_INDEX = 5  # processings table


class Geoalert:
    """Initialize the plugin."""

    def __init__(self, iface):
        # Save refs to key variables used throughout the plugin
        self.iface = iface
        self.mainWindow = iface.mainWindow()
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
        # Store processings selected in the table as dict(id=row_number)
        self.selected_processings = []
        # Hide the ID columns as only needed for table operations, not the user
        self.dlg.processingsTable.setColumnHidden(ID_COLUMN_INDEX, True)
        self.dlg.maxarMetadataTable.setColumnHidden(0, True)
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

    def monitor_polygon_layer_feature_selection(self, layers):
        """For every layer added to the project, monitor its feature selection to be able to calculate AOI area."""
        for layer in [layer for layer in layers if helpers.is_polygon_layer(layer)]:
            layer.selectionChanged.connect(self.calculate_aoi_area)

    def toggle_use_image_extent_as_aoi(self, _):
        """Toggle the checkbox depending on the item in the raster combo box."""
        enabled = bool(self.dlg.rasterCombo.currentLayer())
        self.dlg.useImageExtentAsAOI.setEnabled(enabled)
        self.dlg.useImageExtentAsAOI.setChecked(enabled)
        self.dlg.updateCache.setEnabled(not enabled)

    def select_output_directory(self):
        """Update the user's output directory."""
        path = QFileDialog.getExistingDirectory(self.mainWindow)
        if path:
            self.dlg.outputDirectory.setText(path)
            self.settings.setValue("outputDir", path)

    def select_tif(self):
        """Start a file selection dialog for a local GeoTIFF."""
        dlg = QFileDialog(self.mainWindow, self.tr("Select GeoTIFF"))
        dlg.setMimeTypeFilters(['image/tiff'])
        if dlg.exec():
            path = dlg.selectedFiles()[0]
            layer = QgsRasterLayer(path, os.path.basename(path).split('.')[0])
            self.project.addMapLayer(layer)
            self.dlg.rasterCombo.setLayer(layer)

    def set_maxar_feature_id(self):
        """Fill the Maxar FeatureID field out with the currently selecte feature ID."""
        row = self.dlg.maxarMetadataTable.currentRow()
        feature_id = self.dlg.maxarMetadataTable.model().index(row, 0).data()
        self.dlg.maxarFeatureID.setText(str(feature_id))

    def get_maxar_metadata(self):
        """Get SecureWatch image footprints."""
        self.save_custom_provider_auth()
        # Check if user specified an existing output dir
        if not os.path.exists(self.dlg.outputDirectory.text()):
            self.alert(self.tr('Please, specify an existing output directory'))
            return
        aoi_layer = self.dlg.maxarAOICombo.currentLayer()
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
        layer_crs = aoi_layer.crs()
        if layer_crs != helpers.WGS84:
            aoi = helpers.to_wgs84(aoi, layer_crs, self.project.transformContext())
        extent = aoi.boundingBox().toString()
        # Change lon,lat to lat,lon for Maxar
        coords = [reversed(position.split(',')) for position in extent.split(':')]
        bbox = ','.join([coord.strip() for position in coords for coord in position])
        # Read other form inputs
        connectID = self.dlg.maxarConnectID.text()
        login = self.dlg.customProviderLogin.text()
        password = self.dlg.customProviderPassword.text()
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
            for col, field in enumerate(('featureId', 'sourceUnit', 'productType', 'colorBandOrder', 'cloudCover', 'formattedDate')):
                self.dlg.maxarMetadataTable.setItem(row, col, QTableWidgetItem(str(feature[field])))

    def get_maxar_url(self):
        """Fill out the imagery provider URL field with the Maxar Secure Watch URL."""
        connectID = self.dlg.maxarConnectID.text()
        featureID = self.dlg.maxarFeatureID.text()
        url = 'https://securewatch.digitalglobe.com/earthservice/wmtsaccess'
        params = '&'.join(f'{key}={value}' for key, value in {
            'CONNECTID': connectID,
            'SERVICE': 'WMTS',
            'VERSION': '1.0.0',
            'STYLE': '',
            'REQUEST': 'GetTile',
            'LAYER': 'DigitalGlobe:ImageryTileService',
            'FORMAT': 'image/jpeg',
            'TileRow': '{y}',
            'TileCol': '{x}',
            'TileMatrixSet': 'EPSG:3857',
            'TileMatrix': 'EPSG:3857:{z}',
            'CQL_FILTER': f"feature_id=%27{featureID}%27" if featureID else ''
        }.items())
        self.dlg.customProviderURL.setText(f'{url}?{params}')
        self.dlg.customProviderType.setCurrentIndex(0)
        self.settings.setValue('connectID', connectID)

    def calculate_aoi_area(self, arg):
        if arg is None:  # Mapbox Satellite or Custom provider
            self.dlg.labelAOIArea.setText('')
            return
        elif isinstance(arg, list) and not self.dlg.useImageExtentAsAOI.isChecked():  # feature selection changed
            layer = self.dlg.polygonCombo.currentLayer()
            if (layer != self.iface.activeLayer()) or self.dlg.useImageExtentAsAOI.isChecked():
                return
            layer = self.dlg.polygonCombo.currentLayer()
        elif isinstance(arg, bool):  # checkbox state changed
            combo = self.dlg.rasterCombo if arg else self.dlg.polygonCombo
            layer = combo.currentLayer()
        else:  # real layer
            layer = arg
        # Layer identified, now let's extract the geometry
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
        layer_crs = layer.crs()
        area_calculator = QgsDistanceArea()
        area_calculator.setEllipsoid(layer_crs.ellipsoidAcronym() or 'EPSG:7030')
        area_calculator.setSourceCrs(layer_crs, self.project.transformContext())
        area = area_calculator.measureArea(aoi) / 10**6  # sq m to sq km
        label = self.tr('Area: ') + str(round(area, 2)) + self.tr(' sq.km')
        self.dlg.labelAOIArea.setText(label)

    def memorize_selected_processings(self):
        """Memorize the currently selected processing by its ID."""
        selected_rows = [row.row() for row in self.dlg.processingsTable.selectionModel().selectedRows()]
        self.selected_processings = [{
            'id': self.dlg.processingsTable.item(row, ID_COLUMN_INDEX).text(),
            'name': self.dlg.processingsTable.item(row, 0).text(),
            'row': row
        } for row in selected_rows]

    def delete_processings(self):
        """Delete one or more processings on the server."""
        if not self.dlg.processingsTable.selectionModel().hasSelection():
            return
        selected_rows = self.dlg.processingsTable.selectionModel().selectedRows()
        if self.alert(self.tr('Delete ') + str(len(selected_rows)) + self.tr(' processings?'), 'question') == QMessageBox.No:
            return
        for index in [QPersistentModelIndex(row) for row in selected_rows]:
            row = index.row()
            pid = self.dlg.processingsTable.item(row, ID_COLUMN_INDEX).text()
            name = self.dlg.processingsTable.item(row, 0).text()
            r = requests.delete(
                url=f'{self.server}/rest/processings/{pid}',
                auth=self.server_basic_auth
            )
            r.raise_for_status()
            self.dlg.processingsTable.removeRow(row)
            self.processing_names.remove(name)

    def create_processing(self):
        """Spin up a thread to create a processing on the server."""
        processing_name = self.dlg.processingName.text()
        if not processing_name:
            self.alert(self.tr('Please, specify a name for your processing'))
            return
        elif processing_name in self.processing_names:
            self.alert(self.tr('Processing name taken. Please, choose a different name.'))
            return
        if self.dlg.polygonCombo.currentIndex() == -1 and not self.dlg.useImageExtentAsAOI.isChecked():
            self.alert(self.tr('Please, select an area of interest'))
            return
        update_cache = str(self.dlg.updateCache.isChecked())
        worker_kwargs = {
            'processing_name': processing_name,
            'server': self.server,
            'auth': self.server_basic_auth,
            'wd': self.dlg.workflowDefinitionCombo.currentText(),
            'params': {},  # workflow definition parameters
            'meta': {'source-app': 'qgis'}  # optional metadata
        }
        current_raster_layer = self.dlg.rasterCombo.currentLayer()
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
        # Basemap
        else:
            raster_option = self.dlg.rasterCombo.currentText()
            if raster_option == 'Mapbox Satellite':
                worker_kwargs['meta']['source'] = 'mapbox'
                worker_kwargs['params']["cache_raster_update"] = update_cache
            # Custom provider
            else:
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
            layer_crs = aoi_layer.crs()
            if layer_crs != helpers.WGS84:
                worker_kwargs['aoi'] = helpers.to_wgs84(aoi_feature.geometry(), layer_crs, self.project.transformContext())
            else:
                worker_kwargs['aoi'] = aoi_feature.geometry()
        thread = QThread(self.mainWindow)
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

    def processing_created(self):
        """"""
        self.alert(self.tr("Success! Processing may take up to several minutes"))
        self.worker.thread().start()
        self.dlg.processingName.clear()

    def save_custom_provider_auth(self):
        """"""
        # Save the checkbox state itself
        self.settings.setValue("customProviderSaveAuth", self.dlg.customProviderSaveAuth.isChecked())
        # If checked, save the credentials
        if self.dlg.customProviderSaveAuth.isChecked():
            self.settings.setValue("customProviderLogin", self.dlg.customProviderLogin.text())
            self.settings.setValue("customProviderPassword", self.dlg.customProviderPassword.text())

    def preview(self):
        """Custom provider imagery preview."""
        self.save_custom_provider_auth()
        url = self.dlg.customProviderURL.text()
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

    def download_processing_results(self, row):
        """Download the resulting features and open them in QGIS."""
        # Check if user specified an existing output dir
        if not os.path.exists(self.dlg.outputDirectory.text()):
            self.alert(self.tr('Please, specify an existing output directory'))
            return
        processing_name = self.dlg.processingsTable.item(row, 0).text()  # 0th column is Name
        pid = self.dlg.processingsTable.item(row, ID_COLUMN_INDEX).text()
        r = requests.get(f'{self.server}/rest/processings/{pid}/result', auth=self.server_basic_auth)
        r.raise_for_status()
        # Add COG if it has been created
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
            uri = '&'.join(f'{key}={val}' for key, val in params.items())
            tif_layer = QgsRasterLayer(uri, f'{processing_name}_image', 'wms')
        # First, save to GeoJSON
        geojson_file_name = os.path.join(self.dlg.outputDirectory.text(), f'{processing_name}.geojson')
        with open(geojson_file_name, 'wb') as f:
            f.write(r.content)
        # Export to Geopackage to avoid QGIS hanging if GeoJSON is very large
        output_path = os.path.join(self.dlg.outputDirectory.text(), f'{processing_name}.gpkg')
        write_options = QgsVectorFileWriter.SaveVectorOptions()
        write_options.layerOptions = ['fid=id']
        error, msg = QgsVectorFileWriter.writeAsVectorFormatV2(
            QgsVectorLayer(geojson_file_name, 'temp', "ogr"),
            output_path,
            self.project.transformContext(),
            write_options
        )
        if error:
            self.push_message(self.tr('Error saving results! See QGIS logs.'), Qgis.Warning)
            self.log(msg)
            return
        # Try to delete the GeoJSON file
        try:
            os.remove(geojson_file_name)
        except:
            pass
        # Load the results into QGIS
        results_layer = QgsVectorLayer(output_path, processing_name, "ogr")
        if not results_layer:
            self.push_message(self.tr("Could not load the results"), Qgis.Warning)
            return
        # Add style
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

    def alert(self, message, kind='information'):
        """Display an interactive modal pop up."""
        return getattr(QMessageBox, kind)(self.dlg, 'Mapflow', message)

    def push_message(self, text, level=Qgis.Info, duration=5):
        """Display a translated message on the message bar."""
        self.iface.messageBar().pushMessage("Mapflow", text, level, duration)

    def log(self, message, level=Qgis.Warning):
        """Log a message to the Mapflow tab in the QGIS Message Log."""
        QgsMessageLog.logMessage(message, 'Mapflow', level=level)

    def fill_out_processings_table(self, processings):
        """Insert current processings in the table.

        This function is called by a daemon thread that runs fetch_processings().
        """
        self.processings = processings
        # Save ref to check name uniqueness at processing creation
        self.processing_names = [processing['name'] for processing in self.processings]
        processing = [processing['id'] for processing in self.processings]
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
        # Turn sorting off while inserting
        self.dlg.processingsTable.setSortingEnabled(False)
        # Fill out the table
        columns = ('name', 'workflowDef', 'status', 'percentCompleted', 'created', 'id')
        selected_processing_names = [processing['name'] for processing in self.selected_processings]
        for row, processing in enumerate(self.processings):
            for col, attr in enumerate(columns):
                self.dlg.processingsTable.setItem(row, col, QTableWidgetItem(processing[attr]))
            if processing['name'] in selected_processing_names:
                self.dlg.processingsTable.selectRow(row)

        # Turn sorting on again
        self.dlg.processingsTable.setSortingEnabled(True)
        # Sort by creation date (5th column) descending
        self.dlg.processingsTable.sortItems(4, Qt.DescendingOrder)

    def tr(self, message):
        return QCoreApplication.translate(PLUGIN_NAME, message)

    def add_action(self, icon_path, text, callback, enabled_flag=True, add_to_menu=False,
                   add_to_toolbar=True, status_tip=None, whats_this=None, parent=None):

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        if status_tip:
            action.setStatusTip(status_tip)
        if whats_this:
            action.setWhatsThis(whats_this)
        if add_to_toolbar:
            self.toolbar.addAction(action)
        if add_to_menu:
            self.iface.addPluginToVectorMenu(self.menu, action)
        self.actions.append(action)
        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        icon_path = self.plugin_dir + '/icon.png'
        self.add_action(
            icon_path,
            text=PLUGIN_NAME,
            callback=self.run,
            parent=self.mainWindow)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        self.dlg.close()
        self.dlg_login.close()
        for action in self.actions:
            self.iface.removePluginVectorMenu(PLUGIN_NAME, action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar

    def connect_to_server(self):
        """Connect to Geoalert server."""
        server_name = self.dlg_login.serverCombo.currentText()
        self.server = f'https://whitemaps-{server_name}.mapflow.ai'
        login = self.dlg_login.loginField.text()
        password = self.dlg_login.passwordField.text()
        remember_me = self.dlg_login.rememberMe.isChecked()
        self.settings.setValue("serverRememberMe", remember_me)
        self.server_basic_auth = requests.auth.HTTPBasicAuth(login, password)
        try:
            res = requests.get(f'{self.server}/rest/projects/default', auth=self.server_basic_auth)
            res.raise_for_status()
            # Success!
            self.logged_in = True
            self.dlg_login.invalidCredentialsMessage.hide()
            if remember_me:
                self.settings.setValue('server', self.server)
                self.settings.setValue('serverLogin', login)
                self.settings.setValue('serverPassword', password)
        except requests.exceptions.HTTPError:
            if res.status_code == 401:
                self.dlg_login.invalidCredentialsMessage.setVisible(True)

    def logout(self):
        """Close the plugin and clear credentials from cache."""
        self.dlg.close()
        if not self.settings.value('serverRememberMe'):
            for setting in ('serverLogin', 'serverPassword', 'serverRememberMe'):
                self.settings.remove(setting)
            for field in (self.dlg_login.loginField, self.dlg_login.passwordField):
                field.clear()
        self.logged_in = False
        self.run()

    def run(self):
        """Plugin entrypoint."""
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
        wds = [wd['name'] for wd in res.json()['workflowDefs']]
        self.dlg.workflowDefinitionCombo.clear()
        self.dlg.workflowDefinitionCombo.addItems(wds)
        # Fetch processings
        thread = QThread(self.mainWindow)
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
