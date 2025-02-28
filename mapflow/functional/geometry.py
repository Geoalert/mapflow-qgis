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
        intersection = intersect_geoms(aoi_layer, image_extent_layer)
    except:
        # If intersection function fails, fix mosaic geometries beforehand
        fixed_image_layer = fix_geoms(image_extent_layer)
        fixed_aoi_layer = fix_geoms(aoi_layer)
        # And then use fixed layers for intersection
        intersection = intersect_geoms(fixed_aoi_layer, fixed_image_layer)
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
        intersection = intersect_geoms(aoi_layer, catalog_layer)
    except:
        # If intersection function fails, fix geometries beforehand
        fixed_aoi_layer = fix_geoms(aoi_layer)
        fixed_catalog_layer = fix_geoms(catalog_layer)
        # And then use fixed layers for intersection
        intersection = intersect_geoms(fixed_aoi_layer, fixed_catalog_layer)
    return intersection.getFeatures()

def fix_geoms(layer: QgsVectorLayer) -> QgsVectorLayer:
    fixed_layer = qgis_processing.run(
        'native:fixgeometries', 
        {'INPUT':layer, 'METHOD':1, 'OUTPUT':'memory:'}
    )['OUTPUT']
    return fixed_layer

def intersect_geoms(input_layer: QgsVectorLayer, 
                    overlay_layer: QgsVectorLayer) -> QgsVectorLayer:
    intersection = qgis_processing.run('qgis:intersection',
                                       {'INPUT': input_layer, 'OVERLAY': overlay_layer, 'OUTPUT': 'memory:'}
                                      )['OUTPUT']
    return intersection