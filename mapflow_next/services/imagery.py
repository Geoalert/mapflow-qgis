"""Imagery catalog search and the user's own imagery (My imagery)."""
from __future__ import annotations

import time
from datetime import date
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Tuple

from qgis.PyQt.QtCore import QObject, pyqtSignal

from ..api.client import MapflowApi
from ..api.http import ApiError
from ..config import MOSAICS_PAGE_SIZE, POLL_FAILURES_BEFORE_ALERT
from ..core.failures import ALERT, STOP, PollFailures, poll_notice
from ..core.messages import image_download_failure
from ..core.models import CatalogImage, ImageDownload, Mosaic, MosaicImage, StorageLimits

# A refresh reloads the listing in one request up to this many; collections loaded beyond stay as they are
MAX_RELOAD = 200


class Imagery(QObject):
    searchDone = pyqtSignal(list, int)        # [CatalogImage], total
    moreDone = pyqtSignal(list, int)          # the next page's new images, total
    searchFailed = pyqtSignal(str)
    mosaicsChanged = pyqtSignal(list)         # the listing: [Mosaic] loaded so far
    mosaicSearchChanged = pyqtSignal(str, list)   # query, [Mosaic] found so far ("" when the search ended)
    mosaicImagesChanged = pyqtSignal(str, list)   # mosaic id, [MosaicImage]
    uploadProgress = pyqtSignal(int)          # percent
    uploadDone = pyqtSignal(str)              # collection name
    uploadFailed = pyqtSignal(str)
    mosaicsFailed = pyqtSignal(str)           # a listing nobody waited on failed: the line to show ("": none)
    limitsChanged = pyqtSignal()              # the account's limits were asked for: the answer, or the fallback
    limitsFailed = pyqtSignal(str)            # they didn't load and the user is told: Mapflow's reason
    notice = pyqtSignal(str)                  # a line for the message bar: a request failed
    imagesFailed = pyqtSignal(str, str, bool)   # mosaic id, the reason, whether to tell the user (once per outage)

    def __init__(self, api: MapflowApi, parent=None):
        super().__init__(parent)
        self.api = api
        self.results: List[CatalogImage] = []
        self.total = 0                          # images matching the last search, loaded or not
        self.loading_more = False
        self._request: Optional[dict] = None
        self._search_id = 0
        self.mosaics: List[Mosaic] = []
        self.images: Dict[str, List[MosaicImage]] = {}
        self._images_loading: Set[str] = set()
        self.uploading = False
        self.limits = StorageLimits()           # GET rasters/memory; all None until it answers: the built-in limits
        self._limits_at = 0.0                   # when My imagery last asked for it (monotonic)
        self._limits_loading = False
        self._limits_alerted = False            # a failure was told and no success since
        # Asked when Mapflow says a collection already has a file: (file name, collection name) →
        # "upload" (add it again), "skip" or "cancel". The controller sets it; without it, the upload stops.
        self.on_duplicate: Optional[Callable[[str, str], str]] = None
        self._mosaics_at = 0.0                  # when the collections were last asked for (monotonic)
        self._mosaics_loading = False
        self.mosaics_total = 0                  # collections in the account, listed or not
        self.mosaics_loaded = False             # a listing answered
        self.mosaics_failed = False             # the last answer to a listing was a failure
        self._mosaics_poll = PollFailures(POLL_FAILURES_BEFORE_ALERT)
        self._images_alerted = False            # an image list failed and the user was told; a success clears it
        self._listing_id = 0                    # the listing's requests: a late answer to an older one is dropped
        self._known: Dict[str, Mosaic] = {}     # every collection seen, by id: listings, searches, lookups
        # The collection search (server-side): its query, the collections found so far, how many match
        self.found: List[Mosaic] = []
        self.found_query = ""
        self.found_total = 0
        self.found_loading = False
        self.found_failed = False
        self._found_id = 0
        self._downloads: Set[str] = set()       # ids of the images being downloaded
        self._download_epoch = 0                # moves when the downloads stop: an answer of an older one is dropped

    def search(self, geometry: dict, date_from: date, date_to: date, max_cloud: Optional[float],
               min_off_nadir: Optional[float], max_off_nadir: Optional[float],
               product_types: Optional[List[str]] = None, min_coverage: Optional[float] = None,
               hide_unavailable: bool = False) -> None:
        """`min_coverage`: the least share of the area, in %, an image must cover (None: any overlap).
        Both off-nadir angles are sent as given, also 0; None leaves a bound out. `hide_unavailable` ("Available
        for me") is always sent, also False; "Show more" repeats it with the rest of this request."""
        request = {
            "aoi": geometry,
            "acquisitionDateFrom": f"{date_from.isoformat()}T00:00:00Z",
            "acquisitionDateTo": f"{date_to.isoformat()}T23:59:59Z",
            "maxCloudCover": max_cloud,
            "minOffNadirAngle": min_off_nadir,
            "maxOffNadirAngle": max_off_nadir,
            "minAoiIntersectionPercent": min_coverage,
            "productTypes": product_types or None,
            "sortBy": "ACQUISITION_DATE",
            "sortOrder": "DESC",
        }
        request = {key: value for key, value in request.items() if value is not None}
        request["hideUnavailable"] = bool(hide_unavailable)
        self._request, self.total, self.loading_more = request, 0, False
        self._search_id += 1
        search_id = self._search_id
        self.api.search_catalog(request, lambda images, total: self._found(search_id, images, total),
                                lambda error: self.searchFailed.emit(error.message))

    def _found(self, search_id: int, images: List[CatalogImage], total: int) -> None:
        if search_id != self._search_id:            # a newer search went out
            return
        self.results = images
        self.total = max(total, len(images))
        self.searchDone.emit(images, self.total)

    @property
    def has_more(self) -> bool:
        return bool(self._request) and len(self.results) < self.total

    def search_more(self) -> None:
        """The next page of the same search."""
        if not self.has_more or self.loading_more:
            return
        self.loading_more = True
        search_id = self._search_id

        def done(images: List[CatalogImage], total: int) -> None:
            if search_id != self._search_id:
                return
            self.loading_more = False
            known = {i.key for i in self.results}
            self.results += [i for i in images if i.key not in known]
            # A page that brings nothing new ends the list, whatever the total says
            self.total = max(total, len(self.results)) if any(i.key not in known for i in images) else len(self.results)
            self.moreDone.emit([i for i in images if i.key not in known], self.total)

        def failed(error) -> None:
            if search_id == self._search_id:
                self.loading_more = False
                self.searchFailed.emit(f"More images didn't load: {error.message}")

        self.api.search_catalog(self._request, done, failed, offset=len(self.results))

    def clear_results(self) -> None:
        self._search_id += 1
        self.results, self.total, self._request, self.loading_more = [], 0, None, False

    def get_result(self, key: str) -> Optional[CatalogImage]:
        """A search result by its key (CatalogImage.key)."""
        return next((i for i in self.results if i.key == key), None)

    # ---------- My imagery collections: listed a page at a time, searched on the server ----------

    def load_mosaics(self, poll: bool = False) -> None:
        """The listing again from its first page, as many as are loaded (up to MAX_RELOAD); the ones loaded
        beyond that stay, so a refresh never takes away what "Show more" brought. `poll`: a timer asks. Its
        failures are counted (`_mosaics_poll`); any other caller's failure is told at once through
        `mosaicsFailed`, and the controller clears what it marked as waiting for the listing."""
        if poll and self._mosaics_poll.stopped:
            return
        self._mosaics_at = time.monotonic()
        self._mosaics_loading = True
        self._listing_id += 1
        listing = self._listing_id
        loaded = len(self.mosaics)
        limit = min(MAX_RELOAD, max(MOSAICS_PAGE_SIZE, -(-loaded // MOSAICS_PAGE_SIZE) * MOSAICS_PAGE_SIZE))

        def done(items: List[Mosaic], total: int, _has_next: bool) -> None:
            if listing != self._listing_id:
                return                              # a newer load or "Show more" went out
            self._mosaics_loading = False
            self.mosaics_loaded, self.mosaics_failed = True, False
            self._mosaics_poll.succeeded()
            fresh = self._remember(items)
            seen = {m.id for m in fresh}
            for gone in [m for m in self.mosaics[:limit] if m.id not in seen]:
                self._known.pop(gone.id, None)      # deleted elsewhere (Mapflow Web) since the last load
            self.mosaics = fresh + [m for m in self.mosaics[limit:] if m.id not in seen]
            self.mosaics_total = max(total, len(self.mosaics))
            self.mosaicsChanged.emit(self.mosaics)

        def failed(error: ApiError) -> None:
            if listing != self._listing_id:
                return                              # a newer request owns the flag
            self._mosaics_loading = False           # before anything that can raise
            self.mosaics_failed = True
            if poll:
                outcome = self._mosaics_poll.failed(error.kind, error.status)
                text = poll_notice(outcome, "collections list", error.message, error.kind) \
                    if outcome in (ALERT, STOP) else ""
                if text:
                    self.notice.emit(text)
            else:                                   # "auth" is the session's: it says so, so no line here
                self.mosaicsFailed.emit("" if error.kind == "auth" else f"Collections didn't load: {error.message}")
            self.mosaicsChanged.emit(self.mosaics)  # the page leaves "Loading"
        self.api.mosaic_page(0, limit, "", done, failed)

    def load_more_mosaics(self) -> None:
        """The listing's next page."""
        if self._mosaics_loading or not self.has_more_mosaics:
            return
        self._mosaics_loading = True
        self._listing_id += 1
        listing = self._listing_id
        self.mosaicsChanged.emit(self.mosaics)      # "Show more" says it's loading

        def done(items: List[Mosaic], total: int, _has_next: bool) -> None:
            if listing != self._listing_id:
                return
            self._mosaics_loading = False
            known = {m.id for m in self.mosaics}
            fresh = [m for m in self._remember(items) if m.id not in known]
            self.mosaics += fresh
            # A page that brings nothing new ends the list, whatever the total says
            self.mosaics_total = max(total, len(self.mosaics)) if fresh else len(self.mosaics)
            self.mosaicsChanged.emit(self.mosaics)

        def failed(error: ApiError) -> None:
            if listing == self._listing_id:
                self._mosaics_loading = False
                self.mosaicsChanged.emit(self.mosaics)      # the button comes back
                if error.kind != "auth":
                    self.notice.emit(f"More collections didn't load: {error.message}")
        self.api.mosaic_page(len(self.mosaics), MOSAICS_PAGE_SIZE, "", done, failed)

    @property
    def has_more_mosaics(self) -> bool:
        return len(self.mosaics) < self.mosaics_total

    @property
    def loading_mosaics(self) -> bool:
        return self._mosaics_loading

    def search_mosaics(self, query: str, more: bool = False) -> None:
        """Collections whose name, or one of whose images' names, contains `query`: asked of the server, so
        it finds collections beyond the loaded pages. `more`: its next page. An empty query ends the search."""
        query = query.strip()
        self._found_id += 1
        search = self._found_id
        if not query:
            self.found, self.found_query, self.found_total, self.found_loading = [], "", 0, False
            self.found_failed = False
            self.mosaicSearchChanged.emit("", [])
            return
        offset = len(self.found) if more and query == self.found_query else 0
        if not offset:
            self.found = []
        self.found_query, self.found_loading, self.found_failed = query, True, False
        if offset:
            self.mosaicSearchChanged.emit(query, self.found)    # "Show more" says it's loading

        def done(items: List[Mosaic], total: int, _has_next: bool) -> None:
            if search != self._found_id:
                return                              # typed on since
            self.found_loading, self.found_failed = False, False
            known = {m.id for m in self.found}
            fresh = [m for m in self._remember(items) if m.id not in known]
            self.found += fresh
            self.found_total = max(total, len(self.found)) if fresh or not offset else len(self.found)
            self.mosaicSearchChanged.emit(query, self.found)

        def failed(error: ApiError) -> None:
            if search == self._found_id:
                self.found_loading, self.found_failed = False, True
                self.mosaicSearchChanged.emit(query, self.found)
                if error.kind != "auth":
                    self.notice.emit(f"The search didn't work: {error.message}")
        self.api.mosaic_page(offset, MOSAICS_PAGE_SIZE, query, done, failed)

    @property
    def has_more_found(self) -> bool:
        return bool(self.found_query) and len(self.found) < self.found_total

    def fetch_mosaic(self, mosaic_id: str, on_done: Callable[[Mosaic], None],
                     on_missing: Callable[[], None], on_error: Optional[Callable[[str], None]] = None) -> None:
        """A collection not on the loaded pages (the imagery of a processing run again), asked for by id.
        `on_missing` when Mapflow says it isn't there (deleted)."""
        known = self._known.get(mosaic_id)
        if known is not None:
            on_done(known)
            return

        def failed(error: ApiError) -> None:
            if error.status == 404 or error.kind == "not_found":
                on_missing()
            elif on_error is not None:
                on_error(error.message)
        self.api.mosaic(mosaic_id, lambda mosaic: on_done(self._remember([mosaic])[0]), failed)

    def _remember(self, items: List[Mosaic]) -> List[Mosaic]:
        """Collections as listed, kept by id (the same object everywhere they show), with the image counts the
        listing doesn't carry filled in from their image lists."""
        kept = []
        for mosaic in items:
            if not mosaic.id:
                continue
            if mosaic.image_count is None and mosaic.id in self.images:
                mosaic.image_count = len(self.images[mosaic.id])
            self._known[mosaic.id] = mosaic
            kept.append(mosaic)
        for mosaic in kept:
            if mosaic.image_count is None:          # older deployments: the list has no status_summary
                self.load_images(mosaic.id)
        return kept

    def refresh_mosaics(self, max_age: float = 10.0, poll: bool = False) -> None:
        """Collections made elsewhere (Mapflow Web) show up: ask again if the list is older than `max_age`."""
        if not self._mosaics_loading and time.monotonic() - self._mosaics_at >= max_age:
            self.load_mosaics(poll)

    def load_limits(self, on_done: Optional[Callable[[StorageLimits], None]] = None, waiting: bool = False) -> None:
        """Ask for the account's upload limits and free storage. `on_done` gets them, or the built-in ones (all
        None) when the request fails: an upload goes on either way. `waiting`: an upload waits for the answer, so
        a failure is told at once; any other failure is told once, until a request succeeds."""
        answered = False

        def done(limits: StorageLimits) -> None:
            nonlocal answered
            answered = True
            self.limits = limits
            self._limits_loading = self._limits_alerted = False
            self.limitsChanged.emit()
            if on_done:
                on_done(limits)

        def failed(error: ApiError) -> None:
            if answered:
                return              # `on_done` raised after the answer: the http layer reports it, then calls this
            self._limits_loading = False            # before anything that can raise
            self.limits = StorageLimits()           # free space of an older answer may be out of date
            if error.kind != "auth" and (waiting or not self._limits_alerted):
                self._limits_alerted = self._limits_alerted or not waiting     # an upload's failure is its own
                self.limitsFailed.emit(error.message)
            self.limitsChanged.emit()
            if on_done:
                on_done(self.limits)
        self.api.storage_limits(done, failed)

    def refresh_limits(self, max_age: float = 5.0) -> None:
        """My imagery opens: ask for the limits, unless a request is out or the last answer is younger than
        `max_age`."""
        if not self._limits_loading and time.monotonic() - self._limits_at >= max_age:
            self._limits_at = time.monotonic()
            self._limits_loading = True
            self.load_limits()

    def reset_busy(self) -> None:
        """After sign-out: requests in flight were aborted and won't call back, so nothing is loading."""
        self.uploading = False
        self._limits_loading = self._limits_alerted = False
        self.limits = StorageLimits()
        self.loading_more = False
        self._images_loading.clear()
        self._mosaics_loading = False
        self.found_loading = False
        self._search_id += 1
        self._listing_id += 1
        self._found_id += 1
        self._downloads.clear()
        self._download_epoch += 1
        self._forget_failures()

    def stop(self) -> None:
        """Unload: abort the requests, clear the flags and drop the answers that still come. Emits nothing: the dock
        goes too."""
        self.reset_busy()
        self.on_duplicate = None
        self.api.abort_all()

    def _forget_failures(self) -> None:
        self.mosaics_loaded = self.mosaics_failed = self.found_failed = False
        self._mosaics_poll.succeeded()
        self._images_alerted = False

    def forget_mosaics(self) -> None:
        """After sign-out: the next account's collections are listed afresh, none of these kept."""
        self.mosaics, self.mosaics_total, self._mosaics_at = [], 0, 0.0
        self.found, self.found_query, self.found_total = [], "", 0
        self._known.clear()
        self.images.clear()
        self._forget_failures()

    def load_images(self, mosaic_id: str, force: bool = False, waiting: bool = False) -> None:
        """A collection's images. `waiting`: a click waits for the answer, so a failure is told at once. Without
        it, the lists of a listing (for the counts) tell one failure, not one per collection."""
        if mosaic_id in self._images_loading or (mosaic_id in self.images and not force):
            if mosaic_id in self.images:
                self.mosaicImagesChanged.emit(mosaic_id, self.images[mosaic_id])
            return
        self._images_loading.add(mosaic_id)

        def done(images: List[MosaicImage]):
            self._images_loading.discard(mosaic_id)
            self._images_alerted = False
            self.images[mosaic_id] = sorted(images, key=lambda i: (i.filename or "").lower())
            mosaic = self.get_mosaic(mosaic_id)
            if mosaic:
                mosaic.image_count = len(images)
            self.mosaicImagesChanged.emit(mosaic_id, self.images[mosaic_id])

        def failed(error: ApiError):
            self._images_loading.discard(mosaic_id)
            tell = (waiting or not self._images_alerted) and error.kind != "auth"
            self._images_alerted = self._images_alerted or tell
            self.imagesFailed.emit(mosaic_id, error.message, tell)

        self.api.mosaic_images(mosaic_id, done, failed)

    def get_image(self, mosaic_id: str, image_id: Optional[str]) -> Optional[MosaicImage]:
        return next((i for i in self.images.get(mosaic_id, []) if i.id == image_id), None)

    def get_mosaic(self, mosaic_id: Optional[str]) -> Optional[Mosaic]:
        """A collection seen in any listing, search or lookup; None if it hasn't been (see fetch_mosaic)."""
        return self._known.get(mosaic_id or "")

    def mosaic_names(self) -> Dict[str, str]:
        """Id → name of every collection seen so far (what processings' sources are named by)."""
        return {mosaic_id: mosaic.name for mosaic_id, mosaic in self._known.items()}

    def upload(self, file_path: str, name: str) -> None:
        if self.uploading:
            return
        self.uploading = True

        def progress(sent: int, total: int):
            if total > 0:
                self.uploadProgress.emit(int(sent * 100 / total))

        def done(_data):
            self.uploading = False
            self.uploadDone.emit(name)
            self.load_mosaics()

        def failed(error: ApiError):
            self.uploading = False
            self.uploadFailed.emit(error.message)

        self.api.upload_to_new_mosaic(file_path, name, done, failed, progress)

    def upload_many(self, paths: List[str], name: str) -> None:
        """Several GeoTIFFs into one new collection: the collection first, then each file in turn."""
        if self.uploading or not paths:
            return
        self.uploading = True
        if self._file_sizes(paths) is None:         # before the collection is made, so none stays empty
            return

        def created(data):
            mosaic_id = (data or {}).get("id")
            if not mosaic_id:
                self.uploading = False
                self.uploadFailed.emit("Mapflow didn't create the collection")
                self.load_mosaics()
                return
            self._send_files(mosaic_id, paths, name)

        def failed(error: ApiError):
            self.uploading = False
            self.uploadFailed.emit(error.message)

        self.api.create_mosaic(name, [], created, failed)

    def _file_sizes(self, paths: List[str]) -> Optional[List[int]]:
        """The size of each file, or None after the upload ended with a message naming the file that can't be
        read. It runs after `uploading` is set, inside a callback whose guard would swallow a raise and leave the
        flag set, so it clears the flag itself."""
        sizes: List[int] = []
        for path in paths:
            try:
                sizes.append(Path(path).stat().st_size)
            except OSError as exc:
                self.uploading = False
                self.uploadFailed.emit(f"“{Path(path).name}” can't be read: {exc.strerror or 'no access'}. "
                                       "Nothing was uploaded.")
                return None
        return sizes

    def upload_into(self, mosaic_id: str, paths: List[str], duplicates_allowed: Optional[Set[str]] = None) -> None:
        """GeoTIFFs added to an existing collection, one after another. `duplicates_allowed`: file names the
        user already agreed to add although the collection has them."""
        if self.uploading or not paths:
            return
        self.uploading = True
        mosaic = self.get_mosaic(mosaic_id)
        self._send_files(mosaic_id, paths, mosaic.name if mosaic else "My imagery", duplicates_allowed or set())

    def _send_files(self, mosaic_id: str, paths: List[str], name: str, allowed: Optional[Set[str]] = None) -> None:
        """Each file in turn into the collection, progress counted in bytes across them all. A file the
        collection already has is up to the user (on_duplicate): added again, skipped, or the upload stops.
        Any other failure stops there; what is uploaded stays, and the message names the file."""
        sizes = self._file_sizes(paths)
        if sizes is None:
            self.load_mosaics()         # the collection of upload_many exists, empty
            return
        total = max(1, sum(sizes))
        allowed = set(allowed or ())
        sent_files: List[str] = []

        def finish() -> None:
            self.load_images(mosaic_id, force=True)
            self.load_mosaics()

        def failed(error: ApiError, index: int):
            file = Path(paths[index]).name
            if "existing_image_id" in (error.params or {}) and self.on_duplicate is not None:
                choice = self.on_duplicate(file, name)
                if choice == "upload":
                    allowed.add(file)
                    send(index)
                    return
                if choice == "skip":
                    send(index + 1)
                    return
            self.uploading = False
            self.uploadFailed.emit(f"{file}: {error.message}" if file not in error.message else error.message)
            finish()

        def send(index: int) -> None:
            if index == len(paths):
                self.uploading = False
                if sent_files:
                    self.uploadDone.emit(name)
                else:
                    self.uploadFailed.emit(f"Nothing new to upload: “{name}” already has these images.")
                finish()
                return
            done_bytes = sum(sizes[:index])

            def progress(sent: int, _total: int):
                self.uploadProgress.emit(min(99, int((done_bytes + sent) * 100 / total)))

            def uploaded(_data) -> None:
                sent_files.append(paths[index])
                send(index + 1)
            self.api.upload_to_mosaic(mosaic_id, paths[index], uploaded, lambda error: failed(error, index), progress,
                                      allow_duplicate=Path(paths[index]).name in allowed)

        send(0)

    def delete_mosaic(self, mosaic_id: str, on_done: Callable[[], None], on_error: Callable[[str], None]) -> None:
        def done(_data):
            if any(m.id == mosaic_id for m in self.mosaics):
                self.mosaics_total = max(0, self.mosaics_total - 1)
            self.mosaics = [m for m in self.mosaics if m.id != mosaic_id]
            if any(m.id == mosaic_id for m in self.found):
                self.found = [m for m in self.found if m.id != mosaic_id]
                self.found_total = max(0, self.found_total - 1)
                self.mosaicSearchChanged.emit(self.found_query, self.found)
            self.images.pop(mosaic_id, None)
            self._known.pop(mosaic_id, None)
            self.mosaicsChanged.emit(self.mosaics)
            on_done()
            self.load_mosaics()

        self.api.delete_mosaic(mosaic_id, done, lambda error: on_error(error.message))

    def delete_image(self, mosaic_id: str, image_id: str, on_done: Callable[[], None],
                     on_error: Callable[[str], None]) -> None:
        """The collection stays when its last image goes: empty, ready for other uploads."""
        def done(_data):
            left = [i for i in self.images.get(mosaic_id, []) if i.id != image_id]
            self.images[mosaic_id] = left
            mosaic = self.get_mosaic(mosaic_id)
            if mosaic is not None:
                mosaic.image_count = len(left)
            self.mosaicImagesChanged.emit(mosaic_id, left)
            on_done()
            self.load_mosaics()                     # its size changes

        self.api.delete_image(image_id, done, lambda error: on_error(error.message))

    def is_downloading(self, image_id: str) -> bool:
        return image_id in self._downloads

    def download_image(self, image_id: str, choose_path: Callable[[str], str], on_done: Callable[[str], None],
                       on_error: Callable[[str], None]) -> None:
        """An image's original file: Mapflow gives an address, `choose_path(filename)` asks the user where to save
        (an empty answer is a Cancel: nothing happens and nobody is told), and the file is streamed there.
        `on_done` gets the path, `on_error` the reason. After `reset_busy` or `stop` nothing is called back."""
        epoch = self._download_epoch
        self._downloads.add(image_id)

        def end() -> bool:
            """False: the downloads were stopped meanwhile, so this answer is not for anyone."""
            if epoch != self._download_epoch:
                return False
            self._downloads.discard(image_id)
            return True

        def failed(step: str):
            def report(error: ApiError) -> None:
                if end():
                    on_error(image_download_failure(step, error.status, error.message))
            return report

        def saved(path: str) -> None:
            if end():
                on_done(path)

        def linked(link: ImageDownload) -> None:
            if epoch != self._download_epoch:
                return
            if not link.url.startswith(("http://", "https://")):     # `Http` would read it as a path of the API
                if end():
                    on_error("Mapflow sent no download address for this image.")
                return
            path = choose_path(link.filename)
            if epoch != self._download_epoch:       # a sign-out came while the dialog was open
                return
            if not path:
                self._downloads.discard(image_id)
                return
            self.api.download_image_file(link.url, path, saved, failed("file"))

        self.api.image_download_link(image_id, linked, failed("link"))

    def create_collection(self, name: str, tags: List[str], on_done: Callable[[str], None],
                          on_error: Callable[[str], None]) -> None:
        """An empty collection, for uploads to come. `on_done` gets its id once Mapflow lists it."""
        def created(data):
            mosaic_id = (data or {}).get("id") or ""
            self.load_mosaics()
            on_done(mosaic_id)

        self.api.create_mosaic(name, tags, created, lambda error: on_error(error.message))

    def rename_collection(self, mosaic_id: str, name: str, tags: List[str], on_done: Callable[[str], None],
                          on_error: Callable[[str], None]) -> None:
        """A collection's new name and tags. `on_done` gets the old name. The collection changes where it is
        cached, with no new listing. The listing, the search and the lookups can each hold an object of its own
        for the collection, so all of them change. The window that shows the search redraws its rows itself (see
        MosaicPicker.collection_renamed)."""
        def done(_data):
            known = self.get_mosaic(mosaic_id)
            old = known.name if known is not None else name
            for mosaic in (*self.mosaics, *self.found, *([known] if known else [])):
                if mosaic.id == mosaic_id:
                    mosaic.name, mosaic.tags = name, list(tags)
            self.mosaicsChanged.emit(self.mosaics)
            on_done(old)

        self.api.update_mosaic(mosaic_id, name, tags, done, lambda error: on_error(error.message))

    def validate(self, images: List[Tuple[str, dict]], on_done: Callable[[List[str], List[str]], None]) -> None:
        """Mapflow's check of each image, (file name, request), before it is uploaded. `on_done` gets the
        reasons it refuses images and its warnings about the others. A request it can't answer (the check
        isn't there, or failed) doesn't block the upload: the upload itself is checked again."""
        problems: List[str] = []
        warnings: List[str] = []

        def ask(index: int) -> None:
            if index == len(images):
                on_done(problems, warnings)
                return
            filename, request = images[index]

            def answered(data: dict) -> None:
                def messages(key: str) -> List[str]:
                    return [str(r.get("message") or r.get("code")) for r in data.get(key) or []
                            if isinstance(r, dict) and (r.get("message") or r.get("code"))]
                if data.get("compatible") is False:
                    problems.append(f"{filename}: {'; '.join(messages('reasons')) or 'Mapflow can’t process it'}")
                warnings.extend(f"{filename}: {m}" for m in messages("warnings"))
                ask(index + 1)

            def failed(_error: ApiError) -> None:      # http logs it
                ask(index + 1)
            self.api.validate_image(request, answered, failed)

        ask(0)
