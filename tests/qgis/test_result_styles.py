"""Every style the plugin can ask for resolves to a file, and that file loads.

`loadNamedStyle` fails silently on a missing or malformed path: results appear unstyled and
nothing is logged. So the failure mode this guards is not a wrong-looking map, it is a
refactor that moves `static/styles/` — Phase D moves `styles.py` — with no test noticing.

Deliberately not asserting the mapping table. Which .qml belongs to which model is a design
decision that changes legitimately; restating it here would make the test a copy of the
implementation, red on every intended change and silent on the one that matters.

What the results *look like* stays a manual visual check.
"""
import os
from types import SimpleNamespace

import pytest
from qgis.core import QgsVectorLayer, QgsVectorTileLayer

from mapflow.styles import (generate_local_style_path, generate_tile_style_path,
                            get_style_name)

#: Styles loaded by hardcoded name rather than through get_style_name. They break the same
#: way and are just as invisible, so they are guarded in the same place.
FIXED_STYLES = ("aoi.qml", "metadata.qml", "metadata_footprint.qml",
                "aoi_template_blue.qml", "aoi_template_processing_green.qml")


def _vector(geometry="Polygon", fields=()):
    definition = f"{geometry}?crs=EPSG:4326" + "".join(f"&field={f}" for f in fields)
    layer = QgsVectorLayer(definition, "result", "memory")
    assert layer.isValid(), f"test layer {definition} is not valid"
    return layer


def _tiles():
    """A vector-tile layer with a file:// source.

    Only its type matters to the style choice, and a remote source would make QGIS reach for
    the network during construction — which stalls rather than fails when the host does not
    resolve.
    """
    return QgsVectorTileLayer("type=xyz&url=file:///tmp/{z}/{x}/{y}.pbf", "tiles")


def _wd(name):
    return SimpleNamespace(name=name)


#: One case per branch that changes the answer: model name, layer geometry, and the fields
#: that switch buildings and forest onto their variants.
STYLE_CASES = [
    ("🏠 Buildings", "Polygon", ("class_id:integer",)),
    ("🏠 Buildings", "Polygon", ()),
    ("🏠 Buildings", "Polygon", ("class_id:integer", "building_height:double")),
    ("🏠 Buildings", "Polygon", ("building_height:double",)),
    ("Buildings Detection With Heights", "Polygon", ()),
    ("🌲 Forest and trees", "Polygon", ()),
    ("🌲 Forest and trees", "Point", ()),
    ("🌲 Forest and trees", "Polygon", ("class_id:integer",)),
    ("🌲↕️ Forest with heights", "Polygon", ()),
    ("🚗 Roads", "LineString", ()),
    ("🏗️ Construction sites", "Polygon", ()),
    ("Download Open Data", "Polygon", ()),
    ("Download Open Data", "LineString", ()),
    ("[multi] Buildings + Roads + Forest", "Polygon", ()),
    ("Something The Plugin Has Never Heard Of", "Polygon", ()),
]


@pytest.mark.parametrize("model,geometry,fields", STYLE_CASES)
def test_a_style_file_exists_for_every_result_layer(model, geometry, fields):
    path = get_style_name(_wd(model), _vector(geometry, fields))
    assert os.path.exists(path), f"{model} on a {geometry} layer wants a missing style: {path}"


@pytest.mark.parametrize("model", [case[0] for case in STYLE_CASES])
def test_a_style_file_exists_for_every_tiled_result(model):
    """Tiled results take an entirely separate directory, so covering one proves nothing
    about the other."""
    path = get_style_name(_wd(model), _tiles())
    assert os.path.exists(path), f"{model} as tiles wants a missing style: {path}"


@pytest.mark.parametrize("api_style", ["combo", "buildings", "building_heights", "forest",
                                       "roads", "construction", "open_data", "unknown"])
def test_a_style_file_exists_for_every_name_the_backend_can_send(api_style):
    """The API may name a style directly, which takes a different branch from the model name.

    'unknown' is included on purpose: an unrecognised name must fall back to a style that
    exists rather than building a path from None.
    """
    local = get_style_name(_wd("🏠 Buildings"), _vector(), style_name=api_style)
    tiled = get_style_name(_wd("🏠 Buildings"), _tiles(), style_name=api_style)
    assert os.path.exists(local), f"backend style {api_style!r} has no local file: {local}"
    assert os.path.exists(tiled), f"backend style {api_style!r} has no tile file: {tiled}"


def test_the_chosen_style_actually_applies():
    """Existence is not enough — a malformed .qml resolves and then fails to load."""
    layer = _vector("Polygon", ("class_id:integer",))
    path = get_style_name(_wd("🏠 Buildings"), layer)

    _message, applied = layer.loadNamedStyle(path)
    assert applied, f"{path} exists but QGIS refused to apply it"


def test_models_are_not_all_collapsing_to_the_default():
    """A mapping that quietly returns the fallback for everything would pass every check
    above, and every result would render identically."""
    chosen = {get_style_name(_wd(model), _vector("Polygon", ("class_id:integer",)))
              for model in ("🏠 Buildings", "🌲 Forest and trees", "🚗 Roads",
                            "🏗️ Construction sites")}
    assert len(chosen) > 1, f"every model resolved to the same style: {chosen}"


@pytest.mark.parametrize("filename", FIXED_STYLES)
def test_the_styles_loaded_by_hardcoded_name_exist(filename):
    """AOI, search footprints and template AOIs are styled by literal filename rather than
    through get_style_name, so they are invisible to the checks above."""
    from mapflow import styles

    path = os.path.join(os.path.dirname(styles.__file__), "static", "styles", filename)
    assert os.path.exists(path), f"a style loaded by name is missing: {path}"


def test_both_style_families_are_reachable():
    """Guards the directory split itself: one family moving would otherwise look fine as long
    as the other still resolved."""
    assert os.path.exists(generate_local_style_path("default"))
    assert os.path.exists(generate_tile_style_path("default"))
