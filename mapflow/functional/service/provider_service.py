# provider_service.py
from typing import List, Optional, Tuple
from PyQt5.QtCore import QObject
from qgis.core import QgsGeometry

from ...entity.provider import ProviderInterface, ImagerySearchProvider, MyImageryProvider
from ...schema import ProductType
from ...config import Config
from ...errors import PluginError


class ProviderService(QObject):
    _instance: Optional['ProviderService'] = None
    _initialized: bool = False
    
    def __new__(cls, providers, dlg, app_context, config: Config):
        if cls._instance is None:
            cls._instance = super().__new__(cls, providers, dlg, app_context, config)
        return cls._instance
    
    def __init__(self, providers, dlg, app_context, config: Config):
        if ProviderService._initialized:
            return
        super().__init__()
        ProviderService._initialized = True
        self.providers = providers
        self.dlg = dlg
        self.app_context = app_context
        self.config = config
        self.my_imagery_provider_instance = None
        self.imagery_search_provider_instance = None
    
    @classmethod
    def instance(cls) -> 'ProviderService':
        if cls._instance is None:
            raise RuntimeError("ProviderService not initialized.")
        return cls._instance
        
    def get_current_provider_index(self):
        return self.dlg.providerIndex()
    
    def get_data_provider(self):
        return self.providers[self.dlg.providerIndex()]
    
    def update_providers_list(self, new_providers):
        self.providers += new_providers
        for provider in self.providers:
            if isinstance(provider, MyImageryProvider):
                self.my_imagery_provider_instance = provider
            if isinstance(provider, ImagerySearchProvider):
                self.imagery_search_provider_instance = provider

    def get_provider_params(self, provider, zoom):
        meta = {'source-app': 'qgis',
                'version': self.app_context.plugin_version,
                'source': provider.name.lower()}
        if not provider:
            raise PluginError(self.tr('Providers are not initialized'))
        provider_name = None
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
                    self.dlg.disable_processing_start("Test") #!
                self.imagery_search_provider_instance.image_id = image_ids
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
        if isinstance(provider, MyImageryProvider):
            if self.my_imagery_provider_instance.mosaic_id == self.my_imagery_provider_instance.image_ids == None:
                return self.tr('Choose imagery collection or image to start processing')
        elif isinstance(provider, ImagerySearchProvider):
            if self.imagery_search_provider_instance.image_id == None:
                return self.tr("This provider requires image ID. Use search tab to find imagery for you requirements, "
                               "and select image in the table.")

            




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
            self.imagery_search_provider_instance.image_id = image_id
        else:
            self.imagery_search_provider_instance.requires_id = False
            self.imagery_search_provider_instance.image_id = []
        return image_id, selection_error

        
    
    """ def get_search_images_ids(self, provider_names, product_types):
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
            self.imagery_search_provider_instance.image_id = image_id
        else:
            self.imagery_search_provider_instance.requires_id = False
            self.imagery_search_provider_instance.image_id = []
        return image_id, selection_error """



    """ def get_s3_uri(self, provider):
        s3_uri = None
        if isinstance(provider, MyImageryProvider):
            image = self.app_context.selected_image
            mosaic = self.app_context.selected_mosaic
            if image:
                s3_uri = image.image_url
            elif mosaic:
                try:
                    image_uri = self.app_context.images[0].image_url
                    # to launch for the whole mosaic we need to use minio path without the filename
                    s3_uri = image_uri.rsplit('/',1)[0]+'/'
                except:
                    s3_uri = None
        return s3_uri """

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

""" def get_s3_uri(provider):
    return ProviderService.instance().get_s3_uri(provider) """
    
'''
    def get_selected_image_indices(self):
        """Get local image indices from metadata table."""
        selected_images = self.dlg.metadataTable.selectedItems()
        if not selected_images:
            return []
        
        rows = list(set(image.row() for image in selected_images))
        return [int(self.dlg.metadataTable.item(row, self.config.LOCAL_INDEX_COLUMN).text()) 
                for row in rows]
    
    def get_search_providers_and_types(self, local_image_indices):
        """Get provider names and product types for selected images."""
        provider_names, product_types = [], []
        try:
            for idx in local_image_indices:
                feature = self.app_context.search_footprints.get(idx)
                if feature:
                    provider_names.append(feature.attribute("providerName"))
                    product_types.append(feature.attribute("productType"))
        except KeyError:
            pass
        return provider_names, product_types
    
    def get_selected_imagery_info(self):
        """Get information about selected imagery for processing request."""
        provider = self.get_current_provider()
        local_image_indices = self.get_selected_image_indices()
        provider_names, product_types = self.get_search_providers_and_types(local_image_indices)
        
        return {
            'provider': provider,
            'local_image_indices': local_image_indices,
            'provider_names': provider_names,
            'product_types': product_types
        }
    
    def get_zoom_info(self, provider, local_image_indices, product_types):
        """Get zoom information for the current provider."""
        zoom = None
        zoom_error = ""
        
        if isinstance(provider, ImagerySearchProvider):
            if local_image_indices:
                zooms = []
                for idx in local_image_indices:
                    feature = self.app_context.search_footprints.get(idx)
                    if feature:
                        zoom_val = feature.attribute("zoom")
                        if zoom_val not in (None, ''):
                            zooms.append(zoom_val)
                
                # Allow zooms only for mosaics
                if set(product_types) == set(["Mosaic"]):
                    unique_zooms = set(zooms)
                    if len(unique_zooms) > 1:
                        zoom_error = self.tr("Selected search results must have the same zoom level")
                    elif len(unique_zooms) == 1:
                        zoom = str(int(list(unique_zooms)[0]))
        elif isinstance(provider, MyImageryProvider):
            # No zoom for MyImagery
            pass
        else:
            # For XYZ providers, use settings
            if self.dlg.zoomCombo.isVisible():
                saved_zoom = self.app_context.settings.value('zoom')
                if saved_zoom:
                    zoom = saved_zoom
        
        return zoom, zoom_error
        '''