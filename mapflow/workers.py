import json
from typing import Any, Dict, Tuple

import requests
from PyQt5.QtCore import QObject, pyqtSignal
from qgis.core import QgsGeometry, QgsRasterLayer


class ProcessingCreator(QObject):
    """A worker that posts a 'create processing' request to Mapflow."""

    finished = pyqtSignal()
    maxar_unauthorized = pyqtSignal()
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
