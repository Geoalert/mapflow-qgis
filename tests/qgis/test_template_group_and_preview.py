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

from mapflow.mapflow import Mapflow


def _plugin_for_group(project, add_layers_to_group=True):
    plugin = Mapflow.__new__(Mapflow)
    settings = MagicMock()
    settings.value.return_value = None  # no custom layerGroup -> falls back to plugin_name
    plugin.app_context = SimpleNamespace(project=project, settings=settings, plugin_name="Mapflow")
    plugin.result_loader = SimpleNamespace(add_layers_to_group=add_layers_to_group)
    return plugin


def test_template_group_created_under_mapflow_group_when_absent():
    project = QgsProject()
    root = project.layerTreeRoot()
    plugin = _plugin_for_group(project)

    group = plugin._ensure_template_group("T1")

    mapflow_group = root.findGroup("Mapflow")
    assert mapflow_group is not None
    assert mapflow_group.findGroup("T1") is group
    # No stray template group directly at the root (findGroup recurses, so check children).
    assert not any(c.name() == "T1" for c in root.children())


def test_open_then_preview_reuse_the_same_single_group():
    project = QgsProject()
    root = project.layerTreeRoot()
    plugin = _plugin_for_group(project)

    open_group = plugin._ensure_template_group("T1", subgroup_name="AOI: North")
    preview_group = plugin._ensure_template_group("T1")  # later preview call

    mapflow_group = root.findGroup("Mapflow")
    # Exactly one "T1" group exists, under the Mapflow group.
    assert preview_group is mapflow_group.findGroup("T1")
    assert open_group.parent() is mapflow_group.findGroup("T1")
    assert len([c for c in root.children() if c.name() == "T1"]) == 0
    assert len([c for c in mapflow_group.children() if c.name() == "T1"]) == 1


def test_template_group_falls_back_to_root_when_user_deleted_mapflow_group():
    project = QgsProject()
    root = project.layerTreeRoot()
    plugin = _plugin_for_group(project, add_layers_to_group=False)

    group = plugin._ensure_template_group("T1")

    assert root.findGroup("Mapflow") is None
    assert root.findGroup("T1") is group


def test_finding_a_template_group_creates_nothing():
    """The whole point of the find/ensure split. `_find_template_group` is called from paths
    that fire on every AOI selection and every preview click; if it created the group as a
    side effect, opening a template and clicking around would conjure groups the user never
    asked for — which is why those callers previously had to defer it behind a lambda."""
    project = QgsProject()
    root = project.layerTreeRoot()
    plugin = _plugin_for_group(project)

    assert plugin._find_template_group("T1") is None
    assert plugin._find_template_group("T1", subgroup_name="AOI: North") is None

    assert root.findGroup("Mapflow") is None
    assert not any(child.name() == "T1" for child in root.children())


def test_finding_a_template_group_returns_the_one_ensure_made():
    project = QgsProject()
    plugin = _plugin_for_group(project)

    created = plugin._ensure_template_group("T1", subgroup_name="AOI: North")

    assert plugin._find_template_group("T1") is created.parent()
    assert plugin._find_template_group("T1", subgroup_name="AOI: North") is created


def _plugin_for_preview(in_template_mode):
    plugin = Mapflow.__new__(Mapflow)
    plugin.dlg = MagicMock()
    plugin.preview_search_from_cell = MagicMock()
    plugin.result_loader = MagicMock()
    plugin.processing_service = SimpleNamespace(in_template_mode=in_template_mode)
    return plugin


def test_reconnect_cell_preview_disconnects_previous_first():
    plugin = _plugin_for_preview(in_template_mode=False)
    plugin.cell_preview_connection = object()

    plugin._reconnect_cell_preview()

    plugin.dlg.metadataTable.disconnect.assert_called_once()
    plugin.dlg.metadataTable.cellClicked.connect.assert_called_once_with(
        plugin.preview_search_from_cell)


def test_reconnect_cell_preview_first_time_no_disconnect_error():
    plugin = _plugin_for_preview(in_template_mode=False)
    # No prior cell_preview_connection: disconnect raises, must be swallowed.

    plugin._reconnect_cell_preview()

    plugin.dlg.metadataTable.cellClicked.connect.assert_called_once()


def test_add_aoi_to_preview_skipped_in_template_mode():
    plugin = _plugin_for_preview(in_template_mode=True)

    plugin._add_aoi_to_preview_if_needed()

    plugin.result_loader.add_aoi_to_preview.assert_not_called()


def test_add_aoi_to_preview_runs_outside_template_mode():
    plugin = _plugin_for_preview(in_template_mode=False)

    plugin._add_aoi_to_preview_if_needed()

    plugin.result_loader.add_aoi_to_preview.assert_called_once()
