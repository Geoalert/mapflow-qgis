"""Which requests may carry Mapflow credentials: only those of the API's own scheme, host and port.

No Qt and no qgis import: the caller passes the parts of the URL that it is going to send.
"""
from __future__ import annotations

import ipaddress
from typing import NamedTuple, Optional

DEFAULT_PORTS = {"http": 80, "https": 443}


class Origin(NamedTuple):
    scheme: str
    host: str
    port: int

    @classmethod
    def from_parts(cls, scheme: str, host: str, port: int = -1) -> Optional["Origin"]:
        """The origin of a URL's parts, or None when the URL has no scheme or no host (a relative or broken one).
        `port` is -1 or 0 when the URL names none."""
        scheme = (scheme or "").strip().lower()
        host = (host or "").strip().lower().rstrip(".")
        if not scheme or not host:
            return None
        if not port or port < 0:
            port = DEFAULT_PORTS.get(scheme, -1)
        return cls(scheme, host, port)


def is_local(host: str) -> bool:
    """`localhost` or a loopback address: a test host that needs no TLS."""
    host = (host or "").strip().lower().rstrip(".")
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host.strip("[]")).is_loopback
    except ValueError:
        return False


def carries_credentials(request: Optional[Origin], api: Optional[Origin]) -> bool:
    """True when the request goes to the API's own origin, over https or to a local test host."""
    if request is None or api is None or request != api:
        return False
    return api.scheme == "https" or is_local(api.host)
