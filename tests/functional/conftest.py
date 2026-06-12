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
import importlib

from qgis.testing import start_app


def pytest_configure(config):
    start_app()
    # Pre-warm the mapflow module tree to survive the circular import on first
    # load. The chain mapflow.schema.processing -> entity.provider ->
    # functional.layer_utils -> dialogs -> mapflow.schema fails on the first
    # attempt but succeeds on retry because partial modules are cached.
    for _ in range(2):
        try:
            importlib.import_module("mapflow.schema.processing")
            break
        except ImportError:
            pass
