import sys  # Python version check for ensuring compatibility
import json
import os.path
import tempfile
from base64 import b64encode, b64decode
from typing import List, Optional, Union
from datetime import datetime, timedelta  # processing creation datetime formatting
from configparser import ConfigParser  # parse metadata.txt -> QGIS version check (compatibility)

from PyQt5.QtGui import QIcon
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest, QHttpMultiPart, QHttpPart
from PyQt5.QtCore import (
    QObject, QSettings, QCoreApplication, QTimer, QTranslator, Qt, QFile, QIODevice
)
from PyQt5.QtWidgets import (
    QMessageBox, QFileDialog, QTableWidgetItem, QAction, QAbstractItemView, QLabel,
    QProgressBar
)
from qgis import processing as qgis_processing  # to avoid collisions
from qgis.gui import QgsMessageBarItem
from qgis.core import (
    QgsProject, QgsSettings, QgsMapLayer, QgsVectorLayer, QgsRasterLayer, QgsFeature,
    QgsCoordinateReferenceSystem, QgsDistanceArea, QgsGeometry, QgsMapLayerType, Qgis,
    QgsVectorFileWriter, QgsRectangle
)

from .dialogs import MainDialog, LoginDialog, ProviderDialog, ConnectIdDialog, ErrorMessage
from .http import Http
from . import helpers, config


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
        self.server = f'https://whitemaps-{mapflow_env}.mapflow.ai/rest'
        # Create a namespace for the plugin settings
        self.settings.beginGroup(self.plugin_name.lower())
        # By default, plugin adds layers to a group unless user explicitly deletes it
        self.add_layers_to_group = True
        self.layer_tree_root = self.project.layerTreeRoot()
        # Store user's current processing
        self.processings = []
        # Init toolbar and toolbar buttons
        self.toolbar = self.iface.addToolBar(self.plugin_name)
        self.toolbar.setObjectName(self.plugin_name)
        # Translation
        locale = QSettings().value('locale/userLocale', '')[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n', f'mapflow_{locale}.qm')
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)
        # Translate native Qt texts; doesn't work in a cycle for some reason
        QCoreApplication.translate('QPlatformTheme', 'Cancel')
        QCoreApplication.translate('QPlatformTheme', '&Yes')
        QCoreApplication.translate('QPlatformTheme', '&No')
        # Init dialogs
        self.dlg = MainDialog(self.main_window)
        self.dlg_login = LoginDialog(self.main_window)
        self.dlg_login.setWindowTitle(self.plugin_name + ' - ' + self.tr('Log in'))
        self.dlg_login.logIn.clicked.connect(self.read_mapflow_token)
        self.dlg_login.finished.connect(self.clean_up_login_dialog)
        self.dlg_provider = ProviderDialog(self.dlg)
        self.dlg_provider.accepted.connect(self.add_or_edit_provider)
        self.dlg_connect_id = ConnectIdDialog(self.dlg)
        self.offline_alert = QMessageBox(
            QMessageBox.Critical,
            self.plugin_name,
            self.tr('Mapflow requires Internet connection'),
            parent=self.main_window
        )
        self.timeout_alert = ErrorMessage(
            self.tr('Mapflow is not responding.\nPlease, try again later or send us an email.'),
            self.main_window
        )
        # Display the plugin's version
        metadata_parser = ConfigParser()
        metadata_parser.read(os.path.join(self.plugin_dir, 'metadata.txt'))
        self.plugin_version = metadata_parser.get('general', 'version')
        self.dlg.help.setText(
            self.dlg.help.text().replace('Mapflow', f'{self.plugin_name} {self.plugin_version}')
        )
        # Initialize HTTP request sender
        self.http = Http(self.plugin_version, self.handle_request_errors)
        # RESTORE LATEST FIELD VALUES & OTHER ELEMENTS STATE
        # Check if there are stored credentials
        self.logged_in = bool(self.settings.value('token'))
        self.dlg.outputDirectory.setText(self.settings.value('outputDir'))
        self.dlg.maxZoom.setValue(int(self.settings.value('maxZoom') or 18))
        if self.settings.value('providerSaveAuth'):
            self.dlg.providerSaveAuth.setChecked(True)
            self.dlg.providerUsername.setText(self.settings.value('providerUsername'))
            self.dlg.providerPassword.setText(self.settings.value('providerPassword'))
        self.update_providers(self.settings.value('providers', config.MAXAR_PRODUCTS))
        # Hide the ID columns as only needed for table operations, not the user
        self.dlg.processingsTable.setColumnHidden(config.PROCESSING_TABLE_ID_COLUMN_INDEX, True)
        self.dlg.rasterCombo.setCurrentText('Mapbox')  # otherwise SW will be set due to combo sync
        # SET UP SIGNALS & SLOTS
        # Memorize dialog element sizes & positioning
        self.dlg.finished.connect(self.save_dialog_state)
        self.dlg_connect_id.accepted.connect(self.edit_connect_id)
        # Connect buttons
        self.dlg.logoutButton.clicked.connect(self.logout)
        self.dlg.selectOutputDirectory.clicked.connect(self.select_output_directory)
        self.dlg.selectTif.clicked.connect(self.select_tif)
        # (Dis)allow the user to use raster extent as AOI
        self.dlg.rasterCombo.currentTextChanged.connect(self.toggle_use_image_extent_as_aoi)
        self.dlg.useImageExtentAsAoi.stateChanged.connect(
            lambda is_checked: self.dlg.polygonCombo.setEnabled(not is_checked)
        )
        self.dlg.startProcessing.clicked.connect(self.create_processing)
        # Calculate AOI area
        self.dlg.polygonCombo.layerChanged.connect(self.calculate_aoi_area)
        self.dlg.rasterCombo.layerChanged.connect(self.calculate_aoi_area)
        self.dlg.useImageExtentAsAoi.toggled.connect(self.calculate_aoi_area)
        self.project.layersAdded.connect(self.monitor_polygon_layer_feature_selection)
        # Processings
        self.dlg.processingsTable.cellDoubleClicked.connect(self.download_results)
        self.dlg.deleteProcessings.clicked.connect(self.delete_processings)
        # Providers
        self.dlg.preview.clicked.connect(self.preview)
        self.dlg.addProvider.clicked.connect(self.dlg_provider.show)
        self.dlg.addProvider.clicked.connect(
            lambda: setattr(self, 'is_provider_dialog_editing_mode', False)
        )
        self.dlg.editProvider.clicked.connect(self.edit_provider)
        self.dlg.editProvider.clicked.connect(
            lambda: setattr(self, 'is_provider_dialog_editing_mode', True)
        )
        self.dlg.removeProvider.clicked.connect(self.remove_provider)
        self.dlg.maxZoom.valueChanged.connect(lambda value: self.settings.setValue('maxZoom', value))
        # Maxar
        self.dlg.maxarMetadataTable.itemSelectionChanged.connect(self.highlight_maxar_image)
        self.dlg.getImageMetadata.clicked.connect(self.get_maxar_metadata)
        self.dlg.maxarMetadataTable.cellDoubleClicked.connect(self.preview)
        self.dlg.providerCombo.currentTextChanged.connect(self.limit_max_zoom_for_maxar)
        self.dlg.providerCombo.currentTextChanged.connect(self.clear_metadata_table)
        # Poll processings
        self.processing_fetch_timer = QTimer(self.main_window)
        self.processing_fetch_timer.setInterval(config.PROCESSING_TABLE_REFRESH_INTERVAL * 1000)
        self.processing_fetch_timer.timeout.connect(
            lambda: self.http.get(
                url=f'{self.server}/processings',
                callback=self.fill_out_processings_table
            ),
        )

    def clear_metadata_table(self) -> None:
        """"""
        self.dlg.maxarMetadataTable.clearContents()
        self.dlg.maxarMetadataTable.setRowCount(0)

    def limit_max_zoom_for_maxar(self, provider: str) -> None:
        """Limit zoom to 13 for Maxar if user is not a premium one."""
        max_zoom = 13 if provider in config.MAXAR_PRODUCTS and not self.is_premium_user else 21
        self.dlg.maxZoom.setMaximum(max_zoom)

    def save_dialog_state(self):
        """Memorize dialog element sizes & positioning to allow user to customize the look."""
        # Save main dialog size & position
        self.settings.setValue('mainDialogState', self.dlg.saveGeometry())
        # Save table columns widths and sorting
        for table in 'processingsTable', 'maxarMetadataTable':
            header = getattr(self.dlg, table).horizontalHeader()
            self.settings.setValue(table + 'HeaderState', header.saveState())

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
                self.layer_group.setExpanded(True)
                self.settings.setValue('layerGroup', self.plugin_name)
                # If the group has been deleted, assume user wants to add layers to root, memorize it
                self.layer_group.destroyed.connect(lambda: setattr(self, 'add_layers_to_group', False))
                # Let user rename the group, memorize the new name
                self.layer_group.nameChanged.connect(lambda _, name: self.settings.setValue('layerGroup', name))
            # To be added to group, layer has to be added to project first
            self.project.addMapLayer(layer, addToLegend=False)
            # Explcitly add layer to the position 0 or else it adds it to bottom
            self.layer_group.insertLayer(0, layer)
        else:  # assume user opted to not use a group, add layers as usual
            self.project.addMapLayer(layer)

    def highlight_maxar_image(self) -> None:
        """Select an image footprint in Maxar metadata layer when it's selected in the table.

        Is called by selecting (clicking on) a row in Maxar metadata table.
        """
        selected_items = self.dlg.maxarMetadataTable.selectedItems()
        image_id = selected_items[config.MAXAR_METADATA_ID_COLUMN_INDEX].text() if selected_items else ''
        try:
            self.metadata_layer.selectByExpression(f"featureId='{image_id}'")
        except RuntimeError:  # layer has been deleted
            pass
        # Sync the raster combo in the Processing tab so user doesn't forget to set Maxar there
        self.dlg.rasterCombo.setCurrentText(self.dlg.providerCombo.currentText())

    def remove_provider(self) -> None:
        """Delete a web tile provider from the list of registered providers.

        Is called by clicking the red minus button near the provider dropdown list.
        """
        provider = self.dlg.providerCombo.currentText()
        # Ask for confirmation
        if self.alert(self.tr('Permanently remove {}?'.format(provider)), QMessageBox.Question):
            providers = self.settings.value('providers', [])
            del providers[provider]
            self.settings.setValue('providers', providers)
            self.dlg.providerCombo.removeItem(self.dlg.providerCombo.currentIndex())
            self.dlg.rasterCombo.setAdditionalItems(providers)

    def add_or_edit_provider(self) -> None:
        """Add a web imagery provider."""
        providers = self.settings.value('providers')
        if self.is_provider_dialog_editing_mode:  # remove the old definition
            del providers[self.dlg.providerCombo.currentText()]
        name = self.dlg_provider.name.text()
        # Add the new one
        providers[name] = {
            'url': self.dlg_provider.url.text(),
            'type': self.dlg_provider.type.currentText()
        }
        # Update the combos
        self.update_providers(providers)
        self.dlg.providerCombo.setCurrentText(name)
        self.dlg.rasterCombo.setCurrentText(name)

    def edit_provider(self) -> None:
        """Edit a web imagery provider.

        Is called by the corresponding button.
        """
        provider = self.dlg.providerCombo.currentText()
        if provider in config.MAXAR_PRODUCTS:
            self.show_connect_id_dialog(provider)
        else:
            self.dlg_provider.setWindowTitle(provider)
            # Fill out the edit dialog with the current data
            providers = self.settings.value('providers')
            self.dlg_provider.name.setText(provider)
            self.dlg_provider.url.setText(providers[provider]['url'])
            self.dlg_provider.type.setCurrentText(providers[provider]['type'])
            # Open the edit dialog
            self.dlg_provider.show()

    def update_providers(self, providers: dict) -> None:
        """"""
        self.dlg.rasterCombo.setAdditionalItems((*providers, 'Mapbox'))
        self.dlg.providerCombo.clear()
        self.dlg.providerCombo.addItems(providers)
        self.settings.setValue('providers', providers)

    def show_connect_id_dialog(self, product: str) -> None:
        """"""
        # Display the current Connect ID
        providers = self.settings.value('providers')
        self.dlg_connect_id.connectId.setText(providers[product]['connectId'])
        self.dlg_connect_id.connectId.setCursorPosition(0)
        # Specify the product being edited in the window title
        self.dlg_connect_id.setWindowTitle(f'{product} - {self.dlg_connect_id.windowTitle()}')
        self.dlg_connect_id.show()

    def edit_connect_id(self) -> None:
        """Change the Connect ID for the given Maxar product.

        :param provider: Maxar product name, as in the config and dropdown list.
        """
        provider = self.dlg.providerCombo.currentText()
        providers = self.settings.value('providers')
        providers[provider]['connectId'] = self.dlg_connect_id.connectId.text()
        self.settings.setValue('providers', providers)

    def monitor_polygon_layer_feature_selection(self, layers: List[QgsMapLayer]) -> None:
        """Set up connection between feature selection in polygon layers and AOI area calculation.

        Since the plugin allows using a single feature withing a polygon layer as an AOI for processing,
        its area should then also be calculated and displayed in the UI, just as with a single-featured layer.
        For every polygon layer added to the project, this function sets up a signal-slot connection for
        monitoring its feature selection by passing the changes to calculate_aoi_area().

        :param layers: A list of layers of any type (all non-polygon layers will be skipped)
        """
        for layer in filter(helpers.is_polygon_layer, layers):
            layer.selectionChanged.connect(self.calculate_aoi_area)

    def toggle_use_image_extent_as_aoi(self, provider: str) -> None:
        """Toggle 'Use image extent' checkbox depending on the item in the imagery combo box.

        :param provider: A combo box entry representing an imagery provider
        """
        enabled = provider in (*self.settings.value('providers', {}), 'Mapbox')  # False if GeoTIFF
        # There's no extent for a tile provider
        self.dlg.useImageExtentAsAoi.setEnabled(not enabled)
        # Presume user would like to process within its extent
        self.dlg.useImageExtentAsAoi.setChecked(not enabled)
        # Mapflow doesn't currently support caching user imagery
        self.dlg.updateCache.setEnabled(enabled)

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
        dlg = QFileDialog(self.main_window, self.tr('Select GeoTIFF'))
        dlg.setMimeTypeFilters(['image/tiff'])
        if dlg.exec():
            path: str = dlg.selectedFiles()[0]
            layer = QgsRasterLayer(path, os.path.splitext(os.path.basename(path))[0])
            self.add_layer(layer)
            self.dlg.rasterCombo.setLayer(layer)

    def get_maxar_metadata(self) -> None:
        """Get SecureWatch image footprints and metadata.

        SecureWatch 'metadata' is image footprints with such attributes as capture date or cloud cover.
        The data is requested via WFS, loaded as a 'Maxar metadata' layer and shown in the maxarMetadataTable.

        Is called by clicking the 'Get Image Metadata' button in the main dialog.
        """
        self.save_provider_auth()
        provider = self.dlg.providerCombo.currentText()
        # Perform checks
        if provider not in config.MAXAR_PRODUCTS:
            self.alert(self.tr('Select a Maxar product in the provider list'))
            return
        aoi_layer = self.dlg.maxarAOICombo.currentLayer()
        if not aoi_layer:
            self.alert(self.tr('Please, select an area of interest'))
            return
        # Start off with the static params
        params = {
            'REQUEST': 'GetFeature',
            'TYPENAME': 'DigitalGlobe:FinishedFeature',
            'SERVICE': 'WFS',
            'VERSION': '2.0.0',
            'SRSNAME': 'EPSG:4326',
            'FEATUREPROFILE': 'Default_Profile',
            'WIDTH': 3000,
            'HEIGHT': 3000
        }
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
        coords = [position.split(',')[::-1] for position in extent.split(':')]
        params['BBOX'] = ','.join([coord.strip() for position in coords for coord in position])
        query_params = '&'.join(f'{key}={val}' for key, val in params.items())
        url = 'https://securewatch.digitalglobe.com/catalogservice/wfsaccess?' + query_params
        # Read credentials
        username = self.dlg.providerUsername.text()
        password = self.dlg.providerPassword.text()
        if username or password:  # user has their own account
            _, product = provider.split()
            try:
                connect_id = self.settings.value('providers')[product]['connectId']
            except KeyError:
                self.show_connect_id_dialog(product)
                return
            url += '&CONNECTID=' + connect_id
            self.http.get(
                url=url,
                callback=lambda: self.get_maxar_metadata_callback(provider),
                error_handler=self.get_maxar_metadata_error_handler,
                basic_auth=f'Basic {b64encode(f"{username}:{password}".encode()).decode()}'.encode(),
            )
        else:  # assume user wants to use our account, proxy thru Mapflow
            self.http.post(
                url=f'{self.server}/meta',
                callback=lambda: self.get_maxar_metadata_callback(provider),
                body=json.dumps({
                    'url': url,
                    'connectId': provider.split()[1].lower()
                }).encode(),
                timeout=7
            )

    def get_maxar_metadata_error_handler(self) -> None:
        """"""
        response = self.sender()
        error = response.error()
        if not error:
            return
        if error == QNetworkReply.ContentAccessDenied:
            self.alert(self.tr('Please, check your credentials'))
            return
        elif error == QNetworkReply.OperationCanceledError:
            self.alert(self.tr('SecureWatch is not responding. Please, try again later.'))
            return
        elif error == QNetworkReply.HostNotFoundError:
            if not self.offline_alert.isVisible():
                self.offline_alert.setParent(self.dlg)
                self.offline_alert.show()
            return
        elif error:
            self.alert(f'{error}: {response.errorString()}')
            return

    def get_maxar_metadata_callback(self, product: str) -> None:
        """"""
        response = self.sender()
        if response.error():
            return
        # Memorize the product to prevent further errors if user changes item in the dropdown list
        layer_name = f'{product} metadata'
        # Save metadata to a file; I couldn't get WFS to work, or else no file would be necessary
        output_file_name = os.path.join(self.temp_dir, os.urandom(32).hex()) + '.gml'
        with open(output_file_name, 'wb') as f:
            f.write(response.readAll().data())
        self.metadata_layer = QgsVectorLayer(output_file_name, layer_name, 'ogr')
        self.add_layer(self.metadata_layer)
        # Add style
        self.metadata_layer.loadNamedStyle(os.path.join(self.plugin_dir, 'static', 'styles', 'wfs.qml'))
        # Get the list of features (don't use the generator itself, or it'll get exhausted)
        features = list(self.metadata_layer.getFeatures())
        # Memorize IDs and extents to be able to clip the user's AOI to image on processing creation
        self.maxar_metadata_extents = {feature['featureId']: feature for feature in features}
        # Format decimals and dates
        for feature in features:
            feature['acquisitionDate'] = feature['acquisitionDate'][:16]  # no seconds
            if feature['offNadirAngle']:
                feature['offNadirAngle'] = round(feature['offNadirAngle'])
            if feature['cloudCover']:
                feature['cloudCover'] = round(feature['cloudCover'], 2)
        # Fill out the table
        self.dlg.maxarMetadataTable.setRowCount(len(features))
        # Row insertion triggers sorting -> row indexes shift -> duplicate rows, so turn sorting off
        self.dlg.maxarMetadataTable.setSortingEnabled(False)
        for row, feature in enumerate(features):
            for col, attr in enumerate(config.MAXAR_METADATA_ATTRIBUTES):
                try:
                    value = str(feature[attr])
                except KeyError:  # e.g. <colorBandOrder/> for pachromatic images
                    value = ''
                self.dlg.maxarMetadataTable.setItem(row, col, QTableWidgetItem(value))
        # Turn sorting on again
        self.dlg.maxarMetadataTable.setSortingEnabled(True)

    def get_maxar_image_id(self) -> str:
        """Return the Feature ID of the Maxar image selected in the metadata table, or empty string."""
        selected_cells = self.dlg.maxarMetadataTable.selectedItems()
        return selected_cells[config.MAXAR_METADATA_ID_COLUMN_INDEX].text() if selected_cells else ''

    def calculate_aoi_area(self, arg: Optional[Union[bool, QgsMapLayer, List[QgsFeature]]]) -> None:
        """Display the AOI size in sq.km.

        Users are charged by the amount of sq km they process. So it's important for them to know
        the size of the current AOI.
        An AOI must be a single feature, or the extent of a GeoTIFF layer, so the area is only displayed when either:
            a) the layer in the polygon combo has a single feature, or, if more, a single feature is selected in it
            b) 'Use image extent' is checked and the current raster combo entry is a GeoTIFF layer
        The area is calculated on the sphere if the CRS is geographical.

        Is called when the current layer has been changed in either of the combos in the processings tab.

        :param arg: A list of selected polygons (layer selection changed),
            a polygon or raster layer (combo item changed),
            or the state of the 'Use image extent' checkbox
        """
        if arg is None:  # 'virtual' layer: a web tile provider
            layer = self.dlg.polygonCombo.currentLayer()
            if not layer:
                self.dlg.labelAoiArea.setText('')
                return
        elif isinstance(arg, list) and not self.dlg.useImageExtentAsAoi.isChecked():  # feature selection changed
            layer = self.dlg.polygonCombo.currentLayer()
            # All polygon layers are monitored so have to check if it's the one in the combo
            if layer != self.iface.activeLayer():
                return
        elif isinstance(arg, bool):  # 'Use image extent as AOI' toggled
            combo = self.dlg.rasterCombo if arg else self.dlg.polygonCombo
            layer = combo.currentLayer()
            if not layer:
                self.dlg.labelAoiArea.setText('')
                return
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
            self.dlg.labelAoiArea.setText('')
            return
        layer_crs: QgsCoordinateReferenceSystem = layer.crs()
        if not layer_crs.authid():  # unidentified CRS; calculations may be erroneous
            self.dlg.labelAoiArea.setText('')
            return
        # Now, do the math
        calculator = QgsDistanceArea()
        # Set ellipsoid to calculate on sphere for geographic CRSs; default to 7030 (WGS84)
        calculator.setEllipsoid(layer_crs.ellipsoidAcronym() or 'EPSG:7030')
        calculator.setSourceCrs(layer_crs, self.project.transformContext())
        self.aoi_size = calculator.measureArea(aoi) / 10**6  # sq. m to sq.km
        label = self.tr('Area: {:.2f} sq.km').format(self.aoi_size)
        self.dlg.labelAoiArea.setText(label)

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
                    callback=lambda id_=id_: self.delete_processings_callback(id_)
                )

    def delete_processings_callback(self, id_: str) -> None:
        """Delete processings from the table after they've been successfully
        deleted from the server.
        """
        response = self.sender()  # calling self.sender().error() crashes; gotta save to local
        if not response.error():
            row = self.dlg.processingsTable.findItems(id_, Qt.MatchExactly)[0].row()
            self.processing_names.remove(self.dlg.processingsTable.item(row, 0).text())
            self.dlg.processingsTable.removeRow(row)
            self.processing_fetch_timer.start()

    def create_processing(self) -> None:
        """Create and start a processing on the server.

        The UI inputs are read, validated, and if valid, passed to a worker in a separate thread.
        This worker then post a requests to Mapflow and executes a callback based on the request outcome.

        Is called by clicking the 'Create processing' button.
        """
        processing_name = self.dlg.processingName.text()
        if not processing_name:
            self.alert(self.tr('Please, specify a name for your processing'))
            return
        if processing_name in self.processing_names:
            self.alert(self.tr('Processing name taken. Please, choose a different name.'))
            return
        if not (self.dlg.polygonCombo.currentLayer() or self.dlg.useImageExtentAsAoi.isChecked()):
            self.alert(self.tr('Please, select an area of interest'))
            return
        if self.remainingLimit < self.aoi_size:
            self.alert(self.tr('Processing limit exceeded'))
            return
        if self.aoi_area_limit < self.aoi_size:
            self.alert(self.tr(
                'Up to {} sq km can be processed at a time. '
                'Try splitting up your area of interest.'
            ).format(self.aoi_area_limit))
            return
        self.message_bar.pushInfo(self.plugin_name, self.tr('Starting the processing...'))
        imagery = self.dlg.rasterCombo.currentLayer()
        if imagery:  # check if local raster is a GeoTIFF
            path = imagery.dataProvider().dataSourceUri()
            if not os.path.splitext(path)[-1] in ('.tif', '.tiff'):
                self.alert(self.tr('Please, select a GeoTIFF layer'))
                return
        raster_option = self.dlg.rasterCombo.currentText()
        processing_params = {
            'name': processing_name,
            'wdName': self.dlg.modelCombo.currentText(),
            'meta': {  # optional metadata
                'source-app': 'qgis',
                'source': raster_option.lower()
            }
        }
        params = {}  # processing parameters
        transform_context = self.project.transformContext()
        providers = self.settings.value('providers')
        if raster_option in providers:
            params['raster_login'] = self.dlg.providerUsername.text()
            params['raster_password'] = self.dlg.providerPassword.text()
            params['url'] = providers[raster_option]['url']
            if raster_option in config.MAXAR_PRODUCTS:  # add Connect ID and CQL Filter, if any
                processing_params['meta']['source'] = 'maxar'
                if params['raster_login'] or params['raster_password']:  # user's own account
                    params['url'] += '&CONNECTID=' + providers[raster_option]['connectId']
                else:  # our account
                    processing_params['meta']['maxar_product'] = raster_option.split()[1].lower()
                image_id = self.get_maxar_image_id()
                if image_id:
                    params['url'] += f'&CQL_FILTER=feature_id=%27{image_id}%27'
            params['source_type'] = providers[raster_option]['type']
            if params['source_type'] == 'wms':
                params['target_resolution'] = 0.000005  # for the 18th zoom
            params['cache_raster_update'] = str(self.dlg.updateCache.isChecked())
            self.save_provider_auth()
        processing_params['params'] = params
        # Get processing AOI
        if self.dlg.useImageExtentAsAoi.isChecked():
            aoi_geometry = helpers.get_layer_extent(imagery, transform_context)
        else:
            aoi_layer = self.dlg.polygonCombo.currentLayer()
            # AOI must be either the only feature or the only selected feature in its layer
            feature_count = aoi_layer.featureCount()
            selected_features = list(aoi_layer.getSelectedFeatures())
            if feature_count == 1:
                aoi_feature = next(aoi_layer.getFeatures())
            elif len(selected_features) == 1:
                aoi_feature = selected_features[0]
            elif feature_count == 0:
                self.alert(self.tr('Your AOI layer is empty'))
                return
            else:
                self.alert(self.tr('Please, select a single feature in your AOI layer'))
                return
            aoi_geometry = aoi_feature.geometry()
            # Reproject it to WGS84 if the layer has another CRS
            layer_crs = aoi_layer.crs()
            if layer_crs != helpers.WGS84:
                aoi_geometry = helpers.to_wgs84(aoi_geometry, layer_crs, transform_context)
            # Clip AOI to image extent if a single Maxar image is requested
            selected_image = self.dlg.maxarMetadataTable.selectedItems()
            if raster_option in config.MAXAR_PRODUCTS and selected_image:
                aoi_layer = QgsVectorLayer('Polygon?crs=epsg:4326', '', 'memory')
                aoi = QgsFeature()
                aoi.setGeometry(aoi_geometry)
                aoi_layer.dataProvider().addFeatures([aoi])
                aoi_layer.updateExtents()
                # Create a temp layer for the image extent
                feature_id = selected_image[config.MAXAR_METADATA_ID_COLUMN_INDEX].text()
                image_extent_layer = QgsVectorLayer('Polygon?crs=epsg:4326', '', 'memory')
                extent = self.maxar_metadata_extents[feature_id]
                image_extent_layer.dataProvider().addFeatures([extent])
                aoi_layer.updateExtents()
                # Find the intersection and pass it to the worker
                intersection = qgis_processing.run(
                    'qgis:intersection',
                    {'INPUT': aoi_layer, 'OVERLAY': image_extent_layer, 'OUTPUT': 'memory:'}
                )['OUTPUT']
                aoi_geometry = next(intersection.getFeatures()).geometry()
        processing_params['geometry'] = json.loads(aoi_geometry.asJson())
        if not imagery:
            self.post_processing(processing_params)
            return
        # Upload the image to the server
        processing_params['meta']['source'] = 'tif'
        body = QHttpMultiPart(QHttpMultiPart.FormDataType)
        tif = QHttpPart()
        tif.setHeader(QNetworkRequest.ContentTypeHeader, 'image/tiff')
        tif.setHeader(QNetworkRequest.ContentDispositionHeader, 'form-data; name="file"; filename=""')
        image = QFile(path, body)
        image.open(QIODevice.ReadOnly)
        tif.setBodyDevice(image)
        body.append(tif)
        response = self.http.post(
            url=f'{self.server}/rastersmultipart',
            callback=lambda: self.upload_tif_callback(processing_params),
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
        response.uploadProgress.connect(
            lambda bytes_sent, bytes_total: self.upload_tif_progress(
                progress_message,
                bytes_sent,
                bytes_total
            )
        )

    def upload_tif_callback(self, processing_params: dict) -> None:
        """"""
        response = self.sender()
        if not response.error():
            processing_params['params']['url'] = json.loads(response.readAll().data())['url']
            self.post_processing(processing_params)

    def upload_tif_progress(self, message: QgsMessageBarItem, bytes_sent: int, bytes_total: int) -> None:
        """Display current upload progress in the message bar."""
        if bytes_total > 0:
            message.widget().setValue(round(bytes_sent / bytes_total * 100))
            if bytes_sent == bytes_total:
                self.message_bar.popWidget(message)

    def post_processing(self, request_body: dict) -> None:
        """"""
        self.http.post(
            url=f'{self.server}/processings',
            callback=self.post_processing_callback,
            body=json.dumps(request_body).encode()
        )

    def post_processing_callback(self) -> None:
        """Display a success message and clear the processing name field.

        This is a callback executed after a successful create processing request.
        """
        response = self.sender()
        error = response.error()
        if not error:
            self.alert(
                self.tr("Success! We'll notify you when the processing has finished."),
                QMessageBox.Information
            )
            self.dlg.processingName.clear()
        elif error == QNetworkReply.ContentAccessDenied:
            ErrorMessage(
                self.tr('You need to upgrade your subscription to process Maxar imagery. '),
                self.dlg
            ).show()
        else:
            ErrorMessage(
                self.tr('Processing creation failed: ') + response.errorString(),
                self.dlg
            ).show()

    def save_provider_auth(self) -> None:
        """Save provider credentials to settings if user checked the save option.

        Is called at three occasions: preview, processing creation and metadata request.
        """
        # Save the checkbox state itself
        self.settings.setValue('providerSaveAuth', self.dlg.providerSaveAuth.isChecked())
        # If checked, save the credentials
        if self.dlg.providerSaveAuth.isChecked():
            self.settings.setValue('providerUsername', self.dlg.providerUsername.text())
            self.settings.setValue('providerPassword', self.dlg.providerPassword.text())

    def preview(self) -> None:
        """Display raster tiles served over the Web.

        Is called by clicking the preview button.
        """
        self.save_provider_auth()
        username = self.dlg.providerUsername.text()
        password = self.dlg.providerPassword.text()
        provider = self.dlg.providerCombo.currentText()
        layer_name = provider
        provider_info = self.settings.value('providers')[provider]
        url = provider_info['url']
        if provider in config.MAXAR_PRODUCTS:
            if username or password:  # own account
                url += '&CONNECTID=' + provider_info['connectId']
                url = url.replace('jpeg', 'png')  # for transparency support
            else:  # our account; send to our endpoint
                url = self.server + '/png?TileRow={y}&TileCol={x}&TileMatrix={z}'
                url += '&CONNECTID=' + provider.split()[1].lower()
                username = self.username
                password = self.password
            image_id = self.get_maxar_image_id()  # request a single image if selected in the table
            if image_id:
                url += f'&CQL_FILTER=feature_id=%27{image_id}%27'
                row = self.dlg.maxarMetadataTable.currentRow()
                layer_name = ' '.join((
                    layer_name,
                    self.dlg.maxarMetadataTable.item(
                        row,
                        config.MAXAR_METADATA_ATTRIBUTES.index('acquisitionDate')
                    ).text(),
                    self.dlg.maxarMetadataTable.item(
                        row,
                        config.MAXAR_METADATA_ATTRIBUTES.index('productType')
                    ).text()
                ))
        # Can use urllib.parse but have to specify safe='/?:{}' which sort of defeats the purpose
        url_escaped = url.replace('&', '%26').replace('=', '%3D')
        params = {
            'type': provider_info['type'],
            'url': url_escaped,
            'zmax':  self.dlg.maxZoom.value(),
            'zmin': 0,
            'username': username,
            'password': password
        }
        uri = '&'.join(f'{key}={val}' for key, val in params.items())  # don't url-encode it
        layer = QgsRasterLayer(uri, layer_name, 'wms')
        if layer.isValid():
            self.add_layer(layer)
        else:
            self.alert(self.tr('Error loading: ') + url)

    def download_results(self, row: int) -> None:
        """Download and display processing results along with the source raster, if available.

        Results will be downloaded into the user's output directory.
        If it's unset, the user will be prompted to select one.
        Unfinished or failed processings yield partial or no results.

        Is called by double-clicking on a row in the processings table.

        :param int: Row number in the processings table (0-based)
        """
        if self.check_if_output_directory_is_selected():
            pid = self.dlg.processingsTable.item(row, config.PROCESSING_TABLE_ID_COLUMN_INDEX).text()
            self.http.get(
                url=f'{self.server}/processings/{pid}/result',
                callback=lambda: self.download_results_callback(pid),
                timeout=300
            )

    def download_results_callback(self, pid: str) -> None:
        """"""
        response = self.sender()
        if response.error():
            return
        processing = next(filter(lambda p: p['id'] == pid, self.processings))
        # Avoid overwriting existing files by adding (n) to their names
        output_path = os.path.join(self.dlg.outputDirectory.text(), processing['name'])
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
            self.message_bar.pushWarning(self.tr('Error loading results. Error code: ' + str(error)))
            return
        # Load the results into QGIS
        results_layer = QgsVectorLayer(output_path, processing['name'], 'ogr')
        results_layer.loadNamedStyle(os.path.join(
            self.plugin_dir,
            'static',
            'styles',
            config.STYLES.get(processing['workflowDef'], 'default') + '.qml'
        ))
        # Add the source raster (COG) if it has been created
        raster_url = processing['rasterLayer'].get('tileUrl')
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
                processing['name'] + '_image',
                'wms'
            )
        # Set image extent explicitly because as XYZ, it doesn't have one by default
        self.http.get(
            url=f'{self.server}/processings/{pid}/aois',
            callback=lambda: self.set_raster_extent(results_layer, raster)
        )

    def set_raster_extent(self, vector: QgsVectorLayer, raster: QgsRasterLayer) -> None:
        """"""
        response = self.sender()
        if response.error():
            return
        aoi_outer_ring = json.loads(response.readAll().data())[0]['geometry']['coordinates'][0]
        # Extract BBOX corners manually to construct a BBOX
        min_lon, *_, max_lon = sorted([point[0] for point in aoi_outer_ring])
        min_lat, *_, max_lat = sorted([point[1] for point in aoi_outer_ring])
        raster.setExtent(helpers.from_wgs84(
            QgsGeometry.fromRect(QgsRectangle(min_lon, min_lat, max_lon, max_lat)),
            raster.crs(),
            self.project.transformContext()
        ).boundingBox())
        # Add the layers to the project
        self.add_layer(vector)
        self.add_layer(raster)
        self.iface.zoomToActiveLayer()

    def alert(self, message: str, icon: QMessageBox.Icon = QMessageBox.Critical) -> None:
        """Display a minimalistic modal dialog with some info or a question.

        :param message: A text to display
        :param icon: Info/Warning/Critical/Question
        """
        return QMessageBox(icon, self.plugin_name, message, parent=self.dlg).exec() == QMessageBox.Ok

    def fill_out_processings_table(self) -> None:
        """Fill out the processings table with the processings in the user's default project.

        Is called by upon successful processing fetch.
        """
        response = self.sender()
        if response.error():
            return
        processings = json.loads(response.readAll().data())
        if sys.version_info.minor < 7:  # python 3.6 doesn't understand 'Z' as UTC
            for processing in processings:
                processing['created'] = processing['created'].replace('Z', '+0000')
        for processing in processings:
            # Add % signs to progress column for clarity
            processing['percentCompleted'] = f'{processing["percentCompleted"]}%'
            # Parse and localize creation datetime
            processing['created'] = datetime.strptime(
                processing['created'], '%Y-%m-%dT%H:%M:%S.%f%z'
            ).astimezone()
            # Extract WD names from WD objects
            processing['workflowDef'] = processing['workflowDef']['name']
        # Memorize which processings had been finished to alert user later
        env = self.server.split('-')[1].split('.')[0]
        all_finished = self.settings.value('finished_processings', {})
        previously_finished = all_finished.get(env, {}).get(self.username, [])
        now = datetime.now().astimezone()
        one_day = timedelta(1)
        finished = [
            processing['name'] for processing in processings
            if processing['percentCompleted'] == '100%'
            and now - processing['created'] < one_day
        ]
        # Update the list of finished processings for the given account
        if not all_finished.get(env):  # 1st assignment
            all_finished[env] = {}
        all_finished[env][self.username] = finished
        self.settings.setValue('finished_processings', all_finished)
        # Drop seconds to save space
        for processing in processings:
            processing['created'] = processing['created'].strftime('%Y-%m-%d %H:%M')
        # Memorize selected processings by id
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
        for row, processing in enumerate(processings):
            for col, attr in enumerate(('name', 'workflowDef', 'status', 'percentCompleted', 'created', 'id')):
                self.dlg.processingsTable.setItem(row, col, QTableWidgetItem(processing[attr]))
            if processing['id'] in selected_processings:
                self.dlg.processingsTable.selectRow(row)
        self.dlg.processingsTable.setSortingEnabled(True)
        # Restore extended selection
        self.dlg.processingsTable.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # Inform user about finished processings
        for processing in set(finished) - set(previously_finished):
            self.alert(
                processing + self.tr(' finished. Double-click it in the table to download the results.'),
                QMessageBox.Information
            )
            # Update user processing limit
            self.remainingLimit -= round(next(filter(
                lambda x: x['name'] == processing, processings
            ))['aoiArea']/10**6)
            self.dlg.remainingLimit.setText(self.tr('Processing limit: {} sq.km').format(self.remainingLimit))
        # Save as an instance attribute to reuse elsewhere
        self.processings = processings
        # Save ref to check name uniqueness at processing creation
        self.processing_names = [processing['name'] for processing in self.processings]

    def tr(self, message: str) -> str:
        """Localize a UI element text.

        :param message: A text to translate
        """
        # Don't use self.plugin_name as context since it'll be overriden in supermodules
        return QCoreApplication.translate(config.PLUGIN_NAME, message)

    def initGui(self) -> None:
        """Create the menu entries and toolbar icons inside the QGIS GUI.

        This function is referenced by the QGIS plugin loading system, so it can't be renamed.
        Since there are submodules, the various UI texts are set dynamically.
        """
        # Set main dialog title dynamically so it could be overridden when used as a submodule
        self.dlg.setWindowTitle(self.plugin_name)
        # Display plugin icon in own toolbar
        icon = QIcon(os.path.join(self.plugin_dir, 'icon.png'))
        plugin_button = QAction(icon, self.plugin_name, self.main_window)
        plugin_button.triggered.connect(self.main)
        self.toolbar.addAction(plugin_button)
        self.project.readProject.connect(self.set_layer_group)
        self.dlg.processingsTable.sortByColumn(4, Qt.DescendingOrder)

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
        for dlg in self.dlg, self.dlg_login, self.dlg_connect_id, self.dlg_provider:
            dlg.close()
        del self.toolbar

    def clean_up_login_dialog(self) -> None:
        """"""
        invalid_token_label = self.dlg_login.findChild(QLabel, 'invalidToken')
        self.dlg_login.token.clear()
        if invalid_token_label:
            invalid_token_label.deleteLater()
            new_size = self.dlg_login.width(), self.dlg_login.height() - invalid_token_label.height()
            self.dlg_login.setMaximumSize(*new_size)
            self.dlg_login.setMinimumSize(*new_size)

    def read_mapflow_token(self) -> None:
        """"""
        self.mapflow_auth = f'Basic {self.dlg_login.token.text()}'
        self.http.basic_auth = self.mapflow_auth
        self.log_in()

    def log_in(self) -> None:
        """Log into Mapflow."""
        mapflow_env = QgsSettings().value('variables/mapflow_env') or 'production'
        self.server = f'https://whitemaps-{mapflow_env}.mapflow.ai/rest'
        self.http.get(url=f'{self.server}/user/status', callback=self.log_in_callback)

    def logout(self) -> None:
        """Close the plugin and clear credentials from cache."""
        self.settings.remove('token')
        self.logged_in = False
        self.dlg_login.show()  # assume user wants to log into another account

    def handle_request_errors(self) -> None:
        """"""
        response = self.sender()
        error = response.error()
        if not error:
            return
        elif error == QNetworkReply.AuthenticationRequiredError:  # invalid/empty credentials
            if self.dlg_login.findChild(QLabel, 'invalidToken'):
                return  # the invalid credentials warning is already there
            invalid_token_label = QLabel(self.tr('Invalid token'), self.dlg_login)
            invalid_token_label.setObjectName('invalidToken')
            invalid_token_label.setStyleSheet('color: rgb(239, 41, 41);')
            self.dlg_login.layout().insertWidget(1, invalid_token_label, alignment=Qt.AlignCenter)
            new_size = self.dlg_login.width(), self.dlg_login.height() + invalid_token_label.height()
            self.dlg_login.setMaximumSize(*new_size)
            self.dlg_login.setMinimumSize(*new_size)
        elif error == QNetworkReply.HostNotFoundError:
            if not self.offline_alert.isVisible():
                self.offline_alert.setParent(self.main_window)
                self.offline_alert.show()
        elif error in (QNetworkReply.OperationCanceledError, QNetworkReply.ServiceUnavailableError):
            ErrorMessage(
                self.tr('Mapflow is not responding.\nPlease, try again later or send us an email.'),
                parent=self.main_window
            ).show()
        else:
            ErrorMessage(f'{error}: {response.errorString()}', parent=self.main_window).show()

    def get_default_project_callback(self) -> None:
        """"""
        response = self.sender()
        if response.error():
            return
        self.dlg.modelCombo.clear()
        self.dlg.modelCombo.addItems([
            wd['name'] for wd in json.loads(response.readAll().data())['workflowDefs']
        ])

    def log_in_callback(self) -> None:
        """"""
        response = self.sender()
        if response.error():
            return
        # Refresh the list of workflow definitions
        self.http.get(url=f'{self.server}/projects/default', callback=self.get_default_project_callback)
        # Fetch processings at startup
        self.http.get(url=f'{self.server}/processings', callback=self.fill_out_processings_table)
        # Keep fetching them at regular intervals afterwards
        self.processing_fetch_timer.start()
        self.logged_in = True  # allows skipping auth if the user's remembered
        token = self.mapflow_auth.split()[1]
        self.settings.setValue('token', token)
        self.username, self.password = b64decode(token).decode().split(':')
        user_status = json.loads(response.readAll().data())
        self.is_premium_user = user_status['isPremium']
        self.limit_max_zoom_for_maxar(self.dlg.providerCombo.currentText())
        self.remainingLimit = round(user_status['remainingLimit'])
        self.aoi_area_limit = round(user_status['aoiAreaLimit'])
        self.dlg.remainingLimit.setText(
            self.tr('Processing limit: {} sq.km').format(self.remainingLimit)
        )
        self.dlg_login.close()
        self.show_main_dialog()

    def show_main_dialog(self) -> None:
        """"""
        # Calculate area of the current AOI layer or feature
        combo = self.dlg.rasterCombo if self.dlg.useImageExtentAsAoi.isChecked() else self.dlg.polygonCombo
        self.calculate_aoi_area(combo.currentLayer())
        # Restore table section sizes
        for table in 'processingsTable', 'maxarMetadataTable':
            header = getattr(self.dlg, table).horizontalHeader()
            header.restoreState(self.settings.value(table + 'HeaderState', b''))
        # Show
        self.dlg.restoreGeometry(self.settings.value('mainDialogState', b''))
        self.dlg.show()

    def check_plugin_version_callback(self) -> None:
        """"""
        response = self.sender()
        if not response.error() and int(response.readAll().data()) != 1:
            QMessageBox.warning(
                self.main_window,
                self.plugin_name,
                self.tr(
                    'There is a new plugin version available.\n'
                    'Please, upgrade to make sure everything works as expected. '
                    'Go to Plugins -> Manage and Install Plugins -> Upgradable.'
                )
            )

    def main(self) -> None:
        """Plugin entrypoint.

        Is called by clicking the plugin icon.
        """
        # Check plugin version for compatibility with Processing API
        self.http.get(url=f'{self.server}/version', callback=self.check_plugin_version_callback)
        token = self.settings.value('token')
        if bool(token):  # token saved
            # Save Mapflow Basic Auth to be used with every request to Mapflow
            self.mapflow_auth = f'Basic {token}'
            self.http.basic_auth = self.mapflow_auth
            self.log_in()
        else:
            self.dlg_login.show()
