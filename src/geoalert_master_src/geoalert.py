import time
import json
import traceback
import os.path
from math import *
from base64 import b64encode
from threading import Thread

import gdal
import ogr
import osr
import requests
from PyQt5 import *  # Qt
from PyQt5.QtGui import *  # QIcon
from PyQt5.QtWidgets import *  # QAction, QMessageBox, QProgressBar
from PyQt5.QtCore import *  # QSettings, QTranslator, qVersion, QCoreApplication, QVariant, Qt
from qgis.core import *
from qgis.gui import *
from qgis.utils import iface
from qgis.PyQt.QtXml import QDomDocument

from .resources_rc import *
from .geoalert_dialog import GeoalertDialog


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
    """"""

    def __init__(self, iface):
        self.iface = iface
        self.project = QgsProject.instance()
        self.settings = QgsSettings()
        self.plugin_dir = os.path.dirname(__file__)
        # Translation
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n', f'Geoalert_{locale}.qm')
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)
        # Init dialog and keep reference
        self.dlg = GeoalertDialog()
        self.actions = []
        self.toolbar = self.iface.pluginToolBar()
        # Save ref to output dir (empty str if plugin loaded 1st time or cache cleaned manually)
        self.output_dir = self.settings.value('geoalert/outputDir')
        # Нажатие кнопки "Подключить".
        self.dlg.ButtonConnect.clicked.connect(self.button_connect)
        # загрузить выбраный результат
        self.dlg.ButtonDownload.clicked.connect(self.addSucces)
        # Кнопка: Выгрузить слой на сервер для обработки
        self.dlg.ButtonUpload.clicked.connect(self.uploadOnServer)
        # кнопка удаления слоя
        self.dlg.ButtonDel.clicked.connect(self.DelLay)
        # Кнопка подключения снимков
        self.dlg.button_preview.clicked.connect(self.sart_view)
        # кнопка выбора папки через обзор
        self.dlg.but_dir.clicked.connect(self.select_output_dir)
        # ввести стандартную максаровскую ссылку
        self.dlg.maxarStandardURL.clicked.connect(self.maxarStandard)
        # чтение настроек логин/пароль
        if self.read_settings("serverSaveAuth"):
            self.dlg.server_save_auth.setChecked(True)
            # загружаем логин/пароль платформы и вставляем в поля
            self.dlg.server_login.setText(self.read_settings("serverLogin"))
            self.dlg.server_password.setText(self.read_settings("serverPassword"))
        if self.read_settings("customProviderSaveAuth"):
            self.dlg.custom_provider_save_auth.setChecked(True)
            # загружаем логин/пароль платформы и вставляем в поля
            self.dlg.custom_provider_login.setText(self.read_settings("customProviderLogin"))
            self.dlg.custom_provider_password.setText(self.read_settings("customProviderPassword"))
        # чтение connect ID
        connectID = self.read_settings('connectID')
        self.dlg.connectID.setText(connectID)
        # чтение настроек URL
        surl = self.read_settings('customProviderURL')
        self.dlg.custom_provider_url.setText(surl)

        # чекбокс максар
        self.dlg.checkMaxar.clicked.connect(self.con)
        # дизейблим фрейм на старте
        self.dlg.frame.setEnabled(False)

        # чекбокс экстент растра вместо полигонального слоя
        # self.dlg.checkRasterExtent.clicked.connect(self.rasterExtentSand())

        # загрузка рабочей папки из настроек в интерфейс
        self.dlg.output_directory.setText(self.output_dir)
        # срабатывает при выборе источника снимков в комбобоксе
        self.dlg.comboBox_satelit.activated.connect(self.comboClick)
        # загрузка полей комбобокса
        self.comboImageS()

        # подключение слоя WFS
        self.dlg.ButWFS.clicked.connect(self.ButWFS)

        self.dlg.tabListRast.clicked.connect(self.feID)
        # self.dlg.ButExtent.clicked.connect(self.extent)

    # тест экстента
    # def test(self):
    #     n = self.dlg.comboBox_satelit.currentIndex()-3
    #     rLayer = self.listLay[n][1]
    #     print(rLayer.crs())
    #     coord = self.extent(rLayer).split(',')
    #     print(coord)
    #     # создание текста для файла .geojson
    #     text = '{"type": "FeatureCollection", "name": "extent", ' \
    #            '"crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } }, ' \
    #            '"features": [{ "type": "Feature", "properties": { }, ' \
    #            '"geometry": { "type": "Polygon", "coordinates":[[' \
    #            '[ %s, %s ],[ %s, %s ],[ %s, %s ],[ %s, %s ],[ %s, %s ]' \
    #            ']] } }]}' % (coord[1], coord[0],
    #                          coord[1], coord[2],
    #                          coord[3], coord[2],
    #                          coord[3], coord[0],
    #                          coord[1], coord[0])
    #     print(text)
    #     # временный файл создание и запись
    #     name_temp = self.dlg.output_directory.text() + 'extent_raster_temp.geojson'
    #     file_temp = open(name_temp, 'w')
    #     file_temp.write(text)
    #     file_temp.close()
    #     print(name_temp)
    #     Vlayer = QgsVectorLayer(name_temp, 'extent_temp', "ogr")
    #
    #     self.project.addMapLayer(Vlayer)

# Вписываем feature ID из таблицы в поле

    def feID(self):
        # получить номер выбранной строки в таблице!
        row = self.dlg.tabListRast.currentIndex().row()
        print(row)
        id_v = self.dlg.tabListRast.model().index(row, 4).data()
        print(id_v)
        self.dlg.featureID.setText(str(id_v))

    def update_layer_list(self):
        """Update layer list at plugin start."""

        # выполняется пока окно открыто
        lenL = 0
        while self.potok:
            # print('Старт проверки')
            lenLayers = len(self.project.mapLayers())
            if lenL != lenLayers:
                lenL = lenLayers  # запоминаем значение для проверки в следующий раз
                # обновление списков комбобокса
                # растры
                self.comboImageS()
                # полигоны
                self.comboPolygons()
            # пауза перед повторной проверкой
            time.sleep(6)

    # заполнение комбобокса полигональных слоев
    def comboPolygons(self):
        self.dlg.polygonLayerComboBox.clear()
        ll = ['Raster extent (.tif)']
        # заполняем обязательные пункты
        for idx, field in enumerate(ll):
            self.dlg.polygonLayerComboBox.addItem(field, idx)

        print('-----------------------------------')
        # заполняем полигональными слоями

        self.listPolyLay = []
        layersAll = self.project.mapLayers()
        # print(layersAll)
        id = len(ll)
        # перебор всех слоев и проверка их типа
        for i in layersAll:
            # тип слоя
            nType = self.project.mapLayers()[i].type()
            # print(nType)
            # проверка на векторность
            if nType == 0:
                # получаем один объект из слоя для определения полигонального слоя
                # в случае если слой пустой, пропускаем его
                try:
                    features = self.project.mapLayers()[i].getFeatures()
                    for feature in features:
                        # определяем тип геометрии по первому объекту
                        geom = feature.geometry()
                        break

                    # если тип = полигон
                    if geom.type() == QgsWkbTypes.PolygonGeometry:
                        # добавляем название и вектор в список
                        nameV = self.project.mapLayers()[i].name()
                        layV = self.project.mapLayers()[i]
                        self.listPolyLay.append([nameV, layV])
                        # print(name)
                        self.dlg.polygonLayerComboBox.addItem(nameV, id)
                        id += 1
                except:
                    print('пропуск пустого слоя')
                    continue
        # print(self.listPolyLay)

    def con(self):
        # срабатывание чекбокса
        ch = self.dlg.checkMaxar.isChecked()
        self.dlg.frame.setEnabled(ch)  # включение/отключение элемента

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
        self.save_settings('connectID', connectID)

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
        self.save_settings('connectID', connectID)

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
            self.settings.setValue("geoalert/outputDir", output_dir+'/')

    # получаем список дефинишинсов
    def WFDefeni(self):
        URL_up = self.server + '/rest/projects/default'  # url запроса
        headers = self.authorization
        r = requests.get(URL_up, headers=headers)
        # print(r)
        # Проверка логин/пароль
        if str(r) == '<Response [200]>':  # пароль верный - подключение
            # print('ОК')
            wfds = r.json()['workflowDefs']
            self.dlg.comboBoxTypeProc.clear()
            for wfd in enumerate(wfds):
                # print(wfd)
                try:
                    self.dlg.comboBoxTypeProc.addItem(wfd[1]['name'])
                    print(wfd[1]['name'])
                    # if wfd[0] == 0: #устанавливаем выбранным первый пункт в списке
                    #     self.dlg.comboBoxTypeProc.setText(wfd[1]['name'])
                except:
                    print('Не добавлен дефенишенс:', wfd[1]['name'])
                    None
            return True  # разрешить дальнейшее выполнение
        elif str(r) == '<Response [401]>':  # пароль НЕ верный, показать предупреждение!
            self.flag = 'report error'
            print('Wrong login or password! Please try again.')

            return False  # self.flag

    # выбор tif для загрузки на сервер
    def select_tif(self):
        filename = QFileDialog.getOpenFileName(None, "Select .TIF File", './', 'Files (*.tif *.TIF *.Tif)')
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
            row_nom = (self.kol_tab - row - 1)
            # получаем данные о слое и его ID
            id_v = self.dictData[row_nom]['id']
            URL_f = self.server + "/rest/processings/" + id_v
            r = requests.delete(url=URL_f, headers=self.headers)

        # всплывающее сообщение
        self.iface.messageBar().pushMessage("Massage", "Processing has been removed.",
                                            level=Qgis.Warning,
                                            duration=7)
        # обновить список слоев
        self.button_connect()

    def comboClick(self):
        """Cрабатывание от выбора в комбобоксе."""
        comId = self.dlg.comboBox_satelit.currentIndex()
        # открытие tif файла
        if comId == 2:
            self.addres_tiff = self.select_tif()  # выбрать tif на локальном компьютере
            # print('comb:', self.addres_tiff)
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
                        self.dlg.comboBox_satelit.setCurrentIndex(n+3)
            else:
                # обновляем весь список слоев
                self.comboImageS()
        elif comId > 2:
            print(self.listLay[comId - 3][1].dataProvider().dataSourceUri())
        #     self.dlg.comboBox_satelit.setCurrentIndex(comId)
        # self.dlg.comboBox_satelit.setDisabled(True) # отключение элемента

    # заполнение комбобокса растров
    def comboImageS(self):
        self.dlg.comboBox_satelit.clear()
        ll = ['Mapbox Satellite', self.tr('Custom (in settings)'), 'Open new .tif']
        # заполняем обязательные пункты
        for idx, field in enumerate(ll):
            self.dlg.comboBox_satelit.addItem(field, idx)

        print('-----------------------------------')
        # заполняем локальными подключенными растрами
        # self.comboImageS()
        self.listLay = []
        layersAll = self.project.mapLayers()
        # print(layersAll)
        id = 3
        # перебор всех слоев и проверка их типа
        for i in layersAll:
            # тип слоя
            nType = self.project.mapLayers()[i].type()
            if nType == 1:
                # # тип растра
                # rt = self.project.mapLayers()[i].rasterType()
                # # если тип = локальному растру
                # if rt == 2:
                # добавляем название и растр в список
                name = self.project.mapLayers()[i].name()
                lay = self.project.mapLayers()[i]

                fN = lay.dataProvider().dataSourceUri()
                # добавляем только файлы с расширением .tif и .tiff
                if fN[-4:] in ['.tif', '.Tif', '.TIF'] or fN[-5:] in ['.tiff', '.Tiff', '.TIFF']:
                    self.listLay.append([name, lay])
                    # print(name)
                    # print(fN)
                    self.dlg.comboBox_satelit.addItem(name, id)
                    id += 1
        # print(self.listLay)

    def uploadOnServer(self, iface):
        """Выгрузить слой на сервер для обработки"""
        NewLayName = self.dlg.NewLayName.text()
        if len(NewLayName) > 0 and NewLayName not in self.listNameProc:  # если имя не пустое - начинаем загрузку

            # Подложка для обработки
            ph_satel = self.dlg.comboBox_satelit.currentIndex()
            # print(ph_satel)
            # чекбокс (обновить кеш)
            cacheUP = str(self.dlg.checkUp.isChecked())
            # print(cacheUP)

            # всплывающее сообщение
            self.iface.messageBar().pushMessage("Massage", "Please, wait. Uploading a file to the server...",
                                                level=Qgis.Info,
                                                duration=10)

            if ph_satel == 0:  # Mapbox Satellite
                # url_xyz = ''
                # proj_EPSG = 'epsg:3857'
                params = {}
                self.upOnServ_proc(params)
            elif ph_satel == 1:  # Custom
                infoString = "Поставщиком космических снимков может взыматься плата за их использование!"
                QMessageBox.information(self.dlg, "About", infoString)
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

        else:
            print('Сначала укажите имя для обработки, выберите полигональный слой и тип обработки')
            # создать и показать сообщение//create a string and show it
            infoString = "Название обработки не задано или уже есть обработка с таким названием. " \
                "\n Введите другое название!"
            QMessageBox.information(self.dlg, "About", infoString)

    def upOnServ_proc(self, params):
        # название новой обработки
        NewLayName = self.dlg.NewLayName.text()
        # получение индекса векторного слоя из комбобокса
        idv = self.dlg.polygonLayerComboBox.currentIndex()
        # получение индекса растрового слоя
        ph_satel = self.dlg.comboBox_satelit.currentIndex()
        # генерация охвата растра (если выбран локальный растр)
        # если выбрана обработка по охвату растра

        if idv == 0:
            # проверяем выбран ли локальный растр (id из комбобокса > 2)
            if ph_satel > 2:
                n = self.dlg.comboBox_satelit.currentIndex() - 3
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
                infoString = 'Use local ".tif" file'

                QMessageBox.information(self.dlg, "About", infoString)
                print('сначала выберите локальный .tif')
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
        proc = self.dlg.comboBoxTypeProc.currentText()
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

        print(bodyUp)
        bodyUp = bodyUp.encode('utf-8')

        rpost = requests.request("POST", url=URL_up, data=bodyUp, headers=self.headers)
        print(rpost.text)
        # print(rpost.status_code)

        self.dlg.NewLayName.clear()  # очистить поле имени

        # создать и показать сообщение
        infoString = "Слой загружен на сервер! \n Обработка может занять от 10 секунд до нескольких минут"
        print(infoString)
        # QMessageBox.information(self.dlg, "About", infoString)
        self.button_connect()

    def sart_view(self):
        """Custom provider imagery preview."""
        # Save the checkbox state itself
        self.save_settings("custom_provider_save_auth", self.dlg.custom_provider_save_auth.isChecked())
        # If checked, save the credentials
        if self.dlg.custom_provider_save_auth.isChecked():
            self.save_settings("customProviderLogin", self.dlg.custom_provider_login.text())
            self.save_settings("customProviderPassword", self.dlg.custom_provider_password.text())
        # если чекбокс включен - ограничиваем зум предпросмотра до 14 иначе до 18
        z_max = '14' if self.dlg.custom_provider_limit_zoom.isChecked() else '18'
        z_min = '0'
        min_max = "&zmax=" + z_max + "&zmin=" + z_min
        provider_type = self.dlg.custom_provider_type.currentText()
        url = self.dlg.custom_provider_url.text()
        self.save_settings('customProviderURL', url)
        # замена символов в адресе для корректной работы
        url = url.replace('=', '%3D')
        url = url.replace('&', '%26')
        url = '&url=' + url

        typeXYZ = 'type=' + provider_type
        login = '&username=' + self.dlg.custom_provider_login.text()
        password = '&password=' + self.dlg.custom_provider_password.text()
        urlWithParams = typeXYZ + url + min_max + login + password
        rlayer = QgsRasterLayer(urlWithParams, self.tr('User_servise ') + z_min + '-' + z_max, 'wms')
        self.project.addMapLayer(rlayer)

    def addSucces(self):
        """Загрузка слоя с сервера."""
        # получить номер выбранной строки в таблице!
        row = self.dlg.processingsTable.currentIndex().row()
        print(row)
        if row != -1:
            # Номер в dictData
            # row_nom =  (self.kol_tab - row - 1)
            # #получаем данные о слое и его ID
            # id_v = self.dictData[row_nom]['id']
            # print(id_v)

            id_v = self.dlg.processingsTable.model().index(row, 4).data()
            print(id_v)
            URL_f = self.server + "/rest/processings/" + id_v + "/result"
            r = requests.get(url=URL_f, headers=self.headers)

            # адрес для сохранения файла
            name_d = self.dlg.processingsTable.model().index(row, 1).data()  # self.dictData[row_nom]['name']

            # находим ссылку на растр по id
            for dD in self.dictData:
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
            if error == QgsVectorFileWriter.NoError:
                print("success again!")
            else:
                print('ERROR WRITING SHP')

            # Открытие файла
            vlayer = QgsVectorLayer(file_adr, name_d, "ogr")
            if not vlayer:
                print("Layer failed to load!")
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
        else:
            print('Сначала выберите слой в таблице')

    def message(self, message):
        """Display an info message."""
        QMessageBox.information(self.dlg, 'Geoalert', self.tr(message))

    def button_connect(self):
        """Подключение к серверу."""
        # Check if user specified an existing output dir
        if not os.path.exists(self.output_dir):
            self.message('Please, specify an existing output directory')
            self.select_output_dir()
        else:
            self.save_settings("serverSaveAuth", self.dlg.server_save_auth.isChecked())
            login = self.dlg.server_login.text()
            password = self.dlg.server_password.text()
            if self.dlg.server_save_auth.isChecked():
                self.save_settings("serverLogin", login)
                self.save_settings("serverPassword", password)
            self.server = self.dlg.server_url.text()
            url = self.server + "/rest/processings"
            # we need to base 64 encode it
            # and then decode it to acsii as python 3 stores it as a byte string
            # шифруем логин и пароль (переводим строки в байты)
            userAndPass = b64encode(str.encode(login) + b":" + str.encode(password)).decode("ascii")
            # составляем хеадер для запроса
            self.authorization = {'Authorization': 'Basic %s' % userAndPass}  # для авторизации при загрузке TIF
            self.headers = {'Authorization': 'Basic %s' % userAndPass, 'content-type': "application/json"}

            # заполняем комбобокс доступными воркфлоудифинишинсами
            self.flag = self.WFDefeni()

            if self.flag:
                # запуск потока
                proc = Thread(target=self.button_con, args=(url,))
                proc.start()
            else:
                self.message('Invalid credentials! Please try again.')

    def button_con(self, URL):
        """Циклическое переподключение к серверу для получения статусов обработок."""
        while self.flag:
            # выполняем запрос
            r = requests.get(url=URL, headers=self.headers)
            # print(r.text) # получаем ответ
            # print(r.status_code) # код ответа
            # текст ответа от сервера распознаем как json и разбиваем на список со словарями
            self.dictData = json.loads(r.text)
            # print(self.dictData)
            # получаем список ключей по которым можно получить знаечния
            # print(self.dictData[0].keys())

            self.kol_tab = len(self.dictData)  # количество элементов
            self.dlg.processingsTable.setRowCount(self.kol_tab)  # создаем строки таблицы
            # перебор в цикле элементов списка и ключей
            # nx = 0 #счетчик
            self.flag = False
            self.listNameProc = []  # список названий обработок
            self.listProc = []  # список обработок в таблице
            for i in range(self.kol_tab):
                self.listNameProc.append(self.dictData[i]['name'])  # заполняем список названий обработок
                # print(self.dictData[i]['projectId'])
                # statf = QTableWidgetItem(str(self.dictData[i]['percentCompleted'])+'%')
                # namef = QTableWidgetItem(self.dictData[i]['name'])
                # Status = QTableWidgetItem(self.dictData[i]['status'])
                # ids = QTableWidgetItem(self.dictData[i]['id'])
                # #дата и время создания
                # cre = self.dictData[i]['created']
                # cre2 = cre.split('T')
                # createf = QTableWidgetItem(cre2[0] + ' ' + cre2[1][:8])

                if self.dictData[i]['status'] == "IN_PROGRESS" or self.dictData[i]['status'] == "UNPROCESSED":  # если хоть одна задача в процессе выполнения
                    self.flag = True  # добавляем значение для обновления статуса
                # print('-'*18)
                # print(self.dictData[i])

                # # вывод всех значений
                # spisok_znachen = ['id',
                #                   'name',
                #                   'projectId',
                #                   'vectorLayer',
                #                   'rasterLayer',
                #                   'workflowDef',
                #                   'aoiCount',
                #                   'aoiArea',
                #                   'status',
                #                   'percentCompleted',
                #                   'params',
                #                   'meta',
                #                   'created',
                #                   'updated']
                #
                # for x in spisok_znachen:
                #     print(x + ': ', self.dictData[i][x], )
                # print('-'*12)

                # print(self.dictData[i]['workflowDef']['name'])

                # вписываем значения в список для сортировке по дате и времени
                self.listProc.append([self.dictData[i]['created'],
                                      self.dictData[i]['percentCompleted'],
                                      self.dictData[i]['name'], self.dictData[i]['status'],
                                      self.dictData[i]['id'],
                                      self.dictData[i]['workflowDef']['name']])

            # сортировка обработок в в списке по дате в обратном порядке
            self.listProc.sort(reverse=True)
            # print(listProc)
            # заполнение таблицы значениями
            for nx in range(len(self.listProc)):
                statf = QTableWidgetItem(str(self.listProc[nx][1]) + '%')
                namef = QTableWidgetItem(self.listProc[nx][2])
                Status = QTableWidgetItem(self.listProc[nx][3])
                ids = QTableWidgetItem(self.listProc[nx][4])
                # название сценария обработки
                WFDef = QTableWidgetItem(self.listProc[nx][5])

                # дата и время создания
                cre2 = self.listProc[nx][0].split('T')
                createf = QTableWidgetItem(cre2[0] + ' ' + cre2[1][:8])
                # построчная запись в таблицу
                self.dlg.processingsTable.setItem(nx, 0, statf)
                self.dlg.processingsTable.setItem(nx, 1, namef)
                self.dlg.processingsTable.setItem(nx, 2, Status)
                self.dlg.processingsTable.setItem(nx, 3, createf)
                self.dlg.processingsTable.setItem(nx, 4, ids)
                self.dlg.processingsTable.setItem(nx, 5, WFDef)

            if self.flag == True:
                secn = 5  # задержка обновления в секундах
                # print('Обновление через', secn, 'секунд')
                time.sleep(secn)  # ожидание следующей итеррации
            else:
                print('Нет выполняющихся обработок')

    def save_settings(self, key, val):
        """Cache values for reuse."""
        self.settings.setValue(f"geoalert/{key}", val)

    def read_settings(self, key):
        """Read cached values."""
        # Returns None if undefined
        val = self.settings.value(f"geoalert/{key}")
        return '' if val is None else val

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
            self.iface.removePluginVectorMenu('&Geoalert', action)
            self.iface.removeToolBarIcon(action)
        # del self.toolbar

    def run(self):
        """Обновление списка слоев для выбора источника растра."""
        # запускаем отдельным потоком
        self.potok = True
        upLayers = Thread(target=self.update_layer_list)
        upLayers.start()

        # Открыть диалог
        self.dlg.show()
        self.dlg.exec_()

        print("Закрытие окна, завершение потока")
        # закрываем поток после закрытия окна плагина
        self.potok = False
        upLayers.join()
