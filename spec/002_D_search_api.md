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

The plugin does not re-filter results offline — the server's filtered, paginated result is
shown verbatim.

See also `002_F_plan_processing_api.md` for `POST /processings/template/{templateId}/images`,
which returns a template's search results filtered server-side (a subset of the same filters).
