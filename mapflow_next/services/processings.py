"""The current project's processings: list, polling, cost, start and per-processing actions."""
from __future__ import annotations

from functools import partial
from typing import Dict, List, Optional, Set

from qgis.PyQt.QtCore import QObject, QTimer, pyqtSignal

from ..api.client import MapflowApi
from ..api.http import ApiError
from ..config import COST_DEBOUNCE_MS, POLL_INTERVAL_MS, PROCESSINGS_PAGE_SIZE
from ..core.draft import RunDraft
from ..core.models import Processing, Project, Status


MAX_PAGE = 100


def _merge(fresh: List[Processing], shown: List[Processing]) -> List[Processing]:
    """The refreshed newest page, then the older processings already shown below it (from "Show more").
    Something deleted inside the refreshed window drops out; older ones stay in place."""
    if len(shown) <= len(fresh):
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
        self._poll.timeout.connect(self.refresh)
        self._cost_timer = QTimer(self)
        self._cost_timer.setSingleShot(True)
        self._cost_timer.setInterval(COST_DEBOUNCE_MS)
        self._cost_timer.timeout.connect(self._ask_cost)
        self._cost_payload: Optional[dict] = None
        self._cost_token = 0
        self._cost_request = 0
        self._loading = False
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
        self.refresh()
        self.changed.emit([])

    def stop(self) -> None:
        self._poll.stop()
        self._cost_timer.stop()

    def refresh(self) -> None:
        if not self.project or self._loading:
            return
        self._loading = True
        project_id = self.project.id
        # The newest processings, as many as are shown (up to the API's page limit); polling keeps them current
        limit = min(max(PROCESSINGS_PAGE_SIZE, len(self.items)), MAX_PAGE)
        self.api.processings(project_id, partial(self._on_list, project_id), partial(self._on_list_error, project_id),
                             limit=limit)

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
            if item.id not in known:
                self.items.append(item)
                self._last_status.setdefault(item.id, item.status)
        self.total = max(total, len(self.items))
        self.changed.emit(self.items)

    def _on_more_error(self, project_id: str, error: ApiError) -> None:
        if self._current(project_id):
            self.loading_more = False
            self.changed.emit(self.items)
            self.actionFailed.emit(f"Couldn't load more processings: {error.message}")

    def _current(self, project_id: str) -> bool:
        return self.project is not None and self.project.id == project_id

    def _on_list(self, project_id: str, items: List[Processing], total: int) -> None:
        if not self._current(project_id):
            return
        self._loading = False
        for item in items:
            before = self._last_status.get(item.id)
            if before is not None and not before.is_terminal and item.status.is_terminal:
                (self.finished if item.status is Status.ok else self.failed).emit(item)
            self._last_status[item.id] = item.status
        self.items, self.total = _merge(items, self.items), total
        self.changed.emit(self.items)
        if any(not p.is_final for p in items):
            self._poll.start()

    def _on_list_error(self, project_id: str, error: ApiError) -> None:
        if not self._current(project_id):
            return
        self._loading = False
        self._poll.start()        # transient errors: try again on the next tick

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
            self.refresh()

        self.api.start(payload, done, lambda error: self.startFailed.emit(error.message))

    def restart(self, processing: Processing) -> None:
        self._last_status[processing.id] = Status.in_progress
        self.started_here.add(processing.id)
        self.api.restart(processing.id, lambda _: self.refresh(), self._action_failed)

    def delete(self, processing: Processing) -> None:
        self.api.delete(processing.id, lambda _: self.refresh(), self._action_failed)

    def rename(self, processing: Processing, name: str, description: str) -> None:
        self.api.rename(processing, name, description, lambda _: self.refresh(), self._action_failed)

    def rate(self, processing: Processing, rating: int, feedback: str = "") -> None:
        self.api.rate(processing.id, rating, feedback, lambda _: None, self._action_failed)

    def _action_failed(self, error: ApiError) -> None:
        self.actionFailed.emit(error.message)
        self.refresh()
