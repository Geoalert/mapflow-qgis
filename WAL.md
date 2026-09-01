# Planned and in-flight work

Forward-facing only: `[ ]` planned, `[ready-for-review]` in flight. Entries are removed when they
merge — the WHY lives in the commit message and, for durable decisions, in `spec/`.
See AGENTS.md § WHERE THE WHY GOES.

# V 3.7.0 LTR

We are planning a long-term release, effectively the LAST, stable release for QGIS3, the next version will be for QGIS4,
and this version will get only API compatibility changes and bug fixes.

So, the main idea behind the release is HARDENINIG so that this support will be easier, AND transfer to QGIS4 will go smoother.
current plugin code needs a major refactoring.

However, as we don't want to release an "empty" version (without any user-facing features), we will add some improvements.

## 1. Refactoring

Target structure, layer rules and invariants: **`spec/007_architecture.md`**. The steps below
are the route there. Phases run in order; each step is one MR.

### Phase A — clear the ground

Landed: the layering test, `constants.py` merged into `config.py`, and the rule that a broad
exception handler must surface what it caught (`tests/functional/test_exception_reporting.py`).
Both allowlists only shrink from here.

### Phase B — a test surface that survives the move

Landed: `tests/qgis/behavioral/` (twelve journeys) and `tests/qgis/test_result_styles.py`. The
existing `Class.__new__(Class)` tests stay until the code they pin moves; no extraction may
leave a behaviour covered by neither.

### Phase C — dissolve the god object

One domain per MR, each ending with `mapflow.py` smaller and no behaviour changed. Ordered
leaf-first so each extraction depends only on what already moved.

Service and controller boundaries are tabulated in `spec/007_architecture.md`.

**The templates domain is extracted.** It was the phase's largest — ~50 methods in `mapflow.py`
plus the template half of `processing_service.py`, with ~50 cross-service references to its
navigation state — and it took several MRs: create/update-search-params/exclude and plan-search
gating; the seen-markers cluster; the map layers and their navigation slots; the search request,
results, footprints and AOI scoping; the run-state actions; one owner for the processings table's
refresh; and finally the in-template view with its navigation state.
**`ProcessingService` now references nothing on `TemplateService`** apart from the seam below.

[ ] Finish the split: the `templates`-keyed queries, the context menu, and the seam
The templates extraction stopped here on purpose, not by omission. `selected_template(s)`,
`is_only_templates_selected`, `all_selected_templates_editable` and `template_to_run` read
`ProcessingService.templates` — the project's template dict, which its own project fetch fills —
and `template_to_run` is what `handle_processing_submission` forks the start path on. Moving them
means moving that fork, so they belong with **"Extract processing lifecycle: options, start, review,
rating"** below rather than with templates.

What that leaves in `mapflow.py`, all of it reading those queries:
* the processings-table **context menu** (`update_processing_options_menu`, ~`mapflow.py:588-660`) —
  its template branch reads `selected_template` and the run-state gating;
* `show_selected_details`, `update_delete_button_state`, `load_results`/`_open_template`, and the
  plan-mode branch of the Search button.
The in-template forks in `apply_local_filter`, the header sort and the pager now read
`template_service` directly and are fine where they are.

Until that step, `ProcessingService.template_state` is a documented read-only seam (a null object by
default, `TemplateService` at wiring time) covering the three places the start path asks whether a
template is open — `template_to_run`, the start callback, and resolving the table selection to
objects. It is duck-typed and never imported, so no cycle is possible; delete it when that step
lands.
[ready-for-review] Give template-group layer placement one owner
The two footprint-layer builders become one: `SearchService.build_metadata_layer` builds and
registers the layer for both searches, and *where it goes* arrives as a `place` callable — beside
the AOI layer for a regular search, inside the template group for a template's. `PreviewService`
hands its preview layer to `TemplateService.place_preview_layer` instead of doing the tree surgery
itself, so nothing but `TemplateService` reaches for a template group now.

[ ] Extract processing lifecycle: options, start, review, rating → existing processing service/controller
[ ] Split auth from account status → `SessionService` + `AccountService`
[ ] Reduce what remains of `mapflow.py` to initGui/unload, wiring and construction
Acceptance for the phase: no `self.dlg.<widget>` access in `mapflow.py`, and the layering test's
allowlist is empty (`spec/007_architecture.md` invariants 1 and 5).

### Phase D — move the packages

Mechanical, and cheaper here than earlier: the god object is gone, so fewer files churn.

[ ] `functional/` dissolved: `api/`, `controller/`, `service/`, `view/` to the root; `app_context`
    → `context.py`; `geometry`, `helpers`, `styles` to the root; `auth` → `SessionService`;
    `layer_utils` → `ResultService` plus the layer-tree helpers in `view/`
[ ] `http`, `error_guard`, `report_throttle`, `log_config` → `infra/`
Note: the `schema/` ⇄ `model/` split already happened in Phase A, so this phase is package
moves only — no type is reclassified here.

[ ] Separate the technical layer styles from the result styles
`static/styles/` currently mixes two unrelated things at one level. `file/` and `tiles/` hold
**result** styles, chosen per model by `get_style_name`. Loose alongside them sit the
**technical** styles for the plugin's own layers — `aoi.qml`, `metadata.qml`,
`metadata_footprint.qml`, `aoi_template_blue.qml`, `aoi_template_processing_green.qml` — which
are loaded by literal filename from nine call sites and can never be tile styles, because the
layers they dress are always vector layers the plugin builds itself.
Nothing in the layout says which is which, so the natural reading is that the loose files are
just result styles that have not been sorted yet. Give them their own directory and the
distinction becomes structural instead of tribal knowledge.
While there: `static/styles/aoi_templates_processing.qml` is referenced from nowhere. Confirm
whether it is dead or a rename that lost its caller.
`tests/qgis/test_result_styles.py` guards both groups today and will need its paths updated.

[ ] Decide whether result styles should share one name set across `file/` and `tiles/`
**A call for the user, and not before the structural refactoring has landed** — it changes
what the tile path is allowed to inspect, which is easier to judge once the services own
their own code.
The two directories diverge: `tiles/` has six styles, `file/` thirteen. The seven extra —
`buildings_noclass`, `building_heights_class`, `forest_crowns_points`, `forest_with_heights`,
`landuse`, `open_data_polygon`, `open_data_line` — are variants chosen from the layer's
**fields and geometry**, which only the local path inspects; the tile path keys off the model
name alone. So this is not a naming slip to tidy up, and matching the sets means choosing one:
- teach the tile path to inspect vector-tile fields, and add the missing seven to `tiles/`; or
- accept that tiled results are coarser, and say so where the split is defined.
Worth settling because there are two independent name-derivation functions today
(`get_tile_style_name_from_wd_name`, `get_local_style_name_from_wd_name`) that can drift apart
silently — a model added to one and not the other renders as `default` in the other view, and
no test can catch that while the two sets are legitimately different.

### Phase E — UI consistency

[ ] Move static widgets out of Python and into the `.ui` files
The loading pattern is already right — every dialog uses `uic.loadUiType` and no `pyuic5`
output is committed. What breaks Designer is the Python layered on top, chiefly in
`main_dialog.py` (803 lines), which builds statically-placed widgets in code where Designer
cannot see them. Rules and the acceptance test in `spec/007_architecture.md` § Dialogs and
.ui files.

[ ] Review what the plugin stores in settings
Against `spec/003_local_storage.md`; drop what is no longer read.

### Phase F — after the structure is settled

### Error reporting — one suppression policy for every dialog

Planned in full and approved; **sequenced after Phase C by decision, and not to be re-raised
unless a discovery changes that order.** Steps 1–3 are independent of the extractions and fix a
live violation of `spec/006_error_reporting.md`; step 4 genuinely needs Phase C finished.

The state that motivates it, as measured on `dev`:

* two report paths do the same job with different plumbing — `report_unexpected_error`
  (exception → `get_exception_report_body`) and `report_http_error` (response →
  `get_error_report_body`) — and both build `ErrorMessageWidget` themselves, with different
  wording conventions;
* **only the exception path is throttled.** The response path can stack dialogs without bound,
  which is exactly what the volume-limit contract forbids and why the opt-outs below exist;
* **six request sites opt out of error handling and supply no handler**, so their server errors
  reach nobody: `mapflow.py:475,2617,3732`, `functional/api/processing_api.py:86`,
  `functional/api/data_catalog_api.py:97,257`. (A previous version of this entry said three; it
  missed both data_catalog ones. A further 26 sites opt out but pass their own handler, which is
  correct and out of scope.)

[ ] 1. Signature and throttle for the HTTP path
`response_signature(response)` = Qt error code + endpoint path; `http._request_path` already
computes that path, query-free, because it lands in a mail body. Carry `suppressed_count` into
the dialog text and report body the way the exception path does.

[ ] 2. One reporter, in `infra/`
Both entry points behind one module owning the throttle, the dialog and the suppressed-count
wording. This **moves `report_http_error` out of `AlertService`**, where the preview step put it:
a service may import `infra/`, so it never needed to be in the message tier. `AlertService` keeps
the message tier, which is what `spec/007_architecture.md` assigns it.

[ ] 3. Restore the six silent request paths
With the throttle covering them, opting out has no remaining justification — `spec/006` already
says so. Each site takes the default handler back, or states in a comment why not.

[ ] 4. Apply `guard_entry_point` at the entry points
`guard_entry_point` is written and tested but applied nowhere; only `Http.response_dispatcher` is
guarded. Everything entering plugin code from Qt without passing through `Http` still escapes to
QGIS's raw unhandled-exception dialog: button clicks, selection changes, timer ticks,
drag-and-drop, dialog accept/reject. 203 `.connect()` sites today, 109 still in `mapflow.py` —
which is why this waits for Phase C, where a controller slot becomes the definition of an entry
point (`spec/007_architecture.md` § Entry points).
The decorator is the cheap half. The expensive half is `spec/006` § "A guarded callback is
interrupted, not completed": every slot needs checking for cleanup placed after code that can
raise. That is the bug that polled `/user/status` twice a second for a whole session.

[ ] 5. Throttle the message tier too
Decided with the above: the contract says *no failure* may produce unbounded dialogs, and
`alert()` is `exec()`-modal like the report dialog. It is reachable from polled paths (the
template callbacks hang off the 6 s processing poll), so the same storm is possible there.
Throttle parameters move into `config.py` so they can be tuned during live UX testing without a
code change — the current values (60 s window, ×2 backoff, 30 min cap, 10 s global floor) were
reasoned from poll intervals, not measured against users.

[ ] A refused price is undone by the next UI refresh
When `/processing/cost/v2` refuses, `ProcessingService.disable_processing_start` correctly
disables Start and formats the server's reason — and then both effects are thrown away.
`update_start_processing_button_state` (`mapflow.py:700`) re-enables the button whenever there
is no *planned-processing* gate error; it knows nothing about pricing. The label goes the same
way: the user ends up reading "Set AOI to start processing" with the AOI plainly set and the
area showing a real figure (3.12 sq.km in the behavioral run).
Two consequences, the second serious:
- the actual cause is invisible — in the captured case a workflow-def the backend does not
  recognise;
- **Start becomes clickable again for a processing the backend refused to price**, so the user
  can submit it.
Reproduced behaviourally: price one AOI successfully (Start enabled), then switch to an AOI
whose pricing is refused — Start stays enabled.
The fix is for the enable/disable decision to have one owner rather than several writers, which
is what the Phase C extraction is for. `tests/qgis/behavioral/test_cost_estimate.py` asserts
only that changing the AOI re-prices, and says why it stops there.

[ ] Check whether the behavioral tier reaches the real backend
The fake network replaces `QgsNetworkAccessManager` for everything the plugin requests through
`Http`, but a raster or vector-tile layer handed to QGIS is fetched by the provider, which the
fake never sees. Fixture tile URLs point at the real staging host.
Symptom that raised it: a mutation pointing a *raster* layer at an unroutable host stalled the
run inside QGIS rather than failing a test, which means layer construction does something
network-shaped rather than nothing.
So it is worth confirming whether B10 touches the network on every run. If it does, the tier is
quietly dependent on staging being up, and the fixture URLs should be rewritten to a host that
resolves but serves nothing.
No evidence of a plugin defect here — the vector-tile assertions (source and extent) pass, and
the only stall came from a deliberately unroutable host.

[ ] Detach the plugin from QgsProject on unload
`unload()` closes the dialogs but never disconnects the `QgsProject` subscriptions made in
`mapflow.py:349-350` and `:4028` (`layersAdded` ×2, `readProject`). After a QGIS plugin reload
the previous instance is still subscribed, so adding a layer runs its handlers against a
closed dialog — and against whatever state that instance was left in, which can take a branch
the live instance never would.
Found because the behavioral suite builds a plugin per test: opening a mosaic in one journey
made a *later, unrelated* journey fail, with the traceback running through the previous
plugin's dialog. `tests/qgis/behavioral/conftest.py` disconnects those signals at teardown to
compensate; that should go when unload() does it properly.
Same family as the singleton entry below — state that outlives the object that owns it.

[ ] Close the settings group the plugin opens
`Mapflow.__init__` calls `self.app_context.settings.beginGroup(plugin_name.lower())` and
nothing ever calls `endGroup` — it is the only occurrence of either in the codebase. Worse,
`AppContext.settings` is a plain class attribute, so one `QgsSettings` object is shared by
every instance in the process.
So a second construction in one QGIS session nests: keys move to `mapflow/mapflow/…`, a third
to `mapflow/mapflow/mapflow/…`. After a plugin reload the user's token, providers, working
directory and last project are written where nothing will read them on the next start, and
appear lost.
Not the cause of the test contamination above (that was the QgsProject subscriptions), but
found alongside it and fixed the same way in the harness.

[ ] Stop the services being process-global singletons
`ProviderService` and `AlertService` cache their instance on the class (`_instance`,
`_initialized`), so `get_instance` returns the first one ever built and ignores the arguments
of every later call. The instance keeps `self.dlg` pointing at the dialog it was born with.
Consequence beyond tests: after QGIS reloads the plugin — Plugin Reloader, or an in-place
upgrade without restarting QGIS — the surviving `ProviderService` writes the imagery-source
list into the destroyed dialog, and the new one comes up with an empty provider combo. The
user sees a plugin that cannot start a processing until QGIS is restarted.
Found because the behavioral suite builds a plugin per test and every journey after the first
saw an empty combo; `tests/qgis/behavioral/conftest.py` resets both classes to compensate, and
that fixture should be deleted as part of this step.
Belongs to Phase C: the fix is for the plugin to construct and own its services, which is what
the extraction does anyway.

[ ] Check the startup ordering between the project fetch and the account poll
`setup_providers` filters the imagery sources by `modelCombo.currentText()`, and the model
list arrives with a *project's* `workflowDefs` — not with the account response. So when the
500 ms startup poll wins the race against `projects/{id}`, the provider combo is built from
an empty model name.
Found while writing the behavioral startup journey, where it surfaced as a hard failure:
`providerIndex()` returned -1, `ProvidersList.__getitem__` handed back the `NoneProvider`
null object, and `requires_image_id` raised `NotImplementedError` — aborting the rest of
startup configuration, silently, because the error guard absorbed it. The null object is
fixed; the ordering is not.
Open question rather than a confirmed defect: on a fresh profile the user sees the projects
table and picks a project, which populates both combos, so this may be the intended flow. What
needs checking is the slow-network case on an account that *does* have a saved project —
whether the provider list is left empty until something re-triggers it.
Sequenced here because `SessionService` will own this poll after Phase C.

[ ] Gate the features whose prerequisites never arrived
Startup stops retrying `/user/status` and `/rasters/memory` instead of polling forever, which is
right for the traffic and wrong for the UI: the prerequisites those responses carry are simply
missing, and the affected actions currently fail late or behave as if the limits were zero.
- no `/user/status` → no billing type, no remaining limit/credits, no area caps. Processings and
  templates must not be launchable. Viewing them stays available.
- no `/rasters/memory` → no storage quota. My Imagery uploads must not be startable.
Blocked controls should not be silently disabled: show why, plus a **Retry** button that re-runs
the request and unblocks on success.
Needs one owner for "is this prerequisite satisfied"; today the answer is scattered across
`app_context` fields written from inside `set_processing_limit`.

[ ] Normalise the residual whitespace findings
Clears most of the `.flake8` ledger (~450: W291/W292/W293/W391, E501, E1xx/E2xx/E3xx).
Last on purpose: the refactoring rewrites most of the offending lines anyway, and a whole-tree
whitespace diff would collide with every in-flight branch, including
`feature/track-uploaded-image-status` (§3).
Until then the ledger only shrinks — new and moved code adds nothing to it.

[ ] Take `F401` out of the ledger — after the Phase C/D moves have landed
Not part of the whitespace bulk: **16 unused imports tree-wide**, not ~450, and unlike
whitespace it is the one suppressed rule the extraction actively *creates* work for. Moving a
method strands the imports it needed, and with `F401` suppressed nothing says so — the AOI
extraction left nine (four in `mapflow.py`, five in `test_template_updates.py`), all found by
hand.
Scheduled after the moves rather than before (user's call): a whole-tree import cleanup while
extraction MRs are in flight collides with all of them, and every extraction rewrites the import
blocks it touches anyway, so doing it first would largely be redone.
The cost of that ordering, stated so it is not a surprise: **until this lands, every extraction
must grep the names it moved.** Lint cannot tell you. That is how the nine above were found, and
it is the check to run before calling an extraction finished.

## 2. Add new zoom-selector feature
[ ]
- Use 002_E_zoom_selector_api.md
- Add a small button near zoom selector comboBox to call zoom-selector API, active when selected source is a Mapflow data provider.
- On button press, call API and select zoom automatically depending on response.
- On error, show a reasonable user-facing message.

## 3. Add myImagery upload status tracking
[ ] 
Mainly already implemented at branch `feature/track-uploaded-image-status`
Need to rebase on current state, or directly move the code if it's too complicated. 
The most important part is described in the `spec` change on the branch.

## 4. Update styles for both loaded geojson/gpkg layers and vector tile layers
[ ] 
The styles will be provided by the designer team, we need only to put it into the code

## 5. Add "Search by image ID" functionality
[ ] 
See API in `../whitemaps-backend`
```
- GET /meta/{image_id} request
- GET /meta/{image_id}?provider_name={}
```

## 6. Add "move image to other mosaic" functionality
[ ]
See API in `../data-catalog/spec/002_api.md`
```
POST /rest/rasters/image/{image_id}/move/precheck
POST /rest/rasters/image/{image_id}/move
```

