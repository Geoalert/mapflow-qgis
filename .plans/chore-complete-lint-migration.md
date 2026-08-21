# chore/complete-lint-migration — handover

WAL 3.7.0 §1, completion of the linter-migration bullet. Gitignored scratchpad.

## Approved at the Confirmation Gate

1. **Scoping** — complete the migration + gate CI, and close W191 + F403/F405 outright.
   Defer WAL bullets 1 (broad handlers) and 2 (assert → test), and the residual whitespace.
2. **pyright** — accept the coverage loss, record it in the WAL motivation. Nothing in the
   new toolchain replaces `reportPossiblyUnbound`; revisit after the refactor.
3. **Write scope** — the orchestrator makes the five out-of-scope edits (`.flake8`,
   `pyproject.toml`, `pyrightconfig.json`, `README.md`, `.github/workflows/tests.yml`)
   plus `AGENTS.md` and `spec/**`. The implementer stays inside `mapflow/**` + `tests/**`.
   Subagent write boundaries are left intact rather than exception-carved.
4. **Spec extras** — both included: the `.flake8` debt-ledger policy paragraph and the
   `spec/index.md` one-liner.

## Phase A — baseline (done)

`agent-make lint` on a clean branch checkout, 2026-08-05. Total **≈1,425**.

```
539 W191    157 W293    109 W291     93 E501     87 E261     73 F401
 70 E302     60 E251     50 E128     38 E127     29 E124     19 E231
 16 E722     13 W292     13 E303      9 E203      6 W391      5 E117
  4 E306      4 E301      4 E265      4 E211      4 E122      3 E502
  3 E225      2 E222      2 E201      2 E131      1 F405      1 F403
  1 E275      1 E271      1 E262      1 E202      1 E111
```

bandit: exit 0. detect-secrets: exit 0. Both blocking checks already green — this step is
about flake8 and about making the gate real, not about fixing a security finding.

Bandit also emits 7 `Test in comment: … is not a test name or id, ignoring` warnings. Their
disappearance is an acceptance criterion (C.3).

## Phase B — implementer, `tests/**`

- **B.1** `tests/functional/test_layer_utils.py:1` — replace the star import with
  `from mapflow.functional.layer_utils import generate_xyz_layer_definition`
  (the only symbol used). Closes F403 + F405.
- **B.2** `tests/qgis/test_template_start_processing.py` — tabs → 4 spaces. Preconditions
  verified in planning: 730 lines, 539 tab-indented, **0 space-indented**, max nesting 3
  tabs. Closes W191 (38% of all findings). Up to 6 lines currently ≥112 chars may cross 120
  after expansion — re-wrap exactly those.
  Gate: `git diff -w` shows only the re-wrapped lines; `agent-make test-qgis` green.

## Phase C — implementer, `mapflow/**`

- **C.3** Canonicalise 7 `# nosec` comments. Current `# nosec - reason` fails bandit's
  test-ID parse (`-` matches neither `B\d+` nor `[a-z_]+`), producing a warning per site per
  run. Correct form `# nosec B105 - reason`. All 7 were re-reviewed in planning and are
  genuine false positives — **keep every suppression, change syntax only**.

  | file | line | id |
  |---|---|---|
  | `mapflow/config.py` | 105 | B105 |
  | `mapflow/entity/provider/provider.py` | 35 | B107 |
  | `mapflow/mapflow.py` | 4055 | B105 |
  | `mapflow/dialogs/login_dialog.py` | 12 | B107 |
  | `mapflow/dialogs/login_dialog.py` | 28 | B107 |
  | `mapflow/dialogs/provider_dialog.py` | 56 | B105 |
  | `mapflow/functional/layer_utils.py` | 52 | B107 |

  If an ID is uncertain, use a bare `# nosec` on the code line with prose on the *preceding*
  line. Never leave prose directly after `# nosec` with no ID. No behavioral effect —
  `bandit -ll` filters LOW, so B105/B106/B107 cannot move the exit code.

## Phases D–G — orchestrator

`.flake8` (per-file-ignores first, then the measured ledger), `pyproject.toml` ruff removal,
`pyrightconfig.json` deletion, CI lint job, `README.md`, `spec/004_stack.md` + `spec/index.md`,
`AGENTS.md` STATIC ANALYSIS, WAL.

## Risks

- **R1 (high impact)** — if flake8 in the container does not discover `/app/.flake8`, the only
  fixes require editing the **Makefile**, a watched file, which blocks `agent-make` repo-wide.
  **Mitigation:** first config action is `.flake8` with *only* `per-file-ignores`, then
  `agent-make lint` to confirm the F401 count drops from 73. If it does not drop — **STOP and
  escalate. Do not edit the Makefile.**
- **R3** — `tests/functional/conftest.py:26-32` documents a circular-import chain that only
  resolves on retry via partial-module caching. An import flake8 calls unused may be
  load-bearing. **No F401 outside `__init__.py` is fixed in this step**; residual goes to the
  ledger.
- **R4** — pyright removal loses possibly-unbound analysis. Accepted; must appear in the WAL
  motivation.
- **R5** — `extend-ignore` is global, so a new file can introduce fresh W291/E501 unnoticed.
  Accepted while the ledger is expected to shrink to empty within the release.

## Carried forward (not this step)

- **C2** — WAL says step 1.2's key-collision test goes in `tests/qgis/`; spec 004 and
  `tests/README.md` both place pure-logic tests in `tests/functional/`. Spec wins per AGENTS.md
  SPECIFICATION GUIDELINES rule 2. Correct the WAL when 1.2 starts.
- **C3 — verified** — `tests/test_imagery_search_multi.py` holds **23 test functions** at the
  tests root, outside all three tiers. `make test` uses explicit per-tier paths, so these have
  **never run in CI**. Needs its own WAL item.
- Whitespace normalisation (~450 residual) — deferred to immediately before the refactor branch
  cut, after `origin/feature/track-uploaded-image-status` lands. The residual concentrates in
  `mapflow.py`, `provider_service.py`, `data_catalog.py`, `data_catalog_view.py`,
  `main_dialog.py` — exactly the files the refactoring rewrites.

## Final Review Summary

Review was performed inline by the orchestrator, not the reviewer subagent — that dispatch was
declined by the user, so it was not retried verbatim. **0 CRITICAL, 0 MAJOR.** No push-back rounds.

**Deviations from plan, with reasons:**
- The `# nosec` fix in the plan (`# nosec B105 - reason`) **would not have worked.** bandit's
  `NOSEC_COMMENT` regex captures `[^#]+` after `nosec`, so trailing prose is still parsed as test
  IDs and the warnings persist. Corrected to `# nosec B105  # reason` — a second `#` terminates the
  capture. Verified empirically: 7 warnings → 0.
- The plan predicted ~6 lines would cross 120 chars from tab expansion and need re-wrapping.
  Actual: **0 new E501.** The 4 over-length lines (666, 692, 693, 720) were already E501 in the
  baseline. Nothing re-wrapped.
- GNU `expand -i` is unavailable on macOS (BSD expand has no `-i`); used
  `perl -i -pe 's{^(\t+)}{" " x (4 * length($1))}e'`, anchored to line start.

**Finding raised and accepted (MINOR):** `git diff -w` is empty, but it structurally cannot see
inside string literals. Six docstring-internal continuation lines (220, 248–250, 326–327) had a
leading tab become 4 spaces, changing those docstring values. Harmless — nothing asserts on
docstring text, 403 qgis tests pass, and the indentation is now consistent — but the "no semantic
change" claim does not extend to them, and the PR says so.

**Finding raised, deferred (MINOR):** `mapflow/mapflow.py:4054` is a bare `except:` visible in the
diff context. One of the 16 E722s, ledgered for bullet 1. Correctly not fixed opportunistically.

**NIT:** all 7 `nosec` suppressions are inert under `bandit -ll` (B105/B107 are LOW severity, so
they are filtered before the suppression matters). They are documentation, not functional gates.

**R1 result — the plan's highest-impact risk — did not materialise.** flake8 discovered
`/app/.flake8`; F401 dropped 73 → 1. No Makefile edit, `agent-make` stays unblocked.

**Process note:** the commit message for `920ba78` lost three backtick spans to shell command
substitution. `agent-git` blocks amend and force-push, so the corrected text went into the PR
description via `--body-file` instead. Prefer `--body-file` over inline `-m` for any message
containing backticks.
