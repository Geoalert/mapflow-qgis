# refactor/extract-preview-service

Phase C, second extraction. Scratchpad — gitignored.

## Decisions taken at the gate

1. **PreviewService owns preview *layers on the map*.** That takes the `mapflow.py` search
   previews and the two My Imagery map-layer methods (`mosaic_preview`, `get_image_preview_l` →
   `display_image_preview`). It does **not** take `get_image_preview_s`, which paints a `QImage`
   into a panel widget — a thumbnail, not a layer, so it stays with the catalog.
2. **`ResultsLoader`'s four preview helpers stay put** (`add_preview_layer`, `add_aoi_to_preview`,
   `display_preview_with_gcp`, `georeference_preview_part`) and are called from the service.
   They are mechanical layer builders and Phase D moves `layer_utils` wholesale; moving them now
   churns a file that step rewrites.
3. **`_template_group_target` is split first** — scope change agreed at the gate. See below.
4. Widget reads stay in `mapflow.py` until the next step: everything preview touches
   (`metadataTable` selection, `providerIndex()`, the `cellClicked` reconnect) is a *search-tab*
   widget, and `SearchController` + `view/search_view.py` is the step immediately after this one.

## Why `_template_group_target` comes first

It is find-**or-create**: asking where the template's layer-tree group is materialises it. Both
`AoiService.select_aois_as_processing_area` and `_relocate_preview_to_template_group` are on
paths that fire on every selection / every preview, so neither can call it eagerly. The AOI step
worked around it with a `group_factory` lambda whose only job is to defer a side effect.

That workaround was going to be written a second time here. Splitting the function into a pure
`find` and an explicit `ensure` removes it from both, and deletes the note the templates step
was carrying instead of growing it.

Note the create-if-missing looks defensive rather than load-bearing on these two paths: the
template group already exists by the time a template's AOIs can be selected or its previews
placed, because opening the template draws its AOI display layers through the same function.
The paths that legitimately *create* are the ones that add the first layer.

## Ownership moves

`_pending_preview_ids` and `_mosaic_preview_footprint_id` move onto `PreviewService`. Both are
dedup state for preview layers and nothing outside the preview code reads them.

## Tests

* `tests/qgis/behavioral/test_preview.py` (5) covers the journey end-to-end and names no
  internals — it is the safety net and must keep passing untouched.
* 16 `Class.__new__` tests move to the new owner: `test_preview_dedup` (3),
  `test_preview_null_metadata` (3), `test_template_preview_layers` (3),
  `test_template_group_and_preview` (7).

## Discoveries

**`report_http_error` needed the same treatment as `alert` — an unplanned second prerequisite.**
`preview_png_error_handler` reports a failed download through `ErrorMessageWidget`, a dialog, so
the service could not call it. Options were to downgrade it to a plain alert (a behaviour change,
losing the mail-report path), to emit a signal (the ceremony that was pushed back on last step),
or to move it into the message tier next to `alert_*` and `ask_text`. Took the third. It has nine
callers in `mapflow.py` and four of them belong to steps still to come (templates, processing,
auth), so this would have recurred regardless.

**The deferred dialog import is an established pattern here, not a way round the layering test.**
`error_guard.report_unexpected_error` already imports `ErrorMessageWidget` inside the function,
and its comment gives the real reason: the module is imported early, the dialog pulls in the Qt
widget tree, and laziness lets a headless context use the logging half. My first version of the
comment justified it as keeping `dialogs/` out of a service module — which would have been the
test dictating the design rather than the reverse. Corrected.

**Ten stranded imports in `mapflow.py`** (`gdal`, `Tuple`, `OSM`, `ImageIdRequired`,
`MultiPreviewList`, `PreviewType`, `QgsRasterLayer`, `QgsRectangle`, `QgsLayerTreeLayer`,
`QgsCoordinateReferenceSystem`) — none visible to lint, all found with the AST check. Concrete
evidence for the cost recorded on the `F401` WAL entry.

**`_relocate_to_template_group` kept its blanket `except (AttributeError, RuntimeError)`.** It is
the pre-existing behaviour and the layer-tree calls it wraps can genuinely raise on a deleted
node; narrowing it is not this step's business.

## Mutation verification

Three mutations on the moved code, all reverted:

A. `preview_catalog` drops the in-flight guard → `test_preview_catalog_skips_when_download_in_flight`
   fails **and** so does the behavioral
   `test_a_second_click_while_downloading_does_not_download_again`. The safety net caught a
   regression in moved code without naming any internal, which is the whole reason it exists.
B. `_add_aoi_to_preview_if_needed` drops the in-template check →
   `test_add_aoi_to_preview_skipped_in_template_mode` fails.
C. `_relocate_to_template_group` always appends at the bottom →
   `test_relocate_preview_places_it_above_footprints_inside_template_group` fails.

**The three My Imagery methods had no test coverage at all.** Moving them broke nothing — 577
tests passed before and after the move, which is the tell. `spec/007_architecture.md` says a step
that moves code must not leave a behaviour covered by neither suite, so
`tests/qgis/test_my_imagery_preview.py` was written against the new owner (7 tests,
mutation-verified). Two of them cover cases the old code handled silently through a bare
`except AttributeError`: a collection with no imagery yet (no `rasterLayer`), and a preview that
failed to georeference (`display_preview_with_gcp` returns None).

## Result

`mapflow.py` 4078 → 3761 lines across the branch. `PreviewService` 458, `DataCatalogService`
shed its three map-layer preview methods.

`DataCatalogController` now takes `preview_service` as well, and is constructed after it — which
forced `PreviewService` construction to sit between `processing_service` and the catalog
controller. That ordering is load-bearing and easy to break: building the controller first fails
every catalog test at fixture setup.
