from typing import Sequence, Union, Optional, Callable, List, Tuple
from pathlib import Path
from uuid import UUID
import json
import tempfile
import os.path
from osgeo import gdal

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QImage
from PyQt5.QtNetwork import QNetworkReply
from PyQt5.QtWidgets import QMessageBox, QApplication, QFileDialog
from qgis.core import QgsCoordinateReferenceSystem, QgsProject, QgsRasterLayer, QgsRectangle

from ...dialogs.main_dialog import MainDialog
from ...schema.data_catalog import PreviewSize, MosaicCreateSchema, MosaicReturnSchema, ImageReturnSchema, UserLimitSchema
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
                 result_loader,
                 plugin_version):
        super().__init__()
        self.dlg = dlg
        self.iface = iface
        self.temp_dir = tempfile.gettempdir()
        self.project = QgsProject.instance()
        self.result_loader = result_loader
        self.plugin_version = plugin_version
        self.api = DataCatalogApi(http=http, server=server, dlg=dlg, iface=iface, result_loader=self.result_loader, plugin_version=self.plugin_version)
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
        mosaic = MosaicReturnSchema.from_dict(json.loads(response.readAll().data()))
        self.mosaics.update({mosaic.id: mosaic})
        self.mosaicsUpdated.emit()

    def delete_mosaic(self, mosaic_id: UUID):
        self.api.delete_mosaic(mosaic_id=mosaic_id,
                               callback=self.delete_mosaic_callback,
                               callback_kwargs={'mosaic_id': mosaic_id})

    def delete_mosaic_callback(self, response: QNetworkReply, mosaic_id: UUID):
        self.mosaics.pop(mosaic_id)
        self.mosaicsUpdated.emit()

    def mosaic_clicked(self):
        mosaic = self.selected_mosaic()
        if not mosaic:
            return
        self.view.display_mosaic_info(mosaic)
        self.get_mosaic_images(mosaic.id)
        self.dlg.imageTable.clearSelection()
        self.dlg.imageDetails.setText("Image Info")
        self.dlg.imagePreview.setText(" ")

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


    # Images CRUD
    def upload_images(self,
                      response: QNetworkReply,
                      mosaic_id: UUID,
                      image_paths: Sequence[Union[Path, str]],
                      uploaded: Sequence[Union[Path, str]],
                      failed: Sequence[Union[Path, str]]):             
        if not image_paths:
            return
        image_to_upload = image_paths[0]
        non_uploaded = image_paths[1:] 
        if len(image_paths) == 1:
            callback=self.upload_images_callback
        else:
            callback=self.upload_images
        self.api.upload_image(mosaic_id=mosaic_id,
                              image_path=image_to_upload,
                              callback=callback,
                              callback_kwargs={'mosaic_id':mosaic_id,
                                               'image_paths': non_uploaded,
                                               'uploaded': list(uploaded) + [image_to_upload],
                                               'failed': failed},
                              error_handler=callback,
                              error_handler_kwargs={'mosaic_id':mosaic_id,
                                                    'image_paths': non_uploaded,
                                                    'uploaded': uploaded,
                                                    'failed': list(failed) + [image_to_upload]},
                              )

    def upload_images_callback (self, 
                                response: QNetworkReply, 
                                mosaic_id: UUID, 
                                image_paths: Sequence[Union[Path, str]], 
                                uploaded: List[str], 
                                failed: List[str]):
        if failed:
            self.api.upload_image_error_handler(image_paths=failed)
        self.get_mosaic(mosaic_id)
        self.get_mosaic_images(mosaic_id)
    
    def upload_images_to_mosaic(self):
        mosaic = self.selected_mosaic()
        image_paths = QFileDialog.getOpenFileNames(QApplication.activeWindow(), "Choose image to upload", filter='(TIF files *.tif; *.tiff)')[0]
        self.upload_images(response=None, mosaic_id=mosaic.id, image_paths=image_paths, uploaded=[], failed=[])

    def get_mosaic_images(self, mosaic_id):
        self.api.get_mosaic_images(mosaic_id=mosaic_id, callback=self.get_mosaic_images_callback)
        return self.images

    def get_mosaic_images_callback(self, response: QNetworkReply):
        self.images = [ImageReturnSchema.from_dict(data) for data in json.loads(response.readAll().data())]
        self.view.display_images(self.images)

    def get_image(self, image_id: UUID, callback: Callable):
        self.api.get_image(image_id=image_id, callback=callback)

    def delete_image(self):
        images = {}
        for image in self.selected_images():
            images[image.id] = image.filename
        self.delete_images(response = None, images=list(images.items()), deleted=[], failed=[])

    def delete_images(self, 
                      response: QNetworkReply, 
                      images: List[Tuple[str, str]],
                      deleted: List[str], 
                      failed: List[str]):
        if not images:
            return
        image_to_delete = images[0]
        non_deleted = images[1:]
        if len(images) == 1:
            callback=self.delete_images_callback
        else:
            callback=self.delete_images
        self.api.delete_image(image_id=image_to_delete[0],
                              callback=callback,
                              callback_kwargs={'images': non_deleted,
                                               'deleted': list(deleted) + [image_to_delete[1]],
                                               'failed': failed},
                              error_handler=callback,
                              error_handler_kwargs={'images': non_deleted,
                                                    'deleted': deleted,
                                                    'failed': list(failed) + [image_to_delete[1]]},
                              )        
            
    def delete_images_callback (self, 
                                response: QNetworkReply, 
                                images: List[Tuple[str, str]],
                                deleted: List[str], 
                                failed: List[str]):
        if failed:
            self.api.delete_image_error_handler(image_paths=failed)
        mosaic_id = self.selected_mosaic().id
        self.get_mosaic(mosaic_id)
        self.get_mosaic_images(mosaic_id)

    def image_clicked(self):
        image = self.selected_image()
        if not image:
            return
        self.view.display_image_info(image)
        self.get_image_preview_s(image, PreviewSize.small)
        return image

    def image_info(self):
        image = self.selected_image()
        if not image:
            return
        self.view.full_image_info(image=image)

    def get_image_preview_s(self,
                           image: ImageReturnSchema,
                           size: PreviewSize):
        self.api.get_image_preview(image=image, size=PreviewSize.small, callback=self.get_image_preview_s_callback)

    def get_image_preview_s_callback(self, response: QNetworkReply):
        image = QImage.fromData(response.readAll().data())
        self.view.show_preview_s(image)

    def get_image_preview_l(self, image: ImageReturnSchema):
        try:
            image = self.selected_image()
            extent = layer_utils.footprint_to_extent(image.footprint)
            self.api.get_image_preview_l(image=image, extent=extent, callback=self.display_image_preview, image_id=image.id)
        except AttributeError:
            return

    def display_image_preview(self,
                                response: QNetworkReply,
                                extent: QgsRectangle,
                                crs: QgsCoordinateReferenceSystem = QgsCoordinateReferenceSystem("EPSG:3857"),
                                image_id: str = ""):
        with open(Path(self.temp_dir)/os.urandom(32).hex(), mode='wb') as f:
            f.write(response.readAll().data())
        preview = gdal.Open(f.name)
        pixel_xsize = extent.width() / preview.RasterXSize
        pixel_ysize = extent.height() / preview.RasterYSize
        preview.SetProjection(crs.toWkt())
        preview.SetGeoTransform([
            extent.xMinimum(),  # north-west corner x
            pixel_xsize,  # pixel horizontal resolution (m)
            0,  # x-axis rotation
            extent.yMaximum(),  # north-west corner y
            0,  # y-axis rotation
            -pixel_ysize  # pixel vertical resolution (m)
        ])
        preview.FlushCache()
        layer = QgsRasterLayer(f.name, f"preview {image_id}", 'gdal')
        layer.setExtent(extent)
        self.project.addMapLayer(layer)
        self.iface.setActiveLayer(layer)
        self.iface.zoomToActiveLayer()


    # Legacy:
    def upload_to_new_mosaic(self,
                             image_path: Union[Path, str],
                             callback: Callable):
        self.api.upload_to_new_mosaic(image_path=image_path,
                                      callback=callback)


    # Status
    def get_user_limit(self):
        self.api.get_user_limit(callback=self.get_user_limit_callback)

    def get_user_limit_callback(self, response: QNetworkReply):
        data_limit = UserLimitSchema.from_dict(json.loads(response.readAll().data()))
        taken = data_limit.memoryUsed
        free = data_limit.memoryFree
        self.view.show_storage(taken, free)


    # Selection
    def selected_mosaics(self, limit=None) -> List[MosaicReturnSchema]:
        ids = self.view.selected_mosaic_ids(limit=limit)
        # limit None will give full selection
        mosaics = [self.mosaics[id] for id in ids]
        return mosaics

    def selected_mosaic(self) -> Optional[MosaicReturnSchema]:
        first = self.selected_mosaics(limit=1)
        if not first:
            return None
        return first[0]
        
    def selected_images(self, limit=None) -> List[MosaicReturnSchema]:
        indices = self.view.selected_images_indecies(limit=limit)
        images = [i for i in self.images if self.images.index(i) in indices]
        return images

    def selected_image(self) -> Optional[ImageReturnSchema]:
        first = self.selected_images(limit=1)
        if not first:
            return None
        return first[0]
    
    def check_image_selection(self):
        if self.dlg.imageTable.selectionModel().hasSelection() is False:
            self.dlg.imagePreview.setText(" ")
            self.dlg.imageDetails.setText("Image info")
        else:
            self.image_clicked()
