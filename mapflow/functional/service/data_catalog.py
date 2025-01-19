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
from PyQt5.QtWidgets import QMessageBox, QApplication, QFileDialog, QAbstractItemView
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
        data = json.loads(response.readAll().data())
        self.mosaics.clear()
        for item in data:
            mosaic = MosaicReturnSchema.from_dict(item)
            self.mosaics[mosaic.id] = mosaic
        self.view.display_mosaics(list(self.mosaics.values()))
        self.mosaicsUpdated.emit()

    def get_mosaic(self, mosaic_id: UUID):
        self.api.get_mosaic(mosaic_id=mosaic_id,
                            callback=self.get_mosaic_callback)

    def get_mosaic_callback(self, response: QNetworkReply):
        mosaic = MosaicReturnSchema.from_dict(json.loads(response.readAll().data()))
        # Temporary forbit selection to prevent weird bug
        self.dlg.mosaicTable.setSelectionMode(QAbstractItemView.NoSelection)
        self.mosaics.update({mosaic.id: mosaic})
        self.mosaicsUpdated.emit()
        self.view.display_mosaics(list(self.mosaics.values()))
        # Allow selection back
        self.dlg.mosaicTable.setSelectionMode(QAbstractItemView.SingleSelection) 
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

    def delete_mosaics(self, 
                       response: QNetworkReply, 
                       mosaics: List[MosaicReturnSchema],
                       deleted: List[str], 
                       failed: List[str]):
        if len(mosaics) == 0:
            if failed:
                self.api.delete_mosaic_error_handler(mosaics=failed)
            self.get_mosaics()
            self.dlg.mosaicTable.clearSelection()
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

    def confirm_mosaic_deletion(self):
        mosaics = self.selected_mosaics()
        if not mosaics:
            return
        mosaic_names = [mosaic.name for mosaic in mosaics]
        if len(mosaic_names) == 1:
            message = self.tr("<center>Delete mosaic <b>'{name}'</b>?"
                             ).format(name=mosaic_names[0])
        elif len(mosaic_names) <= 3:
            message = self.tr("<center>Delete following mosaics:<br><b>'{names}'</b>?"
                             ).format(names="', <br>'".join(mosaic_names))
        else:
            message = self.tr("<center>Delete <b>{len}</b> mosaics?"
                             ).format(len=len(mosaic_names))
        box = QMessageBox(QMessageBox.Question, "Mapflow", message, parent=QApplication.activeWindow())
        box.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        box_exec = box.exec()
        if box_exec == QMessageBox.Ok:
            self.delete_mosaics(response = None, mosaics=mosaics, deleted=[], failed=[])

    def on_mosaic_selection(self, mosaic: MosaicReturnSchema):
        # Clear previous images details
        self.dlg.imageTable.clearSelection()
        self.dlg.imageTable.setRowCount(0)
        self.dlg.selected_mosaic_cell = self.dlg.mosaicTable.selectedIndexes()[0]
        self.view.add_mosaic_cell_buttons()
        self.get_mosaic_images(mosaic.id)
        self.view.show_mosaic_info(mosaic.name)

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
        image_paths = QFileDialog.getOpenFileNames(QApplication.activeWindow(), self.tr("Choose image to upload"), filter='(TIF files *.tif; *.tiff)')[0]
        if image_paths:
            self.upload_images(response=None, 
                               mosaic_id=mosaic.id, mosaic_name=mosaic.name, 
                               image_paths=image_paths, uploaded=[], failed=[])

    def upload_raster_layers_to_mosaic(self, layers_paths):
        mosaic = self.selected_mosaic()
        if layers_paths:
            self.upload_images(response=None, mosaic_id=mosaic.id, mosaic_name=mosaic.name, image_paths=layers_paths, uploaded=[], failed=[])

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
                                  " and file size less than {memory}").format(size=self.image_max_size_pixels,
                                                                              memory=helpers.get_readable_size(self.image_max_size_bytes))
                self.view.alert(self.tr("<center><b>Error uploading '{name}'</b>").format(name=Path(image_to_upload).name)+"<br>"+message)
                return
            # Check if user has enough stogage
            image_size=Path(image_to_upload).stat().st_size
            self.free_storage = 10
            if image_size > self.free_storage:#self.free_storage and image_size > self.free_storage:
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
        self.view.display_images(self.images)
        if self.view.mosaic_table_visible:
            self.view.display_mosaic_info(self.selected_mosaic(), self.images)

    def get_image(self, image_id: UUID, callback: Callable):
        self.api.get_image(image_id=image_id, callback=callback)

    def delete_images(self, 
                      response: QNetworkReply, 
                      images: List[ImageReturnSchema],
                      deleted: List[str], 
                      failed: List[str]):
        if len(images) == 0:
            if failed:
                self.api.delete_image_error_handler(image_paths=failed)
            mosaic_id = self.selected_mosaic().id
            self.get_mosaic(mosaic_id)
            self.dlg.imageTable.clearSelection()
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
            
    def confirm_image_deletion(self):
        mosaic = self.selected_mosaic()
        images = self.selected_images()
        if not images:
            return
        image_names = [image.filename for image in images]
        if len(image_names) == 1:
            message = self.tr("<center>Delete image <b>'{name}'</b> from '{mosaic}' mosaic?"
                             ).format(name=image_names[0], mosaic=mosaic.name)
        elif len(image_names) <= 3:
            message = self.tr("<center>Delete following images from '{mosaic}' mosaic:<br><b>'{names}'</b>?"
                             ).format(names="', <br>'".join(image_names), mosaic=mosaic.name)
        else:
            message = self.tr("<center>Delete <b>{len}</b> images from '{mosaic}' mosaic?"
                             ).format(len=len(image_names), mosaic=mosaic.name)
        box = QMessageBox(QMessageBox.Question, "Mapflow", message, parent=QApplication.activeWindow())
        box.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        box_exec = box.exec()
        if box_exec == QMessageBox.Ok:
            self.delete_images(response = None, images=images, deleted=[], failed=[])

    def on_image_selection(self, image: ImageReturnSchema):
        self.view.show_image_info(image)
        self.view.add_image_cell_buttons()
        self.get_image_preview_s(image)
        return image

    def image_info(self):
        image = self.selected_image()
        if not image:
            return
        self.view.full_image_info(image=image)

    def get_image_preview_s(self,
                            image: ImageReturnSchema):
        self.api.get_image_preview(image=image,
                                   size=PreviewSize.small,
                                   callback=self.get_image_preview_s_callback)

    def get_image_preview_s_callback(self, response: QNetworkReply):
        image = QImage.fromData(response.readAll().data())
        self.view.show_preview_s(image)

    def get_image_preview_l(self):
        try:
            image = self.selected_image()
            extent = layer_utils.footprint_to_extent(image.footprint)
            self.api.get_image_preview_l(image=image,
                                         extent=extent,
                                         callback=self.display_image_preview,
                                         image_name=image.filename)
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
        if self.view.mosaic_table_visible:
            self.create_mosaic()
        else:
            self.upload_images_to_mosaic()

    def delete_mosaic_or_image(self):
        image = self.selected_image()
        mosaic = self.selected_mosaic()
        if image:
            self.confirm_image_deletion()
        elif mosaic:
            self.confirm_mosaic_deletion()

    def switch_to_mosaics_table(self):
        mosaic = self.selected_mosaic()
        self.view.show_mosaics_table(mosaic.name)
        self.view.display_mosaic_info(mosaic, self.images)

    def check_image_selection(self):
        image = self.selected_image()
        if image:
            self.on_image_selection(image)
        else:
            self.view.clear_image_info()

    def check_mosaic_selection(self):
        mosaic = self.selected_mosaic()
        if mosaic:
            self.on_mosaic_selection(mosaic)
        else:
            self.view.clear_mosaic_info()

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
        mosaics = (self.mosaics.get(id) for id in ids)
        return [m for m in mosaics if m is not None]

    def selected_mosaic(self) -> Optional[MosaicReturnSchema]:
        first = self.selected_mosaics(limit=1)
        if not first:
            return None
        return first[0]
        
    def selected_images(self, limit=None) -> List[MosaicReturnSchema]:
        ids = self.view.selected_images_indecies(limit=limit)
        images = [i for i in self.images if i.id in ids]
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
        my_imagery_index = None
        if not isinstance (current_provider, MyImageryProvider):
            # Get index of My imagery provider
            for index in range(len(providers)):
                provider = providers[index]
                if isinstance(provider, MyImageryProvider):
                    my_imagery_index = index
            # Set My imagery data source
            if my_imagery_index:
                self.dlg.sourceCombo.setCurrentIndex(my_imagery_index)
