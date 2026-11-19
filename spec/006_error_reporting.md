# 006 Error reporting

## Purpose
Define how a failure reaches the user, which failures are allowed to interrupt them, and
what keeps an interruption from becoming a lockout.

## Content

### Expected versus unexpected

Two categories, handled differently. Deciding which one a failure belongs to is the first
question at every `except`.

**Expected** — the failure is a foreseeable outcome of the operation: a validation error, a
rejected input, a missing selection, a documented API error code, a network that is down. It
is caught narrowly at the point it occurs, and answered there with a message that tells the
user what to do ("Choose the imagery in the form"). It is not a bug, and it must never offer
a report: training users to send reports for their own typos, or for their own proxy,
guarantees the real reports get ignored too.

**Unexpected** — the failure means plugin code is wrong. There is no correct local
handling, because the code that would handle it is the code that is broken. It goes through
the **guard**, which logs it with a traceback and offers a pre-filled report the user can
send.

An unexpected failure must never reach Qt's event loop unguarded. QGIS then shows its own
raw unhandled-exception dialog, which names the plugin, offers the user no action, and is
dismissed without a report ever being sent.

### The three presentation tiers

| tier | mechanism | use for |
|---|---|---|
| log | `QgsMessageLog` (the QGIS message log) | everything, always; the complete record |
| message | a line in the QGIS message bar, or an issue shown next to the control it is about | expected failures the user can act on |
| report | a Critical line in the message bar with a **"Send a report"** button, which opens the report dialog | unexpected failures only |

The log tier is unconditional. It is where a developer reconstructs how often something
fired and in what order, which is exactly the information the other two tiers discard.

**No tier opens a modal dialog by itself.** A message-bar line does not take the focus and
does not run a nested event loop. The report dialog is modal, but only the user opens it, by
pressing the button on the line.

### The report dialog

- It shows a one-line summary of what failed and the full report text, read-only: the
  exception and its traceback, the plugin version, the QGIS and Qt versions, the operating
  system and the environment name. For a failure of a request it also carries the method,
  the URL **without its query string**, the HTTP status and the response body. It never
  carries a token, a password or an `Authorization` header.
- It has **an input for the user's own comment** — what they were doing — which goes into
  the report above the technical part.
- "Send" opens the user's mail client with the report addressed to Mapflow support
  (a `mailto:` link). **Nothing is sent without that action**, and nothing is sent by the
  plugin itself: the user sees the whole text before it leaves. "Copy" puts the same text on
  the clipboard, for a mail client that cuts a long `mailto:` short.
- Connectivity failures do not get the button: offline, a proxy error, a timeout, 403 and
  5xx are message tier.

### The guard

One guard serves every layer that owns a Qt entry point, so it lives where the controller,
the services, `plugin.py` and the HTTP client can all import it — not inside
`controller.py`.

**Every entry point Qt calls into is guarded**: slots of QGIS and Qt signals (layers,
project, map canvas, actions, menus, timers), slots of the plugin's own signals, and the
callbacks the HTTP client runs. A `lambda` connected to a signal is an entry point like any
other. How this is enforced is open: a source check in `tests/test_core.py`, like the ones for
the Qt 5/6 rules, is the intended form.

**The HTTP client guards the callbacks it runs.** `Http` separates two things that the same
`try` must not cover:

- reading the response — a body that is not the JSON the endpoint promises is an
  *expected* failure, "Unexpected response from Mapflow", and goes to the request's
  `on_error`;
- running the caller's `on_success` — an exception there is an *unexpected* failure of
  plugin code. It is logged with its traceback, reported through the guard, and then the
  request's `on_error` runs **once**, so the caller's cleanup still happens. A `ValueError`
  raised by callback code is never shown as a bad response from Mapflow.

Either way a request ends in exactly one outcome for its caller: `on_success` completed,
or `on_error`.

### Volume

**Contract: no failure, however often it recurs, may lock the user out of QGIS.**

The 3.x plugin opened its report dialog itself, with `exec()`. That runs a nested event
loop, so `QTimer` keeps firing while a dialog is up and dialogs *stack* rather than queue;
an unthrottled failure on a polled path made QGIS unusable, and the plugin needed a
throttle (`report_throttle`: per-signature windows, a global floor) to bound it.

Mapflow Next meets the contract by construction instead, and **has no throttle**:

- nothing opens a dialog from a timer path, or from any path the user did not start;
- a timer-driven request that fails is silent until it has failed repeatedly, and then
  says so once (`spec/005` § Failed requests);
- a timer-driven request that fails for good stops.

What remains: a slot on a timer that raises on every tick adds one Critical line to the
message bar per tick. The lines are not modal and QGIS stacks them behind a counter, so
this is noise, not a lockout. It is accepted. If live use shows otherwise, the answer is a
per-signature limit on the lines (exception type plus the source line it was raised from —
not the message, which carries ids), and this section is where it gets specified.

### A guarded callback is interrupted, not completed

The guard swallows the exception and returns. Everything after the raise point in that
callback **does not run** — including work the callback owns rather than merely performs:
stopping a timer, clearing an in-flight flag, closing a dialog, releasing a lock.

So a callback that owns a state transition must perform it **before** anything that can
raise, or in a `finally`. Placing it at the end is only correct for code that cannot fail,
and a network callback parsing a server payload always can.

This is not theoretical. In the 3.x plugin `set_processing_limit` ended with the stop for
the 500 ms startup retry timer. When the response was malformed, the callback raised on the
way there, the guard absorbed it, the timer was never stopped, and the plugin re-issued
/user/status and /rasters/memory twice a second for the rest of the session — while the UI
looked healthy. Mapflow Next had the same shape twice when this rule was written for it:
a result whose bounds could not be transformed left the "loading" flag of its processing
set until sign-out, and a file that disappeared between the upload check and the upload
left "uploading" set, so every later upload returned without a word.

Two corollaries:

- **A flag set before a request is cleared on every way out of it**: success, the
  request's failure, and an exception in the code between them (a file that can no longer
  be read, a response that lacks a field).
- **A poll that retries until it succeeds needs a bound and a terminal state**, and the
  terminal state must be latched rather than implied by a stopped timer. "It cannot fire
  again because we stopped the timer" is the same reasoning that failed above.

### The tests must see what the guard hides

A guard that turns exceptions into message-bar lines also turns failing tests into passing
ones, unless the tests look at the message bar. The end-to-end flow therefore **fails on
any Critical message it did not ask for** (`spec/004` § Test runtime). A check that
exercises a guarded path and asserts only on state proves nothing about whether the path
raised.

### Consequences for new code

- Any new timer-driven or event-loop-driven entry point routes unexpected failures through
  the guard, never to a raw modal, and never to a bare log-and-continue.
- A callback reached through the guard must not leave cleanup after code that can raise.
- A request that opts out of telling the user about its failure must say in a comment why,
  and must still clear what it left pending. Tolerating a transient failure of a polled
  request is `spec/005` § Failed requests' job, never a silent opt-out's.
- Suppression must never be implemented by dropping log records.
