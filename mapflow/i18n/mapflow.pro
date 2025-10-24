FORM_DIRECTORY = ../dialogs/static/ui

FORMS = $$FORM_DIRECTORY/login_dialog.ui $$FORM_DIRECTORY/main_dialog.ui\
        $$FORM_DIRECTORY/provider_dialog.ui $$FORM_DIRECTORY/mosaic_dialog.ui\
        $$FORM_DIRECTORY/project_dialog.ui $$FORM_DIRECTORY/processing_start_confirmation.ui\
        $$FORM_DIRECTORY/processing_details.ui $$FORM_DIRECTORY/processing_dialog.ui

SOURCES = ../mapflow.py ../errors/data_errors.py ../errors/error_message_list.py ../errors/errors.py ../errors/processing_errors.py\ 
          ../errors/api_errors.py ../dialogs/login_dialog.py ../dialogs/main_dialog.py ../functional/service/data_catalog.py\
          ../functional/view/data_catalog_view.py ../functional/api/data_catalog_api.py ../dialogs/mosaic_dialog.py ../config.py\
          ../dialogs/project_dialog.py ../functional/helpers.py ../functional/view/project_view.py ../dialogs/processing_dialog.py\
          ../dialogs/processing_details_dialog.py ../dialogs/image_dialog.py ../dialogs/confirm_processing_start_dialog.py
TRANSLATIONS = mapflow_ru.ts
