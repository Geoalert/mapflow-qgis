from pathlib import Path

from qgis.core import QgsMapLayerType, QgsWkbTypes


def is_geotiff_layer(layer):
    """"""
    uri = layer.dataProvider().dataSourceUri()
    return Path(uri).suffix.lower() in ('.tif', '.tiff')


def is_polygon_layer(layer):
    """"""
    return (
        layer.type() == QgsMapLayerType.VectorLayer and
        layer.geometryType() == QgsWkbTypes.PolygonGeometry
    )
