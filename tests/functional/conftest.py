"""Bootstrap for the functional-tier tests.

Functional tests are pure-logic tests that don't exercise real QGIS
state or any UI surface. They still run inside the qgis/qgis Docker
image, because the plugin's leaf modules import qgis.* / PyQt5.* at
module load time and stubbing that surface portably is more brittle
than just running with the real runtime.

Convention for adding tests here:
* test only pure-Python helpers (string ops, schema parsing, dataclass
  validation) — anything that needs `QgsProject`, real layers, real
  network access, or live signals belongs in `tests/qgis/`,
* anything that opens a widget / starts an event loop belongs in
  `tests/ui/`.
"""
from qgis.testing import start_app


def pytest_configure(config):
    start_app()
