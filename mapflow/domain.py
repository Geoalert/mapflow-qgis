"""The domain of the Mapflow addresses (spec/002_api.md, section "The `mapflow.ru` domain").

Pure Python: standard library only, no Qt and no QGIS.

The Mapflow backend is not reachable from some networks through `mapflow.ai`. `mapflow.ru` is a proxy of
the same service. When the QGIS global variable `mapflow_ru` is `true`, the plugin uses `mapflow.ru` in
every Mapflow address: the ones it builds (`config.py`), the links in its texts (`text_with_domain`), and
the addresses that the server gives in its answers (`url_with_domain`).
"""
import re

DEFAULT_DOMAIN = 'mapflow.ai'
RU_DOMAIN = 'mapflow.ru'

_CHANGED_SCHEMES = ('http', 'https')


def domain_from_setting(value) -> str:
    """The domain for a value of the QGIS global variable `mapflow_ru`: `mapflow.ru` for `true` (any case,
    spaces removed), `mapflow.ai` for every other value and for no value."""
    return RU_DOMAIN if str(value or '').strip().lower() == 'true' else DEFAULT_DOMAIN


def url_with_domain(url, new: str, old: str = DEFAULT_DOMAIN):
    """`url` with the domain `old` replaced by `new` in its host, when the host is `old` or ends with `.old`.

    For one address, such as an address from a server answer. Everything else stays as it is, character by
    character: the text is sliced, never parsed and rebuilt, so a tile template (`{z}/{x}/{y}`) and a
    presigned query keep their form. These stay unchanged: a value that is not text, `new == old`, a scheme
    other than http and https, a relative address, an IPv6 host, and a host that only contains `old` (`old`
    in the path, the query, the user part or a longer name).
    """
    if not isinstance(url, str) or not url or new == old or not old:
        return url
    scheme, separator, rest = url.partition('://')
    if not separator or scheme.lower() not in _CHANGED_SCHEMES:
        return url
    end = len(rest)
    for mark in '/?#':
        found = rest.find(mark)
        if found != -1:
            end = min(end, found)
    authority = rest[:end]
    start = authority.rfind('@') + 1                    # skip the user part, if the address has one
    host_end = len(authority)
    colon = authority.rfind(':')
    if colon >= start and authority[colon + 1:].isdigit():
        host_end = colon                                # skip `:port`
    host = authority[start:host_end]
    if host.startswith('['):                            # an IPv6 host
        return url
    lowered, old_lowered = host.lower(), old.lower()
    if lowered != old_lowered and not lowered.endswith('.' + old_lowered):
        return url
    cut = len(scheme) + len(separator) + start + len(host) - len(old)
    return url[:cut] + new + url[cut + len(old):]


def text_with_domain(text, new: str, old: str = DEFAULT_DOMAIN):
    """`text` with the domain `old` replaced by `new` wherever it stands as a whole domain.

    For a text that holds links: an HTML text of a label, a translated message, the JSON of the sign-in
    configuration. `app.mapflow.ai`, `https://mapflow.ai/pricing` and the visible word `mapflow.ai` change.
    A longer name (`notmapflow.ai`, `mapflow.ai.example.com`, `mapflow.aix`) and an e-mail address
    (`name@mapflow.ai`) do not.
    """
    if not isinstance(text, str) or not text or new == old or not old:
        return text
    pattern = r'(?<![\w@-])' + re.escape(old) + r'(?![\w-]|\.\w)'
    return re.sub(pattern, lambda _match: new, text, flags=re.IGNORECASE)
