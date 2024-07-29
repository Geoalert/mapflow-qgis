from typing import Sequence, Union, Optional, Callable, List
from pathlib import Path
from uuid import UUID
import json

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QImage
from PyQt5.QtNetwork import QNetworkReply
from PyQt5.QtWidgets import QMessageBox, QApplication

from ...dialogs.main_dialog import MainDialog
from ...schema.data_catalog import PreviewSize, MosaicCreateSchema, MosaicReturnSchema, ImageReturnSchema
from ..api.data_catalog_api import DataCatalogApi
from ..view.data_catalog_view import DataCatalogView
from ...http import Http
from ...functional import layer_utils


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
                 server: str,
                 dlg: MainDialog,
                 iface,
                 result_loader):
        super().__init__()
        self.dlg = dlg
        self.result_loader = result_loader
        self.api = DataCatalogApi(http=http, server=server, dlg=dlg, iface=iface, result_loader=self.result_loader)
        self.view = DataCatalogView(dlg=dlg)
        self.mosaics = {}
        self.images = []

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
        self.view.display_mosaics(list(self.mosaics.values()))
        #self.mosaicsUpdated.emit()

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

    def mosaic_clicked(self):
        mosaic = self.selected_mosaic()
        if not mosaic:
            return
        self.view.display_mosaic_info(mosaic)
        self.get_mosaic_images(mosaic.id)
        self.dlg.imageTable.clearSelection()
        self.dlg.imageDetails.setText("Image Info")

    def get_mosaic_images(self, mosaic_id):
        self.api.get_mosaic_images(mosaic_id=mosaic_id, callback=self.get_mosaic_images_callback)

    def get_mosaic_images_callback(self, response: QNetworkReply):
        self.images = [ImageReturnSchema.from_dict(data) for data in json.loads(response.readAll().data())]
        self.view.display_images(self.images)

    def get_image(self, image_id: UUID, callback: Callable):
        self.api.get_image(image_id=image_id, callback=callback)

    def delete_image(self, image_id: UUID):
        self.api.delete_image(image_id=image_id, callback=self.delete_image_callback)

    def delete_image_callback(self, response: QNetworkReply):
        pass

    def image_clicked(self):
        image = self.selected_image()
        if not image:
            return
        self.view.display_image_info(image)

    def get_image_preview_s(self,
                           image: ImageReturnSchema,
                           size: PreviewSize):
        self.api.get_image_preview(image=image, size=PreviewSize.small, callback=self.get_image_preview_s_callback)

    def get_image_preview_s_callback(self, response: QNetworkReply):
        image = QImage.fromData(response.readAll().data())
        self.view.show_preview_s(image)

    # Legacy:
    def upload_to_new_mosaic(self,
                             image_path: Union[Path, str],
                             callback: Callable):
        self.api.upload_to_new_mosaic(image_path=image_path,
                                      callback=callback)

    # Status
    def get_user_limit(self, callback):
        self.api.get_user_limit(callback=callback)

    # Selection
    def selected_mosaics(self, limit=None) -> List[MosaicReturnSchema]:
        ids = self.view.selected_mosaic_ids(limit=limit)
        print(ids)
        # limit None will give full selection
        mosaics = [self.mosaics[id] for id in ids]
        return mosaics

    def selected_mosaic(self) -> Optional[MosaicReturnSchema]:
        first = self.selected_mosaics(limit=1)
        if not first:
            return None
        return first[0]

    def mosaic_preview(self):
        try:
            mosaic = self.selected_mosaic()
            url = mosaic.rasterLayer.tileUrl
            url_json = mosaic.rasterLayer.tileJsonUrl
            name = mosaic.name
            layer = layer_utils.generate_raster_layer(url, name)
            self.api.request_mosaic_extent(url_json, layer)
        except AttributeError:
            message = 'Please, select mosaic'
            info_box = QMessageBox(QMessageBox.Information, "Mapflow", message, parent=QApplication.activeWindow())
            return info_box.exec()
        
    def selected_images(self, limit=None) -> List[MosaicReturnSchema]:
        indices = self.view.selected_images_indecies(limit=limit)
        images = [i for i in self.images if self.images.index(i) in indices]
        return images

    def selected_image(self) -> Optional[ImageReturnSchema]:
        first = self.selected_images(limit=1)
        if not first:
            return None
        return first[0]
    
    def image_info(self):
        image = self.selected_image()
        if not image:
            return
        self.view.full_image_info(image=image)