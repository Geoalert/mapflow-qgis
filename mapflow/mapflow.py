import sys  # Python version check for ensuring compatibility
import json
import os.path
from typing import List, Dict, Optional, Union
from datetime import datetime, timedelta  # processing creation datetime formatting
from configparser import ConfigParser  # parse metadata.txt -> QGIS version check (compatibility)

import requests
from PyQt5.QtCore import (
    QSettings, QCoreApplication, QTranslator, QPersistentModelIndex, QModelIndex,
    QThread, Qt
)
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QMessageBox, QFileDialog, QTableWidgetItem, QAction, QAbstractItemView, QLabel
)
from qgis import processing as qgis_processing  # to avoid collisions
from qgis.core import (
    QgsProject, QgsSettings, QgsMapLayer, QgsVectorLayer, QgsRasterLayer, QgsFeature,
    QgsCoordinateReferenceSystem, QgsDistanceArea, QgsGeometry, QgsMapLayerType, Qgis,
    QgsVectorFileWriter, QgsMessageLog
)

from .dialogs import MainDialog, LoginDialog, CustomProviderDialog, ConnectIdDialog
from .workers import ProcessingFetcher, ProcessingCreator
from . import helpers, config


class Mapflow:
    """This class represents the plugin.

    It is instantiated by QGIS and shouldn't be used directly.
    """

    def __init__(self, iface) -> None:
        """Initialize the plugin.

        :param iface: an instance of the QGIS interface.
        """
        # Save refs to key variables used throughout the plugin
        self.iface = iface
        self.main_window = iface.mainWindow()
        self.project = QgsProject.instance()
        self.plugin_dir = os.path.dirname(__file__)
        self.plugin_name = config.PLUGIN_NAME  # aliased here to be overloaded in submodules
        # QGIS Settings will be used to store user credentials and various UI element state
        self.settings = QgsSettings()
        # get the server environment to connect to (for admins)
        mapflow_env = self.settings.value('variables/mapflow_env')
        self.server = f'https://whitemaps-{mapflow_env or "production"}.mapflow.ai/rest'
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
        self.dlg_custom_provider = CustomProviderDialog(self.dlg)
        self.dlg_connect_id = ConnectIdDialog(self.dlg)
        self.red_border_style = 'border-color: rgb(239, 41, 41);'  # used to highlight invalid inputs
        self.timeout_alert = QMessageBox(
            QMessageBox.Warning, self.plugin_name,
            self.tr("Sorry, we couldn't connect to Mapflow. Please try again later."
                    'If the problem remains, please, send us an email to help@geoalert.io.'),
            parent=self.dlg
        )
        self.offline_alert = QMessageBox(
            QMessageBox.Information,
            self.plugin_name,
            self.tr('Mapflow requires Internet connection'),
            parent=self.dlg
        )
        # Display the plugin's version
        metadata_parser = ConfigParser()
        metadata_parser.read(os.path.join(self.plugin_dir, 'metadata.txt'))
        plugin_name_and_version = f'{self.plugin_name} {metadata_parser.get("general", "version")}'
        self.dlg.help.setText(self.dlg.help.text().replace('Mapflow', plugin_name_and_version))
        # Used for previewing a Maxar image by double-clicking its row
        self.current_maxar_metadata_product = ''
        # RESTORE LATEST FIELD VALUES & OTHER ELEMENTS STATE
        # Check if there are stored credentials
        self.logged_in = bool(self.settings.value('serverLogin') and self.settings.value('serverPassword'))
        self.dlg_login.username.setText(self.settings.value('serverLogin'))
        self.dlg_login.password.setText(self.settings.value('serverPassword'))
        self.dlg.outputDirectory.setText(self.settings.value('outputDir'))
        self.dlg.maxZoom.setValue(int(self.settings.value('maxZoom') or 18))
        if self.settings.value('customProviderSaveAuth'):
            self.dlg.customProviderSaveAuth.setChecked(True)
            self.dlg.customProviderLogin.setText(self.settings.value('customProviderLogin'))
            self.dlg.customProviderPassword.setText(self.settings.value('customProviderPassword'))
        # Restore custom providers
        self.custom_provider_config = os.path.join(self.plugin_dir, 'custom_providers.json')
        with open(self.custom_provider_config) as f:
            self.custom_providers = json.load(f)
        self.dlg.rasterCombo.setAdditionalItems((*self.custom_providers, 'Mapbox'))
        self.dlg.customProviderCombo.addItems(self.custom_providers)
        # Hide the ID columns as only needed for table operations, not the user
        self.dlg.processingsTable.setColumnHidden(config.PROCESSING_TABLE_ID_COLUMN_INDEX, True)
        self.dlg.rasterCombo.setCurrentText('Mapbox')  # otherwise SW will be set due to combo sync
        # SET UP SIGNALS & SLOTS
        # Memorize dialog element sizes & positioning
        self.dlg.finished.connect(self.save_dialog_state)
        # Connect buttons
        self.dlg.logoutButton.clicked.connect(self.logout)
        self.dlg.selectOutputDirectory.clicked.connect(self.select_output_directory)
        self.dlg.selectTif.clicked.connect(self.select_tif)
        # (Dis)allow the user to use raster extent as AOI
        self.dlg.rasterCombo.currentTextChanged.connect(self.toggle_use_image_extent_as_aoi)
        self.dlg.useImageExtentAsAoi.stateChanged.connect(lambda is_checked: self.dlg.polygonCombo.setEnabled(not is_checked))
        self.dlg.startProcessing.clicked.connect(self.create_processing)
        # Calculate AOI area
        self.dlg.polygonCombo.layerChanged.connect(self.calculate_aoi_area)
        self.dlg.rasterCombo.layerChanged.connect(self.calculate_aoi_area)
        self.dlg.useImageExtentAsAoi.toggled.connect(self.calculate_aoi_area)
        self.project.layersAdded.connect(self.monitor_polygon_layer_feature_selection)
        # Processings
        self.dlg.processingsTable.cellDoubleClicked.connect(self.download_processing_results)
        self.dlg.deleteProcessings.clicked.connect(self.delete_processings)
        # Custom provider
        self.dlg.preview.clicked.connect(self.preview)
        self.dlg.addCustomProvider.clicked.connect(self.add_custom_provider)
        self.dlg.editCustomProvider.clicked.connect(self.edit_provider)
        self.dlg.removeCustomProvider.clicked.connect(self.remove_custom_provider)
        self.dlg.maxZoom.valueChanged.connect(lambda value: self.settings.setValue('maxZoom', value))
        # Maxar
        self.dlg.maxarMetadataTable.itemSelectionChanged.connect(self.highlight_maxar_image)
        self.dlg.getImageMetadata.clicked.connect(self.get_maxar_metadata)
        self.dlg.maxarMetadataTable.cellDoubleClicked.connect(self.preview)
        self.dlg.customProviderCombo.currentTextChanged.connect(self.limit_max_zoom_for_maxar)

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

        By default, layers are added to a group with the same name as the plugin. If the group has been
        deleted by the user, assume they prefer to have the layers outside the group, and add them to root.
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

    def restore_maxar_metadata_product(self) -> None:
        """Reset provider combo to match the current metadata table state.

        SecureWatch single-image requests are constructed based on the current selection
        in the metadata table and with the current item in the provider list. The user may
        change list item after requesting metadata. To avoid ambiguity, this function set
        the provider combo to the current metadata product.
        """
        if (
            self.dlg.customProviderCombo.currentText() != self.current_maxar_metadata_product
            and self.dlg.maxarMetadataTable.selectedItems()
        ):
            self.dlg.customProviderCombo.setCurrentText(self.current_maxar_metadata_product)

    def highlight_maxar_image(self) -> None:
        """Select an image footprint in Maxar metadata layer when it's selected in the table.

        Is called by selecting (clicking on) a row in Maxar metadata table.
        """
        self.restore_maxar_metadata_product()
        selected_items = self.dlg.maxarMetadataTable.selectedItems()
        image_id = selected_items[config.MAXAR_METADATA_ID_COLUMN_INDEX].text() if selected_items else ''
        try:
            self.metadata_layer.selectByExpression(f"featureId='{image_id}'")
        except RuntimeError:  # layer has been deleted
            pass
        # Sync the raster combo in the Processing tab so user doesn't forget to set Maxar there
        self.dlg.rasterCombo.setCurrentText(self.dlg.customProviderCombo.currentText())

    def remove_custom_provider(self) -> None:
        """Delete a an entry from the list of providers and custom_providers.json.

        Is called by clicking the red minus button near the provider dropdown list.
        """
        provider = self.dlg.customProviderCombo.currentText()
        # Ask for confirmation
        if self.alert(self.tr('Permanently remove ') + provider + '?', 'question') == QMessageBox.No:
            return
        del self.custom_providers[provider]
        self.update_custom_provider_config()
        self.dlg.customProviderCombo.removeItem(self.dlg.customProviderCombo.currentIndex())
        self.dlg.rasterCombo.setAdditionalItems((*self.custom_providers, 'Mapbox'))

    def validate_custom_provider(self) -> None:
        """Check if provider inputs are valid. If not, outline the invalid field with red."""
        for attr in ('name', 'url'):
            field = getattr(self.dlg_custom_provider, attr)
            field_value = field.text()
            if field_value:
                field.setStyleSheet('')  # remove red outline if previously invalid
            else:
                field.setStyleSheet(self.red_border_style)
                return False
        return True

    def update_custom_provider_config(self) -> None:
        """Write changes to file after a provider has been added, removed or modified."""
        with open(self.custom_provider_config, 'w') as f:
            json.dump(self.custom_providers, f, indent=4)

    def clear_fields(self, *args) -> None:
        """Empty the fields and remove the red outline (invalid input signal), if any.

        :param args: A list of fields to clear.
        """
        for field in args:
            field.setStyleSheet('')
            field.setText('')

    def add_custom_provider(self) -> None:
        """Add a web imagery provider.

        Is called by the corresponding button.
        """
        while self.dlg_custom_provider.exec():
            if not self.validate_custom_provider():
                continue
            name = self.dlg_custom_provider.name.text()
            if name in self.custom_providers:
                self.alert(name + self.tr(' already exists. Click edit button to update it.'))
                break
            self.custom_providers[name] = {
                'url': self.dlg_custom_provider.url.text(),
                'type': self.dlg_custom_provider.type.currentText()
            }
            self.update_custom_provider_config()
            self.dlg.rasterCombo.setAdditionalItems((*self.custom_providers, 'Mapbox'))
            self.dlg.rasterCombo.setCurrentText(name)
            self.dlg.customProviderCombo.addItem(name)
            self.dlg.customProviderCombo.setCurrentText(name)
            break
        self.clear_fields(self.dlg_custom_provider.name, self.dlg_custom_provider.url)

    def edit_provider(self) -> None:
        """Edit a web imagery provider.

        Is called by the corresponding button.
        """
        provider = self.dlg.customProviderCombo.currentText()
        edit_method = self.edit_connect_id if provider in config.MAXAR_PRODUCTS else self.edit_custom_provider
        edit_method(provider)

    def edit_custom_provider(self, provider) -> None:
        """Change a provider's name, URL or type.

        :param provider: Provider's name, as in the config and dropdown list.
        """
        # Fill out the edit dialog with the current data
        self.dlg_custom_provider.setWindowTitle(provider)
        self.dlg_custom_provider.name.setText(provider)
        self.dlg_custom_provider.url.setText(self.custom_providers[provider]['url'])
        self.dlg_custom_provider.type.setCurrentText(self.custom_providers[provider]['type'])
        # Open the edit dialog
        while self.dlg_custom_provider.exec():
            if not self.validate_custom_provider():
                continue
            name = self.dlg_custom_provider.name.text()
            # Remove the old definition first
            del self.custom_providers[provider]
            # Add the new definition
            self.custom_providers[name] = {
                'url': self.dlg_custom_provider.url.text(),
                'type': self.dlg_custom_provider.type.currentText()
            }
            self.dlg.customProviderCombo.removeItem(self.dlg.customProviderCombo.currentIndex())
            self.update_custom_provider_config()
            self.dlg.rasterCombo.setAdditionalItems((*self.custom_providers, 'Mapbox'))
            self.dlg.customProviderCombo.addItem(name)
            self.dlg.customProviderCombo.setCurrentText(name)
            break
        self.clear_fields(self.dlg_custom_provider.name, self.dlg_custom_provider.url)

    def edit_connect_id(self, product) -> None:
        """Change the Connect ID for the given Maxar product.

        :param provider: Maxar product name, as in the config and dropdown list.
        """
        current_id = self.custom_providers[product]['connectId']
        self.dlg_connect_id.connectId.setText(current_id)
        # Specify the product being edited in the window title
        self.dlg_connect_id.setWindowTitle(f'{product} - {self.dlg_connect_id.windowTitle()}')
        while self.dlg_connect_id.exec():
            if not self.dlg_connect_id.connectId.hasAcceptableInput():
                self.dlg_connect_id.connectId.setStyleSheet(self.red_border_style)
                continue
            new_id = self.dlg_connect_id.connectId.text()
            self.custom_providers[product]['connectId'] = new_id
            self.update_custom_provider_config()
            break
        self.clear_fields(self.dlg_connect_id.connectId)

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
        enabled = provider in (*self.custom_providers, 'Mapbox')  # False if GeoTIFF
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
        # Memorize the product to prevent further errors if user changes item in the dropdown list
        self.current_maxar_metadata_product = self.dlg.customProviderCombo.currentText()
        params = config.MAXAR_METADATA_REQUEST_PARAMS.copy()
        try:
            params['CONNECTID'] = self.custom_providers[self.current_maxar_metadata_product]['connectId']
        except KeyError:
            self.alert(self.tr('Select a Maxar product in the provider list'))
            return
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
        aoi = aoi_feature.geometry()
        # Reproject to WGS84, if necessary
        layer_crs: QgsCoordinateReferenceSystem = aoi_layer.crs()
        if layer_crs != helpers.WGS84:
            aoi = helpers.to_wgs84(aoi, layer_crs, self.project.transformContext())
        # Get the '{min_lon},{min_lat} : {max_lon},{max_lat}' (SW-NE) representation of the AOI's bbox
        extent = aoi.boundingBox().toString()
        # Change lon,lat to lat,lon for Maxar
        coords = [reversed(position.split(',')) for position in extent.split(':')]
        params['BBOX'] = ','.join([coord.strip() for position in coords for coord in position])
        # Read credentials
        login = self.dlg.customProviderLogin.text()
        password = self.dlg.customProviderPassword.text()
        if login or password:  # user has their own account
            service = 'SecureWatch'
            method = 'get'
            kwargs = {
                'url': config.MAXAR_METADATA_URL,
                'params': params,
                'auth': (login, password),
                'timeout': 5
            }
        else:  # assume user wants to use our account, proxy thru Mapflow
            service = 'Mapflow'
            method = 'post'
            params = '&'.join(f'{key}={val}' for key, val in params.items())
            kwargs = {
                'url': self.server + '/meta',
                'json': {'url': config.MAXAR_METADATA_URL + '?' + params},
                'auth': (self.login, self.password),
                'timeout': 10
            }
        try:
            r = getattr(requests, method)(**kwargs)
        except (requests.ConnectionError, requests.Timeout):  # check for network errors
            self.alert(service + self.tr(' is not responding. Please, try again later.'))
            return
        try:
            r.raise_for_status()  # check for HTTP errors
        except requests.HTTPError:
            if r.status_code in (401, 403) and service == 'SecureWatch':
                self.alert(self.tr('Please, check your credentials'), kind='warning')
                return
            elif r.status_code >= 500:
                self.alert(service + self.tr(' is not responding. Please, try again later.'))
                return
        layer_name = f'{self.current_maxar_metadata_product} metadata'
        # Save metadata to a file; I couldn't get WFS to work, or else no file would be necessary
        output_file_name = os.path.join(
            self.dlg.outputDirectory.text(), f'{layer_name.lower().replace(" ", "_")}.gml'
        )
        with open(output_file_name, 'wb') as f:
            f.write(r.content)
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
            feature['acquisitionDate'] = feature['acquisitionDate'][:10]  # only date
            # Round up cloud cover to two decimal numbers if it's provided
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
        if arg is None:  # 'virtual' layer: Mapbox or custom provider
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
        # Now, do the math
        layer_crs: QgsCoordinateReferenceSystem = layer.crs()
        calculator = QgsDistanceArea()
        # Set ellipsoid to use spherical calculations for geographic CRSs
        calculator.setEllipsoid(layer_crs.ellipsoidAcronym() or 'EPSG:7030')  # WGS84 ellipsoid
        calculator.setSourceCrs(layer_crs, self.project.transformContext())
        self.aoi_size = calculator.measureArea(aoi) / 10**6  # sq. m to sq.km
        label = self.tr('Area: {:.2f} sq.km').format(self.aoi_size)
        self.dlg.labelAoiArea.setText(label)

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
            pid = self.dlg.processingsTable.item(row, config.PROCESSING_TABLE_ID_COLUMN_INDEX).text()
            name = self.dlg.processingsTable.item(row, 0).text()
            try:
                r = requests.delete(f'{self.server}/processings/{pid}', auth=self.server_basic_auth, timeout=5)
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
            self.alert(self.tr('Processing limit exceeded'), kind='critical')
            return
        if self.aoi_area_limit < self.aoi_size:
            self.alert(self.tr(
                'Up to {} sq km can be processed at a time. '
                'Try splitting up your area of interest.'
            ).format(self.aoi_area_limit), kind='critical')
            return
        auth_fields = (self.dlg.customProviderLogin.text(), self.dlg.customProviderPassword.text())
        if any(auth_fields) and not all(auth_fields):
            self.alert(self.tr('Invalid custom provider credentials'), kind='warning')
        update_cache = str(self.dlg.updateCache.isChecked())  # server fails if bool
        raster_option = self.dlg.rasterCombo.currentText()
        worker_kwargs = {
            'processing_name': processing_name,
            'server': self.server,
            'auth': self.server_basic_auth,
            'wd': self.dlg.modelCombo.currentText(),
            'meta': {  # optional metadata
                'source-app': 'qgis',
                'source': 'maxar' if raster_option in config.MAXAR_PRODUCTS else raster_option.lower()
            }
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
            worker_kwargs['meta']['source'] = 'tif'
            params['source_type'] = 'tif'
        elif raster_option != 'Mapbox':  # non-default provider
            params['url'] = self.custom_providers[raster_option]['url']
            if raster_option in config.MAXAR_PRODUCTS:  # add the Connect ID and CQL Filter, if any
                params['url'] += f'&CONNECTID={self.custom_providers[raster_option]["connectId"]}&'
                image_id = self.get_maxar_image_id()
                if image_id:
                    params['url'] += f'CQL_FILTER=feature_id=%27{image_id}%27'
            params['source_type'] = self.custom_providers[raster_option]['type']
            if params['source_type'] == 'wms':
                params['target_resolution'] = 0.000005  # for the 18th zoom
            params['cache_raster_update'] = update_cache
            params['raster_login'] = self.dlg.customProviderLogin.text()
            params['raster_password'] = self.dlg.customProviderPassword.text()
            self.save_custom_provider_auth()
        worker_kwargs['params'] = params
        if not self.dlg.useImageExtentAsAoi.isChecked():
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
                worker_kwargs['aoi'] = helpers.to_wgs84(
                    aoi_feature.geometry(),
                    layer_crs,
                    self.project.transformContext()
                )
            else:
                worker_kwargs['aoi'] = aoi_feature.geometry()
            # Clip AOI to image if a single Maxar image is requested
            selected_image = self.dlg.maxarMetadataTable.selectedItems()
            if raster_option in config.MAXAR_PRODUCTS and selected_image:
                # Recreate AOI layer; shall we change helpers.to_wgs84 to return layer, not geometry?
                aoi_layer = QgsVectorLayer('Polygon?crs=epsg:4326', 'aoi', 'memory')
                aoi = QgsFeature()
                aoi.setGeometry(worker_kwargs['aoi'])
                aoi_layer.dataProvider().addFeatures([aoi])
                aoi_layer.updateExtents()
                # Create a temp layer for the image extent
                feature_id = selected_image[config.MAXAR_METADATA_ID_COLUMN_INDEX].text()
                image_extent_layer = QgsVectorLayer('Polygon?crs=epsg:4326', 'image extent', 'memory')
                extent = self.maxar_metadata_extents[feature_id]
                image_extent_layer.dataProvider().addFeatures([extent])
                aoi_layer.updateExtents()
                # Find the intersection and pass it to the worker
                intersection = qgis_processing.run(
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
        worker.tif_uploaded.connect(
            lambda url: self.log(self.tr('Your image was uploaded to: ') + url, Qgis.Success)
        )
        worker.maxar_unauthorized.connect(lambda: self.alert(self.tr(
            'You need to upgrade your subscription to process Maxar imagery. '
            "Please, send us an email to help@geoalert.io if you'd like to."), kind='critical'
        ))
        worker.error.connect(
            lambda error: self.alert(self.tr('Processing creation failed: ') + error, kind='critical')
        )
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
        self.settings.setValue('customProviderSaveAuth', self.dlg.customProviderSaveAuth.isChecked())
        # If checked, save the credentials
        if self.dlg.customProviderSaveAuth.isChecked():
            self.settings.setValue('customProviderLogin', self.dlg.customProviderLogin.text())
            self.settings.setValue('customProviderPassword', self.dlg.customProviderPassword.text())

    def preview(self) -> None:
        """Display raster tiles served over the Web.

        Is called by clicking the preview button.
        """
        # Align the provider combo with the table
        self.restore_maxar_metadata_product()
        self.save_custom_provider_auth()
        username = self.dlg.customProviderLogin.text()
        password = self.dlg.customProviderPassword.text()
        provider = self.dlg.customProviderCombo.currentText()
        url = self.custom_providers[provider]['url']
        layer_name = provider
        if provider in config.MAXAR_PRODUCTS:
            if username or password:  # own account
                url = url.replace('jpeg', 'png')  # for transparency support
            else:  # our account; send to our endpoint
                url = self.server + '/png?TileRow={y}&TileCol={x}&TileMatrix={z}'
                username = self.login
                password = self.password
            url += f'&CONNECTID={self.custom_providers[provider]["connectId"]}'  # add product id
            image_id = self.get_maxar_image_id()  # request a single image if selected in the table
            if image_id:
                url += f'&CQL_FILTER=feature_id=%27{image_id}%27'
                layer_name = f'{layer_name} {image_id}'
        # Can use urllib.parse but have to specify safe='/?:{}' which sort of defeats the purpose
        url_escaped = url.replace('&', '%26').replace('=', '%3D')
        params = {
            'type': self.custom_providers[provider]['type'],
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
            self.alert(self.tr("Sorry, we couldn't load: ") + url)

    def download_processing_results(self, row: int) -> None:
        """Download and display processing results along with the source raster, if available.

        Results will be downloaded into the user's output directory. If unset, the user will be prompted to select one.
        If the processing hasn't finished yet or has failed, the resulting feature layer will be empty.

        Is called by double-clicking on a row in the processings table.

        :param int: Row number in the processings table (0-based)
        """
        if not self.check_if_output_directory_is_selected():
            return
        processing_name = self.dlg.processingsTable.item(row, 0).text()  # 0th column is Name
        pid = self.dlg.processingsTable.item(row, config.PROCESSING_TABLE_ID_COLUMN_INDEX).text()
        try:
            r = requests.get(f'{self.server}/processings/{pid}/result', auth=self.server_basic_auth)
        except requests.ConnectionError:
            self.offline_alert.show()
            return
        r.raise_for_status()
        # Add the source raster (COG) if it has been created
        tif_url = next(filter(lambda p: p['id'] == pid, self.processings))['rasterLayer'].get('tileUrl')
        if tif_url:
            params = {
                'type': 'xyz',
                'url': tif_url,
                'zmin': 0,
                'zmax': 18,
                'username': self.dlg_login.username.text(),
                'password': self.dlg_login.password.text()
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
        results_layer = QgsVectorLayer(output_path, processing_name, 'ogr')
        if not results_layer:
            self.push_message(self.tr("Couldn't load the results"), Qgis.Warning)
            return
        # Add a style
        wd = self.dlg.processingsTable.item(row, 1).text()
        style = os.path.join(self.plugin_dir, 'static', 'styles', f'{config.STYLES.get(wd, "default")}.qml')
        results_layer.loadNamedStyle(style)
        # Set image extent explicitly bc as XYZ, it have doesn't have one by default
        tif_layer.setExtent(helpers.from_wgs84(
            QgsGeometry.fromRect(results_layer.extent()),
            tif_layer.crs(),
            self.project.transformContext()
        ).boundingBox())
        # Add the layers to the project
        self.add_layer(tif_layer)
        self.add_layer(results_layer)
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
        user_namespace = self.login.split('@')[0] + '@' + self.server.split('-')[1].split('.')[0]
        finished_processings_setting = f'finishedProcessings_{user_namespace}'
        previously_finished = self.settings.value(finished_processings_setting, [])
        now = datetime.now().astimezone()
        one_day = timedelta(1)
        finished = [
            processing['name'] for processing in processings
            if processing['percentCompleted'] == '100%'
            and now - processing['created'] < one_day
        ]
        self.settings.setValue(finished_processings_setting, finished)
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
            self.alert(processing + self.tr(' finished. Double-click it in the table to download the results.'))
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
        self.dlg_login.setWindowTitle(self.plugin_name + ' - ' + self.tr('Log in'))
        # Display plugin icon in own toolbar
        icon = QIcon(os.path.join(self.plugin_dir, 'icon.png'))
        plugin_button = QAction(icon, self.plugin_name, self.main_window)
        plugin_button.triggered.connect(self.run)
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
        try:
            self.worker.thread().requestInterruption()
        except AttributeError:  # user quit QGIS or reload the plugin w/out first opening it
            pass
        for dlg in self.dlg, self.dlg_login, self.dlg_connect_id, self.dlg_custom_provider:
            dlg.close()
        del self.toolbar

    def connect_to_server(self) -> None:
        """Log into Mapflow.

        Is called at plugin startup.
        """
        # Get the server environment to connect to (for admins)
        mapflow_env = QgsSettings().value('variables/mapflow_env')
        self.server = f'https://whitemaps-{mapflow_env or "production"}.mapflow.ai/rest'
        # Read input credentials
        login = self.dlg_login.username.text()
        password = self.dlg_login.password.text()
        self.server_basic_auth = requests.auth.HTTPBasicAuth(login, password)
        try:
            res = requests.get(self.server + '/projects/default', auth=self.server_basic_auth, timeout=5)
            res.raise_for_status()
        except requests.ConnectionError:
            self.offline_alert.show()
        except requests.Timeout:
            self.timeout_alert.show()
        except requests.HTTPError:
            if res.status_code == 401 and not hasattr(self, 'invalid_credentials_label'):
                self.invalid_credentials_label = QLabel(self.tr('Invalid credentials'))
                self.invalid_credentials_label.setStyleSheet('color: rgb(239, 41, 41);')
                self.dlg_login.layout().insertWidget(1, self.invalid_credentials_label, alignment=Qt.AlignCenter)
                new_size = self.dlg_login.width(), self.dlg_login.height() + 21
                self.dlg_login.setMaximumSize(*new_size)
                self.dlg_login.setMinimumSize(*new_size)
        else:  # success!
            self.logged_in = True  # this var allows skipping auth if the user's remembered
            self.settings.setValue('serverLogin', login)
            self.settings.setValue('serverPassword', password)

    def logout(self) -> None:
        """Close the plugin and clear credentials from cache."""
        self.dlg.close()
        # Erase stored credentials
        self.settings.remove('serverLogin')
        self.settings.remove('serverPassword')
        self.logged_in = False
        # Stop monitoring processings
        self.worker.thread().requestInterruption()
        # Recreate the login dialog to start afresh
        self.dlg_login = LoginDialog(self.main_window)
        try:
            del self.invalid_credentials_label
        except AttributeError:
            pass
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
                try:
                    self.invalid_credentials_label.deleteLater()
                    del self.invalid_credentials_label
                    new_size = self.dlg_login.width(), self.dlg_login.height() - 21
                    self.dlg_login.setMaximumSize(*new_size)
                    self.dlg_login.setMinimumSize(*new_size)
                except AttributeError:
                    pass
                return
        # Refresh the list of workflow definitions
        self.login = self.dlg_login.username.text()
        self.password = self.dlg_login.password.text()
        self.server_basic_auth = requests.auth.HTTPBasicAuth(self.login, self.password)
        try:
            res = requests.get(self.server + '/projects/default', auth=self.server_basic_auth, timeout=5)
            user_status = requests.get(self.server + '/user/status', auth=self.server_basic_auth, timeout=5)
            res.raise_for_status()
            user_status.raise_for_status()
        except requests.ConnectionError:
            self.offline_alert.show()
            return
        except requests.Timeout:
            self.timeout_alert.show()
            return
        except requests.HTTPError:
            if res.status_code == 401:
                if not hasattr(self, 'invalid_credentials_label'):
                    self.invalid_credentials_label = QLabel(self.tr('Invalid credentials'))
                    self.invalid_credentials_label.setStyleSheet('color: rgb(239, 41, 41);')
                    self.dlg_login.layout().insertWidget(1, self.invalid_credentials_label, alignment=Qt.AlignCenter)
                    new_size = self.dlg_login.width(), self.dlg_login.height() + 21
                    self.dlg_login.setMaximumSize(*new_size)
                    self.dlg_login.setMinimumSize(*new_size)
                self.dlg_login.show()
                return
        wds = [wd['name'] for wd in res.json()['workflowDefs']]
        self.dlg.modelCombo.clear()
        self.dlg.modelCombo.addItems(wds)
        # Get user status
        user_status = user_status.json()
        self.is_premium_user = user_status['isPremium']
        self.limit_max_zoom_for_maxar(self.dlg.customProviderCombo.currentText())
        self.remainingLimit = round(user_status['remainingLimit'])
        self.aoi_area_limit = round(user_status['aoiAreaLimit'])
        self.dlg.remainingLimit.setText(self.tr('Processing limit: {} sq.km').format(self.remainingLimit))
        # Fetch processings
        thread = QThread(self.main_window)
        self.worker = ProcessingFetcher(self.server + '/processings', self.server_basic_auth)
        self.worker.moveToThread(thread)
        thread.started.connect(self.worker.fetch_processings)
        self.worker.fetched.connect(self.fill_out_processings_table)
        self.worker.error.connect(lambda error: self.log(error))
        self.worker.finished.connect(thread.quit)
        thread.start()
        # Calculate area of the current AOI layer or feature
        combo = self.dlg.rasterCombo if self.dlg.useImageExtentAsAoi.isChecked() else self.dlg.polygonCombo
        self.calculate_aoi_area(combo.currentLayer())
        # Restore table section sizes
        for table in 'processingsTable', 'maxarMetadataTable':
            header = getattr(self.dlg, table).horizontalHeader()
            header.restoreState(self.settings.value(table + 'HeaderState', b''))
        # Show main dialog
        self.dlg.restoreGeometry(self.settings.value('mainDialogState', b''))
        self.dlg.show()
