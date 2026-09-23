"""QGIS-tier tests: what `unload` must still do when part of its teardown fails.

The metadata filter the user set is written to QgsSettings in `unload`. Those writes used to sit at
the tail of unload, after service stops and dialog closes that can raise; a raise there stranded
them and lost the filter on the next start. They now run first, so a teardown failure cannot drop
them (spec/006 § a guarded callback is interrupted).

The same reasoning covers detaching. The plugin subscribes to objects that outlive it — `QgsProject`
and the layers in it — and opens a group on the process-wide settings object. Both are undone in a
`finally`, so a failing service stop cannot leave the dead instance subscribed or the group open.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from mapflow.mapflow import Mapflow


def _plugin_with_dialog():
    plugin = Mapflow.__new__(Mapflow)
    plugin.processing_service = MagicMock()
    plugin.account_service = MagicMock()
    plugin.iface = MagicMock()
    plugin.add_layer_action = MagicMock()
    plugin.remove_layer_action = MagicMock()
    plugin.toolbar = MagicMock()
    plugin.dlg_login = None
    plugin.dlg_provider = None
    plugin.app_context = SimpleNamespace(settings=MagicMock())
    dlg = MagicMock()
    dlg.minIntersection.value.return_value = 5
    dlg.maxCloudCover.value.return_value = 20
    dlg.off_nadir_range.return_value = (0, 45)
    plugin.dlg = dlg
    # What `__init__` records for `unload` to undo.
    plugin._external_connections = []
    plugin.http = MagicMock()
    return plugin


def _persisted_keys(settings):
    return [c.args[0] for c in settings.setValue.call_args_list]


def test_unload_persists_metadata_settings():
    plugin = _plugin_with_dialog()

    plugin.unload()

    keys = _persisted_keys(plugin.app_context.settings)
    assert 'metadataMinIntersection' in keys
    assert 'metadataTo' in keys


def test_unload_still_persists_settings_when_teardown_raises():
    plugin = _plugin_with_dialog()
    plugin.processing_service.stop.side_effect = RuntimeError("stop failed")

    with pytest.raises(RuntimeError):
        plugin.unload()

    keys = _persisted_keys(plugin.app_context.settings)
    assert 'metadataMinIntersection' in keys  # written before the teardown that raised
    assert 'metadataTo' in keys


def test_unload_detaches_and_closes_the_settings_group_even_when_teardown_raises():
    plugin = _plugin_with_dialog()
    plugin.processing_service.stop.side_effect = RuntimeError("stop failed")
    project_signal, layer_signal = MagicMock(), MagicMock()
    plugin._external_connections = [(project_signal, "project-token"),
                                    (layer_signal, "layer-token")]

    with pytest.raises(RuntimeError):
        plugin.unload()

    # By token: a bare disconnect() would also cut QGIS's and other plugins' slots.
    project_signal.disconnect.assert_called_once_with("project-token")
    layer_signal.disconnect.assert_called_once_with("layer-token")
    plugin.app_context.settings.endGroup.assert_called_once()
    # A background retry still waiting would call into this instance after it is gone.
    plugin.http.close.assert_called_once()


def test_a_sender_already_gone_does_not_stop_the_rest_of_the_detach():
    """A layer removed from the project is deleted, and disconnecting from it then raises. That must
    not leave the other subscriptions in place or the settings group open."""
    plugin = _plugin_with_dialog()
    gone, live = MagicMock(), MagicMock()
    gone.disconnect.side_effect = RuntimeError("wrapped C/C++ object has been deleted")
    plugin._external_connections = [(gone, "gone-token"), (live, "live-token")]

    plugin.unload()

    live.disconnect.assert_called_once_with("live-token")
    plugin.app_context.settings.endGroup.assert_called_once()
