# Journal for logging and planning of features to implement

## 1. Add AI setup
[v]
- Modify agents.md to meet this repo's structure (no makefile, no docker, etc.)
- Modify planning, implementation and stabilization instructions to address stack and UI component of this app (QT, PyQGis)
Adapted from generic Docker/Makefile/alembic template to QGIS plugin structure; UI instructions derived from existing dialog patterns (uic.loadUiType, signal/slot, separation of concerns)

## 2. Generate spec
[ready-for-review]
- Research existing codebase
- Populate spec with necessary documents; ask for API documentation if needed
All 5 specs populated from codebase analysis: goal (plugin purpose/constraints), API (all Mapflow/Maxar/Sentinel endpoints consumed), persistence (QgsSettings keys), stack (PyQt5/QGIS/pytest), interactions (all external systems with protocols and failure handling)

## 3. Plan test
[ ]
- Unit tests on functional
- Integration tests on API calls
- UI testing