# 005 Interactions

## Purpose
Describe integration boundaries and interaction rules with external/internal systems.

## Content

### Mapflow Backend API
- Direction: outbound
- Protocol: HTTPS REST (JSON)
- Auth: Basic Auth (token) or OAuth2 (Keycloak)
- Timeout: 30 s default (`config.TIMEOUT_S`), 1 h for file uploads, and a longer one of its own for a
  result download (`config.RESULT_TIMEOUT_S`). **Every request has a timeout**: none waits on the network
  stack alone.
- Retry: only what a timer sends again anyway — see § Failed requests. Nothing retries a request that
  changes server state.
- Failure handling: parse error response (multiple formats), display a user-friendly message in the QGIS
  message bar or next to the control that failed. No modal dialog opens for a failed request, with one
  exception: an upload that Mapflow refuses because the collection already has the file asks what to do
  (upload again, skip, cancel), since the upload cannot go on without the answer.

### Failed requests

A failed request nobody is waiting on is not worth interrupting the user: the next attempt usually
succeeds. A failed request the user just triggered is, at once. And a failure that asking again cannot
change must end the asking. Three rules follow, by **what triggered the request**, not by its endpoint
(the processings page is both the 6 s refresh and "Show more").

| the request is | a transient failure | a permanent failure |
|---|---|---|
| one the user just triggered and is waiting on (a click, a search, a run, an upload) | shown at once | shown at once |
| a one-off load nobody is waiting on (collections and image lists, the project list, what loads after sign-in) | shown once in the message bar, and whatever was marked as pending is cleared | the same |
| one a timer sends again on its own (the processings list, the account status, the collections refresh) | dropped and logged until `POLL_FAILURES_BEFORE_ALERT` consecutive attempts have failed, then said **once**; any success resets the count | the timer stops asking, and the user is told why |

- **Transient** means the connection or the server, not the request: a timeout, 500/502/503/504, a
  refused or dropped connection, host not found, a proxy failure. **Permanent** is every other answer —
  403, 404 and the other 4xx: asking again cannot change it. (401 is the session's: it renews the token
  or signs the user out.)
- **No failure is silent for good.** A list that failed to load must not look like an empty list:
  "No processings in this project yet" is shown only after a successful answer with no items.
- **A failed load leaves nothing pending.** A flag set before the request ("loading", "use this
  collection when it arrives") is cleared in the failure path as well as in the success path, so the
  control that set it works again.
- **The open project is gone** (the processings list answers 403 or 404 — deleted or unshared in Mapflow
  Web): the poll stops, the user is told, and the plugin opens the default project.
- **Only reads may be sent again.** A create that timed out may still have landed, and sending it again
  would create twice.
- `POLL_FAILURES_BEFORE_ALERT` lives in `config.py`: it is a first guess for live use to move.

The 3.x plugin implemented these rules as a required `mode` argument of its HTTP client
(`INTERACTIVE` / `BACKGROUND` / `POLL`). Mapflow Next is free to implement them another way; what is
specified is the behaviour in the table.

### Keycloak (OAuth2)
- Direction: outbound (browser redirect + token exchange)
- Protocol: OpenID Connect Authorization Code with PKCE
- Hosts: `auth.mapflow.ai` in production, `auth-{env}.mapflow.ai` in staging, internal and duty
  (see `002_api.md`)
- With the variable `mapflow_ru`, the same hosts on the domain `mapflow.ru` (`002_api.md` § The `mapflow.ru` domain)
- Local redirect: `http://127.0.0.1:7070/qgis`, served by a listener the plugin opens for the sign-in
- Token storage: the refresh token in the QGIS authentication database (encrypted); the access token in
  memory only
- Token refresh: by the plugin's own timer, ahead of expiry, with a retry through a network hiccup.
  QGIS's OAuth2 authentication method is not used

### QGIS Application
- Direction: bidirectional
- Inbound: layer events, canvas changes, project open/save, settings access
- Outbound: add/remove layers, apply styles, zoom canvas, display messages, persist settings
- Protocol: QGIS Python API (qgis.core, qgis.gui)
- Layer types produced: QgsVectorLayer (a result saved as GeoPackage), QgsRasterLayer (XYZ tiles, preview
  pictures), QgsVectorTileLayer
- Persistence: QgsSettings for plugin config, the QGIS authentication database for secrets
- **The GUI thread is not blocked by a result.** Converting a downloaded result (it can be hundreds of
  megabytes) to GeoPackage runs in a background task (`QgsTask`); only adding the finished layer to the
  project happens on the GUI thread.
- **A basemap provider without a preview has no preview control.** The 3.x plugin added an OpenStreetMap
  layer in its place; Mapflow Next adds nothing, because a layer that is not the imagery says nothing
  about the imagery.

### Local Filesystem
- Direction: outbound (write)
- Purpose: save processing results (GeoPackage), download raster previews, save My Imagery images the user downloads
- Location: user-configured output directory; a downloaded My Imagery image goes to the path the user picks
  (see `002_C_myimagery_api.md` § Client-side download)
- Failure handling: display permission/space errors to user
