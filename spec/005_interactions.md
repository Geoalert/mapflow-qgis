# 005 Interactions

## Purpose
Describe integration boundaries and interaction rules with external/internal systems.

## Content

### Mapflow Backend API
- Direction: outbound
- Protocol: HTTPS REST (JSON)
- Auth: Basic Auth (token) or OAuth2 (Keycloak)
- Timeout: 10s default, 1h for file uploads
- Retry: no automatic retry; user can re-trigger actions manually
- Failure handling: parse error response (multiple formats), display user-friendly message via QMessageBox or QGIS message bar

### Maxar SecureWatch
- Direction: outbound
- Protocol: WFS (XML over HTTPS) for metadata search; WMTS for tile preview
- Auth: ConnectID credential (user-provided or Geoalert default)
- Failure handling: parse HTML error responses, display to user

### Sentinel-2 (via Skywatch)
- Direction: outbound
- Protocol: HTTPS (JSON metadata, JPEG2000 preview)
- Auth: routed through Mapflow backend (no direct Skywatch auth from plugin)
- Failure handling: standard HTTP error display

### Keycloak (OAuth2)
- Direction: outbound (browser redirect + token exchange)
- Protocol: OpenID Connect Authorization Code with PKCE
- Local redirect: `http://localhost:7070`
- Token storage: QGIS Auth Manager (encrypted)
- Token refresh: automatic via Auth Manager before expiration

### QGIS Application
- Direction: bidirectional
- Inbound: layer events, canvas changes, project open/save, settings access
- Outbound: add/remove layers, apply styles, zoom canvas, display messages, persist settings
- Protocol: QGIS Python API (qgis.core, qgis.gui)
- Layer types produced: QgsVectorLayer (GeoJSON), QgsRasterLayer (XYZ tiles), QgsVectorTileLayer
- Persistence: QgsSettings for plugin config, QgsAuthManager for OAuth2 tokens

### Local Filesystem
- Direction: outbound (write)
- Purpose: save GeoJSON processing results, download raster previews
- Location: user-configured output directory
- Failure handling: display permission/space errors to user
