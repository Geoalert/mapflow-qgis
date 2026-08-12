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

[ready-for-review] Delete the dead modules and the empty package

[ready-for-review] Split `schema/` and `model/`, break the import cycle, delete `entity/`

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

[ ] Behavioral test tier
43 of 51 QGIS-tier test files build objects with `Class.__new__(Class)` and hand-set attributes,
so they pin internal structure and break the moment a method moves. They cannot be the safety
net for Phase C.
Build `tests/behavioral/`: drive a user journey from a controller entry point with `Http`
replaced by a recording fake, and assert only on the four surfaces in `spec/007_architecture.md`
§ The test surface that survives a move — HTTP conversation, QGIS layer state, settings, and
widget-visible state.
Cover, at minimum, one journey per domain moved in Phase C. Existing `__new__` tests stay until
the code they pin moves; no step may leave a behaviour covered by neither.

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

