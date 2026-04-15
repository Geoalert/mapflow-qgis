# SAM Interactive Backend API

Plugin-side specification for the SAM Interactive debug interface.

## Overview

The SAM Interactive backend provides an API for interactive segmentation using SAM3 models.
It shares the same base URL and authentication as the main Mapflow API (`config.SERVER`).

## Endpoints

### Processing Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/processings` | Create a SAM interactive processing |
| GET | `/processings/page` | List processings (paginated) |
| GET | `/processings/{id}` | Get processing detail |
| GET | `/processings/{id}/workflows` | List workflows for a processing |
| GET | `/processings/{id}/sessions` | List sessions for a processing |
| GET | `/processings/{id}/results` | List results for a processing |
| GET | `/workflows/{id}` | Get workflow detail |

### Prompt Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/prompts` | Create a prompt (with optional text) |
| GET | `/prompts/page` | List prompts (paginated) |
| GET | `/prompts/{id}` | Get prompt detail (includes point/bbox prompts) |
| POST | `/prompts/{id}/point_prompts` | Add a point prompt to a prompt |
| POST | `/prompts/{id}/bbox_prompts` | Add a bbox prompt to a prompt |

### Session Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/sessions` | Create a session (processing + prompt) |
| GET | `/sessions/{id}` | Get session detail (includes inferences) |
| GET | `/sessions/{id}/prompts` | Get frozen prompt snapshot for a session |
| POST | `/sessions/{id}/copy` | Copy a session |
| POST | `/sessions/{id}/inferences` | Create an inference for an existing session |

### Inference Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/inference` | Create a new session and the first inference |
| GET | `/inference/{id}` | Get inference status |

### Result Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/result/{session_id}` | Get session result (GeoJSON) |

## Request/Response Schemas

### ProcessingCreateRequest
```json
{
  "name": "string (1-512)",
  "projectId": "string",
  "promptId": "UUID | null",
  "text_prompt": "string | null",
  "confidence_threshold": "float | null",
  "geometry": "GeoJSON",
  "params": {"sourceParams": {}, "inferenceParams": {}},
  "description": "string | null",
  "meta": "object | null"
}
```
- `promptId` and `text_prompt` are mutually exclusive.
- `confidence_threshold` is optional and SAM-specific; when provided it must be a float in the `[0, 1]` range.

### InferenceCreateRequest
```json
{
  "prompt_id": "UUID",
  "workflow_id": "UUID",
  "geometry": "GeoJSON",
  "confidence_threshold": "float | null"
}
```
- `confidence_threshold` is optional and SAM-specific; when provided it must be a float in the `[0, 1]` range.

### SessionInferenceCreateRequest
```json
{
  "workflow_id": "UUID",
  "geometry": "GeoJSON",
  "confidence_threshold": "float | null"
}
```
- `confidence_threshold` is optional and SAM-specific; when provided it must be a float in the `[0, 1]` range.

### ProcessingSummaryResponse
```json
{"id": "UUID", "name": "string", "status": "string", "embedding_uri": "string|null", "created_at": "datetime", "updated_at": "datetime"}
```

### ProcessingDetailResponse
Extends ProcessingSummaryResponse with `"sessions": ["UUID"]`.

### ProcessingListResponse
```json
{"total": 0, "limit": 20, "offset": 0, "items": [ProcessingSummaryResponse]}
```

### MapflowProcessingResponse
```json
{"id": "UUID", "name": "string", "status": "string", "percentCompleted": 0, "cost": "float|null", "created": "datetime"}
```

### WorkflowSummaryResponse
```json
{"id": "UUID", "external_id": "int|null", "geometry": "GeoJSON|null", "raw_raster_uri": "string|null", "embedding_uri": "string|null", "processing_id": "UUID", "status": "string"}
```

### PromptResponse
```json
{"id": "UUID", "text_prompt_id": "UUID|null", "text_prompt": "string|null"}
```

### PromptDetailResponse
Extends PromptResponse with `"point_prompts": [PointPromptResponse]`, `"bbox_prompts": [BboxPromptResponse]`.

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

## Pagination

Paginated endpoints accept query parameters:
- `filter`: string filter
- `limit`: page size (default 20)
- `offset`: offset for pagination

## Authentication

Same as main Mapflow API — Basic Auth or OAuth2 via the shared `Http` instance.

## Error Handling

Standard HTTP error codes. The plugin displays errors in the debug output panel.
- 4xx: client errors (validation, not found, etc.)
- 5xx: server errors
