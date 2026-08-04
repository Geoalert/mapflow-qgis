# SPECIFICATION GUIDELINES
1. NEVER change specifications unless explicitly and separately asked to work on them. If some specification produces suboptimal code, raise it in the WAL motivation and surface to the user during the Confirmation Gate or Review Loop.
2. Tests MUST directly follow SPECIFICATION found in /spec folder. If some test is impossible to write according to specification, STOP ITERATION and ask user.
3. Application code SHOULD follow specifications unless impossible; in this case STOP ITERATION and ask user before deviating.

# BRANCH MODEL — READ BEFORE ANY GIT OR MAKE COMMAND

This repo uses **git flow with `dev` as the integration branch**. Feature branches are cut from `dev` and their MRs target `dev`. `master` is the release branch.

**`master` is also the branch `agent-make` verifies watched files against.** These two facts collide, and the collision is load-bearing:

- Editing a watched file (`Makefile`, `Dockerfile.tests`) and merging it to `dev` does **not** unblock `agent-make`. Every invocation keeps failing with *"local files differ from origin/master"* until that change also reaches `master`.
- So a step that touches a watched file needs its own MR merged to `master` **before** any subsequent step can run tests. Plan such steps first in a release, or land them as a standalone MR.
- Never "fix" this by reverting the watched file to match `master`. That silently discards the change. STOP and surface to the user — merging to `master` is a human action.

Everywhere below, `dev` is the branch you branch from, pull, and target. `master` appears only as the `agent-make` reference point.

# GIT COMMAND POLICY FOR AGENTS

Assume the agent-security-toolkit is installed and the repo is onboarded (`agent-repo-init` already run). Use `agent-git` for every git operation. Raw `git` is not recommended and almost always requires manual approval; reach for it only when the task genuinely needs an operation `agent-git` does not expose, and state the justification in the command text.

## What `agent-git` enforces (do not try to bypass)
- Push only from branches prefixed `feature/`, `fix/`, `chore/`, `refactor/`, `test/`, `agent/`.
- Never pushes to `main`, `master`, `develop`, `release/*`, `hotfix/*`.
- Blocks `--force`, `-f`, `--mirror`, `--all`, `--prune`, `--delete`, `-d`, `--tags`, `--follow-tags`.
- Blocks `git rm -r`, `git reset --hard`, `git config` writes, and reads of `agent-*.*` / `core.hooksPath` (so don't probe).
- `fetch`/`pull` accept only `origin`.
- `git clone`, `git init`, `git remote …`, `git submodule …`, `git worktree …` are not exposed — escalate to the user if you need them.
- Commits are signed with the bot identity from `/etc/agent-security-toolkit.conf`. **Do NOT add `Co-Authored-By:` trailers — the bot account IS the agent attribution.**

## What `agent-git push` does for you (do not duplicate)
On every push, `agent-git` automatically adds:
- `--set-upstream` (first push wires up tracking)
- `-o merge_request.create`
- `-o merge_request.draft`
- `-o merge_request.target=<policy>` — the target comes from per-repo `agent-git.mr-target`; **agent-supplied `merge_request.target=` is rejected**.

So the entire MR-open flow is one command:
```
agent-git push
```
By default GitLab uses the **last commit subject** as the MR title. Override at first open by passing the title explicitly:
```
agent-git push -o merge_request.title="add review loop and language packs"
```

## Modifying the MR header on follow-up pushes
GitLab updates the existing Draft MR on every subsequent push from the same branch. To change the title or body without touching the UI:
```
agent-git push \
  -o merge_request.title="new title" \
  -o merge_request.description="updated summary…"
```
The only push options `agent-git` accepts: `merge_request.create`, `merge_request.draft`, `merge_request.title=…`, `merge_request.description=…`. Anything else (including `merge_request.target=…`) is rejected by policy.

## When `agent-git` blocks you
Read the `agent-git BLOCKED:` line — it is the spec. **Do not work around it.** Stop and surface to the user with the exact message. Common cases:
- Branch name doesn't match the allowed prefix → rename the branch.
- MR target equals current branch → user must run `agent-repo-init --mr-target <branch>`.
- Push to protected branch → switch to a feature branch first.
- Watched-file mismatch from `agent-make` → see make policy below.

# MAKE COMMAND POLICY FOR AGENTS

Use `agent-make` for every build / test / lint invocation in this repo. Raw `make` and direct `docker` / `docker-compose` calls usually require manual approval and bypass the watched-file verification.

## Usage
- `agent-make <target> [<target>…]` — root Makefile (`agent-make test`, `agent-make lint test`).
- `agent-make --in <subdir> <target>` — monorepo sub-Makefile (the sub-Makefile must be on the watched-files list).
- Targets must be plain identifiers (`[A-Za-z0-9._/-]+`). No flags, no `VAR=val` overrides, no shell metacharacters. If a flag-style invocation is needed, define a dedicated Makefile target instead — but note that adding a target edits a watched file, which blocks `agent-make` until it reaches `master` (see BRANCH MODEL).

## What `agent-make` enforces
- Fetches `origin/master` and verifies every watched file (here: `Makefile`, `Dockerfile.tests`) byte-for-byte against the remote before running. **Any local modification to a watched file blocks every `agent-make` invocation** — including test runs for unrelated work on the same branch.
- Optional per-repo target allowlist (`agent-make.allowed-targets`) — unlisted targets are blocked.

## When `agent-make` blocks you
- *"local files differ from origin/master"* — a watched file was edited locally. **STOP and surface to user.** The fix is human-only: the change must be merged to `master`, not just `dev` (see BRANCH MODEL). Do not revert other agent work to satisfy this check.
- *"Target 'X' is not in agent-make.allowed-targets"* — STOP and ask the user to extend the allowlist via `agent-repo-init --allowed-targets …`.
- *"Sub-Makefile '<path>' is not in agent-make.files"* — STOP and ask the user to add it via `agent-repo-init --files …`.

# PROJECT STRUCTURE AND ADDRESSING
This is a **QGIS 3 plugin** (Python, Qt/PyQGIS). It ships as a zip to the QGIS plugin repository — there is no server, no database, and no deployment image.

- `Dockerfile.tests`: the QGIS test image (`qgis/qgis:release-3_28`). Test-only; nothing is deployed from it.
- `Makefile`: test tiers + lint. **No docker-compose in this repo** — targets use a plain `docker run` with the repo bind-mounted at `/app`.
- /spec: contains specifications, ordered by hierarchy: the very foundation in 001, then go the most important architecture details (api, db, stack), all further decisions and rationale are documented in subsequent files. Enter via `/spec/index.md`.
- /mapflow: plugin source code
  - /mapflow/dialogs: Qt dialog classes; `.ui` files live in `/mapflow/dialogs/static/ui/`
  - /mapflow/functional: business logic, split `api/` (Mapflow HTTP clients) / `controller/` / `service/` / `view/`
  - /mapflow/entity: domain models (processing, provider, billing, etc.)
  - /mapflow/schema: data schemas
  - /mapflow/errors: error types and user-facing messages
- /tests: pytest suites, split by **runtime tier**, not by unit/integration — `functional/` (pure logic, no QGIS), `qgis/` (needs the QGIS runtime), `ui/` (Qt widgets, runs under xvfb)
- WAL.md - persistent journal of completed steps and the WHY of each decision. Distilled, committed, survives across branches.
- .plans/ - **gitignored** per-branch agent handover scratchpad. One file per feature branch: `.plans/<sanitized-branch-name>.md` (slashes in the branch name become dashes, e.g. `feature/foo-bar` → `.plans/feature-foo-bar.md`). Holds the detailed step plan, stabilization discoveries, push-back rounds, and Final Review Summary. Never reaches the remote; the distilled motivation lands in WAL.md at merge.

# SESSION PROTOCOL FOR FEATURE IMPLEMENTATION
Execute it every time a session is initiated.

0. Ensure local dev is up to date: `agent-git checkout dev && agent-git pull --ff-only`.
    - If there are unstaged/uncommitted changes, STOP ITERATION and ask user how to proceed.
1. Read WAL.md to update the state of the previous steps to revisit decision making (`instructions/planning.md`)
2. planning.md: Find next step to work on in WAL.md (`instructions/planning.md`)
3. planning.md: Revisit `/spec` folder for the documentation related to the task. Use `/spec/index.md` to find related documents, then dive into them (`instructions/planning.md`).
    - If contradictions are found, STOP ITERATION, ask user to clarify spec and task, and highlight inconsistent documentation.
4. planning.md: Specification coverage gate (`instructions/planning.md`):
    - If needed behavior is not fully covered by existing specs, propose spec delta in chat.
    - Modify/add spec files only after explicit user approval.
    - If a new spec document is added, update `/spec/index.md` accordingly.
5. planning.md: Plan execution in more detail (in session chat) (`instructions/planning.md`).
6. **Confirmation gate** — MANDATORY (`instructions/planning.md`):
    - STOP and present the plan to user. Do NOT proceed to git management or implementation until user explicitly confirms.
    - The plan must include: scope, spec references, assumptions, and implementation steps.
    - Wait for user approval. If user requests changes, revise the plan and re-present.
7. planning.md: Write detailed implementation plan to `.plans/<branch>.md` for handover (gitignored — slashes in the branch name become dashes, e.g. `feature/foo-bar` → `.plans/feature-foo-bar.md`). This file is the implementer/stabilizer scratchpad; it never reaches the remote.
8. Git management (`AGENTS.md`) — MUST happen before ANY file edits:
    - Check repository state with `agent-git status --porcelain`.
    - If there are unstaged/uncommitted changes or conflicts, STOP ITERATION and ask user how to proceed.
    - Refresh `dev` branch with `agent-git checkout dev && agent-git pull --ff-only`.
    - Create a feature branch with `agent-git checkout -b feature/<feature_name>`.
    - **No file may be created, edited, or deleted before this step completes successfully.**
    - **Never work directly on `dev` or `master`** — see BRANCH MODEL.
9. delivery.md: Implement the plan (`instructions/delivery.md`). Typical implementation order:
    - tests;
    - code;
10. stabilization.md:
    - run tests;
    - if tests pass, continue;
    - if tests fail, use delivery.md to iterate on code changes; and test execution until tests pass or you are blocked (`instructions/stabilization.md`).
    - write discoveries to `.plans/<branch>.md`
11. **Review loop** (`instructions/review.md`):
    - Bounded cycle (`MAX_REVIEW_CYCLES = 2`) of: review → push-back protocol → implementation fixes → stabilization on fixes → re-review.
    - Reviewer has final say within the loop; the second push-back on a confirmed CRITICAL escalates to user. Every push-back round is logged in the Final Review Summary.
    - Early stop & escalate (token-budget aware): plan/spec change required, per-cycle caps exceeded, repeated CRITICAL signature, cycles exhausted with CRITICAL still open.
    - Reviewer inputs are limited to WAL.md, spec files referenced by the step, and the diff — the reviewer MUST NOT read `.plans/<branch>.md` (reading the implementer's step-by-step biases review toward plan-compliance instead of spec-compliance).
    - Reviewer appends Final Review Summary to `.plans/<branch>.md` before exit (fixed / push-backs accepted / push-backs confirmed / deferred / open questions / escalation reason if any) AND prints the summary in chat.
    - On escalation, STOP ITERATION and present the summary to user; do NOT proceed to step 12.
12. Pre-merge WAL update (`AGENTS.md`):
    - Update WAL step status to `[ready-for-review]` with concise motivation.
    - Distil important insights from `.plans/<branch>.md` into the WAL.md motivation line. The `.plans/` file itself stays local — gitignored, no cleanup needed.
13. Commit, publish branch, and open Draft MR (`AGENTS.md`):
    - Commit work with a meaningful message — the subject doubles as the default MR title.
    - Publish branch and open the Draft MR in one shot:
      ```
      agent-git push
      ```
    - `agent-git push` automatically adds `--set-upstream`, `merge_request.create`, `merge_request.draft`, and the policy-controlled `merge_request.target`. Do NOT supply them manually — explicit `merge_request.target=…` is rejected.
    - To pin a different MR title at first open: `agent-git push -o merge_request.title="…"`.
    - For follow-up pushes (review-loop fixes, stabilization, header updates), see the FULL LOOP EXAMPLE section below.
14. MR review and merge decision gate (in chat) (`AGENTS.md`):
    - Wait for user to confirm review outcome (`approved`, `changes requested`, or `merged`).
    - If `changes requested`: address feedback, push to the same MR, keep WAL status `[ready-for-review]`.
    - If `approved`: 
    -- update WAL step status to `[v]`. 
    -- create a follow-up commit for WAL update, and `agent-git push`. Then wait for user to merge.
    -- `.plans/<branch>.md` is gitignored — no removal step needed; it stays on the local machine and is naturally orphaned when the branch is deleted.
    - If `merged` (user merged directly without separate approval): update WAL step to `[v]` on `dev` (see step 15).
15. Post-merge finalization (`AGENTS.md`):
    - If WAL was already updated to `[v]` in the MR (approval path): nothing to do, WAL is correct on `dev` after merge.
    - If user merged without prior approval signal: `agent-git checkout dev && agent-git pull --ff-only`, mark WAL step `[v]`, then land it through a short-lived `chore/wal-*` branch + MR. A direct push from `dev` is blocked — `dev` carries none of the allowed branch prefixes (`feature/`, `fix/`, `chore/`, `refactor/`, `test/`, `agent/`).

# IMPLEMENTATION DEFINITION OF DONE (PRE-MERGE)
- tests added/updated according to the feature specification
- `agent-make test` runs successfully
- review loop converged (0 open CRITICAL) or was explicitly escalated to user with Final Review Summary
- branch pushed and `[Draft]` MR created
- WAL step is updated to `[ready-for-review]` with concise motivation

# APPROVAL DEFINITION OF DONE (PRE-MERGE)
- user confirms `approved` in chat
- WAL step is updated to `[v]` in the MR branch, pushed
- user merges the MR

# WORKFLOW DEFINITION OF DONE (POST-MERGE)
- MR is merged (WAL step already `[v]` from approval step)
- `dev` is up to date
- if the step touched a watched file (`Makefile`, `Dockerfile.tests`), it has ALSO reached `master` — otherwise `agent-make` stays blocked for every later step (see BRANCH MODEL)

# COMPANION INSTRUCTIONS (SCOPED)
- `instructions/planning.md`: use for strategic planning and architecture decisions in `spec/**`.
- `instructions/delivery.md`: use for feature/fix delivery (methodology only — no language-specific style).
- `instructions/stabilization.md`: use when tests fail, CI is red, or user review requests iterations.
- `instructions/review.md`: use after stabilization for the bounded review loop on the staged diff.
- If multiple companion instructions seem relevant, prioritize by phase: `planning` -> `delivery` -> `stabilization` -> `review`.
- These companion files augment this `AGENTS.md`; they do not override specification requirements.

# LANGUAGE PACKS (SCOPED)
- `instructions/lang/python.md`: Python + PyQGIS conventions (PEP 8, module-function pattern, Qt/QGIS imports, containerized tests). Applies to `{mapflow,tests}/**`.
- `instructions/lang/ui.md`: Qt dialog conventions (`uic.loadUiType`, `.ui` file placement, signal/slot style, icon handling, translatable strings). Applies to `mapflow/dialogs/**`.
- Add packs for other languages under `instructions/lang/` as the project grows. Each pack declares its own scope via `applyTo:` frontmatter.
- During delivery, stabilization, and review, consult the pack(s) matching the files being touched. A change under `mapflow/dialogs/**` is in scope for **both** packs. If no pack covers a language present in the diff, ask the user before inventing conventions.

# OPTIONAL: PER-PHASE MODEL SELECTION (CLAUDE CODE)
- When running under Claude Code, each phase MAY be delegated to the corresponding subagent in `.claude/agents/` (`planner`, `implementer`, `stabilizer`, `reviewer`). Subagents pin a recommended model per phase and reference the same instruction files.
- The main agent stays as orchestrator: it drives the session protocol above and dispatches each phase to the matching subagent.
- In environments without subagent support (Copilot, generic agents), ignore `.claude/agents/` and execute the instruction files inline — the workflow is unchanged.

# WAL MOTIVATION EXAMPLES
*Illustration — substitute your stack. The pattern (motivate the WHY, not the WHAT) is language-agnostic.*

BAD EXAMPLE (describes WHAT, which is already obvious from code). Don't do this.
```
[v] Implement request to external service
Used aiohttp; set the number of connections to 20
```
GOOD EXAMPLE:
```
[v] Implement request to external service
aiohttp is better than httpx for high throughput
limited connections to avoid server DDoS protection, issues can start around 40 connections
```

# COMMANDS TO RUN
All build/test invocations go through `agent-make` (raw `make` requires manual approval per call and bypasses watched-file verification).

`agent-make test` — all three test tiers (this is the DoD gate)
`agent-make test-functional` — pure-logic tests under `tests/functional/`
`agent-make test-qgis` — QGIS-runtime tests under `tests/qgis/`
`agent-make test-ui` — UI tests under `tests/ui/` (xvfb)
`agent-make lint` — static analysis on the host (see STATIC ANALYSIS)
`agent-make docker-build` — rebuild the test image explicitly
`agent-make clean` — remove pytest cache + bytecode
`agent-make help` — list targets

Note: `agent-make` does not accept `VAR=val` overrides. Every test target already depends on `docker-build`, so there is no separate rebuild flag — and no no-rebuild/attach path in this repo.

# TEST EXECUTION MODES
- All tests run **inside the `qgis/qgis:release-3_28` Docker image**, never from a host venv — the QGIS Python bindings are not importable on the host. The repo is bind-mounted at `/app`, so the container always sees your current working tree; the rebuild is for the image's dependencies, not your source.
- Tiers exist because of **runtime cost and requirements**, not test scope:
  - `test-functional` — no QGIS needed; fastest. Use this while iterating on `entity/`, `schema/`, `errors/`, and pure `functional/` logic.
  - `test-qgis` — needs the QGIS runtime. Use when touching layers, providers, projections, or anything importing `qgis.core` / `qgis.gui`.
  - `test-ui` — Qt widgets under `xvfb-run`. Currently an **empty harness**: the Makefile treats pytest's exit code 5 ("no tests collected") as a pass. A green `test-ui` therefore proves nothing yet — remove that guard in the Makefile once the first UI test lands.
- Run the narrow tier while iterating, but `agent-make test` must pass before review.
- If `agent-make` blocks with *"local files differ from origin/master"*, a watched file (`Makefile`, `Dockerfile.tests`) was edited locally — escalate to the user. Do not undo other work to satisfy the check.

# STATIC ANALYSIS (LINTING)
- `agent-make lint` runs **ruff** (config in `pyproject.toml`) then **pyright** (config in `pyrightconfig.json`).
- Unlike tests, lint runs on the **host**, not in Docker: ruff is AST-only and pyright runs in lenient
  `basic` mode, so neither needs the QGIS runtime. Both are installed in the project `venv`.
- Division of labour: ruff finds unused code and real-bug patterns (pyflakes `F` + bugbear `B`); pyright
  adds flow analysis ruff cannot do — `reportPossiblyUnbound` and `reportUndefinedVariable`. Pyright's
  type-completeness reports are intentionally muted until the codebase is annotated (see `pyrightconfig.json`).
- The rule set is deliberately narrow to start (`select = ["F", "B"]`); broaden it (`E`, `W`, `I`, `UP`)
  once the baseline is clean. `F401` is ignored in `__init__.py` (intentional re-exports).
- **Pending change (WAL 3.7.0, step 1):** the linter moves from ruff to **flake8**, adding **bandit** and
  **detect-secrets** to match the checks qgis.org runs on plugin submissions. Update this section when that lands.

# TERMINAL COMMAND BATCHING
- Read-only commands (`agent-git status`, `agent-git diff`, `agent-git log`, `agent-git show`, etc.) are allowlisted — call them directly, don't batch.
- Combine state-changing commands into a single `&&`-chained invocation when there is no need to inspect intermediate output. Example after a Confirmation-Gate-approved task with a clear path list:
  ```
  agent-git add mapflow/functional/service/foo.py tests/functional/test_foo.py && \
    agent-git commit -m "feat: foo handles empty input" && \
    agent-git push
  ```
- Prefer explicit paths over `agent-git add -A` / `add .` so untracked secrets or scratch files do not slip in. Use `-A` only when you have just run `agent-git status` and confirmed every untracked path belongs in the commit.
- Preferred fixup flow: new commit + `agent-git push`. Amend / force-push are blocked by `agent-git` by design.
- Raw `git push --force-with-lease` is blocked and should not be attempted — surface to user if you genuinely need it.

# FULL LOOP EXAMPLE — START TO MR
Concrete copy-paste of every step. The exact flow the SESSION PROTOCOL above expects.

```bash
# 0. Fresh start from the integration branch
agent-git checkout dev
agent-git pull --ff-only

# 1. Investigate recent history before planning
agent-git log --oneline -20                        # recent commits
agent-git log --oneline dev..origin/dev            # what landed since last sync
agent-git log --oneline master..dev                # unreleased — and what agent-make can't see yet
agent-git show <sha>                               # inspect a specific commit
agent-git diff <sha>~..<sha> -- path/              # narrow diff for a file/dir
agent-git blame path/to/file.py                    # who/why on a specific line

# 2. After the Confirmation Gate (step 6): create the work branch
agent-git checkout -b feature/short-descriptive-name

# 3. While working: track changes incrementally
agent-git status
agent-git diff                                     # unstaged changes
agent-git diff --staged                            # staged changes
agent-git log --oneline -5                         # commits on this branch

# 4. Stage explicit paths, then commit
agent-git add mapflow/functional/service/foo.py tests/functional/test_foo.py
agent-git commit -m "feat: foo handles empty input"
# The commit subject becomes the default MR title.

# 5. Open the Draft MR in one command
agent-git push
# Optional: pin the MR title at open instead of inheriting commit subject
agent-git push -o merge_request.title="feat: foo handles empty input"

# 6. Follow-up commit (review-loop fix, stabilization, etc.) — same flow
agent-git add mapflow/functional/service/foo.py
agent-git commit -m "fix: address review comment from the review loop"
agent-git push                                     # GitLab updates the existing MR

# 7. Update MR header on a follow-up push (no UI needed)
# IMPORTANT: git rejects newlines in push-option values with
#   fatal: push options must not have new line characters
# So MR title and description passed via -o must each fit on a single line.
agent-git push \
  -o merge_request.title="feat: foo handles empty input + N+1 fix" \
  -o merge_request.description="Summary: foo accepts empty input; provider lookup no longer raises on a missing key. Test plan: agent-make test."

# For a rich, multi-line MR description, do NOT try to cram it into a
# push option. Instead, put the body into the commit message itself —
# GitLab uses the commit body as the MR description by default whenever
# you do not override it with -o merge_request.description=.
agent-git commit -m "$(cat <<'EOF'
feat: foo handles empty input + N+1 fix

## Summary
- foo accepts empty input without raising
- provider lookup no longer raises on a missing key

## Test plan
- agent-make test-functional
- agent-make test
EOF
)"
agent-git push   # title = commit subject; description = commit body
```

Hard rules surfaced again here:
- `agent-git push` always opens or updates a Draft MR — never call `gh`, `glab`, or `git push -o merge_request.target=…` yourself.
- `--set-upstream` is added automatically; do not pass `-u`.
- No `Co-Authored-By:` trailers — the bot account identity is the agent attribution.
- Only `merge_request.{create,draft,title,description}` push options are accepted by `agent-git`; anything else is rejected.
- Push-option values are **single-line only** — git rejects newlines. For multi-line MR descriptions, write them into the commit body and push without `-o merge_request.description=`.

# IMPLEMENTATION GUIDELINES
- Methodology: `instructions/delivery.md`.
- Language style: matching pack under `instructions/lang/` — `lang/python.md` for `{mapflow,tests}/**`, `lang/ui.md` for `mapflow/dialogs/**`.
