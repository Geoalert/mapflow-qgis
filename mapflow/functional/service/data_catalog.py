from typing import Sequence, Union, Optional, List
from pathlib import Path
from uuid import UUID
import json

from PyQt5.QtCore import QObject, QUrl, pyqtSignal
from PyQt5.QtGui import QImage
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest
from qgis.core import QgsRasterLayer

from ...schema.data_catalog import PreviewSize, MosaicReturnSchema, ImageReturnSchema, UserLimitSchema
from ...schema import MyImageryParams
from ..api.data_catalog_api import DataCatalogApi
from ..service.alert_service import alert
from ...http import Http
from ...functional import helpers
from ...functional.app_context import AppContext
from ...config import Config


class DataCatalogService(QObject):
    """
    A service for querying mapflow data catalog: requests, response parsing and the mosaic/image
    state. It holds no widget — the My Imagery panel is `DataCatalogView`, driven by
    `DataCatalogController`, which this service *tells* what changed (the signals below) and is
    *told* the current selection (`set_selected_*`). See `spec/007_architecture.md` § Services.

    It stores the mosaics as a dict keyed by id for access from other places.
    """
    mosaicsUpdated = pyqtSignal()

    # ---------- what the My Imagery panel must show (announced, never drawn) ----------
    #: The mosaic list changed: render it and clear the selection.
    mosaicsChanged = pyqtSignal(object)
    #: A single mosaic was (re)fetched: render the list and reselect its cell.
    mosaicReselected = pyqtSignal(object, object)
    #: The open mosaic's images changed.
    imagesChanged = pyqtSignal(object)
    #: (mosaic, images) for the info panel.
    mosaicInfoChanged = pyqtSignal(object, object)
    #: A preview image (QImage) arrived.
    previewChanged = pyqtSignal(object)
    #: (images count, current index) for the ‹ › preview controls.
    previewNavChanged = pyqtSignal(int, int)
    #: (index, count) for the "n/total" preview label.
    imageNumberChanged = pyqtSignal(int, int)
    #: A rename round trip finished: update the row for this image.
    imageRenamedInTable = pyqtSignal(object)
    #: (used bytes, free bytes) for the storage label. `object`, not `int`: byte counts run into
    #: the billions and PyQt's `int` is 32-bit, which would wrap a multi-GB quota to a negative.
    storageChanged = pyqtSignal(object, object)
    #: Standalone selection clears (no reload).
    mosaicSelectionCleared = pyqtSignal()
    imageSelectionCleared = pyqtSignal()
    #: Reopening a processing's My Imagery source: select the mosaic cell / bind the image row.
    sourceMosaicSelected = pyqtSignal(object)
    sourceImageReady = pyqtSignal(object)
    #: 'Go to source' asked to focus the My Imagery tab for these params.
    mySourceShown = pyqtSignal(object)
    #: An error handler wants the panel back on the mosaics table.
    catalogResetToMosaics = pyqtSignal()
    #: A source image/mosaic was not found (summary text for the error widget).
    imageSourceError = pyqtSignal(str)
    #: A download URL and its suggested filename are ready for a save-as prompt.
    downloadUrlReady = pyqtSignal(str, str)
    #: An upload finished — bring the plugin window back to the front.
    dialogShouldRaise = pyqtSignal()
    #: A catalog action needs the data source switched to My Imagery (carries the provider list).
    switchToMyImageryRequested = pyqtSignal(object)

    #: The current table selections, pushed from the controller (a service reads no table).
    _selected_mosaic_ids = ()
    _selected_image_ids = ()
    #: Which catalog table is showing (mosaics vs images), pushed from the controller — the
    #: service branches on it in poll/refresh paths but may not read the stacked layout.
    _mosaic_table_visible = True

    def __init__(self,
                 http: Http,
                 server: str,
                 iface,
                 result_loader,
                 plugin_version,
                 app_context: AppContext):
        super().__init__()
        self.iface = iface
        self.app_context = app_context
        self.result_loader = result_loader
        self.plugin_version = plugin_version
        self.api = DataCatalogApi(http=http, server=server, iface=iface, result_loader=self.result_loader, plugin_version=self.plugin_version)
        self.mosaics = {}
        self.images = []
        self.image_max_size_pixels = Config.MAX_FILE_SIZE_PIXELS
        self.image_max_size_bytes = Config.MAX_FILE_SIZE_BYTES
        self.free_storage = None
        self.preview_idx = 0

    # ---------- pushed state (the controller tells the service, the service never reads a widget) ----------

    def set_selected_mosaic_ids(self, ids) -> None:
        self._selected_mosaic_ids = tuple(ids or ())

    def set_selected_image_ids(self, ids) -> None:
        self._selected_image_ids = tuple(ids or ())

    def set_mosaic_table_visible(self, visible: bool) -> None:
        self._mosaic_table_visible = bool(visible)


    # Mosaics CRUD
    #
    # The dialogs (create / update / confirm-delete) are `DataCatalogController`'s; a service
    # builds none. What arrives here is the assembled request, and what leaves is a signal.

    def create_mosaic(self, mosaic):
        """Create an empty mosaic from an assembled request object."""
        self.api.create_mosaic(mosaic, callback=self.create_mosaic_callback)

    def create_mosaic_from_images(self, mosaic, image_paths: List):
        """Create a mosaic and upload the chosen images into it."""
        self.api.create_mosaic_from_images(mosaic,
                                           callback=self.create_mosaic_from_images_callback,
                                           callback_kwargs={'image_paths': image_paths,
                                                            'mosaic_name': mosaic.name},
                                           error_handler=self.create_mosaic_from_images_error_handler,
                                           error_handler_kwargs={'image_paths': image_paths,
                                                                 'mosaic_name': mosaic.name},
                                           image_paths=image_paths)

    def create_mosaic_callback(self, response: QNetworkReply):
        self.get_mosaics()  # mosaicsChanged clears the selection
        self.previewNavChanged.emit(0, 0)

    def create_mosaic_from_images_callback(self, response: QNetworkReply, image_paths: List, mosaic_name: str):
        mosaic_id = json.loads(response.readAll().data())['mosaic_id']
        self.upload_images(response=None,
                           mosaic_id=mosaic_id, mosaic_name=mosaic_name,
                           image_paths=image_paths[1:], uploaded=[image_paths[0]], failed=[])

    def create_mosaic_from_images_error_handler(self,
                                                response: QNetworkReply,
                                                image_paths: List,
                                                mosaic_name: str):
        alert(self.tr("<center>Creation of imagery collection '{mosaic_name}' failed"
                      "<br>while trying to upload '{image}'").format(mosaic_name=mosaic_name,
                                                                     image=Path(image_paths[0]).name))
        self.mosaicSelectionCleared.emit()

    def get_mosaics(self):
        self.api.get_mosaics(callback=self.get_mosaics_callback)

    def get_mosaics_callback(self, response: QNetworkReply):
        data = json.loads(response.readAll().data())
        self.mosaics.clear()
        for item in data:
            mosaic = MosaicReturnSchema.from_dict(item)
            self.mosaics[mosaic.id] = mosaic
        self.mosaicsChanged.emit(list(self.mosaics.values()))
        self.mosaicsUpdated.emit()
        self.app_context.mosaics = self.mosaics

    def get_mosaic(self, mosaic_id: UUID):
        self.api.get_mosaic(mosaic_id=mosaic_id,
                            callback=self.get_mosaic_callback)

    def get_mosaic_callback(self, response: QNetworkReply):
        mosaic = MosaicReturnSchema.from_dict(json.loads(response.readAll().data()))
        self.mosaics.update({mosaic.id: mosaic})
        self.mosaicsUpdated.emit()
        # The list is redrawn and this mosaic's cell reselected; the view guards the reselect
        # against the selection-mode bug that the explicit No/Extended dance used to.
        self.mosaicReselected.emit(list(self.mosaics.values()), mosaic.id)
        self.app_context.mosaics = self.mosaics

    def update_mosaic(self, mosaic_id, mosaic):
        """Apply an edited mosaic (the dialog was read by the controller)."""
        self.api.update_mosaic(mosaic_id=mosaic_id,
                               mosaic=mosaic,
                               callback=self.update_mosaic_callback,
                               callback_kwargs={'mosaic_id': mosaic_id})

    def update_mosaic_callback(self, response: QNetworkReply, mosaic_id):
        self.mosaicSelectionCleared.emit()
        self.get_mosaic(mosaic_id)

    def delete_mosaics(self,
                       response: QNetworkReply,
                       mosaics: List[MosaicReturnSchema],
                       deleted: List[str],
                       failed: List[str]):
        if len(mosaics) == 0:
            if failed:
                self.api.delete_mosaic_error_handler(mosaics=failed)
            self.get_mosaics()  # mosaicsChanged clears the selection
            self.previewNavChanged.emit(0, 0)
        else:
            mosaic_to_delete = mosaics[0]
            non_deleted = mosaics[1:]
            self.api.delete_mosaic(mosaic_id=mosaic_to_delete.id,
                                   callback=self.delete_mosaics,
                                   callback_kwargs={'mosaics': non_deleted,
                                                    'deleted': list(deleted) + [mosaic_to_delete.name],
                                                    'failed': failed},
                                   error_handler=self.delete_mosaics,
                                   error_handler_kwargs={'mosaics': non_deleted,
                                                         'deleted': deleted,
                                                         'failed': list(failed) + [mosaic_to_delete.name]},
                                  )

    # Images CRUD
    def upload_images_to_mosaic(self, image_paths):
        """Upload chosen image files into the selected mosaic (the file dialog is the
        controller's). No-op without a selection or without files."""
        mosaic = self.selected_mosaic()
        if not mosaic or not image_paths:
            return
        self.upload_images(response=None,
                           mosaic_id=mosaic.id, mosaic_name=mosaic.name,
                           image_paths=image_paths, uploaded=[], failed=[])

    def upload_raster_layers_to_mosaic(self, layers_paths):
        mosaic = self.selected_mosaic()
        if mosaic and layers_paths:
            self.upload_images(response=None, mosaic_id=mosaic.id, mosaic_name=mosaic.name, image_paths=layers_paths, uploaded=[], failed=[])

    def upload_images(self,
                      response: QNetworkReply,
                      mosaic_id: UUID,
                      mosaic_name: str,
                      image_paths: Sequence[Union[Path, str]],
                      uploaded: Sequence[Union[Path, str]],
                      failed: Sequence[Union[Path, str]]):
        if len(image_paths) == 0:
            self.get_mosaic(mosaic_id)
            self.mosaicSelectionCleared.emit()
            self.dialogShouldRaise.emit()
            self.mosaicsUpdated.emit()
            if failed:
                self.api.upload_image_error_handler(response=response, mosaic_name=mosaic_name, image_paths=failed)
        else:
            image_to_upload = image_paths[0]
            non_uploaded = image_paths[1:]
            # Check for erros that should stop further uploading
            if failed and response.error() in (201, 203, 204):
                failed += [image_to_upload] + non_uploaded
                self.api.upload_image_error_handler(response=response, mosaic_name=mosaic_name, image_paths=failed)
                self.get_mosaics()
                return
            # Check if raster to be uploaded meets restrictions
            layer = QgsRasterLayer(image_to_upload, "rasterLayerCheck", 'gdal')
            if not helpers.raster_layer_is_allowed(layer, self.image_max_size_pixels, self.image_max_size_bytes):
                message = self.tr("Raster TIFF file must be georeferenced,"
                                  " have size less than {size} pixels"
                                  " and file size less than {memory}").format(size=self.image_max_size_pixels,
                                                                              memory=helpers.get_readable_size(self.image_max_size_bytes))
                alert(self.tr("<center><b>Error uploading '{name}'</b>").format(name=Path(image_to_upload).name)+"<br>"+message)
                return
            # Check if user has enough stogage
            image_size=Path(image_to_upload).stat().st_size
            if self.free_storage and image_size > self.free_storage:
                message = (self.tr("<b>Not enough storage space. </b>"
                                   "You have {free_storage} left, but '{name}' is "
                                   "{image_size}").format(free_storage=helpers.get_readable_size(self.free_storage),
                                                          name=Path(image_to_upload).name,
                                                          image_size=helpers.get_readable_size(image_size)))
                self.iface.messageBar().pushWarning("Mapflow", message)
                self.get_mosaic(mosaic_id)
                self.mosaicsUpdated.emit()
                return
            # Upload allowed raster 
            self.api.upload_image(mosaic_id=mosaic_id,
                                  image_path=image_to_upload,
                                  callback=self.upload_images,
                                  callback_kwargs={'mosaic_id': mosaic_id,
                                                   'mosaic_name': mosaic_name,
                                                   'image_paths': non_uploaded,
                                                   'uploaded': list(uploaded) + [image_to_upload],
                                                   'failed': failed},
                                  error_handler=self.upload_images,
                                  error_handler_kwargs={'mosaic_id': mosaic_id,
                                                        'mosaic_name': mosaic_name,
                                                        'image_paths': non_uploaded,
                                                        'uploaded': uploaded,
                                                        'failed': list(failed) + [image_to_upload]},
                                  image_number=len(uploaded+[image_to_upload]+failed),
                                  image_count=len(uploaded+[image_to_upload]+non_uploaded+failed)
                                 )

    def get_mosaic_images(self, mosaic_id):
        self.api.get_mosaic_images(mosaic_id=mosaic_id, callback=self.get_mosaic_images_callback)

    def get_mosaic_images_callback(self, response: QNetworkReply):
        self.images = [ImageReturnSchema.from_dict(data) for data in json.loads(response.readAll().data())]
        self.imagesChanged.emit(self.images)
        if self._mosaic_table_visible:
            self.mosaicInfoChanged.emit(self.selected_mosaic(), self.images)
            self.preview_idx = 0
            if len(self.images) > 0:
                self.get_image_preview_s(self.images[self.preview_idx])
            else:
                self.previewNavChanged.emit(len(self.images), self.preview_idx)
        self.app_context.images = self.images

    def get_next_preview(self):
        try:
            self.preview_idx += 1
            self.get_image_preview_s(self.images[self.preview_idx])
            self.imageNumberChanged.emit(self.preview_idx, len(self.images))
        except IndexError:
            pass

    def get_previous_preview(self):
        try:
            self.preview_idx += -1
            self.get_image_preview_s(self.images[self.preview_idx])
            self.imageNumberChanged.emit(self.preview_idx, len(self.images))
        except IndexError:
            pass

    def get_image(self, image_id: UUID):
        self.api.get_image(image_id=image_id, callback=self.get_image_callback, error_handler=self.get_image_error_handler)

    def delete_images(self, 
                      response: QNetworkReply, 
                      images: List[ImageReturnSchema],
                      deleted: List[str], 
                      failed: List[str]):
        if len(images) == 0:
            if failed:
                self.api.delete_image_error_handler(image_paths=failed)
            mosaic_id = self.selected_mosaic().id
            self.mosaicSelectionCleared.emit()
            self.get_mosaic(mosaic_id)
            self.imageSelectionCleared.emit()
        else:
            image_to_delete = images[0]
            non_deleted = images[1:] 
            self.api.delete_image(image_id=image_to_delete.id,
                                  callback=self.delete_images,
                                  callback_kwargs={'images': non_deleted,
                                                   'deleted': list(deleted) + [image_to_delete.filename],
                                                   'failed': failed},
                                  error_handler=self.delete_images,
                                  error_handler_kwargs={'images': non_deleted,
                                                        'deleted': deleted,
                                                        'failed': list(failed) + [image_to_delete.filename]},
                                 )
            
    def delete_selected_images(self):
        """Delete the selected images (the confirmation dialog is the controller's)."""
        images = self.selected_images()
        if not images:
            return
        self.delete_images(response=None, images=images, deleted=[], failed=[])

    def get_image_preview_s(self,
                            image: ImageReturnSchema):
        self.api.get_image_preview(image=image,
                                   size=PreviewSize.small,
                                   callback=self.get_image_preview_s_callback)

    def get_image_preview_s_callback(self, response: QNetworkReply):
        image = QImage.fromData(response.readAll().data())
        self.previewChanged.emit(image)
        if self._mosaic_table_visible:
            self.previewNavChanged.emit(len(self.images), self.preview_idx)

    def rename_image_callback(self, response: QNetworkReply):
        new_image = ImageReturnSchema.from_dict(json.loads(response.readAll().data()))
        for image in self.images:
            if image.id == new_image.id:
                image.filename = new_image.filename
                break
        self.imageRenamedInTable.emit(new_image)
        self.iface.messageBar().pushMessage("Mapflow", "Image renamed")

    def rename_image(self, image_id, new_name: str):
        if not new_name or len(new_name) > 255:
            self.iface.messageBar().pushWarning("Mapflow",
                                                self.tr("Image name should be 1-255 characters long"))
            return
        self.api.update_image_name(image_id=image_id,
                                   name=new_name,
                                   callback=self.rename_image_callback)

    def download_image(self):
        image = self.selected_image()
        if not image:
            return
        self.api.download_image(image_id=image.id,
                                callback=self.download_image_callback,
                                error_handler=self.api.download_image_error_handler)

    def download_image_callback(self, response: QNetworkReply):
        data = json.loads(response.readAll().data())
        download_url = data.get("download_url")
        suggested_filename = data.get("filename", "image.tif")
        if not download_url:
            alert(self.tr("Download URL not available"))
            return
        # The save-as prompt is the controller's; it calls back into `save_downloaded`.
        self.downloadUrlReady.emit(download_url, suggested_filename)

    def save_downloaded(self, url: str, save_path: str):
        """Fetch `url` and write it to `save_path` (the path came from the controller's dialog)."""
        request = QNetworkRequest(QUrl(url))
        nam = self.api.http.nam
        reply = nam.get(request)
        reply.finished.connect(lambda: self._save_downloaded_file(reply, save_path))

    def _save_downloaded_file(self, reply: QNetworkReply, save_path: str):
        if reply.error() != QNetworkReply.NoError:
            alert(self.tr("Failed to download image: {}").format(reply.errorString()))
            reply.deleteLater()
            return
        data = reply.readAll().data()
        try:
            with open(save_path, 'wb') as f:
                f.write(data)
            self.iface.messageBar().pushMessage("Mapflow", self.tr("Image saved to {}").format(save_path))
        except OSError as e:
            alert(self.tr("Failed to save file: {}").format(str(e)))
        reply.deleteLater()

    def refresh_catalog(self):
        if self._mosaic_table_visible:
            self.get_mosaics()  # mosaicsChanged clears the selection
        else:
            if self.selected_mosaic():
                self.get_mosaic_images(self.selected_mosaic().id)

    # Status
    def get_user_limit(self):
        self.api.get_user_limit(callback=self.get_user_limit_callback)

    def get_user_limit_callback(self, response: QNetworkReply):
        data_limit = UserLimitSchema.from_dict(json.loads(response.readAll().data()))
        taken = data_limit.memoryUsed
        free = data_limit.memoryFree
        if data_limit.maxPixelCount:
            self.image_max_size_pixels = int(data_limit.maxPixelCount)
        if data_limit.maxUploadFileSize:
            self.image_max_size_bytes = int(data_limit.maxUploadFileSize)
        if data_limit.memoryLimit:
            self.free_storage = free
        self.storageChanged.emit(taken, free)

    # Selection (resolved from ids pushed by the controller)
    def selected_mosaics(self, limit=None) -> List[MosaicReturnSchema]:
        ids = self._selected_mosaic_ids[:limit]
        mosaics = (self.mosaics.get(id) for id in ids)
        return [m for m in mosaics if m is not None]

    def selected_mosaic(self) -> Optional[MosaicReturnSchema]:
        first = self.selected_mosaics(limit=1)
        if not first:
            return None
        self.app_context.selected_mosaic = first[0]
        return first[0]

    def selected_images(self, limit=None) -> List[MosaicReturnSchema]:
        ids = self._selected_image_ids[:limit]
        images = [i for i in self.images if i.id in ids]
        return images

    def selected_image(self) -> Optional[ImageReturnSchema]:
        first = self.selected_images(limit=1)
        if not first:
            return None
        return first[0]

    # Provider
    def set_catalog_provider(self, providers):
        """Ask the panel to switch the data source to 'My imagery'.

        Called by other services (area calculator, provider), so it cannot read the source combo
        itself — deciding whether a switch is needed and doing it is the controller's, off this
        signal. The provider list is carried because only the caller has it."""
        self.switchToMyImageryRequested.emit(providers)

    def select_mosaic_cell(self, mosaic_id):
        """Ask the panel to select a mosaic's cell. Called by other services (a service reaches
        no view of its own, nor another service's)."""
        self.sourceMosaicSelected.emit(mosaic_id)

    def clear_mosaic_selection(self):
        """Ask the panel to clear the mosaic selection. Called by ProviderService when it
        duplicates a My Imagery source — it holds no view to do it itself."""
        self.mosaicSelectionCleared.emit()

    def show_my_imagery_source(self,
                               source_params: MyImageryParams):
        if source_params.myImagery.imageIds: # if the source was an image:
            image_id = source_params.myImagery.imageIds[0] # get full image info to obtain mosaic_id
            self.get_image(image_id)
        self.mySourceShown.emit(source_params)

    def get_image_callback(self, response: QNetworkReply):
        image = ImageReturnSchema.from_dict(json.loads(response.readAll().data()))
        self.sourceImageReady.emit(image)

    def get_image_error_handler(self, response: QNetworkReply) -> None:
        response_data = json.loads(response.readAll().data())
        error_params = response_data['detail']['parameters']
        if error_params['instance_type'] == "mosaic":
            error_summary = self.tr("Source imagery collection with id '{}' was not found ").format(error_params['uid'])
        else:
            error_summary = self.tr("Source image with id '{}' was not found in any of your imagery collections").format(error_params['uid'])
        self.imageSourceError.emit(error_summary)
        self.catalogResetToMosaics.emit()
        for key in self.app_context.allow_enable_processing:
            self.app_context.allow_enable_processing[key] = True


    # Other
    def open_imagery_docs(self):
        helpers.open_imagery_docs()
