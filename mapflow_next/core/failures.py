"""What a failed request means for the user, by what triggered it (spec/005 § Failed requests).

Pure Python: the services decide with these rules, and the Qt side only shows the text they return.
"""
from __future__ import annotations

import re
from typing import Optional

from .formatting import km2

# What triggered a request. The rule follows the trigger, not the endpoint.
USER = "user"        # a click, a search, a refresh button: the user waits on it
LOAD = "load"        # a one-off load nobody waits on
POLL = "poll"        # a timer sends it again on its own

DROP, ALERT, STOP = "drop", "alert", "stop"

# The connection or the server, not the request: asking again can change the answer.
TRANSIENT_KINDS = ("offline", "proxy", "timeout", "server")
_STRONGER = {USER: 3, LOAD: 2, POLL: 1}


def is_transient(kind: str, status: Optional[int] = None) -> bool:
    """`client` without a status is a connection-level Qt error `classify` has no name for (SSL, an unknown
    network error): the connection, not the request. `client` with a status is another 4xx: permanent.
    Two kinds are neither: "auth" belongs to the session (it renews the token or signs the user out and says
    so), and "plugin" means a callback of the plugin raised (the guard has already told the user)."""
    return kind in TRANSIENT_KINDS or (kind == "client" and status is None)


def keeps_schedule(kind: str, status: Optional[int] = None) -> bool:
    """A timer's request that failed in a way asking again may fix, or that the session decides: a 401 makes the
    session renew the token (the poll goes on) or sign out (which stops every timer)."""
    return is_transient(kind, status) or kind == "auth"


def stronger(first: Optional[str], second: Optional[str]) -> Optional[str]:
    """The trigger the user feels most: USER over LOAD over POLL. A refresh asked for while another is in flight
    is sent with this one."""
    return max((first, second), key=lambda trigger: _STRONGER.get(trigger or "", 0)) or None


class PollFailures:
    """The failures of one timer's request. Transient ones are counted: the user is told once, at `threshold`
    in a row. A permanent one stops the timer for good until a success (`stopped` is a latch: a stopped timer
    alone cannot tell "nobody asked" from "asking is pointless")."""

    def __init__(self, threshold: int):
        self.threshold = threshold
        self.count = 0
        self.stopped = False

    def failed(self, kind: str, status: Optional[int] = None) -> str:
        if kind in ("auth", "cancelled"):
            return DROP
        if kind == "plugin":
            self.stopped = True
            return STOP                 # a bug repeats on every tick; the guard's line is the user's notice
        if is_transient(kind, status):
            self.count += 1
            return ALERT if self.count == self.threshold else DROP
        self.stopped = True
        return STOP

    def succeeded(self) -> None:
        self.count = 0
        self.stopped = False


def poll_notice(outcome: str, what: str, error_message: str, kind: str = "") -> str:
    """The line for the message bar: "" when nothing is to be said (`DROP`, or `STOP` after a plugin error)."""
    if outcome == ALERT:
        return f"Mapflow is not answering: the {what} could not be refreshed several times in a row. {error_message}"
    if outcome == STOP and kind != "plugin":
        return f"The {what} is no longer refreshed: {error_message}"
    return ""


def empty_list_text(what: str, none_text: str, loaded: bool, loading: bool, failed: bool) -> str:
    """The text of a list with no rows. `none_text` ("No processings in this project yet.") only after a
    successful answer with no items: a list that failed to load must not look empty."""
    if loading or (not loaded and not failed):
        return f"Loading {what}…"
    if failed:
        return f"{what[:1].upper()}{what[1:]} didn't load."
    return none_text


def project_gone_text(name: str, opened_default: bool) -> str:
    label = f"“{name}”" if name else "The project"
    if opened_default:
        return f"{label} is gone or no longer shared with you. The default project is open instead."
    return f"{label} is gone or no longer shared with you, and there is no other project to open."


def project_deleted_text(name: str, opened_default: Optional[bool]) -> str:
    """The notice after a delete. `opened_default` is None when the deleted project was not the open one."""
    label = f"Project “{name}”" if name else "The project"
    if opened_default is None:
        return f"{label} is deleted."
    if opened_default:
        return f"{label} is deleted. The default project is open instead."
    return f"{label} is deleted, and there is no other project to open."


BACKGROUND_SEARCH_NOTE = "Note, you can run the background search in Mapflow Web."
_AREA_SIZES = re.compile(r"gotArea\W*(?P<got>\d+(?:\.\d+)?).*?allowedArea\W*(?P<allowed>\d+(?:\.\d+)?)",
                         re.IGNORECASE | re.DOTALL)


def search_area_text(message: str) -> Optional[str]:
    """The catalog search's refusal of a large area, e.g. "Too large extent of AOI (gotArea: 701687808,
    allowedArea: 250000000)" (m²), as a line the user can act on, with the note that Mapflow Web searches larger
    areas in the background. None for any other message."""
    message = message or ""
    sizes = _AREA_SIZES.search(message)
    if not sizes and "too large extent" not in message.lower():
        return None
    if sizes:
        got, allowed = float(sizes.group("got")) / 1e6, float(sizes.group("allowed")) / 1e6
        text = f"The area is too large to search here: {km2(got)}, the limit is {km2(allowed)}. Choose a smaller area."
    else:
        text = "The area is too large to search here. Choose a smaller area."
    return f"{text} {BACKGROUND_SEARCH_NOTE}"
