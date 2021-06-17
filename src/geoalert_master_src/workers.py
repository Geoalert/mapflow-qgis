import json

import requests
from PyQt5.QtCore import QObject, pyqtSignal


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

    def __init__(self, processing_name, server, auth, wd, params, aoi, tif=None, meta={}) -> None:
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
            url = r.json()['uri']
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
