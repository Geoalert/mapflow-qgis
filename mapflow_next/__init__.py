"""Mapflow Next: a redesigned QGIS plugin for Mapflow AI mapping (model → area → imagery → processing → results)."""


def classFactory(iface):
    from .plugin import MapflowNextPlugin
    return MapflowNextPlugin(iface)
