# -*- coding: utf-8 -*-
from qgis.core import *
from PyQt5 import * # Qt
from PyQt5.QtGui import *# QIcon
from PyQt5.QtWidgets import * #QAction, QMessageBox, QProgressBar
from PyQt5.QtCore import *# QSettings, QTranslator, qVersion, QCoreApplication, QVariant, Qt
from qgis.gui import *
# Импорт файла resources.py
from .resources_rc import *
# Импорт кода диалога
from .geoalert_dialog import GeoalertDialog
import os.path
# добавленные
from qgis.PyQt.QtXml import QDomDocument
import time
import processing
import glob
import qgis
import gdal
import ogr
import osr
import requests
import json
from math import *
from base64 import b64encode

class Geoalert:

    def __init__(self, iface):

        self.iface = iface
        # определяем папку в которой находится модуль
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]

        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'Geoalert_{}.qm'.format(locale))
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Создание диалога (после перевода) and keep reference
        self.dlg = GeoalertDialog()

        # Declare instance attributes
        self.actions = []

        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'Geoalert')
        self.toolbar.setObjectName(u'Geoaler')

#-------Вкладка (Обработка)
        # работа с таблицей
        self.dlg.tableWidget.clear()
        stolbci = [u" Обработка", u"Название", u"Статус", u"Создано"]

        StolbKol = len(stolbci) #4#количество столбцов
        self.dlg.tableWidget.setColumnCount(StolbKol) #создаем столбцы
        self.dlg.tableWidget.setHorizontalHeaderLabels(stolbci) #даем названия столбцам
        #перебор всех столбцов и настройка
        for nom in range(StolbKol):
            # Устанавливаем выравнивание на заголовки
            self.dlg.tableWidget.horizontalHeaderItem(nom).setTextAlignment(Qt.AlignCenter)
        # указываем ширину столбцов
        self.dlg.tableWidget.setColumnWidth(0, 80)
        self.dlg.tableWidget.setColumnWidth(1, 200)
        self.dlg.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)  # выделять всю строку при нажатии
        self.dlg.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)  # запретить редактировать таблицу пользователю
        # Нажатие кнопки "Подключить"
        self.dlg.ButtonConnect.clicked.connect(self.button_connect)
        # загрузить выбраный результат
        self.dlg.ButtonDownload.clicked.connect(self.addSucces)
        #Кнопка: Выгрузить слой на сервер для обработки
        self.dlg.ButtonUpload.clicked.connect(self.uploadOnServer)
        #кнопка удаления слоя
        self.dlg.ButtonDel.clicked.connect(self.DelLay)

        #кнопка выбора TIF для загрузки
        self.dlg.but_inputTIF.clicked.connect(self.select_tif)

#--------------------------------------------------------

    #Настройки

        # Кнопка предпросмотра снимков
        self.dlg.Button_view.clicked.connect(self.sart_view)
        # кнопка выбора папки через обзор
        self.dlg.but_dir.clicked.connect(self.select_output_file)
        #загрузка рабочей папки из файла
        try:
            with open(self.plugin_dir + '\\pathdir', "r") as Re:

                for line in Re:
                    name = line
                    self.dlg.input_directory.setText(name)  # вписываем адрес в поле
        # если не получилось, тогда пропускаем
        except:
            infoString = "Рабочая папка не найдена! Укажите в настройках рабочую папку"
            QMessageBox.information(self.dlg, "Внимание!", infoString)
#------------------------------

    # получаем список дефинишинсов
    def WFDefeni(self):
        URL_up = self.server + '/rest/projects/default' #url запроса
        headers = self.authorization

        r = requests.get(URL_up, headers=headers)
        #print(r.text)
        wfds = r.json()['workflowDefs']
        self.dlg.comboBoxTypeProc.clear()
        for wfd in wfds:
            print(wfd['name'])
            try:
                self.dlg.comboBoxTypeProc.addItem(wfd['name'])
            except:
                None

    #адрес рабочей папки
    def select_output_file(self):
        filename = QFileDialog.getExistingDirectory(None, "Select Folder") + '/'
        # запоминаем адрес в файл для автоматической подгрузки, если он не пустой
        if len(filename) > 0:
            self.dlg.input_directory.setText(filename)
            # print filename
            with open(self.plugin_dir + '/pathdir', "wb") as f:  # записать в файл путь к папке
                f.write(filename.encode('utf8'))
                # пишем текст в окно статуса
    def select_output_file_2(self):
        filename = QFileDialog.getExistingDirectory(None, "Select Folder") + '/'
        # запоминаем адрес в файл для автоматической подгрузки, если он не пустой
        if len(filename) > 0:
            self.dlg.input_directory_2.setText(filename)
    #кнопка выбора tif для загрузки на сервер
    def select_tif(self):
        filename = QFileDialog.getOpenFileName(None, "Select .TIF File", './', 'Files (*.tif *.TIF *.Tif)')
        # запоминаем адрес в файл для автоматической подгрузки, если он не пустой
        print(filename)
        if len(filename[0]) > 0:
            self.dlg.input_TIF.setText(filename[0])
    # загрузка tif на сервер
    def up_tif(self):
        file_in = self.dlg.input_TIF.text() #получаем адрес файла
        headers = self.authorization #{'Authorization': 'Basic idxxxxxxxxxxxxxxxxx'} # формируем заголовок для залогинивания
        files = {'file': open(file_in, 'rb')}
        ip = self.server
        URL_up = ip + '/rest/rasters'
        r = requests.post(URL_up, headers=headers, files=files)
        print('Ответ сервера:')
        print(r.text)
        uri = r.json()['uri'] #получаем адрес для использования загруженного файла
        return uri
    #Удалить слой
    def DelLay(self):
        # получить номер выбранной строки в таблице!
        row = self.dlg.tableWidget.currentIndex().row()
        print(row)
        if row != -1:
            # Номер в dictData
            row_nom = (self.kol_tab - row - 1)
            #получаем данные о слое и его ID
            id_v = self.dictData[row_nom]['id']
            print(id_v, 'Удален')
            URL_f = self.server + "/rest/processings/" + id_v
            print(URL_f, self.headers)
            r = requests.delete(url=URL_f, headers=self.headers)
            # получаем ответ
            print(r.text)
        #обновить список слоев
        self.button_connect()
    # Выгрузить слой на сервер для обработки
    def uploadOnServer(self, iface):
        self.button_connect()
        NewLayName = self.dlg.NewLayName.text()
        if len(NewLayName) > 0 and NewLayName not in self.listNameProc: #если имя не пустое - начинаем загрузку
            self.dlg.NewLayName.clear() #очистить поле имени
            # сценарий обработки
            proc = self.dlg.comboBoxTypeProc.currentText()
            # получение слоев из комбобокса
            Vlayer = self.dlg.mMapLayerComboBox.currentLayer()
            # Подложка для обработки
            ph_satel = self.dlg.comboBox_satelit.currentIndex()
            #print(ph_satel)
            # чекбокс (обновить кеш)
            cacheUP = str(self.dlg.checkUp.isChecked())
            #print(cacheUP)
            # Features_lay = Vlayer.getFeatures()
            if ph_satel == 0: #Google
                url_xyz = 'http://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga'
                proj_EPSG = 'epsg:3857' #'3857'
                params = {"source_type": "xyz",
                          "url": "%s" % (url_xyz),
                          "cache_raster": "%s" % (cacheUP),
                          "zoom": "18",  # }#,
                          "projection": "%s" % (proj_EPSG)}  # Проекция

            elif ph_satel == 1: #Yandex
                url_xyz = 'http://sat04.maps.yandex.net/tiles?l=sat&x={x}&y={y}&z={z}'
                proj_EPSG = 'epsg:3395'
                params = {"source_type": "xyz",
                          "url": "%s" % (url_xyz),
                          "cache_raster": "%s" % (cacheUP),
                          "zoom": "18",  # }#,
                          "projection": "%s" % (proj_EPSG)}  # Проекция

            elif ph_satel == 2: # Ручной ввод - секьюр вотч
                infoString = "Поставщиком космических снимков может взыматься плата за их использование!"
                QMessageBox.information(self.dlg, "About", infoString)
                login = self.dlg.line_login_3.text()
                password = self.dlg.mLinePassword_3.text()
                url_xyz = self.dlg.line_server_2.text()

                params = {"source_type": "xyz",
                          "url": "%s" % (url_xyz),
                          "zoom": "18",
                          "cache_raster": "%s" % (cacheUP),
                          "raster_login": "%s" % (login),
                          "raster_password": "%s" % (password)}
            elif ph_satel == 3: # Передача TIF файла для обработки
                uri = self.up_tif()

                params = {"source_type": "tif",
                          "url": "%s" % (uri)}
                print(uri)


            projection = Vlayer.crs() #получаем проекцию EPSG
            projection_text =str(Vlayer.crs()).split(' ')[1][:-1] #текстовое значение проекции EPSG
            projection_text = projection_text.split(":")[1]
            print('Проекция исходного файла:', projection_text)
            #система координат для сервера
            crsDest = QgsCoordinateReferenceSystem(4326)
            #адрес хранения экспортного файла
            file_adrG = self.plugin_dir + NewLayName + '.geojson'
            #экспорт в GEOJSON
            error = QgsVectorFileWriter.writeAsVectorFormat(Vlayer, file_adrG, "utf-8", crsDest, "GeoJSON")
            if error == QgsVectorFileWriter.NoError:
                print("success again!")

            URL_up = self.server + "/rest/processings"

            meta = {"EPSG": "%s" % (projection_text),
                    "CACHE": "%s" % (cacheUP)}
            #print(params)
            #print(meta)
            with open(file_adrG, "r") as read_file:
                GeomJ = json.load(read_file)
            os.remove(file_adrG) #удаление временного файла
            for i in GeomJ['features']:
                #print(i)
                GeomJ = i['geometry']

            GeomJ = str(GeomJ).replace("\'", "\"")
            params = str(params).replace("\'", "\"")
            meta = str(meta).replace("\'", "\"")
            #print(meta)
            # название будущего слоя#тип обработки#геометрия из геоджейсона
            NewLayName = NewLayName
            NewLayName = str(NewLayName).replace("\'", "\\\"")
            #NewLayName = NewLayName.encode('utf-8')

            bodyUp = '{ "name": "%s", "wdName": "%s", "geometry": %s, "params": %s, "meta": %s}' % (NewLayName, proc, GeomJ, params, meta)

            bodyUp = bodyUp.encode('utf-8')

            #print(bodyUp)

            rpost = requests.request("POST", url=URL_up, data=bodyUp, headers=self.headers)
            print(rpost.text)
            print(rpost.status_code)

            # создать и показать сообщение//create a string and show it
            infoString = "Слой загружен на сервер! \n Обработка может занять от 10 секунд до нескольких минут"
            QMessageBox.information(self.dlg, "About", infoString)
        else:
            print('Сначала укажите имя для обработки, выберите полигональный слой и тип обработки')
            # создать и показать сообщение//create a string and show it
            infoString = "Название обработки не задано или уже есть обработка с таким названием. \n Введите другое название!"
            QMessageBox.information(self.dlg, "About", infoString)

        self.button_connect()

    #предпросмотр снимков
    def sart_view(self):
        z_min = self.dlg.zmin.text()
        z_max = self.dlg.zmax.text()
        min_max = "&zmax=" + z_max + "&zmin=" + z_min
        ind_preview = self.dlg.comBox_satelit_mon.currentIndex()#получаем индекс выбора в комбобоксе

        if ind_preview == 0: #Google
            urlWithParams = 'crs=EPSG:3857&format&type=xyz&url=https://mt1.google.com/vt/lyrs%3Ds%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D' + min_max
            rlayer = QgsRasterLayer(urlWithParams, 'Google Satelite ' + z_min + '-' + z_max, 'wms')
            QgsProject.instance().addMapLayer(rlayer)

        elif ind_preview == 1: #Yandex
            urlWithParams = 'crs=EPSG:3395&format&type=xyz&url=http://sat04.maps.yandex.net/tiles?l%3Dsat%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D' + min_max
            rlayer = QgsRasterLayer(urlWithParams, 'Yandex Satelite ' + z_min + '-' + z_max, 'wms')
            QgsProject.instance().addMapLayer(rlayer)
        elif ind_preview == 2: #User input
            # line_server_2 - поле урл

            url = self.dlg.line_server_2.text()# получаем url из настроек

            #замена символов в адресе для корректной работы
            url = url.replace('=', '%3D')
            url = url.replace('&', '%26')
            url = '&url=' + url


            typeXYZ = 'type=xyz'
            login = '&username=' +  self.dlg.line_login_3.text()
            password = '&password=' + self.dlg.mLinePassword_3.text()
            urlWithParams = typeXYZ + url + min_max + login + password
            rlayer = QgsRasterLayer(urlWithParams, 'Cервис от пользователя ' + z_min + '-' + z_max, 'wms')
            QgsProject.instance().addMapLayer(rlayer)
            #print('Загрузка пользовательских снимков')
    #загрузка слоя с сервера
    def addSucces(self):
        # получить номер выбранной строки в таблице!
        row = self.dlg.tableWidget.currentIndex().row()
        #print(row)
        if row != -1:
            # Номер в dictData
            row_nom = (self.kol_tab - row - 1)
            #получаем данные о слое и его ID
            id_v = self.dictData[row_nom]['id']
            #print(id_v)

            URL_f = self.server + "/rest/processings/" + id_v + "/result"
            r = requests.get(url=URL_f, headers=self.headers)

            # получаем ответ
            #print(r.text)
            # адрес для сохранения файла
            name_d = self.dictData[row_nom]['name']

            #Получаем растр-подложку
            #print(self.dictData[row_nom]['rasterLayer']['tileUrl'])
            rastrXYZ = self.dictData[row_nom]['rasterLayer']['tileUrl']
            url = '&url=' + rastrXYZ
            #print(rastrXYZ)
            min_max = "&zmax=18&zmin=0"
            typeXYZ = 'type=xyz'
            login = '&username=' + self.dlg.line_login.text()
            password = '&password=' + self.dlg.mLinePassword.text()
            urlWithParams = typeXYZ + url + min_max + login + password
            rlayer = QgsRasterLayer(urlWithParams, name_d + 'xyz', 'wms')
            QgsProject.instance().addMapLayer(rlayer)

            #x1 = name_d.rfind('_')
            #извлекаем проекцию из метаданных
            Projection = self.dictData[row_nom]['meta']['EPSG'] #name_d[x1 + 1:]

            #система координат для преобразования файла
            crs_EPSG = QgsCoordinateReferenceSystem(Projection)
            #временный файл

            file_temp = self.dlg.input_directory.text() + name_d + '_temp.geojson'
            print(file_temp)
            with open(file_temp, "wb") as f:
                f.write(str.encode(r.text))

            vlayer_temp = QgsVectorLayer(file_temp, name_d+'_temp', "ogr")

            #экспорт в shp
            file_adr = self.dlg.input_directory.text() + name_d + '.shp'
            error = QgsVectorFileWriter.writeAsVectorFormat(vlayer_temp, file_adr, "utf-8", crs_EPSG, "ESRI Shapefile")
            if error == QgsVectorFileWriter.NoError:
                print("success again!")
            #-------------------------------------------------------------------

            #print(file_adr)
            #with open(file_adr, "wb") as f:
             #   f.write(str.encode(r.text))

            # Открытие файла
            vlayer = QgsVectorLayer(file_adr, name_d, "ogr")
            if not vlayer:
                print("Layer failed to load!")
            # Загрузка файла в окно qgis
            QgsProject.instance().addMapLayer(vlayer)

        else:
            print('Сначала выберите слой в таблице')
        try:
            os.remove(file_temp)  # удаление временного файла
        except:
            print('Временный файл удалить не удалось, ну пусть будет, он никому не мешает и весит мало.', file_temp)
    #подключение по сигналу с кнопки"подключить"
    def button_connect(self):
        print('подключение')
        # получаем введенный логин и праоль
        self.login = self.dlg.line_login.text()
        self.password = self.dlg.mLinePassword.text()
        self.server = self.dlg.line_server.text()

        #print(self.login, self.password, self.server)

        URL = self.server + "/rest/processings"
        # we need to base 64 encode it
        # and then decode it to acsii as python 3 stores it as a byte string
        # шифруем логин и пароль (переводим строки в байты)
        userAndPass = b64encode(str.encode(self.login)+b":"+str.encode(self.password)).decode("ascii")
        # составляем хеадер для запроса
        self.authorization = {'Authorization': 'Basic %s' % userAndPass} #для авторизации при загрузке TIF
        self.headers = {'Authorization': 'Basic %s' % userAndPass, 'content-type': "application/json"}
        print('Пользовательский ключ: %s' % userAndPass)
        # выполняем запрос
        r = requests.get(url=URL, headers=self.headers)
        # получаем ответ
        #print(r.text)
        # код ответа
        #print(r.status_code)
        #заполняем комбобокс доступными воркфлоудифинишинсами
        self.WFDefeni()

        # текст ответа от сервера распознаем как json и разбиваем на список со словарями
        self.dictData = json.loads(r.text)
        #print(self.dictData)

        # получаем список ключей по которым можно получить знаечния
        #print(self.dictData[0].keys())

        self.kol_tab = len(self.dictData) #количество элементов
        self.dlg.tableWidget.setRowCount(self.kol_tab)  # создаем строки таблицы
        # перебор в цикле элементов списка и ключей
        nx = 0 #счетчик
        self.listNameProc = []  # список названий обработок
        for i in reversed(range(self.kol_tab)):
            self.listNameProc.append(self.dictData[i]['name']) #заполняем список названий обработок
            #print(self.dictData[i]['projectId'])
            statf = QTableWidgetItem(str(self.dictData[i]['percentCompleted'])+'%')
            namef = QTableWidgetItem(self.dictData[i]['name'])
            createf = QTableWidgetItem(self.dictData[i]['created'])
            Status = QTableWidgetItem(self.dictData[i]['status'])

            #вывод всех значений
            spisok_znachen = ['id',
                              'name',
                              'projectId',
                              'vectorLayer',
                              'rasterLayer',
                              'workflowDef',
                              'aoiCount',
                              'aoiArea',
                              'status',
                              'percentCompleted',
                              'params',
                              'meta',
                              'created',
                              'updated']
            for x in spisok_znachen:
                print(x + ': ', self.dictData[i][x], )
            print('-'*12)

            # вписываем значения в соответствующие ячейки
            self.dlg.tableWidget.setItem(nx, 0, statf)  #
            self.dlg.tableWidget.setItem(nx, 1, namef)
            self.dlg.tableWidget.setItem(nx, 2, Status)
            self.dlg.tableWidget.setItem(nx, 3, createf)
            nx += 1
        print(self.listNameProc)
    def tr(self, message):

        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('Geoalert', message)
    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=False,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):


        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action
    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = self.plugin_dir + '/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Geoalert'),
            callback=self.run,
            parent=self.iface.mainWindow())
    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.tr(u'&Geoalert'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar
    # def run_buffer(self, geom, distance, segments):
    #     if geom is not None:
    #         buf = geom.buffer(distance, segments)
    #         return buf
    #     else:
    #         return None
    def dissolve(self, input_feats):
        # Function to dissolve input features to allow for buffering of multiple features
        feats = []
        # Create and empty list of features and add all features to it.
        # We use feature 0 later and this ensures it exits.
        for each_feat in input_feats:
            feats.append(each_feat)
        # Do not run if geometry is empty, produce an error instead.
        if len(feats) > 0:
            # Need to create empty geometry to hold the dissolved features, we use the first feature to seed it.
            # Combine require a non-empty geometry to work (I could not get it to work).
            feat = feats[0]
            dissolved_geom = feat.geometry()

            # Progress bar for dissolving
            progressMessageBar = self.iface.messageBar().createMessage("Dissolving...")
            progress = QProgressBar()
            progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
            progressMessageBar.layout().addWidget(progress)
            self.iface.messageBar().pushWidget(progressMessageBar)
            maximum_progress = len(feats)
            progress.setMaximum(maximum_progress)
            i = 0

            # Run through the features and dissolve them all.
            for each_feat in feats:
                geom = each_feat.geometry()
                dissolved_geom = geom.combine(dissolved_geom)
                i = i + 1
                progress.setValue(i + 1)
            return_f = QgsFeature()
            return_f.setGeometry(dissolved_geom)
            self.iface.messageBar().clearWidgets()
            return return_f
        else:
            QMessageBox.warning(self.iface.mainWindow(), "Warning",
                                "No features to dissolve.", QMessageBox.Ok)
            return input_feats
    def run(self):
        # Get list of vector layers
        #получение списка векторных слоев
        layers = list(QgsProject.instance().mapLayers().values())

        # Check there is at least one vector layer.
        #Выбор векторных слоев и их подсчет
        vlayer_count = 0
        for layer in layers:
            if layer.type() == QgsMapLayer.VectorLayer:
                vlayer_count = vlayer_count + 1
        # Run the dialog event loop

        if vlayer_count > 0:
            # Открыть диалог
            self.dlg.show()
            #self.dlg.isSomethingSelected()
            result = self.dlg.exec_()

        else:
            # если векторных слоев нет - вывести предупреждение
            QMessageBox.warning(self.iface.mainWindow(), "Warning",
                                "Сначала загрузите векторные слои!", QMessageBox.Ok)
            result = 0
            # See if OK was pressed


        if result == 1 and self.dlg.mMapLayerComboBox.currentLayer():
            buffering_layer = self.dlg.mMapLayerComboBox.currentLayer()

            sel_feats = []
            # Either buffer with all features or just selected ones
            if self.dlg.selectedfeats.isChecked():
                sel_feats = buffering_layer.selectedFeatures()
            else:
                selecting_feats_iterator = buffering_layer.getFeatures()
                sel_feats = []
                for s_feat in selecting_feats_iterator:
                    sel_feats.append(s_feat)

            # Switch between sequential and central buffer styles.
            # A toggle was added, but it seems too complex of a question for most users.
            # buffer_style = "sequential"
            if self.dlg.central_style.isChecked():
                buffer_style = "central"
            else:
                buffer_style = "sequential"

            # Inputs from the dialog:
            if self.dlg.dissovle_button_2.isChecked():
                dissolve_bool = 1
            else:
                dissolve_bool = 0

            segments_to_approximate = self.dlg.segmentsToApproximate.value()

            # Check if regular buffers (no dissolving)
            if self.dlg.radioDonut.isChecked():
                clipper = True
            else:
                clipper = False

            run_csv_buffer = False

            # Check if rings and distance supplied or list of rings as csv
            if self.dlg.radioRings.isChecked():
                num_of_rings = self.dlg.numberOfRings.value()
                buffer_distance = self.dlg.bufferDistance.value()
                # If not dislving we want to start from the outside and come in
                # So smaller buffers will be on top of the bigger ones.
                # We will do this by creating a list
                if not clipper:
                    buffer_csv = []
                    buf_dist = buffer_distance
                    for i in range(num_of_rings):
                        buffer_csv.append(buf_dist)
                        buf_dist += buffer_distance
                    buffer_csv.sort(reverse=True)
                    run_csv_buffer = True

            else:
                buffer_csv = self.dlg.distancesCommaSep.text()
                # Parse csv into list of numbers
                buffer_csv = buffer_csv.split(",")
                try:
                    # Remove negatives
                    buffer_csv = [float(i) for i in buffer_csv if float(i) >= 0]
                    run_csv_buffer = True
                    # Sort list small to large, or large to small if not disolving
                    if clipper:
                        buffer_csv.sort()
                    else:
                        buffer_csv.sort(reverse=True)
                except Exception as e:
                    QMessageBox.warning(self.iface.mainWindow(), "Warning",
                                        "Error in comma seperated numbers: {}.".format(e),
                                        QMessageBox.Ok)
                    result = 0

            add_old_attributes = 1

            # Create data provider for input layer to get fields.
            in_prov = buffering_layer.dataProvider()
            in_fields = in_prov.fields()

            buffer_crs_object = buffering_layer.crs()
            # Check the current CRS of the layer
            buffer_crs = buffer_crs_object.authid()
            # Apply that to the created layer if recognised
            buffer_input_crs = "Polygon?crs=%s" % buffer_crs
            # Create empty memory vector layer for buffers
            layer_name = buffering_layer.name()
            vl = QgsVectorLayer(buffer_input_crs,
                                "%s_geoalert" % layer_name, "memory")
            vl_pr = vl.dataProvider()

            copy_atts = 0
            # Copy old attributes, only if not dissolving multiple features
            if (add_old_attributes == 1 and dissolve_bool == 0) or len(sel_feats) == 1:
                copy_atts = 1
                fields_to_add = []
                for field in in_fields:
                    fields_to_add.append(field)
                vl_pr.addAttributes(fields_to_add)
                vl.updateFields()
            else:
                copy_atts = 0
            # Distance feature for buffer distance
            vl_pr.addAttributes([QgsField("mrb_dist", QVariant.String)])
            vl.updateFields()

            # Dissolve the features if selected.
            if dissolve_bool == 1 and result == 1:
                sel2feats = []
                add_feat = self.dissolve(sel_feats)
                if copy_atts == 1:
                    new_attributes = []
                    for attributes in sel_feats[0].attributes():
                        new_attributes.append(attributes)
                    add_feat.setAttributes(new_attributes)
                # Our buffer loops require a list (as sel_feats originally is), so we append the features to a list.
                sel2feats.append(add_feat)
            else:
                sel2feats = sel_feats

            # Run if there are features in the layer
            if len(sel2feats) > 0 and result == 1:
                # Progress bar.
                progressMessageBar = self.iface.messageBar().createMessage("Buffering...")
                progress = QProgressBar()
                progress.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                progressMessageBar.layout().addWidget(progress)
                self.iface.messageBar().pushWidget(progressMessageBar)
                if run_csv_buffer:
                    maximum_progress = len(sel2feats) * len(buffer_csv)
                else:
                    maximum_progress = len(sel2feats) * num_of_rings
                progress.setMaximum(maximum_progress)
                i = 0

                # Buffer a feature then buffer the buffer (used)
                if run_csv_buffer:
                    buffered = []
                    for each_feat in sel2feats:
                        to_clip = each_feat.geometry()

                        for dist in buffer_csv:
                            geom = each_feat.geometry()
                            buff = self.run_buffer(geom, dist, segments_to_approximate)
                            new_f = QgsFeature()
                            if clipper:
                                new_f_clipped = buff.difference(to_clip)
                            else:
                                new_f_clipped = buff

                            new_f.setGeometry(new_f_clipped)

                            if copy_atts == 1:
                                new_attributes = []
                                for attributes in each_feat.attributes():
                                    new_attributes.append(attributes)
                                new_attributes.append(dist)
                                new_f.setAttributes(new_attributes)
                            else:
                                new_f.setAttributes([dist])

                            buffered.append(new_f)

                            to_clip = to_clip.combine(buff)
                            i += 1
                            progress.setValue(i + 1)
                    vl_pr.addFeatures(buffered)
                    QgsProject.instance().addMapLayer(vl)


                elif buffer_style == "sequential":
                    num_attributes = len(sel2feats[0].attributes())
                    # fix_print_with_import
                    print(num_attributes)
                    new_buff_feats = []
                    distance = buffer_distance
                    while num_of_rings > 0:
                        to_buffer = []
                        for each_feat in sel2feats:
                            geom = each_feat.geometry()
                            buff = self.run_buffer(geom, buffer_distance, segments_to_approximate)
                            new_f = QgsFeature()
                            new_f.setGeometry(buff)
                            new_f_geom = new_f.geometry()
                            new_f_clipped = new_f_geom.difference(geom)
                            new_f2 = QgsFeature()
                            new_f2.setGeometry(new_f_clipped)
                            if copy_atts == 1:
                                new_attributes = []
                                for attributes in each_feat.attributes():
                                    new_attributes.append(attributes)
                                if len(new_attributes) > num_attributes:
                                    # Need to delete the distance field from
                                    # the previous run.
                                    new_attributes = new_attributes[:-1]
                                new_attributes.append(distance)
                                new_f2.setAttributes(new_attributes)
                                new_f.setAttributes(new_attributes)
                            else:
                                new_f2.setAttributes([distance])
                            new_buff_feats.append(new_f2)
                            i += 1
                            to_buffer.append(new_f)
                            progress.setValue(i + 1)
                        sel2feats = to_buffer
                        num_of_rings -= 1
                        distance = distance + buffer_distance
                    vl_pr.addFeatures(new_buff_feats)
                    QgsProject.instance().addMapLayer(vl)

                # Sequential buffers of the original feature with larger buffers
                elif buffer_style == "central":
                    orig_buffer_distance = buffer_distance
                    buffered = []
                    for each_feat in sel2feats:
                        num_to_buffer = num_of_rings
                        to_clip = each_feat.geometry()
                        buffer_distance = orig_buffer_distance

                        while num_to_buffer > 0:
                            geom = each_feat.geometry()
                            buff = self.run_buffer(geom, buffer_distance, segments_to_approximate)
                            new_f = QgsFeature()
                            new_f_clipped = buff.difference(to_clip)
                            new_f.setGeometry(new_f_clipped)

                            if copy_atts == 1:
                                new_attributes = []
                                for attributes in each_feat.attributes():
                                    new_attributes.append(attributes)
                                new_attributes.append(buffer_distance)
                                new_f.setAttributes(new_attributes)
                            else:
                                new_f.setAttributes([buffer_distance])

                            buffered.append(new_f)

                            buffer_distance = buffer_distance + orig_buffer_distance
                            num_to_buffer = num_to_buffer - 1
                            to_clip = to_clip.combine(buff)
                            i += 1
                            progress.setValue(i + 1)
                    vl_pr.addFeatures(buffered)
                    QgsProject.instance().addMapLayer(vl)

            self.iface.messageBar().clearWidgets()