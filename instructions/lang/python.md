---
description: "Python + PyQGIS conventions: PEP 8, module-function pattern, Qt/QGIS imports, layered functional/ structure, containerized test tiers. Applies during delivery, stabilization, and review when files under mapflow/ or tests/ are touched."
applyTo: "{mapflow,tests}/**"
---

# Python / PyQGIS Language Pack

Layered on top of `instructions/delivery.md`, `instructions/stabilization.md`, and `instructions/review.md`. Read this pack whenever the change touches Python sources or tests. Changes under `mapflow/dialogs/**` are additionally covered by `instructions/lang/ui.md`.

## Style
- Follow PEP 8.
- Keep imports at file top — no lazy imports inside functions unless a circular dependency requires it.
- Type-hint public functions and module-level constants.

## Architecture Pattern: Module-Level Functions
Prefer module-level functions over classes unless OOP is genuinely necessary (state machines, Qt classes, polymorphism with shared invariants). Use `import module` and call `module.function()` rather than importing the function directly.

Good
```python
# file: my_service.py
def do_smth():
    pass

# file: my_controller.py
from mapflow.functional.service import my_service

def do_smth_request():
    return my_service.do_smth()
```

Bad
```python
# file: my_service.py
class MyService:
    def do_smth(self):
        pass

# file: my_controller.py
from mapflow.functional.service.my_service import MyService

def do_smth_request():
    my_service = MyService()
    return my_service.do_smth()
```

Qt subclasses are the standing exception — dialogs, widgets, and anything carrying signals must be classes.

## Layering
Where a given kind of code belongs (see AGENTS.md PROJECT STRUCTURE for the full tree):

- `mapflow/functional/api/` — HTTP calls to the Mapflow backend. No Qt imports, no user-facing strings.
- `mapflow/functional/service/` — business logic and orchestration. No Qt widget access.
- `mapflow/functional/controller/` — coordinates services and views; owns the flow of a user action.
- `mapflow/functional/view/` — populates and reads UI state.
- `mapflow/dialogs/` — display and user interaction only (see `lang/ui.md`).
- `mapflow/entity/` — domain models. `mapflow/schema/` — wire/data schemas. `mapflow/errors/` — error types and user-facing messages.

Do not reach across layers: a dialog must not call `api/` directly, and `api/`/`service/` must not import Qt widgets.

## PyQGIS / Qt Conventions
- Use PyQt5 imports (e.g. `from PyQt5.QtWidgets import QDialog`). This plugin targets **QGIS 3 / Qt5**; 3.7.0 is the last QGIS 3 release, so avoid adding Qt5-only idioms that will be expensive to port to Qt6.
- For the QGIS API: `from qgis.core import ...`, `from qgis.gui import ...`.
- Connect signals with new-style syntax: `widget.signal.connect(slot)`.
- Keep business logic out of dialog classes — delegate to `functional/`.
- Anything importing `qgis.*` or `PyQt5.*` can only be tested in the `qgis`/`ui` tiers, never in `functional`. If you want a behavior covered by the fast tier, keep it in a module free of those imports.

## Error Handling
- Do not use broad `except Exception` to keep the plugin alive. Catch the specific exceptions the call can actually raise, so unrelated failures surface instead of being logged and ignored.
- User-facing messages belong in `mapflow/errors/` — not inline at the raise site.

## Tests
- All tests run **inside the QGIS Docker image** via `agent-make` — never from a host venv. The QGIS bindings are not importable on the host.
- Place a test in the cheapest tier that can run it: `tests/functional/` (no QGIS import anywhere in the chain), `tests/qgis/` (needs the QGIS runtime), `tests/ui/` (Qt widgets, xvfb).
- Entry points: `agent-make test-functional`, `agent-make test-qgis`, `agent-make test-ui`, and `agent-make test` for all three. See AGENTS.md COMMANDS and MAKE COMMAND POLICY.
- `tests/ui/` is an empty harness today and its target passes on "no tests collected" — do not read a green `test-ui` as evidence your UI change works.

### Three ways a test here fails invisibly

Each of these produces a **passing or hanging** run rather than a failing one, so nothing tells you
the test stopped testing. All three were hit repeatedly during the Phase C extractions.

1. **A mocked view answers every question truthily.** After moving a read from `self.dlg.<widget>`
   to a view method, any fixture still setting `dlg.<widget>` becomes inert — and a bare
   `MagicMock()` returns a truthy stand-in for the new call, so guards like
   `if view.row_count() == 0: return` silently stop firing. When a guard's *falsiness* is what the
   test is about, set the view method's `return_value` explicitly; never rely on the default.
   After any such move, grep the suite for the old `dlg.<widget>` fixture lines by hand.
2. **`Class.__new__(Class)` on a QObject makes `connect()` a no-op.** Without
   `QObject.__init__(obj)` the signal machinery is absent, so every connection silently does
   nothing and any assertion on an emitted effect passes for the wrong reason. Call
   `QObject.__init__` in the helper that builds it.
3. **An unstubbed modal hangs the suite instead of failing it.** `alert()` and friends default to
   `blocking=True`, which is `QMessageBox.exec()` — an event loop with nothing in the headless
   container to close it. There is no output naming the test; the tier simply never finishes.
   `tests/qgis/conftest.py` patches the dialog entry points suite-wide, so this is handled — do not
   remove that guard, and when adding a new alert helper, add it there too.

## Stabilization Checklist (Python-specific, per fix cycle)
- Imports remain at file top (PEP 8) — no lazy imports introduced by the fix.
- Module-function pattern preserved; no incidental class wrapping.
- No new broad `except Exception` introduced to make a test pass.
- A fix that moves code between modules has not silently pushed a `functional`-tier test into needing the QGIS runtime.

## Review Checklist Add-ons (Python-specific)
- Layering respected — no dialog calling `api/` directly, no Qt import in `api/`/`service/`.
- Exception handling is narrow and intentional; failures the user must know about are not swallowed.
- User-facing strings are translatable and sourced from `mapflow/errors/` where they describe failures.
- New behavior is covered in the cheapest viable tier, not parked in `tests/qgis/` out of convenience.
