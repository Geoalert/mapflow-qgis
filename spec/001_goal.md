# 001 Goal

## Purpose
Describe why this project exists and what business/user problem it solves.

## Content

Problem statement: GIS professionals need to extract real-world features (buildings, roads, forests, agricultural fields, construction sites) from satellite imagery using AI — without leaving QGIS.

Target users: GIS analysts, remote sensing specialists, urban planners, agricultural/forestry professionals, and organizations needing automated feature extraction from satellite imagery.

Success criteria:
- Users can authenticate, select a model and imagery source, define an AOI, and submit processing jobs from within QGIS.
- Processing results load as native QGIS layers (vector GeoJSON, raster tiles, vector tiles) with appropriate styling.
- Users can manage their imagery collections (upload, mosaic, search) and projects within the plugin.
- The plugin supports multiple data providers (Mapflow basemaps, Maxar SecureWatch, Sentinel-2, user uploads, custom XYZ/TMS).

Non-goals:
- Implementing AI/ML models locally — all inference runs on the Mapflow backend.
- Replacing the Mapflow web application — the plugin is a QGIS-native interface to a subset of Mapflow functionality.
- Supporting QGIS versions below 3.20.

Constraints:
- Must use QGIS-native networking (QgsNetworkAccessManager) for proxy/firewall compatibility.
- Must use PyQt5 (not PyQt6) as bundled with QGIS 3.x.
- All HTTP communication goes through the Mapflow REST API; no direct database access.
