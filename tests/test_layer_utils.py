import pytest

from mapflow.layer_utils import *


def test_maxar_layer_our_proxy():
    result = generate_maxar_layer_definition(None,
                                             'name', 'pwd',
                                             12, connect_id='03360066-3616-4a76-aace-561d6a9b2c35',
                                             image_id='892b953c-1160-4fb0-96fa-5fcf92b10421',
                                             proxy='https://api.mapflow.ai/rest')
    assert result == 'type=xyz' \
                     '&url=https://api.mapflow.ai/rest/png?TileRow%3D{y}' \
                     '%26TileCol%3D{x}%26TileMatrix%3D{z}' \
                     '%26CONNECTID%3D03360066-3616-4a76-aace-561d6a9b2c35' \
                     '%26CQL_FILTER%3Dfeature_id%3D\'892b953c-1160-4fb0-96fa-5fcf92b10421\'' \
                     '&zmin=0' \
                     '&zmax=12' \
                     '&username=name' \
                     '&password=pwd'


def test_maxar_layer_our_proxy_no_imageid():
    result = generate_maxar_layer_definition(None,
                                             'name', 'pwd',
                                             12, connect_id='03360066-3616-4a76-aace-561d6a9b2c35',
                                             proxy='https://api.mapflow.ai/rest')
    assert result == 'type=xyz' \
                     '&url=https://api.mapflow.ai/rest/png?TileRow%3D{y}' \
                     '%26TileCol%3D{x}%26TileMatrix%3D{z}' \
                     '%26CONNECTID%3D03360066-3616-4a76-aace-561d6a9b2c35' \
                     '&zmin=0' \
                     '&zmax=12' \
                     '&username=name' \
                     '&password=pwd'

maxar_url = 'https://securewatch.digitalglobe.com/png?'


def test_maxar_layer_users_creds():
    result = generate_maxar_layer_definition(maxar_url,
                                             'name', 'pwd',
                                             12, connect_id='03360066-3616-4a76-aace-561d6a9b2c35')
    assert result == 'type=xyz' \
                     '&url=https://securewatch.digitalglobe.com/png?' \
                     '%26CONNECTID%3D03360066-3616-4a76-aace-561d6a9b2c35' \
                     '&zmin=0' \
                     '&zmax=12' \
                     '&username=name' \
                     '&password=pwd'


def test_xyz_no_creds():
    result = generate_xyz_layer_definition('https://xyz.tile.server/{z}/{x}/{y}.png',
                                           "", "", 18, "xyz")
    assert result == 'type=xyz' \
                     '&url=https://xyz.tile.server/{z}/{x}/{y}.png' \
                     '&zmin=0' \
                     '&zmax=18' \
                     '&username=' \
                     '&password='

