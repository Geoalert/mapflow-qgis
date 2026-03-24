# 005 Interactions

## Purpose
Describe integration boundaries and interaction rules with external/internal systems.

## Template
- Actor/system:
- Direction (inbound/outbound):
- Protocol:
- Auth/security:
- Retry/timeout/idempotency:
- Failure handling:

## Sample
Actor/system: AI coding agent.
Direction: Outbound to local tools and version control.
Protocol: Workspace file tools + terminal commands.
Auth/security: Follow local machine auth context and least privilege.
Retry/timeout/idempotency: Retry read operations safely; avoid destructive retries.
Failure handling: Stop on policy/spec contradictions and request user decision.
