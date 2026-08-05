# Journal for active implementation planning

# V 3.7.0 LTR

We are planning a long-term release, effectively the LAST, stable release for QGIS3, the next version will be for QGIS4,
and this version will get only API compatibility changes and bug fixes.

So, the main idea behind the release is HARDENINIG so that this support will be easier, AND transfer to QGIS4 will go smoother.
current plugin code needs a major refactoring.

However, as we don't want to release an "empty" version (without any user-facing features), we will add some improvements.

## 1. Refactoring

[ ] Address the security check problems
- The 3.6.0 security scan flagged several broad `try/except Exception` blocks that only logged
  (previously swallowed silently). Narrow them to the specific exceptions actually expected, so
  unrelated errors surface instead of being logged and ignored.
- Move the `assert` key-collision checks in errors/error_message_list.py `update()` to a unit test
  (Bandit B101). Decided: the merge only combines the statically-defined ProcessingErrors/DataErrors/
  ApiErrors dicts at import, so the invariant is a source-code property — a test catches it in CI,
  runs even under `python -O`, and costs nothing in production. Delete the two asserts, add
  tests/qgis/test_error_message_list.py asserting no key collisions (error_descriptions and
  message_descriptions).
- [ready-for-review] Change the linter from current **ruff** to **flake8** and add **bandit** and
  **detect-secrets** to match the qgis.org checks.
  Verified against the qgis.org scanner rather than assumed: it runs exactly these three, and
  **pyright is not among them** — so pyright is dropped. That is a real coverage loss, not just
  cleanup: `reportPossiblyUnbound` (use-before-assignment across branches) has no replacement in
  the new toolchain — flake8's F821 catches undefined names only — and this codebase has broad
  `except Exception` handlers that would mask exactly that class of bug. Accepted for qgis.org
  parity; revisit when the refactor lands type annotations.
  The old ruff config (`select = ["F","B"]`) was *narrower* than qgis.org's default rule set, which
  is why the 3.6.0 scan surfaced E-codes local lint could never report. Matching them raised the
  count to ~1425, of which ~811 remain in a documented `.flake8` ledger.
  CI ran **no lint at all** before this. That is the reason the gate went in first, ahead of the
  cleanup bullets: without a ratchet, every finding-reduction MR is a snapshot the next MR silently
  undoes — which is how 1425 findings accumulated. Ledger entries name the step that removes them
  and the list only shrinks.
  Closed outright rather than deferred: W191 (539 findings, 38% of the total, all in one test file
  with uniform tab indentation — `git diff -w` empty proves the conversion was semantics-free) and
  F403/F405 (one star-import line). Whitespace normalisation of the ~450 residual is deliberately
  **deferred to immediately before the refactor branch cut**: it concentrates in `mapflow.py` and
  the service layer, which the refactoring rewrites, so doing it now means doing it twice, and it
  would make the in-flight `feature/track-uploaded-image-status` rebase materially worse.
  F401 outside `__init__.py` is ledgered, not fixed: `tests/functional/conftest.py` documents a
  circular-import chain that only resolves via partial-module caching, so a nominally unused import
  may be load-bearing.
  `# nosec` comments were emitting a bandit warning per site per run. The fix is not an ID prefix —
  bandit captures everything after `nosec` up to the next `#`, so prose keeps getting parsed as test
  IDs. Correct form is `# nosec B105  # reason`, with a second `#` terminating the capture.

[ ] Bring `tests/test_imagery_search_multi.py` into a tier
Discovered while wiring up the lint gate. The file sits at the tests root with 23 test
functions, outside all three tiers. `make test` runs `pytest tests/functional`, `pytest
tests/qgis`, `pytest tests/ui` with explicit paths, which override `testpaths = tests` in
pytest.ini — so these 23 tests have **never run in CI**, and the spec's three-tier coverage
claim is wrong by that much. Decide the correct tier (likely `qgis/`, it exercises search
against real objects), move it, and fix whatever fails once it actually runs. Sizing is
unknown until it runs — treat the failures as the real work, not the move.

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

