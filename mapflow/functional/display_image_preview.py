import os.path
from osgeo import gdal
from typing import Optional, Callable

from PyQt5.QtNetwork import QNetworkReply
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QApplication
from qgis.core import QgsRasterLayer, QgsCoordinateReferenceSystem, QgsRectangle

from ..dialogs import ErrorMessageWidget
from ..http import get_error_report_body
from configparser import ConfigParser
from ..functional import helpers


class PreviewImage(QObject):
    #def __init__(self, iface, maindialog, http, server, project, settings, plugin_name, temp_dir):
    def __init__(self, http, project, temp_dir):
        super().__init__()
        #self.message_bar = iface.messageBar()
        #self.dlg = maindialog
        self.http = http
        #self.iface = iface
        #self.server = server
        self.project = project
        #self.layer_tree_root = self.project.layerTreeRoot()
        # By default, plugin adds layers to a group unless user explicitly deletes it
        #self.add_layers_to_group = True
        #self.layer_group = None
        #self.settings = settings
        #self.plugin_name = plugin_name
        self.temp_dir = temp_dir
        self.plugin_dir = os.path.dirname(__file__)
        metadata_parser = ConfigParser()
        metadata_parser.read(os.path.join(self.plugin_dir, 'metadata.txt'))
        self.plugin_version = metadata_parser.get('general', 'version')
        self.metadata_layer = None
    
    def preview_image(self,
                      url: str,
                      extent: QgsRectangle,
                      image_id: str = ""):
        self.http.get(url=url,
                      timeout=30,
                      auth='null'.encode(),
                      callback=self.display_image_preview,
                      use_default_error_handler=False,
                      error_handler=self.preview_image_error_handler,
                      callback_kwargs={"extent": extent,
                                       "image_id": image_id})

    def display_image_preview(self,
                              response: QNetworkReply,
                              extent: QgsRectangle,
                              crs: QgsCoordinateReferenceSystem = QgsCoordinateReferenceSystem("EPSG:3857"),
                              image_id: str = ""):
        """
        We assume that png preview is not internally georeferenced,
        but the footprint specified in the metadata has the same extent, so we generate georef for the image
        """
        with open(os.path.join(self.temp_dir, os.urandom(32).hex()), mode='wb') as f:
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
        layer = QgsRasterLayer(f.name, f"{image_id} preview", 'gdal')
        layer.setExtent(extent)
        self.project.addMapLayer(layer)

    def preview_image_error_handler(self, response: QNetworkReply):
        self.report_http_error(response, "Could not display preview")

    def report_http_error(self,
                          response: QNetworkReply,
                          title: str = None,
                          error_message_parser: Optional[Callable] = None):
        """Prepare and show an error message for the supplied response.

        :param response: The HTTP response.
        :param title: The error message's title.
        :param error_message_parser: function to parse error message, depends on server which is requested.
            Default parser (if None) searches for 'message' section in response json
        """
        error_summary, email_body = get_error_report_body(response=response,
                                                          plugin_version=self.plugin_version,
                                                          error_message_parser=error_message_parser)
        ErrorMessageWidget(parent=QApplication.activeWindow(),
                           text=error_summary,
                           title=title,
                           email_body=email_body).show()
        
def metadata_feature(image_id):
    if not image_id:
        return None
    try:  # Get the image extent to set the correct extent on the raster layer
        return next(PreviewImage.metadata_layer.getFeatures(f"id = '{image_id}'"))
    except (RuntimeError, AttributeError, StopIteration):  # layer doesn't exist or has been deleted, or empty
        return None    
    
def metadata_extent(image_id=None,
                    feature=None,
                    crs: QgsCoordinateReferenceSystem = helpers.WEB_MERCATOR):
    if not feature:
        feature = metadata_feature(image_id=image_id)
    if not feature:
        return None
    return helpers.from_wgs84(feature.geometry(), crs).boundingBox()