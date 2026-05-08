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
| GET | `/processings/page` | List processings (paginated). Supports an optional `projectId` query param that scopes the result to a Mapflow project (any owner). When omitted, the legacy owner-scoped fallback is used. |
| GET | `/processings/{id}` | Get processing detail |
| GET | `/processings/{id}/workflows` | List workflows for a processing |
| GET | `/processings/{id}/sessions` | List sessions for a processing |
| GET | `/processings/{id}/results` | List results for a processing |
| GET | `/workflows/{id}` | Get workflow detail |

### Prompt Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/prompts` | Create a prompt (with optional text) |
| POST | `/prompts/{id}/copy` | Create a copy of an existing prompt (returns the new `PromptDetailResponse`) |
| GET | `/prompts/page` | List prompts (paginated) |
| GET | `/prompts/{id}` | Get prompt detail (includes point/bbox prompts) |
| POST | `/prompts/{id}/point_prompts` | Add a point prompt to a prompt |
| POST | `/prompts/{id}/bbox_prompts` | Add a bbox prompt to a prompt |

### Session Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/sessions/{id}` | Get full session detail — metadata, inferences (with WE refresh + `created_at`), and the frozen prompt snapshot |
| PATCH | `/sessions/{id}` | Rename a session |
| DELETE | `/sessions/{id}` | Archive a session |
| POST | `/sessions/{id}/inferences` | Create an inference batch for an existing session using the session's stored confidence threshold |

`GET /sessions/{id}/prompts` was retired: the frozen prompt snapshot is embedded in `SessionResponse` (see Schemas). On every call, the backend bulk-refreshes WE workflow statuses for non-terminal inferences before responding, so a single `GET /sessions/{id}` is always the freshest view.

Sessions are not created standalone. They are created implicitly by `POST /inference`, which returns the new session containing its initial inference batch.

### Inference Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/inference` | Create a new session and dispatch the first inference batch |
| GET | `/inference/{id}` | Get full inference detail (includes WE workflow status) |

A single `POST /inference` or `POST /sessions/{id}/inferences` request produces N `Inference` rows — one per workflow whose geometry intersects the request AOI — all attached to the same session and sharing one merged result vector layer. Workflows are not exposed as a user-facing concept; the backend selects them automatically.

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
  "processing_id": "UUID",
  "prompt_id": "UUID",
  "geometry": "GeoJSON",
  "confidence_threshold": "float | null"
}
```
- `workflow_id` is no longer required; the backend auto-selects all processing workflows whose geometry intersects the inference AOI.
- `processing_id` identifies the processing whose workflows will be used.
- `confidence_threshold` is optional and SAM-specific; when provided it must be a float in the `[0, 1]` range.
- When provided, `confidence_threshold` is stored on the newly created session and reused by later `POST /sessions/{session_id}/inferences` requests for that session.
- Response body is a `SessionResponse` containing the new session and the N inferences just dispatched (one per intersecting workflow).

### SessionInferenceCreateRequest
```json
{
  "geometry": "GeoJSON"
}
```
- `workflow_id` is no longer required; the backend auto-selects intersecting workflows from the session's processing.
- This endpoint does not accept `confidence_threshold`; it reuses the selected session's stored threshold.
- Response body is a `SessionResponse` reflecting the session after the new inferences have been added.

### ProcessingSummaryResponse
```json
{"id": "UUID", "name": "string", "status": "string", "embedding_uri": "string|null", "created_at": "datetime", "updated_at": "datetime"}
```

### ProcessingDetailResponse
Extends ProcessingSummaryResponse with `"sessions": ["UUID"]`.

### ProcessingListResponse
```json
{"has_more": false, "limit": 20, "offset": 0, "items": [ProcessingSummaryResponse]}
```
- `has_more` replaced the previously-returned `total`. The server skips a `COUNT(*)` over the processings table; clients paginate by `offset + limit` and use `has_more` to decide whether to expose a "next page" affordance.
- A page may legitimately contain fewer than `limit` items even when `has_more=true` — the backend fetches `limit + 1` rows and may drop ones that were confirmed deleted upstream during a per-page sync. The client always advances by `limit`, never by `len(items)`.

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
{"id": "UUID", "name": "string|null", "text_prompt_id": "UUID|null", "text_prompt": "string|null"}
```

### PromptDetailResponse
Extends PromptResponse with `"spatial_prompts": [SpatialPromptResponse]`. Spatial prompts are returned as a single unified array discriminated by `geometry_type` (`"point"` or `"bbox"`).

### PromptCopyRequest
```json
{"name": "string | null", "text_prompt": "string | null"}
```
Body for `POST /prompts/{id}/copy`. Both fields are optional.
- `name` defaults to `"<original.name> (copy)"` when omitted, or `"(copy)"` if the source prompt has no name.
- `text_prompt` — when omitted, `null`, or empty string, the new prompt reuses the source prompt's `text_prompt_id` by FK reuse (no row duplication). Any non-empty string is resolved through the same find-or-create `TextPrompt` path as `POST /prompts`.
- Spatial prompts: junction rows in `prompt_spatial_prompts` are copied to the new prompt id. No new `spatial_prompt` rows are created and no S3 objects are duplicated — this is the same shared-junction model used by the session snapshot (see `003_local_storage.md`).
- Returns `201` with the new `PromptDetailResponse`. Returns `404` when `{id}` is not found or not owned by the caller.

### SpatialPromptResponse
```json
{"id": "UUID", "geometry_type": "point|bbox", "processing_id": "UUID", "embedding_uri": "string|null", "raster_url": "string|null", "geometry": "GeoJSON|null", "positive": true}
```
- `raster_url` is a path to the GeoTIFF preview crop the prompt was created from, **rooted at the `/sam-interactive` base** (the API does not include the server / `/rest/sam-interactive` prefix). The plugin concatenates it with `SamApi.server` before issuing the GET. Replaces the previous `raw_raster_uri` (an `s3://` URI), which the client could not fetch directly. May be `null` for legacy prompts created before the preview pipeline existed.
- The path itself encodes how the backend authorizes the call. When the response came from a session endpoint the URL is `/sessions/{session_id}/spatial_prompts/{sp_id}/raster` (rights derive from the session's processing); when the response came from a prompt endpoint it's the prompt-rooted equivalent (rights derive from prompt ownership). The client must not rewrite the prefix — that would defeat the auth scheme.
- The plugin downloads the GeoTIFF on prompt double-click and attaches it as a raster layer under the `SAM Prompts > SAM Prompt Previews` layer-tree subgroup, replacing whatever previews were attached for the previous prompt.

### SessionResponse
```json
{
  "id": "UUID",
  "processing_id": "UUID",
  "name": "string|null",
  "confidence_threshold": "float|null",
  "text_prompt": {"id": "UUID", "text": "string"} | null,
  "spatial_prompts": [SpatialPromptResponse],
  "inferences": [InferenceStatusSummary],
  "vector_layer": {"id": "UUID", "tile_url": "string", "tile_json_url": "string"} | null
}
```
- `text_prompt` + `spatial_prompts` together form the frozen prompt snapshot; this used to be a separate `GET /sessions/{id}/prompts` call.
- All inferences in the session share the same `vector_layer`. The merged result is rendered by fetching `GET /result/{session_id}`.

### SessionListItem
```json
{
  "id": "UUID",
  "processing_id": "UUID",
  "name": "string|null",
  "inferences_total": 0,
  "inferences_done": 0
}
```
- The `inferences_total` / `inferences_done` aggregates let the sessions list show per-session progress without selecting each row.

### InferenceStatusSummary
```json
{
  "id": "UUID",
  "status": "in_progress|done|error",
  "geometry": "GeoJSON|null",
  "created_at": "datetime"
}
```
- Lightweight per-inference summary returned inside `SessionResponse.inferences`. `geometry` is the per-workflow clipped AOI for that inference.
- WE workflow id/status are deliberately NOT exposed to the user; the abstract `status` is the only signal the UI shows.
- The full `GET /inference/{id}` endpoint stays available for debug.

### InferenceResponse
```json
{"id": "UUID", "session_id": "UUID", "status": "in_progress|done|error", "geometry": "GeoJSON|null", "we_workflow_id": "int|null", "we_workflow_status": "string|null", "created_at": "datetime", "updated_at": "datetime"}
```

### Result
`GET /result/{session_id}` returns:
- `200` with a raw GeoJSON `FeatureCollection` body (the merged session result), or
- `204 No Content` when no result is available yet.

There is no wrapper object — the body is the GeoJSON dict itself.

## Pagination

Paginated endpoints accept query parameters:
- `filter`: string filter
- `limit`: page size (default 20)
- `offset`: offset for pagination

`GET /processings/page` additionally accepts:
- `projectId` (optional): Mapflow project id to scope the listing. When set, the backend returns processings owned by any user as long as the caller has at least `readonly` access to the project (cross-owner visibility for shared projects). When unset, the endpoint falls back to listing processings owned by the calling user only.

`GET /processings/page` and `GET /prompts/page` use a forward-only paging shape:
```json
{"has_more": false, "limit": 20, "offset": 0, "items": [...]}
```
- The server does not return a `total` count (would require a `COUNT(*)`). Clients paginate by `offset + limit` and use `has_more` to drive the "next page" affordance. There is no "page X of N" UI — only previous / next.
- For `/processings/page`, a page may contain fewer than `limit` items even when `has_more=true` (the backend fetches `limit + 1` rows and may drop ones archived upstream during a per-page sync). The client always advances by `limit`, never by `len(items)`.
- For `/prompts/page`, pages are always full up to `limit`.

Other paged listing endpoints (e.g. `GET /processings/{id}/sessions`) keep their existing `total` field for now; this migration only applies to the two endpoints above.

## Authorization & Roles

Access to project-scoped resources is enforced by the backend against the Whitemaps role for the calling user on the processing's project. Role hierarchy (lowest → highest privilege):

`readonly < contributor < maintainer = owner`

Minimum role required per action:
- `readonly`: read endpoints — `GET /processings/page`, `GET /processings/{id}`, `GET /processings/{id}/sessions`, `GET /processings/{id}/results`, `GET /sessions/{id}`, `GET /result/{session_id}`.
- `contributor`: create sessions, inferences, and processing-bound spatial prompts — `POST /inference`, `POST /sessions/{id}/inferences`, `POST /prompts/{id}/point_prompts`, `POST /prompts/{id}/bbox_prompts`, `DELETE /prompts/{id}/point_prompts/{spid}`, `DELETE /prompts/{id}/bbox_prompts/{spid}`.
- `maintainer`: archive sessions and processings, rename sessions — `DELETE /sessions/{id}`, `DELETE /processings/{id}`, `PATCH /sessions/{id}`.

Legacy processings without a `project_id` fall back to the owner check (effective email == owner). Denial is reported as `404 ProcessingNotFound` (no role leak).

The plugin mirrors these gates client-side using the existing `UserRole` enum (`mapflow/schema/project.py`):
- `can_start_processing` (contributor+) — gates create/inference/spatial-prompt actions.
- `can_delete_rename_review_processing` (maintainer+) — gates delete/archive/rename actions.

Prompt CRUD (`POST /prompts`, `PATCH /prompts/{id}`, `DELETE /prompts/{id}`) is user-scoped and not gated by project role.

## Authentication

Same as main Mapflow API — Basic Auth or OAuth2 via the shared `Http` instance.

## Error Handling

Standard HTTP error codes. The plugin displays errors in the debug output panel.
- 4xx: client errors (validation, not found, etc.)
- 5xx: server errors
