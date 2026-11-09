"""Browser sign-in, the parts without Qt: PKCE, the authorization URL, reading the redirect that
brings the code back, the local answer to the browser, and the tokens.

The flow is OAuth2 authorization code with PKCE (RFC 7636) for a native app with a loopback
redirect (RFC 8252). The browser has to come back to the loopback address once, because that is
how the code reaches QGIS; the plugin answers it with a redirect to Mapflow Web.
"""
from __future__ import annotations

import base64
import hashlib
import html
import secrets
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from urllib.parse import parse_qs, urlencode, urlsplit

MAX_REQUEST_BYTES = 16 * 1024


def pkce_pair() -> Tuple[str, str]:
    """(code_verifier, S256 code_challenge)."""
    verifier = secrets.token_urlsafe(64)          # 86 chars of [A-Za-z0-9_-]
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return verifier, base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def new_state() -> str:
    return secrets.token_urlsafe(24)


def authorize_url(base: str, client_id: str, redirect_uri: str, state: str, challenge: str,
                  scope: str = "") -> str:
    params = {"response_type": "code", "client_id": client_id, "redirect_uri": redirect_uri,
              "state": state, "code_challenge": challenge, "code_challenge_method": "S256"}
    if scope:
        params["scope"] = scope
    return f"{base}?{urlencode(params)}"


def code_form(code: str, verifier: str, client_id: str, redirect_uri: str) -> Dict[str, str]:
    return {"grant_type": "authorization_code", "code": code, "code_verifier": verifier,
            "client_id": client_id, "redirect_uri": redirect_uri}


def refresh_form(refresh_token: str, client_id: str) -> Dict[str, str]:
    return {"grant_type": "refresh_token", "refresh_token": refresh_token, "client_id": client_id}


@dataclass(frozen=True)
class Redirect:
    kind: str          # code | error | stale (wrong or missing state) | other (not the redirect path)
    value: str = ""


def read_redirect(head: bytes, path: str, state: str) -> Redirect:
    """What the browser brought back, from the request head received on the loopback address."""
    line = head.split(b"\n", 1)[0].decode("latin-1").strip()
    parts = line.split()
    if len(parts) < 2 or parts[0] != "GET":
        return Redirect("other")
    target = urlsplit(parts[1])
    if target.path.rstrip("/") != path.rstrip("/"):
        return Redirect("other")
    query = {key: values[0] for key, values in parse_qs(target.query).items()}
    if not state or not secrets.compare_digest(query.get("state", "").encode(), state.encode()):
        return Redirect("stale")
    if "error" in query:
        return Redirect("error", query.get("error_description") or query["error"])
    if query.get("code"):
        return Redirect("code", query["code"])
    return Redirect("other")


def http_response(status: str, body: str = "", location: str = "") -> bytes:
    """A complete HTTP/1.1 answer to the browser; the connection closes after it."""
    data = body.encode("utf-8")
    headers = [f"HTTP/1.1 {status}", "Content-Type: text/html; charset=utf-8",
               f"Content-Length: {len(data)}", "Cache-Control: no-store", "Connection: close"]
    if location:
        headers.append(f"Location: {location}")
    return ("\r\n".join(headers) + "\r\n\r\n").encode("latin-1") + data


def page(title: str, text: str, link: str = "", link_text: str = "") -> str:
    """A tiny page for the cases the browser can't be sent on to Mapflow Web."""
    anchor = (f'<p><a href="{html.escape(link)}" style="color:#1f6feb">{html.escape(link_text)}</a></p>'
              if link else "")
    return ("<!doctype html><html><head><meta charset=\"utf-8\"><title>Mapflow</title></head>"
            "<body style=\"font-family:Nunito,system-ui,sans-serif;max-width:420px;margin:15vh auto;"
            "padding:0 16px;color:#1d2330\">"
            f"<h2 style=\"margin:0 0 8px\">{html.escape(title)}</h2>"
            f"<p style=\"color:#5b6475;line-height:1.5\">{html.escape(text)}</p>{anchor}</body></html>")


@dataclass(frozen=True)
class Tokens:
    access: str
    refresh: str
    expires_in: float
    received_at: float

    @classmethod
    def from_response(cls, data, previous_refresh: str = "", now: Optional[float] = None) -> "Tokens":
        """From the token endpoint's JSON. A refresh may not return a new refresh token: keep the old one."""
        data = data if isinstance(data, dict) else {}
        access = data.get("access_token")
        if not access:
            raise ValueError("the sign-in response has no access token")
        return cls(access, data.get("refresh_token") or previous_refresh,
                   float(data.get("expires_in") or 300), time.time() if now is None else now)

    def refresh_delay(self) -> float:
        """Seconds until the access token should be renewed: a minute early, or at 80% of a short lifetime."""
        return max(5.0, self.expires_in - min(60.0, self.expires_in * 0.2))
