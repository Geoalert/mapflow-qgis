"""Map tools for SAM Interactive spatial prompt creation.

SamPointMapTool — click on map to capture a WGS84 point.
SamBboxMapTool — draw a rectangle to capture a WGS84 bbox polygon.

Both tools emit (geojson, positive) where positive is derived from
mouse button: left-click = positive (True), right-click = negative (False).
"""
from PyQt5.QtCore import pyqtSignal, Qt

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsProject,
)
from qgis.gui import QgsMapToolEmitPoint, QgsMapToolExtent


class SamPointMapTool(QgsMapToolEmitPoint):
    """Click on the map canvas to emit a GeoJSON Point in WGS84."""

    point_captured = pyqtSignal(dict, bool)  # (GeoJSON Point, positive)

    def __init__(self, canvas):
        super().__init__(canvas)
        self._canvas = canvas

    def canvasReleaseEvent(self, event):
        point = self.toMapCoordinates(event.pos())
        positive = event.button() != Qt.RightButton

        crs_src = self._canvas.mapSettings().destinationCrs()
        crs_dst = QgsCoordinateReferenceSystem("EPSG:4326")
        transform = QgsCoordinateTransform(crs_src, crs_dst, QgsProject.instance())
        wgs84_point = transform.transform(point)

        geojson = {
            "type": "Point",
            "coordinates": [wgs84_point.x(), wgs84_point.y()],
        }
        self.point_captured.emit(geojson, positive)


class SamBboxMapTool(QgsMapToolExtent):
    """Draw a rectangle on the map canvas to emit a GeoJSON Polygon in WGS84."""

    bbox_captured = pyqtSignal(dict, bool)  # (GeoJSON Polygon, positive)

    def __init__(self, canvas):
        super().__init__(canvas)
        self._positive = True
        self.extentChanged.connect(self._on_extent)

    def canvasPressEvent(self, event):
        self._positive = event.button() != Qt.RightButton
        super().canvasPressEvent(event)

    def _on_extent(self, extent):
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
        self.bbox_captured.emit(geojson, self._positive)
