from pathlib import Path
from qgis.core import QgsVectorLayer

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
    name = STYLES.get(wd_name, DEFAULT_STYLE)
    if name == "buildings" and "class_id" not in layer.fields().names():
        name = DEFAULT_STYLE
        # Buildings classes look bad in legend if there are no classes in layer, so we discard the style in this case
    return str(Path(__file__).parent/'static'/'styles'/(name + '.qml'))
