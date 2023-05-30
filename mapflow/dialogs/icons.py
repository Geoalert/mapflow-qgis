from pathlib import Path
from PyQt5.QtGui import QIcon

ui_path = Path(__file__).parent/'static'/'ui'
icon_path = Path(__file__).parent/'static'/'icons'
plugin_icon = QIcon(str(icon_path/'mapflow.png'))
coins_icon = QIcon(str(icon_path/'coins-solid.svg'))
