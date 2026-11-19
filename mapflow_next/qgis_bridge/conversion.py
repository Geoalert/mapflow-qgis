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

from qgis.core import (QgsCoordinateTransformContext, QgsFeedback, QgsTask, QgsVectorFileWriter, QgsVectorLayer)

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
    transform_context: QgsCoordinateTransformContext


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


def convert_geojson(job: Job, is_canceled: Callable[[], bool], feedback: QgsFeedback,
                    progress: Callable[[float], None] = lambda _percent: None) -> Converted:
    """Write the GeoJSON to a GeoPackage (one layer per geometry type) and move it to `job.target`. Falls back to
    the GeoJSON file itself if the GeoPackage can't be written. Raises `Cancelled` when `is_canceled()` turns true.
    The output folder never holds a partial file: the writes go to `job.work`, and only a finished file is moved."""
    job.work.parent.mkdir(parents=True, exist_ok=True)

    def stop_if_canceled() -> None:
        if is_canceled() or feedback.isCanceled():
            raise Cancelled()

    try:
        stop_if_canceled()
        normalise_json_fields(str(job.geojson))
        names: List[str] = []
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        options.feedback = feedback             # a long write stops on cancel
        for index, geometry_type in enumerate(GEOMETRY_TYPES):
            stop_if_canceled()
            progress(100.0 * index / len(GEOMETRY_TYPES))
            source = QgsVectorLayer(f"{job.geojson}|geometrytype={geometry_type}", "source", "ogr")
            if not source.isValid() or source.featureCount() == 0:
                del source
                continue
            layer_name = job.name if geometry_type == "Polygon" else f"{job.name} ({geometry_type.lower()}s)"
            options.layerName = layer_name
            options.actionOnExistingFile = (QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteLayer if names
                                            else QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteFile)
            error, *_ = QgsVectorFileWriter.writeAsVectorFormatV3(
                source, str(job.work), job.transform_context, options)
            del source                          # the file is closed before it is moved or removed
            stop_if_canceled()                  # the writer reports a cancel as an error: tell it apart
            if error != QgsVectorFileWriter.WriterError.NoError:
                remove_files(job.work, WORK_SUFFIXES)
                job.geojson.replace(job.fallback)
                return Converted(job.fallback, [job.name], GEOJSON)
            names.append(layer_name)
        progress(100.0)
        if not names:
            return Converted(job.target, [], GPKG)
        stop_if_canceled()
        os.replace(job.work, job.target)        # same disk: the file appears whole or not at all
        return Converted(job.target, names, GPKG)
    finally:
        remove_files(job.work, WORK_SUFFIXES)


_LIVE: Set["ConvertTask"] = set()               # a detached task must not be collected while Qt still runs it


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

    def cancel(self) -> None:
        self.feedback.cancel()                  # first: a write in progress checks the feedback, not the task
        super().cancel()

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
