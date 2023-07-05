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


def get_style_name(wd_name: str, layer: QgsVectorLayer):
    name = STYLES.get(wd_name, "default")
    if name == "buildings" and "class_id" not in layer.fields().names():
        name = "default"
    return str(Path(__file__).parent/'static'/'styles'/(name + '.qml'))
