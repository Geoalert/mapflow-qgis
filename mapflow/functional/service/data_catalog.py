from typing import Sequence, Union, Optional, Callable
from pathlib import Path
from uuid import UUID
import json

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtNetwork import QNetworkReply

from ...schema.data_catalog import PreviewSize, MosaicCreateSchema, MosaicReturnSchema, ImageReturnSchema
from  ..api.data_catalog_api import DataCatalogApi

class DataCatalogService(QObject):
    """

    """
    mosaicsUpdated = pyqtSignal()

    def __init__(self,
                 api: DataCatalogApi,
                 main_dialog):
        self.api = api
        self.dlg = main_dialog
        self.mosaics = []

    # Mosaics CRUD
    def create_mosaic(self, mosaic: MosaicCreateSchema):
        self.api.create_mosaic(mosaic, callback=self.create_mosaic_callback)

    def create_mosaic_callback(self, response: QNetworkReply):
        self.get_mosaics()

    def get_mosaics(self):
        self.api.get_mosaics(callback=self.get_mosaics_callback)

    def get_mosaics_callback(self, response: QNetworkReply):
        self.mosaics = [MosaicReturnSchema.from_dict(data) for data in json.loads(response.readAll().data())]
        self.mosaicsUpdated.emit()

    def get_mosaic(self, mosaic_id: UUID):
        self.api.get_mosaic(mosaic_id=mosaic_id,
                            callback=self.get_mosaic_callback)

    def get_mosaic_callback(self, response: QNetworkReply):
        pass

    def delete_mosaic(self, mosaic_id: UUID):
        self.api.delete_mosaic(mosaic_id=mosaic_id,
                               callback=self.delete_mosaic_callback)

    def delete_mosaic_callback(self, response: QNetworkReply):
        pass

    # Images CRUD

    def upload_images(self, mosaic_id: UUID, image_paths: Sequence[Union[Path, str]]):
        pass

    def get_mosaic_images(self, mosaic_id: UUID, callback: Callable):
        self.http.get(url=f"{self.server}/rasters/mosaic/{mosaic_id}/image",
                      callback=callback,
                      use_default_error_handler=True
                      )

    def get_image(self, image_id: UUID, callback: Callable):
        self.http.get(url=f"{self.server}/rasters/image/{image_id}",
                      callback=callback,
                      use_default_error_handler=True
                      )

    def delete_image(self, image_id: UUID):
        self.http.delete(url=f"{self.server}/rasters/image/{image_id}",
                      callback=self.delete_image_callback,
                      use_default_error_handler=True
                      )

    def delete_image_callback(self, response: QNetworkReply):
        pass

    def get_image_preview(self,
                          image: ImageReturnSchema,
                          size: PreviewSize,
                          callback: Callable):
        url = image.preview_url_l if size == PreviewSize.large else image.preview_url_s
        self.http.get(url=url,
                      callback=callback,
                      use_default_error_handler=True
                      )

    # Legacy:
    def upload_to_new_mosaic(self, image_path: Union[Path, str]):
        pass

    # Status
    def get_user_limit(self, callback):
        self.http.get(url=f"{self.server}/rasters/memory",
                      callback=callback,
                      use_default_error_handler=True)

