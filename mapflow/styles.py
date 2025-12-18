from pathlib import Path
from typing import Optional

from qgis.core import QgsVectorLayer, QgsVectorTileLayer, QgsWkbTypes

STYLES = {
    '🏠 Buildings': 'buildings',
    'Buildings Detection With Heights': 'building_heights_class',
    '🌲 Forest': 'forest',
    '🌲 Forest and trees': 'forest',
    '🌲↕️ Forest with heights': 'forest_with_heights',
    '🚗 Roads': 'roads',
    '🏗️ Construction sites': 'construction'
}

DEFAULT_STYLE = "default"

def generate_local_style_path(name: str) -> str:
    return str(Path(__file__).parent / 'static' / 'styles' / 'file' / (name + '.qml'))

def generate_tile_style_path(name: str) -> str:
    return str(Path(__file__).parent / 'static' / 'styles' / 'tiles' / (name + '.qml'))

def get_style_name(wd_name: str, layer: QgsVectorLayer, style_name: Optional[str] = None) -> str:
    if isinstance(layer, QgsVectorTileLayer):
        style_name = get_tile_style_name(wd_name, style_name)
        return generate_tile_style_path(style_name)
    else:
        style_name = get_local_style_name(wd_name, layer, style_name)
        return generate_local_style_path(style_name)

def get_tile_style_name(wd_name, style_name=None):
    if style_name:
        style = get_tile_style_name_from_api(style_name)
        if style:
            return style
    return get_tile_style_name_from_wd_name(wd_name)

def get_local_style_name(wd_name, layer, style_name=None):
    if style_name:
        style = get_local_style_name_from_api(style_name, layer)
        if style:
            return style
    return get_local_style_name_from_wd_name(wd_name, layer)

def get_tile_style_name_from_api(style_name: str) -> Optional[str]:
    return {"buildings": "buildings",
            "building_heights": "building_heights",
            "forest": "forest",
            "roads": "roads",
            "construction": "construction"}.get(style_name, None)

def get_local_style_name_from_api(style_name: str, layer:QgsVectorLayer) -> Optional[str]:
    base_style = {"combo": "landuse",
                  "buildings": "buildings",
                  "building_heights": "building_heights",
                  "forest": "forest",
                  "roads": "roads",
                  "construction": "construction",
                  "open_data": "open_data"}.get(style_name, None)
    if base_style == "buildings":
        # modify buildings style according to the layer properties
        if "class_id" in layer.fields().names() and "building_height" in layer.fields().names():
            return "building_heights_class"
        elif "building_height" in layer.fields().names():
            return "building_heights"
        elif "class_id" in layer.fields().names():
            return "buildings"
        else:
            return "buildings_noclass"
    elif base_style == "forest":
        # modify forest style according to the layer properties (classification)
        if layer.geometryType() == QgsWkbTypes.PointGeometry:
            return "forest_crowns_points"
        elif "class_id" in layer.fields().names():
            return "forest_with_heights"
        else:
            return "forest"
    elif base_style == "open_data":
        # modify open_data style according to the layer geometry (poly / line)
        if layer.geometryType() == QgsWkbTypes.PolygonGeometry:
            return "open_data_polygon"
        else:
            return "open_data_line"

    return base_style


def get_tile_style_name_from_wd_name(wd_name: str) -> str:
    if "building" in wd_name.lower() and "height" in wd_name.lower():
        name = 'building_heights'
    elif "building" in wd_name.lower():
        name = 'buildings'
    elif "forest" in wd_name.lower():
        name = "forest"
    elif "road" in wd_name.lower():
        name = "roads"
    elif "construction" in wd_name.lower():
        name = "construction"
    else:
        name = 'default'
    return name


def get_local_style_name_from_wd_name(wd_name: str, layer: QgsVectorLayer) -> str:
    name = STYLES.get(wd_name, DEFAULT_STYLE)
    
    # Land use
    if "building" in wd_name.lower() and "road" in wd_name.lower():
        name = 'landuse'

    # Buildings with heights
    elif "building" in wd_name.lower() and "height" in wd_name.lower():
        name = 'building_heights'
    # Classification and heights enabled
    elif "building" in wd_name.lower() and "building_height" in layer.fields().names() and "class_id" in layer.fields().names():
        name = "building_heights_class"
    # Only heights
    elif "building" in wd_name.lower() and "class_id" not in layer.fields().names() and "building_height" in layer.fields().names():
        name = "building_heights"
    # No options
    elif "building" in wd_name.lower() and "class_id" not in layer.fields().names():
        name = "buildings_noclass"
    # Other cases (only classification) 
    elif "building" in wd_name.lower():
        name = 'buildings'

    # Show crowns as points
    elif name == "forest" and layer.geometryType() == QgsWkbTypes.PointGeometry:
        name = "forest_crowns_points"
    # Show forest heights for new (updated) forest with block config
    elif name == "forest" and "class_id" in layer.fields().names():
        name = "forest_with_heights"

    # Apply different styles for polygon and line layers
    elif "download" in wd_name.lower():
        if layer.geometryType() == QgsWkbTypes.PolygonGeometry:
            name = "open_data_polygon"
        else:
            name = "open_data_line"
    return name
