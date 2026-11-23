"""QGIS-tier tests: the users of the `mapflow_ru` variable (spec/002_api.md, section "The `mapflow.ru` domain").

`Config` reads the variable once, at import. These tests set `Config.DOMAIN` as the variable would, and
check the two places where a text or an address reaches the user: the labels of a dialog and a tile layer.
"""
from PyQt5.QtWidgets import QLabel, QWidget

from mapflow.config import Config
from mapflow.dialogs.domain_labels import labels_on_domain
from mapflow.domain import DEFAULT_DOMAIN, RU_DOMAIN
from mapflow.functional.layer_utils import generate_raster_layer

LINK = '<a href="https://docs.mapflow.ai/api/qgis_mapflow.html">mapflow.ai</a>'
TILES = 'https://tiles.mapflow.ai/{z}/{x}/{y}.png'


def test_the_labels_of_a_dialog_show_the_domain_in_use(monkeypatch):
    monkeypatch.setattr(Config, 'DOMAIN', RU_DOMAIN)
    dialog = QWidget()
    link, plain = QLabel(LINK, dialog), QLabel('Area', dialog)

    labels_on_domain(dialog)

    assert link.text() == '<a href="https://docs.mapflow.ru/api/qgis_mapflow.html">mapflow.ru</a>'
    assert plain.text() == 'Area'


def test_the_labels_stay_on_the_default_domain():
    assert Config.DOMAIN == DEFAULT_DOMAIN
    dialog = QWidget()
    link = QLabel(LINK, dialog)

    labels_on_domain(dialog)

    assert link.text() == LINK


def test_a_tile_layer_of_a_server_address_uses_the_domain_in_use(monkeypatch):
    monkeypatch.setattr(Config, 'DOMAIN', RU_DOMAIN)

    layer = generate_raster_layer(TILES, 'result')

    assert 'tiles.mapflow.ru' in layer.source()
    assert 'mapflow.ai' not in layer.source()


def test_a_tile_layer_stays_on_the_default_domain():
    layer = generate_raster_layer(TILES, 'result')

    assert 'tiles.mapflow.ai' in layer.source()
