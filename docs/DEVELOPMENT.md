# Developing Mapflow Next

How the plugin is built, tested and released. For what the plugin does, see the [README](../README.md).

## Set up

`make link` symlinks `mapflow_next/` into your QGIS profile, then reload the
  plugin with Plugin Reloader. The default path is the macOS one for QGIS 3; use `make link QGIS_MAJOR=4`
  for QGIS 4, or set `PLUGINS_DIR` on Linux or Windows.

A plugin built with `make zip` installs as **Mapflow Next** (folder `mapflow_next`), next to the 3.x Mapflow plugin. The update check (Plugins › Mapflow Next › Check for updates…) asks the plugin repositories through QGIS's own installer; a plugin installed from a ZIP isn't in any repository, so it points to the releases page instead.

## QGIS 3 and QGIS 4

One zip runs in QGIS 3.28 and later (Qt 5) and in QGIS 4 (Qt 6): `metadata.txt` sets
`qgisMinimumVersion=3.28` and `qgisMaximumVersion=4.99`. Every feature works in both. 3.28 is the oldest
version the tests run on, so it is the oldest one declared.

To keep it that way, write code both Qt versions accept. `tests/test_core.py` and `tools/qt6_check.py`
check these rules:
- Import Qt only through `qgis.PyQt`, never from `PyQt5` or `PyQt6` directly.
- Use scoped enum names: `Qt.AlignmentFlag.AlignLeft`, `QSizePolicy.Policy.Expanding`,
  `Qgis.MessageLevel.Info`. Qt 6 rejects `Qt.AlignLeft`, and enum values read from an object
  (`action.NoRole`).
- Use `exec()`, not `exec_()`.
- Build menu items as `QAction`s, with `widgets.menu_action`.
- Read mouse positions through `widgets.event_pos`.
- Take geometry types from `qgis_bridge/compat.py`.
- `QSvgWidget` moved to `QtSvgWidgets` in Qt 6. `ui/icons.py` imports it from either place.

Run `tools/qt6_check.py --fix` to rewrite unscoped enum names automatically.

The tests run on both versions (see [Tests and CI](#tests-and-ci)). `tests/qt6_ui.py` also drives the
pages, the browser sign-in listener and the HTTP client on plain PyQt6, through a stand-in for QGIS 4's
`qgis.PyQt` (`tests/qt6_shim/`), for when QGIS 4 isn't at hand. From the Python console of any
installed QGIS, `tools/run_in_qgis.py` runs the end-to-end tests with that QGIS's own Python.

## How it works

```
mapflow_next/
  plugin.py          QGIS entry: the Mapflow toolbar, the plugin menu, the dock, wiring of the parts below
  controller.py      the flow: connects services (state) to pages (views) and to QGIS
  config.py          environments, URLs, timings, the result modes
  settings.py        QgsSettings under mapflow_next/ (never credentials), the default output folder
  core/              pure Python, no Qt: testable without QGIS
    models.py          API responses → Project, Model (workflow def), DataProvider, Processing, …
    draft.py           the run form as data: issues(), estimate(), payload()
    scenarios.py       scenario catalogue and scenario → model matching
    messages.py        readable texts for Mapflow error codes
    failures.py        what a failed request means by what triggered it: transient or permanent, the poll's count
    guard.py           the guard: no exception escapes from an entry point Qt calls (no Qt; every layer imports it)
    oauth.py           browser sign-in without Qt: PKCE, the redirect, tokens
    origin.py          which requests may carry credentials: the API's own scheme, host and port
    filenames.py       file names made from server ids: a hash, never the id
  api/
    http.py            async HTTP over QgsNetworkAccessManager, error classification
    auth.py            credentials in the QGIS authentication database
    oauth.py           browser sign-in: the loopback listener and token requests
    client.py          the Mapflow endpoints the plugin uses
  services/          Qt objects with signals: session, processings, imagery, results
  qgis_bridge/       map-side code: area from layers, layers and styles, draw tool, QGIS 3/4 compat
  ui/                dock, pages, gallery, dialogs, theme (design tokens) and icons, built in code
  resources/         scenario data and pictures, result styles (QML), Nunito, brand icons
```

Services hold state, pages render it and emit what the user wants, and `controller.py` connects the two.
That is the rule; today the controller also holds the run form's state itself. `spec/007_architecture.md`
§ Mapflow Next (4.x) has the layer rules and where the code is not there yet.

## What it keeps from the 3.x plugin

- **API:** the same endpoints and v2 processing payload (`processings/v2`, `processing/cost/v2`,
  `projects/{id}/processings/v2/page`, `catalog/meta`, `rasters/mosaic…`, `processings/{id}/result`).
- **Sign-in:** the same Mapflow sign-in client (`qgis`) and redirect address
  (`http://127.0.0.1:7070/qgis`). The `mapflow_env` QGIS variable picks the environment, as before. The
  `mapflow_ru` QGIS variable, set to `true`, switches the plugin to the domain `mapflow.ru` in place of `mapflow.ai`
  (support gives it to a user who needs it); the saved sign-in stays valid.
- **Area rules** (spec 002_B):
  - The area is measured on the union of its parts, and each part is repaired first.
  - The plan limit is checked both on the total and on each polygon's bounding box.
  - A selection on the area's layer narrows the area to the selected polygons.
  - An area under the smallest order the imagery's provider sells (inside the image, for a catalog image)
    blocks Run, with "Enlarge": a rectangle over the area that meets the minimum, and a way back.
- **Results:**
  - Downloaded as GeoJSON, written to a GeoPackage, styled with the same QML styles, and added to the
    "Mapflow" group.
  - Vector tiles are an option. Their extent comes from the tilejson `bounds`, or else from the
    processing's area.
- **Error texts:** all 64 error-code descriptions.
- **3.6.x fixes:**
  - In-flight replies are held until they finish, and large downloads are streamed to disk.
  - Overlapping polygons are counted once.
  - Your rights in shared projects follow your account.

## What it does differently

- **Browser sign-in:** the plugin runs it itself instead of using QGIS's OAuth2 method, then sends the
  browser on to app.mapflow.ai.
  - It listens on 127.0.0.1 only and checks the answer with PKCE and a state value.
  - You stay signed in across QGIS restarts. The plugin never opens the browser on its own, and QGIS
    doesn't need a restart after the first sign-in.
- **Credentials:** the API token (a fallback) and the browser sign-in are kept in the QGIS
  authentication database, never in plain settings.
- **One flow instead of five tabs:** the tabs are Start, Processings and Imagery sources. Settings and
  the account move to the header.
- **Scenario gallery:** 16 ready-made setups built on Mapflow models. The processing name is generated
  from the model and the area, and the pencil next to it opens a dialog for a name and a description.
- **Projects window:** project tiles with their description, done and failed counts, the last update
  and whether they're shared.
  - Search by name on the server, and load more with "Show more".
  - Pin projects to the top. Pins are Mapflow Web's starred projects, so they follow the account.
  - Rename a project you own, from the ⋯ menu of its tile: its name and description. The default project can't be renamed.
  - Delete a project you own, from the same menu, after a confirmation. The processings of the project are deleted with it; results already on the map stay. If it is the open project, the default project opens. The default project can't be deleted.
  - Share a project, or open the team page, in Mapflow Web.
- **Zoom:** basemaps offer z17–z21, with the scenario's zoom preselected and marked ★.
- **My imagery:**
  - Collections show their image count, and a picker lets you use the whole collection or one image.
  - Collections are listed 50 at a time, newest first, with "Show more". The collection search runs on
    the server: it finds collections that aren't loaded yet, by their name or by the file name of an
    image in them.
  - The imagery's extent becomes the area, and any other area is clipped to the imagery.
  - An area outside the imagery blocks Run, with a way back to the extent.
- **Imagery search:** the same Area drop-down as on Start, dates with presets (last 3 months, 6 months, year),
  slider filters (cloud cover, off-nadir range, minimum area coverage), the "Available for me" switch, and
  "Clear". Filters apply when you press "Search imagery", except Mosaics and Scenes: a click on one sends the
  last search again with that type, and a second click shows both. The list always shows what the last search
  returned.
- **Processings:** pages of 30 with "Show more". Polling refreshes the shown window and leaves older
  pages in place. The planned processings load and refresh with the list; if they fail to load, the rows are hidden with no message.
- **Live cost:** a local estimate at once, then the figure from `/cost`.
- **Results:** they go to `Documents/Mapflow` unless you choose another folder. Finished results load
  automatically, which you can turn off. "Run again" restores a processing's settings and its area.
- **Theming:** follows the QGIS light or dark theme, with the Mapflow design tokens.

## 3.x features in 4.0, feature by feature

The plugin keeps what is done while looking at the map; managing things moves to Mapflow Web, and the plugin links to the right page wherever it leaves something out.

| 3.x plugin | 4.0 | Why, and where to do it |
|---|---|---|
| Run processings: models, options, area, providers, catalog, My imagery | **Kept**, redesigned as one form | The core of the plugin |
| Processings list, results on the map, rename, delete, run again | **Kept** | Results belong in QGIS |
| Imagery search in the catalog | **Kept** | Footprints are judged on the map |
| Upload a GeoTIFF to My imagery | **Kept**: into a new or an existing collection, from one or several files or layers | Your imagery is made in QGIS and processed from there |
| My imagery collections: create, rename, delete, add, download or delete images | **Kept**: the My imagery window and its ⋯ menus | Adding imagery and clearing out what was added by mistake belong where the imagery is chosen |
| My imagery: rename an image, storage usage | **Mapflow Web** › [My data](https://app.mapflow.ai/my-data) ("Manage collections in Mapflow Web") | File management, not mapping |
| Create a project | **Kept**: New project in the Projects window | Starting new work shouldn't need a trip to the browser |
| Rename a project | **Kept**: the ⋯ menu of a project tile in the Projects window (the owner; not the default project) | A name is fixed where the project is picked |
| Delete a project | **Kept**: the ⋯ menu of a project tile in the Projects window, after a confirmation (the owner; not the default project) | The processings of the project go with it; results already on the map stay |
| Forced upgrade | **Kept**, as one page: when Mapflow expects a higher major version of the plugin, the dock asks to upgrade and opens the QGIS plugin manager | An old plugin would send requests the backend no longer understands. A higher minor or patch version is not announced |
| Projects: share | **Mapflow Web** › the project ("Share project in Mapflow Web" and the share icon in the Projects window) | Sharing needs the team's members and roles. The plugin creates, renames, deletes, switches, searches and pins projects |
| Review: accept or send back results | **Mapflow Web** (the processing links there) | Review is a step of its own, with its own page, after the processing; the plugin shows that a processing needs it |
| Balance and top-up, API tokens | **Mapflow Web** › [Account](https://app.mapflow.ai/account/balance) ("Top up" in the run form) | Payments and keys stay with the account |
| Planned processings (search templates): the list | **Kept**: the Processings tab lists them with a "Planned search" mark. Clicking a row opens that search in Mapflow Web | The plugin lists them and does nothing else |
| Planned processings: create one, its areas and results, pause and resume, run from it, delete it | **Mapflow Web** | Managing a search template is a task of its own; the plugin only shows that one exists |
| XYZ/TMS tile layers of the QGIS project as imagery | **Kept**, as a fourth kind of imagery: the run form lists them under "QGIS tile layers"; the plugin reads the layer and has no editor for tile sources. A login goes to Mapflow after an alert; a layer on this computer or a private network, with a referer or other headers, or with a non-Basic authentication configuration is listed disabled, with the reason | The tile sources a team already has in QGIS can be mapped without being entered again; Mapflow's servers can read only public addresses and send no custom headers |
| Translations (es, pt, ru, zh) | **Not yet**: planned for 4.1 | Every text is new, so the 3.x translations don't apply |
| Settings of the 3.x plugin | **Not migrated** | The two plugins install side by side; sign in and set the output folder again |
| Georeferenced catalog previews, Segment Anything zooms | **Not yet** | Smaller features, after the first release |

## To verify against the real API

- **Live API:** the tests use a mock API shaped like the spec. Nothing has been run against the live
  Mapflow API yet.
- **Mapflow Web links:** "Open in Mapflow Web" opens `/projects/{project}?processing={id}`, the address
  the API itself reports for a processing. The team page address (`TEAM_URL` in `config.py`) is a guess.
- **AOI names:** a processing is created with its area as one geometry (`geometry` in `processings/v2`).
  The API documents no field for the names of its AOIs, so Mapflow Web lists them without the names the
  layer has.
- **Plugin version header:** requests send `x-plugin-version: 4.0.0`. Check the backend doesn't treat
  it specially.
- **Scenario → model matching:** scenarios find their model by keywords in the project's model names. A
  stable scenario id on the backend would make this exact.
- **Pinned projects:** pinning stars the project (`POST`/`DELETE /projects/{id}/starred`), and projects
  starred in Mapflow Web are pinned here. The list of starred projects is read from `POST /projects/starred`.
- **Browser sign-in:**
  - The `qgis` client has to accept PKCE.
  - The `offline_access` scope would keep a sign-in for weeks.
  - A "You're signed in to QGIS" page in Mapflow Web would be a better landing than the home page.

## Tests and CI

Tests and lint run in the official `qgis/qgis` Docker images, so only Docker is needed:

```
make test          # both of the two runs below (the gate before review)
make test-qgis3    # unit + end-to-end tests on QGIS 3 (qgis/qgis:release-3_28)
make test-qgis4    # the same on QGIS 4 (qgis/qgis:4.2), plus the Qt 6 code check
make test-core     # pure-Python tests only (61)
make lint          # the plugins.qgis.org checks: flake8, bandit, detect-secrets
make screens       # run the end-to-end flow and rewrite docs/screens/*.png
```

With QGIS or PyQt6 installed, there are local variants:

```
make test-local QGIS_PYTHON=/Applications/QGIS-LTR.app/Contents/MacOS/bin/python3
make test-qt6 QT6_PYTHON=…    # the pages, sign-in and HTTP client on PyQt6 (42 checks)
make check-qt6 QT6_PYTHON=…   # Qt enum names and calls that only Qt 5 accepts
```

**The end-to-end test** (`tests/e2e_flow.py`, 540 checks) runs a real offscreen QGIS against a mock
Mapflow API and sign-in server (`tests/mock_server.py`).
- **Request checks:** the mock rejects request bodies the real API rejects, such as `myImagery` with both
  `mosaicId` and `imageIds`.
- **Sign-in:** a simulated browser signs in. The test then checks that the session renews, survives a
  restart, can be cancelled and is forgotten on sign-out.
- **The flow:** from there it covers scenarios and the run form, cost and the run itself, and results on
  the map. It also covers imagery search, My imagery, the projects window, processings paging and
  renaming, "Run again", the account menu, unload and dark mode.
- **Critical messages:** the plugin's guard turns an exception into a Critical line in the message bar and
  the log. An unexpected Critical message in the bar or the log fails the flow; a check that expects one
  declares it. A source check in `tests/test_core.py` fails on any `connect` or `QTimer.singleShot` whose
  callable is not guarded (`@guarded`, or `guarded(...)` at the connection site).
- **Isolation:** each run gets its own QGIS settings and authentication database in a temporary folder.
- **Real clicks:** the test clicks the real buttons wherever a bug hid behind a click. For example,
  toggling an option must leave the form's scroll position alone.

CI (`.github/workflows/tests.yml`) runs `test-qgis3`, `test-qgis4`, `test-qt6` and `lint` on every push to `dev` and
`master` and on pull requests. **Releases are made by hand**: `make zip` builds the archive, and a
maintainer uploads it to the QGIS Plugin Repository. No workflow publishes a release (`.qgis-plugin-ci`
is kept for the `qgis-plugin-ci` tool, which nothing runs today; `release.yml` in the repository root is
not under `.github/workflows/` and never runs).

**Release review.** Every release PR into `master` is reviewed by Claude, following
[`.claude/agents/release-reviewer.md`](../.claude/agents/release-reviewer.md)
(`.github/workflows/release-review.yml`). It reads the whole plugin and starts from what changed since the
last `v*` tag. It looks for wrong paid runs, stuck states, stale async answers, deleted QGIS objects, API
contracts (checked against Mapflow's published OpenAPI) and QGIS 3/4 support. The report is posted on the PR
and in the job summary. CRITICAL findings fail the check: make "release review" a required check on `master`.
It needs an `ANTHROPIC_API_KEY` repository secret. To run it on any commit, use the workflow's "Run
workflow" button; locally, ask Claude Code to "run the release-reviewer agent".

## Screenshots

`make screens` runs the end-to-end flow and rewrites the numbered `docs/screens/*.png`. `results-on-map.jpg` and `scenarios.jpg`, used by the README, are real screenshots and are not rewritten.
