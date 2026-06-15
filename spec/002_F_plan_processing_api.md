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

### `POST /processings/template/{templateId}/image/{imageId}/seen`
Mark one image as seen for template.

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