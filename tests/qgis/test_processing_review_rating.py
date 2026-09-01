"""QGIS-tier tests for rating a processing and reviewing one.

These had no direct tests while they lived in `mapflow.py` — the move is what makes them testable,
because the requests now go through `ProcessingApi` instead of a hand-built URL on `Http`, and the
widget reads are `ProcessingView`'s.

The split under test: `ProcessingService` decides whether a processing can be rated or reviewed and
issues the request; `ProcessingController` gathers what lives in widgets (which star, what feedback,
the review dialog's comment) and hands it over; `ProcessingView` writes to the panel.
"""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from PyQt5.QtCore import QObject

from mapflow.functional.controller.processing_controller import ProcessingController
from mapflow.functional.service import processing_service as ps_mod
from mapflow.functional.service.processing_service import ProcessingService


def _processing(is_ok=True, in_review=True, is_failed=False, is_cancelled=False):
    return SimpleNamespace(
        id="p-1",
        name="Run 1",
        status=SimpleNamespace(is_ok=is_ok, is_failed=is_failed, is_cancelled=is_cancelled),
        reviewStatus=SimpleNamespace(is_in_review=in_review),
    )


def _service(processing=None):
    service = ProcessingService.__new__(ProcessingService)
    QObject.__init__(service)  # the panel updates are signals
    service.tr = lambda text: text
    service.api = MagicMock()
    service.processing_fetch_timer = MagicMock()
    service.selected_processing = MagicMock(return_value=processing)
    return service


def _response(payload):
    reply = MagicMock()
    reply.readAll.return_value.data.return_value = (
        payload if isinstance(payload, bytes) else json.dumps(payload).encode())
    return reply


@pytest.fixture
def alerts(monkeypatch):
    """Everything the service told the user, in order."""
    said = []
    monkeypatch.setattr(ps_mod, "alert", lambda message, *a, **k: said.append(message))
    monkeypatch.setattr(ps_mod, "alert_info", lambda message, *a, **k: said.append(message))
    return said


# ---------- showing the rating a processing already has ----------

def test_loading_a_rating_shows_the_name_before_the_request_answers():
    """Otherwise the panel keeps the previous processing's name until the response lands."""
    service = _service(_processing())
    shown = []
    service.ratingLoaded.connect(lambda name, rating, feedback: shown.append((name, rating, feedback)))

    service.load_current_rating()

    assert shown == [("Run 1", 0, "")]
    assert service.api.get_processing.call_args.kwargs["processing_id"] == "p-1"


def test_loading_a_rating_without_a_selection_asks_nothing():
    service = _service(None)

    service.load_current_rating()

    service.api.get_processing.assert_not_called()


def test_the_stored_rating_reaches_the_panel():
    service = _service(_processing())
    shown = []
    service.ratingLoaded.connect(lambda name, rating, feedback: shown.append((name, rating, feedback)))

    service.load_current_rating_callback(
        _response({"name": "Run 1", "rating": {"rating": 4, "feedback": "good"}}))

    assert shown == [("Run 1", 4, "good")]


def test_an_unrated_processing_leaves_the_panel_alone():
    service = _service(_processing())
    shown = []
    service.ratingLoaded.connect(lambda *a: shown.append(a))

    service.load_current_rating_callback(_response({"name": "Run 1", "rating": None}))

    assert shown == []


def test_a_body_that_is_not_json_does_not_raise():
    service = _service(_processing())

    service.load_current_rating_callback(_response(b"not json"))  # must not raise


# ---------- rating ----------

def test_rating_a_finished_processing_sends_the_score_and_the_feedback():
    service = _service(_processing())

    service.submit_rating(4, "nice")

    kwargs = service.api.rate_processing.call_args.kwargs
    assert kwargs["processing_id"] == "p-1"
    assert kwargs["rating"] == 4
    assert kwargs["feedback"] == "nice"


def test_an_unfinished_processing_cannot_be_rated(alerts):
    service = _service(_processing(is_ok=False))

    service.submit_rating(4, "")

    service.api.rate_processing.assert_not_called()
    assert alerts == ["Only finished processings can be rated"]


def test_no_star_picked_sends_nothing(alerts):
    """The combo's 'None' row resolves to 6, which is out of range."""
    service = _service(_processing())

    service.submit_rating(6, "")

    service.api.rate_processing.assert_not_called()


def test_the_thank_you_depends_on_whether_feedback_was_written(alerts):
    service = _service(_processing())
    service.load_current_rating = MagicMock()

    service.submit_rating_callback(_response({}), feedback="")
    service.submit_rating_callback(_response({}), feedback="useful")

    assert "would appreciate" in alerts[0]
    assert "rating and feedback are submitted" in alerts[1]
    # The panel is refreshed so it shows what was just submitted.
    assert service.load_current_rating.call_count == 2


# ---------- review ----------

def test_accepting_a_review_sends_the_acceptation():
    service = _service(_processing())

    service.accept_processing()

    assert service.api.accept_processing.call_args.kwargs["processing_id"] == "p-1"


def test_a_processing_not_awaiting_review_cannot_be_accepted(alerts):
    service = _service(_processing(in_review=False))

    service.accept_processing()

    service.api.accept_processing.assert_not_called()
    assert alerts == ["Processing must be in `Review required` status"]


def test_rejecting_sends_the_comment_and_the_corrections():
    service = _service(_processing())

    service.reject_processing("p-1", comment="please redo", features={"type": "FeatureCollection"})

    kwargs = service.api.reject_processing.call_args.kwargs
    assert kwargs["comment"] == "please redo"
    assert kwargs["features"] == {"type": "FeatureCollection"}


def test_a_finished_review_clears_the_box_and_refreshes_the_list():
    service = _service(_processing())
    events = []
    service.reviewSubmitted.connect(lambda: events.append("submitted"))
    service.refreshRequested.connect(lambda: events.append("refresh"))

    service.review_processing_callback(_response({}))

    assert events == ["submitted", "refresh"]
    service.processing_fetch_timer.start.assert_called_once()


# ---------- the controller: widget reads and the enable/disable decision ----------

def _controller(processing=None, review_workflow=False, can_review=True, can_start=True):
    controller = ProcessingController.__new__(ProcessingController)
    QObject.__init__(controller)
    controller.tr = lambda text: text
    controller.processing_service = MagicMock()
    controller.processing_service.selected_processing.return_value = processing
    controller.processing_view = MagicMock()
    controller.processing_view.rating_is_selected.return_value = True
    controller.review_dialog = MagicMock()
    controller.app_context = SimpleNamespace(
        review_workflow_enabled=review_workflow,
        user_role=SimpleNamespace(can_delete_rename_review_processing=can_review,
                                  can_start_processing=can_start,
                                  value="contributor"))
    return controller


def test_the_controller_reads_the_star_and_the_feedback_off_the_panel():
    controller = _controller(_processing())
    controller.processing_view.selected_rating.return_value = 5
    controller.processing_view.rating_feedback.return_value = "great"

    controller.submit_rating()

    controller.processing_service.submit_rating.assert_called_once_with(5, "great")


def test_the_review_dialog_opens_only_for_a_reviewable_processing():
    controller = _controller()
    controller.processing_service._reviewable_processing.return_value = None

    controller.show_review_dialog()

    controller.review_dialog.show.assert_not_called()


def test_the_review_dialog_opens_for_the_processing_the_service_approved():
    controller = _controller()
    processing = _processing()
    controller.processing_service._reviewable_processing.return_value = processing

    controller.show_review_dialog()

    controller.review_dialog.setup.assert_called_once_with(processing)
    controller.review_dialog.show.assert_called_once()


def test_review_workflow_enables_the_review_controls_not_the_rating():
    controller = _controller(_processing(), review_workflow=True)

    controller.refresh_feedback_controls()

    controller.processing_view.enable_review.assert_called_once()
    assert controller.processing_view.enable_review.call_args.args[0] is True
    controller.processing_view.enable_rating.assert_not_called()


def test_without_the_review_workflow_the_rating_controls_are_used():
    controller = _controller(_processing(), review_workflow=False)

    controller.refresh_feedback_controls()

    controller.processing_view.enable_rating.assert_called_once()
    controller.processing_view.enable_review.assert_not_called()


def test_a_role_without_review_rights_is_told_why_rating_is_blocked():
    controller = _controller(_processing(), can_review=False)

    controller.refresh_feedback_controls()

    reason = controller.processing_view.enable_rating.call_args.kwargs["reason"]
    assert "Not enough rights" in reason


def test_no_selection_disables_the_controls_and_says_so():
    controller = _controller(None)

    controller.refresh_feedback_controls()

    kwargs = controller.processing_view.enable_rating.call_args.kwargs
    assert kwargs["can_interact"] is False
    assert kwargs["reason"] == "Please select processing"
    # Nothing to restart when nothing is selected.
    controller.processing_view.enable_restart_action.assert_not_called()


def test_a_failed_processing_offers_restart_to_a_role_that_may_start_one():
    controller = _controller(_processing(is_ok=False, is_failed=True))

    controller.refresh_feedback_controls()

    controller.processing_view.enable_restart_action.assert_called_once_with(True)
