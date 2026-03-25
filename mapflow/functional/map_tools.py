"""Map tools for SAM Interactive spatial prompt creation.

SamPointMapTool — click on map to capture a WGS84 point.
SamBboxMapTool — draw a rectangle to capture a WGS84 bbox polygon.
"""
from PyQt5.QtCore import pyqtSignal

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsProject,
)
from qgis.gui import QgsMapToolEmitPoint, QgsMapToolExtent


class SamPointMapTool(QgsMapToolEmitPoint):
    """Click on the map canvas to emit a GeoJSON Point in WGS84."""

    point_captured = pyqtSignal(dict)  # GeoJSON Point geometry

    def __init__(self, canvas):
        super().__init__(canvas)
        self._canvas = canvas

    def canvasReleaseEvent(self, event):
        point = self.toMapCoordinates(event.pos())
        # Transform to WGS84
        crs_src = self._canvas.mapSettings().destinationCrs()
        crs_dst = QgsCoordinateReferenceSystem("EPSG:4326")
        transform = QgsCoordinateTransform(crs_src, crs_dst, QgsProject.instance())
        wgs84_point = transform.transform(point)

        geojson = {
            "type": "Point",
            "coordinates": [wgs84_point.x(), wgs84_point.y()],
        }
        self.point_captured.emit(geojson)


class SamBboxMapTool(QgsMapToolExtent):
    """Draw a rectangle on the map canvas to emit a GeoJSON Polygon in WGS84."""

    bbox_captured = pyqtSignal(dict)  # GeoJSON Polygon geometry

    def __init__(self, canvas):
        super().__init__(canvas)
        self.extentChanged.connect(self._on_extent)

    def _on_extent(self, extent):
        # Transform to WGS84
        canvas = self.canvas()
        crs_src = canvas.mapSettings().destinationCrs()
        crs_dst = QgsCoordinateReferenceSystem("EPSG:4326")
        transform = QgsCoordinateTransform(crs_src, crs_dst, QgsProject.instance())
        wgs84_extent = transform.transformBoundingBox(extent)

        x_min = wgs84_extent.xMinimum()
        y_min = wgs84_extent.yMinimum()
        x_max = wgs84_extent.xMaximum()
        y_max = wgs84_extent.yMaximum()

        geojson = {
            "type": "Polygon",
            "coordinates": [[
                [x_min, y_min],
                [x_max, y_min],
                [x_max, y_max],
                [x_min, y_max],
                [x_min, y_min],
            ]],
        }
        self.bbox_captured.emit(geojson)
