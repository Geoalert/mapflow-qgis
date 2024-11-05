## 2.6.3
    - Added schemas for shared projects
    - Disabled certain buttons depending on user role in a project
## 2.6.2
    - Fixed preview georeference for Mapflow Imagery Search
    - Fixed search results filtering after search provider change
    - Search results are now cleared on exit from QGIS
    - Force clearing of temporary files from previous launch on plugin startup
    - Optimized imports via PyCharm to avoid circular dependency
## 2.6.1
    - Fix python error on logout/login
## 2.6.0
    - Allow to create, modify and delete projects
    - Rename processings
    - Download and display processing AOI
    - Show preview (or OpenStreetMap) on "magnifying glass" button beside data provider
    - Fix: now all changes to the AOI layer are applied immediately to the processing area calculation
## 2.5.0
    - Allow direct login to Mapflow via OAuth2 protocol, without token
    - Add Mapflow project selection. Note: these projects are from API, not from Mapflow Web!
    - Fixed UI bugs: 
        - zooming to the selected image on "preview" button is now working properly
        - search results are now really cleared on "clear" button, and will not appear after restart
## 2.4.0
    - Show processing results via vector tiles link. Experimental feature, may be turned off in "settings".
    - Add separate "save to file" button to directly download results to .geojson (not adding layer to the project)
    - Add "Draw polygon" to AOI menu
    - Minor bug fixes and translation additions
    - Remove QGIS pre-3.20 version support
## 2.3.0
    - Add "Imagery Catalog" to search and preview archive satellite imagert via Mapflow API.
    Requires commercial subscription to process this data.
    - You can disable auto addition of any vector layer to the AOI drop-down list. See "settings" tab
    - UI state (selected processing/aoi/name) is now preserved when closing&opening plugin window
    - (for MacOS users): click on the plugin button now moves plugin window on top
    - Fix bug when the download of the result silently fails
## 2.2.1
    Hotfix:
    - fix bug with unhandled exception on opening of the plugin with opened vector layers
    - add "forest with heights" style for Forest model when classes are present
## 2.2.0
    - Add "Model options" for the models that support setup
        - This will work in the same way as options in Mapflow Web
        - Options will be available for Buildings and Forest models
    - Use data providers that are set for the users at the server, instead of builtin default providers in the plugin.
        - Old API for the default providers will be deprecated
        - All users will have access to Mapflow and ArcGIS Satellite basemaps, 
          Satimagery basemaps will be available for payed customers
        - We pause support for Maxar Securewatch via Mapflow account; you still can use it with your own Maxar credentials
    - Add "See details" button to display processing options and data source
## 2.1.1
    Hotfix: adaptation to non-breaking API changes
## 2.1.0
    - Add visibility settings for "Processings" table (see "Settings" tab)
    - Add "Cost" and "ID" as processing columns
    - For enterprise customers: new "review workflow" enabled 
      to allow reject unsatisfying processing results
    - Show all the rasters in the "Data source" list, 
      and show the reason, if the raster cannot be processed
    - Fix: allow to use selected features for processing and search 
      even if the layer contains more than 10 features
## 2.0.0
    - Reflect breaking API changes: credits-based billing instead of area-based
    - Add new error descriptions
    - Improve UI:
        - more compact layout
        - icons style like in Mapflow web
        - providers setup moved to "settings"
        - remove doubling controls, like area for imagery search, image ID label, etc.
        - more intuitive drop-down list for processing rating
    - Display processing cost
    - Display warning with processing creation parameters
    - Add Top bar with the links to top up balance and billing history pages in Mapflow user profile

## 1.8.0:
    - Change UI
        - processing controls moved to left panel
        - processings table locks while loading results
        - not allow to load results of non-finished or failed processings
        - logout button moved to "settings" tab
    - Add "rate processing" function
    - handle errors that happened on data upload
    - Turn off Sentinel-2 data processing
    - Improve user data validation:
        - Not allow upload/processing of too big images
        - Not allow AOI out of projection bounds
    - Use tilejson for processing results extent: allows to zoom to raster layers with empty processing results
    - Changes for API updates on the server-side (team accounts)

 ## 1.7.0:
    - Improve data providers management
        - Builtin Maxar and Mapbox providers now cannot be reemoved or edited
        - Maxar with user's credentials is now a separate provider
    - Display selected ImageID for maxar/sentinel provider in Processings tab
    - Group finished/failed processings notifications into one messageBox
    - Add API version check and update notifications
    - Fix some rare bugs
## 1.6.5:
    - Remove WMS raster layer support
    - Fix raster provider preview for tms and quadkey
    - Remove previous Maxar and Sentinel-2 search results layer before the new search
    - Add new tool: creation of AOI layer from map extent and from vector file
    - Improve description and links in login dialog
    - Add more processing errors descriptions, fix some translations
    - Remove "use cache" option which did not work properly
## 1.6.4:
    - Show error description in failed processings message box and in the tooltip over the processing table row
    - Exclude Maxar Basemaps from the list of default basemaps for new installations (not supported anymore)
## 1.6.3:
    - Improve error reporting
    - Fix repeating alerts on processing completion
## 1.6.2:
    - Make model & source choice more intuitive
    - Improve catalog filters & UX
## 1.6.1:
    - Fix SecureWatch single-image processing error
    - Raise Sentinel metadata area size limits
## 1.6.0:
    - Add support for Sentinel imagery: Catalog & Processing
    - Add date, cloud & intersection filters to the Catalog for both Maxar and Sentinel
## 1.5.2: 
    - Limit Maxar max zoom to 12 to prevent accidental traffic wasting
    - Alert about an invalid GeoTIFF CRS
##  1.5.1:
    - Fix permission denied when processing Maxar w/ own account
    - Prompt to enter a Connect ID on preview and metadata requests when unset
    - Add a checkbox to provider credentials to make their use more explicit
## 1.5.0:
    - Proxy support: now you can work from behind a proxy/firewall
    - New Mapflow token format: log in with a single token
    - Own GeoTIFF: upload progress is displayed in the message bar
    (!) This version introduces some breaking changes. Please, do the following:
        - Re-issue your token at https://app.mapflow.ai/account/api
        - Re-add web tile providers & Maxar Connect IDs
    Sorry for the inconvenience, enjoy using Mapflow :-)
## 1.4.1:
    - Improve Maxar usage
    - Display remaining processing limit in sq km
## 1.4.0:
    UI:
    - Plugin window is now expandable and the contents scale together with its size
    - Plugin & table size customizations are kept between sessions
    - Double-click a Maxar metadata item to preview the image
    - Plugin informs you when a processing has finished
    Tile providers:
    - Tile providers are now customizable, including Maxar. 
    - Use the drop-down list in the dedicated Provider tab to add, edit or delete providers.
    - In the case of Maxar, you can change the product's Connect ID to your own.
    - If the provider requires authentication, you can fill out the credentials below the provider list
    - Don't have a Maxar account? Use ours: leave provider credentials blank to use Geoalert's Maxar account (see https://docs.mapflow.ai/api/qgis_mapflow#how-to-connect-to-maxar-securewatch for details on limitations)
## 1.3.1: Fix forest styles
##  1.3.0: 
    - Simplify Maxar URL forming: no 'Get URL' button anymore, just enter you credentials, and the link's there.
    - The plugin's version is displayed in Help in case you need it for a support request.
    - A registration link is added to the login dialog.
    - UI improved.
## 1.2.0: 
    - Remove the Feature ID field as unnecessary. The FID is added to the URL based on the metadata table selection.
## 1.1.2: 
    - Display an alert if no AOI is selected when requesting Maxar metadata.
## 1.1.1: 
    - Add missing translations.
## 1.1.0: 
    - Add support for QGIS 3.10, 3.12 and 3.14
