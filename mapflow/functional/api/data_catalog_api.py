from typing import Union, Callable, Optional
from pathlib import Path
from uuid import UUID
import tempfile

from PyQt5.QtCore import QObject, pyqtSignal, QFile, QIODevice
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest, QHttpMultiPart, QHttpPart
from PyQt5.QtWidgets import QApplication
from qgis.core import QgsMapLayer, QgsProject, QgsSettings

from ...schema.data_catalog import PreviewSize, MosaicCreateSchema, MosaicReturnSchema, ImageReturnSchema
from ...http import Http
from ...functional import layer_utils
from ...config import Config
from ...dialogs.dialogs import ErrorMessageWidget
from ...dialogs.main_dialog import MainDialog


class DataCatalogApi(QObject):
    """

    """
    mosaicsUpdated = pyqtSignal()

    def __init__(self,
                 http: Http,
                 server: str,
                 dlg: MainDialog,
                 iface):
        super().__init__()
        self.server = server
        self.http = http
        self.iface = iface
        self.dlg = dlg
        self.result_loader = layer_utils.ResultsLoader(iface=self.iface,
                                                       maindialog=self.dlg,
                                                       http=self.http,
                                                       server=self.server,
                                                       project=QgsProject.instance(),
                                                       settings=QgsSettings(),
                                                       plugin_name=Config().PLUGIN_NAME,
                                                       temp_dir=tempfile.gettempdir()
                                                       )

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
        
    def request_mosaic_extent(self,
                             tilejson_uri: str,
                             layer: QgsMapLayer,
                             errors: bool = False,
                             processing_id: Optional[str] = None
                             ):
        self.http.get(url=tilejson_uri,
                      callback=self.add_mosaic_with_extent,
                      callback_kwargs={"layer": layer,
                                       "processing_id": processing_id,
                                       "errors": errors},
                      error_handler=self.add_mosaic_with_extent,
                      error_handler_kwargs={"layer": layer,
                                            "processing_id": processing_id,
                                            "errors": errors},
                      use_default_error_handler=False,
                      )
    
    def add_mosaic_with_extent(self,
                                response: QNetworkReply,
                                layer: QgsMapLayer,
                                errors: bool = False,
                                processing_id: Optional[str] = None
                                ) -> None:
        if response.error() != QNetworkReply.NoError:
            errors = True
        else:
            try:
                bounding_box = layer_utils.get_bounding_box_from_tile_json(response=response)
            except Exception as e:
                errors = True
            else:
                layer.setExtent(rect=bounding_box)
                self.result_loader.add_layer(layer)
            self.iface.setActiveLayer(layer)
            self.iface.zoomToActiveLayer()
        if errors:
            error_summary =  self.tr('Failed to load mosaic \n'
                                     'please try again later or report error').format(processing_id)
            title = self.tr("Error")
            email_body = "Error while loading results layer." \
                        f"Processing id: {processing_id}"
            ErrorMessageWidget(parent=QApplication.activeWindow(),
                            text=error_summary,
                            title=title,
                            email_body=email_body).show()

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
                      use_default_error_handler=True
                      )

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
