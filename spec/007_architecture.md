# 007 Architecture

## Purpose
Define the module structure, the layers and what each may depend on, and the
invariants that keep the structure from decaying back.

This document has two parts. **§ Mapflow Next (4.x)** is the structure of `mapflow_next/` and is
what gates work on it. Everything from **§ Why the current structure fails** on was written for
the 3.7.0 refactoring of the 3.x plugin (`mapflow/`): it is kept because it is the reasoning the
4.x rules come from, but its module names, its `.ui` rules and its tests
(`tests/functional/test_layering.py`, `test_entry_points_guarded.py`, `guarded_connect`) do not
exist in `mapflow_next/` and bind nothing there.

## Mapflow Next (4.x)

### Structure

```
mapflow_next/
  plugin.py        the composition root: toolbar, menu, dock, wiring; undoes all of it on unload
  controller.py    the flow: connects services to pages and to QGIS
  config.py        environments, URLs, timings      settings.py   QgsSettings under mapflow_next/
  core/            pure Python, no Qt: models, the run form as data (draft.py), scenarios, messages, OAuth helpers
  api/             HTTP over QgsNetworkAccessManager (http.py), the endpoints (client.py), credentials, browser sign-in
  services/        Qt objects that hold state and emit signals: session, processings, imagery, results
  qgis_bridge/     map-side code: area from layers, layers and styles, draw tool; compat.py for QGIS 3/4
  ui/              dock, pages, dialogs, theme and icons — built in code, no .ui files
  resources/       scenarios, result styles (QML), fonts, icons
```

### Layer rules

| layer | may import | must not |
|---|---|---|
| `core/` | the standard library | import Qt or QGIS: it is tested without them |
| `api/` | `core/`, `config`, Qt/QGIS networking, the QGIS authentication manager and message log, `QDesktopServices` (to open the browser for sign-in) | know about pages or services |
| `services/` | `api/`, `core/`, `qgis_bridge/`, `config`, `settings` | import `ui/`, or build a widget |
| `qgis_bridge/` | `core/`, `config`, QGIS | import `ui/` or `services/` |
| `ui/` | `core/`, `config`, `settings`, other `ui/` modules | import `services/` or `api/`: a page renders what it is given and emits what the user wants |
| `controller.py` | everything above | talk to `Http` directly: requests go through `api/client.py` or a service |
| `plugin.py` | everything | — |

A value that both a page and a service need (the result modes, the default output folder) lives in
`config` or `core/`, where both may import it — not in the service.

### Unload

`plugin.py` undoes everything it and the controller set up: timers stopped, QGIS and project signals
disconnected, actions, toolbar and dock removed, and **every window the plugin opened closed and
deleted** — the scenario gallery, the Projects window and the My imagery window are children of the
QGIS main window and would otherwise outlive the plugin. Every service has a `stop()` that ends its
timers and pending requests. After unload, no late reply or timer reaches plugin code.

### Where the code is not there yet

Recorded so that nobody mistakes the current shape for the intended one, and so that a change in these
areas moves toward the rule instead of copying its neighbour.

- **State lives in the controller as well as in the services.** The rule is that services hold state,
  pages render it and the controller connects them. In fact `controller.py` — one class of some 2,200
  lines — holds the run draft, the chosen catalog image, zoom choices, project pins and a number of
  pending flags, and runs the upload check flow itself. This was a deliberate shortcut to ship the
  redesign: the run form's state touches every service, and no service was its natural owner.
  **It is to be reviewed after 4.0.0.** The direction to examine first is an explicit application
  context object (an `AppContext`) that owns the draft and the selections, with the controller split
  by dock region; the 3.x analysis below (§ Why the current structure fails, § Controllers) is the
  reasoning to start from.
- **Services take callbacks as well as emitting signals.** `Imagery.on_duplicate` is a function the
  controller sets and the service calls for a modal answer; `fetch_mosaic`, `delete_mosaic`,
  `delete_image`, `create_collection` and `validate` take `on_done` / `on_error` arguments. The rule is signals. A callback is tolerable for a one-shot answer to
  the caller that asked; it is not for anything a second listener could want. To be settled in the same
  review.
- **Not every entry point is guarded yet** — see `006_error_reporting.md` § The guard, which is the rule.

No new code may add to the first two: new state goes into a service, and a new service method reports
through a signal unless it answers exactly one caller.

## Content (3.x — rationale only, see Purpose)

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
  infra/               http, error_guard, report_throttle, log_config,
                       alert_service (message tier), reporter (report tier)
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
| `service/` | api, model, schema, infra, other services | import `view/`, `dialogs/`, or touch a widget |
| `api/` | model, schema, infra | know about widgets or business rules |
| `infra/` | dialogs, model, schema, errors, config, Qt | hold domain state or business rules |
| `model/` | schema, errors, config | import anything above it |
| `schema/` | errors, config | import `model/`, or anything above it |

**The rule that does the work: `service/` may not touch a widget.** Every current
layering violation is an instance of it, and it is mechanically checkable — a service
module must not import `PyQt5.QtWidgets`, `dialogs`, or `view`, and must not receive a
`dlg` argument.

**`infra/` is the exception that proves it: the one layer that may hold Qt, and the one
every other layer may import.** The message tier (`alert_service`) and the report tier
(`reporter`) live there for exactly that reason — a service may not build a `QMessageBox`
and a view may not import a service, yet both must be able to alert. `infra/` holds
cross-cutting mechanism (transport, reporting, alerts, logging), never domain state.

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

### The composition root

`mapflow.py` is the composition root: it builds the services, views and controllers, wires their
signals, sequences startup, and undoes all of it on `unload`. Three things follow from that.

**It names widgets, and only there.** Constructing a controller means handing it the widgets it
owns, and restoring saved settings into widgets at startup is nobody else's job. So "no widget
access in `mapflow.py`" means *no widget access outside construction and wiring* — behaviour that
reads or writes a widget belongs in a view.

**A fork between two regions belongs here.** When an action must choose which region handles it —
the Search button choosing between an immediate search and creating a template, a results page
served from the catalogue or from an open template, an imagery-source change touching search,
catalog and processing at once — that choice cannot sit in either controller without one calling
the other.

The test is whether the code **decides between** regions or **acts within** one. Deciding belongs
to the root; acting belongs to a controller. Moving such a fork into a controller reintroduces
exactly the coupling the rule above forbids, so it is left where it is on purpose.

**It owns teardown as well as construction.** QGIS does not restart to replace a plugin: an in-place
upgrade from the plugin manager, or Plugin Reloader, calls the old instance's `unload` and builds a
new one in the same process. Anything the old instance attached itself to and did not let go of
keeps running it, against a closed dialog and stale state. So **every subscription to something
that outlives the plugin is undone by `unload`**, whichever layer made it. The root sequences that
teardown; a service or controller that makes such a subscription must leave `unload` a way to
reach it.

What outlives the plugin:

* `QgsProject` and its layer tree, including the groups the plugin created in it;
* every layer in the project — the user's, and equally the ones the plugin added (search
  footprints, results, previews), which stay in the project across a reload;
* the QGIS interface and its map canvas;
* the process-wide `QgsSettings` object `AppContext.settings` shares. A group opened on it and never
  closed nests the next instance's keys one level deeper (`mapflow/mapflow/…`), where no later start
  reads them.

Three constraints on how:

1. **Disconnect by token, never all.** `guarded_connect` returns the connection token; keep it where
   `unload` can reach it. A bare `signal.disconnect()` also removes QGIS's own slots on the project
   and other plugins' slots on the user's layers.
2. **PyQt's automatic clean-up does not apply.** PyQt drops a connection to a bound method when its
   receiver is deleted, but `guarded_connect` connects a closure, which holds the receiver alive and
   is never dropped. A subscription `unload` cannot reach is a leak, not a missed optimisation.
3. **Teardown survives a failing step.** Disconnecting and closing the settings group run in a
   `finally`, so a service stop that raises cannot leave the old instance subscribed. A sender
   already deleted took its connections with it, and must not stop the rest from being undone.

This is not a licence to leave arbitrary logic in the root. A method here must be a fork, a
construction step, a startup sequence, or teardown; anything else has an owner.

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

A slot connected to a **Qt-owned** signal — a widget, `QAction`, `QTimer`, `QgsVectorLayer`,
`QgsProject`, or dialog — is an entry point: its invocation begins a fresh call stack from Qt's
event loop, so an unexpected exception there escapes to QGIS's raw dialog unless it is guarded. A
slot connected to a plugin `pyqtSignal` is **not** a separate entry point: that signal emits
synchronously inside some other entry point's stack, so guarding every Qt-owned connection covers
it transitively.

The guard is applied two ways:

* **At the connection site, `error_guard.guarded_connect(signal, slot, context, version_source)`** —
  used instead of a raw `signal.connect(slot)` for every Qt-owned signal. It wraps the slot in
  `call_guarded` and returns the connection token. This covers what a decorator cannot without
  changing call semantics: lambdas, signal-to-signal forwards, and connections made directly to a
  service or view method.
* **`error_guard.guard_entry_point` (the decorator)** for entry points that are not `.connect`
  sites — the Qt/QGIS event-handler overrides `initGui`, `unload`, `main`, `resizeEvent`.

See `spec/006_error_reporting.md` for what the guard does and the constraint that a
guarded callback is interrupted rather than completed — a slot that owns a state transition
(stopping a timer, clearing an in-flight flag) must perform it before anything that can raise.

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

### What survives the refactoring, and what does not

The natural assumption is that the behavioral suite is scaffolding to be removed once the
refactoring is signed off. It is the other way round.

**Permanent — the behavioral tests, their fixtures, and `capture_fixtures.py`.**
They are the only tests in the repo that assert *user-visible* behaviour; everything else
pins internals, and the tests written against the new structure will pin internals too. The
`test-ui` tier is an empty harness, so without them the plugin ships with no end-to-end
coverage at all. And the release after this one is the QGIS 4 / Qt 6 port — the single
migration where an end-to-end net is worth the most. Deleting it on the way in would be
throwing away the ladder while still on the roof.

**Transient — the `Class.__new__(Class)` suite.** Those 43 files are the ones that shrink,
file by file, as the code they pin moves and their coverage lands in the behavioral suite or
in new unit tests against the new owner.

**The capture tool is part of the deliverable, not a one-off.** Fixtures rot when the API
changes, and a fixture set nobody can regenerate dies the first time the backend adds a
required field — hand-editing fifteen JSON files is not a maintenance plan. Re-running the
tool is how they are reset, and the diff it produces is itself the signal that the API moved.

Consequently the tool must stay runnable, which is why the size caps live inside it rather
than in a manual trimming pass: a re-capture has to reproduce the same small fixtures, not
restore the several hundred kilobytes the raw responses carry.

### Invariants

1. A service module imports no widget and receives no dialog.
2. `schema/` imports nothing from `model/` or from the layers above it.
3. There are no import cycles. The test-tier bootstraps must not need a retry loop; when
   the cycle is gone, that workaround is deleted, and its absence is the check.
4. One concept has one home. A type is defined once — no parallel copies across packages.
5. `mapflow.py` contains no `self.dlg.<widget>` access.
6. New and moved code adds nothing to the `.flake8` debt ledger. The ledger only shrinks.
7. Every Qt-owned signal is connected through `error_guard.guarded_connect`, so no unexpected
   failure at an entry point escapes to Qt's event loop. (Plugin-`pyqtSignal` connections are
   exempt — they are covered transitively; see § Entry points.)

### Enforcement

Invariants 1–3 are checked by a test, not by review. `tests/functional/test_layering.py`
walks the import statements of each package and fails with the offending module and import
when a rule is broken.

Invariant 7 is checked the same way by `tests/functional/test_entry_points_guarded.py`: it walks
every `.connect` call, and a connection to a Qt-owned signal made with a raw `.connect` (rather than
`guarded_connect`) fails unless it is in that test's `ALLOWED_UNGUARDED` allowlist. The allowlist
holds the connections not yet converted; it only shrinks, and a stale entry (a site now guarded)
fails too — the same discipline as the layering allowlist and `test_silent_opt_outs.py`.

This is deliberate, and `tests/functional/test_tier_layout.py` is the precedent: the
stranded-test-file problem it now guards against had survived review for a long time
precisely because nothing executed the rule. View isolation decays the same way — it is
invisible in a diff that adds one import to one service — so the rule ships with its check
or it does not hold.

The check is written **before** the extraction starts, with the current violations recorded
as an explicit allowlist. Each extraction MR removes entries; the list only shrinks, like
the `.flake8` ledger. That way the invariant is enforced for all new code from day one
instead of only after the last domain moves.
