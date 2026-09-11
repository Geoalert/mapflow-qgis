# 002_C My Imagery (Data Catalog) API

## Purpose
Define the REST API contracts for data catalog (My Imagery) management consumed by this plugin.

My Imagery is also reachable through **imagery search** (`002_D_search_api.md`), via the
`my_imagery_images` / `my_imagery_mosaics` providers on `POST /catalog/meta`. Those results
carry mostly-empty metadata and their `previewUrl` is on this data-catalog host, no auth required.

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

#### Client-side download (plugin behavior)
After receiving the response, the plugin asks the user where to save the image (the dialog suggests
`filename`) and fetches `download_url` directly, without Mapflow credentials.

- **Streamed to disk:** the response body is written to disk as it arrives. The plugin never holds the
  whole image in memory: images can be several GB, beyond what Qt5 can hold in one buffer (2 GiB).
- **Atomic replace:** data goes to a temporary file next to the target, which replaces the target only
  once the download has completed successfully. On any failure the target path is left untouched — no
  partial file is created, and a file already at that path is kept.
- **Completes however long it takes:** an in-flight download stays alive until it finishes; its
  completion is never lost, whatever the download's duration.
- **Target not writable:** if the target file cannot be opened for writing, the user is told why and no
  download request is sent.
- **Outcome shown to the user:** on success, a message-bar notice "Image saved to {path}". On a network,
  HTTP or disk error, a plain error message with the reason.

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
