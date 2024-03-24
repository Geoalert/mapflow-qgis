import os
import json
import tempfile
from typing import Optional, List
from pyproj import Proj, transform
from PyQt5.QtNetwork import QNetworkReply
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QFileDialog, QApplication
from qgis.core import (Qgis,
                       QgsRectangle,
                       QgsRasterLayer,
                       QgsFeature,
                       QgsMapLayer,
                       QgsVectorLayer,
                       QgsVectorTileLayer,
                       QgsJsonExporter,
                       QgsGeometry,
                       QgsMapLayerType,
                       QgsDataSourceUri,
                       QgsWkbTypes,
                       QgsCoordinateReferenceSystem,
                       QgsDistanceArea,
                       QgsVectorFileWriter,
                       QgsProject)
from pathlib import Path

from .geometry import clip_aoi_to_image_extent
from .helpers import WGS84, to_wgs84, WGS84_ELLIPSOID
from ..styles import get_style_name
from ..schema.catalog import AoiResponseSchema


def get_layer_extent(layer: QgsMapLayer) -> QgsGeometry:
    """Get a layer's bounding box aka extent/envelope
    /bounds.

    :param layer: The layer of interest
    """
    # Create a geometry from the layer's extent
    extent_geometry = QgsGeometry.fromRect(layer.extent())
    # Reproject it to WGS84 if the layer has another CRS
    layer_crs = layer.crs()
    if layer_crs != WGS84:
        extent_geometry = to_wgs84(extent_geometry, layer_crs)
    return extent_geometry


def generate_xyz_layer_definition(url, username, password, max_zoom, source_type):
    """
    It includes quadkey, tms and xyz layers, because QGIS treats them the same
    """
    if source_type == 'tms':
        # that is how QGIS understands that this is TMS basemap
        url = url.replace('{y}', '{-y}')
    url = url.replace('&', '%26').replace('=', '%3D')
    params = {
        'type': 'xyz',  # QGIS shows quadkey, tms, xyz - all as xyz layer
        'url': url,
        'zmin': 0,
        'zmax': max_zoom,
        'username': username,
        'password': password
    }
    uri = '&'.join(f'{key}={val}' for key, val in params.items())  # don't url-encode it
    return uri


def maxar_tile_url(base_url, image_id=None):
    """
    base_url is copied from maxar website and looks like
    https://securewatch.digitalglobe.com/earthservice/wmtsaccess?connectid=<UUID>
    we need to return TileUrl with TileMatrix set and so on
    """
    if not base_url.endswith('?'):
        # case when this is not the first arguments in layer
        base_url = base_url + '&'
    url = base_url + "SERVICE=WMTS" \
                     "&VERSION=1.0.0" \
                     "&STYLE=" \
                     "&REQUEST=GetTile" \
                     "&LAYER=DigitalGlobe:ImageryTileService" \
                     "&FORMAT=image/jpeg" \
                     "&TileRow={y}" \
                     "&TileCol={x}" \
                     "&TileMatrixSet=EPSG:3857" \
                     "&TileMatrix=EPSG:3857:{z}"
    url = add_image_id(url, image_id)
    return url


def add_image_id(url: str, image_id: str):
    if not image_id:
        return url
    if not url.endswith('?'):
        url = url + '&'
    return url + f'CQL_FILTER=feature_id=\'{image_id}\''


def add_connect_id(url: str, connect_id: str):
    if not url.endswith('?'):
        url = url + '&'
    return url + f'CONNECTID={connect_id}'


def get_bounding_box_from_tile_json(response: QNetworkReply) -> QgsRectangle:
    """Construct bounding box from response got from tile server as tile_json.
    As tile server returns tile_json in epsg:4326, first transform it to epsg:3857.
    :param: response: QNetworkReply, response got from tile server, tile_json.
    :return: QgsRectangle
    """
    bounds = json.loads(response.readAll().data()).get('bounds')
    out_proj = Proj(init='epsg:3857')
    in_proj = Proj(init='epsg:4326')

    xmin, ymin = transform(in_proj, out_proj, bounds[0], bounds[1])
    xmax, ymax = transform(in_proj, out_proj, bounds[2], bounds[3])

    return QgsRectangle(xmin, ymin, xmax, ymax)


def get_raster_aoi(raster_layer: QgsRasterLayer,
                   selected_aoi: QgsFeature,
                   use_image_extent_as_aoi: bool) -> QgsGeometry:
    layer_extent = QgsFeature()
    layer_extent.setGeometry(get_layer_extent(raster_layer))
    if not use_image_extent_as_aoi:
        # If we do not use the layer extent as aoi, we still create it and use it to crop the selected AOI
        try:
            feature = next(clip_aoi_to_image_extent(aoi_geometry=selected_aoi,
                                                    extent=layer_extent))
        except StopIteration:
            return None
    else:
        feature = layer_extent
    return feature.geometry()


def is_polygon_layer(layer: QgsMapLayer) -> bool:
    """Determine if a layer is of vector type and has polygonal geometry.
    :param layer: A layer to test
    """
    return layer.type() == QgsMapLayerType.VectorLayer and layer.geometryType() == QgsWkbTypes.PolygonGeometry


def calculate_aoi_area(aoi: QgsGeometry,
                       project_crs: QgsCoordinateReferenceSystem) -> float:
    calculator = QgsDistanceArea()
    calculator.setEllipsoid(WGS84_ELLIPSOID)
    calculator.setSourceCrs(WGS84, project_crs)
    aoi_size = calculator.measureArea(aoi) / 10 ** 6  # sq. m to sq.km
    return aoi_size


def collect_geometry_from_layer(layer: QgsMapLayer) -> QgsGeometry:
    features = list(layer.getSelectedFeatures()) or list(layer.getFeatures())
    if len(features) == 1:
        aoi = features[0].geometry()
    else:
        aoi = QgsGeometry.collectGeometry([feature.geometry() for feature in features])
    return aoi


def calculate_layer_area(layer: QgsMapLayer,
                         project_crs: QgsCoordinateReferenceSystem) -> float:
    crs = layer.crs()
    aoi = collect_geometry_from_layer(layer)
    if crs != WGS84:
        aoi = to_wgs84(aoi, crs)

    return calculate_aoi_area(aoi,
                              crs,
                              project_crs)


def export_as_geojson(layer: Optional[QgsVectorLayer]) -> dict:
    if not layer:
        return {"type": "FeatureCollection", "features": []}
    exporter = QgsJsonExporter(layer)
    gejson_str = exporter.exportFeatures(layer.getFeatures())
    return json.loads(gejson_str)


def generate_raster_layer(layer_uri,
                          name,
                          min_zoom=0,
                          max_zoom=18,
                          username=None,
                          password=None,
                          ):
    if not layer_uri:
        return None
    params = {
        'type': 'xyz',
        'url': layer_uri,
        'zmin': min_zoom,
        'zmax': max_zoom,
    }
    if username and password:
        params.update(username=username, password=password)
    layer = QgsRasterLayer(
        '&'.join(f'{key}={val}' for key, val in params.items()),  # don't URL-encode it
        name,
        'wms'
    )
    return layer


def generate_vector_layer(layer_uri,
                          name,
                          min_zoom=14,
                          max_zoom=25,
                          username=None,
                          password=None,
                          ):
    if not layer_uri:
        return None
    params = {
        'type': 'xyz',
        'url': layer_uri,
        'zmin': min_zoom,
        'zmax': max_zoom,
    }
    if username and password:
        params.update(username=username, password=password)
    layer = QgsVectorTileLayer(
        '&'.join(f'{key}={val}' for key, val in params.items()),  # don't URL-encode it
        name
    )
    return layer


# Layer management for results
class ResultsLoader(QObject):
    def __init__(self, iface, maindialog, http, server, project, settings, plugin_name, temp_dir):
        super().__init__()
        self.message_bar = iface.messageBar()
        self.dlg = maindialog
        self.http = http
        self.iface = iface
        self.server = server
        self.project = project
        self.layer_tree_root = self.project.layerTreeRoot()
        # By default, plugin adds layers to a group unless user explicitly deletes it
        self.add_layers_to_group = True
        self.layer_group = None
        self.settings = settings
        self.plugin_name = plugin_name
        self.temp_dir = temp_dir

    # ======= General layer management  ====== #

    def add_layer(self, layer: Optional[QgsMapLayer]) -> None:
        """Add layers created by the plugin to the legend.

        By default, layers are added to a group with the same name as the plugin.
        If the group has been deleted by the user, assume they prefer to not use
        the group, and add layers to the legend root.

        :param layer: A vector or raster layer to be added.
        """
        if not layer:
            return
        self.layer_group = self.layer_tree_root.findGroup(self.settings.value('layerGroup'))
        if self.add_layers_to_group:
            if not self.layer_group:  # сreate a layer group
                self.layer_group = self.layer_tree_root.insertGroup(0, self.plugin_name)
                # A bug fix, - gotta collapse first to be able to expand it
                # Or else it'll ignore the setExpanded(True) calls
                self.layer_group.setExpanded(False)
                self.settings.setValue('layerGroup', self.plugin_name)
                # If the group has been deleted, assume user wants to add layers to root, memorize it
                self.layer_group.destroyed.connect(lambda: setattr(self, 'add_layers_to_group', False))
                # Let user rename the group, memorize the new name
                self.layer_group.nameChanged.connect(lambda _, name: self.settings.setValue('layerGroup', name))
            # To be added to group, layer has to be added to project first
            self.project.addMapLayer(layer, addToLegend=False)
            # Explcitly add layer to the position 0 or else it adds it to bottom
            self.layer_group.insertLayer(0, layer)
            self.layer_group.setExpanded(True)
        else:  # assume user opted to not use a group, add layers as usual
            self.project.addMapLayer(layer)

    def add_layer_by_order(self, layer: Optional[QgsMapLayer], order) -> None:
        if not layer:
            return
        self.layer_group = self.layer_tree_root.findGroup(self.settings.value('layerGroup'))
        if self.add_layers_to_group:
            if not self.layer_group:  # сreate a layer group
                self.layer_group = self.layer_tree_root.insertGroup(0, self.plugin_name)
                # A bug fix, - gotta collapse first to be able to expand it
                # Or else it'll ignore the setExpanded(True) calls
                self.layer_group.setExpanded(False)
                self.settings.setValue('layerGroup', self.plugin_name)
                # If the group has been deleted, assume user wants to add layers to root, memorize it
                self.layer_group.destroyed.connect(lambda: setattr(self, 'add_layers_to_group', False))
                # Let user rename the group, memorize the new name
                self.layer_group.nameChanged.connect(lambda _, name: self.settings.setValue('layerGroup', name))
            # To be added to group, layer has to be added to project first
            self.project.addMapLayer(layer, addToLegend=False)
            # Explcitly add layer to the position 0 or else it adds it to bottom
            self.layer_group.insertLayer(order, layer)
            self.layer_group.setExpanded(True)
        else:  # assume user opted to not use a group, add layers as usual
            self.project.addMapLayer(layer)

    def add_basemap_layer(self, basemap, layer):
        # Remove layer if already exists
        for l in self.iface.mapCanvas().layers():
            if basemap in l.dataProvider().dataSourceUri():
                QgsProject.instance().removeMapLayers([l.id()])
        # Append each basemap layer to a list and add new ones at the top of a group
        basemaps = []
        for l in self.iface.mapCanvas().layers():
            if "{z}" or "http" in l.dataProvider().dataSourceUri():
                basemaps.append(l.id())
            other_preview_layer_id = basemaps[-1]
            other_preview_layer = QgsProject.instance().layerTreeRoot().findLayer(other_preview_layer_id)
            parent_group = other_preview_layer.parent()
            index = parent_group.children().index(other_preview_layer)
            self.add_layer_by_order(order = index, layer = layer)
            return
        self.add_layer_by_order(layer=layer, order=-1)
        return

    # ======= Load as tile layers ====== #

    def load_result_tiles(self, processing):
        raster_tilejson = processing.raster_layer.get("tileJsonUrl", None)
        vector_tilejson = processing.vector_layer.get("tileJsonUrl", None)
        raster_layer = generate_raster_layer(processing.raster_layer.get("tileUrl", None),
                                             name=f"{processing.name} raster")
        vector_layer = generate_vector_layer(processing.vector_layer.get("tileUrl", None),
                                             name=processing.name)
        vector_layer.loadNamedStyle(get_style_name(processing.workflow_def, vector_layer))
        #os.path.join(self.plugin_dir, 'static', 'styles', 'tiles.qml'))
        self.add_layer(raster_layer)
        self.add_layer(vector_layer)
        self.request_layer_extent(None,
                                  tilejson_uris=[uri for uri in (raster_tilejson, vector_tilejson) if
                                                 uri is not None],
                                  raster_layer=raster_layer,
                                  vector_layer=vector_layer)

    def request_layer_extent(self,
                             response: QNetworkReply,
                             tilejson_uris: List[str],
                             raster_layer,
                             vector_layer):
        if not tilejson_uris:
            # All available tilejson urls were tried and none returned success
            self.message_bar.pushWarning(self.tr("Results loaded"),
                                         self.tr("Extent failed to load, zoom to the layers manually"))
        # request with the first and save the rest in case of error
        main_tilejson_uri = tilejson_uris[0]
        other_tilejson_uris = tilejson_uris[1:]
        self.http.get(url=main_tilejson_uri,
                      callback=self.add_layers_with_extent,
                      callback_kwargs={"raster": raster_layer,
                                       "vector": vector_layer},
                      error_handler=self.request_layer_extent,
                      error_handler_kwargs={"tilejson_uris": other_tilejson_uris,
                                            "raster_layer": raster_layer,
                                            "vector_layer": vector_layer},
                      use_default_error_handler=False,
                      )

    def add_layers_with_extent(
            self,
            response: QNetworkReply,
            vector: QgsVectorLayer,
            raster: QgsRasterLayer
    ) -> None:
        """Set processing raster extent upon successfully requesting the processing's AOI.

        :param response: The HTTP response.
        :param vector: The downloaded feature layer.
        :param raster: The downloaded raster which was used for processing.
        """
        bounding_box = get_bounding_box_from_tile_json(response=response)
        raster.setExtent(rect=bounding_box)
        vector.setExtent(rect=bounding_box)
        self.iface.setActiveLayer(vector)
        self.iface.zoomToActiveLayer()
        self.message_bar.pushSuccess(self.tr("Success"),
                                     self.tr("Results loaded to the project"))

    # ====== Download as geojson ===== #
    def download_results_file(self, pid) -> None:
        """
        Download result and save directly to a geojson file
        It is the most reliable way to get results, applicable if everything else failed
        """
        path, _ = QFileDialog.getSaveFileName(QApplication.activeWindow(),
                                              self.tr('Save processing results'),
                                              filter="*.geojson")
        if not path:
            # if the path was not selected
            return
        self.dlg.saveOptionsButton.setEnabled(False)
        self.http.get(
            url=f'{self.server}/processings/{pid}/result',
            callback=self.download_results_file_callback,
            callback_kwargs={'path': path},
            use_default_error_handler=False,
            error_handler=self.download_results_file_error_handler,
            timeout=300
        )

    def download_aoi_file(self, pid) -> None:
        """
        Download area of interest and save to a geojson file
        """ 
        path = Path(self.temp_dir)/f'{pid}_aoi.geojson'                         
        self.dlg.saveOptionsButton.setEnabled(False)
        self.http.get(
            url=f'{self.server}/processings/{pid}/aois',
            callback=self.download_aoi_file_callback,
            callback_kwargs={'path': path},
            use_default_error_handler=True,
            timeout=30
        )

    def download_results_file_callback(self, response: QNetworkReply, path: str) -> None:
        """
        Write results to the geojson file
        """
        self.dlg.saveOptionsButton.setEnabled(True)
        with open(path, mode='wb') as f:
            f.write(response.readAll().data())
        self.message_bar.pushSuccess(self.tr("Results saved"),
                                     self.tr("see in {path}!").format(path=path))
        
    def download_aoi_file_callback(self, response: QNetworkReply, path: str) -> None:
        """
        Write area of interest to the geojson file
        """
        self.dlg.saveOptionsButton.setEnabled(True)
        data = json.loads(response.readAll().data())
        geojson = AoiResponseSchema(data).aoi_as_geojson()
        with open(path, "w") as f:
            json.dump(geojson, f)
        id = Path(path).stem[:-4]
        aoi_layer = QgsVectorLayer(str(path), "AOI: {id}".format(id=id))
        self.add_layer(aoi_layer)
        aoi_layer.loadNamedStyle(str(Path(__file__).parents[1]/'static'/'styles'/'aoi.qml'))
        
    def download_results_file_error_handler(self, response: QNetworkReply) -> None:
        """Error handler for downloading processing results.

        :param response: The HTTP response.
        """
        self.dlg.saveResultsButton.setEnabled(True)
        self.message_bar.pushWarning(self.tr("Error"),
                                     self.tr('could not download results, \n try again later or report error'),
                                     )

    # ======= Save as geopackage and add as layer - old variant ======= #

    def download_results_callback(self, response: QNetworkReply, processing) -> None:
        """Display processing results upon their successful fetch.

        :param response: The HTTP response.
        :param pid: ID of the inspected processing.
        """
        self.dlg.processingsTable.setEnabled(True)
        # Avoid overwriting existing files by adding (n) to their names
        output_path = os.path.join(self.dlg.outputDirectory.text(), processing.id_)
        extension = '.gpkg'
        if os.path.exists(output_path + extension):
            count = 1
            while os.path.exists(output_path + f'({count})' + extension):
                count += 1
            output_path += f'({count})' + extension
        else:
            output_path += extension
        transform = self.project.transformContext()
        # Layer creation options for QGIS 3.10.3+
        write_options = QgsVectorFileWriter.SaveVectorOptions()
        write_options.layerOptions = ['fid=id']
        with open(os.path.join(self.temp_dir, os.urandom(32).hex()), mode='wb+') as f:
            f.write(response.readAll().data())
            f.seek(0)
            layer = QgsVectorLayer(f.name, '', 'ogr')
            # V3 returns two additional str values but they're not documented, so just discard them
            error, msg, *_ = QgsVectorFileWriter.writeAsVectorFormatV3(
                layer,
                output_path,
                transform,
                write_options
            )
        if error:
            self.message_bar.pushWarning(self.tr("Error"),
                                         self.tr('Failed to save results to file. '
                                                 'Error code: {code}. Message: {message}').format(code=error,
                                                                                                  message=msg))
            return
        # Load the results into QGIS
        results_layer = QgsVectorLayer(output_path, processing.name, 'ogr')
        results_layer.loadNamedStyle(get_style_name(processing.workflow_def, layer))
        # Add the source raster (COG) if it has been created
        raster_url = processing.raster_layer.get('tileUrl')
        tile_json_url = processing.raster_layer.get("tileJsonUrl")
        if raster_url:
            params = {
                'type': 'xyz',
                'url': raster_url,
                'zmin': 0,
                'zmax': 18,
                # 'username': self.username,
                # 'password': self.password
            }
            raster = QgsRasterLayer(
                '&'.join(f'{key}={val}' for key, val in params.items()),  # don't URL-encode it
                processing.name + ' image',
                'wms'
            )
            self.http.get(
                url=tile_json_url,
                callback=self.set_raster_extent,
                callback_kwargs={
                    'vector': results_layer,
                    'raster': raster
                },
                use_default_error_handler=False,
                error_handler=self.set_raster_extent_error_handler,
                error_handler_kwargs={
                    'vector': results_layer,
                }
            )
        else:
            self.set_raster_extent_error_handler(response=None, vector=results_layer)

    def download_results_error_handler(self, response: QNetworkReply) -> None:
        """Error handler for downloading processing results.

        :param response: The HTTP response.
        """
        self.dlg.processingsTable.setEnabled(True)
        self.message_bar.pushWarning(self.tr("Error"),
                                     self.tr('failed to download results, \n try again later or report error'))

    def set_raster_extent(
            self,
            response: QNetworkReply,
            vector: QgsVectorLayer,
            raster: QgsRasterLayer
    ) -> None:
        """Set processing raster extent upon successfully requesting the processing's AOI.

        :param response: The HTTP response.
        :param vector: The downloaded feature layer.
        :param raster: The downloaded raster which was used for processing.
        """
        bounding_box = get_bounding_box_from_tile_json(response=response)
        raster.setExtent(rect=bounding_box)
        self.add_layer(raster)
        self.add_layer(vector)
        self.iface.zoomToActiveLayer()

    def set_raster_extent_error_handler(self,
                                        response: QNetworkReply,
                                        vector: Optional[QgsVectorLayer] = None):

        """Error handler for processing AOI requests. If tilejson can't be loaded, we do not add raster layer, and
        """
        self.add_layer(vector)
