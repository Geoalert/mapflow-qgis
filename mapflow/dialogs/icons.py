from pathlib import Path

from PyQt5.QtGui import QIcon

icon_path = Path(__file__).parent/'static'/'icons'
plugin_icon = QIcon(str(icon_path/'mapflow.png'))
coins_icon = QIcon(str(icon_path/'coins-solid.svg'))
plus_icon = QIcon(str(icon_path/'add.svg'))
info_icon = QIcon(str(icon_path/'info.svg'))
logout_icon = QIcon(str(icon_path/'log-out.svg'))
minus_icon = QIcon(str(icon_path/'remove_provider.svg'))
edit_icon = QIcon(str(icon_path/'edit_provider.svg'))
chart_icon = QIcon(str(icon_path/'bar-chart-2.svg'))
lens_icon = QIcon(str(icon_path/'magnifying-glass-solid.svg'))
user_gear_icon = QIcon(str(icon_path/'user-gear-solid.svg'))
processing_icon = QIcon(str(icon_path/'processing.svg'))
options_icon = QIcon(str(icon_path/'ellipsis-solid.svg'))
arrow_right_icon = QIcon(str(icon_path/'arrow_right.svg'))