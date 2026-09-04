"""Infrastructure tier (`spec/007_architecture.md`).

Modules every layer may import and that may hold Qt: the message tier (`alert_service`) and, as the
error-reporting phase and Phase D fill it in, the report tier. It exists because a service may not
import a widget yet the message/report tiers must build one, and a view may not import a service yet
views legitimately raise alerts — `infra/` is the one layer reachable from services, views, apis and
controllers alike.
"""
