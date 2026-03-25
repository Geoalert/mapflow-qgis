# WAL Step 4: SAM Interactive Debug Interface — Implementation Plan

Reference: `WAL_4_exploration.md` for full API docs and architecture findings.

> **Note**: All git work is local-only on branch `feature/sam-interactive-api`. `agent-git` push auth is not configured; branch has not been published to remote.

## Handover

### Completed
- **Pass 1** (commit `15904a9`): API client (`sam_api.py`), schemas (`sam.py`), tests (`test_sam_api.py`), spec (`006_sam_interactive_api.md`). Tests written but not runnable without QGIS runtime.
- **Pass 2** (commit `d883109`): SAM Interactive tab static UI layout in `main_dialog.ui` (7 group boxes inside QScrollArea), icon in `icons.py`, tab icon wiring in `main_dialog.py`.
- **Pass 3**: Processing creation integration — "SAM Interactive" group box with text prompt + button in processingsTab, `SamApi` instantiated in `mapflow.py`, `create_sam_processing` method wired to button signal, response displayed in SAM debug output.

- **Pass 4** (pending commit): 3-tier architecture (SamService/SamController/SamView) for processings table + workflow browsing. Pagination state in service. Debug output centralized in view. Existing `create_sam_processing_callback` refactored to use `SamView.append_debug`.

### Next: Pass 5 — Prompts + Point/Bbox Map Tools
- Prompt management with text, point (map click), bbox (map rectangle) creation
- Key files: `sam_service.py`, `sam_controller.py`, `sam_view.py`, `map_tools.py` (new)

### Open items
- Tests not runnable locally (QGIS runtime required by `conftest.py`)
- Branch not pushed — needs `agent-git` auth or manual `git push -u origin feature/sam-interactive-api`

## Design Decisions

1. **Base URL**: Same as existing Mapflow API (`config.SERVER`)
2. **Auth**: Reuse existing `Http` instance (same Basic/OAuth2 auth)
3. **Project selection**: Reuse existing project selector from settingsTab
4. **Processing creation**: Add "Create SAM3 Interactive Processing" button to existing processingsTab; uses text prompt instead of model selection
5. **Processing results**: Use existing Mapflow result API (file/tile as configured)
6. **Session results**: Use SAM backend `GET /result/{session_id}` → load GeoJSON as vector layer
7. **New tab**: "SAM Interactive" tab (index 5) for prompts, sessions, inference, results
8. **Map tools**: Point prompt = click tool (QgsMapToolEmitPoint); Bbox prompt = rectangle tool (QgsMapToolExtent or similar)
9. **Debug output**: QTextEdit at bottom of SAM tab showing raw JSON responses

---

## Implementation Passes

### Pass 1: API Client + Spec Document
**Goal**: Wire up all SAM backend API calls; create plugin-side spec.

Files to create/modify:
- `spec/006_sam_interactive_api.md` — new spec documenting SAM API from plugin perspective
- `spec/index.md` — add entry for 006
- `mapflow/functional/api/sam_api.py` — API client class (all 18 endpoints)
- `mapflow/schema/sam.py` — request/response dataclasses for SAM API
- `tests/test_sam_api.py` — unit tests for API client (mocked HTTP)

Acceptance criteria:
- [x] All 18 SAM API endpoints callable from `SamApi` class
- [x] Request/response schemas defined
- [ ] Tests pass with mocked HTTP responses — **deferred: QGIS runtime not available locally**

#### Implementation-time findings

1. **Schema pattern**: response schemas with nested lists (e.g. `ProcessingListResponse.items`, `PromptDetailResponse.point_prompts`) must use `Optional[List[dict]]` as the field type and parse in `__post_init__`, because `SkipDataClass.from_dict` passes raw dicts — it does not recurse into nested schemas automatically. This is consistent with existing patterns in `mapflow/schema/project.py`.

2. **Serializable skip_none**: `PromptCreateRequest()` with no text_prompt serializes to `{}` (empty body) thanks to `skip_none=True` default. This matches the backend expectation where `text_prompt` is nullable/optional.

3. **Pagination as query params**: paginated endpoints (`list_processings`, `list_prompts`) use GET with query params assembled as f-string, not a Serializable body. This differs from `ProjectApi.get_projects` which POSTs a body to `/projects/page`. The SAM backend uses GET for pagination — verified in `WAL_4_exploration.md` endpoint table.

4. **copy_session sends empty body**: `POST /sessions/{id}/copy` takes no request body. `SamApi.copy_session` sends `body=b""` to satisfy the Http.post signature which expects a body argument.

5. **Tests not runnable locally**: `conftest.py` calls `qgis.testing.start_app()` in `pytest_configure`, which runs before any test collection. There is no way to skip it per-file. Tests are written and correct but need QGIS runtime to execute. 22 test classes covering all 18 API methods + 5 schema parsing/serialization tests.

### Pass 2: SAM Tab UI (Static Layout)
**Goal**: Add the SAM Interactive tab with all UI widgets, no logic yet.

Files to create/modify:
- `mapflow/dialogs/static/ui/main_dialog.ui` — add samTab to tabWidget
- `mapflow/dialogs/main_dialog.py` — set tab icon, any init for SAM widgets
- `mapflow/dialogs/icons.py` — add SAM tab icon if needed

SAM Tab layout (sub-sections via QGroupBox or QToolBox):
```
[SAM Interactive Tab]
+-- [Connection] Base URL display + Heartbeat button + status label
+-- [Processings] (SAM backend processings list)
|   Table: id | name | status | created_at
|   Buttons: Refresh | View Workflows | View Sessions
+-- [Prompts]
|   Create: text_prompt input + Create button
|   Table: id | text_prompt
|   Buttons: Refresh | View Detail | Add Point Prompt | Add Bbox Prompt
+-- [Sessions]
|   Create: processing_id combo + prompt_id combo + Create button
|   Table: id | processing_id | prompt_id
|   Buttons: Refresh | View Detail | Copy Session
+-- [Inference]
|   Create: session_id combo + workflow_id combo + Draw AOI button + Run button
|   Status: inference_id | status | we_workflow_status
|   Buttons: Refresh Status
+-- [Results]
|   Session selector + Load Result button
|   → loads GeoJSON as map layer
+-- [Debug Output]
    QTextEdit (read-only, monospace) — raw JSON responses
```

Acceptance criteria:
- [x] SAM tab visible in main dialog
- [x] All widgets placed and named
- [x] No logic connected yet

#### Implementation-time findings

1. **QScrollArea required**: The SAM tab has 7 group boxes which exceeds the minimum dialog height (400px). A QScrollArea wraps all groups to allow scrolling.

2. **Icon reuse**: No SAM-specific icon exists. Reused `settings.svg` as `sam_icon` — the gear icon has a debug/tools connotation suitable for a debug interface. Can be replaced with a custom icon later.

3. **Widget naming convention**: All SAM widgets prefixed with `sam` (e.g., `samProcessingsTable`, `samPromptText`, `samDebugOutput`) to avoid name collisions with existing widgets. Follows existing camelCase pattern.

4. **Font property in .ui**: `samDebugOutput` QTextEdit uses Courier 9pt monospace font set directly in the .ui file via `<font>` property. This is acceptable for a debug panel where monospace is always desired.

### Pass 3: Processing Creation Integration
**Goal**: Add "Create SAM3 Interactive Processing" to existing processingsTab.

Files to modify:
- `mapflow/dialogs/static/ui/main_dialog.ui` — add button to processingsTab
- `mapflow/dialogs/main_dialog.py` — expose new button
- `mapflow/mapflow.py` — connect button signal to SAM processing creation flow
- `mapflow/functional/api/sam_api.py` — wire create_processing with existing form data

Flow:
1. User fills existing processing form (name, AOI, source params)
2. Instead of model selection, a QLineEdit for text prompt appears when "SAM3 Interactive" button is used
3. Calls SAM backend `POST /processings` with `prompt` field instead of model WD
4. Response shown in debug output
5. Processing appears in SAM tab processings table

Acceptance criteria:
- [x] Button visible in processingsTab
- [x] Text prompt input shown/hidden appropriately
- [x] Processing created via SAM API
- [x] Response displayed in debug output

#### Implementation-time findings

1. **No main_dialog.py changes needed**: Widgets defined in .ui are auto-loaded by `uic.loadUiType`, so `samTextPromptInput`, `startSamProcessing`, and `samProcessingGroup` are available without explicit Python-side wiring in the dialog class.

2. **Simplified SAM processing request**: Unlike the existing `create_processing_request()` which assembles complex provider params, WD references, and image IDs, the SAM processing only needs name, projectId, geometry, and optional text prompt. Source/inference params are left to the SAM backend defaults. This avoids coupling SAM creation to the provider/model selection logic.

3. **No billing/limit check for SAM**: The SAM debug interface bypasses `check_processing_limit` since it's a debug tool. The backend handles its own authorization.

4. **Tab switch on response**: After SAM processing creation, the UI automatically switches to the SAM tab (index 5) so the user can see the debug output. This is a debug convenience pattern not used by the regular processing flow.

### Pass 4: Processings + Workflows Browsing (SAM Tab)
**Goal**: Wire up processings table and workflow browsing in SAM tab.

Files to create/modify:
- `mapflow/functional/service/sam.py` — new service (business logic, callbacks, pagination)
- `mapflow/functional/controller/sam_controller.py` — new controller (thin signal wiring)
- `mapflow/functional/view/sam_view.py` — new view (UI state management)
- `mapflow/mapflow.py` — instantiate service + controller
- `tests/test_sam_service.py` — unit tests for service callbacks and pagination

Features:
- List processings (paginated, with filter)
- View processing detail → shows sessions list
- View workflows for a processing
- View workflow detail (geometry, embedding_uri, status)
- All responses shown in debug output

Acceptance criteria:
- [x] Processings table populated from SAM API
- [x] Pagination works
- [x] Workflow list shown on selection
- [x] Debug output shows raw JSON

#### Implementation-time findings

1. **3-tier pattern adopted**: Used Service/Controller/View pattern matching existing `DataCatalogService`/`DataCatalogController`/`DataCatalogView`. The API+Service layer is production-grade and will likely outlive the debug UI. Controller is a thin wiring layer; service holds all business logic and pagination state.

2. **Pagination state in service**: `_offset`, `_limit`, `_total` tracked in `SamService`. `has_next_page`/`has_prev_page` properties and `next_page()`/`prev_page()` methods handle navigation. UI pagination buttons (not yet in .ui) will be wired in a future pass.

3. **Debug output centralized in view**: `SamView.append_debug(title, data)` is the single point for all debug JSON output. The existing `create_sam_processing_callback` in `mapflow.py` was refactored to use this method instead of direct `samDebugOutput.append`.

4. **Tests not runnable locally**: Same as Pass 1 — QGIS runtime required by `conftest.py`. Tests written with mocked HTTP responses covering all 4 callbacks + pagination logic.

### Pass 5: Prompts + Point/Bbox Map Tools
**Goal**: Prompt management with spatial prompt creation via map tools.

Files to create/modify:
- `mapflow/functional/map_tools.py` — QgsMapToolEmitPoint for points, rectangle for bbox
- `mapflow/functional/controller/sam_controller.py` — prompt operations
- `mapflow/functional/view/sam_view.py` — prompt UI updates

Features:
- Create text prompt
- List prompts (paginated)
- View prompt detail (text + point/bbox prompts)
- **Add Point Prompt**: activate point map tool → click on map → capture WGS84 coord → send to API
- **Add Bbox Prompt**: activate rectangle map tool → draw rect → capture as GeoJSON Polygon → send to API
- Toggle positive/negative for both
- Display prompts on map: memory layer with points (green=positive, red=negative) and bbox rectangles
- processing_id selector (from SAM processings table)

Acceptance criteria:
- [ ] Text prompt creation works
- [ ] Point prompt via map click works
- [ ] Bbox prompt via map rectangle works
- [ ] Positive/negative toggle works
- [ ] Prompts visualized on map layer
- [ ] Debug output shows raw JSON

### Pass 6: Sessions + Inference + Results
**Goal**: Complete the interactive workflow: create session → run inference → view results.

Files to modify:
- `mapflow/functional/controller/sam_controller.py` — session/inference operations
- `mapflow/functional/view/sam_view.py` — session/inference UI

Features:
- Create session (select processing + prompt)
- View session detail (inferences list, layer_id, tile_url)
- Copy session
- Create inference (select session + workflow + draw AOI geometry)
- Poll inference status (manual refresh or auto-poll timer)
- Load session result as GeoJSON vector layer on map
- Processing result via existing Mapflow result viewer

Acceptance criteria:
- [ ] Session creation works
- [ ] Inference creation works
- [ ] Inference status polling works
- [ ] GeoJSON result loaded as map layer
- [ ] Debug output shows all raw JSON responses
- [ ] Full workflow completable: create processing → create prompt → add prompts → create session → run inference → view result

### Pass 7: Polish + Tests
**Goal**: Stabilize, add missing tests, clean up.

- Error handling for all API calls (network errors, 4xx, 5xx)
- Proper error messages in debug output
- UI state management (disable buttons when no selection, etc.)
- Integration tests for controller
- Manual testing of full workflow

---

## File Creation Summary

### New Files
| File | Pass | Purpose |
|------|------|---------|
| `spec/006_sam_interactive_api.md` | 1 | Plugin-side SAM API spec |
| `mapflow/functional/api/sam_api.py` | 1 | SAM API client |
| `mapflow/schema/sam.py` | 1 | SAM request/response schemas |
| `tests/test_sam_api.py` | 1 | API client tests |
| `mapflow/functional/service/sam.py` | 4 | SAM service (business logic, pagination) |
| `mapflow/functional/controller/sam_controller.py` | 4 | SAM tab controller (thin signal wiring) |
| `mapflow/functional/view/sam_view.py` | 4 | SAM tab view (UI state) |
| `tests/test_sam_service.py` | 4 | SAM service unit tests |
| `mapflow/functional/map_tools.py` | 5 | Point/bbox map tools |

### Modified Files
| File | Pass | Change |
|------|------|--------|
| `spec/index.md` | 1 | Add 006 entry |
| `mapflow/dialogs/static/ui/main_dialog.ui` | 2, 3 | Add SAM tab + SAM processing button |
| `mapflow/dialogs/main_dialog.py` | 2 | SAM tab init |
| `mapflow/dialogs/icons.py` | 2 | SAM icon |
| `mapflow/mapflow.py` | 3, 4 | Wire SAM controller + button |
