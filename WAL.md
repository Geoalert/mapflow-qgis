# Journal for active implementation planning

## 1. Add support of planned processing feature (processing templates)
[ ]
- Implement planned processings using templates_service, templates_api, templates_view logic.
- User should be able to:
  - see created templates as planned processings
  - see AOIs and connected processings in one layer with clear statuses
  - navigate from template to processings launched from it
  - create, launch, delete, and update template parameters

### 1a. See & edit template AOIs (feature/see-template-aois) [ready-for-review]
- Added a 3rd navigation level (Projects -> Processings -> Template). Reused the
  existing left/right "fake" nav buttons rather than new widgets; the right
  (placeholder) button becomes "enter selected template", the left button is
  context-aware (template -> processings -> projects). Decoupled map side-effects
  via ProcessingService.templateOpened/templateClosed signals so the service stays
  UI-agnostic and selection-independent (inside a template there is no template row).
- AOI names: backend parses names from searchParams.aoiDetails InputAoiProperties
  (max 64 chars); create now sends a per-feature aoiDetails FeatureCollection built
  from the source layer's `name` attribute, falling back to combined `aoi`.
- DELETE-with-body needed for bulk AOI delete: QNetworkAccessManager.deleteResource
  has no body, so http.py routes DELETE+body through sendCustomRequest with a QBuffer
  parented to the reply.
- Runtime ids are strings (dataclasses don't coerce UUID), so table_id/selection
  keys are strings throughout. ProcessingService gained class-level in_template_mode
  default so partially-constructed (test) instances don't trip PyQt's QObject guard.
- See WAL_1.md for the full step list and remaining notes.

- UI requirements:
  - show processings from template in related map layers
  - support mark image/all as seen flows
  - display template current results in search table and on map
  - expose template edit/activate/deactivate controls
  - adapt Start processing button behavior for planned processing flow
  - display templates together with processings table entries

- API spec work:
  - maintain and implement support for 002_F_plan_processing_api.md endpoints

## 2. Add new zoom-selector feature
[ ]
- Use 002_E_zoom_selector_api.md
- Add a small button near zoom selector comboBox to call zoom-selector API, active when selected source is a Mapflow data provider.
- On button press, call API and select zoom automatically depending on response.
- On error, show a reasonable user-facing message.
