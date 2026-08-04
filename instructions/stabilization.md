---
description: "Use when tests fail, CI is red, or review feedback requests rework: run iterative fix cycles with breakpoints and explicit stop conditions."
---

# Stabilization Instructions

## Objective
Drive failing work to implementation DoD through controlled iterative fix cycles while avoiding unbounded loops.

## Inputs
- The failing test output / CI log.
- `.plans/<branch>.md` — the planner's handover, plus any implementer notes from delivery. Treat it as the running scratchpad for this branch.
- The minimal set of files implicated by the failure signature.

## Iteration Loop
1. Reproduce failures and capture the exact failing signature.
2. Apply the smallest targeted fix.
3. Re-run the narrowest relevant tests, then broader tests. Tier order for this repo: `agent-make test-functional` → `test-qgis` / `test-ui` → `agent-make test` (see AGENTS.md TEST EXECUTION MODES).
4. Repeat until green or a stop condition is reached.

## Breakpoints and Stop Conditions
- Stop after 3 failed cycles and ask user whether to continue.
- Stop earlier if the same failure signature repeats after a fix attempt.
- Stop if resolving requires changing the spec or accepting a behavior tradeoff.
- Stop if tool/runtime limits prevent reliable validation.
- **Stop immediately if `agent-make` reports *"local files differ from origin/master"*** — a watched file (`Makefile`, `Dockerfile.tests`) was edited. No fix cycle can proceed, and reverting the file to unblock yourself would discard someone's work. Surface to the user; merging to `master` is a human action (see AGENTS.md BRANCH MODEL).

## Feedback Handling
- Treat user review feedback as authoritative input.
- Group fixes by feedback thread and report which comments were addressed.
- If feedback is unavailable in chat, request it explicitly before proceeding.

## Reporting
For each cycle, report in chat AND append to `.plans/<branch>.md`:
- failure signature
- change applied
- tests executed
- current status and next action

The `.plans/<branch>.md` trail is what the pre-merge step distils into the WAL.md motivation line; without it, the WHY of stabilization decisions is lost.

## Convention Checklist (verify each fix cycle)
- No unintended scope creep in the fix.
- Language-specific style rules from the matching pack under `instructions/lang/` still hold after the fix.
- No silently-introduced patterns (lazy imports, ad-hoc wrappers, dead code) that the language pack discourages.
