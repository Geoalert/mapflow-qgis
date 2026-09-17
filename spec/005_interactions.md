# 005 Interactions

## Purpose
Describe integration boundaries and interaction rules with external/internal systems.

## Content

### Mapflow Backend API
- Direction: outbound
- Protocol: HTTPS REST (JSON)
- Auth: Basic Auth (token) or OAuth2 (Keycloak)
- Timeout: 10s default, 1h for file uploads
- Retry: decided per request by its **mode** — see § Request modes. Nothing retries a request that
  changes server state.
- Failure handling: parse error response (multiple formats), display user-friendly message via QMessageBox or QGIS message bar

### Request modes

A failed request nobody is waiting on is not worth a dialog: the next attempt usually succeeds. A
failed request the user just triggered is, and a hidden retry would only add seconds of silence
before it — the user can press the button again. So every request declares which it is, as
`Http`'s `mode` argument, and **there is no default**: a request nobody classified fails at the call.

| mode | declare it for | a transient failure is |
|---|---|---|
| `INTERACTIVE` | a request the user just triggered and is waiting on | handed to the error handlers at once |
| `BACKGROUND` | a one-off request nobody is waiting on — a refresh sent from another response's callback, the data loaded after login | re-sent once after `BACKGROUND_RETRY_DELAY_SECONDS`, and handed to the handlers only if that fails too |
| `POLL` | a request a timer sends again on its own | dropped (and logged) until `POLL_FAILURES_BEFORE_ALERT` consecutive attempts at the same endpoint have failed; any success on that endpoint resets the count |

- **Transient** means the connection or the server, not the request: a timeout, 500/502/503/504,
  a refused or dropped connection, host not found, a temporary network failure. Anything else —
  401, 403, 404 and every other 4xx — is handed to the handlers at once in every mode: asking again
  cannot change the answer.
- **The mode belongs to the trigger, not the endpoint.** One endpoint is often reached from a timer
  and from a click — the processings page is the 6 s refresh, and also paging, sorting and
  filtering. So an api method for a read takes the mode as a required parameter and the caller that
  knows the trigger passes it. A follow-up request sent from a response's callback to complete the
  same data inherits that response's mode.
- **Only reads may retry.** An api method for a request that changes server state declares
  `INTERACTIVE` itself: a create that timed out may still have landed, and sending it again would
  create twice. For the same reason nothing but `INTERACTIVE` accepts a multipart upload body, which
  the first send consumes.
- **A `BACKGROUND` request still gets exactly one outcome** — its callback or its error handler —
  only later, unless logout or `unload` cancels its re-send (below); whatever those cancel is the
  session's or the plugin's to clean up, not the request's. A dropped `POLL` failure gets **none**,
  so a `POLL` request takes no error handler of its own: cleanup placed there would silently not
  run (`spec/006` § A guarded callback is interrupted, not completed).
- A timer-driven request that counts its own attempts and needs every failure — the post-login
  `/user/status` retry — is `INTERACTIVE`, not `POLL`: its budget is the tolerance.
- A pending `BACKGROUND` re-send is cancelled on logout, where it would go out without credentials,
  and on `unload`, like any other subscription that would outlive the plugin (`spec/007` § The
  composition root). After `unload` a late failure schedules no new one.
- `BACKGROUND_RETRY_DELAY_SECONDS` and `POLL_FAILURES_BEFORE_ALERT` live in `config.py`, next to the
  throttle's numbers and for the same reason: they are a first guess for live use to move.

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
