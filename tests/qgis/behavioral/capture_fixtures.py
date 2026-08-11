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

#: Query strings are stripped from values under these keys: presigned S3 links carry an AWS
#: signature, and detect-secrets rightly objects to one landing in the repo.
URL_KEYS = {"url", "downloadUrl", "previewUrl", "tileUrl", "link", "href"}


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

    def scrub(self, node, key=None):
        if isinstance(node, dict):
            return {k: self.scrub(v, key=k) for k, v in node.items()}
        if isinstance(node, list):
            return [self.scrub(v, key=key) for v in node]
        if isinstance(node, str):
            if key in PII_KEYS:
                self.report["pii_values"] += 1
                return self.fake_email(node) if "@" in node else "redacted"
            if key in URL_KEYS and "?" in node:
                self.report["urls_stripped"] += 1
                return self._scrub_string(node.split("?", 1)[0]) + "?scrubbed=1"
            return self._scrub_string(node)
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
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        scrubbed = self.scrubber.scrub(envelope)
        target = OUT_DIR / "{}.json".format(name)
        target.write_text(json.dumps(scrubbed, indent=2, ensure_ascii=False) + "\n")
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


def find_by_status(payload, wanted):
    """First item whose status matches — used to capture a genuinely failed processing."""
    if not isinstance(payload, dict):
        return None
    for item in payload.get("results") or []:
        if isinstance(item, dict) and str(item.get("status", "")).upper() == wanted:
            return item
    return None


def run(capture: Capture, include_create_failure: bool):
    print("\n-- account --")
    capture.get("login_projects_default", "projects/default")
    capture.get("user_status", "user/status")
    capture.get("version", "version")

    print("\n-- projects --")
    projects = capture.post("projects_page", "projects/page", {
        "limit": 20, "offset": 0, "sortBy": "UPDATED", "sortOrder": "DESC",
    })
    project_id = first_id(projects, "id")
    if not project_id:
        capture.skipped.append(("project_detail", "no projects on this account"))
        return
    capture.get("project_detail", "projects/{}".format(project_id))

    print("\n-- processings --")
    processings = capture.post(
        "processings_page", "projects/{}/processings/v2/page".format(project_id),
        {"limit": 20, "offset": 0})
    processing_id = first_id(processings, "id")
    if processing_id:
        capture.get("processing_detail", "processings/{}/v2".format(processing_id))
        capture.get("processing_aois", "processings/{}/aois".format(processing_id))
    else:
        capture.skipped.append(("processing_detail", "no processings in this project"))

    failed = find_by_status(processings, "FAILED")
    if failed and failed.get("id"):
        print("\n-- failed processing (real) --")
        capture.get("processing_detail_failed", "processings/{}/v2".format(failed["id"]))
    else:
        capture.skipped.append(
            ("processing_detail_failed",
             "no FAILED processing found in the first page of this project"))

    print("\n-- templates --")
    templates = capture.get("templates_by_project",
                            "processings/template/project/{}".format(project_id))
    template_id = first_id(templates, "id")
    if template_id:
        capture.get("template_detail", "processings/template/{}".format(template_id))
        capture.get("template_processings",
                    "processings/template/{}/processings".format(template_id))
        capture.get("template_images", "processings/template/{}/images".format(template_id))
    else:
        capture.skipped.append(("template_detail", "no templates in this project"))

    print("\n-- my imagery --")
    capture.get("rasters_memory", "rasters/memory")
    mosaics = capture.get("mosaics", "rasters/mosaic")
    mosaic_id = first_id(mosaics, "id")
    if mosaic_id:
        capture.get("mosaic_detail", "rasters/mosaic/{}".format(mosaic_id))
        images = capture.get("mosaic_images", "rasters/mosaic/{}/image".format(mosaic_id))
        image_id = first_id(images, "id")
        if image_id:
            capture.get("image_detail", "rasters/image/{}".format(image_id))
    else:
        capture.skipped.append(("mosaic_detail", "no mosaics on this account"))

    print("\n-- imagery search --")
    capture.post("search_meta", "catalog/meta", {
        "aoi": SMALL_AOI, "limit": 20, "offset": 0, "hideUnavailable": False,
    })
    print("\n-- imagery search, rejected --")
    capture.post("search_meta_rejected", "catalog/meta", {
        "aoi": {"type": "Polygon", "coordinates": []}, "limit": 20, "offset": 0,
    })

    print("\n-- processing cost --")
    capture.post("processing_cost", "processing/cost/v2", {
        "workflowDef": "🏠 Buildings",
        "geometry": SMALL_AOI,
        "processingParams": {"sourceParams": {"data_provider": "Mapflow"}},
    })
    print("\n-- processing cost, rejected --")
    capture.post("processing_cost_rejected", "processing/cost/v2", {
        "workflowDef": "__no_such_model__",
        "geometry": SMALL_AOI,
    })

    if include_create_failure:
        print("\n-- processing create, rejected (opt-in) --")
        capture.post("processing_create_rejected", "processings/v2", {
            "name": "fixture-capture-should-be-rejected",
            "workflowDef": "__no_such_model__",
            "geometry": {"type": "Polygon", "coordinates": []},
            "projectId": project_id,
        })
    else:
        capture.skipped.append(
            ("processing_create_rejected", "not requested; pass --include-create-failure"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--env", default=os.environ.get("MAPFLOW_ENV", "production"),
                        help="backend environment, as in the plugin's mapflow_env setting")
    parser.add_argument("--include-create-failure", action="store_true",
                        help="also POST a deliberately invalid processing to capture the "
                             "rejection envelope. Shaped to be refused, but it is the only "
                             "non-read-only call in this script.")
    args = parser.parse_args()

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
