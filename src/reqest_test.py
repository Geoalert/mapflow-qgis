
import requests
import io

headers = {
    'authorization': 'Basic c25lZ3VyYXdAZ21haWwuY29tOlh6MTIzNDU2',
    'content-type': 'multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW',
}

print(open('C:/test/test.tif', 'rb'))

files = {'file': ('test.tif', open('C:/test/test.tif', 'rb'))}


ip = 'http://178.57.73.151:8050'
#ip = 'http://localhost:8001'
r = requests.post(ip+'/rest/rasters', headers=headers, files=files)
print('Ответ сервера:')
print(r.text)
print('Ответ закончился')



# ip = 'http://178.57.73.151:8050'
# headers1 = {'Authorization': 'Basic c25lZ3VyYXdAZ21haWwuY29tOlh6MTIzNDU2', 'content-type': 'application/json'}
#
# URL_f ="http://178.57.73.151:8050/rest/processings" #51eb8f48-d461-4103-9d23-a1e8977deee6"
# print('этап1')
# r = requests.get(url=URL_f, headers=headers1)
#             # получаем ответ
#print(r.text)

#
# attrs_lay = {'47_48': ['236.63', '22', '21', '10m-99m', 142232999, 4229.080078125], '31_32': ['213.35', '22', '21', '10m-99m', 142232999, 74.0888671875], '46_47': ['234.51', '22', '21', '10m-99m', 142232999, 44.434326171875], '10_11': ['179.38', '22', '21', '10m-99m', 142232999, 254.743896484375], '13_14': ['165.20', '22', '21', '10m-99m', 142232999, 5.17138671875], '32_33': ['230.68', '22', '21', '04m-10m', 142232949, 10.423583984375], '28_29': ['232.35', '22', '21', '10m-99m', 142232999, 320.684326171875], '14_15': ['166.77', '22', '21', '10m-99m', 142232999, 144.071533203125], '29_30': ['229.01', '22', '21', '04m-10m', 142232949, 0.0078125], '44_45': ['232.34', '22', '21', '10m-99m', 142232999, 0.003662109375], '3_4': ['258.85', '22', '21', '04m-10m', 142232949, 3.32470703125], '20_21': ['174.18', '22', '21', '10m-99m', 142232999, 15.923095703125], '30_31': ['238.60', '22', '21', '10m-99m', 142232999, 7.876220703125], '7_8': ['292.60', '22', '21', '10m-99m', 142232999, 197.39501953125], '33_34': ['230.68', '22', '21', '04m-10m', 142232949, 1.423828125], '17_18': ['161.63', '22', '21', '10m-99m', 142232999, 497.489501953125], '49_50': ['242.78', '22', '21', '10m-99m', 142232999, 2001.47021484375], '42_43': ['237.67', '22', '21', '10m-99m', 142232999, 97.270751953125], '18_19': ['218.95', '22', '21', '10m-99m', 142232999, 59.719482421875], '48_49': ['236.55', '22', '21', '10m-99m', 142232999, 2931.23095703125], '19_20': ['160.87', '22', '21', '10m-99m', 142232999, 142.548095703125], '43_44': ['232.94', '22', '21', '10m-99m', 142232999, 209.67138671875], '27_28': ['234.26', '22', '21', '04m-10m', 142232949, 5.86962890625], '51_52': ['232.77', '22', '21', '10m-99m', 142232999, 4452.263671875]}
#
# attrs_lay_seg = {'1_2': ['24.43', '22', '21', 861.2578125, 137.51644340874773], '2_3': ['71.88', '22', '21', 2125.086181640625, 228.34789789357868], '3_4': ['258.85', '22', '21', 9482.0048828125, 602.994926639306], '4_5': ['137.57', '22', '21', 5872.686767578125, 361.0449901895862], '5_6': ['153.88', '22', '21', 6614.1689453125, 393.8179009779503], '6_7': ['236.58', '22', '21', 10156.537109375, 559.254451545658], '7_8': ['292.60', '22', '21', 12386.292724609375, 671.5282486195256], '8_9': ['121.90', '22', '21', 5170.527587890625, 330.01913146921686], '9_10': ['360.01', '22', '21', 9424.134521484375, 807.7604654246178], '10_11': ['179.38', '22', '21', 7122.62548828125, 444.02103279715914], '11_12': ['203.75', '22', '21', 6916.748046875, 494.2250972350497], '12_13': ['190.07', '22', '21', 7986.212158203125, 465.8558435383233], '13_14': ['165.20', '22', '21', 6931.4931640625, 416.11573057397976], '14_15': ['166.77', '22', '21', 6796.1552734375, 418.92593359485716], '15_16': ['183.54', '22', '21', 6835.390380859375, 453.44078679576455], '16_17': ['198.33', '22', '21', 7623.06787109375, 483.4157883490905], '17_18': ['161.63', '22', '21', 6051.703369140625, 410.12914587180495], '18_19': ['218.95', '22', '21', 8002.866455078125, 524.8408389357709], '19_20': ['160.87', '22', '21', 6259.933349609375, 407.26780152159233], '20_21': ['174.18', '22', '21', 6294.355712890625, 433.3046996815084], '21_22': ['213.81', '22', '21', 8597.22900390625, 513.1710810454828], '22_23': ['238.83', '22', '21', 10269.73828125, 563.6624379170472], '23_24': ['206.15', '22', '21', 8864.768310546875, 498.31499366122364], '24_25': ['183.68', '22', '21', 7898.581298828125, 453.37590008625403], '25_26': ['218.58', '22', '21', 9222.122802734375, 522.9118903742857], '26_27': ['237.18', '22', '21', 10007.19580078125, 560.1049913784483], '27_28': ['234.26', '22', '21', 10073.634765625, 554.5450490425774], '28_29': ['232.35', '22', '21', 9991.378173828125, 550.715941118239], '29_30': ['229.01', '22', '21', 9847.502685546875, 544.023690117759], '30_31': ['238.60', '22', '21', 10260.241455078125, 563.2250553856959], '31_32': ['213.35', '22', '21', 9174.166748046875, 512.7059007665539], '32_33': ['230.68', '22', '21', 9919.2021484375, 547.3587087419168], '33_34': ['230.68', '22', '21', 9919.2236328125, 547.3597660673222], '34_35': ['235.25', '22', '21', 10115.953125, 556.5098201482205], '35_36': ['237.44', '22', '21', 10209.912841796875, 560.879695305864], '36_37': ['225.96', '22', '21', 9716.52490234375, 537.9314884839464], '37_38': ['232.56', '22', '21', 10000.092041015625, 551.120690888815], '38_39': ['229.65', '22', '21', 9875.306640625, 545.3188613736379], '39_40': ['240.04', '22', '21', 10321.87646484375, 566.0882130726308], '40_41': ['224.66', '22', '21', 9660.671142578125, 535.3341692497635], '41_42': ['235.04', '22', '21', 10107.133056640625, 556.0992135407113], '42_43': ['237.67', '22', '21', 10220.192138671875, 561.3577747315378], '43_44': ['232.94', '22', '21', 10016.40625, 551.8797748706066], '44_45': ['232.34', '22', '21', 9990.705810546875, 550.6851524375572], '45_46': ['233.09', '22', '21', 10023.27490234375, 552.198916492793], '46_47': ['234.51', '22', '21', 10084.090576171875, 555.0274751778128], '47_48': ['236.63', '22', '21', 10175.279052734375, 559.2688135173197], '48_49': ['236.55', '22', '21', 10172.022705078125, 559.117573190484], '49_50': ['242.78', '22', '21', 10439.7646484375, 571.5772367806435], '50_51': ['220.88', '22', '21', 9497.912841796875, 527.7640579537951], '51_52': ['232.77', '22', '21', 10009.4130859375, 551.5543680058472], '52_53': ['227.72', '22', '21', 9792.260009765625, 541.454241249757], '53_54': ['245.56', '22', '21', 10559.2578125, 577.1282721521845], '54_55': ['245.66', '22', '21', 10563.064208984375, 577.3445372732709], '55_56': ['175.06', '22', '21', 7030.95166015625, 435.71025985316044], '56_57': ['32.73', '22', '21', 1306.20751953125, 151.25147187699193]}
#
# iter_art = attrs_lay_seg.keys() #получаем список всех названий опор
# print()
# for i in iter_art:
#    print(attrs_lay_seg[i])
#    print(attrs_lay.get(i))
#
#    if attrs_lay.get(i) != None:
#       print(attrs_lay.get(i)[0])
#       print(attrs_lay.get(i)[1])
#       print(attrs_lay.get(i)[2])
#       print(attrs_lay.get(i)[3])
#       print(attrs_lay.get(i)[4])
#       print(attrs_lay.get(i)[5])
#    else:
#       print(0)
#

# """
# This script should be run from the Python consol inside QGIS.
#
# It adds online sources to the QGIS Browser.
# Each source should contain a list with the folowing items (string type):
# [sourcetype, title, authconfig, password, referer, url, username, zmax, zmin]
#
# You can add or remove sources from the sources section of the code.
#
# Script by Klas Karlsson
# Sources from https://qms.nextgis.com/
#
# Licence GPL-3
#
# Regarding the terms of use for these background maps YOU will need to verify that you
# follow the individual EULA that comes with the different services,
# Most likely they will restrict how you can use the data.
#
# """
#
#
# # Sources
# sources = []
# sources.append(["connections-xyz","Google Maps","","","","https://mt1.google.com/vt/lyrs=m&x=%7Bx%7D&y=%7By%7D&z=%7Bz%7D","","19","0"])
#
# # Add sources to browser
# for source in sources:
#    connectionType = source[0]
#    connectionName = source[1]
#    QSettings().setValue("qgis/%s/%s/authcfg" % (connectionType, connectionName), source[2])
#    QSettings().setValue("qgis/%s/%s/password" % (connectionType, connectionName), source[3])
#    QSettings().setValue("qgis/%s/%s/referer" % (connectionType, connectionName), source[4])
#    QSettings().setValue("qgis/%s/%s/url" % (connectionType, connectionName), source[5])
#    QSettings().setValue("qgis/%s/%s/username" % (connectionType, connectionName), source[6])
#    QSettings().setValue("qgis/%s/%s/zmax" % (connectionType, connectionName), source[7])
#    QSettings().setValue("qgis/%s/%s/zmin" % (connectionType, connectionName), source[8])
# print('Работает')
# # Update GUI
# iface.reloadConnections()
# zzz = QSettings().value("qgis/connections-xyz")
# print(zzz)
# QgsProject.instance().addMapLayer(["connections-xyz","Google Maps","","","","https://mt1.google.com/vt/lyrs=m&x=%7Bx%7D&y=%7By%7D&z=%7Bz%7D","","19","0"])
#
#
# def areas(self, layer):
#    # layer = iface.activeLayer()
#    # создание нового поля в слое
#    # caps = layer.dataProvider().capabilities()
#    # Check if a particular capability is supported:
#    # caps & QgsVectorDataProvider.DeleteFeatures
#    # Print 2 if DeleteFeatures is supported
#    # if caps & QgsVectorDataProvider.AddAttributes:
#    #    res = layer.dataProvider().addAttributes([QgsField("area", QVariant.Double)])
#    #    layer.updateFields()
#    # print(res)
#    area_list = []
#    features = layer.getFeatures()
#    for feature in features:
#       # retrieve every feature with its geometry and attributes
#       print("Feature ID: ", feature.id())
#       # fetch geometry
#       # show some information about the feature geometry
#       geom = feature.geometry()
#       geomSingleType = QgsWkbTypes.isSingleType(geom.wkbType())
#       if geom.type() == QgsWkbTypes.PointGeometry:
#          # the geometry type can be of single or multi type
#          if geomSingleType:
#             x = geom.asPoint()
#             print("Point: ", x)
#          else:
#             x = geom.asMultiPoint()
#             print("MultiPoint: ", x)
#       elif geom.type() == QgsWkbTypes.LineGeometry:
#          if geomSingleType:
#             x = geom.asPolyline()
#             print("Line: ", x, "length: ", geom.length())
#          else:
#             x = geom.asMultiPolyline()
#             print("MultiLine: ", x, "length: ", geom.length())
#       elif geom.type() == QgsWkbTypes.PolygonGeometry:
#          if geomSingleType:
#             x = geom.asPolygon()
#             area_list.append(geom.area())
#             print("Polygon: ", x, "Area: ", geom.area())
#          else:
#             x = geom.asMultiPolygon()
#             # print("MultiPolygon: ", x, "Area: ", geom.area())
#             area_list.append(geom.area())
#             print("Area: ", geom.area())
#       else:
#          print("Unknown or invalid geometry")
#       # fetch attributes
#       # attrs = feature.attributes()
#       # attrs is a list. It contains all the attribute values of this feature
#       # print(attrs)
#       return area_list