# SPECIFICATION GUIDELINES
1. NEVER change specifications unless explicitly and separately asked to work on them. If some specification produces suboptimal code, raise it in the WAL motivation and surface to the user during the Confirmation Gate or Review Loop.
2. Tests MUST directly follow SPECIFICATION found in /spec folder. If some test is impossible to write according to specification, STOP ITERATION and ask user.
3. Application code SHOULD follow specifications unless impossible; in this case STOP ITERATION and ask user before deviating.

# BRANCH MODEL — READ BEFORE ANY GIT OR MAKE COMMAND

This repo uses **git flow with `dev` as the integration branch**. Feature branches are cut from `dev` and their PRs target `dev`. `master` is the release branch.

**`master` is also the branch `agent-make` verifies watched files against.** Not a choice — `agent-repo-init` refuses any `--branch` but `main` or `master`. These two facts collide, and the collision is load-bearing:

- Editing a watched file (`Makefile`, `Dockerfile.tests`) and merging it to `dev` does **not** unblock `agent-make`. Every invocation keeps failing with *"local files differ from origin/master"* until that change also reaches `master`.
- So a step that touches a watched file needs its own PR merged to `master` **before** any subsequent step can run tests. Plan such steps first in a release, or land them as a standalone PR.
- Never "fix" this by reverting the watched file to match `master`. That silently discards the change. STOP and surface to the user — merging to `master` is a human action.

The collision applies to **watched files only**. `AGENTS.md`, `instructions/`, `spec/`, `.claude/` and all plugin code are not compared against anything, so they merge to `dev` like any other change and never need a trip through `master`.

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
`origin` here is **GitHub**, so pushing and opening the PR are two commands, not one.

`agent-git push` moves the branch and adds `--set-upstream` on the first push. It does **not** open a pull request: `merge_request.*` push options are a GitLab feature that GitHub ignores, so `agent-git` strips them on this remote and prints

```
agent-git: pushed '<branch>'. Open a Draft PR with: agent-pr create
```

This split is deliberate. Because `agent-git push` never touches PR state, a follow-up push can never flip a PR a human marked "Ready" back to Draft.

# PULL REQUESTS: `agent-pr`

`agent-pr` wraps the GitHub CLI (`gh`) with the same policy `agent-git` enforces.

```
agent-pr create                       # open a Draft PR for the current branch
agent-pr create --title "…" --body "…"
agent-pr update --title "…"           # edit the current branch's PR
agent-pr update --body-file NOTES.md
agent-pr view                         # show the current branch's PR
agent-pr --self-check                 # verify gh, token and bot identity
```

What it enforces, and what that means for you:
- **The base branch comes from `agent-git.mr-target` and cannot be overridden.** There is no `--base`. If a PR opens against the wrong branch, the fix is `agent-repo-init --mr-target <branch>`, which is the user's to run.
- **`create` always opens a Draft**, and only for the current branch.
- **`create` takes BOTH `--title` and `--body`, or NEITHER.** Which form to use depends on how many commits the branch has:
  - **One commit** — use the bare form. Title and body come from that commit message, which is where the WHY already lives (see WHERE THE WHY GOES).
  - **More than one** — pass both explicitly. The derived title is the **branch name** with separators replaced, not any commit subject, and the derived body is a bullet list of subjects. Write the body to a file and pass `--body-file`; a heredoc needs `cat`, which is denied.
- The same branch rules as `agent-git`: refuses a detached HEAD, a protected branch, and any branch not prefixed `feature/`, `fix/`, `chore/`, `refactor/`, `test/`, `agent/`.
- Multi-line bodies are fine here — unlike push options, `--body` is a normal argument. Use `--body-file` for anything long.

So the full flow is:
```
agent-git push
agent-pr create
```

**If `agent-pr` reports a missing token**, stop and surface it. It needs `AGENT_GH_TOKEN` (a GitHub fine-grained PAT for the bot account, Pull requests: write + Contents: read) in `/etc/agent-security-toolkit.conf` — a root-owned file. That is a human action; do not attempt to work around it, and do not fall back to `gh` directly. Report the branch as pushed and say the PR must be opened manually.

## Stacking a PR on an unmerged one — prefer not to

The repo merges with GitHub's **"Rebase and merge"**, which replays commits as *new objects*. A branch stacked on the one being merged still holds the originals, so after the parent merges the child PR shows the parent's changes all over again. The fix is a rebase and a **force push**, which `agent-git` blocks by design — so it becomes the user's manual step.

Avoid the situation rather than handling it:

- **Sequence instead of stacking.** Finish a step, let it merge, `agent-git checkout dev && agent-git pull --ff-only`, branch again.
- **If you must work ahead, keep it local.** Commit on a branch cut from the current `dev`, but do not push. When the parent merges, `agent-git rebase origin/dev` (it drops the already-applied commits on its own) and push *once*. A first push never needs `--force`.
- Only stack a pushed branch when the user explicitly asks for it, and say up front that they will have to force-push after the parent merges.

If it happens anyway: `agent-git rebase origin/dev` cleans the history, then the user runs the force push. Do not attempt to work around the block.

## When `agent-git` or `agent-pr` blocks you
Read the `BLOCKED:` / error line — it is the spec. **Do not work around it.** Stop and surface to the user with the exact message. Common cases:
- Branch name doesn't match the allowed prefix → rename the branch.
- PR base equals the current branch → user must run `agent-repo-init --mr-target <branch>`.
- Push to protected branch → switch to a feature branch first.
- `AGENT_GH_TOKEN` not set → human action, see above.
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
- `WAL.md` — **lean, forward-facing** plan + in-flight tracker: holds only `[ ]` planned and `[ready-for-review]` in-flight steps. It is NOT a permanent journal. The **WHY** of completed work is preserved in (1) the change's **commit message** and (2) `spec/` files for durable decisions. When a step merges, its rationale is distilled into those places and the entry is **removed** from `WAL.md`.
  - Authors: the **user** and the **planner**. Implementer, stabilizer and reviewer read it but never write it.
  - Consult it when planning the next step — it should answer "what is left", not "what did we do".
  - Corollary: never write anything into `WAL.md` that belongs in `spec/`. A decision that outlives the step is a spec change; the WAL entry only points at it.
- .plans/ - **gitignored** per-branch agent handover scratchpad. One file per feature branch: `.plans/<sanitized-branch-name>.md` (slashes in the branch name become dashes, e.g. `feature/foo-bar` → `.plans/feature-foo-bar.md`). Holds the detailed step plan, stabilization discoveries, push-back rounds, and Final Review Summary. Never reaches the remote; its distilled insights land in the **commit message** (and `spec/`, if a durable decision changed) at merge.

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
12. Pre-merge distillation (`AGENTS.md`):
    - Mark the WAL step `[ready-for-review]`. Keep the entry itself short — it is a tracker line, not a write-up.
    - Distil the important insights from `.plans/<branch>.md` into **the commit message body** (the WHY), and into `spec/` for anything that outlives this step. The `.plans/` file stays local — gitignored, no cleanup needed.
    - Add a `## Manual test` section to the commit message: new behaviour to try, and the regression surface with the symptom to watch for. Write `none` explicitly rather than omitting it. See `instructions/delivery.md` § Manual Test Notes — the release checklist is compiled from these, so a missing one is a gap nobody notices until a user finds it.
    - If a durable decision changed, the spec edit is part of THIS PR. Do not leave it as a WAL note to apply later.
13. Commit, publish branch, and open the Draft PR (`AGENTS.md`):
    - Commit work with a meaningful message — `agent-pr create` derives the PR from it.
    - Publish the branch, then open the Draft PR:
      ```
      agent-git push
      agent-pr create
      ```
    - `agent-git push` adds `--set-upstream` itself; do not pass it. It does **not** open the PR — on this GitHub remote that is `agent-pr`'s job.
    - Prefer bare `agent-pr create`: with neither `--title` nor `--body` it takes both from the branch's commits, which is where the WHY already lives. Passing one means passing both.
    - The base branch is policy (`agent-git.mr-target`) and cannot be passed. If it is wrong, stop — the fix is `agent-repo-init --mr-target <branch>`, which the user runs.
    - For follow-up pushes (review-loop fixes, stabilization, header updates), see the FULL LOOP EXAMPLE section below.
14. PR review and merge decision gate (in chat) (`AGENTS.md`):
    - Wait for user to confirm review outcome (`approved`, `changes requested`, or `merged`).
    - If `changes requested`: address feedback, push to the same branch, keep WAL status `[ready-for-review]`.
    - If `approved`: 
    -- **remove** the step's entry from `WAL.md` — its WHY is already in the commit message and, where durable, in `spec/`. Do not mark it done and leave it; the WAL only carries planned and in-flight work.
    -- create a follow-up commit for the WAL removal, and `agent-git push`. Then wait for user to merge.
    -- `.plans/<branch>.md` is gitignored — no removal step needed; it stays on the local machine and is naturally orphaned when the branch is deleted.
    - If `merged` (user merged directly without separate approval): remove the entry on `dev` (see step 15).
15. Post-merge finalization (`AGENTS.md`):
    - If the entry was already removed in the PR (approval path): nothing to do, `WAL.md` is correct on `dev` after merge.
    - **Verify the merge before acting on it.** `agent-git log --oneline origin/dev..origin/<branch>` must come back empty. A report of "merged" can arrive for a different branch than the one you are on, and re-pulling `dev` on a wrong assumption silently reverts the working tree to the pre-merge state.
    - If user merged without prior approval signal: `agent-git checkout dev && agent-git pull --ff-only`, remove the step's entry, then land it through a short-lived `chore/wal-*` branch + PR. A direct push from `dev` is blocked — `dev` carries none of the allowed branch prefixes (`feature/`, `fix/`, `chore/`, `refactor/`, `test/`, `agent/`).
    - Before removing, confirm the WHY actually survives elsewhere. If the rationale exists only in the WAL entry, it is not yet distilled — move it to `spec/` first, or the removal destroys it.

# IMPLEMENTATION DEFINITION OF DONE (PRE-MERGE)
- tests added/updated according to the feature specification
- `agent-make test` runs successfully
- review loop converged (0 open CRITICAL) or was explicitly escalated to user with Final Review Summary
- branch pushed and Draft PR opened with `agent-pr create`
- WAL step is marked `[ready-for-review]`; the WHY is in the commit message body, and any durable decision is in `spec/`
- the commit message has a `## Manual test` section (new behaviour + regression surface, or an explicit `none`)

# APPROVAL DEFINITION OF DONE (PRE-MERGE)
- user confirms `approved` in chat
- the step's entry is **removed** from `WAL.md` in the PR branch, pushed
- user merges the PR

# WORKFLOW DEFINITION OF DONE (POST-MERGE)
- PR is merged, confirmed by `agent-git log --oneline origin/dev..origin/<branch>` coming back empty
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

# WHERE THE WHY GOES
Three destinations, and the split is not optional — see PROJECT STRUCTURE for the WAL's scope.

| content | destination | lifetime |
|---|---|---|
| what is planned / in flight | `WAL.md` | deleted when the step merges |
| why this change was made | **commit message body** | forever, attached to the diff |
| a decision that outlives the step | `spec/` | forever, findable without git |
| why this code would otherwise look wrong | **code comment** | until the code changes |

A code comment addresses the next reader of that line, who has never seen the previous
version. It justifies what is *surprising* about the code as it stands — never that the
code is now normal, and never by contrast with what used to be there. "We stopped doing
the strange thing" is commit-message content. See `instructions/delivery.md` § Comments
Describe The Code, Not Its History.

## WAL entries are tracker lines, not write-ups
BAD — a WAL entry carrying rationale that belongs in the commit message:
```
[ready-for-review] Implement request to external service
aiohttp is better than httpx for high throughput; limited connections to 20 because
the server's DDoS protection starts rejecting around 40; retries use exponential
backoff since the 502s are transient …
```
GOOD:
```
[ready-for-review] Implement request to external service
```

## Commit messages carry the WHY
*Illustration — substitute your stack. The pattern (motivate the WHY, not the WHAT) is language-agnostic.*

BAD EXAMPLE (describes WHAT, which is already obvious from the diff). Don't do this.
```
Implement request to external service

Used aiohttp; set the number of connections to 20
```
GOOD EXAMPLE:
```
Implement request to external service

aiohttp is better than httpx for high throughput
limited connections to avoid server DDoS protection, issues can start around 40 connections
```
If that rationale constrains future work — "we cap connections at 20" is a contract, not a
one-off — it belongs in `spec/` as well. The commit message explains this change; the spec
tells the next person what they may not break.

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
- `agent-make lint` runs **flake8**, then **bandit**, then **detect-secrets** — the three checks
  plugins.qgis.org runs on plugin submission, with the same invocations, so a green run here predicts
  a clean scan there. Full rationale in `spec/004_stack.md` § Static analysis.
- Unlike the previous ruff/pyright setup, lint runs **in the same Docker image as the tests**, not on
  the host. Tool versions are pinned in `Dockerfile.tests` so every developer and CI get identical
  results. There is no host `venv` step and no `pip install`.
- Scope differs per tool on purpose: flake8 covers `mapflow/` **and** `tests/`; bandit covers `mapflow/`
  only (it is the code that ships, and `B101` would otherwise fire on every pytest assertion);
  detect-secrets runs against the committed `.secrets.baseline`.
- At qgis.org, bandit and detect-secrets are **blocking** and flake8 is advisory. Locally all three
  block — a check that cannot fail the build does not hold a line.
- `.flake8` carries a **debt ledger** under `extend-ignore`: rule classes still outstanding from the
  3.6.0 scan, each commented with the WAL step that removes it. **The list only shrinks.** Do not add a
  code to it to make your MR pass — fix the finding, or escalate. Note the qgis.org scan never reads
  `.flake8`, so everything in that list is debt still owed at submission time.
- Use `extend-ignore`, never `ignore` — the latter *replaces* flake8's default ignore set and silently
  re-enables rules qgis.org itself does not report. flake8 parses config with `RawConfigParser`, so
  inline comments on value lines are a syntax error; keep comments on their own line.
- Suppressing a bandit finding: the form is `# nosec B105  # reason` — test ID first, then a
  **second `#`** before the prose. bandit captures everything after `nosec` up to the next `#` and
  parses it as test IDs, so `# nosec - reason` makes it warn once per word, once per run. A bare
  `# nosec` with the reason on the preceding line also parses cleanly.
- **Known gap:** nothing in this toolchain replaces pyright's `reportPossiblyUnbound`
  (use-before-assignment across branches). flake8's `F821` covers undefined names only. Accepted
  deliberately for qgis.org parity; revisit after the refactor lands type annotations.

# WHICH TERMINAL COMMANDS TO REACH FOR

**Every command outside the allowlist costs a permission prompt**, which stalls an unattended run
until a human answers. Autonomy therefore depends on staying inside the list, not on being clever
with the shell. The allowlist is `.claude/settings.json` (Claude Code) — read it rather than
guessing, and if something you need is genuinely missing, ask for it to be added instead of
routing around it.

Allowlisted: the toolkit wrappers (`agent-git`, `agent-make`, `agent-pr`, `agent-doctor`) and
read-only inspection (`grep`, `rg`, `find`, `ls`, `wc`, `head`, `tail`, `sort`, `uniq`, `cut`,
`diff`, `file`, `which`, `mkdir`).

**Use the built-in tools instead of shell equivalents.** They are always permitted, they do not
prompt, and they are what the deny list exists to push you toward:

| Instead of | Use |
|---|---|
| `cat`, `head -n`, `sed -n '1,50p'` to read | the **Read** tool (it takes `offset`/`limit`) |
| `sed -i`, `awk`, `python3` heredocs to rewrite a file | the **Edit** tool, with a unique anchor string |
| `echo … > file`, `tee`, `cat <<EOF` | the **Write** tool |
| `git`, `make`, `docker`, `gh` | `agent-git`, `agent-make`, `agent-pr` |

Deleting a range of lines has no shell shortcut here: anchor an **Edit** on the first and last
lines of the block and replace it with what should follow. Reaching for `python3` to do it by line
number is denied outright, because a line number is exactly the thing that goes stale between
reading a file and editing it.

Shell-compound forms (`;`, `||`, `&&` with a denied command, a pipe into `awk`) are matched
per-command, so one denied element blocks the whole invocation. Keep each call to a single
allowlisted command, and let the built-in tools do the rest.

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

# FULL LOOP EXAMPLE — START TO PR
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

# 4. Stage explicit paths, then commit.
# The commit message is the PR: `agent-pr create` takes the title from the subject
# and the body from the message body, so write it for a reader of the PR.
agent-git add mapflow/functional/service/foo.py tests/functional/test_foo.py
agent-git commit -m "$(cat <<'EOF'
feat: foo handles empty input

Empty input reached the provider lookup as None and raised there, three frames from
the cause. Rejecting it at the boundary is what makes the error name the input.

## Manual test
Submit the form with the field blank: it is refused with "specify a name" instead of
failing mid-request. Regression surface: a filled field must still submit.
EOF
)"

# 5. Publish the branch, then open the Draft PR
agent-git push
agent-pr create                                    # single-commit branch: derives from the commit
# Multi-commit branch: derive gives you the BRANCH NAME as the title, so be explicit.
agent-pr create --title "feat: foo handles empty input" --body-file /tmp/pr-body.md

# 6. Follow-up commit (review-loop fix, stabilization, etc.) — same flow
agent-git add mapflow/functional/service/foo.py
agent-git commit -m "fix: address review comment from the review loop"
agent-git push                                     # updates the branch; PR state untouched

# 7. Update the PR header without touching the UI
agent-pr update --title "feat: foo handles empty input + N+1 fix"
agent-pr update --body-file .plans/pr-body.md      # multi-line is fine here
agent-pr view                                      # what the PR currently says

# 8. If agent-pr reports a missing token, STOP.
agent-pr --self-check                              # gh present? token set? bot identity?
# AGENT_GH_TOKEN lives in /etc/agent-security-toolkit.conf and is a human's to add.
# Report the branch as pushed and let the user open the PR.
```

Hard rules surfaced again here:
- `agent-git push` moves the branch; `agent-pr create` opens the Draft PR. Never call `gh` or `glab` yourself — both are denied.
- `--set-upstream` is added automatically; do not pass `-u`.
- The PR base is policy and has no flag. A wrong base is `agent-repo-init --mr-target`, which the user runs.
- `agent-pr create` takes both `--title` and `--body` or neither — prefer neither.
- Never run `agent-repo-init` yourself: it sets the boundary you operate inside, and that authorization is the user's.
- No `Co-Authored-By:` trailers — the bot account identity is the agent attribution.

# IMPLEMENTATION GUIDELINES
- Methodology: `instructions/delivery.md`.
- Language style: matching pack under `instructions/lang/` — `lang/python.md` for `{mapflow,tests}/**`, `lang/ui.md` for `mapflow/dialogs/**`.
