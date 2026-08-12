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
from unittest.mock import MagicMock, patch

import pytest
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QMainWindow
from qgis.core import QgsNetworkAccessManager

from fake_network import FakeNetwork


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
def network():
    """Replace QGIS's network manager for the whole test.

    Patched on the QGIS class rather than on the name imported into a plugin module, so it
    keeps working when `Http` moves package in Phase D.
    """
    fake = FakeNetwork()
    with patch.object(QgsNetworkAccessManager, "instance", staticmethod(lambda: fake)):
        yield fake


@pytest.fixture
def plugin(plugin_iface, network):
    """The real plugin object, built the way QGIS builds it.

    Depends on `network` so the manager is already faked when the plugin builds its Http.
    """
    from mapflow.mapflow import Mapflow

    instance = Mapflow(plugin_iface)
    yield instance
    # Timers created in __init__ keep firing into a dead object otherwise, and a stray tick
    # during a later test surfaces as an unrelated failure.
    instance.unload()


@pytest.fixture
def logged_in(plugin, network):
    """A plugin past the login exchange, which is the precondition for most journeys.

    Driven through the login dialog's own widgets rather than by calling a plugin method, so
    it keeps working when that method moves.
    """
    log_in(plugin)
    settle(network)
    return plugin


def log_in(plugin):
    """Type a token and press Log in, exactly as a user does."""
    plugin.dlg_login.token.setText("ZGVtbzpkZW1v")  # pragma: allowlist secret
    plugin.dlg_login.logIn.click()


def settle(network, rounds=8, wait_ms=120):
    """Let the plugin finish whatever the last action started.

    Real time has to pass, not just replies be delivered: most of the startup configuration
    hangs off a 500 ms QTimer, and the account response that carries the model list, the
    providers and the project table only arrives because that timer fires. Waiting for it
    rather than poking the timer object keeps the helper honest — it names nothing the
    refactoring moves, and it will still work when the timer belongs to a session service.

    Each round pumps the event loop and then answers whatever was asked, so a chain of
    request -> callback -> next request unwinds without the test knowing its length.
    """
    for _ in range(rounds):
        QTest.qWait(wait_ms)
        network.deliver()
