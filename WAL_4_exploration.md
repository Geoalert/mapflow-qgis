# WAL Step 4: SAM Interactive Debug Interface — Exploration Findings

## SAM Interactive Backend API Reference

Base URL: same as existing mapflow API (`https://whitemaps-{env}.mapflow.ai/rest`)
Auth: same as existing mapflow API (Basic/OAuth2 via Http class)
API_PREFIX on backend: configurable via env var (default: empty)

### Processing Endpoints

| Method | Path | Request | Response |
|--------|------|---------|----------|
| POST | `/processings` | `ProcessingCreateRequest` | `MapflowProcessingResponse` (201) |
| GET | `/processings/page?filter=&limit=&offset=` | query params | `ProcessingListResponse` |
| GET | `/processings/{id}` | - | `ProcessingDetailResponse` |
| GET | `/processings/{id}/workflows` | - | `WorkflowListResponse` |
| GET | `/processings/{id}/sessions` | - | `SessionListResponse` |
| GET | `/processings/{id}/results` | - | `ResultListResponse` |
| GET | `/workflows/{id}` | - | `WorkflowSummaryResponse` |

### Prompt Endpoints

| Method | Path | Request | Response |
|--------|------|---------|----------|
| POST | `/prompts` | `{text_prompt: str\|null}` | `PromptResponse` (201) |
| GET | `/prompts/page?filter=&limit=&offset=` | query params | `PromptListResponse` |
| GET | `/prompts/{id}` | - | `PromptDetailResponse` (includes point_prompts, bbox_prompts) |
| POST | `/prompts/{id}/point_prompts` | `{processing_id, geometry: GeoJSON Point, positive: bool}` | `PointPromptResponse` (201) |
| POST | `/prompts/{id}/bbox_prompts` | `{processing_id, geometry: GeoJSON Polygon, positive: bool}` | `BboxPromptResponse` (201) |

### Session Endpoints

| Method | Path | Request | Response |
|--------|------|---------|----------|
| POST | `/sessions` | `{processing_id, prompt_id}` | `SessionResponse` (201) |
| GET | `/sessions/{id}` | - | `SessionResponse` (includes inferences, layer_id, tile_url) |
| POST | `/sessions/{id}/copy` | - | `SessionResponse` (201) |

### Inference Endpoints

| Method | Path | Request | Response |
|--------|------|---------|----------|
| POST | `/inference` | `{session_id, workflow_id, geometry: GeoJSON}` | `InferenceResponse` (201) |
| GET | `/inference/{id}` | - | `InferenceResponse` |

### Result Endpoints

| Method | Path | Request | Response |
|--------|------|---------|----------|
| GET | `/result/{session_id}` | - | `ResultResponse` or 204 |

---

## Response Schemas (from backend Pydantic models)

### ProcessingCreateRequest
```json
{
  "name": "string (1-512)",
  "projectId": "string",
  "promptId": "UUID | null",       // mutually exclusive with prompt
  "prompt": "string | null",        // mutually exclusive with promptId
  "geometry": "GeoJSON",
  "params": {"sourceParams": {...}, "inferenceParams": {...}},
  "description": "string | null",
  "meta": "object | null"
}
```

### MapflowProcessingResponse
```json
{"id": "UUID", "name": "string", "status": "string", "percentCompleted": 0, "cost": "float|null", "created": "datetime"}
```

### ProcessingSummaryResponse
```json
{"id": "UUID", "name": "string", "status": "string", "embedding_uri": "string|null", "created_at": "datetime", "updated_at": "datetime"}
```

### ProcessingDetailResponse (extends Summary)
```json
{...summary, "sessions": ["UUID"]}
```

### ProcessingListResponse
```json
{"total": 0, "limit": 20, "offset": 0, "items": [ProcessingSummaryResponse]}
```

### WorkflowSummaryResponse
```json
{"id": "UUID", "external_id": "int|null", "geometry": "GeoJSON|null", "raw_raster_uri": "string|null", "embedding_uri": "string|null", "processing_id": "UUID", "status": "string"}
```

### PromptResponse
```json
{"id": "UUID", "text_prompt_id": "UUID|null", "text_prompt": "string|null"}
```

### PromptDetailResponse (extends PromptResponse)
```json
{...prompt, "point_prompts": [PointPromptResponse], "bbox_prompts": [BboxPromptResponse]}
```

### PointPromptResponse / BboxPromptResponse
```json
{"id": "UUID", "processing_id": "UUID", "embedding_uri": "string|null", "geometry": "GeoJSON|null", "positive": true}
```

### SessionResponse
```json
{"id": "UUID", "processing_id": "UUID", "prompt_id": "UUID", "inferences": [InferenceStatusSummary], "layer_id": "UUID", "tile_url": "string"}
```

### InferenceResponse
```json
{"id": "UUID", "session_id": "UUID", "status": "in_progress|done|error", "geometry": "GeoJSON|null", "we_workflow_id": "int|null", "we_workflow_status": "string|null", "created_at": "datetime", "updated_at": "datetime"}
```

### ResultResponse
```json
{"id": "UUID", "geometry": "GeoJSON|null", "layer_id": "UUID|null", "processing_id": "UUID|null", "session_id": "UUID|null"}
```

---

## Existing Plugin Architecture (mapflow-qgis)

### File Locations
- UI files: `mapflow/dialogs/static/ui/*.ui`
- Dialog classes: `mapflow/dialogs/*.py`
- API clients: `mapflow/functional/api/*.py`
- Controllers: `mapflow/functional/controller/*.py`
- Views: `mapflow/functional/view/*.py`
- Services: `mapflow/functional/service/*.py`
- HTTP client: `mapflow/http.py` (wraps QgsNetworkAccessManager)
- Config: `mapflow/config.py` (Config dataclass, base URLs)
- Main plugin: `mapflow/mapflow.py`

### Tab Structure (main_dialog.ui)
- Tab 0: processingsTab (processing icon)
- Tab 1: providersTab (lens icon)
- Tab 2: catalogTab (images icon)
- Tab 3: settingsTab (user_gear icon)
- Tab 4: helpTab (info icon)
- **Tab 5 (new): samTab** — SAM Interactive debug tab

### HTTP Client Pattern
```python
class ProjectApi(QObject):
    def __init__(self, http: Http, server: str):
        self.server = server
        self.http = http

    def create_project(self, project, callback):
        self.http.post(url=f"{self.server}/projects",
                       body=project.as_json().encode(),
                       callback=callback, ...)
```
- All requests async via Qt signal/slot
- Auth handled automatically by Http.authorize()
- Callbacks receive QNetworkReply

### Map Interaction Patterns
- AOI creation: `QgsVectorLayer('Polygon?crs=epsg:4326', name, 'memory')` + editing mode
- No custom QgsMapTool subclasses in existing code
- Layer styles from `static/styles/*.qml`
- Layers added via `QgsProject.instance().addMapLayer(layer)`

### Processing Creation Flow (existing)
Located in `mapflow/mapflow.py`:
- User fills form in processingsTab: name, polygon layer, source combo, model combo, zoom
- Calls existing Mapflow API POST /projects/{pid}/processings
- Processing table auto-refreshes on timer

### Key Design Decisions for SAM Integration
1. Reuse existing Http instance (same auth)
2. Reuse existing processing creation UI, add "Create SAM3 Interactive" button
3. New tab only for SAM-specific: prompts, sessions, inference, results
4. Base URL = same `config.SERVER`
5. Processing results via existing Mapflow result API
6. Session results via SAM backend /result/{session_id}
