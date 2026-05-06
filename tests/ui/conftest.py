"""Bootstrap for the ui-tier tests.

UI tests need a real Qt event loop and pytest-qt's `qtbot` fixture. They
run inside the qgis/qgis:release-3_28 Docker image under `xvfb-run`
(which provides the headless X display Qt requires).

This tier currently has no tests — only the harness. When adding the
first UI test:

* mark each test with `@pytest.mark.ui` for grep-ability (not strictly
  required since we select tests by directory),
* request the `qtbot` fixture from pytest-qt for interaction,
* keep dialog modal shows minimal — `qtbot.addWidget(dlg); dlg.show()`,
  no `dlg.exec_()`,
* run via `make test-ui` (Makefile wires `xvfb-run -a pytest tests/ui`).
"""
import importlib

from qgis.testing import start_app


def pytest_configure(config):
    start_app()
    # Same circular-import warmup as the qgis tier — UI tests touch the
    # full plugin tree and hit the same issue.
    for _ in range(2):
        try:
            importlib.import_module("mapflow.schema.processing")
            break
        except ImportError:
            pass
