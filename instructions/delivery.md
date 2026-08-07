---
description: "Use during the delivery phase: implement features/fixes and their tests with maximum alignment to /spec and the workflow in AGENTS.md. Language-specific style lives in instructions/lang/*."
---

# Delivery Instructions

## Objective
Implement production code and tests together with maximum alignment to `/spec` and the repository workflow in `AGENTS.md`. Pull language-specific style from the matching pack under `instructions/lang/`.

## Required Workflow
1. Read the planner's handover at `.plans/<branch>.md` (gitignored per-branch scratchpad — see AGENTS.md PROJECT STRUCTURE). It contains the approved scope, spec references, acceptance criteria, and ordered steps.
2. Confirm the target behavior from `/spec` before edits — `.plans/<branch>.md` is a roadmap, not a spec.
3. Add or update tests first when behavior is changed.
4. Implement code changes with minimal, clear diffs.
5. Run the project's test suite (entry points listed in `AGENTS.md` COMMANDS section), plus focused suites when needed.
6. Append discoveries, deviations, and decisions to `.plans/<branch>.md` as you work — the stabilizer and the pre-merge WAL distillation rely on this trail. Do NOT commit the file (it is gitignored).
7. If blocked by ambiguity, stop and ask for clarification.

## Push-back Handling (inside the Review Loop)
When the reviewer raises a CRITICAL comment (AGENTS.md step 11), respond per the push-back protocol in `instructions/review.md`:
- Apply the fix, OR
- Push back with a citation to `/spec`, the WAL step, or the relevant section of `.plans/<branch>.md`.

Every push-back the reviewer accepts or confirms is logged by the reviewer into `.plans/<branch>.md` automatically — do not duplicate the log yourself.

## Comments Describe The Code, Not Its History

A comment is read by someone opening the file for the first time, who has never seen any
earlier version of it. Write for that reader.

**The test — delete the comment, then ask: could a competent reader now make a change that
reintroduces a real problem?**
- Yes → keep it. That is the comment's job.
- No → delete it. It is narration.

### Comment when the code would otherwise look wrong
These are the cases where silence invites someone to "clean up" working code:
- a deliberately broad `except` — say why narrowing is impossible
- a lazy or otherwise misplaced import — say which cycle it dodges
- a narrow exception tuple — say what each member covers, so it is not widened back
- the deliberate **absence** of something (a guard, a log call, a check) and where it lives instead
- a non-obvious constant or threshold — say what breaks on either side of it
- an ordering dependency between statements
- a workaround for external behaviour (backend quirk, Qt binding, library bug)

### Never comment to say the code is fine
Normal code needs no defence. If the current form is the obvious choice, silence conveys
that better than a paragraph does.
```python
# BAD — reassurance that nothing strange is happening
# No lazy import needed any more: logging is stdlib, so it cannot re-enter the
# circular chain this module used to have to dodge.
logger.info("...")

# GOOD
logger.info("...")
```

### Never reference a previous state
The reader cannot see the state you are contrasting against, so the comment is noise to
them — and it rots the moment the code changes again. Treat these as banned openings:
*"used to"*, *"previously"*, *"no longer"*, *"any more"*, *"instead of the old"*,
*"simplified from"*, *"now correctly"*.

The historical WHY belongs in the **commit message** (see AGENTS.md WHERE THE WHY GOES).
That is exactly what it is for, and it stays attached to the diff that made the change.

### Turn history into a constraint
When the old state was a genuine hazard, the knowledge is worth keeping — but address it
to the person about to reintroduce it, not to the person who removed it:
```
BAD   The previous helper lived in functional/service/, which made it unreachable
      from leaf modules like schema/catalog.py.

GOOD  Do not move this behind a helper in functional/service/ — that package sits on
      the circular import chain documented in tests/functional/conftest.py, which
      would force lazy-import shims at every call site.
```
Same knowledge, forward-facing, and it stays true.

### The same rule applies to tests
Explain a non-obvious harness choice — *"the cap is patched rather than reached by deep
recursion, because Python collapses identical repeated frames"* — not what the test used
to assert or which bug prompted it. Name the bug in the test's docstring only when it
defines the expected behaviour being locked in.

## Language Conventions
Language-specific style, idioms, and patterns live in per-language packs under `instructions/lang/`. Consult the pack that matches the file you are editing (e.g. `lang/python.md` for `.py` files). If no pack exists for the language you need, ask the user before inventing conventions.

## Tooling Policy For File Operations
Use the agent's native file-edit/write tools for **all writes**. Never shell out for destructive or stateful operations — they bypass the agent's edit tracking and trigger an approval prompt per invocation. This includes: `sed -i`, `awk -i inplace`, `echo > file`, `tee`, `mv`, `rm`, `mkdir`, `touch`, `cp`.

Read-only shell commands are encouraged when they save tokens — they are typically pre-approved and let you load only the lines you need rather than full files:
- `grep -n` / `rg` to locate symbols without reading entire files
- `find` / `ls` to enumerate paths
- `head` / `tail` / `wc` for bounded reads
- `cat` only when a full read is cheaper than a targeted one

Rule of thumb: **writes → native tool; reads → whichever costs fewer tokens.**

For git operations, follow the `agent-git` policy in `AGENTS.md`.

## Quality Guardrails
- No speculative refactors outside the requested scope.
- Keep performance-sensitive paths explicit (avoid hidden N+1 patterns, unnecessary loops, and redundant DB calls).
- Preserve backward compatibility unless the spec explicitly requires a contract change.
