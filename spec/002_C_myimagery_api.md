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

### `GET /rasters/mosaic/{id}`
Get mosaic details.

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
