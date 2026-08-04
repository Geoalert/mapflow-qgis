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
