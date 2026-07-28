"""QGIS-tier tests: loading an empty processing result must not crash.

A processing can return an empty FeatureCollection ({"features": []}), which yields no vector
layers. set_raster_extent_error_handler then did ``vectors[0]`` -> IndexError. It must instead
report that there are no features and return cleanly.
"""
from unittest.mock import MagicMock

from mapflow.functional.layer_utils import ResultsLoader


def _loader():
    loader = ResultsLoader.__new__(ResultsLoader)
    loader.tr = lambda text: text
    loader.iface = MagicMock()
    loader.message_bar = MagicMock()
    loader.add_layer = MagicMock()
    return loader


def test_error_handler_with_no_vectors_reports_and_does_not_crash():
    loader = _loader()

    loader.set_raster_extent_error_handler(response=None, vectors=[])  # must not raise

    loader.iface.setActiveLayer.assert_not_called()
    loader.message_bar.pushInfo.assert_called_once()


def test_error_handler_with_none_vectors_does_not_crash():
    loader = _loader()

    loader.set_raster_extent_error_handler(response=None, vectors=None)  # default None path

    loader.iface.setActiveLayer.assert_not_called()
    loader.message_bar.pushInfo.assert_called_once()


def test_error_handler_with_vectors_adds_and_activates_first():
    loader = _loader()
    first, second = MagicMock(name="v0"), MagicMock(name="v1")

    loader.set_raster_extent_error_handler(response=None, vectors=[first, second])

    assert loader.add_layer.call_count == 2
    loader.iface.setActiveLayer.assert_called_once_with(first)
    loader.iface.zoomToActiveLayer.assert_called_once()
    loader.message_bar.pushInfo.assert_not_called()
