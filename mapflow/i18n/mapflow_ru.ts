<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="ru_RU" sourcelanguage="en">
<context>
    <name>ErrorMessageList</name>
    <message>
        <location filename="../errors.py" line="19"/>
        <source>Key &apos;url&apos; in your request must be a string, got {url_type} instead.</source>
        <translation>Ключ &apos;url&apos; в запросе должен быть строкой, не {url_type}.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="24"/>
        <source>Your URL must be a link starting with &quot;http://&quot; or &quot;https://&quot;.</source>
        <translation>URL должен начинаться с &quot;http://&quot; или &quot;https://&quot;.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="26"/>
        <source>Format of &apos;url&apos; is invalid and cannot be parsed. Error: {parse_error_message}</source>
        <translation>Невалидный формат URL. Ошибка {parse_error_message}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="28"/>
        <source>Zoom must be either empty, or integer, got {actual_zoom}</source>
        <translation>Поле „zoom“ должно быть либо пустым, либо целым числом. Получено {actual_zoom}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="30"/>
        <source>Zoom must be between 0 and 22, got {actual_zoom}</source>
        <translation>Значение поля „zoom“ в вашем запросе должно быть в интервале от 0 до 22. Получено {actual_zoom}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="31"/>
        <source>Zoom must be not lower than {min_zoom}, got {actual_zoom}</source>
        <translation>Значение поля „zoom“ в вашем запросе должно быть не менее {min_zoom}. Получено {actual_zoom}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="32"/>
        <source>Image metadata must be a dict (json)</source>
        <translation>Метаданные вашего изображения должны быть типа &quot;словарь&quot; (json)</translation>
    </message>
    <message>
        <location filename="../errors.py" line="33"/>
        <source>Image metadata must have keys: crs, transform, dtype, count</source>
        <translation>Метаданные вашего изображения должны содержать ключи: crs, transform, dtype, count</translation>
    </message>
    <message>
        <location filename="../errors.py" line="35"/>
        <source>URL of the image at s3 storage must be a string starting with s3://, got {actual_s3_link}</source>
        <translation>URL изображения на хранилище S3 должен быть строкой и начинаться с S3://. Получено {actual_s3_link}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="37"/>
        <source>Request must contain either &apos;profile&apos; or &apos;url&apos; keys</source>
        <translation>Запрос должен содержать либо „profile“, либо „url“</translation>
    </message>
    <message>
        <location filename="../errors.py" line="38"/>
        <source>Failed to read file from {s3_link}.</source>
        <translation>Ошибка чтения файла из {s3_link}.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="39"/>
        <source>Image data type (Dtype) must be one of {required_dtypes}, got {request_dtype}</source>
        <translation>Тип данных изображения (Dtype) должен быть одним из {required_dtypes}. Получено {request_dtype}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="41"/>
        <source>Number of channels in image must be one of {required_nchannels}. Got {real_nchannels}</source>
        <translation>Изображение имеет {real_nchannels} каналов, требуемое количество каналов {required_nchannels}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="43"/>
        <source>Spatial resolution of you image is too high: pixel size is {actual_res}, minimum allowed pixel size is {min_res}</source>
        <translation>Пространственное разрешение вашего изображения слишком высокое: размер пикселя {actual_res}, минимальный допустимый размер пикселя равен {min_res}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="46"/>
        <source>Spatial resolution of you image is too low: pixel size is {actual_res}, maximum allowed pixel size is {max_res}</source>
        <translation>Пространственное разрешение вашего изображения слишком низкое: размер пикселя равен {actual_res}, максимально допустимый размер пикселя равен {max_res}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="49"/>
        <source>Error occurred during image {checked_param} check: {message}. Image metadata = {metadata}.</source>
        <translation>Ошибка произошла во время проверки параметра {checked_param} изображения: {message}. Метаданные изображения = {metadata}.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="51"/>
        <source>Your &apos;url&apos; doesn&apos;t match the format, Quadkey basemap must be a link containing &quot;q&quot; placeholder.</source>
        <translation>Ссылка на Quadkey подложку не соответствует формату. Это должна быть ссылка, содержащая поле «q».</translation>
    </message>
    <message>
        <location filename="../errors.py" line="54"/>
        <source>Input string {input_string} is of unknown format. It must represent Sentinel-2 granule ID.</source>
        <translation>Строка {input_string} неизвестного формата. Она должна представлять собой ID гранулы снимка Sentinel-2.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="56"/>
        <source>Selected Sentinel-2 image cell is {actual_cell}, this model is for the cells: {allowed_cells}</source>
        <translation>Выбранная ячейка {actual_cell} не подходит для обработки, модель рассчитана на ячейки: {allowed_cells}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="58"/>
        <source>Selected Sentinel-2 image month is {actual_month}, this model is for: {allowed_months}</source>
        <translation>Выбранный месяц {actual_month} не подходит для обработки, модель рассчитана на месяцы: {allowed_months}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="60"/>
        <source>You request TMS basemap link doesn&apos;t match the format, it must be a link containing &apos;{x}&apos;, &apos;{y}&apos;, &apos;{z}&apos; placeholders, correct it and start processing again.</source>
        <translation>Ссылка на TMS подложку не соответствует формату. Это должна быть ссылка, содержащая поля &quot;{x}&quot;, &quot;{y}&quot;, &quot;{z}&quot;.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="63"/>
        <source>Requirements must be dict, got {requirements_type}.</source>
        <translation>Секция «requirements» в запросе должна быть словарем (dict), а не {requirements_type}.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="64"/>
        <source>Request must be dict, got {request_type}.</source>
        <translation>Секция «request» в запросе должна быть словарем (dict), а не {request_type}.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="65"/>
        <source>Request must contain &quot;source_type&quot; key</source>
        <translation>Запрос должен содержать тип источника спутниковых снимков (ключ «source_type»)</translation>
    </message>
    <message>
        <location filename="../errors.py" line="66"/>
        <source>Source type {source_type} is not allowed. Use one of: {allowed_sources}</source>
        <translation>Источник данных {source_type}, не поддерживется платформой. Ипользуйте один из разрешенных: {allowed_sources}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="68"/>
        <source>&quot;Required&quot; section of the requirements must contain dict, not {required_section_type}</source>
        <translation>Секция «Required» в требованиях к данным должна быть словарем (dict), а не {required_section_type}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="70"/>
        <source>&quot;Recommended&quot; section of the requirements must contain dict, not {recommended_section_type}</source>
        <translation>Секция «recommended» в требованиях к данным должна быть словарем (dict), а не {recommended_section_type}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="72"/>
        <source>You XYZ basemap link doesn&apos;t match the format, it must be a link containing &apos;{x}&apos;, &apos;{y}&apos;, &apos;{z}&apos; placeholders.</source>
        <translation>Ссылка на XYZ подложку не соответствует формату. Это должна быть ссылка, содержащая поля &quot;{x}&quot;, &quot;{y}&quot;, &quot;{z}&quot;.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="77"/>
        <source>Internal error in process of data source validation. We are working on the fix, our support will contact you.</source>
        <translation>Произошла ошибка в процессе проверки источника данных. Мы работаем над исправлением и свяжемся с вами.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="98"/>
        <source>Internal error in process of loading data. We are working on the fix, our support will contact you.</source>
        <translation>Произошла ошибка в процессе загрузки данных. Мы работаем над исправлением и свяжемся с вами.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="81"/>
        <source>Wrong source type {real_source_type}. Specify one of the allowed types {allowed_source_types}.</source>
        <translation>Неправильный тип источника данных {real_source_type}. Используйте один из допустимых {allowed_source_types}.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="83"/>
        <source>Your data loading task requires {estimated_size} MB of memory, which exceeded allowed memory limit {allowed_size}</source>
        <translation>Ваш запрос на загрузку данных требует {estimated_size} MB, что превышает лимит в {allowed_size}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="85"/>
        <source>Dataloader argument {argument_name} has type {argument_type}, excpected to be {expected_type}</source>
        <translation>Функция загрузки данных {argument_name} имеет тип {argument_type}, допустимый тип {expected_type}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="87"/>
        <source>Loaded tile has {real_nchannels} channels, required number is {expected_nchannels}</source>
        <translation>Загруженное изображение имеет {real_nchannels} каналов, требуемое количество каналов {expected_nchannels}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="89"/>
        <source>Loaded tile has size {real_size}, expected tile size is {expected_size}</source>
        <translation>Загруженное изображение имеет размер {real_size}, допустимый размер {expected_size}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="91"/>
        <source>Tile at location {tile_location} cannot be loaded, server response is {status}</source>
        <translation>Изображение по адресу {tile_location} не может быть загружено, ответ сервера {status}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="93"/>
        <source>Response content at {tile_location} cannot be decoded as an image</source>
        <translation>Ответ сервера {tile_location} не представляет собой изображение</translation>
    </message>
    <message>
        <location filename="../errors.py" line="100"/>
        <source>Internal error in process of data preparation. We are working on the fix, our support will contact you.</source>
        <translation>Произошла ошибка в процессе предобработки данных. Мы работаем над исправлением и свяжемся с вами.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="102"/>
        <source>Internal error in process of data processing. We are working on the fix, our support will contact you.</source>
        <translation>Произошла ошибка в процессе обработки данных. Мы работаем над исправлением и свяжемся с вами.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="104"/>
        <source>Internal error in process of saving the results. We are working on the fix, our support will contact you.</source>
        <translation>Произошла ошибка в процессе сохранения результатов обработки. Мы работаем над исправлением и свяжемся с вами.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="110"/>
        <source>Unknown error. Contact us to resolve the issue! help@geoalert.io</source>
        <translation>Неизвестная ошибка. Свяжитесь с нами чтобы решить проблему! help@geoalert.io</translation>
    </message>
    <message>
        <location filename="../errors.py" line="16"/>
        <source>Image profile (metadata) must have keys {required_keys}, got profile {profile}</source>
        <translation>Метаданные изображения должны содержать следующие теги: {required_keys}, метаданные загруженного изображения: {profile}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="13"/>
        <source>Task for source-validation must contain area of interest (`geometry` section)</source>
        <translation>Задача на проверку источника данных должна содержать область интереса (ключ `geometry`)</translation>
    </message>
    <message>
        <location filename="../errors.py" line="15"/>
        <source>We could not open and read the image you have uploaded</source>
        <translation>Мы не смогли открыть и прочитать загруженное изображение</translation>
    </message>
    <message>
        <location filename="../errors.py" line="18"/>
        <source>AOI does not intersect the selected Sentinel-2 granule {actual_cell}</source>
        <translation>Области интереса не пересекает выбранное изображение Sentinel-2 (код ячейки {actual_cell} )</translation>
    </message>
    <message>
        <location filename="../errors.py" line="21"/>
        <source>The specified basemap {url} is forbidden for processing because it contains a map, not satellite image. Our models are suited for satellite imagery.</source>
        <translation>Указанная подложка {url} запрещена к обработке, так как содержит карту, а не спутниковый снимок. Наши модели предназначены для обработки спутниковых снимков.</translation>
    </message>
</context>
<context>
    <name>LoginDialog</name>
    <message>
        <location filename="../static/ui/login_dialog.ui" line="32"/>
        <source>Mapflow - Log In</source>
        <translation>Mapflow - Авторизация</translation>
    </message>
    <message>
        <location filename="../static/ui/login_dialog.ui" line="96"/>
        <source>Cancel</source>
        <translation>Отмена</translation>
    </message>
    <message>
        <location filename="../static/ui/login_dialog.ui" line="103"/>
        <source>Log in</source>
        <translation>Вход</translation>
    </message>
    <message>
        <location filename="../static/ui/login_dialog.ui" line="53"/>
        <source>Token</source>
        <translation>Токен</translation>
    </message>
    <message>
        <location filename="../static/ui/login_dialog.ui" line="59"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href=&quot;https://docs.mapflow.ai/userguides/mapflow_auth.html&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Need an account?&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;a href=&quot;https://mapflow.ai/terms-of-use-en.pdf&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Terms of use&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation type="obsolete">&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href=&quot;https://ru.docs.mapflow.ai/userguides/mapflow_auth.html&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Зарегистрироваться&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;a href=&quot;https://mapflow.ai/terms-of-use.pdf&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Условия использования&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../static/ui/login_dialog.ui" line="40"/>
        <source>This plugin is an interface to to the Mapflow.ai satellite image processing platform. You need to register an account to use it. </source>
        <translation>Этот плагин - интерфейс для работы с Mapflow.ai - платформой обработки спутниковых снимков. Чтобы его использовать, нужно зарегистрировать аккаунт. </translation>
    </message>
    <message>
        <location filename="../static/ui/login_dialog.ui" line="62"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href=&quot;https://app.mapflow.ai/account/api&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Get token&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;a href=&quot;https://mapflow.ai/terms-of-use-en.pdf&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Terms of use&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;Register at &lt;a href=&quot;https://mapflow.ai&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;mapflow.ai&lt;/span&gt;&lt;/a&gt; to use the plugin&lt;/p&gt;&lt;p&gt;&lt;br/&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href=&quot;https://app.mapflow.ai/account/api&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Получить токен&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;a href=&quot;https://mapflow.ai/terms-of-use.pdf&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Условия использования&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;Зарегистрируйтесь на &lt;a href=&quot;https://mapflow.ai&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;mapflow.ai&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt; чтобы использовать плагин&lt;/p&gt;&lt;p&gt;&lt;br/&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
</context>
<context>
    <name>MainDialog</name>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="27"/>
        <source>Processing</source>
        <translation>Обработка</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="166"/>
        <source>Name:</source>
        <translation>Название:</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="159"/>
        <source>Mapflow model:</source>
        <translation>Модель Mapflow:</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="597"/>
        <source>Area:</source>
        <translation>Область:</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="152"/>
        <source>Imagery source:</source>
        <translation>Данные ДЗЗ:</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="38"/>
        <source>Use image extent</source>
        <translation>Использовать охват снимка</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="83"/>
        <source>Start processing</source>
        <translation>Начать обработку</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="318"/>
        <source>Name</source>
        <translation>Название</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="326"/>
        <source>Model</source>
        <translation>Модель</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="334"/>
        <source>Status</source>
        <translation>Состояние</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="358"/>
        <source>Created</source>
        <translation>Дата</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="110"/>
        <source>Log out</source>
        <translation>Выйти</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="141"/>
        <source>Delete</source>
        <translation>Удалить</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="895"/>
        <source>Output directory:</source>
        <translation>Рабочая папка:</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="488"/>
        <source>Max zoom:</source>
        <translation>Макс зум:</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="508"/>
        <source>Preview</source>
        <translation>Просмотр</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="517"/>
        <source>Use imagery provider credentials</source>
        <translation>Использовать реквизиты для провайдера</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="543"/>
        <source>Login:</source>
        <translation>Логин:</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="557"/>
        <source>Password:</source>
        <translation>Пароль:</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="573"/>
        <source>Save Login/Password</source>
        <translation>Запомнить</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="946"/>
        <source>Help</source>
        <translation>Помощь</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="196"/>
        <source>wms</source>
        <translation>wms</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="197"/>
        <source>postgresraster</source>
        <translation>postgresraster</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="198"/>
        <source>grassraster</source>
        <translation>grassraster</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="378"/>
        <source>Providers</source>
        <translation>Источники данных</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="350"/>
        <source>Area, sq. km</source>
        <translation>Площадь, кв. км</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="58"/>
        <source>Cached imagery will be reused if you&apos;ve previously processed the exact same area with the same imagery source</source>
        <translation type="obsolete">Снимки будут переиспользованы если вы уже обрабатывали по ним точно такую же область</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="61"/>
        <source>Use cache</source>
        <translation type="obsolete">Переиспользовать снимки</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="71"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#caching&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;How caching works&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation type="obsolete">&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href=&quot;https://ru.docs.mapflow.ai/api/qgis_mapflow#caching&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Как это работает&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="342"/>
        <source>Progress %</source>
        <translation>Прогресс %</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="474"/>
        <source>Image ID:</source>
        <translation>ID снимка:</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="481"/>
        <source>Select in the table below or paste here</source>
        <translation>Выберите в таблице ниже или вставьте сюда</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="586"/>
        <source>Provider Imagery Catalog</source>
        <translation>Каталог снимков</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="617"/>
        <source>Use canvas extent</source>
        <translation>Использовать охват экрана</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="631"/>
        <source>From:</source>
        <translation>С:</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="709"/>
        <source>yyyy-MM-dd</source>
        <translation>yyyy-MM-dd</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="675"/>
        <source>Search imagery</source>
        <translation>Искать снимки</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="685"/>
        <source>To:</source>
        <translation>По:</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="731"/>
        <source>Additional filters</source>
        <translation>Дополнительные фильтры</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="743"/>
        <source>Min intersection:</source>
        <translation>Минимальное пересечение:</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="820"/>
        <source>%</source>
        <translation>%</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="788"/>
        <source>Cloud cover up to:</source>
        <translation>Облачность не более:</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="887"/>
        <source>Settings</source>
        <translation>Настройки</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="412"/>
        <source>Add your own web imagery provider</source>
        <translation>Добавьте собственный источник снимков</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="583"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Here, you can search Maxar or Sentinel imagery for your area and timespan.&lt;/p&gt;&lt;p&gt;Additional filters are also available below.&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Здесь вы можете искать подходящие для ваших области и времени снимки Maxar и Sentinel-2.&lt;/p&gt;&lt;p&gt;Дополнительные параметры поиска находятся во вкладке ниже.&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="604"/>
        <source>Any (multi-)polygon(s)</source>
        <translation>Любые (мульти-)полигон(ы)</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="614"/>
        <source>Use your current screen area</source>
        <translation>Область ограниченная вашим экраном</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="628"/>
        <source>Earlier images won&apos;t be shown</source>
        <translation>Более ранние снимки не будут показаны</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="692"/>
        <source>Dates are inclusive</source>
        <translation>Даты включительны</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="672"/>
        <source>Click and wait for a few seconds until the table below is filled out</source>
        <translation>Нажмите и подождите несколько секунд пока данные загрузятся</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="682"/>
        <source>More recent images won&apos;t be shown</source>
        <translation>Более поздние снимки не будут показаны</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="728"/>
        <source>Click to specify additional search criteria</source>
        <translation>Нажмите чтобы указать дополнительные условия поиска</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="750"/>
        <source>Images that cover fewer % of your area won&apos;t be shown</source>
        <translation>Снимки покрывающие меньший % вашей области не будут показаны</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="847"/>
        <source>Double-click on a row to preview its image</source>
        <translation>Двойной щелчок мыши загрузит предпросмотр снимка</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="955"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=&quot; margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#user-interface&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;User Interface walkthrough&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#how-to-process-your-own-imagery&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;How to process your own image&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#how-to-use-other-imagery-services&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;How to use a different imagery tileset&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#how-to-connect-to-maxar-securewatch&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;How to connect to Maxar SecureWatch&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=&quot; margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow Agro&lt;/span&gt;&lt;/h3&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://agro.geoalert.io/&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;About&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow.html#sentinel-2&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Sentinel imagery&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/userguides/iterative_mapping.html&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Iterative mapping workflow for cropland maps&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;span style=&quot; font-weight:600;&quot;&gt;If you have a feature request or have spotted a bug,&lt;br/&gt;create an issue on our &lt;/span&gt;&lt;a href=&quot;https://github.com/Geoalert/mapflow-qgis&quot;&gt;&lt;span style=&quot; font-weight:600; text-decoration: underline; color:#0000ff;&quot;&gt;GitHub&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=&quot; margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://ru.docs.mapflow.ai/api/qgis_mapflow#user-interface&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Пользовательский интерфейс&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://ru.docs.mapflow.ai/api/qgis_mapflow#id19&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Как использовать собственный снимок для обработки&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://ru.docs.mapflow.ai/api/qgis_mapflow#id17&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Как использовать снимки из других источников&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://ru.docs.mapflow.ai/api/qgis_mapflow#maxar-securewatch&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Как подключить Maxar SecureWatch&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=&quot; margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow Agro&lt;/span&gt;&lt;/h3&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://agro.geoalert.io/&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;О проекте&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://ru.docs.mapflow.ai/api/qgis_mapflow.html#sentinel-2&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Снимки Sentinel&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://ru.docs.mapflow.ai/userguides/iterative_mapping.html&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Пошаговый способ картирования полей&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;span style=&quot; font-weight:600;&quot;&gt;Если у вас есть предложения или замечания по работе плагина,&lt;br/&gt;мы будем рады если вы создадите задачу на нашем &lt;/span&gt;&lt;a href=&quot;https://github.com/Geoalert/mapflow-qgis&quot;&gt;&lt;span style=&quot; font-weight:600; text-decoration: underline; color:#0000ff;&quot;&gt;GitHub&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="238"/>
        <source>Create or load vector layer with your area of interest</source>
        <translation>Создать или загрузить векторный слой с вашей областью интереса</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="260"/>
        <source>...</source>
        <translation>...</translation>
    </message>
</context>
<context>
    <name>Mapflow</name>
    <message>
        <location filename="../mapflow.py" line="265"/>
        <source>Currently, Mapflow doesn&apos;t support uploading own Sentinel-2 imagery. To process Sentinel-2, go to the Providers tab and either search for your image in the catalog or paste its ID in the Image ID field.</source>
        <translation>Mapflow пока не поддерживает загрузку пользовательских снимков Sentinel-2. Чтобы обработать Sentinel-2, пожалуйста, перейдите во вкладку &quot;Источники данных&quot; и либо найдите ваш снимок в каталоге либо вставьте его ID в поле &quot;ID Снимка&quot;.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="349"/>
        <source>Log in</source>
        <translation>Вход</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="387"/>
        <source>If you already know which {provider_name} image you want to process,
simply paste its ID here. Otherwise, search suitable images in the catalog below.</source>
        <translation>Если вы уже знаете ID снимка {provider_name} который вы хотите обработать, просто вставьте его в это поле. Иначе, используйте каталог ниже чтобы найти подходящий снимок.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="398"/>
        <source>e.g. S2B_OPER_MSI_L1C_TL_VGS4_20220209T091044_A025744_T36SXA_N04_00</source>
        <translation>например S2B_OPER_MSI_L1C_TL_VGS4_20220209T091044_A025744_T36SXA_N04_00</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="413"/>
        <source>e.g. a3b154c40cc74f3b934c0ffc9b34ecd1</source>
        <translation>например a3b154c40cc74f3b934c0ffc9b34ecd1</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="426"/>
        <source>Leave this field empty for </source>
        <translation>Оставьте это поле пустым для </translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="428"/>
        <source> doesn&apos;t allow processing single images.</source>
        <translation> не поддерживает обработку отдельных снимков.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="443"/>
        <source> Imagery Catalog</source>
        <translation> - Каталог снимков</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="489"/>
        <source>Permanently remove {}?</source>
        <translation>Удалить {}?</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="604"/>
        <source>Select output directory</source>
        <translation>Выберите папку для сохранения данных</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="620"/>
        <source>Please, specify an existing output directory</source>
        <translation>Пожалуйста, выберите папку для сохранения данных</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="628"/>
        <source>Select GeoTIFF</source>
        <translation>Выберите GeoTIFF</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1362"/>
        <source>Please, select an area of interest</source>
        <translation>Пожалуйста, выберите слой с областью обработки</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="684"/>
        <source>Your area of interest is too large.</source>
        <translation>Слишком большая область запроса метаданных.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1124"/>
        <source>Please, check your credentials</source>
        <translation>Пожалуйста, проверьте реквизиты</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="943"/>
        <source>We couldn&apos;t fetch Sentinel metadata</source>
        <translation>Мы не смогли получить метаданные Сентинел</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1064"/>
        <source>No images match your criteria. Try relaxing the filters.</source>
        <translation>Нет подходящий снимков. Попробуйте изменить параметры поиска.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="912"/>
        <source>More</source>
        <translation>Еще</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1126"/>
        <source>We couldn&apos;t get metadata from Maxar</source>
        <translation>Мы не смогли получить метаданные от Максар</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1199"/>
        <source>A Sentinel image ID should look like S2B_OPER_MSI_L1C_TL_VGS4_20220209T091044_A025744_T36SXA_N04_00 or /36/S/XA/2022/02/09/0/</source>
        <translation>ID снимка Sentinel должен иметь формат S2B_OPER_MSI_L1C_TL_VGS4_20220209T091044_A025744_T36SXA_N04_00 или /36/S/XA/2022/02/09/0/</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1286"/>
        <source>Area: {:.2f} sq.km</source>
        <translation>Площадь: {:.2f} кв.км</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1301"/>
        <source>Delete selected processings?</source>
        <translation>Удалить выбранные обработки?</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1326"/>
        <source>Error deleting a processing</source>
        <translation>Ошибка удаления обработки</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1353"/>
        <source>Please, specify a name for your processing</source>
        <translation>Пожалуйста, выберите название обработки</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1358"/>
        <source>GeoTIFF has invalid projection</source>
        <translation>Мы не смогли распознать проекцию снимка</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1360"/>
        <source>Processing area has invalid projection</source>
        <translation>Мы не смогли распознать проекцию области обработки</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1366"/>
        <source>Processing limit exceeded</source>
        <translation>Превышен доступный лимит обработки</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1369"/>
        <source>Up to {} sq km can be processed at a time. Try splitting your area(s) into several processings.</source>
        <translation>За раз можно обработать не более {} кв км. Попробуйте разделить область обработки на части.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1378"/>
        <source>Click on the link below to send us an email</source>
        <translation>Нажмите на ссылку ниже чтобы отправить нам отчет об ошибке</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1378"/>
        <source>Upgrade your subscription to process Maxar imagery</source>
        <translation>Чтобы обрабатывать по Максар, нужно стать Премиум пользователем Mapflow</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1378"/>
        <source>I&apos;d like to upgrade my subscription to Mapflow Processing API to be able to process Maxar imagery.</source>
        <translation>Я хотел бы стать премиум пользователем Mapflow чтобы обрабатывать по Максар.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1409"/>
        <source>Search the Sentinel-2 catalog for a suitable image</source>
        <translation>Выберите подходящий снимок Sentinel-2 в каталоге</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1445"/>
        <source>Image and processing area do not intersect</source>
        <translation>Снимок и область обработки не пересекаются</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1448"/>
        <source>Starting the processing...</source>
        <translation>Создаем обработку...</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1472"/>
        <source>Uploading image to Mapflow...</source>
        <translation>Загружаем ваш снимок на Mapflow...</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1505"/>
        <source>We couldn&apos;t upload your GeoTIFF</source>
        <translation>Мы не смогли загрузить ваш снимок</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1525"/>
        <source>Processing creation failed</source>
        <translation>Мы не смогли создать обработку</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1529"/>
        <source>Success! We&apos;ll notify you when the processing has finished.</source>
        <translation>Обработка создана! Мы оповестим вас когда она завершится.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1559"/>
        <source>Processing limit: {} sq.km</source>
        <translation>Доступный лимит: {} кв.км</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1620"/>
        <source>Sorry, we couldn&apos;t load the image</source>
        <translation>Ошибка предпросмотра снимка</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1621"/>
        <source>Error previewing Sentinel imagery</source>
        <translation>Ошибка предпросмотра снимка</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1629"/>
        <source>Sorry, there&apos;s no preview for this image</source>
        <translation>К сожалению, для этого снимка нет предпросмотра</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1717"/>
        <source>We couldn&apos;t load a preview for this image</source>
        <translation>Мы не смогли осуществить предпросмотр этого снимка</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1644"/>
        <source>Please, select an image to preview</source>
        <translation>Пожалуйста, выберите снимок</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1798"/>
        <source>Error loading results. Error code: </source>
        <translation>Ошибка загрузки результатов. Код ошибки: </translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1840"/>
        <source>Error downloading results</source>
        <translation>Мы не смогли скачать результаты обработки</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1871"/>
        <source>Error loading results</source>
        <translation>Мы не смогли загрузить результаты</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1907"/>
        <source> failed.
</source>
        <translation> завершилась с ошибкой.
</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1914"/>
        <source> finished. Double-click it in the table to download the results.</source>
        <translation> завершилась. Дважды кликните на нее в таблице чтобы загрузить результаты.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2040"/>
        <source>Can&apos;t log in to Mapflow</source>
        <translation>Мы не смогли подключиться к Mapflow</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2058"/>
        <source>Invalid token</source>
        <translation>Неверный токен</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2090"/>
        <source>Proxy error. Please, check your proxy settings.</source>
        <translation>Ошибка прокси. Пожалуйста, проверьте настройки прокси в QGIS.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2107"/>
        <source>Unknown error</source>
        <translation>Неизвестная ошибка</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2169"/>
        <source>There is a new version of Mapflow for QGIS available.
Please, upgrade to make sure everything works as expected. Go to Plugins -&gt; Manage and Install Plugins -&gt; Upgradable.</source>
        <translation>Пожалуйста, обновите версию плагина чтобы все работало как нужно. Модули -&gt; Управление модулями -&gt; Обновляемые.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="232"/>
        <source>Select vector file</source>
        <translation>Выберите векторный файл</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="197"/>
        <source>Create new AOI layer from map extent</source>
        <translation>Создать новый слой области интереса из видимой области карты</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="198"/>
        <source>Add AOI from vector file</source>
        <translation>Добавить AOI из векторного файла</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="244"/>
        <source>Your file is not valid vector data source!</source>
        <translation>Ваш файл не подходит как источник векторных данных!</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1955"/>
        <source>Double click to add results to the map</source>
        <translation>Двойной клик добавит результаты на карту</translation>
    </message>
</context>
<context>
    <name>ProviderDialog</name>
    <message>
        <location filename="../static/ui/provider_dialog.ui" line="43"/>
        <source>Name</source>
        <translation>Название</translation>
    </message>
    <message>
        <location filename="../static/ui/provider_dialog.ui" line="67"/>
        <source>Type</source>
        <translation>Тип</translation>
    </message>
</context>
<context>
    <name>QPlatformTheme</name>
    <message>
        <location filename="../mapflow.py" line="79"/>
        <source>Cancel</source>
        <translation>Отмена</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="80"/>
        <source>&amp;Yes</source>
        <translation>Да</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="81"/>
        <source>&amp;No</source>
        <translation>Нет</translation>
    </message>
</context>
<context>
    <name>SentinelAuthDialog</name>
    <message>
        <location filename="../static/ui/sentinel_auth_dialog.ui" line="35"/>
        <source>SkyWatch API Key</source>
        <translation>Ключ для SkyWatch API</translation>
    </message>
    <message>
        <location filename="../static/ui/sentinel_auth_dialog.ui" line="43"/>
        <source>API key:</source>
        <translation>Ключ API:</translation>
    </message>
</context>
</TS>
