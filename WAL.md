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

## 4. Feature: download image from data-catalog
[v]
- Refactored 002_api.md into index + 4 sub-files (A: project, B: processing, C: my imagery, D: search) for maintainability
- Added `GET /rest/rasters/image/{image_id}/download` spec with presigned URL response model and error codes (404/403/409)
- Added `available_for_download` boolean to ImageReturnSchema (defaults True for backward compat via SkipDataClass.from_dict)
- Download uses two-step flow: authenticated GET for presigned URL, then unauthenticated direct S3 download — avoids routing large files through the backend
- Download button placed first in image cell layout for discoverability; disabled with tooltip change when `available_for_download=False`
- 6 tests added (schema parsing, default values, API URL construction); all pass on QGIS 3.28 Python 3.9

## 5. Feature: processings pagination
[v]
- Add arrow buttons (like projectsPreviousPageButton and projectsNextPageButton) to be able to show in processings table only 30 processings per page;
- Add 'sort by' combo box, filtering line edit already exists;
- Change get_processings function, use the following description for new api:
#### `POST /projects/{projectId}/processings/v2/page`
    Returns paginated processings of project with filtering and sorting.
    
    Parameters:
    - 'terms' (string) - Search term to filter by name, project name, workflow name, or email;
    - 'limit' (integer) - Maximum number of results to return
    - 'offset' (integer) - Number of results to skip
    - sortBy	(string) - Field to sort by: [ scenario, name, project, email, created, status, progress, completed, cost, area, provider ]
    - sortOrder	(string) - Sort direction [ ASC, DESC ]
    
    Response shape:
    ```json
    {
        "results": List[Processing],
        "total": integer,
        "count": integer
    }
    ```;
- Implement pagination, sorting and new filtering (troug the request on text change, not though the table filtering).

## 6. Add support of planned processing feature (processing templates)
[ ]
- Implement planned processings, using the templates_service, templates_api, templwtes_view logic

- User should be able to:
    - see created templates (as "planned processings")
    - see all AOIs and connected processings in one layer with different colors for unprocessed/in-progress/processed aois
    - navigate from template to a processing launched from this template
    - create a new template (as "planned processing") from search results
    - launch a processing when something is found, using one or several AOIs from the template
    - delete template
    - update template parameters (search params, aoi, name, etc)

- UI:
    - Show all processings from template in the same layer as template geometries (When we open template, we should immediately call [API] Get all processing ran from the template and add their AOIs as a separate layer with different style)
    - Mark image/all as seen (button or context menu "already seen" for every line that is marked as "new" and button "seen all" for the table)
    - Display template current results in the search table (After the template is selected in "processings" table and retrieved (see [API] Get template) we need to display it in search result table. Also, display at the map as "Planned processing" layer. Add UI elements for template editing. Button or menu entry to upload edited layer as new geometry. Same button acts for search parameters, model etc. Also, template activation/deactivation button + label)
    - When provider is "Imagery search" and the search result table does not have selection, rename button "Start processing" → "Plan processing". When template is loaded AND image(s) are selected, we need option "Start planned processing" in the same button
    - Display templates along with processings table (To the same table add labels (color? Or additional column with labels?) or sorting/filtering "show planned/ hide planned/show planned only")

- Create 002_F_plan_processing_api with the help of this:

    1) POST /processings/template - Creates a new processing template
    Request body example:
    {
    "name": "string",
    "searchParams": {
        "aoi": {}
    },
    "processingParams": {},
    "projectId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "activeUntil": "2026-04-06T11:03:37.721Z"
    }
    Response example:
    {
    "template": {
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "name": "string",
        "status": "ACTIVE",
        "createdAt": "2026-04-06T11:03:37.743Z",
        "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "searchParams": {},
        "processingParams": {},
        "lastCheckedAt": "2026-04-06T11:03:37.743Z",
        "activeUntil": "2026-04-06T11:03:37.743Z",
        "searchResults": [
        {
            "id": "string",
            "metadata": {}
        }
        ],
        "projectId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "area": 0,
        "newImagesCount": 0
    },
    "searchResults": [
        {
        "id": "string",
        "metadata": {}
        }
    ]
    }

    2) GET /processings/template - Retrieves all templates for the authenticated user
    Response example:
    [
    {
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "name": "string",
        "status": "ACTIVE",
        "createdAt": "2026-04-06T11:05:13.838Z",
        "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "searchParams": {},
        "processingParams": {},
        "lastCheckedAt": "2026-04-06T11:05:13.838Z",
        "activeUntil": "2026-04-06T11:05:13.838Z",
        "searchResults": [
        {
            "id": "string",
            "metadata": {}
        }
        ],
        "projectId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "area": 0,
        "newImagesCount": 0
    }
    ]

    3) GET /processings/template/{templateId} - Retrieves a specific template by ID
    Parameter templateId (string(uuid)) - The id of the template
    Response example:
    {
    "template": {
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "name": "string",
        "status": "ACTIVE",
        "createdAt": "2026-04-06T11:06:19.534Z",
        "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "searchParams": {},
        "processingParams": {},
        "lastCheckedAt": "2026-04-06T11:06:19.534Z",
        "activeUntil": "2026-04-06T11:06:19.534Z",
        "searchResults": [
        {
            "id": "string",
            "metadata": {}
        }
        ],
        "projectId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "area": 0,
        "newImagesCount": 0
    },
    "searchResults": [
        {
        "id": "string",
        "metadata": {}
        }
    ]
    }

    4) POST /processings/template/{templateId} - Runs processing using a template
    Request body example:
    {
    "name": "string",
    "description": "string",
    "wdName": "string",
    "wdId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "geometry": {},
    "params": {},
    "meta": {},
    "blocks": [
        {
        "name": "string",
        "enabled": true,
        "displayName": "string"
        }
    ],
    "updateTemplateGeometry": true
    }

    5) PUT /processings/template/{templateId} - Updates an existing template
    Request body example:
    {
    "name": "string",
    "searchParams": {
        "aoi": {}
    },
    "processingParams": {},
    "activeUntil": "2026-04-06T11:44:33.912Z"
    }
    Response example:
    {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "name": "string",
    "status": "ACTIVE",
    "createdAt": "2026-04-06T11:44:33.916Z",
    "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "searchParams": {},
    "processingParams": {},
    "lastCheckedAt": "2026-04-06T11:44:33.916Z",
    "activeUntil": "2026-04-06T11:44:33.916Z",
    "searchResults": [
        {
        "id": "string",
        "metadata": {}
        }
    ],
    "projectId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "area": 0,
    "newImagesCount": 0
    }

    6) DELETE /processings/template/{templateId} - Marks template as deleted
    Parameter templateId (string(uuid)) - The id of the template

    7) POST /processings/template/{templateId}/v2 - Runs processing using a template with V2 params format
    Request body example:
    {
    "name": "string",
    "description": "string",
    "wdName": "string",
    "wdId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "geometry": {},
    "params": {
        "sourceParams": {
        "myImagery": {
            "imageIds": [
            "string"
            ],
            "mosaicId": "string"
        },
        "imagerySearch": {
            "dataProvider": "orbview",
            "imageIds": [
            "string"
            ],
            "zoom": 0
        },
        "dataProvider": {
            "providerName": "string",
            "zoom": 0
        },
        "userDefined": {
            "sourceType": "XYZ",
            "url": "string",
            "zoom": 0,
            "crs": "string",
            "rasterLogin": "string",
            "rasterPassword": "string"
        }
        },
        "inferenceParams": {
        "key1": "value1",
        "key2": "value2",
        "keyN": "valueN"
        }
    },
    "meta": {},
    "blocks": [
        {
        "name": "string",
        "enabled": true,
        "displayName": "string"
        }
    ],
    "updateTemplateGeometry": true
    }

    8) POST /processings/template/{templateId}/pause - Changes template status to Inactive
    Response example:
    {
    "template": {
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "name": "string",
        "status": "ACTIVE",
        "createdAt": "2026-04-06T11:52:29.861Z",
        "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "searchParams": {},
        "processingParams": {},
        "lastCheckedAt": "2026-04-06T11:52:29.861Z",
        "activeUntil": "2026-04-06T11:52:29.861Z",
        "searchResults": [
        {
            "id": "string",
            "metadata": {}
        }
        ],
        "projectId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "area": 0,
        "newImagesCount": 0
    },
    "searchResults": [
        {
        "id": "string",
        "metadata": {}
        }
    ]
    }

    9) POST /processings/template/{templateId}/resume - Changes template status to Active. Note: Expired templates cannot be reactivated without first updating the activeUntil date.
    Response example:
    {
    "template": {
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "name": "string",
        "status": "ACTIVE",
        "createdAt": "2026-04-06T11:54:46.588Z",
        "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "searchParams": {},
        "processingParams": {},
        "lastCheckedAt": "2026-04-06T11:54:46.588Z",
        "activeUntil": "2026-04-06T11:54:46.588Z",
        "searchResults": [
        {
            "id": "string",
            "metadata": {}
        }
        ],
        "projectId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "area": 0,
        "newImagesCount": 0
    },
    "searchResults": [
        {
        "id": "string",
        "metadata": {}
        }
    ]
    }

    10) GET /processings/template/{templateId}/processings - Retrieves all processings associated with a template
    Response example:
    [
    {
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "name": "string",
        "description": "string",
        "projectId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "vectorLayer": {
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "name": "string",
        "tileJsonUrl": "string",
        "tileUrl": "string"
        },
        "rasterLayer": {
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "tileJsonUrl": "string",
        "tileUrl": "string"
        },
        "workflowDef": {
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "name": "string",
        "description": "string",
        "created": "2026-04-06T11:55:47.335Z",
        "updated": "2026-04-06T11:55:47.335Z",
        "pricePerSqKm": 0,
        "blocks": [
            {
            "name": "string",
            "description": "string",
            "optional": 0,
            "price": 0
            }
        ]
        },
        "aoiCount": 0,
        "aoiArea": 0,
        "area": 0,
        "cost": 0,
        "status": "UNPROCESSED",
        "reviewStatus": {
        "reviewStatus": "ACCEPTED",
        "feedback": "2026-04-06T11:55:47.335Z"
        },
        "rating": {
        "rating": "string",
        "feedback": "string"
        },
        "percentCompleted": 0,
        "params": {
        "key": "string",
        "value": "string"
        },
        "blocks": [
        {
            "name": "string",
            "enabled": true,
            "displayName": "string"
        }
        ],
        "meta": {
        "key": "string",
        "value": "string"
        },
        "messages": [
        {
            "code": "string",
            "parameters": {
            "key": "string",
            "value": "string"
            }
        }
        ],
        "created": "2026-04-06T11:55:47.335Z",
        "updated": "2026-04-06T11:55:47.335Z"
    }
    ]

    11) POST /processings/template/{templateId}/image/{imageId}/seen - Marks an image as seen in a template
    Parameters:
    templateId (string($uuid)) - The id of the template
    imageId (string) - The id of the image

    12) GET /processings/template/user/{userId} - Retrieves all templates for a specific user ID
    Response example:
    [
    {
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "name": "string",
        "status": "ACTIVE",
        "createdAt": "2026-04-06T11:58:06.918Z",
        "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "searchParams": {},
        "processingParams": {},
        "lastCheckedAt": "2026-04-06T11:58:06.918Z",
        "activeUntil": "2026-04-06T11:58:06.918Z",
        "searchResults": [
        {
            "id": "string",
            "metadata": {}
        }
        ],
        "projectId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "area": 0,
        "newImagesCount": 0
    }
    ]

    13) GET /processings/template/project/{projectId} - Retrieves all templates for a specific project ID
    Response example:
    [
    {
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "name": "string",
        "status": "ACTIVE",
        "createdAt": "2026-04-06T11:59:25.085Z",
        "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "searchParams": {},
        "processingParams": {},
        "lastCheckedAt": "2026-04-06T11:59:25.085Z",
        "activeUntil": "2026-04-06T11:59:25.085Z",
        "searchResults": [
        {
            "id": "string",
            "metadata": {}
        }
        ],
        "projectId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "area": 0,
        "newImagesCount": 0
    }
    ]


## 7. Add new zoom-selector feature
[ ]
Use 002_E_zoom_selector_api.md
- Add small button near zoom selector comboBox to call for zoom selector api, active if selected source is Mapflow data provider
- On press of the button, call api and select zoom automatically depending on response
- on error, report to user with reasonable message

## 8. Set up host-independent test runtime
[ready-for-review]
- All three tiers (functional/qgis/ui) run inside qgis/qgis:release-3_28 Docker; directory split is taxonomy, not runtime separation. Mocking PyQGIS portably broke at the first `class Foo(QObject):` because Python's metaclass machinery rejects MagicMock-as-base — real PyQGIS in a container is simpler than emulating Qt's class semantics.
- Makefile drives `docker-build / test-functional / test-qgis / test-ui / test`; GitHub Actions tests.yml runs the same three Make targets as separate jobs.
- Pinned to Linux + QGIS 3.28 LTR; cross-OS / non-LTR coverage is manual-smoke (documented in README + tests/README + spec/004_stack).
- Discovered (NOT fixed — out of scope): test_xyz_no_creds passes args in wrong positional order vs. signature; test_processings_pagination expects lowercase enum values but code emits uppercase. Both are real test/code drift exposed because the suite had never actually run.