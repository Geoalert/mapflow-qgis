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
