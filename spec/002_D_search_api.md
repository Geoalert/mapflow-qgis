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

#### What the plugin sends

| Field | Plugin control | Sent |
|---|---|---|
| `aoi` | the Area drop-down, "Use map view", Draw | always |
| `acquisitionDateFrom` / `acquisitionDateTo` | From / To, the last year by default | always |
| `maxCloudCover` | slider 0–100 %, 20 by default | always |
| `minOffNadirAngle` / `maxOffNadirAngle` | one range slider 0–30°, the full range by default | always |
| `minAoiIntersectionPercent` | "Min area coverage" slider 0–100 %, 20 by default | not at 0 |
| `hideUnavailable` | "Available for me" switch, off by default | always |
| `productTypes` | "Type" chips: Mosaics, Scenes | only when exactly one chip is on |
| `limit` / `offset` | pages of 50 with "Show more" | always |
| `sortBy` / `sortOrder` | — (newest first) | always |

`minResolution`, `maxResolution` and `dataProviders` are not sent: the plugin has no control for them.
The controls follow Mapflow Web's search, so the same search gives the same list in both.

### Response and missing metadata

The response is a paginated list of image footprints with metadata (`acquisitionDate`,
`cloudCover`, `offNadirAngle`, `pixelResolution`, `providerName`, `productType`, `previewUrl`, …).

A scene may come with its preview in several parts: `previews` is then a list of `{url, geometry}`
(Roscosmos). The plugin fetches every part, lays each on its own geometry and shows them as one layer.

**Metadata may be absent.** Results from the user's own imagery (see the My Imagery providers
below) carry mostly-empty metadata — `acquisitionDate`, `cloudCover` and angles may be `null`,
because most user uploads have no catalog metadata. The governing rule, implemented server-side,
is: **a missing (`null`) value matches any condition** — a `null` column satisfies every
predicate on that column.

### No client-side filtering

Filters are applied **only by the server**, and only when the user presses "Search imagery". Moving a
filter control changes nothing on screen until then: the list always shows exactly what the last
request returned. The 3.x plugin also re-applied the filters locally and greyed the rows that no longer
matched; Mapflow Next does not, so the list, its count and its pages can never disagree with the
server's.

### My Imagery search providers

Two providers return the user's own imagery through this endpoint (user-scoped; they appear in
the server-driven provider list automatically):

- `my_imagery_images` — individual images, `productType = IMAGE`
- `my_imagery_mosaics` — whole mosaics, `productType = MOSAIC`

Their `previewUrl` points at the data-catalog host (same Mapflow origin, under `/rest/rasters/…`)

Those two names are internal, so a search-result **card** shows **"My image"** and **"My
collection"** instead. The substitution is display-only and happens where the card is drawn:
the footprint layer attributes and the provider list keep the API's own names, and every match
on them — the per-provider minimum-area lookup, the processing request — keeps comparing raw
names. A provider without a mapping is shown as it
comes, so a new one is never blank.

See also `002_F_plan_processing_api.md` for `POST /processings/template/{templateId}/images`,
which returns a template's search results filtered server-side (a subset of the same filters).
