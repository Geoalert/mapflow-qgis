# Specification index
This document describes the scope of each spec file.
All spec files are created in this directory.

## 001_goal.md
Full scope of the application: why it exists and what problem it solves.

## 002_api.md
REST API contracts consumed by the plugin: Mapflow backend endpoints, external APIs (Maxar, Sentinel), authentication, error model.

## 003_local_storage.md
Local persistence: QgsSettings keys, QGIS Auth Manager (OAuth2), temporary files. Full key inventory derived from code.

## 004_stack.md
Used libraries, pinned versions where important, and external system implementation choices.

## 005_interactions.md
Integration boundaries: Mapflow backend, Maxar WFS, Sentinel/Skywatch, Keycloak OAuth2, QGIS application, local filesystem.

## etc.
Additional documents can be added with increasing numeric prefixes (for example: `006_security.md`, `007_observability.md`).