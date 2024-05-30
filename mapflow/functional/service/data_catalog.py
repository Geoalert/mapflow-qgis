from typing import Sequence, Union, Optional, Callable
from pathlib import Path
from uuid import UUID
import json

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtNetwork import QNetworkReply

from ...schema.data_catalog import PreviewSize, MosaicCreateSchema, MosaicReturnSchema, ImageReturnSchema
from ..api.data_catalog_api import DataCatalogApi
from ...http import Http


class DataCatalogService(QObject):
    """
    A service for querying mapflow data catalog.
    It depends on DataCatalogApi to send requests, and implements the loginc behind the data catalog use.
    Where possible, the service specifies api error handlers/callbacks.

    It also stores the mosaic in memory as a dict with mosaic_id as the key for access from other places.
    todo: maybe move storage to some repo/localstorage layer?
    """
    mosaicsUpdated = pyqtSignal()

    def __init__(self,
                 http: Http,
                 server: str):
        self.api = DataCatalogApi(http=http, server=server)
        self.mosaics = {}

    # Mosaics CRUD
    def create_mosaic(self, mosaic: MosaicCreateSchema):
        self.api.create_mosaic(mosaic, callback=self.create_mosaic_callback)

    def create_mosaic_callback(self, response: QNetworkReply):
        self.get_mosaics()

    def get_mosaics(self):
        self.api.get_mosaics(callback=self.get_mosaics_callback)

    def get_mosaics_callback(self, response: QNetworkReply):
        for data in json.loads(response.readAll().data()):
            mosaic = MosaicReturnSchema.from_dict(data)
            self.mosaics[mosaic.id] = mosaic
        self.mosaicsUpdated.emit()

    def get_mosaic(self, mosaic_id: UUID):
        self.api.get_mosaic(mosaic_id=mosaic_id,
                            callback=self.get_mosaic_callback)

    def get_mosaic_callback(self, response: QNetworkReply):
        mosaic = MosaicReturnSchema.from_dict(response.readAll().data())
        self.mosaics.update({mosaic.id: mosaic})
        self.mosaicsUpdated.emit()

    def delete_mosaic(self, mosaic_id: UUID):
        self.api.delete_mosaic(mosaic_id=mosaic_id,
                               callback=self.delete_mosaic_callback,
                               callback_kwargs={'mosaic_id': mosaic_id})

    def delete_mosaic_callback(self, response: QNetworkReply, mosaic_id: UUID):
        self.mosaics.pop(mosaic_id)
        self.mosaicsUpdated.emit()

    # Images CRUD

    def upload_images(self,
                      mosaic_id: UUID,
                      image_paths: Sequence[Union[Path, str]],
                      upoaded: Sequence[Union[Path, str]],
                      failed: Sequence[Union[Path, str]]):
        if not image_paths:
            return

        image_to_upload = image_paths[0]
        non_uploaded = image_paths[1:]

        self.api.upload_image(mosaic_id=mosaic_id,
                              image_path=image_to_upload,
                              callback=self.upload_images,
                              callback_kwargs={'mosaic_id': mosaic_id,
                                               'image_paths': non_uploaded,
                                               'uploaded': list(upoaded) + [image_to_upload],
                                               'failed': failed},
                              error_handler=self.upload_images,
                              error_handler_kwargs={'mosaic_id': mosaic_id,
                                                    'image_paths': non_uploaded,
                                                    'uploaded': upoaded,
                                                    'failed': list(failed) + [image_to_upload]},
                              )

        for image_path in non_uploaded:
            self.api.upload_image(mosaic_id=mosaic_id, image_path=image_path)

    def get_mosaic_images(self, mosaic_id: UUID, callback: Callable):
        self.api.get_mosaic_images(mosaic_id=mosaic_id, callback=callback)

    def get_image(self, image_id: UUID, callback: Callable):
        self.api.get_image(image_id=image_id, callback=callback)

    def delete_image(self, image_id: UUID):
        self.api.delete_image(image_id=image_id, callback=self.delete_image_callback)

    def delete_image_callback(self, response: QNetworkReply):
        pass

    def get_image_preview(self,
                          image: ImageReturnSchema,
                          size: PreviewSize,
                          callback: Callable):
        self.api.get_image_preview(image=image, size=size, callback=callback)

    # Legacy:
    def upload_to_new_mosaic(self,
                             image_path: Union[Path, str],
                             callback: Callable):
        self.api.upload_to_new_mosaic(image_path=image_path,
                                      callback=callback)

    # Status
    def get_user_limit(self, callback):
        self.api.get_user_limit(callback=callback)
