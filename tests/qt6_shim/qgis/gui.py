from PyQt6.QtWidgets import QDockWidget


class QgsDockWidget(QDockWidget):
    pass


class _Placeholder:
    def __init__(self, *args, **kwargs):
        pass


def __getattr__(name):
    return type(name, (_Placeholder,), {})
