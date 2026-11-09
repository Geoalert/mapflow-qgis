"""Pure-Python tests: API parsing, the run draft (payload, estimate, issues) and scenario matching."""
import pytest
from pathlib import Path

from mapflow_next.core.draft import AreaOfInterest, ImageryChoice, RunDraft
from mapflow_next.core.messages import describe
from mapflow_next.core.models import (BillingType, DataProvider, Model, Processing, Project, Role, Status,
                                      UserStatus)
from mapflow_next.core.scenarios import Catalogue, match_model, resolve, scenario_for_model
from mapflow_next.config import RESOURCES, Config, load_config
from mapflow_next.core import oauth

from .fixtures import BUILDINGS, FOREST, MULTI, ROADS, OPEN_DATA, MAPBOX, PROJECT, STATUS, processing_json


def test_model_prices_and_options():
    model = Model.from_api(BUILDINGS)
    assert model.base_price == 10
    assert [b.name for b in model.options] == ["classification", "heights", "simplification"]
    assert model.price({"heights"}) == 20
    assert model.blocks_payload({"classification"}) == [
        {"name": "classification", "enabled": True}, {"name": "heights", "enabled": False},
        {"name": "simplification", "enabled": False}]
    assert model.short_name == "Buildings"


def test_status_and_providers():
    status = UserStatus.from_api(STATUS)
    assert status.billing is BillingType.credits
    assert status.remaining_credits == 1240
    mapbox = status.data_providers[0]
    assert mapbox.zooms == [17, 18, 19]
    assert mapbox.nearest_zoom(20) == 19 and mapbox.nearest_zoom(None) == 19
    assert mapbox.price_at(18) == 3


def test_project_roles():
    own = Project.from_api(PROJECT, "me@example.com")
    assert own.role is Role.owner and own.aoi_area_limit_km2 == 100
    shared = dict(PROJECT, shareProject={"owners": [{"email": "boss@example.com"}],
                                         "users": [{"email": "ME@example.com", "role": "contributor"}]})
    assert Project.from_api(shared, "me@example.com ").role is Role.contributor
    assert Project.from_api(shared, "stranger@example.com").role is Role.readonly
    assert not Project.from_api(shared, "").role.can_run


def test_processing_parsing():
    processing = Processing.from_api(processing_json("p1", "OK", 100))
    assert processing.status is Status.ok and processing.is_done and processing.is_final
    assert processing.source.kind == "provider" and processing.source.zoom == 18
    assert processing.area_km2 == pytest.approx(2.4)
    assert processing.enabled_blocks == ["classification"]
    running = Processing.from_api(processing_json("p2", "IN_PROGRESS", 40))
    assert running.is_running and not running.is_final


def _draft(area=2.4, zoom=19):
    model = Model.from_api(BUILDINGS)
    provider = DataProvider.from_api(MAPBOX)
    aoi = AreaOfInterest("Old town", {"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 1], [0, 0]]]},
                         area_km2=area, max_bbox_km2=area * 1.3, polygons=1, layer_id="L1")
    return RunDraft(model=model, options={"heights"}, aoi=aoi, imagery=ImageryChoice.from_provider(provider, zoom))


def test_payload_matches_the_v2_contract():
    payload = _draft().payload("project-1")
    assert payload["projectId"] == "project-1" and payload["wdId"] == "wd-buildings"
    assert payload["name"] == "Buildings · Old town"
    assert payload["params"] == {"sourceParams": {"dataProvider": {"providerName": "mapbox", "zoom": "19"}}}
    assert {"name": "heights", "enabled": True} in payload["blocks"]
    assert payload["geometry"]["type"] == "Polygon"


def test_other_imagery_payloads():
    mosaic = ImageryChoice.from_mosaic("m-1", "Drone")
    assert mosaic.source_params() == {"myImagery": {"mosaicId": "m-1"}}
    assert mosaic.price_per_km2 == 0
    image = ImageryChoice.from_catalog("img-9", "Maxar", 18, "Maxar scene")
    assert image.source_params() == {"imagerySearch": {"dataProvider": "maxar", "imageIds": ["img-9"], "zoom": 18}}
    assert image.price_per_km2 is None


def test_estimate_rounds_like_mapflow():
    estimate = _draft(area=2.4, zoom=19).estimate()
    assert estimate.per_km2 == 10 + 10 + 9
    assert estimate.credits == 70                       # ceil(2.4 * 29 = 69.6)
    small = _draft(area=0.2, zoom=18).estimate()
    assert small.billed_km2 == 1 and small.credits == 23   # areas under 1 km² are billed as 1 km²


def test_issues_point_at_the_right_step():
    project = Project.from_api(PROJECT, "me@example.com")
    status = UserStatus.from_api(STATUS)
    assert _draft().issues(project, status) == []
    empty = RunDraft()
    assert {i.field for i in empty.issues(project, status)} == {"model", "area", "imagery"}
    too_big = _draft(area=150)
    assert too_big.issues(project, status)[0].field == "area"
    poor = UserStatus.from_api(dict(STATUS, remainingCredits=10))
    assert _draft().issues(project, poor)[0].field == "account"
    # the server's figure wins over the local estimate
    assert _draft().issues(project, status, server_cost=2000)[0].field == "account"


def test_error_messages():
    assert "km²" in describe("TOO_LARGE_PROCESSING", {"area": 5e6, "aoiAreaLimit": 3e6})
    assert describe("dataloader.NoDataTile").startswith("The data provider contains no data")
    assert describe("SOMETHING_NEW", {"x": 1}, "Bad thing") == "Bad thing (x: 1)"


@pytest.fixture(scope="module")
def catalogue():
    return Catalogue.load(RESOURCES / "scenarios")


def test_catalogue(catalogue):
    assert len(catalogue.scenarios) == 16
    assert all(catalogue.image_path(s).exists() for s in catalogue.scenarios if s.image)
    assert [s.id for s in catalogue.popular(4)] == ["buildings", "forest", "veg-height", "crowns"]
    assert [s.id for s in catalogue.search("solar")] == ["solar"]


def test_scenarios_find_their_models(catalogue):
    models = [Model.from_api(m) for m in (BUILDINGS, FOREST, ROADS, MULTI, OPEN_DATA)]
    expected = {"buildings": "🏠 Buildings", "classes": "🏠 Buildings", "roads": "🚗 Roads",
                "multi": "[multi] Buildings + Roads + Forest", "veg-height": "🌲 Forest and trees",
                "opendata": "Download Open Data"}
    for scenario_id, name in expected.items():
        assert resolve(catalogue.get(scenario_id), models).model.name == name, scenario_id
    heights = resolve(catalogue.get("heights"), models)
    assert heights.options == ["heights"] and heights.zoom == 19
    classes = resolve(catalogue.get("classes"), models)
    assert classes.options == ["classification"] and not classes.missing_options
    crowns = resolve(catalogue.get("crowns"), [Model.from_api(BUILDINGS)])
    assert crowns.model is None


def test_scenario_for_model(catalogue):
    forest = Model.from_api(FOREST)
    assert scenario_for_model(catalogue, forest, ["heights"]).id == "veg-height"
    assert scenario_for_model(catalogue, forest, []).id == "forest"
    assert match_model([forest], {"all": ["road"]}) is None


def test_sign_in_addresses():
    production = Config("production", "https://whitemaps-production.mapflow.ai/rest")
    assert production.authorize_url == "https://auth.mapflow.ai/auth/realms/mapflow/protocol/openid-connect/auth"
    assert production.redirect_uri == "http://127.0.0.1:7070/qgis"
    assert Config("duty", "x").token_url.startswith("https://auth-duty.mapflow.ai/auth/realms/mapflow-duty/")
    settings = {"variables/mapflow_env": "staging", "mapflow_next/auth_url": "http://localhost:9/oidc/"}
    staging = load_config(type("S", (), {"value": lambda self, k, d=None: settings.get(k, d)})())
    assert staging.server == "https://whitemaps-staging.mapflow.ai/rest"
    assert staging.token_url == "http://localhost:9/oidc/token"


def test_pkce_and_authorize_url():
    import base64
    import hashlib
    from urllib.parse import parse_qs, urlsplit
    verifier, challenge = oauth.pkce_pair()
    assert 43 <= len(verifier) <= 128
    assert challenge == base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    url = oauth.authorize_url("https://auth/x/auth", "qgis", "http://127.0.0.1:7070/qgis", "st", challenge)
    query = parse_qs(urlsplit(url).query)
    assert query["redirect_uri"] == ["http://127.0.0.1:7070/qgis"] and query["code_challenge_method"] == ["S256"]
    assert "scope" not in query


def test_reading_the_redirect():
    def head(target):
        return f"GET {target} HTTP/1.1\r\nHost: 127.0.0.1:7070\r\n\r\n".encode()
    assert oauth.read_redirect(head("/qgis?state=s1&code=abc"), "/qgis", "s1") == oauth.Redirect("code", "abc")
    assert oauth.read_redirect(head("/qgis?state=s2&code=abc"), "/qgis", "s1").kind == "stale"
    assert oauth.read_redirect(head("/qgis?code=abc"), "/qgis", "s1").kind == "stale"
    assert oauth.read_redirect(head("/qgis?state=\u00e9&code=abc"), "/qgis", "s1").kind == "stale"
    denied = oauth.read_redirect(head("/qgis?state=s1&error=access_denied"), "/qgis", "s1")
    assert denied == oauth.Redirect("error", "access_denied")
    assert oauth.read_redirect(head("/favicon.ico"), "/qgis", "s1").kind == "other"
    assert oauth.read_redirect(b"POST /qgis?state=s1&code=a HTTP/1.1\r\n\r\n", "/qgis", "s1").kind == "other"
    answer = oauth.http_response("302 Found", location="https://app.mapflow.ai")
    assert answer.startswith(b"HTTP/1.1 302 Found\r\n") and b"\r\nLocation: https://app.mapflow.ai\r\n" in answer


def test_tokens():
    tokens = oauth.Tokens.from_response({"access_token": "a", "refresh_token": "r", "expires_in": 300}, now=0)
    assert tokens.refresh_delay() == 240
    renewed = oauth.Tokens.from_response({"access_token": "b", "expires_in": 30}, previous_refresh="r", now=0)
    assert renewed.refresh == "r" and renewed.refresh_delay() == 24
    with pytest.raises(ValueError):
        oauth.Tokens.from_response({"error": "invalid_grant"})


def test_zoom_choices_and_recommendation():
    from mapflow_next.core.models import DataProvider
    from mapflow_next.core.scenarios import Catalogue, recommended_zoom
    wide = DataProvider.from_api({"name": "wide", "price": [{"zoom": z, "priceSqKm": z} for z in range(12, 23)]})
    assert wide.zooms == [17, 18, 19, 20, 21]
    assert wide.nearest_zoom(14) == 17 and wide.nearest_zoom(22) == 21
    low = DataProvider.from_api({"name": "low", "price": [{"zoom": 15, "priceSqKm": 1}, {"zoom": 16, "priceSqKm": 2}]})
    assert low.zooms == [16]
    assert DataProvider.from_api({"name": "free"}).zooms == [17, 18, 19, 20, 21]
    catalogue = Catalogue.load(RESOURCES / "scenarios")
    assert recommended_zoom(catalogue.get("heights")) == 19
    assert recommended_zoom(catalogue.get("forest")) == 18
    assert recommended_zoom(None) == 18


def test_project_sharing_and_numbers():
    from mapflow_next.core.models import Project, Role
    shared = Project.from_api({"id": "p", "name": "Harbor", "description": "  Port  ",
                               "processingCounts": {"succeeded": 12, "failed": 1},
                               "updated": "2026-11-05T09:00:00Z",
                               "shareProject": {"owners": [{"email": "me@example.com"}],
                                                "users": [{"email": "ana@example.com", "role": "contributor"}]}},
                              "me@example.com")
    assert shared.shared and shared.members == 1 and shared.role is Role.owner
    assert shared.description == "Port" and shared.succeeded == 12 and shared.failed == 1 and shared.updated
    theirs = Project.from_api({"id": "q", "name": "Theirs", "shareProject": {"owners": [{"email": "boss@example.com"}],
                                                                             "users": []}}, "me@example.com")
    assert theirs.shared and theirs.role is Role.readonly
    mine = Project.from_api({"id": "r", "name": "Mine"}, "me@example.com")
    assert not mine.shared


def test_collections_and_images():
    from mapflow_next.core.models import Mosaic, MosaicImage
    assert Mosaic.from_api({"id": "m", "name": "A"}).image_count is None
    assert Mosaic.from_api({"id": "m", "name": "A", "status_summary": {"total": 3}}).image_count == 3
    image = MosaicImage.from_api({"id": "i", "mosaic_id": "m", "filename": "a.tif", "preview_url_s": "u",
                                  "file_size": 10, "meta_data": {"pixel_size": [0.15, 0.15]}})
    assert image.filename == "a.tif" and image.pixel_size == 0.15 and image.preview_s == "u"
    from mapflow_next.core.draft import ImageryChoice
    one = ImageryChoice.from_mosaic("m", "A", "i", "a.tif")
    # one image goes as imageIds alone: the API rejects mosaicId and imageIds together
    assert one.source_params() == {"myImagery": {"imageIds": ["i"]}} and one.label == "A · a.tif"
    assert ImageryChoice.from_mosaic("m", "A").source_params() == {"myImagery": {"mosaicId": "m"}}


def _swallows_checked(handler, methods) -> bool:
    """Would `checked` (passed by some PyQt builds) land in a parameter that has a default value?"""
    import ast
    if isinstance(handler, ast.Lambda):
        params = handler.args.args
        return (bool(params) and not handler.args.vararg and params[0].arg != "_"
                and len(handler.args.defaults) == len(params))
    if isinstance(handler, ast.Attribute) and isinstance(handler.value, ast.Name) and handler.value.id == "self":
        method = methods.get(handler.attr)
        if method is None:
            return False
        params = method.args.args[1:]
        if params and params[0].arg == "checked":
            return False                    # meant to receive it (a checkable action)
        return bool(params) and not method.args.vararg and len(method.args.defaults) == len(params)
    return False


def test_no_handlers_that_swallow_qt_arguments():
    """Qt's clicked/triggered carry `checked`, and some PyQt builds hand it to the handler. A handler whose
    first parameter has a default then gets False instead of its value, and a signal's emit() given to a
    menu rejects the extra argument: the button or the menu item does nothing (it happened to “Other
    ways to sign in” and to the account menu). Handlers take `*_`, or `_=False` first."""
    import ast
    root = Path(__file__).resolve().parents[1] / "mapflow_next"
    problems = []
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        methods = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            where = f"{path.relative_to(root)}:{node.lineno}"
            func = node.func
            if func.attr == "connect" and isinstance(func.value, ast.Attribute) \
                    and func.value.attr in ("clicked", "triggered", "toggled") and node.args:
                handler = node.args[0]
                if _swallows_checked(handler, methods):
                    problems.append(f"{where}: handler takes `checked` into a defaulted parameter")
                if func.value.attr == "triggered" and isinstance(handler, ast.Attribute) and handler.attr == "emit":
                    problems.append(f"{where}: a menu action connected straight to a signal's emit")
            if func.attr == "addAction" and len(node.args) >= 2:
                handler = node.args[-1]
                if isinstance(handler, ast.Attribute) and handler.attr == "emit":
                    problems.append(f"{where}: a menu action connected straight to a signal's emit")
                elif _swallows_checked(handler, methods):
                    problems.append(f"{where}: menu handler takes `checked` into a defaulted parameter")
    assert not problems, "\n".join(problems)


def test_code_runs_on_qt5_and_qt6():
    """QGIS 3 runs Qt 5 and QGIS 4 runs Qt 6. Code both accept: qgis.PyQt imports only, exec() not exec_(),
    scoped enums for QGIS too, geometry types from qgis_bridge/compat.py, menu items built as QActions.
    (tools/qt6_check.py checks every Qt enum name; it needs PyQt6.)"""
    import re
    root = Path(__file__).resolve().parents[1] / "mapflow_next"
    rules = [
        (re.compile(r"^\s*(from|import) PyQt[56]\b"), "import from qgis.PyQt, not PyQt5/PyQt6 directly"),
        (re.compile(r"\.exec_\("), "exec_() is gone in PyQt6: use exec()"),
        (re.compile(r"\bQgis\.(Info|Warning|Critical|Success)\b"), "use Qgis.MessageLevel.<level>"),
        (re.compile(r"\bQgsWkbTypes\.\w+Geometry\b"), "use the geometry types in qgis_bridge/compat.py"),
        (re.compile(r"\bmenu\.addAction\(\s*icons\."), "build menu items with widgets.menu_action"),
        (re.compile(r"\bQRegExp\b|\bQDesktopWidget\b|\.desktop\(\)"), "removed in Qt 6"),
    ]
    allowed = {"qgis_bridge/compat.py": {"use the geometry types in qgis_bridge/compat.py"},
               "ui/icons.py": {"import from qgis.PyQt, not PyQt5/PyQt6 directly"}}   # QSvgWidget fallback
    problems = []
    for path in sorted(root.rglob("*.py")):
        name = str(path.relative_to(root))
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for pattern, why in rules:
                if pattern.search(line) and why not in allowed.get(name, set()):
                    problems.append(f"{name}:{number}: {why}")
    assert not problems, "\n".join(problems)
    metadata = (root / "metadata.txt").read_text(encoding="utf-8")
    assert "qgisMaximumVersion=4.99" in metadata and "qgisMinimumVersion=3.22" in metadata


def test_update_check_reads_the_plugin_installer_record():
    from mapflow_next.core.updates import LATEST, NOT_LISTED, UPDATE, assess, version_key
    assert version_key("4.0.10") > version_key("4.0.9") > version_key("4.0")
    assert version_key("4.1.0") > version_key("4.1.0-beta") and version_key("4.0") == version_key("4.0.0")
    # QGIS 3.34+: stable and experimental versions listed apart; experimental counts only when allowed
    record = {"version_available_stable": "4.0.0", "version_available_experimental": "4.1.0-beta"}
    assert assess("4.0.0", record, True, True).state == UPDATE
    assert assess("4.0.0", record, True, True).available == "4.1.0-beta"
    assert assess("4.0.0", record, False, True).state == LATEST
    assert assess("4.1.0", record, True, True).state == LATEST          # newer than the repository
    # QGIS before 3.34: one version and an experimental flag
    old = {"version_available": "4.2.0", "experimental": True}
    assert assess("4.0.0", old, True, True).available == "4.2.0"
    hidden = assess("4.0.0", old, False, True)
    assert hidden.state == NOT_LISTED and hidden.experimental_hidden
    zip_install = assess("4.0.0", None, True, True)
    assert zip_install.state == NOT_LISTED and not zip_install.experimental_hidden


def test_processing_meta_like_the_current_plugin():
    from mapflow_next.core.draft import ImageryChoice, processing_meta
    assert processing_meta(ImageryChoice.from_mosaic("m", "A"), "4.0.0") == {
        "source-app": "qgis", "source": "my imagery", "version": "4.0.0"}
    payload = _draft().payload("project-1", "4.0.0")
    assert all(isinstance(v, str) for v in payload["meta"].values()) and payload["meta"]["source-app"] == "qgis"


def test_my_imagery_coverage():
    """With My imagery, only the part of the area inside the imagery is processed and billed, and an
    area outside it blocks the run."""
    from mapflow_next.core.draft import AreaOfInterest, Coverage
    draft = _draft()
    whole = draft.aoi
    inside = AreaOfInterest(name=whole.name,
                            geometry={"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
                            area_km2=whole.area_km2 / 4, max_bbox_km2=whole.area_km2 / 4, polygons=1)
    draft.coverage = Coverage("centre.tif", True, inside)
    assert draft.processed_area is inside
    assert draft.payload("project-1")["geometry"] == inside.geometry
    assert draft.estimate().billed_km2 == max(inside.area_km2, 1.0)
    draft.coverage = Coverage("centre.tif", False, None)
    assert draft.processed_area is whole
    assert any(i.field == "area" and "doesn't overlap “centre.tif”" in i.text for i in draft.issues(None, None))
    draft.coverage = None
    assert not any("overlap" in i.text for i in draft.issues(None, None))
