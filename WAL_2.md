# Templates — Round 2 Testing Feedback: Fix Plan

## For a fresh agent picking up a task
- Work on branch `fix/templates-feedback-round2`. Follow `AGENTS.md` (+ `.github/instructions/*`).
- Pick ONE task (T#) below. Read `/spec` (via `/spec/index.md`) for anything touching templates/search/processing; if behavior isn't covered, flag a spec delta before coding (don't change specs unsilently).
- Order: write/adjust tests to the spec, then code. Run `agent-make test` (Docker) and `agent-make lint` (host: ruff+pyright) — both must pass; my changes added 0 lint errors, keep it that way. There are ~16 pre-existing baseline lint errors in untouched files — ignore those.
- One task = one commit (`git`-flow; never touch `master`). Message: what/why, not just what.
- Key domain facts already in the codebase: `processing_service.in_template_mode` / `active_template` distinguish the in-template view from the project list; `app_context.open_template_results_id` marks whose results are shown; `app_context.processing_aoi` is the cropped AOI actually sent; `_template_group_target(name, subgroup)` resolves the `Mapflow → <template> → [subgroup]` layer group; `templateAreaLimit`/`aoiAreaLimit` come from `/user/status` (`set_processing_limit`). Providers min-area lives in `app_context.provider_min_areas`.

**Branch:** `fix/templates-feedback-round2` (off `dev`).
**Base note:** `dev` already carries in-flight template-mode infra — `processing_service.in_template_mode`, `active_template`, and `config.TEMPLATE_TABLE_REFRESH_INTERVAL` (uncommitted in `config.py`, to be committed with T11). Fixes build on that.

Each task = one commit. `[ ]` todo · `[~]` in progress · `[x]` done · `[?]` needs a decision before coding.

---

## T1 — Investigate `add_aoi_to_preview` on preview display  (feedback 1)  · S · investigate  · [x] DONE (27bdefe)
Verdict: legacy simple-search behavior; gated OFF in template mode (`_add_aoi_to_preview_if_needed`), kept for regular search. Committed with T4/T5.

**Problem:** `add_aoi_to_preview` is called on preview display; AOIs are already shown with the template — seems redundant (legacy from simple search?).
**Where:** `mapflow.py:2603`, `mapflow.py:2653` (preview paths call `self.result_loader.add_aoi_to_preview()`).
**Approach:** trace what `add_aoi_to_preview` adds and whether it duplicates the template AOI layers. If it's legacy simple-search behavior, gate it off in template mode (`in_template_mode`) or remove; if it has value (e.g. regular search), keep for non-template only.
**Depends on:** overlaps T4/T5 (preview + groups) — do together or immediately after.

## T2 — Template opens with only first AOI's results when aoiIntersection > 0  (feedback 2)  · M · bug  · [x] DONE (9c90299)
ROOT CAUSE (not what the plan guessed): client already sends ALL aoiIds; the bug was client-side `filter_metadata` (wired to `metadataTableFilled`) re-filtering template results offline against a SINGLE AOI (`metadata_aoi`). minIntersection>0 dropped other AOIs' images; =0 → threshold 0 → nothing dropped. Fix: guard `filter_metadata` to skip offline filtering in template mode (server already filters per spec 002_F). Decoupled from T13.

**Problem:** opening a template with `aoiIntersection` filter > 0 shows only the first AOI's results (intersection computed per-first-aoi); with `aoiIntersection = 0` all results show.
**Where:** `_aoi_ids_from_template` (`mapflow.py:667`), `show_template_search_results` (`mapflow.py:851` → `get_template_images` with `aoiIds`), `processing_api.get_template_images` (`processing_api.py:164`, sends `aoiIds`/`minAoiIntersectionPercent`?).
**Approach:** determine whether the client sends only the first `aoiId`, or sends all but the server applies intersection to the first only. If client-side: send all AOI ids (or per-AOI requests merged). Tightly related to **T13** (multi-select AOI) — likely fixed together.

## T3 — Template searchParams not loaded into Imagery Search tab  (feedback 3)  · M · feature  · [x] DONE (9466bc3)
Editable (web parity). `apply_search_params_to_ui` maps searchParams→widgets in `on_template_opened`. Providers via `_apply_search_providers_to_combo`. 7 new tests in `test_template_search_params_ui.py`.

**Problem:** opening a template doesn't populate the search filters — no way to view them (web does populate).
**Where:** `_open_template` / `show_template_search_results`; UI fields: `metadataFrom/To`, `maxCloudCover`, `minIntersection`, `hideUnavailableResults`, `searchProvidersCombo`, product-type checkboxes; `dlg.setup_imagery_search`.
**Approach:** on template open, map `template.searchParams` → the search UI widgets (dates, cloud, intersection, hideUnavailable, dataProviders, productTypes). Read-only vs editable: match web (editable, but that changes the *search*, not the template). Add a helper `apply_search_params_to_ui(searchParams)`.

## T4 — Template layer group added to ROOT, not Mapflow group; preview re-adds a duplicate group  (feedback 4.1)  · M · bug  · [x] DONE (27bdefe)
Root cause: `_template_group_target` fell back to root when Mapflow group missing at open; later preview created a 2nd group under Mapflow. Fix: create the Mapflow group when missing (respect user-deleted via result_loader.add_layers_to_group).

**Problem:** on template open the `"<template name>"` group is added to the **root**, not the Mapflow group; calling preview then adds **another** `"<template name>"` group under the Mapflow group → two groups. Want: one group under the Mapflow group, created on open, reused by previews.
**Where:** `_template_group_target` (finds Mapflow group → template group), `_add_geojson_aoi_layer` / `_store_template_search_footprints` (AOI + footprint layer placement), and the preview add path (`add_aoi_to_preview` / preview layer group).
**Approach:** make BOTH the open-time layers and the preview layers resolve the same group via `_template_group_target` (Mapflow group → template group). Investigate why the open path lands in root (likely a different add path than `_template_group_target`). Edge: user deleted Mapflow group → falls back to root; acceptable once single-path.

## T5 — Preview column click adds duplicate / multiple layers (separate code path bypasses layer check)  (feedback 4.2)  · M · bug  · [x] DONE (27bdefe)
Root cause: `filter_metadata` reconnected cellClicked→preview without disconnecting → stacked connections. Fix: `_reconnect_cell_preview` disconnects first; both filter_metadata branches use it.

**Problem:** with the "Preview" column active, clicking it sometimes adds several layers at once / duplicates for one preview — a separate preview-add path bypasses the existing layer-exists check.
**Where:** `preview_search_from_cell` (`mapflow.py:2925`) via `cell_preview_connection` (`mapflow.py:1120`), plus `preview` (`mapflow.py:2767`) and the mosaic/png preview adders.
**Approach:** unify on one preview-add routine that checks for an existing layer before adding; remove the bypassing path. Pairs with T4 (same preview code).

## T6 — Template results pagination buttons don't appear  (feedback 5)  · M · bug  · [x] DONE (26d31a4)
Extracted `_update_search_pager` (shared); template callback calls it. next/prev template-aware via `_load_template_search_page` (preserves AOI filter). 8 tests. NOTE: SEARCH_RESULTS_PAGE_LIMIT left at 100 (the 5 was the user's manual paging test; reverted in this commit — code works for any limit).

**Problem:** page-nav buttons show for regular search but not for templates.
**Where:** regular search shows nav via search-page widgets (`searchPageLabel`, `show_search_next_page` `mapflow.py:3568`); template path (`show_template_search_results` → `get_template_images` with `limit`/`offset` = `SEARCH_RESULTS_PAGE_LIMIT=5`) fills the table but never toggles the nav UI / wires next-prev to the template fetch.
**Approach:** in `get_selected_template_callback`, read `total`/`limit`/`offset` from the response and show/wire the search pager to re-call `get_template_images` with the new offset (template-aware next/prev). Precondition for T7.

## T7 — Offline filters vs pagination: server-side filtering for template search  (feedback 6)  · L · feature · [x] DONE (db06086)
Backend confirmed (white-maps-backend ProcessingTemplateRequestJson): /images accepts date/resolution/cloud/off-nadir + aoiIds/paging, applies server-side, returns filtered total. NOT intersection%/hideUnavailable/providers/productTypes. Added a separate **Filter** button (template-only) that re-issues get_template_images with the current date+cloud filters (sticky across AOI + paging; read-only view, doesn't modify template). Also: legacy Maxar/Sentinel search removed entirely (separate refactor, merged); simple search now relies on server-side filtering (offline filter_metadata dropped → refresh_search_display). Spec 002_F/002_D updated. 6 tests.

**Problem:** offline filters (min intersection, dates, cloud cover) applied after paging shrink the page (e.g. 100 returned, 1 passes → user sees 1 row + nav). Want filters in the page request and drop offline filtering.
**Where:** `get_template_images` body (currently `limit`/`offset`/`aoiIds`); the offline filter step after fetch.
**Open decision (ask user):** trigger model — (a) re-request on every filter input (chatty), (b) a dedicated "Apply / Search" button, (c) re-request only on paging. **Recommend (b)**: an explicit Apply button that re-issues a server request with all filters, disabling offline filtering. Confirm the server endpoint accepts these filters.
**Depends on:** T6 (pagination), T3 (filters in UI).

## T8 — Prompt "Plan Search" when AOI area > searchAreaLimit  (feedback 7)  · L · feature  · [x] DONE (def136d)
Approved defaults. searchAreaLimit → app_context; `handle_metadata_button_click` gates regular search; `_prompt_plan_search` modal [Cancel]/[Plan Search]; Plan Search → `create_search_template(name_override="Searching <date time>")` (existing templateAreaLimit check covers step 3). Spec 002_F documents it. 10 tests.

**Problem/spec (web parity):**
1. If `aoi_area > searchAreaLimit` → modal: *"The search area is too large for immediate processing. The Planned Search will be created and run in the background. You will be notified when results are available."* — [Cancel] [Plan Search].
2. "Plan Search" → create a template in the selected project named `"Searching {date} {time}"`.
3. If also `aoi_area > templateAreaLimit` → show the existing template-area-limit message.
**Where:** `set_processing_limit` (add `searchAreaLimit` from `/user/status`, cf. existing `templateAreaLimit`), the search action (`get_metadata`/`handle_metadata_button_click`), `create_search_template` (auto-name path), existing `TEMPLATE_AREA_LIMIT_EXCEEDED` message.
**Approach:** store `searchAreaLimit` on app_context; gate the regular search; on "Plan Search" call the template-create flow with the generated name; reuse the templateAreaLimit block for step 3. New confirm dialog.

## T9 — Selecting a template AOI should auto-select it as the processing Area  (feedback 8.1)  · M · bug  · [x] DONE (1ba1930)
DECISION: union of selected AOIs (approved). Root cause: add_to_layers setLayer per display AOI → last stuck. Fix: display layers `set_current=False`; `sync_processing_area_to_selected_aois` unions selected AOIs into a dedicated 'Selected AOI' layer as the Area. Spec 002_F documents it. 7 tests.

**Problem:** the last AOI in `aoiDetails` is selected as Area and doesn't change when another is picked.
**Where:** `select_template_processings` / `_add_geojson_aoi_layer` (Planned AOI layers), `polygonCombo` (the AOI-for-processing selector), and the AOI-selection sync.
**Approach:** when a template AOI feature is selected, set it as `polygonCombo.currentLayer()` / the processing AOI, and keep it in sync on change. Related to T13 (multi-AOI). Note the recent cropped-AOI (`processing_aoi`) work.

## T10 — Newly created processing shows "No AOI" until re-entering the template  (feedback 8.2)  · S · bug  · [x] DONE (72d0d0e)
Root cause: AOI binding lives in aoiDetails (not in run response); flat optimistic add → unbound → "No AOI". Fix: `start_processing_callback` in template mode calls new `_refresh_active_template` (get_template re-hydrate + _fetch_template_processings) instead of flat add; also skips fragile ProcessingDTO parse. 3 new tests.

**Problem:** right after creating a processing from a template, it displays as "No AOI"; re-entering the template fixes it.
**Where:** `start_processing_callback` / `view.add_new_processing` (optimistic local add) vs the refetch; the new row's AOI area/geometry not populated in the optimistic DTO.
**Approach:** ensure the optimistic add carries the AOI (or trigger the refetch that populates it) so the row isn't "No AOI".

## T11 — Poll template statuses while in the project processings table  (feedback 9)  · M · feature  · [x] DONE (1042c26)
NOTE: TEMPLATE_TABLE_REFRESH_INTERVAL was already committed on HEAD; the WAL header was wrong. The uncommitted config.py change is SEARCH_RESULTS_PAGE_LIMIT 100→5, which belongs to T6 (still uncommitted). Fix: poll-stop decision moved to `_apply_poll_timer_state` (after templates fetched), keeps polling while any template `is_search_in_progress`; folds into existing poll. 6 tests.

**Problem:** a template created while the user waits in the projects/processings table stays "Searching" until re-entering the project. Need periodic refetch on `GET /processings/template/project/{id}` while any template is in a non-terminal status.
**Where:** `config.TEMPLATE_TABLE_REFRESH_INTERVAL=15` (already added), `get_templates_by_project`, the processings poll timer, `in_template_mode`.
**Approach:** add a timer (or fold into the existing poll) that refetches project templates on `TEMPLATE_TABLE_REFRESH_INTERVAL` when non-terminal templates exist; stop when all terminal. Commit the `config.py` change here.

## T12 — MultiPolygon AOI features rejected on template creation  (feedback 10)  · S · bug  · [x] DONE (4bf3fae)
Spec delta approved (line 190). `_polygon_aoi_features` splits via `asGeometryCollection` in both layer + fallback paths. 4 new tests; 3 existing tests switched from mocked asJson to real QgsGeometry.

**Problem:** backend ignores `MultiPolygon` features in `aoiDetails` → all-MultiPolygon upload creates an empty, Failed template. Web converts uploaded features to Polygon in the AOI table.
**Where:** `create_search_template` `SearchParams(aoi=...)` / the geometry serialized into the request; possibly `_aoi_features`.
**Approach:** convert MultiPolygon → Polygon(s) when building the template-create request (explode multipolygon parts into separate Polygon features).

## T13 — Multi-select AOI for template results  (feedback 11)  · M · feature  · [x] DONE (904eeb1)
Spec delta approved (single→multi AOI, line 257). processingsTable → ExtendedSelection; `filter_search_by_selected_aoi` collects all `selected_aois()` ids as a frozenset, sends all as aoiIds. Decoupled from T2. 5 new tests + 3 updated in test_template_aoi.py.

**Problem:** filtering template results by a selected template AOI should support multi-select (several AOIs at once).
**Where:** the AOI-selection → `get_template_images(aoi_ids=...)` path; `_aoi_ids_from_template`.
**Approach:** allow multiple AOI selection and pass all selected `aoiIds`. Fixes/overlaps **T2** (first-AOI-only). Do T2 + T13 together.

---

## Suggested commit order (dependencies)
1. **T3** (searchParams → UI) — standalone, enables T7 filters.
2. **T2 + T13** (multi-AOI + intersection) — one investigation, likely one commit.
3. **T4 + T5 + T1** (groups + preview de-dup + add_aoi_to_preview) — same preview/group code.
4. **T6** (pagination UI) → **T7** (server-side filters) — T7 depends on T6 + decision.
5. **T9**, **T10** (processing creation bugs) — independent.
6. **T11** (template status polling) — commit config.py here.
7. **T12** (MultiPolygon→Polygon) — standalone.
8. **T8** (searchAreaLimit → Plan Search modal) — larger feature, standalone.

## Decisions to confirm before coding
- **T7 trigger model:** re-request per input / **Apply button (recommended)** / re-request on paging only. Confirm server endpoint accepts cloud/date/intersection filters.
- **T8:** confirm auto-name format `"Searching {date} {time}"` and that the target is the currently selected project; confirm modal copy.
- **T3:** search filters editable (like web) vs read-only display when opened from a template.

## Subagent split (if spawning)
Group 3 (preview/groups) and Group 2 (multi-AOI) are self-contained investigations — good subagent candidates. T7 and T8 need a decision first, so hold. Each subagent: own the listed files, follow AGENTS.md (tests + `agent-make lint`), one commit.
