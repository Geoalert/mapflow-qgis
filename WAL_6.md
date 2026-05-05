# WAL_6 implementation plan

## Scope
- Add spec for planned processing API.
- Add template schema models and API methods.
- Add focused tests for new schema and API path/body behavior.

## Steps
1. Add `spec/002_F_plan_processing_api.md`.
2. Update `spec/index.md` and `spec/002_api.md` to reference 002_F.
3. Extend `mapflow/schema/processing.py` with template dataclasses and request schemas.
4. Extend `mapflow/functional/api/processing_api.py` with template endpoint methods.
5. Add/update tests under `tests/`.
6. Run focused pytest on updated tests; then run full suite if feasible.

## Assumptions
- Remote `origin/dev` fetch issue remains unresolved; work proceeds from local branch state.
- Existing local modifications in `WAL.md` and `mapflow/schema/processing.py` are user-owned and preserved.
