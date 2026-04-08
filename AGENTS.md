# SPECIFICATION GUIDELINES
1. NEVER change specifications unless explicitly and separately asked to work on them. If some specification produces suboptimal code, add `#WARNING` comment to the code explaining how specification could be improved
2. Tests MUST directly follow SPECIFICATION found in /spec folder. If some test is impossible to write according to specification, STOP ITERATION and ask user
3. Application code SHOULD follow specifications unless impossible; in this case add `WARNING` comment to the code

# GIT COMMAND POLICY FOR AGENTS
- Use `agent-git` whenever possible for git operations. `agent-git` is expected to be in the "always allowed" command pool, so it should be the default path for agent workflows.
- Use raw `git` only when `agent-git` cannot express the required operation. Such usage is **not recommended** and must be explicitly justified in the command text.

# PROJECT STRUCTURE AND ADDRESSING
- /mapflow: QGIS plugin source code (Python, Qt/PyQGIS)
- /mapflow/dialogs: Qt dialog classes and `.ui` files
- /mapflow/functional: business logic, API clients, controllers, views
- /mapflow/entity: domain models (processing, provider, billing, etc.)
- /mapflow/schema: data schemas
- /mapflow/errors: error types and messages
- /tests: test files (pytest)
- /spec: contains specifications, ordered by hierarchy: the very foundation in 001, then go the most important architecture details (api, db, stack), all further decisions and rationale are documented in subsequent files
- WAL.md - file with current implementation plan, updated regularly on completion/changes

# SESSION PROTOCOL FOR FEATURE IMPLEMENTATION
Execute it every time a session is initiated.

0. Ensure local dev is up to date: `agent-git checkout dev && agent-git pull --ff-only`.
    - If there are unstaged/uncommitted changes, STOP ITERATION and ask user how to proceed.
1. Read WAL.md to update the state of the previous steps to revisit decision making (`.github/instructions/planning.instructions.md`)
2. panning.instructions.md: Find next step to work on in WAL.md (`.github/instructions/planning.instructions.md`)
3. panning.instructions.md: Revisit `/spec` folder for the documentation related to the task. Use `/spec/index.md` to find related documents, then dive into them (`.github/instructions/planning.instructions.md`).
    - If contradictions are found, STOP ITERATION, ask user to clarify spec and task, and highlight inconsistent documentation.
4. panning.instructions.md: Specification coverage gate (`.github/instructions/planning.instructions.md`):
    - If needed behavior is not fully covered by existing specs, propose spec delta in chat.
    - Modify/add spec files only after explicit user approval.
    - If a new spec document is added, update `/spec/index.md` accordingly.
5. panning.instructions.md: Plan execution in more detail (in session chat) (`.github/instructions/planning.instructions.md`).
6. **Confirmation gate** — MANDATORY (`.github/instructions/planning.instructions.md`):
    - STOP and present the plan to user. Do NOT proceed to git management or implementation until user explicitly confirms.
    - The plan must include: scope, spec references, assumptions, and implementation steps.
    - Wait for user approval. If user requests changes, revise the plan and re-present.
7. panning.instructions.md: Write detailed implementation plan to a temporary file `WAL_<N>.md` for handover
8. Git management (`AGENTS.md`) — MUST happen before ANY file edits:
    - Check repository state with `agent-git status --porcelain`.
    - If there are unstaged/uncommitted changes or conflicts, STOP ITERATION and ask user how to proceed.
    - Refresh `dev` branch with `agent-git checkout dev && agent-git pull --ff-only`.
    - Create a feature branch with `agent-git checkout -b feature/<feature_name>`.
    - **No file may be created, edited, or deleted before this step completes successfully.**
    - **This repo uses git flow with feature branches inherited from `dev` branch. Never work with `master` branch.
9. delivery.instructions.md: Implement the plan (`.github/instructions/delivery.instructions.md`). Typical implementation order:
    - tests;
    - code;
10. stabilization.instructions.md:
    - run tests;
    - if tests pass, continue;
    - if tests fail, use delivery.instruction.md to iterate on code changes; and test execution until tests pass or you are blocked (`.github/instructions/stabilization.instructions.md`).
    - write discoveries to `WAL_<N>.md`
9. Pre-merge WAL update (`AGENTS.md`):
    - Update WAL step status to `[ready-for-review]` with concise motivation.
    - Move important insights from `WAL_<N>.md`
10. Commit, publish branch, and create `[Draft]` MR (`AGENTS.md`):
    - Commit work with a meaningful message.
        - Publish branch with `agent-git push`.
        - Create `[Draft]` MR via UI (preferred) or with GitLab push options through `agent-git`:
      ```
            agent-git push --set-upstream <commit message summary>"
      ```
11. MR review and merge decision gate (in chat) (`AGENTS.md`):
    - Wait for user to confirm review outcome (`approved`, `changes requested`, or `merged`).
    - If `changes requested`: address feedback, push to the same MR, keep WAL status `[ready-for-review]`.
    - If `approved`: 
    -- update WAL step status to `[v]`. 
    -- remove temporary file `WAL_<N>.md`
    -- create a follow-up commit for WAL update, and `agent-git push`. Then wait for user to merge.
    - If `merged` (user merged directly without separate approval): update WAL step to `[v]` on `dev` (see step 12).
12. Post-merge finalization (`AGENTS.md`):
    - If WAL was already updated to `[v]` in the MR (approval path): nothing to do, WAL is correct on `dev` after merge.
    - If user merged without prior approval signal: `agent-git checkout dev && agent-git pull --ff-only`, mark WAL step `[v]`, commit and push directly to dev using `agent-git push`.

# IMPLEMENTATION DEFINITION OF DONE (PRE-MERGE)
- tests added/updated according to the feature specification
- `pytest tests/` runs successfully
- branch pushed and `[Draft]` MR created
- WAL step is updated to `[ready-for-review]` with concise motivation

# APPROVAL DEFINITION OF DONE (PRE-MERGE)
- user confirms `approved` in chat
- WAL step is updated to `[v]` in the MR branch, pushed
- user merges the MR

# WORKFLOW DEFINITION OF DONE (POST-MERGE)
- MR is merged (WAL step already `[v]` from approval step)
- dev is up to date

# COMPANION INSTRUCTIONS (SCOPED)
- `.github/instructions/planning.instructions.md`: use for strategic planning and architecture decisions in `spec/**`.
- `.github/instructions/delivery.instructions.md`: use for feature/fix delivery in `{mapflow,tests}/**`.
- `.github/instructions/stabilization.instructions.md`: use when tests fail, CI is red, or user review requests iterations.
- If multiple companion instructions seem relevant, prioritize by phase: `planning` -> `delivery` -> `stabilization`.
- These companion files augment this `AGENTS.md`; they do not override specification requirements.

# WAL MOTIVATION EXAMPLES
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
`pytest tests/` to run the full test suite
`pytest tests/test_<name>.py` to run a specific test file
`pytest tests/ -k "test_name"` to run a specific test by name

# TEST EXECUTION MODES
- All tests run locally with pytest (no containers).
- QGIS-dependent tests may require a QGIS environment or mocking of `qgis.*` / `PyQt5.*` imports.
- Pure logic tests (data transforms, URL building, schema validation) should not depend on QGIS runtime.

# TERMINAL COMMAND BATCHING
- Combine commands that both require user approval into a single `&&`-chained invocation to minimize approval prompts.
- Example: use `agent-git add -A && agent-git commit -m "message" && agent-git push` instead of separate invocations, if the repo state is clear and there is no need to steer on command output.
- Preferred WAL fixup flow: use a new commit and `agent-git push` instead of amend+force workflows.
- Raw `git push --force-with-lease` is **not recommended** (outside `agent-git` policy). Use only when strictly unavoidable and explicitly justified.
- Read-only commands (`agent-git status`, `agent-git diff`, `agent-git log`) do NOT need batching — they are auto-approved.

# IMPLEMENTATION GUIDELINES
- Full implementation conventions are defined in `.github/instructions/delivery.instructions.md` and apply to `{mapflow,tests}/**`.
- UI-specific conventions are in `.github/instructions/ui.delivery.instructions.md` and apply to `mapflow/dialogs/**`.
