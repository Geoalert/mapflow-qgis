"""QGIS-tier tests for preview-layer handling: de-duplicating by moving to top, and the
in-template precedence (AOIs > previews > search-results footprints).

Owned by `PreviewService` since the preview extraction. The group lookup it uses is
`layer_utils.find_template_group`, which creates nothing — so relocating a preview can never
conjure the template group it was looking for."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from qgis.core import QgsProject, QgsVectorLayer

from mapflow.functional.service.preview_service import PreviewService
from mapflow.functional.service.template_service import TemplateService


def _mem_layer(name):
    return QgsVectorLayer("Polygon?crs=epsg:4326", name, "memory")


def _add(project, group, layer):
    project.addMapLayer(layer, addToLegend=False)
    group.addLayer(layer)
    return layer


def _service(app_context, template_service=None):
    return PreviewService(
        iface=MagicMock(),
        app_context=app_context,
        http=MagicMock(),
        plugin_dir="",
        config=MagicMock(),
        result_loader=MagicMock(),
        processing_service=MagicMock(),
        template_service=template_service or SimpleNamespace(in_template_mode=False,
                                                                 active_template=None))


def test_move_layer_to_top_brings_node_first():
    project = QgsProject()
    root = project.layerTreeRoot()
    _add(project, root, _mem_layer("first"))
    second = _add(project, root, _mem_layer("second"))

    service = _service(SimpleNamespace(project=project))

    service._move_layer_to_top(second.id())

    assert root.children()[0].layerId() == second.id()


def _template_service(app_context, in_template_mode=True, template_name="T1"):
    """Placing a layer among a template's layers is TemplateService's call since the
    layer-placement step; PreviewService just hands the built layer over."""
    service = TemplateService(app_context=app_context, processing_service=MagicMock())
    service.in_template_mode = in_template_mode
    service.active_template = SimpleNamespace(name=template_name) if in_template_mode else None
    return service


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

    settings = MagicMock()
    settings.value.return_value = "Mapflow"
    service = _template_service(
        SimpleNamespace(project=project, settings=settings, plugin_name="Mapflow",
                        metadata_layer=footprints))

    service.place_preview_layer(preview)

    names = [c.name() for c in template_group.children()]
    # Order within the template group: AOI subgroup, preview, footprints.
    assert names == ["AOI: North", "img-1 preview", "metadata"]
    # The preview no longer sits at the root.
    assert all(getattr(c, "layerId", lambda: None)() != preview.id() for c in root.children())


def test_relocate_preview_noop_outside_template_mode():
    project = QgsProject()
    root = project.layerTreeRoot()
    preview = _add(project, root, _mem_layer("img-1 preview"))

    service = _template_service(SimpleNamespace(project=project), in_template_mode=False)

    service.place_preview_layer(preview)

    assert root.children()[-1].layerId() == preview.id()


def test_preview_service_hands_the_layer_to_the_template_service():
    """The placement decision is not PreviewService's; it only passes the layer along."""
    service = _service(SimpleNamespace(project=QgsProject()),
                       template_service=MagicMock())
    layer = object()

    service._relocate_to_template_group(layer)

    service.template_service.place_preview_layer.assert_called_once_with(layer)
