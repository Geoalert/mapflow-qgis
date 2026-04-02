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
[v]
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

### 4.1 sam-interactive-backend stabilization

#### Fix textPrompt display
- Currently sessions table in `text prompt` column dislpays empty text. Change Session return schema, add optional field `text_prompt`, display it in this column. 
- Prompts table lacks name: add `name` to the response model (optional, default to text prompt for backwards compatibility)
#### Incorporate SAM3 processings into existing processing table
- Processings listed under SAM3-interactive API now have "project_id" + can be filtered by project id. 
/processings/page?project_id=<UUID>&...
- For the open project in the main project/processings tab:
-- request this api, mark "sam3-interactive" processings with "SAM3-interactive" in "Model" column instead of model name
-- add a checkbox "show only sam3-interactive" to hide other 
- remove processings table from Sam3-interactive tab; replace it with a Label with processings' name 
-- take current processing from Processing tab/ProcessingsTable if it is from SAM3 list, select/fetch corresponding sessions and worklfows on selection immediately
-- No need for refresh/preview/delete buttons here as well, remove dangling code.


#### Incorporate runnning SAM3 inference with the standard "Start processing" button
- On startup, request `/rest/sam-interactive/wdid` API -> returns a single UUID, save it.
- If there is WorkflowDef with this ID available in the current project, on start of the processing with this workflow_id, use not Maplfow API /rest/processings/V2, but /rest/sam-interactive/processings instead
-- Use TextPrompt from corresponging field
-- Do not allow starat with empty text prompt

#### 

### Manual testing findings — prompt map tools

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