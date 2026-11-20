"""File names made from text the server sent (no Qt, no qgis)."""
import hashlib


def safe_stem(text: str) -> str:
    """`preview_` and 16 hex digits of the SHA-256 of `text`: no separator, no dot and no part of `text`.
    The same text gives the same stem; different texts give different stems."""
    digest = hashlib.sha256(text.encode("utf-8", "surrogatepass")).hexdigest()
    return f"preview_{digest[:16]}"


_FORBIDDEN = set('<>:"|?*')


def _plain_name(text) -> str:
    last = str(text or "").replace("\\", "/").split("/")[-1]
    kept = "".join(c for c in last if c >= " " and c != "\x7f" and c not in _FORBIDDEN)
    return kept.strip(". ")


def safe_filename(name, fallback) -> str:
    """A file name the user can be offered, from a name the server sent: its last path part, with no control
    character and none that a file name can't hold, and no dot or space at its ends. When nothing is left, the same
    cleaning of `fallback`; when that is empty too, "download"."""
    return _plain_name(name) or _plain_name(fallback) or "download"
