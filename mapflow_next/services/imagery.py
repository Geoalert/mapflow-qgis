"""Imagery catalog search and the user's own imagery (My imagery)."""
from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional, Set

from qgis.PyQt.QtCore import QObject, pyqtSignal

from ..api.client import MapflowApi
from ..api.http import ApiError
from ..core.models import CatalogImage, Mosaic, MosaicImage


class Imagery(QObject):
    searchDone = pyqtSignal(list, int)        # [CatalogImage], total
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
        self.mosaics: List[Mosaic] = []
        self.images: Dict[str, List[MosaicImage]] = {}
        self._images_loading: Set[str] = set()
        self.uploading = False

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
        self.api.search_catalog(request, self._found, lambda error: self.searchFailed.emit(error.message))

    def _found(self, images: List[CatalogImage], total: int) -> None:
        self.results = images
        self.searchDone.emit(images, total)

    def get_result(self, image_id: str) -> Optional[CatalogImage]:
        return next((i for i in self.results if i.id == image_id), None)

    def load_mosaics(self) -> None:
        self.api.mosaics(self._on_mosaics, on_error=lambda e: None)

    def _on_mosaics(self, mosaics: List[Mosaic]) -> None:
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
