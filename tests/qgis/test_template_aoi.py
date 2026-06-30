"""QGIS-tier tests for template AOIs: parsing names/processings from aoiDetails,
the in-template table rows, AOI rename, and AOI-filtered search (spec 002_F)."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.functional.service import processing_service as ps_mod
from mapflow.functional.service.processing_service import ProcessingService
from mapflow.mapflow import Mapflow
from mapflow.schema.processing import ProcessingParams
from mapflow.schema.template import (
    AOI_NAME_MAX_LENGTH,
    ProcessingTemplateDTO,
    TemplateAoiDTO,
    UpdateAoiSchema,
)


def test_refresh_template_view_polls_only_processings():
    """The poll tick must be a single /processings request, not get_template + processings."""
    service = ProcessingService.__new__(ProcessingService)
    service.active_template = SimpleNamespace(id="t-1")
    service.api = MagicMock()

    service.refresh_template_view()

    service.api.get_template_processings.assert_called_once()
    service.api.get_template.assert_not_called()


def test_sync_aoi_statuses_from_processings_refreshes_aoi_status():
    """AOI status stays current from the polled processings without re-fetching the template."""
    from mapflow.schema.status import ProcessingStatus
    service = ProcessingService.__new__(ProcessingService)
    aoi = TemplateAoiDTO.from_feature(
        _aoi_feature(processings=[{"processingId": "p1", "processingStatus": "OK"}])
    )
    service.template_aois = {aoi.table_id: aoi}
    service.template_processings = {"p1": SimpleNamespace(status=ProcessingStatus("FAILED"))}

    service._sync_aoi_statuses_from_processings()

    assert aoi.processings[0].processingStatus == "FAILED"
    assert aoi.table_status == "Failed (0/1)"


def test_update_processing_table_blocks_signals_during_render():
    """The programmatic table rebuild must not emit selection signals (which would re-run
    the AOI search filter / map rebuild every poll)."""
    from mapflow.functional.view.processing_view import ProcessingView
    view = ProcessingView.__new__(ProcessingView)
    view._header_sort_by = None
    view.dlg = MagicMock()
    view.selected_processing_ids = MagicMock(return_value=[])

    view.update_processing_table([])

    block_calls = [c.args for c in view.dlg.processingsTable.blockSignals.call_args_list]
    assert (True,) in block_calls and (False,) in block_calls


def _aoi_feature(aoi_id="aoi-1", name="North field", processings=None, has_new=False):
    return {
        "type": "Feature",
        "id": aoi_id,
        "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]},
        "properties": {
            "id": aoi_id,
            "name": name,
            "processings": processings or [],
            "hasNewImages": has_new,
        },
    }


def test_template_aoi_dto_parses_name_and_processings():
    feature = _aoi_feature(
        name="North field",
        processings=[{
            "processingId": "p-1",
            "processingName": "Run 1",
            "processingStatus": "OK",
            "area": 123,
            "projectId": "proj-1",
        }],
        has_new=True,
    )
    aoi = TemplateAoiDTO.from_feature(feature)
    assert aoi.id == "aoi-1"
    assert aoi.name == "North field"
    assert aoi.hasNewImages is True
    assert len(aoi.processings) == 1
    assert aoi.processings[0].processingName == "Run 1"
    assert aoi.can_rename is True


def test_template_aoi_dto_null_name_is_unnamed_and_not_renamable_without_id():
    feature = {
        "type": "Feature",
        "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 1], [0, 0]]]},
        "properties": {"name": None},
    }
    aoi = TemplateAoiDTO.from_feature(feature)
    assert aoi.name is None
    assert aoi.display_name == "(unnamed)"
    # No id -> cannot rename/delete via the per-AOI endpoint.
    assert aoi.can_rename is False
    # A synthetic table id is still assigned so the row is selectable.
    assert aoi.table_id


def test_template_aoi_table_dict_keys_match_processing_columns():
    aoi = TemplateAoiDTO.from_feature(_aoi_feature())
    row = aoi.as_processing_table_dict()
    assert row["name"] == "North field"
    assert row["workflowDef"] == "AOI"
    assert row["id"] == "aoi-1"


def _template_with_aois(features):
    return ProcessingTemplateDTO.from_dict({
        "id": "t-1",
        "name": "T1",
        "status": "READY",
        "createdAt": "2025-09-26T06:25:55.820336Z",
        "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "searchParams": {"aoiDetails": {"type": "FeatureCollection", "features": features}},
        "projectId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "activeUntil": "2026-03-15T17:00:00Z",
    })


def test_template_dto_aoi_dtos():
    template = _template_with_aois([_aoi_feature("a1", "A"), _aoi_feature("a2", "B")])
    aois = template.aoi_dtos()
    assert {a.name for a in aois} == {"A", "B"}


def test_combined_template_rows_groups_processings_under_their_aoi():
    """Grouped layout: AOI row, then its processings, then the next AOI."""
    service = ProcessingService.__new__(ProcessingService)
    aoi1 = TemplateAoiDTO.from_feature(_aoi_feature(
        "a1", "Alpha",
        processings=[
            {"processingId": "p1", "processingName": "P1", "processingStatus": "OK"},
            {"processingId": "p2", "processingName": "P2", "processingStatus": "OK"},
        ],
    ))
    aoi2 = TemplateAoiDTO.from_feature(_aoi_feature("a2", "Beta", processings=[]))
    service.template_aois = {aoi1.table_id: aoi1, aoi2.table_id: aoi2}
    service.template_processings = {}  # full processings not loaded -> link fallback

    rows = service.combined_template_rows()

    assert rows[0] is aoi1
    assert [r.processingName for r in rows[1:3]] == ["P1", "P2"]
    assert rows[3] is aoi2
    # Every row must expose `.id` — update_processing_table uses it for selection restore.
    assert [r.id for r in rows[1:3]] == ["p1", "p2"]
    assert all(hasattr(r, "id") for r in rows)


def test_get_template_processings_callback_keeps_full_processings(monkeypatch):
    """The v1 /processings list is parsed into TemplateProcessingSchema, keyed by id,
    for double-click loading (grouped display itself comes from aoiDetails)."""
    service = ProcessingService.__new__(ProcessingService)

    sentinel = SimpleNamespace(id="p-1")
    monkeypatch.setattr(ps_mod.TemplateProcessingSchema, "from_dict", staticmethod(lambda d: sentinel))

    response = MagicMock()
    response.readAll.return_value.data.return_value = b'[{"id":"p-1"}]'

    service.get_template_processings_callback(response)

    assert service.template_processings == {"p-1": sentinel}


def test_rename_aoi_calls_update_aoi_endpoint(monkeypatch):
    service = ProcessingService.__new__(ProcessingService)
    service.tr = lambda text: text
    service.dlg = MagicMock()
    service.api = MagicMock()
    aoi = TemplateAoiDTO.from_feature(_aoi_feature("aoi-1", "Old"))
    service.selected_aoi = MagicMock(return_value=aoi)
    service.active_template = SimpleNamespace(id="t-1")

    monkeypatch.setattr(ps_mod.QInputDialog, "getText", lambda *args, **kwargs: ("New name", True))

    service.rename_aoi()

    service.api.update_aoi.assert_called_once()
    kwargs = service.api.update_aoi.call_args.kwargs
    assert kwargs["template_id"] == "t-1"
    assert kwargs["aoi_id"] == "aoi-1"
    assert isinstance(kwargs["data"], UpdateAoiSchema)
    assert kwargs["data"].name == "New name"


def test_rename_aoi_rejects_overlong_name(monkeypatch):
    service = ProcessingService.__new__(ProcessingService)
    service.tr = lambda text: text
    service.dlg = MagicMock()
    service.api = MagicMock()
    aoi = TemplateAoiDTO.from_feature(_aoi_feature("aoi-1", "Old"))
    service.selected_aoi = MagicMock(return_value=aoi)
    service.active_template = SimpleNamespace(id="t-1")
    alerts = []
    monkeypatch.setattr(ps_mod, "alert", lambda *a, **k: alerts.append(a))
    monkeypatch.setattr(
        ps_mod.QInputDialog, "getText",
        lambda *args, **kwargs: ("x" * (AOI_NAME_MAX_LENGTH + 1), True),
    )

    service.rename_aoi()

    service.api.update_aoi.assert_not_called()
    assert alerts  # user was warned


def test_filter_search_by_selected_aoi_passes_single_aoi_id():
    plugin = Mapflow.__new__(Mapflow)
    plugin.processing_service = MagicMock()
    plugin.processing_service.in_template_mode = True
    template = SimpleNamespace(id="t-1")
    plugin.processing_service.active_template = template
    plugin.processing_service.selected_aoi.return_value = SimpleNamespace(id="aoi-1")
    plugin._load_template_search = MagicMock()

    plugin.filter_search_by_selected_aoi()

    plugin._load_template_search.assert_called_once_with(template, aoi_ids=["aoi-1"])


def test_filter_search_resets_to_all_when_aoi_deselected():
    """De-selecting the AOI (or selecting a processing) restores the full template results."""
    plugin = Mapflow.__new__(Mapflow)
    plugin.processing_service = MagicMock()
    plugin.processing_service.in_template_mode = True
    template = SimpleNamespace(id="t-1")
    plugin.processing_service.active_template = template
    plugin.processing_service.selected_aoi.return_value = None
    plugin._template_search_aoi_filter = "aoi-1"  # previously filtered by an AOI
    plugin._load_template_search = MagicMock()

    plugin.filter_search_by_selected_aoi()

    plugin._load_template_search.assert_called_once_with(template, aoi_ids=None)
    assert plugin._template_search_aoi_filter is None


def test_filter_search_noop_when_filter_unchanged():
    """Selection churn that doesn't change the effective AOI filter must not reload."""
    plugin = Mapflow.__new__(Mapflow)
    plugin.processing_service = MagicMock()
    plugin.processing_service.in_template_mode = True
    plugin.processing_service.active_template = SimpleNamespace(id="t-1")
    plugin.processing_service.selected_aoi.return_value = None
    plugin._template_search_aoi_filter = None  # already showing all results
    plugin._load_template_search = MagicMock()

    plugin.filter_search_by_selected_aoi()

    plugin._load_template_search.assert_not_called()


def test_aoi_status_aggregates_processing_statuses():
    ok = {"processingId": "p1", "processingStatus": "OK"}
    in_progress = {"processingId": "p2", "processingStatus": "IN_PROGRESS"}
    failed = {"processingId": "p3", "processingStatus": "FAILED"}

    all_ok = TemplateAoiDTO.from_feature(_aoi_feature(processings=[ok, dict(ok, processingId="p1b")]))
    assert all_ok.table_status == "OK (2)"

    running = TemplateAoiDTO.from_feature(_aoi_feature(processings=[ok, in_progress, failed]))
    assert running.table_status == "In progress (1/3)"

    has_failed = TemplateAoiDTO.from_feature(_aoi_feature(processings=[ok, failed]))
    assert has_failed.table_status == "Failed (1/2)"

    empty = TemplateAoiDTO.from_feature(_aoi_feature(processings=[]))
    assert empty.table_status == "—"


def test_combined_template_rows_appends_unbound_under_no_aoi_separator():
    from mapflow.schema.template import NoAoiProcessingsRow
    service = ProcessingService.__new__(ProcessingService)
    aoi = TemplateAoiDTO.from_feature(_aoi_feature(
        "a1", "Alpha",
        processings=[{"processingId": "p1", "processingName": "P1", "processingStatus": "OK"}],
    ))
    service.template_aois = {aoi.table_id: aoi}
    bound = SimpleNamespace(id="p1", is_final_state=True)
    unbound = SimpleNamespace(id="p9", is_final_state=True)
    service.template_processings = {"p1": bound, "p9": unbound}

    rows = service.combined_template_rows()

    assert rows[0] is aoi
    assert rows[1] is bound  # full processing used in place of the link
    assert isinstance(rows[2], NoAoiProcessingsRow)
    assert rows[3] is unbound


def test_processing_params_legacy_flat_shape_returns_none():
    """The template /processings endpoint returns legacy flat params (no sourceParams);
    parsing must not raise (a raise dropped the whole processing from the list)."""
    legacy = {"url": "1145053", "zoom": "17", "data_provider": "arcgis_world_imagery"}
    assert ProcessingParams.from_dict(legacy) is None


def test_processing_params_v2_shape_still_parses():
    v2 = {"sourceParams": {"dataProvider": {"providerName": "arcgis", "zoom": "17"}}}
    assert ProcessingParams.from_dict(v2) is not None


def test_template_to_run_uses_active_template_in_template_mode():
    """Inside a template there is no selected template row, so the planned-start gate must
    use the active template — otherwise 'Start planned processing' never triggers."""
    from mapflow.entity.provider import ImagerySearchProvider
    service = ProcessingService.__new__(ProcessingService)
    service.in_template_mode = True
    template = SimpleNamespace(id="t-1")
    service.active_template = template
    service.app_context = SimpleNamespace(
        data_provider=ImagerySearchProvider(proxy="https://example"),
        open_template_results_id="t-1",
    )

    assert service.template_to_run() is template


def test_template_to_run_none_when_open_results_belong_to_other_template():
    from mapflow.entity.provider import ImagerySearchProvider
    service = ProcessingService.__new__(ProcessingService)
    service.in_template_mode = True
    service.active_template = SimpleNamespace(id="t-1")
    service.app_context = SimpleNamespace(
        data_provider=ImagerySearchProvider(proxy="https://example"),
        open_template_results_id="other",
    )

    assert service.template_to_run() is None


def test_filter_search_by_selected_aoi_noop_outside_template_mode():
    plugin = Mapflow.__new__(Mapflow)
    plugin.processing_service = MagicMock()
    plugin.processing_service.in_template_mode = False
    plugin._load_template_search = MagicMock()

    plugin.filter_search_by_selected_aoi()

    plugin._load_template_search.assert_not_called()
