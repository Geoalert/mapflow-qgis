from typing import Sequence, Union, Optional, Callable, List
from pathlib import Path
from uuid import UUID
import json

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QImage
from PyQt5.QtNetwork import QNetworkReply

from ...dialogs.main_dialog import MainDialog
from ...dialogs.mosaic_dialog import CreateMosaicDialog, UpdateMosaicDialog
from ...schema.data_catalog import PreviewSize, MosaicCreateSchema, MosaicReturnSchema, ImageReturnSchema
from ..api.data_catalog_api import DataCatalogApi
from ..view.data_catalog_view import DataCatalogView
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
                 server: str,
                 dlg: MainDialog):
        super().__init__()
        self.dlg = dlg
        self.api = DataCatalogApi(http=http, server=server)
        self.view = DataCatalogView(dlg=dlg)
        self.mosaics = {}
        

    # Mosaics CRUD
    def create_mosaic(self, mosaic: MosaicCreateSchema):
        dialog = CreateMosaicDialog(self.dlg)
        dialog.accepted.connect(lambda: self.api.create_mosaic(dialog.mosaic()))
        dialog.setup()
        dialog.deleteLater()

        #self.api.create_mosaic(mosaic, callback=self.create_mosaic_callback)

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

    def get_mosaic_images(self, mosaic_id):
        self.api.get_mosaic_images(mosaic_id=mosaic_id, callback=self.get_mosaic_images_callback)

    def get_mosaic_images_callback(self, response: QNetworkReply):
        images = [ImageReturnSchema.from_dict(data) for data in json.loads(response.readAll().data())]
        self.view.display_images(images)

    def get_image(self, image_id: UUID, callback: Callable):
        self.api.get_image(image_id=image_id, callback=callback)

    def delete_image(self, image_id: UUID):
        self.api.delete_image(image_id=image_id, callback=self.delete_image_callback)

    def delete_image_callback(self, response: QNetworkReply):
        pass

    def image_clicked(self):
        pass

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
        mosaics = [m for mid, m in self.mosaics.items() if mid in ids]
        return mosaics

    def selected_mosaic(self) -> Optional[MosaicReturnSchema]:
        first = self.selected_mosaics(limit=1)
        if not first:
            return None
        return first[0]