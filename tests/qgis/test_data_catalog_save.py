"""QGIS-tier test: a downloaded-image save routes its reply through the guard (4-PR2, RISK 3).

`save_downloaded` wires `reply.finished` to write the fetched bytes to disk. `finished` is a
Qt-owned signal, so an unexpected raise in the slot would reach the event loop unguarded
(spec/007 invariant 7). The connection goes through `guarded_connect`, never a raw `.connect`.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.functional.service import data_catalog as data_catalog_module
from mapflow.functional.service.data_catalog import DataCatalogService


def test_save_downloaded_routes_the_reply_through_the_guard(monkeypatch):
    service = DataCatalogService.__new__(DataCatalogService)
    service.app_context = SimpleNamespace(plugin_version="1.2.3")
    reply = MagicMock()
    nam = MagicMock()
    nam.get.return_value = reply
    service.api = SimpleNamespace(http=SimpleNamespace(nam=nam))

    connected = []
    monkeypatch.setattr(data_catalog_module, "guarded_connect",
                        lambda signal, slot, *a, **k: connected.append((signal, slot)))

    service.save_downloaded("https://example.com/img.tif", "/tmp/out.tif")

    assert connected, "save_downloaded must connect the reply's finished signal"
    signal, _slot = connected[0]
    assert signal is reply.finished             # guarded, not a raw reply.finished.connect
    reply.finished.connect.assert_not_called()  # the raw connect path is gone
