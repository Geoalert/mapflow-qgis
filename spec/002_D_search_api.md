# 002_D Imagery Search API

## Purpose
Define the REST API contracts for imagery search consumed by this plugin.

## Endpoints

### `GET /catalog/meta`
Search imagery across providers. Accepts provider type and spatial/temporal filters.

### `GET /meta/skywatch/id`
Sentinel-2 metadata lookup by ID.

## External APIs (non-Mapflow) — LEGACY

### Maxar SecureWatch WFS
- URL: `https://securewatch.digitalglobe.com/catalogservice/wfsaccess`
- Protocol: XML WFS GetFeature
- Purpose: image metadata search
- Auth: ConnectID credential (user-provided or Geoalert default)

### Maxar WMTS
- URL: `https://securewatch.digitalglobe.com/earthservice/wmtsaccess`
- Purpose: tile service for image preview

### Sentinel-2 Preview
- URL: `https://preview.skywatch.com/esa/sentinel-2/{id}.jp2`
- Purpose: JPEG2000 preview images
- Note: routed through Mapflow backend (no direct Skywatch auth from plugin)
