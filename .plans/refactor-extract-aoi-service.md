# refactor/extract-aoi-service

Phase C, first extraction. Scratchpad — gitignored.

## Decisions taken at the gate

1. **AoiService + a new `view/aoi_view.py`.** The service holds session state, geometry and the
   API calls; the view holds the panel hide/show, the Save/Cancel message bar, the name prompt
   and every `polygonCombo` read/write.
2. **`ProcessingController` is created now**, holding the start-processing AOI wiring. The
   existing `controller/processing_controller.py` (which holds `ProjectProcessingController`,
   a different row of the spec table) is renamed to `project_processing_controller.py`.

## The layering constraint that shapes the design

`spec/007_architecture.md`: a service may not import `view/` or `dialogs/` **and a view may not
import `service/`** (`view/` may import model, schema, dialogs — not service). Existing services
hold a `view` attribute; those are recorded violations in `tests/functional/test_layering.py`
and only shrink. So `AoiService` must not hold an `AoiView`, and `AoiView` must not hold the
service.

Consequence: everything crossing the boundary goes through the controller, or through a service
signal the controller subscribes to. Concretely, the two places that look like they need a
back-reference:

* `filter_aoi_layers` reads `dlg.useAllVectorLayers.isChecked()`. The service method takes the
  flag as an argument — `excepted_layers(use_all_vector_layers: bool)` — and the controller
  reads the checkbox through the view and pushes the result back to the view.
* The edit session hides the panel and shows the message bar. The service emits
  `editSessionStarted(str)` / `editSessionEnded()`; the controller subscribes and drives the
  view.

## Ownership moves

`app_context.aoi_layers` moves onto `AoiService`. Nothing outside the AOI code reads it (checked
across `mapflow/` and `tests/`), so leaving it on `AppContext` would keep one concept in two
homes — invariant 4.

## Out of scope, deliberately

* `filter_search_by_selected_aoi` — search filtering; goes with `SearchService`.
* `download_aoi_file` — a processing result, not AOI geometry.
* `_add_geojson_aoi_layer`, `on_template_aois_changed`, `_no_aoi_*` — building a *template's*
  AOI display layers, entangled with template groups. "Which AOIs a template has" is
  `TemplateService` by spec.
* Template-side connects (`dlg.aoi_add_action`, `aoi_update_geometry_action`, `aoi_draw_action`,
  `processingsTable.itemSelectionChanged → sync_processing_area_to_selected_aois`) stay in
  `mapflow.py` until `TemplateController` exists. The spec allows `mapflow.py` to hold wiring;
  it forbids domain logic.

## Tests

~25 existing tests pin this code through `Mapflow.__new__(Mapflow)`:
`tests/qgis/test_template_updates.py`, `tests/qgis/test_template_processing_area.py`. They move
to the new owner rather than being deleted — per spec, no step may leave a behaviour covered by
neither suite. The behavioral tier covers only the area/cost path through `polygonCombo`.

## Progress

Landed in `5976e2e`: the registry (`register_layer`/`unregister_layer`/`excepted_layers`) and
layer creation (`create_layer_from_rect`/`_from_imagery`/`create_editable_layer`), plus
`ProcessingController`, `AoiView`, and the `project_processing_controller.py` rename.

Left, and the shape each one has to take:

**1. The on-map edit sessions.** `add_aoi_from_layer_dialog`, `_selectable_aoi_layers`,
`start_update/draw_aoi_session`, `_find_aoi_layer`, `_begin/_show/_save/_cancel/_end`,
`_commit_aoi_update/draw`.
The session state machine, `_find_aoi_layer`, `_selectable_aoi_layers` and both commits go to
`AoiService`. The widget half — hiding the panel, the Save/Cancel message-bar widget, the name
prompt, the layer-picker dialog — goes to `AoiView`, reached only through the controller via
`editSessionStarted(str)` / `editSessionEnded()`.
Note the session also stops and restarts `processing_service.processing_fetch_timer`. That is a
second service, which `service/` may import, so it stays in the service.

**2. The selected-AOIs layer.** `sync_processing_area_to_selected_aois`,
`_layer_for_selected_aois`, `_rebuild_selected_aois_layer`, `_remove_selected_aois_layer`.
`_rebuild_selected_aois_layer` inserts into the *template's* layer-tree group via
`_template_group_target`, which is template work and stays in `mapflow.py` (→ `TemplateService`
later). So the service takes the target group as an argument — a `QgsLayerTreeGroup` is a QGIS
core object, not a widget, so this does not breach the layer rule. The combo update travels out
on the existing `currentAoiLayerChanged` signal rather than the service setting it.

**3. Two shared helpers with out-of-scope callers.**
`_aoi_features_from_layer` / `_polygon_aoi_features` are used by `_build_template_aoi_details`
(out of scope) as well as by both in-scope commits → move to `AoiService`, out-of-scope caller
goes through it.
`_geometry_from_geojson` is used by `_processing_footprints_by_aoi` and the template AOI display
layers (both out of scope) → move to `functional/geometry.py` as a free function instead, next to
`geojson_feature_area_sqkm`, which already does the same ogr dance. Putting it on `AoiService`
would make template code depend on the AOI service for a pure geometry conversion.

## Discoveries

**The inherited `_selectable_aoi_layers` test measured less than it claimed.** It asserted that
a template's AOI display layer is not offered as an AOI source, and the layer it used was both
tagged `mapflow/aoi_id` *and* inside the template's group — either exclusion alone hides it. So
deleting the tag check entirely left the test green (mutation 4, first run). Fixed by adding a
tagged layer outside any template group, which is also a real case: a display layer left behind
by another template, or one the user dragged out. Re-verified — the mutation now fails exactly
that test.

**`api_message_parser`-style dead guards have a sibling here:** `_commit_aoi_draw` used to
validate the name length *after* prompting, inside the service. The prompt moved to the view, so
the service validates a name it is handed. The check stays (the caller is not trusted) and is
pinned by `test_commit_draw_rejects_an_overlong_name`.

**F401 is in the `.flake8` ledger**, so lint does not catch imports left behind by a move.
`SelectAoiLayersDialog`, `AOI_NAME_MAX_LENGTH`, `AddAoisSchema` and `AddSingleAoiSchema` were all
dead in `mapflow.py` after the move and had to be found by hand. Worth remembering for every
later extraction: grep the moved names, do not rely on the linter.

## Mutation verification

Four mutations, run in the container:

1. `_commit_update` returns True on empty geometry → `test_commit_update_rejects_empty_geometry`
   fails.
2. `save_session` ends the session unconditionally →
   `test_save_session_ends_only_on_successful_commit` fails.
3. `Mapflow.save_aoi_session` ignores the prompt's cancel →
   `test_cancelling_the_name_prompt_keeps_the_session_open` fails.
4. `selectable_layers` drops the tag exclusion → **passed initially**; see Discoveries. After
   strengthening the test, fails exactly that test and nothing else.

All reverted.

### Selected-AOIs layer (third commit)

Three more mutations:

A. `select_aois_as_processing_area` drops the unchanged-selection guard →
   `test_unchanged_selection_does_not_rebuild_area` fails.
B. `_layer_for_selected_aois` uses `len(aois) == 0` instead of `== 1` →
   `test_single_aoi_points_the_area_at_that_aois_own_layer` and
   `test_missing_aoi_layer_leaves_the_area_untouched` fail.
C. `clear_processing_area_selection` stops clearing the filter →
   `test_leaving_the_template_forgets_the_selection` fails.

**A and C are not independent**, which the first run hid: with A applied there is no dedup guard
left for C to break, so the re-selection emitted anyway and C's test passed for the wrong reason.
Verified C on its own afterwards. Worth remembering — batching mutations only proves anything
when they cannot mask each other, and "different function" is not sufficient for that.

## Push-back accepted: the name prompt was a self-inflicted round trip

Reviewed in chat. I had `_commit_draw` take the name as an argument, with
`Mapflow.save_aoi_session` reading `session_mode`, prompting through the view, and passing it
in — justified as "a service cannot open a dialog".

That premise was wrong twice over:

* `AlertService` already exposes `alert_confirm(message) -> bool`, a blocking modal returning
  user input, callable from any service. There is no principled line between a modal that
  returns a bool and one that returns a string.
* `processing_service` — a service — already calls `QInputDialog.getText` twice, once in
  `rename_aoi`, forty lines from the code I contorted. Same domain, same dialog class, two
  architectures.

And the rule *as tested* would have allowed the inline prompt all along: `test_layering.py`
forbids importing `PyQt5.QtWidgets` and taking a `dlg` parameter, and says nothing about modal
interaction. My prose reading was stricter than my own check.

Fixed by adding `ask_text` to the message tier next to `alert_confirm`, so the service asks for
the name where it uses it. `Mapflow.save_aoi_session` is gone (`saveRequested` connects straight
to `save_session`), `session_mode` is gone with it, and "cancelling the prompt keeps the session
open" is tested against the thing that owns sessions again.

The general shape of the rule this settles: **a service may not read or write the plugin's own
dialog; it may cause a modal interaction through a named function of the message tier, which
owns the Qt types.** That also gives `processing_service` a route to drop its `QInputDialog`
import later, shrinking the layering allowlist rather than growing it.

## Result

`mapflow.py` 4521 → 4078 lines (-443 across the step). `AoiService` 552, `AoiView` 99,
`ProcessingController` 76.

Still in `mapflow.py`, deliberately: `sync_processing_area_to_selected_aois` (four lines of
trigger), `save_aoi_session` (the name prompt), `add_aoi_from_layer_dialog` (the picker), and the
`dlg.aoi_*_action` connects. All template-region wiring, all bound for `TemplateController`.
