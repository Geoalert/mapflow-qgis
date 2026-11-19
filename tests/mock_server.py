"""A small stand-in for the Mapflow API and its sign-in server, enough to drive the whole flow in tests.

The API requires `Authorization: Basic …` (API token) or `Bearer …` (browser sign-in) like the real
one; a processing advances one step per list call. The sign-in server (under OIDC) behaves like
Keycloak for a person who is already signed in to Mapflow in their browser: it checks the client,
the redirect address and PKCE, and hands out short access tokens and rotating refresh tokens.
"""
import base64
import copy
import hashlib
import json
import re
import threading
import time
import uuid
from urllib.parse import parse_qs, unquote, urlencode, urlsplit
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import fixtures

TOKEN = base64.b64encode(b"me@example.com:secret-password").decode().rstrip("=")
OIDC = "/auth/realms/mapflow/protocol/openid-connect"
# An 8×8 green PNG, for image previews
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAACXBIWXMAAA9hAAAPYQGoP6dpAAAAFElEQVQImWOM"
                       "6vdjwAaYsIoOWgkA954BR71+LSAAAAAASUVORK5CYII=")  # pragma: allowlist secret (a PNG)
REDIRECT_URI = "http://127.0.0.1:7070/qgis"
ODD_BOUNDS_ID = "odd-bounds"          # a processing whose tilejson bounds cannot be transformed
ODD_BOUNDS = [37.595, 91.0, 37.615, 92.0]


class State:
    def __init__(self):
        self.processings = [fixtures.processing_json("old-1", "OK", 100, name="Forest · River corridor", cost=57),
                            fixtures.processing_json("old-2", "FAILED", 0, name="Roads · North district", cost=0)]
        self.processings[1]["messages"] = [{"code": "dataloader.NoDataTile", "parameters": {}}]
        self.steps = {}
        self.requests = []
        self.lock = threading.Lock()
        self.starred = {"project-3"}       # starred in Mapflow Web
        self.catalog_many = False          # the catalog answers with 60 images, in pages
        self.extra_mosaics = []            # collections added while the test runs (an empty one)
        self.created_projects = []         # POST /projects
        self.no_mosaics = False            # an account without collections
        self.status = None                 # GET /user/status answers this, not fixtures.STATUS (a changed balance)
        self.many_mosaics = 0              # this many more collections, listed after the fixtures' (for paging)
        self.uploads = []                  # (what, mosaic, detail) for each upload request
        self.list_uploads = False          # a one-file upload is listed afterwards as a collection with one image
        self.extra_images = {}             # …and its image: mosaic id → image names
        self.created_tags = {}             # collection id → the tags it was created with
        self.added_names = {}              # collection id → file names uploaded into it during the run
        self.deleted_mosaics = set()       # DELETE rasters/mosaic/{id}
        self.created_mosaics = 0           # POST rasters/mosaic so far: numbers the new collections' ids
        self.deleted_images = set()        # DELETE rasters/image/{id}
        self.codes = {}                 # code → (code_challenge, redirect_uri)
        self.access_tokens = set()
        self.refresh_tokens = set()
        self.issued = 0
        self.expires_in = 300
        self.pkce_checked = 0
        self.failures = []                 # rules from fail(): requests that answer an error instead
        self.hang_seconds = 3              # how long a "hang" holds the request before it closes

    def fail(self, method, pattern, what, times=None):
        """Requests of `method` whose path (without /rest) matches the regex `pattern` fail. `what`: an HTTP
        status (503, 403, 404, 400), "drop" (the connection closes with no answer) or "hang" (no answer for
        `hang_seconds`). `times`: how many requests fail, or None until `heal()`."""
        with self.lock:
            self.failures.append({"method": method, "pattern": re.compile(pattern), "what": what, "left": times})

    def heal(self):
        with self.lock:
            self.failures = []

    def failure_for(self, method, path):
        """The rule that fails this request, if any (and one use of it counted)."""
        with self.lock:
            for rule in self.failures:
                if rule["method"] == method and rule["pattern"].search(path) and rule["left"] != 0:
                    if rule["left"] is not None:
                        rule["left"] -= 1
                    return rule["what"]
        return None


class Handler(BaseHTTPRequestHandler):
    state: State = None

    def log_message(self, *args):
        pass

    def _projects(self):
        with self.state.lock:
            created = list(self.state.created_projects)
        return created + [fixtures.PROJECT, fixtures.PROJECT_2] + fixtures.MORE_PROJECTS

    def _mosaics(self):
        """Every collection of the account, newest first, as the data catalog lists them."""
        if self.state.no_mosaics:
            return []
        many = [{"id": f"m-many-{n:03d}", "name": f"Survey tile {n:03d}", "created_at": f"2025-01-01T00:{n // 60:02d}:"
                 f"{n % 60:02d}Z", "sizeInBytes": 1000, "footprint": None, "tags": [],
                 "rasterLayer": {"tileUrl": "", "tileJsonUrl": ""}, "status_summary": {"total": 1}}
                for n in range(self.state.many_mosaics)]
        every = [m for m in fixtures.MOSAICS + self.state.extra_mosaics + many
                 if m["id"] not in self.state.deleted_mosaics]
        return sorted(every, key=lambda m: m.get("created_at") or "", reverse=True)

    def _image_names(self, mosaic_id):
        return fixtures.MOSAIC_IMAGES.get(mosaic_id) or self.state.extra_images.get(mosaic_id, [])

    def _send(self, status, body, content_type="application/json"):
        data = body if isinstance(body, bytes) else (body if isinstance(body, str) else json.dumps(body)).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _fail(self, what):
        """An answer the test asked for: an error status, no answer at all ("drop"), or one that never comes."""
        if what == "drop":
            self.close_connection = True
            return
        if what == "hang":
            time.sleep(self.state.hang_seconds)
            self.close_connection = True
            return
        messages = {503: "Service unavailable", 403: "No access", 404: "Not found", 400: "Bad request"}
        return self._send(what, {"code": f"HTTP_{what}", "message": messages.get(what, "Failure")})

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
        if method == "GET" and path == "/open/preview.png":     # a public picture: no sign-in
            return self._send(200, PNG, "image/png")
        if not self._authorized():
            return
        if path == "/redirect":                                 # answers 302 to the `to` query value
            target = parse_qs(urlsplit(self.path).query).get("to", [""])[0]
            return self._redirect(target or self.path)             # no `to`: back to itself, a loop
        failure = self.state.failure_for(method, path)
        if failure is not None:
            return self._fail(failure)
        if method == "GET" and path == "/projects/default":
            return self._send(200, fixtures.PROJECT)
        if method == "GET" and path == "/user/status":
            return self._send(200, self.state.status or fixtures.STATUS)
        if method == "POST" and path == "/projects":
            name = (body or {}).get("name", "").strip()
            if not name:
                return self._send(400, {"code": "INVALID_BODY", "message": "Invalid value for: body"})
            project = dict(fixtures.PROJECT, id=f"project-new-{len(self.state.created_projects) + 1}", name=name,
                           description=(body or {}).get("description"), isDefault=False,
                           created="2026-11-13T19:00:00Z", updated="2026-11-13T19:00:00Z")
            with self.state.lock:
                self.state.created_projects.insert(0, project)
            return self._send(200, project)
        if method == "POST" and path == "/projects/starred":
            every = self._projects()
            with self.state.lock:
                page = [dict(p, starred=True) for p in every if p["id"] in self.state.starred]
            return self._send(200, {"results": page, "total": len(page), "count": len(page)})
        match = re.fullmatch(r"/projects/([\w-]+)/starred", path)
        if method in ("POST", "DELETE") and match:
            with self.state.lock:
                (self.state.starred.add if method == "POST" else self.state.starred.discard)(match.group(1))
            return self._send(200, "", "text/plain")
        match = re.fullmatch(r"/processings/([\w-]+)", path)
        if method == "DELETE" and match:
            with self.state.lock:
                self.state.processings = [p for p in self.state.processings if p["id"] != match.group(1)]
            return self._send(200, "", "text/plain")
        match = re.fullmatch(r"/catalog/preview/([\w-]+)", path)
        if method == "GET" and match:
            return self._send(200, PNG, "image/png")
        if method == "POST" and path == "/projects/page":
            with self.state.lock:
                starred = set(self.state.starred)
            projects = [dict(p, starred=p["id"] in starred)
                        for p in self._projects()]
            needle = (body.get("filter") or "").lower()
            if needle:
                projects = [p for p in projects if needle in p["name"].lower()]
            offset, limit = int(body.get("offset") or 0), int(body.get("limit") or 20)
            page = projects[offset:offset + limit]
            return self._send(200, {"results": page, "total": len(projects), "count": len(page)})
        match = re.fullmatch(r"/projects/([\w-]+)", path)
        if method == "GET" and match:
            every = self._projects()
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
            # Latitudes beyond 90°: QgsCoordinateTransform.transformBoundingBox raises QgsCsException (QGIS 3 and 4)
            bounds = ODD_BOUNDS if match.group(1) == ODD_BOUNDS_ID else [37.595, 55.745, 37.615, 55.755]
            return self._send(200, {"tilejson": "2.2.0", "minzoom": 0, "maxzoom": 18, "bounds": bounds})
        if method == "GET" and path == "/not-json":     # a maintenance page where JSON is promised
            return self._send(200, "<html>maintenance</html>", "text/html")
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
            return self._send(200, [{"id": "a1", "status": "OK", "percentCompleted": 100, "area": 1,
                                     "messages": [], "geometry": geometry}])     # a list, as Mapflow answers
        if method == "POST" and path == "/catalog/meta":
            bad = [t for t in body.get("productTypes") or [] if t not in ("IMAGE", "MOSAIC")]
            if bad:   # what the real API answers
                return self._send(400, {"code": "BAD_REQUEST", "message": f"Invalid value for: body ('{bad[0]}' is "
                                        "not a member of enum io.geoalert.mapflow.model.enums.ProductType)"})
            base = f"http://127.0.0.1:{self.server.server_address[1]}/rest"
            if self.state.catalog_many:
                every = [dict(copy.deepcopy(fixtures.CATALOG["images"][0]), id=f"many-{n:02d}",
                              previewUrl=f"{base}/catalog/preview/many-{n:02d}") for n in range(60)]
                offset, limit = int(body.get("offset") or 0), int(body.get("limit") or 50)
                return self._send(200, {"images": every[offset:offset + limit], "total": len(every),
                                        "limit": limit, "offset": offset})
            catalog = copy.deepcopy(fixtures.CATALOG)
            catalog["images"][0]["previewUrl"] = f"{base}/catalog/preview/img-1"   # a picture preview
            return self._send(200, catalog)
        if method == "POST" and path == "/rasters/validate-image-metadata":
            # the schema of Mapflow's ValidationRequest (rasters/openapi.json): these fields, no others
            body = body if isinstance(body, dict) else {}
            required = {"width", "height", "channels", "dtype", "crs", "pixel_size_meters", "footprint",
                        "file_size_bytes"}
            detail = [{"loc": ["body", k], "msg": "Field required", "type": "missing"}
                      for k in sorted(required - set(body))]
            detail += [{"loc": ["body", k], "msg": "Extra inputs are not permitted", "type": "extra_forbidden"}
                       for k in sorted(set(body) - required - {"mosaic_id", "preserve_data_type"})]
            footprint = body.get("footprint") or {}
            if body.get("dtype", "uint8") not in ("uint8", "uint16", "int16", "float32", "int32") \
                    or len(body.get("pixel_size_meters") or [0, 0]) != 2 \
                    or (footprint and (footprint.get("type") != "Polygon" or not footprint.get("coordinates"))):
                detail.append({"loc": ["body"], "msg": "Input should be valid", "type": "value_error"})
            if detail:
                return self._send(422, {"detail": detail})
            reasons, warnings = [], []
            if body["dtype"] != "uint8":
                reasons.append({"code": "FileValidationFailed", "parameters": {"dtype": body["dtype"]},
                                "message": "the image must be 8-bit"})
            if body["channels"] == 1:
                warnings.append({"code": "SingleBand", "parameters": {},
                                 "message": "a single band is processed as grayscale"})
            return self._send(200, {"compatible": not reasons, "reasons": reasons, "warnings": warnings,
                                    "needs_preprocessing": False, "needs_async_preprocessing": False,
                                    "estimated_preprocessed_size_bytes": None})
        if method == "POST" and path == "/rasters/mosaic":
            body = body if isinstance(body, dict) else {}
            if not body.get("name") or not isinstance(body.get("tags"), list):     # MosaicCreateRequestSchema
                return self._send(422, {"detail": [{"loc": ["body"], "msg": "Field required", "type": "missing"}]})
            # A new id every time, as Mapflow gives: tests clear `uploads` between scenarios, so an id counted from
            # it repeated, and a second new collection "already had" the first one's files (409, and a dialog)
            with self.state.lock:
                self.state.created_mosaics += 1
                number = self.state.created_mosaics
            mosaic = {"id": f"m-new-{number}", "name": body["name"],
                      "created_at": "2026-11-13T21:00:00Z", "tags": body["tags"], "sizeInBytes": 0,
                      "footprint": None, "rasterLayer": {"tileUrl": "", "tileJsonUrl": ""}}
            with self.state.lock:
                self.state.uploads.append(("create", mosaic["id"], mosaic["name"]))
                self.state.created_tags[mosaic["id"]] = body["tags"]
                if self.state.list_uploads:
                    self.state.extra_mosaics.append(mosaic)
            return self._send(200, mosaic)
        match = re.fullmatch(r"/rasters/mosaic/([\w-]+)/image", path)
        if method == "POST" and match:
            mosaic_id = match.group(1)
            found = re.search(rb'filename="([^"]+)"', body if isinstance(body, bytes) else b"")
            filename = found.group(1).decode() if found else ""
            have = fixtures.MOSAIC_IMAGES.get(mosaic_id, []) + self.state.extra_images.get(mosaic_id, []) \
                + self.state.added_names.get(mosaic_id, [])
            if filename.lower() in {n.lower() for n in have} and "allow_duplicate=true" not in self.path:
                # as the data catalog answers: no message, the file and the image it repeats in the parameters
                with self.state.lock:
                    self.state.uploads.append(("duplicate", mosaic_id, filename))
                return self._send(409, {"detail": {"code": "ImageAlreadyExists", "message": "",
                                                   "parameters": {"filename": filename,
                                                                  "existing_image_id": f"{mosaic_id}-i0"}}})
            with self.state.lock:
                self.state.added_names.setdefault(mosaic_id, []).append(filename)
                self.state.uploads.append(("image", match.group(1), len(body or b"")))
                if self.state.list_uploads and match.group(1) not in fixtures.MOSAIC_IMAGES:
                    self.state.extra_images.setdefault(match.group(1), []).append("centre.tif")
            return self._send(200, {"id": f"img-{len(self.state.uploads)}", "mosaic_id": match.group(1)})
        if method == "POST" and path == "/rasters/mosaic/image":
            name = unquote(self.path.split("name=")[-1].split("&")[0])
            with self.state.lock:
                self.state.uploads.append(("new", name, len(body or b"")))
                if self.state.list_uploads:
                    mosaic_id = f"m-up-{len(self.state.uploads)}"
                    self.state.extra_mosaics.append({
                        "id": mosaic_id, "name": name, "created_at": "2026-11-15T12:00:00Z", "sizeInBytes": 10,
                        "footprint": None, "rasterLayer": {"tileUrl": "", "tileJsonUrl": ""}, "tags": []})
                    self.state.extra_images[mosaic_id] = ["centre.tif"]     # a footprint the fixtures know
                    return self._send(200, {"id": "img-new", "mosaic_id": mosaic_id})
            return self._send(200, {"id": "img-new", "mosaic_id": "m-new"})
        if method == "GET" and path == "/rasters/mosaic/page":
            # As the data catalog pages them: newest first, name_contains matched against the collection's
            # name and its images' file names, and an empty name_contains refused
            query = {k: v[0] for k, v in parse_qs(urlsplit(self.path).query, keep_blank_values=True).items()}
            if query.get("name_contains", None) == "":
                return self._send(422, {"detail": [{"loc": ["query", "name_contains"], "msg": "too short"}]})
            every = self._mosaics()
            needle = (query.get("name_contains") or "").lower()
            if needle:
                every = [m for m in every if needle in m["name"].lower()
                         or any(needle in n.lower() for n in self._image_names(m["id"]))]
            offset, limit = int(query.get("offset") or 0), int(query.get("limit") or 50)
            with self.state.lock:
                self.state.mosaic_pages = getattr(self.state, "mosaic_pages", []) + [query]
            page = every[offset:offset + limit]
            return self._send(200, {"items": page, "offset": offset, "limit": limit, "total": len(every),
                                    "has_next": offset + limit < len(every)})
        match = re.fullmatch(r"/rasters/mosaic/([\w-]+)", path)
        if method == "GET" and match:
            found = next((m for m in self._mosaics() if m["id"] == match.group(1)), None)
            return self._send(200, found) if found else \
                self._send(404, {"detail": {"code": "ItemNotFound", "message": "mosaicId not found"}})
        if method == "DELETE" and match:
            with self.state.lock:
                self.state.deleted_mosaics.add(match.group(1))
            return self._send(200, {})
        match = re.fullmatch(r"/rasters/image/([\w-]+)", path)
        if method == "DELETE" and match:
            with self.state.lock:
                self.state.deleted_images.add(match.group(1))
            return self._send(200, {})
        match = re.fullmatch(r"/rasters/mosaic/([\w-]+)/image", path)
        if method == "GET" and match:
            base = f"http://127.0.0.1:{self.server.server_address[1]}/rest"
            names = fixtures.MOSAIC_IMAGES.get(match.group(1)) or self.state.extra_images.get(match.group(1), [])
            with self.state.lock:
                self.state.image_requests = getattr(self.state, "image_requests", 0) + 1
            images = [fixtures.mosaic_image(f"{match.group(1)}-i{n}", match.group(1), name, base)
                      for n, name in enumerate(names)]
            return self._send(200, [i for i in images if i["id"] not in self.state.deleted_images])
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
