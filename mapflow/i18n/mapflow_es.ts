<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1">
<context>
    <name>ApiErrors</name>
    <message>
        <location filename="../errors/api_errors.py" line="8" />
        <source>Upgrade your subscription to get access to Maxar imagery</source>
        <translation>Actualiza tu suscripción para acceder a imágenes Maxar</translation>
    </message>
    <message>
        <location filename="../errors/api_errors.py" line="9" />
        <source>Geometry area is {aoiArea} sq km, which is smaller than the minimum required area for {providerName} data provider ({providerMinArea} sq km)</source>
        <translation>El área de la geometría es {aoiArea} km², que es menor que el área mínima requerida para el proveedor de datos {providerName} ({providerMinArea} km²)</translation>
    </message>
    <message>
        <location filename="../errors/api_errors.py" line="13" />
        <source>Up to {templateAreaLimit} sq km can be used for a planned processing. Try reducing your area of interest.</source>
        <translation>Se pueden usar hasta {templateAreaLimit} km² para un procesamiento planificado. Intente reducir su área de interés.</translation>
    </message>
    <message>
        <location filename="../errors/api_errors.py" line="17" />
        <source>The processing area is too large: {area} sq.m exceeds the {aoiAreaLimit} sq.m limit. Reduce the area of interest.</source>
        <translation>El área de procesamiento es demasiado grande: {area} m² supera el límite de {aoiAreaLimit} m². Reduzca el área de interés.</translation>
    </message>
    <message>
        <location filename="../errors/api_errors.py" line="23" />
        <source>You don't have enough limit to create this planned processing. Please contact your administrator to increase the limit.</source>
        <translation>No tiene suficiente límite para crear este procesamiento planificado. Póngase en contacto con su administrador para aumentar el límite.</translation>
    </message>
    <message>
        <location filename="../errors/api_errors.py" line="27" />
        <source>You have reached the maximum number of active planned processings. Pause or delete another one before activating this template.</source>
        <translation>Ha alcanzado el número máximo de procesamientos planificados activos. Pause o elimine otro antes de activar esta plantilla.</translation>
    </message>
</context>
<context>
    <name>AreaCalculatorService</name>
    <message>
        <location filename="../functional/service/area_calculator_service.py" line="66" />
        <source>Not enough rights to start processing in a shared project ({})</source>
        <translation>No tienes suficientes permisos para iniciar un procesamiento en un proyecto compartido ({})</translation>
    </message>
    <message>
        <location filename="../functional/service/area_calculator_service.py" line="43" />
        <source>Set AOI to start processing</source>
        <translation>Establecer Área de Interés para iniciar el procesamiento</translation>
    </message>
    <message>
        <location filename="../functional/service/area_calculator_service.py" line="68" />
        <source>AOI must contain not more than {} polygons</source>
        <translation>El Área de Interés no debe contener más de {} polígonos</translation>
    </message>
    <message>
        <location filename="../functional/service/area_calculator_service.py" line="108" />
        <source>Use extent of '{name}'</source>
        <translation>Usar extensión de '{name}'</translation>
    </message>
    <message>
        <location filename="../functional/service/area_calculator_service.py" line="113" />
        <source>Use imagery extent</source>
        <translation>Usar extensión de la imagen</translation>
    </message>
    <message>
        <location filename="../functional/service/area_calculator_service.py" line="118" />
        <source>Selected AOI does not intersect the selected imagery</source>
        <translation>El Área de Interés seleccionada no intersecta con la imagen seleccionada</translation>
    </message>
    <message>
        <location filename="../functional/service/area_calculator_service.py" line="186" />
        <source>Area: {:.2f} sq.km</source>
        <translation>Área: {:.2f} km²</translation>
    </message>
    <message>
        <location filename="../functional/service/area_calculator_service.py" line="195" />
        <source>Bad AOI. AOI must be inside boundaries: 
[-180, 180] by longitude, [-90, 90] by latitude</source>
        <translation>Área de Interés inválida. El Área de Interés debe estar dentro de los límites: 
[-180, 180] en longitud, [-90, 90] en latitud</translation>
    </message>
    <message>
        <location filename="../functional/service/area_calculator_service.py" line="200" />
        <source>Providers are not initialized</source>
        <translation>Los proveedores no están inicializados</translation>
    </message>
</context>
<context>
    <name>Config</name>
    <message>
        <location filename="../config.py" line="14" />
        <source>Product Type</source>
        <translation>Tipo de Producto</translation>
    </message>
    <message>
        <location filename="../config.py" line="15" />
        <source>Provider Name</source>
        <translation>Nombre del Proveedor</translation>
    </message>
    <message>
        <location filename="../config.py" line="16" />
        <source>Preview</source>
        <translation>Vista Previa</translation>
    </message>
    <message>
        <location filename="../config.py" line="17" />
        <source>Sensor</source>
        <translation>Sensor</translation>
    </message>
    <message>
        <location filename="../config.py" line="18" />
        <source>Band Order</source>
        <translation>Orden de Bandas</translation>
    </message>
    <message>
        <location filename="../config.py" line="100" />
        <source>Cloud %</source>
        <translation>% de Nubes</translation>
    </message>
    <message>
        <location filename="../config.py" line="20" />
        <source>Off Nadir</source>
        <translation>Fuera de Nadir</translation>
    </message>
    <message>
        <location filename="../config.py" line="97" />
        <source>Date &amp; Time</source>
        <translation>Fecha y Hora</translation>
    </message>
    <message>
        <location filename="../config.py" line="22" />
        <source>Zoom level</source>
        <translation>Nivel de Zoom</translation>
    </message>
    <message>
        <location filename="../config.py" line="23" />
        <source>Spatial Resolution, m</source>
        <translation>Resolución Espacial, m</translation>
    </message>
    <message>
        <location filename="../config.py" line="24" />
        <source>Image ID</source>
        <translation>ID de Imagen</translation>
    </message>
    <message>
        <location filename="../config.py" line="29" />
        <source>Project</source>
        <translation>Proyecto</translation>
    </message>
    <message>
        <location filename="../config.py" line="27" />
        <source>Succeeded</source>
        <translation type="obsolete">Exitoso</translation>
    </message>
    <message>
        <location filename="../config.py" line="28" />
        <source>Failed</source>
        <translation type="obsolete">Fallido</translation>
    </message>
    <message>
        <location filename="../config.py" line="31" />
        <source>Author</source>
        <translation>Autor</translation>
    </message>
    <message>
        <location filename="../config.py" line="32" />
        <source>Updated at</source>
        <translation>Actualizado el</translation>
    </message>
    <message>
        <location filename="../config.py" line="33" />
        <source>Created at</source>
        <translation>Creado el</translation>
    </message>
    <message>
        <location filename="../config.py" line="30" />
        <source>State</source>
        <translation>Estado</translation>
    </message>
</context>
<context>
    <name>ConfirmProcessingStartDialog</name>
    <message>
        <location filename="../dialogs/confirm_processing_start_dialog.py" line="17" />
        <source>Confirm processing start</source>
        <translation>Confirmar inicio del procesamiento</translation>
    </message>
    <message>
        <location filename="../dialogs/confirm_processing_start_dialog.py" line="32" />
        <source>No zoom selected</source>
        <translation>No se seleccionó zoom</translation>
    </message>
    <message>
        <location filename="../dialogs/confirm_processing_start_dialog.py" line="42" />
        <source>No options selected</source>
        <translation>No se seleccionaron opciones</translation>
    </message>
</context>
<context>
    <name>CreateMosaicDialog</name>
    <message>
        <location filename="../dialogs/mosaic_dialog.py" line="30" />
        <source>Imagery collection</source>
        <translation>Colección de imágenes</translation>
    </message>
    <message>
        <location filename="../dialogs/mosaic_dialog.py" line="37" />
        <source>Imagery collection name must not be empty!</source>
        <translation>¡El nombre de la colección de imágenes no debe estar vacío!</translation>
    </message>
</context>
<context>
    <name>CreateProjectDialog</name>
    <message>
        <location filename="../dialogs/project_dialog.py" line="36" />
        <source>Create project</source>
        <translation>Crear proyecto</translation>
    </message>
</context>
<context>
    <name>DataCatalogApi</name>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="277" />
        <source>Error</source>
        <translation>Error</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="126" />
        <source>Could not delete imagery collection '{mosaic_name}'</source>
        <translation>No se pudo eliminar la colección de imágenes '{mosaic_name}'</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="128" />
        <source>Error. Could not delete following imagery collections:</source>
        <translation>Error. No se pudieron eliminar las siguientes colecciones de imágenes:</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="170" />
        <source>Failed to load imagery collection. 
Please try again later or report error</source>
        <translation>Error al cargar la colección de imágenes. 
Por favor, inténtalo de nuevo más tarde o informa del error</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="231" />
        <source>This operation is forbidden for your account, contact us</source>
        <translation>Esta operación está prohibida para tu cuenta, contáctanos</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="233" />
        <source>Imagery collection '{mosaic_name}' does not exist</source>
        <translation>La colección de imágenes '{mosaic_name}' no existe</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="235" />
        <source>Authentication error. Please log in to your account</source>
        <translation>Error de autenticación. Por favor, inicia sesión en tu cuenta</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="237" />
        <source>The image does not meet this imagery collection '{mosaic_name}' parameters. 
Either modify your image or upload it to a different collection</source>
        <translation>La imagen no cumple con los parámetros de esta colección de imágenes '{mosaic_name}'. 
Modifica tu imagen o súbela a una colección diferente</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="240" />
        <source>Could not upload '{image}' to imagery collection</source>
        <translation>No se pudo subir '{image}' a la colección de imágenes</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="242" />
        <source>Could not upload following images:
{images}</source>
        <translation>No se pudieron subir las siguientes imágenes:
{images}</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="278" />
        <source>Could not delete '{image}' from imagery collection</source>
        <translation>No se pudo eliminar '{image}' de la colección de imágenes</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="280" />
        <source>Error. Could not delete following images:</source>
        <translation>Error. No se pudieron eliminar las siguientes imágenes:</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="227" />
        <source>Request timed out or was canceled. 
Try increasing QGIS global timeout setting: 
Settings -&gt; Options -&gt; Network -&gt; Timeout</source>
        <translation>La solicitud expiró o fue cancelada. 
Intenta aumentar el tiempo de espera global de QGIS: 
Configuración -&gt; Opciones -&gt; Red -&gt; Tiempo de espera</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="364" />
        <source>Image not found or you don't have access to it</source>
        <translation>Imagen no encontrada o no tienes acceso a ella</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="366" />
        <source>This image is not available for download</source>
        <translation>Esta imagen no está disponible para descargar</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="368" />
        <source>Image data is not yet available. Please try again later</source>
        <translation>Los datos de la imagen aún no están disponibles. Por favor, inténtalo de nuevo más tarde</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="374" />
        <source>Download error</source>
        <translation>Error de descarga</translation>
    </message>
</context>
<context>
    <name>DataCatalogService</name>
    <message>
        <location filename="../functional/service/data_catalog.py" line="76" />
        <source>Choose image to upload</source>
        <translation>Elegir imagen para subir</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="118" />
        <source>&lt;center&gt;Creation of imagery collection '{mosaic_name}' failed&lt;br&gt;while trying to upload '{image}'</source>
        <translation>&lt;center&gt;La creación de la colección de imágenes '{mosaic_name}' falló&lt;br&gt;al intentar subir '{image}'</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="199" />
        <source>&lt;center&gt;Delete imagery collection &lt;b&gt;'{name}'&lt;/b&gt;?</source>
        <translation>&lt;center&gt;¿Eliminar colección de imágenes &lt;b&gt;'{name}'&lt;/b&gt;?</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="202" />
        <source>&lt;center&gt;Delete following imagery collections:&lt;br&gt;&lt;b&gt;'{names}'&lt;/b&gt;?</source>
        <translation>&lt;center&gt;¿Eliminar las siguientes colecciones de imágenes:&lt;br&gt;&lt;b&gt;'{names}'&lt;/b&gt;?</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="205" />
        <source>&lt;center&gt;Delete &lt;b&gt;{len}&lt;/b&gt; imagery collections?</source>
        <translation>&lt;center&gt;¿Eliminar &lt;b&gt;{len}&lt;/b&gt; colecciones de imágenes?</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="245" />
        <source>Please, select existing imagery collection</source>
        <translation>Por favor, selecciona una colección de imágenes existente</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="247" />
        <source>Choose images to upload</source>
        <translation>Elegir imágenes para subir</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="296" />
        <source>Raster TIFF file must be georeferenced, have size less than {size} pixels and file size less than {memory}</source>
        <translation>El archivo TIFF ráster debe estar georreferenciado, tener un tamaño menor a {size} píxeles y tamaño de archivo menor a {memory}</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="300" />
        <source>&lt;center&gt;&lt;b&gt;Error uploading '{name}'&lt;/b&gt;</source>
        <translation>&lt;center&gt;&lt;b&gt;Error al subir '{name}'&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="305" />
        <source>&lt;b&gt;Not enough storage space. &lt;/b&gt;You have {free_storage} left, but '{name}' is {image_size}</source>
        <translation>&lt;b&gt;No hay suficiente espacio de almacenamiento. &lt;/b&gt;Te quedan {free_storage}, pero '{name}' ocupa {image_size}</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="400" />
        <source>&lt;center&gt;Delete image &lt;b&gt;'{name}'&lt;/b&gt; from '{mosaic}' imagery collection?</source>
        <translation>&lt;center&gt;¿Eliminar imagen &lt;b&gt;'{name}'&lt;/b&gt; de la colección de imágenes '{mosaic}'?</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="403" />
        <source>&lt;center&gt;Delete following images from '{mosaic}' imagery collection:&lt;br&gt;&lt;b&gt;'{names}'&lt;/b&gt;?</source>
        <translation>&lt;center&gt;¿Eliminar las siguientes imágenes de la colección de imágenes '{mosaic}':&lt;br&gt;&lt;b&gt;'{names}'&lt;/b&gt;?</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="406" />
        <source>&lt;center&gt;Delete &lt;b&gt;{len}&lt;/b&gt; images from '{mosaic}' imagery collection?</source>
        <translation>&lt;center&gt;¿Eliminar &lt;b&gt;{len}&lt;/b&gt; imágenes de la colección de imágenes '{mosaic}'?</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="462" />
        <source>Please, select existing output directory in the Settings tab</source>
        <translation type="obsolete">Por favor, selecciona un directorio de salida existente en la pestaña Configuración</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="495" />
        <source>Image name should be 1-255 characters long</source>
        <translation>El nombre de la imagen debe tener entre 1 y 255 caracteres</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="667" />
        <source>Source imagery collection with id '{}' was not found </source>
        <translation>No se encontró la colección de imágenes fuente con id '{}'</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="669" />
        <source>Source image with id '{}' was not found in any of your imagery collections</source>
        <translation>No se encontró la imagen fuente con id '{}' en ninguna de tus colecciones de imágenes</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="515" />
        <source>Download URL not available</source>
        <translation>URL de descarga no disponible</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="517" />
        <source>Save image as</source>
        <translation>Guardar imagen como</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="535" />
        <source>Failed to download image: {}</source>
        <translation>Error al descargar la imagen: {}</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="542" />
        <source>Image saved to {}</source>
        <translation>Imagen guardada en {}</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="544" />
        <source>Failed to save file: {}</source>
        <translation>Error al guardar el archivo: {}</translation>
    </message>
</context>
<context>
    <name>DataCatalogView</name>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="24" />
        <source>Upload from file</source>
        <translation>Subir desde archivo</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="25" />
        <source>Choose raster layer</source>
        <translation>Elegir capa ráster</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="45" />
        <source>Add images</source>
        <translation>Añadir imágenes</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="46" />
        <source>Show images</source>
        <translation>Mostrar imágenes</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="49" />
        <source>Preview</source>
        <translation>Vista previa</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="48" />
        <source>Edit</source>
        <translation>Editar</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="50" />
        <source>Info</source>
        <translation>Información</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="51" />
        <source>Rename</source>
        <translation>Renombrar</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="75" />
        <source>A-Z</source>
        <translation>A-Z</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="75" />
        <source>Z-A</source>
        <translation>Z-A</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="75" />
        <source>Biggest first</source>
        <translation>Mayor primero</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="75" />
        <source>Smallest first</source>
        <translation>Menor primero</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="75" />
        <source>Newest first</source>
        <translation>Más reciente primero</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="75" />
        <source>Oldest first</source>
        <translation>Más antiguo primero</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="96" />
        <source>More about My imagery</source>
        <translation>Más información sobre Mis imágenes</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="519" />
        <source>Filter imagery collections by name or id</source>
        <translation>Filtrar colecciones de imágenes por nombre o id</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="130" />
        <source>Imagery collections</source>
        <translation>Colecciones de imágenes</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="293" />
        <source>Size</source>
        <translation>Tamaño</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="130" />
        <source>Created</source>
        <translation>Creado</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="469" />
        <source>Double-click to show images</source>
        <translation>Doble clic para mostrar imágenes</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="178" />
        <source>Number of images: {count} 
</source>
        <translation>Número de imágenes: {count} 
</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="188" />
        <source>Size: {mosaic_size} 
Pixel size: {pixel_size} 
CRS: {crs} 
Number of bands: {count} 
</source>
        <translation>Tamaño: {mosaic_size} 
Tamaño de píxel: {pixel_size} 
CRS: {crs} 
Número de bandas: {count} 
</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="197" />
        <source>Created: {date} at {time} 
Tags: {tags}</source>
        <translation>Creado: {date} a las {time} 
Etiquetas: {tags}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="249" />
        <source>&lt;b&gt;Name&lt;/b&gt;: {filename}                              &lt;br&gt;&lt;b&gt;Uploaded&lt;/b&gt;&lt;/br&gt;: {date} at {time}                              &lt;br&gt;&lt;b&gt;Size&lt;/b&gt;&lt;/br&gt;: {file_size}                              &lt;br&gt;&lt;b&gt;CRS&lt;/b&gt;&lt;/br&gt;: {crs}                              &lt;br&gt;&lt;b&gt;Number of bands&lt;/br&gt;&lt;/b&gt;: {bands}                              &lt;br&gt;&lt;b&gt;Width&lt;/br&gt;&lt;/b&gt;: {width} pixels                              &lt;br&gt;&lt;b&gt;Height&lt;/br&gt;&lt;/b&gt;: {height} pixels                              &lt;br&gt;&lt;b&gt;Pixel size&lt;/br&gt;&lt;/b&gt;: {pixel_size}</source>
        <translation>&lt;b&gt;Nombre&lt;/b&gt;: {filename}                              &lt;br&gt;&lt;b&gt;Subido&lt;/b&gt;&lt;/br&gt;: {date} a las {time}                              &lt;br&gt;&lt;b&gt;Tamaño&lt;/b&gt;&lt;/br&gt;: {file_size}                              &lt;br&gt;&lt;b&gt;CRS&lt;/b&gt;&lt;/br&gt;: {crs}                              &lt;br&gt;&lt;b&gt;Número de bandas&lt;/br&gt;&lt;/b&gt;: {bands}                              &lt;br&gt;&lt;b&gt;Ancho&lt;/br&gt;&lt;/b&gt;: {width} píxeles                              &lt;br&gt;&lt;b&gt;Altura&lt;/br&gt;&lt;/b&gt;: {height} píxeles                              &lt;br&gt;&lt;b&gt;Tamaño de píxel&lt;/br&gt;&lt;/b&gt;: {pixel_size}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="293" />
        <source>Images</source>
        <translation>Imágenes</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="293" />
        <source>Uploaded</source>
        <translation>Subido</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="349" />
        <source>No imagery collection with id '{mosaic_id}' was found</source>
        <translation>No se encontró ninguna colección de imágenes con id '{mosaic_id}'</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="362" />
        <source>No image with id '{image_id}' was found</source>
        <translation>No se encontró ninguna imagen con id '{image_id}'</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="376" />
        <source>Your data: {taken}. Free space: {free}</source>
        <translation>Tus datos: {taken}. Espacio libre: {free}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="392" />
        <source>Selected imagery collection: &lt;b&gt;{mosaic_name}</source>
        <translation>Colección de imágenes seleccionada: &lt;b&gt;{mosaic_name}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="406" />
        <source>No imagery collection selected</source>
        <translation>No se seleccionó ninguna colección de imágenes</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="428" />
        <source>Uploaded: {date} at {time} 
File size: {size} 
Pixel size: {pixel_size} 
CRS: {crs} 
Bands: {count}</source>
        <translation>Subido: {date} a las {time} 
Tamaño de archivo: {size} 
Tamaño de píxel: {pixel_size} 
CRS: {crs} 
Bandas: {count}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="441" />
        <source>Selected image: &lt;b&gt;{image_name}</source>
        <translation>Imagen seleccionada: &lt;b&gt;{image_name}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="456" />
        <source>No image selected</source>
        <translation>No se seleccionó ninguna imagen</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="466" />
        <source>'Cmd' + click to deselect</source>
        <translation>'Cmd' + clic para deseleccionar</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="466" />
        <source>'Ctrl' + click to deselect</source>
        <translation>'Ctrl' + clic para deseleccionar</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="483" />
        <source>Delete image</source>
        <translation>Eliminar imagen</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="484" />
        <source>Add image</source>
        <translation>Añadir imagen</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="497" />
        <source>Filter images by name or id</source>
        <translation>Filtrar imágenes por nombre o id</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="504" />
        <source>Delete collection</source>
        <translation>Eliminar colección</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="505" />
        <source>Add collection</source>
        <translation>Añadir colección</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="451" />
        <source>Download</source>
        <translation>Descargar</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="449" />
        <source>Image is not available for download</source>
        <translation>La imagen no está disponible para descargar</translation>
    </message>
</context>
<context>
    <name>DataErrors</name>
    <message>
        <location filename="../errors/data_errors.py" line="8" />
        <source>File {filename} cannot be processed. Parameters {bad_parameters} are incompatible with our catalog. See the documentation for more info.</source>
        <translation>El archivo {filename} no puede ser procesado. Los parámetros {bad_parameters} son incompatibles con nuestro catálogo. Consulta la documentación para más información.</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="11" />
        <source>Your file has size {memory_requested} bytes, but you have only {available_memory} left. Upgrade your subscription or remove older imagery from your catalog</source>
        <translation>Tu archivo tiene un tamaño de {memory_requested} bytes, pero solo te quedan {available_memory}. Actualiza tu suscripción o elimina imágenes antiguas de tu catálogo</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="14" />
        <source>Max file size allowed to upload is {max_file_size} bytes, your file is {actual_file_size} bytes instead. Compress your file or cut it into smaller parts</source>
        <translation>El tamaño máximo de archivo permitido para subir es {max_file_size} bytes, tu archivo es de {actual_file_size} bytes. Comprime tu archivo o divídelo en partes más pequeñas</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="17" />
        <source>{instance_type} with id: {uid} can't be found</source>
        <translation>No se puede encontrar {instance_type} con id: {uid}</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="18" />
        <source>You do not have access to {instance_type} with id {uid}</source>
        <translation>No tienes acceso a {instance_type} con id {uid}</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="19" />
        <source>File {filename} cannot be uploaded to imagery collection: {mosaic_id}. {param_name} of the file is {got_param}, it should be {expected_param} to fit the collection. Fix your file, or upload it to another imagery collection</source>
        <translation>El archivo {filename} no puede subirse a la colección de imágenes: {mosaic_id}. {param_name} del archivo es {got_param}, debería ser {expected_param} para encajar en la colección. Corrige tu archivo o súbelo a otra colección de imágenes</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="23" />
        <source>File can't be uploaded, because its extent is out of coordinate range.Check please CRS and transform of the image, they may be invalid</source>
        <translation>El archivo no puede subirse porque su extensión está fuera del rango de coordenadas. Verifica el CRS y la transformación de la imagen, pueden ser inválidos</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="25" />
        <source>File cannot be opened as a GeoTIFF file. Only valid geotiff files are allowed for uploading. You can use Raster-&gt;Conversion-&gt;Translate to change your file type to GeoTIFF</source>
        <translation>El archivo no puede abrirse como un archivo GeoTIFF. Solo se permiten archivos geotiff válidos para subir. Puedes usar Ráster-&gt;Conversión-&gt;Traducir para cambiar el tipo de archivo a GeoTIFF</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="28" />
        <source>File can't be uploaded, because the geometry of the image is too big, we will not be able to process it properly.Make sure that your image has valid CRS and transform, or cut the image into parts</source>
        <translation>El archivo no puede subirse porque la geometría de la imagen es demasiado grande, no podremos procesarla correctamente. Asegúrate de que tu imagen tenga un CRS y transformación válidos, o divide la imagen en partes</translation>
    </message>
</context>
<context>
    <name>Dialog</name>
    <message>
        <location filename="../dialogs/static/ui/processing_dialog.ui" line="14" />
        <source>Dialog</source>
        <translation>Diálogo</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_dialog.ui" line="20" />
        <source>Name</source>
        <translation>Nombre</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_dialog.ui" line="34" />
        <source>Description</source>
        <translation>Descripción</translation>
    </message>
</context>
<context>
    <name>ErrorDialog</name>
    <message>
        <location filename="../dialogs/static/ui/error_message.ui" line="64" />
        <source>Error</source>
        <translation>Error</translation>
    </message>
</context>
<context>
    <name>ErrorMessageList</name>
    <message>
        <location filename="../errors/error_message_list.py" line="26" />
        <source>Unknown error. Contact us to resolve the issue! help@geoalert.io</source>
        <translation>Error desconocido. ¡Contáctanos para resolver el problema! help@geoalert.io</translation>
    </message>
</context>
<context>
    <name>ErrorMessageWidget</name>
    <message>
        <location filename="../dialogs/error_message_widget.py" line="22" />
        <source>"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Let us know&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Infórmenos&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
</context>
<context>
    <name>Header</name>
    <message>
        <location filename="../functional/helpers.py" line="158" />
        <source> | Project: </source>
        <translation> | Proyecto: </translation>
    </message>
    <message>
        <location filename="../functional/helpers.py" line="161" />
        <source>owner: </source>
        <translation>propietario: </translation>
    </message>
</context>
<context>
    <name>LoginDialog</name>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="32" />
        <source>Mapflow - Log In</source>
        <translation>Mapflow - Iniciar Sesión</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="53" />
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;span style=" color:#ff0000;"&gt;Authorization is not configured! &lt;/span&gt;&lt;/p&gt;&lt;p&gt;&lt;br/&gt;Setup authorization config &lt;br/&gt;and restart QGIS before login. &lt;br/&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#oauth2_setup"&gt;&lt;span style=" text-decoration: underline; color:#094fd1;"&gt;See documentation for help &lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;span style=" color:#ff0000;"&gt;¡La autorización no está configurada! &lt;/span&gt;&lt;/p&gt;&lt;p&gt;&lt;br/&gt;Configura la autorización &lt;br/&gt;y reinicia QGIS antes de iniciar sesión. &lt;br/&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#oauth2_setup"&gt;&lt;span style=" text-decoration: underline; color:#094fd1;"&gt;Consulta la documentación para ayuda &lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="68" />
        <source>Token</source>
        <translation>Token</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="75" />
        <source>This plugin is an interface to to the Mapflow.ai satellite image processing platform. You need to register an account to use it. </source>
        <translation>Este complemento es una interfaz para la plataforma de procesamiento de imágenes satelitales Mapflow.ai. Necesitas registrar una cuenta para usarlo.</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="90" />
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href="https://app.mapflow.ai/account/api"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Get token&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;a href="https://mapflow.ai/terms-of-use-en.pdf"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Terms of use&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;Register at &lt;a href="https://mapflow.ai"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;mapflow.ai&lt;/span&gt;&lt;/a&gt; to use the plugin&lt;/p&gt;&lt;p&gt;&lt;br/&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href="https://app.mapflow.ai/account/api"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Obtener token&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;a href="https://mapflow.ai/terms-of-use-en.pdf"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Términos de uso&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;Regístrate en &lt;a href="https://mapflow.ai"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;mapflow.ai&lt;/span&gt;&lt;/a&gt; para usar el complemento&lt;/p&gt;&lt;p&gt;&lt;br/&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="111" />
        <source>Use Oauth2</source>
        <translation>Usar Oauth2</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="131" />
        <source>Cancel</source>
        <translation>Cancelar</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="138" />
        <source>Log in</source>
        <translation>Iniciar sesión</translation>
    </message>
</context>
<context>
    <name>MainDialog</name>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="106" />
        <source>Name:</source>
        <translation>Nombre:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="139" />
        <source>Area:</source>
        <translation>Área:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="146" />
        <source>Create or load vector layer with your area of interest</source>
        <translation>Crea o carga una capa vectorial con tu área de interés</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="249" />
        <source>Data source:</source>
        <translation>Fuente de datos:</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="577" />
        <source>Zoom</source>
        <translation>Zoom</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="303" />
        <source> –</source>
        <translation> –</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="308" />
        <source>14</source>
        <translation>14</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="313" />
        <source>15</source>
        <translation>15</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="318" />
        <source>16</source>
        <translation>16</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="323" />
        <source>17</source>
        <translation>17</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="328" />
        <source>18</source>
        <translation>18</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="333" />
        <source>19</source>
        <translation>19</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="338" />
        <source>20</source>
        <translation>20</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="403" />
        <source>AI model:</source>
        <translation>Modelo de IA:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="450" />
        <source>Price of the processing per sq.km</source>
        <translation>Precio del procesamiento por km²</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="431" />
        <source>CC</source>
        <translation>CC</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="453" />
        <source>10</source>
        <translation>10</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="522" />
        <source>Ctrl+S</source>
        <translation>Ctrl+S</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="536" />
        <source>Model options: </source>
        <translation>Opciones del modelo: </translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="587" />
        <source>Start processing</source>
        <translation>Iniciar procesamiento</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="513" />
        <source>Rate processing:</source>
        <translation>Calificar procesamiento:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="662" />
        <source>...</source>
        <translation>...</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="667" />
        <source>⭐⭐⭐⭐⭐</source>
        <translation>⭐⭐⭐⭐⭐</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="672" />
        <source>⭐⭐⭐⭐</source>
        <translation>⭐⭐⭐⭐</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="677" />
        <source>⭐⭐⭐</source>
        <translation>⭐⭐⭐</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="682" />
        <source>⭐⭐</source>
        <translation>⭐⭐</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="687" />
        <source>⭐</source>
        <translation>⭐</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="715" />
        <source>Share your thoughts on what aspects of this data processing work well or could be improved</source>
        <translation>Comparte tus opiniones sobre qué aspectos de este procesamiento de datos funcionan bien o podrían mejorarse</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="727" />
        <source>Accept</source>
        <translation>Aceptar</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3062" />
        <source>Review</source>
        <translation>Revisar</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="398" />
        <source>Please select processing and rating to submit</source>
        <translation>Por favor, selecciona el procesamiento y la calificación para enviar</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="764" />
        <source>Submit feedback</source>
        <translation>Enviar comentarios</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="811" />
        <source>Your balance:</source>
        <translation>Tu saldo:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="824" />
        <source> Top up balance </source>
        <translation> Recargar saldo </translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="841" />
        <source>Open billing history</source>
        <translation>Abrir historial de facturación</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="870" />
        <source>Log out</source>
        <translation>Cerrar sesión</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="902" />
        <source>Processing</source>
        <translation>Procesamiento</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="976" />
        <source>Sort by:</source>
        <translation>Ordenar por:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2965" />
        <source>Name</source>
        <translation>Nombre</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2984" />
        <source>Model</source>
        <translation>Modelo</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2997" />
        <source>Status</source>
        <translation>Estado</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1208" />
        <source>Progress %</source>
        <translation>Progreso %</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1213" />
        <source>Area, sq. km</source>
        <translation>Área, km²</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3036" />
        <source>Cost</source>
        <translation>Costo</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3049" />
        <source>Created</source>
        <translation>Creado</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1228" />
        <source>Review until</source>
        <translation>Revisar hasta</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1249" />
        <source>View results</source>
        <translation>Ver resultados</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1353" />
        <source>Delete</source>
        <translation>Eliminar</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1379" />
        <source>Filter processings by name</source>
        <translation>Filtrar procesamientos por nombre</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1434" />
        <source>Project:</source>
        <translation>Proyecto:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1493" />
        <source>Imagery search</source>
        <translation>Búsqueda de imágenes</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1499" />
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Here, you can search imagery for your area and timespan.&lt;/p&gt;&lt;p&gt;Additional filters are also available below.&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Aquí puedes buscar imágenes para tu área y período de tiempo.&lt;/p&gt;&lt;p&gt;También hay filtros adicionales disponibles a continuación.&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1502" />
        <source>Provider Imagery Catalog</source>
        <translation>Catálogo de Imágenes del Proveedor</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1513" />
        <source>Earlier images won't be shown</source>
        <translation>No se mostrarán imágenes anteriores</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1516" />
        <source>From:</source>
        <translation>Desde:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1567" />
        <source>Dates are inclusive</source>
        <translation>Las fechas son inclusivas</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1584" />
        <source>yyyy-MM-dd</source>
        <translation>aaaa-MM-dd</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1557" />
        <source>More recent images won't be shown</source>
        <translation>No se mostrarán imágenes más recientes</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1560" />
        <source>To:</source>
        <translation>Hasta:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1614" />
        <source>Mosaic</source>
        <translation>Mosaico</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1624" />
        <source>Image</source>
        <translation>Imagen</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1693" />
        <source>Click and wait for a few seconds until the table below is filled out</source>
        <translation>Haz clic y espera unos segundos hasta que se llene la tabla de abajo</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="342" />
        <source>Search </source>
        <translation>Buscar </translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1716" />
        <source>Double-click on a row to preview its image</source>
        <translation>Haz doble clic en una fila para previsualizar su imagen</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1767" />
        <source>1/1</source>
        <translation>1/1</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1850" />
        <source>Clear </source>
        <translation>Limpiar </translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1877" />
        <source>Click to specify additional search criteria</source>
        <translation>Haz clic para especificar criterios de búsqueda adicionales</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1880" />
        <source>Additional filters</source>
        <translation>Filtros adicionales</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1934" />
        <source>%</source>
        <translation>%</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1920" />
        <source>Min intersection:</source>
        <translation>Intersección mínima:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1927" />
        <source>Cloud cover up to:</source>
        <translation>Cobertura de nubes hasta:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1956" />
        <source>Images that cover fewer % of your area won't be shown</source>
        <translation>No se mostrarán imágenes que cubran menos del % de tu área</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2008" />
        <source>Providers: </source>
        <translation>Proveedores: </translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2053" />
        <source>Search only through available providers</source>
        <translation>Buscar solo entre proveedores disponibles</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2091" />
        <source>My imagery</source>
        <translation>Mis imágenes</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2116" />
        <source>Add collection</source>
        <translation>Añadir colección</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2129" />
        <source>Delete collection</source>
        <translation>Eliminar colección</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2194" />
        <source>No current selection</source>
        <translation>Sin selección actual</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2297" />
        <source>Sort by</source>
        <translation>Ordenar por</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2349" />
        <source>Imagery data</source>
        <translation>Datos de imágenes</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2615" />
        <source>Settings</source>
        <translation>Configuración</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2642" />
        <source>Add or edit imagery providers:</source>
        <translation>Añadir o editar proveedores de imágenes:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2687" />
        <source>Add your own web imagery provider</source>
        <translation>Añadir tu propio proveedor de imágenes web</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2801" />
        <source>Use all vector layers as Areas Of Interest</source>
        <translation>Usar todas las capas vectoriales como Áreas de Interés</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2811" />
        <source>Confirm processing start</source>
        <translation>Confirmar inicio del procesamiento</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2823" />
        <source>view results as a vector tiles</source>
        <translation>ver resultados como teselas vectoriales</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2836" />
        <source>save results as a local vector file</source>
        <translation>guardar resultados como archivo vectorial local</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2885" />
        <source>Configure search table:</source>
        <translation>Configurar tabla de búsqueda:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2892" />
        <source>Configure processings table:</source>
        <translation>Configurar tabla de procesamientos:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3010" />
        <source>Progress</source>
        <translation>Progreso</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3023" />
        <source>Area</source>
        <translation>Área</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3075" />
        <source>ID</source>
        <translation>ID</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3151" />
        <source>Product Type</source>
        <translation>Tipo de Producto</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3167" />
        <source>Provider Name</source>
        <translation>Nombre del Proveedor</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3183" />
        <source>Sensor</source>
        <translation>Sensor</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3199" />
        <source>Band Order</source>
        <translation>Orden de Bandas</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3215" />
        <source>Cloud %</source>
        <translation>% de Nubes</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3231" />
        <source>° Off Nadir</source>
        <translation>° Fuera de Nadir</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3247" />
        <source>Date and Time</source>
        <translation>Fecha y Hora</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3263" />
        <source>Mosaic Zoom</source>
        <translation>Zoom del Mosaico</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3276" />
        <source>Image Spatial Resolution</source>
        <translation>Resolución Espacial de la Imagen</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3289" />
        <source>Image ID</source>
        <translation>ID de Imagen</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3302" />
        <source>Preview</source>
        <translation>Vista Previa</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3334" />
        <source>Set up local working directory, where all the temporary files will be stored</source>
        <translation>Configurar directorio de trabajo local, donde se almacenarán todos los archivos temporales</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3352" />
        <source>Output directory:</source>
        <translation>Directorio de salida:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3438" />
        <source>Help</source>
        <translation>Ayuda</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3359" />
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=" margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#user-interface"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;User Interface walkthrough&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#how-to-upload-your-image"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;How to process your own image&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#how-to-use-other-imagery-services"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;How to use a different imagery tileset (XYZ or TMS)&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#how-to-connect-to-maxar-securewatch"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;How to connect to Maxar SecureWatch&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=" margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow credits&lt;/span&gt;&lt;span style=" font-size:large; font-weight:700;"&gt;&lt;br/&gt;&lt;/span&gt;&lt;/h3&gt;&lt;table border="0" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;" align="center" cellspacing="2" cellpadding="0"&gt;&lt;thead&gt;&lt;tr&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:600;"&gt;Pay as you go&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:696;"&gt;$50&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:696;"&gt;$90&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:696;"&gt;$800&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/thead&gt;&lt;tr&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;Credits for processing&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;500&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;1000&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;10000&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/table&gt;&lt;p&gt;See also – &lt;a href="https://docs.mapflow.ai/userguides/prices.html"&gt;&lt;span style=" text-decoration: underline; color:#094fd1;"&gt;How much do the processings and data cost?&lt;/span&gt;&lt;/a&gt;&lt;br/&gt;&lt;/p&gt;&lt;h3 style=" margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Join the project on &lt;a href="https://github.com/Geoalert/mapflow-qgis"&gt;&lt;span style=" font-weight:600; text-decoration: underline; color:#0000ff;"&gt;GitHub&lt;/span&gt;&lt;/a&gt; or &lt;a href="https://github.com/Geoalert/mapflow-qgis/issues"&gt;&lt;span style=" font-weight:600; text-decoration: underline; color:#0000ff;"&gt;report an issue&lt;/span&gt;&lt;/a&gt;&lt;/span&gt;&lt;/h3&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation type="obsolete">&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=" margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#user-interface"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Recorrido de la interfaz de usuario&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#how-to-upload-your-image"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Cómo procesar tu propia imagen&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#how-to-use-other-imagery-services"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Cómo usar un conjunto de teselas de imágenes diferente (XYZ o TMS)&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#how-to-connect-to-maxar-securewatch"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Cómo conectarse a Maxar SecureWatch&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=" margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Créditos de Mapflow&lt;/span&gt;&lt;span style=" font-size:large; font-weight:700;"&gt;&lt;br/&gt;&lt;/span&gt;&lt;/h3&gt;&lt;table border="0" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;" align="center" cellspacing="2" cellpadding="0"&gt;&lt;thead&gt;&lt;tr&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:600;"&gt;Pago por uso&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:696;"&gt;$50&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:696;"&gt;$90&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:696;"&gt;$800&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/thead&gt;&lt;tr&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;Créditos para procesamiento&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;500&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;1000&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;10000&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/table&gt;&lt;p&gt;Ver también – &lt;a href="https://docs.mapflow.ai/userguides/prices.html"&gt;&lt;span style=" text-decoration: underline; color:#094fd1;"&gt;¿Cuánto cuestan los procesamientos y datos?&lt;/span&gt;&lt;/a&gt;&lt;br/&gt;&lt;/p&gt;&lt;h3 style=" margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Únete al proyecto en &lt;a href="https://github.com/Geoalert/mapflow-qgis"&gt;&lt;span style=" font-weight:600; text-decoration: underline; color:#0000ff;"&gt;GitHub&lt;/span&gt;&lt;/a&gt; o &lt;a href="https://github.com/Geoalert/mapflow-qgis/issues"&gt;&lt;span style=" font-weight:600; text-decoration: underline; color:#0000ff;"&gt;reporta un problema&lt;/span&gt;&lt;/a&gt;&lt;/span&gt;&lt;/h3&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3474" />
        <source>see_details_action</source>
        <translation>ver_detalles_accion</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="132" />
        <source>Save results</source>
        <translation>Guardar resultados</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="133" />
        <source>Download AOI</source>
        <translation>Descargar Área de Interés</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="134" />
        <source>See details</source>
        <translation>Ver detalles</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="141" />
        <source>Rename</source>
        <translation>Renombrar</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="138" />
        <source>Restart</source>
        <translation>Reiniciar</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="139" />
        <source>Duplicate</source>
        <translation>Duplicar</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="359" />
        <source>
Price: {} credits per square km</source>
        <translation>
Precio: {} créditos por km cuadrado</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="370" />
        <source>Rate processing &lt;b&gt;{name}&lt;/b&gt;:</source>
        <translation>Calificar procesamiento &lt;b&gt;{name}&lt;/b&gt;:</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="503" />
        <source>Not enough rights to start processing in a shared project ({})</source>
        <translation>No tienes suficientes permisos para iniciar un procesamiento en un proyecto compartido ({})</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="516" />
        <source>Not enough rights to rate processing in a shared project ({})</source>
        <translation>No tienes suficientes permisos para calificar un procesamiento en un proyecto compartido ({})</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="518" />
        <source>Please select processing</source>
        <translation>Por favor, selecciona un procesamiento</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="522" />
        <source>Not enough rights to delete processing in a shared project ({})</source>
        <translation>No tienes suficientes permisos para eliminar un procesamiento en un proyecto compartido ({})</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="555" />
        <source>Delete project</source>
        <translation>Eliminar proyecto</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="556" />
        <source>Edit project</source>
        <translation>Editar proyecto</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="572" />
        <source>Zoom is derived from found imagery resolution</source>
        <translation>El zoom se deriva de la resolución de las imágenes encontradas</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="587" />
        <source>Previous page</source>
        <translation>Página anterior</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="588" />
        <source>Next page</source>
        <translation>Página siguiente</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="589" />
        <source>Page</source>
        <translation>Página</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="749" />
        <source>&lt;b&gt;URL:&lt;/b&gt; {url}&lt;br&gt;&lt;b&gt;Source type:&lt;/b&gt; {type}</source>
        <translation>&lt;b&gt;URL:&lt;/b&gt; {url}&lt;br&gt;&lt;b&gt;Tipo de fuente:&lt;/b&gt; {type}</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="753" />
        <source>&lt;br&gt;&lt;b&gt;CRS:&lt;/b&gt; {crs}</source>
        <translation>&lt;br&gt;&lt;b&gt;CRS:&lt;/b&gt; {crs}</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="755" />
        <source>&lt;br&gt;&lt;b&gt;Zoom:&lt;/b&gt; {zoom}</source>
        <translation>&lt;br&gt;&lt;b&gt;Zoom:&lt;/b&gt; {zoom}</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="757" />
        <source>&lt;br&gt;&lt;b&gt;Raster login:&lt;/b&gt; {login}&lt;br&gt;&lt;b&gt;Raster password:&lt;/b&gt; {password}</source>
        <translation>&lt;br&gt;&lt;b&gt;Usuario ráster:&lt;/b&gt; {login}&lt;br&gt;&lt;b&gt;Contraseña ráster:&lt;/b&gt; {password}</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="167" />
        <source>Project: &lt;b&gt;{}</source>
        <translation>Proyecto: &lt;b&gt;{}</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1665" />
        <source>Some current filters are wider than the last search. Click for details.</source>
        <translation>Algunos filtros actuales son más amplios que la última búsqueda. Haga clic para más detalles.</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1668" />
        <source>(!)</source>
        <translation>(!)</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1812" />
        <source>Save the current search filters to this template (replaces its stored search parameters)</source>
        <translation>Guarda los filtros de búsqueda actuales en esta plantilla (reemplaza sus parámetros de búsqueda guardados)</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1815" />
        <source>Update search</source>
        <translation>Actualizar búsqueda</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1828" />
        <source>Seen</source>
        <translation>Vista</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2072" />
        <source>Reset the filters to the parameters the current results were fetched with (search request or template)</source>
        <translation>Restablece los filtros a los parámetros con los que se obtuvieron los resultados actuales (petición de búsqueda o plantilla)</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2075" />
        <source>Reset filters</source>
        <translation>Restablecer filtros</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3447" />
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=" margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#user-interface"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;User Interface walkthrough&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#how-to-upload-your-image"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;How to process your own image&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#how-to-use-other-imagery-services"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;How to use a different imagery tileset (XYZ or TMS)&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=" margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow credits&lt;/span&gt;&lt;span style=" font-size:large; font-weight:700;"&gt;&lt;br/&gt;&lt;/span&gt;&lt;/h3&gt;&lt;table border="0" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;" align="center" cellspacing="2" cellpadding="0"&gt;&lt;thead&gt;&lt;tr&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:600;"&gt;Pay as you go&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:696;"&gt;$50&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:696;"&gt;$90&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:696;"&gt;$800&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/thead&gt;&lt;tr&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;Credits for processing&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;500&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;1000&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;10000&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/table&gt;&lt;p&gt;See also – &lt;a href="https://docs.mapflow.ai/userguides/prices.html"&gt;&lt;span style=" text-decoration: underline; color:#094fd1;"&gt;How much do the processings and data cost?&lt;/span&gt;&lt;/a&gt;&lt;br/&gt;&lt;/p&gt;&lt;h3 style=" margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Join the project on &lt;a href="https://github.com/Geoalert/mapflow-qgis"&gt;&lt;span style=" font-weight:600; text-decoration: underline; color:#0000ff;"&gt;GitHub&lt;/span&gt;&lt;/a&gt; or &lt;a href="https://github.com/Geoalert/mapflow-qgis/issues"&gt;&lt;span style=" font-weight:600; text-decoration: underline; color:#0000ff;"&gt;report an issue&lt;/span&gt;&lt;/a&gt;&lt;/span&gt;&lt;/h3&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation type="unfinished" />
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="63" />
        <source>Back</source>
        <translation>Atrás</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="65" />
        <source>Open processings</source>
        <translation>Abrir procesamientos</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="67" />
        <source>Open selected template</source>
        <translation>Abrir la plantilla seleccionada</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="135" />
        <source>See processings</source>
        <translation>Ver procesamientos</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="136" />
        <source>See search results</source>
        <translation>Ver resultados de búsqueda</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="142" />
        <source>Pause</source>
        <translation>Pausar</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="143" />
        <source>Resume</source>
        <translation>Reanudar</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="145" />
        <source>Rename AOI</source>
        <translation>Renombrar AOI</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="146" />
        <source>Delete AOI</source>
        <translation>Eliminar AOI</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="147" />
        <source>Add AOI from layer…</source>
        <translation>Añadir AOI desde una capa…</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="148" />
        <source>Update selected AOI</source>
        <translation>Actualizar el AOI seleccionado</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="149" />
        <source>Draw AOI on the map</source>
        <translation>Dibujar AOI en el mapa</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="150" />
        <source>Exclude from search</source>
        <translation>Excluir de la búsqueda</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="667" />
        <source>Off-Nadir °:</source>
        <translation>Off-Nadir °:</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="673" />
        <source>Show only images within this off-nadir angle range</source>
        <translation>Mostrar solo las imágenes dentro de este rango de ángulo off-nadir</translation>
    </message>
</context>
<context>
    <name>Mapflow</name>
    <message>
        <location filename="../mapflow.py" line="275" />
        <source>Error during loading the data providers: {e}</source>
        <translation>Error durante la carga de los proveedores de datos: {e}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="278" />
        <source>We failed to import providers from the settings. Please add them again</source>
        <translation>Fallamos al importar proveedores desde la configuración. Por favor, añádelos nuevamente</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="284" />
        <source>Draw AOI at the map</source>
        <translation>Dibujar Área de Interés en el mapa</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="285" />
        <source>Use imagery extent</source>
        <translation>Usar extensión de la imagen</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="287" />
        <source>Create AOI from map extent</source>
        <translation>Crear Área de Interés desde la extensión del mapa</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1518" />
        <source>Choose imagery collection or image to start processing</source>
        <translation>Elige una colección de imágenes o imagen para iniciar el procesamiento</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2015" />
        <source>Log in </source>
        <translation>Iniciar sesión </translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2087" />
        <source>This provider is default and cannot be removed</source>
        <translation>Este proveedor es por defecto y no puede ser eliminado</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2091" />
        <source>Permanently remove {}?</source>
        <translation>¿Eliminar permanentemente {}?</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2123" />
        <source>Provider name must be unique. {name} already exists, select another or delete/edit existing</source>
        <translation>El nombre del proveedor debe ser único. {name} ya existe, selecciona otro o elimina/edita el existente</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2134" />
        <source>Add new provider</source>
        <translation>Añadir nuevo proveedor</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2142" />
        <source>This is a default provider, it cannot be edited</source>
        <translation>Este es un proveedor por defecto, no puede ser editado</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2197" />
        <source>If you already know which {provider_name} image you want to process,
simply paste its ID here. Otherwise, search suitable images in the catalog below.</source>
        <translation>Si ya sabes qué imagen de {provider_name} quieres procesar,
simplemente pega su ID aquí. De lo contrario, busca imágenes adecuadas en el catálogo a continuación.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="773" />
        <source>e.g. S2B_OPER_MSI_L1C_TL_VGS4_20220209T091044_A025744_T36SXA_N04_00</source>
        <translation type="obsolete">ej. S2B_OPER_MSI_L1C_TL_VGS4_20220209T091044_A025744_T36SXA_N04_00</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2201" />
        <source>e.g. a3b154c40cc74f3b934c0ffc9b34ecd1</source>
        <translation>ej. a3b154c40cc74f3b934c0ffc9b34ecd1</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2233" />
        <source>Select output directory</source>
        <translation>Seleccionar directorio de salida</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2256" />
        <source>Please, specify an existing output directory</source>
        <translation>Por favor, especifica un directorio de salida existente</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3007" />
        <source>Please, select a valid area of interest</source>
        <translation>Por favor, selecciona un área de interés válida</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2831" />
        <source>We couldn't get metadata from the Mapflow Imagery Catalog</source>
        <translation>No pudimos obtener metadatos del Catálogo de Imágenes de Mapflow</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2834" />
        <source>. Error {error}</source>
        <translation>. Error {error}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2869" />
        <source>No images match your criteria. Try relaxing the filters.</source>
        <translation>Ninguna imagen coincide con tus criterios. Intenta relajar los filtros.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2885" />
        <source>&lt;b&gt;Results could not be loaded &lt;/b&gt;&lt;br&gt;Please, make sure you chose the right output folder in the Settings tab                                 and you have access rights to this folder</source>
        <translation>&lt;b&gt;No se pudieron cargar los resultados &lt;/b&gt;&lt;br&gt;Por favor, asegúrate de haber elegido la carpeta de salida correcta en la pestaña Configuración                                 y de que tienes derechos de acceso a esta carpeta</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1061" />
        <source>Your area of interest is too large.</source>
        <translation type="obsolete">Tu área de interés es demasiado grande.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1164" />
        <source>Please, check your credentials</source>
        <translation type="obsolete">Por favor, verifica tus credenciales</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1318" />
        <source>We couldn't fetch Sentinel metadata</source>
        <translation type="obsolete">No pudimos obtener metadatos de Sentinel</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1285" />
        <source>More</source>
        <translation type="obsolete">Más</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1404" />
        <source>Please, check your Maxar credentials</source>
        <translation type="obsolete">Por favor, verifica tus credenciales de Maxar</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1406" />
        <source>We couldn't get metadata from Maxar, error {error}</source>
        <translation type="obsolete">No pudimos obtener metadatos de Maxar, error {error}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1522" />
        <source>A Sentinel image ID should look like S2B_OPER_MSI_L1C_TL_VGS4_20220209T091044_A025744_T36SXA_N04_00 or /36/S/XA/2022/02/09/0/</source>
        <translation type="obsolete">Un ID de imagen de Sentinel debe verse como S2B_OPER_MSI_L1C_TL_VGS4_20220209T091044_A025744_T36SXA_N04_00 o /36/S/XA/2022/02/09/0/</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1530" />
        <source>A Maxar image ID should look like a3b154c40cc74f3b934c0ffc9b34ecd1</source>
        <translation type="obsolete">Un ID de imagen de Maxar debe verse como a3b154c40cc74f3b934c0ffc9b34ecd1</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1577" />
        <source>Not enough rights to start processing in a shared project ({})</source>
        <translation type="obsolete">No tienes suficientes permisos para iniciar un procesamiento en un proyecto compartido ({})</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1554" />
        <source>Set AOI to start processing</source>
        <translation type="obsolete">Establecer Área de Interés para iniciar el procesamiento</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1579" />
        <source>AOI must contain not more than {} polygons</source>
        <translation type="obsolete">El Área de Interés no debe contener más de {} polígonos</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1621" />
        <source>Use extent of '{name}'</source>
        <translation type="obsolete">Usar extensión de '{name}'</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1623" />
        <source>Select AOI to start processing</source>
        <translation type="obsolete">Seleccionar Área de Interés para iniciar el procesamiento</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1858" />
        <source>Selected AOI does not intersect the selected imagery</source>
        <translation type="obsolete">El Área de Interés seleccionada no intersecta con la imagen seleccionada</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1699" />
        <source>Area: {:.2f} sq.km</source>
        <translation type="obsolete">Área: {:.2f} km²</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1833" />
        <source>Error! Models are not initialized.
Please, make sure you have selected a project</source>
        <translation type="obsolete">¡Error! Los modelos no están inicializados.
Por favor, asegúrate de haber seleccionado un proyecto</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1845" />
        <source>Processing cost is not available:
{error}</source>
        <translation type="obsolete">El costo del procesamiento no está disponible:
{error}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1860" />
        <source>This provider requires image ID. Use search tab to find imagery for you requirements, and select image in the table.</source>
        <translation type="obsolete">Este proveedor requiere ID de imagen. Usa la pestaña de búsqueda para encontrar imágenes según tus requisitos y selecciona la imagen en la tabla.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1854" />
        <source>Choose imagery to start processing</source>
        <translation type="obsolete">Elige imágenes para iniciar el procesamiento</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1880" />
        <source>Sorry, there's no preview for this image</source>
        <translation type="obsolete">Lo sentimos, no hay vista previa para esta imagen</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1885" />
        <source>Processsing cost: {cost} credits</source>
        <translation type="obsolete">Costo del procesamiento: {cost} créditos</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1899" />
        <source>Delete selected processings?</source>
        <translation type="obsolete">¿Eliminar los procesamientos seleccionados?</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1925" />
        <source>Error deleting a processing</source>
        <translation type="obsolete">Error al eliminar un procesamiento</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3002" />
        <source>Please, specify a name for your processing</source>
        <translation>Por favor, especifica un nombre para tu procesamiento</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3005" />
        <source>Processing area layer is corrupted or has invalid projection</source>
        <translation>La capa del área de procesamiento está corrupta o tiene proyección inválida</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3009" />
        <source>Up to {} sq km can be processed at a time. Try splitting your area(s) into several processings.</source>
        <translation>Se pueden procesar hasta {} km² a la vez. Intenta dividir tu(s) área(s) en varios procesamientos.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3025" />
        <source>Providers are not initialized</source>
        <translation>Los proveedores no están inicializados</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1755" />
        <source>Bad AOI. AOI must be inside boundaries: 
[-180, 180] by longitude, [-90, 90] by latitude</source>
        <translation type="obsolete">Área de Interés inválida. El Área de Interés debe estar dentro de los límites: 
[-180, 180] en longitud, [-90, 90] en latitud</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1865" />
        <source>No project is selected</source>
        <translation type="obsolete">No se seleccionó ningún proyecto</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1894" />
        <source>Processing limit exceeded. Visit "&lt;a href="https://app.mapflow.ai/account/balance"&gt;Mapflow&lt;/a&gt;" to top up your balance</source>
        <translation type="obsolete">Límite de procesamiento excedido. Visita &lt;a href="https://app.mapflow.ai/account/balance"&gt;Mapflow&lt;/a&gt; para recargar tu saldo</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1901" />
        <source>Starting the processing...</source>
        <translation type="obsolete">Iniciando el procesamiento...</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1906" />
        <source>Could not launch processing! Error: {}.</source>
        <translation type="obsolete">¡No se pudo lanzar el procesamiento! Error: {}.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1920" />
        <source>{cost} credits</source>
        <translation type="obsolete">{cost} créditos</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1953" />
        <source> sq.km</source>
        <translation type="obsolete"> km²</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2205" />
        <source>We couldn't upload your GeoTIFF</source>
        <translation type="obsolete">No pudimos subir tu GeoTIFF</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2227" />
        <source>Success! We'll notify you when the processing has finished.</source>
        <translation type="obsolete">¡Éxito! Te notificaremos cuando el procesamiento haya terminado.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1992" />
        <source>The selected data provider is unavailable on your plan. 
 Upgrade your subscription to get access to the data. 
See pricing at &lt;a href="https://mapflow.ai/pricing"&gt;mapflow.ai&lt;/a&gt;</source>
        <translation type="obsolete">El proveedor de datos seleccionado no está disponible en tu plan. 
 Actualiza tu suscripción para acceder a los datos. 
Ver precios en &lt;a href="https://mapflow.ai/pricing"&gt;mapflow.ai&lt;/a&gt;</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2003" />
        <source>Processing creation failed</source>
        <translation type="obsolete">La creación del procesamiento falló</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3058" />
        <source>Your balance: {} credits</source>
        <translation>Tu saldo: {} créditos</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3060" />
        <source>Remaining limit: {:.2f} sq.km</source>
        <translation>Límite restante: {:.2f} km²</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3129" />
        <source>Show all</source>
        <translation>Mostrar todos</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1694" />
        <source>Sorry, we couldn't load the image</source>
        <translation type="obsolete">Lo sentimos, no pudimos cargar la imagen</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1695" />
        <source>Error previewing Sentinel imagery</source>
        <translation type="obsolete">Error al previsualizar imágenes Sentinel</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3145" />
        <source>Preview is unavailable when metadata layer is removed</source>
        <translation>La vista previa no está disponible cuando se elimina la capa de metadatos</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3197" />
        <source>Selected imagery has no preview</source>
        <translation>La imagen seleccionada no tiene vista previa</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3202" />
        <source>Preview with such URL is unavailable</source>
        <translation>La vista previa con dicha URL no está disponible</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3210" />
        <source>Preview for '{iid}' is unavailable</source>
        <translation>La vista previa para '{iid}' no está disponible</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3321" />
        <source>Could not display preview</source>
        <translation>No se pudo mostrar la vista previa</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3417" />
        <source>We couldn't load a preview for this image</source>
        <translation>No pudimos cargar una vista previa para esta imagen</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1895" />
        <source>Please, select an image to preview</source>
        <translation type="obsolete">Por favor, selecciona una imagen para previsualizar</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3394" />
        <source>Provider {name} requires image id for preview!</source>
        <translation>¡El proveedor {name} requiere ID de imagen para la vista previa!</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3398" />
        <source>Preview is unavailable for the provider {}. 
OSM layer will be added instead.</source>
        <translation>La vista previa no está disponible para el proveedor {}. 
En su lugar se añadirá la capa OSM.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3429" />
        <source>This provider requires image ID!</source>
        <translation>¡Este proveedor requiere ID de imagen!</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3680" />
        <source>Only finished processings can be rated</source>
        <translation>Solo los procesamientos finalizados pueden ser calificados</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3683" />
        <source>Processing must be in `Review required` status</source>
        <translation>El procesamiento debe estar en estado `Revisión requerida`</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3699" />
        <source>Thank you! Your rating is submitted!
We would appreciate if you add feedback as well.</source>
        <translation>¡Gracias! ¡Tu calificación ha sido enviada!
Agradeceríamos si también añades comentarios.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3706" />
        <source>Thank you! Your rating and feedback are submitted!</source>
        <translation>¡Gracias! ¡Tu calificación y comentarios han sido enviados!</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2570" />
        <source>Only correctly finished processings (status OK) can be reviewed</source>
        <translation type="obsolete">Solo los procesamientos correctamente finalizados (estado OK) pueden ser revisados</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3721" />
        <source>Not enough rights to rate processing in a shared project ({})</source>
        <translation>No tienes suficientes permisos para calificar un procesamiento en un proyecto compartido ({})</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3724" />
        <source>Please select processing</source>
        <translation>Por favor, selecciona un procesamiento</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3726" />
        <source>Only correctly finished processings (status OK) can be rated</source>
        <translation>Solo los procesamientos correctamente finalizados (estado OK) pueden ser calificados</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3728" />
        <source>Please select rating to submit</source>
        <translation>Por favor, selecciona una calificación para enviar</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3944" />
        <source>Only the results of correctly finished processing can be loaded</source>
        <translation>Solo los resultados de procesamientos correctamente finalizados pueden ser cargados</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2221" />
        <source>Directory '{}' does not exist</source>
        <translation type="obsolete">El directorio '{}' no existe</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2221" />
        <source>&lt;br&gt;Using Settings tab, change the output directory to an existing one to download the results</source>
        <translation type="obsolete">&lt;br&gt;Usando la pestaña Configuración, cambia el directorio de salida a uno existente para descargar los resultados</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4016" />
        <source>We have just set the authentication config for you. 
 You may need to restart QGIS to apply it so you could log in</source>
        <translation>Acabamos de configurar la autenticación para ti. 
 Es posible que necesites reiniciar QGIS para aplicarla y poder iniciar sesión</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4041" />
        <source>Please restart QGIS before using OAuth2 login.</source>
        <translation>Por favor, reinicia QGIS antes de usar el inicio de sesión OAuth2.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4103" />
        <source>Wrong token. Visit "&lt;a href="https://app.mapflow.ai/account/api"&gt;mapflow.ai&lt;/a&gt;" to get a new one</source>
        <translation>Token incorrecto. Visita &lt;a href="https://app.mapflow.ai/account/api"&gt;mapflow.ai&lt;/a&gt; para obtener uno nuevo</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4135" />
        <source>Proxy error. Please, check your proxy settings.</source>
        <translation>Error de proxy. Por favor, verifica la configuración de tu proxy.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4139" />
        <source>Not enough rights for this action
in a shared project '{project_name}' ({user_role})</source>
        <translation>No tienes suficientes permisos para esta acción
en un proyecto compartido '{project_name}' ({user_role})</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4145" />
        <source>This operation is forbidden for your account, contact us</source>
        <translation>Esta operación está prohibida para tu cuenta, contáctanos</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4150" />
        <source>Error</source>
        <translation>Error</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4256" />
        <source>You must upgrade your plugin version to continue work with Mapflow. 
The server requires version {server_version}, your plugin is {local_version}
Go to Plugins -&gt; Manage and Install Plugins -&gt; Upgradable</source>
        <translation>Debes actualizar la versión de tu complemento para continuar trabajando con Mapflow. 
El servidor requiere la versión {server_version}, tu complemento es {local_version}
Ve a Complementos -&gt; Administrar e instalar complementos -&gt; Actualizables</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4266" />
        <source>A new version of Mapflow plugin {server_version} is released 
We recommend you to upgrade to get all the latest features
Go to Plugins -&gt; Manage and Install Plugins -&gt; Upgradable</source>
        <translation>Se ha lanzado una nueva versión del complemento Mapflow {server_version} 
Te recomendamos actualizar para obtener todas las últimas funciones
Ve a Complementos -&gt; Administrar e instalar complementos -&gt; Actualizables</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3043" />
        <source>You can launch multiple image processing only if they have the same provider</source>
        <translation type="obsolete">Solo puedes lanzar múltiples procesamientos de imágenes si tienen el mismo proveedor</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3072" />
        <source>Selected search results must have the same zoom level</source>
        <translation type="obsolete">Los resultados de búsqueda seleccionados deben tener el mismo nivel de zoom</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3715" />
        <source>Only correctly finished processings with 'Review required' status can be reviewed</source>
        <translation>Solo los procesamientos finalizados correctamente con estado 'Revisión requerida' pueden ser revisados</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="220" />
        <source>The working directory '{dir}' is unavailable:&lt;br&gt;{error}&lt;br&gt;&lt;br&gt;It is needed to save processing results on your computer.</source>
        <translation>El directorio de trabajo '{dir}' no está disponible:&lt;br&gt;{error}&lt;br&gt;&lt;br&gt;Es necesario para guardar los resultados del procesamiento en su ordenador.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="582" />
        <source>Restart</source>
        <translation>Reiniciar</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="622" />
        <source>Start planned processing</source>
        <translation>Iniciar procesamiento planificado</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="624" />
        <source>Start processing</source>
        <translation>Iniciar procesamiento</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="636" />
        <source>Select one or more images in search results to start planned processing</source>
        <translation>Seleccione una o más imágenes en los resultados de búsqueda para iniciar el procesamiento planificado</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="667" />
        <source>No images was found</source>
        <translation>No se encontraron imágenes</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="817" />
        <source>AOI: {name}</source>
        <translation>AOI: {name}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="839" />
        <source>No AOI</source>
        <translation>Sin AOI</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1091" />
        <source>There are no polygon layers to add as AOIs. Draw one on the map or load a vector layer first.</source>
        <translation>No hay capas poligonales para añadir como AOI. Dibuje una en el mapa o cargue primero una capa vectorial.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1111" />
        <source>The selected layer(s) have no polygon features to add.</source>
        <translation>La(s) capa(s) seleccionada(s) no tienen entidades poligonales para añadir.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1175" />
        <source>This AOI has no id yet and cannot be updated. Reopen the template and try again.</source>
        <translation>Este AOI aún no tiene id y no se puede actualizar. Vuelva a abrir la plantilla e inténtelo de nuevo.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1180" />
        <source>Could not find this AOI's layer on the map. Reopen the template and try again.</source>
        <translation>No se encontró la capa de este AOI en el mapa. Vuelva a abrir la plantilla e inténtelo de nuevo.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1183" />
        <source>Editing AOI '{name}': move its vertices on the map, then Save AOI.</source>
        <translation>Editando el AOI '{name}': mueva sus vértices en el mapa y luego Guardar AOI.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1194" />
        <source>New AOI</source>
        <translation>Nuevo AOI</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1197" />
        <source>Draw the AOI polygon on the map, then Save AOI.</source>
        <translation>Dibuje el polígono del AOI en el mapa y luego pulse Guardar AOI.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1235" />
        <source>Save AOI</source>
        <translation>Guardar AOI</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1236" />
        <source>Cancel</source>
        <translation>Cancelar</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1305" />
        <source>The AOI has no geometry — draw or keep at least one polygon.</source>
        <translation>El AOI no tiene geometría: dibuje o conserve al menos un polígono.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1312" />
        <source>The edited AOI has no valid geometry.</source>
        <translation>El AOI editado no tiene una geometría válida.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1334" />
        <source>Draw at least one polygon before saving.</source>
        <translation>Dibuje al menos un polígono antes de guardar.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1336" />
        <source>Name the AOI</source>
        <translation>Nombre del AOI</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1336" />
        <source>AOI name:</source>
        <translation>Nombre del AOI:</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1342" />
        <source>AOI name must not exceed {limit} characters.</source>
        <translation>El nombre del AOI no debe superar los {limit} caracteres.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1411" />
        <source>Selected AOIs</source>
        <translation>AOI seleccionados</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1869" />
        <source>Start date {cur} is earlier than searched ({base})</source>
        <translation>La fecha inicial {cur} es anterior a la buscada ({base})</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1872" />
        <source>End date {cur} is later than searched ({base})</source>
        <translation>La fecha final {cur} es posterior a la buscada ({base})</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1877" />
        <source>Max cloud cover {cur}% is higher than searched ({base}%)</source>
        <translation>La nubosidad máxima {cur}% es mayor que la buscada ({base}%)</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1882" />
        <source>Min intersection {cur}% is lower than searched ({base}%)</source>
        <translation>La intersección mínima {cur}% es menor que la buscada ({base}%)</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1889" />
        <source>Off-nadir range {lo}-{hi}° is wider than searched ({blo}-{bhi}°)</source>
        <translation>El rango de off-nadir {lo}-{hi}° es más amplio que el buscado ({blo}-{bhi}°)</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1896" />
        <source>Product type(s) not searched: {extra}</source>
        <translation>Tipo(s) de producto no buscados: {extra}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1902" />
        <source>Showing all providers, but search was limited to: {base}</source>
        <translation>Se muestran todos los proveedores, pero la búsqueda se limitó a: {base}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1907" />
        <source>Provider(s) not searched: {extra}</source>
        <translation>Proveedor(es) no buscados: {extra}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1913" />
        <source>These filters are wider than the last search, so they will not bring more images. Run a new Search to fetch them:</source>
        <translation>Estos filtros son más amplios que la última búsqueda, por lo que no traerán más imágenes. Ejecute una nueva búsqueda para obtenerlas:</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2244" />
        <source>Cannot use '{dir}' as the working directory:
{error}

Please choose another directory.</source>
        <translation>No se puede usar '{dir}' como directorio de trabajo:
{error}

Elija otro directorio.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2268" />
        <source>Select directory…</source>
        <translation>Seleccionar directorio…</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2269" />
        <source>Later</source>
        <translation>Más tarde</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2336" />
        <source>Search</source>
        <translation>Buscar</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2336" />
        <source>Plan search</source>
        <translation>Planificar búsqueda</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2326" />
        <source>Seen</source>
        <translation>Vista</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2327" />
        <source>Seen all</source>
        <translation>Ver todas</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2340" />
        <source>Select a project to create a template</source>
        <translation>Seleccione un proyecto para crear una plantilla</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2371" />
        <source>Searching {datetime}</source>
        <translation>Buscando {datetime}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2378" />
        <source>The search area is too large for immediate processing. The Planned Search will be created and run in the background. You will be notified when results are available.</source>
        <translation>El área de búsqueda es demasiado grande para un procesamiento inmediato. Se creará una Búsqueda planificada que se ejecutará en segundo plano. Se le notificará cuando los resultados estén disponibles.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2387" />
        <source>Plan Search</source>
        <translation>Planificar búsqueda</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2437" />
        <source>AOI name '{name}' exceeds {limit} characters</source>
        <translation>El nombre del AOI '{name}' supera los {limit} caracteres</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2507" />
        <source>Please, specify a name for your search</source>
        <translation>Especifique un nombre para su búsqueda</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2523" />
        <source>Creating planned search...</source>
        <translation>Creando búsqueda planificada...</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2532" />
        <source>Planned search created successfully.</source>
        <translation>Búsqueda planificada creada correctamente.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2537" />
        <source>Template creation failed</source>
        <translation>Error al crear la plantilla</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2577" />
        <source>Updating template search parameters...</source>
        <translation>Actualizando los parámetros de búsqueda de la plantilla...</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2587" />
        <source>Template updated.</source>
        <translation>Plantilla actualizada.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2593" />
        <source>Template update failed</source>
        <translation>Error al actualizar la plantilla</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2637" />
        <source>This processing is not linked to any AOI geometry.</source>
        <translation>Este procesamiento no está vinculado a ninguna geometría de AOI.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2640" />
        <source>Exclude this processing's area from the template's search? The already-processed area will be removed from the AOI(s).</source>
        <translation>¿Excluir el área de este procesamiento de la búsqueda de la plantilla? El área ya procesada se eliminará de los AOI.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3515" />
        <source>Could not mark image(s) as seen, please try again.</source>
        <translation>No se pudieron marcar la(s) imagen(es) como vistas, inténtelo de nuevo.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3580" />
        <source>Planned processing</source>
        <translation>Procesamiento planificado</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3582" />
        <source>Planned processing. New images: {count}</source>
        <translation>Procesamiento planificado. Nuevas imágenes: {count}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3929" />
        <source>A working directory is required to save the processing results on your computer.</source>
        <translation>Se necesita un directorio de trabajo para guardar los resultados del procesamiento en su ordenador.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3955" />
        <source>A working directory is required to save the area of interest on your computer.</source>
        <translation>Se necesita un directorio de trabajo para guardar el área de interés en su ordenador.</translation>
    </message>
<message><source>The template has been created, but is inactive.

You have reached the maximum number of active planned processings. Pause or delete another one before activating this template.</source><translation>La plantilla se ha creado, pero está inactiva.

Ha alcanzado el número máximo de procesamientos planificados activos. Pause o elimine otro antes de activar esta plantilla.</translation></message></context>
<context>
    <name>MapflowLoginDialog</name>
    <message>
        <location filename="../dialogs/login_dialog.py" line="32" />
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;You will be redirecrted to web browser &lt;br/&gt;to enter your Mapflow login and password&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Serás redirigido al navegador web &lt;br/&gt;para ingresar tu usuario y contraseña de Mapflow&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/login_dialog.py" line="33" />
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;span style=" color:#ff0000;"&gt;Authorization is not completed! &lt;/span&gt;&lt;/p&gt;&lt;p&gt;&lt;br/&gt;1. Complete authorization in browser. &lt;br/&gt;&lt;br/&gt;2. If it does not help, restart QGIS. &lt;br/&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#oauth2_setup"&gt;&lt;span style=" text-decoration: underline; color:#094fd1;"&gt;See documentation for help &lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;span style=" color:#ff0000;"&gt;¡La autorización no se ha completado! &lt;/span&gt;&lt;/p&gt;&lt;p&gt;&lt;br/&gt;1. Completa la autorización en el navegador. &lt;br/&gt;&lt;br/&gt;2. Si no ayuda, reinicia QGIS. &lt;br/&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#oauth2_setup"&gt;&lt;span style=" text-decoration: underline; color:#094fd1;"&gt;Consulta la documentación para ayuda &lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/login_dialog.py" line="38" />
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href="https://app.mapflow.ai/account/api"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Get token&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;a href="https://mapflow.ai/terms-of-use-en.pdf"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Terms of use&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;Register at &lt;a href="https://mapflow.ai"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;mapflow.ai&lt;/span&gt;&lt;/a&gt; to use the plugin&lt;/p&gt;&lt;p&gt;&lt;br/&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href="https://app.mapflow.ai/account/api"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Obtener token&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;a href="https://mapflow.ai/terms-of-use-en.pdf"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Términos de uso&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;Regístrate en &lt;a href="https://mapflow.ai"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;mapflow.ai&lt;/span&gt;&lt;/a&gt; para usar el complemento&lt;/p&gt;&lt;p&gt;&lt;br/&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/login_dialog.py" line="39" />
        <source>Invalid credentials</source>
        <translation>Credenciales inválidas</translation>
    </message>
</context>
<context>
    <name>MosaicDialog</name>
    <message>
        <location filename="../dialogs/mosaic_dialog.py" line="19" />
        <source>Imagery collection name must not be empty!</source>
        <translation>¡El nombre de la colección de imágenes no debe estar vacío!</translation>
    </message>
</context>
<context>
    <name>ProcessingDetailsDialog</name>
    <message>
        <location filename="../dialogs/processing_details_dialog.py" line="15" />
        <source>Processing details</source>
        <translation>Detalles del procesamiento</translation>
    </message>
    <message>
        <location filename="../dialogs/processing_details_dialog.py" line="47" />
        <source>My imagery</source>
        <translation>Mis imágenes</translation>
    </message>
</context>
<context>
    <name>ProcessingErrors</name>
    <message>
        <location filename="../errors/processing_errors.py" line="8" />
        <source>Folder `{s3_link}` selected for processing does not contain any images. </source>
        <translation>La carpeta `{s3_link}` seleccionada para procesamiento no contiene imágenes. </translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="10" />
        <source>Task for source-validation must contain area of interest (`geometry` section)</source>
        <translation>La tarea para validación de fuente debe contener un área de interés (sección `geometry`)</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="12" />
        <source>We could not open and read the image you have uploaded</source>
        <translation>No pudimos abrir y leer la imagen que has subido</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="13" />
        <source>Image profile (metadata) must have keys {required_keys}, got profile {profile}</source>
        <translation>El perfil de imagen (metadatos) debe tener las claves {required_keys}, se obtuvo el perfil {profile}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="15" />
        <source>AOI does not intersect the selected Sentinel-2 granule {actual_cell}</source>
        <translation>El Área de Interés no intersecta con el granulo Sentinel-2 seleccionado {actual_cell}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="17" />
        <source>Key 'url' in your request must be a string, got {url_type} instead.</source>
        <translation>La clave 'url' en tu solicitud debe ser una cadena, se obtuvo {url_type} en su lugar.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="19" />
        <source>The specified basemap {url} is forbidden for processing because it contains a map, not satellite image. Our models are suited for satellite imagery.</source>
        <translation>El mapa base especificado {url} está prohibido para procesamiento porque contiene un mapa, no una imagen satelital. Nuestros modelos están diseñados para imágenes satelitales.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="22" />
        <source>Your URL must be a link starting with "http://" or "https://".</source>
        <translation>Tu URL debe ser un enlace que comience con "http://" o "https://".</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="24" />
        <source>Format of 'url' is invalid and cannot be parsed. Error: {parse_error_message}</source>
        <translation>El formato de 'url' es inválido y no puede ser analizado. Error: {parse_error_message}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="26" />
        <source>Zoom must be either empty, or integer, got {actual_zoom}</source>
        <translation>El zoom debe estar vacío o ser un entero, se obtuvo {actual_zoom}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="28" />
        <source>Zoom must be between 0 and 22, got {actual_zoom}</source>
        <translation>El zoom debe estar entre 0 y 22, se obtuvo {actual_zoom}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="29" />
        <source>Zoom must be not lower than {min_zoom}, got {actual_zoom}</source>
        <translation>El zoom no debe ser menor que {min_zoom}, se obtuvo {actual_zoom}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="30" />
        <source>Image metadata must be a dict (json)</source>
        <translation>Los metadatos de la imagen deben ser un diccionario (json)</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="31" />
        <source>Image metadata must have keys: crs, transform, dtype, count</source>
        <translation>Los metadatos de la imagen deben tener las claves: crs, transform, dtype, count</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="33" />
        <source>URL of the image at s3 storage must be a string starting with s3://, got {actual_s3_link}</source>
        <translation>La URL de la imagen en almacenamiento s3 debe ser una cadena que comience con s3://, se obtuvo {actual_s3_link}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="35" />
        <source>Request must contain either 'profile' or 'url' keys</source>
        <translation>La solicitud debe contener las claves 'profile' o 'url'</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="36" />
        <source>Failed to read file from {s3_link}.</source>
        <translation>Error al leer el archivo desde {s3_link}.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="37" />
        <source>Image data type (Dtype) must be one of {required_dtypes}, got {request_dtype}</source>
        <translation>El tipo de datos de la imagen (Dtype) debe ser uno de {required_dtypes}, se obtuvo {request_dtype}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="39" />
        <source>Number of channels in image must be one of {required_nchannels}. Got {real_nchannels}</source>
        <translation>El número de canales en la imagen debe ser uno de {required_nchannels}. Se obtuvo {real_nchannels}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="41" />
        <source>Spatial resolution of you image is too high: pixel size is {actual_res}, minimum allowed pixel size is {min_res}</source>
        <translation>La resolución espacial de tu imagen es demasiado alta: el tamaño de píxel es {actual_res}, el tamaño mínimo permitido es {min_res}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="44" />
        <source>Spatial resolution of you image is too low: pixel size is {actual_res}, maximum allowed pixel size is {max_res}</source>
        <translation>La resolución espacial de tu imagen es demasiado baja: el tamaño de píxel es {actual_res}, el tamaño máximo permitido es {max_res}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="47" />
        <source>Error occurred during image {checked_param} check: {message}. Image metadata = {metadata}.</source>
        <translation>Ocurrió un error durante la verificación de {checked_param} de la imagen: {message}. Metadatos de la imagen = {metadata}.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="49" />
        <source>Your 'url' doesn't match the format, Quadkey basemap must be a link containing "q" placeholder.</source>
        <translation>Tu 'url' no coincide con el formato, el mapa base Quadkey debe ser un enlace que contenga el marcador "q".</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="52" />
        <source>Input string {input_string} is of unknown format. It must represent Sentinel-2 granule ID.</source>
        <translation>La cadena de entrada {input_string} tiene un formato desconocido. Debe representar un ID de granulo Sentinel-2.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="54" />
        <source>Selected Sentinel-2 image cell is {actual_cell}, this model is for the cells: {allowed_cells}</source>
        <translation>La celda de imagen Sentinel-2 seleccionada es {actual_cell}, este modelo es para las celdas: {allowed_cells}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="56" />
        <source>Selected Sentinel-2 image month is {actual_month}, this model is for: {allowed_months}</source>
        <translation>El mes de la imagen Sentinel-2 seleccionada es {actual_month}, este modelo es para: {allowed_months}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="58" />
        <source>You request TMS basemap link doesn't match the format, it must be a link containing "x", "y", "z" placeholders, correct it and start processing again.</source>
        <translation>El enlace del mapa base TMS de tu solicitud no coincide con el formato, debe ser un enlace que contenga los marcadores "x", "y", "z", corrígelo e inicia el procesamiento nuevamente.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="61" />
        <source>Requirements must be dict, got {requirements_type}.</source>
        <translation>Los requisitos deben ser un diccionario, se obtuvo {requirements_type}.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="62" />
        <source>Request must be dict, got {request_type}.</source>
        <translation>La solicitud debe ser un diccionario, se obtuvo {request_type}.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="63" />
        <source>Request must contain "source_type" key</source>
        <translation>La solicitud debe contener la clave "source_type"</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="64" />
        <source>Source type {source_type} is not allowed. Use one of: {allowed_sources}</source>
        <translation>El tipo de fuente {source_type} no está permitido. Usa uno de: {allowed_sources}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="66" />
        <source>"Required" section of the requirements must contain dict, not {required_section_type}</source>
        <translation>La sección "Required" de los requisitos debe contener un diccionario, no {required_section_type}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="68" />
        <source>"Recommended" section of the requirements must contain dict, not {recommended_section_type}</source>
        <translation>La sección "Recommended" de los requisitos debe contener un diccionario, no {recommended_section_type}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="70" />
        <source>You XYZ basemap link doesn't match the format, it must be a link containing "x", "y", "z"  placeholders.</source>
        <translation>El enlace de tu mapa base XYZ no coincide con el formato, debe ser un enlace que contenga los marcadores "x", "y", "z".</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="75" />
        <source>Internal error in process of data source validation. We are working on the fix, our support will contact you.</source>
        <translation>Error interno en el proceso de validación de fuente de datos. Estamos trabajando en la solución, nuestro soporte se pondrá en contacto contigo.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="96" />
        <source>Internal error in process of loading data. We are working on the fix, our support will contact you.</source>
        <translation>Error interno en el proceso de carga de datos. Estamos trabajando en la solución, nuestro soporte se pondrá en contacto contigo.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="79" />
        <source>Wrong source type {real_source_type}. Specify one of the allowed types {allowed_source_types}.</source>
        <translation>Tipo de fuente incorrecto {real_source_type}. Especifica uno de los tipos permitidos {allowed_source_types}.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="81" />
        <source>Your data loading task requires {estimated_size} MB of memory, which exceeded allowed memory limit {allowed_size}</source>
        <translation>Tu tarea de carga de datos requiere {estimated_size} MB de memoria, lo que excede el límite de memoria permitido {allowed_size}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="83" />
        <source>Dataloader argument {argument_name} has type {argument_type}, excpected to be {expected_type}</source>
        <translation>El argumento del cargador de datos {argument_name} tiene tipo {argument_type}, se esperaba {expected_type}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="85" />
        <source>Loaded tile has {real_nchannels} channels, required number is {expected_nchannels}</source>
        <translation>El mosaico cargado tiene {real_nchannels} canales, el número requerido es {expected_nchannels}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="87" />
        <source>Loaded tile has size {real_size}, expected tile size is {expected_size}</source>
        <translation>El mosaico cargado tiene tamaño {real_size}, el tamaño esperado es {expected_size}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="89" />
        <source>Tile at location {tile_location} cannot be loaded, server response is {status}</source>
        <translation>El mosaico en la ubicación {tile_location} no se puede cargar, la respuesta del servidor es {status}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="91" />
        <source>Response content at {tile_location} cannot be decoded as an image</source>
        <translation>El contenido de la respuesta en {tile_location} no se puede decodificar como una imagen</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="98" />
        <source>The data provider contains no data for your area of interest (returned NoData tiles). Try other the data sources to get the results.</source>
        <translation>El proveedor de datos no contiene datos para tu área de interés (devuelve mosaicos sin datos). Prueba otras fuentes de datos para obtener resultados.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="100" />
        <source>Internal error in process of data preparation. We are working on the fix, our support will contact you.</source>
        <translation>Error interno en el proceso de preparación de datos. Estamos trabajando en la solución, nuestro soporte se pondrá en contacto contigo.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="102" />
        <source>Internal error in process of data processing. We are working on the fix, our support will contact you.</source>
        <translation>Error interno en el proceso de procesamiento de datos. Estamos trabajando en la solución, nuestro soporte se pondrá en contacto contigo.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="104" />
        <source>Internal error in process of saving the results. We are working on the fix, our support will contact you.</source>
        <translation>Error interno en el proceso de guardado de resultados. Estamos trabajando en la solución, nuestro soporte se pondrá en contacto contigo.</translation>
    </message>
</context>
<context>
    <name>ProcessingService</name>
    <message>
        <location filename="../functional/service/processing_service.py" line="137" />
        <source>Specify processing parameters</source>
        <translation>Especifica los parámetros del procesamiento</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="142" />
        <source>Please, specify a name for your processing</source>
        <translation>Por favor, especifica un nombre para tu procesamiento</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="147" />
        <source>Processing area layer is corrupted or has invalid projection</source>
        <translation>La capa del área de procesamiento está corrupta o tiene proyección inválida</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="149" />
        <source>Please, select a valid area of interest</source>
        <translation>Por favor, selecciona un área de interés válida</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="102" />
        <source>Up to {} sq km can be processed at a time. Try splitting your area(s) into several processings.</source>
        <translation type="obsolete">Se pueden procesar hasta {} km² a la vez. Intenta dividir tu(s) área(s) en varios procesamientos.</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="189" />
        <source>Selected AOI does not intersect the selected imagery</source>
        <translation>El Área de Interés seleccionada no intersecta con la imagen seleccionada</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="191" />
        <source>This provider requires image ID. Use search tab to find imagery for you requirements, and select image in the table.</source>
        <translation>Este proveedor requiere ID de imagen. Usa la pestaña de búsqueda para encontrar imágenes según tus requisitos y selecciona la imagen en la tabla.</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1112" />
        <source>Not enough rights to start processing in a shared project ({})</source>
        <translation>No tienes suficientes permisos para iniciar un procesamiento en un proyecto compartido ({})</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="248" />
        <source>Set AOI to start processing</source>
        <translation>Establecer Área de Interés para iniciar el procesamiento</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="250" />
        <source>Error! Models are not initialized.
Please, make sure you have selected a project</source>
        <translation>¡Error! Los modelos no están inicializados.
Por favor, asegúrate de haber seleccionado un proyecto</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="322" />
        <source>Processing limit exceeded. Visit "&lt;a href="https://app.mapflow.ai/account/balance"&gt;Mapflow&lt;/a&gt;" to top up your balance</source>
        <translation>Límite de procesamiento excedido. Visita &lt;a href="https://app.mapflow.ai/account/balance"&gt;Mapflow&lt;/a&gt; para recargar tu saldo</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="351" />
        <source>Starting the processing...</source>
        <translation>Iniciando el procesamiento...</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="361" />
        <source>Could not launch processing! Error: {}.</source>
        <translation>¡No se pudo lanzar el procesamiento! Error: {}.</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="405" />
        <source>{cost} credits</source>
        <translation>{cost} créditos</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="409" />
        <source> sq.km</source>
        <translation> km²</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="460" />
        <source>Success! We'll notify you when the processing has finished.</source>
        <translation>¡Éxito! Te notificaremos cuando el procesamiento haya terminado.</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="260" />
        <source>Failed to start processing</source>
        <translation type="obsolete">Error al iniciar el procesamiento</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="947" />
        <source>Processing completed</source>
        <translation>Procesamiento completado</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="947" />
        <source>Processing '{name}' has finished successfully</source>
        <translation>El procesamiento '{name}' ha finalizado correctamente</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="957" />
        <source>Processing failed</source>
        <translation>Procesamiento fallido</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="957" />
        <source>Processing '{name}' has failed</source>
        <translation>El procesamiento '{name}' ha fallado</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1114" />
        <source>Processing cost is not available:
{message}</source>
        <translation>El costo del procesamiento no está disponible:
{message}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="496" />
        <source>Delete selected processings?</source>
        <translation type="obsolete">¿Eliminar los procesamientos seleccionados?</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="511" />
        <source>Failed to remove processings with following ids: &lt;center&gt; {failed_ids}</source>
        <translation type="obsolete">Error al eliminar los procesamientos con los siguientes ids: &lt;center&gt; {failed_ids}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="517" />
        <source>The selected data provider is unavailable on your plan. 
 Upgrade your subscription to get access to the data. 
See pricing at &lt;a href="https://mapflow.ai/pricing"&gt;mapflow.ai&lt;/a&gt;</source>
        <translation>El proveedor de datos seleccionado no está disponible en tu plan. 
 Actualiza tu suscripción para acceder a los datos. 
Ver precios en &lt;a href="https://mapflow.ai/pricing"&gt;mapflow.ai&lt;/a&gt;</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="528" />
        <source>Processing creation failed</source>
        <translation>La creación del procesamiento falló</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="157" />
        <source>The processing area is {area} sq km, over the {limit} sq km limit. Try splitting your area(s) into several processings.</source>
        <translation>El área de procesamiento es de {area} km², por encima del límite de {limit} km². Intente dividir su área en varios procesamientos.</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="170" />
        <source>An AOI is too large: its bounding box is {area} sq km, over the {limit} sq km limit. Reduce the area of interest.</source>
        <translation>Un AOI es demasiado grande: su rectángulo delimitador es de {area} km², por encima del límite de {limit} km². Reduzca el área de interés.</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="180" />
        <source>the selected</source>
        <translation>el seleccionado</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="288" />
        <source>Select one or more images in search results to start planned processing</source>
        <translation>Seleccione una o más imágenes en los resultados de búsqueda para iniciar el procesamiento planificado</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="340" />
        <source>Starting planned processing...</source>
        <translation>Iniciando procesamiento planificado...</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="989" />
        <source>Rename template</source>
        <translation>Renombrar plantilla</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="989" />
        <source>Template name:</source>
        <translation>Nombre de la plantilla:</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1000" />
        <source>Please, specify template name</source>
        <translation>Especifique el nombre de la plantilla</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1045" />
        <source>Error renaming template: {}</source>
        <translation>Error al renombrar la plantilla: {}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1232" />
        <source>Unknown server error</source>
        <translation>Error del servidor desconocido</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1129" />
        <source>Delete selected items?</source>
        <translation>¿Eliminar los elementos seleccionados?</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1144" />
        <source>Failed to remove items with following ids: &lt;center&gt; {failed_ids}</source>
        <translation>No se pudieron eliminar los elementos con los siguientes ids: &lt;center&gt; {failed_ids}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1210" />
        <source>Template is not active</source>
        <translation>La plantilla no está activa</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1216" />
        <source>Template paused successfully</source>
        <translation>Plantilla pausada correctamente</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1218" />
        <source>Failed to pause template: {}</source>
        <translation>No se pudo pausar la plantilla: {}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1236" />
        <source>Error pausing template: {}</source>
        <translation>Error al pausar la plantilla: {}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1254" />
        <source>Template is already active</source>
        <translation>La plantilla ya está activa</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1285" />
        <source>Template resumed successfully</source>
        <translation>Plantilla reanudada correctamente</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1287" />
        <source>Failed to resume template: {}</source>
        <translation>No se pudo reanudar la plantilla: {}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1292" />
        <source>Error resuming template: {}</source>
        <translation>Error al reanudar la plantilla: {}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1301" />
        <source>Only failed templates can be restarted</source>
        <translation>Solo se pueden reiniciar las plantillas fallidas</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1313" />
        <source>Template restarted successfully</source>
        <translation>Plantilla reiniciada correctamente</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1315" />
        <source>Failed to restart template: {}</source>
        <translation>No se pudo reiniciar la plantilla: {}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1319" />
        <source>Error restarting template: {}</source>
        <translation>Error al reiniciar la plantilla: {}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1328" />
        <source>Delete Template</source>
        <translation>Eliminar plantilla</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1328" />
        <source>Are you sure you want to delete the template '{}'?</source>
        <translation>¿Seguro que desea eliminar la plantilla '{}'?</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1346" />
        <source>Template deleted successfully</source>
        <translation>Plantilla eliminada correctamente</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1348" />
        <source>Failed to delete template: {}</source>
        <translation>No se pudo eliminar la plantilla: {}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1352" />
        <source>Error deleting template: {}</source>
        <translation>Error al eliminar la plantilla: {}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1364" />
        <source>This AOI has no id yet and cannot be renamed. Reopen the template and try again.</source>
        <translation>Este AOI aún no tiene id y no se puede renombrar. Vuelva a abrir la plantilla e inténtelo de nuevo.</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1368" />
        <source>Rename AOI</source>
        <translation>Renombrar AOI</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1368" />
        <source>AOI name:</source>
        <translation>Nombre del AOI:</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1378" />
        <source>Please, specify AOI name</source>
        <translation>Especifique el nombre del AOI</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1381" />
        <source>AOI name must not exceed {limit} characters</source>
        <translation>El nombre del AOI no debe superar los {limit} caracteres</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1403" />
        <source>Delete selected AOI(s)?</source>
        <translation>¿Eliminar el/los AOI seleccionados?</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1441" />
        <source>AOI update failed: {}</source>
        <translation>Error al actualizar el AOI: {}</translation>
    </message>
</context>
<context>
    <name>ProcessingView</name>
    <message>
        <location filename="../functional/view/processing_view.py" line="230" />
        <source>Please review or accept this processing until {}. Double click to add results to the map</source>
        <translation>Por favor, revisa o acepta este procesamiento hasta {}. Haz doble clic para añadir resultados al mapa</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="235" />
        <source>Double click to add results to the map.</source>
        <translation>Haz doble clic para añadir resultados al mapa.</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="321" />
        <source>Loading...</source>
        <translation>Cargando...</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="322" />
        <source>Fetching your processings from server, please wait</source>
        <translation>Obteniendo tus procesamientos del servidor, por favor espera</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="379" />
        <source>Processing cost: {cost} credits</source>
        <translation>Costo del procesamiento: {cost} créditos</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="388" />
        <source> failed with error:
</source>
        <translation> falló con error:
</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="395" />
        <source>{} processings failed: 
 {} 
 See tooltip over the processings table for error details</source>
        <translation>{} procesamientos fallaron: 
 {} 
 Ver información sobre herramientas en la tabla de procesamientos para detalles del error</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="402" />
        <source>{} processings failed: 
 See tooltip over the processings table for error details</source>
        <translation>{} procesamientos fallaron: 
 Ver información sobre herramientas en la tabla de procesamientos para detalles del error</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="414" />
        <source> finished. Double-click it in the table to download the results.</source>
        <translation> finalizado. Haz doble clic en la tabla para descargar los resultados.</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="422" />
        <source>{} processings finished: 
 {} 
 Double-click it in the table to download the results</source>
        <translation>{} procesamientos finalizaron: 
 {} 
 Haz doble clic en la tabla para descargar los resultados</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="430" />
        <source>{} processings finished. 
 Double-click it in the table to download the results</source>
        <translation>{} procesamientos finalizaron. 
 Haz doble clic en la tabla para descargar los resultados</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="36" />
        <source>Newest first</source>
        <translation>Más reciente primero</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="36" />
        <source>Oldest first</source>
        <translation>Más antiguo primero</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="36" />
        <source>A-Z</source>
        <translation>A-Z</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="36" />
        <source>Z-A</source>
        <translation>Z-A</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="36" />
        <source>Status A-Z</source>
        <translation>Estado A-Z</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="36" />
        <source>Status Z-A</source>
        <translation>Estado Z-A</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="45" />
        <source>Filter processings</source>
        <translation>Filtrar procesamientos</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="140" />
        <source>Open Details</source>
        <translation>Abrir detalles</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="142" />
        <source>Pause Template</source>
        <translation>Pausar plantilla</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="143" />
        <source>Resume Template</source>
        <translation>Reanudar plantilla</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="145" />
        <source>Delete Template</source>
        <translation>Eliminar plantilla</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="212" />
        <source>Planned processing</source>
        <translation>Procesamiento planificado</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="214" />
        <source>Planned processing. New images: {count}</source>
        <translation>Procesamiento planificado. Nuevas imágenes: {count}</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="219" />
        <source>Template AOI</source>
        <translation>AOI de la plantilla</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="221" />
        <source>Template AOI with new images</source>
        <translation>AOI de la plantilla con nuevas imágenes</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="224" />
        <source>Processing from this AOI. Double-click to load results.</source>
        <translation>Procesamiento de este AOI. Haga doble clic para cargar los resultados.</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="226" />
        <source>Processings not intersecting any AOI</source>
        <translation>Procesamientos que no intersecan ningún AOI</translation>
    </message>
</context>
<context>
    <name>ProjectDialog</name>
    <message>
        <location filename="../dialogs/static/ui/project_dialog.ui" line="14" />
        <source>Project</source>
        <translation>Proyecto</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/project_dialog.ui" line="20" />
        <source>Name</source>
        <translation>Nombre</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/mosaic_dialog.ui" line="34" />
        <source>Tags</source>
        <translation>Etiquetas</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/mosaic_dialog.ui" line="51" />
        <source>Note: separate tags with comma (", ") </source>
        <translation>Nota: separa las etiquetas con coma (", ") </translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/mosaic_dialog.ui" line="75" />
        <source>Create empty mosaic</source>
        <translation>Crear mosaico vacío</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/mosaic_dialog.ui" line="80" />
        <source>Upload from files</source>
        <translation>Subir desde archivos</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/mosaic_dialog.ui" line="85" />
        <source>Choose raster layers</source>
        <translation>Elegir capas ráster</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/project_dialog.ui" line="34" />
        <source>Description</source>
        <translation>Descripción</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="26" />
        <source>Start processing with specified parameters?</source>
        <translation>¿Iniciar procesamiento con los parámetros especificados?</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="66" />
        <source>Area:</source>
        <translation>Área:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="82" />
        <source>Name:</source>
        <translation>Nombre:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="132" />
        <source>Data source:</source>
        <translation>Fuente de datos:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="216" />
        <source>Zoom:</source>
        <translation>Zoom:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="232" />
        <source>Model options:</source>
        <translation>Opciones del modelo:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="248" />
        <source>Price:</source>
        <translation>Precio:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="332" />
        <source>Model:</source>
        <translation>Modelo:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="428" />
        <source>Don't show this message again</source>
        <translation>No mostrar este mensaje de nuevo</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_details.ui" line="177" />
        <source>ID:</source>
        <translation>ID:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_details.ui" line="193" />
        <source>Status:</source>
        <translation>Estado:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_details.ui" line="209" />
        <source>Description:</source>
        <translation>Descripción:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_details.ui" line="444" />
        <source>Data provider:</source>
        <translation>Proveedor de datos:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_details.ui" line="492" />
        <source>Error:</source>
        <translation>Error:</translation>
    </message>
    <message>
        <location filename="../dialogs/project_dialog.py" line="25" />
        <source>Project name must not be empty!</source>
        <translation>¡El nombre del proyecto no debe estar vacío!</translation>
    </message>
    <message>
        <location filename="../dialogs/project_dialog.py" line="55" />
        <source>Edit project </source>
        <translation>Editar proyecto </translation>
    </message>
</context>
<context>
    <name>ProjectProcessingController</name>
    <message>
        <location filename="../functional/controller/processing_controller.py" line="205" />
        <source>Do you really want to remove project {}? This action cannot be undone, all processings will be lost!</source>
        <translation>¿Realmente desea eliminar el proyecto {}? ¡Esta acción no se puede deshacer, todos los procesamientos se perderán!</translation>
    </message>
    <message>
        <location filename="../functional/controller/processing_controller.py" line="107" />
        <source>Processing</source>
        <translation>Procesamiento</translation>
    </message>
</context>
<context>
    <name>ProjectService</name>
    <message>
        <location filename="../functional/service/project_service.py" line="227" />
        <source>Project: &lt;b&gt;{}</source>
        <translation>Proyecto: &lt;b&gt;{}</translation>
    </message>
    <message>
        <location filename="../functional/service/project_service.py" line="244" />
        <source>No project selected</source>
        <translation>No se seleccionó ningún proyecto</translation>
    </message>
    <message>
        <location filename="../functional/service/project_service.py" line="246" />
        <source>You can't remove or modify default project</source>
        <translation>No puedes eliminar o modificar el proyecto por defecto</translation>
    </message>
    <message>
        <location filename="../functional/service/project_service.py" line="249" />
        <source>Not enough rights to delete or update shared project ({})</source>
        <translation>No tienes suficientes permisos para eliminar o actualizar un proyecto compartido ({})</translation>
    </message>
</context>
<context>
    <name>ProjectView</name>
    <message>
        <location filename="../functional/view/project_view.py" line="59" />
        <source>See projects</source>
        <translation>Ver proyectos</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="61" />
        <source>See processings</source>
        <translation>Ver procesamientos</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="63" />
        <source>Filter projects by name</source>
        <translation>Filtrar proyectos por nombre</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="64" />
        <source>Create project</source>
        <translation>Crear proyecto</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="66" />
        <source>A-Z</source>
        <translation>A-Z</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="66" />
        <source>Z-A</source>
        <translation>Z-A</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="66" />
        <source>Newest first</source>
        <translation>Más reciente primero</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="66" />
        <source>Oldest first</source>
        <translation>Más antiguo primero</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="66" />
        <source>Updated recently</source>
        <translation>Actualizado recientemente</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="66" />
        <source>Updated long ago</source>
        <translation>Actualizado hace mucho</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="164" />
        <source>Project</source>
        <translation>Proyecto</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="170" />
        <source>Processing</source>
        <translation>Procesamiento</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="145" />
        <source>No project that meets specified criteria was found</source>
        <translation>No se encontró ningún proyecto que cumpla con los criterios especificados</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="118" />
        <source>Succeeded: {ok} · Failed: {failed} · Planned: {templates}</source>
        <translation>Correctos: {ok} · Fallidos: {failed} · Planificados: {templates}</translation>
    </message>
</context>
<context>
    <name>ProviderDialog</name>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="35" />
        <source>Provider</source>
        <translation>Proveedor</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="53" />
        <source>Type</source>
        <translation>Tipo</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="66" />
        <source>Tile coordinate scheme. XYZ is the most popular format, use it if you are not sure</source>
        <translation>Esquema de coordenadas de teselas. XYZ es el formato más popular, úsalo si no estás seguro</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="85" />
        <source>Maxar WMTS</source>
        <translation type="obsolete">Maxar WMTS</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="88" />
        <source>Name</source>
        <translation>Nombre</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="112" />
        <source>Login</source>
        <translation>Usuario</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="122" />
        <source>Password</source>
        <translation>Contraseña</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="129" />
        <source>CRS</source>
        <translation>CRS</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="154" />
        <source>Projection of the tile layer. The most popular is Web Mercator, use it if you are not sure</source>
        <translation>Proyección de la capa de teselas. La más popular es Web Mercator, úsala si no estás seguro</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="158" />
        <source>EPSG:3857</source>
        <translation>EPSG:3857</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="163" />
        <source>EPSG:3395</source>
        <translation>EPSG:3395</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="171" />
        <source>Warninig! Login and password, if saved, will be stored in QGIS settings without encryption!</source>
        <translation>¡Advertencia! El usuario y contraseña, si se guardan, se almacenarán en la configuración de QGIS sin encriptación.</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="174" />
        <source>Save login and password</source>
        <translation>Guardar usuario y contraseña</translation>
    </message>
</context>
<context>
    <name>ProviderService</name>
    <message>
        <location filename="../functional/service/provider_service.py" line="109" />
        <source>Providers are not initialized</source>
        <translation>Los proveedores no están inicializados</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="191" />
        <source>Choose imagery collection or image to start processing</source>
        <translation>Elige una colección de imágenes o imagen para iniciar el procesamiento</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="197" />
        <source>This provider requires image ID. Use search tab to find imagery for you requirements, and select image in the table.</source>
        <translation>Este proveedor requiere ID de imagen. Usa la pestaña de búsqueda para encontrar imágenes según tus requisitos y selecciona la imagen en la tabla.</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="316" />
        <source>You can launch multiple image processing only if it has the same provider of mosaic type</source>
        <translation>Solo puedes lanzar múltiples procesamientos de imágenes si tienen el mismo proveedor o tipo de mosaico</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="346" />
        <source>Duplication failed on copying data source</source>
        <translation>La duplicación falló al copiar la fuente de datos</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="354" />
        <source>Model '{wd}' is not enabled for your account</source>
        <translation>El modelo '{wd}' no está habilitado para tu cuenta</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="383" />
        <source>The following options no longer exist, so they have not been duplicated: {}</source>
        <translation>Las siguientes opciones ya no existen, por lo que no se han duplicado: {}</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="388" />
        <source>Duplication failed on copying model options</source>
        <translation>La duplicación falló al copiar las opciones del modelo</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="397" />
        <source>Provider '{provider}' is not enabled for your account</source>
        <translation>El proveedor '{provider}' no está habilitado para tu cuenta</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="495" />
        <source>Duplicated user provider</source>
        <translation>Proveedor de usuario duplicado</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="217" />
        <source>Selected search results must be of the same product type</source>
        <translation>Los resultados de búsqueda seleccionados deben ser del mismo tipo de producto</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="227" />
        <source>Selected search results must have the same zoom level</source>
        <translation>Los resultados de búsqueda seleccionados deben tener el mismo nivel de zoom</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="361" />
        <source>Duplication failed on copying model</source>
        <translation>La duplicación falló al copiar el modelo</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="268" />
        <source>Geometry area is {aoiArea:.2f} sq km, which is smaller than the minimum required area for {providerName} data provider ({providerMinArea} sq km)</source>
        <translation>El área de la geometría es {aoiArea:.2f} km², menor que el área mínima requerida para el proveedor de datos {providerName} ({providerMinArea} km²)</translation>
    </message>
</context>
<context>
    <name>QPlatformTheme</name>
    <message>
        <location filename="../mapflow.py" line="163" />
        <source>Cancel</source>
        <translation>Cancelar</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="164" />
        <source>&amp;Yes</source>
        <translation>&amp;Sí</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="165" />
        <source>&amp;No</source>
        <translation>&amp;No</translation>
    </message>
</context>
<context>
    <name>RenameImageDialog</name>
    <message>
        <location filename="../dialogs/image_dialog.py" line="18" />
        <source>Dialog requires current image</source>
        <translation>El diálogo requiere la imagen actual</translation>
    </message>
    <message>
        <location filename="../dialogs/image_dialog.py" line="19" />
        <source>Rename image {}</source>
        <translation>Renombrar imagen {}</translation>
    </message>
    <message>
        <location filename="../dialogs/image_dialog.py" line="34" />
        <source>Image name must not be empty!</source>
        <translation>¡El nombre de la imagen no debe estar vacío!</translation>
    </message>
</context>
<context>
    <name>ReviewDialog</name>
    <message>
        <location filename="../dialogs/review_dialog.py" line="25" />
        <source>Review {processing}</source>
        <translation>Revisar {processing}</translation>
    </message>
</context>
<context>
    <name>UpdateMosaicDialog</name>
    <message>
        <location filename="../dialogs/mosaic_dialog.py" line="49" />
        <source>UpdateMosaicDialog requires a imagery collection to update</source>
        <translation>UpdateMosaicDialog requiere una colección de imágenes para actualizar</translation>
    </message>
    <message>
        <location filename="../dialogs/mosaic_dialog.py" line="50" />
        <source>Edit imagery collection {}</source>
        <translation>Editar colección de imágenes {}</translation>
    </message>
    <message>
        <location filename="../dialogs/mosaic_dialog.py" line="62" />
        <source>Imagery collection name must not be empty!</source>
        <translation>¡El nombre de la colección de imágenes no debe estar vacío!</translation>
    </message>
</context>
<context>
    <name>UpdateProcessingDialog</name>
    <message>
        <location filename="../dialogs/processing_dialog.py" line="26" />
        <source>Processing name must not be empty!</source>
        <translation>¡El nombre del procesamiento no debe estar vacío!</translation>
    </message>
    <message>
        <location filename="../dialogs/processing_dialog.py" line="34" />
        <source>Edit processing {}</source>
        <translation>Editar procesamiento {}</translation>
    </message>
</context>
<context>
    <name>UploadRasterLayersDialog</name>
    <message>
        <location filename="../dialogs/upload_raster_layer_dialog.py" line="17" />
        <source>Choose raster layers to upload to imagery collection</source>
        <translation>Elegir capas ráster para subir a la colección de imágenes</translation>
    </message>
</context>
<context>
    <name>raterLayerSelection</name>
    <message>
        <location filename="../dialogs/static/ui/raster_layers_dialog.ui" line="14" />
        <source>Multiple selection</source>
        <translation>Selección múltiple</translation>
    </message>
</context>
<context>
    <name>reviewDialog</name>
    <message>
        <location filename="../dialogs/static/ui/review_dialog.ui" line="14" />
        <source>Dialog</source>
        <translation>Diálogo</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/review_dialog.ui" line="25" />
        <source>Map layer with review</source>
        <translation>Capa del mapa con revisión</translation>
    </message>
</context>
<context><name>ProcessingTable</name><message><source>(unnamed)</source><translation>(sin nombre)</translation></message><message><source>AOI</source><translation>AOI</translation></message><message><source>Created</source><translation>Creado</translation></message><message><source>Failed</source><translation>Fallido</translation></message><message><source>Failed ({ok}/{total})</source><translation>Fallidos ({ok}/{total})</translation></message><message><source>In progress ({ok}/{total})</source><translation>En curso ({ok}/{total})</translation></message><message><source>Inactive</source><translation>Inactivo</translation></message><message><source>No AOI</source><translation>Sin AOI</translation></message><message><source>OK ({ok}/{total})</source><translation>OK ({ok}/{total})</translation></message><message><source>OK ({total})</source><translation>OK ({total})</translation></message><message><source>Planned</source><translation>Planificado</translation></message><message><source>Searching</source><translation>Buscando</translation></message><message><source>Updated</source><translation>Actualizado</translation></message><message><source>Updated ({count})</source><translation>Actualizado ({count})</translation></message></context></TS>