"""QGIS-tier tests for logging in and out.

Barely covered while this lived in `mapflow.py` — the only test that touched it drove `logout`
for its side effect on the account poll. The move is what makes it testable: the credentials and
the auth method are now a service that needs no dialog, and the dialog's effects arrive as signals
a test can listen to.
"""
from base64 import b64encode
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from mapflow.errors import ProxyIsAlreadySet
from mapflow.functional.service import session_service as ss_mod
from mapflow.functional.service.session_service import SessionService


def _service(use_oauth=False, token="", on_authenticated=None):
    settings = MagicMock()
    stored = {"use_oauth": str(use_oauth).lower(), "token": token}
    settings.value.side_effect = lambda key, default=None: stored.get(key, default)
    settings.setValue.side_effect = lambda key, value: stored.__setitem__(key, value)

    service = SessionService(
        http=MagicMock(),
        app_context=SimpleNamespace(settings=settings, logged_in=True, username="", password=""),
        config=SimpleNamespace(SERVER="https://mapflow.test",
                               AUTH_CONFIG_NAME="mapflow",
                               AUTH_CONFIG_MAP={}),
        on_authenticated=on_authenticated or (lambda response: None))
    service.tr = lambda text: text
    service._stored = stored
    return service


@pytest.fixture(autouse=True)
def alerts(monkeypatch):
    """Everything the service told the user, in order.

    `autouse` is load-bearing, not convenience. `alert()` defaults to `blocking=True`, which is
    `QMessageBox.exec()` — a modal event loop with nothing to close it in the headless test
    container. A single unstubbed call does not fail the suite, it **hangs** it indefinitely, with
    no output to say which test is stuck. Stubbing every test in this module removes the whole
    failure mode; tests that care about the wording still take `alerts` as an argument."""
    said = []
    monkeypatch.setattr(ss_mod, "alert_info", lambda message, *a, **k: said.append(message))
    monkeypatch.setattr(ss_mod, "alert_warning", lambda message, *a, **k: said.append(message))
    return said


def _basic_token(user="me@example.com", password="pw"):  # pragma: allowlist secret
    """A Basic-auth token shaped like the real one: base64 of "user:password"."""
    return b64encode(f"{user}:{password}".encode()).decode()


# ---------- which auth method ----------

def test_the_auth_method_is_read_from_settings():
    assert _service(use_oauth=True).use_oauth is True
    assert _service(use_oauth=False).use_oauth is False


def test_switching_auth_method_persists_it_and_announces_the_saved_token():
    service = _service(use_oauth=False, token="saved-token")
    announced = []
    service.authTypeChanged.connect(lambda oauth, token: announced.append((oauth, token)))

    service.set_auth_type(True)

    assert service._stored["use_oauth"] == "true"
    assert announced == [(True, "saved-token")]


# ---------- basic auth ----------

def test_a_typed_token_is_padded_to_a_multiple_of_four():
    # Base64 decodes only at length % 4 == 0; the issued token may arrive unpadded.
    assert SessionService.pad_token("abc") == "abc="
    assert SessionService.pad_token("ab") == "ab=="
    assert SessionService.pad_token("abcd") == "abcd"


def test_logging_in_saves_the_token_and_requests_the_default_project():
    service = _service()
    token = _basic_token()

    service.login_basic(token)

    assert service._stored["token"] == token
    assert service.http.setup_auth.call_args.kwargs["basic_auth_token"] == f"Basic {token}"
    assert service.http.get.call_args.kwargs["url"].endswith("/projects/default")


def test_the_token_is_saved_before_it_is_validated():
    """A rejected login must still replace the old token, or the next launch retries the stale
    one and fails the same way with no way for the user to see why."""
    service = _service(token="previous")

    service.login_basic("not-base64!!")

    assert service._stored["token"] == "not-base64!!"


def test_a_malformed_token_is_refused_without_a_request(alerts):
    service = _service()
    rejected, login_shown = [], []
    service.tokenRejected.connect(rejected.append)
    service.loginRequired.connect(lambda: login_shown.append(True))

    service.login_basic("not-base64!!")

    service.http.get.assert_not_called()
    assert rejected == [True]
    assert login_shown == [True]
    assert "Wrong token" in alerts[0]


def test_a_token_without_a_colon_is_malformed_too():
    """b64decode succeeds and the split fails — a different failure mode, same handler."""
    service = _service()

    service.login_basic(b64encode(b"no-colon-here").decode())

    service.http.get.assert_not_called()
    assert service.app_context.username == ""


def test_a_valid_token_populates_the_credentials():
    service = _service()

    service.login_basic(_basic_token("me@example.com", "pw"))

    assert service.app_context.username == "me@example.com"
    assert service.app_context.password == "pw"  # pragma: allowlist secret


def test_authenticate_with_no_typed_token_does_nothing():
    service = _service(use_oauth=False)

    service.authenticate("")

    service.http.get.assert_not_called()


def test_authenticate_pads_what_the_user_typed():
    service = _service(use_oauth=False)

    service.authenticate(_basic_token().rstrip("="))

    assert service._stored["token"].endswith("=") or len(service._stored["token"]) % 4 == 0


# ---------- oauth ----------

def test_oauth_login_without_an_auth_id_is_refused(monkeypatch):
    service = _service(use_oauth=True)
    monkeypatch.setattr(ss_mod, "get_auth_id", lambda name, mapping: (None, False))
    rejected = []
    service.tokenRejected.connect(rejected.append)

    service.authenticate()

    assert rejected == [True]
    service.http.setup_auth.assert_not_called()


def test_a_freshly_created_auth_config_tells_the_user_to_restart(monkeypatch, alerts):
    service = _service(use_oauth=True)
    monkeypatch.setattr(ss_mod, "get_auth_id", lambda name, mapping: ("id-1", True))

    service.authenticate()

    assert "restart QGIS" in alerts[0]
    assert service.http.setup_auth.call_args.kwargs["oauth_id"] == "id-1"


def test_oauth_login_clears_the_invalid_token_line_and_requests_the_project(monkeypatch):
    service = _service(use_oauth=True)
    monkeypatch.setattr(ss_mod, "get_auth_id", lambda name, mapping: ("id-1", False))
    rejected = []
    service.tokenRejected.connect(rejected.append)

    service.authenticate()

    assert rejected == [False]
    assert service.http.get.call_args.kwargs["url"].endswith("/projects/default")


def test_an_already_configured_proxy_asks_for_a_restart_instead_of_requesting(alerts):
    service = _service()
    service.http.setup_auth.side_effect = ProxyIsAlreadySet

    service.login_oauth("id-1")

    service.http.get.assert_not_called()
    assert "restart QGIS" in alerts[0]


def test_a_corrupt_auth_config_names_the_config_to_remove(alerts):
    service = _service()
    service.http.setup_auth.side_effect = RuntimeError("boom")

    service.login_oauth("id-1")

    service.http.get.assert_not_called()
    assert "mapflow" in alerts[0]


# ---------- logging out ----------

def test_logout_clears_the_token_and_the_session():
    service = _service(token="saved")
    events = []
    service.loggedOut.connect(lambda: events.append("out"))
    service.loginRequired.connect(lambda: events.append("login"))

    service.logout()

    assert service._stored["token"] == ""
    assert service.app_context.logged_in is False
    service.http.logout.assert_called_once()
    # The session ends before the login dialog is offered, so listeners stop their polling first.
    assert events == ["out", "login"]


def test_rejecting_a_saved_token_offers_the_login_dialog(alerts):
    service = _service(token="stale")
    login_shown = []
    service.loginRequired.connect(lambda: login_shown.append(True))

    service.reject_saved_token()

    assert login_shown == [True]
    assert "Wrong token" in alerts[0]
