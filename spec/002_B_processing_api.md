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
