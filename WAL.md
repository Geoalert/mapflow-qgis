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

## 3. Hotfix 3.6.1: count an overlapping AOI's area once
[ready-for-review]
- Root cause is `measureArea` over a collected (not unioned) MultiPolygon: its area is the sum of
  the parts, so an overlap is added once per polygon. A real layer of two nearly-coincident AOIs
  showed 2203.96 sq.km instead of 1108.96 — the price follows the same number.
- Scope deliberately stops at the measurement. The first attempt also unioned the submitted
  geometry; that is unnecessary (the backend unions on start, and cost will union too) and actively
  wrong for Planned Search, where intersecting named AOIs are a feature: "City" enclosing
  "District 1"/"District 2", each keeping its own results. Union what we measure, send what the
  user drew.
- The union sits inside `layer_utils.calculate_aoi_area`, so every consumer of `aoi_size` (Area
  label, cost estimate, aoiAreaLimit / templateAreaLimit / provider-minimum checks) agrees with the
  backend without each caller remembering to dissolve.
- A failed union falls back to measuring the geometry as-is: GEOS raises on invalid rings, and an
  over-counted area beats a broken area display.
- Not touched, on purpose: `maxAoisPerProcessing` still counts the source polygons, and
  `max_aoi_bbox_area` still takes the per-part bounding box. Both now differ slightly from what the
  backend sees after its own union — worth revisiting if a user hits it, not worth widening a
  hotfix for.
- Spec delta approved by user: 002_B "AOI area measurement".
