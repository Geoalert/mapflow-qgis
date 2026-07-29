<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="ru_RU" sourcelanguage="en_US">
<context>
    <name>ApiErrors</name>
    <message>
        <location filename="../errors/api_errors.py" line="8" />
        <source>Upgrade your subscription to get access to Maxar imagery</source>
        <translation>Перейдите на коммерческий план, чтобы получить доступ к изображениям Maxar</translation>
    </message>
    <message>
        <location filename="../errors/api_errors.py" line="9" />
        <source>Geometry area is {aoiArea} sq km, which is smaller than the minimum required area for {providerName} data provider ({providerMinArea} sq km)</source>
        <translation>Выбрана область площадью {aoiArea} кв.км, что меньше минимально допустимой площади для провайдера {providerName} ({providerMinArea} кв.км)</translation>
    </message>
    <message>
        <location filename="../errors/api_errors.py" line="13" />
        <source>Up to {templateAreaLimit} sq km can be used for a planned processing. Try reducing your area of interest.</source>
        <translation>Для запланированной обработки можно использовать до {templateAreaLimit} км². Уменьшите область интереса.</translation>
    </message>
    <message>
        <location filename="../errors/api_errors.py" line="17" />
        <source>The processing area is too large: {area} sq.m exceeds the {aoiAreaLimit} sq.m limit. Reduce the area of interest.</source>
        <translation>Область обработки слишком большая: {area} м² превышает лимит {aoiAreaLimit} м². Уменьшите область интереса.</translation>
    </message>
    <message>
        <location filename="../errors/api_errors.py" line="23" />
        <source>You don't have enough limit to create this planned processing. Please contact your administrator to increase the limit.</source>
        <translation>У вас недостаточно лимита для создания этой запланированной обработки. Обратитесь к администратору, чтобы увеличить лимит.</translation>
    </message>
    <message>
        <location filename="../errors/api_errors.py" line="27" />
        <source>You have reached the maximum number of active planned processings. Pause or delete another one before activating this template.</source>
        <translation>Достигнуто максимальное число активных запланированных обработок. Приостановите или удалите другую, прежде чем активировать этот шаблон.</translation>
    </message>
</context>
<context>
    <name>AreaCalculatorService</name>
    <message>
        <location filename="../functional/service/area_calculator_service.py" line="66" />
        <source>Not enough rights to start processing in a shared project ({})</source>
        <translation>Недостаточно прав в проекте для запауска обработки ({})</translation>
    </message>
    <message>
        <location filename="../functional/service/area_calculator_service.py" line="43" />
        <source>Set AOI to start processing</source>
        <translation>Задайте область интереса, чтобы запустить обработку</translation>
    </message>
    <message>
        <location filename="../functional/service/area_calculator_service.py" line="68" />
        <source>AOI must contain not more than {} polygons</source>
        <translation>Область интереса не должна содержать более {} полигонов</translation>
    </message>
    <message>
        <location filename="../functional/service/area_calculator_service.py" line="108" />
        <source>Use extent of '{name}'</source>
        <translation>Использовать пространственный охват '{name}'</translation>
    </message>
    <message>
        <location filename="../functional/service/area_calculator_service.py" line="113" />
        <source>Use imagery extent</source>
        <translation>Использовать охват изображений</translation>
    </message>
    <message>
        <location filename="../functional/service/area_calculator_service.py" line="118" />
        <source>Selected AOI does not intersect the selected imagery</source>
        <translation>Выбранная область не пересекается с выбранным изображением</translation>
    </message>
    <message>
        <location filename="../functional/service/area_calculator_service.py" line="186" />
        <source>Area: {:.2f} sq.km</source>
        <translation>Площадь: {:.2f} кв.км</translation>
    </message>
    <message>
        <location filename="../functional/service/area_calculator_service.py" line="195" />
        <source>Bad AOI. AOI must be inside boundaries: 
[-180, 180] by longitude, [-90, 90] by latitude</source>
        <translation>Неверный AOI. AOI должен быть в пределах:
[-180, 180] по долготе, [-90, 90] по широте</translation>
    </message>
    <message>
        <location filename="../functional/service/area_calculator_service.py" line="200" />
        <source>Providers are not initialized</source>
        <translation>Провайдеры данных не установлены</translation>
    </message>
</context>
<context>
    <name>Config</name>
    <message>
        <location filename="../config.py" line="14" />
        <source>Product Type</source>
        <translation>Тип продукта</translation>
    </message>
    <message>
        <location filename="../config.py" line="17" />
        <source>Sensor</source>
        <translation>Сенсор</translation>
    </message>
    <message>
        <location filename="../config.py" line="18" />
        <source>Band Order</source>
        <translation>Порядок каналов</translation>
    </message>
    <message>
        <location filename="../config.py" line="100" />
        <source>Cloud %</source>
        <translation>Облачность, %</translation>
    </message>
    <message>
        <location filename="../config.py" line="20" />
        <source>Off Nadir</source>
        <translation>Угол от надира,</translation>
    </message>
    <message>
        <location filename="../config.py" line="54" />
        <source>Date &amp; Time ({TIMEZONE})</source>
        <translation type="obsolete">Дата и время ({TIMEZONE})</translation>
    </message>
    <message>
        <location filename="../config.py" line="24" />
        <source>Image ID</source>
        <translation>ID изображения</translation>
    </message>
    <message>
        <location filename="../config.py" line="56" />
        <source>local_index</source>
        <translation type="obsolete">Локальный индекс</translation>
    </message>
    <message>
        <location filename="../config.py" line="97" />
        <source>Date &amp; Time</source>
        <translation>Дата и время</translation>
    </message>
    <message>
        <location filename="../config.py" line="15" />
        <source>Provider Name</source>
        <translation>Имя провайдера</translation>
    </message>
    <message>
        <location filename="../config.py" line="22" />
        <source>Zoom level</source>
        <translation>Уровень масштабирования</translation>
    </message>
    <message>
        <location filename="../config.py" line="23" />
        <source>Spatial Resolution, m</source>
        <translation>Пространственное разрешение, м</translation>
    </message>
    <message>
        <location filename="../config.py" line="29" />
        <source>Project</source>
        <translation>Проект</translation>
    </message>
    <message>
        <location filename="../config.py" line="27" />
        <source>Succeeded</source>
        <translation type="obsolete">Завершено</translation>
    </message>
    <message>
        <location filename="../config.py" line="28" />
        <source>Failed</source>
        <translation type="obsolete">Ошибка</translation>
    </message>
    <message>
        <location filename="../config.py" line="31" />
        <source>Author</source>
        <translation>Автор</translation>
    </message>
    <message>
        <location filename="../config.py" line="32" />
        <source>Updated at</source>
        <translation>Обновлен</translation>
    </message>
    <message>
        <location filename="../config.py" line="33" />
        <source>Created at</source>
        <translation>Создан</translation>
    </message>
    <message>
        <location filename="../config.py" line="16" />
        <source>Preview</source>
        <translation>Просмотр</translation>
    </message>
    <message>
        <location filename="../config.py" line="30" />
        <source>State</source>
        <translation>Состояние</translation>
    </message>
</context>
<context>
    <name>ConfigColumns</name>
    <message>
        <location filename="../config.py" line="11" />
        <source>Product Type</source>
        <translation type="obsolete">Тип продукта</translation>
    </message>
</context>
<context>
    <name>ConfirmProcessingStart</name>
    <message>
        <location filename="../dialogs/dialogs.py" line="89" />
        <source>Confirm processing start</source>
        <translation type="obsolete">Подтвердите запуск обработки</translation>
    </message>
    <message>
        <location filename="../dialogs/dialogs.py" line="104" />
        <source>No zoom selected</source>
        <translation type="obsolete">Не выбран</translation>
    </message>
    <message>
        <location filename="../dialogs/dialogs.py" line="110" />
        <source>No options selected</source>
        <translation type="obsolete">Не выбраны</translation>
    </message>
</context>
<context>
    <name>ConfirmProcessingStartDialog</name>
    <message>
        <location filename="../dialogs/confirm_processing_start_dialog.py" line="17" />
        <source>Confirm processing start</source>
        <translation>Подтверждение запуска обработки</translation>
    </message>
    <message>
        <location filename="../dialogs/confirm_processing_start_dialog.py" line="32" />
        <source>No zoom selected</source>
        <translation>Масштабный уровень не выбран</translation>
    </message>
    <message>
        <location filename="../dialogs/confirm_processing_start_dialog.py" line="42" />
        <source>No options selected</source>
        <translation>Опции не выбраны</translation>
    </message>
</context>
<context>
    <name>CreateMosaicDialog</name>
    <message>
        <location filename="../dialogs/mosaic_dialog.py" line="37" />
        <source>Imagery collection name must not be empty!</source>
        <translation>Имя коллекции изображений должно быть заполнено!</translation>
    </message>
    <message>
        <location filename="../dialogs/mosaic_dialog.py" line="30" />
        <source>Imagery collection</source>
        <translation>Коллекции изображений</translation>
    </message>
</context>
<context>
    <name>CreateProjectDialog</name>
    <message>
        <location filename="../dialogs/project_dialog.py" line="36" />
        <source>Create project</source>
        <translation>Создать проект</translation>
    </message>
</context>
<context>
    <name>DataCatalogApi</name>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="88" />
        <source>Could not delete mosaic '{mosaic_name}'</source>
        <translation type="obsolete">Не удалось удалить мозаику '{mosaic_name}'</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="277" />
        <source>Error</source>
        <translation>Ошибка</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="191" />
        <source>Mosaic '{mosaic_name}' does not exist</source>
        <translation type="obsolete">Мозаика '{mosaic_name}' не существует</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="90" />
        <source>Error. Could not delete following mosaics:</source>
        <translation type="obsolete">Ошибка. Не удалось удалить следующие мозаики:</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="132" />
        <source>Failed to load mosaic 
please try again later or report error</source>
        <translation type="obsolete">Не удалось загрузить мозаику. 
Пожалуйста, попробуйте снова или сообщите об ошибке</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="231" />
        <source>This operation is forbidden for your account, contact us</source>
        <translation>Эта операция запрещена для вашего аккаунта, свяжитесь с нами</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="235" />
        <source>Authentication error. Please log in to your account</source>
        <translation>Ошибка аутентификации. Войдите в свою учётную запись</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="195" />
        <source>The image does not meet mosaic '{mosaic_name}' paremeters. 
Either modify your image or upload it to a different mosaic</source>
        <translation type="obsolete">Изображение не соответствует параметрам мозаики '{mosaic_name}'. 
Либо измените своё изображение, либо загрузите его в другую мозаику</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="198" />
        <source>Could not upload '{image}' to mosaic</source>
        <translation type="obsolete">Не удалось загрузить '{image}' в мозаику</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="242" />
        <source>Could not upload following images:
{images}</source>
        <translation>Не удалось загрузить следующие изображения:
{images}</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="280" />
        <source>Error. Could not delete following images:</source>
        <translation>Ошибка. Не удалось удалить следующие изображения:</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="126" />
        <source>Could not delete imagery collection '{mosaic_name}'</source>
        <translation>Не удалось удалить коллекцию изображений '{mosaic_name}'</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="128" />
        <source>Error. Could not delete following imagery collections:</source>
        <translation>Ошибка. Не удалось удалить следующие коллекции изображений:</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="170" />
        <source>Failed to load imagery collection. 
Please try again later or report error</source>
        <translation>Не удалось загрузить коллекцию изображений. 
Пожалуйста, попробуйте снова или сообщите об ошибке</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="233" />
        <source>Imagery collection '{mosaic_name}' does not exist</source>
        <translation>Коллекция изображений '{mosaic_name}' не существует</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="237" />
        <source>The image does not meet this imagery collection '{mosaic_name}' parameters. 
Either modify your image or upload it to a different collection</source>
        <translation>Изображение не соответствует параметрам коллекции '{mosaic_name}'. 
Измените своё изображение или загрузите его в другую коллекцию</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="278" />
        <source>Could not delete '{image}' from imagery collection</source>
        <translation>Не удалось удалить '{image}' из коллекции изображений</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="240" />
        <source>Could not upload '{image}' to imagery collection</source>
        <translation>Не удалось загрузить '{image}' в коллекцию изображений</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="262" />
        <source>Source imagery collection with id '{}' was not found </source>
        <translation type="obsolete">Коллекция изображений с id '{}' не найдена </translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="264" />
        <source>Source image with id '{}' was not found in any of your imagery collections</source>
        <translation type="obsolete">Изображение с id '{}' не найдено ни в одной из Ваших коллекций</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="227" />
        <source>Request timed out or was canceled. 
Try increasing QGIS global timeout setting: 
Settings -&gt; Options -&gt; Network -&gt; Timeout</source>
        <translation>Запрос истек по времени или был отменен. 
Попробуйте увеличить глобальный параметр тайм-аута QGIS: 
Настройки -&gt; Параметры -&gt; Сеть -&gt; Тайм-аут</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="364" />
        <source>Image not found or you don't have access to it</source>
        <translation>Изображение не найдено или у вас нет к нему доступа</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="366" />
        <source>This image is not available for download</source>
        <translation>Изображение недоступно для скачивания</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="368" />
        <source>Image data is not yet available. Please try again later</source>
        <translation>Данные изображения пока недоступны. Пожалуйста, повторите попытку позже</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="374" />
        <source>Download error</source>
        <translation>Ошибка скачивания</translation>
    </message>
</context>
<context>
    <name>DataCatalogService</name>
    <message>
        <location filename="../functional/service/data_catalog.py" line="125" />
        <source>Delete mosaic '{name}'?</source>
        <translation type="obsolete">Удалить мозаику '{name}'?</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="76" />
        <source>Choose image to upload</source>
        <translation>Выберите изображение для загрузки</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="204" />
        <source>Raster TIFF file must be georeferenced, have size less than {size} pixels and file size less than {memory} MB</source>
        <translation type="obsolete">Растровый TIFF файл должен иметь географическую привязку, размер растра менее {size} пикселей и менее {memory} Мб</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="300" />
        <source>&lt;center&gt;&lt;b&gt;Error uploading '{name}'&lt;/b&gt;</source>
        <translation>&lt;center&gt;&lt;b&gt;Ошибка загрузки '{name}'&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="214" />
        <source>&lt;b&gt;Not enough storage space. &lt;/b&gt;You have {free_storage} MB left, but '{name}' is {image_size} MB</source>
        <translation type="obsolete">&lt;b&gt;Недостаточно свободного места. &lt;/b&gt;Свободно: {free_storage} Мб, а размер '{name}' составляет {image_size} Мб</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="324" />
        <source>&lt;center&gt;Delete image &lt;b&gt;'{name}'&lt;/b&gt; from '{mosaic}' mosaic?</source>
        <translation type="obsolete">&lt;center&gt;Удалить изображение &lt;b&gt;'{name}'&lt;/b&gt; из мозаики '{mosaic}'?</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="327" />
        <source>&lt;center&gt;Delete following images from '{mosaic}' mosaic:&lt;br&gt;&lt;b&gt;'{names}'&lt;/b&gt;?</source>
        <translation type="obsolete">&lt;center&gt;Удалить следующие изображения из мозаики '{mosaic}':&lt;br&gt;&lt;b&gt;'{names}'&lt;/b&gt;?</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="330" />
        <source>&lt;center&gt;Delete &lt;b&gt;{len}&lt;/b&gt; images from '{mosaic}' mosaic?</source>
        <translation type="obsolete">&lt;center&gt;Удалить &lt;b&gt;{len}&lt;/b&gt; изображений из мозаики '{mosaic}'?</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="145" />
        <source>&lt;center&gt;Delete mosaic &lt;b&gt;'{name}'&lt;/b&gt;?</source>
        <translation type="obsolete">&lt;center&gt;Удалить мозаику &lt;b&gt;'{name}'&lt;/b&gt;?</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="148" />
        <source>&lt;center&gt;Delete following mosaics:&lt;br&gt;&lt;b&gt;'{names}'&lt;/b&gt;?</source>
        <translation type="obsolete">&lt;center&gt;Удалить следующие мозаики:&lt;br&gt;&lt;b&gt;'{names}'&lt;/b&gt;?</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="151" />
        <source>&lt;center&gt;Delete &lt;b&gt;{len}&lt;/b&gt; mosaics?</source>
        <translation type="obsolete">&lt;center&gt;Удалить &lt;b&gt;{len}&lt;/b&gt; мозаик?</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="191" />
        <source>Please, select existing mosaic</source>
        <translation type="obsolete">Пожалуйста, выберите существующую мозаику</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="296" />
        <source>Raster TIFF file must be georeferenced, have size less than {size} pixels and file size less than {memory}</source>
        <translation>Растровый TIFF файл должен иметь географическую привязку, размер менее {size} пикселей и менее {memory} Мб</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="305" />
        <source>&lt;b&gt;Not enough storage space. &lt;/b&gt;You have {free_storage} left, but '{name}' is {image_size}</source>
        <translation>&lt;b&gt;Недостаточно места. &lt;/b&gt;Свободно {free_storage}, но размер '{name}' составляет {image_size}</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="462" />
        <source>Please, select existing output directory in the Settings tab</source>
        <translation type="obsolete">Пожалуйста, выберите рабочую папку для сохраенения временных файлов во вкладке Настройки</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="118" />
        <source>&lt;center&gt;Creation of imagery collection '{mosaic_name}' failed&lt;br&gt;while trying to upload '{image}'</source>
        <translation>&lt;center&gt;Не удолось создать коллекцию изображений '{mosaic_name}'&lt;br&gt;при попытке загрузить '{image}'</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="199" />
        <source>&lt;center&gt;Delete imagery collection &lt;b&gt;'{name}'&lt;/b&gt;?</source>
        <translation>&lt;center&gt;Удалить коллекцию изображений &lt;br&gt;&lt;b&gt;'{name}'&lt;/b&gt;?</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="202" />
        <source>&lt;center&gt;Delete following imagery collections:&lt;br&gt;&lt;b&gt;'{names}'&lt;/b&gt;?</source>
        <translation>&lt;center&gt;Удалить следующие коллекции изображений:&lt;br&gt;&lt;b&gt;'{names}'&lt;/b&gt;?</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="205" />
        <source>&lt;center&gt;Delete &lt;b&gt;{len}&lt;/b&gt; imagery collections?</source>
        <translation>&lt;center&gt;Удалить &lt;b&gt;{len}&lt;/b&gt; коллекций изображений'?</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="245" />
        <source>Please, select existing imagery collection</source>
        <translation>Пожалуйста, выберите существующую коллекцию изображений</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="247" />
        <source>Choose images to upload</source>
        <translation>Выберите изображения для загрузки</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="400" />
        <source>&lt;center&gt;Delete image &lt;b&gt;'{name}'&lt;/b&gt; from '{mosaic}' imagery collection?</source>
        <translation>&lt;center&gt;Удалить изображение &lt;b&gt;'{name}'&lt;/b&gt; из коллекции '{mosaic}'?</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="403" />
        <source>&lt;center&gt;Delete following images from '{mosaic}' imagery collection:&lt;br&gt;&lt;b&gt;'{names}'&lt;/b&gt;?</source>
        <translation>&lt;center&gt;Удалить следующие изображения из коллекции '{mosaic}':&lt;br&gt;&lt;b&gt;'{names}'&lt;/b&gt;?</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="406" />
        <source>&lt;center&gt;Delete &lt;b&gt;{len}&lt;/b&gt; images from '{mosaic}' imagery collection?</source>
        <translation>&lt;center&gt;Удалить &lt;b&gt;{len}&lt;/b&gt; изображений из коллекции '{mosaic}'?</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="495" />
        <source>Image name should be 1-255 characters long</source>
        <translation>Название изображения должно иметь длину 1-255 символов</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="667" />
        <source>Source imagery collection with id '{}' was not found </source>
        <translation>Коллекция изображений с id '{}' не найдена </translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="669" />
        <source>Source image with id '{}' was not found in any of your imagery collections</source>
        <translation>Изображение с id '{}' не найдено ни в одной из Ваших коллекций</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="515" />
        <source>Download URL not available</source>
        <translation>Ссылка для скачивания недоступна</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="517" />
        <source>Save image as</source>
        <translation>Сохранить изображение как</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="535" />
        <source>Failed to download image: {}</source>
        <translation>Не удалось загрузить изображение: {}</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="542" />
        <source>Image saved to {}</source>
        <translation>Изображение сохранено в {}</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="544" />
        <source>Failed to save file: {}</source>
        <translation>Не удалось сохранить файл: {}</translation>
    </message>
</context>
<context>
    <name>DataCatalogView</name>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="24" />
        <source>Upload from file</source>
        <translation>Из файла</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="25" />
        <source>Choose raster layer</source>
        <translation>Из растрового слоя</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="45" />
        <source>Add images</source>
        <translation>Загрузить изображения</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="46" />
        <source>Show images</source>
        <translation>Показать изображения</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="49" />
        <source>Preview</source>
        <translation>Просмотр</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="48" />
        <source>Edit</source>
        <translation>Редактировать</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="50" />
        <source>Info</source>
        <translation>Информация</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="105" />
        <source>Mosaics</source>
        <translation type="obsolete">Мозаики</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="469" />
        <source>Double-click to show images</source>
        <translation>Нажмите дважды для просмотра изображений</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="151" />
        <source>Mosaic: {name} 
Number of images: {count} 
</source>
        <translation type="obsolete">Мозаика: {name} 
Количество изображений: {count} 
</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="112" />
        <source>Size: {mosaic_size} MB 
Pixel size: {pixel_size} m 
</source>
        <translation type="obsolete">Размер файла: {mosaic_size} Мб 
Размер пикселя: {pixel_size} м 
</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="197" />
        <source>Created: {date} at {time} 
Tags: {tags}</source>
        <translation>Создана: {date} в {time} 
Тэги: {tags}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="123" />
        <source>&lt;b&gt;Name&lt;/b&gt;: {filename}                              &lt;br&gt;&lt;b&gt;Uploaded&lt;/b&gt;&lt;/br&gt;: {date} at {time}                              &lt;br&gt;&lt;b&gt;Size&lt;/b&gt;&lt;/br&gt;: {file_size} MB                              &lt;br&gt;&lt;b&gt;CRS&lt;/b&gt;&lt;/br&gt;: {crs}                              &lt;br&gt;&lt;b&gt;Number of bands&lt;/br&gt;&lt;/b&gt;: {bands}                              &lt;br&gt;&lt;b&gt;Width&lt;/br&gt;&lt;/b&gt;: {width} pixels                              &lt;br&gt;&lt;b&gt;Height&lt;/br&gt;&lt;/b&gt;: {height} pixels                              &lt;br&gt;&lt;b&gt;Pixel size&lt;/br&gt;&lt;/b&gt;: {pixel_size} m</source>
        <translation type="obsolete">&lt;b&gt;Имя файла&lt;/b&gt;: {filename}                              &lt;br&gt;&lt;b&gt;Загружено&lt;/b&gt;&lt;/br&gt;: {date} в {time}                              &lt;br&gt;&lt;b&gt;Размер файла&lt;/b&gt;&lt;/br&gt;: {file_size} Мб                              &lt;br&gt;&lt;b&gt;Система координат&lt;/b&gt;&lt;/br&gt;: {crs}                              &lt;br&gt;&lt;b&gt;Количество каналов&lt;/br&gt;&lt;/b&gt;: {bands}                              &lt;br&gt;&lt;b&gt;Ширина&lt;/br&gt;&lt;/b&gt;: {width} пикселей                              &lt;br&gt;&lt;b&gt;Высота&lt;/br&gt;&lt;/b&gt;: {height} пикселей                              &lt;br&gt;&lt;b&gt;Размер пикселя&lt;/br&gt;&lt;/b&gt;: {pixel_size} м</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="293" />
        <source>Images</source>
        <translation>Изображения</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="196" />
        <source>Your data: {taken} MB. Free space: {free} MB</source>
        <translation type="obsolete">Занято: {taken} Мб. Свободно: {free} Мб</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="264" />
        <source>Selected mosaic: &lt;b&gt;{mosaic_name}</source>
        <translation type="obsolete">Выбранная мозаика: &lt;b&gt;{mosaic_name}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="279" />
        <source>No mosaic selected</source>
        <translation type="obsolete">Мозаика не выбрана</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="235" />
        <source>uploaded: {date} at {time} 
file size: {size} MB 
pixel size: {pixel_size} m 
bands: {count}</source>
        <translation type="obsolete">загружено: {date} в {time} 
размер файла: {size} Мб 
размер пиксела: {pixel_size} м 
каналы: {count}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="441" />
        <source>Selected image: &lt;b&gt;{image_name}</source>
        <translation>Выбранное изображение: &lt;b&gt;{image_name}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="456" />
        <source>No image selected</source>
        <translation>Изображение не выбрано</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="466" />
        <source>'Cmd' + click to deselect</source>
        <translation>Нажмите на ячейку, зажав 'Cmd', чтобы снять выделение</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="466" />
        <source>'Ctrl' + click to deselect</source>
        <translation>Нажмите на ячейку, зажав 'Ctrl', чтобы снять выделение</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="335" />
        <source>Image preview</source>
        <translation type="obsolete">Предпросмотр изображения</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="483" />
        <source>Delete image</source>
        <translation>Удалить изображение</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="484" />
        <source>Add image</source>
        <translation>Загрузить изображение</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="352" />
        <source>Mosaic data</source>
        <translation type="obsolete">Информация о мозаике</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="353" />
        <source>Delete mosaic</source>
        <translation type="obsolete">Удалить мозаику</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="354" />
        <source>Add mosaic</source>
        <translation type="obsolete">Создать мозаику</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="237" />
        <source>uploaded: {date} at {time}</source>
        <translation type="obsolete">Загружено: {date} в {time}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="75" />
        <source>A-Z</source>
        <translation>А-Я</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="75" />
        <source>Z-A</source>
        <translation>Я-А</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="75" />
        <source>Biggest first</source>
        <translation>Сначала большие</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="75" />
        <source>Smallest first</source>
        <translation>Сначала маленькие</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="75" />
        <source>Newest first</source>
        <translation>Сначала новые</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="75" />
        <source>Oldest first</source>
        <translation>Сначала старые</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="293" />
        <source>Size</source>
        <translation>Размер</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="130" />
        <source>Created</source>
        <translation>Создано</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="158" />
        <source>Size: {mosaic_size} 
Pixel size: {pixel_size} m 
</source>
        <translation type="obsolete">Размер файла: {mosaic_size} 
Размер пикселя: {pixel_size} м 
</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="169" />
        <source>&lt;b&gt;Name&lt;/b&gt;: {filename}                              &lt;br&gt;&lt;b&gt;Uploaded&lt;/b&gt;&lt;/br&gt;: {date} at {time}                              &lt;br&gt;&lt;b&gt;Size&lt;/b&gt;&lt;/br&gt;: {file_size}                              &lt;br&gt;&lt;b&gt;CRS&lt;/b&gt;&lt;/br&gt;: {crs}                              &lt;br&gt;&lt;b&gt;Number of bands&lt;/br&gt;&lt;/b&gt;: {bands}                              &lt;br&gt;&lt;b&gt;Width&lt;/br&gt;&lt;/b&gt;: {width} pixels                              &lt;br&gt;&lt;b&gt;Height&lt;/br&gt;&lt;/b&gt;: {height} pixels                              &lt;br&gt;&lt;b&gt;Pixel size&lt;/br&gt;&lt;/b&gt;: {pixel_size} m</source>
        <translation type="obsolete">&lt;b&gt;Имя файла&lt;/b&gt;: {filename}                              &lt;br&gt;&lt;b&gt;Загружено&lt;/b&gt;&lt;/br&gt;: {date} в {time}                              &lt;br&gt;&lt;b&gt;Размер файла&lt;/b&gt;&lt;/br&gt;: {file_size}                              &lt;br&gt;&lt;b&gt;Система координат&lt;/b&gt;&lt;/br&gt;: {crs}                              &lt;br&gt;&lt;b&gt;Количество каналов&lt;/br&gt;&lt;/b&gt;: {bands}                              &lt;br&gt;&lt;b&gt;Ширина&lt;/br&gt;&lt;/b&gt;: {width} пикселей                              &lt;br&gt;&lt;b&gt;Высота&lt;/br&gt;&lt;/b&gt;: {height} пикселей                              &lt;br&gt;&lt;b&gt;Размер пикселя&lt;/br&gt;&lt;/b&gt;: {pixel_size} м</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="293" />
        <source>Uploaded</source>
        <translation>Обновлено</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="376" />
        <source>Your data: {taken}. Free space: {free}</source>
        <translation>Занято: {taken}. Свободно: {free}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="289" />
        <source>uploaded: {date} at {time} 
file size: {size} 
pixel size: {pixel_size} m 
bands: {count}</source>
        <translation type="obsolete">загружено: {date} в {time} 
размер файла: {size} 
размер пикселя: {pixel_size} м 
каналы: {count}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="96" />
        <source>More about My imagery</source>
        <translation>Подробнее про Мои изображения</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="519" />
        <source>Filter imagery collections by name or id</source>
        <translation>Отфильтровать коллекции изображений по имени или id</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="130" />
        <source>Imagery collections</source>
        <translation>Коллекции изображений</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="178" />
        <source>Number of images: {count} 
</source>
        <translation>Количество изображений: {count} 
</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="188" />
        <source>Size: {mosaic_size} 
Pixel size: {pixel_size} 
CRS: {crs} 
Number of bands: {count} 
</source>
        <translation>Размер: {mosaic_size} 
Размер пикселя: {pixel_size} 
Система координат: {crs} 
Количество каналов: {count} 
</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="249" />
        <source>&lt;b&gt;Name&lt;/b&gt;: {filename}                              &lt;br&gt;&lt;b&gt;Uploaded&lt;/b&gt;&lt;/br&gt;: {date} at {time}                              &lt;br&gt;&lt;b&gt;Size&lt;/b&gt;&lt;/br&gt;: {file_size}                              &lt;br&gt;&lt;b&gt;CRS&lt;/b&gt;&lt;/br&gt;: {crs}                              &lt;br&gt;&lt;b&gt;Number of bands&lt;/br&gt;&lt;/b&gt;: {bands}                              &lt;br&gt;&lt;b&gt;Width&lt;/br&gt;&lt;/b&gt;: {width} pixels                              &lt;br&gt;&lt;b&gt;Height&lt;/br&gt;&lt;/b&gt;: {height} pixels                              &lt;br&gt;&lt;b&gt;Pixel size&lt;/br&gt;&lt;/b&gt;: {pixel_size}</source>
        <translation>&lt;b&gt;Имя файла&lt;/b&gt;: {filename}                              &lt;br&gt;&lt;b&gt;Загружено&lt;/b&gt;&lt;/br&gt;: {date} в {time}                              &lt;br&gt;&lt;b&gt;Размер файла&lt;/b&gt;&lt;/br&gt;: {file_size}                              &lt;br&gt;&lt;b&gt;Система координат&lt;/b&gt;&lt;/br&gt;: {crs}                              &lt;br&gt;&lt;b&gt;Количество каналов&lt;/br&gt;&lt;/b&gt;: {bands}                              &lt;br&gt;&lt;b&gt;Ширина&lt;/br&gt;&lt;/b&gt;: {width} пикселей                              &lt;br&gt;&lt;b&gt;Высота&lt;/br&gt;&lt;/b&gt;: {height} пикселей                              &lt;br&gt;&lt;b&gt;Размер пикселя&lt;/br&gt;&lt;/b&gt;: {pixel_size}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="392" />
        <source>Selected imagery collection: &lt;b&gt;{mosaic_name}</source>
        <translation>Выбранная коллекция изображений: &lt;b&gt;{mosaic_name}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="406" />
        <source>No imagery collection selected</source>
        <translation>Коллекция изображений не выбрана</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="428" />
        <source>Uploaded: {date} at {time} 
File size: {size} 
Pixel size: {pixel_size} 
CRS: {crs} 
Bands: {count}</source>
        <translation>Загружено: {date} в {time} 
Размер файла: {size} 
Размер пикселя: {pixel_size} 
Система координат: {crs} 
Каналы: {count}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="497" />
        <source>Filter images by name or id</source>
        <translation>Отфильтровать изображения по имени или id</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="504" />
        <source>Delete collection</source>
        <translation>Удалить коллекцию</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="505" />
        <source>Add collection</source>
        <translation>Создать коллекцию</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="51" />
        <source>Rename</source>
        <translation>Переименовать</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="349" />
        <source>No imagery collection with id '{mosaic_id}' was found</source>
        <translation>Коллекция изображений с id '{mosaic_id}' не найдена</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="362" />
        <source>No image with id '{image_id}' was found</source>
        <translation>Изобрадение с id '{image_id}' не найденo</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="581" />
        <source>&lt;b&gt;URL:&lt;/b&gt; {url},&lt;br&gt;&lt;b&gt;Source type:&lt;/b&gt; {type},&lt;br&gt;&lt;b&gt;CRS:&lt;/b&gt; {crs}</source>
        <translation type="obsolete">&lt;b&gt;URL:&lt;/b&gt; {url},&lt;br&gt;&lt;b&gt;Тип:&lt;/b&gt; {type},&lt;br&gt;&lt;b&gt;Система координат:&lt;/b&gt; {crs}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="587" />
        <source>, &lt;br&gt;&lt;b&gt;Zoom:&lt;/b&gt; {zoom}</source>
        <translation type="obsolete">, &lt;br&gt;&lt;b&gt;Уровень масштабирования:&lt;/b&gt; {zoom}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="589" />
        <source>, &lt;br&gt;&lt;b&gt;Raster login:&lt;/b&gt; {login}, &lt;br&gt;&lt;b&gt;Raster password:&lt;/b&gt; {password}</source>
        <translation type="obsolete">, &lt;br&gt;&lt;b&gt;Логин:&lt;/b&gt; {login}, &lt;br&gt;&lt;b&gt;Пароль:&lt;/b&gt; {password}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="451" />
        <source>Download</source>
        <translation>Скачать</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="449" />
        <source>Image is not available for download</source>
        <translation>Изображение недоступно для скачивания</translation>
    </message>
</context>
<context>
    <name>DataErrors</name>
    <message>
        <location filename="../errors/data_errors.py" line="8" />
        <source>File {filename} cannot be processed. Parameters {bad_parameters} are incompatible with our catalog. See the documentation for more info.</source>
        <translation>Файл {filename} не может быть обработан. Параметры {bad_parameters} не совместимы с нашим каталогом данных. См. документацию для подробной информации.</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="11" />
        <source>Your file has size {memory_requested} bytes, but you have only {available_memory} left. Upgrade your subscription or remove older imagery from your catalog</source>
        <translation>Объем вашего файла {memory_requested} байтов, но у вас осталось только {available_memory} байтов. Обновите подписку или удалите старые изображения из каталога</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="14" />
        <source>Max file size allowed to upload is {max_file_size} bytes, your file is {actual_file_size} bytes instead. Compress your file or cut it into smaller parts</source>
        <translation>Максимальный размер файла, разрешенный для загрузки, составляет {max_file_size} байт, размер вашего файла составляет {actual_file_size} байт. Сожмите файл или разрежьте его на более мелкие части</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="17" />
        <source>{instance_type} with id: {uid} can't be found</source>
        <translation>{instance_type} с id {uid} не может быть найден</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="18" />
        <source>You do not have access to {instance_type} with id {uid}</source>
        <translation>У вас нет доступа к {instance_type} с id {uid}</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="19" />
        <source>File {filename} cannot be uploaded to imagery collection: {mosaic_id}. {param_name} of the file is {got_param}, it should be {expected_param} to fit the collection. Fix your file, or upload it to another imagery collection</source>
        <translation>Файл {filename} не может быть загружен в коллекцию изображений: {mosaic_id}. {param_name} файла {got_param}, однако для данной мозаики этот параметр должен быть следующим: {expected_param}. Исправьте  файл или загрузите его в другую коллекцию</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="23" />
        <source>File can't be uploaded, because its extent is out of coordinate range.Check please CRS and transform of the image, they may be invalid</source>
        <translation>Файл не может быть загружен, так как его размер выходит за пределы диапазона координат. Проверьте, пожалуйста, координатную систему изображения, она может быть недействительным</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="25" />
        <source>File cannot be opened as a GeoTIFF file. Only valid geotiff files are allowed for uploading. You can use Raster-&gt;Conversion-&gt;Translate to change your file type to GeoTIFF</source>
        <translation>Файл не может быть открыт как файл GeoTIFF. Для загрузки разрешены только действительные файлы GeoTIFF. Вы можете использовать Raster-&gt;Conversion-&gt;Translate, чтобы изменить тип файла на GeoTIFF</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="28" />
        <source>File can't be uploaded, because the geometry of the image is too big, we will not be able to process it properly.Make sure that your image has valid CRS and transform, or cut the image into parts</source>
        <translation>Файл не может быть загружен, так как геометрия изображения слишком велика, мы не сможем его правильно обработать. Убедитесь, что ваше изображение имеет действующую CRS и преобразование, или разрежьте изображение на части</translation>
    </message>
</context>
<context>
    <name>Dialog</name>
    <message>
        <location filename="../dialogs/static/ui/processing_dialog.ui" line="14" />
        <source>Dialog</source>
        <translation>Окно</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_dialog.ui" line="20" />
        <source>Name</source>
        <translation>Имя</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_dialog.ui" line="34" />
        <source>Description</source>
        <translation>Описание</translation>
    </message>
</context>
<context>
    <name>ErrorDialog</name>
    <message>
        <location filename="../dialogs/static/ui/error_message.ui" line="64" />
        <source>Error</source>
        <translation>Ошибка</translation>
    </message>
</context>
<context>
    <name>ErrorMessage</name>
    <message>
        <location filename="../errors/errors.py" line="44" />
        <source>
 Warning: some error parameters were not loaded : {}!</source>
        <translation type="obsolete">
 Внимание: часть параметров не были загружены: {}!</translation>
    </message>
    <message>
        <location filename="../errors/errors.py" line="36" />
        <source>Unknown error while fetching processing errors: {exception}
 Error code: {code}
 Contact us to resolve the issue! help@geoalert.io</source>
        <translation type="obsolete">Неизвестная ошибка при загрузке ошибок обработки: {exception}
 Код ошибки: {}
 Свяжитесь с нами, мы поможем решить проблему! help@geoalert.io</translation>
    </message>
    <message>
        <location filename="../errors/errors.py" line="48" />
        <source>Error {code}: {message}</source>
        <translation type="obsolete">Ошибка {code}: {message}</translation>
    </message>
    <message>
        <location filename="../errors/errors.py" line="50" />
        <source>Unknown error while fetching errors: {exception}
 Error code: {code}
 Contact us to resolve the issue! help@geoalert.io</source>
        <translation type="obsolete">Неизвестная ошибка при получении информации: {exception}
Код ошибки: {code}
Напишите нам чтобы мы смогли исправить это! help@geoalert.io</translation>
    </message>
</context>
<context>
    <name>ErrorMessageList</name>
    <message>
        <location filename="../errors.py" line="20" />
        <source>Key 'url' in your request must be a string, got {url_type} instead.</source>
        <translation type="obsolete">Ключ 'url' в запросе должен быть строкой, не {url_type}.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="25" />
        <source>Your URL must be a link starting with "http://" or "https://".</source>
        <translation type="obsolete">URL должен начинаться с "http://" или "https://".</translation>
    </message>
    <message>
        <location filename="../errors.py" line="27" />
        <source>Format of 'url' is invalid and cannot be parsed. Error: {parse_error_message}</source>
        <translation type="obsolete">Невалидный формат URL. Ошибка {parse_error_message}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="29" />
        <source>Zoom must be either empty, or integer, got {actual_zoom}</source>
        <translation type="obsolete">Поле „zoom“ должно быть либо пустым, либо целым числом. Получено {actual_zoom}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="31" />
        <source>Zoom must be between 0 and 22, got {actual_zoom}</source>
        <translation type="obsolete">Значение поля „zoom“ в вашем запросе должно быть в интервале от 0 до 22. Получено {actual_zoom}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="32" />
        <source>Zoom must be not lower than {min_zoom}, got {actual_zoom}</source>
        <translation type="obsolete">Значение поля „zoom“ в вашем запросе должно быть не менее {min_zoom}. Получено {actual_zoom}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="33" />
        <source>Image metadata must be a dict (json)</source>
        <translation type="obsolete">Метаданные вашего изображения должны быть типа "словарь" (json)</translation>
    </message>
    <message>
        <location filename="../errors.py" line="34" />
        <source>Image metadata must have keys: crs, transform, dtype, count</source>
        <translation type="obsolete">Метаданные вашего изображения должны содержать ключи: crs, transform, dtype, count</translation>
    </message>
    <message>
        <location filename="../errors.py" line="36" />
        <source>URL of the image at s3 storage must be a string starting with s3://, got {actual_s3_link}</source>
        <translation type="obsolete">URL изображения на хранилище S3 должен быть строкой и начинаться с S3://. Получено {actual_s3_link}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="38" />
        <source>Request must contain either 'profile' or 'url' keys</source>
        <translation type="obsolete">Запрос должен содержать либо „profile“, либо „url“</translation>
    </message>
    <message>
        <location filename="../errors.py" line="39" />
        <source>Failed to read file from {s3_link}.</source>
        <translation type="obsolete">Ошибка чтения файла из {s3_link}.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="40" />
        <source>Image data type (Dtype) must be one of {required_dtypes}, got {request_dtype}</source>
        <translation type="obsolete">Тип данных изображения (Dtype) должен быть одним из {required_dtypes}. Получено {request_dtype}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="42" />
        <source>Number of channels in image must be one of {required_nchannels}. Got {real_nchannels}</source>
        <translation type="obsolete">Изображение имеет {real_nchannels} каналов, требуемое количество каналов {required_nchannels}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="44" />
        <source>Spatial resolution of you image is too high: pixel size is {actual_res}, minimum allowed pixel size is {min_res}</source>
        <translation type="obsolete">Пространственное разрешение вашего изображения слишком высокое: размер пикселя {actual_res}, минимальный допустимый размер пикселя равен {min_res}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="47" />
        <source>Spatial resolution of you image is too low: pixel size is {actual_res}, maximum allowed pixel size is {max_res}</source>
        <translation type="obsolete">Пространственное разрешение вашего изображения слишком низкое: размер пикселя равен {actual_res}, максимально допустимый размер пикселя равен {max_res}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="50" />
        <source>Error occurred during image {checked_param} check: {message}. Image metadata = {metadata}.</source>
        <translation type="obsolete">Ошибка произошла во время проверки параметра {checked_param} изображения: {message}. Метаданные изображения = {metadata}.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="52" />
        <source>Your 'url' doesn't match the format, Quadkey basemap must be a link containing "q" placeholder.</source>
        <translation type="obsolete">Ссылка на Quadkey подложку не соответствует формату. Это должна быть ссылка, содержащая поле «q».</translation>
    </message>
    <message>
        <location filename="../errors.py" line="55" />
        <source>Input string {input_string} is of unknown format. It must represent Sentinel-2 granule ID.</source>
        <translation type="obsolete">Строка {input_string} неизвестного формата. Она должна представлять собой ID гранулы снимка Sentinel-2.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="57" />
        <source>Selected Sentinel-2 image cell is {actual_cell}, this model is for the cells: {allowed_cells}</source>
        <translation type="obsolete">Выбранная ячейка {actual_cell} не подходит для обработки, модель рассчитана на ячейки: {allowed_cells}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="59" />
        <source>Selected Sentinel-2 image month is {actual_month}, this model is for: {allowed_months}</source>
        <translation type="obsolete">Выбранный месяц {actual_month} не подходит для обработки, модель рассчитана на месяцы: {allowed_months}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="60" />
        <source>You request TMS basemap link doesn't match the format, it must be a link containing '{x}', '{y}', '{z}' placeholders, correct it and start processing again.</source>
        <translation type="obsolete">Ссылка на TMS подложку не соответствует формату. Это должна быть ссылка, содержащая поля "{x}", "{y}", "{z}".</translation>
    </message>
    <message>
        <location filename="../errors.py" line="64" />
        <source>Requirements must be dict, got {requirements_type}.</source>
        <translation type="obsolete">Секция «requirements» в запросе должна быть словарем (dict), а не {requirements_type}.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="65" />
        <source>Request must be dict, got {request_type}.</source>
        <translation type="obsolete">Секция «request» в запросе должна быть словарем (dict), а не {request_type}.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="66" />
        <source>Request must contain "source_type" key</source>
        <translation type="obsolete">Запрос должен содержать тип источника спутниковых снимков (ключ «source_type»)</translation>
    </message>
    <message>
        <location filename="../errors.py" line="67" />
        <source>Source type {source_type} is not allowed. Use one of: {allowed_sources}</source>
        <translation type="obsolete">Источник данных {source_type}, не поддерживется платформой. Ипользуйте один из разрешенных: {allowed_sources}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="69" />
        <source>"Required" section of the requirements must contain dict, not {required_section_type}</source>
        <translation type="obsolete">Секция «Required» в требованиях к данным должна быть словарем (dict), а не {required_section_type}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="71" />
        <source>"Recommended" section of the requirements must contain dict, not {recommended_section_type}</source>
        <translation type="obsolete">Секция «recommended» в требованиях к данным должна быть словарем (dict), а не {recommended_section_type}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="72" />
        <source>You XYZ basemap link doesn't match the format, it must be a link containing '{x}', '{y}', '{z}' placeholders.</source>
        <translation type="obsolete">Ссылка на XYZ подложку не соответствует формату. Это должна быть ссылка, содержащая поля "{x}", "{y}", "{z}".</translation>
    </message>
    <message>
        <location filename="../errors.py" line="78" />
        <source>Internal error in process of data source validation. We are working on the fix, our support will contact you.</source>
        <translation type="obsolete">Произошла ошибка в процессе проверки источника данных. Мы работаем над исправлением и свяжемся с вами.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="99" />
        <source>Internal error in process of loading data. We are working on the fix, our support will contact you.</source>
        <translation type="obsolete">Произошла ошибка в процессе загрузки данных. Мы работаем над исправлением и свяжемся с вами.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="82" />
        <source>Wrong source type {real_source_type}. Specify one of the allowed types {allowed_source_types}.</source>
        <translation type="obsolete">Неправильный тип источника данных {real_source_type}. Используйте один из допустимых {allowed_source_types}.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="84" />
        <source>Your data loading task requires {estimated_size} MB of memory, which exceeded allowed memory limit {allowed_size}</source>
        <translation type="obsolete">Ваш запрос на загрузку данных требует {estimated_size} MB, что превышает лимит в {allowed_size}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="86" />
        <source>Dataloader argument {argument_name} has type {argument_type}, excpected to be {expected_type}</source>
        <translation type="obsolete">Функция загрузки данных {argument_name} имеет тип {argument_type}, допустимый тип {expected_type}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="88" />
        <source>Loaded tile has {real_nchannels} channels, required number is {expected_nchannels}</source>
        <translation type="obsolete">Загруженное изображение имеет {real_nchannels} каналов, требуемое количество каналов {expected_nchannels}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="90" />
        <source>Loaded tile has size {real_size}, expected tile size is {expected_size}</source>
        <translation type="obsolete">Загруженное изображение имеет размер {real_size}, допустимый размер {expected_size}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="92" />
        <source>Tile at location {tile_location} cannot be loaded, server response is {status}</source>
        <translation type="obsolete">Изображение по адресу {tile_location} не может быть загружено, ответ сервера {status}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="94" />
        <source>Response content at {tile_location} cannot be decoded as an image</source>
        <translation type="obsolete">Ответ сервера {tile_location} не представляет собой изображение</translation>
    </message>
    <message>
        <location filename="../errors.py" line="101" />
        <source>Internal error in process of data preparation. We are working on the fix, our support will contact you.</source>
        <translation type="obsolete">Произошла ошибка в процессе предобработки данных. Мы работаем над исправлением и свяжемся с вами.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="103" />
        <source>Internal error in process of data processing. We are working on the fix, our support will contact you.</source>
        <translation type="obsolete">Произошла ошибка в процессе обработки данных. Мы работаем над исправлением и свяжемся с вами.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="105" />
        <source>Internal error in process of saving the results. We are working on the fix, our support will contact you.</source>
        <translation type="obsolete">Произошла ошибка в процессе сохранения результатов обработки. Мы работаем над исправлением и свяжемся с вами.</translation>
    </message>
    <message>
        <location filename="../errors/error_message_list.py" line="26" />
        <source>Unknown error. Contact us to resolve the issue! help@geoalert.io</source>
        <translation>Неизвестная ошибка. Свяжитесь с нами, чтобы решить проблему! help@geoalert.io</translation>
    </message>
    <message>
        <location filename="../errors.py" line="17" />
        <source>Image profile (metadata) must have keys {required_keys}, got profile {profile}</source>
        <translation type="obsolete">Метаданные изображения должны содержать следующие теги: {required_keys}, метаданные загруженного изображения: {profile}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="14" />
        <source>Task for source-validation must contain area of interest (`geometry` section)</source>
        <translation type="obsolete">Задача на проверку источника данных должна содержать область интереса (ключ `geometry`)</translation>
    </message>
    <message>
        <location filename="../errors.py" line="16" />
        <source>We could not open and read the image you have uploaded</source>
        <translation type="obsolete">Мы не смогли открыть и прочитать загруженное изображение</translation>
    </message>
    <message>
        <location filename="../errors.py" line="19" />
        <source>AOI does not intersect the selected Sentinel-2 granule {actual_cell}</source>
        <translation type="obsolete">Области интереса не пересекает выбранное изображение Sentinel-2 (код ячейки {actual_cell} )</translation>
    </message>
    <message>
        <location filename="../errors.py" line="22" />
        <source>The specified basemap {url} is forbidden for processing because it contains a map, not satellite image. Our models are suited for satellite imagery.</source>
        <translation type="obsolete">Указанная подложка {url} запрещена к обработке, так как содержит карту, а не спутниковый снимок. Наши модели предназначены для обработки спутниковых снимков.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="61" />
        <source>You request TMS basemap link doesn't match the format, it must be a link containing "x", "y", "z" placeholders, correct it and start processing again.</source>
        <translation type="obsolete">Ссылка на TMS подложку не соответствует формату. Это должна быть ссылка, содержащая поля "x", "y", "z".</translation>
    </message>
    <message>
        <location filename="../errors.py" line="73" />
        <source>You XYZ basemap link doesn't match the format, it must be a link containing "x", "y", "z"  placeholders.</source>
        <translation type="obsolete">Ссылка на XYZ подложку не соответствует формату. Это должна быть ссылка, содержащая поля "x", "y", "z".</translation>
    </message>
</context>
<context>
    <name>ErrorMessageWidget</name>
    <message>
        <location filename="../dialogs/error_message_widget.py" line="22" />
        <source>"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Let us know&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Свяжитесь с нами&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
</context>
<context>
    <name>Header</name>
    <message>
        <location filename="../functional/helpers.py" line="158" />
        <source> | Project: </source>
        <translation> | Проект: </translation>
    </message>
    <message>
        <location filename="../functional/helpers.py" line="161" />
        <source>owner: </source>
        <translation>владелец: </translation>
    </message>
</context>
<context>
    <name>LoginDialog</name>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="32" />
        <source>Mapflow - Log In</source>
        <translation>Mapflow - Авторизация</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="131" />
        <source>Cancel</source>
        <translation>Отмена</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="138" />
        <source>Log in</source>
        <translation>Вход</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="68" />
        <source>Token</source>
        <translation>Токен</translation>
    </message>
    <message>
        <location filename="../static/ui/login_dialog.ui" line="59" />
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href="https://docs.mapflow.ai/userguides/mapflow_auth.html"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Need an account?&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;a href="https://mapflow.ai/terms-of-use-en.pdf"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Terms of use&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation type="obsolete">&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href="https://ru.docs.mapflow.ai/userguides/mapflow_auth.html"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Зарегистрироваться&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;a href="https://mapflow.ai/terms-of-use-ru.pdf"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Условия использования&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="75" />
        <source>This plugin is an interface to to the Mapflow.ai satellite image processing platform. You need to register an account to use it. </source>
        <translation>Этот плагин - интерфейс для работы с Mapflow.ai - платформой обработки спутниковых снимков. Чтобы его использовать, нужно зарегистрировать аккаунт. </translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="90" />
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href="https://app.mapflow.ai/account/api"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Get token&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;a href="https://mapflow.ai/terms-of-use-en.pdf"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Terms of use&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;Register at &lt;a href="https://mapflow.ai"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;mapflow.ai&lt;/span&gt;&lt;/a&gt; to use the plugin&lt;/p&gt;&lt;p&gt;&lt;br/&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href="https://app.mapflow.ai/account/api"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Получить токен&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;a href="https://mapflow.ai/terms-of-use-ru.pdf"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Условия использования&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;Зарегистрируйтесь на &lt;a href="https://mapflow.ai"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;mapflow.ai&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt; чтобы использовать плагин&lt;/p&gt;&lt;p&gt;&lt;br/&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="53" />
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;span style=" color:#ff0000;"&gt;Authorization is not configured! &lt;/span&gt;&lt;/p&gt;&lt;p&gt;&lt;br/&gt;Setup authorization config &lt;br/&gt;and restart QGIS before login. &lt;br/&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#oauth2_setup"&gt;&lt;span style=" text-decoration: underline; color:#094fd1;"&gt;See documentation for help &lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;span style=" color:#ff0000;"&gt;Авторизация не настроена! &lt;/span&gt;&lt;/p&gt;&lt;p&gt;&lt;br/&gt;Настройте авторизацию &lt;br/&gt;и перезапустите QGIS.чтобы войти &lt;br/&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#oauth2_setup"&gt;&lt;span style=" text-decoration: underline; color:#094fd1;"&gt;См. документацию &lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="111" />
        <source>Use Oauth2</source>
        <translation>Использовать Oauth2</translation>
    </message>
</context>
<context>
    <name>MainDialog</name>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="902" />
        <source>Processing</source>
        <translation>Обработка</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="106" />
        <source>Name:</source>
        <translation>Название:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1003" />
        <source>Mapflow model:</source>
        <translation type="obsolete">Модель Mapflow:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="139" />
        <source>Area:</source>
        <translation>Область:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1023" />
        <source>Imagery source:</source>
        <translation type="obsolete">Данные ДЗЗ:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="189" />
        <source>Use image extent</source>
        <translation type="obsolete">По изображению</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="587" />
        <source>Start processing</source>
        <translation>Начать обработку</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2965" />
        <source>Name</source>
        <translation>Название</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2984" />
        <source>Model</source>
        <translation>Модель</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2997" />
        <source>Status</source>
        <translation>Состояние</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3049" />
        <source>Created</source>
        <translation>Дата</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="870" />
        <source>Log out</source>
        <translation>Выйти</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1353" />
        <source>Delete</source>
        <translation>Удалить</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3352" />
        <source>Output directory:</source>
        <translation>Рабочая папка:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2199" />
        <source>Max zoom:</source>
        <translation type="obsolete">Макс зум:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3302" />
        <source>Preview</source>
        <translation>Просмотр</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="517" />
        <source>Use imagery provider credentials</source>
        <translation type="obsolete">Использовать реквизиты для провайдера</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="543" />
        <source>Login:</source>
        <translation type="obsolete">Логин:</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="557" />
        <source>Password:</source>
        <translation type="obsolete">Пароль:</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="573" />
        <source>Save Login/Password</source>
        <translation type="obsolete">Запомнить</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3438" />
        <source>Help</source>
        <translation>Помощь</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="260" />
        <source>wms</source>
        <translation type="obsolete">wms</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="261" />
        <source>postgresraster</source>
        <translation type="obsolete">postgresraster</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="262" />
        <source>grassraster</source>
        <translation type="obsolete">grassraster</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="185" />
        <source>Providers</source>
        <translation type="obsolete">Источники данных</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1213" />
        <source>Area, sq. km</source>
        <translation>Площадь, кв. км</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="58" />
        <source>Cached imagery will be reused if you've previously processed the exact same area with the same imagery source</source>
        <translation type="obsolete">Снимки будут переиспользованы если вы уже обрабатывали по ним точно такую же область</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="61" />
        <source>Use cache</source>
        <translation type="obsolete">Переиспользовать снимки</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="71" />
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#caching"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;How caching works&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation type="obsolete">&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href="https://ru.docs.mapflow.ai/api/qgis_mapflow#caching"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Как это работает&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1208" />
        <source>Progress %</source>
        <translation>Прогресс %</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1243" />
        <source>Image ID:</source>
        <translation type="obsolete">ID снимка:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1250" />
        <source>Select in the table below or paste here</source>
        <translation type="obsolete">Выберите в таблице ниже или вставьте сюда</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1502" />
        <source>Provider Imagery Catalog</source>
        <translation>Каталог снимков</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1291" />
        <source>Use canvas extent</source>
        <translation type="obsolete">По видимой области</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1516" />
        <source>From:</source>
        <translation>С:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1584" />
        <source>yyyy-MM-dd</source>
        <translation>yyyy-MM-dd</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1128" />
        <source>Search imagery</source>
        <translation type="obsolete">Искать снимки</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1560" />
        <source>To:</source>
        <translation>По:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1880" />
        <source>Additional filters</source>
        <translation>Дополнительные фильтры</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1920" />
        <source>Min intersection:</source>
        <translation>Минимальное пересечение:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1934" />
        <source>%</source>
        <translation>%</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1927" />
        <source>Cloud cover up to:</source>
        <translation>Облачность не более:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2615" />
        <source>Settings</source>
        <translation>Настройки</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2687" />
        <source>Add your own web imagery provider</source>
        <translation>Добавьте собственный источник снимков</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1499" />
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Here, you can search imagery for your area and timespan.&lt;/p&gt;&lt;p&gt;Additional filters are also available below.&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Здесь вы можете искать подходящие для ваших области и времени снимки.&lt;/p&gt;&lt;p&gt;Дополнительные параметры поиска находятся во вкладке ниже.&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="602" />
        <source>Any (multi-)polygon(s)</source>
        <translation type="obsolete">Любые (мульти-)полигон(ы)</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1288" />
        <source>Use your current screen area</source>
        <translation type="obsolete">Область ограниченная вашим экраном</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1513" />
        <source>Earlier images won't be shown</source>
        <translation>Более ранние снимки не будут показаны</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1567" />
        <source>Dates are inclusive</source>
        <translation>Даты включительны</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1693" />
        <source>Click and wait for a few seconds until the table below is filled out</source>
        <translation>Нажмите и подождите несколько секунд пока данные загрузятся</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1557" />
        <source>More recent images won't be shown</source>
        <translation>Более поздние снимки не будут показаны</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1877" />
        <source>Click to specify additional search criteria</source>
        <translation>Нажмите чтобы указать дополнительные условия поиска</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1956" />
        <source>Images that cover fewer % of your area won't be shown</source>
        <translation>Снимки покрывающие меньший % вашей области не будут показаны</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1716" />
        <source>Double-click on a row to preview its image</source>
        <translation>Двойной щелчок мыши загрузит предпросмотр снимка</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="917" />
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=" margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#user-interface"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;User Interface walkthrough&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#how-to-process-your-own-imagery"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;How to process your own image&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#how-to-use-other-imagery-services"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;How to use a different imagery tileset&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#how-to-connect-to-maxar-securewatch"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;How to connect to Maxar SecureWatch&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=" margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow Agro&lt;/span&gt;&lt;/h3&gt;&lt;p align="center"&gt;&lt;a href="https://agro.geoalert.io/"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;About&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#sentinel-2"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Sentinel imagery&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/userguides/iterative_mapping.html"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Iterative mapping workflow for cropland maps&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;span style=" font-weight:600;"&gt;If you have a feature request or have spotted a bug,&lt;br/&gt;create an issue on our &lt;/span&gt;&lt;a href="https://github.com/Geoalert/mapflow-qgis"&gt;&lt;span style=" font-weight:600; text-decoration: underline; color:#0000ff;"&gt;GitHub&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation type="obsolete">&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=" margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align="center"&gt;&lt;a href="https://ru.docs.mapflow.ai/api/qgis_mapflow#user-interface"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Пользовательский интерфейс&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://ru.docs.mapflow.ai/userguides/prices.html"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Тарифы&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://ru.docs.mapflow.ai/api/qgis_mapflow#id19"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Как использовать собственный снимок для обработки&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://ru.docs.mapflow.ai/api/qgis_mapflow#id17"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Как использовать снимки из других источников&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://ru.docs.mapflow.ai/api/qgis_mapflow#maxar-securewatch"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Как подключить Maxar SecureWatch&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=" margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow Agro&lt;/span&gt;&lt;/h3&gt;&lt;p align="center"&gt;&lt;a href="https://agro.geoalert.io/"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;О проекте&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://ru.docs.mapflow.ai/api/qgis_mapflow.html#sentinel-2"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Снимки Sentinel&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://ru.docs.mapflow.ai/userguides/iterative_mapping.html"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Пошаговый способ картирования полей&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;span style=" font-weight:600;"&gt;Если у вас есть предложения или замечания по работе плагина,&lt;br/&gt;мы будем рады если вы создадите задачу на нашем &lt;/span&gt;&lt;a href="https://github.com/Geoalert/mapflow-qgis"&gt;&lt;span style=" font-weight:600; text-decoration: underline; color:#0000ff;"&gt;GitHub&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="146" />
        <source>Create or load vector layer with your area of interest</source>
        <translation>Создать или загрузить векторный слой с вашей областью интереса</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="662" />
        <source>...</source>
        <translation>...</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="920" />
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=" margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#user-interface"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;User Interface walkthrough&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/userguides/prices.html#mapflow-qgis-pricing-model"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Pricing&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#how-to-process-your-own-imagery"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;How to process your own image&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#how-to-use-other-imagery-services"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;How to use a different imagery tileset&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#how-to-connect-to-maxar-securewatch"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;How to connect to Maxar SecureWatch&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=" margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow Agro&lt;/span&gt;&lt;/h3&gt;&lt;p align="center"&gt;&lt;a href="https://agro.geoalert.io/"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;About&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#sentinel-2"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Sentinel imagery&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/userguides/iterative_mapping.html"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Iterative mapping workflow for cropland maps&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;span style=" font-weight:600;"&gt;If you have a feature request or have spotted a bug,&lt;br/&gt;create an issue on our &lt;/span&gt;&lt;a href="https://github.com/Geoalert/mapflow-qgis"&gt;&lt;span style=" font-weight:600; text-decoration: underline; color:#0000ff;"&gt;GitHub&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation type="obsolete">&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=" margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align="center"&gt;&lt;a href="https://ru.docs.mapflow.ai/api/qgis_mapflow#user-interface"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Пользовательский интерфейс&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://ru.docs.mapflow.ai/userguides/prices.html#mapflow-qgis-pricing-model"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Тарифы&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://ru.docs.mapflow.ai/api/qgis_mapflow#id19"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Как использовать собственный снимок для обработки&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://ru.docs.mapflow.ai/api/qgis_mapflow#id17"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Как использовать снимки из других источников&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://ru.docs.mapflow.ai/api/qgis_mapflow#maxar-securewatch"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Как подключить Maxar SecureWatch&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=" margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow Agro&lt;/span&gt;&lt;/h3&gt;&lt;p align="center"&gt;&lt;a href="https://agro.geoalert.io/"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;О проекте&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://ru.docs.mapflow.ai/api/qgis_mapflow.html#sentinel-2"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Снимки Sentinel&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://ru.docs.mapflow.ai/userguides/iterative_mapping.html"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Пошаговый способ картирования полей&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;span style=" font-weight:600;"&gt;Если у вас есть предложения или замечания по работе плагина,&lt;br/&gt;мы будем рады если вы создадите задачу на нашем &lt;/span&gt;&lt;a href="https://github.com/Geoalert/mapflow-qgis"&gt;&lt;span style=" font-weight:600; text-decoration: underline; color:#0000ff;"&gt;GitHub&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1249" />
        <source>View results</source>
        <translation>Просмотр результатов</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="754" />
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=" margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#user-interface"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;User Interface walkthrough&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/userguides/prices.html#mapflow-qgis-pricing-model"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Pricing&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#how-to-upload-your-image"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;How to process your own image&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#how-to-use-other-imagery-services"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;How to use a different imagery tileset&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#how-to-connect-to-maxar-securewatch"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;How to connect to Maxar SecureWatch&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=" margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow Agro&lt;/span&gt;&lt;/h3&gt;&lt;p align="center"&gt;&lt;a href="https://agro.geoalert.io/"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;About&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#sentinel-2"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Sentinel imagery&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/userguides/iterative_mapping.html"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Iterative mapping workflow for cropland maps&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;span style=" font-weight:600;"&gt;If you have a feature request or have spotted a bug,&lt;br/&gt;create an issue on our &lt;/span&gt;&lt;a href="https://github.com/Geoalert/mapflow-qgis"&gt;&lt;span style=" font-weight:600; text-decoration: underline; color:#0000ff;"&gt;GitHub&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation type="obsolete">&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=" margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#user-interface"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Пользовательский интерфейс&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/userguides/prices.html#mapflow-qgis-pricing-model"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Тарифы&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#how-to-upload-your-image"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Как использовать собственный снимок для обработки&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#how-to-use-other-imagery-services"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Как использовать снимки из других источников&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#how-to-connect-to-maxar-securewatch"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Как подключить Maxar SecureWatch&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=" margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow Agro&lt;/span&gt;&lt;/h3&gt;&lt;p align="center"&gt;&lt;a href="https://agro.geoalert.io/"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;О проекте&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#sentinel-2"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Снимки Sentinel&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/userguides/iterative_mapping.html"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Пошаговый способ картирования полей&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;span style=" font-weight:600;"&gt;Если у вас есть предложения или замечания по работе плагина,&lt;br/&gt;мы будем рады если вы создадите задачу на нашем &lt;/span&gt;&lt;a href="https://github.com/Geoalert/mapflow-qgis"&gt;&lt;span style=" font-weight:600; text-decoration: underline; color:#0000ff;"&gt;GitHub&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="47" />
        <source>Processing name:</source>
        <translation type="obsolete">Название обработки:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1284" />
        <source>Rate processing</source>
        <translation type="obsolete">Оценить обработку</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="398" />
        <source>Please select processing and rating to submit</source>
        <translation>Пожалуйста, выберите обработку и оценку для отправки</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1305" />
        <source>Submit</source>
        <translation type="obsolete">Отправить</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1375" />
        <source>1</source>
        <translation type="obsolete">1</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1382" />
        <source>2</source>
        <translation type="obsolete">2</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1389" />
        <source>3</source>
        <translation type="obsolete">3</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1396" />
        <source>4</source>
        <translation type="obsolete">4</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1403" />
        <source>5</source>
        <translation type="obsolete">5</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1426" />
        <source>Type your feedback here</source>
        <translation type="obsolete">Введите свой отзыв здесь</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="189" />
        <source>Top up balance</source>
        <translation type="obsolete">Пополнить</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="403" />
        <source>AI model:</source>
        <translation>Модель:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="450" />
        <source>Price of the processing per sq.km</source>
        <translation>Цена обработки за кв.км</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="431" />
        <source>CC</source>
        <translation>СС</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="453" />
        <source>10</source>
        <translation>10</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="522" />
        <source>Ctrl+S</source>
        <translation />
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="249" />
        <source>Data source:</source>
        <translation>Данные:</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="513" />
        <source>Rate processing:</source>
        <translation>Оцените обработку:</translation>
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
        <translation>Поделитесь с нами, что вам понравилось в этой обработке, а что можно было бы улучшить</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="764" />
        <source>Submit feedback</source>
        <translation>Отправить отзыв</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1493" />
        <source>Imagery search</source>
        <translation>Поиск снимков</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1114" />
        <source>User profile</source>
        <translation type="obsolete">Профиль пользователя</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1120" />
        <source>Manage your Mapflow account</source>
        <translation type="obsolete">Упаравление вашим аккаунтом Mapflow</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="811" />
        <source>Your balance:</source>
        <translation>Ваш баланс:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="824" />
        <source> Top up balance </source>
        <translation> Пополнить баланс </translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="841" />
        <source>Open billing history</source>
        <translation>Открыть историю</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1267" />
        <source>Edit imagery providers available to the plugin</source>
        <translation type="obsolete">Настройка провайдеров данных, доступных в плагине</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1276" />
        <source>Imagery providers:</source>
        <translation type="obsolete">Провайдеры данных:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3334" />
        <source>Set up local working directory, where all the temporary files will be stored</source>
        <translation>Настройка рабочей папки на вашем компьютере, где будут храниться все временные файлы</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1451" />
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=" margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#user-interface"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;User Interface walkthrough&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#how-to-upload-your-image"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;How to process your own image&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#how-to-use-other-imagery-services"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;How to use a different imagery tileset (XYZ or TMS)&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#how-to-connect-to-maxar-securewatch"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;How to connect to Maxar SecureWatch&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=" margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow Pricing&lt;/span&gt;&lt;/h3&gt;&lt;p align="center"&gt;&lt;br/&gt;&lt;/p&gt;&lt;table border="0" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;" align="center" cellspacing="2" cellpadding="0"&gt;&lt;thead&gt;&lt;tr&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:700;"&gt;Billing plan&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:700;"&gt;$50&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:700;"&gt;$90&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:700;"&gt;$800&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/thead&gt;&lt;tr&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;Default or user custom imagery, km²&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;50&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;100&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;1000&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;tr&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;Premium satellite imagery, km²&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;10&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;20&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;200&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/table&gt;&lt;p&gt;See also – &lt;a href="https://docs.mapflow.ai/faq.html"&gt;&lt;span style=" text-decoration: underline; color:#094fd1;"&gt;*How to buy credits for using the platform? How much is it?*&lt;/span&gt;&lt;/a&gt;&lt;br/&gt;&lt;/p&gt;&lt;h3 style=" margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Join the project on Github&lt;/span&gt;&lt;/h3&gt;&lt;p&gt;&lt;span style=" font-weight:600;"&gt;If you have a feature request or spotted a bug,&lt;br/&gt;create an issue on &lt;/span&gt;&lt;a href="https://github.com/Geoalert/mapflow-qgis"&gt;&lt;span style=" font-weight:600; text-decoration: underline; color:#0000ff;"&gt;GitHub&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation type="obsolete">&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=" margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#user-interface"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Руководство по интерфейсу пользователя&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#how-to-upload-your-image"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Как обработать ваше изображение&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#how-to-use-other-imagery-services"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Как использовать сторонний тайловый сервис (XYZ или TMS)&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#how-to-connect-to-maxar-securewatch"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Как подключиться к Maxar SecureWatch&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=" margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Цены&lt;/span&gt;&lt;/h3&gt;&lt;p align="center"&gt;&lt;br/&gt;&lt;/p&gt;&lt;table border="0" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;" align="center" cellspacing="2" cellpadding="0"&gt;&lt;thead&gt;&lt;tr&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:700;"&gt;Тариф&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:700;"&gt;$50&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:700;"&gt;$90&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:700;"&gt;$800&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/thead&gt;&lt;tr&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;Базовое покрытие или ваши данные, км²&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;50&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;100&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;1000&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;tr&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt; Снимки коммерческих провайдеров, км²&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;10&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;20&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;200&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/table&gt;&lt;p&gt;См. также – &lt;a href="https://docs.mapflow.ai/faq.html"&gt;&lt;span style=" text-decoration: underline; color:#094fd1;"&gt;*Как купить кредиты? Сколько это стоит?*&lt;/span&gt;&lt;/a&gt;&lt;br/&gt;&lt;/p&gt;&lt;h3 style=" margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Присоединиться к проекту на Github&lt;/span&gt;&lt;/h3&gt;&lt;p&gt;&lt;span style=" font-weight:600;"&gt;Если у вас есть предложение или сообщение об ошибке,&lt;br/&gt;создайте issue на &lt;/span&gt;&lt;a href="https://github.com/Geoalert/mapflow-qgis"&gt;&lt;span style=" font-weight:600; text-decoration: underline; color:#0000ff;"&gt;GitHub&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1878" />
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=" margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#user-interface"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;User Interface walkthrough&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#how-to-upload-your-image"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;How to process your own image&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#how-to-use-other-imagery-services"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;How to use a different imagery tileset (XYZ or TMS)&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#how-to-connect-to-maxar-securewatch"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;How to connect to Maxar SecureWatch&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=" margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow credits&lt;/span&gt;&lt;span style=" font-size:large; font-weight:700;"&gt;&lt;br/&gt;&lt;/span&gt;&lt;/h3&gt;&lt;table border="0" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;" align="center" cellspacing="2" cellpadding="0"&gt;&lt;thead&gt;&lt;tr&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:600;"&gt;Pay as you go&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:696;"&gt;$50&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:696;"&gt;$90&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:696;"&gt;$800&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/thead&gt;&lt;tr&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;Credits for processing&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;500&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;1000&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;10000&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/table&gt;&lt;p&gt;See also – &lt;a href="https://docs.mapflow.ai/userguides/prices.html"&gt;&lt;span style=" text-decoration: underline; color:#094fd1;"&gt;*How much do the processings and data cost?*&lt;/span&gt;&lt;/a&gt;&lt;br/&gt;&lt;/p&gt;&lt;h3 style=" margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Join the project on &lt;a href="https://github.com/Geoalert/mapflow-qgis"&gt;&lt;span style=" font-weight:600; text-decoration: underline; color:#0000ff;"&gt;GitHub&lt;/span&gt;&lt;/a&gt; or &lt;a href="https://github.com/Geoalert/mapflow-qgis/issues"&gt;&lt;span style=" font-weight:600; text-decoration: underline; color:#0000ff;"&gt;report an issue&lt;/span&gt;&lt;/a&gt;&lt;/span&gt;&lt;/h3&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation type="obsolete">&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=" margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#user-interface"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Описание пользовательского интерфейса&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#how-to-upload-your-image"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Как загрузить и обработать свои данные&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#how-to-use-other-imagery-services"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Как использовать другие тайловые сервисы (XYZ или TMS)&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#how-to-connect-to-maxar-securewatch"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Как подключиться к Maxar SecureWatch&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=" margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow credits&lt;/span&gt;&lt;span style=" font-size:large; font-weight:700;"&gt;&lt;br/&gt;&lt;/span&gt;&lt;/h3&gt;&lt;table border="0" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;" align="center" cellspacing="2" cellpadding="0"&gt;&lt;thead&gt;&lt;tr&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:600;"&gt;Единовременная покупка&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:696;"&gt;$50&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:696;"&gt;$90&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:696;"&gt;$800&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/thead&gt;&lt;tr&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;Количество кредитов&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;500&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;1000&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;10000&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/table&gt;&lt;p&gt;См. также – &lt;a href="https://docs.mapflow.ai/userguides/prices.html"&gt;&lt;span style=" text-decoration: underline; color:#094fd1;"&gt;*Сколько стоят данные и их обработка?*&lt;/span&gt;&lt;/a&gt;&lt;br/&gt;&lt;/p&gt;&lt;h3 style=" margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Присоединяйтесь к проекту на  &lt;a href="https://github.com/Geoalert/mapflow-qgis"&gt;&lt;span style=" font-weight:600; text-decoration: underline; color:#0000ff;"&gt;GitHub&lt;/span&gt;&lt;/a&gt; или &lt;a href="https://github.com/Geoalert/mapflow-qgis/issues"&gt;&lt;span style=" font-weight:600; text-decoration: underline; color:#0000ff;"&gt;сообщите об ошибке&lt;/span&gt;&lt;/a&gt;&lt;/span&gt;&lt;/h3&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="727" />
        <source>Accept</source>
        <translation>Принять</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3062" />
        <source>Review</source>
        <translation>Статус отзыва</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3036" />
        <source>Cost</source>
        <translation>Стоимость</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1228" />
        <source>Review until</source>
        <translation>Отзыв до</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2642" />
        <source>Add or edit imagery providers:</source>
        <translation>Добавить или изменить провайдеров данных:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2892" />
        <source>Configure processings table:</source>
        <translation>Настроить таблицу обработок:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3075" />
        <source>ID</source>
        <translation>ID</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3023" />
        <source>Area</source>
        <translation>Площадь</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3010" />
        <source>Progress</source>
        <translation>Прогресс</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="536" />
        <source>Model options: </source>
        <translation>Опции: </translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="134" />
        <source>See details</source>
        <translation>Подробности</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="342" />
        <source>Search </source>
        <translation>Искать </translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1850" />
        <source>Clear </source>
        <translation>Очистить </translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2801" />
        <source>Use all vector layers as Areas Of Interest</source>
        <translation>Добавлять все векторные слои</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="132" />
        <source>Save results</source>
        <translation>Сохранить результаты</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2238" />
        <source>view results as a vector layer</source>
        <translation type="obsolete">просмотр результатов в виде векторного слоя</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2251" />
        <source>save local gpkg file to view results</source>
        <translation type="obsolete">сохранять локальный файл gpkg для просмотра результатов</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3359" />
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=" margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#user-interface"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;User Interface walkthrough&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#how-to-upload-your-image"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;How to process your own image&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#how-to-use-other-imagery-services"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;How to use a different imagery tileset (XYZ or TMS)&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#how-to-connect-to-maxar-securewatch"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;How to connect to Maxar SecureWatch&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=" margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow credits&lt;/span&gt;&lt;span style=" font-size:large; font-weight:700;"&gt;&lt;br/&gt;&lt;/span&gt;&lt;/h3&gt;&lt;table border="0" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;" align="center" cellspacing="2" cellpadding="0"&gt;&lt;thead&gt;&lt;tr&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:600;"&gt;Pay as you go&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:696;"&gt;$50&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:696;"&gt;$90&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:696;"&gt;$800&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/thead&gt;&lt;tr&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;Credits for processing&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;500&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;1000&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;10000&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/table&gt;&lt;p&gt;See also – &lt;a href="https://docs.mapflow.ai/userguides/prices.html"&gt;&lt;span style=" text-decoration: underline; color:#094fd1;"&gt;How much do the processings and data cost?&lt;/span&gt;&lt;/a&gt;&lt;br/&gt;&lt;/p&gt;&lt;h3 style=" margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Join the project on &lt;a href="https://github.com/Geoalert/mapflow-qgis"&gt;&lt;span style=" font-weight:600; text-decoration: underline; color:#0000ff;"&gt;GitHub&lt;/span&gt;&lt;/a&gt; or &lt;a href="https://github.com/Geoalert/mapflow-qgis/issues"&gt;&lt;span style=" font-weight:600; text-decoration: underline; color:#0000ff;"&gt;report an issue&lt;/span&gt;&lt;/a&gt;&lt;/span&gt;&lt;/h3&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation type="obsolete">&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=" margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#user-interface"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Описание пользовательского интерфейса&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#how-to-upload-your-image"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Как загрузить и обработать свои данные&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#how-to-use-other-imagery-services"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Как использовать другие тайловые сервисы (XYZ или TMS)&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#how-to-connect-to-maxar-securewatch"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Как подключиться к Maxar SecureWatch&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=" margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow credits&lt;/span&gt;&lt;span style=" font-size:large; font-weight:700;"&gt;&lt;br/&gt;&lt;/span&gt;&lt;/h3&gt;&lt;table border="0" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;" align="center" cellspacing="2" cellpadding="0"&gt;&lt;thead&gt;&lt;tr&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:600;"&gt;Единовременная покупка&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:696;"&gt;$50&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:696;"&gt;$90&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:696;"&gt;$800&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/thead&gt;&lt;tr&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;Количество кредитов&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;500&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;1000&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;10000&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/table&gt;&lt;p&gt;См. также – &lt;a href="https://docs.mapflow.ai/userguides/prices.html"&gt;&lt;span style=" text-decoration: underline; color:#094fd1;"&gt;Сколько стоят данные и их обработка?&lt;/span&gt;&lt;/a&gt;&lt;br/&gt;&lt;/p&gt;&lt;h3 style=" margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Присоединяйтесь к проекту на  &lt;a href="https://github.com/Geoalert/mapflow-qgis"&gt;&lt;span style=" font-weight:600; text-decoration: underline; color:#0000ff;"&gt;GitHub&lt;/span&gt;&lt;/a&gt; или &lt;a href="https://github.com/Geoalert/mapflow-qgis/issues"&gt;&lt;span style=" font-weight:600; text-decoration: underline; color:#0000ff;"&gt;сообщите об ошибке&lt;/span&gt;&lt;/a&gt;&lt;/span&gt;&lt;/h3&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2251" />
        <source>Select Mapflow project:</source>
        <translation type="obsolete">Выберите проект:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3474" />
        <source>see_details_action</source>
        <translation>see_details_action</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="359" />
        <source>
Price: {} credits per square km</source>
        <translation>
Цена: {} кредитов за кв.км</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="370" />
        <source>Rate processing &lt;b&gt;{name}&lt;/b&gt;:</source>
        <translation>Оценить обработку &lt;b&gt;{name}&lt;/b&gt;:</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="447" />
        <source>You can't remove or modify default project</source>
        <translation type="obsolete">Нельзя удалять или менять проект по умолчанию</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="522" />
        <source>Not enough rights to delete processing in a shared project ({})</source>
        <translation>Недостаточно прав для удаления проекта ({})</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="577" />
        <source>Zoom</source>
        <translation>Масштабный уровень</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="303" />
        <source> –</source>
        <translation />
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="308" />
        <source>14</source>
        <translation />
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="313" />
        <source>15</source>
        <translation />
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="318" />
        <source>16</source>
        <translation />
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="323" />
        <source>17</source>
        <translation />
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="328" />
        <source>18</source>
        <translation />
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="333" />
        <source>19</source>
        <translation />
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="338" />
        <source>20</source>
        <translation />
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="133" />
        <source>Download AOI</source>
        <translation>Скачать область интереса</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="141" />
        <source>Rename</source>
        <translation>Переименовать</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="503" />
        <source>Not enough rights to start processing in a shared project ({})</source>
        <translation>Недостаточно прав в проекте для запауска обработки ({})</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="516" />
        <source>Not enough rights to rate processing in a shared project ({})</source>
        <translation>Недостаточно прав в проекте для оценивания обработки ({})</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="518" />
        <source>Please select processing</source>
        <translation>Пожалуйста, выберите обработку</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="195" />
        <source>Use image / mosaic extent</source>
        <translation type="obsolete">Использовать охват
изображения / мозаики</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2091" />
        <source>My imagery</source>
        <translation>Мои изображения</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2194" />
        <source>No current selection</source>
        <translation>Нет выбранных данных</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1558" />
        <source>Mosaic info</source>
        <translation type="obsolete">Информация о мозаике</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1972" />
        <source>Add mosaic</source>
        <translation type="obsolete">Добавить мозаику</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1985" />
        <source>Delete mosaic</source>
        <translation type="obsolete">Удалить мозаику</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1379" />
        <source>Filter processings by name</source>
        <translation>Отфильтровать обработки по имени</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1264" />
        <source>Max preview zoom:</source>
        <translation type="obsolete">Макс зум просмотра:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1614" />
        <source>Mosaic</source>
        <translation>Мозаика</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1624" />
        <source>Image</source>
        <translation>Изображение</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1767" />
        <source>1/1</source>
        <translation>1/1</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2053" />
        <source>Search only through available providers</source>
        <translation>Искать только среди доступных источников</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1856" />
        <source>Mosaic data</source>
        <translation type="obsolete">Информация о мозаике</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2297" />
        <source>Sort by</source>
        <translation>Сортировать:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2261" />
        <source>Filter project by name</source>
        <translation type="obsolete">Отфильтровать проекты по имени</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2823" />
        <source>view results as a vector tiles</source>
        <translation>просматривать результат как векторные тайлы</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2836" />
        <source>save results as a local vector file</source>
        <translation>сохранять результат локально как векторные файлы</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2885" />
        <source>Configure search table:</source>
        <translation>Настроить таблицу поиска:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3151" />
        <source>Product Type</source>
        <translation>Тип продукта</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3167" />
        <source>Provider Name</source>
        <translation>Источник данных</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3183" />
        <source>Sensor</source>
        <translation>Сенсор</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3199" />
        <source>Band Order</source>
        <translation>Порядок каналов</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3215" />
        <source>Cloud %</source>
        <translation>Облачность</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3231" />
        <source>° Off Nadir</source>
        <translation>Угол от надира</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3247" />
        <source>Date and Time</source>
        <translation>Дата и время</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3263" />
        <source>Mosaic Zoom</source>
        <translation>Уровень масштабирования</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3276" />
        <source>Image Spatial Resolution</source>
        <translation>Пространственное разрешение</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3289" />
        <source>Image ID</source>
        <translation>ID изображения</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="572" />
        <source>Zoom is derived from found imagery resolution</source>
        <translation>Уровень масштабирования задан выбрраным изображением</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="587" />
        <source>Previous page</source>
        <translation>Предыдущая страница</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="588" />
        <source>Next page</source>
        <translation>Следующая страница</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="589" />
        <source>Page</source>
        <translation>Страница</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1434" />
        <source>Project:</source>
        <translation>Проект:</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="167" />
        <source>Project: &lt;b&gt;{}</source>
        <translation>Проект: &lt;b&gt;{}</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="500" />
        <source>Project</source>
        <translation type="obsolete">Проект</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="500" />
        <source>Succeeded</source>
        <translation type="obsolete">Успешно</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="500" />
        <source>Failed</source>
        <translation type="obsolete">Ошибка</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="500" />
        <source>Author</source>
        <translation type="obsolete">Автор</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="500" />
        <source>Updated</source>
        <translation type="obsolete">Обновлен</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="500" />
        <source>Updated at</source>
        <translation type="obsolete">Обновлен</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="500" />
        <source>Created at</source>
        <translation type="obsolete">Создан</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="976" />
        <source>Sort by:</source>
        <translation>Сортировать:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2008" />
        <source>Providers: </source>
        <translation>Источники данных:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2116" />
        <source>Add collection</source>
        <translation>Создать коллекцию</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2129" />
        <source>Delete collection</source>
        <translation>Удалить коллекцию</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2349" />
        <source>Imagery data</source>
        <translation>Данные</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2811" />
        <source>Confirm processing start</source>
        <translation>Подтверждать запуск обработок</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="555" />
        <source>Delete project</source>
        <translation>Удалить проект</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="556" />
        <source>Edit project</source>
        <translation>Редактировать проект</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="138" />
        <source>Restart</source>
        <translation>Перезапустить</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="139" />
        <source>Duplicate</source>
        <translation>Дублировать</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="749" />
        <source>&lt;b&gt;URL:&lt;/b&gt; {url}&lt;br&gt;&lt;b&gt;Source type:&lt;/b&gt; {type}</source>
        <translation>&lt;b&gt;URL:&lt;/b&gt; {url}&lt;br&gt;&lt;b&gt;Тип источника:&lt;/b&gt; {type}</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="753" />
        <source>&lt;br&gt;&lt;b&gt;CRS:&lt;/b&gt; {crs}</source>
        <translation>&lt;br&gt;&lt;b&gt;Система координат:&lt;/b&gt; {crs}</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="755" />
        <source>&lt;br&gt;&lt;b&gt;Zoom:&lt;/b&gt; {zoom}</source>
        <translation>&lt;br&gt;&lt;b&gt;Уровень масштабирования:&lt;/b&gt; {zoom}</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="757" />
        <source>&lt;br&gt;&lt;b&gt;Raster login:&lt;/b&gt; {login}&lt;br&gt;&lt;b&gt;Raster password:&lt;/b&gt; {password}</source>
        <translation>&lt;br&gt;&lt;b&gt;Логин:&lt;/b&gt; {login}&lt;br&gt;&lt;b&gt;Пароль:&lt;/b&gt; {password}</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1665" />
        <source>Some current filters are wider than the last search. Click for details.</source>
        <translation>Некоторые текущие фильтры шире последнего поиска. Нажмите для подробностей.</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1668" />
        <source>(!)</source>
        <translation>(!)</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1812" />
        <source>Save the current search filters to this template (replaces its stored search parameters)</source>
        <translation>Сохранить текущие фильтры поиска в этот шаблон (заменяет его сохранённые параметры поиска)</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1815" />
        <source>Update search</source>
        <translation>Обновить поиск</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1828" />
        <source>Seen</source>
        <translation>Просмотрено</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2072" />
        <source>Reset the filters to the parameters the current results were fetched with (search request or template)</source>
        <translation>Сбросить фильтры к параметрам, с которыми были получены текущие результаты (запрос поиска или шаблон)</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2075" />
        <source>Reset filters</source>
        <translation>Сбросить фильтры</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3447" />
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=" margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#user-interface"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;User Interface walkthrough&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#how-to-upload-your-image"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;How to process your own image&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#how-to-use-other-imagery-services"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;How to use a different imagery tileset (XYZ or TMS)&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=" margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow credits&lt;/span&gt;&lt;span style=" font-size:large; font-weight:700;"&gt;&lt;br/&gt;&lt;/span&gt;&lt;/h3&gt;&lt;table border="0" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;" align="center" cellspacing="2" cellpadding="0"&gt;&lt;thead&gt;&lt;tr&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:600;"&gt;Pay as you go&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:696;"&gt;$50&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:696;"&gt;$90&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:696;"&gt;$800&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/thead&gt;&lt;tr&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;Credits for processing&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;500&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;1000&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;10000&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/table&gt;&lt;p&gt;See also – &lt;a href="https://docs.mapflow.ai/userguides/prices.html"&gt;&lt;span style=" text-decoration: underline; color:#094fd1;"&gt;How much do the processings and data cost?&lt;/span&gt;&lt;/a&gt;&lt;br/&gt;&lt;/p&gt;&lt;h3 style=" margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Join the project on &lt;a href="https://github.com/Geoalert/mapflow-qgis"&gt;&lt;span style=" font-weight:600; text-decoration: underline; color:#0000ff;"&gt;GitHub&lt;/span&gt;&lt;/a&gt; or &lt;a href="https://github.com/Geoalert/mapflow-qgis/issues"&gt;&lt;span style=" font-weight:600; text-decoration: underline; color:#0000ff;"&gt;report an issue&lt;/span&gt;&lt;/a&gt;&lt;/span&gt;&lt;/h3&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation type="unfinished" />
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="63" />
        <source>Back</source>
        <translation>Назад</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="65" />
        <source>Open processings</source>
        <translation>Открыть обработки</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="67" />
        <source>Open selected template</source>
        <translation>Открыть выбранный шаблон</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="135" />
        <source>See processings</source>
        <translation>Показать обработки</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="136" />
        <source>See search results</source>
        <translation>Показать результаты поиска</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="142" />
        <source>Pause</source>
        <translation>Приостановить</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="143" />
        <source>Resume</source>
        <translation>Возобновить</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="145" />
        <source>Rename AOI</source>
        <translation>Переименовать AOI</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="146" />
        <source>Delete AOI</source>
        <translation>Удалить AOI</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="147" />
        <source>Add AOI from layer…</source>
        <translation>Добавить AOI из слоя…</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="148" />
        <source>Update selected AOI</source>
        <translation>Обновить выбранную AOI</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="149" />
        <source>Draw AOI on the map</source>
        <translation>Нарисовать AOI на карте</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="150" />
        <source>Exclude from search</source>
        <translation>Исключить из поиска</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="667" />
        <source>Off-Nadir °:</source>
        <translation>Отклонение от надира °:</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="673" />
        <source>Show only images within this off-nadir angle range</source>
        <translation>Показывать только изображения в этом диапазоне угла отклонения от надира</translation>
    </message>
</context>
<context>
    <name>Mapflow</name>
    <message>
        <location filename="../mapflow.py" line="277" />
        <source>Currently, Mapflow doesn't support uploading own Sentinel-2 imagery. To process Sentinel-2, go to the Providers tab and either search for your image in the catalog or paste its ID in the Image ID field.</source>
        <translation type="obsolete">Mapflow пока не поддерживает загрузку пользовательских снимков Sentinel-2. Чтобы обработать Sentinel-2, пожалуйста, перейдите во вкладку "Источники данных" и либо найдите ваш снимок в каталоге либо вставьте его ID в поле "ID Снимка".</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="394" />
        <source>Log in</source>
        <translation type="obsolete">Вход</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2197" />
        <source>If you already know which {provider_name} image you want to process,
simply paste its ID here. Otherwise, search suitable images in the catalog below.</source>
        <translation>Если вы уже знаете ID снимка {provider_name} который вы хотите обработать,
просто вставьте его в это поле. Иначе, используйте каталог ниже чтобы найти подходящий снимок.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="773" />
        <source>e.g. S2B_OPER_MSI_L1C_TL_VGS4_20220209T091044_A025744_T36SXA_N04_00</source>
        <translation type="obsolete">например S2B_OPER_MSI_L1C_TL_VGS4_20220209T091044_A025744_T36SXA_N04_00</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2201" />
        <source>e.g. a3b154c40cc74f3b934c0ffc9b34ecd1</source>
        <translation>например, a3b154c40cc74f3b934c0ffc9b34ecd1</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="464" />
        <source>Leave this field empty for </source>
        <translation type="obsolete">Оставьте это поле пустым для </translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="466" />
        <source> doesn't allow processing single images.</source>
        <translation type="obsolete"> не поддерживает обработку отдельных снимков.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="480" />
        <source> Imagery Catalog</source>
        <translation type="obsolete"> - Каталог снимков</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2091" />
        <source>Permanently remove {}?</source>
        <translation>Удалить {}?</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2233" />
        <source>Select output directory</source>
        <translation>Выберите папку для сохранения данных</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2256" />
        <source>Please, specify an existing output directory</source>
        <translation>Пожалуйста, выберите папку для сохранения данных</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="653" />
        <source>Select GeoTIFF</source>
        <translation type="obsolete">Выберите GeoTIFF</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1643" />
        <source>Please, select an area of interest</source>
        <translation type="obsolete">Пожалуйста, выберите слой с областью обработки</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1061" />
        <source>Your area of interest is too large.</source>
        <translation type="obsolete">Слишком большая область запроса метаданных.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1164" />
        <source>Please, check your credentials</source>
        <translation type="obsolete">Пожалуйста, проверьте реквизиты</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1318" />
        <source>We couldn't fetch Sentinel metadata</source>
        <translation type="obsolete">Мы не смогли получить метаданные Сентинел</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2869" />
        <source>No images match your criteria. Try relaxing the filters.</source>
        <translation>Нет подходящих снимков. Попробуйте изменить параметры поиска.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1285" />
        <source>More</source>
        <translation type="obsolete">Еще</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1057" />
        <source>We couldn't get metadata from Maxar</source>
        <translation type="obsolete">Мы не смогли получить метаданные от Максар</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1522" />
        <source>A Sentinel image ID should look like S2B_OPER_MSI_L1C_TL_VGS4_20220209T091044_A025744_T36SXA_N04_00 or /36/S/XA/2022/02/09/0/</source>
        <translation type="obsolete">ID снимка Sentinel должен иметь формат S2B_OPER_MSI_L1C_TL_VGS4_20220209T091044_A025744_T36SXA_N04_00 или /36/S/XA/2022/02/09/0/</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1699" />
        <source>Area: {:.2f} sq.km</source>
        <translation type="obsolete">Площадь: {:.2f} кв.км</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1899" />
        <source>Delete selected processings?</source>
        <translation type="obsolete">Удалить выбранные обработки?</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1925" />
        <source>Error deleting a processing</source>
        <translation type="obsolete">Ошибка при удалении обработки</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3002" />
        <source>Please, specify a name for your processing</source>
        <translation>Пожалуйста, укажите название обработки</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1352" />
        <source>GeoTIFF has invalid projection</source>
        <translation type="obsolete">Мы не смогли распознать проекцию снимка</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1354" />
        <source>Processing area has invalid projection</source>
        <translation type="obsolete">Мы не смогли распознать проекцию области обработки</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3009" />
        <source>Up to {} sq km can be processed at a time. Try splitting your area(s) into several processings.</source>
        <translation>За раз можно обработать не более {} кв км. Попробуйте разделить область обработки на части.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1583" />
        <source>Click on the link below to send us an email</source>
        <translation type="obsolete">Нажмите на ссылку ниже чтобы отправить нам отчет об ошибке</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1583" />
        <source>Upgrade your subscription to process Maxar imagery</source>
        <translation type="obsolete">Чтобы обрабатывать по Максар, нужно стать Премиум пользователем Mapflow</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1583" />
        <source>I'd like to upgrade my subscription to Mapflow Processing API to be able to process Maxar imagery.</source>
        <translation type="obsolete">Я хотел бы стать премиум пользователем Mapflow чтобы обрабатывать по Максар.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3005" />
        <source>Processing area layer is corrupted or has invalid projection</source>
        <translation>Выбранная область некорректна или имеет неправильную проекцию</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1755" />
        <source>Bad AOI. AOI must be inside boundaries: 
[-180, 180] by longitude, [-90, 90] by latitude</source>
        <translation type="obsolete">Неверный AOI. AOI должен быть в пределах:
[-180, 180] по долготе, [-90, 90] по широте</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1901" />
        <source>Starting the processing...</source>
        <translation type="obsolete">Создаем обработку...</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1852" />
        <source>Uploading image to Mapflow...</source>
        <translation type="obsolete">Загружаем ваш снимок на Mapflow...</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2205" />
        <source>We couldn't upload your GeoTIFF</source>
        <translation type="obsolete">Мы не смогли загрузить ваш снимок</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2003" />
        <source>Processing creation failed</source>
        <translation type="obsolete">Мы не смогли создать обработку</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2227" />
        <source>Success! We'll notify you when the processing has finished.</source>
        <translation type="obsolete">Обработка создана! Мы оповестим вас когда она завершится.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1523" />
        <source>Processing limit: {} sq.km</source>
        <translation type="obsolete">Доступный лимит: {} кв.км</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1694" />
        <source>Sorry, we couldn't load the image</source>
        <translation type="obsolete">Ошибка предпросмотра снимка</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1695" />
        <source>Error previewing Sentinel imagery</source>
        <translation type="obsolete">Ошибка предпросмотра снимка</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1880" />
        <source>Sorry, there's no preview for this image</source>
        <translation type="obsolete">Стоимость обработки недоступна</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3417" />
        <source>We couldn't load a preview for this image</source>
        <translation>Мы не смогли осуществить предпросмотр этого снимка</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1895" />
        <source>Please, select an image to preview</source>
        <translation type="obsolete">Пожалуйста, выберите снимок</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2408" />
        <source>Error loading results. Error code: </source>
        <translation type="obsolete">Ошибка загрузки результатов. Код ошибки: </translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2148" />
        <source>Error downloading results</source>
        <translation type="obsolete">Мы не смогли скачать результаты обработки</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1981" />
        <source>Error loading results</source>
        <translation type="obsolete">Мы не смогли загрузить результаты</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1907" />
        <source> failed.
</source>
        <translation type="obsolete"> завершилась с ошибкой.
</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3076" />
        <source> finished. Double-click it in the table to download the results.</source>
        <translation type="obsolete"> завершилась. Дважды кликните на нее в таблице чтобы загрузить результаты.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2019" />
        <source>Can't log in to Mapflow</source>
        <translation type="obsolete">Мы не смогли подключиться к Mapflow</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2655" />
        <source>Invalid token</source>
        <translation type="obsolete">Неверный токен</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4135" />
        <source>Proxy error. Please, check your proxy settings.</source>
        <translation>Ошибка прокси. Пожалуйста, проверьте настройки прокси в QGIS.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2115" />
        <source>Unknown error</source>
        <translation type="obsolete">Неизвестная ошибка</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4266" />
        <source>A new version of Mapflow plugin {server_version} is released 
We recommend you to upgrade to get all the latest features
Go to Plugins -&gt; Manage and Install Plugins -&gt; Upgradable</source>
        <translation>Появилась новая версия mapflow {server_version}. Реомендуем обновить версию чтобы получить доступ к новым возможностям. Выберите меню Модули -&gt; Управление модулями -&gt; Обновляемые</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="467" />
        <source>Select vector file</source>
        <translation type="obsolete">Выберите векторный файл</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="322" />
        <source>Create new AOI layer from map extent</source>
        <translation type="obsolete">Создать новый слой области интереса из видимой области карты</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="284" />
        <source>Draw AOI at the map</source>
        <translation>Нарисовать AOI на карте</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="479" />
        <source>Your file is not valid vector data source!</source>
        <translation type="obsolete">Ваш файл не подходит как источник векторных данных!</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3123" />
        <source>Please review or accept this processing until {}. Double click to add results to the map</source>
        <translation type="obsolete">Пожалуйста, оставьте отзыв или примите результаты до {}. Двойной клик для добавления результатов на карту</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="209" />
        <source>Selected Image ID: {text}</source>
        <translation type="obsolete">Выберите ID снимка: {text}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="528" />
        <source>This provider cannot be removed</source>
        <translation type="obsolete">Данный источник данных не может быть удален</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="704" />
        <source>Provider {name} does not support metadata requests</source>
        <translation type="obsolete">Источник данных {name} не поддерживает запрос метаданных</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1390" />
        <source>Provider {} requires selected Image ID</source>
        <translation type="obsolete">Провайдеру {} требуется выбранный ID снимка</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1906" />
        <source>Could not launch processing! Error: {}.</source>
        <translation type="obsolete">Не удалось запустить обработку! Ошибка: {}.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3050" />
        <source> failed with error:
</source>
        <translation type="obsolete"> завершилась с ошибкой:
</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="275" />
        <source>Error during loading the data providers: {e}</source>
        <translation>Ошибка при загрузке источников данных: {e}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="150" />
        <source>We failed to import providers {errors} from the settings. Please add them again</source>
        <translation type="obsolete">Нам не удалось импортировать провайдеров из настроек {errors}. Пожалуйста, добавьте их снова</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2123" />
        <source>Provider name must be unique. {name} already exists, select another or delete/edit existing</source>
        <translation>Название источника данных должен быть уникальным. {name} уже существует, выберите другое название или удалите/измените существующий</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1406" />
        <source>We couldn't get metadata from Maxar, error {error}</source>
        <translation type="obsolete">Мы не смогли получить метаданные от Maxar, ошибка {error}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1894" />
        <source>Processing limit exceeded. Visit "&lt;a href="https://app.mapflow.ai/account/balance"&gt;Mapflow&lt;/a&gt;" to top up your balance</source>
        <translation type="obsolete">Превышен доступный лимит обработки. Посетите "&lt;a href="https://app.mapflow.ai/account/balance"&gt;Mapflow&lt;/a&gt;" для пополнения баланса</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1525" />
        <source>.  Project name: {}</source>
        <translation type="obsolete">. Название проекта: {}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2172" />
        <source>Preview is unavailable for the provider {}</source>
        <translation type="obsolete">Просмотр недоступен для источника данных {}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4145" />
        <source>This operation is forbidden for your account, contact us</source>
        <translation>Эта операция запрещена для вашего аккаунта, свяжитесь с нами</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4103" />
        <source>Wrong token. Visit "&lt;a href="https://app.mapflow.ai/account/api"&gt;mapflow.ai&lt;/a&gt;" to get a new one</source>
        <translation>Неправильный токен. Перейдите на "&lt;a href="https://app.mapflow.ai/account/api"&gt;mapflow.ai&lt;/a&gt;" чтообы получить новый</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4256" />
        <source>You must upgrade your plugin version to continue work with Mapflow. 
The server requires version {server_version}, your plugin is {local_version}
Go to Plugins -&gt; Manage and Install Plugins -&gt; Upgradable</source>
        <translation>Обновите версию плагина чтобы продолжить работать с Mapflow. Требуется версия {server_version}, установлена версия {local_version}. Выберите меню Модули -&gt; Управление модулями -&gt; Обновляемые</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2134" />
        <source>Add new provider</source>
        <translation>Добавить новый источник данных</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2142" />
        <source>This is a default provider, it cannot be edited</source>
        <translation>Этот источник данных встроен в mapflow, его нельзя редактировать</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3057" />
        <source>{} processings failed: 
 {} 
 See tooltip over the processings table for error details</source>
        <translation type="obsolete">Завершено обработок с ошибкой: {} 
 {} 
 Наведите курсор мыши на обработку в таблице чтобы увидеть сообщение об ошибке</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3064" />
        <source>{} processings failed: 
 See tooltip over the processings table for error details</source>
        <translation type="obsolete">Завершено с ошибкой {} обработок
 Наведите курсор мыши на обработку в таблице чтобы увидеть сообщение об ошибке</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3084" />
        <source>{} processings finished: 
 {} 
 Double-click it in the table to download the results</source>
        <translation type="obsolete">Успешно завершено обработок: {}. 
 {} 
 Двойной клик по строке обработки в таблице скачает результаты</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3092" />
        <source>{} processings finished. 
 Double-click it in the table to download the results</source>
        <translation type="obsolete">Завершено успешно {} обработок.
 Наведите курсор мыши на обработку в таблице чтобы увидеть сообщение об ошибке</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1554" />
        <source>Set AOI to start processing</source>
        <translation type="obsolete">Задайте область интереса, чтобы запустить обработку</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1568" />
        <source>Project name: {}</source>
        <translation type="obsolete">Название проекта: {}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1586" />
        <source>Processing limit: {:.2f} sq.km</source>
        <translation type="obsolete">Лимит обработки: {:.2f} кв.км</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3680" />
        <source>Only finished processings can be rated</source>
        <translation>Только законченные обработки могут быть оценены</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1789" />
        <source>Please, provide feedback for rating. Thank you!</source>
        <translation type="obsolete">Пожалуйста, оставьте отзыв для оценки. Спасибо!</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3706" />
        <source>Thank you! Your rating and feedback are submitted!</source>
        <translation>Спасибо! Ваша оценка и отзыв отправлены!</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3726" />
        <source>Only correctly finished processings (status OK) can be rated</source>
        <translation>Только правильно завершенные обработки (состояние OK) могут быть оценены</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3025" />
        <source>Providers are not initialized</source>
        <translation>Провайдеры данных не установлены</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3944" />
        <source>Only the results of correctly finished processing can be loaded</source>
        <translation>Загружать можно только результаты корректно законченной обработки</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4150" />
        <source>Error</source>
        <translation>Ошибка</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3699" />
        <source>Thank you! Your rating is submitted!
We would appreciate if you add feedback as well.</source>
        <translation>Спасибо! Ваша оценка отправлена! Мы будем благодарны, если добавите комментарий к оценке.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2015" />
        <source>Log in </source>
        <translation>Вход </translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2087" />
        <source>This provider is default and cannot be removed</source>
        <translation>Этот провайдер встроен в плагин, его нельзя удалить</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="701" />
        <source>{} doesn't allow processing single images.</source>
        <translation type="obsolete">{} не позволяет обрабатывать отдельные изображения.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1579" />
        <source>AOI must contain not more than {} polygons</source>
        <translation type="obsolete">Область интереса не должна содержать более {} полигонов</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1845" />
        <source>Processing cost is not available:
{error}</source>
        <translation type="obsolete">Стоимость обработки недоступна:
{error}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1885" />
        <source>Processsing cost: {cost} credits</source>
        <translation type="obsolete">Стоимость обработки: {cost} кредитов</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1723" />
        <source>Please select image in Search table for {}</source>
        <translation type="obsolete">Пожалуйста выберете изображение в таблице поиска для {}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3058" />
        <source>Your balance: {} credits</source>
        <translation>Ваш баланс: {} кредитов</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3394" />
        <source>Provider {name} requires image id for preview!</source>
        <translation>Чтобы открыть предпросмотр провайдера {name}, задайте ID изображения!</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3429" />
        <source>This provider requires image ID!</source>
        <translation>Выберите ID изображения!</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3060" />
        <source>Remaining limit: {:.2f} sq.km</source>
        <translation>Доступная площадь: {:.2f} кв.км</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1530" />
        <source>A Maxar image ID should look like a3b154c40cc74f3b934c0ffc9b34ecd1</source>
        <translation type="obsolete">ID снимка Maxar должен выглядеть как a3b154c40cc74f3b934c0ffc9b34ecd1</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1833" />
        <source>Error! Models are not initialized.
Please, make sure you have selected a project</source>
        <translation type="obsolete">Ошибка! Модели не инициализирваны
Пожалуйста, убедитесь, что выбран проект</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1746" />
        <source>Raster image is not acceptable.  It must be a Tiff file, have size less than {size} pixels and file size less than {memory} MB</source>
        <translation type="obsolete">Недопустимое изображение. Это должен быть файл Tiff , иметь размер растра меньше чем {size} пикселей, и размер файла менее чем {memory} МБ</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3683" />
        <source>Processing must be in `Review required` status</source>
        <translation>Обработка должна быть в статусе "Ожидается отзыв"</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2570" />
        <source>Only correctly finished processings (status OK) can be reviewed</source>
        <translation type="obsolete">Только на корректно завершенные обработки (статус Ок) можно оставить отзыв</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3728" />
        <source>Please select rating to submit</source>
        <translation>Пожалуйста, выберите оценку</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2288" />
        <source>Please review this processing until {}. Double click to add results to the map</source>
        <translation type="obsolete">Пожалуйста, оставьте отзыв до {}. Двойной клик для добавления результатов на карту</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="278" />
        <source>We failed to import providers from the settings. Please add them again</source>
        <translation>Не получилось загрузить провайдеров данных из настроек. Пожалуйста, добавьте их заново</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3128" />
        <source>Double click to add results to the map.</source>
        <translation type="obsolete">Двойной клик чтобы добавить результаты на карту.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2939" />
        <source>Name: {name}
Status: {status}

Model: {model},</source>
        <translation type="obsolete">Имя: {name}
Статус: {status}

Модель: {model},</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2945" />
        <source>
Model options: {options}</source>
        <translation type="obsolete">
Опции: {options}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2950" />
        <source>

Data provider: {provider}</source>
        <translation type="obsolete">

Источник данных: {provider}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2954" />
        <source>

Data source: uploaded file</source>
        <translation type="obsolete">

Источник данных: загруженный файл</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2956" />
        <source>

Data source link {url}</source>
        <translation type="obsolete">

Источник данных: {url}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1022" />
        <source>We couldn't get metadata from the Mapflow Imagery Catalog, error {error}</source>
        <translation type="obsolete">Мы не смогли получить метаданные из каталога изображений, ошибка {error}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1404" />
        <source>Please, check your Maxar credentials</source>
        <translation type="obsolete">Пожалуйста проверьте реквизиты своего аккаунта Maxar</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2056" />
        <source>Data provider with id is unavailable on your plan. 
 Upgrade your subscription to get access to the data. 
See pricing at &lt;a href="https://mapflow.ai/pricing"&gt;mapflow.ai&lt;/a&gt;</source>
        <translation type="obsolete">Провайдер недоступен для вашего тарифного плана.
Купите подписку чтобы получить доступ к данным.
Тарифные планы на  &lt;a href="https://mapflow.ai/pricing"&gt;mapflow.ai&lt;/a&gt;</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3145" />
        <source>Preview is unavailable when metadata layer is removed</source>
        <translation>Предпросмотр недоступен когда слой с метаданными поиска удален</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2452" />
        <source>Error downloading results, 
 try again later or report error</source>
        <translation type="obsolete">Ошибка при скачивании результатов
 попробуйте позже или сообщите нам об ошибке</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3007" />
        <source>Please, select a valid area of interest</source>
        <translation>Пожалуйста, выберите допустимый слой с областью обработки</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1918" />
        <source>Raster TIFF file must be georeferenced, have size less than {size} pixels and file size less than {memory} MB</source>
        <translation type="obsolete">Растровый TIFF файл должен быть с географической привязкой, иметь размер растра менее чем {size} пикселей и размер файла менее чем {memory} МБ</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1860" />
        <source>This provider requires image ID. Use search tab to find imagery for you requirements, and select image in the table.</source>
        <translation type="obsolete">Этому провайдеру нужен ID снимка. Используйте вкладку "Поиск" чтобы найти изображения по вашим требованиям, и выберите изображение в таблице.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4016" />
        <source>We have just set the authentication config for you. 
 You may need to restart QGIS to apply it so you could log in</source>
        <translation>Авторизация настроена. Может потребоваться перезагрузить QGIS чтобы применить конфигурацию и войти в систему</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4041" />
        <source>Please restart QGIS before using OAuth2 login.</source>
        <translation>Пожалуйста перезагрузите QGIS перед использованием авторизации OAuth2.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3158" />
        <source>No projects found! Contact us to resolve the issue</source>
        <translation type="obsolete">Проектов не найдено! Свяжитесь с нами чтобы решить проблему</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="303" />
        <source>Save results</source>
        <translation type="obsolete">Сохранить результаты</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="304" />
        <source>Download AOI</source>
        <translation type="obsolete">Скачать область интереса</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="305" />
        <source>See details</source>
        <translation type="obsolete">Подробности</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="306" />
        <source>Rename</source>
        <translation type="obsolete">Переименовать</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="763" />
        <source>Do you really want to remove project {}? This action cannot be undone, all processings will be lost!</source>
        <translation type="obsolete">Вы действительно хотите удалить проект {}? Это действие нельзя отменить, все обработки будут потеряны!</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3398" />
        <source>Preview is unavailable for the provider {}. 
OSM layer will be added instead.</source>
        <translation>Предпросмотр для источника {} недоступен.
Вместо этого будет добвален слой OSM.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3324" />
        <source>&lt;b&gt;Name&lt;/b&gt;: {name}&lt;br&gt;&lt;b&gt;ID&lt;/b&gt;&lt;/br&gt;: {pid}&lt;br&gt;&lt;b&gt;Status&lt;/b&gt;&lt;/br&gt;: {status}&lt;br&gt;&lt;b&gt;Model&lt;/b&gt;&lt;/br&gt;: {model}</source>
        <translation type="obsolete">&lt;b&gt;Название&lt;/b&gt;: {name}&lt;br&gt;&lt;b&gt;ID&lt;/b&gt;&lt;/br&gt;: {pid}&lt;br&gt;&lt;b&gt;Статус&lt;/b&gt;&lt;/br&gt;: {status}&lt;br&gt;&lt;b&gt;Модель&lt;/b&gt;&lt;/br&gt;: {model}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3332" />
        <source>&lt;br&gt;&lt;b&gt;Description&lt;/b&gt;&lt;/br&gt;: {description}</source>
        <translation type="obsolete">&lt;br&gt;&lt;b&gt;Описание&lt;/b&gt;&lt;/br&gt;: {description}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3335" />
        <source>&lt;br&gt;&lt;b&gt;Model options:&lt;/b&gt;&lt;/br&gt; {options}</source>
        <translation type="obsolete">&lt;br&gt;&lt;b&gt;Опции:&lt;/b&gt;&lt;/br&gt; {options}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3340" />
        <source>&lt;br&gt;&lt;b&gt;Model options:&lt;/b&gt;&lt;/br&gt; No options selected</source>
        <translation type="obsolete">&lt;br&gt;&lt;b&gt;Опции:&lt;/b&gt;&lt;/br&gt; Не выбраны</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3343" />
        <source>&lt;br&gt;&lt;b&gt;Data provider&lt;/b&gt;&lt;/br&gt;: {provider}</source>
        <translation type="obsolete">&lt;br&gt;&lt;b&gt;Источник данных&lt;/b&gt;&lt;/br&gt;: {provider}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3347" />
        <source>&lt;br&gt;&lt;b&gt;Data source&lt;/b&gt;&lt;/br&gt;: uploaded file</source>
        <translation type="obsolete">&lt;br&gt;&lt;b&gt;Источник данных&lt;/b&gt;&lt;/br&gt;: загруженный файл</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3349" />
        <source>&lt;br&gt;&lt;b&gt;Data source link&lt;/b&gt;&lt;/br&gt; {url}</source>
        <translation type="obsolete">&lt;br&gt;&lt;b&gt;Ссылка на источник данных&lt;/b&gt;&lt;/br&gt; {url}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="744" />
        <source>Not enough rights to delete or update shared project ({})</source>
        <translation type="obsolete">Недостаточно прав для удаления или изменения проекта ({})</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1577" />
        <source>Not enough rights to start processing in a shared project ({})</source>
        <translation type="obsolete">Недостаточно прав в проекте для запауска обработки ({})</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2457" />
        <source>Preview is unavailable</source>
        <translation type="obsolete">Предпросмотр недоступен</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3321" />
        <source>Could not display preview</source>
        <translation>Неудалось осуществить предпросмотр</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3721" />
        <source>Not enough rights to rate processing in a shared project ({})</source>
        <translation>Недостаточно прав в проекте для оценивания обработки ({})</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3724" />
        <source>Please select processing</source>
        <translation>Пожалуйста, выберите обработку</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4139" />
        <source>Not enough rights for this action
in a shared project '{project_name}' ({user_role})</source>
        <translation>Недостаточно прав для этого действия
в проекте '{project_name}' ({user_role})</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1817" />
        <source>Choose mosaic or image to start processing</source>
        <translation type="obsolete">Выберите мозаику или изображение для запуска обработки</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1858" />
        <source>Selected AOI does not intersect the selected imagery</source>
        <translation type="obsolete">Выбранная область не пересекается с выбранным изображением</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1992" />
        <source>The selected data provider is unavailable on your plan. 
 Upgrade your subscription to get access to the data. 
See pricing at &lt;a href="https://mapflow.ai/pricing"&gt;mapflow.ai&lt;/a&gt;</source>
        <translation type="obsolete">Выбранный провайдер данных недоступен в Вашем тарифном плане. 
 Обновите подписку для получения доступа к данным. 
Узнать цену: &lt;a href="https://mapflow.ai/pricing"&gt;mapflow.ai&lt;/a&gt;</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2272" />
        <source>Only PNG preview type is supported</source>
        <translation type="obsolete">Поддерживается предпросмотр только в формате PNG</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="739" />
        <source>No project selected</source>
        <translation type="obsolete">Проект не выбран</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="741" />
        <source>You can't remove or modify default project</source>
        <translation type="obsolete">Нельзя удалять или менять проект по умолчанию</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2831" />
        <source>We couldn't get metadata from the Mapflow Imagery Catalog</source>
        <translation>Мы не смогли получить метаданные из каталога изображений</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2834" />
        <source>. Error {error}</source>
        <translation>. Ошибка {error}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3503" />
        <source>You can launch multiple image processing only if it has the same provider of mosaic type</source>
        <translation type="obsolete">Запуск по нескольким изображениям доступен только если у них один источник мозаичного типа</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3072" />
        <source>Selected search results must have the same zoom level</source>
        <translation type="obsolete">Выбранные результаты поиска должны иметь один уровень масштабирования</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1099" />
        <source>&lt;b&gt;Results could not be loaded &lt;/b&gt;&lt;br&gt;Please, make sure you chose the right output folder in the Settings tab                             and you have access rights to this folder</source>
        <translation type="obsolete">&lt;b&gt;Неудалось загрузить результат поиска &lt;/b&gt;&lt;br&gt;Пожалуйста, убедитесь, что во вкладке Настройки выбрана существующая рабочая папка                             и что пользователь обладает правами доступа к ней</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2885" />
        <source>&lt;b&gt;Results could not be loaded &lt;/b&gt;&lt;br&gt;Please, make sure you chose the right output folder in the Settings tab                                 and you have access rights to this folder</source>
        <translation>&lt;b&gt;Не удалось загрузить результаты поиска &lt;/b&gt;&lt;br&gt;Пожалуйста, убедитесь, что во вкладке Настройки выбрана существующая рабочая папка                                 и к ней имеются права доступа</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="725" />
        <source>Project: &lt;b&gt;{}</source>
        <translation type="obsolete">Проект: &lt;b&gt;{}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="285" />
        <source>Use imagery extent</source>
        <translation>Использовать охват изображений</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="287" />
        <source>Create AOI from map extent</source>
        <translation>Создать слой области интереса из видимой области карты</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1518" />
        <source>Choose imagery collection or image to start processing</source>
        <translation>Выберите изображение или коллекцию для запуска обработки</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1621" />
        <source>Use extent of '{name}'</source>
        <translation type="obsolete">Использовать пространственный охват '{name}'</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1854" />
        <source>Choose imagery to start processing</source>
        <translation type="obsolete">Выберите изображение или коллекцию для запуска обработки</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1920" />
        <source>{cost} credits</source>
        <translation type="obsolete">{cost} кредитов</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1953" />
        <source> sq.km</source>
        <translation type="obsolete"> кв.км</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3129" />
        <source>Show all</source>
        <translation>Показать все</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2330" />
        <source>Only PNG preview type is supported.&lt;br&gt;See &lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#how-to-preview-the-search-results"&gt;&lt;span style=" text-decoration: underline; color:#094fd1;"&gt;documentation&lt;/span&gt;&lt;/a&gt; for help</source>
        <translation type="obsolete">Предпросмотр доступен только для PNG.&lt;br&gt;Подробности в &lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#how-to-preview-the-search-results"&gt;&lt;span style=" text-decoration: underline; color:#094fd1;"&gt;документации&lt;/span&gt;&lt;/a&gt;</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3431" />
        <source>Project</source>
        <translation type="obsolete">Проект</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3427" />
        <source>No project that meets specified criteria was found</source>
        <translation type="obsolete">Не найдено проектов, удовлетворяющих заданным критериям</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1623" />
        <source>Select AOI to start processing</source>
        <translation type="obsolete">Задайте область интереса, чтобы запустить обработку</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1865" />
        <source>No project is selected</source>
        <translation type="obsolete">Проект не выбран</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3197" />
        <source>Selected imagery has no preview</source>
        <translation>Предпросмотр данного изображения недоступен</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3202" />
        <source>Preview with such URL is unavailable</source>
        <translation>Предпросмотр данного изображения недоступен</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2426" />
        <source>Only PNG and JPG preview types are supported.&lt;br&gt;See &lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#how-to-preview-the-search-results"&gt;&lt;span style=" text-decoration: underline; color:#094fd1;"&gt;documentation&lt;/span&gt;&lt;/a&gt; for help</source>
        <translation type="obsolete">Предпросмотр доступен только для PNG и JPG.&lt;br&gt;Подробности в &lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#how-to-preview-the-search-results"&gt;&lt;span style=" text-decoration: underline; color:#094fd1;"&gt;документации&lt;/span&gt;&lt;/a&gt;</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2830" />
        <source>Change the output directory to an existing one to download the results</source>
        <translation type="obsolete">Выберите существующую рабочую папку, чтобы сохранить результаты обработки</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3722" />
        <source>Duplication failed on copying data source</source>
        <translation type="obsolete">Ошибка дублирования при копировании источника данных</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3730" />
        <source>Model '{wd}' is not enabled for your account</source>
        <translation type="obsolete">Модель '{wd}' не подключена к Вашему аккаунту</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3737" />
        <source>Duplication failed on copying model</source>
        <translation type="obsolete">Ошибка дублирования при копировании модели</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3759" />
        <source>The following options no longer exist, so they have not been duplicated: {}</source>
        <translation type="obsolete">В настоящий момент данные опции не существуют, поэтому они не были продублированы: {}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3764" />
        <source>Duplication failed on copying model options</source>
        <translation type="obsolete">Ошибка дублирования при копировании опций модели</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3773" />
        <source>Provider '{provider}' is not enabled for your account</source>
        <translation type="obsolete">Источник данных '{provider}' не подключён к Вашему аккаунту</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3848" />
        <source>Duplicated user provider</source>
        <translation type="obsolete">Дублированный пользовательский источник</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2221" />
        <source>Directory '{}' does not exist</source>
        <translation type="obsolete">Путь '{}' не существует</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2221" />
        <source>&lt;br&gt;Using Settings tab, change the output directory to an existing one to download the results</source>
        <translation type="obsolete">&lt;br&gt;Используя вкладку Настройки, выберите существующую рабочую папку, чтобы сохранить результаты обработки</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3043" />
        <source>You can launch multiple image processing only if they have the same provider</source>
        <translation type="obsolete">Запуск по нескольким изображениям доступен только если они имеют один источник</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3210" />
        <source>Preview for '{iid}' is unavailable</source>
        <translation>Предпросмотр для '{iid}' недоступен</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3715" />
        <source>Only correctly finished processings with 'Review required' status can be reviewed</source>
        <translation>Только на корректно завершенные обработки со статусом 'Review reqired' можно оставить отзыв</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="220" />
        <source>The working directory '{dir}' is unavailable:&lt;br&gt;{error}&lt;br&gt;&lt;br&gt;It is needed to save processing results on your computer.</source>
        <translation>Рабочая папка «{dir}» недоступна:&lt;br&gt;{error}&lt;br&gt;&lt;br&gt;Она нужна для сохранения результатов обработки на компьютере.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="582" />
        <source>Restart</source>
        <translation>Перезапустить</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="622" />
        <source>Start planned processing</source>
        <translation>Запустить запланированную обработку</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="624" />
        <source>Start processing</source>
        <translation>Запустить обработку</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="636" />
        <source>Select one or more images in search results to start planned processing</source>
        <translation>Выберите одно или несколько изображений в результатах поиска, чтобы запустить запланированную обработку</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="667" />
        <source>No images was found</source>
        <translation>Изображения не найдены</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="817" />
        <source>AOI: {name}</source>
        <translation>AOI: {name}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="839" />
        <source>No AOI</source>
        <translation>Без AOI</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1091" />
        <source>There are no polygon layers to add as AOIs. Draw one on the map or load a vector layer first.</source>
        <translation>Нет полигональных слоёв для добавления как AOI. Нарисуйте полигон на карте или сначала загрузите векторный слой.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1111" />
        <source>The selected layer(s) have no polygon features to add.</source>
        <translation>В выбранных слоях нет полигональных объектов для добавления.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1175" />
        <source>This AOI has no id yet and cannot be updated. Reopen the template and try again.</source>
        <translation>У этой AOI ещё нет id, её нельзя обновить. Откройте шаблон заново и повторите попытку.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1180" />
        <source>Could not find this AOI's layer on the map. Reopen the template and try again.</source>
        <translation>Не удалось найти слой этой AOI на карте. Откройте шаблон заново и повторите попытку.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1183" />
        <source>Editing AOI '{name}': move its vertices on the map, then Save AOI.</source>
        <translation>Редактирование AOI «{name}»: переместите её вершины на карте, затем «Сохранить AOI».</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1194" />
        <source>New AOI</source>
        <translation>Новая AOI</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1197" />
        <source>Draw the AOI polygon on the map, then Save AOI.</source>
        <translation>Нарисуйте полигон AOI на карте, затем нажмите «Сохранить AOI».</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1235" />
        <source>Save AOI</source>
        <translation>Сохранить AOI</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1236" />
        <source>Cancel</source>
        <translation>Отмена</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1305" />
        <source>The AOI has no geometry — draw or keep at least one polygon.</source>
        <translation>У AOI нет геометрии — нарисуйте или оставьте хотя бы один полигон.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1312" />
        <source>The edited AOI has no valid geometry.</source>
        <translation>У отредактированной AOI нет допустимой геометрии.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1334" />
        <source>Draw at least one polygon before saving.</source>
        <translation>Нарисуйте хотя бы один полигон перед сохранением.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1336" />
        <source>Name the AOI</source>
        <translation>Название AOI</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1336" />
        <source>AOI name:</source>
        <translation>Имя AOI:</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1342" />
        <source>AOI name must not exceed {limit} characters.</source>
        <translation>Имя AOI не должно превышать {limit} символов.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1411" />
        <source>Selected AOIs</source>
        <translation>Выбранные AOI</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1869" />
        <source>Start date {cur} is earlier than searched ({base})</source>
        <translation>Начальная дата {cur} раньше, чем в поиске ({base})</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1872" />
        <source>End date {cur} is later than searched ({base})</source>
        <translation>Конечная дата {cur} позже, чем в поиске ({base})</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1877" />
        <source>Max cloud cover {cur}% is higher than searched ({base}%)</source>
        <translation>Макс. облачность {cur}% выше, чем в поиске ({base}%)</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1882" />
        <source>Min intersection {cur}% is lower than searched ({base}%)</source>
        <translation>Мин. пересечение {cur}% ниже, чем в поиске ({base}%)</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1889" />
        <source>Off-nadir range {lo}-{hi}° is wider than searched ({blo}-{bhi}°)</source>
        <translation>Диапазон отклонения от надира {lo}-{hi}° шире, чем в поиске ({blo}-{bhi}°)</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1896" />
        <source>Product type(s) not searched: {extra}</source>
        <translation>Не искали типы продукта: {extra}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1902" />
        <source>Showing all providers, but search was limited to: {base}</source>
        <translation>Показаны все поставщики, но поиск был ограничен: {base}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1907" />
        <source>Provider(s) not searched: {extra}</source>
        <translation>Не искали поставщиков: {extra}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1913" />
        <source>These filters are wider than the last search, so they will not bring more images. Run a new Search to fetch them:</source>
        <translation>Эти фильтры шире последнего поиска, поэтому они не добавят изображений. Запустите новый поиск, чтобы их получить:</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2244" />
        <source>Cannot use '{dir}' as the working directory:
{error}

Please choose another directory.</source>
        <translation>Не удаётся использовать «{dir}» как рабочую папку:
{error}

Выберите другую папку.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2268" />
        <source>Select directory…</source>
        <translation>Выбрать папку…</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2269" />
        <source>Later</source>
        <translation>Позже</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2336" />
        <source>Search</source>
        <translation>Поиск</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2336" />
        <source>Plan search</source>
        <translation>Запланировать поиск</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2326" />
        <source>Seen</source>
        <translation>Просмотрено</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2327" />
        <source>Seen all</source>
        <translation>Просмотреть все</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2340" />
        <source>Select a project to create a template</source>
        <translation>Выберите проект, чтобы создать шаблон</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2371" />
        <source>Searching {datetime}</source>
        <translation>Поиск {datetime}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2378" />
        <source>The search area is too large for immediate processing. The Planned Search will be created and run in the background. You will be notified when results are available.</source>
        <translation>Область поиска слишком велика для немедленной обработки. Будет создан запланированный поиск, который выполнится в фоне. Вы получите уведомление, когда результаты будут готовы.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2387" />
        <source>Plan Search</source>
        <translation>Запланировать поиск</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2437" />
        <source>AOI name '{name}' exceeds {limit} characters</source>
        <translation>Имя AOI «{name}» превышает {limit} символов</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2507" />
        <source>Please, specify a name for your search</source>
        <translation>Укажите имя для поиска</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2523" />
        <source>Creating planned search...</source>
        <translation>Создание запланированного поиска...</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2532" />
        <source>Planned search created successfully.</source>
        <translation>Запланированный поиск успешно создан.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2537" />
        <source>Template creation failed</source>
        <translation>Не удалось создать шаблон</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2577" />
        <source>Updating template search parameters...</source>
        <translation>Обновление параметров поиска шаблона...</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2587" />
        <source>Template updated.</source>
        <translation>Шаблон обновлён.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2593" />
        <source>Template update failed</source>
        <translation>Не удалось обновить шаблон</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2637" />
        <source>This processing is not linked to any AOI geometry.</source>
        <translation>Эта обработка не связана ни с какой геометрией AOI.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2640" />
        <source>Exclude this processing's area from the template's search? The already-processed area will be removed from the AOI(s).</source>
        <translation>Исключить область этой обработки из поиска шаблона? Уже обработанная область будет удалена из AOI.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3515" />
        <source>Could not mark image(s) as seen, please try again.</source>
        <translation>Не удалось отметить изображения как просмотренные, повторите попытку.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3580" />
        <source>Planned processing</source>
        <translation>Запланированная обработка</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3582" />
        <source>Planned processing. New images: {count}</source>
        <translation>Запланированная обработка. Новых изображений: {count}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3929" />
        <source>A working directory is required to save the processing results on your computer.</source>
        <translation>Для сохранения результатов обработки на компьютере нужна рабочая папка.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3955" />
        <source>A working directory is required to save the area of interest on your computer.</source>
        <translation>Для сохранения области интереса на компьютере нужна рабочая папка.</translation>
    </message>
</context>
<context>
    <name>MapflowLoginDialog</name>
    <message>
        <location filename="../dialogs/login_dialog.py" line="32" />
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;You will be redirecrted to web browser &lt;br/&gt;to enter your Mapflow login and password&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;В браузере откроется страница входа в Mapflow, &lt;br/&gt;введите своё имя пользователя и пароль&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/login_dialog.py" line="33" />
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;span style=" color:#ff0000;"&gt;Authorization is not completed! &lt;/span&gt;&lt;/p&gt;&lt;p&gt;&lt;br/&gt;1. Complete authorization in browser. &lt;br/&gt;&lt;br/&gt;2. If it does not help, restart QGIS. &lt;br/&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#oauth2_setup"&gt;&lt;span style=" text-decoration: underline; color:#094fd1;"&gt;See documentation for help &lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;span style=" color:#ff0000;"&gt;Авторизация не завершена! &lt;/span&gt;&lt;/p&gt;&lt;p&gt;&lt;br/&gt;1. Авторизуйтесь в браузере. &lt;br/&gt;&lt;br/&gt;2. Если это не помогло, перезапустите QGIS. &lt;br/&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#oauth2_setup"&gt;&lt;span style=" text-decoration: underline; color:#094fd1;"&gt;См. документацию &lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/login_dialog.py" line="38" />
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href="https://app.mapflow.ai/account/api"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Get token&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;a href="https://mapflow.ai/terms-of-use-en.pdf"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Terms of use&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;Register at &lt;a href="https://mapflow.ai"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;mapflow.ai&lt;/span&gt;&lt;/a&gt; to use the plugin&lt;/p&gt;&lt;p&gt;&lt;br/&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href="https://app.mapflow.ai/account/api"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Получить токен&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;a href="https://mapflow.ai/terms-of-use-ru.pdf"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Условия использования&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;Зарегистрируйтесь на &lt;a href="https://mapflow.ai"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;mapflow.ai&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt; чтобы использовать плагин&lt;/p&gt;&lt;p&gt;&lt;br/&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/login_dialog.py" line="39" />
        <source>Invalid credentials</source>
        <translation>Неправильные данные авторизации</translation>
    </message>
</context>
<context>
    <name>MosaicDialog</name>
    <message>
        <location filename="../dialogs/mosaic_dialog.py" line="19" />
        <source>Imagery collection name must not be empty!</source>
        <translation>Имя коллекции изображений должно быть заполнено!</translation>
    </message>
</context>
<context>
    <name>ProcessingDetailsDialog</name>
    <message>
        <location filename="../dialogs/processing_details_dialog.py" line="15" />
        <source>Processing details</source>
        <translation>Подробности обработки</translation>
    </message>
    <message>
        <location filename="../dialogs/processing_details_dialog.py" line="47" />
        <source>My imagery</source>
        <translation>Мои изображения</translation>
    </message>
</context>
<context>
    <name>ProcessingErrors</name>
    <message>
        <location filename="../errors/processing_errors.py" line="10" />
        <source>Task for source-validation must contain area of interest (`geometry` section)</source>
        <translation>Задача на проверку источника данных должна содержать область интереса (ключ `geometry`)</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="12" />
        <source>We could not open and read the image you have uploaded</source>
        <translation>Мы не смогли открыть и прочитать загруженное изображение</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="13" />
        <source>Image profile (metadata) must have keys {required_keys}, got profile {profile}</source>
        <translation>Метаданные изображения должны содержать следующие теги: {required_keys}, метаданные загруженного изображения: {profile}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="15" />
        <source>AOI does not intersect the selected Sentinel-2 granule {actual_cell}</source>
        <translation>Области интереса не пересекает выбранное изображение Sentinel-2 (код ячейки {actual_cell} )</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="17" />
        <source>Key 'url' in your request must be a string, got {url_type} instead.</source>
        <translation>Ключ 'url' в запросе должен быть строкой, не {url_type}.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="19" />
        <source>The specified basemap {url} is forbidden for processing because it contains a map, not satellite image. Our models are suited for satellite imagery.</source>
        <translation>Указанная подложка {url} запрещена к обработке, так как содержит карту, а не спутниковый снимок. Наши модели предназначены для обработки спутниковых снимков.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="22" />
        <source>Your URL must be a link starting with "http://" or "https://".</source>
        <translation>URL должен начинаться с "http://" или "https://".</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="24" />
        <source>Format of 'url' is invalid and cannot be parsed. Error: {parse_error_message}</source>
        <translation>Невалидный формат URL. Ошибка {parse_error_message}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="26" />
        <source>Zoom must be either empty, or integer, got {actual_zoom}</source>
        <translation>Поле „zoom“ должно быть либо пустым, либо целым числом. Получено {actual_zoom}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="28" />
        <source>Zoom must be between 0 and 22, got {actual_zoom}</source>
        <translation>Значение поля „zoom“ в вашем запросе должно быть в интервале от 0 до 22. Получено {actual_zoom}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="29" />
        <source>Zoom must be not lower than {min_zoom}, got {actual_zoom}</source>
        <translation>Значение поля „zoom“ в вашем запросе должно быть не менее {min_zoom}. Получено {actual_zoom}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="30" />
        <source>Image metadata must be a dict (json)</source>
        <translation>Метаданные вашего изображения должны быть типа "словарь" (json)</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="31" />
        <source>Image metadata must have keys: crs, transform, dtype, count</source>
        <translation>Метаданные вашего изображения должны содержать ключи: crs, transform, dtype, count</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="33" />
        <source>URL of the image at s3 storage must be a string starting with s3://, got {actual_s3_link}</source>
        <translation>URL изображения на хранилище s3 должен быть строкой и начинаться с s3://. Получено {actual_s3_link}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="35" />
        <source>Request must contain either 'profile' or 'url' keys</source>
        <translation>Запрос должен содержать либо „profile“, либо „url“</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="36" />
        <source>Failed to read file from {s3_link}.</source>
        <translation>Ошибка чтения файла из {s3_link}.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="37" />
        <source>Image data type (Dtype) must be one of {required_dtypes}, got {request_dtype}</source>
        <translation>Тип данных изображения (Dtype) должен быть одним из {required_dtypes}. Получено {request_dtype}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="39" />
        <source>Number of channels in image must be one of {required_nchannels}. Got {real_nchannels}</source>
        <translation>Изображение имеет {real_nchannels} каналов, требуемое количество каналов {required_nchannels}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="41" />
        <source>Spatial resolution of you image is too high: pixel size is {actual_res}, minimum allowed pixel size is {min_res}</source>
        <translation>Пространственное разрешение вашего изображения слишком высокое: размер пикселя {actual_res}, минимальный допустимый размер пикселя равен {min_res}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="44" />
        <source>Spatial resolution of you image is too low: pixel size is {actual_res}, maximum allowed pixel size is {max_res}</source>
        <translation>Пространственное разрешение вашего изображения слишком низкое: размер пикселя равен {actual_res}, максимально допустимый размер пикселя равен {max_res}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="47" />
        <source>Error occurred during image {checked_param} check: {message}. Image metadata = {metadata}.</source>
        <translation>Ошибка произошла во время проверки параметра {checked_param} изображения: {message}. Метаданные изображения = {metadata}.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="49" />
        <source>Your 'url' doesn't match the format, Quadkey basemap must be a link containing "q" placeholder.</source>
        <translation>Ссылка на Quadkey подложку не соответствует формату. Это должна быть ссылка, содержащая поле «q».</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="52" />
        <source>Input string {input_string} is of unknown format. It must represent Sentinel-2 granule ID.</source>
        <translation>Строка {input_string} неизвестного формата. Она должна представлять собой ID гранулы снимка Sentinel-2.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="54" />
        <source>Selected Sentinel-2 image cell is {actual_cell}, this model is for the cells: {allowed_cells}</source>
        <translation>Выбранная ячейка {actual_cell} не подходит для обработки, модель рассчитана на ячейки: {allowed_cells}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="56" />
        <source>Selected Sentinel-2 image month is {actual_month}, this model is for: {allowed_months}</source>
        <translation>Выбранный месяц {actual_month} не подходит для обработки, модель рассчитана на месяцы: {allowed_months}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="58" />
        <source>You request TMS basemap link doesn't match the format, it must be a link containing "x", "y", "z" placeholders, correct it and start processing again.</source>
        <translation>Ссылка на TMS подложку не соответствует формату. Это должна быть ссылка, содержащая поля "x", "y", "z".</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="61" />
        <source>Requirements must be dict, got {requirements_type}.</source>
        <translation>Секция «requirements» в запросе должна быть словарем (dict), а не {requirements_type}.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="62" />
        <source>Request must be dict, got {request_type}.</source>
        <translation>Секция «request» в запросе должна быть словарем (dict), а не {request_type}.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="63" />
        <source>Request must contain "source_type" key</source>
        <translation>Запрос должен содержать тип источника спутниковых снимков (ключ «source_type»)</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="64" />
        <source>Source type {source_type} is not allowed. Use one of: {allowed_sources}</source>
        <translation>Источник данных {source_type}, не поддерживется платформой. Ипользуйте один из разрешенных: {allowed_sources}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="66" />
        <source>"Required" section of the requirements must contain dict, not {required_section_type}</source>
        <translation>Секция «Required» в требованиях к данным должна быть словарем (dict), а не {required_section_type}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="68" />
        <source>"Recommended" section of the requirements must contain dict, not {recommended_section_type}</source>
        <translation>Секция «recommended» в требованиях к данным должна быть словарем (dict), а не {recommended_section_type}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="70" />
        <source>You XYZ basemap link doesn't match the format, it must be a link containing "x", "y", "z"  placeholders.</source>
        <translation>Ссылка на XYZ подложку не соответствует формату. Это должна быть ссылка, содержащая поля "x", "y", "z".</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="75" />
        <source>Internal error in process of data source validation. We are working on the fix, our support will contact you.</source>
        <translation>Произошла ошибка в процессе проверки источника данных. Мы работаем над исправлением и свяжемся с вами.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="96" />
        <source>Internal error in process of loading data. We are working on the fix, our support will contact you.</source>
        <translation>Произошла ошибка в процессе загрузки данных. Мы работаем над исправлением и свяжемся с вами.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="79" />
        <source>Wrong source type {real_source_type}. Specify one of the allowed types {allowed_source_types}.</source>
        <translation>Неправильный тип источника данных {real_source_type}. Используйте один из допустимых {allowed_source_types}.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="81" />
        <source>Your data loading task requires {estimated_size} MB of memory, which exceeded allowed memory limit {allowed_size}</source>
        <translation>Ваш запрос на загрузку данных требует {estimated_size} MB, что превышает лимит в {allowed_size}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="83" />
        <source>Dataloader argument {argument_name} has type {argument_type}, excpected to be {expected_type}</source>
        <translation>Функция загрузки данных {argument_name} имеет тип {argument_type}, допустимый тип {expected_type}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="85" />
        <source>Loaded tile has {real_nchannels} channels, required number is {expected_nchannels}</source>
        <translation>Загруженное изображение имеет {real_nchannels} каналов, требуемое количество каналов {expected_nchannels}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="87" />
        <source>Loaded tile has size {real_size}, expected tile size is {expected_size}</source>
        <translation>Загруженное изображение имеет размер {real_size}, допустимый размер {expected_size}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="89" />
        <source>Tile at location {tile_location} cannot be loaded, server response is {status}</source>
        <translation>Изображение по адресу {tile_location} не может быть загружено, ответ сервера {status}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="91" />
        <source>Response content at {tile_location} cannot be decoded as an image</source>
        <translation>Ответ сервера {tile_location} не представляет собой изображение</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="100" />
        <source>Internal error in process of data preparation. We are working on the fix, our support will contact you.</source>
        <translation>Произошла ошибка в процессе предобработки данных. Мы работаем над исправлением и свяжемся с вами.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="102" />
        <source>Internal error in process of data processing. We are working on the fix, our support will contact you.</source>
        <translation>Произошла ошибка в процессе обработки данных. Мы работаем над исправлением и свяжемся с вами.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="104" />
        <source>Internal error in process of saving the results. We are working on the fix, our support will contact you.</source>
        <translation>Произошла ошибка в процессе сохранения результатов обработки. Мы работаем над исправлением и свяжемся с вами.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="8" />
        <source>Folder `{s3_link}` selected for processing does not contain any images. </source>
        <translation>Папка `{s3_link}`, выбранная для обработки, не содержит изображений. </translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="98" />
        <source>The data provider contains no data for your area of interest (returned NoData tiles). Try other the data sources to get the results.</source>
        <translation>Выбранный провайдер не обладает данными на выбранную территорию (возвращены NoData-тайлы). Попробуйте выбрать другой источник для получения результата.</translation>
    </message>
</context>
<context>
    <name>ProcessingService</name>
    <message>
        <location filename="../functional/service/processing_service.py" line="137" />
        <source>Specify processing parameters</source>
        <translation>Укажите параметры обработки</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="142" />
        <source>Please, specify a name for your processing</source>
        <translation>Пожалуйста, укажите название обработки</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="147" />
        <source>Processing area layer is corrupted or has invalid projection</source>
        <translation>Выбранная область некорректна или имеет неправильную проекцию</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="149" />
        <source>Please, select a valid area of interest</source>
        <translation>Пожалуйста, выберите допустимый слой с областью обработки</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="102" />
        <source>Up to {} sq km can be processed at a time. Try splitting your area(s) into several processings.</source>
        <translation type="obsolete">За раз можно обработать не более {} кв км. Попробуйте разделить область обработки на части.</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="189" />
        <source>Selected AOI does not intersect the selected imagery</source>
        <translation>Выбранная область не пересекается с выбранным изображением</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="191" />
        <source>This provider requires image ID. Use search tab to find imagery for you requirements, and select image in the table.</source>
        <translation>Этому провайдеру нужен ID снимка. Используйте вкладку "Поиск", чтобы найти изображения по вашим требованиям, и выберите изображение в таблице.</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1112" />
        <source>Not enough rights to start processing in a shared project ({})</source>
        <translation>Недостаточно прав в проекте для запауска обработки ({})</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="248" />
        <source>Set AOI to start processing</source>
        <translation>Задайте область интереса, чтобы запустить обработку</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="250" />
        <source>Error! Models are not initialized.
Please, make sure you have selected a project</source>
        <translation>Ошибка! Модели не инициализирваны
Пожалуйста, убедитесь, что выбран проект</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="322" />
        <source>Processing limit exceeded. Visit "&lt;a href="https://app.mapflow.ai/account/balance"&gt;Mapflow&lt;/a&gt;" to top up your balance</source>
        <translation>Превышен доступный лимит обработки. Посетите "&lt;a href="https://app.mapflow.ai/account/balance"&gt;Mapflow&lt;/a&gt;" для пополнения баланса</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="351" />
        <source>Starting the processing...</source>
        <translation>Создаем обработку...</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="361" />
        <source>Could not launch processing! Error: {}.</source>
        <translation>Не удалось запустить обработку! Ошибка: {}.</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="405" />
        <source>{cost} credits</source>
        <translation>{cost} кредитов</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="409" />
        <source> sq.km</source>
        <translation> кв.км</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="460" />
        <source>Success! We'll notify you when the processing has finished.</source>
        <translation>Обработка создана! Мы оповестим вас, когда она завершится.</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="260" />
        <source>Failed to start processing</source>
        <translation type="obsolete">Не удалось запустить обработку</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="947" />
        <source>Processing completed</source>
        <translation>Обработка завершена</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="947" />
        <source>Processing '{name}' has finished successfully</source>
        <translation>Обработка '{name}' завершена успешно</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="957" />
        <source>Processing failed</source>
        <translation>Ошибка обработки</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="957" />
        <source>Processing '{name}' has failed</source>
        <translation>Не удалось завершить обработку '{name}'</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1114" />
        <source>Processing cost is not available:
{message}</source>
        <translation>Стоимость обработки недоступна:
{message}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="496" />
        <source>Delete selected processings?</source>
        <translation type="obsolete">Удалить выбранные обработки?</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="511" />
        <source>Failed to remove processings with following ids: &lt;center&gt; {failed_ids}</source>
        <translation type="obsolete">Неудалось удалить обработки со следующими id: &lt;center&gt; {failed_ids}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="517" />
        <source>The selected data provider is unavailable on your plan. 
 Upgrade your subscription to get access to the data. 
See pricing at &lt;a href="https://mapflow.ai/pricing"&gt;mapflow.ai&lt;/a&gt;</source>
        <translation>Выбранный провайдер данных недоступен в Вашем тарифном плане. 
Обновите подписку для получения доступа к данным. 
Узнать цену: &lt;a href="https://mapflow.ai/pricing"&gt;mapflow.ai&lt;/a&gt;</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="528" />
        <source>Processing creation failed</source>
        <translation>Не удалось создать обработку</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="157" />
        <source>The processing area is {area} sq km, over the {limit} sq km limit. Try splitting your area(s) into several processings.</source>
        <translation>Область обработки — {area} км², что превышает лимит {limit} км². Разбейте область на несколько обработок.</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="170" />
        <source>An AOI is too large: its bounding box is {area} sq km, over the {limit} sq km limit. Reduce the area of interest.</source>
        <translation>AOI слишком большая: её ограничивающий прямоугольник — {area} км², что превышает лимит {limit} км². Уменьшите область интереса.</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="180" />
        <source>the selected</source>
        <translation>выбранный</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="288" />
        <source>Select one or more images in search results to start planned processing</source>
        <translation>Выберите одно или несколько изображений в результатах поиска, чтобы запустить запланированную обработку</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="340" />
        <source>Starting planned processing...</source>
        <translation>Запуск запланированной обработки...</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="989" />
        <source>Rename template</source>
        <translation>Переименовать шаблон</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="989" />
        <source>Template name:</source>
        <translation>Имя шаблона:</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1000" />
        <source>Please, specify template name</source>
        <translation>Укажите имя шаблона</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1045" />
        <source>Error renaming template: {}</source>
        <translation>Ошибка переименования шаблона: {}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1232" />
        <source>Unknown server error</source>
        <translation>Неизвестная ошибка сервера</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1129" />
        <source>Delete selected items?</source>
        <translation>Удалить выбранные элементы?</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1144" />
        <source>Failed to remove items with following ids: &lt;center&gt; {failed_ids}</source>
        <translation>Не удалось удалить элементы со следующими id: &lt;center&gt; {failed_ids}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1210" />
        <source>Template is not active</source>
        <translation>Шаблон не активен</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1216" />
        <source>Template paused successfully</source>
        <translation>Шаблон успешно приостановлен</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1218" />
        <source>Failed to pause template: {}</source>
        <translation>Не удалось приостановить шаблон: {}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1236" />
        <source>Error pausing template: {}</source>
        <translation>Ошибка приостановки шаблона: {}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1254" />
        <source>Template is already active</source>
        <translation>Шаблон уже активен</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1285" />
        <source>Template resumed successfully</source>
        <translation>Шаблон успешно возобновлён</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1287" />
        <source>Failed to resume template: {}</source>
        <translation>Не удалось возобновить шаблон: {}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1292" />
        <source>Error resuming template: {}</source>
        <translation>Ошибка возобновления шаблона: {}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1301" />
        <source>Only failed templates can be restarted</source>
        <translation>Перезапустить можно только шаблоны с ошибкой</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1313" />
        <source>Template restarted successfully</source>
        <translation>Шаблон успешно перезапущен</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1315" />
        <source>Failed to restart template: {}</source>
        <translation>Не удалось перезапустить шаблон: {}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1319" />
        <source>Error restarting template: {}</source>
        <translation>Ошибка перезапуска шаблона: {}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1328" />
        <source>Delete Template</source>
        <translation>Удалить шаблон</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1328" />
        <source>Are you sure you want to delete the template '{}'?</source>
        <translation>Удалить шаблон «{}»?</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1346" />
        <source>Template deleted successfully</source>
        <translation>Шаблон успешно удалён</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1348" />
        <source>Failed to delete template: {}</source>
        <translation>Не удалось удалить шаблон: {}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1352" />
        <source>Error deleting template: {}</source>
        <translation>Ошибка удаления шаблона: {}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1364" />
        <source>This AOI has no id yet and cannot be renamed. Reopen the template and try again.</source>
        <translation>У этой AOI ещё нет id, её нельзя переименовать. Откройте шаблон заново и повторите попытку.</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1368" />
        <source>Rename AOI</source>
        <translation>Переименовать AOI</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1368" />
        <source>AOI name:</source>
        <translation>Имя AOI:</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1378" />
        <source>Please, specify AOI name</source>
        <translation>Укажите имя AOI</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1381" />
        <source>AOI name must not exceed {limit} characters</source>
        <translation>Имя AOI не должно превышать {limit} символов</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1403" />
        <source>Delete selected AOI(s)?</source>
        <translation>Удалить выбранные AOI?</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1441" />
        <source>AOI update failed: {}</source>
        <translation>Не удалось обновить AOI: {}</translation>
    </message>
</context>
<context>
    <name>ProcessingView</name>
    <message>
        <location filename="../functional/view/processing_view.py" line="230" />
        <source>Please review or accept this processing until {}. Double click to add results to the map</source>
        <translation>Пожалуйста, оставьте отзыв или примите результаты до {}. Двойной клик для добавления результатов на карту</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="235" />
        <source>Double click to add results to the map.</source>
        <translation>Двойной клик, чтобы добавить результаты на карту.</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="321" />
        <source>Loading...</source>
        <translation>Загрузка...</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="322" />
        <source>Fetching your processings from server, please wait</source>
        <translation>Получаение обработки с сервера. Пожалуйста, подождите</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="379" />
        <source>Processing cost: {cost} credits</source>
        <translation>Стоимость обработки: {cost} кредитов</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="388" />
        <source> failed with error:
</source>
        <translation> завершилась с ошибкой:
</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="395" />
        <source>{} processings failed: 
 {} 
 See tooltip over the processings table for error details</source>
        <translation>Завершено обработок с ошибкой: {} 
 {} 
 Наведите курсор мыши на обработку в таблице, чтобы увидеть сообщение об ошибке</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="402" />
        <source>{} processings failed: 
 See tooltip over the processings table for error details</source>
        <translation>Завершено с ошибкой {} обработок
 Наведите курсор мыши на обработку в таблице чтобы увидеть сообщение об ошибке</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="414" />
        <source> finished. Double-click it in the table to download the results.</source>
        <translation> завершилась. Дважды кликните на нее в таблице, чтобы загрузить результаты.</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="422" />
        <source>{} processings finished: 
 {} 
 Double-click it in the table to download the results</source>
        <translation>Успешно завершено обработок: {}. 
 {} 
 Двойной клик по строке обработки в таблице скачает результаты</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="430" />
        <source>{} processings finished. 
 Double-click it in the table to download the results</source>
        <translation>Завершено успешно {} обработок.
 Двойной клик по строке обработки в таблице скачает результаты</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="36" />
        <source>Newest first</source>
        <translation>Сначала новые</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="36" />
        <source>Oldest first</source>
        <translation>Сначала старые</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="36" />
        <source>A-Z</source>
        <translation>А-Я</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="36" />
        <source>Z-A</source>
        <translation>Я-А</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="36" />
        <source>Status A-Z</source>
        <translation>Статус А-Я</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="36" />
        <source>Status Z-A</source>
        <translation>Статус Я-А</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="45" />
        <source>Filter processings</source>
        <translation>Отфильтровать обработки</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="140" />
        <source>Open Details</source>
        <translation>Открыть подробности</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="142" />
        <source>Pause Template</source>
        <translation>Приостановить шаблон</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="143" />
        <source>Resume Template</source>
        <translation>Возобновить шаблон</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="145" />
        <source>Delete Template</source>
        <translation>Удалить шаблон</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="212" />
        <source>Planned processing</source>
        <translation>Запланированная обработка</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="214" />
        <source>Planned processing. New images: {count}</source>
        <translation>Запланированная обработка. Новых изображений: {count}</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="219" />
        <source>Template AOI</source>
        <translation>AOI шаблона</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="221" />
        <source>Template AOI with new images</source>
        <translation>AOI шаблона с новыми изображениями</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="224" />
        <source>Processing from this AOI. Double-click to load results.</source>
        <translation>Обработка из этой AOI. Дважды щёлкните, чтобы загрузить результаты.</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="226" />
        <source>Processings not intersecting any AOI</source>
        <translation>Обработки, не пересекающие ни одну AOI</translation>
    </message>
</context>
<context>
    <name>ProjectDialog</name>
    <message>
        <location filename="../dialogs/static/ui/project_dialog.ui" line="14" />
        <source>Project</source>
        <translation>Проект</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/project_dialog.ui" line="20" />
        <source>Name</source>
        <translation>Имя</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/mosaic_dialog.ui" line="34" />
        <source>Tags</source>
        <translation>Тэги</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/mosaic_dialog.ui" line="51" />
        <source>Note: separate tags with comma (", ") </source>
        <translation>Разделитель тэгов: ", "</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/project_dialog.ui" line="34" />
        <source>Description</source>
        <translation>Описание</translation>
    </message>
    <message>
        <location filename="../dialogs/project_dialog.py" line="25" />
        <source>Project name must not be empty!</source>
        <translation>Имя проекта должно быть заполнено!</translation>
    </message>
    <message>
        <location filename="../dialogs/project_dialog.py" line="57" />
        <source>owner: </source>
        <translation type="obsolete">владелец: </translation>
    </message>
    <message>
        <location filename="../dialogs/project_dialog.py" line="55" />
        <source>Edit project </source>
        <translation>Редактировать проект </translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/mosaic_dialog.ui" line="75" />
        <source>Create empty mosaic</source>
        <translation>Создать пустую коллекцию</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/mosaic_dialog.ui" line="80" />
        <source>Upload from files</source>
        <translation>Загрузить из файла</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/mosaic_dialog.ui" line="85" />
        <source>Choose raster layers</source>
        <translation>Добавить из растрового слоя</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="26" />
        <source>Start processing with specified parameters?</source>
        <translation>Запустить обработку с указанными параметрами?</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="66" />
        <source>Area:</source>
        <translation>Площадь:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="232" />
        <source>Model options:</source>
        <translation>Опции:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="216" />
        <source>Zoom:</source>
        <translation>Масштабный уровень:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="82" />
        <source>Name:</source>
        <translation>Название:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="132" />
        <source>Data source:</source>
        <translation>Источник данных:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="332" />
        <source>Model:</source>
        <translation>Модель:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="248" />
        <source>Price:</source>
        <translation>Стоимость:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="428" />
        <source>Don't show this message again</source>
        <translation>Не показывать снова</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_details.ui" line="193" />
        <source>Status:</source>
        <translation>Статус:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_details.ui" line="209" />
        <source>Description:</source>
        <translation>Описание:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_details.ui" line="492" />
        <source>Error:</source>
        <translation>Ошибка:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_details.ui" line="444" />
        <source>Data provider:</source>
        <translation>Источник данных:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_details.ui" line="177" />
        <source>ID:</source>
        <translation>ID:</translation>
    </message>
</context>
<context>
    <name>ProjectProcessingController</name>
    <message>
        <location filename="../functional/controller/processing_controller.py" line="205" />
        <source>Do you really want to remove project {}? This action cannot be undone, all processings will be lost!</source>
        <translation>Вы действительно хотите удалить проект {}? Это действие нельзя отменить, все обработки будут потеряны!</translation>
    </message>
    <message>
        <location filename="../functional/controller/processing_controller.py" line="107" />
        <source>Processing</source>
        <translation>Обработка</translation>
    </message>
</context>
<context>
    <name>ProjectService</name>
    <message>
        <location filename="../functional/service/project_service.py" line="227" />
        <source>Project: &lt;b&gt;{}</source>
        <translation>Проект: &lt;b&gt;{}</translation>
    </message>
    <message>
        <location filename="../functional/service/project_service.py" line="244" />
        <source>No project selected</source>
        <translation>Проект не выбран</translation>
    </message>
    <message>
        <location filename="../functional/service/project_service.py" line="246" />
        <source>You can't remove or modify default project</source>
        <translation>Нельзя удалять или менять проект по умолчанию</translation>
    </message>
    <message>
        <location filename="../functional/service/project_service.py" line="249" />
        <source>Not enough rights to delete or update shared project ({})</source>
        <translation>Недостаточно прав для удаления или изменения проекта ({})</translation>
    </message>
</context>
<context>
    <name>ProjectView</name>
    <message>
        <location filename="../functional/view/project_view.py" line="59" />
        <source>See projects</source>
        <translation>Открыть проекты</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="61" />
        <source>See processings</source>
        <translation>Открыть обработки</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="63" />
        <source>Filter projects by name</source>
        <translation>Отфильтровать проекты по имени</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="64" />
        <source>Create project</source>
        <translation>Создать проект</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="66" />
        <source>A-Z</source>
        <translation>А-Я</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="66" />
        <source>Z-A</source>
        <translation>Я-А</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="66" />
        <source>Newest first</source>
        <translation>Сначала новые</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="66" />
        <source>Oldest first</source>
        <translation>Сначала старые</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="66" />
        <source>Updated recently</source>
        <translation>Обновлены недавно</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="66" />
        <source>Updated long ago</source>
        <translation>Обновлены давно</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="164" />
        <source>Project</source>
        <translation>Проект</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="170" />
        <source>Processing</source>
        <translation>Обработка</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="145" />
        <source>No project that meets specified criteria was found</source>
        <translation>Не найдено проектов, удовлетворяющих заданным критериям</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="118" />
        <source>Succeeded: {ok} · Failed: {failed} · Planned: {templates}</source>
        <translation>Успешно: {ok} · Ошибок: {failed} · Запланировано: {templates}</translation>
    </message>
</context>
<context>
    <name>ProviderDialog</name>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="88" />
        <source>Name</source>
        <translation>Название</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="53" />
        <source>Type</source>
        <translation>Тип</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="66" />
        <source>Tile coordinate scheme. XYZ is the most popular format, use it if you are not sure</source>
        <translation>Тайловая схема. Самый популярный формат - XYZ, используйте его если не уверены</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="112" />
        <source>Login</source>
        <translation>Логин</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="122" />
        <source>Password</source>
        <translation>Пароль</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="129" />
        <source>CRS</source>
        <translation>CRS</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="154" />
        <source>Projection of the tile layer. The most popular is Web Mercator, use it if you are not sure</source>
        <translation>Проекция тайлового слоя. Самая популярная - Web Mercator (EPSG:3857), используйте её если не уверены</translation>
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
        <translation>Предупреждение! Логин и пароль, в случае сохранения, будут храниться в настройках QGIS без шифрования!</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="174" />
        <source>Save login and password</source>
        <translation>Сохранить логин и пароль</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="35" />
        <source>Provider</source>
        <translation>Источник данных</translation>
    </message>
</context>
<context>
    <name>ProviderService</name>
    <message>
        <location filename="../functional/service/provider_service.py" line="109" />
        <source>Providers are not initialized</source>
        <translation>Провайдеры данных не установлены</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="191" />
        <source>Choose imagery collection or image to start processing</source>
        <translation>Выберите изображение или коллекцию для запуска обработки</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="197" />
        <source>This provider requires image ID. Use search tab to find imagery for you requirements, and select image in the table.</source>
        <translation>Этому провайдеру нужен ID снимка. Используйте вкладку "Поиск", чтобы найти изображения по вашим требованиям, и выберите изображение в таблице.</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="316" />
        <source>You can launch multiple image processing only if it has the same provider of mosaic type</source>
        <translation>Запуск по нескольким изображениям доступен только если у них один источник мозаичного типа</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="346" />
        <source>Duplication failed on copying data source</source>
        <translation>Ошибка дублирования при копировании источника данных</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="354" />
        <source>Model '{wd}' is not enabled for your account</source>
        <translation>Модель '{wd}' не подключена к Вашему аккаунту</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="383" />
        <source>The following options no longer exist, so they have not been duplicated: {}</source>
        <translation>В настоящий момент данные опции не существуют, поэтому они не были продублированы: {}</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="388" />
        <source>Duplication failed on copying model options</source>
        <translation>Ошибка дублирования при копировании опций модели</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="397" />
        <source>Provider '{provider}' is not enabled for your account</source>
        <translation>Источник данных '{provider}' не подключён к Вашему аккаунту</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="495" />
        <source>Duplicated user provider</source>
        <translation>Дублированный пользовательский источник</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="217" />
        <source>Selected search results must be of the same product type</source>
        <translation>Тип продукта для выбранных результатов поиска должен быть одинаковым</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="227" />
        <source>Selected search results must have the same zoom level</source>
        <translation>Выбранные результаты поиска должны иметь один уровень масштабирования</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="361" />
        <source>Duplication failed on copying model</source>
        <translation>Ошибка дублирования при копировании модели</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="268" />
        <source>Geometry area is {aoiArea:.2f} sq km, which is smaller than the minimum required area for {providerName} data provider ({providerMinArea} sq km)</source>
        <translation>Площадь геометрии — {aoiArea:.2f} км², что меньше минимальной площади для поставщика данных {providerName} ({providerMinArea} км²)</translation>
    </message>
</context>
<context>
    <name>QPlatformTheme</name>
    <message>
        <location filename="../mapflow.py" line="163" />
        <source>Cancel</source>
        <translation>Отмена</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="164" />
        <source>&amp;Yes</source>
        <translation>&amp;Да</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="165" />
        <source>&amp;No</source>
        <translation>&amp;Нет</translation>
    </message>
</context>
<context>
    <name>RenameImageDialog</name>
    <message>
        <location filename="../dialogs/image_dialog.py" line="18" />
        <source>Dialog requires current image</source>
        <translation>Необходимо выбрать изображение</translation>
    </message>
    <message>
        <location filename="../dialogs/image_dialog.py" line="19" />
        <source>Rename image {}</source>
        <translation>Переименовать изображение {}</translation>
    </message>
    <message>
        <location filename="../dialogs/image_dialog.py" line="34" />
        <source>Image name must not be empty!</source>
        <translation>Имя изображения должно быть заполнено!</translation>
    </message>
</context>
<context>
    <name>ReviewDialog</name>
    <message>
        <location filename="../dialogs/review_dialog.py" line="25" />
        <source>Review {processing}</source>
        <translation>Отзыв на {processing}</translation>
    </message>
</context>
<context>
    <name>SentinelAuthDialog</name>
    <message>
        <location filename="../static/ui/sentinel_auth_dialog.ui" line="35" />
        <source>SkyWatch API Key</source>
        <translation type="obsolete">Ключ для SkyWatch API</translation>
    </message>
    <message>
        <location filename="../static/ui/sentinel_auth_dialog.ui" line="43" />
        <source>API key:</source>
        <translation type="obsolete">Ключ API:</translation>
    </message>
</context>
<context>
    <name>UpdateMosaicDialog</name>
    <message>
        <location filename="../dialogs/mosaic_dialog.py" line="49" />
        <source>UpdateMosaicDialog requires a imagery collection to update</source>
        <translation>UpdateMosaicDialog требует выбор коллекции изображений для редактирования</translation>
    </message>
    <message>
        <location filename="../dialogs/mosaic_dialog.py" line="51" />
        <source>Edit mosaic {}</source>
        <translation type="obsolete">Редактировать мозаику {}</translation>
    </message>
    <message>
        <location filename="../dialogs/mosaic_dialog.py" line="61" />
        <source>Mosaic name must not be empty!</source>
        <translation type="obsolete">Имя мозаики должно быть заполнено!</translation>
    </message>
    <message>
        <location filename="../dialogs/mosaic_dialog.py" line="50" />
        <source>Edit imagery collection {}</source>
        <translation>Редактировать коллекцию изображений {}</translation>
    </message>
    <message>
        <location filename="../dialogs/mosaic_dialog.py" line="62" />
        <source>Imagery collection name must not be empty!</source>
        <translation>Имя коллекции изображений должно быть заполнено!</translation>
    </message>
</context>
<context>
    <name>UpdateProcessingDialog</name>
    <message>
        <location filename="../dialogs/processing_dialog.py" line="26" />
        <source>Processing name must not be empty!</source>
        <translation>Имя обработки должно быть заполнено!</translation>
    </message>
    <message>
        <location filename="../dialogs/processing_dialog.py" line="34" />
        <source>Edit processing {}</source>
        <translation>Редактировать обработку {}</translation>
    </message>
</context>
<context>
    <name>UploadRasterLayersDialog</name>
    <message>
        <location filename="../dialogs/upload_raster_layer_dialog.py" line="17" />
        <source>Choose raster layers to upload to imagery collection</source>
        <translation>Выберите растровый слой для загрузки в коллекцию изображений</translation>
    </message>
</context>
<context>
    <name>raterLayerSelection</name>
    <message>
        <location filename="../dialogs/static/ui/raster_layers_dialog.ui" line="14" />
        <source>Multiple selection</source>
        <translation>Множественный выбор</translation>
    </message>
</context>
<context>
    <name>reviewDialog</name>
    <message>
        <location filename="../dialogs/static/ui/review_dialog.ui" line="14" />
        <source>Dialog</source>
        <translation>Окно</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/review_dialog.ui" line="25" />
        <source>Map layer with review</source>
        <translation>Слой карты с отзывом</translation>
    </message>
</context>
<context><name>ProcessingTable</name><message><source>(unnamed)</source><translation>(без имени)</translation></message><message><source>AOI</source><translation>AOI</translation></message><message><source>Created</source><translation>Создан</translation></message><message><source>Failed</source><translation>Ошибка</translation></message><message><source>Failed ({ok}/{total})</source><translation>Ошибки ({ok}/{total})</translation></message><message><source>In progress ({ok}/{total})</source><translation>В процессе ({ok}/{total})</translation></message><message><source>Inactive</source><translation>Неактивен</translation></message><message><source>No AOI</source><translation>Без AOI</translation></message><message><source>OK ({ok}/{total})</source><translation>OK ({ok}/{total})</translation></message><message><source>OK ({total})</source><translation>OK ({total})</translation></message><message><source>Planned</source><translation>Запланировано</translation></message><message><source>Searching</source><translation>Поиск</translation></message><message><source>Updated</source><translation>Обновлён</translation></message><message><source>Updated ({count})</source><translation>Обновлён ({count})</translation></message></context></TS>