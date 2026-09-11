# WAL 3 — Hotfix 3.6.3: My Imagery image download crash (handover)

Branch `fix/stream-image-download` → PR into `master`. Remove this file once the PR is approved.

## Report
QGIS 3.34.6 (macOS) crashed when downloading some images from My Imagery:
`EXC_BAD_ACCESS at 0x18` on the main thread, in
`QNetworkReplyHttpImplPrivate::finished → PyQtSlotProxy::unislot → PyQtSlot::invoke → PyQtSlot::call`.

## Root cause
`DataCatalogService._download_file_from_url` connected
`reply.finished` to `lambda: self._save_downloaded_file(reply, save_path)`.

- PyQt's QObject GC support (`%GCTraverseCode` → `qpycore_visitSlotProxies`) reports a connected Python
  slot as owned by the sender's wrapper. The lambda's closure holds `reply`, so wrapper ↔ lambda is a
  cycle, and once the function returns nothing outside the cycle references either.
- Any cyclic GC pass while the download is in flight collects it. The teardown order decides the outcome:
  - reply wrapper cleared first → PyQt drops the slot → the download finishes and nothing is saved, silently;
  - lambda cleared first (its generation is younger, e.g. an incidental gen-0 pass between `nam.get()` and
    the lambda's creation, then a full pass) → `func_clear` NULLs `func_code` while the C++ proxy still
    holds the function → `finished` calls it → `_PyFunction_Vectorcall` reads `co->co_kwonlyargcount`
    at NULL+0x18.
- The crash report's instruction bytes decode to exactly that load (`83 7e 18 00` = `cmp [rsi+0x18],0`
  with `rsi = func->func_code`); the `???` frame is the unsymbolised `_PyFunction_Vectorcall`.
- "Some images": large images download long enough for a GC pass to land mid-flight.
- The `mach_vm_allocate_kernel failed` lines in the report's kernel triage are unrelated noise.

## Evidence
- Standalone repro with the local QGIS-LTR 3.34.9 runtime (Python 3.9.5, PyQt 5.15.4, Qt 5.15.2) and a
  slow local HTTP server: no GC → saved; GC mid-flight → silently never saved; GC with the lambda cleared
  first → SIGSEGV whose macOS crash report matches the user's (same fault address, same frame offsets
  `call+39 / invoke+374 / unislot+85`, identical instruction bytes).
- The new tests against the OLD code: the streaming test fails and the runner itself segfaults (exit 139)
  while pytest-qt processes events — the production crash, reproduced in the Docker image (QGIS 3.28,
  Python 3.10).
- Candidate fixes (hold the reply on the service; bound method + `sender()`) both survive the crashing order.

## Fix
- `_download_file_from_url` opens a `QSaveFile` first (unwritable target → alert, no request), sends the
  request, stores `reply → QSaveFile` in `self._downloads`, connects `readyRead` / `finished` to methods.
- `_on_download_ready_read` writes each chunk; a failed write aborts the reply (the finished handler reports
  the file error — the chunk handler must never alert, `view.alert` is a blocking modal).
- `_on_download_finished` pops the entry, writes any remainder, then commits or discards (`cancelWriting` +
  `commit`) and reports. Message texts are unchanged, so existing translations still match.
- Spec: `002_C_myimagery_api.md` § Client-side download (user-approved delta); `005_interactions.md`
  Local Filesystem; `spec/index.md` entry.
- Version 3.6.3: `metadata.txt` (version + changelog), `CHANGELOG.md`.

## Tests (`tests/qgis/test_data_catalog.py::TestImageDownloadToDisk`)
Real `QgsNetworkAccessManager` + a threaded local HTTP server; the service is built by its real constructor
(api/view stubbed) so `sender()` and the `_downloads` initialiser are exercised for real.
- served bytes saved + success message names the path, no temp file left;
- mid-download the bytes are on disk and the target does not exist yet;
- `gc.collect()` mid-download does not lose the completion (the regression);
- HTTP 403 keeps an existing file; dropped connection leaves no partial file;
- unwritable target → alert and no request reaches the server.

Mutation checks: removing `cancelWriting()` → 403 + drop tests fail; skipping the up-front `open()` return
→ unwritable test fails. Removing the tail `write(readAll())` in the finished handler SURVIVES: Qt emitted
readyRead for every byte in all scenarios; the line is defensive and commented as such.

## Verification status
- `agent-make test`: functional 16 passed, qgis 428 passed, ui empty (pass).
- `agent-make lint` fails on pre-existing flake8 debt on master (~1400 findings in other files); none on
  the changed lines. Because make stops at flake8, bandit/detect-secrets did not run.

## Follow-ups (not in this PR)
- Port to dev: same bug in `DataCatalogService.save_downloaded` behind `guarded_connect`; the master change
  will not merge cleanly there (dev moved the save-as prompt to the controller and alerts to infra).
- No progress/cancel UI for long downloads.
