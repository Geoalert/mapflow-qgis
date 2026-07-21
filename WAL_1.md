# WAL_1 — See & edit template AOIs ("one step to the right")

Handover for WAL step 1 sub-feature `feature/see-template-aois`.
Spec: `spec/002_F_plan_processing_api.md` (AOI mgmt + in-template navigation sections,
added in this branch). Backend confirmation done against `../white-maps-backend`.

## Scope (agreed with user)
- Parse AOI names from the API (`aoiDetails` feature `properties.name`).
- Send AOI names when **creating a template** from a layer with a `name` attribute;
  absent attribute → `null` name, renamable later.
- Double-click / forward = enter template (level 3). Back = leave template.
- In-template: same table shows template **AOIs** + **processings** with statuses.
- Map: template group gets AOIs (blue transparent) and processings' AOIs
  (green transparent) as separate layers; layers removed on navigate-back.
- Rename/add/delete AOI via right-click (table stays `NoEditTriggers`).
- S7: selecting an AOI filters search results (table + footprint layer) by intersection.
- Out of scope (next PR): named AOIs on regular (non-template) processing creation.

## Confirmed backend facts
- Create reads names from `searchParams.aoiDetails` features as `InputAoiProperties{id,name}`
  (`ProcessingTemplateService.scala:153`). Name max length **64**.
- `aoiDetails` feature props = `TemplateAoiProperties{id?, name?, processings:[AoiProcessingInfo], hasNewImages}`.
  `AoiProcessingInfo{processingId, processingName, processingStatus, area, geometry, projectId}`.
- AOI mgmt endpoints: `POST/DELETE /processings/template/{id}/aoi`,
  `PUT /processings/template/{id}/aoi/{aoiId}` (`ProcessingResource.scala:598-671`).
- Processings list: `GET /processings/template/{id}/processings` (full DTOs) — already
  has unused client method `ProcessingApi.get_template_processings`.
- AOI ids only guaranteed after re-fetch (`GET /template/{id}`); refetch-on-enter is fine.

## Implementation steps

### A. Schema & API client  (`schema/processing.py`, `api/processing_api.py`)
1. `AoiProcessingLink` dataclass: processingId, processingName, processingStatus, area, geometry, projectId.
2. `TemplateAoiDTO` dataclass:
   - fields: `id: Optional[UUID]`, `name: Optional[str]`, `processings: List[AoiProcessingLink]`,
     `hasNewImages: bool`, `geometry: Mapping` (feature geometry).
   - classmethod `from_feature(feature: dict)` reading `properties`.
   - `aoi_area` via existing `geojson_feature_area_sqkm`.
   - `table_status` (e.g. "AOI", or "AOI (new)" when hasNewImages, or count of processings).
   - `as_processing_table_dict()` matching `config.PROCESSING_TABLE_COLUMNS` keys
     (name→display name or "(unnamed)", workflowDef→"AOI", status, aoiArea, id, others N/A).
   - `is_aoi` property = True (mirror `ProcessingTemplateDTO.is_template`).
3. Helper on `ProcessingTemplateDTO`: `aoi_dtos() -> List[TemplateAoiDTO]` from `_aoi_features()`.
4. API client methods:
   - `update_aoi(template_id, aoi_id, data, callback, error_handler)` → PUT `.../aoi/{aoiId}`.
   - `add_aois(template_id, data, callback, error_handler)` → POST `.../aoi`.
   - `delete_aois(template_id, aoi_ids, callback, error_handler)` → DELETE `.../aoi`.
   - New schemas: `UpdateAoiSchema{name?, geometry?}`, `AddAoisSchema`, `DeleteAoisSchema{aoiIds}`.

### B. Named-AOI create  (`mapflow.py: create_search_template`, ~1366)
5. Build `aoiDetails` FeatureCollection from the AOI source features: one Feature per
   feature, `properties.name` from layer `name` attribute if present (trim, validate ≤64),
   else omit/`null`. Keep `aoi` combined geometry as fallback. Validate names client-side.
6. `SearchParams` already has `aoiDetails` field — populate it.

### C. Navigation level  (`processing_controller.py`, `project_view.py`, `app_context.py`)
7. Introduce a nav level state (enum or int) in app_context: PROJECTS/PROCESSINGS/TEMPLATE.
   `stackedProjectsWidget` keeps 0/1; TEMPLATE reuses the processings page (index 1) with a
   `processing_service.in_template_mode` flag + `active_template` ref.
8. Back button (`switchProjectsButton`/left): if in TEMPLATE → exit template (clear flag,
   remove template layer group, repopulate project processings); else existing projects nav.
9. Forward into template: from `_open_template` (double-click) and a forward affordance when a
   template row is selected. Set `in_template_mode`, store template, fetch processings +
   hydrate AOIs, render combined rows.
10. Tab text / breadcrumb: set processings tab text to template name in TEMPLATE level.
11. Poll scoping: while in TEMPLATE, poll template processings, not the project list.

### D. In-template table  (`processing_service.py`, `processing_view.py`)
12. `combined_processing_rows()` (or a new `template_rows()`): when `in_template_mode`,
    return `aoi_dtos + template_processings` (sorted), else current behavior.
13. `get_template_processings` callback stores DTOs; render combined rows.
14. `create_table_items`: handle `TemplateAoiDTO` row type (distinct color, tooltip).
15. `_sort_key`, selection helpers: add AOI branch; add `selected_aoi()/selected_aois()`.
16. Double-click on AOI row: zoom to / select its map layer (no result load).

### E. Map layers  (`mapflow.py: select_template_processings`, `_add_geojson_aoi_layer`)
17. AOI layer style: blue transparent fill; processings' AOIs: green transparent. Use/extend
    `aoi.qml` / `aoi_templates_processing.qml` (confirm colors) — separate layers in template group.
18. On navigate-back, remove the template's layer group (`_template_group_target`) from project.

### F. AOI intersection filter (S7)  (`mapflow.py: show_template_search_results`)
19. When an AOI row is selected, pass that AOI's `id` (single) as `aoiIds` to
    `get_template_images`; also filter the footprint layer features to those intersecting the
    selected AOI geometry (client-side) so table + layer agree.

### G. Rename/add/delete AOI  (`mapflow.py`, `main_dialog.py`, `processing_service.py`)
20. Context menu in TEMPLATE level for AOI rows: "Rename AOI" (QInputDialog, validate ≤64) →
    `update_aoi`; "Delete AOI" → `delete_aois`; "Add AOI" (from selected layer/feature) → `add_aois`.
    Disable rename/delete when AOI has no `id`. Refetch template after each.
21. Keep `processingsTable` `NoEditTriggers`.

### H. Tests  (`tests/qgis/`)  — spec-driven per AGENTS.md
- `test_template_aoi_parse.py`: `aoiDetails` → `TemplateAoiDTO` (name, processings, hasNewImages, area).
- `test_template_named_aoi_create.py`: create payload includes `aoiDetails` names from layer attr; null when absent; 64-char validation.
- `test_template_navigation.py`: enter/leave template toggles mode + rows + layer group.
- `test_template_aoi_rename.py`: rename calls `update_aoi` with right path/body; disabled w/o id.
- `test_template_aoi_search_filter.py`: selecting AOI passes `aoiIds` + filters footprints.
Run: `agent-make test` then `agent-make lint`.

## Discoveries / risks
- One table now holds 3 row types (template / processing / AOI): audit every
  `selected_processing*` / `selected_template*` / `_sort_key` / context-menu / double-click
  branch so AOI rows never get treated as processings (delete/restart/duplicate).
- `aoiDetails` may be absent on project-list templates (omits searchParams) → hydrate via
  `GET /template/{id}` on enter (already done by `_template_hydrated_callback`).
- Removing the template layer group must not remove the persistent Mapflow group.
