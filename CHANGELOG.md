## 2.0.0
    - Reflect breaking API changes: credits-based billing instead of area-based
    - Add new error descriptions
    - Improve UI:
        - more compact layout
        - icons style like in Mapflow web
        - providers setup moved to "settings"
        - remove doubling controls, like area for imagery search, image ID label, etc.
        - more intuitive drop-down list for processing rating
    - Display processing cost or problems with processing creation parameters
    - Add links to top up balance and billing statistics pages

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