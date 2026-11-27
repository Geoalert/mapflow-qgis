# 001 Goal

## Purpose
Describe why this project exists and what business/user problem it solves.

## Content

Problem statement: GIS professionals need to extract real-world features (buildings, roads, forests, agricultural fields, construction sites) from satellite imagery using AI — without leaving QGIS.

Target users: GIS analysts, remote sensing specialists, urban planners, agricultural/forestry professionals, and organizations needing automated feature extraction from satellite imagery.

Success criteria:
- Users can authenticate, select a model and imagery source, define an AOI, and submit processing jobs from within QGIS.
- Processing results load as native QGIS layers (vector layers saved as GeoPackage, raster tiles, vector tiles) with appropriate styling.
- Users can manage their imagery collections (upload, mosaic, search) and projects within the plugin.
- The plugin supports multiple data providers (Mapflow basemaps and imagery catalog, user uploads, custom XYZ/TMS).
  Custom XYZ/TMS sources are not configured in the plugin: the user picks one of the XYZ/TMS tile layers
  that QGIS already has, and the plugin turns its QGIS description into the API's source parameters, or
  says why it can't.

Non-goals:
- Implementing AI/ML models locally — all inference runs on the Mapflow backend.
- Replacing the Mapflow web application — the plugin is a QGIS-native interface to a subset of Mapflow functionality.
- Supporting QGIS versions below 3.28. 3.28 is the oldest version the tests run on; an older one is not
  declared in `metadata.txt`.
- Migrating the settings of the 3.x plugin. Mapflow Next installs next to it under its own settings group,
  and a user who moves over signs in and sets the output folder again.

Constraints:
- Must use QGIS-native networking (QgsNetworkAccessManager) for proxy/firewall compatibility.
- Must run on both Qt 5 (QGIS 3.28+) and Qt 6 (QGIS 4) from one code base. The rules that
  keep it so are in `README.md` § QGIS 3 and QGIS 4, and the tests check them.
- All HTTP communication goes through the Mapflow REST API; no direct database access.
