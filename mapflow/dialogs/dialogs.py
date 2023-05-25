from pathlib import Path

from PyQt5 import uic
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QWidget
from qgis.core import QgsMapLayerProxyModel

from ..entity.billing import BillingType

ui_path = Path(__file__).parent/'static'/'ui'
icon_path = Path(__file__).parent/'static'/'icons'
plugin_icon = QIcon(str(icon_path/'mapflow.png'))


class MainDialog(*uic.loadUiType(ui_path/'main_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        """Plugin's main dialog."""
        super().__init__(parent)
        self.setupUi(self)
        # Restrict combos to relevant layer types; QGIS 3.10-3.20 (at least) bugs up if set in .ui
        self.polygonCombo.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.rasterCombo.setFilters(QgsMapLayerProxyModel.RasterLayer)
        # Set icons (can be done in .ui but brings about the resources_rc import bug)
        self.setWindowIcon(plugin_icon)
        self.addProvider.setIcon(QIcon(str(icon_path/'add.svg')))
        self.removeProvider.setIcon(QIcon(str(icon_path/'remove_provider.svg')))
        self.editProvider.setIcon(QIcon(str(icon_path/'edit_provider.svg')))
        self.toolButton.setIcon(QIcon(str(icon_path/'add.svg')))
        self.modelInfo.setIcon(QIcon(str(icon_path/'info.svg')))
        self.billingHistoryButton.setIcon(QIcon(str(icon_path/'bar-chart-2.svg')))
        self.logoutButton.setIcon(QIcon(str(icon_path/'log-out.svg')))
        self.tabWidget.setTabIcon(1, QIcon(str(icon_path/'magnifying-glass-solid.svg')))
        self.tabWidget.setTabIcon(2, QIcon(str(icon_path/'user-gear-solid.svg')))
        self.tabWidget.setTabIcon(3, QIcon(str(icon_path/'info.svg')))

        pixmap = QIcon(str(icon_path/'coins-solid.svg')).pixmap(16,16)
        self.labelCoins_1.setPixmap(pixmap)
        self.labelCoins_2.setPixmap(pixmap)

    def setup_for_billing(self, billing_type: BillingType):
        if billing_type == billing_type.credits:
            self.balanceLabel.setVisible(True)
            self.labelCoins_1.setVisible(True)
            self.labelCoins_2.setToolTip(self.tr("This is a paid data provider"))
            self.labelWdPrice.setVisible(True)
        elif billing_type == billing_type.area:
            self.balanceLabel.setVisible(True)
            self.labelCoins_1.setVisible(False)
            self.labelWdPrice.setVisible(False)
            self.labelCoins_2.setToolTip(self.tr("This is a premium data provider"))
        else: # None billing
            self.balanceLabel.setVisible(False)
            self.topUpBalanceButton.setVisible(False)
            self.labelCoins_1.setVisible(False)
            self.labelCoins_2.setVisible(False)
            self.labelWdPrice.setVisible(False)



class LoginDialog(*uic.loadUiType(ui_path/'login_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        """Auth dialog."""
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(plugin_icon)

class ErrorMessageWidget(*uic.loadUiType(ui_path / 'error_message.ui')):
    def __init__(self, parent: QWidget, text: str, title: str = None, email_body: str = '') -> None:
        """A message box notifying user about a plugin error, with a 'Send a report' button."""
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(plugin_icon)
        self.text.setText(text)
        if title:
            self.title.setText(title)
        self.mailTo.setText(
            '<html><head/><body><p><a href="mailto:help@geoalert.io?subject=Mapflow-QGIS&body=' +
            email_body +
            '"><span style=" text-decoration: underline; color:#0057ae;">Let us know</span></a></p></body></html>'
        )
