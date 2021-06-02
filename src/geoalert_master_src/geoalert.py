import time
import json
import os.path
from math import *
from threading import Thread

import requests
from dateutil.parser import parse as parse_datetime
from PyQt5 import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from qgis.core import *
from qgis.gui import *
from qgis.utils import iface
from qgis.PyQt.QtXml import QDomDocument

from . import helpers
from .resources_rc import *
from .geoalert_dialog import MainDialog, LoginDialog


PROCESSING_LIST_REFRESH_INTERVAL = 5  # in seconds
ID_COLUMN_INDEX = 5

SW_ENDPOINT = 'https://securewatch.digitalglobe.com/earthservice/wmtsaccess'
SW_PARAMS = {
    'SERVICE': 'WMTS',
    'VERSION': '1.0.0',
    'STYLE': '',
    'REQUEST': 'GetTile',
    'LAYER': 'DigitalGlobe:ImageryTileService',
    'FORMAT': 'image/jpeg',
    'TileRow': r'{y}',
    'TileCol': r'{x}',
    'TileMatrixSet': 'EPSG:3857',
    'TileMatrix': r'EPSG:3857:{z}'
}


class Geoalert:
    """Initialize the plugin."""

    def __init__(self, iface):
        self.iface = iface
        self.project = QgsProject.instance()
        self.plugin_dir = os.path.dirname(__file__)
        # Init toolbar and toolbar buttons
        self.actions = []
        self.toolbar = self.iface.addToolBar('Geoalert')
        self.toolbar.setObjectName('Geoalert')
        self.settings = QgsSettings()
        # Create a namespace for the plugin settings
        self.settings.beginGroup('geoalert')
        # Translation
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n', f'geoalert_{locale}.qm')
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)
        # Init dialogs and keep references
        self.dlg = MainDialog()
        self.dlg_login = LoginDialog()
        # RESTORE LATEST FIELD VALUES & OTHER ELEMENTS STATE
        if self.settings.value('serverRememberMe'):
            self.server = self.settings.value('server')
        self.dlg.outputDirectory.setText(self.settings.value('outputDir'))
        self.dlg.connectID.setText(self.settings.value('connectID'))
        self.dlg.custom_provider_url.setText(self.settings.value('customProviderURL'))
        if self.settings.value("customProviderRememberMe"):
            self.dlg.custom_provider_save_auth.setChecked(True)
            self.dlg.custom_provider_login.setText(self.settings.value("customProviderLogin"))
            self.dlg.custom_provider_password.setText(self.settings.value("customProviderPassword"))
        # Number of fixed 'virtual' layers in the raster combo box
        self.raster_combo_offset = 3
        # Store processings selected in the table as dict(id=row_number)
        self.selected_processings = {}
        # Fill out the combo boxes
        self.fill_out_combos_with_layers()
        # SET UP SIGNALS & SLOTS
        # Watch processing table row selection
        self.dlg.processingsTable.itemSelectionChanged.connect(self.memorize_selected_processings)
        # Hide the ID column since it's only needed for table operations, not the user
        # self.dlg.processingsTable.setColumnHidden(ID_COLUMN_INDEX, True)
        # Watch layer addition/removal
        self.project.layersAdded.connect(self.add_layers)
        self.project.layersRemoved.connect(self.remove_layers)
        self.dlg.logoutButton.clicked.connect(self.logout)
        # (Dis)allow the user to use raster extent as AOI
        self.dlg.rasterCombo.currentIndexChanged.connect(self.toggle_use_image_extent_as_aoi)
        self.dlg.useImageExtentAsAOI.stateChanged.connect(self.toggle_polygon_combo)
        # Select a local GeoTIFF if user chooses the respective option
        self.dlg.rasterCombo.currentTextChanged.connect(self.select_tif)
        self.dlg.startProcessing.clicked.connect(self.start_processing)
        # Download processing results
        self.dlg.loadProcessingResults.clicked.connect(self.download_processing_results)
        # кнопка удаления слоя
        self.dlg.deleteProcessings.clicked.connect(self.delete_processings)
        # Кнопка подключения снимков
        self.dlg.button_preview.clicked.connect(self.load_custom_tileset)
        # кнопка выбора папки через обзор
        self.dlg.selectOutputDirectory.clicked.connect(self.select_output_directory)
        # ввести стандартную максаровскую ссылку
        self.dlg.maxarStandardURL.clicked.connect(self.maxarStandard)
        # подключение слоя WFS
        self.dlg.ButWFS.clicked.connect(self.maxar_wfs)
        self.dlg.tabListRast.clicked.connect(self.feID)

    def fill_out_combos_with_layers(self):
        """Add all relevant (polygon & GeoTIFF) layer names to their respective combo boxes."""
        # Fetch the layers
        all_layers = self.project.mapLayers()
        # Split by type (only the relevant ones)
        polygon_layers = [layer for lid, layer in all_layers.items() if helpers.is_polygon_layer(layer)]
        tif_layers = [layer for lid, layer in all_layers.items() if helpers.is_geotiff_layer(layer)]
        # Fill out the combos
        self.dlg.polygonCombo.addItems([layer.name() for layer in polygon_layers])
        self.dlg.rasterCombo.addItems([layer.name() for layer in tif_layers])
        # Watch layer renaming
        for layer in polygon_layers + tif_layers:
            layer.nameChanged.connect(self.rename_layer)
        # Make and store a list of layer ids for addition & removal triggers
        self.polygon_layer_ids = [layer.id() for layer in polygon_layers]
        self.raster_layer_ids = [layer.id() for layer in tif_layers]

    def add_layers(self, layers):
        """Add layer_ids to combo boxes and memory."""
        for layer in layers:
            if helpers.is_geotiff_layer(layer):
                self.dlg.rasterCombo.addItem(layer.name())
                self.raster_layer_ids.append(layer.id())
                layer.nameChanged.connect(self.rename_layer)
            elif helpers.is_polygon_layer(layer):
                self.dlg.polygonCombo.addItem(layer.name())
                self.polygon_layer_ids.append(layer.id())
                layer.nameChanged.connect(self.rename_layer)

    def remove_layers(self, layer_ids):
        """Remove layer_ids from combo boxes and memory."""
        for lid in layer_ids:
            if lid in self.raster_layer_ids:
                self.dlg.rasterCombo.removeItem(self.raster_layer_ids.index(lid) + self.raster_combo_offset)
                self.raster_layer_ids.remove(lid)
            elif lid in self.polygon_layer_ids:
                self.dlg.polygonCombo.removeItem(self.polygon_layer_ids.index(lid))
                self.polygon_layer_ids.remove(lid)

    def rename_layer(self):
        """Update combo box contents when a project layer gets renamed."""
        # Remove all polygon combo entries
        self.dlg.polygonCombo.clear()
        # Remove all raster combo entries except 'virtual'
        for i in range(self.raster_combo_offset, self.dlg.rasterCombo.count()):
            self.dlg.rasterCombo.removeItem(i)
        # Now add all the relevant layer names to their combos again
        self.fill_out_combos_with_layers()

    def toggle_use_image_extent_as_aoi(self, index):
        """Toggle the checkbox depending on the item in the raster combo box."""
        enabled = index >= self.raster_combo_offset
        self.dlg.useImageExtentAsAOI.setEnabled(enabled)
        self.dlg.useImageExtentAsAOI.setChecked(enabled)
        self.dlg.updateCache.setEnabled(not enabled)
        self.dlg.updateCache.setChecked(not enabled)

    def toggle_polygon_combo(self, is_checked):
        """Enable/disable the polygon layer combo with reverse dependence on the use image extent as AOI checkbox."""
        self.dlg.polygonCombo.setEnabled(not is_checked)

    def select_output_directory(self):
        """Update the user's output directory."""
        path = QFileDialog.getExistingDirectory(self.iface.mainWindow())
        if path:
            self.dlg.outputDirectory.setText(path)
            self.settings.setValue("outputDir", path)

    def feID(self):
        # Вписываем feature ID из таблицы в поле
        # получить номер выбранной строки в таблице!
        row = self.dlg.tabListRast.currentIndex().row()
        id_v = self.dlg.tabListRast.model().index(row, 4).data()
        self.dlg.featureID.setText(str(id_v))

    def maxar_wfs(self):
        """Get SecureWatch image footprints."""
        # Check if user specified an existing output dir
        if not os.path.exists(self.dlg.outputDirectory.text()):
            self.alert(self.tr('Please, specify an existing output directory'))
            return
        aoi_layer = self.dlg.VMapLayerComboBox.currentLayer()
        connectID = self.dlg.connectID.text()
        self.settings.setValue('connectID', connectID)
        extent = self.get_layer_extent(aoi_layer).boundingBox().toString()
        # Change lon,lat to lat,lon for Maxar
        coords = [reversed(position.split(',')) for position in extent.split(':')]
        bbox = ','.join([coord.strip() for position in coords for coord in position])
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
        auth = requests.auth.HTTPBasicAuth(
            self.dlg.custom_provider_login.text(),
            self.dlg.custom_provider_password.text()
        )
        r = requests.get(url, params=params, auth=auth)
        r.raise_for_status()
        file_temp = os.path.join(self.dlg.outputDirectory.text(), 'WFS_temp.geojson')
        with open(file_temp, "wb") as f:
            f.write(r.content)
        layer_name = 'WFS extent'
        metadata_layer = QgsVectorLayer(file_temp, layer_name, "ogr")
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
        # Fill out the imagery table
        fields_names = [field.name() for field in metadata_layer.fields()]
        attributes = [feature.attributes() for feature in metadata_layer.getFeatures()]
        self.mTableListRastr(fields_names, attributes)

    def maxarStandard(self):
        """Fill out the imagery provider URL field with the Maxar Secure Watch URL."""
        connectID = self.dlg.connectID.text()
        featureID = self.dlg.featureID.text()
        SW_PARAMS['CONNECTID'] = connectID
        if featureID:
            SW_PARAMS['CQL_FILTER'] = f"feature_id='{featureID}'"
            SW_PARAMS['FORMAT'] = 'image/png'
        request = requests.Request('GET', SW_ENDPOINT, params=SW_PARAMS).prepare()
        self.dlg.custom_provider_url.setText(request.url)
        self.dlg.custom_provider_type.setCurrentIndex(0)
        self.settings.setValue('connectID', connectID)

    def mTableListRastr(self, nameFields, attrFields):
        # создание и настройка таблицы
        # очистка таблицы
        self.dlg.tabListRast.clear()
        # названия столбцов
        stolbci = ['featureId', 'sourceUnit', 'productType', 'colorBandOrder', 'formattedDate']

        listN = []
        # ищем номера столбцов по названиям
        for i in range(len(stolbci)):
            for n in range(len(nameFields)):
                if stolbci[i] == nameFields[n]:
                    print(stolbci[i], n)
                    listN.append(n)
        # print(listN)

        stolbci = []  # обнуляем, дальше код заполнит их сам
        # содержимое столбцов
        attrStolb = []
        # список номерв столбцов, которые нужно добавить в таблицу
        # listN = [1,4,6,7,17,24]
        # выбираем только нужные столбцы и добавляем их в отдельные списки
        # перебор атрибутов всех объектов
        for fi in attrFields:
            # промежуточный список атрибутов для одного объекта
            at = []
            for n in reversed(range(len(nameFields))):
                if n in listN:
                    # заполняем список названий (пока не достигним их максимального количества)
                    if len(listN) > len(stolbci):
                        stolbci.append(nameFields[n])
                    at.append(fi[n])
            attrStolb.append(at)
        #     print(at)
        # print(stolbci)
        # сортировка обработок в в списке по дате в обратном порядке
        attrStolb.sort(reverse=True)
        # print(attrStolb)
        # количество столбцов
        StolbKol = len(stolbci)
        self.dlg.tabListRast.setColumnCount(StolbKol)  # создаем столбцы
        self.dlg.tabListRast.setHorizontalHeaderLabels(stolbci)  # даем названия столбцам
        # перебор всех столбцов и настройка
        for nom in range(StolbKol):
            # Устанавливаем выравнивание на заголовки
            self.dlg.tabListRast.horizontalHeaderItem(nom).setTextAlignment(Qt.AlignCenter)
        # указываем ширину столбцов
        # self.dlg.tabListRast.setColumnWidth(0, 80)
        # выделять всю строку при нажатии
        self.dlg.tabListRast.setSelectionBehavior(QAbstractItemView.SelectRows)
        # запретить редактировать таблицу пользователю
        self.dlg.tabListRast.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # включить сортировку в таблице
        # self.dlg.tabListRast.setSortingEnabled(True)
        kol_tab = len(attrStolb)  # количество элементов
        self.dlg.tabListRast.setRowCount(kol_tab)  # создаем строки таблицы
        # заполнение таблицы значениями
        for x in range(len(attrStolb)):
            for y in range(len(attrStolb[x])):
                container = QTableWidgetItem(str(attrStolb[x][y]))
                self.dlg.tabListRast.setItem(x, y, container)

    def memorize_selected_processings(self):
        """Memorize the currently selected processing by its ID."""
        self.selected_processings = {
            cell.text(): cell.row()
            for cell in self.dlg.processingsTable.selectedItems()
            if cell.column() == ID_COLUMN_INDEX
        }

    def delete_processings(self):
        """Delete one or more processings on the server."""
        for pid, row_number in self.selected_processings.items():
            r = requests.delete(
                url=f'{self.server}/rest/processings/{pid}',
                auth=self.server_basic_auth
            )
            r.raise_for_status()
            self.dlg.processingsTable.removeRow(row_number)
            self.push_message(self.tr("Processing successfully deleted!"))

    def select_tif(self, text):
        """Start a file selection dialog for a local GeoTIFF."""
        if not text == self.tr('Open new .tif'):
            return
        dlg = QFileDialog(self.iface.mainWindow(), self.tr("Select GeoTIFF"))
        dlg.setMimeTypeFilters(['image/tiff'])
        if dlg.exec():
            path = dlg.selectedFiles()[0]
            layer_name = os.path.basename(path).split('.')[0]
            self.iface.addRasterLayer(path, layer_name)
            self.dlg.rasterCombo.setCurrentText(layer_name)

    def start_processing(self):
        """Spin up a thread to create a processing on the server."""
        processing_name = self.dlg.processingName.text()
        if not processing_name:
            self.alert(self.tr('Please, specify a name for your processing'))
            return
        elif processing_name in self.processing_names:
            self.alert(self.tr('Processing name taken. Please, choose a different name.'))
            return
        raster_combo_index = self.dlg.rasterCombo.currentIndex()
        if raster_combo_index == 1:
            self.alert(self.tr("Please, be aware that you may be charged by the imagery provider!"))
        elif raster_combo_index > 2:
            self.push_message(self.tr("Please, wait. Uploading the file to the server..."))
        thread = Thread(target=self.create_processing)
        thread.start()
        # self.refresh_processing_list(f'{self.server}/rest/processings')
        self.dlg.processingName.clear()
        self.alert(self.tr("Success! Processing may take up to several minutes"))
        # print('STARTING TASK')
        # task = QgsTask.fromFunction(
        #     'Create processing', self.create_processing, on_finished=self.after_create_processing)
        # QgsApplication.taskManager().addTask(task)

    def create_processing(self):
        """Initiate a processing."""
        # QgsMessageLog.logMessage(self.tr(f'TASK STARTED'), 'Mapflow', Qgis.Info)
        processing_name = self.dlg.processingName.text()
        wd = self.dlg.ai_model.currentText()
        update_cache = str(not self.dlg.updateCache.isChecked())
        aoi_layer = self.project.mapLayer(self.polygon_layer_ids[self.dlg.polygonCombo.currentIndex()])
        # Workflow definition parameters
        params = {}
        # Optional metadata
        meta = {"source-app": "qgis"}
        # Imagery selection
        raster_combo_index = self.dlg.rasterCombo.currentIndex()
        # Mapbox
        if raster_combo_index == 0:
            meta['source'] = 'mapbox'
            params["use_cache"] = update_cache
        # Custom provider
        if raster_combo_index == 1:
            params["source_type"] = self.dlg.custom_provider_type.currentText()
            params["url"] = self.dlg.custom_provider_url.text()
            params["raster_login"] = self.dlg.custom_provider_login.text()
            params["raster_password"] = self.dlg.custom_provider_password.text()
            params["use_cache"] = update_cache
        elif raster_combo_index > 2:
            # Upload user-selected GeoTIFF to the server
            raster_layer_id = self.raster_layer_ids[self.dlg.rasterCombo.currentIndex() - self.raster_combo_offset]
            raster_layer = self.project.mapLayer(raster_layer_id)
            with open(raster_layer.dataProvider().dataSourceUri(), 'rb') as f:
                r = requests.post(f'{self.server}/rest/rasters', auth=self.server_basic_auth, files={'file': f})
            r.raise_for_status()
            url = r.json()['uri']
            # QgsMessageLog.logMessage(self.tr(f'Your image was uploaded to ') + url, 'Mapflow', Qgis.Info)
            params["source_type"] = "tif"
            params["url"] = url
            if self.dlg.useImageExtentAsAOI.isChecked():
                aoi_layer = raster_layer
        # Get processing extent
        extent = self.get_layer_extent(aoi_layer)
        # Post the processing
        r = requests.post(
            url=f'{self.server}/rest/processings',
            auth=self.server_basic_auth,
            json={
                "name": processing_name.encode(),
                "wdName": wd,
                "geometry": json.loads(extent.asJson()),
                "params": params,
                "meta": meta
            })
        r.raise_for_status()

    # def after_create_processing(self, result=None):
    #     """"""
    #     print(result)
    #     self.refresh_processing_list(f'{self.server}/rest/processings')
    #     self.check_processings = True
    #     self.dlg.processingName.clear()
    #     self.alert(self.tr("Success! Processing may take up to several minutes"))

    def load_custom_tileset(self):
        """Custom provider imagery preview."""
        # Save the checkbox state itself
        self.settings.setValue("custom_provider_save_auth", self.dlg.custom_provider_save_auth.isChecked())
        # If checked, save the credentials
        if self.dlg.custom_provider_save_auth.isChecked():
            self.settings.setValue("customProviderLogin", self.dlg.custom_provider_login.text())
            self.settings.setValue("customProviderPassword", self.dlg.custom_provider_password.text())
        url = self.dlg.custom_provider_url.text()
        self.settings.setValue('customProviderURL', url)
        url_escaped = url.replace('&', '%26').replace('=', '%3D')
        params = {
            'type': self.dlg.custom_provider_type.currentText(),
            'url': url_escaped,
            'zmax': 14 if self.dlg.custom_provider_limit_zoom.isChecked() else 18,
            'zmin': 0,
            'username': self.dlg.custom_provider_login.text(),
            'password': self.dlg.custom_provider_password.text()
        }
        uri = '&'.join(f'{key}={val}' for key, val in params.items())
        layer = QgsRasterLayer(uri, self.tr('Custom tileset'), 'wms')
        if not layer.isValid():
            self.alert(self.tr('Invalid custom imagery provider:') + url_escaped)
        else:
            self.project.addMapLayer(layer)

    def download_processing_results(self):
        """Download the resulting features and open them in QGIS."""
        # Check if user specified an existing output dir
        if not os.path.exists(self.dlg.outputDirectory.text()):
            self.alert(self.tr('Please, specify an existing output directory'))
            return

        for pid, row_number in self.selected_processings.items():
            r = requests.get(f'{self.server}/rest/processings/{pid}/result', auth=self.server_basic_auth)
            output_file_name = self.dlg.processingsTable.item(row_number, 0).text()  # 0th column is Name
            # Add GeoTIFF that was used in the processing
            tif_url = [processing['rasterLayer']['tileUrl'] for processing in self.processings if processing['id'] == pid][0]
            params = {
                'type': 'xyz',
                'url': tif_url,
                'zmin': 0,
                'zmax': 18,
                'username': self.dlg_login.loginField.text(),
                'password': self.dlg_login.passwordField.text()
            }
            uri = '&'.join(f'{key}={val}' for key, val in params.items())
            tif_layer = QgsRasterLayer(uri, f'{output_file_name}_image', 'wms')
            self.project.addMapLayer(tif_layer)
        # временный файл
        file_temp = os.path.join(self.dlg.outputDirectory.text(), f'{output_file_name}_temp.geojson')
        with open(file_temp, "wb") as f:
            f.write(r.content)
        feature_layer = QgsVectorLayer(file_temp, output_file_name+'_temp', "ogr")

        # экспорт в shp
        file_adr = os.path.join(self.dlg.outputDirectory.text(), f'{output_file_name}.shp')
        error, msg = QgsVectorFileWriter.writeAsVectorFormat(
            feature_layer,
            file_adr,
            "utf-8",
            QgsCoordinateReferenceSystem('EPSG:4326'),
            "ESRI Shapefile"
        )
        if error:
            self.push_message(self.tr('There was an error writing the Shapefile!'), Qgis.Warning)
            return

        # Load the results into QGSI
        results_layer = QgsVectorLayer(file_adr, output_file_name, "ogr")
        if not results_layer:
            self.push_message(self.tr("Could not load the layer!"), Qgis.Warning)
        self.project.addMapLayer(results_layer)
        # Add style
        wd = self.dlg.processingsTable.item(row_number, 1).text()
        if wd in ('Buildings Detection', 'Buildings Detection With Heights'):
            style = '/styles/style_buildings.qml'
        elif wd == 'Forest Detection':
            style = '/styles/style_forest.qml'
        elif wd == 'Forest Detection With Heights':
            style = '/styles/style_forest_with_heights.qml'
        elif wd == 'Roads Detection':
            style = '/styles/style_roads.qml'
        else:
            style = '/styles/style_default.qml'

        # подключаем стиль!!!!!!!!!!!!!!!!!!
        qml_path = self.plugin_dir + style
        layer = self.iface.activeLayer()
        style_manager = layer.styleManager()
        # read valid style from layer
        style = QgsMapLayerStyle()
        style.readFromLayer(layer)
        # get style name from file
        style_name = os.path.basename(qml_path).strip('.qml')
        # add style with new name
        style_manager.addStyle(style_name, style)
        # set new style as current
        style_manager.setCurrentStyle(style_name)
        # load qml to current style
        message, success = layer.loadNamedStyle(qml_path)
        if not success:  # if style not loaded remove it
            style_manager.removeStyle(style_name)

        time.sleep(1)
        iface.zoomToActiveLayer()
        os.remove(file_temp)

    def alert(self, message):
        """Display an info message."""
        QMessageBox.information(self.dlg, 'Mapflow', message)

    def push_message(self, text, level=Qgis.Info, duration=5):
        """Display a translated message on the message bar."""
        self.iface.messageBar().pushMessage("Mapflow", text, level, duration)

    def get_layer_extent(self, layer):
        """Get a layer's bounding box (extent)."""
        # Create a geometry from the layer's extent
        extent_geometry = QgsGeometry.fromRect(layer.extent())
        # Reproject it to WGS84 if the layer has another CRS
        layer_crs = QgsCoordinateReferenceSystem(layer.crs().authid())
        wgs84 = QgsCoordinateReferenceSystem('EPSG:4326')
        transform = QgsCoordinateTransform(layer_crs, wgs84, self.project.transformContext())
        if layer_crs != wgs84:
            extent_geometry.transform(transform)
        # # Create a feature with the resulting geometry
        # extent_feature = QgsFeature()
        # extent_feature.setGeometry(extent_geometry)
        # # Make a temp layer out of it (for the user to see the extent)
        # extent_layer = QgsVectorLayer(f"Polygon?crs=EPSG:4326", f"{layer.name()} extent", 'memory')
        # extent_layer.dataProvider().addFeature(extent_feature)
        # self.project.addMapLayer(extent_layer)
        return extent_geometry

    def refresh_processing_list(self, url):
        """Repeatedly refresh the list of processings."""
        while self.check_processings:
            # Fetch all user processings visible to the user
            r = requests.get(url, auth=self.server_basic_auth)
            r.raise_for_status()
            self.processings = r.json()
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
                processing['created'] = local_datetime.strftime('%Y-%m-%d %H:%m')
                # Extract WD names from WD objects
                processing['workflowDef'] = processing['workflowDef']['name']
            # Check for active processings and set flag to keep polling
            self.check_processings = bool([p for p in self.processings if p['status'] in ("IN_PROGRESS", "UNPROCESSED")])
            # Turn sorting off while inserting
            self.dlg.processingsTable.setSortingEnabled(False)
            # Fill out the table
            columns = ('name', 'workflowDef', 'status', 'percentCompleted', 'created', 'id')
            for row, processing in enumerate(self.processings):
                for col, attr in enumerate(columns):
                    self.dlg.processingsTable.setItem(row, col, QTableWidgetItem(processing[attr]))
                # Restore selection
                row_number = self.selected_processings.get(processing['id'])
                if row_number:
                    self.dlg.processingsTable.selectRow(row_number)
            # Turn sorting on again
            self.dlg.processingsTable.setSortingEnabled(True)
            # Sort by creation date (5th column) descending
            self.dlg.processingsTable.sortItems(4, Qt.DescendingOrder)
            # Check on the running processings after some time
            if self.check_processings:
                time.sleep(PROCESSING_LIST_REFRESH_INTERVAL)

    def tr(self, message):
        return QCoreApplication.translate('Geoalert', message)

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
            text='Geoalert',
            callback=self.run,
            parent=self.iface.mainWindow())

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        self.dlg.close()
        self.dlg_login.close()
        for action in self.actions:
            self.iface.removePluginVectorMenu('Geoalert', action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar

    def connect_to_server(self):
        """Connect to Geoalert server."""
        self.server = f'https://whitemaps-{self.dlg_login.serverCombo.currentText()}.mapflow.ai'
        login = self.dlg_login.loginField.text().encode()
        password = self.dlg_login.passwordField.text().encode()
        remember_me = self.dlg_login.rememberMe.isChecked()
        self.settings.setValue("serverRememberMe", remember_me)
        self.server_basic_auth = requests.auth.HTTPBasicAuth(login, password)
        try:
            res = requests.get(f'{self.server}/rest/projects/default', auth=self.server_basic_auth)
            res.raise_for_status()
            # Load the list of WDs in the default project
            wds = [wd['name'] for wd in res.json()['workflowDefs']]
            self.dlg.ai_model.clear()
            self.dlg.ai_model.addItems(wds)
            self.logged_in = True
            if remember_me:
                self.settings.setValue('serverLogin', login)
                self.settings.setValue('serverPassword', password)
                self.settings.setValue('server', self.server)
        except requests.exceptions.HTTPError:
            if res.status_code == 401:
                self.dlg_login.invalidCredentialsMessage.setVisible(True)

    def logout(self):
        """Close the plugin and clear credentials from cache."""
        self.dlg.close()
        for setting in ('serverLogin', 'serverPassword', 'serverRememberMe'):
            self.settings.setValue(setting, '')

    def run(self):
        """Plugin entrypoint."""
        # Check if there are stored credentials
        self.logged_in = self.settings.value("serverLogin") and self.settings.value("serverPassword")
        # If not, show the login form
        while not self.logged_in:
            # If the user hits OK, - try to log in
            if self.dlg_login.exec():
                self.connect_to_server()
            else:
                # Refresh the form & quit
                self.dlg_login.loginField.clear()
                self.dlg_login.passwordField.clear()
                self.dlg_login.invalidCredentialsMessage.hide()
                return
        # If logged in successfully, start polling the server for the list of processings
        self.check_processings = True
        url = f'{self.server}/rest/processings'
        proc = Thread(target=self.refresh_processing_list, args=(url,))
        proc.start()
        # Show main dialog
        self.dlg.show()
        # Stop refreshing the processing list once the dialog has been closed
        self.check_processings = bool(self.dlg.exec())
