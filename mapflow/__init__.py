from qgis.gui import QgisInterface

from .mapflow import Mapflow

"""
This plugin is developed and maintained by Geoalert LLC (https://www.geoalert.io) and provides a QGIS interface
for Mapflow, - an AI-based platform for detecting real-world object in satellite/aerial imagery (https://mapflow.ai/).

Python modules:
    dialogs: defines the plugin's interfaces, - a main tabbed dialog and a smaller login dialog
    mapflow: the 'main' module; it contains the Mapflow class that implements the plugin logic
    workers: contains classes that represent the logic exectuted concurrently in a separate thread to avoid UI blocking
    helpers: contains functions that are used in both geoalert and workers and needn't be methods of the Mapflow class
"""


def classFactory(iface: QgisInterface) -> Mapflow:
    """Initialize the plugin."""
    return Mapflow(iface)
