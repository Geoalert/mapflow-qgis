"""Converting a downloaded result to a GeoPackage in a `QgsTask`, so QGIS stays usable while a result of
hundreds of megabytes is read and written (spec/005 § QGIS Application).

Everything the worker needs is a value copied on the GUI thread (`Job`). The worker touches no project, no
widget and no message bar; the GUI thread reports (`ConvertTask.finished`) and opens the finished file."""
from __future__ import annotations

import json
import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set

from osgeo import gdal, ogr
from qgis.core import QgsFeedback, QgsTask

from ..core.guard import guarded
from .compat import TASK_CAN_CANCEL

GEOMETRY_TYPES = ("Polygon", "LineString", "Point")
WORK_SUFFIXES = ("", "-wal", "-shm", "-journal")       # a GeoPackage and the files SQLite keeps beside it
LARGE_JSON_BYTES = 200 * 1024 * 1024

GPKG, GEOJSON = "gpkg", "geojson"


class Cancelled(Exception):
    """The conversion stopped because the task was cancelled."""


@dataclass(frozen=True)
class Job:
    """What a conversion needs, copied on the GUI thread: no layer, no widget."""
    geojson: Path                           # the downloaded result
    name: str                               # the processing's name: the first layer's name
    work: Path                              # where the GeoPackage is written, in `.downloads/`
    target: Path                            # where the finished GeoPackage goes
    fallback: Path                          # where the GeoJSON goes when it can't be converted


@dataclass(frozen=True)
class Converted:
    path: Path
    layer_names: List[str]
    kind: str                               # GPKG, or GEOJSON for the fallback


def work_path(downloads: Path, processing_id: str) -> Path:
    """The work file of one conversion. The random part keeps a task that is still stopping from meeting the
    file of a new task of the same processing."""
    return downloads / f"{processing_id}-{secrets.token_hex(4)}.gpkg"


def remove_files(path: Path, suffixes=("",)) -> None:
    for suffix in suffixes:
        try:
            Path(f"{path}{suffix}").unlink(missing_ok=True)
        except OSError:
            pass                            # a file that can't be removed must not hide the task's real outcome


def normalise_json_fields(path: str) -> None:
    """Nested objects (e.g. Open Data `bbox`) become strings: GeoPackage has no JSON type.
    Very large results skip this (they come from models that return flat attributes)."""
    try:
        if Path(path).stat().st_size > LARGE_JSON_BYTES:
            return

        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return
    changed = False
    for feature in data.get("features") or []:
        properties: Dict = feature.get("properties") or {}
        for key, value in list(properties.items()):
            if isinstance(value, (dict, list)):
                properties[key] = json.dumps(value)
                changed = True
    if changed:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle)


def _close_dataset(dataset) -> bool:
    close = getattr(dataset, "Close", None)  # older bundled GDAL releases close on reference release
    return close is None or close() in (None, gdal.CE_None)


def _write_geometry_layers(job: Job, stop_if_canceled: Callable[[], None],
                           report_progress: Callable[..., int]) -> Optional[List[str]]:
    """Write through GDAL so QGIS's OGR iterator cache cannot retain a Windows lock on the download."""
    try:
        source = gdal.OpenEx(str(job.geojson), gdal.OF_VECTOR, allowed_drivers=["GeoJSON"])
    except RuntimeError:
        return []
    if source is None:
        return []

    layer = None
    try:
        layer = source.GetLayer(0)
        if layer is None:
            return []
        source_name = layer.GetName().replace("\\", "\\\\").replace('"', '\\"')
        mixed = ogr.GT_Flatten(layer.GetGeomType()) == ogr.wkbUnknown
        names: List[str] = []
        for index, geometry_type in enumerate(GEOMETRY_TYPES):
            stop_if_canceled()
            kind = geometry_type.upper()
            where = f"OGR_GEOMETRY IN ('{kind}', 'MULTI{kind}')"
            layer.SetAttributeFilter(where)
            if layer.GetFeatureCount() == 0:
                continue
            geometry = None
            if mixed:
                # GeoPackage layers need a declared geometry family even when GeoJSON mixes families.
                layer.SetAttributeFilter(f"OGR_GEOMETRY = 'MULTI{kind}'")
                geometry = f"MULTI{kind}" if layer.GetFeatureCount() else kind
            layer.SetAttributeFilter(None)
            layer_name = job.name if geometry_type == "Polygon" else f"{job.name} ({geometry_type.lower()}s)"
            # OGRSQL reports a fast feature count for the filtered result, which GDAL needs to call progress.
            selection = f'SELECT * FROM "{source_name}" WHERE {where}'
            output = None
            try:
                output = gdal.VectorTranslate(str(job.work), source, format="GPKG", layerName=layer_name,
                                              accessMode="append" if names else None,
                                              SQLStatement=selection, SQLDialect="OGRSQL",
                                              geometryType=geometry, callback=report_progress, callback_data=index)
                written = output is not None and _close_dataset(output)
            except RuntimeError:
                written = False
            finally:
                del output
            stop_if_canceled()                  # GDAL also reports cancellation as a write error
            if not written:
                return None
            names.append(layer_name)
        return names
    finally:
        del layer
        try:
            _close_dataset(source)
        finally:
            del source


def convert_geojson(job: Job, is_canceled: Callable[[], bool], feedback: QgsFeedback,
                    progress: Callable[[float], None] = lambda _percent: None) -> Converted:
    """Write the GeoJSON to a GeoPackage (one layer per geometry type) and move it to `job.target`. Falls back to
    the GeoJSON file itself if the GeoPackage can't be written. Raises `Cancelled` when `is_canceled()` turns true.
    The output folder never holds a partial file: the writes go to `job.work`, and only a finished file is moved."""
    job.work.parent.mkdir(parents=True, exist_ok=True)

    def canceled() -> bool:
        return is_canceled() or feedback.isCanceled()

    def stop_if_canceled() -> None:
        if canceled():
            raise Cancelled()

    def report_progress(fraction: float, _message: str, index: int) -> int:
        progress(100.0 * (index + fraction) / len(GEOMETRY_TYPES))
        return int(not canceled())

    try:
        stop_if_canceled()
        normalise_json_fields(str(job.geojson))
        remove_files(job.work, WORK_SUFFIXES)
        names = _write_geometry_layers(job, stop_if_canceled, report_progress)
        stop_if_canceled()
        if names is None:
            job.geojson.replace(job.fallback)
            return Converted(job.fallback, [job.name], GEOJSON)
        progress(100.0)
        if not names:
            return Converted(job.target, [], GPKG)
        stop_if_canceled()
        os.replace(job.work, job.target)        # same disk: the file appears whole or not at all
        return Converted(job.target, names, GPKG)
    finally:
        remove_files(job.work, WORK_SUFFIXES)


_LIVE: Set["ConvertTask"] = set()               # a detached task must not be collected while Qt still runs it


def claimed(path: Path) -> bool:
    """True when `path` is the target or the fallback of a live task. The names stay claimed while the task is
    live, because a cancelled task may still move or remove files after a new add of the same processing began."""
    return any(path in (task.job.target, task.job.fallback) for task in _LIVE)


class ConvertTask(QgsTask):
    """Runs `convert_geojson` on a worker thread. `callback(task)` runs once on the GUI thread when it ends,
    with `result` set on success, `error` set when the worker raised, and neither when it was cancelled."""

    def __init__(self, job: Job, callback: Callable[["ConvertTask"], None]):
        super().__init__(f"Mapflow: converting “{job.name}”", TASK_CAN_CANCEL)
        self.job = job
        self.feedback = QgsFeedback()
        self.result: Optional[Converted] = None
        self.error: Optional[Exception] = None
        self._callback: Optional[Callable[["ConvertTask"], None]] = callback
        self._detached = False
        _LIVE.add(self)

    def run(self) -> bool:
        # Worker thread. An exception that leaves a Python `run` is not reported to the plugin and would leave the
        # processing "loading", so it is kept for the GUI thread, which reports it. Nothing here touches a widget,
        # the message bar or the guard: they are not thread-safe.
        try:
            self.result = convert_geojson(self.job, self.isCanceled, self.feedback, self.setProgress)
        except Cancelled:
            return False
        except Exception as exc:  # noqa: BLE001
            self.error = exc
            return False
        return not self.isCanceled()

    @guarded
    def cancel(self) -> None:
        try:
            self.feedback.cancel()              # first: a write in progress checks the feedback, not the task
        finally:
            super().cancel()                    # the task stops even when the feedback raised

    @guarded
    def finished(self, ok: bool) -> None:
        """GUI thread. The cleanup comes before anything that can raise: the callback is reported by the guard,
        and what it interrupts is not completed (spec/006)."""
        _LIVE.discard(self)
        if not ok or self._detached:
            self.discard()
            self.result = None                  # what was made is gone: the callback sees a cancel or an error
        else:
            remove_files(self.job.geojson)
        callback, self._callback = self._callback, None
        if callback is not None:
            callback(self)

    def detach(self) -> None:
        """Drop the callback: nobody is waiting for the outcome (sign-out, unload)."""
        self._callback = None
        self._detached = True

    def discard(self) -> None:
        """Remove every file the task made or was given. Safe to call twice, and after the worker has stopped."""
        remove_files(self.job.work, WORK_SUFFIXES)
        remove_files(self.job.geojson)
        if self.result is not None and self.result.layer_names:
            remove_files(self.result.path)      # a result that was moved into place before the cancel was seen

    def release(self) -> None:
        """Let go of a task that has ended without `finished` running (see `Results.stop`)."""
        _LIVE.discard(self)
