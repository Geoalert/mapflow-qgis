---
description: "Use when tests fail, CI is red, or review feedback requests rework: run iterative fix cycles with breakpoints and explicit stop conditions."
applyTo: "{app,alembic,tests}/**"
---

# Stabilization Instructions

## Objective
Drive failing work to implementation DoD through controlled iterative fix cycles while avoiding unbounded loops.

## Iteration Loop
1. Reproduce failures and capture the exact failing signature.
2. Apply the smallest targeted fix.
3. Re-run the narrowest relevant tests, then broader tests.
4. Repeat until green or a stop condition is reached.

## Breakpoints and Stop Conditions
- Stop after 3 failed cycles and ask user whether to continue.
- Stop earlier if the same failure signature repeats after a fix attempt.
- Stop if resolving requires changing the spec or accepting a behavior tradeoff.
- Stop if tool/runtime limits prevent reliable validation.

## Feedback Handling
- Treat user review feedback as authoritative input.
- Group fixes by feedback thread and report which comments were addressed.
- If feedback is unavailable in chat, request it explicitly before proceeding.

## Reporting
For each cycle, report:
- failure signature
- change applied
- tests executed
- current status and next action

## Code Convention Checklist (verify each fix cycle)
- Imports at file top (PEP 8) — no lazy imports inside functions unless circular dependency requires it.
- Follow module-function pattern from delivery instructions.
- No unintended scope creep in the fix.
