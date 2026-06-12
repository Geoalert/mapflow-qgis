from mapflow.functional.layer_utils import *


def test_xyz_no_creds():
    result = generate_xyz_layer_definition(url='https://xyz.tile.server/{z}/{x}/{y}.png',
                                           username="", password="", max_zoom=18, source_type="xyz")
    assert result == 'type=xyz' \
                     '&url=https://xyz.tile.server/{z}/{x}/{y}.png' \
                     '&zmin=0' \
                     '&zmax=18' \
                     '&username=' \
                     '&password='

