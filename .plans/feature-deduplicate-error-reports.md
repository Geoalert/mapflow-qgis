# feature/deduplicate-error-reports

WAL step: **Deduplicate error-guard reports**

## Scope

`report_unexpected_error` shows one modal per occurrence. It is wired into
`Http.response_dispatcher`, which runs on every async response — including the timer-driven
polls. A recurring bug in a poll callback therefore spawns a dialog every few seconds.

## Findings that shaped the plan

1. **`use_default_error_handler=False` does not protect the guard.** In `http.py`
   `response_dispatcher`, *both* branches call `call_guarded`. The flag only skips
   `self.default_error_handler`; the callback (success branch) and the caller-supplied
   `error_handler` still run guarded. So the poll callbacks are exposed.

2. **The HTTP-error half of the storm is already mitigated**, crudely, at the three
   timer-driven call sites, each with a comment saying why:
   - `mapflow.py:482` `refresh_status` — "ignore errors to prevent repetitive alerts"
   - `mapflow.py:3042` — "it is done by timer, so we ignore errors to avoid stacking"
   - `processing_api.py:89` `get_processings` (6s poll)
   Consequence: real server errors on those paths are invisible. Once the throttle exists,
   those three can be flipped back to `True`. **Follow-up WAL entry, not this step.**

3. **Modals stack rather than queue.** `AlertService.alert` uses `box.exec()`
   (`alert_service.py:47`), a nested event loop — QTimer keeps firing while a modal is up.
   This is why an unthrottled recurring failure makes QGIS unusable rather than merely noisy.

4. Poll intervals (`config.py`): `PROCESSING_TABLE_REFRESH_INTERVAL` 6s,
   `TEMPLATE_TABLE_REFRESH_INTERVAL` 15s, `USER_STATUS_UPDATE_INTERVAL` 30s, plus a 500 ms
   startup timer (`mapflow.py:211`). The global floor is sized against the 6s figure.

## Decisions taken at the Confirmation Gate

- Spec delta approved: new `spec/006_error_reporting.md` + `spec/index.md` entry, in this MR.
- Throttle policy approved: per-signature escalating window 60s → ×2 → 30 min cap, plus a
  ~10s global floor across all signatures.

## Design

New module `mapflow/report_throttle.py`. Root level, deliberately:
- no Qt / QGIS imports → runs in the `functional` tier;
- `functional/service/` sits on the circular-import chain documented in
  `tests/functional/conftest.py`, and `error_guard.py` (a root module) must import this.

API:

```python
class ReportThrottle:
    def __init__(self, first_window, max_window, global_floor, clock=time.monotonic)
    def should_report(self, signature: str) -> Optional[int]
        # None  -> suppress (caller still logs)
        # int   -> show; value is how many were suppressed since the last shown report
    def reset(self) -> None   # tests
```

Signature = `type(exc).__name__` + final traceback frame `file:lineno`.
- Not the message: messages embed ids/paths and would defeat dedup.
- Not the context: the same failing line reached from two endpoints is one bug.
- No traceback → fall back to the type name alone.

## Steps

1. `mapflow/report_throttle.py` — `ReportThrottle`, `exception_signature`, module default instance.
2. `tests/functional/test_report_throttle.py` — injected clock, no sleeping.
3. `mapflow/http.py` — `get_exception_report_body(..., suppressed_count=0)`; add a
   `Repeated` line to the report dict when non-zero.
4. `mapflow/error_guard.py` — consult the throttle; always log; suppressed count into the
   dialog text and the mail body.
5. `tests/functional/test_error_guard.py` — extend for the throttled path.
6. `spec/006_error_reporting.md` + `spec/index.md`.
7. `WAL.md` — mark `[ready-for-review]`; add the follow-up entry for re-enabling the three
   `use_default_error_handler=False` workarounds.

## Discoveries during implementation

- The autouse `fresh_throttle` fixture in `test_error_guard.py` is load-bearing, not tidiness.
  The production throttle is process-wide, so without it the first test to report an error
  pushes every later test inside the 10s global floor — the existing dialog assertions would
  have gone vacuous without failing.
- `test_a_repeated_failure_shows_one_dialog` asserts `widget.call_count == 1`, which also
  proves the lazy `ErrorMessageWidget` import actually succeeds in the functional tier. Had
  the import chain raised, the guard's own `except` would have logged and the count would be
  0 — the assertion catches that, so this is not a vacuous pass.
- Latent, pre-existing, NOT fixed here: `report_unexpected_error` and `report_http_error`
  both build a widget into a local and call `.show()`. With no parent (both `parent=None`
  and `QApplication.activeWindow()` returning None) the widget can be garbage collected
  before it appears. Same shape at `mapflow.py:4179`. Out of scope for this step.

## Second commit — startup poll runaway (found in manual testing)

`app_startup_user_update_timer` (500 ms) only ever stopped from a `stop()` at the tail of
`set_processing_limit`. Guarded callback → exception swallowed → stop skipped → /user/status
+ /rasters/memory polled at 4 req/s for the session, UI looking healthy. Error branch had no
handler at all, so a real outage retried forever. `logout()` did not stop this timer.

Fixed: stop before configuring; skip ticks while in flight; bound the attempts with a
**latched** give-up; move `get_user_limit()` out of the tick into the success path.

The latch came from a test failure, not from review: `test_no_further_requests_after_the_budget_is_spent`
showed the give-up alert firing once per call. Production would not have hit it (the timer is
stopped), but "cannot fire again because the timer is stopped" is the exact reasoning that
produced the original bug, so the terminal state is now explicit.

`/rasters/memory` uses `use_default_error_handler=True` → on a real outage it opened an
`AlertService` modal every 500 ms, stacked via nested `exec()`. The report throttle does not
cover that path (it goes through `alert`, not `error_guard`). Removing it from the tick fixes
this instance; the general case is the WAL follow-up.

**Not committed:** the user's `TEMPORARY TEST INJECTION` block in `http.py`
`response_dispatcher` is still in the working tree, deliberately excluded from both commits.
It must be removed before the MR is un-drafted.

## Result

- `agent-make test`: 53 functional + 426 qgis pass; UI tier still the empty harness.
- `agent-make lint`: flake8, bandit, detect-secrets all clean.
- Commit `bae8c2c`, Draft PR #323 → `dev`.

Note: `agent-git push` reported "Draft MR targeting 'master'" and created no PR — GitLab
push options are no-ops on this GitHub remote, and the configured mr-target is `master`,
not `dev`. PR opened with `gh pr create --base dev` instead. Both facts contradict what
AGENTS.md promises; worth fixing in the doc or the repo config.
