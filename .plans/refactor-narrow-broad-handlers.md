# refactor/narrow-broad-handlers

Last Phase A chore. Scratchpad — gitignored.

## Why the WAL entry was rewritten

The entry's acceptance was "`E722` out of the `.flake8` ledger, bandit reports no `B110`".
Both were already true on `dev`: the bare `except:` were fixed in `93a7d65`, which took `E722`
out of the ledger, and bandit reports no `B110` because there are no `except/pass` handlers
left. A criterion that cannot fail is not a criterion.

The count in the entry (38) was also stale — there are 54.

But counting `except Exception` was never the right metric. Measured on `dev`:

| | count |
|---|---|
| broad handlers that surface the failure (log a traceback, re-raise, or alert the user) | 23 |
| broad handlers that swallow silently | 31 |

A broad handler that logs a traceback hides nothing. A *narrow* `except ValueError: pass`
hides plenty. So the invariant is about surfacing, not about the width of the except clause.

## The rule this step establishes

A handler catching `Exception` must surface the failure: log it with a traceback, re-raise,
or tell the user. Otherwise it must name the exceptions it expects.

Enforced by `tests/functional/test_exception_reporting.py`, because flake8 has no rule for
it — same reasoning as `test_layering.py`.

## The four template callbacks

`pause/resume/restart/delete_template_callback` are **success** callbacks; refusals go to
their own `*_error_handler`. Each wrapped `get_processings()` + the success alert in
`except Exception: alert("Failed to pause template: {e}")`.

`get_processings()` only dispatches — it reads `dlg.filterProcessings.text()`, builds the
request and hands it to the api; the reply lands in `get_processings_callback`, outside the
try. So the handler could only ever catch a *refresh dispatch* failure and report it as a
pause failure, while the template was in fact paused. The success alert sat inside the try
after the refresh, so the user would see only the false failure.

User's call (approved in chat): remove them. The table refreshes on the poll timer anyway, so
a failed refresh dispatch does not warrant a message; a real failure now reaches the guard in
`Http.response_dispatcher` and is reported as the unexpected error it is.

## Result

54 broad handlers → 32; 31 silent → 1 (the allowlisted logging handler). The 32 that stay are
the ones that log a traceback, re-raise, or put the exception in front of the user.

## Discoveries

**`api_message_parser` never raises.** It already catches `(ValueError, AttributeError,
TypeError)` and returns None, with a broad logging handler behind that. Two call sites in
`processing_service` wrapped it in `try/except Exception` anyway — dead code, removed rather
than narrowed. Worth knowing before Phase C moves those callers around.

**Three sites keep `except Exception` deliberately.** `get_bounding_box_from_tile_json` parses
JSON, indexes `bounds` and reprojects through pyproj, so its failure set genuinely spans
ValueError, TypeError, AttributeError, IndexError and pyproj's own errors. Listing that tuple
would be `Exception` with extra steps, so those three now log instead — which is the point of
the rule.

**`PluginError` subclasses `ValueError`.** So `except PluginError` in
`area_calculator_service.calculate_aoi_area` is narrower than it looks in a file that also
catches ValueError elsewhere. Noted because the reverse mistake — assuming a plugin error is
caught by `except ValueError` somewhere unintended — is easy to make during the extraction.

## Mutation verification

Both new assertions were verified by breaking the code they cover, in the container:

1. `_parse_template_response` back to `except Exception: return None` →
   `test_no_broad_handler_swallows_silently` fails, naming
   `processing_service.py:749 in ProcessingService._parse_template_response`.
2. `log_config`'s handler made to surface (`as exc` + a use) →
   `test_the_allowlist_has_no_stale_entries` fails, naming the now-stale entry.

Both reverted; `agent-git diff --stat` no longer lists `log_config.py`.
