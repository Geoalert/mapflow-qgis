"""The one rule for an address that came from a server answer when the plugin uses another domain (spec/002,
the section about the second domain). Pure Python: standard library only.

The caller names both domains, so this file holds no address of either. `Http` applies it to a request and
`MapLayers` to a layer source; nothing else calls it, and no address that goes back to the server in a request
body passes through it.
"""
from __future__ import annotations

_CHANGED_SCHEMES = ("http", "https")


def with_domain(url: str, old: str, new: str) -> str:
    """`url` with the domain `old` replaced by `new` in its host, when the host is `old` or ends with `.old`.

    Everything else stays as it is, character by character: the text is sliced, never parsed and rebuilt, so
    a tile template (`{z}/{x}/{y}`), a presigned query and an empty `?` keep their form. These stay unchanged:
    a value that is not text, `new == old`, a scheme other than http and https, a relative address, an IPv6
    host, a host that only contains `old` (`old` in the path, the query, the user part or a longer name), and a
    host with a trailing dot (`old.`).
    """
    if not isinstance(url, str) or not url or new == old or not old:
        return url
    scheme, separator, rest = url.partition("://")
    if not separator or scheme.lower() not in _CHANGED_SCHEMES:
        return url
    end = len(rest)
    for mark in "/?#":
        found = rest.find(mark)
        if found != -1:
            end = min(end, found)
    authority = rest[:end]
    start = authority.rfind("@") + 1                     # skip `user:password@`
    host_end = len(authority)
    colon = authority.rfind(":")
    if colon >= start and authority[colon + 1:].isdigit():
        host_end = colon                                  # skip `:port`
    host = authority[start:host_end]
    if host.startswith("["):                              # an IPv6 host
        return url
    lowered, old_lowered = host.lower(), old.lower()
    if lowered != old_lowered and not lowered.endswith("." + old_lowered):
        return url
    cut = len(scheme) + len(separator) + start + len(host) - len(old)
    return url[:cut] + new + url[cut + len(old):]
