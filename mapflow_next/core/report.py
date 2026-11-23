"""The text of a report for Mapflow support (spec/006 § The report dialog). Pure Python: no Qt, no qgis.

`technical_text` builds the technical part from named parts, never from a dump of objects, and passes the whole
of it through `redact`, the one place that removes secrets. `compose` puts the user's comment above it, and
`mailto` makes the link that "Send" opens. The plugin sends nothing itself.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Optional
from urllib.parse import quote, urlsplit

REMOVED = "[removed]"
SUMMARY_LIMIT = 200          # characters of the one-line summary
BODY_LIMIT = 2000            # characters of a response body in a report
SUBJECT_LIMIT = 100          # characters of the mail subject


@dataclass
class RequestInfo:
    """The request that failed. The URL has no query string, and the headers and the request body are not kept."""
    method: str
    url: str
    status: Optional[int]
    body: str                # the response body


@dataclass
class Environment:
    plugin_version: str
    qgis_version: str
    qt_version: str
    os: str
    env: str                 # production, staging, ...


def without_query(url: str) -> str:
    """The query string can carry a token (a presigned URL): it never goes to a log or a report."""
    return url.split("?", 1)[0]


# ---------- redact ----------

# Keys whose value is a secret: any name that ends in one of these words (`access_token`, `X-Amz-Signature`),
# and `authorization`. The value is a JSON or repr string (also one that was cut, with no closing quote), or
# plain text up to the next separator (a form body, a query).
_KEY_NAMES = (r"""["']?[\w-]*?(?:token|password|passwd|secret|api[_-]?key|signature)["']?"""
              r"""|["']?\bauthorization\b["']?""")
_VALUE = r"""(?:\[removed\]|"(?:[^"\\]|\\.)*"?|'(?:[^'\\]|\\.)*'?|[^\s&,;"'}\]]+)"""
_KEYED = re.compile(rf"(?P<key>{_KEY_NAMES})(?P<sep>\s*[:=]\s*){_VALUE}", re.IGNORECASE)
# `code` is the OAuth authorization code in a form or a query. The API's own `"code": "..."` names an error
# and is what support needs, so only the `code=value` shape is removed.
_CODE = re.compile(rf"(?P<key>\bcode)(?P<sep>=){_VALUE}", re.IGNORECASE)
_HEADER = re.compile(r"\bauthorization\b[ \t]*:[^\r\n]*", re.IGNORECASE)
_BEARER = re.compile(r"\bbearer\s+[^\s\"',;]+", re.IGNORECASE)
_BASIC = re.compile(r"\bbasic\s+[A-Za-z0-9+/_-]{8,}={0,2}", re.IGNORECASE)
_JWT = re.compile(r"\beyJ[\w.-]{8,}")
_URL_TAIL = re.compile(r"(https?://[^\s?#\"'<>]+)[?#][^\s\"'<>]*", re.IGNORECASE)


# ---------- the source of a QGIS tile layer ----------
# The answers of Mapflow about a processing hold `params.sourceParams.userDefined`: the full address of the layer
# (a key can sit in its path or its query), `rasterLogin` and maybe `rasterPassword`. `hide_tile_source` is the one
# filter for them; `redact` applies it, and so does the HTTP layer to every answer text it keeps.

_QUOTED = r"""\"(?:[^"\\]|\\.)*"?|'(?:[^'\\]|\\.)*'?"""
_USER_DEFINED = re.compile(rf"""(?P<head>["']userDefined["']\s*:\s*\{{)(?P<body>(?:{_QUOTED}|[^{{}}"'])*)""",
                           re.IGNORECASE)
_URL_VALUE = re.compile(rf"""(?P<key>["']url["']\s*:\s*)(?P<value>{_QUOTED})""", re.IGNORECASE)
_RASTER_SECRET = re.compile(
    rf"""(?P<key>["']?\braster[_-]?(?:login|password)["']?\s*[:=]\s*)"""
    rf"""(?P<value>\[removed\]|{_QUOTED}|[^\s&,;"'}}\]]+)""",
    re.IGNORECASE)
_TILE_WORDS = ("userdefined", "rasterlogin", "rasterpassword", "raster_login", "raster_password", "raster-login",
               "raster-password")


def address_origin(url: str) -> str:
    """The scheme, host and port of an address, with no user info, path, query or fragment. `[removed]` when
    the text is not an address."""
    try:
        parts = urlsplit(url.replace("\\/", "/").strip())
        host, port = parts.hostname, parts.port
    except ValueError:
        return REMOVED
    if not parts.scheme or not host:
        return REMOVED
    return f"{parts.scheme}://{'[' + host + ']' if ':' in host else host}{f':{port}' if port else ''}"


def _quoted_replacement(value: str, replacement: str) -> str:
    """`replacement` in the quotes that `value` had, so a JSON or repr text stays valid."""
    return f"{value[0]}{replacement}{value[0]}" if value[:1] in ("'", '"') else replacement


def hide_tile_source(text: str) -> str:
    """`text` with the secrets of a `userDefined` tile source removed, and its shape kept (JSON stays JSON):
    the value of every `rasterLogin` and `rasterPassword` becomes `[removed]`, and every `url` inside a
    `userDefined` object is cut to its scheme, host and port. It works on a text that was cut short too."""
    if not any(word in text.lower() for word in _TILE_WORDS):
        return text

    def cut_urls(found):
        def cut(url):
            value = url.group("value")
            inner = value[1:-1] if value.endswith(value[0]) and len(value) > 1 else value[1:]
            return f"{url.group('key')}{_quoted_replacement(value, address_origin(inner))}"
        return found.group("head") + _URL_VALUE.sub(cut, found.group("body"))

    text = _USER_DEFINED.sub(cut_urls, text)
    return _RASTER_SECRET.sub(lambda f: f.group("key") + _quoted_replacement(f.group("value"), REMOVED), text)


def redact(text: str, secrets: Iterable[str] = ()) -> str:
    """Remove from `text` what must not leave the machine: an `Authorization` header, bearer and basic
    credentials, the values of keys that name a secret, the login, password and address of a tile layer source
    (`hide_tile_source`), a JWT, the query string and fragment of every URL, and
    each of `secrets` (literals the caller knows, such as the current access token). It is a pattern filter, not a
    proof: the report is also built from named parts only."""
    text = hide_tile_source(text)
    text = _URL_TAIL.sub(r"\1", text)
    text = _HEADER.sub(REMOVED, text)
    text = _BEARER.sub(REMOVED, text)
    text = _BASIC.sub(REMOVED, text)
    text = _JWT.sub(REMOVED, text)
    text = _KEYED.sub(lambda m: f"{m.group('key')}{m.group('sep')}{REMOVED}", text)
    text = _CODE.sub(lambda m: f"{m.group('key')}{m.group('sep')}{REMOVED}", text)
    for secret in secrets:
        if secret:
            text = text.replace(secret, REMOVED)
    return text


# ---------- the parts of a report ----------

def _one_line(text: str, limit: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"


def summary_from(kind: str, message: str, secrets: Iterable[str] = ()) -> str:
    """One line that says what failed: the exception's type name and message, without secrets."""
    return _one_line(redact(f"{kind}: {message}", secrets), SUMMARY_LIMIT)


def summary_of(exc: BaseException, secrets: Iterable[str] = ()) -> str:
    return summary_from(type(exc).__name__, str(exc), secrets)


def technical_text(summary: str, details: str, request: Optional[RequestInfo], environment: Environment,
                   secrets: Iterable[str] = ()) -> str:
    """The technical part: the summary, the versions, the request (if the failure had one) and the traceback.
    Everything passes through `redact` as a whole."""
    secrets = tuple(secrets)
    lines = [summary, "",
             f"Plugin: {environment.plugin_version}",
             f"QGIS: {environment.qgis_version}",
             f"Qt: {environment.qt_version}",
             f"OS: {environment.os}",
             f"Environment: {environment.env}"]
    if request is not None:
        body = redact(request.body or "", secrets)       # redact first: a cut could leave half a token
        if len(body) > BODY_LIMIT:
            body = body[:BODY_LIMIT] + "\n[cut]"
        lines += ["", f"Request: {request.method} {without_query(request.url)}",
                  f"HTTP status: {request.status if request.status is not None else 'none'}",
                  "Response body:", body]
    if details:
        lines += ["", details.rstrip()]
    return redact("\n".join(lines), secrets)


def compose(comment: str, technical: str) -> str:
    """The user's comment (their own words, not redacted) above the technical part."""
    comment = comment.strip()
    return f"{comment}\n\n{technical}" if comment else technical


def mailto(address: str, subject: str, body: str) -> str:
    """A `mailto:` link (RFC 6068): the subject on one line, line breaks of the body as CRLF."""
    subject = _one_line(subject, SUBJECT_LIMIT)
    body = body.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")
    return f"mailto:{quote(address, safe='@')}?subject={quote(subject, safe='')}&body={quote(body, safe='')}"
