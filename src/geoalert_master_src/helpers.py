from pathlib import Path

from qgis.core import QgsMapLayerType, QgsWkbTypes, QgsCoordinateReferenceSystem, QgsGeometry, QgsCoordinateTransform


WGS84 = QgsCoordinateReferenceSystem('EPSG:4326')


def is_geotiff_layer(layer):
    """"""
    uri = layer.dataProvider().dataSourceUri()
    return Path(uri).suffix.lower() in ('.tif', '.tiff')


def is_polygon_layer(layer):
    """"""
    return layer.type() == QgsMapLayerType.VectorLayer and layer.geometryType() == QgsWkbTypes.PolygonGeometry


def to_wgs84(geometry, source_crs, transform_context):
    """"""
    transform = QgsCoordinateTransform(source_crs, WGS84, transform_context)
    geometry.transform(transform)
    return geometry


def get_layer_extent(layer, transform_context):
    """Get a layer's bounding box (extent)."""
    # Create a geometry from the layer's extent
    extent_geometry = QgsGeometry.fromRect(layer.extent())
    # Reproject it to WGS84 if the layer has another CRS
    layer_crs = layer.crs()
    if layer_crs != WGS84:
        extent_geometry = to_wgs84(extent_geometry, layer_crs, transform_context)
    return extent_geometry
