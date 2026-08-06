# Planned and in-flight work

Forward-facing only: `[ ]` planned, `[ready-for-review]` in flight. Entries are removed when they
merge — the WHY lives in the commit message and, for durable decisions, in `spec/`.
See AGENTS.md § WHERE THE WHY GOES.

# V 3.7.0 LTR

We are planning a long-term release, effectively the LAST, stable release for QGIS3, the next version will be for QGIS4,
and this version will get only API compatibility changes and bug fixes.

So, the main idea behind the release is HARDENINIG so that this support will be easier, AND transfer to QGIS4 will go smoother.
current plugin code needs a major refactoring.

However, as we don't want to release an "empty" version (without any user-facing features), we will add some improvements.

## 1. Refactoring

[ ] Bring `tests/test_imagery_search_multi.py` into a tier
Discovered while wiring up the lint gate. The file sits at the tests root with 23 test
functions, outside all three tiers. `make test` runs `pytest tests/functional`, `pytest
tests/qgis`, `pytest tests/ui` with explicit paths, which override `testpaths = tests` in
pytest.ini — so these 23 tests have **never run in CI**, and the spec's three-tier coverage
claim is wrong by that much. Pick the tier by runtime need, not by scope (spec/004_stack.md):
the file is heavily mocked but imports `Config`, so confirm by running rather than assuming.
Sizing is unknown until it runs — treat the failures as the real work, not the move.

[ ] Narrow the broad exception handlers
The 3.6.0 security scan flagged `try/except Exception` blocks that only log. Narrow them to the
exceptions actually expected, so unrelated errors surface instead of being swallowed.
Scope: 16 bare `except:` (provider_service 5, geometry 4, mapflow 2, http 2, layer_utils 2,
catalog 1) and 38 `except Exception` (processing_service 14, mapflow 11, 9 files with 1–2).
Acceptance: `E722` comes out of the `.flake8` ledger, and bandit reports no `B110`.
Sequenced after the untiered tests: those 23 tests exercise provider_service and
processing_service, the two heaviest files here, so they are the safety net for this change.

[ ] Normalise the residual whitespace findings
Clears most of the `.flake8` ledger (~450: W291/W292/W293/W391, E501, E1xx/E2xx/E3xx).
**Ordering constraint:** must come *after* `feature/track-uploaded-image-status` is rebased and
landed (§3), and immediately *before* the refactor branch cut. A whole-tree whitespace diff makes
that rebase materially worse, and the findings concentrate in `mapflow.py` and the service layer,
which the refactoring rewrites — normalising earlier means doing the work twice.

[ ] Plan the refactoring
Address known problems, be open to push back if the proposals are wrong; 
assess the code for good/bad practices and evaluate what to improve (maximum impact, minimum effort)
The ultimate goals are:
- consistency of the codebase (a developer or AI agent who knows one part of functionality should easily find the corresponding parts in others)
- industry standards (a new developer should not be surprised or turned off by the code structure or smells)
- cheap to maintain in case of API changes
- ready to transfer to QGIS4 (Qt6)

Known problems:
- Current code has obviously problematic god-object (in mapflow.py) which tightly couples a lot of functionality. 
- Code/folder structure is uneven: 
  - there are orphans like `./mapflow/requests`
  - `./mapflow/entity` and `./mapflow/schema` don't have clear responsibilities
  - same for `constants.py` and `config.py` 
  - ???
I would suggest the following:
- minimize `mapflow.py` responsibilities
- create a classic folder structure "api/controller/service/view", practically moving them out of `functional` to the root 
- create services and other instances for the other parts of functionality.
- move templates to a separate template_service (controller probably stays the same, but let's decide later)
- refactor dialogs (ui + py dialog files). Some of them are created manually in the Qt designer,
and some are heavily python-coded or generated, and they are inconsistent in how can you change them. We need to select a consistent way.
- review the settings and what do we store there

[ ] Improve test coverage (behavioral/e2e)
- Document the current behavior and cover it with the tests BEFORE the refactoring
- Factor the refactoring structure plan in to match the proposed tests to the final functionality rather than the current functions and code

[ ] Implement the refactoring
- Should follow the plan proposed before
- Should not break the tests implemented before (behavioral/e2e), allowed to rewrite/add unit tests

## 2. Add new zoom-selector feature
[ ]
- Use 002_E_zoom_selector_api.md
- Add a small button near zoom selector comboBox to call zoom-selector API, active when selected source is a Mapflow data provider.
- On button press, call API and select zoom automatically depending on response.
- On error, show a reasonable user-facing message.

## 3. Add myImagery upload status tracking
[ ] 
Mainly already implemented at branch `feature/track-uploaded-image-status`
Need to rebase on current state, or directly move the code if it's too complicated. 
The most important part is described in the `spec` change on the branch.

## 4. Update styles for both loaded geojson/gpkg layers and vector tile layers
[ ] 
The styles will be provided by the designer team, we need only to put it into the code

## 5. Add "Search by image ID" functionality
[ ] 
See API in `../whitemaps-backend`
```
- GET /meta/{image_id} request
- GET /meta/{image_id}?provider_name={}
```

## 6. Add "move image to other mosaic" functionality
[ ]
See API in `../data-catalog/spec/002_api.md`
```
POST /rest/rasters/image/{image_id}/move/precheck
POST /rest/rasters/image/{image_id}/move
```

