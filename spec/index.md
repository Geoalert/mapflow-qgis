# Specification index
This document describes the scope of each spec file.
All spec files are created in this directory.

## 001_goal.md
Full scope of the application: why it exists and what problem it solves.

## 002_api.md
REST API contracts consumed by the plugin: authentication, error model, versioning. Acts as an index for endpoint sub-files:

### 002_A_project_api.md
Projects: CRUD, pagination, sharing.

### 002_B_processing_api.md
Processings: submit, list, update.

### 002_C_myimagery_api.md
Data Catalog (My Imagery): mosaics, images, upload, download, storage limits. Includes `GET /rasters/image/{image_id}/download` for presigned S3 download URLs.

### 002_D_search_api.md
Imagery Search: catalog search, external APIs (Maxar, Sentinel — legacy).

## 002_E_zoom_selector_api.md
Zoom selector API for automatic zoom detection based on imagery source resolution.

## 003_local_storage.md
Local persistence: QgsSettings keys, QGIS Auth Manager (OAuth2), temporary files. Full key inventory derived from code.

## 004_stack.md
Used libraries, pinned versions where important, and external system implementation choices.

## 005_interactions.md
Integration boundaries: Mapflow backend, Maxar WFS, Sentinel/Skywatch, Keycloak OAuth2, QGIS application, local filesystem.

## etc.
Additional documents can be added with increasing numeric prefixes (for example: `006_security.md`, `007_observability.md`).