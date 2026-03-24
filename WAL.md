# Journal for logging and planning of features to implement

## 1. Add AI setup
[v]
- Modify agents.md to meet this repo's structure (no makefile, no docker, etc.)
- Modify planning, implementation and stabilization instructions to address stack and UI component of this app (QT, PyQGis)
Adapted from generic Docker/Makefile/alembic template to QGIS plugin structure; UI instructions derived from existing dialog patterns (uic.loadUiType, signal/slot, separation of concerns)

## 2. Generate spec
[v]
- Research existing codebase
- Populate spec with necessary documents; ask for API documentation if needed
All 5 specs populated from codebase analysis: goal (plugin purpose/constraints), API (all Mapflow/Maxar/Sentinel endpoints consumed), persistence (full QgsSettings key inventory from code), stack (PyQt5/QGIS/pytest + strict no-external-deps policy), interactions (all external systems; Maxar/Sentinel marked legacy)

## 3. Plan test
[v]
- Unit tests on functional
- Integration tests on API calls
- UI testing
All tests require QGIS runtime — no value in partial testing without it. Tools: pytest + pytest-qt + unittest.mock (stdlib). QgsApplication bootstrapped via qgis.testing.start_app() in pytest_configure hook (must run before collection because plugin modules create QIcon at import time). conftest.py provides iface mock and http_mock fixtures. pytest-qt chosen over raw PyQt5.QtTest for signal-heavy architecture (waitSignal, auto widget cleanup via qtbot).

## 4. Feature: download image from data-catalog
[ready-for-review]
- Refactored 002_api.md into index + 4 sub-files (A: project, B: processing, C: my imagery, D: search) for maintainability
- Added `GET /rest/rasters/image/{image_id}/download` spec with presigned URL response model and error codes (404/403/409)
- Added `available_for_download` boolean to ImageReturnSchema (defaults True for backward compat via SkipDataClass.from_dict)
- Download uses two-step flow: authenticated GET for presigned URL, then unauthenticated direct S3 download — avoids routing large files through the backend
- Download button placed first in image cell layout for discoverability; disabled with tooltip change when `available_for_download=False`
- 6 tests added (schema parsing, default values, API URL construction); all pass on QGIS 3.28 Python 3.9

## 5. Add new zoom-selector feature
[ ]
Use 002_E_zoom_selector_api.md
- Add small button near zoom selector comboBox to call for zoom selector api, active if selected source is Mapflow data provider
- On press of the button, call api and select zoom automatically depending on response
- on error, report to user with reasonable message