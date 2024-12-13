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
from ...dialogs.mosaic_dialog import CreateMosaicDialog, UpdateMosaicDialog
from ...dialogs.dialogs import UploadRasterLayersDialog
from ...schema.data_catalog import PreviewSize, MosaicCreateSchema, MosaicReturnSchema, ImageReturnSchema, MosaicCreateReturnSchema, UserLimitSchema
from ..api.data_catalog_api import DataCatalogApi
from ..view.data_catalog_view import DataCatalogView
from ...http import Http
from ...functional import layer_utils, helpers
from ...config import Config
from ...entity.provider import MyImageryProvider


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
        self.image_max_size_pixels = Config.MAX_FILE_SIZE_PIXELS
        self.image_max_size_bytes = Config.MAX_FILE_SIZE_BYTES
        self.free_storage = None


    # Mosaics CRUD
    def create_mosaic(self):
        dialog = CreateMosaicDialog(self.dlg)
        dialog.accepted.connect(lambda: self.api.create_mosaic(dialog.mosaic(), callback=self.create_mosaic_callback))
        dialog.setup()
        dialog.deleteLater()

    def create_mosaic_callback(self, response: QNetworkReply):
        self.get_mosaics()
        self.dlg.mosaicTable.clearSelection()

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
        self.view.display_mosaics(list(self.mosaics.values())) 
        # Go to the right cell in case sorting changed items' order
        self.view.select_mosaic_cell(mosaic.id)

    def update_mosaic(self):
        mosaic = self.selected_mosaic()
        dialog = UpdateMosaicDialog(self.dlg)
        dialog.accepted.connect(lambda: self.api.update_mosaic(mosaic_id=mosaic.id, 
                                                               mosaic=dialog.mosaic(), 
                                                               callback=self.update_mosaic_callback, 
                                                               callback_kwargs={'mosaic': mosaic}))
        dialog.setup(mosaic)
        dialog.deleteLater()

    def update_mosaic_callback(self, response: QNetworkReply, mosaic: MosaicReturnSchema):
        self.get_mosaic(mosaic.id)        

    def delete_mosaic(self, mosaic):
        # Store widgets before deleting a row
        self.view.contain_mosaic_cell_buttons()
        # Delete mosaic
        self.api.delete_mosaic(mosaic_id=mosaic.id,
                               callback=self.delete_mosaic_callback,
                               callback_kwargs={'mosaic_id': mosaic.id},
                               error_handler=self.api.delete_mosaic_error_handler,
                               error_handler_kwargs={'mosaic_name': mosaic.name})
        self.dlg.mosaicTable.clearSelection()

    def delete_mosaic_callback(self, response: QNetworkReply, mosaic_id: UUID):
        self.get_mosaics()
        self.mosaics.pop(mosaic_id)

    def confirm_mosaic_deletion(self):
        mosaic = self.selected_mosaic()
        message = self.tr("Delete mosaic '{name}'?".format(name=mosaic.name))
        box = QMessageBox(QMessageBox.Question, "Mapflow", message, parent=QApplication.activeWindow())
        box.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        box_exec = box.exec()
        if box_exec == QMessageBox.Ok:
            self.delete_mosaic(mosaic)

    def mosaic_clicked(self):
        if not self.dlg.mosaicTable.selectedIndexes():
            return
        if self.dlg.selected_mosaic_cell is not None:
            if self.dlg.mosaicTable.selectedIndexes()[0] == self.dlg.selected_mosaic_cell:
                return # i.e. do noting when clicking on the same cell
        else: # assign selected cell if it is None
            self.dlg.selected_mosaic_cell = self.dlg.mosaicTable.selectedIndexes()[0]
        mosaic = self.selected_mosaic()
        if not mosaic:
            return
        self.get_mosaic_images(mosaic.id)
        # Store widgets before deleting previous mosaic's image table
        self.view.contain_image_cell_buttons()
        # Clear previous image details
        self.dlg.imageTable.clearSelection()
        self.dlg.imageTable.setRowCount(0)
        self.dlg.imagePreview.setText("")
        # Assing newly selected cell
        self.dlg.selected_mosaic_cell = self.dlg.mosaicTable.selectedIndexes()[0]

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
    def upload_images_to_mosaic(self):
        mosaic = self.selected_mosaic()
        image_paths = QFileDialog.getOpenFileNames(QApplication.activeWindow(), "Choose image to upload", filter='(TIF files *.tif; *.tiff)')[0]
        if image_paths:
            self.upload_images(response=None, 
                               mosaic_id=mosaic.id, mosaic_name=mosaic.name, 
                               image_paths=image_paths, uploaded=[], failed=[])

    def upload_raster_layers_to_mosaic(self, layers_paths):
        mosaic = self.selected_mosaic()
        if layers_paths:
            self.upload_images(response=None, mosaic_id=mosaic.id, image_paths=layers_paths, uploaded=[], failed=[])

    def choose_raster_layers(self):
        dialog = UploadRasterLayersDialog(self.dlg)
        dialog.accepted.connect(lambda: dialog.get_selected_rasters_list(callback=self.upload_raster_layers_to_mosaic))
        # Show all acceptable (TIFF) raster layers
        layers = []
        for layer in self.project.mapLayers().values():
            if Path(layer.source()).suffix.lower() in ['.tif', '.tiff']:
                layers.append(layer)
        dialog.setup(layers)
        dialog.deleteLater()

    def upload_images(self,
                      response: QNetworkReply,
                      mosaic_id: UUID,
                      mosaic_name: str,
                      image_paths: Sequence[Union[Path, str]],
                      uploaded: Sequence[Union[Path, str]],
                      failed: Sequence[Union[Path, str]]):        
        if len(image_paths) == 0:
            if failed:
                self.api.upload_image_error_handler(response=response, mosaic_name=mosaic_name, image_paths=failed)
            self.get_mosaic(mosaic_id)
            self.get_mosaic_images(mosaic_id)
            self.mosaicsUpdated.emit()
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
                                  " and file size less than {memory}"
                                  " MB").format(size=self.image_max_size_pixels,
                                                memory=self.image_max_size_bytes // (1024 * 1024))
                self.view.alert(self.tr("<center><b>Error uploading '{name}'</b>".format(name=Path(image_to_upload).name))+"<br>"+message)
                return
            # Check if user has enough stogage
            image_size=Path(image_to_upload).stat().st_size
            if self.free_storage and image_size > self.free_storage:
                message = (self.tr("<b>Not enough storage space. </b>"
                                   "You have {free_storage} MB left, but '{name}' is "
                                   "{image_size} MB".format(free_storage=round(self.free_storage/(1024*1024), 1),
                                                                name=Path(image_to_upload).name,
                                                                image_size=round(image_size/(1024*1024), 1)
                                                               )))
                self.iface.messageBar().pushWarning("Mapflow", message)
                self.get_mosaic(mosaic_id)
                self.get_mosaic_images(mosaic_id)
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
        return self.images

    def get_mosaic_images_callback(self, response: QNetworkReply):
        self.images = [ImageReturnSchema.from_dict(data) for data in json.loads(response.readAll().data())]
        self.view.display_images(self.images)
        self.view.display_mosaic_info(self.selected_mosaic(), self.images)

    def get_image(self, image_id: UUID, callback: Callable):
        self.api.get_image(image_id=image_id, callback=callback)

    def delete_image(self, selected_images):
        images = {}
        for image in selected_images:
            images[image.id] = image.filename
        self.delete_images(response = None, images=list(images.items()), deleted=[], failed=[])

    def delete_images(self, 
                      response: QNetworkReply, 
                      images: List[Tuple[str, str]],
                      deleted: List[str], 
                      failed: List[str]):
        if len(images) == 0:
            if failed:
                self.api.delete_image_error_handler(image_paths=failed)
            mosaic_id = self.selected_mosaic().id
            self.get_mosaic(mosaic_id)
            self.get_mosaic_images(mosaic_id)
            # Store widgets before deleting a row
            self.view.contain_image_cell_buttons()
            self.dlg.imageTable.clearSelection()
        else:
            image_to_delete = images[0]
            non_deleted = images[1:] 
            self.api.delete_image(image_id=image_to_delete[0],
                                  callback=self.delete_images,
                                  callback_kwargs={'images': non_deleted,
                                                   'deleted': list(deleted) + [image_to_delete[1]],
                                                   'failed': failed},
                                  error_handler=self.delete_images,
                                  error_handler_kwargs={'images': non_deleted,
                                                        'deleted': deleted,
                                                        'failed': list(failed) + [image_to_delete[1]]},
                                 )
            
    def confirm_image_deletion(self):
        mosaic = self.selected_mosaic()
        images = self.selected_images()
        image_names = []
        for image in images:
            image_names.append(image.filename)
        if len(image_names) == 0:
            return
        if len(image_names) == 1:
            message = self.tr("<center>Delete image <b>'{name}'</b> from '{mosaic}' mosaic?"
                              .format(name=image_names[0], mosaic=mosaic.name))
        elif len(image_names) <= 3:
            message = self.tr("<center>Delete following images from '{mosaic}' mosaic:<br><b>'{names}'</b>?"
                              .format(names="', <br>'".join(image_names), mosaic=mosaic.name))
        else:
            message = self.tr("<center>Delete <b>{len}</b> images from '{mosaic}' mosaic?"
                              .format(len=len(image_names), mosaic=mosaic.name))
        box = QMessageBox(QMessageBox.Question, "Mapflow", message, parent=QApplication.activeWindow())
        box.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        box_exec = box.exec()
        if box_exec == QMessageBox.Ok:
            self.delete_image(images)

    def image_clicked(self):
        image = self.selected_image()
        if not image:
            return
        self.view.display_image_info(image)
        self.get_image_preview_s(image, PreviewSize.small)
        self.view.add_image_cell_buttons()
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

    def get_image_preview_l(self):
        try:
            image = self.selected_image()
            extent = layer_utils.footprint_to_extent(image.footprint)
            self.api.get_image_preview_l(image=image, extent=extent, callback=self.display_image_preview, image_name=image.filename)
        except AttributeError:
            return

    def display_image_preview(self,
                              response: QNetworkReply,
                              extent: QgsRectangle,
                              crs: QgsCoordinateReferenceSystem = QgsCoordinateReferenceSystem("EPSG:3857"),
                              image_name: str = ""):
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
        layer = QgsRasterLayer(f.name, f"preview {image_name}", 'gdal')
        layer.setExtent(extent)
        self.project.addMapLayer(layer)
        self.iface.setActiveLayer(layer)
        self.iface.zoomToActiveLayer()


    # Functions that depend on mosaic or image selection
    def add_mosaic_or_image(self):
        if self.dlg.stackedLayout.currentIndex() == 0:
            self.create_mosaic()

    def delete_mosaic_or_image(self):
        image = self.selected_image()
        mosaic = self.selected_mosaic()
        if image:
            self.confirm_image_deletion()
        elif mosaic:
            self.confirm_mosaic_deletion()
        
    def check_catalog_selection(self):
        if self.dlg.mosaicTable.selectionModel().hasSelection():
            self.mosaic_clicked()
        image = self.selected_image()
        mosaic = self.selected_mosaic()
        image_name = None
        mosaic_name = None
        if image:
            image_name = image.filename
        elif mosaic:
            mosaic_name = mosaic.name
            self.view.display_mosaic_info(mosaic, self.images)
        self.view.check_mosaic_or_image_selection(mosaic_name, image_name)


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
        if data_limit.maxPixelCount:
            self.image_max_size_pixels = int(data_limit.maxPixelCount)
        if data_limit.maxUploadFileSize:
            self.image_max_size_bytes = int(data_limit.maxUploadFileSize)
        if data_limit.memoryLimit:
            self.free_storage = free
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


    # Provider
    def set_catalog_provider(self, providers):
        """ Sets current provider to 'My imagery' if catalog table cell was clicked.
        """
        # Check current provider
        current_provider = providers[self.dlg.providerIndex()]
        if not isinstance (current_provider, MyImageryProvider):
            # Get index of My imagery provider
            for index in range(len(providers)):
                provider = providers[index]
                if isinstance(provider, MyImageryProvider):
                    my_imagery_index = index
            # Set My imagery data source
            if my_imagery_index:
                self.dlg.sourceCombo.setCurrentIndex(my_imagery_index)
