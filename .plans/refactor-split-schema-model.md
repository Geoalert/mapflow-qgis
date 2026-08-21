# refactor/split-schema-model — implementer notes

## Scope
Split `mapflow/entity/` into `mapflow/schema/provider_types.py` (leaf, stdlib-only wire
vocabulary) and `mapflow/model/` (provider classes + `ProcessingHistory`), per
`spec/007_architecture.md` § "schema/ versus model/". Breaks the
`schema.processing -> entity.provider -> schema.processing` import cycle by making
`schema/processing.py` import `SourceType` from the new leaf module instead of reaching
into the provider package.

## What moved
- `mapflow/entity/provider/provider.py` -> split:
  - `StrEnum`, `SourceType`, `CRS`, `BasicAuth` -> `mapflow/schema/provider_types.py` (new,
    stdlib-only).
  - `staticproperty`, `ProviderInterface`, `UsersProvider`, `NoneProvider` ->
    `mapflow/model/provider/provider.py`, importing the four wire types back from
    `...schema.provider_types`.
- `mapflow/entity/provider/{__init__,basemap_provider,default,factory,collection}.py` ->
  `mapflow/model/provider/` unchanged in content (same relative-import depth, so no dot-count
  changes needed except in `provider.py` itself and the package `__init__.py`).
- `mapflow/schema/processing_history.py` -> `mapflow/model/processing_history.py`.
  Its `from .status import ProcessingStatus` became `from ..schema.status import
  ProcessingStatus`, and — not spelled out verbatim in the task but the same move —
  its `from .processing import ProcessingDTO` became `from ..schema.processing import
  ProcessingDTO` for the same reason (relative depth changed by the move).
- `mapflow/entity/` deleted entirely via `agent-git rm` per file.

## Import sites rewritten
`mapflow/mapflow.py`, `mapflow/dialogs/provider_dialog.py`, `mapflow/dialogs/main_dialog.py`,
`mapflow/functional/app_context.py`, `mapflow/functional/service/{provider_service,
data_catalog,processing_service,area_calculator_service}.py` — all `..entity.provider` /
`...entity.provider` -> `..model.provider` / `...model.provider`.

`processing_service.py` additionally needed `ProcessingHistory` split out of the
`from ...schema import ...` line into its own `from ...model.processing_history import
ProcessingHistory`, since it no longer lives in `schema`.

Tests: `tests/qgis/test_planned_processing_mode.py`, `test_template_search_footprints.py`,
`test_processing_cost.py`, `test_provider_settings_migration.py` (module-level imports), and
`test_template_aoi.py` / `test_imagery_search_multi.py` (inline `from mapflow.entity.provider
import ImagerySearchProvider` inside test bodies, 2 and 9 occurrences respectively, handled
with `replace_all`).

Both `tests/functional/conftest.py` and `tests/qgis/conftest.py`: removed the `for _ in
range(2)` retry loop, its comment, and the now-unused `import importlib`. `agent-make
test-functional` and `test-qgis` both pass with the loop gone, confirming the cycle is
structurally broken rather than papered over.

## Things I decided beyond the literal task text
- `mapflow.py` had a `# Entity/providers` section comment directly above the moved import
  block. Renamed to `# Providers` (it was a section label, not history-referencing prose;
  "Entity/providers" would have become inaccurate after the move, and the delivery-instructions
  rule against history-referencing comments argues for the plain, accurate label over leaving
  a stale one).
- `mapflow/model/provider/default.py`'s existing `from .provider import BasicAuth` /
  `from .provider import ProviderInterface, SourceType, CRS` lines still work unchanged:
  `model/provider/provider.py` imports those three names from `schema/provider_types` into its
  own namespace, so `from .provider import BasicAuth` etc. still resolves. Left as-is since the
  task only specified rewriting `provider.py`'s own import, not `default.py`'s.
- Reformatted a handful of pre-existing trailing-whitespace lines while retyping moved files
  (e.g. in `default.py`, `provider_service.py`). `W291`/`W293` are in the `.flake8` debt ledger
  (`extend-ignore`), so this is neutral for lint either way; not treating it as an in-scope
  cleanup, just an artifact of hand-retyping via the Write tool.

## Verification
- `agent-make test` — 53 functional + 434 qgis passed, `test-ui` empty-harness guard passed.
- `agent-make lint` — flake8, bandit, detect-secrets all clean, nothing added to `.flake8`.
- Repo-wide grep confirms no remaining `mapflow.entity` / `entity.provider` references in
  `mapflow/` or `tests/` (only mentions left are historical prose in `WAL.md` and
  `spec/007_architecture.md`, which are out of write-scope for this task and describe the
  cycle that is now fixed).
