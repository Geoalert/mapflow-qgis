from typing import Union, Callable, Optional
from pathlib import Path
from uuid import UUID

from PyQt5.QtCore import QObject, pyqtSignal, QFile, QIODevice
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest, QHttpMultiPart, QHttpPart

from ...schema.data_catalog import PreviewSize, MosaicCreateSchema, MosaicReturnSchema, ImageReturnSchema
from ...http import Http

class DataCatalogApi(QObject):
    """

    """
    mosaicsUpdated = pyqtSignal()

    def __init__(self,
                 http: Http,
                 server: str):
        super().__init__()
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

    def delete_mosaic(self,
                      mosaic_id: UUID,
                      callback: Callable = lambda *args: None,
                      callback_kwargs: Optional[dict] = None):
        self.http.delete(url=f"{self.server}/rasters/mosaic/{mosaic_id}",
                          callback=callback,
                          use_default_error_handler=True,
                          callback_kwargs=callback_kwargs or {}
                      )
    # Images CRUD
    def upload_image(self,
                     mosaic_id: UUID,
                     image_path: Union[Path, str],
                     callback: Callable = lambda *args: None,
                     callback_kwargs: Optional[dict] = None,
                     error_handler: Optional[Callable] = None,
                     error_handler_kwargs: Optional[dict] = None):
        body = self.create_upload_image_body(image_path = image_path)
        url = f"{self.server}/rasters/mosaic/{mosaic_id}/image"
        self.http.post(url=url,
                       body=body,
                       callback=callback,
                       callback_kwargs=callback_kwargs,
                       use_default_error_handler=error_handler is None,
                       error_handler=error_handler,
                       error_handler_kwargs=error_handler_kwargs or {}
                       )

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
                      use_default_error_handler=False,
                      error_handler=self.preview_s_error_handler
                      )

    def preview_s_error_handler(self, image):
        if not image.preview_url_s:
            self.dlg.imagePreview.setText("Preview is unavailable")

    # Legacy:
    def upload_to_new_mosaic(self,
                             image_path: Union[Path, str],
                             callback: Callable,
                             callback_kwargs: Optional[dict] = None):
        url = f"{self.server}/rasters"
        body = self.create_upload_image_body(image_path=image_path)
        self.http.post(url=url,
                       callback=callback,
                       callback_kwargs=callback_kwargs,
                       body=body,
                       timeout=3600  # one hour
                       )

    # Status
    def get_user_limit(self, callback):
        self.http.get(url=f"{self.server}/rasters/memory",
                      callback=callback,
                      use_default_error_handler=True)

    @staticmethod
    def create_upload_image_body(image_path):
        body = QHttpMultiPart(QHttpMultiPart.FormDataType)
        tif = QHttpPart()
        tif.setHeader(QNetworkRequest.ContentTypeHeader, 'image/tiff')
        filename = Path(image_path).name
        tif.setHeader(QNetworkRequest.ContentDispositionHeader, f'form-data; name="file"; filename="{filename}"')
        image = QFile(image_path, body)
        image.open(QIODevice.ReadOnly)
        tif.setBodyDevice(image)
        body.append(tif)
        return body
