"""QGIS-tier test: a downloaded-image save routes its reply through the guard (4-PR2, RISK 3).

`save_downloaded` streams the reply to disk, so it wires both `readyRead` and `finished`. Both are
Qt-owned signals, so an unexpected raise in either slot would reach the event loop unguarded
(spec/007 invariant 7). The connections go through `guarded_connect`, never a raw `.connect`.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.functional.service import data_catalog as data_catalog_module
from mapflow.functional.service.data_catalog import DataCatalogService


def test_save_downloaded_routes_the_reply_through_the_guard(monkeypatch, tmp_path):
    service = DataCatalogService.__new__(DataCatalogService)
    service.app_context = SimpleNamespace(plugin_version="1.2.3")
    service._downloads = {}
    reply = MagicMock()
    nam = MagicMock()
    nam.get.return_value = reply
    service.api = SimpleNamespace(http=SimpleNamespace(nam=nam))

    connected = []
    monkeypatch.setattr(data_catalog_module, "guarded_connect",
                        lambda signal, slot, *a, **k: connected.append((signal, slot)))

    service.save_downloaded("https://example.com/img.tif", str(tmp_path / "out.tif"))

    signals = [signal for signal, _slot in connected]
    assert reply.readyRead in signals, "the chunks arriving must reach a guarded slot"
    assert reply.finished in signals, "so must the reply finishing"
    reply.readyRead.connect.assert_not_called()  # the raw connect path is gone
    reply.finished.connect.assert_not_called()
