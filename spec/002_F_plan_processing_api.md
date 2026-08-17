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
Update template. All body fields are optional (partial update); provided `searchParams`
are **merged** into the stored ones.

Body fields:
- `name` (string)
- `searchParams` (object) — **non-geometry** params only. The endpoint **rejects** a
  `searchParams` that carries `aoi` or `aoiDetails` (`400 "Geometry updates are not
  supported"`): geometry is changed exclusively through the per-AOI endpoints below.
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
id when **entering** it (and again after an AOI add/rename/delete), but **not** on every
poll tick — the grouping changes slowly, so re-fetching it each tick is wasteful.

This is the source the plugin uses to **group** processings under their AOI — both in the
in-template table (each AOI row followed by its processings) and on the map (a layer-tree
subgroup per AOI containing the AOI polygon plus each processing's footprint). The flat
`GET …/processings` list is used only to obtain the full processing objects (with result
layers) for loading a processing's results on double-click.

### Setting AOI names on creation
`POST /processings/template` accepts AOI names via `searchParams.aoiDetails`: each
feature's `properties` is read as `{ id?, name? }` (`InputAoiProperties`) — `name` is
optional. The plugin **always** sends `searchParams.aoiDetails` (a FeatureCollection),
never the legacy plain `searchParams.aoi`, which is **deprecated** because per-AOI names
cannot be attached to it. One Polygon feature is sent per AOI part: a MultiPolygon AOI is
split into one Polygon feature per part (the backend ignores MultiPolygon features in
`aoiDetails`), each carrying the same `name`. `properties.name` is set from the source
layer's `name` attribute when present, and omitted/`null` otherwise (the AOI can be renamed
later via `POST .../aoi/{aoiId}`). When the AOI does not come from a polygon layer (e.g. an
image/mosaic extent), unnamed feature(s) are built from the combined AOI geometry (again one
Polygon per part). The backend still accepts `aoi` as a fallback, but the plugin no longer sends it.

### Intersecting AOIs are merged
Before the features are built, intersecting polygons are dissolved into one, for the same reason
as in a regular processing (see 002_B "Submitted AOI geometry"): overlapping AOIs would otherwise
be searched — and billed — twice over the shared area. Merging applies to overlaps between
features and between the parts of one MultiPolygon feature. The same dissolve is applied when
AOIs are added to an existing template by drawing them on the map, and when an AOI's geometry is
updated (`POST …/aoi/{aoiId}`).

A merged AOI can carry only one name:

- when the merged polygons agree on a name — one name shared by all of them, some of them
  unnamed — the merged AOI keeps that name, and nothing is asked;
- when they carry **two or more different names** there is no non-arbitrary choice, so the name is
  dropped (`null`) and the user is **asked first**: *"Your AOIs will be merged and name
  information will be lost, do you want to continue?"*. Cancelling aborts the creation (or the
  AOI-add) silently, leaving the user to resolve the overlap in the source layer.

Only the merged AOIs lose their names; AOIs that do not intersect anything keep theirs.

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

The AOI aggregate status is kept current from the polled `/processings` (statuses synced
into the cached grouping), so it does not require re-fetching the full template each tick.

### Polling

The in-template poll is a **single** `GET …/processings` request per tick (no `get_template`,
no `images`), and runs on a **slower** cadence than the project processings list. The
imagery-search (`images`) endpoint is only hit on enter, on the "See search results" action,
and on AOI selection (S7) — never from the poll. The table is re-rendered with selection
signals blocked so a poll does not re-trigger the AOI search filter or rebuild map layers.

Template Progress (`100% × covered AOI area / total AOI area`, i.e. the share of the
template's AOI area processed at least once) is **not implemented (#WARNING)**: it is not
derivable from existing responses without geometric union/difference of AOI vs processing
footprints; it should be computed by the backend and exposed on the template instead.

Selecting one or more AOI rows filters the imagery-search results (both table and
footprint layer) to images intersecting any of the selected AOIs (all selected ids
are sent as `aoiIds` on the template images request). Deselecting all AOIs restores
the full template results.

Selecting one or more AOI rows also sets the processing **Area** to the union of the
selected AOIs' geometries, so a processing started from the template covers exactly
those AOIs. Selecting no AOI (e.g. while a processing row is selected) keeps the
current Area; the template's AOIs are not auto-selected as the Area on open.

### Filtering template results

A **Filter** button (shown only while viewing a template) re-issues the template images
request with the current search-filter widgets applied **server-side**. The
`POST …/template/{id}/images` body accepts `acquisitionDateFrom`/`acquisitionDateTo`,
`minResolution`/`maxResolution`, `maxCloudCover`, `minOffNadirAngle`/`maxOffNadirAngle`
(plus `aoiIds`, `limit`/`offset`, `sortBy`/`sortOrder`) and returns the filtered, paginated
result with the filtered `total` — a read-only filtered **view** of the template's results;
it does **not** modify the template. The plugin sends the supported subset it exposes in the
UI (date range + cloud cover); `minAoiIntersectionPercent`, `hideUnavailable`, `dataProviders`
and `productTypes` are **not** accepted by this endpoint and are not sent. The applied filter
is sticky for the template view — it carries across AOI selection and pagination — and is
cleared on leaving the template. Starting a new (non-template) search or a Plan Search is a
separate action from filtering an open template's results.

### Updating a template

Three client actions edit an existing template (distinct from *filtering* its results,
which is read-only):

- **Update search parameters** (an **"Update template"** button on the Imagery Search tab,
  shown only while a template is open — so the widgets reflect that template): `PUT
  /processings/template/{id}` with `searchParams` built from the current search-filter widgets
  (dates, cloud, resolution, intersection, hide-unavailable, providers, product types) and
  **no** geometry — the backend merges them, preserving the AOIs. Only `name` + `searchParams`
  are sent; `processingParams` is **omitted** (its backend type has a required `rest` field, so
  an empty/partial object fails to decode — omitting it makes the backend preserve the stored
  value), as is `activeUntil`.
- **Update AOI from current layer** (AOI-row context-menu action): replace one AOI's geometry
  with the current polygon layer's geometry via `POST …/aoi/{aoiId}` (`{ geometry }`). Used
  after the user manually edits a layer. Requires an AOI with a persisted `id`.
- **Exclude from search** (processing-row context-menu action, inside a template): the
  processing's already-processed area is removed from the template's search geometry —
  `new AOI geometry = AOI geometry − processing footprint`. A processing is linked to **every**
  AOI it intersects, so the subtraction is applied to **each** such AOI (`POST …/aoi/{aoiId}`);
  an AOI fully consumed by the subtraction is deleted (`DELETE …/aoi`). This mirrors the
  backend's `updateTemplateGeometry` behaviour (which subtracts the geometry at processing-run
  time) but is applied on demand to an already-created processing — the area is already being
  processed, so the user typically no longer wants the template to keep searching over it.

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

### Search area limit (Plan Search prompt)
`GET /user/status` also exposes `searchAreaLimit` (number, square metres): the maximum
AOI area allowed for an *immediate* imagery search. When the user triggers a regular
search with an AOI larger than this limit, the plugin does not run the immediate search;
instead it prompts:

> The search area is too large for immediate processing. The Planned Search will be
> created and run in the background. You will be notified when results are available.

with **[Cancel]** and **[Plan Search]**. Choosing **Plan Search** creates a template in
the currently selected project (`POST /processings/template`) auto-named
`Searching <YYYY-MM-DD HH:MM>`. If the AOI also exceeds `templateAreaLimit`, the existing
template-area-limit message is shown and no template is created. A missing or zero
`searchAreaLimit` disables the prompt and lets the immediate search proceed.

### Error feedback
When the backend rejects template creation because the limit is exceeded it returns
the standard error model (`{"code", "message", "params"}`) with a generic
`code` (e.g. `BAD_REQUEST`) and a human-readable `message`. The plugin resolves the
error to a single, translatable description (see the central error registry in
`mapflow/errors`) rather than surfacing the raw backend text.