"""File names made from text the server sent (no Qt, no qgis)."""
import hashlib


def safe_stem(text: str) -> str:
    """`preview_` and 16 hex digits of the SHA-256 of `text`: no separator, no dot and no part of `text`.
    The same text gives the same stem; different texts give different stems."""
    digest = hashlib.sha256(text.encode("utf-8", "surrogatepass")).hexdigest()
    return f"preview_{digest[:16]}"
