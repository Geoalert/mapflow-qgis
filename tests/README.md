# Tests

The plugin's test suite runs inside the official `qgis/qgis:release-3_28`
Docker image so that no host setup beyond Docker is required. Driver:
the top-level `Makefile`. CI runs the same targets — see
`.github/workflows/tests.yml`.

## Coverage scope

Automated tests cover **Linux + QGIS 3.28 LTR only**. macOS, Windows,
and other QGIS versions are not exercised in CI — verify them by manual
smoke testing. The pin lives in the `FROM` line of `Dockerfile.tests`
and the spec in `spec/004_stack.md`.

## Tiers

Three directories, three intents. **All three run on real PyQGIS in the
container** — the split is taxonomy, not runtime separation.

| Tier | Directory | Intent | Runner |
|------|-----------|--------|--------|
| Functional | `tests/functional/` | Pure logic: schema parsing, string ops, dataclass behavior. Should not exercise real QGIS state. | `make test-functional` |
| QGIS | `tests/qgis/` | Tests that exercise real QGIS objects (layers, projects, settings, network). | `make test-qgis` |
| UI | `tests/ui/` | Tests that open widgets / drive a Qt event loop. Run under `xvfb-run`. Currently a harness only — no tests yet. | `make test-ui` |

Run everything with `make test`.

## Adding a test

1. Pick a tier by what the test *does*, not by what it *can* do:
   * does it just call a pure function and assert the result? → functional
   * does it construct a `QgsVectorLayer` or read `QgsSettings`? → qgis
   * does it `dlg.show()` or rely on an event loop? → ui
2. Drop the file in the matching directory. Pytest collection picks it
   up automatically.
3. Use the shared fixtures from the tier's `conftest.py`
   (`iface`, `http_mock` for the qgis tier).

## Local quickstart

```bash
make docker-build       # one-time, ~3 min on cold cache
make test-functional    # fast pure-logic tier
make test-qgis          # full QGIS-runtime tier
make test               # all three
```

The image is cached — subsequent test runs are just `docker run`.
