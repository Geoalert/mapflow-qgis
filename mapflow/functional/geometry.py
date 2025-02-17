from typing import List

from qgis import processing as qgis_processing  # to avoid collisions
from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsFeatureIterator

def clip_aoi_to_image_extent(aoi_geometry: QgsGeometry,
                             extents: List[QgsFeature]) -> QgsFeatureIterator:
    """Clip user AOI to image extent if the image doesn't cover the entire AOI.
    args:
        aoi_geometry: AOI geometry - selected by user area of interest (input)
        extents: list of QgsFeature objects from image extent(s) (overlay)
    """
    aoi_layer = QgsVectorLayer('Polygon?crs=epsg:4326', '', 'memory')
    aoi = QgsFeature()
    aoi.setGeometry(aoi_geometry)
    aoi_layer.dataProvider().addFeatures([aoi])
    aoi_layer.updateExtents()
    # Create a temp layer for the image extent
    image_extent_layer = QgsVectorLayer('MultiPolygon?crs=epsg:4326', '', 'memory')
    image_extent_layer.dataProvider().addFeatures(extents)
    image_extent_layer.updateExtents()
    try:
        # Find the intersection
        intersection = qgis_processing.run(
            'qgis:intersection',
            {'INPUT': aoi_layer, 'OVERLAY': image_extent_layer, 'OUTPUT': 'memory:'}
        )['OUTPUT']
    except:
        # If intersection function fails (happens sometimes for mosaics), fix mosaic geometries beforehand
        fixed_image_layer = qgis_processing.run(
            'native:fixgeometries', 
            {'INPUT':image_extent_layer, 'METHOD':1, 'OUTPUT':'memory:'}
        )['OUTPUT']
        # And aoi as well
        fixed_aoi_layer = qgis_processing.run(
            'native:fixgeometries', 
            {'INPUT':aoi_layer, 'METHOD':1, 'OUTPUT':'memory:'}
        )['OUTPUT']
        # And then use fixed layers for intersection
        intersection = qgis_processing.run(
            'qgis:intersection',
            {'INPUT': fixed_aoi_layer, 'OVERLAY': fixed_image_layer, 'OUTPUT': 'memory:'}
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
    try:
        # Find the intersection
        intersection = qgis_processing.run('qgis:intersection',
                                           {'INPUT': aoi_layer, 'OVERLAY': catalog_layer, 'OUTPUT': 'memory:'}
                                        )['OUTPUT']
    except:
        # If intersection function fails, fix aoi geometries beforehand
        fixed_aoi_layer = qgis_processing.run(
            'native:fixgeometries', 
            {'INPUT':aoi_layer, 'METHOD':1, 'OUTPUT':'memory:'}
        )['OUTPUT']
        # And catalog as well
        fixed_catalog_layer = qgis_processing.run(
            'native:fixgeometries', 
            {'INPUT':catalog_layer, 'METHOD':1, 'OUTPUT':'memory:'}
        )['OUTPUT']
        # And then use fixed layers for intersection
        intersection = qgis_processing.run('qgis:intersection',
                                           {'INPUT': fixed_aoi_layer, 'OVERLAY': fixed_catalog_layer, 'OUTPUT': 'memory:'}
                                          )['OUTPUT']
    return intersection.getFeatures()
