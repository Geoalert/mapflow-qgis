# 004 Stack

## Purpose
Capture technology choices and required versions.

## Content

Runtime: QGIS Desktop 3.28+ (Qt 5) and QGIS 4 (Qt 6), with the Python environment bundled with QGIS.
`metadata.txt` declares `qgisMinimumVersion=3.28`: the oldest version the tests run on is the oldest one
declared.

Language: Python 3, in the version bundled with QGIS 3.28 or newer.

UI framework: Qt through `qgis.PyQt`, so one code base runs on PyQt5 and PyQt6. **The UI is built in
code** (`mapflow_next/ui/*.py`): there are no Qt Designer `.ui` files and no `uic.loadUiType()`. The few
QGIS 3 / QGIS 4 differences are in `qgis_bridge/compat.py`; the rules that keep the rest portable are in
`README.md` § QGIS 3 and QGIS 4.

Networking: QgsNetworkAccessManager (Qt-based, QGIS-integrated — enables proxy support, auth manager integration). No third-party HTTP clients (no requests/httpx/aiohttp).

GIS libraries:
- QGIS Python API (qgis.core, qgis.gui) — layers, geometry, settings, project management
- GDAL/OGR (osgeo) — raster I/O, coordinate transforms

Build/deploy: **releases are made by hand**. `make zip` builds the archive from `mapflow_next/` alone,
and a maintainer uploads it to the QGIS Plugin Repository. No workflow publishes a release:
`release.yml` in the repository root is not under `.github/workflows/` and never runs, and
`.qgis-plugin-ci` is kept for the `qgis-plugin-ci` tool, which nothing runs today.

Test tools: pytest (no pytest-qt). See **Test runtime** below. Static-analysis tools: flake8, bandit,
detect-secrets — see **Static analysis** below.

CI/CD: GitHub Actions. `.github/workflows/tests.yml` runs `make test-qgis3`, `make test-qgis4` and
`make lint` on pushes to `dev` and `master` and on every pull request; `release-review.yml` reviews the plugin on each pull request
into `master`.

External dependencies: Mapflow REST API backend (required for all functionality beyond UI).

## Test runtime

**The tests run inside the official `qgis/qgis` Docker images**, with real PyQGIS, twice: on
`qgis/qgis:release-3_28` (QGIS 3, Qt 5) and on `qgis/qgis:4.2` (QGIS 4, Qt 6), both built from one
`Dockerfile.tests`. Mocking the QGIS / Qt / GDAL surface portably is more brittle than running the real
runtime in a container.

- `tests/test_core.py` — pure Python (`mapflow_next/core/`) plus source checks: the Qt 5/6 rules of the
  README, and handlers that Qt's `checked` argument would break. Every rule the README lists has a check
  here or in `tools/qt6_check.py`.
- `tests/test_e2e.py` → `tests/e2e_flow.py` — the whole flow in a real offscreen QGIS against a mock
  Mapflow API and sign-in server (`tests/mock_server.py`), from sign-in to results on the map. It is the
  only test of the controller and the services, so it must not pass on a failure it cannot see:
  - **an unexpected Critical message fails the flow.** The plugin's guard turns an exception into a
    Critical line in the message bar and the log; the test's `iface` records them, and any the test did
    not ask for is a failure.
  - **a missing `qgis.core` is a failure in the test images, not a skip.** Skipping is right on a
    developer's host without QGIS and wrong in an image whose whole purpose is to have it.
- `tests/qt6_ui.py` with `tests/qt6_shim/` — the pages, sign-in and HTTP client on PyQt6 without QGIS 4
  (`make test-qt6`). It is the one test that needs no QGIS image: it runs on any Python with PyQt6,
  so that the Qt 6 pages can be checked where QGIS 4 isn't at hand. CI runs it in a job of its own.
- `tools/qt6_check.py` — Qt enum names and calls that only Qt 5 accepts (part of `make test-qgis4`).

Pinned images: **`qgis/qgis:release-3_28`** and **`qgis/qgis:4.2`**. The tags float within a release, so
two runs of the same commit can meet different patch versions of QGIS. Open: pin the images by digest (or
to an exact patch tag), so the end-to-end tests name the QGIS they ran on.

Coverage scope: automated tests cover **Linux, QGIS 3.28 and QGIS 4.2**. macOS, Windows, and other QGIS
versions are exercised by manual testing — there is no CI matrix for them.

Entry points: `make test` (both QGIS versions; the gate before review) / `make test-core` /
`make test-qgis3` / `make test-qgis4` / `make test-qt6` / `make lint` / `make screens`. CI runs
`test-qgis3`, `test-qgis4`, `test-qt6` and `lint`.

## Static analysis

Three checks, chosen to mirror what plugins.qgis.org runs on plugin submission, so that a
green local run predicts a clean scan there:

- **flake8** — style and lint at `--max-line-length=120`, over `mapflow_next/`, `tests/` and
  `tools/` (style debt in tests is still debt).
- **bandit** — security scan over `mapflow_next/` only: it is the code that ships, and B101
  (assert_used) would otherwise fire on every pytest assertion. **No severity floor** (no
  `-ll`): qgis.org applies its own severity per rule — B110 `try_except_pass` is critical
  there and LOW in bandit — so a floor would hide exactly what qgis.org blocks on.
- **detect-secrets** — credential scan of every file in `mapflow_next/`, `tests/` and `tools/`,
  run **without `--baseline`**: with it, `detect-secrets-hook` calls `git diff` to check that
  the baseline is staged, which fails wherever the container cannot read the repository (the
  CI runner). A finding is allowlisted inline (`# pragma: allowlist secret`).
  `.secrets.baseline` stays committed because the qgis.org scanner looks for it.

At qgis.org, bandit and detect-secrets are **blocking** validators; flake8 is advisory.
Locally all three block, because a check that cannot fail the build does not hold a line.

All three run **inside the same `qgis/qgis:release-3_28` image as the tests**, at versions
pinned in `Dockerfile.tests`. Pinning is deliberate: an unpinned linter silently changes its
verdict when upstream adds a rule, turning an unrelated MR red. Running them in the image
rather than a host venv means every developer and CI get identical results instead of
whatever each machine happened to pip-install.

There is no debt ledger: `mapflow_next/` passes flake8's default rules, and `.flake8` adds no
`extend-ignore` (its one exemption is `per-file-ignores = __init__.py:F401`). The qgis.org scan
does not read `.flake8` (it runs against the packaged `mapflow_next/` directory), so anything
ignored there would still be reported at submission.

## Dependency policy

**Only libraries bundled with the QGIS Python environment are allowed *in the shipped plugin*.** Adding third-party packages that are not part of the standard QGIS/Qt/GDAL distribution is strictly forbidden — the plugin must install and run without `pip install` on any QGIS 3.28+ installation.

This governs **runtime plugin dependencies only**. Development and test tooling (pytest, flake8, bandit, detect-secrets) is installed in `Dockerfile.tests`, runs only in the test container, and never ships: `make zip` packages the `mapflow_next/` directory alone. It is therefore exempt from this policy.

Prefer native QGIS/Qt tools over external alternatives:
- Networking: use `QgsNetworkAccessManager`, not requests/httpx/aiohttp
- Geometry: use `QgsGeometry`/`QgsCoordinateTransform`, not shapely
- File dialogs: use `QFileDialog`, not tkinter
- JSON: use stdlib `json`, not orjson/ujson
- HTTP auth: use `QgsAuthManager`, not custom token stores
- Settings: use `QgsSettings`, not configparser/dotenv
