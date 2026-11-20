"""Pure-Python tests: API parsing, the run draft (payload, estimate, issues) and scenario matching."""
import re

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


def test_storage_limits_from_the_memory_answer():
    """spec/002_C § Storage Endpoints: the two limits replace the built-in ones; free space counts only when
    Mapflow limits the account's storage."""
    from mapflow_next.core.models import StorageLimits
    full = StorageLimits.from_api({"memoryLimit": 10_000, "memoryUsed": 400, "memoryFree": 9_600,
                                   "maxUploadFileSize": 5_000, "maxPixelCount": 100_000})
    assert (full.max_upload_bytes, full.max_side_pixels, full.free_bytes) == (5_000, 100_000, 9_600)
    # null (spec/002_E: limiting off), missing, zero, text and a bool are "no value"
    for answer in ({}, None, [], "x", {"maxUploadFileSize": None, "maxPixelCount": None},
                   {"maxUploadFileSize": 0, "maxPixelCount": 0}, {"maxUploadFileSize": "big", "maxPixelCount": True}):
        empty = StorageLimits.from_api(answer)
        assert (empty.max_upload_bytes, empty.max_side_pixels, empty.free_bytes) == (None, None, None), answer
    assert StorageLimits.from_api({"maxUploadFileSize": "5000"}).max_upload_bytes is None     # a text is no number
    assert StorageLimits.from_api({"maxPixelCount": 7.0}).max_side_pixels == 7
    # free space is unknown when the storage is not limited, even if a number comes with it
    for limit in (None, 0):
        assert StorageLimits.from_api({"memoryLimit": limit, "memoryFree": 500}).free_bytes is None
    assert StorageLimits.from_api({"memoryLimit": 100, "memoryFree": None}).free_bytes is None
    assert StorageLimits.from_api({"memoryLimit": 100, "memoryFree": 0}).free_bytes == 0
    assert StorageLimits.from_api({"memoryLimit": 100, "memoryFree": -5}).free_bytes == 0


def test_a_size_limit_prints_without_a_trailing_zero():
    from mapflow_next.core.formatting import size_limit
    assert size_limit(2 * 1024 ** 3) == "2 GB"
    assert size_limit(10 * 1024 ** 3) == "10 GB"
    assert size_limit(int(2.5 * 1024 ** 3)) == "2.5 GB"
    assert size_limit(100) == "100 B"
    assert size_limit(5 * 1024) == "5 KB"


def test_model_price_comes_from_price_per_sq_km():
    # As GET /projects/{id} lists 🏠 Buildings: the price in pricePerSqKm, the required blocks at 0
    real = {"id": "48d77088", "name": "🏠 Buildings", "pricePerSqKm": 10,
            "blocks": [{"name": "Buildings", "optional": False, "price": 0},
                       {"name": "Segmentation", "optional": False, "price": 0},
                       {"name": "Heights", "optional": True, "price": 10}]}
    model = Model.from_api(real)
    assert model.base_price == 10 and model.price({"Heights"}) == 20
    # No pricePerSqKm: the required blocks' prices are the model's
    assert Model.from_api({"id": "x", "name": "x", "blocks": [{"name": "a", "optional": False, "price": 4}]}
                          ).base_price == 4


def test_prices_per_km2_are_rounded():
    from mapflow_next.core.formatting import per_km2, rate
    # Real imagery prices (Mapbox z17–z21, Global mosaic 2021 z17–z18)
    assert [rate(p) for p in (0.5327332298643699, 2.1309329194574795, 8.523731677829918, 34.09492671131967,
                              136.3797068452787, 9.999999999991775, 39.9999999999671)] == \
        ["0.53", "2.1", "8.5", "34", "136", "10", "40"]
    assert rate(10) == "10" and rate(0) == "0" and rate(0.004) == "<0.01" and rate(2559.99) == "2,560"
    assert per_km2(5) == "5 cr/km²"


def test_my_data_address_follows_the_environment():
    assert Config(env="production", server="s").my_data_url == "https://app.mapflow.ai/my-data"
    assert Config(env="staging", server="s", web="https://web.example/").my_data_url == "https://web.example/my-data"


def test_processing_aois_are_a_list():
    from mapflow_next.core.models import aois_geojson
    square = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}
    # What Mapflow answers: a list. "Run again" failed on it with AttributeError: 'list' object has no 'get'
    real = aois_geojson([{"id": "a1", "status": "OK", "percentCompleted": 100, "geometry": square},
                         {"id": "a2", "geometry": None}])
    assert real == {"type": "FeatureCollection",
                    "features": [{"type": "Feature", "geometry": square, "properties": {"id": "a1"}}]}
    assert len(aois_geojson({"aois": [{"id": "a1", "geometry": square}]})["features"]) == 1
    assert aois_geojson(None)["features"] == [] and aois_geojson([])["features"] == []


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


def test_restart_is_for_failed_and_cancelled_and_for_roles_that_may_run():
    """spec/002_B § Plugin behaviour: Restart is offered for a failed or a cancelled processing, to every role
    that may run one."""
    offered = {status for status in Status if status.can_restart}
    assert offered == {Status.failed, Status.cancelled}
    assert not any(s.can_restart for s in (Status.ok, Status.in_progress, Status.awaiting, Status.refunded,
                                           Status.unprocessed))
    assert [role for role in Role if role.can_run] == [Role.contributor, Role.maintainer, Role.owner]
    # A role that may run but not manage: Restart does not depend on can_manage
    assert Role.contributor.can_run and not Role.contributor.can_manage
    assert not Role.readonly.can_run and not Role.readonly.can_manage


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


def test_issues_carry_ways_out():
    project = Project.from_api(PROJECT, "me@example.com")
    poor = UserStatus.from_api(dict(STATUS, remainingCredits=10))
    assert _draft().issues(project, poor)[0].links == (("Top up", "top_up"),)
    # a catalog provider the plan doesn't include: Premium or support
    status = UserStatus.from_api(STATUS)          # searchDataProviders: maxar
    image = ImageryChoice.from_catalog("img-9", "orbview", 18, "Orbview scene")
    draft = _draft()
    draft.imagery = image
    blocked = [i for i in draft.issues(project, status) if i.field == "account"]
    assert blocked and dict(blocked[0].links).keys() == {"See plans", "Contact support"}
    assert status.can_search("maxar") and status.can_search("MAXAR") and not status.can_search("orbview")
    # the provider's smallest order
    big = UserStatus.from_api(dict(STATUS, searchDataProviders=[{"name": "orbview", "minAreaSqKm": 25}]))
    small = [i for i in draft.issues(project, big) if i.field == "imagery"]
    assert small and "25.00 km²" in small[0].text
    draft.aoi.area_km2 = 30
    assert not [i for i in draft.issues(project, big) if i.field == "imagery"]


def test_ratings_are_read_from_processings():
    rated = dict(processing_json("p", "OK", 100), rating={"rating": 4, "feedback": "ok"})
    assert Processing.from_api(rated).rating == 4
    assert Processing.from_api(dict(processing_json("p", "OK", 100), rating=5)).rating == 5
    assert Processing.from_api(processing_json("p", "OK", 100)).rating == 0


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
    settings = {"variables/mapflow_env": "staging", "mapflow_next/auth_url": "http://localhost:9/oidc/"}
    staging = load_config(type("S", (), {"value": lambda self, k, d=None: settings.get(k, d)})())
    assert staging.server == "https://whitemaps-staging.mapflow.ai/rest"
    assert staging.token_url == "http://localhost:9/oidc/token"


@pytest.mark.parametrize("env, base", [
    ("production", "https://auth.mapflow.ai/auth/realms/mapflow/protocol/openid-connect"),
    ("staging", "https://auth-staging.mapflow.ai/auth/realms/mapflow-staging/protocol/openid-connect"),
    ("internal", "https://auth-internal.mapflow.ai/auth/realms/mapflow-internal/protocol/openid-connect"),
    ("duty", "https://auth-duty.mapflow.ai/auth/realms/mapflow-duty/protocol/openid-connect"),
])
def test_sign_in_host_of_each_environment(env, base):
    config = Config(env, f"https://whitemaps-{env}.mapflow.ai/rest")
    assert config.authorize_url == f"{base}/auth"
    assert config.token_url == f"{base}/token"


@pytest.mark.parametrize("env", ["production", "staging", "internal", "duty"])
def test_sign_in_override_wins_in_every_environment(env):
    settings = {"variables/mapflow_env": env, "mapflow_next/auth_url": "http://localhost:9/oidc/"}
    config = load_config(type("S", (), {"value": lambda self, k, d=None: settings.get(k, d)})())
    assert config.token_url == "http://localhost:9/oidc/token"
    assert config.authorize_url == "http://localhost:9/oidc/auth"


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


def test_collection_tags():
    from mapflow_next.core.models import Mosaic
    assert Mosaic.from_api({"id": "m", "name": "A", "tags": ["a", "b"]}).tags == ["a", "b"]
    assert Mosaic.from_api({"id": "m", "name": "A"}).tags == []
    assert Mosaic.from_api({"id": "m", "name": "A", "tags": "a"}).tags == []
    assert Mosaic.from_api({"id": "m", "name": "A", "tags": ["a", "", None, 3, "b"]}).tags == ["a", "b"]


def test_imagery_choice_follows_a_renamed_collection():
    from mapflow_next.core.draft import ImageryChoice
    whole = ImageryChoice.from_mosaic("m", "Old")
    whole.with_collection_name("Old", "New")
    assert whole.label == "New"
    one = ImageryChoice.from_mosaic("m", "Old", "i", "a.tif")
    one.with_collection_name("Old", "New")
    assert one.label == "New · a.tif" and one.source_params() == {"myImagery": {"imageIds": ["i"]}}
    other = ImageryChoice.from_mosaic("m", "Something")
    other.with_collection_name("Old", "New")
    assert other.label == "Something"


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


PLUGIN = Path(__file__).resolve().parents[1] / "mapflow_next"

# Each README rule of § "QGIS 3 and QGIS 4" is a function that takes the source of one file and returns
# problems, as (line, text). RULE_ALLOWED lists the files a rule does not apply to.
EVENT_NAMES = {"event", "e", "ev", "evt"}


def _lines(source, pattern, why):
    import re
    return [(number, why) for number, line in enumerate(source.splitlines(), 1) if re.search(pattern, line)]


def rule_qgis_pyqt(source):
    return _lines(source, r"^\s*(from|import) PyQt[56]\b", "import from qgis.PyQt, not PyQt5/PyQt6 directly")


def rule_scoped_qgis_enums(source):
    return _lines(source, r"\bQgis\.(Info|Warning|Critical|Success)\b", "use Qgis.MessageLevel.<level>")


def rule_exec(source):
    return _lines(source, r"\.exec_\(", "exec_() is gone in PyQt6: use exec()")


def rule_removed_in_qt6(source):
    return _lines(source, r"\bQRegExp\b|\bQDesktopWidget\b|\.desktop\(\)", "removed in Qt 6")


def _calls(source, method):
    import ast
    return [node for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == method]


def rule_menu_actions(source):
    """addAction(text, slot) and addAction(icon, text[, slot]) differ between Qt 5 and Qt 6. Allowed: one argument
    that is not a text literal (a QAction), and QLineEdit.addAction(icon, QLineEdit.ActionPosition.*)."""
    import ast
    problems = []
    for call in _calls(source, "addAction"):
        args = call.args
        if len(args) == 1:
            fine = not (isinstance(args[0], ast.JoinedStr) or isinstance(args[0], ast.Constant))
        else:
            fine = len(args) == 2 and "ActionPosition" in ast.unparse(args[1])
        if not fine:
            problems.append((call.lineno, "build menu items as QActions with widgets.menu_action"))
    return problems


def rule_event_pos(source):
    """pos() is gone from mouse events in Qt 6, as are globalPos(), localPos(), screenPos() and windowPos()."""
    import ast
    problems = []
    for method in ("pos", "globalPos", "localPos", "screenPos", "windowPos"):
        for call in _calls(source, method):
            receiver = call.func.value
            name = receiver.id if isinstance(receiver, ast.Name) else getattr(receiver, "attr", "")
            if method != "pos" or name in EVENT_NAMES or name.endswith("event"):
                problems.append((call.lineno, f"read mouse positions through widgets.event_pos, not {method}()"))
    return problems


def rule_geometry_types(source):
    return _lines(source,
                  r"\bQgsWkbTypes\.\w+Geometry\b|\bQgis\.GeometryType\b|\bQgsMapLayerType\b|\bQgis\.LayerType\b",
                  "use the geometry and layer types in qgis_bridge/compat.py")


def rule_svg_widget(source):
    return _lines(source, r"\bQSvgWidget\b", "QSvgWidget belongs in ui/icons.py, which imports it from either place")


def svg_imports_of_icons(source):
    """ui/icons.py: QSvgWidget from QtSvg (Qt 5) and from QtSvgWidgets (Qt 6)."""
    return [(1, f"ui/icons.py must import QSvgWidget from {module}") for module in ("QtSvg", "QtSvgWidgets")
            if f"qgis.PyQt.{module} import QSvgWidget" not in source]


RULES = {
    "qgis.PyQt": (rule_qgis_pyqt, {"ui/icons.py"}),          # icons.py: the QSvgWidget fallback
    "scoped enums": (rule_scoped_qgis_enums, set()),
    "exec": (rule_exec, set()),
    "removed": (rule_removed_in_qt6, set()),
    "menu actions": (rule_menu_actions, {"ui/widgets.py"}),
    "event_pos": (rule_event_pos, {"ui/widgets.py"}),
    "compat": (rule_geometry_types, {"qgis_bridge/compat.py"}),
    "svg": (rule_svg_widget, {"ui/icons.py"}),
}


def _tree_problems(rule_name):
    rule, allowed = RULES[rule_name]
    problems = []
    for path in sorted(PLUGIN.rglob("*.py")):
        name = str(path.relative_to(PLUGIN))
        if name not in allowed:
            problems += [f"{name}:{number}: {why}" for number, why in rule(path.read_text(encoding="utf-8"))]
    return problems


def _bites(rule, bad, good):
    """The rule reports the bad snippet and accepts the good one."""
    assert rule(bad), f"{rule.__name__} does not report: {bad}"
    assert not rule(good), f"{rule.__name__} reports: {good}"


def imported_modules(source, module):
    """The absolute dotted names a file imports, as (line, name). `module` is the dotted name of the file."""
    import ast
    package = module.rsplit(".", 1)[0]
    names = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names += [(node.lineno, alias.name) for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                parent = package.split(".")[:len(package.split(".")) - (node.level - 1)]
                base = ".".join(parent + ([node.module] if node.module else []))
            names.append((node.lineno, base))
            names += [(node.lineno, f"{base}.{alias.name}") for alias in node.names]
    return names


def rule_ui_imports_no_service(source, module="mapflow_next.ui.page"):
    return sorted({(number, "ui/ must not import services/: a page renders what it is given")
                   for number, name in imported_modules(source, module)
                   if name == "mapflow_next.services" or name.startswith("mapflow_next.services.")})


def rule_controller_no_http(source, module="mapflow_next.controller"):
    import ast
    problems = [(number, "the controller reaches requests through api/client.py, not Http")
                for number, name in imported_modules(source, module)
                if name == "mapflow_next.api.http" or name.startswith("mapflow_next.api.http.")]
    problems += [(node.lineno, "the controller reaches requests through api/client.py, not `.http`")
                 for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Attribute) and node.attr == "http"]
    return sorted(set(problems))


def test_ui_imports_no_service():
    ui = "mapflow_next.ui.page"
    for bad in ("from ..services.results import FILES\n", "from .. import services\n",
                "import mapflow_next.services.results\n", "from mapflow_next.services import results\n"):
        _bites(lambda source: rule_ui_imports_no_service(source, ui), bad, "from .. import config\n")
    for good in ("from .. import config\n", "from ..core.guard import guarded\n", "from . import theme\n",
                 "from ..settings import default_output_dir\n"):
        assert not rule_ui_imports_no_service(good, ui), good
    problems = []
    for path in sorted((PLUGIN / "ui").rglob("*.py")):
        module = ".".join(("mapflow_next",) + path.relative_to(PLUGIN).with_suffix("").parts)
        problems += [f"{path.relative_to(PLUGIN)}:{number}: {why}"
                     for number, why in rule_ui_imports_no_service(path.read_text(encoding="utf-8"), module)]
    assert not problems, "\n".join(problems)


def test_controller_does_not_call_http():
    for bad in ("self.api.http.abort(1)\n", "x = api.http\n", "from .api.http import Http\n",
                "from .api import http\n"):
        _bites(rule_controller_no_http, bad, "self.api.abort(1)\n")
    for good in ("self.api.abort(1)\n", "from .api.client import MapflowApi\n",
                 "# Http logs the failure\nx = 'Http'\n"):
        assert not rule_controller_no_http(good), good
    source = (PLUGIN / "controller.py").read_text(encoding="utf-8")
    problems = [f"controller.py:{number}: {why}" for number, why in rule_controller_no_http(source)]
    assert not problems, "\n".join(problems)


def rule_service_has_stop(source, only=None):
    """The classes of a file that derive from QObject and define no `stop` method. `only` names the one class."""
    import ast
    problems = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.ClassDef) or (only and node.name != only):
            continue
        bases = {base.id if isinstance(base, ast.Name) else getattr(base, "attr", "") for base in node.bases}
        methods = {item.name for item in node.body if isinstance(item, ast.FunctionDef)}
        if "QObject" in bases and "stop" not in methods:
            problems.append((node.lineno, node.name))
    return sorted(problems)


def test_every_service_has_stop():
    bad = "class X(QObject):\n    def __init__(self):\n        pass\n"
    good = bad + "    def stop(self):\n        pass\n"
    _bites(rule_service_has_stop, bad, good)
    assert not rule_service_has_stop("class X:\n    def __init__(self):\n        pass\n")
    assert not rule_service_has_stop("@dataclass\nclass X(Base):\n    a: int = 0\n")
    assert not rule_service_has_stop("class Y(QObject):\n    pass\n", only="X")
    checked = [(path, None) for path in sorted(PLUGIN.glob("services/*.py"))] + [(PLUGIN / "api" / "http.py", "Http")]
    problems = []
    for path, only in checked:
        problems += [f"{path.relative_to(PLUGIN)}:{name}: no stop()"
                     for _number, name in rule_service_has_stop(path.read_text(encoding="utf-8"), only)]
    assert not problems, "\n".join(problems)


def test_qt_is_imported_only_through_qgis_pyqt():
    _bites(rule_qgis_pyqt, "from PyQt6.QtCore import Qt\n", "from qgis.PyQt.QtCore import Qt\n")
    _bites(rule_qgis_pyqt, "import PyQt5\n", "import qgis.PyQt\n")
    assert not _tree_problems("qgis.PyQt")


def test_enum_names_are_scoped():
    """QGIS's own enums; tools/qt6_check.py checks the Qt ones (it needs PyQt6)."""
    _bites(rule_scoped_qgis_enums, "level = Qgis.Critical\n", "level = Qgis.MessageLevel.Critical\n")
    assert not _tree_problems("scoped enums")


def test_exec_is_not_exec_underscore():
    _bites(rule_exec, "menu.exec_(pos)\n", "menu.exec(pos)\n")
    assert not _tree_problems("exec")


def test_nothing_removed_in_qt6_is_used():
    _bites(rule_removed_in_qt6, "x = QRegExp('a')\n", "x = QRegularExpression('a')\n")
    _bites(rule_removed_in_qt6, "QApplication.desktop()\n", "QApplication.primaryScreen()\n")
    assert not _tree_problems("removed")


def test_menu_items_are_qactions():
    _bites(rule_menu_actions, "menu.addAction(icon, 'Open', handler)\n", "menu.addAction(action)\n")
    _bites(rule_menu_actions, "menu.addAction('Open', handler)\n", "toolbar.addAction(self.action)\n")
    _bites(rule_menu_actions, "menu.addAction('Open')\n", "menu.addAction(action)\n")
    _bites(rule_menu_actions, "menu.addAction(icons.icon('x'), 'Open')\n",
           "self.search.addAction(icon, QLineEdit.ActionPosition.LeadingPosition)\n")
    assert not _tree_problems("menu actions")


def test_mouse_positions_come_from_event_pos():
    _bites(rule_event_pos, "def f(event):\n    return event.pos()\n", "def f(event):\n    return event_pos(event)\n")
    _bites(rule_event_pos, "x = ev.globalPos()\n", "x = widget.pos()\n")
    _bites(rule_event_pos, "x = self.mouse_event.pos()\n", "x = QCursor.pos()\n")
    assert not _tree_problems("event_pos")


def test_geometry_and_layer_types_come_from_compat():
    _bites(rule_geometry_types, "g = QgsWkbTypes.PolygonGeometry\n", "g = POLYGON_GEOMETRY\n")
    _bites(rule_geometry_types, "g = Qgis.GeometryType.Polygon\n", "g = compat.POLYGON_GEOMETRY\n")
    _bites(rule_geometry_types, "t = QgsMapLayerType.VectorLayer\n", "t = VECTOR_LAYER\n")
    _bites(rule_geometry_types, "t = Qgis.LayerType.Raster\n", "t = RASTER_LAYER\n")
    assert not _tree_problems("compat")


def test_qsvgwidget_is_imported_from_either_place_in_icons_only():
    _bites(rule_svg_widget, "from qgis.PyQt.QtSvg import QSvgWidget\n", "from qgis.PyQt.QtSvg import QSvgRenderer\n")
    both = ("try:\n    from qgis.PyQt.QtSvg import QSvgWidget\nexcept ImportError:\n"
            "    from qgis.PyQt.QtSvgWidgets import QSvgWidget\n")
    _bites(svg_imports_of_icons, "from qgis.PyQt.QtSvg import QSvgWidget\n", both)
    _bites(svg_imports_of_icons, "from qgis.PyQt.QtSvgWidgets import QSvgWidget\n", both)
    assert not _tree_problems("svg")
    assert not svg_imports_of_icons((PLUGIN / "ui" / "icons.py").read_text(encoding="utf-8"))


def test_code_runs_on_qt5_and_qt6():
    """QGIS 3 runs Qt 5 and QGIS 4 runs Qt 6; metadata.txt declares both."""
    metadata = (PLUGIN / "metadata.txt").read_text(encoding="utf-8")
    assert "qgisMaximumVersion=4.99" in metadata and "qgisMinimumVersion=3.28" in metadata


# Each rule of README § "QGIS 3 and QGIS 4": the start of its bullet -> what checks it. A README rule
# without a key here fails test_every_readme_qt_rule_has_a_check.
README_RULE_CHECKS = {
    "Import Qt only through `qgis.PyQt`": "test_qt_is_imported_only_through_qgis_pyqt",
    "Use scoped enum names": "tools/qt6_check.py",             # Qt enums and enums read from an object
    "Use `exec()`": "test_exec_is_not_exec_underscore",
    "Build menu items as `QAction`s": "test_menu_items_are_qactions",
    "Read mouse positions through `widgets.event_pos`": "test_mouse_positions_come_from_event_pos",
    "Take geometry types from `qgis_bridge/compat.py`": "test_geometry_and_layer_types_come_from_compat",
    "`QSvgWidget` moved to `QtSvgWidgets`": "test_qsvgwidget_is_imported_from_either_place_in_icons_only",
}


def readme_qt_rules(text):
    """The bullets of README § "QGIS 3 and QGIS 4" between "check these rules:" and the --fix line."""
    section = text.split("check these rules:", 1)[1].split("Run `tools/qt6_check.py --fix`", 1)[0]
    rules = []
    for line in section.splitlines():
        if line.startswith("- "):
            rules.append(line[2:].strip())
        elif line.startswith("  ") and rules:
            rules[-1] += " " + line.strip()
    return rules


def unchecked_readme_rules(text):
    return [rule for rule in readme_qt_rules(text) if not any(rule.startswith(key) for key in README_RULE_CHECKS)]


def test_every_readme_qt_rule_has_a_check():
    readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")
    assert len(readme_qt_rules(readme)) == len(README_RULE_CHECKS) == 7
    assert not unchecked_readme_rules(readme)
    for check in README_RULE_CHECKS.values():          # a named test exists; the tool is a file
        assert check in globals() or (Path(__file__).resolve().parents[1] / check).is_file(), check
    fix_line = "Run `tools/qt6_check.py --fix`"
    added = readme.replace(fix_line, "- Never do a new thing.\n\n" + fix_line)
    assert unchecked_readme_rules(added) == ["Never do a new thing."]


def test_ledger_of_critical_messages():
    from tests.ledger import Ledger
    ledger = Ledger()
    assert ledger.unexpected() == []
    ledger.record("bar", "Something went wrong: x")
    ledger.record("log", "Traceback ... x")
    ledger.record("bar", "Layer has no images")
    assert ledger.unexpected() == ["bar: Something went wrong: x", "log: Traceback ... x", "bar: Layer has no images"]
    assert ledger.expect("has no images") == 1
    assert ledger.expect("has no images") == 0               # an entry is expected once
    assert ledger.expect("nothing like it") == 0
    assert ledger.unexpected() == ["bar: Something went wrong: x", "log: Traceback ... x"]
    assert ledger.expect("x") == 2 and ledger.unexpected() == []
    ledger.record("bar", "has no images")                    # a later message is not covered by an earlier declaration
    assert ledger.unexpected() == ["bar: has no images"]


def test_a_missing_qgis_fails_in_the_test_images_and_skips_elsewhere(tmp_path):
    from tests.image_check import missing_qgis_outcome
    marker = tmp_path / "dockerenv"
    marker.write_text("")
    app = Path("/app")
    assert missing_qgis_outcome(app, markers=[str(marker)]) == "fail"
    assert missing_qgis_outcome(app, markers=[str(tmp_path / "absent")]) == "skip"      # a host that has /app
    assert missing_qgis_outcome(tmp_path, markers=[str(marker)]) == "skip"             # another container


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


def test_catalog_coverage():
    """With one catalog image chosen, only the part of the area inside the image's footprint is processed,
    measured against the limits and the provider's minimum, and an area outside it blocks the run."""
    from mapflow_next.core.draft import AreaOfInterest, Coverage
    project = Project.from_api(PROJECT, "me@example.com")          # aoi_area_limit_km2 == 100
    draft = _draft(area=150)
    whole = draft.aoi
    inside = AreaOfInterest(name=whole.name,
                            geometry={"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
                            area_km2=20, max_bbox_km2=25, polygons=1)
    draft.imagery = ImageryChoice.from_catalog("img-9", "maxar", 18, "Maxar scene")
    status = UserStatus.from_api(STATUS)
    assert any(i.field == "area" for i in draft.issues(project, status))      # the whole area is over the limit
    draft.coverage = Coverage("Maxar scene", True, inside)
    assert draft.processed_area is inside
    assert draft.payload("project-1")["geometry"] == inside.geometry
    assert not any(i.field == "area" for i in draft.issues(project, status))  # the part inside is not
    # the provider's smallest order is judged on the part inside
    draft.imagery = ImageryChoice.from_catalog("img-9", "maxar", 18, "Maxar scene", min_area_km2=25)
    small = [i for i in draft.issues(project, status) if i.field == "imagery"]
    assert small and "sells at least 25.00 km²" in small[0].text and "20.00 km²" in small[0].text
    draft.coverage = None
    assert not [i for i in draft.issues(project, status) if i.field == "imagery"]    # the whole area is above it
    draft.coverage = Coverage("Maxar scene", False, None)
    assert draft.processed_area is whole
    assert any(i.field == "area" and "doesn't overlap “Maxar scene”" in i.text
               for i in draft.issues(project, status))


# ---------- the guard (spec/006 § The guard) ----------

@pytest.fixture
def reporter():
    """Install a reporter that records its calls; the previous one comes back after the test."""
    from mapflow_next.core import guard
    saved, calls = guard._reporter, []
    guard.set_reporter(lambda exc, details, request: calls.append((exc, details, request)))
    yield calls
    guard._reporter = saved


def test_guard_returns_its_default_when_the_call_raises(reporter):
    from mapflow_next.core.guard import guarded

    @guarded(default=False)
    def filter_event(value):
        return 1 / value

    assert filter_event(2) == 0.5
    assert filter_event(0) is False
    assert len(reporter) == 1


def test_guard_returns_the_value_and_swallows_an_exception(reporter):
    from mapflow_next.core.guard import guarded

    def divide(a, b):
        return a / b

    assert guarded(divide)(6, 3) == 2
    assert reporter == []
    assert guarded(divide)(1, 0) is None
    assert len(reporter) == 1
    exc, details, request = reporter[0]
    assert request is None
    assert isinstance(exc, ZeroDivisionError)
    assert "ZeroDivisionError" in details and "divide" in details and "Traceback" in details


def test_guard_does_not_swallow_a_system_exit(reporter):
    from mapflow_next.core.guard import guarded

    def stop():
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        guarded(stop)()
    assert reporter == []


def test_guard_without_a_reporter_writes_to_stderr(capsys):
    from mapflow_next.core import guard
    saved = guard._reporter
    guard._reporter = None
    try:
        assert guard.guarded(lambda: 1 / 0)() is None
    finally:
        guard._reporter = saved
    assert "ZeroDivisionError" in capsys.readouterr().err


def test_guard_survives_a_reporter_that_raises(capsys):
    from mapflow_next.core import guard
    saved = guard._reporter

    def broken(exc, details, request):
        raise RuntimeError("reporter is broken")

    guard.set_reporter(broken)
    try:
        assert guard.guarded(lambda: 1 / 0)() is None
    finally:
        guard._reporter = saved
    assert "ZeroDivisionError" in capsys.readouterr().err


def test_clear_reporter_leaves_another_reporter_alone(reporter):
    from mapflow_next.core import guard
    installed = guard._reporter
    guard.clear_reporter(lambda exc, details, request: None)
    assert guard._reporter is installed
    guard.clear_reporter(installed)
    assert guard._reporter is None


def test_a_bound_method_is_cleared_by_an_equal_bound_method():
    from mapflow_next.core import guard

    class Owner:
        def report(self, exc, details, request):
            pass

    saved, owner = guard._reporter, Owner()
    try:
        guard.set_reporter(owner.report)
        guard.clear_reporter(owner.report)           # a new bound-method object each time
        assert guard._reporter is None
    finally:
        guard._reporter = saved


def test_guard_drops_the_arguments_the_slot_does_not_take(reporter):
    """`clicked(bool)` reaches `lambda: ...` in PyQt because PyQt retries with fewer arguments; the wrapper must
    not hide that."""
    from mapflow_next.core.guard import guarded
    calls = []
    guarded(lambda: calls.append("none"))(False)
    guarded(lambda *args: calls.append(args))(False, 1)
    guarded(lambda one: calls.append(one))(7, "extra")
    guarded(lambda one, two=2: calls.append((one, two)))(1)
    guarded(lambda one, **kw: calls.append((one, kw)))(1, other=3)
    assert calls == ["none", (False, 1), 7, (1, 2), (1, {"other": 3})]
    assert reporter == []


def test_a_guarded_method_stays_a_bound_method(reporter):
    from mapflow_next.core.guard import guarded

    class Page:
        def __init__(self):
            self.seen = []

        @guarded
        def slot(self):
            self.seen.append("slot")

        @guarded
        def one(self, value):
            self.seen.append(value)

        @guarded
        def boom(self, *_):
            raise ValueError("boom")

    page = Page()
    assert page.slot.__self__ is page and page.slot.__name__ == "slot"
    page.slot(True)                  # the `checked` that the slot does not take
    page.one(5, 6)
    assert page.seen == ["slot", 5]
    page.boom(1)
    assert [str(call[0]) for call in reporter] == ["boom"] and "Page.boom" in reporter[0][1]


def test_guard_works_on_partials_and_other_objects_methods(reporter):
    from functools import partial
    from mapflow_next.core.guard import guarded

    def add(key, value):
        return key + value

    assert guarded(partial(add, 1))(2, "extra") == 3
    assert guarded([].append)(1) is None and reporter == []      # a builtin: no signature to read, all arguments


def test_transient_and_permanent_failures():
    from mapflow_next.core.failures import is_transient
    for kind in ("offline", "proxy", "timeout", "server"):
        assert is_transient(kind, None), kind
    assert is_transient("server", 503)
    # Another 4xx asks the same question again: permanent
    for status in (400, 422, 429):
        assert not is_transient("client", status)
    assert not is_transient("forbidden", 403) and not is_transient("not_found", 404)
    # A Qt connection error `classify` has no name for carries no status: the connection, not the request
    assert is_transient("client", None)
    # Handled elsewhere: the session's (auth), the guard's (plugin), nobody's (cancelled)
    assert not any(is_transient(kind, None) for kind in ("auth", "plugin", "cancelled"))


def test_a_timer_keeps_its_schedule_through_a_401():
    from mapflow_next.core.failures import DROP, PollFailures, keeps_schedule
    assert keeps_schedule("auth", 401)
    for kind, status in (("server", 503), ("timeout", None), ("offline", None), ("proxy", None), ("client", None)):
        assert keeps_schedule(kind, status), kind
    for kind, status in (("forbidden", 403), ("not_found", 404), ("client", 400), ("plugin", None),
                         ("cancelled", None)):
        assert not keeps_schedule(kind, status), kind
    poll = PollFailures(3)
    assert poll.failed("auth", 401) == DROP and poll.count == 0 and not poll.stopped


def test_strongest_trigger_wins():
    from mapflow_next.core.failures import LOAD, POLL, USER, stronger
    assert stronger(POLL, LOAD) == LOAD and stronger(LOAD, USER) == USER and stronger(USER, POLL) == USER
    assert stronger(None, POLL) == POLL and stronger(None, None) is None


def test_poll_failures_are_told_once_per_run():
    from mapflow_next.core.failures import ALERT, DROP, PollFailures
    poll = PollFailures(3)
    assert [poll.failed("server", 503), poll.failed("timeout"), poll.failed("offline")] == [DROP, DROP, ALERT]
    assert [poll.failed("server", 503), poll.failed("server", 503)] == [DROP, DROP]     # said once
    poll.succeeded()
    assert poll.count == 0
    assert [poll.failed("server", 503), poll.failed("server", 503), poll.failed("server", 503)] == [DROP, DROP, ALERT]
    assert not poll.stopped


def test_a_success_between_failures_resets_the_count():
    from mapflow_next.core.failures import DROP, PollFailures
    poll = PollFailures(3)
    results = [poll.failed("server"), poll.failed("server")]
    poll.succeeded()
    results += [poll.failed("server"), poll.failed("server")]
    assert results == [DROP] * 4


def test_a_permanent_poll_failure_stops_until_a_success():
    from mapflow_next.core.failures import STOP, PollFailures
    poll = PollFailures(3)
    assert poll.failed("forbidden", 403) == STOP and poll.stopped
    poll.succeeded()
    assert not poll.stopped
    assert poll.failed("client", 400) == STOP and poll.stopped
    # A bug in a callback repeats on every tick: stop, and the guard's line is the user's notice
    poll.succeeded()
    assert poll.failed("plugin", 200) == STOP and poll.stopped


def test_auth_is_not_counted_as_a_poll_failure():
    from mapflow_next.core.failures import ALERT, DROP, PollFailures
    poll = PollFailures(3)
    assert [poll.failed("server"), poll.failed("server"), poll.failed("auth", 401), poll.failed("server")] == \
        [DROP, DROP, DROP, ALERT]


def test_poll_notice_names_what_stopped_and_why():
    from mapflow_next.core.failures import ALERT, DROP, STOP, poll_notice
    assert poll_notice(DROP, "account status", "x") == ""
    assert poll_notice(STOP, "account status", "x", "plugin") == ""
    alert = poll_notice(ALERT, "processings list", "Mapflow is down.", "server")
    assert "processings list" in alert and "Mapflow is down." in alert
    stop = poll_notice(STOP, "account status", "Not available for your account.", "forbidden")
    assert "account status" in stop and "Not available for your account." in stop


def test_an_empty_list_text_comes_only_after_a_successful_answer():
    from mapflow_next.core.failures import empty_list_text
    none = "No processings in this project yet."
    assert empty_list_text("processings", none, loaded=False, loading=False, failed=False) == "Loading processings…"
    assert empty_list_text("processings", none, loaded=False, loading=True, failed=False) == "Loading processings…"
    assert empty_list_text("processings", none, loaded=False, loading=False, failed=True) == \
        "Processings didn't load."
    assert empty_list_text("processings", none, loaded=True, loading=True, failed=False) == "Loading processings…"
    assert empty_list_text("processings", none, loaded=True, loading=False, failed=False) == none


def test_project_gone_text_says_what_opened():
    from mapflow_next.core.failures import project_gone_text
    assert "Roads" in project_gone_text("Roads", True) and "default" in project_gone_text("Roads", True)
    assert "no other project" in project_gone_text("Roads", False)
    assert project_gone_text("", True).startswith("The project")


def test_core_imports_no_qt():
    """`core/` is the one package every layer may import (spec/007 layer rules), and it is pure Python."""
    import ast
    problems = []
    for path in sorted((PLUGIN / "core").glob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = ([alias.name for alias in node.names] if isinstance(node, ast.Import)
                     else [node.module or ""] if isinstance(node, ast.ImportFrom) and not node.level else [])
            problems += [f"{path.name}:{node.lineno}: imports {name}" for name in names
                         if name.split(".")[0] in ("qgis", "PyQt5", "PyQt6", "sip")]
    assert not problems, "\n".join(problems)


# ---------- the source check: every entry point Qt calls is guarded ----------

# Qt C++ slots: nothing of the plugin runs, so there is nothing to guard. A new entry needs a comment.
QT_SLOTS = {
    "setChecked",      # plugin.py: the dock's visibility moves the toolbar button
    "reject",          # ui/settings_dialog.py: a button closes its own dialog
}


def _is_guarded_decorator(node):
    import ast
    if isinstance(node, ast.Call):              # @guarded(default=False)
        node = node.func
    return (isinstance(node, ast.Name) and node.id == "guarded") or \
        (isinstance(node, ast.Attribute) and node.attr == "guarded")


def _is_guarded_def(node):
    return any(_is_guarded_decorator(decorator) for decorator in node.decorator_list)


def _entry_point(call):
    """The callable that Qt will run for `x.connect(f)` or `QTimer.singleShot(ms, f)`, or None."""
    import ast
    func = call.func
    if not isinstance(func, ast.Attribute):
        return None
    if func.attr == "connect" and call.args:
        return call.args[0]
    if func.attr == "singleShot" and len(call.args) >= 2:
        return call.args[1]
    return None


def rule_entry_points(source):
    """Every callable that Qt runs is guarded: `guarded(...)` at the connection site, a `self.method` that is
    decorated with `@guarded` in the same class, a local function decorated with it, a `partial` of those,
    or `signal.emit` (nothing of the plugin runs there; the receiving slots are guarded themselves)."""
    import ast
    tree = ast.parse(source)
    problems = []

    def defs(scope, name):
        return [n for n in ast.iter_child_nodes(scope) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                and n.name == name]

    def fine(arg, stack):
        if isinstance(arg, ast.Call):
            func = arg.func
            if isinstance(func, ast.Name) and func.id == "guarded" or \
                    isinstance(func, ast.Attribute) and func.attr == "guarded":
                return True
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
            return name == "partial" and bool(arg.args) and fine(arg.args[0], stack)
        if isinstance(arg, ast.Attribute):
            if arg.attr == "emit":
                return True
            if isinstance(arg.value, ast.Name) and arg.value.id == "self":
                classes = [s for s in stack if isinstance(s, ast.ClassDef)]
                found = defs(classes[-1], arg.attr) if classes else []
                if found:
                    return all(_is_guarded_def(n) for n in found)
            return arg.attr in QT_SLOTS
        if isinstance(arg, ast.Name):
            for scope in reversed(stack):
                if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    found = defs(scope, arg.id)
                    if found:
                        return all(_is_guarded_def(n) for n in found)
        return False

    def visit(node, stack):
        if isinstance(node, ast.Call):
            arg = _entry_point(node)
            if arg is not None and not fine(arg, stack):
                problems.append((node.lineno, f"`{ast.unparse(arg)[:60]}` is an entry point that is not guarded: "
                                              "decorate the method with @guarded, or wrap it: guarded(...)"))
        scoped = isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        for child in ast.iter_child_nodes(node):
            visit(child, stack + [node] if scoped else stack)

    visit(tree, [])
    return problems


def _src(text):
    import textwrap
    return textwrap.dedent(text).lstrip("\n")


def test_every_entry_point_is_guarded():
    _bites(rule_entry_points, "button.clicked.connect(lambda: run())\n",
           "button.clicked.connect(guarded(lambda: run()))\n")
    _bites(rule_entry_points, "QTimer.singleShot(0, lambda: run())\n",
           "QTimer.singleShot(0, guarded(lambda: run()))\n")
    _bites(rule_entry_points, "dock.visibilityChanged.connect(session.set_active)\n",
           "dock.visibilityChanged.connect(self.action.setChecked)\n")
    _bites(rule_entry_points, "a.changed.connect(b.run)\n", "a.changed.connect(b.changed.emit)\n")
    _bites(rule_entry_points, _src("""
        class A:
            def go(self): pass
            def f(self):
                b.clicked.connect(self.go)
        """), _src("""
        class A:
            @guarded
            def go(self): pass
            def f(self):
                b.clicked.connect(self.go)
        """))
    _bites(rule_entry_points, _src("""
        class A:
            def f(self):
                b.clicked.connect(self.missing)
        """), _src("""
        class A:
            def f(self):
                b.clicked.connect(guarded(self.missing))
        """))
    _bites(rule_entry_points, _src("""
        class A:
            def go(self, key): pass
            def f(self):
                s.connect(partial(self.go, 1))
        """), _src("""
        class A:
            @guarded
            def go(self, key): pass
            def f(self):
                s.connect(partial(self.go, 1))
        """))
    _bites(rule_entry_points, _src("""
        def f():
            def apply(): pass
            s.connect(apply)
        """), _src("""
        def f():
            @guarded
            def apply(): pass
            s.connect(apply)
        """))
    # the same method name in two classes: each class is judged by its own def
    _bites(rule_entry_points, _src("""
        class A:
            @guarded
            def go(self): pass
        class B:
            def go(self): pass
            def f(self):
                s.connect(self.go)
        """), _src("""
        class A:
            def go(self): pass
        class B:
            @guarded
            def go(self): pass
            def f(self):
                s.connect(self.go)
        """))
    problems = _tree_problems_of(rule_entry_points)
    assert not problems, "\n".join(problems)


# Qt calls these methods of a class of the plugin: a `*Event` handler, `event`, an event filter,
# the size methods (`sizeHint`, `minimumSizeHint`, `hasHeightForWidth`, `heightForWidth`), `QgsTask.finished` and
# `QgsMapTool.deactivate`. An exception that leaves one opens the raw error dialog of QGIS, as one that leaves a
# slot.
QT_VIRTUALS = re.compile(r"^(?:[a-z][A-Za-z]*Event|event|eventFilter|finished|deactivate|heightForWidth|"
                         r"hasHeightForWidth|sizeHint|minimumSizeHint)$")
# `cancel` is called by Qt on a `QgsTask` only: another class may have a `cancel` that Qt never calls.
QT_TASK_VIRTUALS = {"cancel"}


def _has_base(cls, name):
    import ast
    for base in cls.bases:
        if (isinstance(base, ast.Name) and base.id == name) or \
                (isinstance(base, ast.Attribute) and base.attr == name):
            return True
    return False


def _own_returns(node):
    """The `return` statements of a method's own body: not those of a nested function or lambda."""
    import ast
    found, stack = [], list(node.body)
    while stack:
        item = stack.pop()
        if isinstance(item, ast.Return):
            found.append(item)
        if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            stack.extend(ast.iter_child_nodes(item))
    return found


def _has_result(node):
    """The method gives Qt a value: a return annotation other than `None`, or a `return <value>`."""
    import ast
    if node.returns is not None and not (isinstance(node.returns, ast.Constant) and node.returns.value is None):
        return True
    return any(r.value is not None and not (isinstance(r.value, ast.Constant) and r.value.value is None)
               for r in _own_returns(node))


def _has_default(node):
    """The method has the decorator `guarded(default=...)`."""
    import ast
    return any(isinstance(d, ast.Call) and _is_guarded_decorator(d) and any(k.arg == "default" for k in d.keywords)
               for d in node.decorator_list)


def _default_of(node):
    """The expression of the `default=` of the decorator `guarded(default=...)`, or None."""
    import ast
    for d in node.decorator_list:
        if isinstance(d, ast.Call) and _is_guarded_decorator(d):
            for k in d.keywords:
                if k.arg == "default":
                    return k.value
    return None


def _is_qsize_call(expr):
    import ast
    return isinstance(expr, ast.Call) and (
        (isinstance(expr.func, ast.Name) and expr.func.id == "QSize")
        or (isinstance(expr.func, ast.Attribute) and expr.func.attr == "QSize"))


def rule_virtual_overrides(source):
    """Every method that Qt calls by name (see QT_VIRTUALS) is decorated with `@guarded`, and one that gives Qt
    a value is decorated with `@guarded(default=...)`: PyQt raises a `TypeError` for a `None` where Qt wants a
    `bool` or an `int`."""
    import ast
    problems = []
    for cls in ast.walk(ast.parse(source)):
        if not isinstance(cls, ast.ClassDef):
            continue
        for node in cls.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not (QT_VIRTUALS.match(node.name) or (node.name in QT_TASK_VIRTUALS and _has_base(cls, "QgsTask"))):
                continue
            where = f"`{cls.name}.{node.name}` is a Qt virtual method"
            if not _is_guarded_def(node):
                problems.append((node.lineno, f"{where} that is not guarded: decorate it with @guarded"))
            elif _has_result(node) and not _has_default(node):
                problems.append((node.lineno, f"{where} with a result that is guarded without a default: "
                                              "decorate it with @guarded(default=...)"))
            elif node.name in ("sizeHint", "minimumSizeHint") and not _is_qsize_call(_default_of(node)):
                problems.append((node.lineno, f"{where} whose default is not a QSize: PyQt raises a `TypeError` "
                                              "for another value, so use @guarded(default=QSize(-1, -1))"))
    return problems


def test_every_qt_virtual_override_is_guarded():
    _bites(rule_virtual_overrides, _src("""
        class A(QgsMapTool):
            def canvasReleaseEvent(self, event): pass
        """), _src("""
        class A(QgsMapTool):
            @guarded
            def canvasReleaseEvent(self, event): pass
        """))
    _bites(rule_virtual_overrides, _src("""
        class A(QObject):
            def eventFilter(self, obj, event): return False
        """), _src("""
        class A(QObject):
            @guarded(default=False)
            def eventFilter(self, obj, event): return False
        """))
    _bites(rule_virtual_overrides, _src("""
        class A(QObject):
            @guarded
            def eventFilter(self, obj, event): return False
        """), _src("""
        class A(QObject):
            @guarded(default=False)
            def eventFilter(self, obj, event) -> bool: return False
        """))
    _bites(rule_virtual_overrides, _src("""
        class A(QWidget):
            def event(self, event): return super().event(event)
        """), _src("""
        class A(QWidget):
            @guarded(default=False)
            def event(self, event) -> bool: return super().event(event)
        """))
    _bites(rule_virtual_overrides, _src("""
        class A(QWidget):
            @guarded
            def event(self, event) -> bool: return super().event(event)
        """), _src("""
        class A(QWidget):
            @guarded(default=False)
            def event(self, event) -> bool: return super().event(event)
        """))
    _bites(rule_virtual_overrides, _src("""
        class A(QWidget):
            @guarded
            def heightForWidth(self, width) -> int: return 1
        """), _src("""
        class A(QWidget):
            @guarded(default=-1)
            def heightForWidth(self, width) -> int: return 1
        """))
    _bites(rule_virtual_overrides, _src("""
        class A(QWidget):
            def heightForWidth(self, width): return 1
        """), _src("""
        class A(QWidget):
            @guarded(default=-1)
            def heightForWidth(self, width): return 1
        """))
    # a size method gives Qt a QSize (or a bool): its default is a QSize (or False), not None
    _bites(rule_virtual_overrides, _src("""
        class A(QWidget):
            @guarded
            def sizeHint(self) -> QSize: return QSize(1, 1)
        """), _src("""
        class A(QWidget):
            @guarded(default=QSize(-1, -1))
            def sizeHint(self) -> QSize: return QSize(1, 1)
        """))
    _bites(rule_virtual_overrides, _src("""
        class A(QWidget):
            @guarded(default=None)
            def sizeHint(self) -> QSize: return QSize(1, 1)
        """), _src("""
        class A(QWidget):
            @guarded(default=QSize(-1, -1))
            def sizeHint(self) -> QSize: return QSize(1, 1)
        """))
    _bites(rule_virtual_overrides, _src("""
        class A(QWidget):
            def minimumSizeHint(self): return QSize(1, 1)
        """), _src("""
        class A(QWidget):
            @guarded(default=QSize(-1, -1))
            def minimumSizeHint(self): return QSize(1, 1)
        """))
    _bites(rule_virtual_overrides, _src("""
        class A(QWidget):
            def hasHeightForWidth(self) -> bool: return True
        """), _src("""
        class A(QWidget):
            @guarded(default=False)
            def hasHeightForWidth(self) -> bool: return True
        """))
    _bites(rule_virtual_overrides, _src("""
        class A(QgsTask):
            def finished(self, ok): pass
        """), _src("""
        class A(QgsTask):
            @guarded
            def finished(self, ok): pass
        """))
    _bites(rule_virtual_overrides, _src("""
        class A(QgsTask):
            def cancel(self): pass
        """), _src("""
        class A(QgsTask):
            @guarded
            def cancel(self) -> None: pass
        """))
    _bites(rule_virtual_overrides, _src("""
        class A(core.QgsTask):
            def cancel(self): pass
        """), _src("""
        class A(core.QgsTask):
            @guarded
            def cancel(self): pass
        """))
    # a `cancel` of a class that is not a task is not Qt's; a void handler keeps the bare decorator
    assert not rule_virtual_overrides("class A:\n    def cancel(self): pass\n")
    assert not rule_virtual_overrides(_src("""
        class A(QWidget):
            @guarded
            def paintEvent(self, event) -> None:
                def inner(): return 1
                super().paintEvent(event)
        """))
    _bites(rule_virtual_overrides, "class A:\n    def deactivate(self): pass\n",
           "class A:\n    @guarded\n    def deactivate(self): pass\n")
    # a method of another name, and a function outside a class, are not Qt's
    assert not rule_virtual_overrides("class A:\n    def paint(self): pass\ndef keyPressEvent(e): pass\n")
    problems = _tree_problems_of(rule_virtual_overrides)
    assert not problems, "\n".join(problems)


def _tree_problems_of(rule):
    problems = []
    for path in sorted(PLUGIN.rglob("*.py")):
        name = str(path.relative_to(PLUGIN))
        problems += [f"{name}:{number}: {why}" for number, why in rule(path.read_text(encoding="utf-8"))]
    return problems


# ---------- core/origin.py: which requests may carry Mapflow credentials ----------

def _origin(url):
    from urllib.parse import urlsplit
    from mapflow_next.core.origin import Origin
    parts = urlsplit(url)
    return Origin.from_parts(parts.scheme, parts.hostname or "", parts.port if parts.port else -1)


def _carries(request, api):
    from mapflow_next.core.origin import carries_credentials
    return carries_credentials(_origin(request), _origin(api))


def test_origin_same_scheme_host_and_port_carries():
    assert _carries("https://api.example/rest/x", "https://api.example/rest")
    assert _carries("https://API.Example./a", "https://api.example/rest")


def test_origin_default_port_written_out_is_the_same_origin():
    assert _carries("https://api.example:443/x", "https://api.example")
    assert _carries("https://api.example/x", "https://api.example:443")
    assert _carries("http://127.0.0.1:80/x", "http://127.0.0.1")


def test_origin_another_port_host_or_scheme_does_not_carry():
    assert not _carries("https://api.example:8443/x", "https://api.example")
    assert not _carries("https://cdn.example/x", "https://api.example")
    assert not _carries("https://api.example.evil.example/x", "https://api.example")
    assert not _carries("http://api.example/x", "https://api.example")
    assert not _carries("http://127.0.0.1:9000/x", "http://127.0.0.1:8000")


def test_origin_of_a_relative_or_empty_url_is_none_and_never_carries():
    from mapflow_next.core.origin import Origin, carries_credentials
    assert Origin.from_parts("", "", -1) is None
    assert Origin.from_parts("https", "", -1) is None
    assert Origin.from_parts("", "api.example", -1) is None
    api = _origin("https://api.example")
    assert not carries_credentials(None, api)
    assert not carries_credentials(api, None)
    assert not carries_credentials(None, None)


def test_origin_plain_http_carries_only_on_a_local_host():
    assert not _carries("http://api.example/x", "http://api.example")
    assert not _carries("http://192.168.1.5:8000/x", "http://192.168.1.5:8000")
    assert _carries("http://127.0.0.1:8000/x", "http://127.0.0.1:8000")
    assert _carries("http://localhost:8000/x", "http://localhost:8000")
    assert _carries("http://[::1]:8000/x", "http://[::1]:8000")
    assert _carries("http://127.0.0.2:8000/x", "http://127.0.0.2:8000")


def test_origin_is_local_names():
    from mapflow_next.core.origin import is_local
    assert is_local("localhost") and is_local("LOCALHOST") and is_local("127.0.0.1") and is_local("::1")
    assert not is_local("localhost.evil.example") and not is_local("api.example") and not is_local("")
    assert not is_local("10.0.0.1")


HOSTILE_IDS = ["../../etc/passwd", "../escape", "a/b/c", "a\\b", "..", "/abs", "", "x" * 5000, "id\x00x", "\ud800"]


@pytest.mark.parametrize("image_id", HOSTILE_IDS)
def test_safe_stem_cannot_leave_the_folder(image_id, tmp_path):
    import re
    from mapflow_next.core.filenames import safe_stem
    stem = safe_stem(image_id)
    assert re.fullmatch(r"preview_[0-9a-f]{16}", stem)
    for suffix in (".png", ".jpg", ".vrt", ".tif", ".pgw"):
        assert (tmp_path / (stem + suffix)).resolve().parent == tmp_path.resolve()
        assert Path(stem + suffix).name == stem + suffix


def test_safe_stem_never_carries_the_id():
    from mapflow_next.core.filenames import safe_stem
    uuid = "6f1c2a3e-8b4d-4c5e-9f10-a1b2c3d4e5f6"
    assert uuid not in safe_stem(uuid) and "6f1c2a3e" not in safe_stem(uuid)


def test_safe_stem_is_stable_and_tells_ids_apart():
    from mapflow_next.core.filenames import safe_stem
    assert safe_stem("img-1") == safe_stem("img-1")
    assert safe_stem("a/b") != safe_stem("a_b")
    assert safe_stem("img-1") != safe_stem("img-1_0")


def test_preview_files_have_no_system_temp_folder_of_their_own():
    root = Path(__file__).resolve().parent.parent / "mapflow_next"
    assert "gettempdir" not in (root / "qgis_bridge" / "layers.py").read_text(encoding="utf-8")
    assert "gettempdir" not in (root / "plugin.py").read_text(encoding="utf-8")


# ---------- core/report.py: the text of a report (spec/006 § The report dialog) ----------

REMOVED = "[removed]"


def _environment():
    from mapflow_next.core.report import Environment
    return Environment(plugin_version="4.0.0", qgis_version="3.28.15", qt_version="5.15.3",
                       os="Linux-6.8-x86_64", env="staging")


@pytest.mark.parametrize("text, secret", [
    ("Authorization: Bearer abc123", "abc123"),
    ("authorization: Token zzz999", "zzz999"),
    ("AUTHORIZATION:xyz789", "xyz789"),
    ("sent Bearer eyfake-value now", "eyfake-value"),
    ("sent Basic dXNlcjpwYXNz now", "dXNlcjpwYXNz"),
    ('{"access_token": "AAA111", "ok": 1}', "AAA111"),
    ('{"refresh_token":"RRR222"}', "RRR222"),
    ("{'id_token': 'III333', 'x': 1}", "III333"),
    ('{"password": "pa ss 444"}', "pa ss 444"),  # pragma: allowlist secret
    ('{"client_secret": "SSS555"}', "SSS555"),  # pragma: allowlist secret
    ('{"api_key": "KKK666"}', "KKK666"),  # pragma: allowlist secret
    ("grant_type=password&password=PPP777&username=me", "PPP777"),
    ("token=TTT888 and more", "TTT888"),
    ("code=CCC999&state=s", "CCC999"),
    ('{"access_token": "CUT000', "CUT000"),                       # a body that was cut inside the value
    ("{'refresh_token': 'CUT111", "CUT111"),
    ("seen eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.c2lnbmF0dXJl here", "eyJhbGciOiJIUzI1NiJ9"),  # pragma: allowlist secret
    ("cut eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOi", "eyJzdWIiOi"),
])
def test_redact_removes_each_kind_of_secret(text, secret):
    from mapflow_next.core.report import redact
    assert secret in text
    out = redact(text)
    assert secret not in out and REMOVED in out


@pytest.mark.parametrize("text, secret, kept", [
    ("GET https://s3.example.com/a/b.tif?X-Amz-Signature=SIG123&X-Amz-Date=D", "SIG123",
     "https://s3.example.com/a/b.tif"),
    ("GET https://s3.example.com/a/b.tif?plain=Q42", "Q42", "https://s3.example.com/a/b.tif"),
    ("redirect https://app.example.com/cb#access_token=FRAG5", "FRAG5", "https://app.example.com/cb"),
])
def test_redact_cuts_the_query_and_fragment_of_a_url(text, secret, kept):
    from mapflow_next.core.report import redact
    out = redact(text)
    assert secret not in out and kept in out and "?" not in out and "#" not in out


def test_redact_keeps_the_words_around_a_secret():
    from mapflow_next.core.report import redact
    out = redact('{"access_token": "AAA", "name": "Roads", "count": 3} for https://h.io/p/q?x=1 failed')
    assert '"name": "Roads"' in out and '"count": 3' in out and out.endswith("https://h.io/p/q failed")
    assert redact("Authorization: Bearer abc\nnext line stays").endswith("next line stays")
    assert "Authorization:" not in redact("Authorization: Bearer abc")
    assert redact("Processing failed: area is too large (status 422)") == \
        "Processing failed: area is too large (status 422)"


def test_redact_keeps_an_api_error_code():
    from mapflow_next.core.report import redact
    body = '{"code": "processing.blocksNotAvailable", "message": "No blocks"}'
    assert redact(body) == body


def test_redact_removes_the_literals_it_is_given():
    from mapflow_next.core.report import redact
    out = redact("the session held AbCdEf-literal-token in a place no pattern knows",
                 secrets=("AbCdEf-literal-token", ""))
    assert "AbCdEf" not in out and out.startswith("the session held") and REMOVED in out
    assert redact("no change", secrets=("",)) == "no change"


def test_redact_twice_is_the_same_as_once():
    from mapflow_next.core.report import redact
    once = redact('Authorization: Bearer A\n{"password": "B"} https://h.io/p?q=1 eyJabcdefghijk.l.m')
    assert redact(once) == once


def test_without_query_cuts_at_the_question_mark():
    from mapflow_next.core.report import without_query
    assert without_query("https://h.io/a/b?x=1&y=2") == "https://h.io/a/b"
    assert without_query("https://h.io/a/b") == "https://h.io/a/b"


def test_summary_is_one_short_line_without_secrets():
    from mapflow_next.core.report import summary_of
    text = summary_of(ValueError("line one\nline two  with   gaps"))
    assert text == "ValueError: line one line two with gaps"
    assert "\n" not in summary_of(ValueError("a\r\nb"))
    long = summary_of(ValueError("x" * 1000))
    assert len(long) <= 201 and long.endswith("…")
    out = summary_of(ValueError("bad header Authorization: Bearer BBB"))
    assert "BBB" not in out and out.startswith("ValueError: bad header")


def test_summary_from_strings_is_the_summary_of_the_exception():
    from mapflow_next.core.report import summary_from, summary_of
    exc = ValueError("a\nb  Authorization: Bearer BBB")
    assert summary_from("ValueError", str(exc)) == summary_of(exc)
    assert "TOKEN" not in summary_from("KeyError", "has TOKEN inside", ["TOKEN"])


def _failed_request():
    from mapflow_next.core.report import RequestInfo
    body = ('{"access_token": "AAA", "refresh_token": "RRR", '
            '"password": "PPP", "rest": "kept-text"}')  # pragma: allowlist secret
    return RequestInfo("GET", "https://api.example.com/rest/user/status?X-Amz-Signature=SECRET&token=T", 200, body)


def test_a_request_report_has_the_request_and_no_secret():
    from mapflow_next.core.report import summary_of, technical_text
    try:
        raise ValueError("callback broke on Authorization: Bearer BBB")
    except ValueError as exc:
        details = "GET https://api.example.com/rest/user/status: on_success\n" + "".join(
            __import__("traceback").format_exception(type(exc), exc, exc.__traceback__))
        text = technical_text(summary_of(exc), details, _failed_request(), _environment())
    for secret in ("SECRET", "AAA", "RRR", "PPP", "BBB"):
        assert secret not in text, secret
    assert "token=T" not in text and "?" not in text.split("Response body:")[0].split("Request:")[1].split("\n")[0]
    assert "Authorization:" not in text
    assert "Request: GET https://api.example.com/rest/user/status\n" in text
    assert "HTTP status: 200" in text
    assert "Response body:" in text and "kept-text" in text
    assert "ValueError" in text and "Traceback" in text


def test_a_report_without_a_request_has_no_request_lines():
    from mapflow_next.core.report import technical_text
    text = technical_text("ZeroDivisionError: division by zero", "Page.slot\nTraceback ...", None, _environment())
    assert "Request:" not in text and "HTTP status" not in text and "Response body" not in text
    assert text.startswith("ZeroDivisionError: division by zero")
    assert "Traceback" in text


def test_a_report_names_the_plugin_qgis_qt_os_and_environment():
    from mapflow_next.core.report import technical_text
    text = technical_text("E: x", "", None, _environment())
    for part in ("4.0.0", "3.28.15", "5.15.3", "Linux-6.8-x86_64", "staging"):
        assert part in text, part


def test_the_response_body_is_redacted_before_it_is_cut():
    from mapflow_next.core.report import RequestInfo, technical_text
    body = "x" * 1990 + ' "access_token": "TOKENTOKENTOKEN" ' + "y" * 500
    text = technical_text("E: x", "", RequestInfo("POST", "https://h.io/a", 500, body), _environment())
    assert "TOKENTOKEN" not in text and "TOKEN" not in text.replace("access_token", "")
    shown = text.split("Response body:\n")[1]
    assert "[cut]" in shown and len(shown.split("[cut]")[0]) <= 2100
    short = technical_text("E: x", "", RequestInfo("POST", "https://h.io/a", 500, "short body"), _environment())
    assert "short body" in short and "[cut]" not in short


def test_the_literal_secrets_of_the_session_are_removed_from_a_report():
    from mapflow_next.core.report import RequestInfo, technical_text
    text = technical_text("E: x", "trace with SESSIONVALUE in it",
                          RequestInfo("GET", "https://h.io/a", 200, "body SESSIONVALUE"), _environment(),
                          secrets=("SESSIONVALUE",))
    assert "SESSIONVALUE" not in text


def test_the_comment_goes_above_the_technical_part():
    from mapflow_next.core.report import compose
    out = compose("  I pressed Run twice.  \n", "ValueError: x\nTraceback")
    assert out == "I pressed Run twice.\n\nValueError: x\nTraceback"
    assert compose("", "ValueError: x") == "ValueError: x"
    assert compose("  \n ", "ValueError: x") == "ValueError: x"


def test_mailto_carries_the_address_a_one_line_subject_and_the_body():
    from urllib.parse import parse_qs, unquote, urlsplit
    from mapflow_next.core.report import mailto
    body = "Comment & more #1 100% a+b ünï ☃\n\nLine 2\nLine 3"
    link = mailto("help@example.io", "Mapflow Next 4.0.0: E\nsecond line", body)
    assert link.startswith("mailto:help@example.io?subject=")
    parts = urlsplit(link)
    assert parts.scheme == "mailto" and unquote(parts.path) == "help@example.io"
    query = parse_qs(parts.query, keep_blank_values=True)
    assert set(query) == {"subject", "body"}
    assert query["subject"] == ["Mapflow Next 4.0.0: E second line"]
    assert query["body"] == [body.replace("\n", "\r\n")]
    encoded = link.split("?", 1)[1]
    assert "\n" not in link and " " not in link and "#" not in link and encoded.count("&") == 1


def test_the_mailto_subject_is_cut():
    from urllib.parse import parse_qs, urlsplit
    from mapflow_next.core.report import mailto
    subject = parse_qs(urlsplit(mailto("a@b.io", "S" * 500, "b")).query)["subject"][0]
    assert len(subject) <= 100


def test_the_guard_passes_the_request_to_the_reporter(reporter):
    from mapflow_next.core import guard
    from mapflow_next.core.report import RequestInfo
    request = RequestInfo("GET", "https://h.io/a", 200, "ok")
    guard.report(ValueError("x"), "where", request)
    guard.report(ValueError("y"), "elsewhere")
    assert reporter[0][2] is request and reporter[1][2] is None
    assert reporter[0][1].startswith("where\n")


def rule_report_dialog_is_opened_only_by_the_plugin(source):
    import ast
    problems = []
    for node in ast.walk(ast.parse(source)):
        names = ([alias.name for alias in node.names] if isinstance(node, (ast.Import, ast.ImportFrom)) else [])
        names += [node.id] if isinstance(node, ast.Name) else [node.attr] if isinstance(node, ast.Attribute) else []
        names += [node.module or ""] if isinstance(node, ast.ImportFrom) else []
        if any(name == "ReportDialog" or name.endswith(".report_dialog") or name == "report_dialog"
               for name in names):
            problems.append((node.lineno, "only plugin.py opens the report dialog: it is the user's button"))
    return sorted(set(problems))


def test_only_the_report_button_opens_the_report_dialog():
    _bites(rule_report_dialog_is_opened_only_by_the_plugin,
           "from .ui.report_dialog import ReportDialog\n", "from .ui.dock import MapflowDock\n")
    _bites(rule_report_dialog_is_opened_only_by_the_plugin,
           "dialog = ReportDialog(a, b)\n", "dialog = RenameDialog()\n")
    _bites(rule_report_dialog_is_opened_only_by_the_plugin,
           "from .ui import report_dialog\n", "from .ui import rename_dialog\n")
    problems = []
    for path in sorted(PLUGIN.rglob("*.py")):
        name = str(path.relative_to(PLUGIN))
        if name in ("plugin.py", "ui/report_dialog.py"):
            continue
        problems += [f"{name}:{number}: {why}" for number, why in
                     rule_report_dialog_is_opened_only_by_the_plugin(path.read_text(encoding="utf-8"))]
    assert not problems, "\n".join(problems)
    assert "ReportDialog" in (PLUGIN / "plugin.py").read_text(encoding="utf-8")


# ---------- download an original image (spec/002_C § GET /rasters/image/{image_id}/download) ----------

@pytest.mark.parametrize("data, expected", [
    ({"id": "i"}, True),                                       # the field is absent: downloadable
    ({"id": "i", "available_for_download": None}, True),       # null counts as absent
    ({"id": "i", "available_for_download": True}, True),
    ({"id": "i", "available_for_download": False}, False),
])
def test_image_is_downloadable_unless_the_api_says_not(data, expected):
    from mapflow_next.core.models import MosaicImage
    assert MosaicImage.from_api(data).available_for_download is expected


def test_image_download_link_from_the_answer():
    from mapflow_next.core.models import ImageDownload
    link = ImageDownload.from_api({"download_url": "https://s3.example/a?sig=1", "filename": "a.tif",
                                   "expires_in": 3600})
    assert (link.url, link.filename, link.expires_in) == ("https://s3.example/a?sig=1", "a.tif", 3600)
    empty = ImageDownload.from_api({})
    assert (empty.url, empty.filename, empty.expires_in) == ("", "", 0)
    assert ImageDownload.from_api({"download_url": None, "filename": None, "expires_in": None}).url == ""


@pytest.mark.parametrize("name, expected", [
    ("beirut_0.5m.tif", "beirut_0.5m.tif"),
    ("../../etc/passwd", "passwd"),
    ("C:\\Users\\me\\scene.tif", "scene.tif"),
    ("dir/sub\\scene.tif", "scene.tif"),
    ("a\x00b\x1f.tif", "ab.tif"),
    ('we<ir>d:"na|me?*.tif', "weirdname.tif"),
    ("  ..scene.tif.. ", "scene.tif"),
    ("..", "image.tif"),
    ("", "image.tif"),
    ("dir/", "image.tif"),
    ("   ", "image.tif"),
])
def test_safe_filename_keeps_only_a_plain_name(name, expected):
    from mapflow_next.core.filenames import safe_filename
    assert safe_filename(name, "image.tif") == expected


def test_safe_filename_cleans_its_fallback_too_and_never_returns_empty():
    from mapflow_next.core.filenames import safe_filename
    assert safe_filename("", "../other.tif") == "other.tif"
    assert safe_filename("..", "") == "download"
    assert safe_filename(None, None) == "download"


@pytest.mark.parametrize("step, status, expected", [
    ("link", 403, "This image can't be downloaded."),
    ("link", 404, "The image wasn't found. It may have been deleted."),
    ("link", 409, "The image isn't ready for download yet. Try again later."),
    ("file", 403, "The download link was refused or has expired. Try again."),
    ("file", 404, "The download link was refused or has expired. Try again."),
    ("file", 409, "the fallback"),
    ("link", 500, "the fallback"),
    ("link", None, "the fallback"),
    ("file", None, "the fallback"),
])
def test_image_download_failure_texts(step, status, expected):
    from mapflow_next.core.messages import image_download_failure
    assert image_download_failure(step, status, "the fallback") == expected
