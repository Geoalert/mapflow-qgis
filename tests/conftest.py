"""Shared fixtures for mapflow plugin tests.

All tests run inside the QGIS Python environment.
QgsApplication is bootstrapped before test collection via pytest_configure
so that module-level Qt objects (QIcon etc.) can be created during import.
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
