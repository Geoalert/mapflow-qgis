# 003 Local Storage

## Purpose
Describe the plugin's local persistence layer. No database — all persistence is via QgsSettings (key-value store in QGIS profile), QGIS Auth Manager, and temporary files.

## Content

All plugin settings are scoped under the `"mapflow"` group via `settings.beginGroup("mapflow")`.

### QgsSettings keys

#### Authentication & Session
| Key | Type | Purpose |
|-----|------|---------|
| `token` | string | Basic auth API token |
| `use_oauth` | string ("true"/"false") | OAuth2 vs basic auth flag |
| `project_id` | string | Currently selected project ID |

#### UI State & Preferences
| Key | Type | Purpose |
|-----|------|---------|
| `mainDialogState` | QByteArray | Main dialog geometry/size (persisted across sessions) |
| `outputDir` | string | Output directory path for saved results |
| `zoom` | string or None | Selected zoom level |
| `useAllVectorLayers` | string ("true"/"false") | Use all vector layers in AOI dropdown |
| `confirmProcessingStart` | string ("true"/"false") | Show confirmation dialog before processing |
| `viewResultsMode` | string ("tile"/"file") | Results display mode |
| `layerGroup` | string | Plugin layer group name in QGIS legend |
| `visibleProcessingColumns` | list of strings | Visible column indices in processings table |
| `visibleSearchColumns` | list of strings | Visible column indices in search results table |

#### Metadata Search & Filters
| Key | Type | Purpose |
|-----|------|---------|
| `metadataMinIntersection` | int | Minimum intersection threshold for imagery search |
| `metadataMaxCloudCover` | int (0-100) | Maximum cloud cover percentage |
| `metadataFrom` | QDate | Start date for metadata search |
| `metadataTo` | QDate | End date for metadata search |

#### Processing & History
| Key | Type | Purpose |
|-----|------|---------|
| `processings` | dict | Processing history by environment |
| `latest_reported_version` | string | Last reported server version (update notifications) |

#### Projects
| Key | Type | Purpose |
|-----|------|---------|
| `projectsPage` | dict | Projects table state (offset, sorting, filtering) |

#### Workflow Options
| Key pattern | Type | Purpose |
|-------------|------|---------|
| `wd/{workflow_id}/{block_name}` | bool | Optional block enabled status per workflow |

#### Providers
| Key | Type | Purpose |
|-----|------|---------|
| `mapflow_data_providers` | JSON string | User-configured data providers list |
| `providers` | dict | **(LEGACY)** Old provider format, migrated on load |
| `providerUsername` | string | **(LEGACY)** Old credentials, cleared on migration |
| `providerPassword` | string | **(LEGACY)** Old credentials, cleared on migration |

### QGIS Global Variables (read-only config)
| Variable | Type | Purpose |
|----------|------|---------|
| `variables/mapflow_env` | string | Environment: production/staging/internal/duty |
| `variables/mapflow_project_id` | string | Default project ID override |
| `variables/zoom_selector` | string ("true"/"false") | Enable zoom selector feature |
| `variables/mapflow_enable_sentinel` | string ("true"/"false") | Enable Sentinel-2 imagery |
| `variables/mapflow_raw_error` | string ("true"/"false") | Show raw error messages (debug) |
| `variables/mapflow_max_aois` | string | Max AOIs per processing |

### QGIS Auth Manager (OAuth2)
OAuth2 credentials stored securely per environment, not in QgsSettings:
| Config name | Keycloak realm |
|-------------|---------------|
| `mapflow_production` | mapflow |
| `mapflow_staging` | mapflow-staging |
| `mapflow_internal` | mapflow-internal |
| `mapflow_duty` | mapflow-duty |

Created via `QgsApplication.authManager()` + `QgsAuthMethodConfig()`. Tokens managed and refreshed automatically.

### Temporary Files
| Location | Purpose |
|----------|---------|
| `{outputDir}/Temp/` | Preview images, GeoJSON geometries, VRT files, AOI files. Cleared on plugin startup. |
| `{tempDir}/{provider}_imagery_search` | Cached search results per provider (JSON). Cleared on startup. |
