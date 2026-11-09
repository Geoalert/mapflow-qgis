A stand-in `qgis` package for `tests/qt6_ui.py`: `qgis.PyQt` maps to PyQt6 the way QGIS 4 does it
(including QAction, QActionGroup and QShortcut re-exported from QtWidgets), and `qgis.core` /
`qgis.gui` are placeholders. It lets the plugin's pages run on Qt 6 where QGIS 4 itself isn't installed.
Never put this folder on the path of a real QGIS.
