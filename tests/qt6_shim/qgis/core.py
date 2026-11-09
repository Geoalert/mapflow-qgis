"""Stand-ins for the parts of qgis.core the plugin's pages and its HTTP client touch. Anything else
is a placeholder class, so modules import; the map side is tested in a real QGIS."""
import enum
import sys

from PyQt6.QtNetwork import QNetworkAccessManager


class Qgis:
    QGIS_VERSION_INT = 40200

    class MessageLevel(enum.IntEnum):
        Info = 0
        Warning = 1
        Critical = 2
        Success = 3
        NoLevel = 4

    class GeometryType(enum.IntEnum):
        Point = 0
        Line = 1
        Polygon = 2
        Unknown = 3
        Null = 4


class QgsNetworkAccessManager(QNetworkAccessManager):
    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


class QgsMessageLog:
    messages = []

    @staticmethod
    def logMessage(message, tag="", level=Qgis.MessageLevel.Info, notifyUser=True):
        QgsMessageLog.messages.append((tag, level, message))
        print(f"[log {tag} {getattr(level, 'name', level)}] {message}", file=sys.stderr)


class _Placeholder:
    def __init__(self, *args, **kwargs):
        pass


def __getattr__(name):
    return type(name, (_Placeholder,), {})
