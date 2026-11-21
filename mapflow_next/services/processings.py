"""The current project's processings: list, polling, cost, start and per-processing actions."""
from __future__ import annotations

from functools import partial
from typing import Dict, List, Optional, Set

from qgis.PyQt.QtCore import QObject, QTimer, pyqtSignal

from ..api.client import MapflowApi
from ..api.http import ApiError
from ..config import COST_DEBOUNCE_MS, POLL_FAILURES_BEFORE_ALERT, POLL_INTERVAL_MS, PROCESSINGS_PAGE_SIZE
from ..core.draft import RunDraft
from ..core.failures import ALERT, LOAD, POLL, STOP, USER, PollFailures, keeps_schedule, poll_notice, stronger
from ..core.models import PlannedProcessing, Processing, Project, Status
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


class _Listing:
    """One list of the project's processings, with its own pages: the rows loaded, how many there are in all, and
    what is in flight. The `token` changes when the list is reset: an answer asked for before it is dropped."""

    def __init__(self):
        self.items: List[Processing] = []
        self.total = 0
        self.loaded = False                     # a list of this project came back
        self.failed = False                     # the last answer for this list was a failure
        self.loading = False
        self.loading_more = False
        self.active = False                     # the last refreshed page holds a processing that is not final
        self.again: Optional[str] = None        # refresh once more when the request in flight comes back: its trigger
        self.token = 0
        self.failures = PollFailures(POLL_FAILURES_BEFORE_ALERT)

    def reset(self) -> None:
        self.token += 1
        self.items, self.total = [], 0
        self.loaded = self.failed = self.loading = self.loading_more = self.active = False
        self.again = None
        self.failures.succeeded()

    @property
    def has_more(self) -> bool:
        return len(self.items) < self.total


class Processings(QObject):
    changed = pyqtSignal(list)              # [Processing] of the full listing, newest first
    foundChanged = pyqtSignal(list)         # [Processing] of the search (the matches of `terms`), newest first
    started = pyqtSignal(object)            # Processing (may be None if the API answered without one)
    startFailed = pyqtSignal(str)
    finished = pyqtSignal(object)           # a watched processing reached OK
    failed = pyqtSignal(object)             # a watched processing failed
    costReady = pyqtSignal(int, object, str)   # request token, credits or None, error text
    actionFailed = pyqtSignal(str)
    refreshed = pyqtSignal()                # a refresh of a list came back (or failed)
    listFailed = pyqtSignal(str)            # a line for the message bar: a list did not load
    projectGone = pyqtSignal(str, object)   # project id, ApiError: a list answered 403 or 404
    rated = pyqtSignal(str, int)            # processing id, rating: Mapflow saved it
    plannedChanged = pyqtSignal(list)       # [PlannedProcessing] of the open project, in Mapflow's order

    def __init__(self, api: MapflowApi, parent=None):
        super().__init__(parent)
        self.api = api
        self.project: Optional[Project] = None
        self._full = _Listing()                 # the whole project, newest first: what the Start tab reads
        self._found = _Listing()                # the matches of `terms`: a search is a listing of its own
        self.terms = ""                         # the name search on screen; empty: the full listing is shown
        self.opened: Optional[Processing] = None    # fetched by id for "Show": it is not on the loaded pages
        self._open_token = 0                    # moves on every `open()` and on a new project: older answers drop
        self._opened_refresh = 0                # the newest refresh of `opened`: older answers are dropped
        # The status of each processing a list or the opened card has shown. Every list and the opened card write it
        # and send notices. A processing in two places still gives one notice: the first one that sees the change
        # writes the final status here, so the second sends nothing.
        self._last_status: Dict[str, Status] = {}
        self.started_here: Set[str] = set()
        self._poll = QTimer(self)
        self._poll.setSingleShot(True)
        self._poll.setInterval(POLL_INTERVAL_MS)
        self._poll.timeout.connect(guarded(self._tick))
        self._cost_timer = QTimer(self)
        self._cost_timer.setSingleShot(True)
        self._cost_timer.setInterval(COST_DEBOUNCE_MS)
        self._cost_timer.timeout.connect(self._ask_cost)
        self._cost_payload: Optional[dict] = None
        self._cost_token = 0
        self._cost_request = 0
        self._gone_id: Optional[str] = None     # the project whose 403 or 404 was reported
        self._deleted: Set[str] = set()         # gone from Mapflow, though a reply in flight may still list it
        self._restarting: Set[str] = set()      # restarts sent and not answered: no second one for the same processing
        self._told = False                      # the failure of this round of list requests was said
        # The planned processings are no listing: they have no pages, no poll and no failure count. They load with
        # each refresh of the full listing, and a failure only empties them.
        self._planned: List[PlannedProcessing] = []
        self._planned_seq = 0                   # the newest request for them: an older answer is dropped

    # ---------- the full listing ----------

    @property
    def items(self) -> List[Processing]:
        return self._full.items

    @items.setter
    def items(self, value: List[Processing]) -> None:
        self._full.items = value

    @property
    def total(self) -> int:
        return self._full.total

    @total.setter
    def total(self, value: int) -> None:
        self._full.total = value

    @property
    def loaded(self) -> bool:
        return self._full.loaded

    @property
    def load_failed(self) -> bool:
        return self._full.failed

    @property
    def loading_more(self) -> bool:
        return self._full.loading_more

    @property
    def _loading(self) -> bool:
        return self._full.loading

    @property
    def _poll_failures(self) -> PollFailures:
        return self._full.failures

    @property
    def loading(self) -> bool:
        """The project's list is on its way and nothing is shown yet."""
        return self._full.loading and not self._full.items

    @property
    def has_more(self) -> bool:
        return self._full.has_more

    # ---------- the search listing ----------

    @property
    def found(self) -> List[Processing]:
        return self._found.items

    @property
    def found_total(self) -> int:
        return self._found.total

    @property
    def found_loaded(self) -> bool:
        return self._found.loaded

    @property
    def found_failed(self) -> bool:
        return self._found.failed

    @property
    def found_loading(self) -> bool:
        return self._found.loading and not self._found.items

    @property
    def found_loading_more(self) -> bool:
        return self._found.loading_more

    @property
    def found_has_more(self) -> bool:
        return self._found.has_more

    # ---------- the planned processings ----------

    @property
    def planned(self) -> List[PlannedProcessing]:
        return self._planned

    def _ask_planned(self) -> None:
        self._planned_seq += 1
        seq, project_id, token = self._planned_seq, self.project.id, self._full.token

        def current() -> bool:
            return seq == self._planned_seq and self._current(self._full, project_id, token)

        def done(items: List[PlannedProcessing]) -> None:
            if current():
                self._planned = items
                self.plannedChanged.emit(items)

        def failed(_error: ApiError) -> None:
            # No message, and not the project's 403 or 404: the rows only go
            if current() and self._planned:
                self._planned = []
                self.plannedChanged.emit([])

        self.api.planned_processings(project_id, done, failed)

    def set_project(self, project: Optional[Project]) -> None:
        if self.project and project and self.project.id == project.id:
            self.project = project
            return
        self.project = project
        self.terms = ""
        self.opened = None
        self._open_token += 1
        self._gone_id = None
        self._full.reset()                      # a list still loading for the previous project no longer counts
        self._found.reset()
        self._last_status = {}
        self._planned, self._planned_seq = [], self._planned_seq + 1
        self._poll.stop()
        self.refresh(LOAD)
        self.changed.emit([])
        self.plannedChanged.emit([])
        self.foundChanged.emit([])

    def set_terms(self, terms: str) -> None:
        """Search the project's processings by name on the server; empty returns to the full listing, which stays
        loaded and keeps its poll meanwhile. The matches of the old terms leave at once, and an answer still on its
        way for them is dropped."""
        terms = terms.strip()
        if terms == self.terms:
            return
        self.terms = terms
        was_loading = self._found.loading
        self._found.reset()
        if was_loading:
            self._settle()                      # its answer is dropped now: it can no longer end a Refresh
        if not self.project:
            return
        self.foundChanged.emit(self.found)
        if terms:
            self.refresh_search(USER)           # the user waits on it: a failure shows at once

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
        if not self._full.failures.stopped:
            self._poll.start()

    def _tick(self) -> None:
        self.refresh(POLL)
        if self.terms and not self._found.failures.stopped:
            self.refresh_search(POLL)
        if self.opened is not None and not self.opened.is_final:
            self._refresh_opened()

    def _watching(self) -> bool:
        """A processing of the full listing, of the search listing in use, or the opened card is not final: the poll
        goes on."""
        return (self._full.active or bool(self.terms and self._found.active and not self._found.failures.stopped)
                or (self.opened is not None and not self.opened.is_final))

    def _resume_poll(self) -> None:
        """Start the poll when something watched needs it and it is not running: an old processing in progress that
        "Show" opened, while the loaded pages are final."""
        if self._watching() and not self._poll.isActive():
            self._schedule()

    def _note(self, item: Processing, authority: bool = False) -> None:
        """The status of a watched processing, from any list or the opened card. The first one that sees it reach a
        final status gives the notice and writes the status; the others find it written and send nothing. Only the
        full listing (`authority`) may move a final status back to a running one (a restart in Mapflow Web): an
        older answer of the search or of the opened card must not, or the next answer would give the notice again."""
        before = self._last_status.get(item.id)
        if before is not None and before.is_terminal and not item.status.is_terminal and not authority:
            return
        self._last_status[item.id] = item.status
        if before is not None and not before.is_terminal and item.status.is_terminal:
            (self.finished if item.status is Status.ok else self.failed).emit(item)

    def refresh_shown(self, trigger: str) -> bool:
        """Refresh what the page may show: the full listing, and the search when there is one. False if there is
        nothing to ask (no project)."""
        asked = self.refresh(trigger)
        if self.terms:
            self.refresh_search(trigger)
        if asked:
            self._refresh_opened()
        return bool(asked)

    def _refresh_opened(self) -> None:
        """Ask again for the card fetched by "Show": it is on no list, so no list refresh reaches it. A failure is
        only logged: the card stays as it was, and the next refresh asks again."""
        if not self.project or self.opened is None:
            return
        self._opened_refresh += 1
        token, processing_id, project_id = self._opened_refresh, self.opened.id, self.project.id

        def done(fresh: Processing) -> None:
            if token != self._opened_refresh or not self.project or self.project.id != project_id:
                return
            if self.opened is None or self.opened.id != processing_id:
                return
            if any(p.id == fresh.id for p in self._full.items):
                return                          # it is on the loaded pages now: the listed copy is shown
            self._note(fresh)
            self.opened = fresh
            self.changed.emit(self._full.items)
            self._resume_poll()

        self.api.processing(processing_id, done)

    @guarded
    def refresh(self, trigger: str) -> bool:
        """Ask for the newest page of the full listing. `trigger` (USER, LOAD or POLL) decides who hears of a
        failure. False if there is nothing to ask (no project). While a request is in flight, another follows it:
        what changed in between (a deletion) must show."""
        return self._refresh(self._full, trigger)

    @guarded
    def refresh_search(self, trigger: str) -> bool:
        """Ask for the newest page of the matches of `terms`. A search that failed or that was refreshed in the
        poll tells the user as a list of its own does."""
        return self._refresh(self._found, trigger)

    def _refresh(self, listing: _Listing, trigger: str) -> bool:
        if not self.project or (listing is self._found and not self.terms):
            return False
        if listing.loading:
            listing.again = stronger(listing.again, trigger)
            return True
        if not (self._full.loading or self._found.loading):
            self._gone_id = None                # a new round of requests reports a 403 or a 404 again
            self._told = False                  # ...and a failure again
        listing.loading = True
        project_id, token = self.project.id, listing.token
        # The newest processings, as many as are shown (up to the API's page limit); polling keeps them current
        limit = min(max(PROCESSINGS_PAGE_SIZE, len(listing.items)), MAX_PAGE)
        self.api.processings(project_id, partial(self._on_page, listing, project_id, token, limit),
                             partial(self._on_page_error, listing, project_id, token, trigger), limit=limit,
                             terms=self.terms if listing is self._found else "")
        if listing is self._full:
            self._ask_planned()
        return True

    def load_more(self) -> None:
        """The next page of older processings of the list on screen: the matches, while a search is shown."""
        listing = self._found if self.terms else self._full
        if not self.project or listing.loading_more or not listing.has_more:
            return
        listing.loading_more = True
        project_id, token = self.project.id, listing.token
        self.api.processings(project_id, partial(self._on_more, listing, project_id, token),
                             partial(self._on_more_error, listing, project_id, token),
                             limit=PROCESSINGS_PAGE_SIZE, offset=len(listing.items),
                             terms=self.terms if listing is self._found else "")
        self._emit(listing)

    def _emit(self, listing: _Listing) -> None:
        (self.foundChanged if listing is self._found else self.changed).emit(listing.items)

    def _on_more(self, listing: _Listing, project_id: str, token: int, items: List[Processing], total: int) -> None:
        if not self._current(listing, project_id, token):
            return
        listing.loading_more = False
        known = {p.id for p in listing.items}
        for item in items:
            if item.id not in known and item.id not in self._deleted:
                listing.items.append(item)
                self._last_status.setdefault(item.id, item.status)
        listing.total = max(total, len(listing.items))
        if listing is self._full:
            self._drop_opened_if_listed()
        self._emit(listing)

    def _on_more_error(self, listing: _Listing, project_id: str, token: int, error: ApiError) -> None:
        if self._current(listing, project_id, token):
            listing.loading_more = False
            self._emit(listing)
            if self._is_gone(error):
                self._gone(project_id, error)
            else:
                self.actionFailed.emit(f"Couldn't load more processings: {error.message}")

    def _current(self, listing: _Listing, project_id: str, token: int) -> bool:
        """An answer counts only for the project and the list state it was asked for."""
        return self.project is not None and self.project.id == project_id and listing.token == token

    def _on_page(self, listing: _Listing, project_id: str, token: int, limit: int, items: List[Processing],
                 total: int) -> None:
        if not self._current(listing, project_id, token):
            return
        listing.loading = False
        listing.loaded, listing.failed = True, False
        listing.failures.succeeded()
        complete = len(items) < limit          # fewer than asked for: that is all there is
        items = [p for p in items if p.id not in self._deleted]
        for item in items:
            self._note(item, authority=listing is self._full)
        listing.items = [p for p in _merge(items, listing.items, complete) if p.id not in self._deleted]
        listing.total = max(total, len(listing.items))
        listing.active = any(not p.is_final for p in items)
        if listing is self._full:
            self._drop_opened_if_listed()
        self._emit(listing)
        self._settle()
        if listing.again:
            again, listing.again = listing.again, None
            self._refresh(listing, again)
        elif self._watching():
            self._schedule()

    def _on_page_error(self, listing: _Listing, project_id: str, token: int, trigger: str, error: ApiError) -> None:
        if not self._current(listing, project_id, token):
            return
        listing.loading = False                 # before anything that can raise: the list can be asked for again
        again, listing.again = listing.again, None
        listing.failed = True
        self._emit(listing)                     # the page leaves "Loading" and says the list did not load
        self._settle()
        if self._is_gone(error):
            self._gone(project_id, error)
            return
        # "auth" is the session's: it renews the token (the poll goes on) or signs out and says so (and stops this
        # poll). It is not counted here and tells the user nothing.
        # With a search shown two lists answer: the round says it once, the first text wins
        text = ""
        if trigger == POLL:
            outcome = listing.failures.failed(error.kind, error.status)
            if outcome in (ALERT, STOP):
                text = poll_notice(outcome, "processings search" if listing is self._found else "processings list",
                                   error.message, error.kind)
        elif error.kind != "auth":
            text = f"Processings didn't load: {error.message}"
        if text and not self._told:
            self._told = True
            self.listFailed.emit(text)
        # Spec 002_B: a refresh that failed for a transient reason, or with a 401, is asked again after one poll
        # interval. A permanent failure is not: the poll resumes when a list loads.
        if keeps_schedule(error.kind, error.status):
            self._schedule()
        if again:
            self._refresh(listing, again)

    def _settle(self) -> None:
        """`refreshed` when no list is in flight any more: with a search shown the Refresh ends after both answers."""
        if not (self._full.loading or self._found.loading):
            self.refreshed.emit()

    @staticmethod
    def _is_gone(error: ApiError) -> bool:
        return error.status in (403, 404) or error.kind in ("forbidden", "not_found")

    def _gone(self, project_id: str, error: ApiError) -> None:
        """The open project was deleted or unshared (Mapflow Web): the poll stops and the controller opens
        another project, once however many lists answered so. `stopped` holds until the project changes
        (`set_project`)."""
        self._poll.stop()
        self._full.again = self._found.again = None
        self._full.failures.failed("forbidden", error.status)
        if self._gone_id == project_id:
            return
        self._gone_id = project_id
        self.projectGone.emit(project_id, error)

    def get(self, processing_id: str) -> Optional[Processing]:
        """A processing of the full listing, of the matches, or the one opened by id."""
        return next((p for p in (*self._full.items, *self._found.items, *([self.opened] if self.opened else []))
                     if p.id == processing_id), None)

    def open(self, processing_id: str) -> bool:
        """"Show" in a notice: make the processing's card available. One that is not on the loaded pages (an old
        one) is fetched by id; it is kept apart (`opened`), so it changes neither `total` nor the offset of "Show
        more". True if a request went out. Every call drops the answer of an earlier one, also when it sends
        nothing."""
        self._open_token += 1
        if not self.project or any(p.id == processing_id for p in self._full.items):
            return False
        if self.opened and self.opened.id == processing_id:
            return False
        token, project_id = self._open_token, self.project.id

        def done(processing: Processing) -> None:
            if token != self._open_token or not self.project or self.project.id != project_id:
                return
            if processing.project_id and processing.project_id != project_id:
                self.actionFailed.emit("That processing is in another project.")
                return
            self._note(processing)
            if not any(p.id == processing.id for p in self._full.items):
                self.opened = processing
                self.changed.emit(self._full.items)
                self._resume_poll()

        def failed(error: ApiError) -> None:
            if token == self._open_token and self.project and self.project.id == project_id:
                self.actionFailed.emit(f"Couldn't open the processing: {error.message}")

        self.api.processing(processing_id, done, failed)
        return True

    def _drop_opened_if_listed(self) -> None:
        if self.opened and any(p.id == self.opened.id for p in self._full.items):
            self.opened = None

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
            self.refresh_shown(LOAD)

        self.api.start(payload, done, lambda error: self.startFailed.emit(error.message))

    def restart(self, processing: Processing) -> None:
        if processing.id in self._restarting:
            return
        self._restarting.add(processing.id)

        def done(_answer) -> None:
            self._restarting.discard(processing.id)
            # Only an accepted restart is watched: a refused one changes nothing, so no false "failed" follows
            self._last_status[processing.id] = Status.in_progress
            self.started_here.add(processing.id)
            # Every card of it shows the new status at once, with no Restart button, until the refresh answers
            for holder in (*self._full.items, *self._found.items, *([self.opened] if self.opened else [])):
                if holder.id == processing.id:
                    holder.status, holder.percent, holder.messages = Status.in_progress, 0, []
            self.changed.emit(self._full.items)
            if self.terms:
                self.foundChanged.emit(self._found.items)
            self.refresh_shown(LOAD)

        def failed(error: ApiError) -> None:
            self._restarting.discard(processing.id)
            self._action_failed(error)

        self.api.restart(processing.id, done, failed)

    def delete(self, processing: Processing) -> None:
        def done(_answer) -> None:
            # Off the lists at once: the next page from Mapflow may still be on its way with it
            self._deleted.add(processing.id)
            if self.opened and self.opened.id == processing.id:
                self.opened = None
            for listing in (self._full, self._found):
                before = len(listing.items)
                listing.items = [p for p in listing.items if p.id != processing.id]
                listing.total = max(listing.total - (before - len(listing.items)), len(listing.items))
            self.changed.emit(self.items)
            if self.terms:
                self.foundChanged.emit(self.found)
            self.refresh_shown(LOAD)

        self.api.delete(processing.id, done, self._action_failed)

    def rename(self, processing: Processing, name: str, description: str) -> None:
        self.api.rename(processing, name, description, lambda _: self.refresh_shown(LOAD), self._action_failed)

    def rate(self, processing: Processing, rating: int, feedback: str = "") -> None:
        self.api.rate(processing.id, rating, feedback, lambda _: self.rated.emit(processing.id, rating),
                      self._action_failed)

    def _action_failed(self, error: ApiError) -> None:
        self.actionFailed.emit(error.message)
        self.refresh_shown(LOAD)
