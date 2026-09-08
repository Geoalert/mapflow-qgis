"""QGIS-tier test: unload persists the metadata filter before teardown (4-PR2, RISK 4).

The metadata filter the user set is written to QgsSettings in `unload`. Those writes used to sit at
the tail of unload, after service stops and dialog closes that can raise; a raise there stranded
them and lost the filter on the next start. They now run first, so a teardown failure cannot drop
them (spec/006 § a guarded callback is interrupted).
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
