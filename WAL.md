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

## 3. Hotfix 3.6.3: My Imagery image download crash
[ready-for-review]
- A lambda slot capturing its own QNetworkReply is a cycle PyQt exposes to the cyclic GC; with nothing
  else holding the reply, a GC pass mid-download tears the slot down — the image is silently never saved,
  or QGIS segfaults on `finished`. Long downloads make that GC pass near-certain, hence "some images".
  Slots are now methods using sender(), and the service holds each in-flight reply until it finishes.
- Streamed through QSaveFile rather than readAll(): Qt5's QByteArray caps at 2 GiB and the old path held
  the image 2-3x in memory. QSaveFile also gives the atomic replace, so a failure leaves no partial file.
- `Http.send_request` has the same lambda shape but survives because its abort-timer closure also holds
  the reply — safe by accident; keep it in mind when touching http.py.
- dev has the same bug behind `guarded_connect`; port the fix there after this merges.
