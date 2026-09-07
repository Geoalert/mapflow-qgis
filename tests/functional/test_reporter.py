"""The report tier (`mapflow/infra/reporter.py`): one throttle for both report paths.

Step 1 of the error-reporting phase's behaviour half. The HTTP report path used to be unthrottled —
a recurring poll error could stack a dialog every few seconds. It now shares the exception path's
suppression budget, keyed on a per-failure signature, with the suppressed count carried into both
the dialog text and the report body. These run in the no-QGIS functional tier: the throttle and the
signature are Qt-free; the dialog itself is patched out.
"""
from unittest.mock import MagicMock, patch

import pytest

from mapflow.infra import reporter
from mapflow.http import response_signature
from mapflow.infra.report_body import get_error_report_body
from mapflow.report_throttle import ReportThrottle


def _response(path="/rasters/mosaic", code=299, http_code=400):
    response = MagicMock()
    response.error.return_value = code
    response.request.return_value.url.return_value.path.return_value = path
    response.attribute.return_value = http_code
    return response


class _FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


@pytest.fixture(autouse=True)
def fresh_throttle(monkeypatch):
    """A private budget per test — the production throttle is process-wide."""
    monkeypatch.setattr(reporter, "_throttle", ReportThrottle())


# ---------- the signature (spec/006 § Volume limit) ----------

def test_the_signature_is_the_qt_code_and_the_query_free_path():
    assert response_signature(_response("/rasters/mosaic", code=299)) == "299@/rasters/mosaic"


def test_a_different_path_or_code_is_a_different_signature():
    base = response_signature(_response("/rasters/mosaic", code=299))
    assert response_signature(_response("/rasters/image", code=299)) != base
    assert response_signature(_response("/rasters/mosaic", code=203)) != base


# ---------- the HTTP path is now throttled ----------

def test_a_repeated_http_error_shows_one_dialog():
    """The whole point of step 1: a poll error must not open a dialog every tick."""
    with patch.object(reporter, "_present") as present:
        for _ in range(20):
            reporter.report_http_error(_response(), "1.0", response_body="{}")
    assert present.call_count == 1


def test_the_dialog_returns_after_the_window():
    clock = _FakeClock()
    reporter._throttle = ReportThrottle(first_window=60.0, global_floor=0.0, clock=clock)
    with patch.object(reporter, "_present") as present:
        reporter.report_http_error(_response(), "1.0", response_body="{}")
        for _ in range(5):
            reporter.report_http_error(_response(), "1.0", response_body="{}")
        clock.now += 61.0
        reporter.report_http_error(_response(), "1.0", response_body="{}")
    assert present.call_count == 2


def test_the_suppressed_count_reaches_the_dialog_text():
    clock = _FakeClock()
    reporter._throttle = ReportThrottle(first_window=60.0, global_floor=0.0, clock=clock)
    with patch.object(reporter, "_present") as present, \
            patch("mapflow.infra.reporter.get_error_report_body", return_value=("Server said no", "body")):
        for _ in range(5):  # one shown, four suppressed
            reporter.report_http_error(_response(), "1.0", response_body="{}")
        clock.now += 61.0
        reporter.report_http_error(_response(), "1.0", response_body="{}")

    second_text = present.call_args.kwargs["text"]
    assert "4 more time(s)" in second_text


def test_the_log_records_every_occurrence_even_when_suppressed(caplog):
    import logging
    with patch.object(reporter, "_present"), \
            caplog.at_level(logging.ERROR, logger="mapflow.infra.reporter"):
        for _ in range(20):
            reporter.report_http_error(_response(), "1.0", response_body="{}")
    # 20 logged, 1 shown: suppression governs the dialog, never the log.
    assert sum("HTTP error:" in r.message for r in caplog.records) == 20


# ---------- the global floor spans BOTH report paths (the shared-throttle proof) ----------

def test_an_http_report_and_an_exception_report_share_the_10s_floor():
    """The decisive reason both paths live behind one throttle: a floor that held per-tier would
    let an HTTP error and an exception both fire inside the 10s floor through the same poll tick."""
    clock = _FakeClock()
    reporter._throttle = ReportThrottle(global_floor=10.0, clock=clock)
    with patch.object(reporter, "_present") as present:
        reporter.report_http_error(_response(), "1.0", response_body="{}")   # shown
        try:
            raise ValueError("a different failure entirely")
        except ValueError as exc:
            reporter.report_unexpected_error(exc, "polling", "1.0")          # within the floor
    assert present.call_count == 1  # the second is suppressed by the shared floor


# ---------- the report body carries the query-free path (spec + privacy) ----------

def test_the_report_body_carries_the_query_free_path():
    from urllib.parse import unquote
    response = _response(path="/rasters/mosaic", http_code=400)
    _summary, body = get_error_report_body(response, '{"message": "no"}', "1.0")
    decoded = unquote(body)
    assert "/rasters/mosaic" in decoded


def test_the_report_body_states_how_many_http_repeats_were_suppressed():
    from urllib.parse import unquote
    _summary, body = get_error_report_body(_response(), '{"message": "no"}', "1.0",
                                           suppressed_count=41)
    assert "41" in unquote(body) and "suppressed" in unquote(body)
