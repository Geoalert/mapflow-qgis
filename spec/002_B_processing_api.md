# 002_B Processing API

## Purpose
Define the REST API contracts for processing management consumed by this plugin.

## Endpoints

### `POST /projects/{project_id}/processings`
Submit a processing job. Body includes geometry and processing params.

### `GET /projects/{project_id}/processings/v2`
List processings for a project. Polled approximately every 5 seconds for status updates.

### `PUT /processings/{id}`
Update processing name/description.

## AOI area measurement

The AOI is collected from the selected polygon layer part by part (`QgsGeometry.collectGeometry`)
and submitted as it is: **the plugin does not union it**. Intersecting polygons are meaningful
input — a Planned Search may carry an AOI enclosing another one, each with its own name and its own
results — and the backend unions the geometry itself when it starts a processing and when it
estimates the cost.

The **measurement** must union it, though. The area of a MultiPolygon is the sum of its parts, so
overlapping polygons would contribute their shared area once per part, and the plugin would show
(and pre-check limits against) more area than the backend charges for. `calculate_aoi_area`
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
