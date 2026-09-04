# 006 Error reporting

## Purpose
Define how a failure reaches the user, which failures are allowed to interrupt them, and
the volume limit that keeps an interruption from becoming a lockout.

## Content

### Expected versus unexpected

Two categories, handled differently. Deciding which one a failure belongs to is the first
question at every `except`.

**Expected** — the failure is a foreseeable outcome of the operation: a validation error, a
rejected input, a missing selection, a documented API error code. It is caught narrowly at
the point it occurs, and answered there with a message that tells the user what to do
("Please select a valid area of interest"). It is not a bug, and it must never open a
report dialog: training users to send reports for their own typos guarantees the real
reports get ignored too.

**Unexpected** — the failure means plugin code is wrong. There is no correct local
handling, because the code that would handle it is the code that is broken. It goes through
`mapflow/error_guard.py`, which logs it with a traceback and offers a pre-filled report the
user can send.

An unexpected failure must never reach Qt's event loop unguarded. QGIS then shows its own
raw unhandled-exception dialog, which names the plugin, offers the user no action, and is
dismissed without a report ever being sent.

### The three presentation tiers

| tier | mechanism | use for |
|---|---|---|
| log | `logging` → QGIS message log | everything, always; the complete record |
| message | `AlertService` modal / message bar | expected failures the user can act on |
| report | `ErrorMessageWidget` + "Send a report" | unexpected failures only |

The log tier is unconditional and is never thinned by suppression. It is where a developer
reconstructs how often something fired and in what order, which is exactly the information
the other two tiers discard.

### Where each tier lives

Both tiers live in `infra/` (`mapflow/infra/`): `alert_service` for the message tier, the reporter
for the report tier. `infra/` is the one layer every other layer may import, and the one layer
allowed to hold Qt types (`spec/007_architecture.md` § Layer rules).

The **message** tier is `AlertService`, in `infra/` — **not a service**: `alert_*`, `ask_text` and
anything else that needs a synchronous answer from the user. It owns the Qt types so its callers do
not import them. It is in `infra/`, not `service/`, because a service may not import a widget yet
this tier builds `QMessageBox`/`QInputDialog`, and because a view may not import a service yet views
legitimately raise message-tier alerts (e.g. the processings table's failed/finished
notifications). `infra/` is the only home reachable from services, views, apis and controllers
alike; a service-tier message helper is neither.

The **report** tier lives in `infra/` too. Two reasons, and the second is the binding one:

- it is reached from `Http`, which is itself infra and must not depend on a service singleton;
- every layer may import `infra/`, so putting it there makes it reachable from services, api
  modules and controllers alike, whereas a service-tier reporter is reachable only downward.

A service or api that needs to report an unexpected failure imports the reporter from `infra/`. It
does not emit a signal for someone else to report on its behalf, and it does not construct
`ErrorMessageWidget`. The reporter itself may import `ErrorMessageWidget` from `dialogs/` (an
`infra → dialogs` edge, kept lazy so a headless context need not build the widget tree).

### Volume limit

**Contract: no failure, however often it recurs, may produce an unbounded number of
dialogs.** This covers *every* dialog tier — report and message alike.

This is not a nicety. Plugin modals are opened with `exec()`, which runs a nested event
loop, so `QTimer` keeps firing while a dialog is up and dialogs *stack* rather than queue.
Several plugin operations are timer-driven — processing table refresh (6s), template table
refresh (15s), user status (30s) — so an unthrottled failure on any polled path renders
QGIS unusable. That is a worse outcome than the unhandled exception the reporting was
introduced to replace.

None of that is specific to the report dialog: a message-tier modal saying "Could not refresh"
on a 6-second poll locks QGIS exactly as thoroughly as an unthrottled crash report.

`mapflow/report_throttle.py` implements the limit:

- Failures are identified by **signature**. For an exception: its type plus the source line it
  was raised from. Not the message (messages carry ids and would make every occurrence look
  new) and not the operation context (one broken line reached from two call paths is one
  bug). For an HTTP failure, where there is no raising frame to key on: the **Qt error code
  plus the endpoint path**, query string excluded — the same string the report body carries,
  for the same reason, since a query carries ids and tokens that would make every occurrence
  distinct.
- A signature that has just been reported is suppressed for a **window**, starting at 60s —
  above the slowest poll interval — and **doubling on each further report**, capped at
  30 minutes. A persistent failure therefore still resurfaces a couple of times an hour
  rather than going permanently silent.
- A **global floor** of 10s applies between any two reports regardless of signature. Per-
  signature suppression alone does not stop several *different* exceptions rotating through
  the same 6-second callback.
- Suppressed occurrences are counted, and the count is carried into both the dialog text
  and the report body. A traceback that fired 200 times describes a different bug from one
  that fired once, and the single traceback cannot show the difference.

The four numbers above are **configuration, in `config.py`, not constants in
`report_throttle.py`.** They were derived from poll intervals rather than from watching anyone
use the plugin, so they are a first guess that live UX testing is expected to move. Reasoning
about them stays here; the values do not.

### A guarded callback is interrupted, not completed

The guard swallows the exception and returns. Everything after the raise point in that
callback **does not run** — including work the callback owns rather than merely performs:
stopping a timer, clearing an in-flight flag, closing a dialog, releasing a lock.

So a callback that owns a state transition must perform it **before** anything that can
raise, or in a `finally`. Placing it at the end is only correct for code that cannot fail,
and a network callback parsing a server payload always can.

This is not theoretical. `set_processing_limit` ended with the stop for the 500 ms startup
retry timer. When the response was malformed, the callback raised on the way there, the
guard absorbed it, the timer was never stopped, and the plugin re-issued /user/status and
/rasters/memory twice a second for the rest of the session — while the UI looked healthy.
The guard did not cause that loop, but by absorbing the exception it removed the only
signal that it was running.

Corollary for retry loops: a poll that retries until it succeeds needs a bound and a
terminal state, and the terminal state must be latched rather than implied by a stopped
timer. "It cannot fire again because we stopped the timer" is the same reasoning that
failed above.

### Consequences for new code

- Any new timer-driven or event-loop-driven entry point must route unexpected failures
  through `error_guard`, never to a raw modal, and never to a bare log-and-continue.
- A callback reached through the guard must not leave cleanup after code that can raise.
- A network call that opts out of user-facing error handling
  (`use_default_error_handler=False`) must say in a comment why. Opting out to dodge repeat
  alerts is superseded by the throttle and should be reconsidered rather than copied.
- Suppression must never be implemented by dropping log records.
