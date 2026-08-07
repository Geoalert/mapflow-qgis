# 004 Stack

## Purpose
Capture technology choices and required versions.

## Content

Runtime: QGIS Desktop 3.20+ (Python environment bundled with QGIS).

Language: Python 3 (minimum 3.6 for compatibility with older QGIS builds; datetime parsing workarounds present).

UI framework: PyQt5 (as bundled with QGIS 3.x). Dialogs designed in Qt Designer (`.ui` files), loaded at runtime via `uic.loadUiType()`.

Networking: QgsNetworkAccessManager (Qt-based, QGIS-integrated — enables proxy support, auth manager integration). No third-party HTTP clients (no requests/httpx/aiohttp).

GIS libraries:
- QGIS Python API (qgis.core, qgis.gui) — layers, geometry, settings, project management
- GDAL/OGR (osgeo) — raster I/O, coordinate transforms
- pyproj — CRS transformations

Build/deploy: `qgis-plugin-ci` for packaging and release. Plugin published to QGIS Plugin Repository.

Test tools: pytest, pytest-qt. Automated tests run in three tiers (functional / qgis / ui) — see **Test runtime** below. Static-analysis tools: flake8, bandit, detect-secrets — see **Static analysis** below.

CI/CD: GitHub Actions (implied by `.github/` structure).

External dependencies: Mapflow REST API backend (required for all functionality beyond UI).

## Test runtime

Tests are organized by intent, one directory per tier. **All three tiers run inside the official `qgis/qgis:release-3_28` Docker container** with real PyQGIS — the directory split is taxonomy, not runtime separation. Mocking the QGIS / PyQt5 / GDAL surface portably is more brittle than running the real runtime in a container.

- `tests/functional/` — pure-logic tests: schema parsing, string ops, dataclass behavior, anything that does not exercise real QGIS state. Bootstrap via `qgis.testing.start_app()`.
- `tests/qgis/` — tests that touch real QGIS objects (layers, projects, settings, network). Same bootstrap.
- `tests/ui/` — tests that open widgets / drive a Qt event loop. Same bootstrap, run under `xvfb-run`. Currently a harness only.

Pinned image: **`qgis/qgis:release-3_28`** (LTR through 2026, satisfies the QGIS 3.20+ minimum).

Coverage scope: automated tests cover **Linux + QGIS 3.28 LTR only**. macOS, Windows, and other QGIS versions are exercised by manual smoke testing — there is no CI matrix for them. This is a deliberate trade-off: the official QGIS Docker image is Linux-only, and a cross-OS conda-forge matrix is deferred until the Linux pipeline is stable.

Entry points: `make test-functional` / `make test-qgis` / `make test-ui` / `make test` / `make lint`. CI runs the same targets.

## Static analysis

Three checks, chosen to mirror what plugins.qgis.org runs on plugin submission, so that a
green local run predicts a clean scan there:

- **flake8** — style and lint at `--max-line-length=120`, over `mapflow/` and `tests/`
  (style debt in tests is still debt).
- **bandit** — security scan at medium-or-higher severity (`-ll`), over `mapflow/` only:
  it is the code that ships, and B101 (assert_used) would otherwise fire on every pytest
  assertion.
- **detect-secrets** — credential scan against the committed `.secrets.baseline`.

At qgis.org, bandit and detect-secrets are **blocking** validators; flake8 is advisory.
Locally all three block, because a check that cannot fail the build does not hold a line.

All three run **inside the same `qgis/qgis:release-3_28` image as the tests**, at versions
pinned in `Dockerfile.tests`. Pinning is deliberate: an unpinned linter silently changes its
verdict when upstream adds a rule, turning an unrelated MR red. Running them in the image
rather than a host venv means every developer and CI get identical results instead of
whatever each machine happened to pip-install.

Suppressions are explicit and temporary. `.flake8` enumerates the rule classes still
outstanding from the 3.6.0 scan, each tied to the WAL step that removes it; the list only
shrinks. It is not a permanent exemption — the qgis.org scan does not read `.flake8`
(it runs against the packaged `mapflow/` directory, see `.qgis-plugin-ci`), so anything
listed there is debt still owed at submission time.

## Dependency policy

**Only libraries bundled with the QGIS Python environment are allowed *in the shipped plugin*.** Adding third-party packages that are not part of the standard QGIS/PyQt5/GDAL distribution is strictly forbidden — the plugin must install and run without `pip install` on any QGIS 3.20+ installation.

This governs **runtime plugin dependencies only**. Development and test tooling (pytest, pytest-qt, flake8, bandit, detect-secrets) is installed in `Dockerfile.tests`, runs only in the test container, and never ships: `.qgis-plugin-ci` packages the `mapflow/` directory alone. It is therefore exempt from this policy.

Prefer native QGIS/Qt tools over external alternatives:
- Networking: use `QgsNetworkAccessManager`, not requests/httpx/aiohttp
- Geometry: use `QgsGeometry`/`QgsCoordinateTransform`, not shapely
- File dialogs: use `QFileDialog`, not tkinter
- JSON: use stdlib `json`, not orjson/ujson
- HTTP auth: use `QgsAuthManager`, not custom token stores
- Settings: use `QgsSettings`, not configparser/dotenv
