from PyQt5.QtCore import QObject


class ErrorMessageList(QObject):
    def tr(self, message: str) -> str:
        """Translate string for i18n support."""
        from PyQt5.QtCore import QCoreApplication
        return QCoreApplication.translate('ErrorMessageList', message)
    def __init__(self):
        super().__init__()
        self.error_descriptions = {}

    def update(self, other):
        # sanity check
        assert set(self.error_descriptions.keys()).intersection(set(other.error_descriptions.keys())) == set()
        self.error_descriptions.update(other.error_descriptions)

    def get(self, key, default=None):
        if not default:
            default = self.tr("Unknown error. Contact us to resolve the issue! help@geoalert.io")
        return self.error_descriptions.get(key, default)
