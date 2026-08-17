# Journal for active implementation planning

## 1. Add new zoom-selector feature
[ ]
- Use 002_E_zoom_selector_api.md
- Add a small button near zoom selector comboBox to call zoom-selector API, active when selected source is a Mapflow data provider.
- On button press, call API and select zoom automatically depending on response.
- On error, show a reasonable user-facing message.

## 2. Refactor try/except for more granular exception handling
[ ]
- The 3.6.0 security scan flagged several broad `try/except Exception` blocks that only logged
  (previously swallowed silently). Narrow them to the specific exceptions actually expected, so
  unrelated errors surface instead of being logged and ignored.
- Also revisit the `assert` statements in errors/error_message_list.py (Bandit B101: asserts are
  stripped under `python -O`) — turn the sanity checks into real error handling if they must run.

## 3. Hotfix 3.6.1: dissolve intersecting AOI polygons
[ready-for-review]
- `QgsGeometry.collectGeometry` (not a union) was the single root cause: a MultiPolygon's area is
  the sum of its parts, so any overlap was measured, processed and billed once per polygon. A real
  layer of two nearly-coincident AOIs reported 2203.96 sq.km instead of 1108.96 — an ~2x overcharge.
- Fixed at the point where the geometry is built, not where it is measured: `app_context.aoi` feeds
  both the Area label and the submitted geometry, so dissolving there keeps "shown = sent = billed"
  true by construction. Template `aoiDetails` needed its own dissolve — it is built from the layer
  directly, bypassing `app_context.aoi`.
- `maxAoisPerProcessing` is now counted on the dissolved geometry: the count must describe what the
  backend receives, otherwise overlapping polygons could be rejected for a limit they don't reach.
- Union failures fall back to the old plain collection: GEOS raises on invalid rings, and an
  over-counted AOI is still better than no AOI (the backend re-validates anyway).
- Merging is lossy only for names, so the confirmation prompt is raised exactly when two or more
  *different* names merge — an unnamed neighbour or a shared name loses nothing and must stay silent,
  otherwise the prompt becomes noise that users click through.
- Declining raises `AoiMergeDeclined`, deliberately NOT a `PluginError`/`ValueError`: the callers
  must abort silently, and the existing `except ValueError` would have shown an error box on top of
  the question the user just answered.
- Spec delta approved by user: 002_B "Submitted AOI geometry", 002_F "Intersecting AOIs are merged".
