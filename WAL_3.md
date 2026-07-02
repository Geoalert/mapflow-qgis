# WAL_3 — Track uploaded image preprocessing status

Handover for WAL step 3, branch `feature/track-uploaded-image-status`.
Spec: `spec/002_C_myimagery_api.md` (status endpoints + status_summary, added this branch),
`spec/003_local_storage.md` (`hideUnprocessedImages`). Source API: `data-catalog/spec/002_api.md`.

## Goal (agreed with user)
Uploaded images must not vanish while preprocessing, and failed ones must be visible and manageable.
- Preprocessing image → row with "Preprocessing" flag.
- Failed image → "Preprocessing failed" flag, deletable via normal DELETE.
- Setting to hide these rows (default: show).
- Mosaic table shows per-mosaic counts (✓ ready / 🕑 preprocessing / ✗ failed) from `status_summary`.

## Decisions (from user)
- Auto-poll `/status` (~10s) while any image is pending/in_progress.
- Add mosaic-level "Delete failed" (`DELETE /mosaic/{id}/failed`).
- Setting default = show unprocessed rows.

## Key backend fact (verified in data-catalog source)
`image_repo.get_images_by_mosaic_id(..., only_available=True)` is the default, so
`GET /mosaic/{id}/image` returns **only** `data_available=true` images. Non-ready
(PENDING/IN_PROGRESS/FAILED) images appear **only** via `GET /mosaic/{id}/status`, which
carries just `filename/uploaded_at/preprocessing_status/error/data_available/tiles_ready`
(no size/footprint/preview/meta_data). → merge, don't replace.

## Architecture
- Ready images: `self.images` (`ImageReturnSchema`, full metadata) — used by preview/selection/etc.
- Non-ready images: `self.image_statuses` (`ImageStatusSchema`) — flagged rows only.
- Load flow: `get_mosaic_images` → `_on_mosaic_images_loaded` (fetch `/image`) →
  `_on_mosaic_status_loaded` (fetch `/status`, merge) → `_render_mosaic_images`.
  `/status` error → `_on_mosaic_status_failed` → ready-only render (graceful).
- Poll: `QTimer(10s)` started/stopped by `_manage_status_polling` based on pending presence;
  `_poll_open_mosaic_status` re-loads with `is_poll=True`; `_render_mosaic_images` skips the
  re-render (and preview/selection reset) when `_image_signature` is unchanged.
- Selection/delete: `selected_images()` maps ids to both dicts; both row types expose `.id`/`.filename`.
  Single-image actions guarded by `_is_full_image` (isinstance `ImageReturnSchema`).

## Files touched
- `mapflow/schema/data_catalog.py`: `PreprocessingStatus` (+`_missing_` tolerant),
  `MosaicStatusSummary` (+`preprocessing`/`has_activity`), `status_summary` on `MosaicReturnSchema`,
  `ImageStatusSchema` (+`id` alias/`is_ready`/`is_failed`), `MosaicStatusResponse` (+`non_ready_images`).
- `functional/api/data_catalog_api.py`: `get_mosaic_status`, `delete_failed_images`.
- `functional/service/data_catalog.py`: merge/poll/gating flow, `confirm_delete_failed_images`,
  `on_hide_unprocessed_toggled`, selection guards.
- `functional/view/data_catalog_view.py`: mosaic Status column + `_status_summary_text/_tooltip`,
  image Status column + `_set_image_row`, `show_image_status_info`, `set_failed_images_present`.
- `functional/controller/data_catalog_controller.py`: wire `deleteFailedButton` + setting toggle.
- `dialogs/main_dialog.{py,ui}`: `hideUnprocessedImages` checkbox, `deleteFailedButton`.
- `tests/qgis/test_data_catalog.py`: 28 tests (all green).

## Test / lint status
- `agent-make test-qgis`: 194 passed, 1 failed — the 1 is pre-existing
  `test_processing_aoi_geometry::test_processing_geometry_uses_cropped_aoi` (fails on clean `dev`).
- `agent-make test-functional`: 6 passed. UI tier: 0 tests collected.
- `agent-make lint`: red on **pre-existing** issues only (mapflow.py B006, display_image_preview B008,
  test_layer_utils F403/F405). Changed files: ruff-clean, pyright-clean.

## Endpoint bucketing gotcha (important)
The mosaic-list `status_summary` badge buckets by `preprocessing_status`
(`ready = NONE + COMPLETED`), but `GET /mosaic/{id}/status` buckets `ready` by
`data_available` first. So an image can be `data_available=true` (present in `/image`)
yet `PENDING`/`IN_PROGRESS`. We flag non-ready rows by `preprocessing_status` (so the
per-image flags always match the mosaic 🕑/✗ badge) and **dedupe** the ready `/image`
list against those ids — otherwise such an image would render twice, or (if flagged by
`data_available`) show no flag while the badge says 🕑.

## UI polish (review round 1)
- Mosaic + image Status columns are **fixed-width** (sized to the full 3-segment line /
  "Preprocessing failed") so they don't jump on status changes.
- Status cells are **non-selectable** (`Qt.ItemIsEnabled` only) and row controls are always
  anchored to the name column (`NAME_COLUMN`), so clicking the status column never relocates
  the controls into it.

## Known limitations / follow-ups
- Placeholder glyphs (✓/🕑/✗) — user will swap for real icons.
- Mosaic-list counts refresh on manual refresh/reopen (polling is scoped to the open image list).
- Non-ready rows show no size/preview (API limitation).
- Deleting an image still navigates back to the mosaic list (pre-existing behavior, unchanged).
