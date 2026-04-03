# API Specification

## Overview

The FastAPI application mounts the following routers:
- mosaic management router
- data management router
- healthcheck router
- internal API router

The application also exposes a root endpoint and generated OpenAPI/docs endpoints.

Configured public route prefix:
- `/rest/rasters`

Configured docs endpoints:
- `/rest/rasters/docs`
- `/rest/rasters/openapi.json`

## Authentication Modes

### Public User-Facing Endpoints
Most public endpoints depend on `StandardHTTPSecurity` and therefore require authenticated user credentials.

### Internal Endpoints
Internal endpoints under `/api/...` require API key validation via `validate_api_key`.

### Healthcheck Endpoints
Healthcheck endpoints do not require authentication.

## Root Endpoint

### `GET /`
Returns a simple authenticated status payload.

Response:
- `200 OK`: `{"user status": "authenticated"}`

## Public API

### Memory And Image Utility Endpoints

### `GET /rest/rasters/memory`
Returns current memory-related limits and usage for the authenticated user.

Response shape:
```json
{
	"memoryLimit": 10737418240,
	"memoryUsed": 524288000,
	"memoryFree": 10213130240,
	"maxUploadFileSize": 10737418240,
	"maxPixelCount": 100000
}
```

Notes:
- `memoryLimit` and `memoryFree` may be `null` when memory limiting is disabled by configuration.

### `GET /rest/rasters/image/{image_id}/preview/{preview_type}`
Returns an image preview for the requested image.

Parameters:
- `image_id`: UUID
- `preview_type`: string, expected current values are `l` or `s`

Notes:
- The allowed preview types are inferred from service usage and response URL generation, not explicitly validated at router level.

### `GET /rest/rasters/image/{image_id}/download`
Returns a presigned S3 download URL for the requested image.

Parameters:
- `image_id`: UUID

Access rules:
- Requires `StandardHTTPSecurity` (authenticated user)
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

### `GET /rest/rasters/image/{image_id}/status`
Returns preprocessing status for a single image.

Response shape:
```json
{
	"image_id": "<uuid>",
	"filename": "image.tif",
	"preprocessing_status": "NONE|PENDING|IN_PROGRESS|COMPLETED|FAILED",
	"preprocessing_error": null,
	"data_available": true,
	"uploaded_at": "2026-03-22T12:34:56Z"
}
```

Current behavior:
- returns `404` if the image does not exist
- returns `404` if the authenticated user has no access to the image
- returns status values such as `NONE`, `PENDING`, `IN_PROGRESS`, `COMPLETED`, `FAILED`

### Mosaic Endpoints

### `POST /rest/rasters/mosaic`
Creates an empty mosaic.

Request body:
```json
{
	"name": "Field Survey March",
	"tags": ["survey", "march"]
}
```

Response shape:
```json
{
	"id": "<uuid>",
	"tags": ["survey", "march"],
	"name": "Field Survey March",
	"created_at": "2026-03-22T12:34:56Z"
}
```

### `PUT /rest/rasters/mosaic/{mosaic_id}`
Updates mosaic metadata.

Request body:
```json
{
	"name": "Updated mosaic name",
	"tags": ["updated", "tag"]
}
```

Success response shape:
```json
{
	"id": "<uuid>",
	"tags": ["updated", "tag"],
	"name": "Updated mosaic name",
	"created_at": "2026-03-22T12:34:56Z"
}
```

Domain error shape:
```json
{
	"message": "<error message>"
}
```

### `GET /rest/rasters/mosaic/{mosaic_id}`
Returns one mosaic visible to the authenticated user.

Success response shape:
```json
{
	"id": "<uuid>",
	"rasterLayer": {
		"tileUrl": "https://.../{z}/{x}/{y}.png?uri=...",
		"tileJsonUrl": "https://.../tiles.json?uri=..."
	},
	"tags": ["survey", "march"],
	"name": "Field Survey March",
	"created_at": "2026-03-22T12:34:56Z",
	"footprint": "MULTIPOLYGON (...)",
	"sizeInBytes": 123456789
}
```

Domain error shape:
```json
{
	"message": "<error message>"
}
```

### `GET /rest/rasters/mosaic`
Lists mosaics visible to the authenticated user.

Query parameters:
- `tags`: optional repeated string filter

Response shape:
```json
[
	{
		"id": "<uuid>",
		"rasterLayer": {
			"tileUrl": "https://.../{z}/{x}/{y}.png?uri=...",
			"tileJsonUrl": "https://.../tiles.json?uri=..."
		},
		"tags": ["survey"],
		"name": "Field Survey March",
		"created_at": "2026-03-22T12:34:56Z",
		"footprint": "MULTIPOLYGON (...)",
		"sizeInBytes": 123456789
	}
]
```

### `DELETE /rest/rasters/mosaic/{mosaic_id}`
Deletes a mosaic and related files.

Current behavior:
- returns `200` on successful deletion
- lock-related behavior is influenced by downstream Whitemaps lock checks

### Mosaic Image Endpoints

### `GET /rest/rasters/mosaic/{mosaic_id}/image`
Lists images in a mosaic.

Success response shape:
```json
[
	{
		"id": "<uuid>",
		"mosaic_id": "<uuid>",
		"image_url": "s3://bucket/path/image.tif",
		"preview_url_l": "http://127.0.0.1:8080/rest/rasters/image/<uuid>/preview/l",
		"preview_url_s": "http://127.0.0.1:8080/rest/rasters/image/<uuid>/preview/s",
		"uploaded_at": "2026-03-22T12:34:56Z",
		"file_size": 123456789,
		"footprint": "POLYGON (...)",
		"filename": "image.tif",
		"checksum": "<sha1>",
		"meta_data": {
			"crs": "EPSG:4326",
			"pixel_size": [0.5, 0.5],
			"width": 1024,
			"height": 1024
		},
		"cog_link": "s3://bucket/path/cog/area-1.tif"
	}
]
```

Domain error shape:
```json
{
	"message": "<error message>"
}
```

### `GET /rest/rasters/mosaic/{mosaic_id}/status`
Returns aggregate and per-image status for all images in a mosaic, including non-ready images.

Response shape:
```json
{
	"mosaic_id": "<uuid>",
	"total_images": 3,
	"ready_images": 1,
	"pending_images": 1,
	"in_progress_images": 0,
	"failed_images": 1,
	"images": [
		{
			"image_id": "<uuid>",
			"filename": "image.tif",
			"preprocessing_status": "PENDING",
			"preprocessing_error": null,
			"data_available": false,
			"uploaded_at": "2026-03-22T12:34:56Z"
		}
	]
}
```

### `GET /rest/rasters/image/{image_id}`
Returns one image by ID.

Success response shape:
```json
{
	"id": "<uuid>",
	"mosaic_id": "<uuid>",
	"image_url": "s3://bucket/path/image.tif",
	"preview_url_l": "http://127.0.0.1:8080/rest/rasters/image/<uuid>/preview/l",
	"preview_url_s": "http://127.0.0.1:8080/rest/rasters/image/<uuid>/preview/s",
	"uploaded_at": "2026-03-22T12:34:56Z",
	"file_size": 123456789,
	"footprint": "POLYGON (...)",
	"filename": "image.tif",
	"checksum": "<sha1>",
	"meta_data": {
		"crs": "EPSG:4326",
		"pixel_size": [0.5, 0.5],
		"width": 1024,
		"height": 1024
	},
	"cog_link": "s3://bucket/path/cog/area-1.tif"
}
```

Domain error shape:
```json
{
	"message": "<error message>"
}
```

### `DELETE /rest/rasters/image/{image_id}`
Deletes one image.

### `PUT /rest/rasters/image/{image_id}`
Renames an image.

Query parameters:
- `name`: required string

Success response shape:
```json
{
	"id": "<uuid>",
	"mosaic_id": "<uuid>",
	"image_url": "s3://bucket/path/image.tif",
	"preview_url_l": "http://127.0.0.1:8080/rest/rasters/image/<uuid>/preview/l",
	"preview_url_s": "http://127.0.0.1:8080/rest/rasters/image/<uuid>/preview/s",
	"uploaded_at": "2026-03-22T12:34:56Z",
	"file_size": 123456789,
	"footprint": "POLYGON (...)",
	"filename": "renamed-image.tif",
	"checksum": "<sha1>",
	"meta_data": {
		"crs": "EPSG:4326",
		"pixel_size": [0.5, 0.5],
		"width": 1024,
		"height": 1024
	},
	"cog_link": "s3://bucket/path/cog/area-1.tif"
}
```

### Upload And Link Endpoints

### `POST /rest/rasters/mosaic/image`
Creates a new mosaic and uploads one file into it.

Request shape:
- content type: `multipart/form-data`
- query parameters:
	- `name`: required string
	- `tags`: repeated string parameter
- multipart fields:
	- `file`: required file

Success response shape:
```json
{
	"message": "Files successfully uploaded",
	"mosaic_id": "<uuid>"
}
```

Current behavior:
- request passes through user memory limit and upload size checks
- image validation and preprocessing behavior are further constrained by `006_image_compatibility.md`

### `POST /rest/rasters/mosaic/{mosaic_id}/image`
Uploads one file into an existing mosaic.

Request shape:
- path parameter: `mosaic_id`
- content type: `multipart/form-data`
- multipart fields:
	- `file`: required file

Success response shape:
```json
{
	"message": "Files successfully uploaded",
	"mosaic_id": "<uuid>"
}
```

Current behavior:
- image validation and preprocessing behavior are further constrained by `006_image_compatibility.md`

### `POST /rest/rasters/mosaic/{mosaic_id}/link-image`
Links an externally stored image into an existing mosaic.

Request body:
```json
{
	"url": "s3://bucket/path/image.tif"
}
```

Success response shape:
```json
{
	"message": "File successfully linked to a mosaic",
	"mosaic_id": "<uuid>"
}
```

Current behavior:
- request passes through memory-limit validation
- linked images are still subject to compatibility checks during ingestion into the mosaic

## Internal API

### `GET /api/image/{image_id}`
Returns internal metadata for one image.

Response shape:
```json
{
	"imageId": "<uuid>",
	"url": "s3://bucket/path/image.tif",
	"filename": null,
	"crs": "EPSG:4326",
	"pixelSize": [0.5, 0.5],
	"gsd": 0.5
}
```

Notes:
- current mapper behavior does not populate `filename` even though the schema allows it
- when the image is not yet available, current behavior returns `null` for `url`, `crs`, `pixelSize`, and `gsd`

### `GET /api/mosaic/{mosaic_id}`
Returns internal metadata for one mosaic.

Response shape:
```json
{
	"mosaicId": "<uuid>",
	"url": "s3://bucket/path/mosaic/",
	"crs": "EPSG:4326",
	"pixelSize": [0.5, 0.5],
	"gsd": 0.5,
	"loadStatus": "in_progress|completed|failed",
	"dataAvailable": false
}
```

Notes:
- `url` is normalized to end with `/` for workflow-engine consumers
- when the mosaic is not yet available, `crs`, `pixelSize`, and `gsd` may be `null`

### `DELETE /api/user/{email}`
Deletes a user by email.

Current behavior:
- returns `200` with empty body if deletion happened
- returns `204` with empty body if there was nothing to delete

### `POST /api/mosaic/load`
Creates a load-mosaic request processed through workflow-engine integration.

Request body:
```json
{
	"email": "user@example.com",
	"mosaic_name": "Loaded mosaic",
	"mosaic_tags": ["import", "external"],
	"params": [
		{
			"url": "https://example.com/tiles/{z}/{x}/{y}.png",
			"geometry": {
				"type": "Polygon",
				"coordinates": [[[30.0, 50.0], [31.0, 50.0], [31.0, 51.0], [30.0, 51.0], [30.0, 50.0]]]
			},
			"zoom": 18,
			"res": 0.5,
			"username": "optional-user",
			"password": "optional-password",
			"source_type": "tms|xyz|orbview_zip|roskosmos_tif",
			"image_name": "optional-display-name"
		}
	]
}
```

Response shape:
```json
{
	"mosaicId": "<uuid>",
	"url": null,
	"crs": null,
	"pixelSize": null,
	"gsd": null,
	"loadStatus": "in_progress",
	"dataAvailable": false
}
```

## Healthcheck API

### `GET /heartbeat/lite`
Returns `OK` if the process is running.

### `GET /heartbeat`
Returns `OK` if the database healthcheck succeeds.

Current behavior:
- returns `500` if the DB healthcheck fails

## Legacy Compatibility Endpoints

### `POST /rest/rasters`
Legacy Whitemaps-compatible upload route.

Current behavior:
- accepts a single multipart `file`
- creates upload artifacts through `legacy_whitemaps_upload_service`
- still uses current auth, memory limit update, and upload size checks
- the uploaded image is still processed under the same compatibility and preprocessing rules described in `006_image_compatibility.md`

Success response shape:
```json
{
	"url": "s3://bucket/path/image.tif"
}
```

Planned direction:
- this route should be treated as compatibility-only and is a candidate for future removal

## Code Present But Not Mounted

The file `app/routers/users.py` defines the following routes, but `app/main.py` does not include that router, so they are not currently exposed by the running application:
- `GET /rest/rasters/users/`
- `GET /rest/rasters/users/{user_id}`
- `POST /rest/rasters/users/{user_id}`

## Open Questions And Warnings

- Preview type validation is not specified at the API boundary.
- Error payload shapes are partly defined through FastAPI `HTTPException` usage and partly through custom response models; this is not yet normalized into one error contract.
- The users router exists in code but is not mounted, which suggests incomplete or deprecated API surface.
