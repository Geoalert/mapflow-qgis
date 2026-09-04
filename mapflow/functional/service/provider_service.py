# provider_service.py
import logging
from typing import Optional

from PyQt5.QtCore import QObject, pyqtSignal
from qgis.core import QgsVectorLayer, QgsFeature

from . import DataCatalogService
from ..app_context import AppContext
from ...model.provider import(ImagerySearchProvider,
                               MyImageryProvider,
                               UsersProvider,
                               BasicAuth,
                               ProvidersList,
                               create_provider)
from ...infra.alert_service import alert
from ...schema import (DataProviderParams, 
                       MyImageryParams, 
                       ImagerySearchParams, 
                       UserDefinedParams)
from ...schema.processing import ProcessingDTO
from ...config import Config, ConfigColumns
from ...errors import PluginError


logger = logging.getLogger(__name__)

# `productType` casing varies by provider — My Imagery sends 'MOSAIC'/'IMAGE', other search
# providers send 'Mosaic'/'Image' — so the mosaic/product-type selection rules must compare
# case-insensitively (mirrors the case-insensitive local Mosaic/Image filter).
MOSAIC_PRODUCT_TYPES = frozenset({"MOSAIC"})

# What a duplicate_* step realistically raises when a stored processing no longer matches
# the current account or UI: a missing DTO field or absent combo entry (AttributeError),
# a renamed key (KeyError), a None where a value was expected (TypeError), an empty
# sequence (IndexError). Anything outside this set is a bug rather than stale data, so it
# is logged instead of being folded into the generic "duplication failed" alert.
DUPLICATION_FAILURES = (AttributeError, KeyError, TypeError, IndexError)


def normalized_product_types(product_types) -> set:
    """Upper-cased product-type set, for case-insensitive comparison against MOSAIC_PRODUCT_TYPES."""
    return {str(product_type).strip().upper() for product_type in product_types}


class ProviderService(QObject):
    """Provider selection, validation and the duplicate-a-processing rebuild — as requests and
    state, not widgets. It holds no dialog: the source/provider/zoom combos are `ProviderView`'s,
    the model combo and its options `ProcessingView`'s, the search table `SearchView`'s. What the
    service needs off those it is *told* (`app_context.selected_search_*`, the setters below); what
    it wants drawn it *announces* (the signals below), for `ProviderController` (and, for the
    search table, `SearchController`) to render. See `spec/007_architecture.md` § Services.
    """
    _instance: Optional['ProviderService'] = None
    _initialized: bool = False

    # ---------- what the provider panel and the start button must show (announced, never drawn) ----------
    #: A start is blocked, with this reason (the search-selection error path).
    startDisabled = pyqtSignal(str)
    #: A duplicate step (or its recovery) leaves the Start button usable.
    startEnabled = pyqtSignal()
    #: The provider list changed — refill the provider combo from this {name: api_name}.
    providersListChanged = pyqtSignal(object)
    #: The imagery sources changed — ({name: api_name}, [default names]) for the raster combos.
    imagerySourcesChanged = pyqtSignal(object, object)
    #: Duplication picked this model in the combo.
    modelSelected = pyqtSignal(str)
    #: Duplication resolved which option checkboxes to tick (by label).
    modelOptionsSet = pyqtSignal(object)
    #: Duplication chose a data provider: (source combo index, zoom or None).
    dataProviderSelected = pyqtSignal(int, object)
    #: Duplication matched an existing source by name.
    sourceSelectedByName = pyqtSignal(str)
    #: Duplication needs the provider index set (the imagery-search source, or a freshly added
    #: user provider).
    providerIndexSet = pyqtSignal(int)
    #: Duplication set the zoom (a user provider carries its own).
    zoomSet = pyqtSignal(str)
    #: Duplication of a My Imagery source: reset the mosaic table and show the catalog tab.
    myImageryDuplicated = pyqtSignal()
    #: Duplication of an imagery search: the per-row column values to fill the metadata table with.
    imagerySearchDuplicated = pyqtSignal(object)

    #: The search table's selection, pushed from the composition root — the service reads no table.
    #: `selected_search_indices` / `selected_search_image_ids` live on `app_context` beside
    #: `search_footprints` (the dict they key into); the polygon layer used to rebuild a duplicated
    #: search is pushed to `app_context.aoi_layer`.

    def __init__(self, providers: ProvidersList, app_context: AppContext, config: Config, data_catalog_service: DataCatalogService):
        if ProviderService._initialized:
            return
        super().__init__()
        ProviderService._initialized = True
        self.providers = providers
        self.app_context = app_context
        self.config = config
        self.data_catalog_service = data_catalog_service
        self.my_imagery_provider_instance = None
        self.imagery_search_provider_instance = None
        self.user_providers = ProvidersList([])
        self.default_providers = ProvidersList([])
        self.config_search_columns = ConfigColumns().METADATA_TABLE_ATTRIBUTES
        self.selection_sync_callback = None

    @classmethod
    def instance(cls) -> 'ProviderService':
        if cls._instance is None:
            raise RuntimeError("ProviderService not initialized.")
        return cls._instance

    @classmethod
    def get_instance(cls, providers: ProvidersList, app_context: AppContext, config: Config, data_catalog_service: DataCatalogService) -> 'ProviderService':
        if cls._instance is None:
            cls._instance = cls(providers, app_context, config, data_catalog_service)
        return cls._instance

    # ---------- the search selection, read off app_context (pushed, never a table) ----------

    def _selected_search_indices(self):
        return list(self.app_context.selected_search_indices or [])

    def _selected_search_image_ids(self):
        return list(self.app_context.selected_search_image_ids or [])

    def update_providers_list(self, new_providers):
        for provider in self.providers:
            if isinstance(provider, MyImageryProvider):
                self.my_imagery_provider_instance = provider
            if isinstance(provider, ImagerySearchProvider):
                self.imagery_search_provider_instance = provider

    def update_providers(self, current_model: str = "") -> None:
        """Persist the user providers and announce the refreshed combo list. The current model is
        passed in (a `ProcessingView` read) so this touches no widget."""
        self.user_providers.to_settings(self.app_context.settings)
        provider_names = {p.name: getattr(p, 'api_name', p.name) for p in self.providers}
        self.providersListChanged.emit(provider_names)
        self.set_available_imagery_sources(current_model)

    def set_available_imagery_sources(self, wd: str) -> None:
        """Announce the list of imagery sources (all search goes through the Mapflow catalog)."""
        if self.providers == self.basemap_providers:
            # Providers did not change
            return
        self.providers = self.basemap_providers
        provider_names = {p.name: getattr(p, 'api_name', p.name) for p in self.providers}
        self.imagerySourcesChanged.emit(provider_names, ['Mapbox', '🌍 Mapbox Satellite'])

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

            if self._selected_search_indices():
                local_image_indices = self.get_local_image_indices()
                provider_names, product_types = self.get_search_providers(local_image_indices)
                image_ids, selection_error = self.get_search_images_ids(provider_names, product_types)
                if selection_error:
                    self.startDisabled.emit(selection_error)
                self.imagery_search_provider_instance.image_ids = image_ids
                provider_name = provider_names[0] if provider_names else None # the same for all [i] if there was no 'selection_error'
            else:
                # Selection was cleared. Drop the cached image IDs and provider state so
                # the next /cost or create-processing call doesn't carry stale image IDs
                # paired with a missing dataProvider — that combination is rejected with 400.
                # validate_provider_params catches the missing-id case and short-circuits
                # the request via validate_all_processing_params.
                self.imagery_search_provider_instance.image_ids = None
                self.imagery_search_provider_instance.requires_id = None

        if not provider_name:
            try:
                provider_name = provider.api_name
            except AttributeError:
                # Not every provider type exposes api_name; absence is the normal case here.
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
            selected_image_ids = self._selected_search_image_ids()
            selected_rows_count = len(self._selected_search_indices())
            image_id = selected_image_ids[0] if selected_image_ids else None
            if selected_rows_count > 1:
                provider_text += " ({count} images selected)".format(count=selected_rows_count)
            elif image_id:
                provider_text += " ({iid})".format(iid=image_id)
        return provider_text
    
    def validate_provider_params(self, provider):
        error = None
        if isinstance(provider, MyImageryProvider):
            if self.my_imagery_provider_instance.mosaic_id is None and self.my_imagery_provider_instance.image_ids is None:
                error = self.tr('Choose imagery collection or image to start processing')
        elif isinstance(provider, ImagerySearchProvider):
            # `not image_ids` covers both the cleared-selection case (None) and
            # the empty-list case written by get_search_images_ids when the
            # table is empty.
            if not self.imagery_search_provider_instance.image_ids:
                error = self.tr("This provider requires image ID. Use search tab to find imagery for you requirements, "
                                "and select image in the table.")
        # Check for zoom errors by examining the current selection state
        if not error and isinstance(provider, ImagerySearchProvider):
            if self._selected_search_indices():
                local_image_indices = self.get_local_image_indices()
                provider_names, product_types = self.get_search_providers(local_image_indices)
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
                    product_type_set = normalized_product_types(product_types)
                    if len(product_type_set) > 1: # no image + mosaic
                        error = self.tr("Selected search results must be of the same product type")
                    elif (len(set(provider_names)) > 1
                          and product_type_set != MOSAIC_PRODUCT_TYPES):
                        # Mixing different providers is only allowed for Mosaics
                        # (server combines them). For Image product type, including
                        # orbview_*, the backend rejects mixed providers — block the
                        # request here so the cost/v2 call is not made with a
                        # mismatched dataProvider + imageIds payload.
                        error = self.tr("You can launch multiple image processing only if it has the same provider of mosaic type")
                    elif product_type_set == MOSAIC_PRODUCT_TYPES and len(set(zooms)) > 1: # no mosaics with different zooms
                        error = self.tr("Selected search results must have the same zoom level")
                # Minimum-area check. The server enforces a per-provider minimum
                # (ProviderMinAreaError) on the processing geometry. For credits
                # billing this rides along on the /cost response, but for AREA / NONE
                # billing /cost is not called, so without this the user only sees the
                # rejection when the processing is actually started. minAreaSqkm comes
                # in with each search result, so check it on every selection/AOI change.
                if not error and local_image_indices:
                    min_area_error = self._min_area_error(local_image_indices, provider_names)
                    if min_area_error:
                        error = min_area_error
        return error

    def _min_area_error(self, local_image_indices, provider_names):
        """Return an error string if the processing AOI is below the selected
        provider's minimum area, otherwise None.

        Compares against app_context.aoi_size, which is the cropped AOI area
        (user AOI ∩ selected image footprints) — the same geometry sent to the
        server, so the comparison matches the server-side ProviderMinAreaError.
        """
        min_areas = []
        for local_image_index in local_image_indices:
            try:
                value = self.app_context.search_footprints[local_image_index].attribute("minAreaSqkm")
            except (KeyError, AttributeError):
                continue
            if value in (None, '', 'NULL'):
                continue
            try:
                min_areas.append(float(value))
            except (TypeError, ValueError):
                continue
        if not min_areas:
            return None
        provider_min_area = max(min_areas)
        aoi_size = self.app_context.aoi_size or 0
        # Only error when we actually have an AOI to measure; a missing AOI is
        # handled by the AOI checks upstream.
        if aoi_size and aoi_size < provider_min_area:
            provider_name = provider_names[0] if provider_names else ""
            return self.tr("Geometry area is {aoiArea:.2f} sq km, which is smaller than the "
                           "minimum required area for {providerName} data provider "
                           "({providerMinArea} sq km)").format(aoiArea=aoi_size,
                                                               providerName=provider_name,
                                                               providerMinArea=provider_min_area)
        return None

    def get_local_image_indices(self):
        """The `local_index` of every selected search row. Pushed from the search table, so this
        reads no widget; the ints match `search_footprints`' keys."""
        try:
            return [int(index) for index in self._selected_search_indices()]
        except (TypeError, ValueError):
            return []
    
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
        image_ids = [image_id for image_id in self._selected_search_image_ids() if image_id] or None
        selection_error = ""
        try:
            if len(set(provider_names)) > 1:
                if normalized_product_types(product_types) != MOSAIC_PRODUCT_TYPES:
                    selection_error = self.tr("You can launch multiple image processing only if it has the same provider of mosaic type")
        except TypeError:
            # provider_names is None, or holds unhashable entries, so the selection cannot
            # be classified — return what was gathered without a selection error.
            return image_ids, selection_error
        except Exception:
            logger.exception("Unexpected error classifying the search selection")
            return image_ids, selection_error
        # Require image id only for images (not mosaics)
        if image_ids:
            self.imagery_search_provider_instance.requires_id = True
            self.imagery_search_provider_instance.image_ids = image_ids
        else:
            self.imagery_search_provider_instance.requires_id = False
            self.imagery_search_provider_instance.image_ids = []
        return image_ids, selection_error
    
    def duplicate_provider_and_model(self, processing):
        self.duplicate_provider(processing)
        self.duplicate_model(processing)
        self.duplicate_model_options(processing)
    
    def _abort_duplication(self, message: str) -> None:
        """Report a failed duplication step and return the dialog to a usable state.

        Every duplicate_* step shares this recovery: say which step failed, then re-enable
        processing so the dialog is not left stuck. Extracted because it was copy-pasted
        per handler and one copy had a transposed-letter typo
        (`self.aapp_context.llow_enable_processing`) that raised AttributeError from inside
        the error path — skipping the re-enable below and leaving exactly the stuck dialog
        this recovery exists to prevent. One copy cannot drift.
        """
        alert(message)
        for key in self.app_context.allow_enable_processing:
            self.app_context.allow_enable_processing[key] = True
        self.startEnabled.emit()

    def duplicate_provider(self, processing: ProcessingDTO):
        message = self.tr("Duplication failed on copying data source")
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
        except DUPLICATION_FAILURES:
            self._abort_duplication(message)
        except Exception:
            logger.exception("Unexpected error duplicating the data source")
            self._abort_duplication(message)

    def duplicate_model(self, processing: ProcessingDTO):
        message = self.tr("Duplication failed on copying model")
        try:
            # Whether the model is available is a question about the account's workflow defs, not
            # about the combo — the combo is filled from them. Asking the model avoids the widget.
            if self.app_context.get_workflow_def(processing.workflowDef.name) is None:
                self._abort_duplication(
                    self.tr("Model '{wd}' is not enabled for your account").format(wd=processing.workflowDef.name)
                )
            else:
                self.modelSelected.emit(processing.workflowDef.name)
        except DUPLICATION_FAILURES:
            self._abort_duplication(message)
        except Exception:
            logger.exception("Unexpected error duplicating the model")
            self._abort_duplication(message)

    def duplicate_model_options(self, processing):
        message = self.tr("Duplication failed on copying model options")
        try:
            # The available options are the current model's optional blocks (the checkboxes are
            # built from them), so read them from the workflow def rather than the widgets.
            wd = self.app_context.get_workflow_def(processing.workflowDef.name)
            model_options = [block.displayName for block in wd.optional_blocks] if wd else []
            enabled_options = [block.displayName for block in processing.blocks if block.enabled]
            options_to_enable = [option for option in enabled_options if option in model_options]
            self.modelOptionsSet.emit(options_to_enable)
            deleted_options = [enabled_option for enabled_option in enabled_options if enabled_option not in model_options]
            if deleted_options:
                self._abort_duplication(
                    self.tr("The following options no longer exist, so they have not been duplicated: {}")
                    .format(', '.join(deleted_options))
                )
        except DUPLICATION_FAILURES:
            self._abort_duplication(message)
        except Exception:
            logger.exception("Unexpected error duplicating the model options")
            self._abort_duplication(message)

    def duplicate_data_provider(self, provider: DataProviderParams):
        provider_name = provider.dataProvider.providerName
        # The combo index equals the provider's index in `providers` (set_raster_sources fills it
        # in that order), so resolve availability against `providers` instead of the combo.
        index = next((i for i, p in enumerate(self.providers)
                      if getattr(p, 'api_name', p.name) == provider_name), -1)
        if index == -1:
            self._abort_duplication(
                self.tr("Provider '{provider}' is not enabled for your account").format(provider=provider_name)
            )
        else:
            zoom = str(provider.dataProvider.zoom) if provider.dataProvider.zoom else None
            self.dataProviderSelected.emit(index, zoom)

    def duplicate_my_imagery(self, provider: MyImageryParams):
        self.data_catalog_service.clear_mosaic_selection()
        if provider.myImagery.imageIds:
            self.app_context.allow_enable_processing['my_image_loaded'] = False
            image_id = provider.myImagery.imageIds[0]
            self.data_catalog_service.get_image(image_id)
        elif provider.myImagery.mosaicId:
            self.data_catalog_service.select_mosaic_cell(provider.myImagery.mosaicId)
        self.myImageryDuplicated.emit()
        self.data_catalog_service.set_catalog_provider(self.providers)

    def duplicate_imagery_search(self, provider: ImagerySearchParams):
        self.providerIndexSet.emit(self.imagery_search_provider_index)
        image_ids = list(provider.imagerySearch.imageIds or [])
        # Only name, zoom and id are returned, so we map column indices to per-row value lookups
        def per_row_columns(row, image_id):
            return {
                self.config.NAME_COLUMN_INDEX: provider.imagerySearch.dataProvider,
                self.config.SEARCH_ID_COLUMN_INDEX: image_id,
                self.config.ZOOM_COLUMN_INDEX: provider.imagerySearch.zoom,
                self.config.LOCAL_INDEX_COLUMN: row,
            }
        column_indices = [self.config.NAME_COLUMN_INDEX,
                          self.config.SEARCH_ID_COLUMN_INDEX,
                          self.config.ZOOM_COLUMN_INDEX,
                          self.config.LOCAL_INDEX_COLUMN]
        column_names = [list(self.config_search_columns.values())[index] for index in column_indices]
        # Create pseudo search metadata vector layer
        self.app_context.metadata_layer = QgsVectorLayer('polygon?crs=epsg:4326&index=yes&' +
                                                         '&'.join(f'field={name}' for name in column_names),
                                                         'Duplicated Imagery Search',
                                                         'memory')
        data_provider = self.app_context.metadata_layer.dataProvider()
        # Fill the layer with one feature per (AOI x image_id) combination.
        # Individual image footprints aren't downloaded for duplicated processings,
        # so every row shares the AOI geometry — sufficient for selection-driven cost recalc.
        # The AOI layer is pushed to app_context (the combo is not this service's to read).
        aoi_layer = self.app_context.aoi_layer
        aoi_features = list(aoi_layer.getFeatures()) if aoi_layer is not None else []
        for row, image_id in enumerate(image_ids):
            row_columns = per_row_columns(row, image_id)
            for aoi_feature in aoi_features:
                feature = QgsFeature(self.app_context.metadata_layer.fields())
                feature.setGeometry(aoi_feature.geometry())
                self.app_context.metadata_layer.startEditing()
                for column, value in row_columns.items():
                    field_name = list(self.config_search_columns.values())[column]
                    feature.setAttribute(field_name, value)
                data_provider.addFeatures([feature])
                self.app_context.metadata_layer.commitChanges()
        self.app_context.metadata_layer.updateExtents()
        self.app_context.meta_layer_table_connection = self.app_context.metadata_layer.selectionChanged.connect(self.selection_sync_callback)
        # Create pseudo footprints dict keyed by local_index so multi-image cost requests resolve correctly.
        # local_index is stored as a string in the in-memory layer field (no explicit type was given when
        # the layer was created), but the rest of the codebase expects integer keys
        # (`get_local_image_indices` casts the table text via `int(...)`). Convert here.
        def _coerce_local_index(raw):
            try:
                return int(raw)
            except (TypeError, ValueError):
                return raw

        self.app_context.search_footprints = {
            _coerce_local_index(feature.attribute("local_index")): feature
            for feature in self.app_context.metadata_layer.getFeatures()
        }
        # The table fill and row selection belong to the search table (SearchView/SearchController);
        # hand over one row of column→value maps per image and let it draw and select them.
        self.imagerySearchDuplicated.emit(
            [per_row_columns(row, image_id) for row, image_id in enumerate(image_ids)])

    def duplicate_user_provider(self, provider: UserDefinedParams):
        duplicated_provider = None
        for p in self.providers:
            if isinstance(p, UsersProvider) and p.url == provider.userDefined.url:
                duplicated_provider = p
                self.sourceSelectedByName.emit(duplicated_provider.name)
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
            self.providerIndexSet.emit(provider_index)
        self.zoomSet.emit(str(provider.userDefined.zoom))

    def duplicate_aoi(self, provider):
        if isinstance(provider, ImagerySearchParams):
            self.duplicate_imagery_search(provider)
        if self.app_context.allow_enable_processing['aoi_loaded'] is True: # it became true somewhere else in error handler
            return
        else: # if other two are True - enable start
            self.app_context.allow_enable_processing['aoi_loaded'] = True
            if False not in self.app_context.allow_enable_processing.values():
                self.startEnabled.emit()
    
    @property
    def basemap_providers(self):
        return ProvidersList(self.default_providers + self.user_providers)
    
    @property
    def imagery_search_provider_index(self):
        for index, provider in enumerate(self.providers):
            if isinstance(provider, ImagerySearchProvider):
                return index
        return -1


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