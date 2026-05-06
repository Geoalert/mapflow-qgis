# WAL_8 implementation plan

## Scope
Establish a host-independent test runtime so existing pytest suite actually runs. Three tiers (functional / qgis / ui) with directory-based separation.

## Spec deltas (approved)
- `spec/004_stack.md`: drop "Test tools: pytest (local execution, no containers)" line. Add **Test runtime** subsection: pinned `qgis/qgis:release-3_28` Docker image; auto-tests cover Linux + LTR 3.28 only; macOS / Windows / other QGIS versions are smoke-tested manually.

## Steps
1. Reorganize `tests/`:
   - `tests/functional/`, `tests/qgis/`, `tests/ui/` — three taxonomy directories. **All three run inside the qgis/qgis:release-3_28 Docker container** with real PyQGIS; the directory split is *intent*, not *runtime*. Mocking PyQGIS portably is more brittle than running the real thing in a container.
   - `tests/functional/` — pure-logic / schema / string-op tests. Conftest does `qgis.testing.start_app()` plus the circular-import warmup. Hosts `test_layer_utils.py`.
   - `tests/qgis/` — tests that exercise real QGIS state (layers, projects, settings). Same conftest pattern. Hosts every other existing test.
   - `tests/ui/` — tests that need a Qt event loop / displayed widgets. Same bootstrap; runs under `xvfb-run`. Empty harness for now.
   - Top-level `tests/conftest.py` empty.
2. `Dockerfile.tests` at repo root: `FROM qgis/qgis:release-3_28`, `pip install pytest pytest-qt`, `WORKDIR /app`, `ENV QT_QPA_PLATFORM=offscreen`. No COPY — repo is bind-mounted at run time.
3. `Makefile` at repo root with phony targets:
   - `test-functional` → `python -m pytest tests/functional`
   - `test-qgis` → `docker build -f Dockerfile.tests -t mapflow-qgis-tests . && docker run --rm -v $(PWD):/app mapflow-qgis-tests pytest tests/qgis`
   - `test-ui` → docker run with `xvfb-run -a pytest tests/ui` (collects nothing for now)
   - `test` → all three
   - `docker-build` → just the image build
4. `.github/workflows/tests.yml`: three jobs on `ubuntu-latest`. Functional uses `python:3.10` directly. QGIS and UI use the Docker image (build it via `docker build` step, then run). UI job has `continue-on-error: true` until tests exist.
5. Docs:
   - `tests/README.md` — tier explanation, marker registry, how to add a test to each tier.
   - `README.md` — section "Automated tests" with the Linux + 3.28 LTR pin notice and pointer to `tests/README.md`.
6. Smoke-run locally:
   - `make test-functional` — must collect & pass `test_xyz_no_creds`.
   - `make test-qgis` — must collect & run all moved tests inside the container; pass/fail on real grounds, not import errors.

## Assumptions
- Stubbing `qgis.core` / `qgis.gui` / `PyQt5.*` / `osgeo` / `pyproj` via `sys.modules` is enough for `mapflow.functional.layer_utils` import-time; runtime calls in `generate_xyz_layer_definition` are pure string ops.
- `qgis/qgis:release-3_28` ships pytest-runnable PyQGIS at `/usr/bin/python3` and `pip` is available for `pytest-qt`.
- Repo layout permits `mapflow/__init__.py` to remain unchanged — functional tier never imports `mapflow` itself, only leaves like `mapflow.functional.layer_utils`.

## Insights
- All three tiers run inside `qgis/qgis:release-3_28`. Mocking PyQGIS portably (sys.modules MagicMock stubs) was tried first; it broke at the first class definition that subclasses a Qt type (`class ProcessingStatusDict(QObject):`) because Python's metaclass machinery uses `type(QObject)` and a MagicMock-as-base produces an unusable pseudo-class. Real PyQGIS in a container is simpler than maintaining a stub layer that emulates Qt's class semantics.
- `qgis/qgis:release-3_28` ships pip too old to recognize `--break-system-packages`; just call `pip install` directly.
- Naming a tier directory `qgis/` shadows the real `qgis` Python package once `__init__.py` puts the parent on `sys.path`. Solution: leave `tests/{functional,qgis,ui}/` without `__init__.py` and configure `pythonpath = .` in `pytest.ini` so the repo root is on the path explicitly.
- Pre-existing test failures uncovered (NOT FIXED — out of scope for runtime chore):
  - `tests/functional/test_layer_utils.py::test_xyz_no_creds` — passes args in the wrong positional order vs. `generate_xyz_layer_definition` signature; assertion text matches a different argument layout. Either the function signature changed without updating the test, or the test was authored incorrectly.
  - `tests/qgis/test_processings_pagination.py` — three failures: `ProcessingSortBy` enum values are uppercase in code (`"CREATED"`) but tests expect lowercase (`"created"`). Same drift pattern.
  These should be fixed in a follow-up MR (file the bugs against whoever owns the schema vs. test).
- Final acceptance: `make test-functional` and `make test-qgis` both *run*; failures are content bugs, not runtime errors. `make test-ui` collects zero tests as designed.
