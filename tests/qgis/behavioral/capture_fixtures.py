"""Capture real Mapflow API responses as fixtures for the behavioral tests.

Run by a human, not by CI — it needs a live account and a real token.

    export MAPFLOW_TOKEN='<the same base64 token the plugin stores in settings>'
    python3 tests/qgis/behavioral/capture_fixtures.py

Writes scrubbed JSON into ``responses/`` next to this file. **Review the output before
committing it** — the scrubber is deliberate about what it knows to remove, and a payload
shape nobody has seen before may carry something it does not recognise.

Why real responses: the behavioral tests exist to prove a refactoring changed nothing. If the
canned payloads are hand-written from the spec, they only contain fields we already knew
about, and the tests cannot catch "the parsing broke on a field the server actually sends".

No IDs are hardcoded. Every id is discovered from an earlier response — list projects, take an
id, fetch that project, and so on — so the script works against any account.

Safety: every request here is read-only except the two opt-in failure captures, and even those
are shaped to be rejected. Nothing is created, updated or deleted without ``--include-create-
failure``, which prints a warning first.
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SERVER_TEMPLATE = "https://whitemaps-{env}.mapflow.ai/rest"
OUT_DIR = Path(__file__).parent / "responses"
TIMEOUT_SECONDS = 60

# A small AOI over open water, so a search returns few or no results and a cost request is
# cheap. Deliberately not a populated area: this script runs against a real account.
SMALL_AOI = {
    "type": "Polygon",
    "coordinates": [[
        [0.0, 51.0], [0.01, 51.0], [0.01, 51.01], [0.0, 51.01], [0.0, 51.0],
    ]],
}

UUID_RE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
EMAIL_RE = re.compile(r"[^\s@]+@[^\s@]+\.[^\s@]+")

#: Values under these keys are replaced wholesale — they identify a person or authorise access.
PII_KEYS = {
    "email", "userEmail", "login", "username", "password", "token", "accessToken",
    "refreshToken", "firstName", "lastName", "phone", "secret", "apiKey",
}

#: Query parameters whose name contains any of these carry a credential. Matched on the
#: parameter, not on the key the URL is stored under: an earlier version listed the keys it
#: knew about (`url`, `previewUrl`, ...) and a real Mapbox token walked straight through in a
#: `webPreviewUrl` that was not on the list. Any URL-shaped value is now inspected, and the
#: rest of the query is preserved so the fixture stays a realistic URL.
SECRET_QUERY_MARKERS = ("token", "key", "secret", "signature", "password", "credential",
                        "auth", "sig", "x-amz-")

#: How many entries to keep in the arrays that dominate response size. A real account returns
#: 15 workflow defs and 98 mosaics; keeping them makes a 400 KB fixture that nobody reads and
#: that tells the tests nothing the first few entries do not.
#: Trimming lives here rather than in a manual pass, so re-capturing after an API change
#: reproduces the same small fixtures instead of restoring the bulk.
LIST_CAPS = {
    "workflowDefs": 4,
    "models": 4,
    "dataProviders": 2,
    "searchDataProviders": 2,
    "results": 3,
    "images": 5,
    "previews": 3,
    "aois": 3,
}

#: Cap for an endpoint whose whole body is a list (mosaics returns ~100).
TOP_LEVEL_LIST_CAP = 5

#: Kept in preference to whatever happens to sort first. Truncating blindly can drop
#: `Config.DEFAULT_MODEL` or every model that `styles.py` has a .qml for, which would leave
#: the processing and result-loading journeys unable to exercise the paths they exist for.
PREFERRED_NAMES = {
    "🏠 Buildings",
    "🌲 Forest",
    "🌲 Forest and trees",
    "🚗 Roads",
    "🏗️ Construction sites",
}


def trim(node, key=None):
    """Shorten the bulky repeated arrays, keeping the entries the tests care about."""
    if isinstance(node, dict):
        out = {k: trim(v, key=k) for k, v in node.items()}
        # `count` states how many entries this page carries; leave `total` alone, since a
        # short page of a large total is exactly what the pagination paths must handle.
        if isinstance(out.get("results"), list) and "count" in out:
            out["count"] = len(out["results"])
        return out
    if isinstance(node, list):
        trimmed = [trim(v, key=key) for v in node]
        cap = LIST_CAPS.get(key)
        if cap is not None and len(trimmed) > cap:
            return _pick(trimmed, cap)
        return trimmed
    return node


def _pick(items, cap):
    preferred = [i for i in items
                 if isinstance(i, dict) and i.get("name") in PREFERRED_NAMES]
    rest = [i for i in items if i not in preferred]
    return (preferred + rest)[:cap]


class Scrubber:
    """Replaces identifying values consistently across every captured file.

    Consistency matters: a project id in the project list must still match the id in the
    project detail response, or the fixtures cannot be used together in one test.
    """

    def __init__(self):
        self._ids = {}
        self._emails = {}
        self.report = {"uuids": 0, "emails": 0, "pii_values": 0, "urls_stripped": 0}

    def fake_uuid(self, real: str) -> str:
        if real not in self._ids:
            n = len(self._ids) + 1
            self._ids[real] = "00000000-0000-4000-8000-{:012d}".format(n)
            self.report["uuids"] += 1
        return self._ids[real]

    def fake_email(self, real: str) -> str:
        if real not in self._emails:
            n = len(self._emails) + 1
            self._emails[real] = "user{}@example.com".format(n)
            self.report["emails"] += 1
        return self._emails[real]

    def _scrub_string(self, value: str) -> str:
        value = UUID_RE.sub(lambda m: self.fake_uuid(m.group(0)), value)
        value = EMAIL_RE.sub(lambda m: self.fake_email(m.group(0)), value)
        return value

    def strip_url_secrets(self, value: str) -> str:
        """Drop credential-bearing query parameters, keep the rest of the URL intact."""
        if "://" not in value or "?" not in value:
            return value
        base, _, query = value.partition("?")
        kept, dropped = [], False
        for name, raw in urllib.parse.parse_qsl(query, keep_blank_values=True):
            if any(marker in name.lower() for marker in SECRET_QUERY_MARKERS):
                kept.append((name, "scrubbed"))
                dropped = True
            else:
                kept.append((name, raw))
        if dropped:
            self.report["urls_stripped"] += 1
        return base + "?" + urllib.parse.urlencode(kept) if kept else base

    def scrub(self, node, key=None):
        if isinstance(node, dict):
            return {k: self.scrub(v, key=k) for k, v in node.items()}
        if isinstance(node, list):
            return [self.scrub(v, key=key) for v in node]
        if isinstance(node, str):
            if key in PII_KEYS:
                self.report["pii_values"] += 1
                return self.fake_email(node) if "@" in node else "redacted"
            return self._scrub_string(self.strip_url_secrets(node))
        return node


def build_request(url: str, token: str, method: str, body=None) -> urllib.request.Request:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("authorization", "Basic {}".format(token))
    request.add_header("x-plugin-version", "fixture-capture")
    if data is not None:
        request.add_header("content-type", "application/json")
    return request


def call(url: str, token: str, method: str = "GET", body=None):
    """Return (status, parsed_body). Never raises for an HTTP error — a rejection is a
    fixture we want, not a failure of the script."""
    try:
        with urllib.request.urlopen(build_request(url, token, method, body),
                                    timeout=TIMEOUT_SECONDS) as response:
            raw = response.read().decode("utf-8", "replace")
            return response.status, parse(raw)
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", "replace")
        return error.code, parse(raw)
    except urllib.error.URLError as error:
        print("  ! network error: {}".format(error))
        return None, None


def parse(raw: str):
    try:
        return json.loads(raw)
    except ValueError:
        return {"__raw__": raw[:2000]}


class Capture:
    def __init__(self, server: str, token: str, scrubber: Scrubber):
        self.server = server
        self.token = token
        self.scrubber = scrubber
        self.saved = []
        self.skipped = []

    def get(self, name: str, path: str):
        return self._do(name, path, "GET", None)

    def post(self, name: str, path: str, body):
        return self._do(name, path, "POST", body)

    def _do(self, name: str, path: str, method: str, body):
        url = "{}/{}".format(self.server, path.lstrip("/"))
        print("  {} {}".format(method, path))
        status, payload = call(url, self.token, method, body)
        if status is None:
            self.skipped.append((name, "network error"))
            return None
        self.save(name, {
            "request": {"method": method, "path": path, "body": body},
            "status": status,
            "body": payload,
        })
        return payload

    def save(self, name: str, envelope: dict):
        """Write the trimmed, scrubbed fixture.

        The caller keeps the *untrimmed* payload: requests are made wide on purpose (a
        hundred projects, so there is a chance of finding one with processings in it) and
        saved narrow. Mutating the envelope here would hand the caller the truncated copy
        and defeat that.
        """
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        scrubbed = self.scrubber.scrub(envelope)
        body = scrubbed.get("body")
        if isinstance(body, list) and len(body) > TOP_LEVEL_LIST_CAP:
            scrubbed = dict(scrubbed, body=body[:TOP_LEVEL_LIST_CAP])
        target = OUT_DIR / "{}.json".format(name)
        target.write_text(json.dumps(trim(scrubbed), indent=2, ensure_ascii=False) + "\n")
        self.saved.append((name, envelope.get("status")))


def first_id(payload, *keys):
    """Pull an id out of a list-or-page response without knowing which shape it is."""
    if payload is None:
        return None
    items = payload
    if isinstance(payload, dict):
        for key in ("results", "content", "items", "data"):
            if isinstance(payload.get(key), list):
                items = payload[key]
                break
        else:
            items = [payload]
    if not isinstance(items, list):
        return None
    for item in items:
        if not isinstance(item, dict):
            continue
        for key in keys:
            if item.get(key):
                return item[key]
    return None


def counts(project) -> dict:
    """`processingCounts` as a dict, whatever shape the API reports it in."""
    value = (project or {}).get("processingCounts")
    if isinstance(value, dict):
        return value
    if isinstance(value, int):
        return {"total": value}
    return {}


def pick_project(projects, predicate):
    for project in projects:
        if isinstance(project, dict) and predicate(project):
            return project
    return None


def find_by_status(payload, wanted):
    """First item whose status matches — used to capture a genuinely failed processing."""
    if not isinstance(payload, dict):
        return None
    for item in payload.get("results") or []:
        if isinstance(item, dict) and str(item.get("status", "")).upper() == wanted:
            return item
    return None


def preferred_workflow_def(payload):
    """A workflow-def id to price against, favouring the default model.

    The cost and create endpoints key on `wdId`, not on the model name, so the id has to come
    out of a response like every other id here.
    """
    defs = (payload or {}).get("workflowDefs") or []
    for wanted in ("🏠 Buildings",):
        for entry in defs:
            if isinstance(entry, dict) and entry.get("name") == wanted:
                return entry.get("id")
    for entry in defs:
        if isinstance(entry, dict) and entry.get("id"):
            return entry["id"]
    return None


def run(capture: Capture, include_create_failure: bool):
    print("\n-- account --")
    login = capture.get("login_projects_default", "projects/default")
    capture.get("user_status", "user/status")
    capture.get("version", "version")
    wd_id = preferred_workflow_def(login)
    default_project_id = (login or {}).get("id")

    print("\n-- projects --")
    # Asked wide, saved narrow. The most recently updated projects tend to be empty test
    # projects, so taking the first one yields fixtures with no processings and no templates
    # — which is exactly the data the journeys need.
    projects = capture.post("projects_page", "projects/page", {
        "limit": 100, "offset": 0, "sortBy": "UPDATED", "sortOrder": "DESC",
    })
    all_projects = (projects or {}).get("results") or []
    if not all_projects:
        capture.skipped.append(("project_detail", "no projects on this account"))
        return

    work_project = pick_project(all_projects, lambda p: counts(p).get("total", 0) > 0)
    failed_project = pick_project(all_projects, lambda p: counts(p).get("failed", 0) > 0)
    template_project = pick_project(all_projects, lambda p: (p.get("templatesCount") or 0) > 0)

    project_id = (work_project or all_projects[0]).get("id")
    capture.get("project_detail", "projects/{}".format(project_id))

    print("\n-- processings --")
    if work_project:
        processings = capture.post(
            "processings_page", "projects/{}/processings/v2/page".format(project_id),
            {"limit": 20, "offset": 0})
        processing_id = first_id(processings, "id")
        if processing_id:
            capture.get("processing_detail", "processings/{}/v2".format(processing_id))
            capture.get("processing_aois", "processings/{}/aois".format(processing_id))
    else:
        processings = None
        capture.skipped.append(
            ("processings_page", "no project on this account reports any processings"))

    print("\n-- failed processing --")
    failed = find_by_status(processings, "FAILED")
    if not failed and failed_project and failed_project.get("id") != project_id:
        # The failures live in a different project from the one with the most processings.
        other = capture.post(
            "processings_page_failed",
            "projects/{}/processings/v2/page".format(failed_project["id"]),
            {"limit": 20, "offset": 0})
        failed = find_by_status(other, "FAILED")
    if failed and failed.get("id"):
        capture.get("processing_detail_failed", "processings/{}/v2".format(failed["id"]))
    else:
        capture.skipped.append(
            ("processing_detail_failed", "no FAILED processing found on this account"))

    print("\n-- templates --")
    if template_project:
        templates = capture.get(
            "templates_by_project",
            "processings/template/project/{}".format(template_project["id"]))
        template_id = first_id(templates, "id")
        if template_id:
            capture.get("template_detail", "processings/template/{}".format(template_id))
            capture.get("template_processings",
                        "processings/template/{}/processings".format(template_id))
            capture.get("template_images",
                        "processings/template/{}/images".format(template_id))
    else:
        capture.skipped.append(
            ("templates_by_project", "no project on this account reports any templates"))

    print("\n-- my imagery --")
    capture.get("rasters_memory", "rasters/memory")
    mosaics = capture.get("mosaics", "rasters/mosaic")
    mosaic_list = mosaics if isinstance(mosaics, list) else []
    captured_images = False
    # The first mosaic is often empty; walk a few until one actually holds an image, so the
    # My Imagery journey has a populated table to render.
    for mosaic in mosaic_list[:10]:
        if not isinstance(mosaic, dict) or not mosaic.get("id"):
            continue
        images = capture.get("mosaic_images",
                             "rasters/mosaic/{}/image".format(mosaic["id"]))
        image_id = first_id(images, "id")
        if image_id:
            capture.get("mosaic_detail", "rasters/mosaic/{}".format(mosaic["id"]))
            capture.get("image_detail", "rasters/image/{}".format(image_id))
            captured_images = True
            break
    if not mosaic_list:
        capture.skipped.append(("mosaic_detail", "no mosaics on this account"))
    elif not captured_images:
        capture.skipped.append(
            ("image_detail", "none of the first 10 mosaics contains an image"))

    print("\n-- imagery search --")
    capture.post("search_meta", "catalog/meta", {
        "aoi": SMALL_AOI, "limit": 20, "offset": 0, "hideUnavailable": False,
    })
    print("\n-- imagery search, rejected --")
    capture.post("search_meta_rejected", "catalog/meta", {
        "aoi": {"type": "Polygon", "coordinates": []}, "limit": 20, "offset": 0,
    })

    if not wd_id:
        capture.skipped.append(("processing_cost", "no workflowDefs in projects/default"))
        return

    def cost_body(workflow_def_id, geometry):
        return {
            "name": "fixture-capture",
            "description": "",
            "projectId": default_project_id or project_id,
            "wdId": workflow_def_id,
            "geometry": geometry,
            "params": {"sourceParams": {"dataProvider": {"providerName": "Mapbox",
                                                         "zoom": "17"}}},
            "meta": {"source-app": "qgis"},
            "blocks": [],
        }

    print("\n-- processing cost --")
    capture.post("processing_cost", "processing/cost/v2", cost_body(wd_id, SMALL_AOI))
    print("\n-- processing cost, rejected --")
    capture.post("processing_cost_rejected", "processing/cost/v2",
                 cost_body("00000000-0000-0000-0000-000000000000", SMALL_AOI))

    if include_create_failure:
        print("\n-- processing create, rejected (opt-in) --")
        capture.post("processing_create_rejected", "processings/v2",
                     cost_body("00000000-0000-0000-0000-000000000000",
                               {"type": "Polygon", "coordinates": []}))
    else:
        capture.skipped.append(
            ("processing_create_rejected", "not requested; pass --include-create-failure"))


def strip_secrets_in_place(node, scrubber: Scrubber):
    """Re-run only the URL-secret stripping over an already-scrubbed payload.

    Safe to repeat, unlike the rest of scrubbing: removing a credential-bearing query
    parameter twice is a no-op, whereas re-running the id and email replacement would remap
    the already-anonymised values and break the cross-file references the fixtures rely on.
    """
    if isinstance(node, dict):
        return {k: strip_secrets_in_place(v, scrubber) for k, v in node.items()}
    if isinstance(node, list):
        return [strip_secrets_in_place(v, scrubber) for v in node]
    if isinstance(node, str):
        return scrubber.strip_url_secrets(node)
    return node


def retrim() -> int:
    """Re-apply the size caps and the URL-secret stripping to fixtures already on disk.

    No network, and no id or email re-scrubbing — see strip_secrets_in_place.
    """
    files = sorted(OUT_DIR.glob("*.json"))
    if not files:
        print("nothing in {}".format(OUT_DIR))
        return 1
    scrubber = Scrubber()
    total_before = total_after = 0
    for path in files:
        before = path.stat().st_size
        payload = json.loads(path.read_text())
        body = payload.get("body")
        if isinstance(body, list) and len(body) > TOP_LEVEL_LIST_CAP:
            payload["body"] = body[:TOP_LEVEL_LIST_CAP]
        payload = strip_secrets_in_place(trim(payload), scrubber)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        after = path.stat().st_size
        total_before += before
        total_after += after
        marker = "" if after == before else "  <- changed"
        print("  {:<34} {:>9,} -> {:>9,} B{}".format(path.name, before, after, marker))
    print("\n  {:<34} {:>9,} -> {:>9,} B".format("total", total_before, total_after))
    print("  url query params scrubbed: {}".format(scrubber.report["urls_stripped"]))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--env", default=os.environ.get("MAPFLOW_ENV", "production"),
                        help="backend environment, as in the plugin's mapflow_env setting")
    parser.add_argument("--include-create-failure", action="store_true",
                        help="also POST a deliberately invalid processing to capture the "
                             "rejection envelope. Shaped to be refused, but it is the only "
                             "non-read-only call in this script.")
    parser.add_argument("--retrim", action="store_true",
                        help="re-apply the size caps to the fixtures already on disk and "
                             "exit. No network access, no token needed.")
    args = parser.parse_args()

    if args.retrim:
        return retrim()

    token = os.environ.get("MAPFLOW_TOKEN")
    if not token:
        print("MAPFLOW_TOKEN is not set.\n\n"
              "Use the same base64 token the plugin stores — in QGIS it is under\n"
              "Settings > Options > Advanced > mapflow/token, or copy it from\n"
              "https://app.mapflow.ai/account/api\n\n"
              "    export MAPFLOW_TOKEN='...'")
        return 2

    server = SERVER_TEMPLATE.format(env=args.env)
    print("server: {}".format(server))
    if args.include_create_failure:
        print("\nWARNING: --include-create-failure sends one POST to processings/v2.\n"
              "It uses a nonexistent model and an empty geometry so the server refuses it.\n"
              "If your backend accepts it anyway, a processing would be created.\n")
        if input("continue? [y/N] ").strip().lower() != "y":
            return 1

    scrubber = Scrubber()
    capture = Capture(server, token, scrubber)
    run(capture, args.include_create_failure)

    print("\n=== saved {} file(s) to {} ===".format(len(capture.saved), OUT_DIR))
    for name, status in capture.saved:
        print("  {:<32} HTTP {}".format(name, status))
    if capture.skipped:
        print("\n=== skipped ===")
        for name, why in capture.skipped:
            print("  {:<32} {}".format(name, why))
    print("\n=== scrubbed ===")
    for key, count in scrubber.report.items():
        print("  {:<16} {}".format(key, count))
    print("\nRead the files before committing. The scrubber removes what it recognises;\n"
          "a field shape it has not seen is passed through unchanged.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
