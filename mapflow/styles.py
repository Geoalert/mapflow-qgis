from pathlib import Path

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


def get_style_name(wd_name: str, layer: QgsVectorLayer):
    if isinstance(layer, QgsVectorTileLayer):
        return get_tile_style_name(wd_name)
    else:
        return get_local_style_name(wd_name, layer)


def get_tile_style_name(wd_name):
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
    res = str(Path(__file__).parent / 'static' / 'styles' / 'tiles' / (name + '.qml'))
    return res


def get_local_style_name(wd_name, layer):
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

    # Show forest heights for new (updated) forest with block config
    elif name == "forest" and "class_id" in layer.fields().names():
        name = "forest_with_heights"

    # Apply different styles for polygon and line layers
    elif "download" in wd_name.lower():
        if layer.geometryType() == QgsWkbTypes.PolygonGeometry:
            name = "open_data_polygon"
        else:
            name = "open_data_line"
    
    return str(Path(__file__).parent / 'static' / 'styles' / 'file' / (name + '.qml'))
