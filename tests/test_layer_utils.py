from mapflow.functional.layer_utils import *


def test_xyz_no_creds():
    result = generate_xyz_layer_definition('https://xyz.tile.server/{z}/{x}/{y}.png',
                                           "", "", 18, "xyz")
    assert result == 'type=xyz' \
                     '&url=https://xyz.tile.server/{z}/{x}/{y}.png' \
                     '&zmin=0' \
                     '&zmax=18' \
                     '&username=' \
                     '&password='

