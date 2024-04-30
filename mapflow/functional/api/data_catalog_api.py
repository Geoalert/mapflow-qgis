from typing import Union, Callable
from pathlib import Path
from uuid import UUID

from PyQt5.QtCore import QObject, pyqtSignal

from ..schema.data_catalog import PreviewSize, MosaicCreateSchema, MosaicReturnSchema, ImageReturnSchema
from ..http import Http

class DataCatalogApi(QObject):
    """

    """
    mosaicsUpdated = pyqtSignal()

    def __init__(self,
                 http: Http,
                 server: str):
        self.server = server
        self.http = http

    # Mosaics CRUD
    def create_mosaic(self, mosaic: MosaicCreateSchema, callback: Callable = lambda *args: None):
        self.http.post(url=f"{self.server}/rasters/mosaic",
                       body=mosaic.as_json().encode(),
                       headers={},
                       callback=callback,
                       use_default_error_handler=True,
                       timeout=5)

    def get_mosaics(self, callback: Callable):
        self.http.get(url=f"{self.server}/rasters/mosaic",
                      callback=callback,
                      use_default_error_handler=True)

    def get_mosaic(self, mosaic_id: UUID, callback: Callable):
        self.http.get(url=f"{self.server}/rasters/mosaic/{mosaic_id}",
                      callback=callback,
                      use_default_error_handler=True
                      )

    def delete_mosaic(self, mosaic_id: UUID, callback: Callable = lambda *args: None):
        self.http.delete(url=f"{self.server}/rasters/mosaic/{mosaic_id}",
                      callback=callback,
                      use_default_error_handler=True
                      )
    # Images CRUD
    def upload_image(self, mosaic_id: UUID, image_path: Union[Path, str], callback: Callable = lambda *args: None):
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

    def delete_image(self, image_id: UUID, callback: Callable = lambda *args: None):
        self.http.delete(url=f"{self.server}/rasters/image/{image_id}",
                      callback=callback,
                      use_default_error_handler=True
                      )

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

