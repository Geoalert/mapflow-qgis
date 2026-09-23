"""A stand-in for QGIS's network stack, replaying the captured fixtures.

The fake replaces ``QgsNetworkAccessManager``, not ``Http``. ``Http`` is scheduled to move to
``infra/`` in Phase D, so a test that patched it would break during the very refactoring it
exists to guard; ``QgsNetworkAccessManager`` is a QGIS API and cannot move. It also means the
recorded calls are real ``QNetworkRequest`` objects — real URL, real headers, real body —
which is the wire contract `spec/002_api.md` specifies.

Delivery is explicit. ``Http.send_request`` connects to ``reply.finished`` *after* the
manager returns the reply, so a fake that emitted on creation would be talking to nobody.
Holding replies until ``deliver()`` also lets a test assert on the state between the request
going out and the answer coming back, and lets it prove that an action issued *no* request.

Scope, worth knowing before adding a journey: this intercepts what the *plugin* asks for. A
raster or vector-tile layer handed to QGIS fetches its own tiles through the provider, which
this never sees. So a tile URL in a fixture must at least be resolvable — an unroutable host
stalls the run inside QGIS rather than failing a test.
"""
import json
from pathlib import Path

from PyQt5.QtCore import QByteArray, QObject, pyqtSignal
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest

RESPONSES = Path(__file__).parent / "responses"

#: Any path segment shaped like this is an id and matches any other id at that position, so
#: routes are discovered from the fixtures instead of being written out with live ids in them.
_ID_HINTS = ("-", )


def _is_id(segment: str) -> bool:
    if segment.count("-") == 4 and len(segment) >= 32:
        return True
    return len(segment) >= 24 and any(hint in segment for hint in _ID_HINTS)


def normalise(path: str):
    """Path as a tuple of segments, with ids blanked, so one fixture serves any id."""
    clean = path.split("?", 1)[0].strip("/")
    return tuple("*" if _is_id(part) else part for part in clean.split("/") if part)


def fixture(name: str):
    """The captured body of one response, for a test that needs to route to a variant."""
    return json.loads((RESPONSES / "{}.json".format(name)).read_text())["body"]


class FakeReply(QObject):
    """Enough of QNetworkReply for the plugin's callbacks and error handlers."""

    finished = pyqtSignal()

    def __init__(self, request: QNetworkRequest, status: int, body: bytes,
                 network_error=QNetworkReply.NoError):
        super().__init__()
        self._request = request
        self._status = status
        self._body = QByteArray(body)
        self._error = network_error
        self._finished = False

    # -- the QNetworkReply surface the plugin actually uses --
    def error(self):
        return self._error

    def readAll(self):
        return self._body

    def request(self):
        return self._request

    def attribute(self, attribute):
        if attribute == QNetworkRequest.HttpStatusCodeAttribute:
            return self._status
        return None

    def isFinished(self):
        return self._finished

    def errorString(self):
        """Error handlers fall back to this when the payload carries no message."""
        return "" if self._error == QNetworkReply.NoError else "network error"

    def abort(self):
        self._finished = True

    def deleteLater(self):
        pass

    def _complete(self):
        self._finished = True
        self.finished.emit()


class RecordedRequest:
    def __init__(self, method: str, request: QNetworkRequest, body):
        self.method = method
        self.url = request.url().toString()
        self.path = request.url().path()
        self.body = body
        self.headers = {bytes(name).decode().lower(): bytes(request.rawHeader(name)).decode()
                        for name in request.rawHeaderList()}

    def json(self):
        if not self.body:
            return None
        try:
            return json.loads(bytes(self.body).decode())
        except (ValueError, UnicodeDecodeError):
            return None

    def __repr__(self):
        return "<{} {}>".format(self.method, self.path)


class FakeNetwork:
    """Routes requests to captured fixtures and records everything that was sent."""

    def __init__(self):
        self.requests = []
        self.unmatched = []
        self._pending = []
        self._routes = {}
        self._overrides = {}
        for path in sorted(RESPONSES.glob("*.json")):
            fixture = json.loads(path.read_text())
            recorded = fixture.get("request", {}).get("path")
            if recorded:
                self._routes.setdefault(normalise(recorded), (path.stem, fixture))

    # -- test-facing --
    def respond_with(self, path: str, status: int, body):
        """Override one route, for the paths where a journey needs a specific answer."""
        payload = body if isinstance(body, (bytes, bytearray)) else json.dumps(body).encode()
        self._overrides[normalise(path)] = (status, payload)

    def deliver(self):
        """Complete every outstanding reply, in the order it was requested."""
        pending, self._pending = self._pending, []
        for reply in pending:
            reply._complete()
        return len(pending)

    def paths(self):
        return [r.path for r in self.requests]

    def sent_to(self, path_fragment: str):
        return [r for r in self.requests if path_fragment in r.path]

    # -- the QgsNetworkAccessManager surface Http uses --
    def get(self, request):
        return self._handle("GET", request, None)

    def post(self, request, body=None):
        return self._handle("POST", request, body)

    def put(self, request, body=None):
        return self._handle("PUT", request, body)

    def deleteResource(self, request):
        return self._handle("DELETE", request, None)

    def sendCustomRequest(self, request, verb, device=None):
        return self._handle(bytes(verb).decode(), request, None)

    def setupDefaultProxyAndCache(self):
        pass

    def _handle(self, method: str, request: QNetworkRequest, body):
        self.requests.append(RecordedRequest(method, request, body))
        key = normalise(request.url().path())
        status, payload = self._lookup(key, request)
        reply = FakeReply(request, status, payload)
        self._pending.append(reply)
        return reply

    def _lookup(self, key, request):
        for candidate in self._suffixes(key):
            if candidate in self._overrides:
                return self._overrides[candidate]
        for candidate in self._suffixes(key):
            if candidate in self._routes:
                _name, fixture = self._routes[candidate]
                body = fixture.get("body")
                if isinstance(body, dict) and "__raw__" in body:
                    payload = body["__raw__"].encode()
                else:
                    payload = json.dumps(body).encode()
                return fixture.get("status", 200), payload
        self.unmatched.append(request.url().path())
        return 501, b'{"code": "NO_FIXTURE", "message": "no captured response"}'

    @staticmethod
    def _suffixes(key):
        """Fixture paths are server-relative; request paths carry the API prefix."""
        return [key[i:] for i in range(len(key))]
