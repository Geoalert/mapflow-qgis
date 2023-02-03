from qgis import processing as qgis_processing  # to avoid collisions
from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsFeatureIterator


def clip_aoi_to_image_extent(aoi_geometry: QgsGeometry, extent: QgsFeature) -> QgsFeatureIterator:
    """Clip user AOI to image extent if the image doesn't cover the entire AOI."""
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
