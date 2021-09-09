import os
import json
from typing import Any, Dict, Tuple

import requests
from PyQt5.QtCore import QObject, pyqtSignal
from qgis.core import QgsMessageLog, Qgis, QgsGeometry, QgsRasterLayer

from . import config


class ProcessingFetcher(QObject):
    """A worker that continiously polls Mapflow to refresh the user's processings status."""

    fetched = pyqtSignal(list)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, url: str, auth: Tuple[str, str]) -> None:
        """Initialize the worker with a URL and basic auth.

        :param url: The Mapflow server URL
        :param auth: A (login, password) tuple for user authentication
        """
        super().__init__()
        self.url = url
        self.auth = auth

    def fetch_processings(self) -> None:
        """Keep polling Mapflow to retrieve the current status for each of the user's processings.

        Start an infinite loop that requests the user's processings and if any of those haven't finished,
        waits for <PROCESSING_LIST_REFRESH_INTERVAL> and continues, or breaks otherwise. It also checks at
        the start of iteration if interuption has been requested, and if so, breaks too.

        After every successful processing fetch, it sends a signal to the main thread and supplies the fetched
        processings in a JSON-formatted dict for the main thread to fill out the processings table.
        """
        while True:
            if self.thread().isInterruptionRequested():
                self.finished.emit()
                return
            try:
                r = requests.get(self.url, auth=self.auth, timeout=10)
                r.raise_for_status()
                processings = r.json()
                self.fetched.emit(processings)
                # If there are ongoing processings, keep polling
                if [p for p in processings if p['status'] in ("IN_PROGRESS", "UNPROCESSED")]:
                    self.thread().sleep(config.PROCESSING_LIST_REFRESH_INTERVAL)
                    continue
                self.finished.emit()
                break
            except Exception as e:
                self.error.emit(str(e))
                return


class ProcessingCreator(QObject):
    """A worker that posts a 'create processing' request to Mapflow."""

    finished = pyqtSignal()
    error = pyqtSignal(str)
    tif_uploaded = pyqtSignal(str)

    def __init__(
        self, processing_name: str, server: str, auth: Tuple[str, str], wd: str,
        params: Dict[str, Any], aoi: QgsGeometry, tif: QgsRasterLayer = None, meta: Dict[str, str] = {}
    ) -> None:
        """Initialize the worker.

        :param processing name: A name for the processing (can be in any language)
        :param server: Mapflow URL
        :param auth: A (login, password) tuple for user authentication
        :param wd: The name of one of the workflow definitions present in the user's default project
        :param params: A dictionary containing the various parameters for the processing;
            contains the source imagery type ['wms', 'tms', 'xyz', 'quadkey', 'tif'],
            the custom provider URL, login and password (if custom provider is used),
            caching policy specification and the target imagery resolution in the case of WMS
        :param aoi: A geometry within which the imagery will be processed
        :param tif: A GeoTIFF-based raster layer that'll be used as source imagery
        :param meta: Optional attributes that describe the processing
        """
        super().__init__()
        self.processing_name = processing_name
        self.server = server
        self.auth = auth
        self.aoi = aoi
        self.tif = tif
        self.wd = wd
        self.params = params
        self.meta = meta

    def create_processing(self):
        """Initiate a processing."""
        if self.thread().isInterruptionRequested():
            self.finished.emit()
            return
        if self.tif:
            # Upload the image to the server
            try:
                with open(self.tif.dataProvider().dataSourceUri(), 'rb') as f:
                    r = requests.post(f'{self.server}/rest/rasters', auth=self.auth, files={'file': f})
                r.raise_for_status()
            except Exception as e:
                self.error.emit(str(e))
                return
            url = r.json()['url' if 'url' in r.json() else 'uri']  # may depend on the Mapflow environment
            self.params["url"] = url
            self.tif_uploaded.emit(url)
        # If we pass it as JSON, the URL in params will be urlencoded: e.g. ? -> %3F and the creation will fail
        # To avoid it, we have to convert the body to a string and pass it to the 'data' param instead of 'json'
        # However, Python serializes a dict with single quotes, so the server will see it as invalid JSON
        # To fix this, we have to replace '' in the string with ""
        body = str({
            "name": self.processing_name,
            "wdName": self.wd,
            "geometry": json.loads(self.aoi.asJson()),
            "params": self.params,
            "meta": self.meta
        }).replace('\'', '"').encode()
        if os.getenv('MAPFLOW_QGIS_ENV'):
            QgsMessageLog.logMessage(body.decode(), config.PLUGIN_NAME, level=Qgis.Info)
        # Post the processing
        try:
            r = requests.post(
                url=f'{self.server}/rest/processings',
                headers={'Content-Type': 'application/json'},
                auth=self.auth,
                data=body)
            r.raise_for_status()
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
