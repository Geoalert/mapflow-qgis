"""Check for updates through QGIS's own plugin installer, and report the result in the message bar.

The installer is the same one Plugins › Manage and Install Plugins uses, so the answer covers every
plugin repository the user has set up, and an update is installed the usual way: from the
Upgradeable tab of the Plugin Manager.
"""
from __future__ import annotations

import inspect
from typing import Any, Dict, Optional

from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QDesktopServices
from qgis.core import Qgis, QgsSettings

from .. import config
from ..core.updates import ERROR, LATEST, NOT_LISTED, UPDATE, UpdateCheck, assess
from .message_bar import push

UPGRADEABLE_TAB = 3             # the Plugin Manager's Upgradeable tab, as QGIS itself opens it


def allow_experimental() -> bool:
    """Plugins › Manage and Install Plugins › Settings › Show also experimental plugins."""
    try:
        from qgis.core import QgsSettingsTree       # QGIS 3.30 and later
        return bool(QgsSettingsTree.node("plugin-manager").childSetting("allow-experimental").value())
    except (ImportError, AttributeError):
        return QgsSettings().value("app/plugin_installer/allowExperimental", False, type=bool)


def fetch_record(plugin_key: str) -> Optional[Dict[str, Any]]:
    """Refresh the plugin repositories (QGIS shows its own progress dialog) and return what they say
    about this plugin."""
    import pyplugin_installer
    from pyplugin_installer.installer_data import plugins
    pyplugin_installer.instance().fetchAvailablePlugins(reloadMode=True)
    return plugins.all().get(plugin_key)


def open_upgrades() -> None:
    import pyplugin_installer
    show = pyplugin_installer.instance().showPluginManagerWhenReady
    # Newer QGIS also filters the list by a search term. Older ones take *params and open the default
    # tab when given two, so the term is passed only where the signature names it.
    if "search_term" in inspect.signature(show).parameters:
        show(UPGRADEABLE_TAB, search_term=config.PLUGIN_NAME)
    else:
        show(UPGRADEABLE_TAB)


def check(installed: str, experimental_plugin: bool, plugin_key: str = config.PLUGIN_DIR.name) -> UpdateCheck:
    try:
        record = fetch_record(plugin_key)
    except Exception as error:                      # noqa: BLE001 - any installer failure is reported, not raised
        return UpdateCheck(ERROR, installed, error=str(error) or type(error).__name__)
    return assess(installed, record, allow_experimental(), experimental_plugin)


def report(iface, result: UpdateCheck) -> None:
    name = config.PLUGIN_NAME
    if result.state == UPDATE:
        push(iface, f"{name} {result.available} is available. You have {result.installed}.",
             Qgis.MessageLevel.Info, ("Update…", open_upgrades), duration=0)
    elif result.state == LATEST:
        push(iface, f"{name} is up to date ({result.installed}).", Qgis.MessageLevel.Success)
    elif result.state == NOT_LISTED and result.experimental_hidden:
        push(iface, f"{name} is an experimental plugin, and QGIS hides experimental versions. Turn on "
                    "“Show also experimental plugins” in Plugins › Manage and Install Plugins › Settings, "
                    "then check again.", Qgis.MessageLevel.Info, duration=0)
    elif result.state == NOT_LISTED:
        push(iface, f"{name} {result.installed} isn't in your plugin repositories, so QGIS can't update it. "
                    "New versions are on the releases page.", Qgis.MessageLevel.Info,
             ("Releases", lambda: QDesktopServices.openUrl(QUrl(config.RELEASES_URL))), duration=0)
    else:
        push(iface, f"Couldn't check for updates: {result.error}", Qgis.MessageLevel.Warning)
