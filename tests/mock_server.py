"""A small stand-in for the Mapflow API and its sign-in server, enough to drive the whole flow in tests.

The API requires `Authorization: Basic …` (API token) or `Bearer …` (browser sign-in) like the real
one; a processing advances one step per list call. The sign-in server (under OIDC) behaves like
Keycloak for a person who is already signed in to Mapflow in their browser: it checks the client,
the redirect address and PKCE, and hands out short access tokens and rotating refresh tokens.
"""
import base64
import hashlib
import json
import re
import threading
import uuid
from urllib.parse import parse_qs, urlencode, urlsplit
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import fixtures

TOKEN = base64.b64encode(b"me@example.com:secret-password").decode().rstrip("=")
OIDC = "/auth/realms/mapflow/protocol/openid-connect"
# An 8×8 green PNG, for image previews
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAACXBIWXMAAA9hAAAPYQGoP6dpAAAAFElEQVQImWOM"
                       "6vdjwAaYsIoOWgkA954BR71+LSAAAAAASUVORK5CYII=")  # pragma: allowlist secret (a PNG)
REDIRECT_URI = "http://127.0.0.1:7070/qgis"


class State:
    def __init__(self):
        self.processings = [fixtures.processing_json("old-1", "OK", 100, name="Forest · River corridor", cost=57),
                            fixtures.processing_json("old-2", "FAILED", 0, name="Roads · North district", cost=0)]
        self.processings[1]["messages"] = [{"code": "dataloader.NoDataTile", "parameters": {}}]
        self.steps = {}
        self.requests = []
        self.lock = threading.Lock()
        self.codes = {}                 # code → (code_challenge, redirect_uri)
        self.access_tokens = set()
        self.refresh_tokens = set()
        self.issued = 0
        self.expires_in = 300
        self.pkce_checked = 0


class Handler(BaseHTTPRequestHandler):
    state: State = None

    def log_message(self, *args):
        pass

    def _send(self, status, body, content_type="application/json"):
        data = body if isinstance(body, bytes) else (body if isinstance(body, str) else json.dumps(body)).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _authorized(self):
        header = self.headers.get("Authorization", "")
        expected = "Basic " + base64.b64encode(b"me@example.com:secret-password").decode()
        bearer = header[7:] if header.startswith("Bearer ") else None
        if header != expected and not (bearer and bearer in self.state.access_tokens):
            self._send(401, {"code": "UNAUTHORIZED", "message": "Bad credentials"})
            return False
        return True

    def _body(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            return json.loads(raw) if raw else None
        except ValueError:
            return raw

    def _redirect(self, location):
        self.send_response(302)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _issue(self):
        with self.state.lock:
            self.state.issued += 1
            access, refresh = f"access-{self.state.issued}", f"refresh-{self.state.issued}"
            self.state.access_tokens.add(access)
            self.state.refresh_tokens.add(refresh)
        return self._send(200, {"access_token": access, "refresh_token": refresh, "token_type": "Bearer",
                                "expires_in": self.state.expires_in, "refresh_expires_in": 1800})

    def _oidc(self, method, path, raw):
        if method == "GET" and path == OIDC + "/auth":
            query = {k: v[0] for k, v in parse_qs(urlsplit(self.path).query).items()}
            if (query.get("client_id") != "qgis" or query.get("redirect_uri") != REDIRECT_URI
                    or query.get("response_type") != "code" or query.get("code_challenge_method") != "S256"):
                return self._send(400, "Invalid parameter: redirect_uri", "text/plain")
            code = uuid.uuid4().hex
            with self.state.lock:
                self.state.codes[code] = (query["code_challenge"], query["redirect_uri"])
            return self._redirect(f"{REDIRECT_URI}?{urlencode({'state': query['state'], 'code': code})}")
        if method == "POST" and path == OIDC + "/token":
            form = {k: v[0] for k, v in parse_qs(raw.decode() if isinstance(raw, bytes) else "").items()}
            if form.get("client_id") != "qgis":
                return self._send(401, {"error": "invalid_client"})
            if form.get("grant_type") == "authorization_code":
                with self.state.lock:
                    challenge, redirect_uri = self.state.codes.pop(form.get("code", ""), (None, None))
                verifier = form.get("code_verifier", "").encode()
                expected = base64.urlsafe_b64encode(hashlib.sha256(verifier).digest()).rstrip(b"=").decode()
                if challenge is None or redirect_uri != form.get("redirect_uri") or expected != challenge:
                    return self._send(400, {"error": "invalid_grant"})
                with self.state.lock:
                    self.state.pkce_checked += 1
                return self._issue()
            if form.get("grant_type") == "refresh_token":
                with self.state.lock:
                    valid = form.get("refresh_token") in self.state.refresh_tokens
                    self.state.refresh_tokens.discard(form.get("refresh_token"))   # rotate
                if not valid:
                    return self._send(400, {"error": "invalid_grant", "error_description": "Token is not active"})
                return self._issue()
        return self._send(404, {"error": "not_found"})

    def _route(self, method):
        path = self.path.split("?")[0].replace("/rest", "", 1)
        if path.startswith(OIDC):
            raw = self.rfile.read(int(self.headers.get("Content-Length") or 0)) if method == "POST" else b""
            with self.state.lock:
                self.state.requests.append((method, path, None, dict(self.headers)))
            return self._oidc(method, path, raw)
        body = self._body() if method in ("POST", "PUT") else None
        with self.state.lock:
            self.state.requests.append((method, path, body, dict(self.headers)))
        if not self._authorized():
            return
        if method == "GET" and path == "/projects/default":
            return self._send(200, fixtures.PROJECT)
        if method == "GET" and path == "/user/status":
            return self._send(200, fixtures.STATUS)
        if method == "POST" and path == "/projects/page":
            projects = [fixtures.PROJECT, fixtures.PROJECT_2] + fixtures.MORE_PROJECTS
            needle = (body.get("filter") or "").lower()
            if needle:
                projects = [p for p in projects if needle in p["name"].lower()]
            offset, limit = int(body.get("offset") or 0), int(body.get("limit") or 20)
            page = projects[offset:offset + limit]
            return self._send(200, {"results": page, "total": len(projects), "count": len(page)})
        match = re.fullmatch(r"/projects/([\w-]+)", path)
        if method == "GET" and match:
            every = [fixtures.PROJECT, fixtures.PROJECT_2] + fixtures.MORE_PROJECTS
            project = next((p for p in every if p["id"] == match.group(1)), None)
            if project:
                return self._send(200, project)
            return self._send(404, {"code": "NOT_FOUND", "message": "No project"})
        match = re.fullmatch(r"/projects/([\w-]+)/processings/v2/page", path)
        if method == "POST" and match:
            with self.state.lock:
                for item in self.state.processings:
                    if item["status"] == "IN_PROGRESS":
                        item["percentCompleted"] = min(100, item["percentCompleted"] + 50)
                        if item["percentCompleted"] >= 100:
                            item["status"] = "OK"
                items = list(reversed([p for p in self.state.processings if p["projectId"] == match.group(1)]))
            offset, limit = int(body.get("offset") or 0), int(body.get("limit") or 30)
            if limit > 100:
                return self._send(400, {"code": "BAD_REQUEST", "message": "limit must be at most 100"})
            page = items[offset:offset + limit]
            return self._send(200, {"results": page, "total": len(items), "count": len(page)})
        match = re.fullmatch(r"/processings/([\w-]+)/v2", path)
        if method == "PUT" and match:
            with self.state.lock:
                item = next((p for p in self.state.processings if p["id"] == match.group(1)), None)
                if item is not None:
                    item["name"], item["description"] = body.get("name"), body.get("description")
            return self._send(200, item or {})
        if method == "POST" and path in ("/processing/cost/v2", "/processings/v2") and not valid_processing(body):
            return self._send(400, {"code": "BAD_REQUEST", "message": "Invalid value for: body", "params": None})
        if method == "POST" and path == "/processing/cost/v2":
            return self._send(200, "70", "text/plain")
        match = re.fullmatch(r"/tiles/([\w-]+)\.json", path)
        if method == "GET" and match:     # a processing's vector tilejson: where its results are
            return self._send(200, {"tilejson": "2.2.0", "minzoom": 0, "maxzoom": 18,
                                    "bounds": [37.595, 55.745, 37.615, 55.755]})
        if method == "POST" and path == "/processings/v2":
            new = fixtures.processing_json(str(uuid.uuid4()), "IN_PROGRESS", 0, name=body["name"])
            new["vectorLayer"]["tileJsonUrl"] = \
                f"http://127.0.0.1:{self.server.server_address[1]}/rest/tiles/{new['id']}.json"
            new["params"] = body["params"]
            with self.state.lock:
                self.state.processings.append(new)
            return self._send(200, new)
        match = re.fullmatch(r"/processings/([\w-]+)/result", path)
        if method == "GET" and match:
            return self._send(200, fixtures.RESULT)
        match = re.fullmatch(r"/processings/([\w-]+)/aois", path)
        if method == "GET" and match:
            geometry = fixtures.RESULT["features"][0]["geometry"]
            return self._send(200, {"aois": [{"id": "a1", "status": "OK", "percentCompleted": 100, "area": 1,
                                              "messages": [], "geometry": geometry}]})
        if method == "POST" and path == "/catalog/meta":
            bad = [t for t in body.get("productTypes") or [] if t not in ("IMAGE", "MOSAIC")]
            if bad:   # what the real API answers
                return self._send(400, {"code": "BAD_REQUEST", "message": f"Invalid value for: body ('{bad[0]}' is "
                                        "not a member of enum io.geoalert.mapflow.model.enums.ProductType)"})
            return self._send(200, fixtures.CATALOG)
        if method == "GET" and path == "/rasters/mosaic":
            return self._send(200, fixtures.MOSAICS)
        match = re.fullmatch(r"/rasters/mosaic/([\w-]+)/image", path)
        if method == "GET" and match:
            base = f"http://127.0.0.1:{self.server.server_address[1]}/rest"
            names = fixtures.MOSAIC_IMAGES.get(match.group(1), [])
            return self._send(200, [fixtures.mosaic_image(f"{match.group(1)}-i{n}", match.group(1), name, base)
                                    for n, name in enumerate(names)])
        match = re.fullmatch(r"/rasters/image/([\w-]+)", path)
        if method == "GET" and match:
            base = f"http://127.0.0.1:{self.server.server_address[1]}/rest"
            for mosaic_id, names in fixtures.MOSAIC_IMAGES.items():
                for n, name in enumerate(names):
                    if match.group(1) == f"{mosaic_id}-i{n}":
                        return self._send(200, fixtures.mosaic_image(match.group(1), mosaic_id, name, base))
            return self._send(404, {"message": "Image not found"})
        match = re.fullmatch(r"/rasters/image/([\w-]+)/preview/[sl]", path)
        if method == "GET" and match:
            return self._send(200, PNG, "image/png")
        match = re.fullmatch(r"/processings/([\w-]+)/rate", path)
        if method == "PUT" and match:
            return self._send(200, "", "text/plain")
        return self._send(404, {"code": "NOT_FOUND", "message": f"No route {method} {path}"})

    def do_GET(self):
        self._route("GET")

    def do_POST(self):
        self._route("POST")

    def do_PUT(self):
        self._route("PUT")

    def do_DELETE(self):
        self._route("DELETE")


def start():
    state = State()
    handler = type("BoundHandler", (Handler,), {"state": state})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, state, f"http://127.0.0.1:{server.server_address[1]}/rest"


def valid_processing(body) -> bool:
    """What the real API rejects with "Invalid value for: body" (found the hard way):
    My imagery with both mosaicId and imageIds, and meta values that aren't strings."""
    if not isinstance(body, dict):
        return False
    source = ((body.get("params") or {}).get("sourceParams") or {})
    mine = source.get("myImagery")
    if mine is not None and (("mosaicId" in mine) == ("imageIds" in mine)):
        return False
    meta = body.get("meta") or {}
    if not isinstance(meta, dict) or not all(isinstance(v, str) for v in meta.values()):
        return False
    return all(key in body for key in ("name", "projectId", "geometry", "params"))


def auth_url(api_url):
    """The sign-in base for `mapflow_next/auth_url`, from the address `start()` returned."""
    return api_url[:-len("/rest")] + OIDC
