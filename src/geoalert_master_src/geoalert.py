import time
import json
import os.path
from math import *
from base64 import b64encode
from threading import Thread
from pathlib import Path

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
        # Save ref to output dir ('' if plugin loaded 1st time or cache cleaned manually)
        self.output_dir = self.settings.value('outputDir')
        # Init dialogs and keep references
        self.dlg = MainDialog()
        self.dlg_login = LoginDialog()
        # RESTORE LATEST FIELD VALUES & OTHER ELEMENTS STATE
        self.dlg.output_directory.setText(self.output_dir)
        self.dlg.connectID.setText(self.settings.value('connectID'))
        self.dlg.custom_provider_url.setText(self.settings.value('customProviderURL'))
        if self.settings.value("customProviderRememberMe"):
            self.dlg.custom_provider_save_auth.setChecked(True)
            self.dlg.custom_provider_login.setText(self.settings.value("customProviderLogin"))
            self.dlg.custom_provider_password.setText(self.settings.value("customProviderPassword"))
        # Number of fixed 'virtual' layers in the raster combo box
        self.rasterComboOffset = 3
        # Fill out the combo boxes
        self.fill_out_combos_with_layers()
        # SET UP SIGNALS & SLOTS
        # Watch layer addition/removal
        self.project.layersAdded.connect(self.add_layers)
        self.project.layersRemoved.connect(self.remove_layers)
        self.dlg.logoutButton.clicked.connect(self.logout)
        # (Dis)allow the user to use raster extent as AOI
        self.dlg.rasterCombo.currentIndexChanged.connect(self.toggle_use_image_extent_as_aoi)
        self.dlg.useImageExtentAsAOI.stateChanged.connect(self.toggle_polygon_combo)
        # загрузить выбраный результат
        self.dlg.ButtonDownload.clicked.connect(self.addSucces)
        # Кнопка: Выгрузить слой на сервер для обработки
        self.dlg.ButtonUpload.clicked.connect(self.uploadOnServer)
        # кнопка удаления слоя
        self.dlg.ButtonDel.clicked.connect(self.DelLay)
        # Кнопка подключения снимков
        self.dlg.button_preview.clicked.connect(self.load_custom_tileset)
        # кнопка выбора папки через обзор
        self.dlg.but_dir.clicked.connect(self.select_output_dir)
        # ввести стандартную максаровскую ссылку
        self.dlg.maxarStandardURL.clicked.connect(self.maxarStandard)
        # срабатывает при выборе источника снимков в комбобоксе
        self.dlg.rasterCombo.activated.connect(self.comboClick)
        # подключение слоя WFS
        self.dlg.ButWFS.clicked.connect(self.ButWFS)
        self.dlg.tabListRast.clicked.connect(self.feID)

    def feID(self):
        # Вписываем feature ID из таблицы в поле
        # получить номер выбранной строки в таблице!
        row = self.dlg.tabListRast.currentIndex().row()
        print(row)
        id_v = self.dlg.tabListRast.model().index(row, 4).data()
        print(id_v)
        self.dlg.featureID.setText(str(id_v))

    def fill_out_combos_with_layers(self):
        """Add all relevant (polygon & GeoTIFF) layer names to their respective combo boxes."""
        # Fetch the layers
        all_layers = self.project.mapLayers()
        # Split by type (only the relevant ones)
        polygon_layers = [layer for lid, layer in all_layers.items() if helpers.is_polygon_layer(layer)]
        tif_layers = [layer for lid, layer in all_layers.items() if helpers.is_geotiff_layer(layer)]
        # Fill out the combos
        self.dlg.polygonCombo.addItems([layer.name() for layer in polygon_layers])
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
                self.dlg.rasterCombo.removeItem(self.raster_layer_ids.index(lid) + self.rasterComboOffset)
                self.raster_layer_ids.remove(lid)
            elif lid in self.polygon_layer_ids:
                self.dlg.polygonCombo.removeItem(self.polygon_layer_ids.index(lid))
                self.polygon_layer_ids.remove(lid)

    def rename_layer(self):
        """Update combo box contents when a project layer gets renamed."""
        # Remove all polygon combo entries
        self.dlg.polygonCombo.clear()
        # Remove all raster combo entries except 'virtual'
        for i in range(self.rasterComboOffset, self.dlg.polygonCombo.count()):
            self.dlg.rasterCombo.removeItem(i)
        # Now add all the relevant layer names to their combox again
        self.fill_out_combos_with_layers()

    def toggle_use_image_extent_as_aoi(self, index):
        """Toggle the checkbox depending on the item in the raster combo box."""
        enabled = index >= self.rasterComboOffset
        self.dlg.useImageExtentAsAOI.setEnabled(enabled)
        self.dlg.useImageExtentAsAOI.setChecked(enabled)

    def toggle_polygon_combo(self, is_checked):
        """Enable/disable the polygon layer combo with reverse dependence on the use image extent as AOI checkbox."""
        self.dlg.polygonCombo.setEnabled(not is_checked)

    def ButWFS(self):
        # получаем введенный логин и праоль
        self.loginW = self.dlg.custom_provider_login.text()
        self.passwordW = self.dlg.custom_provider_password.text()
        # векторный слой
        vLayer = self.dlg.VMapLayerComboBox.currentLayer()
        # получаем координаты охвата в EPSG:4326
        coordin = self.extent(vLayer)
        # self.serverW = self.dlg.custom_provider_url.text()

        connectID = self.dlg.connectID.text()

        # сохрангить ID
        self.settings.setValue('connectID', connectID)

        URL = "https://securewatch.digitalglobe.com/catalogservice/wfsaccess?" \
              "REQUEST=GetFeature&TYPENAME=DigitalGlobe:FinishedFeature&" \
              "SERVICE=WFS&VERSION=2.0.0&" \
              "CONNECTID=%s&" \
              "BBOX=%s&" \
              "SRSNAME=EPSG:4326&" \
              "FEATUREPROFILE=Default_Profile&" \
              "WIDTH=3000&HEIGHT=3000" % (connectID, coordin)

        # шифруем логин и пароль (переводим строки в байты)
        userAndPass = b64encode(str.encode(self.loginW) + b":" + str.encode(self.passwordW)).decode("ascii")
        # составляем хеадер для запроса
        authorization = {'Authorization': 'Basic %s' % userAndPass}
        r = requests.get(URL, headers=authorization)
        # print(r.text)

        # временный файл
        file_temp = os.path.join(self.output_dir, 'WFS_temp.geojson')
        with open(file_temp, "wb") as f:
            f.write(str.encode(r.text))
        vlayer_temp = QgsVectorLayer(file_temp, 'WFS_temp', "ogr")
        self.project.addMapLayer(vlayer_temp)

        # подключаем стиль!!!!!!!!!!!!!!!!!!
        style = '/styles/style_wfs.qml'

        qml_path = self.plugin_dir + style
        print(qml_path)
        # print(qml_path)
        layer = self.iface.activeLayer()  # активный слой
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
        (message, success) = layer.loadNamedStyle(qml_path)
        print(message)
        if not success:  # if style not loaded remove it
            style_manager.removeStyle(style_name)

        # список названий полей
        nameFields = []
        # перебор названий полей слоя
        for field in vlayer_temp.fields():
            # print(field.name())
            nameFields.append(field.name())

        # список значей атрибутов
        attrFields = []
        features = vlayer_temp.getFeatures()
        for feature in features:
            # retrieve every feature with its geometry and attributes
            # print("Feature ID: ", feature.id())

            attrs = feature.attributes()
            # attrs is a list. It contains all the attribute values of this feature
            # print(attrs)
            attrFields.append(attrs)

        # Заполняем таблицу из слоя
        self.mTableListRastr(nameFields, attrFields)

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

    def extent(self, vLayer):
        """Получить координаты охвата слоя."""
        srs_ext = str(vLayer.crs()).split(' ')[1][:-1]  # получение проекции слоя
        print(srs_ext)
        try:
            # выполняется только для векторных слоев
            vLayer.updateExtents()
        except:
            None
        e = vLayer.extent()  # .toString()
        x = e.toString().split(' : ')
        coordStr = ''
        # перебор координат
        for i in x:
            z = i.split(',')
            print(z)
            # если проекции отличаются, то перепроицировать
            if srs_ext != "EPSG:4326":
                # перепроицирование
                crsSrc = QgsCoordinateReferenceSystem(srs_ext)  # Исходная crs
                crsDest = QgsCoordinateReferenceSystem("EPSG:4326")  # Целевая crs
                transformContext = self.project.transformContext()
                xform = QgsCoordinateTransform(crsSrc, crsDest, transformContext)

                # forward transformation: src -> dest
                pt1 = xform.transform(QgsPointXY(float(z[0]), float(z[1])))
                # собираем координаты в строку с правильным порядком и разделителями - запятыми
                coordStr += str(pt1.y()) + ',' + str(pt1.x()) + ','

            else:
                coordStr += z[1] + ',' + z[0] + ','

        print("Transformed point:", coordStr[:-1])  # отсекаем лишнюю запятую в конце строки.
        return coordStr[:-1]

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

    def select_output_dir(self):
        """Display dialog for user to select output directory."""
        output_dir = QFileDialog.getExistingDirectory(caption="Select Folder")
        if output_dir:
            # fill out the dialog field
            self.dlg.output_directory.setText(output_dir)
            # save ref
            self.output_dir = output_dir
            # save to settings to load at plugin start
            self.settings.setValue("outputDir", output_dir+'/')

    # выбор tif для загрузки на сервер
    def select_tif(self):
        filename = QFileDialog.getOpenFileName(None, "Select GeoTIFF", './', 'Files (*.tif *.TIF *.Tif)')
        # запоминаем адрес в файл для автоматической подгрузки, если он не пустой
        print(filename)
        if len(filename[0]) > 0:
            return filename[0]

    def up_tif(self, n):
        # загрузка tif на сервер
        # получаем адрес файла
        file_in = self.listLay[n][1].dataProvider().dataSourceUri()

        headers = self.authorization  # формируем заголовок для залогинивания
        files = {'file': open(file_in, 'rb')}
        ip = self.server
        URL_up = ip + '/rest/rasters'
        print('Старт загрузки .tif на сервер...')
        r = requests.post(URL_up, headers=headers, files=files)
        print('Ответ сервера:', r.text)

        if 'url' in r.text:
            url = r.json()['url']  # получаем адрес для использования загруженного файла
            print('Используется: URL')
        elif 'uri' in r.text:
            url = r.json()['uri']  # получаем адрес для использования загруженного файла
            print('Используется: URI')
        params = {"source_type": "tif", "url": "%s" % (url)}
        self.upOnServ_proc(params)

    def DelLay(self):
        """Удаление слоя."""
        # получить номер выбранной строки в таблице!
        row = self.dlg.processingsTable.currentIndex().row()
        if row != -1:
            # Номер в dictData
            row_nom = (len(self.processing_names) - row - 1)
            # получаем данные о слое и его ID
            id_v = self.processings[row_nom]['id']
            URL_f = self.server + "/rest/processings/" + id_v
            r = requests.delete(url=URL_f, headers=self.headers, auth=self.server_basic_auth)

        self.push_message(self.tr("Processing has been removed"), level=Qgis.Warning, duration=7)
        # обновить список слоев
        self.connect_to_server()

    def comboClick(self):
        """Cрабатывание от выбора в комбобоксе."""
        comId = self.dlg.rasterCombo.currentIndex()
        # открытие tif файла
        if comId == 2:
            self.addres_tiff = self.select_tif()  # выбрать tif на локальном компьютере
            # если адрес получен
            if self.addres_tiff:
                nameL = os.path.basename(self.addres_tiff)[:-4]
                # добавление растра в QGIS
                self.iface.addRasterLayer(self.addres_tiff, nameL)
                # заполнение комбобокса
                self.comboImageS()
                # поиск слоя по адресу файла
                for n, nameS in enumerate(self.listLay):
                    # получение адреса файла
                    adr = nameS[1].dataProvider().dataSourceUri()
                    print(adr, self.addres_tiff)
                    if adr == self.addres_tiff:
                        # если нашли, устанавливаем на него выбор
                        self.dlg.rasterCombo.setCurrentIndex(n+3)

    def uploadOnServer(self):
        """Выгрузить слой на сервер для обработки"""
        processing_name = self.dlg.NewLayName.text()
        if not processing_name:
            self.alert(self.tr('Please, specify a name for your processing'))
        elif processing_name in self.processing_names:
            self.alert(self.tr('Processing name taken. Please, choose a different name.'))
            # Подложка для обработки
            ph_satel = self.dlg.rasterCombo.currentIndex()
            # чекбокс (обновить кеш)
            cacheUP = str(self.dlg.checkUp.isChecked())
            self.push_message(self.tr("Please, wait. Uploading the file to the server..."))
            if ph_satel == 0:  # Mapbox Satellite
                # url_xyz = ''
                # proj_EPSG = 'epsg:3857'
                params = {}
                self.upOnServ_proc(params)
            elif ph_satel == 1:  # Custom
                self.alert(self.tr("Please, be aware that you may be charged by the imagery provider!"))
                login = self.dlg.custom_provider_login.text()
                password = self.dlg.custom_provider_password.text()
                url_xyz = self.dlg.custom_provider_url.text()
                # TypeURL = self.dlg.custom_provider_type.currentIndex()  # выбран тип ссылки///

                TypeURL = self.dlg.custom_provider_type.currentText()

                params = {"source_type": TypeURL,
                          "url": "%s" % (url_xyz),
                          "zoom": "18",
                          "cache_raster": "%s" % (cacheUP),
                          "raster_login": "%s" % (login),
                          "raster_password": "%s" % (password)}
                self.upOnServ_proc(params)

            # загрузка выбранного .tif
            elif ph_satel > 2:
                n = ph_satel - 3
                p = Thread(target=self.up_tif, args=(n,))
                p.start()

    def upOnServ_proc(self, params):
        # название новой обработки
        NewLayName = self.dlg.NewLayName.text()
        # получение индекса векторного слоя из комбобокса
        idv = self.dlg.polygonCombo.currentIndex()
        # получение индекса растрового слоя
        ph_satel = self.dlg.rasterCombo.currentIndex()
        # генерация охвата растра (если выбран локальный растр)
        # если выбрана обработка по охвату растра

        if idv == 0:
            # проверяем выбран ли локальный растр (id из комбобокса > 2)
            if ph_satel > 2:
                n = self.dlg.rasterCombo.currentIndex() - 3
                rLayer = self.listLay[n][1]
                print(rLayer.crs())
                coord = self.extent(rLayer).split(',')
                print(coord)
                # создание текста для файла .geojson
                text = '{"type": "FeatureCollection", "name": "extent", ' \
                    '"crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } }, ' \
                    '"features": [{ "type": "Feature", "properties": { }, ' \
                       '"geometry": { "type": "Polygon", "coordinates":[[' \
                       '[ %s, %s ],[ %s, %s ],[ %s, %s ],[ %s, %s ],[ %s, %s ]' \
                       ']] } }]}' % (coord[1], coord[0],
                                     coord[1], coord[2],
                                     coord[3], coord[2],
                                     coord[3], coord[0],
                                     coord[1], coord[0])
                print(text)
                # временный файл создание и запись
                name_temp = os.path.join(self.output_dir, 'extent_raster_temp.geojson')
                file_temp = open(name_temp, 'w')
                file_temp.write(text)
                file_temp.close()
                print(name_temp)
                Vlayer = QgsVectorLayer(name_temp, 'extent_temp', "ogr")

            else:
                self.alert(self.tr('Please, select a GeoTIFF file'))
        # если выбран один из полигональных слоев, пеередаем его дальше
        elif idv > 0:
            # получаем слой из списка полигональных слоев
            Vlayer = self.listPolyLay[idv-1][1]
        # Vlayer = self.dlg.mMapLayerComboBox.currentLayer()

        # projection = Vlayer.crs() #получаем проекцию EPSG
        projection_text = str(Vlayer.crs()).split(' ')[1][:-1]  # текстовое значение проекции EPSG
        projection_text = projection_text.split(":")[1]
        # print('Проекция исходного файла:', projection_text)

        # сценарий обработки
        proc = self.dlg.ai_model.currentText()
        # чекбокс (обновить кеш)
        cacheUP = str(self.dlg.checkUp.isChecked())
        # система координат для сервера
        crsDest = QgsCoordinateReferenceSystem(4326)
        # адрес хранения экспортного файла
        file_adrG = self.plugin_dir + '/' + NewLayName + '.geojson'
        # экспорт в GEOJSON
        error = QgsVectorFileWriter.writeAsVectorFormat(Vlayer, file_adrG, "utf-8", crsDest, "GeoJSON")
        if error == QgsVectorFileWriter.NoError:
            print("success!")

        URL_up = self.server + "/rest/processings"

        try:
            urlt = params['url']
            meta = {"EPSG": "%s" % (projection_text),
                    "CACHE": "%s" % (cacheUP),
                    "source": "mapbox",
                    "source-app": "qgis"}
        except:
            meta = {"EPSG": "%s" % (projection_text),
                    "CACHE": "%s" % (cacheUP),
                    "source-app": "qgis"}
        # print(params)
        # print(meta)
        with open(file_adrG) as f:
            GeomJ = json.load(f)
        # print(file_adrG)
        os.remove(file_adrG)  # удаление временного файла
        for i in GeomJ['features']:
            # print(i)
            GeomJ = i['geometry']

        GeomJ = str(GeomJ).replace("\'", "\"")
        params = str(params).replace("\'", "\"")
        meta = str(meta).replace("\'", "\"")
        # print(meta)
        # название будущего слоя#тип обработки#геометрия из геоджейсона
        NewLayName = NewLayName
        NewLayName = str(NewLayName).replace("\'", "\\\"")

        bodyUp = '{ "name": "%s", "wdName": "%s", "geometry": %s, "params": %s, "meta": %s}' \
            % (NewLayName, proc, GeomJ, params, meta)

        bodyUp = bodyUp.encode('utf-8')

        rpost = requests.request("POST", url=URL_up, data=bodyUp, headers=self.headers, auth=self.server_basic_auth)
        # print(rpost.status_code)

        self.dlg.NewLayName.clear()  # очистить поле имени
        self.alert(self.tr("Success! Processing may take up to several minutes"))
        self.connect_to_server()

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

    def addSucces(self):
        """Загрузка слоя с сервера."""
        # получить номер выбранной строки в таблице!
        row = self.dlg.processingsTable.currentIndex().row()
        if row == -1:
            self.alert(self.tr('Please, select a processing'))
            return
        # Номер в dictData
        # row_nom =  (self.kol_tab - row - 1)
        # #получаем данные о слое и его ID
        # id_v = self.dictData[row_nom]['id']

        id_v = self.dlg.processingsTable.model().index(row, 4).data()
        URL_f = self.server + "/rest/processings/" + id_v + "/result"
        r = requests.get(url=URL_f, headers=self.headers, auth=self.server_basic_auth)

        # адрес для сохранения файла
        name_d = self.dlg.processingsTable.model().index(row, 1).data()  # self.dictData[row_nom]['name']

        # находим ссылку на растр по id
        for dD in self.processings:
            # print(dD)
            if dD['id'] == id_v:

                rastrXYZ = dD['rasterLayer']['tileUrl']
                print(rastrXYZ)
                break

        url = '&url=' + rastrXYZ
        # print(rastrXYZ)
        min_max = "&zmax=18&zmin=0"
        typeXYZ = 'type=xyz'
        login = '&username=' + self.dlg.server_login.text()
        password = '&password=' + self.dlg.server_password.text()
        urlWithParams = typeXYZ + url + min_max + login + password
        rlayer = QgsRasterLayer(urlWithParams, name_d + 'xyz', 'wms')
        self.project.addMapLayer(rlayer)

        # x1 = name_d.rfind('_')
        # извлекаем проекцию из метаданных/перестали извлекать, задали фиксированную
        Projection = 'EPSG:4326'  # self.dictData[row_nom]['meta']['EPSG'] #name_d[x1 + 1:]

        # система координат для преобразования файла
        crs_EPSG = QgsCoordinateReferenceSystem(Projection)

        # временный файл
        file_temp = os.path.join(self.output_dir, f'{name_d}_temp.geojson')
        with open(file_temp, "wb") as f:
            f.write(str.encode(r.text))
        vlayer_temp = QgsVectorLayer(file_temp, name_d+'_temp', "ogr")

        # экспорт в shp
        file_adr = os.path.join(self.output_dir, f'{name_d}.shp')
        error = QgsVectorFileWriter.writeAsVectorFormat(vlayer_temp, file_adr, "utf-8", crs_EPSG, "ESRI Shapefile")
        if error != QgsVectorFileWriter.NoError:
            self.push_message(self.tr('There was an error writing the Shapefile!'), Qgis.Warning)

        # Открытие файла
        vlayer = QgsVectorLayer(file_adr, name_d, "ogr")
        if not vlayer:
            self.push_message(self.tr("Could not load the layer!"), Qgis.Warning)
        # Загрузка файла в окно qgis
        self.project.addMapLayer(vlayer)

        # ---- подключение стилей
        # определяем какой стиль подключить к слою
        WFDef = self.listProc[row][5]  # название дефенишинса
        if WFDef == 'Buildings Detection' or WFDef == 'Buildings Detection With Heights':
            style = '/styles/style_buildings.qml'
        elif WFDef == 'Forest Detection':
            style = '/styles/style_forest.qml'
        elif WFDef == 'Forest Detection With Heights':
            style = '/styles/style_forest_with_heights.qml'
        elif WFDef == 'Roads Detection':
            style = '/styles/style_roads.qml'
        else:
            style = '/styles/style_default.qml'

        # подключаем стиль!!!!!!!!!!!!!!!!!!
        qml_path = self.plugin_dir + style
        print(qml_path)
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
        print(message)
        if not success:  # if style not loaded remove it
            style_manager.removeStyle(style_name)

        time.sleep(1)
        iface.zoomToActiveLayer()  # приблизить к охвату активного слоя
        try:
            os.remove(file_temp)  # удаление временного файла
            print('Временный файл удален:', file_temp)
        except:
            print('Временный файл удалить не удалось, ну пусть будет, он никому не мешает и весит мало:', file_temp)

    def alert(self, message):
        """Display an info message."""
        QMessageBox.information(self.dlg, 'Mapflow', message)

    def push_message(self, text, level=Qgis.Info, duration=5):
        """Display a translated message on the message bar."""
        self.iface.messageBar().pushMessage("Mapflow", text, level, duration)

    def refresh_processing_list(self, url):
        """Repeatedly refresh processing list."""
        while self.check_processings:
            # fetch all user processings visible to the user
            self.processings = requests.get(url, auth=self.server_basic_auth).json()
            # save ref to check name uniqueness at processing creation
            self.processing_names = [processing['name'] for processing in self.processings]
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
            columns = ('name', 'workflowDef', 'status', 'percentCompleted', 'created')
            for row, processing in enumerate(self.processings):
                for col, attr in enumerate(columns):
                    self.dlg.processingsTable.setItem(row, col, QTableWidgetItem(processing[attr]))
            # Turn sorting on again
            self.dlg.processingsTable.setSortingEnabled(True)
            # Sort by creation date descending
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
        for action in self.actions:
            self.iface.removePluginVectorMenu('Geoalert', action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar

    def connect_to_server(self):
        """Connect to Geoalert server."""
        # Check if user specified an existing output dir
        # if not os.path.exists(self.output_dir):
        #     self.alert(self.tr('Please, specify an existing output directory'))
        #     self.select_output_dir()
        # else:
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
