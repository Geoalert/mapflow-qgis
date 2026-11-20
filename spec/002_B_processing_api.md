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
  search is a separate listing with its own pages. The full listing stays loaded and keeps its poll:
  the Start tab, the notices and the automatic add to map read the full listing, never the search
  matches. Clearing the search returns to the full listing.
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
