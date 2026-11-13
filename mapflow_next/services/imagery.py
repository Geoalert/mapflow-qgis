"""Imagery catalog search and the user's own imagery (My imagery)."""
from __future__ import annotations

import time
from datetime import date
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set

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
        self._mosaics_at = 0.0                  # when the collections were last asked for (monotonic)
        self._mosaics_loading = False

    def search(self, geometry: dict, date_from: date, date_to: date, max_cloud: Optional[float],
               max_off_nadir: Optional[float], product_types: Optional[List[str]] = None) -> None:
        request = {
            "aoi": geometry,
            "acquisitionDateFrom": f"{date_from.isoformat()}T00:00:00Z",
            "acquisitionDateTo": f"{date_to.isoformat()}T23:59:59Z",
            "maxCloudCover": max_cloud,
            "maxOffNadirAngle": max_off_nadir,
            "minAoiIntersectionPercent": 0,
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
            known = {i.id for i in self.results}
            self.results += [i for i in images if i.id not in known]
            # A page that brings nothing new ends the list, whatever the total says
            self.total = max(total, len(self.results)) if any(i.id not in known for i in images) else len(self.results)
            self.moreDone.emit([i for i in images if i.id not in known], self.total)

        def failed(error) -> None:
            if search_id == self._search_id:
                self.loading_more = False
                self.searchFailed.emit(f"More images didn't load: {error.message}")

        self.api.search_catalog(self._request, done, failed, offset=len(self.results))

    def clear_results(self) -> None:
        self._search_id += 1
        self.results, self.total, self._request, self.loading_more = [], 0, None, False

    def get_result(self, image_id: str) -> Optional[CatalogImage]:
        return next((i for i in self.results if i.id == image_id), None)

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

    def _on_mosaics(self, mosaics: List[Mosaic]) -> None:
        self._mosaics_loading = False
        self.mosaics = sorted(mosaics or [], key=lambda m: (m.created is not None, m.created or 0), reverse=True)
        for mosaic in self.mosaics:
            if mosaic.id in self.images:
                mosaic.image_count = len(self.images[mosaic.id])
        self.mosaicsChanged.emit(self.mosaics)
        # The list doesn't always say how many images a collection has: their image lists do
        for mosaic in self.mosaics:
            if mosaic.image_count is None:
                self.load_images(mosaic.id)

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
        """Several GeoTIFFs into one new collection: the collection first, then each file in turn. A failure
        stops there; what is uploaded stays, and the message names the file."""
        if self.uploading or not paths:
            return
        self.uploading = True
        sizes = [Path(p).stat().st_size for p in paths]
        total = max(1, sum(sizes))

        def failed(error: ApiError, file: str = ""):
            self.uploading = False
            self.uploadFailed.emit(f"{Path(file).name}: {error.message}" if file else error.message)
            self.load_mosaics()

        def send(mosaic_id: str, index: int) -> None:
            if index == len(paths):
                self.uploading = False
                self.uploadDone.emit(name)
                self.load_mosaics()
                return
            done_bytes = sum(sizes[:index])

            def progress(sent: int, _total: int):
                self.uploadProgress.emit(min(99, int((done_bytes + sent) * 100 / total)))
            self.api.upload_to_mosaic(mosaic_id, paths[index], lambda _d: send(mosaic_id, index + 1),
                                      lambda error: failed(error, paths[index]), progress)

        def created(data):
            mosaic_id = (data or {}).get("id")
            if not mosaic_id:
                failed(ApiError("server", "Mapflow didn't create the collection"))
                return
            send(mosaic_id, 0)

        self.api.create_mosaic(name, created, failed)

    def validate(self, metadata: List[dict], on_done: Callable[[List[str]], None]) -> None:
        """Mapflow's check of each image before it is uploaded: `on_done` gets the problems it reports (none:
        all fine). An answer that isn't a verdict (the check isn't there, or failed) doesn't block the upload,
        which Mapflow checks again anyway."""
        problems: List[str] = []

        def ask(index: int) -> None:
            if index == len(metadata):
                on_done(problems)
                return
            meta = metadata[index]

            def answered(data: dict) -> None:
                verdict = data.get("valid", data.get("isValid"))
                if verdict is False:
                    reason = data.get("message") or "; ".join(str(e) for e in data.get("errors") or []) \
                        or "Mapflow can't process it"
                    problems.append(f"{meta.get('filename', 'image')}: {reason}")
                ask(index + 1)

            def refused(error: ApiError) -> None:
                if error.status in (400, 422) and error.message:
                    problems.append(f"{meta.get('filename', 'image')}: {error.message}")
                ask(index + 1)
            self.api.validate_image(meta, answered, refused)

        ask(0)
