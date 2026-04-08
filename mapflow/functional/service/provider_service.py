# provider_service.py
from typing import List, Optional, Tuple

from PyQt5.QtCore import Qt, QObject, QVariant, pyqtSignal
from PyQt5.QtWidgets import QTableWidgetItem, QWidget
from PyQt5.QtNetwork import QNetworkReply
from qgis.core import QgsGeometry, QgsVectorLayer, QgsFeature

from . import DataCatalogService
from ..app_context import AppContext
from ...entity.provider import(ProviderInterface, 
                               ImagerySearchProvider, 
                               MyImageryProvider, 
                               UsersProvider,
                               BasicAuth,
                               ProvidersList,
                               create_provider)
from ..service.alert_service import alert, AlertService
from ...schema import (ProductType, 
                       DataProviderParams, 
                       MyImageryParams, 
                       ImagerySearchParams, 
                       UserDefinedParams)
from ...schema.processing import ProcessingDTO
from ...config import Config, ConfigColumns
from ...errors import PluginError


class ProviderService(QObject):
    _instance: Optional['ProviderService'] = None
    _initialized: bool = False
    
    def __init__(self, providers: ProvidersList, dlg, app_context: AppContext, config: Config, data_catalog_service: DataCatalogService):
        if ProviderService._initialized:
            return
        super().__init__()
        ProviderService._initialized = True
        self.providers = providers
        self.dlg = dlg
        self.app_context = app_context
        self.config = config
        self.data_catalog_service = data_catalog_service
        self.my_imagery_provider_instance = None
        self.imagery_search_provider_instance = None
        self.user_providers = ProvidersList([])
        self.default_providers = ProvidersList([])
        self.sentinel_providers = ProvidersList([])
        self.config_search_columns = ConfigColumns().METADATA_TABLE_ATTRIBUTES
        self.selection_sync_callback = None

    @classmethod
    def instance(cls) -> 'ProviderService':
        if cls._instance is None:
            raise RuntimeError("ProviderService not initialized.")
        return cls._instance
    
    @classmethod
    def get_instance(cls, providers: ProvidersList, dlg, app_context: AppContext, config: Config, data_catalog_service: DataCatalogService) -> 'ProviderService':
        if cls._instance is None:
            cls._instance = cls(providers, dlg, app_context, config, data_catalog_service)
        return cls._instance
        
    def get_current_provider_index(self):
        return self.dlg.providerIndex()
    
    def get_data_provider(self):
        return self.providers[self.dlg.providerIndex()]
    
    def update_providers_list(self, new_providers):
        for provider in self.providers:
            if isinstance(provider, MyImageryProvider):
                self.my_imagery_provider_instance = provider
            if isinstance(provider, ImagerySearchProvider):
                self.imagery_search_provider_instance = provider
    
    def update_providers(self) -> None:
        """Update imagery & providers dropdown list after edit/add/remove
        It works both ways: if providers is specified, it updates the settings;
        otherwise loads providers list from settings
        """
        self.user_providers.to_settings(self.app_context.settings)
        provider_names = {p.name: getattr(p, 'api_name', p.name) for p in self.providers}
        for name, api_name in provider_names.items():
            self.dlg.providerCombo.addItem(name, api_name)
        self.set_available_imagery_sources(self.dlg.modelCombo.currentText())
    
    def set_available_imagery_sources(self, wd: str) -> None:
        """Restrict the list of imagery sources according to the selected model."""
        if self.config.SENTINEL_WD_NAME_PATTERN in wd and self.providers != self.sentinel_providers:
            self.providers = self.sentinel_providers
        elif not self.providers == self.basemap_providers:
            self.providers = self.basemap_providers
        else:
            # Providers did not change
            return
        provider_names = {p.name: getattr(p, 'api_name', p.name) for p in self.providers}
        self.dlg.set_raster_sources(provider_names=provider_names,
                                    default_provider_names=['Mapbox', '🌍 Mapbox Satellite'])

    def get_provider_params(self, provider, zoom):
        meta = {'source-app': 'qgis',
                'version': self.app_context.plugin_version,
                'source': provider.name.lower()}
        if not provider:
            raise PluginError(self.tr('Providers are not initialized'))
        provider_name = None
        local_image_indices = product_types = []

        if isinstance(provider, MyImageryProvider):
            selected_mosaic = self.app_context.selected_mosaic
            selected_image = self.app_context.selected_image
            if not selected_mosaic:
                mosaic_id = None
                image_id = None
            else:
                mosaic_id = selected_mosaic.id
                if not selected_image:
                    image_id = None
                else:
                    image_id = selected_image.id
                    mosaic_id = None
            self.my_imagery_provider_instance.mosaic_id = mosaic_id
            self.my_imagery_provider_instance.image_ids = [image_id] if image_id else None
            provider_name = provider.name
        elif isinstance(provider, ImagerySearchProvider):
            local_image_indices = []
            provider_names, product_types = [], []
            image_ids, selection_error = None, ""

            selected_images = self.dlg.metadataTable.selectedItems()
            if selected_images:
                local_image_indices = self.get_local_image_indices(selected_images) 
                provider_names, product_types = self.get_search_providers(local_image_indices)
                image_ids, selection_error = self.get_search_images_ids(provider_names, product_types)
                if selection_error:
                    self.dlg.disable_processing_start(selection_error)
                self.imagery_search_provider_instance.image_ids = image_ids
                provider_name = provider_names[0] if provider_names else None # the same for all [i] if there was no 'selection_error'

        if not provider_name:
            try:
                provider_name = provider.api_name
            except:
                provider_name = None

        provider_params, provider_meta = provider.to_processing_params(provider_name=provider_name,
                                                                       zoom=zoom)
        meta.update(**provider_meta)
        return provider_params, meta
    
    def setup_provider_info(self, provider):
        provider_text = provider.name
        if isinstance(provider, MyImageryProvider):
            image = self.app_context.selected_image
            mosaic = self.app_context.selected_mosaic
            if image:
                provider_text += " ({name})". format(name=image.filename)
            elif mosaic:
                provider_text += " ({name})". format(name=mosaic.name)
        elif isinstance(provider, ImagerySearchProvider):
            selected_cells = self.dlg.metadataTable.selectedItems()
            if not selected_cells:
                image_id = None
            else:
                id_column_index = self.config.MAXAR_ID_COLUMN_INDEX
                image_id = self.dlg.metadataTable.item(selected_cells[0].row(), id_column_index).text()
            if image_id:
                provider_text += " ({iid})". format(iid=image_id)
        return provider_text
    
    def validate_provider_params(self, provider):
        error = None
        if isinstance(provider, MyImageryProvider):
            if self.my_imagery_provider_instance.mosaic_id == self.my_imagery_provider_instance.image_ids == None:
                error = self.tr('Choose imagery collection or image to start processing')
        elif isinstance(provider, ImagerySearchProvider):
            if self.imagery_search_provider_instance.image_ids == None:
                error = self.tr("This provider requires image ID. Use search tab to find imagery for you requirements, "
                                "and select image in the table.")
        # Check for zoom errors by examining the UI state
        if not error and isinstance(provider, ImagerySearchProvider):
            selected_images = self.dlg.metadataTable.selectedItems()
            if selected_images:
                local_image_indices = self.get_local_image_indices(selected_images)
                _, product_types = self.get_search_providers(local_image_indices)
                # Check for zoom consistency
                if local_image_indices:
                    zooms = []
                    for local_image_index in local_image_indices:
                        try:
                            zoom_val = self.app_context.search_footprints[local_image_index].attribute("zoom")
                            if zoom_val not in (None, '', 'NULL'):
                                zooms.append(zoom_val)
                        except (KeyError, AttributeError):
                            continue
                    if len(set(product_types)) > 1: # no image + mosaic
                        error = self.tr("Selected search results must be of the same product type")
                    elif set(product_types) == set(["Mosaic"]) and len(set(zooms)) > 1: # no mosaics with different zooms
                        error = self.tr("Selected search results must have the same zoom level")
        return error

    def get_local_image_indices(self, selected_images):
        try:
            rows = list(set(image.row() for image in selected_images))
            local_image_indices = [int(self.dlg.metadataTable.item(row, self.config.LOCAL_INDEX_COLUMN).text()) 
                                   for row in rows]
        except (AttributeError, KeyError):
            local_image_indices = []
        return local_image_indices
    
    def get_search_providers(self, local_image_indices):
        try:
            provider_names = [self.app_context.search_footprints[local_image_index].attribute("providerName")
                              for local_image_index in local_image_indices]
        except KeyError:
            provider_names = []
        try:
            product_types = [self.app_context.search_footprints[local_image_index].attribute("productType")
                             for local_image_index in local_image_indices]
        except KeyError:
            product_types = []
        return provider_names, product_types
    
    def get_search_images_ids(self, provider_names, product_types):
        selected_cells = self.dlg.metadataTable.selectedItems()
        if not selected_cells:
            image_id = None
        else:
            id_column_index = self.config.MAXAR_ID_COLUMN_INDEX
            image_id = [self.dlg.metadataTable.item(selected_cells[0].row(), id_column_index).text()]
        selection_error = ""
        try:
            if len(set(provider_names)) > 1:
                if set(product_types) != set(["Mosaic"]):
                    selection_error = self.tr("You can launch multiple image processing only if it has the same provider of mosaic type")
        except:
            return image_id, selection_error
        # Require image id only for single images and not mosaics
        if image_id:
            self.imagery_search_provider_instance.requires_id = True
            self.imagery_search_provider_instance.image_ids = image_id
        else:
            self.imagery_search_provider_instance.requires_id = False
            self.imagery_search_provider_instance.image_ids = []
        return image_id, selection_error        
    
    def duplicate_provider_and_model(self, processing):
        self.duplicate_provider(processing)
        self.duplicate_model(processing)
        self.duplicate_model_options(processing)
    
    def duplicate_provider(self, processing: ProcessingDTO):
        try:
            provider = processing.params.sourceParams
            if isinstance(provider, DataProviderParams):
                self.duplicate_data_provider(provider)
            elif isinstance(provider, MyImageryParams):
                self.app_context.allow_enable_processing['my_mosaic_loaded'] = False
                self.duplicate_my_imagery(provider)
            elif isinstance(provider, ImagerySearchParams):
                pass # duplicate imagery search after aoi is downloaded
            elif isinstance(provider, UserDefinedParams):
                self.duplicate_user_provider(provider)
        except:
            alert(self.tr("Duplication failed on copying data source"))
            for key in self.app_context.allow_enable_processing:
                self.app_context.allow_enable_processing[key] = True
            self.dlg.startProcessing.setEnabled(True)
    
    def duplicate_model(self, processing: ProcessingDTO):
        try:
            if self.dlg.modelCombo.findText(processing.workflowDef.name) == -1: # index is -1, the item is not found
                alert(self.tr("Model '{wd}' is not enabled for your account").format(wd=processing.workflowDef.name))
                for key in self.app_context.allow_enable_processing:
                    self.app_context.allow_enable_processing[key] = True
                self.dlg.startProcessing.setEnabled(True)
            else: # item is found
                self.dlg.modelCombo.setCurrentText(processing.workflowDef.name)
        except:
            alert(self.tr("Duplication failed on copying model"))
            for key in self.app_context.allow_enable_processing:
                self.app_context.allow_enable_processing[key] = True
            self.dlg.startProcessing.setEnabled(True)
    
    def duplicate_model_options(self, processing):
        try:
            model_options = []
            enabled_options = []
            for checkbox in self.dlg.modelOptions:
                model_options.append(checkbox.text())
            for block in processing.blocks:
                if block.enabled:
                    enabled_options.append(block.displayName)
            options_to_enable = [option for option in enabled_options if option in model_options]
            for checkbox in self.dlg.modelOptions:
                if checkbox.text() in options_to_enable:
                    checkbox.setChecked(True)
                else:
                    checkbox.setChecked(False) 
            deleted_options = [enabled_option for enabled_option in enabled_options if enabled_option not in model_options]
            if deleted_options:
                alert(self.tr("The following options no longer exist, so they have not been duplicated: {}").format(', '.join(deleted_options)))
                for key in self.app_context.allow_enable_processing:
                    self.app_context.allow_enable_processing[key] = True
                self.dlg.startProcessing.setEnabled(True)
        except:
            alert(self.tr("Duplication failed on copying model options"))
            for key in self.app_context.allow_enable_processing:
                self.aapp_context.llow_enable_processing[key] = True
            self.dlg.startProcessing.setEnabled(True)

    def duplicate_data_provider(self, provider: DataProviderParams):
        provider_name = provider.dataProvider.providerName
        index = self.dlg.sourceCombo.findData(provider_name)
        if index == -1:
            alert(self.tr("Provider '{provider}' is not enabled for your account").format(provider=provider_name))
            for key in self.app_context.allow_enable_processing:
                self.app_context.allow_enable_processing[key] = True
            self.dlg.startProcessing.setEnabled(True)
        else:
            self.dlg.sourceCombo.setCurrentIndex(index)
            if self.app_context.zoom_selector:
                if provider.dataProvider.zoom:
                    self.dlg.zoomCombo.setCurrentText(str(provider.dataProvider.zoom))
                else:
                    self.dlg.zoomCombo.setCurrentIndex(0)
    
    def duplicate_my_imagery(self, provider: MyImageryParams):
        self.dlg.mosaicTable.clearSelection()
        if provider.myImagery.imageIds:
            self.app_context.allow_enable_processing['my_image_loaded'] = False
            image_id = provider.myImagery.imageIds[0]
            self.data_catalog_service.get_image(image_id)
        elif provider.myImagery.mosaicId:
            self.data_catalog_service.view.select_mosaic_cell(provider.myImagery.mosaicId)
        my_imagery_tab = self.dlg.tabWidget.findChild(QWidget, "catalogTab") 
        self.dlg.tabWidget.setCurrentWidget(my_imagery_tab)
        self.data_catalog_service.set_catalog_provider(self.providers)

    def duplicate_imagery_search(self, provider: ImagerySearchParams):
        self.dlg.sourceCombo.setCurrentIndex(self.imagery_search_provider_index)
        # Setup table to have one row
        self.dlg.metadataTable.clearContents()
        self.dlg.metadataTable.setRowCount(1)
        imagery_search_tab = self.dlg.tabWidget.findChild(QWidget, "providersTab")
        self.dlg.tabWidget.setCurrentWidget(imagery_search_tab)
        # Only name, zoom and id are returned, so we create dict with them as values and indecies as keys
        columns = {self.config.NAME_COLUMN_INDEX: provider.imagerySearch.dataProvider, 
                   self.config.MAXAR_ID_COLUMN_INDEX: provider.imagerySearch.imageIds[0], 
                   self.config.ZOOM_COLUMN_INDEX: provider.imagerySearch.zoom,
                   self.config.LOCAL_INDEX_COLUMN: 0}
        # And with column indecies we get corresponding field names
        column_names = []
        for index in columns.keys():
            column_names.append(list(self.config_search_columns.values())[index])
        # Create pseudo search metadata vector layer
        self.app_context.metadata_layer = QgsVectorLayer('polygon?crs=epsg:4326&index=yes&' +
                                                         '&'.join(f'field={name}' for name in column_names),
                                                         'Duplicated Imagery Search',
                                                         'memory')
        data_provider = self.app_context.metadata_layer.dataProvider()
        # Fill this layer with AOI (since we don't have accsess to footprint)
        for f in self.dlg.polygonCombo.currentLayer().getFeatures():
            feature = QgsFeature(self.app_context.metadata_layer.fields())
            feature.setGeometry(f.geometry())
            self.app_context.metadata_layer.startEditing()
            for column, value in columns.items():
                field_name = list(self.config_search_columns.values())[column]
                feature.setAttribute(field_name, value)
            data_provider.addFeatures([feature])
            self.app_context.metadata_layer.commitChanges()
        self.app_context.metadata_layer.updateExtents()
        self.app_context.meta_layer_table_connection = self.app_context.metadata_layer.selectionChanged.connect(self.selection_sync_callback)
        # Fill metadata table with the returned values
        for column, value in columns.items():
            table_item = QTableWidgetItem()
            table_item.setData(Qt.DisplayRole, value)
            self.dlg.metadataTable.setItem(0, column, table_item)
        # Create pseudo footprints dict for one created feature
        self.app_context.search_footprints = {0: feature for feature in self.app_context.metadata_layer.getFeatures()}
        self.dlg.metadataTableFilled.emit()
        self.dlg.metadataTable.selectRow(0)

    
    def duplicate_user_provider(self, provider: UserDefinedParams):
        duplicated_provider = None
        for p in self.providers:
            if isinstance(p, UsersProvider) and p.url == provider.userDefined.url:
                duplicated_provider = p
                self.dlg.sourceCombo.setCurrentText(duplicated_provider.name)
        if not duplicated_provider:
            provider_dict = dict(option_name=provider.userDefined.sourceType.lower(),
                                name=self.tr("Duplicated user provider"),
                                url=provider.userDefined.url,
                                crs=(provider.userDefined.crs.upper() 
                                     if provider.userDefined.crs 
                                     else None),
                                credentials=BasicAuth(str(provider.userDefined.rasterLogin), 
                                                        str(provider.userDefined.rasterPassword))
                                                        if provider.userDefined.rasterLogin
                                                        else BasicAuth(),
                                save_credentials=True)
            duplicated_provider = create_provider(**provider_dict)
            self.user_providers.append(duplicated_provider)
            provider_index = len(self.providers)
            self.update_providers()
            self.dlg.setProviderIndex(provider_index)
        if self.app_context.zoom_selector:
            self.dlg.zoomCombo.setCurrentText(str(provider.userDefined.zoom))

    def duplicate_aoi(self, provider):
        if isinstance(provider, ImagerySearchParams):
            self.duplicate_imagery_search(provider)
        if self.app_context.allow_enable_processing['aoi_loaded'] == True: # it became true somewhere else in error handler
            return
        else: # if other two are True - enable start
            self.app_context.allow_enable_processing['aoi_loaded'] = True
            if not False in self.app_context.allow_enable_processing.values():
                self.dlg.startProcessing.setEnabled(True)
    
    @property
    def basemap_providers(self):
        return ProvidersList(self.default_providers + self.user_providers)
    
    @property
    def imagery_search_provider_index(self):
        for index, provider in enumerate(self.providers):
            if isinstance(provider, ImagerySearchProvider):
                return index
        return -1


def get_data_provider():
    return ProviderService.instance().get_data_provider()

def update_providers_list(new_providers):
    ProviderService.instance().update_providers_list(new_providers)

def get_provider_params(provider, zoom):
    return ProviderService.instance().get_provider_params(provider, zoom)

def setup_provider_info(provider):
    return ProviderService.instance().setup_provider_info(provider)

def validate_provider_params(provider):
    return ProviderService.instance().validate_provider_params(provider)

def duplicate_provider_and_model(processing):
    ProviderService.instance().duplicate_provider_and_model(processing)

def duplicate_aoi_based_on_provider(provider):
    ProviderService.instance().duplicate_aoi(provider)