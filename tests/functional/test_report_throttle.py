"""Suppression policy for repeated error reports.

The property under test is bounded dialog volume: a failure that fires on a 6-second timer
must not produce a 6-second dialog cadence, while a failure the user has not seen yet must
still get through. Time is injected rather than slept — the windows are minutes long.
"""
import pytest

from mapflow.report_throttle import ReportThrottle, exception_signature


class Boom(Exception):
    pass


class OtherBoom(Exception):
    pass


class FakeClock:
    """Monotonic clock the test drives by hand."""

    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def throttle(clock):
    return ReportThrottle(first_window=60.0, max_window=480.0, global_floor=10.0, clock=clock)


# ---------- exception_signature ----------

def _raise_boom(message="id=8f21e0 failed"):
    raise Boom(message)


def _raise_boom_elsewhere():
    raise Boom("id=8f21e0 failed")


def _capture(func) -> BaseException:
    try:
        func()
    except Exception as exception:
        return exception
    raise AssertionError("expected the helper to raise")


def test_the_message_does_not_change_the_signature():
    """Messages embed ids; keying on them would let one bug report on every poll tick."""
    first = _capture(lambda: _raise_boom("id=8f21e0 failed"))
    second = _capture(lambda: _raise_boom("id=c74b19 failed"))
    assert exception_signature(first) == exception_signature(second)


def test_the_same_exception_from_a_different_line_is_a_different_signature():
    """Two unrelated bugs of the same type must not silence each other."""
    assert exception_signature(_capture(_raise_boom)) \
        != exception_signature(_capture(_raise_boom_elsewhere))


def test_different_exception_types_differ():
    def raise_other():
        raise OtherBoom("boom")

    assert exception_signature(_capture(_raise_boom)) != exception_signature(_capture(raise_other))


def test_signature_survives_a_missing_traceback():
    """Exceptions constructed but never raised have no traceback; reporting must not break."""
    assert exception_signature(Boom("never raised")) == "Boom"


# ---------- suppression ----------

def test_first_occurrence_is_reported(throttle):
    assert throttle.should_report("sig") == 0


def test_immediate_repeat_is_suppressed(throttle, clock):
    throttle.should_report("sig")
    clock.advance(6.0)  # PROCESSING_TABLE_REFRESH_INTERVAL
    assert throttle.should_report("sig") is None


def test_a_six_second_poll_yields_a_handful_of_dialogs(throttle, clock):
    """The failure this whole module exists for: a bug on the processings poll."""
    reports = 0
    for _ in range(60):  # six minutes at PROCESSING_TABLE_REFRESH_INTERVAL
        if throttle.should_report("sig") is not None:
            reports += 1
        clock.advance(6.0)
    # Shown at 0s, 60s and 180s as the window doubles 60 -> 120 -> 240.
    assert reports == 3


def test_report_after_the_window_carries_the_suppressed_count(throttle, clock):
    throttle.should_report("sig")
    for _ in range(5):
        clock.advance(6.0)
        assert throttle.should_report("sig") is None
    clock.advance(60.0)
    assert throttle.should_report("sig") == 5


def test_the_count_resets_after_it_is_reported(throttle, clock):
    throttle.should_report("sig")
    clock.advance(30.0)
    throttle.should_report("sig")  # suppressed, count 1
    clock.advance(60.0)
    assert throttle.should_report("sig") == 1
    clock.advance(300.0)
    assert throttle.should_report("sig") == 0


def test_the_window_doubles_up_to_the_cap(throttle, clock):
    throttle.should_report("sig")          # window 60
    clock.advance(60.0)
    throttle.should_report("sig")          # shown, window -> 120
    clock.advance(61.0)
    assert throttle.should_report("sig") is None, "61s is inside the 120s window"
    clock.advance(60.0)
    throttle.should_report("sig")          # shown at 121s, window -> 240

    clock.advance(240.0)
    throttle.should_report("sig")          # shown, window -> 480 (the cap)
    clock.advance(480.0)
    throttle.should_report("sig")          # shown, window stays 480
    clock.advance(480.0)
    assert throttle.should_report("sig") == 0, "the cap must stop the doubling"


# ---------- the global floor ----------

def test_a_different_failure_is_held_back_by_the_global_floor(throttle, clock):
    """Distinct exceptions rotating through one poll callback would otherwise still storm."""
    assert throttle.should_report("first") == 0
    clock.advance(6.0)
    assert throttle.should_report("second") is None


def test_a_different_failure_passes_once_the_floor_has_elapsed(throttle, clock):
    throttle.should_report("first")
    clock.advance(11.0)
    assert throttle.should_report("second") == 0


def test_the_floor_still_counts_what_it_hides(throttle, clock):
    throttle.should_report("first")
    clock.advance(1.0)
    assert throttle.should_report("second") is None
    clock.advance(20.0)
    assert throttle.should_report("second") == 1


def test_three_alternating_failures_stay_bounded(throttle, clock):
    reports = 0
    for index in range(60):  # six minutes of a 6-second poll cycling three bugs
        if throttle.should_report(f"sig-{index % 3}") is not None:
            reports += 1
        clock.advance(6.0)
    assert reports <= 12, "the point of the floor is that this cannot approach 60"
