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
Imagery Search: Mapflow catalog search.

## 002_F_plan_processing_api.md
Planned processing: create/list/update/delete, run from template, and template status/actions.
Also covers template AOI management (add/update/delete, naming, `aoiDetails` structure)
and the in-template navigation level (Projects → Processings → Template).

## 002_E_zoom_selector_api.md
Zoom selector API for automatic zoom detection based on imagery source resolution.

## 003_local_storage.md
Local persistence: QgsSettings keys, QGIS Auth Manager (OAuth2), temporary files. Full key inventory derived from code.

## 004_stack.md
Used libraries, pinned versions where important, external system implementation choices, the test runtime, and the static-analysis toolchain.

## 005_interactions.md
Integration boundaries: Mapflow backend, Keycloak OAuth2, QGIS application, local filesystem.

## 006_error_reporting.md
How failures reach the user: the expected/unexpected split, the three presentation tiers (log / message / report dialog), and the suppression contract that bounds dialog volume on timer-driven paths.

## 007_architecture.md
Target module structure for the 3.7.0 refactoring: the layers (api / service / controller / view / model), what each may import, where the entry points are, and the test surfaces the refactoring is verified against.

## etc.
Additional documents can be added with increasing numeric prefixes (for example: `008_security.md`, `009_observability.md`).