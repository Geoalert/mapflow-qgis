---
description: "Use after stabilization, before pre-merge WAL update, to run a bounded review loop on the staged diff: logic gaps, security, performance, duplication, style consistency. Does not re-open the approved plan."
---

# Review Instructions

## Objective
Run a bounded, autonomous review loop over the staged diff to catch issues that implementation and stabilization missed, without re-opening the approved plan.

## Inputs (read only what is needed — token-budget aware)
- Diff vs. branch base (`agent-git diff master...HEAD`).
- `WAL.md`: the persistent journal entry for this step — the WHY and acceptance criteria.
- Spec files referenced by the WAL step (do NOT re-read all of `/spec`).
- Files touched by the diff and their immediate dependencies.

**Forbidden input: `.plans/<branch>.md`.** That file is the implementer's step-by-step scratchpad. Reading it biases review toward "did they follow the plan" instead of "does the result satisfy the spec." If the plan was wrong but executed faithfully, only the spec-vs-diff check catches it.

## Review Checklist (per cycle)
1. **Plan compliance** — every change traces to the approved plan; flag drift.
2. **Logic gaps** — missing branches, off-by-one, error paths, race conditions.
3. **Security** — authn/authz on new endpoints, ownership checks, input validation at API edge, secret handling, SQL/NoSQL injection, SSRF.
4. **Performance** — N+1 queries, redundant DB round-trips, oversized SELECTs, blocking I/O on async paths, unnecessary serialization/copies.
5. **Duplication & dead code** — copy-pasted blocks, unused functions/classes, shadowed helpers from existing modules.
6. **Style & consistency** — naming, typing, language conventions (see `delivery.md` and any language pack referenced from it), parity with neighbouring code.
7. **Tests** — new branches covered, negative/error paths exercised, no over-mocking that hides regressions.
8. **Migrations** — additive, reversible, no destructive defaults.
9. **Observability** — log/metric coverage for new failure modes.

## Comment Severity
- **CRITICAL** — blocks merge: correctness, security, data loss, plan/spec violation.
- **MAJOR** — should fix; may be deferred with explicit rationale logged.
- **MINOR** — improvement; advisory.
- **NIT** — taste; advisory.

Only CRITICAL drives loop iteration. MAJOR/MINOR/NIT are recorded in the Final Review Summary and may be deferred.

## Per-cycle Caps (early stop signal)
- ≤ 10 CRITICAL and ≤ 15 MAJOR per cycle.
- Exceeding either cap → STOP and escalate to user (signals a plan-level issue).
- If the diff is < 50 changed LoC and stabilization passed clean, the loop MAY skip straight to Final Review Summary with no findings.

## Push-back Protocol
For each CRITICAL the reviewer raises:
1. Implementer addresses the comment OR pushes back with a citation (plan section, spec file, or concrete justification).
2. Reviewer responds with exactly one of:
   - **Accept push-back** — comment dropped; logged in summary with rationale.
   - **Confirm problem** — comment stands; implementer must fix.
3. If the implementer pushes back a second time on a confirmed CRITICAL → STOP and escalate to user.

Every push-back round (accepted or confirmed) MUST appear in the Final Review Summary verbatim — discussion is part of the deliverable.

## Loop Control
- `MAX_REVIEW_CYCLES = 2` (override per task only with explicit justification).
- Cycle k:
  1. Reviewer runs checklist on current diff.
  2. If 0 CRITICAL → exit loop, write Final Review Summary.
  3. Else run push-back protocol per comment.
  4. Implementer fixes confirmed CRITICALs.
  5. Re-run stabilization (`stabilization.md`) on fixes.
  6. Increment k. If k > MAX_REVIEW_CYCLES with any CRITICAL still open → STOP and escalate.

## Escalate Immediately (no further cycles, no extra tokens)
- Finding requires changing `/spec` or the approved plan.
- Same CRITICAL signature reappears after a fix attempt.
- Per-cycle caps exceeded.
- Second push-back on a confirmed CRITICAL.
- Reviewer cannot read a file required to evaluate a comment.

## Final Review Summary (append to `.plans/<branch>.md` before exit, and print in chat)
The reviewer writes the summary to `.plans/<branch>.md` so the next implementer cycle (or the pre-merge WAL distillation) has the full push-back record. It also prints the same summary in chat for the user.
```
## Review Summary (cycles run: <k>/<MAX>)
### Fixed
- <comment> → <change>
### Push-backs accepted by reviewer
- <comment> ← <implementer rationale>
### Push-backs confirmed and fixed
- <comment> ← <implementer rationale> → <change>
### Deferred (MAJOR / MINOR)
- <comment> — <reason, follow-up WAL step if any>
### Open questions (spec / plan)
- <question> — <user decision needed>
### Escalation reason (if loop did not converge)
- <one of: cycles exhausted | second push-back | plan/spec change required | caps exceeded>
```

## Guardrails
- Reviewer does NOT modify code, tests, or specs directly — fixes go through the implementer.
- Reviewer does NOT re-open the plan; plan-level concerns escalate to user.
- Reviewer reads only files relevant to the diff to keep token spend bounded.
- Push-back discussion is mandatory output; never silently drop a CRITICAL.
