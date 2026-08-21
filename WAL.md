# Journal for active implementation planning

## 1. Add new zoom-selector feature
[ ]
- Use 002_E_zoom_selector_api.md
- Add a small button near zoom selector comboBox to call zoom-selector API, active when selected source is a Mapflow data provider.
- On button press, call API and select zoom automatically depending on response.
- On error, show a reasonable user-facing message.

## 2. Refactor try/except for more granular exception handling
[ ]
- The 3.6.0 security scan flagged several broad `try/except Exception` blocks that only logged
  (previously swallowed silently). Narrow them to the specific exceptions actually expected, so
  unrelated errors surface instead of being logged and ignored.
- Also revisit the `assert` statements in errors/error_message_list.py (Bandit B101: asserts are
  stripped under `python -O`) — turn the sanity checks into real error handling if they must run.
