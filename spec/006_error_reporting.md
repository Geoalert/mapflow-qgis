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

### Volume limit

**Contract: no failure, however often it recurs, may produce an unbounded number of
dialogs.**

This is not a nicety. Plugin modals are opened with `exec()`, which runs a nested event
loop, so `QTimer` keeps firing while a dialog is up and dialogs *stack* rather than queue.
Several plugin operations are timer-driven — processing table refresh (6s), template table
refresh (15s), user status (30s) — so an unthrottled failure on any polled path renders
QGIS unusable. That is a worse outcome than the unhandled exception the reporting was
introduced to replace.

`mapflow/report_throttle.py` implements the limit:

- Failures are identified by **signature** — exception type plus the source line it was
  raised from. Not the message (messages carry ids and would make every occurrence look
  new) and not the operation context (one broken line reached from two call paths is one
  bug).
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

### Consequences for new code

- Any new timer-driven or event-loop-driven entry point must route unexpected failures
  through `error_guard`, never to a raw modal, and never to a bare log-and-continue.
- A network call that opts out of user-facing error handling
  (`use_default_error_handler=False`) must say in a comment why. Opting out to dodge repeat
  alerts is superseded by the throttle and should be reconsidered rather than copied.
- Suppression must never be implemented by dropping log records.
