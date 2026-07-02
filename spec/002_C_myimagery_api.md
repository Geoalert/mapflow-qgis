# 002_C My Imagery (Data Catalog) API

## Purpose
Define the REST API contracts for data catalog (My Imagery) management consumed by this plugin.

## Mosaic Endpoints

### `POST /rasters/mosaic`
Create an empty mosaic (imagery collection).

Request body:
```json
{"name": "string", "tags": ["string"]}
```

### `GET /rasters/mosaic`
List all user's mosaics.

Each mosaic in the list includes a `status_summary` object aggregating the
preprocessing state of its images (see "Status Summary").

### `GET /rasters/mosaic/{id}`
Get mosaic details. Also includes `status_summary`.

### `PUT /rasters/mosaic/{id}`
Update mosaic name/tags.

### `DELETE /rasters/mosaic/{id}`
Delete a mosaic and all its images.

### `POST /rasters/mosaic/{id}/image`
Upload an image to an existing mosaic. Multipart form data, 1h timeout.

### `POST /rasters/mosaic/image`
Create a new mosaic and upload the first image in one request. Query params: `name`, `tags`.

### `GET /rasters/mosaic/{id}/image`
List images in a mosaic.

**Only returns images with `data_available == true`** (ready images). Images that are
still being preprocessed (`PENDING` / `IN_PROGRESS`) or whose preprocessing `FAILED`
are **not** in this response. To enumerate all images including non-ready ones, use
`GET /rasters/mosaic/{id}/status`.

### `GET /rasters/mosaic/{id}/status`
Aggregate + per-image preprocessing status for **all** images in a mosaic, including
non-ready ones. This is the source of the "preprocessing" / "preprocessing failed"
rows in the plugin's image list.

Response shape (`MosaicStatusResponse`):
```json
{
    "mosaic_id": "uuid",
    "total_images": 3,
    "ready_images": 1,
    "pending_images": 1,
    "in_progress_images": 0,
    "failed_images": 1,
    "tiles_ready_images": 1,
    "images": [
        {
            "image_id": "uuid",
            "filename": "image.tif",
            "preprocessing_status": "NONE|PENDING|IN_PROGRESS|COMPLETED|FAILED",
            "preprocessing_error": "string|null",
            "data_available": false,
            "tiles_ready": false,
            "uploaded_at": "datetime"
        }
    ]
}
```

Field notes:
- `preprocessing_status`: `NONE` (no preprocessing needed, processed synchronously),
  `PENDING` (queued), `IN_PROGRESS` (running), `COMPLETED` (done), `FAILED` (check
  `preprocessing_error`).
- Per-image rows carry only `filename`, `uploaded_at`, and status — **no** `file_size`,
  `footprint`, `meta_data`, or preview URLs. Full metadata for ready images comes from
  `GET /rasters/mosaic/{id}/image`.
- The plugin merges the two lists: ready images use the full `ImageReturnSchema`;
  non-ready images (`PENDING`/`IN_PROGRESS`/`FAILED`) are shown as lightweight rows with a
  status flag. Preview/download are unavailable for non-ready rows; delete works for any
  status (`DELETE /rasters/image/{id}`).

### `DELETE /rasters/mosaic/{id}/failed`
Bulk-deletes every image of the mosaic whose `preprocessing_status` is `FAILED` — the
same set counted as `failed_images` by `GET /rasters/mosaic/{id}/status`. Convenience
over deleting each failed image individually.

Response shape:
```json
{"message": "2 failed image(s) deleted", "count": 2, "deleted_image_ids": ["uuid", "uuid"]}
```

- A mosaic with no failed images is a no-op returning `count: 0`.
- Load failures (a failed `load_data` workflow, leaving `preprocessing_status=NONE`) are
  **not** in the target set; remove them via per-image `DELETE`.

## Status Summary

Mosaic list/detail responses include a `status_summary` object bucketing image
preprocessing states:
```json
{"total": 5, "ready": 3, "pending": 1, "in_progress": 1, "failed": 0}
```
- `ready = NONE + COMPLETED`, `pending = PENDING`, `in_progress = IN_PROGRESS`,
  `failed = FAILED`; `total = ready + pending + in_progress + failed`.
- Mosaics with no images report all-zero counts; the field is always present.
- The plugin renders these counts next to each mosaic (✓ ready · 🕐 pending+in_progress ·
  ✗ failed).

### `GET /rasters/image/{id}/status`
Preprocessing status for a single image. Same per-image shape as the `images[]` entries
of `GET /rasters/mosaic/{id}/status`. Not currently required by the plugin, which polls
the mosaic-level status endpoint (one request per open mosaic).

## Image Endpoints

### `GET /rasters/image/{id}`
Get image details.

Response shape (`ImageReturnSchema`):
```json
{
    "id": "uuid",
    "mosaic_id": "uuid",
    "image_url": "string",
    "preview_url_l": "string",
    "preview_url_s": "string",
    "uploaded_at": "datetime",
    "file_size": 0,
    "footprint": "WKT string",
    "filename": "string",
    "checksum": "string",
    "meta_data": {
        "crs": "string",
        "count": 0,
        "width": 0,
        "height": 0,
        "dtypes": ["string"],
        "nodata": 0.0,
        "pixel_size": [0.0, 0.0]
    },
    "cog_link": "string|null",
    "available_for_download": true
}
```

Field notes:
- `available_for_download`: boolean, defaults to `true` if absent from API response. Indicates whether the image can be downloaded by the user. Images not ingested via `load_data` workflow are not downloadable.

### `PUT /rasters/image/{id}`
Update image (rename). Query param: `name`.

### `DELETE /rasters/image/{id}`
Delete an image from its mosaic.

### `GET /rasters/image/{image_id}/download`
Returns a presigned S3 download URL for the requested image.

Parameters:
- `image_id`: UUID

Access rules:
- Requires authenticated user
- User must own the mosaic containing the image (returns `404` otherwise, to not reveal existence)
- Image must have been ingested via the `load_data` workflow (returns `403` otherwise)
- `data_available` must be `true` (returns `409` otherwise)

Response shape:
```json
{
    "download_url": "https://...",
    "filename": "image.tif",
    "expires_in": 3600
}
```

Errors:
- `404`: image not found or user has no access
- `403`: image is not downloadable (not ingested via `load_data`)
- `409`: image data is not yet available

Notes:
- The presigned URL allows direct download from S3 without credentials; no data transfer through the service.
- URL expiry is configurable via `DOWNLOAD_URL_EXPIRY` (default 3600 seconds).
- The download restriction to `load_data` images prevents misuse of the service as a general file exchange.

## Storage Endpoints

### `GET /rasters/memory`
Get user storage limits and usage.

Response shape (`UserLimitSchema`):
```json
{
    "memoryLimit": 0,
    "memoryUsed": 0,
    "memoryFree": 0,
    "maxUploadFileSize": 0,
    "maxPixelCount": 0
}
```

## Error Model
Data catalog errors use format: `{"detail": {error_data}}`.
