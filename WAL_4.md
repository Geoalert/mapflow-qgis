# WAL Step 4: SAM Interactive Debug Interface — Implementation Plan

Reference: `WAL_4_exploration.md` for full API docs and architecture findings.

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
- [ ] SAM tab visible in main dialog
- [ ] All widgets placed and named
- [ ] No logic connected yet

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
- [ ] Button visible in processingsTab
- [ ] Text prompt input shown/hidden appropriately
- [ ] Processing created via SAM API
- [ ] Response displayed in debug output

### Pass 4: Processings + Workflows Browsing (SAM Tab)
**Goal**: Wire up processings table and workflow browsing in SAM tab.

Files to modify:
- `mapflow/functional/controller/sam_controller.py` — new controller
- `mapflow/functional/view/sam_view.py` — new view for SAM tab
- `mapflow/mapflow.py` — instantiate controller

Features:
- List processings (paginated, with filter)
- View processing detail → shows sessions list
- View workflows for a processing
- View workflow detail (geometry, embedding_uri, status)
- All responses shown in debug output

Acceptance criteria:
- [ ] Processings table populated from SAM API
- [ ] Pagination works
- [ ] Workflow list shown on selection
- [ ] Debug output shows raw JSON

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
| `mapflow/functional/controller/sam_controller.py` | 4 | SAM tab controller |
| `mapflow/functional/view/sam_view.py` | 4 | SAM tab view |
| `mapflow/functional/map_tools.py` | 5 | Point/bbox map tools |

### Modified Files
| File | Pass | Change |
|------|------|--------|
| `spec/index.md` | 1 | Add 006 entry |
| `mapflow/dialogs/static/ui/main_dialog.ui` | 2, 3 | Add SAM tab + SAM processing button |
| `mapflow/dialogs/main_dialog.py` | 2 | SAM tab init |
| `mapflow/dialogs/icons.py` | 2 | SAM icon |
| `mapflow/mapflow.py` | 3, 4 | Wire SAM controller + button |
