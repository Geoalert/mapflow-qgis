"""Draw an area on the map: click to add corners, double-click or right-click to finish, Esc to cancel."""
from __future__ import annotations

from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsGeometry, QgsPointXY
from qgis.gui import QgsMapTool, QgsRubberBand

from .compat import POLYGON_GEOMETRY


class PolygonDrawTool(QgsMapTool):
    finished = pyqtSignal(object)    # QgsGeometry in the canvas CRS
    cancelled = pyqtSignal()

    def __init__(self, canvas):
        super().__init__(canvas)
        self.canvas = canvas
        self.points = []
        self.band = QgsRubberBand(canvas, POLYGON_GEOMETRY)
        self.band.setColor(QColor(49, 130, 206, 200))          # blue-500
        self.band.setFillColor(QColor(49, 130, 206, 40))
        self.band.setWidth(2)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def _redraw(self, hover=None):
        points = self.points + ([hover] if hover else [])
        self.band.reset(POLYGON_GEOMETRY)
        for point in points:
            self.band.addPoint(point, False)
        self.band.show()
        self.band.updatePosition()
        self.canvas.refresh()

    def canvasMoveEvent(self, event):
        if self.points:
            self._redraw(event.mapPoint())

    def canvasReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self._finish()
            return
        self.points.append(QgsPointXY(event.mapPoint()))
        self._redraw()

    def canvasDoubleClickEvent(self, event):
        self._finish()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.reset()
            self.cancelled.emit()
        elif event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete) and self.points:
            self.points.pop()
            self._redraw()

    def _finish(self):
        # a double-click also delivered a release: drop the duplicated last corner
        unique = []
        for point in self.points:
            if not unique or unique[-1] != point:
                unique.append(point)
        if len(unique) < 3:
            return
        geometry = QgsGeometry.fromPolygonXY([unique + [unique[0]]])
        self.reset()
        self.finished.emit(geometry)

    def reset(self):
        self.points = []
        self.band.reset(POLYGON_GEOMETRY)

    def deactivate(self):
        self.reset()
        super().deactivate()
