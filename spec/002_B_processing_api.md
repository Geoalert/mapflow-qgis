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

## Submitted AOI geometry

The AOI is taken from the selected polygon layer (its selected features, or all of them) and sent
as a single geometry. **Intersecting polygons are dissolved (unary union) before submission**, so
that a shared area belongs to exactly one polygon of the submitted geometry. Merely collecting the
features into a MultiPolygon would keep the overlaps as separate parts, and the area of a
MultiPolygon is the sum of its parts: the overlap would be measured, processed and billed once per
overlapping polygon. This applies to overlaps *between* features and to overlapping parts *within*
one MultiPolygon feature.

Consequences of the dissolve, all intended:

- the **Area** shown in the plugin equals the area the backend charges for;
- the per-processing polygon count (`maxAoisPerProcessing`) is checked on the **dissolved**
  geometry — the count the backend receives — so overlapping polygons that merge into one count
  as one;
- disjoint polygons are never merged: a multi-AOI processing stays multi-AOI.

If the union fails (GEOS rejects invalid input, e.g. self-intersecting rings), the plugin falls
back to the plain collection rather than dropping the AOI.

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
