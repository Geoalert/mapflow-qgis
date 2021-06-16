import json

import requests
from PyQt5.QtCore import QObject, pyqtSignal

from .helpers import get_layer_extent, to_wgs84, WGS84


class ProcessingFetcher(QObject):
    """"""
    fetched = pyqtSignal(list)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    processing_created = False

    def __init__(self, url, auth):
        super().__init__()
        self.url = url
        self.auth = auth

    def set_processing_created(self, value):
        self.processing_created = value

    def fetch_processings(self):
        while True:
            if self.thread().isInterruptionRequested():
                self.processing_created = False
                self.finished.emit()
                return
            try:
                r = requests.get(self.url, auth=self.auth)
                r.raise_for_status()
                processings = r.json()
                self.fetched.emit(processings)
                # If a processing was created during the execution, fetch one more time
                if self.processing_created:
                    self.processing_created = False
                    continue
                # If there are ongoing processings, keep polling
                elif [p for p in processings if p['status'] in ("IN_PROGRESS", "UNPROCESSED")]:
                    self.thread().sleep(5)
                    continue
                else:
                    self.finished.emit()
                    break
            except Exception as e:
                self.error.emit(str(e))
                return


class ProcessingCreator(QObject):
    """"""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    tif_uploaded = pyqtSignal(str)

    def __init__(self, processing_name, server, auth, wd, params, transform_context, meta={}, tif=None, aoi_layer=None) -> None:
        super().__init__()
        self.processing_name = processing_name
        self.server = server
        self.auth = auth
        self.tif = tif
        self.wd = wd
        self.params = params
        self.meta = meta
        self.aoi_layer = aoi_layer
        self.transform_context = transform_context

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
            url = r.json()['uri']
            self.params["url"] = url
            self.tif_uploaded.emit(url)
        if self.aoi_layer:
            aoi = next(self.aoi_layer.getFeatures()).geometry()
            # Reproject it to WGS84 if the layer has another CRS
            layer_crs = self.aoi_layer.crs()
            if layer_crs != WGS84:
                aoi = to_wgs84(aoi, layer_crs, self.transform_context)
        else:
            aoi = get_layer_extent(self.tif, self.transform_context)
        # If we pass it as JSON, the URL in params will be urlencoded: e.g. ? -> %3F and the creation will fail
        # To avoid it, we have to convert the body to a string and pass it to the 'data' param instead of 'json'
        # However, Python serializes a dict with single quotes, so the server will see it as invalid JSON
        # To fix this, we have to replace '' in the string with ""
        body = str({
            "name": self.processing_name,
            "wdName": self.wd,
            "geometry": json.loads(aoi.asJson()),
            "params": self.params,
            "meta": self.meta
        }).replace('\'', '"').encode()
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
