from qgis import processing as qgis_processing  # to avoid collisions
from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsFeatureIterator


def clip_aoi_to_image_extent(aoi_geometry: QgsGeometry,
                             extent: QgsFeature) -> QgsFeatureIterator:
    """Clip user AOI to image extent if the image doesn't cover the entire AOI.
    args:
        aoi_geometry: AOI geometry - selected by user area of interest (input)
        extent: image extent (overlay)
    """
    aoi_layer = QgsVectorLayer('Polygon?crs=epsg:4326', '', 'memory')
    aoi = QgsFeature()
    aoi.setGeometry(aoi_geometry)
    aoi_layer.dataProvider().addFeatures([aoi])
    aoi_layer.updateExtents()
    # Create a temp layer for the image extent
    image_extent_layer = QgsVectorLayer('Polygon?crs=epsg:4326', '', 'memory')
    image_extent_layer.dataProvider().addFeatures([extent])
    aoi_layer.updateExtents()
    # Find the intersection
    intersection = qgis_processing.run(
        'qgis:intersection',
        {'INPUT': aoi_layer, 'OVERLAY': image_extent_layer, 'OUTPUT': 'memory:'}
    )['OUTPUT']
    return intersection.getFeatures()

def clip_aoi_to_catalog_extent(catalog_aoi: QgsGeometry,
                               selected_aoi: QgsGeometry) -> QgsFeatureIterator:
    # Create AOI layer from WGS84 geometry
    aoi_layer = QgsVectorLayer('Polygon?crs=epsg:4326', '', 'memory')
    aoi_feature = QgsFeature()
    aoi_feature.setGeometry(selected_aoi)
    aoi_layer.dataProvider().addFeatures([aoi_feature])
    aoi_layer.updateExtents()
    # Create a layer from chosen mosaic or image footprint
    catalog_layer = QgsVectorLayer('Polygon?crs=epsg:4326', '', 'memory')
    catalog_feature = QgsFeature()
    catalog_feature.setGeometry(catalog_aoi)
    catalog_layer.dataProvider().addFeatures([catalog_feature])
    catalog_layer.updateExtents()
    # Find the intersection
    intersection = qgis_processing.run('qgis:intersection',
                                      {'INPUT': aoi_layer, 'OVERLAY': catalog_layer, 'OUTPUT': 'memory:'}
                                      )['OUTPUT']
    return intersection.getFeatures()
