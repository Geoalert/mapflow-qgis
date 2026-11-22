"""A QGIS tile layer as the imagery of a processing (spec/002_B § Imagery from a QGIS tile layer). Pure Python:
standard library only, no Qt, no qgis, and no network (a host is judged from its text, never looked up).

The bridge reads a layer and hands its source text to `tile_source`. `tile_params` turns the parts into what the
plugin sends (`TileParams`), or into the reason the layer cannot be used. Nothing here keeps the address, the
login or the password in a `repr`.

How QGIS 3.28 and QGIS 4 name the parts of a `wms` layer with `type=xyz`: `url`, `zmin`, `zmax`, `username`,
`password`, `authcfg`, `referer` and `http-header:<name>`, joined with `&`. The placeholders are `{x}`, `{y}`,
`{z}`, `{-y}` (TMS) and `{q}` (quadkey). `QgsProviderRegistry.decodeUri` is not used: QGIS 3.28 decodes the
address only in part (`%7B` but not `%2F`) and QGIS 4 in full, while the layer's own source text is the same on
both. So the source is split here, and the address is decoded once, as QGIS does.
"""
from __future__ import annotations

import ipaddress
import re
import socket
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple
from urllib.parse import unquote, urlsplit

XYZ, TMS, QUADKEY = "XYZ", "TMS", "QUADKEY"
MAX_ZOOM = 21                   # the highest zoom the form offers
DEFAULT_ZOOM = 18               # the zoom the form starts at, or the nearest one it offers
QGIS_MIN_ZOOM, QGIS_MAX_ZOOM = 0, 18        # the range QGIS reads when the source has no zmin or zmax
CRS = "epsg:3857"               # QGIS reads every XYZ layer in this projection
UNREADABLE = "?"                # `auth_method` of a configuration the plugin cannot read (QGIS does not know its id)
BASIC = "Basic"

NO_PLACEHOLDERS = "Its address has no {x}, {y} and {z}, and no {q}."
NOT_HTTP = "Its address does not start with http:// or https://."
PRIVATE_HOST = "Its host is this computer, a private network address or an intranet name. Mapflow cannot reach it."
HEADERS = "It needs a referer or other HTTP headers. Mapflow cannot send them."
NOT_BASIC = "It uses an authentication configuration that is not Basic."
NO_ZOOM = "Its zoom range has no zoom that Mapflow reads (0 to 21)."


@dataclass(frozen=True)
class TileSource:
    """The parts of a layer source, as the bridge read them."""
    url: str = field(default="", repr=False)    # as stored in the source (percent-encoded); `tile_params` decodes it
    zmin: Optional[int] = None
    zmax: Optional[int] = None
    login: str = field(default="", repr=False)
    password: str = field(default="", repr=False)
    auth_method: str = ""                       # "" none | "Basic" | another method's key | UNREADABLE
    auth_config_id: str = field(default="", repr=False)     # the `authcfg` of the source, for reading the login
    referer: bool = False
    headers: Tuple[str, ...] = ()               # the names of the HTTP headers, never their values


@dataclass(frozen=True)
class TileParams:
    """What the plugin sends for a usable layer."""
    source_type: str                            # XYZ | TMS | QUADKEY
    url: str = field(repr=False)                # decoded; `{-y}` is written `{y}` for TMS
    zooms: Tuple[int, ...]
    has_login: bool                             # a login and password, or a Basic authentication configuration

    @property
    def meta_source(self) -> str:
        return self.source_type.lower()

    @property
    def host(self) -> str:
        return host_of(self.url)

    @property
    def default_zoom(self) -> int:
        return nearest_zoom(self.zooms, DEFAULT_ZOOM)


@dataclass(frozen=True)
class TileOffer:
    """One row of the run form: a layer of the project, usable or refused with a reason."""
    layer_id: str
    name: str
    params: Optional[TileParams] = None
    reason: str = ""

    @property
    def usable(self) -> bool:
        return self.params is not None


# ---------- reading a source ----------

def tile_source(text: str, auth_method_of: Callable[[str], str] = lambda _id: "") -> Optional[TileSource]:
    """The parts of a layer source `text` (`type=xyz&url=…&zmin=…`), or None when it is not an XYZ source.
    `auth_method_of(id)` gives the key of an authentication configuration ("" when QGIS does not know the id)."""
    parts: Dict[str, str] = {}
    headers: List[str] = []
    for item in text.split("&"):
        key, found, value = item.partition("=")
        if not found:
            continue
        key = unquote(key)
        if key.lower().startswith("http-header:"):
            headers.append(key.split(":", 1)[1])
        else:
            parts[key.lower()] = value
    if parts.get("type", "").lower() != "xyz":
        return None
    authcfg = unquote(parts.get("authcfg", ""))
    method = (auth_method_of(authcfg) or UNREADABLE) if authcfg else ""
    return TileSource(url=parts.get("url", ""), zmin=_int(parts.get("zmin")), zmax=_int(parts.get("zmax")),
                      login=unquote(parts.get("username", "")), password=unquote(parts.get("password", "")),
                      auth_method=method, auth_config_id=authcfg, referer=bool(unquote(parts.get("referer", ""))),
                      headers=tuple(headers))


def _int(value: Optional[str]) -> Optional[int]:
    try:
        return int(unquote(value or ""))
    except ValueError:
        return None


# ---------- from the parts to the fields, or the reason ----------

def tile_params(source: TileSource) -> Tuple[Optional[TileParams], str]:
    """(the params, "") for a layer the plugin can use, else (None, the reason). When several reasons apply, the
    first of the spec's list wins: placeholders, scheme, host, referer or headers, authentication, zoom."""
    url = unquote(source.url)
    quadkey = "{q}" in url
    tms = "{-y}" in url
    if not quadkey and not ("{x}" in url and "{z}" in url and ("{y}" in url or tms)):
        return None, NO_PLACEHOLDERS
    host = host_of(url)
    if not url.lower().startswith(("http://", "https://")) or not host:
        return None, NOT_HTTP
    if private_host(host):
        return None, PRIVATE_HOST
    if source.referer or source.headers:
        return None, HEADERS
    if source.auth_method not in ("", BASIC):
        return None, NOT_BASIC
    zooms = zoom_choices(source.zmin, source.zmax)
    if not zooms:
        return None, NO_ZOOM
    kind = QUADKEY if quadkey else TMS if tms else XYZ
    has_login = (bool(source.login) and bool(source.password)) or source.auth_method == BASIC
    return TileParams(kind, url.replace("{-y}", "{y}") if kind == TMS else url, zooms, has_login), ""


def zoom_choices(zmin: Optional[int], zmax: Optional[int]) -> Tuple[int, ...]:
    """The zooms the form offers: the layer's `zmin` to `zmax` (QGIS's own 0 and 18 when the source has none),
    and none above 21. Empty when the range has no zoom in 0 to 21."""
    low = max(QGIS_MIN_ZOOM if zmin is None else zmin, 0)
    high = min(QGIS_MAX_ZOOM if zmax is None else zmax, MAX_ZOOM)
    return tuple(range(low, high + 1))


def nearest_zoom(zooms: Iterable[int], wanted: Optional[int]) -> int:
    """The offered zoom nearest to `wanted` (18 when it is None); the higher one on a tie."""
    wanted = DEFAULT_ZOOM if wanted is None else wanted
    return min(zooms, key=lambda zoom: (abs(zoom - wanted), -zoom))


def user_defined(params: TileParams, zoom: int, credentials: Optional[Tuple[str, str]] = None) -> Dict[str, Any]:
    """The `sourceParams.userDefined` body. The login and password (`credentials`) are there only when both
    exist."""
    body: Dict[str, Any] = {"sourceType": params.source_type, "url": params.url, "zoom": int(zoom), "crs": CRS}
    login, password = credentials or ("", "")
    if login and password:
        body["rasterLogin"] = login
        body["rasterPassword"] = password
    return body


def match_offer(offers: Iterable[TileOffer], url: str, source_type: str) -> Optional[TileOffer]:
    """The first usable offer with this address and source type (Run again): `url` as `user_defined` sent it."""
    for offer in offers:
        if offer.params and offer.params.url == url and offer.params.source_type == (source_type or "").upper():
            return offer
    return None


# ---------- hosts ----------

_SHORT_IPV4 = re.compile(r"(?:0x[0-9a-f]+|\d+)(?:\.(?:0x[0-9a-f]+|\d+)){0,3}", re.IGNORECASE)


def host_of(url: str) -> str:
    """The host of an address, in lower case, with no user info and no port; "" when there is none. Never
    raises on a bad address."""
    try:
        return (urlsplit(url.strip()).hostname or "").lower()
    except ValueError:
        return ""


def private_host(host: str) -> bool:
    """Is this host the computer itself or a private network, so that Mapflow cannot reach it? Decided from the
    text alone: `ipaddress` and `inet_aton` parse text and send no DNS request. That covers `localhost`, a name
    ending `.localhost` or `.local`, a name with no dot (an intranet name), and an IP address that is loopback,
    private, link-local, shared (100.64.0.0/10), unspecified, reserved or multicast, IPv4 (also the short forms
    `127.1`, `0x7f.1` and a plain number) or IPv6."""
    host = host.strip().lower().rstrip(".")
    if host.startswith("[") and host.endswith("]"):
        host = host[1:-1]
    if not host or host == "localhost" or host.endswith((".localhost", ".local")):
        return True
    address = _ip_literal(host)
    if address is not None:
        if address.version == 6 and address.ipv4_mapped is not None:
            address = address.ipv4_mapped
        return not address.is_global
    return "." not in host


def _ip_literal(host: str):
    try:
        return ipaddress.ip_address(host.split("%", 1)[0])
    except ValueError:
        pass
    if _SHORT_IPV4.fullmatch(host):
        try:
            return ipaddress.IPv4Address(socket.inet_aton(host))
        except (OSError, ValueError):
            return None
    return None


# ---------- an address never reaches a message ----------

_ADDRESS = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)


def hide_addresses(text: str) -> str:
    """`text` with every http or https address replaced by its host: an address can carry a key. Other schemes
    (an `s3://` link in a message of Mapflow) stay."""
    return _ADDRESS.sub(lambda found: host_of(found.group(0)) or "an address", text)


def hide_address_params(params: Any) -> Any:
    """The error parameters of Mapflow with every string that holds an address passed through `hide_addresses`
    (also inside lists and dicts)."""
    if isinstance(params, dict):
        return {key: hide_address_params(value) for key, value in params.items()}
    if isinstance(params, (list, tuple)):
        return [hide_address_params(value) for value in params]
    if isinstance(params, str):
        return hide_addresses(params)
    return params
