# Planned and in-flight work

Forward-facing only: `[ ]` planned, `[ready-for-review]` in flight. Entries are removed when they
merge — the WHY lives in the commit message and, for durable decisions, in `spec/`.
See AGENTS.md § WHERE THE WHY GOES.

# V 4.0.0 — Mapflow Next

Base branch: `feature/mapflow-next`. The steps below are one chain: one branch, one commit per step, in
this order — infrastructure and architecture first, then defects, then features. `spec/` already
describes the state after the chain; each step makes the code match it, and updates its own line in
`README.md` and `CHANGELOG.md`.

## 1. Infrastructure and architecture

[ready-for-review] `on_status` must not raise when the imagery is empty after Run again (`controller.py`, the `elif` after `_imagery_to_choose`). Goes first: the next step makes the end-to-end flow fail on it
[ready-for-review] The end-to-end flow fails on a Critical message it did not ask for; a missing `qgis.core` fails in the test images; CI runs `test-qt6`; every Qt 5/6 rule of the README has a check — `spec/004` § Test runtime, `spec/006` § The tests must see what the guard hides
[ready-for-review] One guard for every Qt entry point and for the callbacks `Http` runs; a callback's exception is never "Unexpected response from Mapflow", and a result whose bounds can't be transformed leaves no "loading" flag set — `spec/006` § The guard
[ready-for-review] Failed requests: lists and polls no longer fail silently, nothing stays pending, the poll stops on 403/404 and the default project opens — `spec/005` § Failed requests
[ready-for-review] Credentials only for the API's own scheme, host and port — `spec/002_api.md` § Authentication
[ready-for-review] Preview files in a per-session temporary folder, with safe file names — `spec/003` § Temporary Files
[ready-for-review] Uploads have a 1 h timeout; every request has one — `spec/005`, `spec/002_C`
[ready-for-review] A result is converted to GeoPackage in a `QgsTask`, off the GUI thread — `spec/005` § QGIS Application
[ready-for-review] `ui/` imports no service, and the controller does not talk to `Http` directly — `spec/007` § Layer rules
[ready-for-review] Unload closes every window the plugin opened; every service has `stop()` — `spec/007` § Unload
[ready-for-review] Sign-in hosts `auth-{env}.mapflow.ai` for staging and internal — `spec/002_api.md`
[ready-for-review] Report dialog behind "Send a report", with the user's comment — `spec/006` § The report dialog

## 2. Defects

[ready-for-review] Run again on a catalog image shows that image in the run form (Fibery milestone 413: "Run again restores … catalog imagery")
[ready-for-review] A file that disappears before its upload leaves no upload flag set — `spec/006` § A guarded callback is interrupted
[ready-for-review] "Review this result in Mapflow Web" opens the processing, not the home page

## 3. Features

[ready-for-review] Restart for failed and cancelled processings, for every role that may run one — `spec/002_B`
[ready-for-review] Processing search on the server (`terms`) — `spec/002_B`
[ready-for-review] Off-nadir range slider 0–30° — `spec/002_D` § What the plugin sends
[ready-for-review] "Available for me" switch in the imagery search — `spec/002_D`
[ready-for-review] The area is clipped to the footprint of the chosen catalog image — `spec/002_B` § AOI and the imagery footprint
[ready-for-review] Upload limits and free storage from `GET /rasters/memory` — `spec/002_C` § Storage Endpoints
[ready-for-review] Rename a collection — `spec/002_C`
[ ] Download an original image — `spec/002_C` § Client-side download
[ ] Rename a project — `spec/002_A`
[ ] Delete a project — `spec/002_A`
[ ] Forced upgrade when the backend expects a higher major version — `spec/002_api.md` § Versioning policy
[ ] Terms of use link on the sign-in page
[ ] XYZ/TMS layers that QGIS already has as an imagery source — `spec/001`. Needs its own spec text for the source parameters before the code
[ ] Planned processings in the Processings tab, with a "search processing" mark; a click opens Mapflow Web — `spec/002_F` § Plugin behaviour in Mapflow Next

## Later, not in 4.0.0

[ ] Pin the test images by digest, so the end-to-end tests name the QGIS they ran on — `spec/004` § Test runtime
[ ] Review where state lives (controller versus services, an `AppContext`) and callbacks versus signals — `spec/007` § Where the code is not there yet
[ ] Translations (es, pt, ru, zh) — 4.1

# V 3.7.0 LTR

**Superseded by 4.0.0 for everything below that is about the 3.x code base (`mapflow/`).** Kept until the
4.0.0 release decides what, if anything, is carried over.


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

Follow-ups it left behind:

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

[ ] Check whether a slot on a plugin signal is really covered by the guard
    `spec/007` § Entry points says a slot connected to a plugin `pyqtSignal` needs no guard of its
    own, because the signal emits synchronously inside an already-guarded stack. If PyQt5 instead
    hands an exception raised in such a slot to `sys.excepthook`, QGIS's raw dialog gets it and the
    report tier is skipped — and the startup configuration is reached exactly that way
    (`statusApplied`, `savedProjectResolved`). A few lines settle it: emit a plugin signal from
    inside `call_guarded` with a slot that raises, and see which tier answers. Then either the spec
    stands or those connections need the guard (and the entry-point test needs to see them).

[ ] Bring master's hotfixes into dev
    `master` carries eight commits `dev` does not (`agent-git log dev..origin/master`), among them
    the My Imagery download rework (`bdcaf51`, `a8f7943`). The download itself still bypasses `Http`
    on `dev` (`DataCatalogService.save_downloaded`, a raw `nam.get`), so it has no request mode, no
    timeout and no plugin-version header; left alone on purpose until the rework is in, then decide
    its mode there.
    Expect conflicts rather than a clean merge: master touches `data_catalog.py`, `layer_utils.py`,
    `mapflow.py`, `config.py`, `main_dialog.py`, `provider_service.py` and `schema/project.py`, and
    the refactoring rewrote all of them. It only gets worse with every further step, and none of
    those eight fixes can ship in 3.7.0 until this lands.

[ ] Bring the remaining outliving subscriptions under `unload` (`spec/007` § The composition root)
    The rule landed with three known violations, all made outside the root:
    - the search footprint layer's `selectionChanged` — `SearchController.on_metadata_layer_ready`
      and `ProviderService` on the duplicate path. Only the current footprint layer carries it (a
      new search removes the previous one), and its token is `app_context.meta_layer_table_connection`.
    - the layer-tree group's `destroyed` / `nameChanged` lambdas — `Mapflow.set_layer_group` and
      `ResultsLoader`. Both are also **raw, unguarded** connects the entry-point test does not see:
      its classifier only knows the signal names it lists, so an unlisted Qt signal fails open.
    Decide with it whether the rule gets an enforcement test, as the guard rule has.

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

