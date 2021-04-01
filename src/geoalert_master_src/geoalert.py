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
# from .geo import geoa
from .geoalert_dialog import GeoalertDialog
import os.path
# добавленные
from qgis.PyQt.QtXml import QDomDocument
import time
import processing
#from multiprocessing import Process
import glob
import qgis
import gdal
import ogr
import osr
import requests
import json
from math import *
from base64 import b64encode, b64decode
from threading import Thread# работа с процессами
import traceback

class Geoalert:

    def __init__(self, iface):
        # self.g = geoa
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

####################################################################
        # создание и настройка таблицы
        self.makeTable()
        # Нажатие кнопки "Подключить"
        self.dlg.ButtonConnect.clicked.connect( self.button_connect )
        # загрузить выбраный результат
        self.dlg.ButtonDownload.clicked.connect(self.addSucces)
        # Кнопка: Выгрузить слой на сервер для обработки
        self.dlg.ButtonUpload.clicked.connect(self.uploadOnServer)
        # кнопка удаления слоя
        self.dlg.ButtonDel.clicked.connect(self.DelLay)
        # Кнопка подключения снимков
        self.dlg.Button_view.clicked.connect(self.sart_view)
        # кнопка выбора папки через обзор
        self.dlg.but_dir.clicked.connect(self.select_output_file)
        # чтение настроек логин/пароль
        self.readSettings()
        # чтение настроек логин/пароль для сервиса космоснимков
        self.readSettingsMap()
        # чекбокс сохранения логин и пароль для сервиса космоснимков
        self.dlg.checkSatelitPass.clicked.connect(self.storeSettingsMap)
        # чекбокс сохранения логин и пароль для Geoalert
        self.dlg.savePass_serv.clicked.connect(self.storeSettings)
        # загрузка рабочей папки из настроек в интерфейс
        self.get_output_file()
        # срабатывает при выборе источника снимков в комбобоксе
        self.dlg.comboBox_satelit.activated.connect(self.comboClick)
        #загрузка полей комбобокса
        self.comboImageS()


# ------------------------------
    # создание и настройка таблицы
    def makeTable(self):
        self.dlg.tableWidget.clear()
        stolbci = [u" Processing", u"Name", u"Status", u"Сreated", u"ID"]
        StolbKol = len(stolbci)  # 4#количество столбцов
        self.dlg.tableWidget.setColumnCount(StolbKol)  # создаем столбцы
        self.dlg.tableWidget.setHorizontalHeaderLabels(stolbci)  # даем названия столбцам
        # перебор всех столбцов и настройка
        for nom in range(StolbKol):
            # Устанавливаем выравнивание на заголовки
            self.dlg.tableWidget.horizontalHeaderItem(nom).setTextAlignment(Qt.AlignCenter)
        # указываем ширину столбцов
        self.dlg.tableWidget.setColumnWidth(0, 80)
        self.dlg.tableWidget.setColumnWidth(1, 200)
        self.dlg.tableWidget.setColumnWidth(4, 50)
        # выделять всю строку при нажатии
        self.dlg.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        # запретить редактировать таблицу пользователю
        self.dlg.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # включить сортировку в таблице
        self.dlg.tableWidget.setSortingEnabled(True)
    # загрузка рабочей папки из настроек в интерфейс
    def get_output_file(self):
        s = QgsSettings()
        name = s.value("geoalert/workDir", "", type=str)
        self.dlg.input_directory.setText(name)  # вписываем адрес в поле
    # выбор рабочей папки
    def select_output_file(self):
        # доступ к настройкам
        s = QgsSettings()
        # адрес папки
        filename = QFileDialog.getExistingDirectory(None, "Select Folder") + '/'
        # запоминаем адрес в файл для автоматической подгрузки, если он не пустой
        if len(filename) > 1:
            self.dlg.input_directory.setText(filename)
            # записываем в настройки
            s.setValue("geoalert/workDir", filename)

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
                    # if wfd[0] == 0: #устанавливаем выбранным первый пункт в списке
                    #     self.dlg.comboBoxTypeProc.setText(wfd[1]['name'])
                except:
                    print('Не добавлен дефенишенс:', wfd[1]['name'])
                    None
            return True  # разрешить дальнейшее выполнение
        elif str(r) == '<Response [401]>':  # пароль НЕ верный, показать предупреждение!
            self.flag = 'report error'
            print('Wrong login or password! Please try again.')

            return False#self.flag

    # выбор tif для загрузки на сервер
    def select_tif(self):
        filename = QFileDialog.getOpenFileName(None, "Select .TIF File", './', 'Files (*.tif *.TIF *.Tif)')
        # запоминаем адрес в файл для автоматической подгрузки, если он не пустой
        print(filename)
        if len(filename[0]) > 0:
            return filename[0]

    # загрузка tif на сервер
    def up_tif(self, n):
        #получаем адрес файла
        file_in = self.listLay[n][1].dataProvider().dataSourceUri()

        headers = self.authorization # формируем заголовок для залогинивания
        files = {'file': open(file_in, 'rb')}
        ip = self.server
        URL_up = ip + '/rest/rasters'
        r = requests.post(URL_up, headers=headers, files=files)
        print('Ответ сервера:', r.text)

        if 'url' in r.text:
            url = r.json()['url'] #получаем адрес для использования загруженного файла
            print('Используется: URL')
        elif 'uri' in r.text:
            url = r.json()['uri']  # получаем адрес для использования загруженного файла
            print('Используется: URI')
        params = {"source_type": "tif", "url": "%s" % (url)}
        self.upOnServ_proc(params)

    # Удалить слой
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

        # всплывающее сообщение
        self.iface.messageBar().pushMessage("Massage", "Processing has been removed.",
                                            level=Qgis.Warning,
                                            duration=7)
        #обновить список слоев
        self.button_connect()

    #срабатывание от выбора в комбобоксе
    def comboClick(self):
        comId = self.dlg.comboBox_satelit.currentIndex()
        # открытие tif файла
        if comId == 2:
            self.addres_tiff = self.select_tif() #выбрать tif на локальном компьютере
            #print('comb:', self.addres_tiff)
            #если адрес получен
            if self.addres_tiff:
                nameL = os.path.basename(self.addres_tiff)[:-4]
                #добавление растра в QGIS
                self.iface.addRasterLayer(self.addres_tiff, nameL)

                #заполнение комбобокса
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

    # заполнение комбобокса
    def comboImageS(self):
        self.dlg.comboBox_satelit.clear()
        ll = ['Mapbox Satellite', self.tr('Custom (in settings)'), 'Open new .tif']
        # заполняем обязательные пункты
        for idx, field in enumerate(ll):
            self.dlg.comboBox_satelit.addItem(field, idx)

        print('-----------------------------------')
        # заполняем локальными подключенными растрами
        #self.comboImageS()
        self.listLay = []
        layersAll = QgsProject.instance().mapLayers()
        # print(layersAll)
        id = 3
        # перебор всех слоев и проверка их типа
        for i in layersAll:
            # тип слоя
            nType = QgsProject.instance().mapLayers()[i].type()
            if nType == 1:
                # тип растра
                rt = QgsProject.instance().mapLayers()[i].rasterType()
                # если тип = локальному растру
                if rt == 2:
                    # добавляем название и растр в список
                    name = QgsProject.instance().mapLayers()[i].name()
                    lay = QgsProject.instance().mapLayers()[i]

                    self.listLay.append([name, lay])
                    # print(name)
                    self.dlg.comboBox_satelit.addItem(name, id)
                    id += 1
        print(self.listLay)


    # Выгрузить слой на сервер для обработки
    def uploadOnServer(self, iface):
        NewLayName = self.dlg.NewLayName.text()
        if len(NewLayName) > 0 and NewLayName not in self.listNameProc: #если имя не пустое - начинаем загрузку

            # Подложка для обработки
            ph_satel = self.dlg.comboBox_satelit.currentIndex()
            #print(ph_satel)
            # чекбокс (обновить кеш)
            cacheUP = str(self.dlg.checkUp.isChecked())

            print(cacheUP)

            #всплывающее сообщение
            self.iface.messageBar().pushMessage("Massage", "Please, wait. Uploading a file to the server...",
                                                level=Qgis.Info,
                                                duration=15)

            if ph_satel == 0: #Mapbox Satellite
                url_xyz = ''
                proj_EPSG = 'epsg:3857'
                params = {"source_type": "xyz",
                          "url": "%s" % (url_xyz),
                          "cache_raster": "%s" % (cacheUP),
                          "zoom": "18",
                          "projection": "%s" % (proj_EPSG)}  # Проекция
                self.upOnServ_proc(params)
            elif ph_satel == 1: #Custom
                infoString = "Поставщиком космических снимков может взыматься плата за их использование!"
                QMessageBox.information(self.dlg, "About", infoString)
                login = self.dlg.line_login_3.text()
                password = self.dlg.mLinePassword_3.text()
                url_xyz = self.dlg.line_server_2.text()
                # TypeURL = self.dlg.comboBoxURLType.currentIndex()  # выбран тип ссылки///

                TypeURL = self.dlg.comboBoxURLType.currentText()

                params = {"source_type": TypeURL,
                          "url": "%s" % (url_xyz),
                          "zoom": "18",
                          "cache_raster": "%s" % (cacheUP),
                          "raster_login": "%s" % (login),
                          "raster_password": "%s" % (password)}
                self.upOnServ_proc(params)

            # загрузка выбранного .tif
            elif ph_satel > 2: #
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
        NewLayName = self.dlg.NewLayName.text()
        # получение слоев из комбобокса
        Vlayer = self.dlg.mMapLayerComboBox.currentLayer()
        # сценарий обработки
        proc = self.dlg.comboBoxTypeProc.currentText()

        # чекбокс (обновить кеш)
        cacheUP = str(self.dlg.checkUp.isChecked())
        # projection = Vlayer.crs() #получаем проекцию EPSG
        projection_text = str(Vlayer.crs()).split(' ')[1][:-1]  # текстовое значение проекции EPSG
        projection_text = projection_text.split(":")[1]
        print('Проекция исходного файла:', projection_text)
        # система координат для сервера
        crsDest = QgsCoordinateReferenceSystem(4326)
        # адрес хранения экспортного файла
        file_adrG = self.plugin_dir + NewLayName + '.geojson'
        # экспорт в GEOJSON
        error = QgsVectorFileWriter.writeAsVectorFormat(Vlayer, file_adrG, "utf-8", crsDest, "GeoJSON")
        if error == QgsVectorFileWriter.NoError:
            print("success again!")

        URL_up = self.server + "/rest/processings"

        meta = {"EPSG": "%s" % (projection_text),
                "CACHE": "%s" % (cacheUP)}
        # print(params)
        # print(meta)
        with open(file_adrG, "r") as read_file:
            GeomJ = json.load(read_file)
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

        rpost = requests.request("POST", url=URL_up, data=bodyUp, headers=self.headers)
        print(rpost.text)
        print(rpost.status_code)

        self.dlg.NewLayName.clear()  # очистить поле имени

        # создать и показать сообщение//create a string and show it
        infoString = "Слой загружен на сервер! \n Обработка может занять от 10 секунд до нескольких минут"
        print(infoString)
        # QMessageBox.information(self.dlg, "About", infoString)
        self.button_connect()

    # предпросмотр снимков
    def sart_view(self):

        # сохранение настроек логин/пароль
        self.storeSettingsMap()

        # если чекбокс включен - ограничиваем зум предпросмотра до 14
        if self.dlg.checkSatelit_Z14.isChecked():
            z_max = '14'  # self.dlg.zmax.text()
        # иначе ограничиваем до 18
        else:
            z_max = '18'

        z_min = '0'#self.dlg.zmin.text()
        min_max = "&zmax=" + z_max + "&zmin=" + z_min
        preview_type = self.dlg.comboBoxURLType.currentText()#получаем

        url = self.dlg.line_server_2.text()# получаем url из настроек
        #замена символов в адресе для корректной работы
        url = url.replace('=', '%3D')
        url = url.replace('&', '%26')
        url = '&url=' + url

        typeXYZ = 'type='+ preview_type
        login = '&username=' + self.dlg.line_login_3.text()
        password = '&password=' + self.dlg.mLinePassword_3.text()
        urlWithParams = typeXYZ + url + min_max + login + password
        rlayer = QgsRasterLayer(urlWithParams, self.tr('User_servise ') + z_min + '-' + z_max, 'wms')
        QgsProject.instance().addMapLayer(rlayer)
        #print('Загрузка пользовательских снимков')

        # self.dlg.comboBox_satelit.setDisabled(False) # активация элемента

    # загрузка слоя с сервера
    def addSucces(self):
        # получить номер выбранной строки в таблице!
        row = self.dlg.tableWidget.currentIndex().row()
        print(row)
        #print(row)
        if row != -1:
            # # Номер в dictData
            # row_nom =  (self.kol_tab - row - 1)
            # #получаем данные о слое и его ID
            # id_v = self.dictData[row_nom]['id']
            # #print(id_v)

            id_v = self.dlg.tableWidget.model().index(row, 4).data()
            print(id_v)
            URL_f = self.server + "/rest/processings/" + id_v + "/result"
            r = requests.get(url=URL_f, headers=self.headers)

            # адрес для сохранения файла
            name_d = self.dlg.tableWidget.model().index(row, 1).data() #self.dictData[row_nom]['name']

            # находим ссылку на растр по id
            for dD in self.dictData:
                #print(dD)
                if dD['id'] == id_v:

                    rastrXYZ = dD['rasterLayer']['tileUrl']
                    print(rastrXYZ)
                    break

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
            # извлекаем проекцию из метаданных/перестали извлекать, задали фиксированную
            Projection = 'EPSG:4326'  # self.dictData[row_nom]['meta']['EPSG'] #name_d[x1 + 1:]

            #система координат для преобразования файла
            crs_EPSG = QgsCoordinateReferenceSystem(Projection)

            #временный файл
            file_temp = self.dlg.input_directory.text() + name_d + '_temp.geojson'
            #print(file_temp)
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
            time.sleep(1)
            qgis.utils.iface.zoomToActiveLayer()  # приблизить к охвату активного слоя
            try:
                os.remove(file_temp)  # удаление временного файла
                print('Временный файл удален:', file_temp)
            except:
                print('Временный файл удалить не удалось, ну пусть будет, он никому не мешает и весит мало:', file_temp)

        else:
            print('Сначала выберите слой в таблице')

    # всплывающее сообщение
    def messege(self, infoString): # Всплывающее сообщение
        QMessageBox.information(self.dlg, self.tr('About'), infoString)
    # подключение к серверу
    def button_connect(self): # подключение и обновление в отдельном процессе
        #проверка рабочей папки
        if os.path.exists(self.dlg.input_directory.text()) != True:
            infoString = self.tr('The working direktory was not found. Specify the direktory folder.')
            self.messege(infoString)
        else:
            # сохранить/сбросить пароль
            self.storeSettings()

            # получаем введенный логин и праоль
            self.login = self.dlg.line_login.text()
            self.password = self.dlg.mLinePassword.text()
            self.server = self.dlg.line_server.text()
            URL = self.server + "/rest/processings"
            # we need to base 64 encode it
            # and then decode it to acsii as python 3 stores it as a byte string
            # шифруем логин и пароль (переводим строки в байты)
            userAndPass = b64encode(str.encode(self.login) + b":" + str.encode(self.password)).decode("ascii")
            # составляем хеадер для запроса
            self.authorization = {'Authorization': 'Basic %s' % userAndPass}  # для авторизации при загрузке TIF
            self.headers = {'Authorization': 'Basic %s' % userAndPass, 'content-type': "application/json"}

            # заполняем комбобокс доступными воркфлоудифинишинсами
            self.flag = self.WFDefeni()

            # сообщение о неверном логине/пароле
            if self.flag == False:  # 'report error':  # Если была ощибка
                infoString = self.tr('Wrong login or password! Please try again.')
                self.messege(infoString)
            else:
                #запуск потока
                proc = Thread(target=self.button_con, args=(URL,))
                proc.start()
    # циклическое переподключение к серверу для получения статусов обработок
    def button_con(self, URL):
        while self.flag == True:

            # выполняем запрос
            r = requests.get(url=URL, headers=self.headers)
            #print(r.text) # получаем ответ
            #print(r.status_code) # код ответа
            # текст ответа от сервера распознаем как json и разбиваем на список со словарями
            self.dictData = json.loads(r.text)
            #print(self.dictData)
            # получаем список ключей по которым можно получить знаечния
            #print(self.dictData[0].keys())

            self.kol_tab = len(self.dictData) #количество элементов
            self.dlg.tableWidget.setRowCount(self.kol_tab)  # создаем строки таблицы
            # перебор в цикле элементов списка и ключей
            nx = 0 #счетчик
            self.flag = False
            self.listNameProc = []  # список названий обработок
            for i in reversed(range(self.kol_tab)):
                self.listNameProc.append(self.dictData[i]['name'])  # заполняем список названий обработок
                #print(self.dictData[i]['projectId'])
                statf = QTableWidgetItem(str(self.dictData[i]['percentCompleted'])+'%')
                namef = QTableWidgetItem(self.dictData[i]['name'])
                Status = QTableWidgetItem(self.dictData[i]['status'])
                ids = QTableWidgetItem(self.dictData[i]['id'])
                #дата и время создания
                cre = self.dictData[i]['created']
                cre2 = cre.split('T')
                createf = QTableWidgetItem(cre2[0] + ' ' + cre2[1][:8])

                if self.dictData[i]['status'] == "IN_PROGRESS": #если хоть одна задача в процессе выполнения
                    self.flag = True #добавляем значение для обновления статуса

                # вывод всех значений
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

                # вписываем значения в соответствующие ячейки
                self.dlg.tableWidget.setItem(nx, 0, statf)
                self.dlg.tableWidget.setItem(nx, 1, namef)
                self.dlg.tableWidget.setItem(nx, 2, Status)
                self.dlg.tableWidget.setItem(nx, 3, createf)
                self.dlg.tableWidget.setItem(nx, 4, ids)

                nx += 1

            if self.flag == True:
                secn = 5 # задержка обновления в секундах
                print('Обновление через', secn, 'секунд')
                time.sleep(secn) # ожидание следующей итеррации
    # запись переменных в хранилилище настроек
    def storeSettings(self):
        print('сохранение настроек Geoalert')
        # доступ к настройкам
        s = QgsSettings()
        # если включен чекбокс сохранять пароль
        if self.dlg.savePass_serv.isChecked():
            login = self.dlg.line_login.text()
            password = self.dlg.mLinePassword.text()
            # сохраняем настройку чекбокса
            s.setValue("geoalert/checkPas_serv", True)
        else: # иначе сохранять пустые значения
            login = ''
            password = ''
            # сохраняем настройку чекбокса
            s.setValue("geoalert/checkPas_serv", False)
        #кодируем в base64 и записываем в настройки
        s.setValue("geoalert/log", login)#unicode(b64encode(str.encode(login))))
        s.setValue("geoalert/pas", password)#unicode(b64encode(str.encode(password))))
    # чтение переменных из хранилища настроек
    def readSettings(self):
        # доступ к настройкам
        s = QgsSettings()
        # если в настройках включен чекбокс,
        if s.value("geoalert/checkPas_serv"):
            # включаем чекбокс в окне
            self.dlg.savePass_serv.setChecked(True)
            # загружаем логин/пароль и вставляем в поля
            loginB64 = s.value("geoalert/log", "", type=str)
            passwordB64 = s.value("geoalert/pas", "", type=str)
            self.dlg.line_login.setText(loginB64) #b64decode(loginB64))
            self.dlg.mLinePassword.setText(passwordB64) #b64decode(passwordB64))
    # запись переменных в хранилилище настроек
    def storeSettingsMap(self):
        print('сохранение настроек сервиса космоснимков')
        # доступ к настройкам
        s = QgsSettings()
        # если включен чекбокс сохранять пароль
        if self.dlg.checkSatelitPass.isChecked():
            login = self.dlg.line_login_3.text()
            password = self.dlg.mLinePassword_3.text()
            # сохраняем настройку чекбокса
            s.setValue("geoalert/checkSatelitPass", True)
        else:  # иначе сохранять пустые значения
            login = ''
            password = ''
            # сохраняем настройку чекбокса
            s.setValue("geoalert/checkSatelitPass", False)
        # кодируем в base64 и записываем в настройки
        s.setValue("geoalert/logMap", login)  # unicode(b64encode(str.encode(login))))
        s.setValue("geoalert/pasMap", password)  # unicode(b64encode(str.encode(password))))
    # чтение переменных из хранилища настроек
    def readSettingsMap(self):
        # доступ к настройкам
        s = QgsSettings()
        # если в настройках включен чекбокс,
        if s.value("geoalert/checkSatelitPass"):
            # включаем чекбокс в окне
            self.dlg.checkSatelitPass.setChecked(True)
            # загружаем логин/пароль и вставляем в поля
            loginB64 = s.value("geoalert/logMap", "", type=str)
            passwordB64 = s.value("geoalert/pasMap", "", type=str)
            self.dlg.line_login_3.setText(loginB64)  # b64decode(loginB64))
            self.dlg.mLinePassword_3.setText(passwordB64)  # b64decode(passwordB64))

#############################################################
#############################################################
#############################################################
    def tr(self, message):
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('Geoalert', message)
    def add_action(self, icon_path, text, callback, enabled_flag=True, add_to_menu=False,
                    add_to_toolbar=True, status_tip=None, whats_this=None, parent=None):

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
    def run(self):
        # Открыть диалог
        self.dlg.show()
        self.dlg.exec_()