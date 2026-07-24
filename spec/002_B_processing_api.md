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
