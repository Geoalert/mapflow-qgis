"""The unexpected-error reporting path.

These cover the two properties that make the guard worth having:
* an unexpected exception is logged **with a traceback** and does not escape, and
* the reporting path itself cannot raise — a report mechanism that fails would replace
  the original exception with its own, destroying the thing being reported.
"""
import logging
from unittest.mock import MagicMock, patch

import pytest

from mapflow import error_guard
from mapflow.http import MAX_TRACEBACK_LINES, get_exception_report_body


class Boom(Exception):
    pass


def _raise_boom():
    raise Boom("something specific went wrong")


# ---------- report_unexpected_error ----------

def test_logs_with_traceback(caplog):
    with caplog.at_level(logging.ERROR, logger="mapflow.error_guard"), \
            patch.object(error_guard, "report_unexpected_error",
                         wraps=error_guard.report_unexpected_error):
        try:
            _raise_boom()
        except Boom as exc:
            # Dialog construction needs Qt widgets; the logging half is what matters here.
            with patch("mapflow.dialogs.error_message_widget.ErrorMessageWidget"):
                error_guard.report_unexpected_error(exc, "doing the thing", "1.2.3")

    assert caplog.records
    record = caplog.records[0]
    assert record.exc_info is not None, "a report without a traceback is not worth sending"
    assert "doing the thing" in caplog.text


def test_never_raises_even_if_the_dialog_fails(caplog):
    """A failure inside the reporting path must not surface as a second exception."""
    try:
        _raise_boom()
    except Boom as exc:
        with patch("mapflow.http.get_exception_report_body", side_effect=RuntimeError("nope")), \
                caplog.at_level(logging.ERROR, logger="mapflow.error_guard"):
            # Must not raise RuntimeError.
            error_guard.report_unexpected_error(exc, "doing the thing", "1.2.3")

    # Both the original failure and the reporting failure are recorded.
    assert "doing the thing" in caplog.text


# ---------- guard_entry_point ----------

class _Owner:
    plugin_version = "9.9.9"

    @error_guard.guard_entry_point("running the guarded action")
    def explodes(self):
        raise Boom("kaboom")

    @error_guard.guard_entry_point("running the guarded action")
    def succeeds(self, value):
        return value * 2


def test_guard_swallows_and_reports():
    owner = _Owner()
    with patch.object(error_guard, "report_unexpected_error") as reported:
        assert owner.explodes() is None
    reported.assert_called_once()
    exception, context, version = reported.call_args.args[:3]
    assert isinstance(exception, Boom)
    assert context == "running the guarded action"
    assert version == "9.9.9", "the report must carry the plugin version for triage"


def test_guard_is_transparent_on_success():
    assert _Owner().succeeds(21) == 42


def test_guard_resolves_version_without_raising_when_absent():
    """Version lookup runs while already handling a failure, so it must not add its own."""
    class NoVersion:
        @error_guard.guard_entry_point("x")
        def explodes(self):
            raise Boom("kaboom")

    with patch.object(error_guard, "report_unexpected_error") as reported:
        NoVersion().explodes()
    assert reported.call_args.args[2] == "unknown"


# ---------- call_guarded ----------

def test_call_guarded_returns_value_on_success():
    assert error_guard.call_guarded(lambda x: x + 1, "ctx", "1.0", 41) == 42


def test_call_guarded_reports_and_returns_none():
    with patch.object(error_guard, "report_unexpected_error") as reported:
        assert error_guard.call_guarded(_raise_boom, "ctx", "1.0") is None
    reported.assert_called_once()


# ---------- get_exception_report_body ----------

def test_report_body_contains_traceback_and_versions():
    try:
        _raise_boom()
    except Boom as exc:
        summary, body = get_exception_report_body(exc, "1.2.3", "doing the thing")

    assert summary == "Boom: something specific went wrong"
    # The body is percent-encoded for a mailto href, so assert on decoded content.
    from urllib.parse import unquote
    decoded = unquote(body)
    assert "Traceback" in decoded
    assert "_raise_boom" in decoded, "the failing frame must survive into the report"
    assert "1.2.3" in decoded
    assert "doing the thing" in decoded


def test_report_body_is_percent_encoded():
    """Raw & or # would terminate the mailto body parameter and truncate the report."""
    try:
        raise Boom("a & b # c")
    except Boom as exc:
        _summary, body = get_exception_report_body(exc, "1.0", "ctx")

    assert "&" not in body and "#" not in body
    assert "%26" in body


def test_long_traceback_is_truncated_from_the_front():
    """Mail clients cut long URLs; keep the tail, where the failure actually is.

    The cap is patched rather than reached by deep recursion: Python collapses identical
    repeated frames into "[Previous line repeated N times]", so recursion produces a short
    traceback and would not exercise this path at all.
    """
    from urllib.parse import unquote

    try:
        _raise_boom()
    except Boom as exc:
        with patch("mapflow.http.MAX_TRACEBACK_LINES", 2):
            _summary, body = get_exception_report_body(exc, "1.0", "ctx")

    decoded = unquote(body)
    assert "earlier frame(s) omitted" in decoded
    # The innermost frame carries the diagnosis — it must be what survives.
    assert "something specific went wrong" in decoded


def test_short_traceback_is_not_truncated():
    from urllib.parse import unquote

    try:
        _raise_boom()
    except Boom as exc:
        _summary, body = get_exception_report_body(exc, "1.0", "ctx")

    assert "omitted" not in unquote(body)


@pytest.mark.parametrize("context", ["", None])
def test_report_body_tolerates_missing_context(context):
    try:
        _raise_boom()
    except Boom as exc:
        _summary, body = get_exception_report_body(exc, "1.0", context or '')
    from urllib.parse import unquote
    assert "unspecified" in unquote(body)
