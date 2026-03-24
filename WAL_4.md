# WAL_4: Download image from data-catalog

## Scope
Add "Download image" capability to the My Imagery tab. When an image is selected in the images table, a download button appears. Clicking it fetches a presigned S3 URL from the API, then downloads the file to a user-chosen location.

## Spec changes
1. Refactor `spec/002_api.md` into index + 4 sub-files (A: projects, B: processings, C: my imagery, D: search)
2. Add `GET /rest/rasters/image/{image_id}/download` endpoint to `002_C_myimagery_api.md`
3. Add `available_for_download` boolean to image return schema
4. Update `spec/index.md`

## Implementation order

### 1. Spec refactoring
- Split 002_api.md keeping it as an index referencing sub-files
- Create 002_A_project_api.md, 002_B_processing_api.md, 002_C_myimagery_api.md, 002_D_search_api.md
- Add download endpoint and `available_for_download` field to 002_C

### 2. Tests (written first)
- `tests/test_data_catalog.py`:
  - `test_image_return_schema_with_download_field`: verify `available_for_download` parsed correctly
  - `test_image_return_schema_without_download_field`: verify defaults to `True`
  - `test_download_url_construction`: verify API client builds correct URL
  - `test_download_button_disabled_when_not_available`: verify view disables button

### 3. Schema changes
- `mapflow/schema/data_catalog.py`: add `available_for_download: bool = True` to `ImageReturnSchema`

### 4. API client
- `mapflow/functional/api/data_catalog_api.py`: add `download_image(image_id, callback, error_handler)` method
  - Calls `GET /rasters/image/{image_id}/download`
  - Returns `{download_url, filename, expires_in}`

### 5. Service
- `mapflow/functional/service/data_catalog.py`: add `download_image()` method
  - Gets selected image, calls API, on callback opens QFileDialog.getSaveFileName
  - Downloads from presigned URL (no auth needed), saves to disk
  - Error handling for 404/403/409

### 6. View + Dialog
- `mapflow/dialogs/main_dialog.py`: add `downloadImageButton = QPushButton()`
- `mapflow/functional/view/data_catalog_view.py`:
  - Add download button to image cell layout
  - Enable/disable based on `available_for_download`
  - Add download icon

### 7. Controller
- `mapflow/functional/controller/data_catalog_controller.py`: connect `downloadImageButton.clicked` to service

## Error handling
- 404: "Image not found or no access"
- 403: "Image is not available for download"
- 409: "Image data is not yet available, try again later"
- Network/file errors: standard error widget

## Acceptance criteria
- Download button visible in image cell when image is selected
- Button disabled when `available_for_download` is False
- Clicking download shows save dialog, then downloads file
- All tests pass
