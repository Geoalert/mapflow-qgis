"""Bootstrap for the qgis-tier tests.

Tests in this directory need a real PyQGIS runtime — they import plugin
modules that touch qgis.core / qgis.gui at module load time. Run inside
the qgis/qgis:release-3_28 Docker image (see Dockerfile.tests + Makefile).
"""
import pytest
from unittest.mock import MagicMock


def pytest_configure(config):
    """Bootstrap QgsApplication before test collection.

    Must happen here (not in a fixture) because mapflow modules create
    Qt objects (QIcon, etc.) at import time, which requires a living
    QApplication before any test file is imported.
    """
    from qgis.testing import start_app
    start_app()

    # start_app() gives QgsApplication but not the Processing framework, so `qgis.processing`
    # resolves to a namespace package with no `run`. Any plugin code that clips or repairs
    # geometry then raises AttributeError instead of doing the work — the AOI/footprint
    # intersection behind My Imagery is the clearest case, and it turns into an error in
    # whichever test happens to trigger it rather than a visible gap.
    # Guarded: if the Processing plugin is not present the tier still runs, just without
    # those code paths, which is what happened before this was added.
    try:
        from processing.core.Processing import Processing
        Processing.initialize()
    except Exception as error:  # pragma: no cover - environment capability probe
        print(f"QGIS Processing unavailable, geometry operations will not run: {error}")


@pytest.fixture(autouse=True)
def _no_blocking_dialogs(monkeypatch):
    """Never let a modal dialog open in the test container.

    `alert()` defaults to `blocking=True`, which is `QMessageBox.exec()` — an event loop with
    nobody to close it here. An unstubbed call does not fail the run, it **hangs** it: pytest
    prints nothing further and the tier sits until it is killed, with no indication of which test
    is stuck. Fourteen test modules stub `alert` themselves precisely to avoid this, which means
    the protection holds only for as long as everyone remembers it.

    Patching the dialog primitives instead makes forgetting harmless: `exec` returns `Ok`
    immediately, so a missed stub produces a normal pass or a normal assertion failure. Modules
    that stub `alert` are unaffected — their patch shadows this one.
    """
    from PyQt5.QtWidgets import QInputDialog, QMessageBox
    monkeypatch.setattr(QMessageBox, "exec", lambda self: QMessageBox.Ok, raising=False)
    monkeypatch.setattr(QMessageBox, "exec_", lambda self: QMessageBox.Ok, raising=False)
    monkeypatch.setattr(QMessageBox, "open", lambda self: None, raising=False)
    # ask_text() is the other blocking prompt reachable from service code.
    monkeypatch.setattr(QInputDialog, "getText", staticmethod(lambda *a, **k: ("", False)),
                        raising=False)


@pytest.fixture()
def iface():
    """Mock QgisInterface for tests that need a plugin iface reference."""
    mock_iface = MagicMock()
    mock_iface.mapCanvas.return_value = MagicMock()
    mock_iface.mainWindow.return_value = MagicMock()
    return mock_iface


@pytest.fixture()
def http_mock():
    """Mock Http client with pre-wired methods.

    Usage:
        def test_something(http_mock):
            api = ProjectApi(http=http_mock, server="https://example.com")
            api.get_projects(callback=my_callback)
            http_mock.get.assert_called_once()
    """
    mock = MagicMock()
    mock.get.return_value = MagicMock()
    mock.post.return_value = MagicMock()
    mock.put.return_value = MagicMock()
    mock.delete.return_value = MagicMock()
    return mock
