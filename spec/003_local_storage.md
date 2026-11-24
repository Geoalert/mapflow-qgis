# 003 Local Storage

## Purpose
Describe the plugin's local persistence layer. No database — all persistence is via QgsSettings (key-value store in QGIS profile), the QGIS authentication database, custom properties on the layers the plugin adds, and temporary files.

## Content

All plugin settings are scoped under the `mapflow_next` group (`config.SETTINGS_GROUP`), read and written
through `mapflow_next/settings.py` (the three developer overrides below are read by `config.load_config`
directly, before anything else exists).

### No migration from the 3.x plugin

Mapflow Next reads nothing from the 3.x plugin's `mapflow` group, and writes nothing there. The two
plugins install side by side, and too much changed between them for the old values to mean the same
thing (the token moved out of settings, the output folder holds files in another layout, the providers
list is gone). A user who moves over signs in again and sets the output folder again. This is stated in
`README.md`, `CHANGELOG.md` and `metadata.txt`, so nobody expects otherwise.

### QgsSettings keys

#### Sign-in and session
| Key | Type | Purpose |
|-----|------|---------|
| `auth_method` | string | How the user signed in: browser (OAuth2) or token |
| `auth_config_id` | string | Id of the Basic configuration in the QGIS authentication database that holds the API token. Never the token itself |
| `project_id` | string | The project that was open last |

#### Preferences
| Key | Type | Purpose |
|-----|------|---------|
| `results_mode` | string (`"file"` / `"tiles"`) | How results are added to the map |
| `output_dir` | string | Folder for saved results. Empty: `<Documents>/Mapflow` |
| `auto_load` | bool | Add the result of a processing started here to the map when it finishes |
| `skip_tile_login_alert` | bool | The user ticked "Don't show this again" in the alert that comes before the plugin sends the login and password of a QGIS tile layer (`002_B_processing_api.md` § Imagery from a QGIS tile layer) |

#### Projects and ratings
| Key | Type | Purpose |
|-----|------|---------|
| `pinned_projects/{env}/{email}` | JSON list of ids | Projects pinned in the Projects window, per environment and account, synced with the stars in Mapflow Web |
| `ratings` | JSON object | The rating the user gave each processing (the last 500). One key for all accounts: processing ids don't collide |

#### Developer overrides (read only, no UI)
| Key | Type | Purpose |
|-----|------|---------|
| `server` | string | API base URL in place of the environment's |
| `auth_url` | string | The sign-in server's OpenID Connect base URL (`…/protocol/openid-connect`) in place of the environment's |
| `web_url` | string | Mapflow Web URL in place of the environment's |

Nothing else is stored. In particular the plugin keeps **no** search filter values, zoom choices, model
options, processing history, column choices or window geometry between sessions: each of these starts
from its default.

### QGIS Global Variables (read-only config)
| Variable | Type | Purpose |
|----------|------|---------|
| `variables/mapflow_env` | string | Environment: production/staging/internal/duty. Empty: production |
| `variables/mapflow_ru` | string | `true`: the plugin uses the domain `mapflow.ru` in place of `mapflow.ai` (`002_api.md` § The `mapflow.ru` domain). Empty: `mapflow.ai` |

The 3.x variables `mapflow_project_id`, `zoom_selector`, `mapflow_raw_error` and `mapflow_max_aois` are
not read.

**No admin mode.** The 3.x plugin opened the project named by `mapflow_project_id` for a user with the
ADMIN role and skipped the project list. Mapflow Next has no special path for the ADMIN role. This was an
internal tool; it is deliberately absent and is not part of the user documentation.

### QGIS authentication database
Secrets are stored encrypted in the QGIS authentication database, per environment, never in QgsSettings:

| Entry | Kind | Holds |
|-------|------|-------|
| `mapflow_next_token_{env}` | Basic authentication configuration | The API token (token sign-in) |
| `mapflow_next/{env}/refresh_token` | authentication setting | The OAuth2 refresh token (browser sign-in) |

The access token lives in memory only. The plugin renews it itself (see `005_interactions.md`); QGIS's
OAuth2 method is not used. Signing out removes the entry of the method in use.

### Layer group
Every layer the plugin adds goes into one group named **Mapflow** at the top of the Layers panel. The
name is fixed (`config.py`), not stored and not configurable; if the user renames or deletes the group,
the plugin makes a new one the next time it adds a layer. The 3.x plugin remembered a renamed group
(`layerGroup`); that was dropped with the rest of its settings.

### Layer custom properties (saved with the user's QGIS project)
| Property | On | Purpose |
|----------|----|---------|
| `mapflow_next/processing_id` | a result layer | Which processing the layer shows, so it is found again and not added twice |
| `mapflow_next/preview` | a preview layer | Which imagery source the preview shows |
| `mapflow_next/extent_of` | an area layer made from My imagery | The name of the imagery whose extent it is |

### Temporary Files
| Location | Purpose |
|----------|---------|
| `{output_dir}/.downloads/` | A result being downloaded, before it is converted and moved into place |
| a folder made with `tempfile.mkdtemp()` once per session | Catalog preview pictures and the files GDAL derives from them. Private to the user, removed at unload. File names never carry an id as the server sent it: ids are made safe first |
| `{tempDir}/mapflow_next_icons/` | Icons drawn for the current theme and scale |

After a result is converted to GeoPackage, the finished file is moved into the output directory
and the temporary GeoJSON is removed. Cancelling the conversion removes the temporary GeoJSON and
any partial GeoPackage. If the writer falls back to GeoJSON, it moves that file into the output
directory as the result.
