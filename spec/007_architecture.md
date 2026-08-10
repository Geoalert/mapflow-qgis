# 007 Architecture

## Purpose
Define the target module structure, the layers and what each may depend on, and the
invariants that keep the structure from decaying back. This is the destination for the
3.7.0 refactoring; the ordered steps to reach it live in `WAL.md`.

## Content

### Why the current structure fails

Recorded because each item below is a rule in this document, and a rule without its
motivating failure gets "simplified away" by the next reader.

- **`mapflow.py` is a god object**: ~4500 lines, ~200 methods, spanning twelve unrelated
  domains (auth, account status, AOI editing, imagery search, local filtering, templates,
  previews, providers, processing, review/rating, results, projects). It holds 351 direct
  `self.dlg.<widget>` references, so business rules and widget manipulation are the same
  code.
- **A `view/` layer exists but is bypassed.** Services reach into dialog widgets directly:
  `provider_service` 38 references, `project_service` 28, `data_catalog` 29,
  `processing_service` 29, `layer_utils` 11. A layer that can be skipped is not a layer.
- **There is a live import cycle.** `schema/processing.py` imports
  `entity.provider.provider.SourceType`; importing the `entity.provider` package runs
  `basemap_provider`, which imports `schema.processing` back. Both test tiers work around
  it by importing the tree twice and swallowing the first `ImportError`.
- **`entity/` is mostly dead.** `entity/status.py` is a byte-for-byte duplicate of
  `schema/status.py` apart from one relative import, and `entity/processing.py` has no
  importers at all. Only `entity/provider/` is live. Two independent `ProcessingStatus`
  enum classes exist at runtime, and enum members from the two are never equal.
- **`requests/` is an empty package.**
- **`constants.py` (5 values) and `config.py` (~150 lines) split on no principle.**
- **`functional/` names nothing.** It contains the api/controller/service/view packages
  *and* loose modules (`auth`, `geometry`, `helpers`, `layer_utils`, `app_context`).
- **The test suite is welded to the current class shapes.** 43 of 51 QGIS-tier test files
  construct objects with `Class.__new__(Class)` and hand-set attributes. They are unit
  tests of internal structure, so moving a method breaks them by construction. They cannot
  serve as the safety net for a refactoring that moves methods.

### Target structure

```
mapflow/
  __init__.py          classFactory only
  mapflow.py           QGIS entry point: initGui/unload, menu and toolbar wiring,
                       construction of services and controllers. No domain logic.
  context.py           AppContext — shared session state
  config.py            all configuration and constants (constants.py merged in)
  helpers.py           free functions with no plugin state
  geometry.py          geometry helpers
  styles.py            .qml style lookup for result layers

  api/                 one module per backend area; builds requests, parses responses
  service/             business logic and state
  controller/          signal wiring: widget signal -> service call -> view update
  view/                widget reads and writes
  dialogs/             .ui files and thin dialog classes
  schema/              shapes that cross the network
  model/               types the plugin owns and persists locally
  errors/
  infra/               http, error_guard, report_throttle, log_config
```

Deleted: `requests/`, `entity/`, `functional/` as a container, `constants.py`.

`mapflow.py` keeps its name. It stays the entry point; what changes is that it holds
wiring instead of domain logic.

### schema/ versus model/

**`schema/` is what crosses the network. `model/` is what the plugin owns and persists
locally.** "API object versus in-app DTO" is close, but has a grey zone this codebase sits
in, so the test is the wire, not the usage.

The distinction is already marked mechanically, and `schema/base.py` says so: `Serializable`
carries `as_dict`/`as_json` and builds request bodies; `SkipDataClass` carries `from_dict` and
exists so response parsing survives non-breaking API changes. Exactly two modules in the
current tree inherit neither — `billing.py`, a vocabulary parsed from `/user/status`, which
stays; and `processing_history.py`, which reads and writes `processing_history_{project_id}`
in QgsSettings, which moves.

So `model/` is small on purpose:

- `model/provider/` — the provider classes. Configured by the user, persisted under
  `mapflow_data_providers`, and carrying real behaviour (`to_processing_params`).
- `model/processing_history.py` — the local per-project processing cache.

**Do not grow `model/` by mirroring response types.** Most of what looks like an in-app DTO
*is* the parsed API object: `MapflowProject`, `ProcessingDTO`, `MosaicReturnSchema` and
`ImageReturnSchema` are all held directly in `AppContext`. Wrapping those in parallel domain
classes buys nothing and costs a hand-written mapping per type, which then drifts — the same
failure `entity/` died of. A response type earns a place in `model/` only when the plugin
starts owning state the response does not describe.

**The split makes the import cycle structurally impossible rather than fixed once.** `model/`
may import `schema/` — a locally-owned provider legitimately produces a request shape.
`schema/` may never import `model/`. Today's cycle is exactly a violation of that direction:
`schema/processing.py` reaches into the provider package for `SourceType`. The fix then
follows from the rule rather than being a one-off: the provider primitives (`SourceType`,
`CRS`, `BasicAuth`) belong in `schema/` as a leaf module, and `model/provider/` imports them
from there.

### Layer rules

Dependencies point downward only. The list is ordered; a layer may import from any layer
below it and from `model/`, `errors/`, `infra/`, `config`, `helpers`, `geometry`.

| layer | may import | must never |
|---|---|---|
| `mapflow.py` | everything | contain domain logic |
| `controller/` | service, view, model, schema | touch `Http`, hold domain state |
| `view/` | model, schema, dialogs | issue requests, contain business rules |
| `service/` | api, model, schema, other services | import `view/`, `dialogs/`, or touch a widget |
| `api/` | model, schema, infra | know about widgets or business rules |
| `model/` | schema, errors, config | import anything above it |
| `schema/` | errors, config | import `model/`, or anything above it |

**The rule that does the work: `service/` may not touch a widget.** Every current
layering violation is an instance of it, and it is mechanically checkable — a service
module must not import `PyQt5.QtWidgets`, `dialogs`, or `view`, and must not receive a
`dlg` argument.

**The rule that keeps the import cycle dead: `schema/` may not import `model/`.** The
dependency between the two runs one way only, so the cycle cannot be reintroduced by
someone who does not know it once existed.

### Services

State and business rules. Each owns one question, and nobody else answers it.

| service | owns | boundary |
|---|---|---|
| `SessionService` | credentials, login (basic/oauth), logout, plugin-version check | knows how to authenticate; knows nothing about what the account may do |
| `AccountService` | everything derived from `/user/status`: billing type, limits, area caps, provider min-areas | the only parser of that response. Read by many services, which is why it is separate from `SessionService` — credentials are consulted by nothing but `Http` |
| `ProviderService` | the provider list (built-in, Mapflow, user-defined), persistence in settings, current selection | what imagery sources exist and which is chosen; not what is done with one |
| `AoiService` | AOI geometry, AOI layers, the on-map draw/update edit sessions, the selected-AOIs layer | AOI *as geometry and layers*. Which AOIs a template has belongs to `TemplateService` |
| `SearchService` | imagery-search requests, the result set, the footprints layer, pagination, sort | fetching and holding results |
| `LocalFilterService` | client-side narrowing of an already-fetched result set, and the "filter is wider than what was fetched" warning | pure computation over a result set plus filter values; issues no request |
| `TemplateService` | planned processings: CRUD, status polling, template AOIs, search params, seen/new markers, exclude-from-search, pause/resume/restart | everything scoped to a template id |
| `ProcessingService` | processings list and polling, start/duplicate/delete/restart, cost, review and rating | loses templates to `TemplateService` |
| `PreviewService` | preview layers (XYZ, PNG, mosaic, catalog image), their dedup and placement | preview layers only; result layers are `ResultService` |
| `CatalogService` | My Imagery: mosaics, images, upload, storage quota | |
| `ProjectService` | projects CRUD, sharing, roles, the current project | |
| `ResultService` | downloading and loading processing results, applying styles | from `layer_utils.ResultsLoader` |
| `AreaCalculatorService` | area computation and limit comparison | unchanged |
| `AlertService` | the *message* tier of `spec/006_error_reporting.md` | unchanged |

Services communicate through Qt signals, never by calling a controller. Several already do
this (`DataCatalogService.mosaicsUpdated`); it becomes the rule. A service that needs to tell
the UI something emits, and a controller subscribes.

### Controllers

One per UI region, not one per service — a region typically drives several services. A
controller wires signals and holds no domain state.

| controller | region |
|---|---|
| `MainController` | dialog shell: tab switching, login/logout wiring, global menus |
| `ProcessingController` | the start-processing panel: model and options, AOI and provider selection, cost, start-button state |
| `ProjectProcessingController` | the projects/processings table and navigation between projects, processings and a template |
| `SearchController` | imagery-search tab: params, run, filter widgets, pagination, sort, table↔layer selection sync |
| `TemplateController` | template view: details, AOIs, search params, template processings, seen markers |
| `CatalogController` | My Imagery |
| `ProviderController` | provider add/edit/remove dialogs and the provider combos |

Controllers must not call each other. Cross-region effects travel as a service signal, so
adding a second listener never means editing the first controller.

### Dialogs and .ui files

Qt Designer is the source of truth for structure. The current pattern is already right —
every dialog calls `uic.loadUiType()` at runtime and **no `pyuic5` output is committed** —
so the inconsistency to fix is the Python layered on top: `main_dialog.py` is 803 lines and
builds static widgets programmatically in several places, which is exactly what makes those
widgets invisible in Designer.

Rules:

1. **Static structure lives in the `.ui` file.** Anything with a fixed place in the layout is
   defined in Designer, not created in Python.
2. **Never commit generated Python.** `.ui` files are loaded at runtime with
   `uic.loadUiType`; unreadable generated code is the reason.
3. **Python may create a widget only when Designer cannot express it** — genuinely dynamic
   sets (one checkbox per model option), or content that depends on runtime data. Widgets
   created this way are added to a container that *is* defined in the `.ui`.
4. **QGIS and custom widget classes go in through promotion**, not through Python
   construction, so they keep their place in the Designer tree.
5. `.ui` is XML and may be edited directly — by a human or an agent — but it must stay
   valid and round-trippable through Designer. Structural edits are verified by opening the
   file in Designer before merge.

The test of a correct dialog: opening its `.ui` in Designer shows the whole layout, and the
matching `.py` contains behaviour only.

### Entry points

A controller method connected to a Qt signal is **the** definition of an entry point in
this plugin. That matters beyond tidiness: `error_guard.guard_entry_point` is applied at
entry points, and today "entry point" cannot be identified because `mapflow.py` mixes
slots, callbacks and helpers in one class. Once controllers own the signal connections,
the set of places needing the guard is enumerable rather than a judgement call.

See `spec/006_error_reporting.md` for what the guard does and the constraint that a
guarded callback is interrupted rather than completed.

### The test surface that survives a move

A test that names a method of a class is invalidated when that method moves. A test that
names an *observable effect* is not. The refactoring is verified against four surfaces,
all of which outlive any file layout:

1. **The HTTP conversation** — which endpoints are called, with which bodies, in what
   order. Specified in `spec/002_api.md` and its sub-files.
2. **QGIS state** — which layers exist, in which groups, with which styles.
3. **Settings** — the keys written and read, per `spec/003_local_storage.md`.
4. **Widget-visible state** — enabled/disabled controls, displayed text, table contents.

Behavioral tests drive a user journey from a controller entry point with `Http` replaced
by a recording fake, and assert only on those four. They are the safety net for every
extraction step, and they are written **before** the first method moves.

The existing `Class.__new__(Class)` tests are not deleted wholesale — they stay until the
code they pin has moved, then are rewritten against the new owner or dropped where the
behavioral test already covers them. A step that moves code must not leave a behaviour
covered by neither.

### Invariants

1. A service module imports no widget and receives no dialog.
2. `schema/` imports nothing from `model/` or from the layers above it.
3. There are no import cycles. The test-tier bootstraps must not need a retry loop; when
   the cycle is gone, that workaround is deleted, and its absence is the check.
4. One concept has one home. A type is defined once — no parallel copies across packages.
5. `mapflow.py` contains no `self.dlg.<widget>` access.
6. New and moved code adds nothing to the `.flake8` debt ledger. The ledger only shrinks.

### Enforcement

Invariants 1–3 are checked by a test, not by review. `tests/functional/test_layering.py`
walks the import statements of each package and fails with the offending module and import
when a rule is broken.

This is deliberate, and `tests/functional/test_tier_layout.py` is the precedent: the
stranded-test-file problem it now guards against had survived review for a long time
precisely because nothing executed the rule. View isolation decays the same way — it is
invisible in a diff that adds one import to one service — so the rule ships with its check
or it does not hold.

The check is written **before** the extraction starts, with the current violations recorded
as an explicit allowlist. Each extraction MR removes entries; the list only shrinks, like
the `.flake8` ledger. That way the invariant is enforced for all new code from day one
instead of only after the last domain moves.
