"""Bootstrap for the qgis-tier tests.

Tests in this directory need a real PyQGIS runtime — they import plugin
modules that touch qgis.core / qgis.gui at module load time. Run inside
the qgis/qgis:release-3_28 Docker image (see Dockerfile.tests + Makefile).
"""
import importlib

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

    # Pre-warm the mapflow module tree to survive the circular import on first load.
    # The chain mapflow.schema.processing -> entity.provider -> functional.layer_utils
    # -> dialogs -> mapflow.schema creates a circular dependency that fails on the
    # first attempt but succeeds on retry because partial modules are cached.
    for _ in range(2):
        try:
            importlib.import_module("mapflow.schema.processing")
            break
        except ImportError:
            pass


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
