---
description: "Use when planning or changing behavior from specifications: architecture, API contract impacts, data model changes, and WAL step design."
applyTo: "spec/**"
---

# Planning Instructions

## Objective
Produce an implementation-ready plan grounded in `spec/index.md` and related spec files before code changes begin.

## Required Workflow
1. Identify the exact spec documents relevant to the requested change.
2. Detect and report contradictions between spec files or between spec and request.
3. Check specification coverage for the requested behavior.
4. If coverage is incomplete, propose a spec delta in chat and request explicit approval before editing any file under `spec/**`.
5. When adding a new spec document, update `spec/index.md` in the same change.
6. Define acceptance criteria that are testable and map to spec language.
7. Propose implementation steps with risk notes and rollback considerations.
8. Update WAL planning details only after assumptions are explicit.

## Planning Output Format
- Scope: what changes and what stays unchanged
- Spec references: exact files used
- Spec delta (if any): files to add/update and rationale
- Acceptance criteria: concrete and testable
- Proposed steps: ordered, minimal, and reversible
- Risks and assumptions: explicit

## Guardrails
- Do not modify application code in planning-only tasks.
- If a requirement is ambiguous, stop and request clarification.
- Prefer minimal architecture changes over broad refactors unless required by spec.
