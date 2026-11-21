# 002_B Processing API

## Purpose
Define the REST API contracts for processing management consumed by this plugin.

## Endpoints

The plugin uses the `v2` variant of an endpoint wherever one exists.

### `POST /processings/v2`
Submit a processing job. Body includes geometry and processing params.

### `POST /projects/{project_id}/processings/v2/page`
One page of a project's processings. Body: `limit`, `offset`, `sortBy`, `sortOrder`, and `terms` (a name
search applied on the server).

### `GET /processings/{id}/v2`
One processing.

### `PUT /processings/{id}/v2`
Update processing name/description.

### `POST /processings/{id}/restart/v2`
Restart the failed and cancelled AOIs of a processing. The backend accepts it for a processing that is
failed, cancelled, in progress or awaiting, from any user who may run a processing in the project.

### `POST /processing/cost/v2`
The cost of the processing the form describes, as text.

### `DELETE /processings/{id}`
Delete a processing.

### `PUT /processings/{id}/rate`
Rate a result. Body: `rating`, `feedback`.

### `GET /processings/{id}/result`
The processing's features as GeoJSON. The plugin streams it to disk.

### `GET /processings/{id}/aois`
The processing's area. "Run again" and "Download the area" read it.

## Plugin behaviour

- The list is asked for **30 at a time, newest first**, with "Show more". There is no other sort order.
- It is polled **every 6 seconds while a processing on the loaded pages is not final**, and again 6
  seconds after a refresh that failed for a transient reason (`005_interactions.md` § Failed requests).
  Not otherwise.
- **Search** sends `terms`, so it covers the whole project and not only the pages already loaded. A
  search is a separate listing with its own pages. The full listing stays loaded, and the Start tab
  reads the full listing, never the search matches. Clearing the search returns to the full listing.
- The poll watches every processing that is not final: on the full listing, on the search listing and
  on the card that "Show" opened. Each of them gives the same notice and the same automatic add to
  map, once.
- "Show" in a notice opens the processing's card. If the processing is not on the loaded pages, the
  plugin fetches it by id (`GET /processings/{id}/v2`).
- **Restart** is offered for a failed or a cancelled processing, to every role that may run one.

## AOI area measurement

The AOI is collected from the selected polygon layer part by part (`QgsGeometry.collectGeometry`)
and submitted as it is: **the plugin does not union it**. Intersecting polygons are meaningful
input — a Planned Search may carry an AOI enclosing another one, each with its own name and its own
results — and the backend unions the geometry itself when it starts a processing and when it
estimates the cost.

The **measurement** must union it, though. The area of a MultiPolygon is the sum of its parts, so
overlapping polygons would contribute their shared area once per part, and the plugin would show
(and pre-check limits against) more area than the backend charges for. `measure` in `qgis_bridge/aoi.py`
therefore measures the union of the parts, which makes the displayed *Area*, the cost estimate
derived from it, and the client-side limit checks agree with the backend.

Invalid input must not cost the user that dissolve. GEOS refuses to union a self-intersecting ring
and answers with a NULL geometry, which would fall straight back to the summed parts — so each
part is made valid **individually** before the union. Individually is the whole point: repairing
the multipart geometry as a whole would also resolve the overlaps *between* the parts, and since a
valid MultiPolygon may not have overlapping components, GEOS turns each overlap into a hole. On
two AOIs that nearly coincide that leaves their thin symmetric difference — a fraction of the real
area — which is a worse answer than the doubled one. The repair applies to a lone invalid polygon
too, whose ring area is meaningless on its own (a bowtie's lobes cancel out to zero). If the union
fails even after the repair, the geometry is measured as-is: an over-counted area beats none.

## AOI and the imagery footprint

When the imagery has a footprint of its own — a My imagery collection or image, or **one image chosen
from the catalog search** — only the part of the AOI inside that footprint can be processed. The plugin
intersects the AOI with the footprint and uses the result for everything that follows: the submitted
geometry, the displayed area, the cost request, the provider's minimum-area check and the area limits
below. An AOI that doesn't touch the footprint blocks the run. Basemap providers have no footprint, and
their AOI is submitted whole.

## Imagery from a QGIS tile layer

A tile layer of the open QGIS project can be the imagery of a processing (`001_goal.md`). The plugin has
no editor for such sources. It reads the layer and sends `sourceParams.userDefined`.

### Which layers are offered

- The raster layers of the open QGIS project whose provider is `wms` and whose source has `type=xyz`.
  QGIS makes such a layer from an XYZ Tiles connection.
- The run form lists them by layer name under "QGIS tile layers". The list follows the project: a layer
  that is added, renamed or removed changes the list.
- The layers that the plugin added itself (previews, results) are not listed.
- Other tile sources (WMS, WMTS, ArcGIS, vector tiles) are not listed.

### What the plugin sends

| `userDefined` field | Value |
|---|---|
| `sourceType` | `QUADKEY` when the address has `{q}`. `TMS` when it has `{-y}`. `XYZ` in every other case |
| `url` | The `url` of the layer source, decoded. For `TMS`, `{-y}` is written as `{y}` |
| `zoom` | The zoom that the user chose |
| `crs` | `epsg:3857`. QGIS reads every XYZ layer in this projection |
| `rasterLogin`, `rasterPassword` | The login and password of the layer, when it has them. Absent in every other case |

- The login and password come from `username` and `password` of the layer source, or from a Basic
  configuration of the QGIS authentication database (`authcfg`).
- The form offers the zooms from `zmin` to `zmax` of the layer, and no zoom above 21. The default is 18,
  or the nearest zoom that the form offers.
- `meta.source` is `xyz`, `tms` or `quadkey`.

### A layer that the plugin cannot use

The layer stays in the list, disabled, with the reason:

- The address has no `{x}`, `{y}` and `{z}`, and no `{q}`.
- The address does not start with `http://` or `https://`.
- The host is this computer or a private network address. Mapflow cannot reach it.
- The layer needs a referer or other HTTP headers. Mapflow cannot send them.
- The layer uses an authentication configuration that is not Basic.

The server checks the source again when the processing starts. Its refusals (`source-validator.*`) show
the texts of `core/messages.py`.

### The alert before the start

When the chosen layer has a login and a password, "Run" first shows an alert:

> Mapflow needs the login and the password of the layer "{layer}" to read its tiles. The plugin sends
> them to Mapflow with the processing. Members of the project can read them.

- The buttons are "Send and run" and "Cancel". "Cancel" starts nothing and changes nothing in the form.
- The alert has a checkbox "Don't show this again". When the user ticks it and presses "Send and run",
  the plugin stores `skip_tile_login_alert` (`003_local_storage.md`), and the alert does not come again.
  "Cancel" never stores the choice.
- A layer without a login gives no alert.

### Other rules

- The plugin stores nothing of the layer: no address, no login and no password in `QgsSettings` or in the
  QGIS authentication database.
- The layer has no footprint. The AOI is submitted whole (§ AOI and the imagery footprint).
- The price is not known locally. The cost comes from `POST /processing/cost/v2`.
- The plugin adds no preview layer: the layer is on the map already.
- A processing card shows "Custom tile layer" and the host of the address. It never shows the full
  address, the login or the password: an address can carry a key.
- "Run again" chooses the project layer that has the same address and source type. When no such layer
  exists, the form asks for the imagery, as it does for other imagery that it cannot restore.

## AOI area limit

Two ellipsoidal-area constraints apply, both against `user.aoiAreaLimit` (sq.m), reported in the
`user` object of the `/projects*` responses (`GET /projects/{id}`, `GET /projects/default`,
`GET /projects`, `POST /projects/page`, `POST /projects/starred`, and the `POST` / `PUT`
create/update responses):

1. **Total processing area** — the whole submitted geometry (all AOIs combined, the polygons'
   own ellipsoidal area, not bounding-boxed) must be ≤ `aoiAreaLimit`.
2. **Per-AOI bounding box** — each AOI's (each polygon's) **lat-lon–oriented bounding box** must
   have an ellipsoidal area ≤ `aoiAreaLimit`. This is the bounding box, not the polygon's own
   area, and is checked per AOI rather than summed.

The plugin mirrors both **before requesting `/cost`**, on the submitted (post-crop) geometry, and
blocks the processing with a warning in the cost area if either is exceeded. A zero/unknown limit
disables the client checks and defers to the backend.

On start, the backend rejects an over-limit job with the `TOO_LARGE_PROCESSING` error
(`params.area`, `params.aoiAreaLimit`, both sq.m); the plugin renders a translated message for
this code.
