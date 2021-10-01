from pathlib import Path

from qgis.core import (
    QgsMapLayer, QgsMapLayerType, QgsWkbTypes, QgsGeometry,
    QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsCoordinateTransformContext
)


WGS84 = QgsCoordinateReferenceSystem('EPSG:4326')


def is_geotiff_layer(layer: QgsMapLayer) -> bool:
    """Determine if a layer is loaded from a GeoTIFF file.

    :param layer: A layer to test
    """
    uri = layer.dataProvider().dataSourceUri()
    return Path(uri).suffix.lower() in ('.tif', '.tiff')


def is_polygon_layer(layer: QgsMapLayer) -> bool:
    """Determine if a layer is of vector type and has polygonal geometry.

    :param layer: A layer to test
    """
    return layer.type() == QgsMapLayerType.VectorLayer and layer.geometryType() == QgsWkbTypes.PolygonGeometry


def to_wgs84(
    geometry: QgsGeometry, source_crs: QgsCoordinateReferenceSystem, transform_context: QgsCoordinateTransformContext
) -> QgsGeometry:
    """Reproject a geometry to WGS84.

    :param geometry: A feature's geometry
    :param source_crs: The current CRS of the passed geometry
    :param transform_context: An object containing information about the CRS, datums and the possible tranformations
        between them available in QGIS
    """
    transform = QgsCoordinateTransform(source_crs, WGS84, transform_context)
    geometry.transform(transform)
    return geometry


def from_wgs84(geometry: QgsGeometry, target_src: QgsCoordinateReferenceSystem, transform_context: QgsCoordinateTransformContext) -> QgsGeometry:
    """Transform a geometry from WGS84.

    :param geometry: A feature's geometry
    :param target_src: The current CRS of the passed geometry
    :param transform_context: An object containing information about the CRS, datums and the possible tranformations
        between them available in QGIS
    """
    geometry.transform(QgsCoordinateTransform(WGS84, target_src, transform_context))
    return geometry


def get_layer_extent(layer: QgsMapLayer, transform_context: QgsCoordinateTransformContext) -> QgsGeometry:
    """Get a layer's bounding box aka extent/envelope/bounds.

    :param layer: The layer of interest
    :param transform_context: An object containing information about the CRS, datums and the possible tranformations
        between them available in QGIS
    :param transform_context: An object containing information about the CRS, datums and the possible tranformations
        between them available in QGIS
    """
    # Create a geometry from the layer's extent
    extent_geometry = QgsGeometry.fromRect(layer.extent())
    # Reproject it to WGS84 if the layer has another CRS
    layer_crs = layer.crs()
    if layer_crs != WGS84:
        extent_geometry = to_wgs84(extent_geometry, layer_crs, transform_context)
    return extent_geometry
