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

[ ] Delete the dead modules and the empty package
`entity/status.py` is byte-identical to `schema/status.py` except one relative import, and
nothing imports `entity/processing.py` or `entity/status.py` at all. `requests/` holds only an
empty `__init__.py`. ~340 lines plus a package.
Note while deleting: two `ProcessingStatus` enum classes exist at runtime today, and members of
the two are never equal. Confirm nothing compares across them before assuming this is inert.

[ ] Break the `schema` ⇄ `entity.provider` import cycle
`schema/processing.py:12` imports `entity.provider.provider.SourceType`; importing the
`entity.provider` package runs `basemap_provider`, which imports `schema.processing` back.
Move the provider primitives (`SourceType`, `CRS`, `BasicAuth`) into a leaf module that imports
nothing from the plugin.
Acceptance: the retry loops in `tests/functional/conftest.py` and `tests/qgis/conftest.py` are
deleted and both tiers still pass. Their absence is the regression check.

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

[ ] Extract AOI editing and AOI layers → `service/aoi_service.py` + controller
[ ] Extract preview → `service/preview_service.py`
[ ] Extract imagery search and the local filter → `service/search_service.py` + `view/search_view.py`
[ ] Extract templates → `service/template_service.py` (the largest domain, ~55 methods)
[ ] Extract processing lifecycle: options, start, review, rating → existing processing service/controller
[ ] Extract session and account status → `service/session_service.py`
[ ] Reduce what remains to `plugin.py` — initGui/unload, wiring, construction
Acceptance for the phase: no `self.dlg.<widget>` access in `plugin.py`, and no service imports a
widget (`spec/007_architecture.md` invariants 1 and 5).

### Phase D — move the packages

Mechanical, and cheaper here than earlier: the god object is gone, so fewer files churn.

[ ] `functional/` dissolved: `api/`, `controller/`, `service/`, `view/` to the root; `app_context`
    → `context.py`; `auth`, `geometry`, `helpers`, `layer_utils` to their layer homes
[ ] `schema/` + the live `entity/provider/` → `model/`; `http`, `error_guard`, `report_throttle`,
    `log_config`, `styles` → `infra/`

### Phase E — UI consistency

[ ] One consistent way to build a dialog
All 13 dialogs load a `.ui` file, so the inconsistency is how much Python is layered on top —
`main_dialog.py` is 803 lines and builds widgets programmatically in several places. Decide the
rule, then apply it.

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

