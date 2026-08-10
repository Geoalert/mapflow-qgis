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
  plugin.py            QGIS entry point: initGui/unload, menu and toolbar wiring,
                       construction of services and controllers. No domain logic.
  context.py           AppContext — shared session state
  config.py            all configuration and constants (constants.py merged in)
  helpers.py           free functions with no plugin state
  geometry.py          geometry helpers

  api/                 one module per backend area; builds requests, parses responses
  service/             business logic and state
  controller/          signal wiring: widget signal -> service call -> view update
  view/                widget reads and writes
  dialogs/             .ui files and thin dialog classes
  model/               domain types (former schema/ plus the live part of entity/)
  errors/
  infra/               http, error_guard, report_throttle, log_config, styles
```

Deleted: `requests/`, `entity/processing.py`, `entity/status.py`, `functional/` as a
container, `constants.py`.

### Layer rules

Dependencies point downward only. The list is ordered; a layer may import from any layer
below it and from `model/`, `errors/`, `infra/`, `config`, `helpers`, `geometry`.

| layer | may import | must never |
|---|---|---|
| `plugin.py` | everything | contain domain logic |
| `controller/` | service, view, model | touch `Http`, hold domain state |
| `view/` | model, dialogs | issue requests, contain business rules |
| `service/` | api, model, other services | import `view/`, `dialogs/`, or touch a widget |
| `api/` | model, infra | know about widgets or business rules |
| `model/` | errors, config | import anything above it |

**The rule that does the work: `service/` may not touch a widget.** Every current
layering violation is an instance of it, and it is mechanically checkable — a service
module must not import `PyQt5.QtWidgets`, `dialogs`, or receive a `dlg` argument.

`model/` must import nothing from `api/`, `service/`, `view/`, `controller/` or
`dialogs/`. This is what keeps the import cycle from coming back, and it is why
`SourceType` and the other provider primitives belong in `model/` rather than being
imported *from* a package that imports schemas.

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
2. `model/` imports nothing from the layers above it.
3. There are no import cycles. The test-tier bootstraps must not need a retry loop; when
   the cycle is gone, that workaround is deleted, and its absence is the check.
4. One concept has one home. A type is defined once — no parallel copies across packages.
5. `plugin.py` contains no `self.dlg.<widget>` access.
6. New and moved code adds nothing to the `.flake8` debt ledger. The ledger only shrinks.
