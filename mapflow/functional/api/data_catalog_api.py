from typing import Union, Callable, Optional
import json
from pathlib import Path
from uuid import UUID

from PyQt5.QtCore import QObject, pyqtSignal, QFile, QIODevice
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest, QHttpMultiPart, QHttpPart
from PyQt5.QtWidgets import QApplication, QProgressBar
from qgis.core import QgsMapLayer, QgsRectangle

from ...schema.data_catalog import PreviewSize, MosaicCreateSchema, ImageReturnSchema, MosaicUpdateSchema
from ...http import Http, get_error_report_body, data_catalog_message_parser
from ...functional import layer_utils
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
                 iface,
                 result_loader,
                 plugin_version):
        super().__init__()
        self.server = server
        self.http = http
        self.iface = iface
        self.dlg = dlg
        self.result_loader = result_loader
        self.plugin_version = plugin_version

    # Mosaics CRUD
    def create_mosaic(self, mosaic: MosaicCreateSchema, callback: Callable = lambda *args: None):
        self.http.post(url=f"{self.server}/rasters/mosaic",
                       body=mosaic.as_json().encode(),
                       headers={},
                       callback=callback,
                       use_default_error_handler=True,
                       timeout=5
                      )
    
    def create_mosaic_from_images(self, 
                                  mosaic: MosaicCreateSchema, 
                                  callback: Callable = lambda *args: None, 
                                  callback_kwargs: Optional[dict] = None,
                                  error_handler: Optional[Callable] = None,
                                  error_handler_kwargs: Optional[dict] = None,
                                  image_paths = None):
        if mosaic.tags:
            tags_str = '%2C%20'.join(mosaic.tags) # separation with ', '
        else:
            tags_str = ''
        body = self.create_upload_image_body(image_path = image_paths[0])
        url = f"{self.server}/rasters/mosaic/image?name={mosaic.name}&tags={tags_str}"
        response = self.http.post(url=url,
                                  body=body,
                                  callback=callback,
                                  callback_kwargs=callback_kwargs,
                                  use_default_error_handler=error_handler is None,
                                  error_handler=error_handler,
                                  error_handler_kwargs=error_handler_kwargs or {},
                                  timeout=3600
                                 )
        body.setParent(response)
        # Disolay progress for first image
        progressMessageBar = self.iface.messageBar().createMessage(f"Uploading image 1/{len(image_paths)}:")
        progress = QProgressBar()
        progressMessageBar.layout().addWidget(progress)
        self.iface.messageBar().pushWidget(progressMessageBar)
        def display_upload_progress(bytes_sent: int, bytes_total: int):
            try:
                progress.setValue(round(bytes_sent / bytes_total * 100))
            except ZeroDivisionError:
                return
            if bytes_total > 0:
                if bytes_sent == bytes_total:
                    self.iface.messageBar().popWidget(progressMessageBar)
        connection = response.uploadProgress.connect(display_upload_progress)
        progressMessageBar.destroyed.connect(lambda: response.uploadProgress.disconnect(connection))

    def get_mosaics(self, callback: Callable):
        self.http.get(url=f"{self.server}/rasters/mosaic",
                      callback=callback,
                      use_default_error_handler=True
                     )

    def get_mosaic(self, mosaic_id: UUID, callback: Callable):
        self.http.get(url=f"{self.server}/rasters/mosaic/{mosaic_id}",
                      callback=callback,
                      use_default_error_handler=False
                     )
    
    def update_mosaic(self, mosaic_id, mosaic: MosaicUpdateSchema, callback: Callable, callback_kwargs: Optional[dict] = None):
        self.http.put(url=f"{self.server}/rasters/mosaic/{mosaic_id}",
                       body=mosaic.as_json().encode(),
                       headers={},
                       callback=callback,
                       callback_kwargs=callback_kwargs,
                       use_default_error_handler=True,
                       timeout=5
                      )

    def delete_mosaic(self,
                      mosaic_id: UUID,
                      callback: Callable = lambda *args: None,
                      callback_kwargs: Optional[dict] = None,
                      error_handler: Optional[Callable] = None,
                      error_handler_kwargs: Optional[dict] = None):
        self.http.delete(url=f"{self.server}/rasters/mosaic/{mosaic_id}",
                         callback=callback,
                         callback_kwargs=callback_kwargs or {},
                         use_default_error_handler=error_handler is None,
                         error_handler=error_handler,
                         error_handler_kwargs=error_handler_kwargs or {}
                        )

    def delete_mosaic_error_handler(self, mosaics: list):
        if len(mosaics) == 1:
            title = self.tr("Error")
            message = self.tr("Could not delete imagery collection '{mosaic_name}'").format(mosaic_name=mosaics[0])
        else:
            title = self.tr("Error. Could not delete following imagery collections:")
            message = ', \n'.join(mosaics)
        ErrorMessageWidget(parent=QApplication.activeWindow(),
                           text=message,
                           title=title,
                           email_body='').show()
        
    def request_mosaic_extent(self,
                              tilejson_uri: str,
                              layer: QgsMapLayer,
                              errors: bool = False,
                              mosaic_id: Optional[str] = None):
        self.http.get(url=tilejson_uri,
                      callback=self.add_mosaic_with_extent,
                      callback_kwargs={"layer": layer,
                                       "mosaic_id": mosaic_id,
                                       "errors": errors},
                      error_handler=self.add_mosaic_with_extent,
                      error_handler_kwargs={"layer": layer,
                                            "mosaic_id": mosaic_id,
                                            "errors": errors},
                      use_default_error_handler=False,
                     )
    
    def add_mosaic_with_extent(self,
                               response: QNetworkReply,
                               layer: QgsMapLayer,
                               errors: bool = False,
                               mosaic_id: Optional[str] = None) -> None:
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
            error_summary =  self.tr('Failed to load imagery collection. \n'
                                     'Please try again later or report error').format(mosaic_id)
            title = self.tr("Error")
            email_body = "Error while loading an imagery collection." \
                        f"Collection id: {mosaic_id}"
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
                     error_handler_kwargs: Optional[dict] = None,
                     image_number: Optional[int] = None,
                     image_count: Optional[int] = None):
        body = self.create_upload_image_body(image_path = image_path)
        url = f"{self.server}/rasters/mosaic/{mosaic_id}/image"
        response = self.http.post(url=url,
                                  body=body,
                                  callback=callback,
                                  callback_kwargs=callback_kwargs,
                                  use_default_error_handler=error_handler is None,
                                  error_handler=error_handler,
                                  error_handler_kwargs=error_handler_kwargs or {},
                                  timeout=3600
                                 )
        body.setParent(response)

        progressMessageBar = self.iface.messageBar().createMessage(f"Uploading image {image_number}/{image_count}:")
        progress = QProgressBar()
        progressMessageBar.layout().addWidget(progress)
        self.iface.messageBar().pushWidget(progressMessageBar)

        def display_upload_progress(bytes_sent: int, bytes_total: int):
            try:
                progress.setValue(round(bytes_sent / bytes_total * 100))
            except ZeroDivisionError:
                return
            if bytes_total > 0:
                if bytes_sent == bytes_total:
                    self.iface.messageBar().popWidget(progressMessageBar)

        connection = response.uploadProgress.connect(display_upload_progress)
        progressMessageBar.destroyed.connect(lambda: response.uploadProgress.disconnect(connection))

    def upload_image_error_handler(self, response: QNetworkReply, mosaic_name: str, image_paths: list):
        response_body = response.readAll().data().decode()
        error_summary, email_body = get_error_report_body(response=response,
                                                          response_body=response_body,
                                                          plugin_version=self.plugin_version,
                                                          error_message_parser=data_catalog_message_parser)
        if response.error() == 201: # ContentAccessDenied (like 403)
            error_summary = self.tr("This operation is forbidden for your account, contact us")
        if response.error() == 203: # ContentNotFoundError (like 404)
            error_summary = self.tr("Imagery collection '{mosaic_name}' does not exist").format(mosaic_name=mosaic_name)
        if response.error() == 204: # AuthenticationRequiredError (like 401)
            error_summary = self.tr("Authentication error. Please log in to your account")
        if response.error() == 299: # UnknownContentError
            error_summary = self.tr("The image does not meet this imagery collection '{mosaic_name}' paremeters. \n"
                                    "Either modify your image or upload it to a different collection").format(mosaic_name=mosaic_name)
        if len(image_paths) == 1:
            message = self.tr("Could not upload '{image}' to imagery collection").format(image=image_paths[0])
        else:
            message = self.tr("Could not upload following images:\n{images}").format(images= ', \n'.join(image_paths))
        ErrorMessageWidget(parent=QApplication.activeWindow(),
                           text= error_summary,
                           title=message,
                           email_body=email_body).show()

    def get_mosaic_images(self, mosaic_id: UUID, callback: Callable):
        self.http.get(url=f"{self.server}/rasters/mosaic/{mosaic_id}/image",
                      callback=callback,
                      use_default_error_handler=False
                     )

    def get_image(self, image_id: UUID, callback: Callable):
        self.http.get(url=f"{self.server}/rasters/image/{image_id}",
                      callback=callback,
                      use_default_error_handler=True
                     )
        
    def delete_image(self,
                     image_id: UUID,
                     callback: Callable = lambda *args: None,
                     callback_kwargs: Optional[dict] = None,
                     error_handler: Optional[Callable] = None,
                     error_handler_kwargs: Optional[dict] = None):
        self.http.delete(url=f"{self.server}/rasters/image/{image_id}",
                         callback=callback,
                         callback_kwargs=callback_kwargs,
                         use_default_error_handler=error_handler is None,
                         error_handler=error_handler,
                         error_handler_kwargs=error_handler_kwargs or {}
                        )

    def delete_image_error_handler(self, image_paths: list):
        if len(image_paths) == 1:
            title = self.tr("Error")
            message = self.tr("Could not delete '{image}' from imagery collection").format(image=image_paths[0])
        else:
            title = self.tr("Error. Could not delete following images:")
            message = ', \n'.join(image_paths)
        ErrorMessageWidget(parent=QApplication.activeWindow(),
                           text=message,
                           title=title,
                           email_body='').show()

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

    def preview_s_error_handler(self, response: QNetworkReply):
        self.dlg.imagePreview.setText("Preview is unavailable")
    
    def get_image_preview_l(self,
                            image: ImageReturnSchema,
                            extent: QgsRectangle,
                            callback: Callable,
                            image_name: str = ""):
        self.http.get(url=image.preview_url_l,
                      callback=callback,
                      use_default_error_handler=False,
                      error_handler=self.image_preview_l_error_handler,
                      callback_kwargs={"extent": extent,
                                       "image_name": image_name}
                     )

    def image_preview_l_error_handler(self, response: QNetworkReply):
        error_summary, email_body = get_error_report_body(response=response,
                                                          plugin_version=self.plugin_version)
        ErrorMessageWidget(parent=QApplication.activeWindow(),
                           text=error_summary,
                           title="Error. Could not display preview",
                           email_body=email_body).show()

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
