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

Landed. `mapflow.py` went from 2993 lines to 1183 across ~25 MRs, each moving one domain and
changing no behaviour: AOI layers, previews, imagery search, the local filter, templates (the
largest — ~50 methods and ~50 cross-service references to its navigation state), the processing
lifecycle, account status, the session, providers, result actions, and the working directory.
Service and controller boundaries are tabulated in `spec/007_architecture.md`; the WHY of each
step is in its commit message.

What `mapflow.py` still holds is composition-root work: `initGui`/`unload`, construction, signal
wiring, startup sequencing (`log_in_callback`, `on_account_status`, `main`, the provider setup),
and the cross-region forks that choose between two controllers — which is precisely what a
controller may not do (`spec/007_architecture.md` § Controllers). Its remaining `self.dlg`
references are construction and wiring, plus the startup block restoring saved filter values.

**The phase's second acceptance criterion is NOT met.** It read "the layering test's allowlist is
empty"; nothing in this phase touched it. Emptying it is a different body of work from moving code
out of `mapflow.py`, and folding it into a phase that already ran ~25 MRs would have hidden it —
so it is **Phase C2** below rather than a footnote here.

### Phase C2 — take the dialog out of the services

Landed. All five services and both api modules dropped the main dialog — 138 `self.dlg` accesses
gone. Writes left as signals a controller connects to a view; reads moved up to controllers, which
push plain values down. `test_layering.py`'s `ALLOWED` is now `set()`: Phase C's unmet acceptance
criterion is met, the last entries having been cleared by the error-reporting phase rather than by
C2 itself. The WHY of each step is in its commit message; the layer rules are in
`spec/007_architecture.md`.

### Phase C3 — fix what the refactoring found

Nine defects surfaced while moving code. Each was left alone at the time because a behaviour change
does not belong inside a move, and several are now **pinned as current behaviour by tests written
during Phase C** — so the suite currently protects them. Those tests change with the fix.

Re-verified against the code on 2026-09-09, after the error-reporting phase: every entry below is
still live except C3.4 (fixed, entry removed), with C3.5 and C3.7 weakened as annotated. Nothing
here was fixed incidentally, so the list is real work rather than inherited paperwork.

Grouped by whether the intended behaviour is obvious.

**C3.1 and C3.2 are one MR — they mask each other.** Fixing C3.1 alone stops the cost being quoted
for every model that has options; see the note under C3.2.

[ ] C3.1 `enable_model_options` discards the user's saved model options
    Two defects in one line pair (`main_dialog.py`):
    (a) `if not can_start_processing: can_start_processing = True` makes the role argument a no-op,
        so option checkboxes are never disabled for a role that may not start a processing.
        **Decided: enforce it** — starting is already forbidden for those roles, so leaving the
        options interactive offers a choice that cannot be acted on.
    (b) `widget.setChecked(can_start_processing)` **force-ticks every option on every model change**,
        overwriting the state `saved_model_options` just restored. Worse, `add_model_option`
        connects `toggled` *after* setting the initial state, so this forced tick emits
        `modelOptionsChanged` -> `on_options_change` -> `save_option_settings`, writing the
        clobbered all-enabled state back to settings. The `wd/{workflow_id}/{block_name}` key in
        `spec/003_local_storage.md` is therefore written but never effectively read back.
        User-visible: unticked options return ticked, and options feed `get_price(enable_blocks=…)`,
        so the user is quoted for blocks they turned off.
    Fix: drop the override, and drop `setChecked` entirely — enabling is not ticking.
    Migration is clean: settings currently hold all-enabled, so the first render is unchanged and
    behaviour only diverges once someone unticks something, which then sticks.

[ ] C3.2 A model whose blocks are all obligatory is never quoted
    `on_model_change` quotes immediately only when `len(wd.blocks) == 0` — *all* blocks, while the
    checkboxes come from `optional_blocks`. So: no blocks -> quoted; some optional -> quoted, but
    **only because C3.1(b)'s forced tick emits**; all obligatory -> no checkbox ever fires and the
    cost stays blank.
    Fix: test `not wd.optional_blocks` — quote now precisely when no checkbox will ever fire.
    Also correct the comment above that condition: it credits the emit to "adding its option
    checkboxes", but creation cannot emit (the `toggled` connect comes after the initial
    `setChecked`). The emit is C3.1(b)'s forced tick, which is why removing it breaks the quote.
    Pinned by `test_a_model_whose_blocks_are_all_obligatory_is_not_quoted_on_selection`, which
    changes with the fix.

**Unambiguous — the current behaviour is not intended by anyone:**

[ ] C3.3 `modelCombo.activated` is emitted but connected to nothing
    Emitted in `mapflow.py` and `project_view.py:195`; only `currentIndexChanged` is connected. The
    model refresh those emits intend happens by accident via `setCurrentText`. Either connect it or
    delete the emits — but decide, because the accident is load-bearing today.
[ ] C3.5a An account with no projects re-requests the list forever
    `ProjectService.get_projects_callback` treats "no projects and no filter" as a stale page and
    re-requests without parameters — which returns the same empty result, and asks again. It is
    guarded only by the assumption that every account has a `Default` project. Asynchronous, so it
    is an endless request loop rather than stack recursion, which makes it look like a hung plugin
    talking to the server rather than a crash. Pinned as current behaviour by
    `test_an_empty_unfiltered_result_asks_again_without_parameters`; that test changes with the fix.
[ ] C3.5 A template rename tells the user nothing when the response shape drifts
    (Re-checked 2026-09-09 — weaker than first written.) The broad `except Exception` around the
    parse now logs via `logger.exception`, forced by Phase A's rule, and `refreshRequested` re-syncs
    from the server afterwards, so the table ends up correct and the drift is recorded. What remains
    is that the *user* gets no signal: a rename the plugin failed to apply locally looks identical
    to one that worked. Decide whether that warrants a message tier alert or is fine as a log line.

**Test-surface gaps found in passing:**

[ ] C3.6 `test-ui` proves nothing
    The Makefile treats pytest's exit code 5 ("no tests collected") as a pass, so a green `test-ui`
    is green on an empty tier. Remove the guard with the first UI test. Note this edits a **watched
    file**, so plan it per the BRANCH MODEL.
[ ] C3.7 `show_template_details` has no direct test (pre-existing; unchanged by the move).
    Re-checked 2026-09-09: `test_processings_table_actions.py` now covers that the controller *calls*
    it, so the wiring is pinned — the method's own behaviour still is not.
[ ] C3.8 Nothing replaces pyright's `reportPossiblyUnbound`
    Use-before-assignment across branches is unchecked; flake8's `F821` covers undefined names only.
    Accepted deliberately for qgis.org parity — revisit once the refactor lands type annotations.
[ ] C3.9 `static/styles/aoi_templates_processing.qml` is referenced from nowhere
    Confirm whether it is dead or a rename that lost its caller. (Also noted under Phase D.)

### Phase D — move the packages

Mechanical, and cheaper here than earlier: the god object is gone, so fewer files churn.

**Runs after C2**, not before: C2 rewrites five of the service files this phase relocates, and
moving a file then rewriting it costs the review twice and makes each diff harder to read than
either change alone. C3 is independent of both and can be interleaved wherever it suits.

[ ] `functional/` dissolved: `api/`, `controller/`, `service/`, `view/` to the root; `app_context`
    → `context.py`; `geometry`, `helpers`, `styles` to the root; `auth` → `SessionService`;
    `layer_utils` → `ResultService` plus the layer-tree helpers in `view/`
    Note: `ResultService` here means **`ResultsLoader`** — the requests, the layer building and the
    styles. The user-facing result *actions* (`load_results`, `download_results_file`,
    `download_aoi_file`) are not part of it: they read the table selection, read the tiles/local
    radio and prompt for a working directory, which is controller work, and they now live in
    `ProjectProcessingController` beside the other processings-table actions.
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

**Delivered.** Both tiers live in `infra/` and are throttled from one set of `config.py`
parameters; the report tier is reserved for unexpected failures while connectivity and server
errors use the message tier; every silent request path but the `/version` probe was restored; and
every Qt entry point reaches plugin code through `guarded_connect`, leaving `ALLOWED_UNGUARDED`
with only the `response_dispatcher` row, which IS the guard. The WHY of each step is in its commit
message; the durable rules are in `spec/006` and `spec/007`.

Two follow-ups it left behind:

[ ] Close the entry-point enforcement gap the rollout exposed
    `test_entry_points_guarded` classifies a connection by the attribute the `.connect` hangs off,
    so `for signal in (...): signal.connect(...)` is invisible to it — the receiver is a bare name.
    `mapflow.py`'s local-filter block was exactly that shape (nine Qt widget signals) and was
    guarded only because the rollout read the code. Either resolve simple loop variables in the
    visitor, or fail on a `.connect` whose receiver cannot be classified.
[ ] Give dialog-originated reports a plugin version
    `guarded_connect`'s `version_source` resolves `plugin_version` off the passed object; dialogs and
    views carry neither it nor `app_context`, so a report raised from one says "unknown". The version
    is parsed once in `Mapflow.__init__` from metadata.txt — a one-time module-level fallback in
    `error_guard` would fix every such site at once.

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
`unload()` closes the dialogs but never disconnects the `QgsProject` subscriptions
(`layersAdded` ×2, `readProject`). After a QGIS plugin reload the previous instance is still
subscribed, so adding a layer runs its handlers against a closed dialog — and against whatever
state that instance was left in, which can take a branch the live instance never would.
The entry-point rollout makes this **more certain, not less**: `guarded_connect` connects a
closure rather than a bound method, so PyQt's auto-disconnect-when-the-receiver-dies no longer
applies. `QgsProject` outlives the plugin, so these subscriptions now survive until something
disconnects them explicitly — which is exactly what this step must add.
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

