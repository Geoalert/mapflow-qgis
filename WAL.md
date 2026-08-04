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
- Change the linter from current **ruff** to **flake8** and add **bandit** and **detect-secrets** to match the qgis.org checks

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

