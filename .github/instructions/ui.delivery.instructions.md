---
description: "Use when creating or modifying Qt dialogs, widgets, and UI interactions in the QGIS plugin."
applyTo: "mapflow/dialogs/**"
---

# UI Delivery Instructions

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

## Separation of Concerns
- **Dialogs** (`mapflow/dialogs/`): display, user interaction, signals. No business logic.
- **Controllers** (`mapflow/functional/controller/`): coordinate between views and services.
- **Views** (`mapflow/functional/view/`): populate and read UI state.
- **Services** (`mapflow/functional/service/`): business logic and orchestration.
- **API clients** (`mapflow/functional/api/`): HTTP calls to Mapflow backend.

## Signal/Slot Conventions
- Use new-style signal connections: `widget.signal.connect(self.on_something)`.
- Define custom signals as class attributes: `mySignal = pyqtSignal(type)`.
- Prefer `pyqtSignal` over manual event handling.

## Icons and Resources
- Icons are managed in `mapflow/dialogs/icons.py`.
- Set icons in Python code (not in `.ui` files) to avoid `resources_rc` import issues.

## Widget Naming
- Use descriptive camelCase names in `.ui` files matching existing conventions (e.g. `polygonCombo`, `outputDirectory`, `addProvider`).

## Quality Guardrails
- Do not add layout logic in Python that can be expressed in `.ui` files.
- Keep dialog `__init__` focused on setup; move complex initialization to dedicated methods.
- Ensure all user-visible strings are translatable (use `self.tr()` or QGIS i18n patterns).
