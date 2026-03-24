# 004 Stack

## Purpose
Capture technology choices and required versions.

## Content

Runtime: QGIS Desktop 3.20+ (Python environment bundled with QGIS).

Language: Python 3 (minimum 3.6 for compatibility with older QGIS builds; datetime parsing workarounds present).

UI framework: PyQt5 (as bundled with QGIS 3.x). Dialogs designed in Qt Designer (`.ui` files), loaded at runtime via `uic.loadUiType()`.

Networking: QgsNetworkAccessManager (Qt-based, QGIS-integrated — enables proxy support, auth manager integration). No third-party HTTP clients (no requests/httpx/aiohttp).

GIS libraries:
- QGIS Python API (qgis.core, qgis.gui) — layers, geometry, settings, project management
- GDAL/OGR (osgeo) — raster I/O, coordinate transforms
- pyproj — CRS transformations

Build/deploy: `qgis-plugin-ci` for packaging and release. Plugin published to QGIS Plugin Repository.

Test tools: pytest (local execution, no containers).

CI/CD: GitHub Actions (implied by `.github/` structure).

External dependencies: Mapflow REST API backend (required for all functionality beyond UI).
