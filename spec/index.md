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
Data Catalog (My Imagery): mosaics, images, upload, download, storage limits. Includes `GET /rasters/image/{image_id}/download` for presigned S3 download URLs, and how the plugin streams the image to disk.

### 002_D_search_api.md
Imagery Search: Mapflow catalog search.

## 002_F_plan_processing_api.md
Planned processing: create/list/update/delete, run from template, and template status/actions.
Mapflow Next only lists planned processings and opens them in Mapflow Web (§ Plugin behaviour in Mapflow Next).
Also covers template AOI management (add/update/delete, naming, `aoiDetails` structure)
and the in-template navigation level (Projects → Processings → Template).

## 002_E_zoom_selector_api.md
The data-catalog service's API as that service documents it (its title is "API Specification"). It is
kept as reference: it is not the zoom selector API the file name promises, and it does not list
`validate-image-metadata` or `allow_duplicate`, which the plugin uses (`mapflow_next/api/client.py`).
Open: neither is specified in `002_C_myimagery_api.md` yet.

## 003_local_storage.md
Local persistence: QgsSettings keys under `mapflow_next`, the QGIS authentication database, the layer group, temporary files. No migration from the 3.x plugin.

## 004_stack.md
Used libraries, pinned versions where important, external system implementation choices, the test runtime, and the static-analysis toolchain.

## 005_interactions.md
Integration boundaries: Mapflow backend, Keycloak OAuth2, QGIS application, local filesystem.

## 006_error_reporting.md
How failures reach the user: the expected/unexpected split, the three presentation tiers (log / message / report dialog), the guard, the report dialog, and why no dialog opens from a timer-driven path.

## 007_architecture.md
Module structure. § Mapflow Next (4.x) is the structure of `mapflow_next/`: the layers, what each may import, unload, and where the code is not there yet. The rest is the 3.7.0 refactoring analysis of the 3.x plugin, kept as rationale.

## etc.
Additional documents can be added with increasing numeric prefixes (for example: `008_security.md`, `009_observability.md`).