"""Processing results onto the map: GeoPackage files (default) or streamed vector tiles."""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from qgis.PyQt.QtCore import QObject, QStandardPaths, pyqtSignal
from qgis.core import QgsMapLayer, QgsRectangle

from ..api.client import MapflowApi
from ..core.models import Processing
from ..qgis_bridge.layers import MapLayers, bounds_extent, extent_is_world, features_extent

FILES, TILES = "file", "tiles"


def default_output_dir() -> Path:
    documents = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation) or str(Path.home())
    return Path(documents) / "Mapflow"


class Results(QObject):
    loaded = pyqtSignal(str, list)      # processing id, [layer ids]
    failed = pyqtSignal(str, str)       # processing id, message
    busy = pyqtSignal(str, bool)        # processing id, loading

    def __init__(self, api: MapflowApi, layers: MapLayers, settings, parent=None):
        super().__init__(parent)
        self.api, self.layers, self.settings = api, layers, settings
        self._busy = set()

    @property
    def mode(self) -> str:
        return self.settings.value("results_mode", FILES)

    @property
    def output_dir(self) -> Path:
        return Path(self.settings.value("output_dir", "") or default_output_dir())

    def reset(self) -> None:
        """After sign-out: downloads were aborted, nothing is loading any more."""
        for processing_id in list(self._busy):
            self._set_busy(processing_id, False)

    def is_busy(self, processing_id: str) -> bool:
        return processing_id in self._busy

    def in_map(self) -> set:
        return self.layers.processing_ids_in_map()

    def add_to_map(self, processing: Processing) -> None:
        if not processing.is_done or processing.id in self._busy:
            return
        self._set_busy(processing.id, True)
        if self.mode == TILES:
            vector = self.layers.vector_tiles(processing)
            if vector is None:
                self._fail(processing, "These results can't be streamed. Switch to files in Settings.")
                return
            # A vector tile layer covers the whole world until told otherwise: give it the results'
            # extent (its tilejson bounds, as the current plugin does, else the processing's area)
            # so the map shows the results, not the planet

            def with_extent(extent):
                if extent is not None:
                    vector.setExtent(extent)
                self._with_imagery(processing, [vector])

            def from_tilejson(tilejson):
                extent = bounds_extent((tilejson or {}).get("bounds"))
                if extent is None or extent_is_world(extent):
                    self._area_extent(processing, with_extent)
                else:
                    with_extent(extent)

            if processing.vector_tilejson_url:
                self.api.tilejson(processing.vector_tilejson_url, from_tilejson,
                                  lambda _error: self._area_extent(processing, with_extent))
            else:
                self._area_extent(processing, with_extent)
            return
        folder = self.output_dir
        try:
            downloads = folder / ".downloads"
            downloads.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self._fail(processing, f"Can't write to {folder}: {exc.strerror}. Pick another folder in Settings.")
            return
        target = str(downloads / f"{processing.id}.geojson")

        def downloaded(path: str):
            vectors = self.layers.save_results(path, processing, folder)
            try:
                Path(path).unlink(missing_ok=True)
            except OSError:
                pass
            if not vectors:
                self._set_busy(processing.id, False)
                self.failed.emit(processing.id, "The processing returned no features.")
                return
            self._with_imagery(processing, vectors)

        self.api.download_result(processing.id, target, downloaded,
                                 lambda error: self._fail(processing, f"Results didn't download: {error.message}"))

    def _with_imagery(self, processing: Processing, vectors: list) -> None:
        """Add the source imagery under the results (its extent comes from the tilejson), then zoom."""
        def finish(raster: Optional[QgsMapLayer]):
            added = []
            if raster is not None:
                added.append(self.layers.add(raster, processing.id))
            for vector in reversed(vectors):
                added.append(self.layers.add(vector, processing.id))
            self.layers.zoom_to([layer for layer in added if not layer.extent().isEmpty()] or added)
            self._set_busy(processing.id, False)
            self.loaded.emit(processing.id, [layer.id() for layer in added])

        if not processing.raster_tile_url:
            finish(None)
            return
        name = f"{processing.name} · imagery"

        def with_extent(tilejson: dict):
            finish(self.layers.tile_raster(processing.raster_tile_url, name,
                                           bounds_extent((tilejson or {}).get("bounds")),
                                           int((tilejson or {}).get("maxzoom") or 21)))

        if processing.raster_tilejson_url:
            self.api.tilejson(processing.raster_tilejson_url, with_extent,
                              lambda _error: finish(self.layers.tile_raster(processing.raster_tile_url, name)))
        else:
            finish(self.layers.tile_raster(processing.raster_tile_url, name))

    def _area_extent(self, processing: Processing, then: Callable[[Optional[QgsRectangle]], None]) -> None:
        """The bounding box of the processing's area (EPSG:3857), from Mapflow; None if it can't be had."""
        def done(collection: dict):
            then(features_extent(collection))
        self.api.processing_aois(processing.id, done, lambda _error: then(None))

    def save_geojson(self, processing: Processing, path: str, done: Callable[[str], None]) -> None:
        self._set_busy(processing.id, True)

        def ok(saved: str):
            self._set_busy(processing.id, False)
            done(saved)

        self.api.download_result(processing.id, path, ok,
                                 lambda error: self._fail(processing, f"Results didn't download: {error.message}"))

    def _fail(self, processing: Processing, message: str) -> None:
        self._set_busy(processing.id, False)
        self.failed.emit(processing.id, message)

    def _set_busy(self, processing_id: str, busy: bool) -> None:
        (self._busy.add if busy else self._busy.discard)(processing_id)
        self.busy.emit(processing_id, busy)
