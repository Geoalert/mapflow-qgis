# 002_A Project API

## Purpose
Define the REST API contracts for project management consumed by this plugin.

## Endpoints

### `POST /projects`
Create a new project.

### `GET /projects/{id}`
Get project details. Response includes `billingType`, `workflowDefs`, `shareProject`.

### `POST /projects/page`
List projects with pagination.

### `PUT /projects/{id}`
Update project name/settings.

### `DELETE /projects/{id}`
Delete a project and its resources.

## Plugin behaviour

- **Rename** (name and description) and **delete** are offered to the project's owner, and never for the
  default project. Delete asks for confirmation first: it removes the project's processings with it.
- **Sharing** stays in Mapflow Web: the plugin's "Share" opens the project there.
- The list is paged (`POST /projects/page`), most recently updated first, with the name search applied on
  the server (`filter`). The plugin offers no other sort order.
