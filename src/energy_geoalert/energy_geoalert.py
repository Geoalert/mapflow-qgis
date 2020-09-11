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
from .energy_geoalert_dialog import EnergyGeoalertDialog
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

class EnergyGeoalert:

    def __init__(self, iface):

        self.iface = iface
        # определяем папку в которой находится модуль
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]

        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'EnergyGeoalert_{}.qm'.format(locale))
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Создание диалога (после перевода) and keep reference
        self.dlg = EnergyGeoalertDialog()

        # Declare instance attributes
        self.actions = []
        #self.menu = self.tr(u'&Inspector energy')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'Inspector_energy')
        self.toolbar.setObjectName(u'Inspector_energy')


#-------!!!!элементы известного кода!!!!!
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
        #self.dlg.tableWidget.setColumnWidth(2, 170)
        #self.dlg.tableWidget.setColumnWidth(3, 170)
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
#-------Вкладка (Подготовка к обработке)
            #добавление типа опоры в список
        self.dlg.ButtonAddToList.clicked.connect(self.writeCSV)
            #удаление типа опоры из списка
        self.dlg.ButtonDelToList.clicked.connect(self.DelCSV)
        self.ListCSV() # загрузки списка типов опор в окно
        self.dlg.vectorComboBox.layerChanged.connect(self.PointProc) #смена выбора в комбобоксе
        if self.dlg.vectorComboBox.currentLayer() != None:
            self.PointProc() # заполнение полей комбобокса
        #кнопка начала обработки точечного слоя
        self.dlg.Button_CreateBufer.clicked.connect(self.CreateBufer)

        self.dlg.listWidget_2.clicked.connect(self.intype) # двойной клик на найденную папку

        # Кнопка предпросмотра снимков
        self.dlg.Button_view.clicked.connect(self.sart_view)
#------------------------------
    #Настройки
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
#ОТЧЕТ
        self.dlg.vectorComboBox_2.layerChanged.connect(self.PointProc_2)  # смена выбора в комбобоксе
        if self.dlg.vectorComboBox_2.currentLayer() != None:
            self.PointProc_2() # заполнение полей комбобокса
        # кнопка генерировать отчет
        self.dlg.ButtonAddReport.clicked.connect(self.report)
        # кнопка выбора папки сохранения отчета через обзор
        self.dlg.but_dir_2.clicked.connect(self.select_output_file_2)



#-------------------------------------------------------------------------

    # получаем список дефинишинсов
    def WFDefeni(self):
            URL_up = self.server + '/rest/projects/default'  # url запроса
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

        #вписываем тип опоры в поле добавления
    def intype(self):
        # получаем id выделенной строки
        x = self.dlg.listWidget_2.currentRow()
        text = self.no_type_list[x]

        self.dlg.NameOpor.clear()
        self.dlg.NameOpor.setText(text)
    #загрузка списка опор в окно
    def ListCSV(self):
        #загружаем список из файла
        self.adr_csv = self.plugin_dir + '/types.csv'
        r_file = []
        self.list_opor = []
        #чтение файла построчно
        with open(self.adr_csv, "r") as read_file_csv:
            for x in read_file_csv:
                r_file.append(x[:-1])
                self.list_opor.append(x[:-1].split(';'))
                #print( float((x[:-1].split(';'))[2]) )
        #print(self.list_opor)
        self.dlg.listWidget.clear()

        #отображение списка типов опор в таблице
        self.dlg.listWidget.addItems(r_file)


        #--------------------------------------------
    #добавление нового типа опоры
    def writeCSV(self):
        #получаем данные из полей
        NameOpor = self.dlg.NameOpor.text()

        #траверсы опор
        TrLeft = self.dlg.TrLeft.text().replace(",", ".")
        TrRight = self.dlg.TrRight.text().replace(",", ".")

        with open(self.adr_csv, "a") as read_file_csv:
            #Если поля не пустые, записываем в файл
            if len(NameOpor) > 0 and len(TrLeft) > 0 and len(TrRight) > 0:
                #if ';' in NameOpor:

                textW = "%s;%s;%s\n" % (NameOpor, TrLeft, TrRight)
                #print(textW)
                read_file_csv.write(textW)
                #чистим поля
                self.dlg.NameOpor.clear()
                self.dlg.TrLeft.setValue(0.00)
                self.dlg.TrRight.setValue(0.00)

            else:
                print('Заполните все поля')
        # обновим список в окне
        self.ListCSV()
    # удаление типа опоры из списка
    def DelCSV(self):
        #получаем id выделенной строки
        id_in_list = self.dlg.listWidget.currentRow()
        print(id_in_list)
        if id_in_list > -1: #если строка выделена..
            # чтение файла построчно
            with open(self.adr_csv, "r") as read_file_csv:
                r_file = []
                for x in read_file_csv:
                    r_file.append(x)
            # открываем для записи
            with open(self.adr_csv, "w") as read_file_csv:
                for z in range(len(r_file)):
                    if z != id_in_list:#перезаписываем все строки кроме удаляемой
                        read_file_csv.write(r_file[z])

        self.ListCSV()
    #заполнение комбобоксов полями слоя

    def PointProc_2(self):
        # получение слоев из комбобокса
        self.Poilayer_2 = self.dlg.vectorComboBox_2.currentLayer()
        #чистим комбобоксы
        self.dlg.categoryComboBox_2.clear()
        #заполняем комбобоксы названиями полей с их индексами
        try:
            for idx, field in enumerate(self.Poilayer_2.fields()):
                self.dlg.categoryComboBox_2.addItem(field.name(), idx)
                #print(idx, field.name())
        except:
            None

    def PointProc(self):
        # получение слоев из комбобокса
        self.Poilayer = self.dlg.vectorComboBox.currentLayer()
        #чистим комбобоксы
        self.dlg.categoryComboBox.clear()
        self.dlg.comboType.clear()

        try:
            #заполняем комбобоксы названиями полей с их индексами
            for idx, field in enumerate(self.Poilayer.fields()):
                self.dlg.categoryComboBox.addItem(field.name(), idx)
                self.dlg.comboType.addItem(field.name(), idx)
                #print(idx, field.name())
        except:
            None
    # Определение координат точки зная угол и расстояние от исходной точки.
    # координаты точки списком ['x','y'], расстояние отклонения точки, угол в радианах
    def PointXY(self, pointAxy, radius, n_rad):
        xA, yA = float(pointAxy[0]), float(pointAxy[1])
        #print('cosinus:', cos(n_rad))
        #print('umnoszhenie:', cos(n_rad) * radius)
        xB = xA + (cos(n_rad) * radius)
        yB = yA + (sin(n_rad) * radius)
        return [xB, yB] #возвращаем координаты списком
    #!!Обработка!!создание линий и буфера по точкам
    def CreateBufer(self):
        # получение слоев из комбобокса
        self.Poilayer = self.dlg.vectorComboBox.currentLayer()
        print('Имя слоя:', self.Poilayer)
        nameF = str(self.Poilayer).split("'")[1] #имя слоя

        numOp = self.dlg.categoryComboBox.currentIndex()#индекс атрибута с номером опоры #получение индекса элемента в комбобоксе
        typeOp = self.dlg.comboType.currentIndex() #индекс атрибута с типом опоры
        #typeOp = self.dlg.comboType.currentText()#получение текстовго значения элемента в комбобоксе
        classNapr_text = self.dlg.classNapr.currentText() #класс напряжения
        # ширина охранной зоны по классам напряжения, м
        if classNapr_text == '35':
            self.classNapr = 15
        elif classNapr_text == '110':
            self.classNapr = 20
        elif classNapr_text == '150, 220':
            self.classNapr = 25
        elif classNapr_text == '300, 500':
            self.classNapr = 30
        elif classNapr_text == '750':
            self.classNapr = 40
        elif classNapr_text == '1150':
            self.classNapr = 55
        print('Класс напряжения, Охранная зона:', classNapr_text, self.classNapr)
        #print('Индексы полей: номера опор и типов опор:',numOp, typeOp)
        #итеррируемая таблица атрибутов слоя
        iter = self.Poilayer.getFeatures(QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry))
        numbList = [] #список номеров опор
        traversList = [] # список траверс опор [0]- левая [1] - правая
        no_type_list = [] # типы опор из файла, которых нет в базе
        signal = 1
        for feature in iter: #перебор атрибутов каждого объекта
            attrs = feature.attributes()
            # For now just search as if it were a string
            #print(attrs)
            #print(attrs[numOp]) #выбор атрибута по индексу из комбобокса
            #если оба атрибута не имеют пустых полей...
            if attrs[numOp] != None and attrs[typeOp] != None:
                numbList.append(attrs[numOp]) # добавляем в список номера опор
                # Проверяем наличие типов опор в базе,
                # если такого не нашли, добавляем в отдельный спиок

                len1 = len(traversList) #проверяем длинну списка до цикла и проверки на совпадения
                for type in self.list_opor:
                    #print(attrs[typeOp], type[0])
                    if attrs[typeOp] == type[0]:
                        traversList.append([type[1], type[2]])
                        #print('УСПЕХ!!!!')
                        break#если нашли совпадение, добавляем его в список и прерываем цикл
                len2 = len(traversList) #проверяем длинну списка после цикла и проверки на совпадения

                if len1 == len2: #если в список ничего не добавили
                    if attrs[typeOp] not in no_type_list:
                        no_type_list.append(attrs[typeOp])
                        print('нет в базе')
                self.no_type_list = no_type_list
                self.dlg.listWidget_2.clear()
                self.dlg.listWidget_2.addItems(no_type_list)
                  # добавляем в список типы опор
            else:
                # создать и показать сообщение//create a string and show it
                infoString = "Атрибуты номера и типов опор должны быть заполнены обязательно." \
                             "Заполните пустующие поля и повторите попытку."
                QMessageBox.information(self.dlg, "Ахтунг!", infoString)
                #print('нет номера опоры')
                signal = 0
                break

        if signal == 1: #если нет пустых полей - выполняем дальше
            #print(no_type_list)
            #print(numbList, typeList)
            #print('-*' * 8)
            geomList = [] # Список геометрии
            for f in self.Poilayer.getFeatures(  ): #получаем все объекты из слоя по очереди
                #print(f.id()) #id объекта
                f = f.geometry().asPoint() #трансформируем геометрию в точку с координатами
                #print(f)
                geomList.append([f.x(), f.y()])  # добавляем в список координаты
                #print(f.x(), f.y())
            #print(geomList)
            self.dic = {} #словарь где ключь=номер опоры, значение = тип и геометрия
            dlin = len(numbList)
            for n in range(dlin):
                #заполняем словарь
                self.dic.update({numbList[n]:[traversList[n],geomList[n]]})
            #print(dic)
            self.sotrD = sorted(self.dic)
            #print(sotrD)
            line = ogr.Geometry(ogr.wkbLineString)#создаем линию

            for i in self.sotrD: #перебор точек по возрастанию номеров
                #print(self.dic[i]) #получение значений по ключу
                line.AddPoint(self.dic[i][1][0], self.dic[i][1][1]) #добавляем точки к линии



            print(line)

            #экспортируем в файл
            #и записываем адрес файл
            self.os_line = self.shape_export([line], '_central', ogr.wkbLineString, 0)
            print('Файл осевой линии создан')
            self.provoda()


    #экспорт во временный слой. Передаем списком объекты, окончание к названию, тип геометрии
    #возвращает временный векторный слой
    def export_vlayer(self, geometry, postfix, type_geom, nameF):
        #print(geometry)
        flag = True
        if nameF == 0:
            flag = False
            nameF = str(self.Poilayer).split("'")[1]  # имя исходного слоя
            name_oporyX2 = self.sotrD + self.sotrD
            smeschen = len(self.sotrD)
            # добавляем по два раза одно название для левого и правого пролета
            #print(name_oporyX2)
        name_d = nameF + postfix
        # указание драйвера
        driverName = "ESRI Shapefile"
        drv = ogr.GetDriverByName(driverName)
        if drv is None:
            print("%s Драйвер не поключился.\n" % driverName)
        # создание файла
        # создание новоо слоя
        file_adr = self.dlg.input_directory.text() + nameF + postfix +'.shp'
        ogrData_save = drv.CreateDataSource(file_adr)
        layerName = os.path.basename(self.dlg.input_directory.text() + nameF)
        #--проекция
        #получение проекции из слоя
        projPoi = str(self.Poilayer.crs()).split(' ')[1][:-1]  # текстовое значение проекции EPSG
        projPoi = int(projPoi.split(":")[1])
        #создание и указание проекции
        self.srs = osr.SpatialReference()
        self.srs.ImportFromEPSG(projPoi)
        try:
            layer_save = ogrData_save.CreateLayer(layerName, self.srs, geom_type=type_geom, options=['ENCODING=UTF-8'])
        except:
            infoString = 'Слой "%s" уже открыт в QGIS. Для перезаписи удалите этот слой из QGIS и запустите обработку повторно.' % (name_d)
            QMessageBox.information(self.dlg, "Ахтунг!", infoString)

        # копируем созданную геометрию(и прикреплённые к ней значения полей)
        # добавлем новое поле

        fieldDef = ogr.FieldDefn( "id", ogr.OFTString )
        fieldDef.SetWidth( 30 )
        if layer_save.CreateField ( fieldDef ) != 0:
            print("не могу создать поле %s" % fieldDef.GetNameRef())
        # fieldDef = ogr.FieldDefn("name", ogr.OFTString)
        # fieldDef.SetWidth( 30 )
        # if layer_save.CreateField ( fieldDef ) != 0:
        #     print("не могу создать поле %s" % fieldDef.GetNameRef())
        # создание полей для полигонов
        if flag == False:

            for name_field in ['name', 'len', 'l', 'r', 'side']:

                fieldDef = ogr.FieldDefn(name_field, ogr.OFTString)
                fieldDef.SetWidth(30)
                if layer_save.CreateField(fieldDef) != 0:
                    print("не могу создать поле %s" % fieldDef.GetNameRef())


            # непонятная поправлялка для полигонов
        if type_geom == ogr.wkbPolygon:#если тип - полигон, то обрабатывать таким макаром
            n_1 = 0
            side_atr = 'L'
            for ring in geometry:
                # Create polygon
                poly = ogr.Geometry(ogr.wkbPolygon)
                poly.AddGeometry(ring)
                # создаем OGRFeature (фигуру/объект)
                feat = ogr.Feature(layer_save.GetLayerDefn())
                feat.SetGeometry(poly)  # присоединяем геометрию к OGRFeature
                outFeat = ogr.Feature(layer_save.GetLayerDefn())

                if flag == False:
                    feat.SetField('type', 'poligon')  # устанавливаем атрибут
                    if n_1 == smeschen-1:
                        n_1 = 0
                        side_atr = 'R'

                    name_atr = str(name_oporyX2[n_1]) + '_' + str(name_oporyX2[n_1 + 1])  # название пролета
                    feat.SetField('name', name_atr)  # устанавливаем атрибут

                    # if n_1 < smeschen - 1:
                    #     side_atr = 'L'
                    # else:
                    #     side_atr = 'R'
                    feat.SetField('side', side_atr)  # устанавливаем атрибут

                    # блокируем старый код
                    # feat.SetField('type', 'poligon')  # устанавливаем атрибут
                    # name_atr = str(self.sotrD[n_1]) + '_' + str(self.sotrD[n_1 + 1]) #название пролета
                    # feat.SetField('name', name_atr)  # устанавливаем атрибут название пролета
                    # # копируем созданную геометрию(и прикреплённые к ней значения полей)

                    feat.SetField('len', self.dist_opor[n_1])  # устанавливаем атрибут длина пролета
                    feat.SetField('l', self.buf_oz[n_1][0])  # устанавливаем атрибут левый буфер
                    feat.SetField('r', self.buf_oz[n_1][1])  # устанавливаем атрибут правый буфер

                    #self.dist_opor = []  # список расстояний между опорами
                    #self.buf_oz = [] #список ОЗ [L,R]

                outFeat.SetFrom(feat)
                #print('Полигон')
                # print(feat)
                if layer_save is None:
                    print('Создание слоя не удалось!')
                # запись объекта в слой
                # сохранялка
                #print('Сохранялка')
                if layer_save.CreateFeature(outFeat) != 0:
                    print("Ошибка создания объекта в шейп файле.\n")
                n_1 += 1

        else: #если тип НЕ полигон....
            for geo in geometry:
                feat = ogr.Feature(layer_save.GetLayerDefn())
                feat.SetGeometry(geo) #присоединяем геометрию к OGRFeature
                feat.SetField('type', 'line')  # устанавливаем атрибут
                #print(feat)
                if layer_save is None:
                    print('Создание слоя проволилось!')
                # запись объекта в слой
                # сохранялка
                #print('Сохранялка')
                if layer_save.CreateFeature(feat) != 0:
                    print("Ошибка создания объекта в шейп файле.\n")


        # Открытие файла
        print(file_adr)
        vlayer = QgsVectorLayer(file_adr, name_d, "ogr")

        vlayer_id = vlayer.id()  # получение айдишника слоя
        # Загрузка файла в окно qgis
        # QgsProject.instance().addMapLayer(vlayer)

        return vlayer, vlayer_id, file_adr


    #экспорт в shp передаем списком объекты, окончание к названию, тип геометрии
    def shape_export(self, geometry, postfix, type_geom, nameF):
        #print(geometry)
        flag = True
        if nameF == 0:
            flag = False
            nameF = str(self.Poilayer).split("'")[1]  # имя исходного слоя
            name_oporyX2 = self.sotrD + self.sotrD
            smeschen = len(self.sotrD)
            # добавляем по два раза одно название для левого и правого пролета
            #print(name_oporyX2)
        name_d = nameF + postfix
        # указание драйвера
        driverName = "ESRI Shapefile"
        drv = ogr.GetDriverByName(driverName)
        if drv is None:
            print("%s Драйвер не поключился.\n" % driverName)
        # создание файла
        # создание новоо слоя
        file_adr = self.dlg.input_directory.text() + nameF + postfix +'.shp'
        ogrData_save = drv.CreateDataSource(file_adr)
        layerName = os.path.basename(self.dlg.input_directory.text() + nameF)
        #--проекция
        #получение проекции из слоя
        projPoi = str(self.Poilayer.crs()).split(' ')[1][:-1]  # текстовое значение проекции EPSG
        projPoi = int(projPoi.split(":")[1])
        #создание и указание проекции
        self.srs = osr.SpatialReference()
        self.srs.ImportFromEPSG(projPoi)
        try:
            layer_save = ogrData_save.CreateLayer(layerName, self.srs, geom_type=type_geom, options=['ENCODING=UTF-8'])
        except:
            infoString = 'Слой "%s" уже открыт в QGIS. Для перезаписи удалите этот слой из QGIS и запустите обработку повторно.' % (name_d)
            QMessageBox.information(self.dlg, "Ахтунг!", infoString)

        # копируем созданную геометрию(и прикреплённые к ней значения полей)
        # добавлем новое поле

        fieldDef = ogr.FieldDefn( "id", ogr.OFTString )
        fieldDef.SetWidth( 30 )
        if layer_save.CreateField ( fieldDef ) != 0:
            print("не могу создать поле %s" % fieldDef.GetNameRef())
        # fieldDef = ogr.FieldDefn("name", ogr.OFTString)
        # fieldDef.SetWidth( 30 )
        # if layer_save.CreateField ( fieldDef ) != 0:
        #     print("не могу создать поле %s" % fieldDef.GetNameRef())
        # создание полей для полигонов
        if flag == False:

            for name_field in ['name', 'len', 'l', 'r', 'side']:

                fieldDef = ogr.FieldDefn(name_field, ogr.OFTString)
                fieldDef.SetWidth(30)
                if layer_save.CreateField(fieldDef) != 0:
                    print("не могу создать поле %s" % fieldDef.GetNameRef())


            # непонятная поправлялка для полигонов
        if type_geom == ogr.wkbPolygon:#если тип - полигон, то обрабатывать таким макаром
            n_1 = 0
            side_atr = 'L'
            for ring in geometry:
                # Create polygon
                poly = ogr.Geometry(ogr.wkbPolygon)
                poly.AddGeometry(ring)
                # создаем OGRFeature (фигуру/объект)
                feat = ogr.Feature(layer_save.GetLayerDefn())
                feat.SetGeometry(poly)  # присоединяем геометрию к OGRFeature
                outFeat = ogr.Feature(layer_save.GetLayerDefn())

                if flag == False:
                    feat.SetField('type', 'poligon')  # устанавливаем атрибут
                    if n_1 == smeschen-1:
                        n_1 = 0
                        side_atr = 'R'

                    name_atr = str(name_oporyX2[n_1]) + '_' + str(name_oporyX2[n_1 + 1])  # название пролета
                    feat.SetField('name', name_atr)  # устанавливаем атрибут

                    # if n_1 < smeschen - 1:
                    #     side_atr = 'L'
                    # else:
                    #     side_atr = 'R'
                    feat.SetField('side', side_atr)  # устанавливаем атрибут

                    # блокируем старый код
                    # feat.SetField('type', 'poligon')  # устанавливаем атрибут
                    # name_atr = str(self.sotrD[n_1]) + '_' + str(self.sotrD[n_1 + 1]) #название пролета
                    # feat.SetField('name', name_atr)  # устанавливаем атрибут название пролета
                    # # копируем созданную геометрию(и прикреплённые к ней значения полей)

                    feat.SetField('len', self.dist_opor[n_1])  # устанавливаем атрибут длина пролета
                    feat.SetField('l', self.buf_oz[n_1][0])  # устанавливаем атрибут левый буфер
                    feat.SetField('r', self.buf_oz[n_1][1])  # устанавливаем атрибут правый буфер

                    #self.dist_opor = []  # список расстояний между опорами
                    #self.buf_oz = [] #список ОЗ [L,R]

                outFeat.SetFrom(feat)
                #print('Полигон')
                # print(feat)
                if layer_save is None:
                    print('Создание слоя не удалось!')
                # запись объекта в слой
                # сохранялка
                #print('Сохранялка')
                if layer_save.CreateFeature(outFeat) != 0:
                    print("Ошибка создания объекта в шейп файле.\n")
                n_1 += 1

        else: #если тип НЕ полигон....
            for geo in geometry:
                feat = ogr.Feature(layer_save.GetLayerDefn())
                feat.SetGeometry(geo) #присоединяем геометрию к OGRFeature
                feat.SetField('type', 'line')  # устанавливаем атрибут
                #print(feat)
                if layer_save is None:
                    print('Создание слоя проволилось!')
                # запись объекта в слой
                # сохранялка
                #print('Сохранялка')
                if layer_save.CreateFeature(feat) != 0:
                    print("Ошибка создания объекта в шейп файле.\n")

        # Открытие файла
        #print(file_adr)
        vlayer = QgsVectorLayer(file_adr, name_d, "ogr")
        if not vlayer:
            print("Layer failed to load!")
        # Загрузка файла в окно qgis
        QgsProject.instance().addMapLayer(vlayer)
        return file_adr

    def provoda(self): #создание линий проводов, полигонов по пролетам и общего полигона
        #значения точек
        n1, n2, n3 = [], [], [] # координаты получаемых точек
        atr1, atr2, atr3 = [], [], [] # траверсы получаемых точек
        xn = 1 # счетчик точек

        max_xn = len(self.sotrD) # максимальное значение счетчика
        lineL = ogr.Geometry(ogr.wkbLineString)  # создаем левую линию
        lineR = ogr.Geometry(ogr.wkbLineString) #cоздаем правую линию

        liPoL = [] # точки полигона слева
        liPoR = [] # точки полигона справа
        liPoC = []  # центральные точки
        numOp = '' # номер опоры
        self.dist_opor = [] #список расстояний между опорами
        self.buf_oz = [] # список расстояний буфера ОЗ слева и справа [L,R]

        n_buf = 1.45 #коэффициент увеличения буфера для разрезания
        #n_buf = 1

        for i in self.sotrD:  # перебор точек по возрастанию номеров
            print('---------------------------------------')
            print(i -1)
            #print(self.dic[i])  # получение значений по ключу
            #атрибуты

            atr2 = atr1
            atr1 = [float(self.dic[i][0][0]), float(self.dic[i][0][1])]
            #координаты точек, последовательная передача
            n3 = n2
            n2 = n1
            n1 = self.dic[i][1]
            liPoC.append(self.dic[i][1])

            #списки для заполнения атрибутов пролетов
            if n2 != []:
                ugoldeg, distan = self.ugol_degrees(n1, n2, [0,0])
                po_n = str(distan).find('.') + 3

                self.dist_opor.append( str(distan)[:po_n] )  # добавляем в список расстояние между точками
                self.buf_oz.append([atr2[0] + self.classNapr, atr2[1] + self.classNapr]) # добавляем в список буфера ОЗ

            #print(atr2)
            if n3 != []:
                #угол линий между точками с центром во второй точке,
                # расстояние между первой и второй точкой
                ugoldeg, distan = self.ugol_degrees(n1, n2, n3)

                #print('Угол:', ugoldeg)
                azim1 = self.azimuts(n1, n2)
                azim2 = self.azimuts(n3, n2)
                #print('Азимуты:', azim1, azim2)
                print('Разница азимутов:', azim1 - azim2)
                azrzn = azim1 - azim2
                #напрвление угла
                #print('значение условия:', ugoldeg + azrzn )
                #направление внутренней части угла




                if azrzn < -180 and n1[1] > n2[1]:
                    azrzn = azrzn * (-1)
                    #print('поправили', i-1)
                #print(ugoldeg - azrzn)
                if ugoldeg - azrzn < 1:
                    #print('Правый внутренний')
                    ugR = azim1 - (ugoldeg / 2)  # угол расположения правой точки
                    ugL = ugR + 180  # угол левой точки
                    ############################
                    # расстояние до точки, левое
                    # координаты точек линий ЛЭП
                    pointL = self.PointXY(n2, atr2[0], radians(ugL))
                    pointR = self.PointXY(n2, atr2[1], radians(ugR))
                    lineL.AddPoint(pointL[0], pointL[1])
                    lineR.AddPoint(pointR[0], pointR[1])

                    # координаты полигонов
                    poiPolyL = self.PointXY(n2, atr2[0] + self.classNapr * n_buf, radians(ugL))
                    poiPolyR = self.PointXY(n2, atr2[1] + self.classNapr * n_buf, radians(ugR))
                    liPoL.append(poiPolyL)
                    liPoR.append(poiPolyR)
                elif -1 < (ugoldeg + azrzn) < 1 or ugoldeg + abs(azrzn) > 359:
                    #print('Левый внутренний')
                    ugL = (ugoldeg / 2) + azim1  # угол расположения левой точки

                    #print(n1, n2, n3)
                    if n1[0] > n2[0] < n3[0]:  # поправлялка для углов с началом в четвертой четверти и концом в первой
                        #print('До Поправлялка:', ugL)
                        ugL = ugL + 90
                        #print('Поправлялка:', ugL)


                    ugR = ugL + 180  # угол правой точки
                    # расстояние до точки, левое
                    # координаты точек линий ЛЭП
                    pointL = self.PointXY(n2, atr2[0], radians(ugL))
                    pointR = self.PointXY(n2, atr2[1], radians(ugR))
                    lineL.AddPoint(pointL[0], pointL[1])
                    lineR.AddPoint(pointR[0], pointR[1])

                    # координаты полигонов
                    poiPolyL = self.PointXY(n2, atr2[0] + self.classNapr * n_buf, radians(ugL))
                    poiPolyR = self.PointXY(n2, atr2[1] + self.classNapr * n_buf, radians(ugR))
                    liPoL.append(poiPolyL)
                    liPoR.append(poiPolyR)

                    #############################

                else:
                    print('Эксклюзив')
            elif n2!= []: #обработка по первой точке
                numOp = i #номер первой опоры
                #print('first point')
                azim = self.azimuts(n1, n2)
                #углы линий и буфера
                #левая сторона
                ugL = azim + 90

                #правая сторона
                ugR = azim - 90
                # расстояние до точки, левое
                # координаты точек линий ЛЭП
                pointL = self.PointXY(n2, atr2[0], radians(ugL))
                pointR = self.PointXY(n2, atr2[1], radians(ugR))
                lineL.AddPoint(pointL[0], pointL[1])
                lineR.AddPoint(pointR[0], pointR[1])

                # координаты полигонов
                poiPolyL = self.PointXY(n2, atr2[0] + self.classNapr * n_buf, radians(ugL))
                poiPolyR = self.PointXY(n2, atr2[1] + self.classNapr * n_buf, radians(ugR))
                liPoL.append(poiPolyL)
                liPoR.append(poiPolyR)

            #print(numOp)
            xn += 1
            #print(i)

        #последняя точка
        azim = self.azimuts(n1, n2)
        # углы линий и буфера
        # левая сторона
        ugL = azim + 90

        # правая сторона
        ugR = azim - 90
        # расстояние до точки, левое
        # координаты точек линий ЛЭП
        pointL = self.PointXY(n1, atr1[0], radians(ugL))
        pointR = self.PointXY(n1, atr1[1], radians(ugR))
        lineL.AddPoint(pointL[0], pointL[1])
        lineR.AddPoint(pointR[0], pointR[1])
        # координаты полигонов
        poiPolyL = self.PointXY(n1, atr1[0] + self.classNapr * n_buf, radians(ugL))
        poiPolyR = self.PointXY(n1, atr1[1] + self.classNapr * n_buf, radians(ugR))
        liPoL.append(poiPolyL)
        liPoR.append(poiPolyR)

        #-----------------------------------------------------------------
        polygonBig = ogr.Geometry(ogr.wkbLinearRing)  # создаем общий полигон буфера
        for poi in liPoL: #вписываем точки левой границы
            polygonBig.AddPoint(poi[0], poi[1])
        for poi in reversed(liPoR): # проходим в обратную сторону и вписываем правую границу
            polygonBig.AddPoint(poi[0], poi[1])
        polygonBig.AddPoint(liPoL[0][0], liPoL[0][1]) #замыкаем полигон на первую точку
        #print(polygonBig)

        # self.shape_export([polygonBig], '_Big_poly', ogr.wkbPolygon, 0) #создание общего полигона
        #-----------------------------------------------------------------


        # создание полигонов пролетов
        # деление на лево и право!
        prolyoty = []
        for side in [liPoL, liPoR]: #перебор по количеству центральных точек
            xn1 = []
            for n in range(len(liPoC)): #перебор левой и правой стороны

                if xn1 != []: #если есть хоть одно значение
                    polygonMin = ogr.Geometry(ogr.wkbLinearRing)  # полигон пролетов
                    xn1.append(liPoC[n])
                    xn1.append(side[n])
                    #print(xn1)
                    for poi in xn1:  # вписываем точки границ
                        polygonMin.AddPoint(poi[0], poi[1])
                    polygonMin.AddPoint(xn1[0][0], xn1[0][1]) # замыкаем полигон на первую точку
                    prolyoty.append(polygonMin) #добавляем полигон в список

                    xn1 = [side[n], liPoC[n]] #перезаписываем переменную
                else: #вписываем значение первой точки
                    xn1 = [side[n], liPoC[n]]

        self.shape_export([lineR, lineL], '_lines', ogr.wkbLineString, 0)  # создание линий проводов

        lines_lay = qgis.utils.iface.activeLayer()
        lines_lay_id = QgsProcessingFeatureSourceDefinition(lines_lay.id())

        nameBP = str(self.Poilayer).split("'")[1]# Название большого полигона
        file_adrB = self.dlg.input_directory.text() + nameBP + '_Big_poly.shp'
        print(file_adrB)

        #  Построение буфера вокруг линий проводов
        processing.run("native:buffer",
                       {'INPUT': lines_lay_id,
                        'DISTANCE': self.classNapr,
                        'SEGMENTS': 5,
                        'END_CAP_STYLE': 1,
                        'JOIN_STYLE': 0,
                        'MITER_LIMIT': 2,
                        'DISSOLVE': True,
                        'OUTPUT': file_adrB})#['OUTPUT']

        vlayer = QgsVectorLayer(file_adrB, nameBP+'_Big_poly', "ogr")
        if not vlayer:
            print("Layer failed to load!")
        buf_id = vlayer.id()
        QgsProject.instance().addMapLayer(vlayer)  # добавим на карту


        self.layer_seg_temp, self.layer_seg_temp_id, adres_rem = self.export_vlayer(prolyoty, '__segbig', ogr.wkbPolygon, 0)  # создание полигонов по пролетам
        # layer_segm = qgis.utils.iface.activeLayer()
        print(self.layer_seg_temp_id)
        QgsProject.instance().addMapLayer(self.layer_seg_temp) #



        lay_s = QgsProcessingFeatureSourceDefinition(self.layer_seg_temp_id)#слой сегментов
        lay_b = QgsProcessingFeatureSourceDefinition( buf_id )
        adr_segm = self.dlg.input_directory.text() + nameBP + '_segment.shp'
        print(adr_segm)
        # обработка пересечения с получением слоя сегментов.
        processing.run("native:intersection",
                       {'INPUT': lay_s,
                        'OVERLAY': lay_b,
                        'OUTPUT': adr_segm})

        vlayer_seg = QgsVectorLayer(adr_segm, nameBP+'_segment', "ogr")
        QgsProject.instance().addMapLayer(vlayer_seg)  # добавим на карту
        QgsProject.instance().removeMapLayer(self.layer_seg_temp_id)# удаляем лишний слой


        #генерация отчета

    # рассчеты расстояния от точки до линии
    def lenPoiToLine(self, nom_prol, poiNXY, featAtXY): # № пролета, список точек с координатами, список объектов с атрибутами и коорлинатами
        minL, minR = 10000, 10000

        nom = [int(nom_prol.split('_')[0]), int(nom_prol.split('_')[1])] #список из двух номеров опор

        #print('Nomera opor:', nom)
        #print('Tochki opor:', poiNXY)
        #print('Объекты:', featAtXY)
        points2 = []
        for point_1 in poiNXY: #перебор точек
            if nom[0] == point_1[0] or nom[1] == point_1[0]:
                # print('Точка:', point_1)
                points2.append(point_1[-2:])

        p1 , p2 = points2[0], points2[1] # координаты точек отрезка

        for feat_1 in featAtXY: #перебор объектов
            if nom_prol == feat_1[0]:
                # print('Полигон: ', feat_1[0])
                # print('Геометрия', feat_1)
                np = 0
                minX = 10000
                for po in feat_1[-1]: #перебираем точки объекта
                    np += 1
                    # print("Номер точки:", np)
                    # print(po)
                    ugolA, len1 = self.ugol_degrees(po, p1, p2) #считаем угол и расстояния
                    ugolB, len2 = self.ugol_degrees(po, p2, p1) #считаем угол и расстояния
                    # print('Угол А, длина, Угол Б, длина:')
                    # print(ugolA, len1, ugolB, len2)

                    if ugolA >= 90 or ugolB >= 90: #если один из углов больше или равер 90 град
                        minH = min([len1, len2]) # выбираем минимальное расстояние до одной из точек отрезка
                        # print('За пределами отрезка. Расстояние:', minH)
                    else:
                        minH = len1 * sin(radians(ugolA)) # считаем длину перпендикуляра к отрезку
                        # print('sin:', ugolA, sin(radians(ugolA)))
                        # print('В пределах отрезка. Расстояние:', minH)
                    if minX > minH:
                        minX = minH
                #         print('Уменьшаем:', minX, minH)

                if feat_1[1] == 'L' and minL > minX:
                    minL = minX
                elif feat_1[1] == 'R' and minR > minX:
                    minR = minX
        minR = round(minR, 2)
        minL = round(minL, 2)

        if minR == 10000:
            minR = 'Нет'
        if minL == 10000:
            minL = 'Нет'

        minR = str(minR)
        minL = str(minL)
        # print('export:', minL, minR)
        return minL, minR



    def report(self):
        #получаем id слоев
        layer_segment = self.dlg.MapLay_CB.currentLayer()
        layer_2 = self.dlg.MapLay_CB_2.currentLayer()#слой леса
        layer_3 = self.dlg.MapLay_CB_3.currentLayer()#слой домов
        # чекбоксы
        checF = self.dlg.checkUp_f.isChecked() # подключить лес
        checB = self.dlg.checkUp_b.isChecked() # подключить дома
        print(checF, checB)
        #получаем адрес папки и название файла
        dir_adres = self.dlg.input_directory_2.text()
        name_file = self.dlg.name_file.text()
        list_for_del = []
        #создаем список атрибутов слоя пролетов
        iter = layer_segment.getFeatures(QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry))
        attrs_seg = [] #список атрибутов
        for feature in iter:  # перебор атрибутов каждого объекта
            attrs_seg.append(feature.attributes())

        # указываем входные файлы по ID и адрес для сохранения выходного
        inputF = QgsProcessingFeatureSourceDefinition(layer_segment.id())
        overlayF = QgsProcessingFeatureSourceDefinition(layer_2.id())
        overBuild = QgsProcessingFeatureSourceDefinition(layer_3.id())

######################-----------------------------
        #Получаем атрибуты и координаты опор
        # vectorComboBox_2x(), fxy.y()])  # добавляем в список координаты
        ###################
        numOp_2 = self.dlg.categoryComboBox_2.currentIndex()  # получаем id поля с номерами опор
        # print(self.Poilayer_2.fields())
        itera_2 = self.Poilayer.getFeatures()  # QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry))
        numbList_2 = []  # список номеров опор
        for feature in itera_2:  # перебор атрибутов каждой точки
            attrs = feature.attributes()
            # если оба атрибута не имеют пустых полей...
            if attrs[numOp_2] != None:
                f = feature.geometry().asPoint()  # координаты из геометрии
                # print(f, [f.x(), f.y()])
                numbList_2.append([attrs[numOp_2], f.x(), f.y()])  # добавляем в список номера опор и x,y координаты

            else:
                print('Есть пустые поля!!')
                break
####--------------------------------------------------------

        if len(name_file) != 0 and len(dir_adres) != 0:
            outputF = dir_adres + '/' + name_file + '.shp'
            print(outputF)
            #type_report = self.dlg.typeReport.currentIndex()#тип отчета 0 - лес, 1 - дома

            if checF is True:
                print('Forest report')
                # объединение объектов по Class_id

                uni_rezult = processing.run("native:dissolve",
                                            {'INPUT': overlayF,
                                             'FIELD': ['class_id'],
                                             'OUTPUT': 'TEMPORARY_OUTPUT'})['OUTPUT']
                uni_rezult_id = uni_rezult.id()
                print('объеденино')
                #print(uni_rezult_id)
                QgsProject.instance().addMapLayer(uni_rezult)#добавим на карту

                ovL = QgsProcessingFeatureSourceDefinition(uni_rezult_id)

                # обработка пересечения во временном файле
                temp_layer = processing.run("native:intersection", {'INPUT': inputF,
                                                                    'OVERLAY': ovL,
                                                                    'OUTPUT':'TEMPORARY_OUTPUT'})
                print('Пересечено')
                QgsProject.instance().removeMapLayer(uni_rezult_id)  # удаляем временный слой

                temp_data = temp_layer['OUTPUT']
                QgsProject.instance().addMapLayer(temp_data) #добавляем временный слой на карту

                #считаем разрезанные площади и сохраняем в шейп
                in_area = QgsProcessingFeatureSourceDefinition(temp_data.id())
                processing.run("qgis:exportaddgeometrycolumns", {'INPUT': in_area,
                                                                 'CALC_METHOD': 2,
                                                                 'OUTPUT':outputF})
                print('Посчитаны площади')
                vlayer = QgsVectorLayer(outputF, name_file, "ogr")
                # Загрузка файла в окно qgis
                QgsProject.instance().addMapLayer(vlayer)
                QgsProject.instance().removeMapLayer(temp_data.id())  # удаляем временный слой

                # получаем список атрибутов слоя леса разбитого по пролетам
                iter_2 = vlayer.getFeatures()#QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry))
                attrs_lay= []  # словарь атрибутов
                for feat2 in iter_2:  # перебор атрибутов каждого объекта
                    # получение геометри и присоединение к атрибутам
                    # fnf = str(feat2.geometry()).find(')')
                    # stf = str(feat2.geometry()).rfind('(') + 1
                    #print('Geometriya:', feat2.geometry().asMultiPolygon())
                    #print('Segm1', feat2.geometry().asMultiPolygon()[0])

                    # получение и добавление в список всех пар коорлинат объекта
                    coord = []
                    for x in feat2.geometry().asMultiPolygon():
                        # print('one:', x[0])
                        for c in x[0]:
                            # print(c.x(), c.y())
                            coord.append([c.x(), c.y()])
                    #print('coord:', coord)

                    # ['name', 'side', 'class_id','area']:
                    attrs_lay.append([feat2['name'], feat2['side'], feat2['class_id'], feat2['area'], coord])
                #print('слой леса: ', attrs_lay)

                #считаем площадь половинок пролетов
                temp_seg_area = processing.run("qgis:exportaddgeometrycolumns",
                                               {'INPUT': inputF,
                                                'CALC_METHOD': 0,
                                                'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']
                #temp_seg_ar_id = temp_seg_area.id()
                #QgsProject.instance().addMapLayer(temp_seg_area)

                # получаем список атрибутов пролетов
                iter_seg = temp_seg_area.getFeatures(QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry))
                attrs_lay_seg= []  # список атрибутов
                for feat3 in iter_seg:  # перебор атрибутов каждого объекта
                    attrs_lay_seg.append([feat3['name'], feat3['len'], feat3['l'], feat3['r'], feat3['side'], feat3['area']])
                #print('атрибуты пролетов: ', attrs_lay_seg)
                #Складываем значения по атрибутам

                table_exp = [] #таблица заполнения для экспорта
                list_seg = [] # список обработаных пролетов

                for seg in attrs_lay_seg: #перебираем все половинки пролетов

                    if seg[0] in list_seg: #если пролет с таким именем уже обрабатывался, то пропускать его.
                        continue
                    area_prol = 0.0  # площадь пролета
                    for se_t in attrs_lay_seg: # перебираем все пролеты и сравниваем
                        if seg[0] == se_t[0]: #если совпадают названия прибавляем площади
                            area_prol += float(se_t[5])

                    #считаем площади по высотам в каждой половине пролета
                    name04_l, name04_r = 0.0, 0.0
                    name10_l, name10_r = 0.0, 0.0
                    name99_l, name99_r = 0.0, 0.0
                    for forest in attrs_lay: #перебираем объекты леса
                        if seg[0] == forest[0]:  # если совпадают названия
                            if forest[2] == '00m-04m':
                                if forest[1] == 'L':
                                    name04_l += forest[3]
                                elif forest[1] == 'R':
                                    name04_r += forest[3]
                            elif forest[2] == '04m-10m':
                                if forest[1] == 'L':
                                    name10_l += forest[3]
                                elif forest[1] == 'R':
                                    name10_r += forest[3]
                            else:
                                if forest[1] == 'L':
                                    name99_l += forest[3]
                                elif forest[1] == 'R':
                                    name99_r += forest[3]

                    list_seg.append(seg[0])

                    table_exp.append([seg[0], seg[1], seg[2], seg[3], area_prol, name04_l, name04_r, name10_l, name10_r, name99_l, name99_r])
                # print('экспортная таблица', table_exp)

                #print(len(attrs_lay_seg))
                #print(attrs_lay_seg)
                csv_text = '№№ опор, ограничивающих пролет;Длина пролета L, м;Ширина охранной зоны от оси ВЛ, м;;;Площадь кустарника в просеке на длине пролета (высота от 1 до 4 м);;Площадь поросли в просеке на длине пролета (высота от 4 до 10 м);;Площадь насаждений высотой свыше 10 м в просеке на длине пролета;;Горизонтальное расстояние до насаждений;;Общая площадь, м2;;Примечание' \
                           '\n;;;;;слева, м2;справа, м2;слева, м2;справа, м2;слева, м2;справа, м2;;;;;' \
                           '\n;;слева (D1);справа (D2);общая (D);от 1 до 4 м;от 1 до 4 м;от 4 до 10 м;от 4 до 10 м;от 10 м и выше;от 10 м и выше;слева, м;справа, м;охр. зоны в пролете ВЛ;растительности в пролете на ширине просеки выше 4 м;' \
                           '\n1;2;3;4;5;6;7;8;9;10;11;12;13;14;15;16\n'

                #iter_art = attrs_lay_seg.keys() #получаем список всех названий опор

                for i in table_exp: #перебор всех пролетов

                    minL, minR = self.lenPoiToLine(i[0], numbList_2, attrs_lay) # рассчет расстояния до линии
                    #minL, minR = '-', '-'

                    #print(attrs_lay.get(i))
                    # значения колонок в отчете
                    kold1 = i[0] #номер пролета (по номерам опор)
                    kold2 = str(round(float(i[1]), 2)) #длина пролета
                    kold3 = round(float(i[2]), 2) #ширина левая
                    kold4 = round(float(i[3]), 2) #ширина правая

                    kold5 = str(kold3 + kold4) #общая ширина
                    kold3 = str(kold3) #преобразование в строку
                    kold4 = str(kold4) #преобразование в строку

                    # площади по высоте, лево и право.
                    kold6 = str(round(float(i[5]), 2))
                    kold7 = str(round(float(i[6]), 2))

                    kold8 = str(round(float(i[7]), 2))
                    kold9 = str(round(float(i[8]), 2))

                    kold10 = str(round(float(i[9]), 2))
                    kold11 = str(round(float(i[10]), 2))

                    kold12 = minL
                    kold13 = minR

                    kold14 = str(round(float(i[4]), 2)) # площадь пролета
                    kold15= str(round(float(i[7]) + float(i[8]) + float(i[9]) + float(i[10]), 2)) #площадь растительности в пролете выше 4м

                    #составляем строку
                    strokad = kold1 + ';' + kold2 + ';' +  kold3 + ';' + kold4 + ';' + kold5 + ';' + kold6 + ';' + kold7 + ';' + kold8 + ';' + kold9 + ';' + kold10 + ';' + kold11 + ';' + kold12 + ';' + kold13 + ';' + kold14 + ';' +  kold15 + ';\n'
                    #добавляем строку к тексту.
                    csv_text += strokad

                file_path = dir_adres +'/'+ name_file + '_forest.csv'#адрес сохранения отчета
                with open(file_path, 'w') as file_csv:
                    file_csv.write(csv_text)

                ######--------- Обработка лейаута
                # адрес файла лейаута
                adr_qpt = self.plugin_dir + '/layout_plugin.qpt'
                #print(adr_qpt)
                with open(adr_qpt, 'r') as file_qpt:  #открываем и читаем файл
                    qpt_text = file_qpt.read()

                    qpt_text = qpt_text.replace('Report power', name_file) # название лейаута
                    qpt_text = qpt_text.replace('SEGMENT_LAYER_ID', layer_segment.id()) # указываем ID слой сегметнов (пролетов)
                    qpt_text = qpt_text.replace('RESULT_LAYER_ID', vlayer.id()) # указываем ID слой обработки разрезаный на сегменты

                    path_lay = layer_segment.dataProvider().dataSourceUri().split('|')[0] #адрес слоя

                    qpt_text = qpt_text.replace('SEGMENT_LAYER_ADRES', path_lay)
                    qpt_text = qpt_text.replace('SEGMENT_LAYER_NAME', layer_segment.name())

                temp_qpt = self.plugin_dir + '/' + name_file + '.qpt' #адрес временного файла
                with open(temp_qpt, 'w') as file_qpt:
                    file_qpt.write(qpt_text)  # записываем обратно в файл

                #загрузка лейаута
                project = QgsProject.instance()
                composition = QgsPrintLayout(project)
                document = QDomDocument()

                template_file = open(temp_qpt)
                template_content = template_file.read()
                template_file.close()
                document.setContent(template_content)
                # load layout from template and add to Layout Manager
                composition.loadFromTemplate(document, QgsReadWriteContext())
                project.layoutManager().addLayout(composition)
                os.remove(self.plugin_dir + '/' + name_file + '.qpt')#удаляем временный файл лейаута

                # создать и показать сообщение//create a string and show it
                infoString = "Создан атлас отчета!\n" \
                             "Перейдите в меню (Проекты > Макеты > %s) и завершите экспорт атласа через меню (Атлас > Export Atlas as images...) " % (name_file)
                QMessageBox.information(self.dlg, "Report", infoString)

            if checB is True:
                print('Build report')

                csv_text = '№№ опор, ограничивающих пролет;Длина пролета L, м;Ширина охранной зоны от оси ВЛ, м;;Количество зданий, сооружений;Расстояние от начальной опоры пролета, м;Расстояние по горизонтали от крайнего провода, м\n' \
                           ';;слева (D1);справа (D2);;;\n' \
                           '1;2;3;4;5;6;7\n'

                # обработка пересечения во временном файле
                temp_layer = processing.run("native:intersection", {'INPUT': inputF,
                                                                    'OVERLAY': overBuild,
                                                                    'OUTPUT': 'TEMPORARY_OUTPUT'})['OUTPUT']

                # получаем таблицу атрибутов порезаного на пролеты слоя домов
                iter_seg = temp_layer.getFeatures() #QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry))
                attrs_lay = []  # список атрибутов
                for feature2 in iter_seg:  # перебор атрибутов каждого объекта
                    ab = feature2.attributes()

                    # получение и добавление в список всех пар коорлинат объекта
                    coord = []
                    for x in feature2.geometry().asMultiPolygon():
                        # print('one:', x[0])
                        for c in x[0]:
                            # print(c.x(), c.y())
                            coord.append([c.x(), c.y()])

                    #ab.append(coord)  # получение геометрии
                    #print(attrs_lay)
                    print('Слой:', ab[5])
                    attrs_lay.append([ab[1], ab[5], coord])

                # получаем таблицу атрибутов слоя пролетов
                iter_prol = layer_segment.getFeatures(QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry))
                attrs_lay_prol = {}  # словарь атрибутов
                for feature2 in iter_prol:  # перебор атрибутов каждого объекта
                    abc = feature2.attributes()
                    attrs_lay_prol[abc[1]] = abc[2:]
                iter_art = attrs_lay_prol.keys()  # получаем список всех названий опор

                for i in iter_art:  # перебор всех пролетов

                    minL, minR = self.lenPoiToLine(i, numbList_2, attrs_lay)  # рассчет расстояния до линии

                    if minL != 'Нет':
                        minL = float(minL)
                    if minR != 'Нет':
                        minR = float(minR)

                    if minL != 'Нет' and minR != 'Нет':
                        minim = str(min([float(minL), float(minR)]))
                    elif minL == 'Нет' and minR != 'Нет':
                        minim = str(minR)
                    elif minL != 'Нет' and minR == 'Нет':
                        minim = str(minL)
                    else:
                        minim = 'Нет'


                    #print('перебор пролета:', i)
                    nom_point = int(i.split('_')[0])# получаем номер первой опоры в пролете
                    #print('nom_point:', nom_point)

                    seg = attrs_lay_prol[i]

                    #значения колонок в отчете
                    kol1 = i
                    kol2 = str(round(float(seg[0]), 2))
                    kol3 = str(round(float(seg[1]), 2))
                    kol4 = str(round(float(seg[2]), 2))

                    #подсчет зданий в пролете
                    n = 0
                    #print(seg)

                    for poi in numbList_2:
                        if nom_point == poi[0]:
                            #print(poi)
                            break
                    # print(poi)

                    min_dist = 10000
                    for xi in attrs_lay: #пербор списка объектов в пролетах
                        #print('перебор:', xi)
                        if xi[0] == i:
                            n += 1
                            #print('по условию', xi[1])
                            for p_o_r in xi[-1]: #перебор точек каждого дома
                                #print('test p_o_r', p_o_r)
                                x = float(p_o_r[0])
                                y = float(p_o_r[1])
                                # print(x, y)
                                # print(poi[1:])
                                ugoldeg_no, dis= self.ugol_degrees(poi[1:], [x,y], [0, 0]) # меряем расстояние (в торая переменная)

                                if dis < min_dist:# если расстояние от опоры до точки меньше чем уже имебщееся
                                    min_dist = dis # заменяем на меньшее
                                    print('Новый минимум!!', min_dist)

                    if min_dist == 10000: #если измерений небыло -то значение Нет
                        min_dist = 'Нет'
                    else:
                        min_dist = str(round(min_dist, 2))

                    kol5 = str(n)
                    kol6 = min_dist
                    kol7 = minim
                    stroka = kol1 + ';' + kol2 + ';' + kol3 + ';' + kol4 + ';' + kol5 + ';' + kol6 +  ';' + kol7 + '\n'
                    csv_text += stroka

                csv_text = csv_text

                file_path = dir_adres + '/' + name_file + '_build.csv'  # адрес сохранения отчета
                with open(file_path, 'w') as file_csv:
                    file_csv.write(csv_text)

                if checF is False: #если не формируется отчет и атлас по лесу, то создается по домам
                    ######--------- Обработка лейаута
                    # адрес файла лейаута
                    adr_qpt = self.plugin_dir + '/layout_build.qpt'
                    # print(adr_qpt)
                    with open(adr_qpt, 'r') as file_qpt:  # открываем и читаем файл
                        qpt_text = file_qpt.read()

                        qpt_text = qpt_text.replace('Report power', name_file)  # название лейаута
                        qpt_text = qpt_text.replace('SEGMENT_LAYER_ID',
                                                    layer_segment.id())  # указываем ID слой сегметнов (пролетов)
                        #qpt_text = qpt_text.replace('RESULT_LAYER_ID', vlayer.id())  # указываем ID слой обработки разрезаный на сегменты

                        path_lay = layer_segment.dataProvider().dataSourceUri().split('|')[0]  # адрес слоя

                        qpt_text = qpt_text.replace('SEGMENT_LAYER_ADRES', path_lay)
                        qpt_text = qpt_text.replace('SEGMENT_LAYER_NAME', layer_segment.name())

                    temp_qpt = self.plugin_dir + '/' + name_file + '.qpt'  # адрес временного файла
                    with open(temp_qpt, 'w') as file_qpt:
                        file_qpt.write(qpt_text)  # записываем обратно в файл

                    # загрузка лейаута
                    project = QgsProject.instance()
                    composition = QgsPrintLayout(project)
                    document = QDomDocument()

                    template_file = open(temp_qpt)
                    template_content = template_file.read()
                    template_file.close()
                    document.setContent(template_content)
                    # load layout from template and add to Layout Manager
                    composition.loadFromTemplate(document, QgsReadWriteContext())
                    project.layoutManager().addLayout(composition)
                    os.remove(self.plugin_dir + '/' + name_file + '.qpt')  # удаляем временный файл лейаута

                    # создать и показать сообщение//create a string and show it
                    infoString = "Создан атлас отчета!\n" \
                                 "Перейдите в меню (Проекты > Макеты > %s) и завершите экспорт атласа через меню (Атлас > Export Atlas as images...) " % (name_file)
                    QMessageBox.information(self.dlg, "Report", infoString)

        else:
            print('Сначала укажите папку для сохранение и название отчета!')


    #расчет азимута между точками на плоскости
    def azimuts(self, n1, n2):
        # измеряем расстояние между точками
        distan = sqrt((n2[0] - n1[0]) ** 2 + (n2[1] - n1[1]) ** 2)
        # print('Расстояние между точками:', distan)
        # рассчитываем азимут (от направления на восток, против часовой стрелки)
        azimut = asin(fabs(n1[1] - n2[1]) / distan)
        # теперь в градусы
        azimut_deg = degrees(azimut)
        az = azimut_deg
        if n1[0] >= n2[0]:
            if n1[1] < n2[1]:
                az = 360 - azimut_deg
        elif n1[0] <= n2[0]:
            if n1[1] <= n2[1]:
                az = 180 + azimut_deg
            elif n1[1] > n2[1]:
                az = 90 - azimut_deg + 90
        #print('Azimuth:', az)
        return az

    def ugol_degrees(self, n0, n1, n2):
        # n1 - будет меряться этот угол
        #измерение расстояния между точками
        a12 = sqrt((n2[0] - n1[0]) ** 2 + (n2[1] - n1[1]) ** 2)
        a10 = sqrt((n0[0] - n1[0]) ** 2 + (n0[1] - n1[1]) ** 2)
        a02 = sqrt((n2[0] - n0[0]) ** 2 + (n2[1] - n0[1]) ** 2)

        # обработка исключений неправильных углов.
        # если ошибка - переход на след. объект.
        try:
            ugol_rad = acos((a12 ** 2 + a10 ** 2 - a02 ** 2) / (2 * a12 * a10))
            #print('Радианы', ugol_rad)
        except:
            print('Ощибка. Исходные показатели: ', a12, a10, a02)
            print('Координаты:', n0, n1, n2)
            ugol_rad = 0
        #    return [181, a10, a12]
        # переведём в градусы
        ugol_deg = degrees(ugol_rad)
        return [ugol_deg, a10]
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


    #-----------------------------
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
        if len(NewLayName) > 0: #если имя не пустое - начинаем загрузку
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
            infoString = "Сначала укажите имя для обработки, выберите полигональный слой и тип обработки"
            QMessageBox.information(self.dlg, "About", infoString)

        self.button_connect()

    #предпросмотр снимков
    def sart_view(self):
        ind_preview = self.dlg.comBox_satelit_mon.currentIndex()#получаем индекс выбора в комбобоксе

        if ind_preview == 0: #Google
            urlWithParams = 'crs=EPSG:3857&format&type=xyz&url=https://mt1.google.com/vt/lyrs%3Ds%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=19&zmin=0'
            rlayer = QgsRasterLayer(urlWithParams, 'Google Satelite (0-19)', 'wms')
            QgsProject.instance().addMapLayer(rlayer)

        elif ind_preview == 1: #Yandex
            urlWithParams = 'crs=EPSG:3395&format&type=xyz&url=http://sat04.maps.yandex.net/tiles?l%3Dsat%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=19&zmin=0'
            rlayer = QgsRasterLayer(urlWithParams, 'Yandex Satelite (0-19)', 'wms')
            QgsProject.instance().addMapLayer(rlayer)
        elif ind_preview == 2: #User input
            # line_server_2 - поле урл

            url = self.dlg.line_server_2.text()# получаем url из настроек

            #замена символов в адресе для корректной работы
            url = url.replace('=', '%3D')
            url = url.replace('&', '%26')
            url = '&url=' + url

            min_max = "&zmax=13&zmin=0"
            typeXYZ = 'type=xyz'
            login = '&username=' +  self.dlg.line_login_3.text()
            password = '&password=' + self.dlg.mLinePassword_3.text()
            urlWithParams = typeXYZ + url + min_max + login + password
            rlayer = QgsRasterLayer(urlWithParams, 'Cервис от пользователя (0-13)', 'wms')
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
        os.remove(file_temp)  # удаление временного файла
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

        # заполняем комбобокс доступными воркфлоудифинишинсами
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

        for i in reversed(range(self.kol_tab)):
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
    # noinspection PyMethodMayBeStatic

    #Перепроецирование
    def projection_transform(self, x, y, num_crs, num_crsNew):
        crs = QgsCoordinateReferenceSystem(num_crs) #исходная проекция
        crsNew = QgsCoordinateReferenceSystem(num_crsNew) #целевая проекция
        tform = QgsCordinateTransform(crs, crsNew, QgsProject.instance())
        pointOut = tform.trasform(QgsPointXY(x, y))

        print(pointOut)
        return pointOut

    def tr(self, message):

        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('Inspector_energy', message)
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
            text=self.tr(u'Инспектор ЛЭП'),
            callback=self.run,
            parent=self.iface.mainWindow())
    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.tr(u'&Energy Inspector'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar
    def run_buffer(self, geom, distance, segments):
        if geom is not None:
            buf = geom.buffer(distance, segments)
            return buf
        else:
            return None
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
                                "%s_energy_geoalert" % layer_name, "memory")
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