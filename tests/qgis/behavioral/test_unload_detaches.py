"""Unloading detaches the plugin from what outlives it.

QGIS rebuilds the plugin on an in-place upgrade and under Plugin Reloader, but `QgsProject`, the
layers in it and the plugin's settings all survive the rebuild. So the old instance has to let go
of them itself: a subscription left on the project keeps running a dead plugin's handlers against
the next one's state, and a settings group left open makes the next instance save every key one
level deeper, where the next start never looks.

These build and unload plugins themselves instead of using the `plugin` fixture, which unloads on
teardown — what they check is what happens *after* an unload.
"""
from types import SimpleNamespace

import pytest
from qgis.core import QgsProject, QgsSettings, QgsVectorLayer


def _polygon_layer(name):
    return QgsVectorLayer("Polygon?crs=EPSG:4326", name, "memory")


@pytest.fixture
def plugins(plugin_iface, network, fresh_profile):
    """Load and unload plugins the way QGIS does. Any the test leaves loaded is unloaded on
    teardown, so a failing assertion cannot leak a subscription into the next journey."""
    from mapflow.mapflow import Mapflow

    loaded = []

    def load():
        instance = Mapflow(plugin_iface)
        loaded.append(instance)
        return instance

    def unload(instance):
        loaded.remove(instance)
        instance.unload()

    yield SimpleNamespace(load=load, unload=unload)
    for instance in reversed(loaded):
        instance.unload()
    QgsProject.instance().removeAllMapLayers()


def test_an_unloaded_plugin_no_longer_reacts_to_layers_added_to_the_project(plugin_iface, plugins):
    plugin = plugins.load()
    QgsProject.instance().addMapLayer(_polygon_layer("added while loaded"))
    # The layer context-menu action is how a newly added layer reaches the plugin. Seeing it here
    # proves the observation is live, so its absence after the unload actually means something.
    plugin_iface.addCustomActionForLayer.assert_called()

    plugins.unload(plugin)
    plugin_iface.addCustomActionForLayer.reset_mock()
    QgsProject.instance().addMapLayer(_polygon_layer("added after unload"))

    plugin_iface.addCustomActionForLayer.assert_not_called()


def test_an_unloaded_plugin_stops_watching_the_layers_it_monitored(plugins):
    layer = _polygon_layer("monitored")
    QgsProject.instance().addMapLayer(layer)
    unwatched = layer.receivers(layer.selectionChanged)

    plugin = plugins.load()  # a plugin watches the polygon layers already in the project
    assert layer.receivers(layer.selectionChanged) > unwatched

    plugins.unload(plugin)

    assert layer.receivers(layer.selectionChanged) == unwatched


def test_a_rebuilt_plugin_saves_its_settings_where_the_next_start_reads_them(plugins):
    plugins.unload(plugins.load())
    plugins.unload(plugins.load())  # unload saves the metadata filter inside the plugin's group

    settings = QgsSettings()
    assert settings.value("mapflow/metadataMinIntersection") is not None
    assert settings.value("mapflow/mapflow/metadataMinIntersection") is None
