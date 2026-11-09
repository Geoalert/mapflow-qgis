"""The few names that differ between QGIS 3 (Qt 5) and QGIS 4 (Qt 6), resolved once.

Everything else in the plugin is written so that both accept it: scoped enums
(`Qt.AlignmentFlag.AlignLeft`, `Qgis.MessageLevel.Info`), `exec()` instead of `exec_()`,
and `qgis.PyQt` imports only.
"""
from __future__ import annotations

from qgis.core import Qgis, QgsWkbTypes

QGIS_VERSION_INT = Qgis.QGIS_VERSION_INT                 # 34400 for 3.44, 40200 for 4.2
QGIS_MAJOR = QGIS_VERSION_INT // 10000

# Geometry types: Qgis.GeometryType since 3.30 (and in QGIS 4); QgsWkbTypes.*Geometry before.
if hasattr(Qgis, "GeometryType"):
    POINT_GEOMETRY = Qgis.GeometryType.Point
    LINE_GEOMETRY = Qgis.GeometryType.Line
    POLYGON_GEOMETRY = Qgis.GeometryType.Polygon
else:                                                     # QGIS 3.22 – 3.28
    POINT_GEOMETRY = QgsWkbTypes.PointGeometry
    LINE_GEOMETRY = QgsWkbTypes.LineGeometry
    POLYGON_GEOMETRY = QgsWkbTypes.PolygonGeometry
