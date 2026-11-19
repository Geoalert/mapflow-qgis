"""Imagery catalog search and the user's own imagery (My imagery)."""
from __future__ import annotations

import time
from datetime import date
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Tuple

from qgis.PyQt.QtCore import QObject, pyqtSignal

from ..api.client import MapflowApi
from ..api.http import ApiError
from ..core.models import CatalogImage, Mosaic, MosaicImage


class Imagery(QObject):
    searchDone = pyqtSignal(list, int)        # [CatalogImage], total
    moreDone = pyqtSignal(list, int)          # the next page's new images, total
    searchFailed = pyqtSignal(str)
    mosaicsChanged = pyqtSignal(list)         # [Mosaic]
    mosaicImagesChanged = pyqtSignal(str, list)   # mosaic id, [MosaicImage]
    uploadProgress = pyqtSignal(int)          # percent
    uploadDone = pyqtSignal(str)              # collection name
    uploadFailed = pyqtSignal(str)

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
        # Asked when Mapflow says a collection already has a file: (file name, collection name) →
        # "upload" (add it again), "skip" or "cancel". The controller sets it; without it, the upload stops.
        self.on_duplicate: Optional[Callable[[str, str], str]] = None
        self._mosaics_at = 0.0                  # when the collections were last asked for (monotonic)
        self._mosaics_loading = False
        self._mosaics_loaded = False

    def search(self, geometry: dict, date_from: date, date_to: date, max_cloud: Optional[float],
               max_off_nadir: Optional[float], product_types: Optional[List[str]] = None,
               min_coverage: Optional[float] = None) -> None:
        """`min_coverage`: the least share of the area, in %, an image must cover (None: any overlap)."""
        request = {
            "aoi": geometry,
            "acquisitionDateFrom": f"{date_from.isoformat()}T00:00:00Z",
            "acquisitionDateTo": f"{date_to.isoformat()}T23:59:59Z",
            "maxCloudCover": max_cloud,
            "maxOffNadirAngle": max_off_nadir,
            "minAoiIntersectionPercent": min_coverage,
            "productTypes": product_types or None,
            "sortBy": "ACQUISITION_DATE",
            "sortOrder": "DESC",
        }
        request = {key: value for key, value in request.items() if value is not None}
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

    def load_mosaics(self) -> None:
        self._mosaics_at = time.monotonic()
        self._mosaics_loading = True

        def failed(_error):
            self._mosaics_loading = False
        self.api.mosaics(self._on_mosaics, on_error=failed)

    def refresh_mosaics(self, max_age: float = 10.0) -> None:
        """Collections made elsewhere (Mapflow Web) show up: ask again if the list is older than `max_age`."""
        if not self._mosaics_loading and time.monotonic() - self._mosaics_at >= max_age:
            self.load_mosaics()

    @property
    def mosaics_loaded(self) -> bool:
        """The collection list has come at least once: a collection missing from it is gone, not unknown yet."""
        return self._mosaics_loaded

    def _on_mosaics(self, mosaics: List[Mosaic]) -> None:
        self._mosaics_loading = False
        self._mosaics_loaded = True
        self.mosaics = sorted(mosaics or [], key=lambda m: (m.created is not None, m.created or 0), reverse=True)
        for mosaic in self.mosaics:
            if mosaic.id in self.images:
                mosaic.image_count = len(self.images[mosaic.id])
        self.mosaicsChanged.emit(self.mosaics)
        # The list doesn't always say how many images a collection has: their image lists do
        for mosaic in self.mosaics:
            if mosaic.image_count is None:
                self.load_images(mosaic.id)

    def reset_busy(self) -> None:
        """After sign-out: requests in flight were aborted and won't call back, so nothing is loading."""
        self.uploading = False
        self.loading_more = False
        self._images_loading.clear()
        self._mosaics_loading = False
        self._search_id += 1

    def load_images(self, mosaic_id: str, force: bool = False) -> None:
        if mosaic_id in self._images_loading or (mosaic_id in self.images and not force):
            if mosaic_id in self.images:
                self.mosaicImagesChanged.emit(mosaic_id, self.images[mosaic_id])
            return
        self._images_loading.add(mosaic_id)

        def done(images: List[MosaicImage]):
            self._images_loading.discard(mosaic_id)
            self.images[mosaic_id] = sorted(images, key=lambda i: (i.filename or "").lower())
            mosaic = self.get_mosaic(mosaic_id)
            if mosaic:
                mosaic.image_count = len(images)
            self.mosaicImagesChanged.emit(mosaic_id, self.images[mosaic_id])

        def failed(_error):
            self._images_loading.discard(mosaic_id)

        self.api.mosaic_images(mosaic_id, done, failed)

    def get_image(self, mosaic_id: str, image_id: Optional[str]) -> Optional[MosaicImage]:
        return next((i for i in self.images.get(mosaic_id, []) if i.id == image_id), None)

    def get_mosaic(self, mosaic_id: Optional[str]) -> Optional[Mosaic]:
        return next((m for m in self.mosaics if m.id == mosaic_id), None)

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
        sizes = [Path(p).stat().st_size for p in paths]
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
            self.mosaics = [m for m in self.mosaics if m.id != mosaic_id]
            self.images.pop(mosaic_id, None)
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

    def create_collection(self, name: str, tags: List[str], on_done: Callable[[str], None],
                          on_error: Callable[[str], None]) -> None:
        """An empty collection, for uploads to come. `on_done` gets its id once Mapflow lists it."""
        def created(data):
            mosaic_id = (data or {}).get("id") or ""
            self.load_mosaics()
            on_done(mosaic_id)

        self.api.create_mosaic(name, tags, created, lambda error: on_error(error.message))

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
