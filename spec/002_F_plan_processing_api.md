# 002_F Planned Processing API

## Purpose
Define REST API contracts for planned processing consumed by the plugin.

## Endpoints

### `POST /processings/template`
Create a template.

Request fields:
- `name` (string)
- `searchParams` (object, includes `aoi`)
- `processingParams` (object)
- `projectId` (uuid)
- `activeUntil` (datetime)

Response:
- `template` (Template object)
- `searchResults` (array of `{id, metadata}`)

### `GET /processings/template`
Get all templates for authenticated user.

Response:
- array of Template objects

### `GET /processings/template/{templateId}`
Get one template by id.

Response:
- `template` (Template object)
- `searchResults` (array of `{id, metadata}`)

### `POST /processings/template/{templateId}`
Run processing from template with legacy params payload.

Body includes:
- `name`, `description`, `wdName`, `wdId`, `geometry`, `params`, `meta`, `blocks`, `updateTemplateGeometry`

### `POST /processings/template/{templateId}/v2`
Run processing from template with v2 params payload.

Body includes:
- `name`, `description`, `wdName`, `wdId`, `geometry`, `params`, `meta`, `blocks`, `updateTemplateGeometry`

### `PUT /processings/template/{templateId}`
Update template.

Body fields:
- `name` (string)
- `searchParams` (object)
- `processingParams` (object)
- `activeUntil` (datetime)

Response:
- updated Template object

### `DELETE /processings/template/{templateId}`
Mark template as deleted.

### `POST /processings/template/{templateId}/pause`
Set template status to Inactive.

Response:
- `template` (Template object)
- `searchResults` (array)

### `POST /processings/template/{templateId}/resume`
Set template status to Active.

Response:
- `template` (Template object)
- `searchResults` (array)

### `GET /processings/template/{templateId}/processings`
Get all processings associated with template.

Response:
- array of Processing objects

The response is `List[ProcessingJson]` (v1): `params` is a flat `Map[String,String]`
(e.g. `{url, zoom, data_provider}`), **not** the v2 `{sourceParams: {...}}` shape, and
there is no `…/processings/v2` variant. The plugin parses it with a dedicated
`TemplateProcessingSchema` that keeps the flat `params` and the result layers, rather than
forcing it through `ProcessingDTO` (whose v2 `ProcessingParams` parsing would choke on the
flat shape). The in-template table groups processings under their AOI from `aoiDetails`
(see above); this endpoint supplies the full objects (with layers) used to load a
processing's results on double-click, keyed by id.

### `POST /processings/template/{templateId}/aoi`
Add one or more AOIs to a template.

Body (one of):
- single: `{ "geometry": <GeoJSON geometry>, "name": <string|null> }`
- multiple: `{ "aois": [ { "geometry": ..., "name": ... }, ... ] }`

Exactly one of `geometry` / `aois` must be provided.

Response:
- `{ "addedCount": <int>, "partitioningTriggered": <bool> }`

### `POST /processings/template/{templateId}/aoi/{aoiId}`
Update an AOI's name and/or geometry. (Served over POST, not PUT — PUT returns 404.)

Body fields (both optional):
- `name` (string)
- `geometry` (GeoJSON geometry)

Response:
- updated AOI

### `DELETE /processings/template/{templateId}/aoi`
Delete one or more AOIs from a template.

Body:
- `{ "aoiIds": [<uuid>, ...] }`

Response:
- `{ "deletedCount": <int>, ... }`

### `POST /processings/template/{templateId}/image/{imageId}/seen`
Mark one image as seen for template.

### `PUT /processings/template/{templateId}/image/seenAll`
Mark all of the template's images as seen in a single call (resets `newImagesCount` to 0).

### `GET /processings/template/user/{userId}`
Get templates for a specific user id.

Response:
- array of Template objects

### `GET /processings/template/project/{projectId}`
Get templates for a specific project id.

Response:
- array of Template objects

## Template Object
- `id` (uuid)
- `name` (string)
- `status` (string)
- `createdAt` (datetime)
- `userId` (uuid)
- `searchParams` (object)
- `processingParams` (object)
- `lastCheckedAt` (datetime)
- `activeUntil` (datetime)
- `searchResults` (array of `{id, metadata}`)
- `projectId` (uuid)
- `area` (number)
- `newImagesCount` (integer)

## AOIs, names, and `aoiDetails`

A template's AOIs are carried in `searchParams.aoiDetails`, a GeoJSON
`FeatureCollection`. Each feature's `properties` object has the shape:

- `id` (uuid, optional) — the persisted AOI id. Required to rename/delete a specific
  AOI. It may be absent for legacy `aoi`-only templates and is only guaranteed after
  the backend has persisted the template and it is re-fetched with
  `GET /processings/template/{templateId}`.
- `name` (string, optional) — the AOI's human name. May be `null` (unnamed).
- `processings` (array) — processings launched for this AOI; each item:
  `{ processingId, processingName, processingStatus, area, geometry, projectId }`. The
  `geometry` is the processing's footprint (used to draw it on the map).
- `hasNewImages` (bool) — whether the AOI has unseen new images.

`aoiDetails` (fully populated with per-AOI `processings`, `name`, `hasNewImages`) is
returned only by endpoints that serialize the full template `searchParams` —
`GET /processings/template/{templateId}`, `GET /processings/template`,
`GET /processings/template/user/{userId}`. It is **absent** from
`GET /processings/template/project/{projectId}` (returns `ProcessingTemplateShortDetails`
without `searchParams`), which the poll uses; the plugin therefore hydrates the template by
id when entering it (and re-hydrates on the in-template poll to refresh processing statuses).

This is the source the plugin uses to **group** processings under their AOI — both in the
in-template table (each AOI row followed by its processings) and on the map (a layer-tree
subgroup per AOI containing the AOI polygon plus each processing's footprint). The flat
`GET …/processings` list is used only to obtain the full processing objects (with result
layers) for loading a processing's results on double-click.

### Setting AOI names on creation
`POST /processings/template` accepts AOI names via `searchParams.aoiDetails`: each
feature's `properties` is read as `{ id?, name? }` (`InputAoiProperties`). The plugin,
when creating a template from a layer whose features carry a `name` attribute, sends
`aoiDetails` as a FeatureCollection with one feature per AOI and `properties.name` set
from that attribute. When the attribute is absent the AOI is created with a `null`
name and can be renamed later via `PUT .../aoi/{aoiId}`. The legacy combined `aoi`
geometry remains accepted as a fallback when no names are needed.

### Name constraints
AOI names must not exceed **64 characters**; the plugin validates this client-side
before issuing create/rename requests and surfaces a translatable error otherwise.

### Scope note (#WARNING)
Naming AOIs is currently **template-only**. Regular processings expose AOIs via
`GET /processings/{processingId}/aois` whose `AoiJson` has no `name` field, so
per-AOI names cannot be set on standalone processing creation yet. Spec for named
AOIs on regular processings is deferred to a later iteration.

## In-template navigation (client behavior)

The plugin's projects/processings table supports a third navigation level. Levels:
`Projects → Processings → Template`. Entering a template ("one step right", via
double-click or the forward button) does all of:
- fetches/hydrates the template's `searchParams` (if missing);
- shows, in the same table, the template's AOIs and their processings **grouped**: each
  AOI row (blue-tinted) is immediately followed by the processings launched from it
  (green-tinted), then the next AOI. Grouping comes from `aoiDetails[].processings`;
- loads the template's map layer group with **one subgroup per AOI** (named after the
  AOI), each containing the AOI polygon (blue, transparent) and its processings'
  footprints (green, transparent);
- fills the imagery-search results table/layer (without stealing tab focus).

Processings attached to the template but not intersecting any AOI are **absent from
`aoiDetails`**; they are listed at the bottom under a non-selectable **"No AOI"** separator
row (their ids come from `GET …/processings` minus the ids referenced by `aoiDetails`).

Double-clicking a processing row loads that processing's results (the full object, with
result layers, model and progress, comes from `GET …/processings`).

### Row statuses

Template row (processings/templates list):
- `Searching` while `status == SEARCHING`;
- `Failed` while `status == FAILED`;
- `Inactive` when paused (`isActive == false`);
- `Created` when ready but `lastCheckedAt` is null (no daily check yet);
- `Updated` after the first check, with a `(newImagesCount)` tag when there are unseen images.

AOI row (in-template) — aggregated from its processings' statuses:
- any `IN_PROGRESS`/`AWAITING` → `In progress (ok/total)`;
- else any `FAILED` → `Failed (ok/total)`;
- else all `OK` → `OK (total)`; no processings → `—`.

Template Progress (`100% × covered AOI area / total AOI area`, i.e. the share of the
template's AOI area processed at least once) is **not implemented (#WARNING)**: it is not
derivable from existing responses without geometric union/difference of AOI vs processing
footprints; it should be computed by the backend and exposed on the template instead.

Selecting an AOI row filters the imagery-search results (both table and footprint
layer) to images intersecting that AOI (`aoiIds` on the template images request).

Leaving a template ("one step left", back button) returns to the project's
processings list and removes the template's layer group from the map.

## Limits and client-side validation

### Template area limit
`GET /user/status` exposes `templateAreaLimit` (number, square metres): the maximum
AOI area allowed for a planned processing (template). It is the template-scoped
counterpart of the per-processing `aoiAreaLimit`.

The plugin stores it as square kilometres and, before issuing
`POST /processings/template`, forbids creation client-side when the selected AOI
exceeds the limit — mirroring the pre-flight check done for regular processing
creation. A missing or zero `templateAreaLimit` disables the client-side check and
defers to the backend.

### Error feedback
When the backend rejects template creation because the limit is exceeded it returns
the standard error model (`{"code", "message", "params"}`) with a generic
`code` (e.g. `BAD_REQUEST`) and a human-readable `message`. The plugin resolves the
error to a single, translatable description (see the central error registry in
`mapflow/errors`) rather than surfacing the raw backend text.