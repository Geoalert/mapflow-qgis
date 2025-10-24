import json
import os
from osgeo import gdal
from pathlib import Path
from typing import Optional, List

from PyQt5.QtCore import QObject
from PyQt5.QtNetwork import QNetworkReply
from PyQt5.QtWidgets import QFileDialog, QApplication
from pyproj import Proj, transform
from qgis.core import (QgsRectangle,
                       QgsRasterLayer,
                       QgsFeature,
                       QgsMapLayer,
                       QgsVectorLayer,
                       QgsVectorTileLayer,
                       QgsJsonExporter,
                       QgsGeometry,
                       QgsMapLayerType,
                       QgsWkbTypes,
                       QgsCoordinateReferenceSystem,
                       QgsDistanceArea,
                       QgsVectorFileWriter,
                       QgsProject,
                       QgsMessageLog,
                       QgsCoordinateTransform
                       )

from .geometry import clip_aoi_to_image_extent, clip_aoi_to_catalog_extent
from .helpers import WGS84, to_wgs84, WGS84_ELLIPSOID
from ..dialogs.error_message_widget import ErrorMessageWidget
from ..schema.catalog import AoiResponseSchema
from ..styles import get_style_name


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


def get_catalog_aoi(catalog_aoi: QgsGeometry,
                    selected_aoi: QgsGeometry) -> QgsGeometry:
    """Return either AOI geometry if it intersects with imagery frootprint or the footprint itself.
    :param catalog_aoi: Image or mosaic footprint.
    :param selected_aoi: Currently selected in polygonCombo AOI layer.
    """
    clipped_aoi_features = clip_aoi_to_catalog_extent(catalog_aoi, selected_aoi)
    clipped_aoi = QgsGeometry.fromWkt('GEOMETRYCOLLECTION()')
    for feature in clipped_aoi_features:
        geom = feature.geometry()
        clipped_aoi = clipped_aoi.combine(geom)
    return clipped_aoi


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

def count_polygons_in_layer(features: list) -> int:
    """ Count polygon geometries in a multipolygon layer (instead of counting features).
    :param features: A list of fetures, obtained by "list(layer.getFeatures())"
    """
    count = sum(len(feature.geometry().asMultiPolygon()) for feature in features)
    return count

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

def footprint_to_extent(footprint: dict) -> QgsRectangle:
    """Construct bounding box from response got from image footprint.
    As tile server returns tile_json in epsg:4326, first transform it to epsg:3857.
    :param: footprint: dict, which should be geojson-like dict (geometry).
    :return: QgsRectangle
    """
    source_crs = QgsCoordinateReferenceSystem(4326)
    dest_crs = QgsCoordinateReferenceSystem(3857)
    tr = QgsCoordinateTransform(source_crs, dest_crs, QgsProject.instance())
    geom = QgsGeometry.fromWkt(footprint)
    geom.transform(tr)
    extent = geom.boundingBox()
    return extent


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

    def add_layer(self, layer: Optional[QgsMapLayer], order=0) -> None:
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
            # Explcitly add layer to the position 0 (default value) or else it adds it to bottom
            self.layer_group.insertLayer(order, layer)
            self.layer_group.setExpanded(True)
        else:  # assume user opted to not use a group, add layers as usual
            self.project.addMapLayer(layer)

    def add_preview_layer(self, preview_layer, preview_dict): 
        # Delete layer from dictionary if it was deleted from layer tree
        for url, id in preview_dict.copy().items():
            if id not in self.project.mapLayers() and id != preview_layer.id():
                del preview_dict[url]
        # Revove the old layer if its url matches current one and its in the dictionary
        url = preview_layer.dataProvider().dataSourceUri()
        if url in preview_dict.keys():
            current_preview_id = preview_dict[url]
            # We can't have many layers with the same ID 
            QgsProject.instance().removeMapLayer(current_preview_id)
            # And delete old item from dictionary to rewrite it to a new position 
            # (So later we can easyly find the last added preview)
            del preview_dict[url] 
        # For the first added preview, just add it to the bottom
        if len(preview_dict) == 0:
            self.add_layer(layer = preview_layer, order=-1)
        # In other cases - add it to the top of plugin added previews
        else:
            top_preview_id = list(preview_dict.values())[-1]
            top_preview_layer = QgsProject.instance().layerTreeRoot().findLayer(top_preview_id)
            index = top_preview_layer.parent().children().index(top_preview_layer)
            self.add_layer(layer = preview_layer, order = index)
        # Add preview url and id to the dictionary
        preview_dict[url] = preview_layer.id()

    def get_footprint_corners(self, footprint: QgsGeometry):
        corners = []
        footprint = footprint.asGeometryCollection()[0].asPolygon() # in case it's a MultiPolygon with only one polygon
        if len(footprint[0]) != 5:
            self.message_bar.pushInfo(self.plugin_name, self.tr('Preview is unavailable'))
            return
        for point in range(4):
            pt = footprint[0][point]
            coords = (pt.x(), pt.y())
            corners.append(coords)
        return corners
  
    def georeference_preview_part(self,
                                  response: QNetworkReply,
                                  footprint: QgsGeometry,
                                  crs: QgsCoordinateReferenceSystem = QgsCoordinateReferenceSystem("EPSG:3857")):
        """ Generate World File for every part of multi-image preview before creating VRT. """
        # Get a list of coordinate pairs
        corners = self.get_footprint_corners(footprint)
        # Get non-referenced raster and set its projection
        with open(self.temp_dir/os.urandom(32).hex(), mode='wb') as f:
            f.write(response.readAll().data())
        preview = gdal.Open(f.name)
        preview.SetProjection(crs.toWkt())
        # Return a list of coordinate pairs
        corners = []
        footprint = footprint.asGeometryCollection()[0].asPolygon() # in case it's a MultiPolygon with only one polygon
        if len(footprint[0]) != 5:
            self.message_bar.pushInfo(self.plugin_name, self.tr('Preview is unavailable'))
            return
        for point in range(4):
            pt = footprint[0][point]
            coords = (pt.x(), pt.y())
            corners.append(coords)
        # Extract coordinates
        ul_lon, ul_lat = corners[0]  # Upper left
        ur_lon, ur_lat = corners[1]  # Upper right
        lr_lon, lr_lat = corners[2]  # Lower right
        ll_lon, ll_lat = corners[3]  # Lower left
        # Get image dimentions
        width = preview.RasterXSize
        height = preview.RasterYSize
        # Calculate pixel sizes
        pixel_width = (ur_lon - ul_lon) / width
        pixel_height = (ll_lat - ul_lat) / height
        # Upper left coordinates (center of upper left pixel)
        x_origin = ul_lon + (pixel_width / 2)
        y_origin = ul_lat - (pixel_height / 2)
        world_file_content = f"""{pixel_width}
                                 0.0
                                 0.0
                                 {pixel_height}
                                 {x_origin}
                                 {y_origin}"""
        # Write world file
        world_file_path = f.name + '.wld'
        with open(world_file_path, 'w') as world_file:
            world_file.write(world_file_content)
        return f.name

    # ======= Load as tile layers ====== #

    def load_result_tiles(self, processing):
        raster_tilejson = processing.raster_layer.get("tileJsonUrl", None)
        vector_tilejson = processing.vector_layer.get("tileJsonUrl", None)
        raster_layer = generate_raster_layer(processing.raster_layer.get("tileUrl", None),
                                             name=f"{processing.name} raster")
        vector_layer = generate_vector_layer(processing.vector_layer.get("tileUrl", None),
                                             name=processing.name)
        vector_layer.loadNamedStyle(get_style_name(processing.workflow_def, vector_layer))
        self.request_layer_extent(tilejson_uri=raster_tilejson,
                                  layer=raster_layer,
                                  next_layers = [vector_layer],
                                  next_tilejson_uris = [vector_tilejson],
                                  processing_id = processing.id_
                                  )

    def request_layer_extent(self,
                             tilejson_uri: str,
                             layer: QgsMapLayer,
                             next_layers: List[QgsMapLayer],
                             next_tilejson_uris: List[str],
                             errors: bool = False,
                             processing_id: Optional[str] = None
                             ):
        self.http.get(url=tilejson_uri,
                      callback=self.add_layers_with_extent,
                      callback_kwargs={"layer": layer,
                                       "processing_id": processing_id,
                                       "next_layers": next_layers,
                                       "next_tilejson_uris": next_tilejson_uris,
                                       "errors": errors},
                      error_handler=self.add_layers_with_extent,
                      error_handler_kwargs={"layer": layer,
                                            "processing_id": processing_id,
                                            "errors": errors,
                                            "next_layers": next_layers,
                                            "next_tilejson_uris": next_tilejson_uris,
                                            },
                      use_default_error_handler=False,
                      )

    def add_layers_with_extent(
            self,
            response: QNetworkReply,
            layer: QgsMapLayer,
            next_layers: List[QgsMapLayer],
            next_tilejson_uris: List[str],
            errors: bool = False,
            processing_id: Optional[str] = None
    ) -> None:
        if response.error() != QNetworkReply.NoError:
            errors = True
        else:
            try:
                bounding_box = get_bounding_box_from_tile_json(response=response)
            except Exception as e:
                errors = True
            else:
                layer.setExtent(rect=bounding_box)
                self.add_layer(layer)
            self.iface.setActiveLayer(layer)
            self.iface.zoomToActiveLayer()
        if next_layers and next_tilejson_uris:
            self.request_layer_extent(tilejson_uri=next_tilejson_uris[0],
                                      layer=next_layers[0],
                                      next_layers=next_layers[1:],
                                      next_tilejson_uris=next_tilejson_uris[1:],
                                      errors=errors,
                                      processing_id=processing_id
                                      )
        elif errors:
            # Report errors if there were any in layers loading
            self.report_layer_error(errors, processing_id=processing_id)


    def report_layer_error(self,
                           response: QNetworkReply = None,
                           processing_id: Optional[str] = None):
        error_summary =  self.tr('Failed to download results \n'
                                 'please try again later or report error').format(processing_id)
        title = self.tr("Error")
        email_body = "Error while loading results layer." \
                     f"Processing id: {processing_id}"

        ErrorMessageWidget(parent=QApplication.activeWindow(),
                           text=error_summary,
                           title=title,
                           email_body=email_body).show()

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

    def download_aoi_file(self, pid, callback) -> None:
        """
        Download area of interest and save to a geojson file
        """ 
        path = Path(self.temp_dir)/f'{pid}_aoi.geojson'                         
        self.dlg.saveOptionsButton.setEnabled(False)
        self.http.get(
            url=f'{self.server}/processings/{pid}/aois',
            callback=callback,
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
        self.dlg.polygonCombo.setLayer(aoi_layer)
        
    def download_results_file_error_handler(self,
                                            response: QNetworkReply,
                                            processing_id: Optional[str] = None) -> None:
        """Error handler for downloading processing results.

        :param response: The HTTP response.
        """
        self.dlg.saveResultsButton.setEnabled(True)
        self.report_layer_error(response, processing_id)

    # ======= Save as geopackage and add as layer - old variant ======= #

    def download_results(self, processing) -> None:
        """
        Download and display processing results along with the source raster, if available.

        Results will be downloaded into the user's output directory.
        If it's unset, the user will be prompted to select one.
        Unfinished or failed processings yield partial or no results.

        Is called by double-clicking on a row in the processings table.
        """
        self.dlg.processingsTable.setEnabled(False)
        self.http.get(
            url=f'{self.server}/processings/{processing.id_}/result',
            callback=self.download_results_callback,
            callback_kwargs={'processing': processing},
            use_default_error_handler=False,
            error_handler=self.download_results_error_handler,
            timeout=300
        )

    def download_results_callback(self, response: QNetworkReply, processing) -> None:
        """Display processing results upon their successful fetch.

        :param response: The HTTP response.
        :param pid: ID of the inspected processing.
        """
        self.dlg.processingsTable.setEnabled(True)
        # Avoid overwriting existing files by adding (n) to their names
        output_path = Path(self.dlg.outputDirectory.text(), processing.id_).with_suffix(".gpkg")
        if output_path.exists():
            count = 1
            while output_path.with_stem(processing.id_ + f"_{count}").exists():
                count += 1
            output_path = output_path.with_stem(processing.id_ + f"_{count}")
        transform = self.project.transformContext()
        # Layer creation options for QGIS 3.10.3+
        write_options = QgsVectorFileWriter.SaveVectorOptions()
        write_options.layerOptions = ['fid=id']
        with open(Path(self.temp_dir, os.urandom(32).hex()), mode='wb+') as f:
            response_data = response.readAll().data()
            # Check if there is more then 1 geometry type
            data = json.loads(response_data)
            geom_types = []
            for feature in data['features']:
                geom_type = feature['geometry']['type']
                if geom_type not in geom_types: # check if we have different geometry types
                    geom_types.append(geom_type)
                if any("Polygon" in geom for geom in geom_types) and any("LineString" in geom for geom in geom_types):
                    break # stop iterating if (multi)lines and (multi)polygons are already found
            # Create layer
            f.write(response_data)
            layer = QgsVectorLayer(f.name, '', 'ogr')
            # V3 returns two additional str values but they're not documented, so just discard them
            error, msg, *_ = QgsVectorFileWriter.writeAsVectorFormatV3(
                layer,
                str(output_path),
                transform,
                write_options
            )
        if error:
            # Give an info message
            text = self.tr('Failed to save results to GeoPackage. '
                           'Error code: {code}. '.format(code=error))
            if msg:
                text +=self.tr('Message: {message}. '.format(message=msg))
            text += self.tr('File will be saved as GeoJSON instead.')
            self.message_bar.pushMessage(self.tr("Warning"), text)
            # Save as GeoJSON instead
            output_path = output_path.with_suffix(".geojson")
            if output_path.exists():
                count = 1
                while output_path.with_stem(processing.id_ + f"_{count}").exists():
                    count += 1
                output_path = output_path.with_stem(processing.id_ + f"_{count}")
            try:
                with open(str(output_path), mode='wb+') as f:
                        f.write(response_data)
            except:
                self.message_bar.pushWarning(self.tr("Error"), self.tr('Failed to save results to file.'))
                return
        # Load the results into QGIS
        results_layers = []
        if any("Polygon" in geom for geom in geom_types) and\
           any("LineString" in geom for geom in geom_types): # e.g. loading roads and buildings from open data
            # Load Polygons
            polygon_uri = f"{output_path}|geometrytype=Polygon"
            polygon_layer = QgsVectorLayer(polygon_uri, processing.name, "ogr")
            polygon_layer.loadNamedStyle(get_style_name(processing.workflow_def+"_polygon", polygon_layer))
            if polygon_layer.isValid():
                results_layers.append(polygon_layer)
            # Load lineStrings
            linestring_uri = f"{output_path}|geometrytype=LineString"
            linestring_layer = QgsVectorLayer(linestring_uri, processing.name, "ogr")
            linestring_layer.loadNamedStyle(get_style_name(processing.workflow_def+"_line", linestring_layer))
            if linestring_layer.isValid():
                results_layers.append(linestring_layer)
        else: # regular processing with one geometry type
            results_layer = QgsVectorLayer(str(output_path), processing.name, 'ogr')
            results_layer.loadNamedStyle(get_style_name(processing.workflow_def, layer))
            results_layers.append(results_layer)
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
                    'vectors': results_layers,
                    'raster': raster
                },
                use_default_error_handler=False,
                error_handler=self.set_raster_extent_error_handler,
                error_handler_kwargs={
                    'vectors': results_layers,
                }
            )
        else:
            self.set_raster_extent_error_handler(response=None, vectors=results_layers)

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
            vectors: List[QgsVectorLayer],
            raster: QgsRasterLayer
    ) -> None:
        """Set processing raster extent upon successfully requesting the processing's AOI.

        :param response: The HTTP response.
        :param vector: The downloaded feature layer.
        :param raster: The downloaded raster which was used for processing.
        """
        try:
            bounding_box = get_bounding_box_from_tile_json(response=response)
        except Exception as e:
            # we assume that the raster extent must be present,
            # otherwise there is some error in raster tile server, and we should not add the layer
            self.message_bar.pushWarning(self.tr("Results loaded"),
                                         self.tr("Extent failed to load, zoom to the layers manually"))
            self.set_raster_extent_error_handler(response, vectors)
            return
        raster.setExtent(rect=bounding_box)
        self.add_layer(raster)
        for vector in vectors:
            self.add_layer(vector)
        # If raster is available, we zoom to the raster to fit the whole processing, not only the detected objects
        self.iface.setActiveLayer(raster)
        self.iface.zoomToActiveLayer()
        self.iface.setActiveLayer(vectors[0])

    def set_raster_extent_error_handler(self,
                                        response: QNetworkReply,
                                        vectors: Optional[List[QgsVectorLayer]] = None):

        """Error handler for processing AOI requests. If tilejson can't be loaded, we do not add raster layer, and
        """
        for vector in vectors:
            self.add_layer(vector)
        self.iface.setActiveLayer(vectors[0])
        self.iface.zoomToActiveLayer()
