# Journal for active implementation planning

## 1. Add support of planned processing feature (processing templates)
[ ]
- Implement planned processings using templates_service, templates_api, templates_view logic.
- User should be able to:
  - see created templates as planned processings
  - see AOIs and connected processings in one layer with clear statuses
  - navigate from template to processings launched from it
  - create, launch, delete, and update template parameters

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
