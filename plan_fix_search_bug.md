# Plan: Fix multi-image bug for Imagery Search (orbview & sibling providers)

## Scope

Three related defects, all on the path
`ImagerySearchProvider` → `/processings/cost` and `POST /projects/{id}/processings`,
plus the "See details" → duplicate flow.

The narrow-scoped fix lives entirely in `mapflow-qgis`. No backend changes.

## Bug summary

### Bug 1 — Only the first selected image ID is sent

`get_provider_params` already passes a list of selected rows
(`get_local_image_indices`, `get_search_providers`), but
`get_search_images_ids` then collapses to row 0:

```python
# mapflow/functional/service/provider_service.py:225-230
selected_cells = self.dlg.metadataTable.selectedItems()
if not selected_cells:
    image_id = None
else:
    id_column_index = self.config.MAXAR_ID_COLUMN_INDEX
    image_id = [self.dlg.metadataTable.item(selected_cells[0].row(), id_column_index).text()]
```

Result: with N rows selected from the same `orbview_*` provider,
`ImagerySearchSchema.imageIds` ends up length-1 instead of length-N for both the
cost call and the create-processing call.

### Bug 2 — Different `orbview_*` providers cannot be combined

`get_search_images_ids` rejects multi-selection whenever provider names differ
(except all-Mosaic), via:

```python
# mapflow/functional/service/provider_service.py:233-236
if len(set(provider_names)) > 1:
    if set(product_types) != set(["Mosaic"]):
        selection_error = self.tr("You can launch multiple image processing only if it has the same provider of mosaic type")
```

On the backend, all `orbview_*` providers are dispatched through a single
`OrbviewService` and are detected by
`repl.toLowerCase.startsWith("orbview")`
(`white-maps-backend/.../service/OrbviewService.scala:42-44`, `OrbviewService.scala:119`).
So selecting `orbview_msi` + `orbview_pan` in the search tab is a legitimate request,
but the plugin blocks it client-side. The validator
`provider_service.validate_provider_params` repeats the same `len(set(product_types)) > 1`
check (line 196) and must learn the same exception.

### Bug 3 — Duplicate ("See details") only shows the first image

`duplicate_imagery_search` hard-codes a single row in both the metadata table
and the pseudo metadata layer:

```python
# mapflow/functional/service/provider_service.py:340-352
self.dlg.metadataTable.setRowCount(1)
columns = {self.config.NAME_COLUMN_INDEX: provider.imagerySearch.dataProvider,
           self.config.MAXAR_ID_COLUMN_INDEX: provider.imagerySearch.imageIds[0],
           ...
           self.config.LOCAL_INDEX_COLUMN: 0}
```

For an N-image processing, the user sees only one ID, and the
selection-driven validation/cost calls reproduce the wrong (single-image)
state when they hit "Duplicate".

## Spec references

- `spec/002_B_processing_api.md` — `POST /projects/{project_id}/processings`
  body's `imagerySearch.imageIds` is already `List[str]` per
  `mapflow/schema/processing.py:87-90`. No schema change.
- `spec/002_D_search_api.md` — no explicit rule about multi-provider selection.
  The backend semantics that any `orbview_*` is handled by a single dispatcher
  is currently undocumented on the plugin side. **Proposed spec delta** (needs
  user approval before merging): add a short note to `002_D_search_api.md`
  stating "Selections whose `providerName` all match `orbview*` (case-insensitive)
  may be combined into a single processing request, even when their full names
  differ." Reference `OrbviewService.isValidRequest` from white-maps-backend.

## Assumptions

1. `ImagerySearchSchema.dataProvider` is a single string and stays that way.
   When combining multiple `orbview_*` rows we MUST pick one canonical
   `dataProvider` to send. Plan: send the first selected row's `providerName`
   verbatim — backend `isOrbView` / `startsWith("orbview")` accepts it
   (`OrbviewService.scala:119`). No new wire-format value is introduced.
2. All other "same provider" semantics stay intact: non-orbview mixes still
   require either identical names or the existing all-Mosaic loophole.
3. Zoom rule (Mosaic-only zoom uniqueness check at `provider_service.py:198`)
   is unrelated and stays.
4. For the duplicate flow, individual image footprints are not available
   (only the AOI is downloaded). The pseudo metadata layer will reuse the AOI
   geometry for each row, mirroring today's single-row behaviour. This is a
   display-only compromise and is acceptable — the row's `id` field still
   matches the real image, so re-running cost/create with the duplicated
   processing keeps the correct multi-image request body.

## Implementation steps

All edits in `mapflow/functional/service/provider_service.py` unless noted.

### Step A — Helper: orbview-family detection

Add a small private helper inside `ProviderService`:

```python
@staticmethod
def _is_orbview_family(provider_names):
    return bool(provider_names) and all(
        isinstance(n, str) and n.lower().startswith("orbview")
        for n in provider_names
    )
```

Used by both `get_search_images_ids` and `validate_provider_params`. Keep it
private to the service; no public API change.

### Step B — `get_search_images_ids` (lines 224-245): collect ALL image IDs

Replace the `selected_cells[0].row()` block with iteration over the unique
rows the caller already computed. Simplest path: pass `local_image_indices`
in (already known by caller), and resolve each row's `id` cell.

Concretely (pseudocode of the new method, exact diff to be produced by the
delivery agent):

1. Walk each unique row in selection. Read `MAXAR_ID_COLUMN_INDEX` cell text.
   Skip blanks defensively.
2. Build `image_ids: List[str]`.
3. Build `selection_error`:
   - same as today when `provider_names` is uniform OR all `product_types`
     are `"Mosaic"`.
   - **new**: also OK when `_is_orbview_family(provider_names)` is true and
     `product_types` are all `"Image"`. (Mosaic + Image mix is still
     rejected — that matches the backend, which routes orbview as "Image"
     product type per `OrbviewService.scala:41`.)
4. Set `self.imagery_search_provider_instance.requires_id` and
   `.image_ids` from the list. `requires_id` should stay `True` when any IDs
   are present, `False` only when truly empty.

### Step C — `get_provider_params` (line 138): canonical provider name for orbview

When `_is_orbview_family(provider_names)` is true, keep the existing
`provider_name = provider_names[0]` behaviour — backend
`startsWith("orbview")` accepts it. No code change needed beyond Step B,
but add a one-line comment near line 138 explaining the why for future
readers (only because it's non-obvious from the call site).

### Step D — `validate_provider_params` (lines 181-200): mirror the rule

The validator re-checks `len(set(product_types)) > 1` and same-provider rules
through indirection. Update so the same orbview-family exception applies:
when `_is_orbview_family(provider_names)` is true and all `product_types` are
`"Image"`, do not emit "Selected search results must be of the same product
type". Other branches (mixed product type that is not orbview-family,
mosaic+image mix, mosaic+different-zoom) stay as-is.

### Step E — `duplicate_imagery_search` (lines 340-382): render all rows

Rewrite to expand to N rows where N = `len(provider.imagerySearch.imageIds)`:

1. `self.dlg.metadataTable.setRowCount(N)`.
2. For each `i, image_id` in `enumerate(provider.imagerySearch.imageIds)`:
   - Set the same `providerName`, `zoom` fields, but
     `MAXAR_ID_COLUMN_INDEX = image_id`, `LOCAL_INDEX_COLUMN = i`.
   - Append a feature to the pseudo metadata layer with the AOI geometry and
     the row's attributes (so `search_footprints[i]` resolves correctly).
3. Rebuild `self.app_context.search_footprints` as
   `{i: feature for i, feature in enumerate(layer.getFeatures())}`.
4. Keep `self.dlg.metadataTable.selectRow(0)`'s spirit: instead, select
   every row so cost recalculation runs with the full N-image payload.
   `for row in range(N): self.dlg.metadataTable.selectRow(row)` (the table is
   in `ExtendedSelection` mode after `sync_layer_selection_with_table`
   finishes; verify it is also in `ExtendedSelection` here before selecting).

### Step F — Unused/legacy bits to leave alone

- `setup_provider_info` at line 160 still uses `selected_cells[0].row()` to
  build the human-readable header. That is purely cosmetic; leave it for now
  but add a `# WARNING` comment per `AGENTS.md` spec guideline noting it
  should show "(N images)" or list IDs for multi-selection. Out of scope for
  this fix.

## Tests (per `AGENTS.md`: tests must follow spec)

Add a new file `tests/test_imagery_search_multi.py` covering:

1. `get_search_images_ids` with N rows of the SAME provider returns N IDs and
   no selection error (Bug 1 regression).
2. With N rows of mixed `orbview_msi` / `orbview_pan` (product type `Image`),
   no selection error AND all IDs are returned (Bug 2).
3. With N rows mixing `orbview_msi` and `maxar` (or any non-orbview), the
   existing selection error is emitted (negative case — make sure we don't
   regress the guard).
4. `validate_provider_params` for the orbview-family Image mix returns
   `None` (no error). For non-orbview mix it still returns the original error.
5. `duplicate_imagery_search` with a fake `ImagerySearchParams` carrying
   3 image IDs:
   - `metadataTable.rowCount() == 3`.
   - Column `MAXAR_ID_COLUMN_INDEX` for each row matches the corresponding
     `imageIds[i]`.
   - `app_context.search_footprints` has 3 entries keyed 0..2.
   - All rows are selected after duplicate (or, at minimum,
     `get_search_images_ids` invoked on the duplicated state returns the
     full list).

All five tests should be pure-logic where possible (mock `dlg`,
`metadataTable`, `app_context.search_footprints`) following the pattern in
`tests/test_data_catalog.py`. The `metadataTable` mock needs `item(row, col)`
and `selectedItems()` to behave consistently.

## Out of scope

- Backend changes (already supports the multi-image request).
- Generalising the "family" concept beyond orbview. If we later need other
  vendor families (Maxar variants, Planet, etc.), refactor `_is_orbview_family`
  into a configurable mapping. For now, leave orbview-specific.
- UI labelling improvements in `setup_provider_info` (see Step F).

## Risk / blast radius

- Code is confined to one file (`provider_service.py`) plus one new test
  module. No schema, no API, no settings.
- Behaviour for single-row selection is unchanged (loop length 1 = today's
  behaviour). Behaviour for non-orbview multi-row selections is unchanged.
- Duplicate flow now creates N rows; the rest of the pipeline already loops
  on `selectedItems()` correctly, so the cost call and the "Start processing"
  call will pick up all N IDs without further wiring.

## Definition of done

- All five tests pass under `pytest tests/`.
- Manual smoke (not required to land, but recommended): on dev backend,
  select 3 `orbview_msi` rows, observe cost call body and create-processing
  call body contain all 3 IDs. Repeat mixing `orbview_msi` + `orbview_pan`.
  Open "See details" on the resulting processing and confirm all 3 IDs are
  in the search table.
- WAL entry added per `AGENTS.md` workflow.
