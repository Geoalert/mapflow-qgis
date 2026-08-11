"""Shared harness for the behavioral tests.

These tests exist to prove that the 3.7.0 refactoring changed no user-visible behaviour, so
they may only touch surfaces that outlive it (`spec/007_architecture.md` § The test surface
that survives a move):

* the plugin entry point — ``Mapflow(iface)``, ``initGui()``, ``unload()``
* widgets, by the object names the ``.ui`` files give them
* the HTTP conversation
* ``QgsProject`` layers and ``QgsSettings`` keys

Naming anything else — a service class, a helper, a private method — makes the test fail when
that thing moves, which is precisely the noise it is meant to filter out. Constructing objects
with ``Class.__new__(Class)`` is banned here for the same reason.
"""
from unittest.mock import MagicMock

import pytest
from PyQt5.QtWidgets import QMainWindow


@pytest.fixture
def plugin_iface():
    """A QGIS interface the plugin can actually be built against.

    ``mainWindow()`` must return a real widget: it becomes the parent of the main dialog and
    of the plugin QObject itself, and PyQt rejects a MagicMock where it expects a QWidget.
    Everything else the plugin asks of iface is inspected, not parented, so a mock suffices.
    """
    iface = MagicMock()
    iface.mainWindow.return_value = QMainWindow()
    iface.mapCanvas.return_value = MagicMock()
    return iface


@pytest.fixture
def plugin(plugin_iface):
    """The real plugin object, built the way QGIS builds it."""
    from mapflow.mapflow import Mapflow

    instance = Mapflow(plugin_iface)
    yield instance
    # Timers created in __init__ keep firing into a dead object otherwise, and a stray tick
    # during a later test surfaces as an unrelated failure.
    instance.unload()
