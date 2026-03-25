# Journal for logging and planning of features to implement

## 1. Add AI setup
[v]
- Modify agents.md to meet this repo's structure (no makefile, no docker, etc.)
- Modify planning, implementation and stabilization instructions to address stack and UI component of this app (QT, PyQGis)
Adapted from generic Docker/Makefile/alembic template to QGIS plugin structure; UI instructions derived from existing dialog patterns (uic.loadUiType, signal/slot, separation of concerns)

## 2. Generate spec
[v]
- Research existing codebase
- Populate spec with necessary documents; ask for API documentation if needed
All 5 specs populated from codebase analysis: goal (plugin purpose/constraints), API (all Mapflow/Maxar/Sentinel endpoints consumed), persistence (full QgsSettings key inventory from code), stack (PyQt5/QGIS/pytest + strict no-external-deps policy), interactions (all external systems; Maxar/Sentinel marked legacy)

## 3. Plan test
[v]
- Unit tests on functional
- Integration tests on API calls
- UI testing
All tests require QGIS runtime — no value in partial testing without it. Tools: pytest + pytest-qt + unittest.mock (stdlib). QgsApplication bootstrapped via qgis.testing.start_app() in pytest_configure hook (must run before collection because plugin modules create QIcon at import time). conftest.py provides iface mock and http_mock fixtures. pytest-qt chosen over raw PyQt5.QtTest for signal-heavy architecture (waitSignal, auto widget cleanup via qtbot).

## 4. Feature: debug interface for sam-interactive-backend
[ ]
We are stabilizing the new backend API, so we need a debug interface to interact with it.

- inspect sam-interactive-backend app spec and (if necessary) code
- Add a new tab "sam interactive" to plugin UI
- Implement all sam-interactive-backend API calls
- Add appropriate UI for api calls: basic, simplest UI solutions + full debug output 
-- Crucial APIs: create processing; page processings; get processing; create session/prompt; add text/point/bbox prompt to the session; run inference for the session; get session/inference status; load inference results
-- For "add point prompt" and "add bbox prompt" we should use map tools
-- Display of session prompts and geometries should create a new layer(s) and add them to the map
-- Display of processing results should be done via basic /result Mapflow API, not vector tiles if possible
-- All response fields should be available for view in the debug output

Use WAL_4.md for particular implementation steps, mark steps as finished after completion.
Use WAL_4_exploration.md for architecture and code insights.

### Manual testing findings — prompt map tools

**Bugs found:**
1. Point prompt: positive/negative determined by checkbox; should be left-click = positive, right-click = negative
2. Bbox prompt: tries to add polygon features to the same memory layer created with Point geometry type → fails silently; needs a separate Polygon layer
3. Bbox prompt: same checkbox issue as point — should use left/right click

**Fix plan:**
1. `map_tools.py`: change signal signatures from `pyqtSignal(dict)` to `pyqtSignal(dict, bool)` — emit `(geojson, positive)`. `SamPointMapTool.canvasReleaseEvent`: detect `Qt.LeftButton` → positive=True, `Qt.RightButton` → positive=False. `SamBboxMapTool`: track button from `canvasPressEvent`, pass to `_on_extent`.
2. `sam_view.py`: split single `_prompts_layer` into `_point_prompts_layer` (Point geometry) and `_bbox_prompts_layer` (Polygon geometry), each with green/red categorized renderer. Update `_add_spatial_prompt_feature` and `_clear_prompts_layer` accordingly.
3. `sam_controller.py`: update `_on_point_captured(geojson, positive)` and `_on_bbox_captured(geojson, positive)` to use `positive` from signal instead of `samPositivePrompt` checkbox. Remove checkbox reads.
4. Consider removing `samPositivePrompt` checkbox from UI if no longer needed.

## 5. Feature: download image from data-catalog
[ ]
- Add button "Donwload image" in My Imagery tab when mosaic is opened (images table active, image is selected)
- Refactor 002_api.md: divide into A)project/b)processing/c)myimagery/d)search API docs in separate files; keep endpoints index in spec/002,
- add more details to separate files. 
- Use the following description for new api:
#### `GET /rest/rasters/image/{image_id}/download`
    Returns a presigned S3 download URL for the requested image.
    
    Parameters:
    - `image_id`: UUID
    
    Access rules:
    - Requires `StandardHTTPSecurity` (authenticated user)
      - User must own the mosaic containing the image (returns `404` otherwise, to not reveal existence)
      - Image must have been ingested via the `load_data` workflow (returns `403` otherwise)
      - `data_available` must be `true` (returns `409` otherwise)
    
    Response shape:
    ```json
    {
        "download_url": "https://...",
        "filename": "image.tif",
        "expires_in": 3600
    }
    ```
    
    Errors:
    - `404`: image not found or user has no access
      - `403`: image is not downloadable (not ingested via `load_data`)
      - `409`: image data is not yet available
    
    Notes:
    - The presigned URL allows direct download from S3 without credentials; no data transfer through the service.
      - URL expiry is configurable via `DOWNLOAD_URL_EXPIRY` (default 3600 seconds).
      - The download restriction to `load_data` images prevents misuse of the service as a general file exchange.

#### Change to `GET /rest/rasters/mosaic/images` API response:
    Add "avaliable_for_download" field to ImageReturnSchema, default if not present in API `True`

- Implement image download API, add file save path dialog
- Disable button if the selected image has `avaliable_for_download=False`

## 6. Add new zoom-selector feature
[ ]
Use 002_E_zoom_selector_api.md
- Add small button near zoom selector comboBox to call for zoom selector api, active if selected source is Mapflow data provider
- On press of the button, call api and select zoom automatically depending on response
- on error, report to user with reasonable message