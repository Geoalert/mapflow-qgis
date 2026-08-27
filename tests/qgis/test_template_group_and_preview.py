"""QGIS-tier tests for the template layer-group placement and preview de-duplication
(round-2 feedback 4.1, 4.2, 1):
* T4 — the template group is nested under the Mapflow group from the first call, even when
  the Mapflow group does not exist yet (previously the open path landed in the root and a
  later preview added a second group under the Mapflow group);
* T5 — the search-table 'Preview' cell click is wired through a single connection, so one
  click does not add several preview layers;
* T1 — the AOI is not cloned over a preview inside a template (already shown there)."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from qgis.core import QgsProject

from mapflow.functional.service.preview_service import PreviewService
from mapflow.functional.service.template_service import TemplateService
from mapflow.functional.view.search_view import SearchView


def _service_for_group(project, add_layers_to_group=True):
    settings = MagicMock()
    settings.value.return_value = None  # no custom layerGroup -> falls back to plugin_name
    app_context = SimpleNamespace(project=project, settings=settings, plugin_name="Mapflow")
    return TemplateService(
        app_context=app_context,
        processing_service=MagicMock(),
        result_loader=SimpleNamespace(add_layers_to_group=add_layers_to_group))


def test_template_group_created_under_mapflow_group_when_absent():
    project = QgsProject()
    root = project.layerTreeRoot()
    service = _service_for_group(project)

    group = service.ensure_template_group("T1")

    mapflow_group = root.findGroup("Mapflow")
    assert mapflow_group is not None
    assert mapflow_group.findGroup("T1") is group
    # No stray template group directly at the root (findGroup recurses, so check children).
    assert not any(c.name() == "T1" for c in root.children())


def test_open_then_preview_reuse_the_same_single_group():
    project = QgsProject()
    root = project.layerTreeRoot()
    service = _service_for_group(project)

    open_group = service.ensure_template_group("T1", subgroup_name="AOI: North")
    preview_group = service.ensure_template_group("T1")  # later preview call

    mapflow_group = root.findGroup("Mapflow")
    # Exactly one "T1" group exists, under the Mapflow group.
    assert preview_group is mapflow_group.findGroup("T1")
    assert open_group.parent() is mapflow_group.findGroup("T1")
    assert len([c for c in root.children() if c.name() == "T1"]) == 0
    assert len([c for c in mapflow_group.children() if c.name() == "T1"]) == 1


def test_template_group_falls_back_to_root_when_user_deleted_mapflow_group():
    project = QgsProject()
    root = project.layerTreeRoot()
    service = _service_for_group(project, add_layers_to_group=False)

    group = service.ensure_template_group("T1")

    assert root.findGroup("Mapflow") is None
    assert root.findGroup("T1") is group


def test_finding_a_template_group_creates_nothing():
    """The whole point of the find/ensure split. `find_template_group` is called from paths
    that fire on every AOI selection and every preview click; if it created the group as a
    side effect, opening a template and clicking around would conjure groups the user never
    asked for — which is why those callers previously had to defer it behind a lambda."""
    project = QgsProject()
    root = project.layerTreeRoot()
    service = _service_for_group(project)

    assert service.find_template_group("T1") is None
    assert service.find_template_group("T1", subgroup_name="AOI: North") is None

    assert root.findGroup("Mapflow") is None
    assert not any(child.name() == "T1" for child in root.children())


def test_finding_a_template_group_returns_the_one_ensure_made():
    project = QgsProject()
    service = _service_for_group(project)

    created = service.ensure_template_group("T1", subgroup_name="AOI: North")

    assert service.find_template_group("T1") is created.parent()
    assert service.find_template_group("T1", subgroup_name="AOI: North") is created


def _search_view():
    """The Preview-cell reconnect is `SearchView.connect_cell_preview` since the search
    extraction — the connection lifecycle it manages is the view's dlg, not the plugin's."""
    return SearchView(dlg=MagicMock(), config=MagicMock())


def test_reconnect_cell_preview_disconnects_previous_first():
    view = _search_view()
    view._cell_preview_connection = object()  # a prior connection exists
    handler = object()

    view.connect_cell_preview(handler)

    view.dlg.metadataTable.disconnect.assert_called_once()
    view.dlg.metadataTable.cellClicked.connect.assert_called_once_with(handler)


def test_reconnect_cell_preview_first_time_no_disconnect_error():
    view = _search_view()
    # No prior connection: disconnect raises, must be swallowed.
    view.dlg.metadataTable.disconnect.side_effect = TypeError

    view.connect_cell_preview(object())

    view.dlg.metadataTable.cellClicked.connect.assert_called_once()


def _preview_service(in_template_mode):
    """T1 moved to `PreviewService` with the rest of the preview code; the reconnect above is
    still `mapflow.py`, because it manages a search-table signal."""
    return PreviewService(
        iface=MagicMock(),
        app_context=SimpleNamespace(project=MagicMock()),
        http=MagicMock(),
        plugin_dir="",
        config=MagicMock(),
        result_loader=MagicMock(),
        processing_service=SimpleNamespace(in_template_mode=in_template_mode,
                                           active_template=None))


def test_add_aoi_to_preview_skipped_in_template_mode():
    service = _preview_service(in_template_mode=True)

    service._add_aoi_to_preview_if_needed()

    service.result_loader.add_aoi_to_preview.assert_not_called()


def test_add_aoi_to_preview_runs_outside_template_mode():
    service = _preview_service(in_template_mode=False)

    service._add_aoi_to_preview_if_needed()

    service.result_loader.add_aoi_to_preview.assert_called_once()
