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

Everything here is behaviour-preserving and verifiable by the current suite. Doing it first
means the extraction MRs move less code and read as pure moves.

[ ] Architecture invariant test
`tests/functional/test_layering.py` — no service imports a widget, `dialogs`, or `view`;
`schema/` imports nothing from `model/` or above; no import cycles. Current violations go in an
explicit allowlist that later steps only shrink.
Written now, not after the extraction, so every new line is held to the rule from the start.
Precedent and rationale: `tests/functional/test_tier_layout.py`.

[ ] Narrow the remaining broad exception handlers
38 `except Exception` sites (processing_service 14, mapflow 11, nine files with 1–2).
Acceptance: `E722` out of the `.flake8` ledger, bandit reports no `B110`.
Kept in Phase A rather than deferred with the other lint work: a handler that swallows
everything hides a broken extraction, and Phase C moves code past these sites constantly.

[ ] Merge `constants.py` into `config.py`
Five values, no principle separating them from the other ~150 lines.

### Phase B — a test surface that survives the move

[ready-for-review] Behavioral test tier
Twelve journeys under `tests/qgis/behavioral/`, one per domain Phase C moves, every test
verified by mutating the code it covers. The existing `Class.__new__(Class)` tests stay until
the code they pin moves; no extraction may leave a behaviour covered by neither.

### Phase C — dissolve the god object

One domain per MR, each ending with `mapflow.py` smaller and no behaviour changed. Ordered
leaf-first so each extraction depends only on what already moved.

Service and controller boundaries are tabulated in `spec/007_architecture.md`.

[ ] Extract AOI editing and AOI layers → `AoiService` + `ProcessingController` wiring
[ ] Extract preview → `PreviewService`
[ ] Extract imagery search → `SearchService` + `SearchController` + `view/search_view.py`
[ ] Extract the local filter → `LocalFilterService` (pure computation; functional-tier tests)
[ ] Extract templates → `TemplateService` + `TemplateController` (largest domain, ~55 methods
    in `mapflow.py` plus the template half of `processing_service.py`)
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

[ ] Wrap user interactions in error_guard
`guard_entry_point` is written and tested but applied nowhere; only `Http.response_dispatcher` is
guarded. Everything entering plugin code from Qt without passing through `Http` still escapes to
QGIS's raw unhandled-exception dialog: button clicks, selection changes, timer ticks,
drag-and-drop, dialog accept/reject.
Cheap once Phase C lands — a controller slot is the definition of an entry point
(`spec/007_architecture.md` § Entry points), so the sites are enumerable instead of guessed.

[ ] Restore user-facing errors on the polled paths
Three call sites opt out of the default error handler purely to avoid stacked modals:
`mapflow.py` `refresh_status`, `mapflow.py:3042`, and `processing_api.py` `get_processings`. A real
server error on those paths is invisible to the user. The throttle removes the reason for the
workaround, but `report_http_error` needs its own signature (Qt error code + endpoint path) first,
so both dialog paths land on one suppression policy.

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

[ready-for-review] B12 — style files are loaded onto the layers that should get them
Scope is the *loading*, not the rendering: which `.qml` is chosen for a given model and layer
kind, and that applying it succeeds. Whether the result looks right on screen is a visual
check and stays manual.
`ResultsLoader.load_result_tiles` styles the result layer with
`layer.loadNamedStyle(get_style_name(...))`, and `loadNamedStyle` fails silently on a missing
file. So a refactor that moves the `.qml` resources — Phase D moves `styles.py` — leaves every
result unstyled with nothing in the log to say so. Note there are two families of path,
`generate_local_style_path` and `generate_tile_style_path`, so a test that only exercises one
would miss half of it.
Left out of the B10 behavioral journey on purpose: every way of checking it from there reaches
into the style helpers, and a behavioral test that names internals is the thing that suite
exists to avoid. It wants a unit test against `get_style_name` covering both path families,
plus a check that each resolves to a file that exists.
While writing it, fix `mapflow/styles.py get_style_name(wd: str, layer, style_name=None)`: the
annotation says `str` but the body reads `wd.name`, so the hint is actively misleading — which
is how the first attempt at this test was written wrong.

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

