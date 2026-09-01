"""AoiService, the new owner of the AOI layer registry and AOI layer creation.

These behaviours used to live on `Mapflow.add_to_layers` / `remove_from_layers` /
`filter_aoi_layers` / `create_*_aoi_layer`, where they were covered only indirectly. The move
is the moment to pin them: `spec/007_architecture.md` says a step that moves code must not
leave a behaviour covered by neither suite.

What is asserted here is the part that is *not* widget work — the service holds no dialog, so
what a caller can observe is the registry, the signals, and the layers it builds.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from qgis.core import (QgsCoordinateReferenceSystem, QgsFeature, QgsGeometry, QgsProject,
                       QgsRectangle, QgsVectorLayer)

from mapflow.functional.service.aoi_service import AoiService


def _layer(name="layer"):
    return QgsVectorLayer('Polygon?crs=epsg:4326', name, 'memory')


@pytest.fixture
def service(tmp_path):
    project = MagicMock()
    project.mapLayers.return_value = {}
    return AoiService(iface=MagicMock(),
                      app_context=SimpleNamespace(project=project, search_provider=None),
                      plugin_dir=str(tmp_path),
                      result_loader=MagicMock(),
                      data_catalog_service=MagicMock(),
                      processing_service=MagicMock(),
                      template_service=MagicMock())


# ---------- the registry ----------

def test_registering_a_layer_records_it_once(service):
    layer = _layer()
    registered = []
    service.aoiLayerRegistered.connect(registered.append)

    service.register_layer(layer)
    service.register_layer(layer)

    assert service.aoi_layers == [layer]
    # The context-menu action is attached per layer, so a second registration must not re-emit.
    assert registered == [layer]


def test_registering_a_layer_points_the_combo_at_it(service):
    layer = _layer()
    current = []
    service.currentAoiLayerChanged.connect(lambda lyr, notify: current.append((lyr, notify)))

    service.register_layer(layer)

    assert current == [(layer, True)]


def test_bulk_registration_neither_selects_nor_prices(service):
    """Template AOI display layers are added in bulk: the last must not become the Area
    (feedback 8.1), and none of them may fire a cost request."""
    layer = _layer()
    current = []
    service.currentAoiLayerChanged.connect(lambda lyr, notify: current.append((lyr, notify)))

    service.register_layer(layer, recompute_cost=False, set_current=False)

    assert service.aoi_layers == [layer]
    assert current == []


def test_registration_can_select_without_pricing(service):
    layer = _layer()
    current = []
    service.currentAoiLayerChanged.connect(lambda lyr, notify: current.append((lyr, notify)))

    service.register_layer(layer, recompute_cost=False)

    assert current == [(layer, False)]


def test_unregistering_a_layer_drops_it(service):
    layer = _layer()
    service.register_layer(layer)

    service.unregister_layer(layer)

    assert service.aoi_layers == []


def test_unregistering_a_layer_twice_is_not_an_error(service):
    """The per-layer 'Remove AOI' action cannot be taken off a single layer's menu, so it stays
    clickable after the first click."""
    layer = _layer()
    service.register_layer(layer)
    service.unregister_layer(layer)

    changed = []
    service.aoiLayersChanged.connect(lambda: changed.append(1))
    service.unregister_layer(layer)

    assert service.aoi_layers == []
    assert changed == [1]


# ---------- what the AOI combo may not offer ----------

def test_only_non_aoi_layers_are_excepted(service):
    aoi, other = _layer("aoi"), _layer("other")
    service.app_context.project.mapLayers.return_value = {"1": aoi, "2": other}
    service.register_layer(aoi)

    assert service.excepted_layers(use_all_vector_layers=False) == [other]


def test_using_all_vector_layers_excepts_only_search_metadata(service):
    """Search-metadata layers stay excluded even in 'use all layers' mode: they are big and
    crowded, and using one as an AOI produces topology errors."""
    metadata, other = _layer("Provider metadata"), _layer("other")
    service.app_context.project.mapLayers.return_value = {"1": metadata, "2": other}
    service.app_context.search_provider = SimpleNamespace(name="Provider")

    assert service.excepted_layers(use_all_vector_layers=True) == [metadata]


def test_using_all_vector_layers_excepts_nothing_without_a_search_provider(service):
    service.app_context.project.mapLayers.return_value = {"1": _layer("other")}

    assert service.excepted_layers(use_all_vector_layers=True) == []


# ---------- creating AOI layers ----------

def test_a_created_layer_is_registered_and_added_to_the_map(service):
    layer = service.create_editable_layer()

    assert layer in service.aoi_layers
    service.result_loader.add_layer.assert_called_once_with(layer)
    assert layer.isEditable()


def test_created_layers_are_numbered(service):
    first = service.create_editable_layer()
    second = service.create_editable_layer()

    assert (first.name(), second.name()) == ("AOI_0", "AOI_1")


def test_a_layer_from_the_map_extent_carries_the_reprojected_rectangle(service):
    rect = QgsRectangle(0.0, 0.0, 1.0, 1.0)

    layer = service.create_layer_from_rect(rect, QgsCoordinateReferenceSystem("EPSG:4326"))

    geometries = [feature.geometry() for feature in layer.getFeatures()]
    assert len(geometries) == 1
    assert geometries[0].boundingBox() == rect


def test_a_layer_from_imagery_uses_the_selected_images_footprint(service):
    footprint = QgsGeometry.fromWkt("POLYGON((0 0, 0 2, 2 2, 2 0, 0 0))")
    service.data_catalog_service.selected_image.return_value = SimpleNamespace(
        footprint=footprint.asWkt())

    layer = service.create_layer_from_imagery()

    geometries = [feature.geometry() for feature in layer.getFeatures()]
    assert len(geometries) == 1
    assert geometries[0].boundingBox() == footprint.boundingBox()


def test_no_imagery_selected_builds_no_layer(service):
    """The caller explains why instead of adding an empty AOI to the map."""
    service.data_catalog_service.selected_image.return_value = None
    service.data_catalog_service.selected_mosaic.return_value = None

    assert service.create_layer_from_imagery() is None
    assert service.aoi_layers == []
    service.result_loader.add_layer.assert_not_called()


# ---------- the on-map edit session ----------
#
# Moved here from tests/qgis/test_template_updates.py, where they drove
# `Mapflow.__new__(Mapflow)`. The behaviours are unchanged: the service still alerts and still
# prompts for a name where it needs one, because both go through the message tier
# (`alert_*`, `ask_text`), which owns the Qt types so its callers do not have to. The `messages`
# and `prompt` fixtures patch those calls.


def _polygon_layer(wkt="POLYGON((0 0,2 0,2 2,0 2,0 0))", name="aoi"):
    layer = QgsVectorLayer("Polygon?crs=epsg:4326", name, "memory")
    feature = QgsFeature()
    feature.setGeometry(QgsGeometry.fromWkt(wkt))
    layer.dataProvider().addFeatures([feature])
    layer.updateExtents()
    return layer


@pytest.fixture
def session_service(service):
    """`service` with an open template. The AOI endpoints and the poll timer are still
    `ProcessingService`'s; the template itself and the AOI selection are `TemplateService`'s."""
    service.processing_service = SimpleNamespace(
        api=MagicMock(),
        processing_fetch_timer=MagicMock())
    service.template_service = SimpleNamespace(
        selected_aoi=lambda: None,
        active_template=SimpleNamespace(id="tpl-1", name="T1"),
        aoi_changed_callback=MagicMock(),
        aoi_change_error_handler=MagicMock())
    return service


@pytest.fixture
def messages(monkeypatch):
    """Everything the service asked AlertService to show, as (text, severity).

    Patched rather than connected: the service calls `alert_info`/`alert_warning` directly
    (AlertService owns the message tier and is a service, so service->service is the normal
    route), and those go through a process-global singleton that no unit test should raise.
    """
    collected = []
    for name in ("alert_info", "alert_warning"):
        monkeypatch.setattr(
            f"mapflow.functional.service.aoi_service.{name}",
            lambda text, severity=name.removeprefix("alert_"): collected.append((text, severity)))
    return collected


# --- update (edit in place) ---

def test_commit_update_sends_edited_geometry(session_service):
    aoi = SimpleNamespace(id="aoi-1", can_rename=True)

    ok = session_service._commit_update(_polygon_layer(), aoi)

    assert ok is True
    kwargs = session_service.processing_service.api.update_aoi.call_args.kwargs
    assert kwargs["aoi_id"] == "aoi-1"
    assert kwargs["data"].geometry["type"] in ("Polygon", "MultiPolygon")


def test_commit_update_rejects_empty_geometry(session_service, messages):
    aoi = SimpleNamespace(id="aoi-1", can_rename=True)
    empty = QgsVectorLayer("Polygon?crs=epsg:4326", "aoi", "memory")  # no features

    ok = session_service._commit_update(empty, aoi)

    assert ok is False
    session_service.processing_service.api.update_aoi.assert_not_called()
    assert len(messages) == 1 and messages[0][1] == 'warning'


def test_start_update_session_rejects_aoi_without_id(session_service, messages):
    session_service.template_service.selected_aoi = (
        lambda: SimpleNamespace(id=None, can_rename=False))

    session_service.start_update_session()

    assert session_service.session_active is False
    assert len(messages) == 1


def test_start_update_session_needs_the_aoi_layer_on_map(session_service, messages):
    session_service.template_service.selected_aoi = lambda: SimpleNamespace(
        id="aoi-1", can_rename=True, display_name="A1")
    session_service.find_layer_for_aoi = MagicMock(return_value=None)

    session_service.start_update_session()

    assert session_service.session_active is False
    assert len(messages) == 1 and messages[0][1] == 'warning'


def test_start_update_session_begins_when_layer_found(session_service):
    aoi = SimpleNamespace(id="aoi-1", can_rename=True, display_name="A1")
    session_service.template_service.selected_aoi = lambda: aoi
    layer = _polygon_layer()
    session_service.find_layer_for_aoi = MagicMock(return_value=layer)
    started = []
    session_service.editSessionStarted.connect(started.append)

    session_service.start_update_session()

    assert session_service._session["mode"] == "update"
    assert session_service._session["layer"] is layer
    # The panel must be told to get out of the way, and told what the user is now doing.
    assert len(started) == 1 and "A1" in started[0]
    # The vertex tool, not the add-feature tool: this edits an existing polygon.
    session_service.iface.actionAddFeature.assert_not_called()


# --- add from layer (layer selection) ---

def test_selectable_layers_keeps_user_layers_hides_plugin_layers(session_service):
    project = QgsProject()
    root = project.layerTreeRoot()
    # A user's own polygon layer at the root -> selectable.
    user_layer = _polygon_layer(name="My field boundaries")
    project.addMapLayer(user_layer)
    # A user AOI layer that lives directly under the Mapflow group (added via "Use as AOI")
    # must STILL be selectable — hiding the whole group was the bug.
    mapflow_group = root.insertGroup(0, "Mapflow")
    user_aoi = _polygon_layer(name="Saved AOI")
    project.addMapLayer(user_aoi, False)
    mapflow_group.addLayer(user_aoi)
    # The template's own AOI display layer (under Mapflow > T1, and tagged) -> hidden.
    template_group = mapflow_group.insertGroup(0, "T1")
    display_layer = _polygon_layer(name="AOI display")
    display_layer.setCustomProperty("mapflow/aoi_id", "aoi-1")
    project.addMapLayer(display_layer, False)
    template_group.addLayer(display_layer)
    # A tagged display layer that is NOT in the template group — left behind by another
    # template, or by a group the user moved. Tagging must be enough on its own: this is the
    # case that isolates the tag rule, since the layer above is excluded by its group anyway.
    stray_display = _polygon_layer(name="Stray AOI display")
    stray_display.setCustomProperty("mapflow/aoi_id", "aoi-2")
    project.addMapLayer(stray_display)
    # A search-metadata layer -> hidden by name.
    project.addMapLayer(_polygon_layer(name="Mapflow metadata"))

    session_service.app_context = SimpleNamespace(
        project=project, plugin_name="Mapflow",
        settings=SimpleNamespace(value=lambda *a: "Mapflow"), metadata_layer=None)

    names = {layer.name() for layer in session_service.selectable_layers()}

    assert "My field boundaries" in names
    assert "Saved AOI" in names                # user layer under Mapflow group is kept
    assert "AOI display" not in names          # excluded by its template group
    assert "Stray AOI display" not in names    # excluded by its tag alone
    assert "Mapflow metadata" not in names


# --- draw ---

@pytest.fixture
def prompt(monkeypatch):
    """Stands in for the name prompt. `ask_text` belongs to the message tier (alongside
    `alert_confirm`), so the service asks for the name where it uses it rather than being handed
    one by a caller that can see a dialog."""
    asked = MagicMock(return_value=("My AOI", True))
    monkeypatch.setattr("mapflow.functional.service.aoi_service.ask_text", asked)
    return asked


def test_commit_draw_prompts_for_a_name_and_sends_it(session_service, prompt):
    ok = session_service._commit_draw(_polygon_layer())

    assert ok is True
    prompt.assert_called_once()
    data = session_service.processing_service.api.add_aois.call_args.kwargs["data"]
    assert data.aois[0].name == "My AOI"


def test_cancelling_the_name_prompt_keeps_the_session_open(session_service, prompt):
    """Otherwise the drawing is lost the moment the user hesitates over the name."""
    prompt.return_value = ("", False)

    ok = session_service._commit_draw(_polygon_layer())

    assert ok is False
    session_service.processing_service.api.add_aois.assert_not_called()


def test_commit_draw_noop_when_nothing_drawn(session_service, messages, prompt):
    empty = QgsVectorLayer("Polygon?crs=epsg:4326", "draw", "memory")

    ok = session_service._commit_draw(empty)

    assert ok is False
    session_service.processing_service.api.add_aois.assert_not_called()
    assert len(messages) == 1
    prompt.assert_not_called()  # nothing to name


def test_commit_draw_rejects_an_overlong_name(session_service, messages, prompt):
    prompt.return_value = ("x" * 200, True)

    ok = session_service._commit_draw(_polygon_layer())

    assert ok is False  # session stays open so the drawing is not lost
    session_service.processing_service.api.add_aois.assert_not_called()
    assert len(messages) == 1 and messages[0][1] == 'warning'


def test_commit_draw_without_a_name_sends_none(session_service, prompt):
    """An empty prompt is not an empty name — the backend takes null."""
    prompt.return_value = ("", True)

    session_service._commit_draw(_polygon_layer())

    data = session_service.processing_service.api.add_aois.call_args.kwargs["data"]
    assert data.aois[0].name is None


# --- session teardown ---

def test_save_session_ends_only_on_successful_commit(session_service):
    session_service._session = {"mode": "update", "layer": MagicMock(),
                                "aoi": SimpleNamespace(id="a"), "is_temp": False}

    session_service._commit_update = MagicMock(return_value=False)
    assert session_service.save_session() is False
    assert session_service.session_active is True  # validation failed -> stay in session

    session_service._commit_update = MagicMock(return_value=True)
    assert session_service.save_session() is True
    assert session_service.session_active is False


def test_cancel_session_rolls_back_in_place_edit(session_service):
    layer = MagicMock()
    layer.isEditable.return_value = True
    session_service._session = {"mode": "update", "layer": layer, "aoi": None, "is_temp": False,
                                "prev_active_layer": None}

    session_service.cancel_session()

    layer.rollBack.assert_called_once()
    assert session_service.session_active is False


def test_end_session_removes_temp_layer_and_restores_the_panel(session_service):
    project = MagicMock()
    session_service.app_context = SimpleNamespace(project=project)
    layer = MagicMock()
    layer.id.return_value = "temp-1"
    session_service._session = {"mode": "draw", "layer": layer, "aoi": None, "is_temp": True,
                                "prev_active_layer": None}
    ended = []
    session_service.editSessionEnded.connect(lambda: ended.append(True))

    session_service._end_session()

    project.removeMapLayer.assert_called_once_with("temp-1")
    assert ended == [True]
    session_service.processing_service.processing_fetch_timer.start.assert_called_once()
    assert session_service._session is None
