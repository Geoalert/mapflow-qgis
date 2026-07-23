# 002_D Imagery Search API

## Purpose
Define the REST API contracts for imagery search consumed by this plugin. All imagery
search goes through the Mapflow catalog API; the plugin no longer talks to any third-party
search service directly.

## Endpoints

### `POST /catalog/meta`
Search the Mapflow imagery catalog. The request body (`ImageCatalogRequestJson`) carries the
AOI geometry and the filters, all applied **server-side**; the response is paginated and
reports the filtered `total`:

- `aoi` (GeoJSON geometry)
- `acquisitionDateFrom` / `acquisitionDateTo`
- `minResolution` / `maxResolution`
- `maxCloudCover`
- `minOffNadirAngle` / `maxOffNadirAngle`
- `minAoiIntersectionPercent`
- `hideUnavailable`
- `dataProviders` (list)
- `productTypes` (list)
- `limit` / `offset`, `sortBy` / `sortOrder`

### Response and missing metadata

The response is a paginated list of image footprints with metadata (`acquisitionDate`,
`cloudCover`, `offNadirAngle`, `resolution`, `providerName`, `productType`, `previewUrl`, …).

**Metadata may be absent.** Results from the user's own imagery (see the My Imagery providers
below) carry mostly-empty metadata — `acquisitionDate`, `cloudCover` and angles may be `null`,
because most user uploads have no catalog metadata. The governing rule, implemented server-side,
is: **a missing (`null`) value matches any condition** — a `null` column satisfies every
predicate on that column.

### Client-side filtering (local filter)

The primary search path shows the server's filtered, paginated result as-is. Separately, the
plugin re-applies the same filters **locally** on the already-fetched page as the user moves the
filter widgets, so the table reacts without a new request. This local filter **demotes and marks**
rows (greys them, sorts them to the bottom, hides their footprint) rather than removing them, so
the page size and pager stay consistent.

The local filter MUST follow the same missing-matches-any rule: a row with a `null`
`acquisitionDate` or `cloudCover` passes the corresponding filter (it is never demoted for a
value it does not have). Otherwise the user's own imagery would disappear the moment any filter
is touched.

### My Imagery search providers

Two providers return the user's own imagery through this endpoint (user-scoped; they appear in
the server-driven provider list automatically):

- `my_imagery_images` — individual images, `productType = IMAGE`
- `my_imagery_mosaics` — whole mosaics, `productType = MOSAIC`

Like every other provider, their `previewUrl` is a **self-authenticating (pre-signed) URL** — the
plugin fetches it without attaching Mapflow credentials. (The backend pre-signs it, as it already
does for `GET /rasters/image/{id}/download`; the plugin needs no per-host preview-auth logic.)

See also `002_F_plan_processing_api.md` for `POST /processings/template/{templateId}/images`,
which returns a template's search results filtered server-side (a subset of the same filters).
