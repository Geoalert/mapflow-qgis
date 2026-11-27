---
description: "Qt dialog conventions for the QGIS plugin: uic.loadUiType pattern, .ui file placement, signal/slot style, icon handling, translatable strings. Applies during delivery, stabilization, and review when files under mapflow/dialogs/ are touched."
applyTo: "mapflow/dialogs/**"
---

# UI Language Pack

Layered on top of `instructions/lang/python.md` — everything in that pack still applies here. Read this pack whenever the change creates or modifies Qt dialogs, widgets, or UI interactions.

## Objective
Maintain consistent Qt/PyQGIS dialog patterns aligned with existing codebase conventions.

## Dialog Pattern
This project uses `uic.loadUiType()` for dialog classes:
```python
from PyQt5 import uic

ui_path = Path(__file__).parent / 'static' / 'ui'

class MyDialog(*uic.loadUiType(ui_path / 'my_dialog.ui')):
    def __init__(self, parent, ...):
        super().__init__(parent)
        self.setupUi(self)
```

- `.ui` files live in `mapflow/dialogs/static/ui/`.
- Dialog classes live in `mapflow/dialogs/`.
- Use Qt Designer to create/edit `.ui` files when possible.

> #WARNING The codebase is currently inconsistent here: some dialogs are Qt Designer `.ui` files loaded at
> runtime, others are heavily hand-coded or generated in Python, and the two are changed in different ways.
> WAL 3.7.0 step "Plan the refactoring" calls for picking one consistent approach. Until that decision lands,
> follow the pattern already used by the dialog you are editing rather than converting it.

## Separation of Concerns
- **Dialogs** (`mapflow/dialogs/`): display, user interaction, signals. No business logic.
- **Controllers** (`mapflow/functional/controller/`): coordinate between views and services.
- **Views** (`mapflow/functional/view/`): populate and read UI state.
- **Services** (`mapflow/functional/service/`): business logic and orchestration.
- **API clients** (`mapflow/functional/api/`): HTTP calls to Mapflow backend.

A dialog must never call `api/` directly.

## Signal/Slot Conventions
- Use new-style signal connections: `widget.signal.connect(self.on_something)`.
- Define custom signals as class attributes: `mySignal = pyqtSignal(type)`.
- Prefer `pyqtSignal` over manual event handling.

## Icons and Resources
- Icons are managed in `mapflow/dialogs/icons.py`.
- **Set icons in Python code, not in `.ui` files** — icons referenced from `.ui` pull in a generated `resources_rc` module that is not reliably importable in the plugin's runtime.

## Widget Naming
- Use descriptive camelCase names in `.ui` files matching existing conventions (e.g. `polygonCombo`, `outputDirectory`, `addProvider`).

## Quality Guardrails
- Do not add layout logic in Python that can be expressed in `.ui` files.
- Keep dialog `__init__` focused on setup; move complex initialization to dedicated methods.
- Ensure all user-visible strings are translatable (use `self.tr()` or QGIS i18n patterns).

## Testing UI Changes
UI code belongs to the `tests/ui/` tier (`agent-make test-ui`, Qt under `xvfb-run`). That tier is an **empty harness today** — its Makefile target treats pytest's "no tests collected" exit code as a pass, so a green run proves nothing about your change. Until the first UI test lands, verify dialog changes manually in QGIS and say so explicitly in the MR; do not present `agent-make test-ui` as evidence.
