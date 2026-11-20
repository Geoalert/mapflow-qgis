"""The current project's processings: list, polling, cost, start and per-processing actions."""
from __future__ import annotations

from functools import partial
from typing import Dict, List, Optional, Set

from qgis.PyQt.QtCore import QObject, QTimer, pyqtSignal

from ..api.client import MapflowApi
from ..api.http import ApiError
from ..config import COST_DEBOUNCE_MS, POLL_FAILURES_BEFORE_ALERT, POLL_INTERVAL_MS, PROCESSINGS_PAGE_SIZE
from ..core.draft import RunDraft
from ..core.failures import ALERT, LOAD, POLL, STOP, PollFailures, keeps_schedule, poll_notice, stronger
from ..core.models import Processing, Project, Status
from ..core.guard import guarded


MAX_PAGE = 100


def _merge(fresh: List[Processing], shown: List[Processing], complete: bool) -> List[Processing]:
    """The refreshed newest page, then the older processings already shown below it (from "Show more").
    Something deleted inside the refreshed window drops out; older ones stay in place. A `complete` page
    (the project has no more than it holds) is the whole list: nothing shown before survives it."""
    if complete or len(shown) <= len(fresh):
        return list(fresh)
    ids = {p.id for p in fresh}
    oldest = fresh[-1].created if fresh else None
    if oldest is None:
        tail = [p for p in shown[len(fresh):] if p.id not in ids]
    else:
        tail = [p for p in shown if p.id not in ids and (p.created is None or p.created <= oldest)]
    return list(fresh) + tail


class Processings(QObject):
    changed = pyqtSignal(list)              # [Processing], newest first
    started = pyqtSignal(object)            # Processing (may be None if the API answered without one)
    startFailed = pyqtSignal(str)
    finished = pyqtSignal(object)           # a watched processing reached OK
    failed = pyqtSignal(object)             # a watched processing failed
    costReady = pyqtSignal(int, object, str)   # request token, credits or None, error text
    actionFailed = pyqtSignal(str)
    refreshed = pyqtSignal()                # a refresh of the list came back (or failed)
    listFailed = pyqtSignal(str)            # a line for the message bar: the list did not load
    projectGone = pyqtSignal(str, object)   # project id, ApiError: the list answered 403 or 404
    rated = pyqtSignal(str, int)            # processing id, rating: Mapflow saved it

    def __init__(self, api: MapflowApi, parent=None):
        super().__init__(parent)
        self.api = api
        self.project: Optional[Project] = None
        self.items: List[Processing] = []
        self.total = 0
        self._last_status: Dict[str, Status] = {}
        self.started_here: Set[str] = set()
        self._poll = QTimer(self)
        self._poll.setSingleShot(True)
        self._poll.setInterval(POLL_INTERVAL_MS)
        self._poll.timeout.connect(guarded(lambda: self.refresh(POLL)))
        self._cost_timer = QTimer(self)
        self._cost_timer.setSingleShot(True)
        self._cost_timer.setInterval(COST_DEBOUNCE_MS)
        self._cost_timer.timeout.connect(self._ask_cost)
        self._cost_payload: Optional[dict] = None
        self._cost_token = 0
        self._cost_request = 0
        self._loading = False
        self._again: Optional[str] = None       # refresh once more when the request in flight comes back: its trigger
        self.loaded = False                     # a list of this project came back
        self.load_failed = False                # the last answer for this project's list was a failure
        self._poll_failures = PollFailures(POLL_FAILURES_BEFORE_ALERT)
        self._deleted: Set[str] = set()         # gone from Mapflow, though a reply in flight may still list it
        self.loading_more = False

    # ---------- list ----------

    @property
    def loading(self) -> bool:
        """The project's list is on its way and nothing is shown yet."""
        return self._loading and not self.items

    @property
    def has_more(self) -> bool:
        return len(self.items) < self.total

    def set_project(self, project: Optional[Project]) -> None:
        if self.project and project and self.project.id == project.id:
            self.project = project
            return
        self.project = project
        self.items, self._last_status, self.total = [], {}, 0
        self._loading = self.loading_more = False   # a list still loading for the previous project no longer counts
        self.loaded = self.load_failed = False
        self._again = None
        self._poll_failures.succeeded()
        self._poll.stop()
        self.refresh(LOAD)
        self.changed.emit([])

    def stop(self) -> None:
        """Unload: stop the timers and abort the pending requests. Emits nothing: the dock goes too."""
        self._poll.stop()
        self._cost_timer.stop()
        if self._cost_request:
            self.api.abort(self._cost_request)
        self._cost_request = 0
        self._cost_payload = None
        self.api.abort_all()

    def _schedule(self) -> None:
        """The next poll, unless a permanent failure stopped it: that holds until a list loads."""
        if not self._poll_failures.stopped:
            self._poll.start()

    @guarded
    def refresh(self, trigger: str) -> bool:
        """Ask for the newest page. `trigger` (USER, LOAD or POLL) decides who hears of a failure. False if
        there is nothing to ask (no project). While a request is in flight, another follows it: what changed in
        between (a deletion) must show."""
        if not self.project:
            return False
        if self._loading:
            self._again = stronger(self._again, trigger)
            return True
        self._loading = True
        project_id = self.project.id
        # The newest processings, as many as are shown (up to the API's page limit); polling keeps them current
        limit = min(max(PROCESSINGS_PAGE_SIZE, len(self.items)), MAX_PAGE)
        self.api.processings(project_id, partial(self._on_list, project_id, limit),
                             partial(self._on_list_error, project_id, trigger), limit=limit)
        return True

    def load_more(self) -> None:
        """The next page of older processings."""
        if not self.project or self.loading_more or not self.has_more:
            return
        self.loading_more = True
        project_id = self.project.id
        self.api.processings(project_id, partial(self._on_more, project_id), partial(self._on_more_error, project_id),
                             limit=PROCESSINGS_PAGE_SIZE, offset=len(self.items))
        self.changed.emit(self.items)

    def _on_more(self, project_id: str, items: List[Processing], total: int) -> None:
        if not self._current(project_id):
            return
        self.loading_more = False
        known = {p.id for p in self.items}
        for item in items:
            if item.id not in known and item.id not in self._deleted:
                self.items.append(item)
                self._last_status.setdefault(item.id, item.status)
        self.total = max(total, len(self.items))
        self.changed.emit(self.items)

    def _on_more_error(self, project_id: str, error: ApiError) -> None:
        if self._current(project_id):
            self.loading_more = False
            self.changed.emit(self.items)
            if self._is_gone(error):
                self._gone(project_id, error)
            else:
                self.actionFailed.emit(f"Couldn't load more processings: {error.message}")

    def _current(self, project_id: str) -> bool:
        return self.project is not None and self.project.id == project_id

    def _on_list(self, project_id: str, limit: int, items: List[Processing], total: int) -> None:
        if not self._current(project_id):
            return
        self._loading = False
        self.loaded, self.load_failed = True, False
        self._poll_failures.succeeded()
        complete = len(items) < limit          # fewer than asked for: that is all there is
        items = [p for p in items if p.id not in self._deleted]
        for item in items:
            before = self._last_status.get(item.id)
            if before is not None and not before.is_terminal and item.status.is_terminal:
                (self.finished if item.status is Status.ok else self.failed).emit(item)
            self._last_status[item.id] = item.status
        self.items = [p for p in _merge(items, self.items, complete) if p.id not in self._deleted]
        self.total = max(total, len(self.items))
        self.changed.emit(self.items)
        self.refreshed.emit()
        if self._again:
            again, self._again = self._again, None
            self.refresh(again)
        elif any(not p.is_final for p in items):
            self._schedule()

    def _on_list_error(self, project_id: str, trigger: str, error: ApiError) -> None:
        if not self._current(project_id):
            return
        self._loading = False                   # before anything that can raise: the list can be asked for again
        again, self._again = self._again, None
        self.load_failed = True
        self.changed.emit(self.items)           # the page leaves "Loading" and says the list did not load
        self.refreshed.emit()
        if self._is_gone(error):
            self._gone(project_id, error)
            return
        # "auth" is the session's: it renews the token (the poll goes on) or signs out and says so (and stops this
        # poll). It is not counted here and tells the user nothing.
        if trigger == POLL:
            outcome = self._poll_failures.failed(error.kind, error.status)
            if outcome in (ALERT, STOP):
                text = poll_notice(outcome, "processings list", error.message, error.kind)
                if text:
                    self.listFailed.emit(text)
        elif error.kind != "auth":
            self.listFailed.emit(f"Processings didn't load: {error.message}")
        # Spec 002_B: a refresh that failed for a transient reason, or with a 401, is asked again after one poll
        # interval. A permanent failure is not: the poll resumes when a list loads.
        if keeps_schedule(error.kind, error.status):
            self._schedule()
        if again:
            self.refresh(again)

    @staticmethod
    def _is_gone(error: ApiError) -> bool:
        return error.status in (403, 404) or error.kind in ("forbidden", "not_found")

    def _gone(self, project_id: str, error: ApiError) -> None:
        """The open project was deleted or unshared (Mapflow Web): the poll stops and the controller opens
        another project. `stopped` holds until the project changes (`set_project`)."""
        self._poll.stop()
        self._again = None
        self._poll_failures.failed("forbidden", error.status)
        self.projectGone.emit(project_id, error)

    def get(self, processing_id: str) -> Optional[Processing]:
        return next((p for p in self.items if p.id == processing_id), None)

    # ---------- cost ----------

    def request_cost(self, draft: RunDraft, token: int) -> None:
        """Debounced: the form changes in bursts (typing a name, toggling options). The answer
        comes back with `token`, so the caller can drop answers for a form that has changed since."""
        if not self.project:
            return
        self._cost_token = token
        try:
            self._cost_payload = draft.payload(self.project.id, self.api.http.plugin_version)
        except ValueError:
            self._cost_payload = None
            self._cost_timer.stop()
            return
        self._cost_timer.start()

    @guarded
    def _ask_cost(self) -> None:
        if not self._cost_payload:
            return
        if self._cost_request:
            self.api.http.abort(self._cost_request)
        token = self._cost_token
        self._cost_request = self.api.cost(self._cost_payload,
                                           lambda value: self.costReady.emit(token, value, ""),
                                           lambda error: self.costReady.emit(token, None, error.message))

    # ---------- start and actions ----------

    def start(self, draft: RunDraft) -> None:
        payload = draft.payload(self.project.id, self.api.http.plugin_version)

        def done(processing: Optional[Processing]):
            if processing:
                self.started_here.add(processing.id)
                self._last_status[processing.id] = processing.status
            self.started.emit(processing)
            self.refresh(LOAD)

        self.api.start(payload, done, lambda error: self.startFailed.emit(error.message))

    def restart(self, processing: Processing) -> None:
        self._last_status[processing.id] = Status.in_progress
        self.started_here.add(processing.id)
        self.api.restart(processing.id, lambda _: self.refresh(LOAD), self._action_failed)

    def delete(self, processing: Processing) -> None:
        def done(_answer) -> None:
            # Off the list at once: the next page from Mapflow may still be on its way with it
            self._deleted.add(processing.id)
            before = len(self.items)
            self.items = [p for p in self.items if p.id != processing.id]
            self.total = max(self.total - (before - len(self.items)), len(self.items))
            self.changed.emit(self.items)
            self.refresh(LOAD)

        self.api.delete(processing.id, done, self._action_failed)

    def rename(self, processing: Processing, name: str, description: str) -> None:
        self.api.rename(processing, name, description, lambda _: self.refresh(LOAD), self._action_failed)

    def rate(self, processing: Processing, rating: int, feedback: str = "") -> None:
        self.api.rate(processing.id, rating, feedback, lambda _: self.rated.emit(processing.id, rating),
                      self._action_failed)

    def _action_failed(self, error: ApiError) -> None:
        self.actionFailed.emit(error.message)
        self.refresh(LOAD)
