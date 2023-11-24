from pathlib import Path
from qgis.core import QgsVectorLayer, QgsVectorTileLayer

STYLES = {
    '🏠 Buildings': 'buildings',
    'Buildings Detection With Heights': 'buildings',
    '🌲 Forest': 'forest',
    '🌲↕️ Forest with heights': 'forest_with_heights',
    '🚗 Roads': 'roads',
    '🏗️ Construction sites': 'construction'
}

DEFAULT_STYLE = "default"


def get_style_name(wd_name: str, layer: QgsVectorLayer):
    if isinstance(layer, QgsVectorTileLayer):
        return str(Path(__file__).parent/'static'/'styles'/'tiles.qml')
    else:
        return get_local_style_name(wd_name, layer)


def get_tile_style_name(wd_name):
    return str(Path(__file__).parent / 'static' / 'styles' / 'tiles.qml')


def get_local_style_name(wd_name, layer):
    name = STYLES.get(wd_name, DEFAULT_STYLE)
    # Buildings classes look bad in legend if there are no classes in layer, so we discard the style in this case
    if name == "buildings" and "class_id" not in layer.fields().names():
        name = DEFAULT_STYLE
    # Show forest heights for new (updated) forest with block config
    elif name == "forest" and "class_id" in layer.fields().names():
        name = "forest_with_heights"
    return str(Path(__file__).parent/'static'/'styles'/(name + '.qml'))
