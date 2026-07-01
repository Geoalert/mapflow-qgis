"""QGIS-tier tests for preview-layer handling: de-duplicating by moving to top, and the
in-template precedence (AOIs > previews > search-results footprints)."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from qgis.core import QgsProject, QgsVectorLayer

from mapflow.mapflow import Mapflow


def _mem_layer(name):
    return QgsVectorLayer("Polygon?crs=epsg:4326", name, "memory")


def _add(project, group, layer):
    project.addMapLayer(layer, addToLegend=False)
    group.addLayer(layer)
    return layer


def test_move_layer_to_top_brings_node_first():
    project = QgsProject()
    root = project.layerTreeRoot()
    _add(project, root, _mem_layer("first"))
    second = _add(project, root, _mem_layer("second"))

    plugin = Mapflow.__new__(Mapflow)
    plugin.app_context = SimpleNamespace(project=project)

    plugin._move_layer_to_top(second.id())

    assert root.children()[0].layerId() == second.id()


def test_relocate_preview_places_it_above_footprints_inside_template_group():
    project = QgsProject()
    root = project.layerTreeRoot()
    mapflow_group = root.insertGroup(0, "Mapflow")
    template_group = mapflow_group.insertGroup(0, "T1")
    # AOI subgroup on top, footprints at the bottom of the template group.
    template_group.insertGroup(0, "AOI: North")
    footprints = _add(project, template_group, _mem_layer("metadata"))
    # A preview added to the root (as the regular preview flow does).
    preview = _add(project, root, _mem_layer("img-1 preview"))

    plugin = Mapflow.__new__(Mapflow)
    settings = MagicMock()
    settings.value.return_value = "Mapflow"
    plugin.app_context = SimpleNamespace(
        project=project, settings=settings, plugin_name="Mapflow", metadata_layer=footprints,
    )
    plugin.processing_service = SimpleNamespace(
        in_template_mode=True, active_template=SimpleNamespace(name="T1"),
    )

    plugin._relocate_preview_to_template_group(preview)

    names = [c.name() for c in template_group.children()]
    # Order within the template group: AOI subgroup, preview, footprints.
    assert names == ["AOI: North", "img-1 preview", "metadata"]
    # The preview no longer sits at the root.
    assert all(getattr(c, "layerId", lambda: None)() != preview.id() for c in root.children())


def test_relocate_preview_noop_outside_template_mode():
    project = QgsProject()
    root = project.layerTreeRoot()
    preview = _add(project, root, _mem_layer("img-1 preview"))

    plugin = Mapflow.__new__(Mapflow)
    plugin.app_context = SimpleNamespace(project=project)
    plugin.processing_service = SimpleNamespace(in_template_mode=False, active_template=None)

    plugin._relocate_preview_to_template_group(preview)

    assert root.children()[-1].layerId() == preview.id()
