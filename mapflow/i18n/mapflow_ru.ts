<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="ru_RU" sourcelanguage="en_US">
<context>
    <name>ApiErrors</name>
    <message>
        <location filename="../errors/api_errors.py" line="8"/>
        <source>Upgrade your subscription to get access to Maxar imagery</source>
        <translation>Перейдите на коммерческий план, чтобы получить доступ к изображениям Maxar</translation>
    </message>
</context>
<context>
    <name>DataErrors</name>
    <message>
        <location filename="../errors/data_errors.py" line="8"/>
        <source>File {filename} cannot be processed. Parameters {bad_parameters} are incompatible with our catalog. See the documentation for more info.</source>
        <translation>Файл {filename} не может быть обработан. Параметры {bad_parameters} не совместимы с нашим каталогом данных. См. документацию для подробной информации.</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="11"/>
        <source>Your file has size {memory_requested} bytes, but you have only {available_memory} left. Upgrade your subscription or remove older imagery from your catalog</source>
        <translation>Объем вашего файла {memory_requested} байтов, но у вас осталось только {available_memory} байтов. Обновите подписку или удалите старые изображения из каталога</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="14"/>
        <source>Max file size allowed to upload is {max_file_size} bytes, your file is {actual_file_size} bytes instead. Compress your file or cut it into smaller parts</source>
        <translation>Максимальный размер файла, разрешенный для загрузки, составляет {max_file_size} байт, размер вашего файла составляет {actual_file_size} байт. Сожмите файл или разрежьте его на более мелкие части</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="17"/>
        <source>{instance_type} with id: {uid} can&apos;t be found</source>
        <translation>{instance_type} с id {uid} не может быть найден</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="18"/>
        <source>You do not have access to {instance_type} with id {uid}</source>
        <translation>У вас нет доступа к {instance_type} с id {uid}</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="19"/>
        <source>File {filename} cannot be uploaded to mosaic: {mosaic_id}. {param_name} of the file is {got_param}, it should be {expected_param} to fit the mosaic. Fix your file, or upload it to another mosaic</source>
        <translation>Файл {filename} не может быть загружен в мозаику: {mosaic_id}. {param_name} файла {got_param}, однако для данной мозаики этот параметр должен быть следующим: {expected_param}. Исправьте ваш файл или загрузите в другую мозаику</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="23"/>
        <source>File can&apos;t be uploaded, because its extent is out of coordinate range.Check please CRS and transform of the image, they may be invalid</source>
        <translation>Файл не может быть загружен, так как его размер выходит за пределы диапазона координат. Проверьте, пожалуйста, координатную систему изображения, она может быть недействительным</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="25"/>
        <source>File cannot be opened as a GeoTIFF file. Only valid geotiff files are allowed for uploading. You can use Raster-&gt;Conversion-&gt;Translate to change your file type to GeoTIFF</source>
        <translation>Файл не может быть открыт как файл GeoTIFF. Для загрузки разрешены только действительные файлы GeoTIFF. Вы можете использовать Raster-&gt;Conversion-&gt;Translate, чтобы изменить тип файла на GeoTIFF</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="28"/>
        <source>File can&apos;t be uploaded, because the geometry of the image is too big, we will not be able to process it properly.Make sure that your image has valid CRS and transform, or cut the image into parts</source>
        <translation>Файл не может быть загружен, так как геометрия изображения слишком велика, мы не сможем его правильно обработать. Убедитесь, что ваше изображение имеет действующую CRS и преобразование, или разрежьте изображение на части</translation>
    </message>
</context>
<context>
    <name>ErrorMessage</name>
    <message>
        <location filename="../errors/errors.py" line="44"/>
        <source>
 Warning: some error parameters were not loaded : {}!</source>
        <translation>
 Внимание: часть параметров не были загружены: {}!</translation>
    </message>
    <message>
        <location filename="../errors/errors.py" line="36"/>
        <source>Unknown error while fetching processing errors: {exception}
 Error code: {code}
 Contact us to resolve the issue! help@geoalert.io</source>
        <translation type="obsolete">Неизвестная ошибка при загрузке ошибок обработки: {exception}
 Код ошибки: {}
 Свяжитесь с нами, мы поможем решить проблему! help@geoalert.io</translation>
    </message>
    <message>
        <location filename="../errors/errors.py" line="48"/>
        <source>Error {code}: {message}</source>
        <translation>Ошибка {code}: {message}</translation>
    </message>
    <message>
        <location filename="../errors/errors.py" line="50"/>
        <source>Unknown error while fetching errors: {exception}
 Error code: {code}
 Contact us to resolve the issue! help@geoalert.io</source>
        <translation>Неизвестная ошибка при получении информации: {exception}
Код ошибки: {code}
Напишите нам чтобы мы смогли исправить это! help@geoalert.io</translation>
    </message>
</context>
<context>
    <name>ErrorMessageList</name>
    <message>
        <location filename="../errors.py" line="20"/>
        <source>Key &apos;url&apos; in your request must be a string, got {url_type} instead.</source>
        <translation type="obsolete">Ключ &apos;url&apos; в запросе должен быть строкой, не {url_type}.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="25"/>
        <source>Your URL must be a link starting with &quot;http://&quot; or &quot;https://&quot;.</source>
        <translation type="obsolete">URL должен начинаться с &quot;http://&quot; или &quot;https://&quot;.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="27"/>
        <source>Format of &apos;url&apos; is invalid and cannot be parsed. Error: {parse_error_message}</source>
        <translation type="obsolete">Невалидный формат URL. Ошибка {parse_error_message}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="29"/>
        <source>Zoom must be either empty, or integer, got {actual_zoom}</source>
        <translation type="obsolete">Поле „zoom“ должно быть либо пустым, либо целым числом. Получено {actual_zoom}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="31"/>
        <source>Zoom must be between 0 and 22, got {actual_zoom}</source>
        <translation type="obsolete">Значение поля „zoom“ в вашем запросе должно быть в интервале от 0 до 22. Получено {actual_zoom}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="32"/>
        <source>Zoom must be not lower than {min_zoom}, got {actual_zoom}</source>
        <translation type="obsolete">Значение поля „zoom“ в вашем запросе должно быть не менее {min_zoom}. Получено {actual_zoom}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="33"/>
        <source>Image metadata must be a dict (json)</source>
        <translation type="obsolete">Метаданные вашего изображения должны быть типа &quot;словарь&quot; (json)</translation>
    </message>
    <message>
        <location filename="../errors.py" line="34"/>
        <source>Image metadata must have keys: crs, transform, dtype, count</source>
        <translation type="obsolete">Метаданные вашего изображения должны содержать ключи: crs, transform, dtype, count</translation>
    </message>
    <message>
        <location filename="../errors.py" line="36"/>
        <source>URL of the image at s3 storage must be a string starting with s3://, got {actual_s3_link}</source>
        <translation type="obsolete">URL изображения на хранилище S3 должен быть строкой и начинаться с S3://. Получено {actual_s3_link}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="38"/>
        <source>Request must contain either &apos;profile&apos; or &apos;url&apos; keys</source>
        <translation type="obsolete">Запрос должен содержать либо „profile“, либо „url“</translation>
    </message>
    <message>
        <location filename="../errors.py" line="39"/>
        <source>Failed to read file from {s3_link}.</source>
        <translation type="obsolete">Ошибка чтения файла из {s3_link}.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="40"/>
        <source>Image data type (Dtype) must be one of {required_dtypes}, got {request_dtype}</source>
        <translation type="obsolete">Тип данных изображения (Dtype) должен быть одним из {required_dtypes}. Получено {request_dtype}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="42"/>
        <source>Number of channels in image must be one of {required_nchannels}. Got {real_nchannels}</source>
        <translation type="obsolete">Изображение имеет {real_nchannels} каналов, требуемое количество каналов {required_nchannels}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="44"/>
        <source>Spatial resolution of you image is too high: pixel size is {actual_res}, minimum allowed pixel size is {min_res}</source>
        <translation type="obsolete">Пространственное разрешение вашего изображения слишком высокое: размер пикселя {actual_res}, минимальный допустимый размер пикселя равен {min_res}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="47"/>
        <source>Spatial resolution of you image is too low: pixel size is {actual_res}, maximum allowed pixel size is {max_res}</source>
        <translation type="obsolete">Пространственное разрешение вашего изображения слишком низкое: размер пикселя равен {actual_res}, максимально допустимый размер пикселя равен {max_res}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="50"/>
        <source>Error occurred during image {checked_param} check: {message}. Image metadata = {metadata}.</source>
        <translation type="obsolete">Ошибка произошла во время проверки параметра {checked_param} изображения: {message}. Метаданные изображения = {metadata}.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="52"/>
        <source>Your &apos;url&apos; doesn&apos;t match the format, Quadkey basemap must be a link containing &quot;q&quot; placeholder.</source>
        <translation type="obsolete">Ссылка на Quadkey подложку не соответствует формату. Это должна быть ссылка, содержащая поле «q».</translation>
    </message>
    <message>
        <location filename="../errors.py" line="55"/>
        <source>Input string {input_string} is of unknown format. It must represent Sentinel-2 granule ID.</source>
        <translation type="obsolete">Строка {input_string} неизвестного формата. Она должна представлять собой ID гранулы снимка Sentinel-2.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="57"/>
        <source>Selected Sentinel-2 image cell is {actual_cell}, this model is for the cells: {allowed_cells}</source>
        <translation type="obsolete">Выбранная ячейка {actual_cell} не подходит для обработки, модель рассчитана на ячейки: {allowed_cells}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="59"/>
        <source>Selected Sentinel-2 image month is {actual_month}, this model is for: {allowed_months}</source>
        <translation type="obsolete">Выбранный месяц {actual_month} не подходит для обработки, модель рассчитана на месяцы: {allowed_months}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="60"/>
        <source>You request TMS basemap link doesn&apos;t match the format, it must be a link containing &apos;{x}&apos;, &apos;{y}&apos;, &apos;{z}&apos; placeholders, correct it and start processing again.</source>
        <translation type="obsolete">Ссылка на TMS подложку не соответствует формату. Это должна быть ссылка, содержащая поля &quot;{x}&quot;, &quot;{y}&quot;, &quot;{z}&quot;.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="64"/>
        <source>Requirements must be dict, got {requirements_type}.</source>
        <translation type="obsolete">Секция «requirements» в запросе должна быть словарем (dict), а не {requirements_type}.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="65"/>
        <source>Request must be dict, got {request_type}.</source>
        <translation type="obsolete">Секция «request» в запросе должна быть словарем (dict), а не {request_type}.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="66"/>
        <source>Request must contain &quot;source_type&quot; key</source>
        <translation type="obsolete">Запрос должен содержать тип источника спутниковых снимков (ключ «source_type»)</translation>
    </message>
    <message>
        <location filename="../errors.py" line="67"/>
        <source>Source type {source_type} is not allowed. Use one of: {allowed_sources}</source>
        <translation type="obsolete">Источник данных {source_type}, не поддерживется платформой. Ипользуйте один из разрешенных: {allowed_sources}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="69"/>
        <source>&quot;Required&quot; section of the requirements must contain dict, not {required_section_type}</source>
        <translation type="obsolete">Секция «Required» в требованиях к данным должна быть словарем (dict), а не {required_section_type}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="71"/>
        <source>&quot;Recommended&quot; section of the requirements must contain dict, not {recommended_section_type}</source>
        <translation type="obsolete">Секция «recommended» в требованиях к данным должна быть словарем (dict), а не {recommended_section_type}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="72"/>
        <source>You XYZ basemap link doesn&apos;t match the format, it must be a link containing &apos;{x}&apos;, &apos;{y}&apos;, &apos;{z}&apos; placeholders.</source>
        <translation type="obsolete">Ссылка на XYZ подложку не соответствует формату. Это должна быть ссылка, содержащая поля &quot;{x}&quot;, &quot;{y}&quot;, &quot;{z}&quot;.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="78"/>
        <source>Internal error in process of data source validation. We are working on the fix, our support will contact you.</source>
        <translation type="obsolete">Произошла ошибка в процессе проверки источника данных. Мы работаем над исправлением и свяжемся с вами.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="99"/>
        <source>Internal error in process of loading data. We are working on the fix, our support will contact you.</source>
        <translation type="obsolete">Произошла ошибка в процессе загрузки данных. Мы работаем над исправлением и свяжемся с вами.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="82"/>
        <source>Wrong source type {real_source_type}. Specify one of the allowed types {allowed_source_types}.</source>
        <translation type="obsolete">Неправильный тип источника данных {real_source_type}. Используйте один из допустимых {allowed_source_types}.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="84"/>
        <source>Your data loading task requires {estimated_size} MB of memory, which exceeded allowed memory limit {allowed_size}</source>
        <translation type="obsolete">Ваш запрос на загрузку данных требует {estimated_size} MB, что превышает лимит в {allowed_size}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="86"/>
        <source>Dataloader argument {argument_name} has type {argument_type}, excpected to be {expected_type}</source>
        <translation type="obsolete">Функция загрузки данных {argument_name} имеет тип {argument_type}, допустимый тип {expected_type}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="88"/>
        <source>Loaded tile has {real_nchannels} channels, required number is {expected_nchannels}</source>
        <translation type="obsolete">Загруженное изображение имеет {real_nchannels} каналов, требуемое количество каналов {expected_nchannels}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="90"/>
        <source>Loaded tile has size {real_size}, expected tile size is {expected_size}</source>
        <translation type="obsolete">Загруженное изображение имеет размер {real_size}, допустимый размер {expected_size}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="92"/>
        <source>Tile at location {tile_location} cannot be loaded, server response is {status}</source>
        <translation type="obsolete">Изображение по адресу {tile_location} не может быть загружено, ответ сервера {status}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="94"/>
        <source>Response content at {tile_location} cannot be decoded as an image</source>
        <translation type="obsolete">Ответ сервера {tile_location} не представляет собой изображение</translation>
    </message>
    <message>
        <location filename="../errors.py" line="101"/>
        <source>Internal error in process of data preparation. We are working on the fix, our support will contact you.</source>
        <translation type="obsolete">Произошла ошибка в процессе предобработки данных. Мы работаем над исправлением и свяжемся с вами.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="103"/>
        <source>Internal error in process of data processing. We are working on the fix, our support will contact you.</source>
        <translation type="obsolete">Произошла ошибка в процессе обработки данных. Мы работаем над исправлением и свяжемся с вами.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="105"/>
        <source>Internal error in process of saving the results. We are working on the fix, our support will contact you.</source>
        <translation type="obsolete">Произошла ошибка в процессе сохранения результатов обработки. Мы работаем над исправлением и свяжемся с вами.</translation>
    </message>
    <message>
        <location filename="../errors/error_message_list.py" line="16"/>
        <source>Unknown error. Contact us to resolve the issue! help@geoalert.io</source>
        <translation>Неизвестная ошибка. Свяжитесь с нами чтобы решить проблему! help@geoalert.io</translation>
    </message>
    <message>
        <location filename="../errors.py" line="17"/>
        <source>Image profile (metadata) must have keys {required_keys}, got profile {profile}</source>
        <translation type="obsolete">Метаданные изображения должны содержать следующие теги: {required_keys}, метаданные загруженного изображения: {profile}</translation>
    </message>
    <message>
        <location filename="../errors.py" line="14"/>
        <source>Task for source-validation must contain area of interest (`geometry` section)</source>
        <translation type="obsolete">Задача на проверку источника данных должна содержать область интереса (ключ `geometry`)</translation>
    </message>
    <message>
        <location filename="../errors.py" line="16"/>
        <source>We could not open and read the image you have uploaded</source>
        <translation type="obsolete">Мы не смогли открыть и прочитать загруженное изображение</translation>
    </message>
    <message>
        <location filename="../errors.py" line="19"/>
        <source>AOI does not intersect the selected Sentinel-2 granule {actual_cell}</source>
        <translation type="obsolete">Области интереса не пересекает выбранное изображение Sentinel-2 (код ячейки {actual_cell} )</translation>
    </message>
    <message>
        <location filename="../errors.py" line="22"/>
        <source>The specified basemap {url} is forbidden for processing because it contains a map, not satellite image. Our models are suited for satellite imagery.</source>
        <translation type="obsolete">Указанная подложка {url} запрещена к обработке, так как содержит карту, а не спутниковый снимок. Наши модели предназначены для обработки спутниковых снимков.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="61"/>
        <source>You request TMS basemap link doesn&apos;t match the format, it must be a link containing &quot;x&quot;, &quot;y&quot;, &quot;z&quot; placeholders, correct it and start processing again.</source>
        <translation type="obsolete">Ссылка на TMS подложку не соответствует формату. Это должна быть ссылка, содержащая поля &quot;x&quot;, &quot;y&quot;, &quot;z&quot;.</translation>
    </message>
    <message>
        <location filename="../errors.py" line="73"/>
        <source>You XYZ basemap link doesn&apos;t match the format, it must be a link containing &quot;x&quot;, &quot;y&quot;, &quot;z&quot;  placeholders.</source>
        <translation type="obsolete">Ссылка на XYZ подложку не соответствует формату. Это должна быть ссылка, содержащая поля &quot;x&quot;, &quot;y&quot;, &quot;z&quot;.</translation>
    </message>
</context>
<context>
    <name>LoginDialog</name>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="32"/>
        <source>Mapflow - Log In</source>
        <translation>Mapflow - Авторизация</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="131"/>
        <source>Cancel</source>
        <translation>Отмена</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="138"/>
        <source>Log in</source>
        <translation>Вход</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="68"/>
        <source>Token</source>
        <translation>Токен</translation>
    </message>
    <message>
        <location filename="../static/ui/login_dialog.ui" line="59"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href=&quot;https://docs.mapflow.ai/userguides/mapflow_auth.html&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Need an account?&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;a href=&quot;https://mapflow.ai/terms-of-use-en.pdf&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Terms of use&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation type="obsolete">&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href=&quot;https://ru.docs.mapflow.ai/userguides/mapflow_auth.html&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Зарегистрироваться&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;a href=&quot;https://mapflow.ai/terms-of-use.pdf&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Условия использования&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="75"/>
        <source>This plugin is an interface to to the Mapflow.ai satellite image processing platform. You need to register an account to use it. </source>
        <translation>Этот плагин - интерфейс для работы с Mapflow.ai - платформой обработки спутниковых снимков. Чтобы его использовать, нужно зарегистрировать аккаунт. </translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="90"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href=&quot;https://app.mapflow.ai/account/api&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Get token&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;a href=&quot;https://mapflow.ai/terms-of-use-en.pdf&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Terms of use&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;Register at &lt;a href=&quot;https://mapflow.ai&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;mapflow.ai&lt;/span&gt;&lt;/a&gt; to use the plugin&lt;/p&gt;&lt;p&gt;&lt;br/&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href=&quot;https://app.mapflow.ai/account/api&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Получить токен&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;a href=&quot;https://mapflow.ai/terms-of-use.pdf&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Условия использования&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;Зарегистрируйтесь на &lt;a href=&quot;https://mapflow.ai&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;mapflow.ai&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt; чтобы использовать плагин&lt;/p&gt;&lt;p&gt;&lt;br/&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="53"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;span style=&quot; color:#ff0000;&quot;&gt;Authorization is not configured! &lt;/span&gt;&lt;/p&gt;&lt;p&gt;&lt;br/&gt;Setup authorization config &lt;br/&gt;and restart QGIS before login. &lt;br/&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow.html#oauth2_setup&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#094fd1;&quot;&gt;See documentation for help &lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;span style=&quot; color:#ff0000;&quot;&gt;Авторизация не настроена! &lt;/span&gt;&lt;/p&gt;&lt;p&gt;&lt;br/&gt;Настройте авторизацию &lt;br/&gt;и перезапустите QGIS.чтобы войти &lt;br/&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow.html#oauth2_setup&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#094fd1;&quot;&gt;См. документацию &lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="111"/>
        <source>Use Oauth2</source>
        <translation>Использовать Oauth2</translation>
    </message>
</context>
<context>
    <name>MainDialog</name>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="888"/>
        <source>Processing</source>
        <translation>Обработка</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="106"/>
        <source>Name:</source>
        <translation>Название:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1003"/>
        <source>Mapflow model:</source>
        <translation type="obsolete">Модель Mapflow:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="133"/>
        <source>Area:</source>
        <translation>Область:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1023"/>
        <source>Imagery source:</source>
        <translation type="obsolete">Данные ДЗЗ:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="189"/>
        <source>Use image extent</source>
        <translation>По изображению</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="573"/>
        <source>Start processing</source>
        <translation>Начать обработку</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1893"/>
        <source>Name</source>
        <translation>Название</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1794"/>
        <source>Model</source>
        <translation>Модель</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1810"/>
        <source>Status</source>
        <translation>Состояние</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1874"/>
        <source>Created</source>
        <translation>Дата</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="856"/>
        <source>Log out</source>
        <translation>Выйти</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1044"/>
        <source>Delete</source>
        <translation>Удалить</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2020"/>
        <source>Output directory:</source>
        <translation>Рабочая папка:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1571"/>
        <source>Max zoom:</source>
        <translation>Макс зум:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1591"/>
        <source>Preview</source>
        <translation>Просмотр</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="517"/>
        <source>Use imagery provider credentials</source>
        <translation type="obsolete">Использовать реквизиты для провайдера</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="543"/>
        <source>Login:</source>
        <translation type="obsolete">Логин:</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="557"/>
        <source>Password:</source>
        <translation type="obsolete">Пароль:</translation>
    </message>
    <message>
        <location filename="../static/ui/main_dialog.ui" line="573"/>
        <source>Save Login/Password</source>
        <translation type="obsolete">Запомнить</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2088"/>
        <source>Help</source>
        <translation>Помощь</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="260"/>
        <source>wms</source>
        <translation>wms</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="261"/>
        <source>postgresraster</source>
        <translation>postgresraster</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="262"/>
        <source>grassraster</source>
        <translation>grassraster</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="185"/>
        <source>Providers</source>
        <translation type="obsolete">Источники данных</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="960"/>
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
        <location filename="../dialogs/static/ui/main_dialog.ui" line="955"/>
        <source>Progress %</source>
        <translation>Прогресс %</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1066"/>
        <source>Image ID:</source>
        <translation>ID снимка:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1073"/>
        <source>Select in the table below or paste here</source>
        <translation>Выберите в таблице ниже или вставьте сюда</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1112"/>
        <source>Provider Imagery Catalog</source>
        <translation>Каталог снимков</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1286"/>
        <source>Use canvas extent</source>
        <translation>По видимой области</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1170"/>
        <source>From:</source>
        <translation>С:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1266"/>
        <source>yyyy-MM-dd</source>
        <translation>yyyy-MM-dd</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1128"/>
        <source>Search imagery</source>
        <translation type="obsolete">Искать снимки</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1242"/>
        <source>To:</source>
        <translation>По:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1320"/>
        <source>Additional filters</source>
        <translation>Дополнительные фильтры</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1332"/>
        <source>Min intersection:</source>
        <translation>Минимальное пересечение:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1409"/>
        <source>%</source>
        <translation>%</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1377"/>
        <source>Cloud cover up to:</source>
        <translation>Облачность не более:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1436"/>
        <source>Settings</source>
        <translation>Настройки</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1484"/>
        <source>Add your own web imagery provider</source>
        <translation>Добавьте собственный источник снимков</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1109"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Here, you can search Maxar or Sentinel imagery for your area and timespan.&lt;/p&gt;&lt;p&gt;Additional filters are also available below.&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Здесь вы можете искать подходящие для ваших области и времени снимки Maxar и Sentinel-2.&lt;/p&gt;&lt;p&gt;Дополнительные параметры поиска находятся во вкладке ниже.&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="602"/>
        <source>Any (multi-)polygon(s)</source>
        <translation type="obsolete">Любые (мульти-)полигон(ы)</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1283"/>
        <source>Use your current screen area</source>
        <translation>Область ограниченная вашим экраном</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1167"/>
        <source>Earlier images won&apos;t be shown</source>
        <translation>Более ранние снимки не будут показаны</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1249"/>
        <source>Dates are inclusive</source>
        <translation>Даты включительны</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1229"/>
        <source>Click and wait for a few seconds until the table below is filled out</source>
        <translation>Нажмите и подождите несколько секунд пока данные загрузятся</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1239"/>
        <source>More recent images won&apos;t be shown</source>
        <translation>Более поздние снимки не будут показаны</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1317"/>
        <source>Click to specify additional search criteria</source>
        <translation>Нажмите чтобы указать дополнительные условия поиска</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1339"/>
        <source>Images that cover fewer % of your area won&apos;t be shown</source>
        <translation>Снимки покрывающие меньший % вашей области не будут показаны</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1129"/>
        <source>Double-click on a row to preview its image</source>
        <translation>Двойной щелчок мыши загрузит предпросмотр снимка</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="917"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=&quot; margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#user-interface&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;User Interface walkthrough&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#how-to-process-your-own-imagery&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;How to process your own image&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#how-to-use-other-imagery-services&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;How to use a different imagery tileset&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#how-to-connect-to-maxar-securewatch&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;How to connect to Maxar SecureWatch&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=&quot; margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow Agro&lt;/span&gt;&lt;/h3&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://agro.geoalert.io/&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;About&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow.html#sentinel-2&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Sentinel imagery&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/userguides/iterative_mapping.html&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Iterative mapping workflow for cropland maps&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;span style=&quot; font-weight:600;&quot;&gt;If you have a feature request or have spotted a bug,&lt;br/&gt;create an issue on our &lt;/span&gt;&lt;a href=&quot;https://github.com/Geoalert/mapflow-qgis&quot;&gt;&lt;span style=&quot; font-weight:600; text-decoration: underline; color:#0000ff;&quot;&gt;GitHub&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation type="obsolete">&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=&quot; margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://ru.docs.mapflow.ai/api/qgis_mapflow#user-interface&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Пользовательский интерфейс&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://ru.docs.mapflow.ai/userguides/prices.html&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Тарифы&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://ru.docs.mapflow.ai/api/qgis_mapflow#id19&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Как использовать собственный снимок для обработки&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://ru.docs.mapflow.ai/api/qgis_mapflow#id17&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Как использовать снимки из других источников&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://ru.docs.mapflow.ai/api/qgis_mapflow#maxar-securewatch&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Как подключить Maxar SecureWatch&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=&quot; margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow Agro&lt;/span&gt;&lt;/h3&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://agro.geoalert.io/&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;О проекте&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://ru.docs.mapflow.ai/api/qgis_mapflow.html#sentinel-2&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Снимки Sentinel&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://ru.docs.mapflow.ai/userguides/iterative_mapping.html&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Пошаговый способ картирования полей&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;span style=&quot; font-weight:600;&quot;&gt;Если у вас есть предложения или замечания по работе плагина,&lt;br/&gt;мы будем рады если вы создадите задачу на нашем &lt;/span&gt;&lt;a href=&quot;https://github.com/Geoalert/mapflow-qgis&quot;&gt;&lt;span style=&quot; font-weight:600; text-decoration: underline; color:#0000ff;&quot;&gt;GitHub&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="140"/>
        <source>Create or load vector layer with your area of interest</source>
        <translation>Создать или загрузить векторный слой с вашей областью интереса</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="648"/>
        <source>...</source>
        <translation>...</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="920"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=&quot; margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#user-interface&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;User Interface walkthrough&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/userguides/prices.html#mapflow-qgis-pricing-model&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Pricing&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#how-to-process-your-own-imagery&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;How to process your own image&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#how-to-use-other-imagery-services&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;How to use a different imagery tileset&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#how-to-connect-to-maxar-securewatch&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;How to connect to Maxar SecureWatch&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=&quot; margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow Agro&lt;/span&gt;&lt;/h3&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://agro.geoalert.io/&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;About&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow.html#sentinel-2&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Sentinel imagery&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/userguides/iterative_mapping.html&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Iterative mapping workflow for cropland maps&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;span style=&quot; font-weight:600;&quot;&gt;If you have a feature request or have spotted a bug,&lt;br/&gt;create an issue on our &lt;/span&gt;&lt;a href=&quot;https://github.com/Geoalert/mapflow-qgis&quot;&gt;&lt;span style=&quot; font-weight:600; text-decoration: underline; color:#0000ff;&quot;&gt;GitHub&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation type="obsolete">&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=&quot; margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://ru.docs.mapflow.ai/api/qgis_mapflow#user-interface&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Пользовательский интерфейс&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://ru.docs.mapflow.ai/userguides/prices.html#mapflow-qgis-pricing-model&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Тарифы&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://ru.docs.mapflow.ai/api/qgis_mapflow#id19&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Как использовать собственный снимок для обработки&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://ru.docs.mapflow.ai/api/qgis_mapflow#id17&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Как использовать снимки из других источников&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://ru.docs.mapflow.ai/api/qgis_mapflow#maxar-securewatch&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Как подключить Maxar SecureWatch&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=&quot; margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow Agro&lt;/span&gt;&lt;/h3&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://agro.geoalert.io/&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;О проекте&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://ru.docs.mapflow.ai/api/qgis_mapflow.html#sentinel-2&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Снимки Sentinel&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://ru.docs.mapflow.ai/userguides/iterative_mapping.html&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Пошаговый способ картирования полей&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;span style=&quot; font-weight:600;&quot;&gt;Если у вас есть предложения или замечания по работе плагина,&lt;br/&gt;мы будем рады если вы создадите задачу на нашем &lt;/span&gt;&lt;a href=&quot;https://github.com/Geoalert/mapflow-qgis&quot;&gt;&lt;span style=&quot; font-weight:600; text-decoration: underline; color:#0000ff;&quot;&gt;GitHub&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="990"/>
        <source>View results</source>
        <translation>Просмотр результатов</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="754"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=&quot; margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#user-interface&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;User Interface walkthrough&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/userguides/prices.html#mapflow-qgis-pricing-model&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Pricing&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow.html#how-to-upload-your-image&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;How to process your own image&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#how-to-use-other-imagery-services&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;How to use a different imagery tileset&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#how-to-connect-to-maxar-securewatch&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;How to connect to Maxar SecureWatch&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=&quot; margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow Agro&lt;/span&gt;&lt;/h3&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://agro.geoalert.io/&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;About&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow.html#sentinel-2&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Sentinel imagery&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/userguides/iterative_mapping.html&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Iterative mapping workflow for cropland maps&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;span style=&quot; font-weight:600;&quot;&gt;If you have a feature request or have spotted a bug,&lt;br/&gt;create an issue on our &lt;/span&gt;&lt;a href=&quot;https://github.com/Geoalert/mapflow-qgis&quot;&gt;&lt;span style=&quot; font-weight:600; text-decoration: underline; color:#0000ff;&quot;&gt;GitHub&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation type="obsolete">&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=&quot; margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#user-interface&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Пользовательский интерфейс&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/userguides/prices.html#mapflow-qgis-pricing-model&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Тарифы&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow.html#how-to-upload-your-image&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Как использовать собственный снимок для обработки&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#how-to-use-other-imagery-services&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Как использовать снимки из других источников&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#how-to-connect-to-maxar-securewatch&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Как подключить Maxar SecureWatch&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=&quot; margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow Agro&lt;/span&gt;&lt;/h3&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://agro.geoalert.io/&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;О проекте&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow.html#sentinel-2&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Снимки Sentinel&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/userguides/iterative_mapping.html&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Пошаговый способ картирования полей&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;span style=&quot; font-weight:600;&quot;&gt;Если у вас есть предложения или замечания по работе плагина,&lt;br/&gt;мы будем рады если вы создадите задачу на нашем &lt;/span&gt;&lt;a href=&quot;https://github.com/Geoalert/mapflow-qgis&quot;&gt;&lt;span style=&quot; font-weight:600; text-decoration: underline; color:#0000ff;&quot;&gt;GitHub&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="47"/>
        <source>Processing name:</source>
        <translation type="obsolete">Название обработки:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1284"/>
        <source>Rate processing</source>
        <translation type="obsolete">Оценить обработку</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="340"/>
        <source>Please select processing and rating to submit</source>
        <translation>Пожалуйста, выберите обработку и оценку для отправки</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1305"/>
        <source>Submit</source>
        <translation type="obsolete">Отправить</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1375"/>
        <source>1</source>
        <translation type="obsolete">1</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1382"/>
        <source>2</source>
        <translation type="obsolete">2</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1389"/>
        <source>3</source>
        <translation type="obsolete">3</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1396"/>
        <source>4</source>
        <translation type="obsolete">4</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1403"/>
        <source>5</source>
        <translation type="obsolete">5</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1426"/>
        <source>Type your feedback here</source>
        <translation type="obsolete">Введите свой отзыв здесь</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="189"/>
        <source>Top up balance</source>
        <translation type="obsolete">Пополнить</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="389"/>
        <source>AI model:</source>
        <translation>Модель:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="436"/>
        <source>Price of the processing per sq.km</source>
        <translation>Цена обработки за кв.км</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="417"/>
        <source>CC</source>
        <translation>СС</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="439"/>
        <source>10</source>
        <translation>10</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="508"/>
        <source>Ctrl+S</source>
        <translation></translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="231"/>
        <source>Data source:</source>
        <translation>Данные:</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="456"/>
        <source>Rate processing:</source>
        <translation>Оцените обработку:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="653"/>
        <source>⭐⭐⭐⭐⭐</source>
        <translation>⭐⭐⭐⭐⭐</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="658"/>
        <source>⭐⭐⭐⭐</source>
        <translation>⭐⭐⭐⭐</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="663"/>
        <source>⭐⭐⭐</source>
        <translation>⭐⭐⭐</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="668"/>
        <source>⭐⭐</source>
        <translation>⭐⭐</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="673"/>
        <source>⭐</source>
        <translation>⭐</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="701"/>
        <source>Share your thoughts on what aspects of this data processing work well or could be improved</source>
        <translation>Поделитесь с нами, что вам понравилось в этой обработке, а что можно было бы улучшить</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="750"/>
        <source>Submit feedback</source>
        <translation>Отправить отзыв</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1058"/>
        <source>Imagery search</source>
        <translation>Поиск снимков</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1114"/>
        <source>User profile</source>
        <translation type="obsolete">Профиль пользователя</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1120"/>
        <source>Manage your Mapflow account</source>
        <translation type="obsolete">Упаравление вашим аккаунтом Mapflow</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="797"/>
        <source>Your balance:</source>
        <translation>Ваш баланс:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="810"/>
        <source> Top up balance </source>
        <translation> Пополнить баланс </translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="827"/>
        <source>Open billing history</source>
        <translation>Открыть историю</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1267"/>
        <source>Edit imagery providers available to the plugin</source>
        <translation type="obsolete">Настройка провайдеров данных, доступных в плагине</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1276"/>
        <source>Imagery providers:</source>
        <translation type="obsolete">Провайдеры данных:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2005"/>
        <source>Set up local working directory, where all the temporary files will be stored</source>
        <translation>Настройка рабочей папки на вашем компьютере, где будут храниться все временные файлы</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1451"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=&quot; margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#user-interface&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;User Interface walkthrough&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow.html#how-to-upload-your-image&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;How to process your own image&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#how-to-use-other-imagery-services&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;How to use a different imagery tileset (XYZ or TMS)&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#how-to-connect-to-maxar-securewatch&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;How to connect to Maxar SecureWatch&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=&quot; margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow Pricing&lt;/span&gt;&lt;/h3&gt;&lt;p align=&quot;center&quot;&gt;&lt;br/&gt;&lt;/p&gt;&lt;table border=&quot;0&quot; style=&quot; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;&quot; align=&quot;center&quot; cellspacing=&quot;2&quot; cellpadding=&quot;0&quot;&gt;&lt;thead&gt;&lt;tr&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:700;&quot;&gt;Billing plan&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:700;&quot;&gt;$50&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:700;&quot;&gt;$90&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:700;&quot;&gt;$800&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/thead&gt;&lt;tr&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;Default or user custom imagery, km²&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;50&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;100&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;1000&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;tr&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;Premium satellite imagery, km²&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;10&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;20&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;200&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/table&gt;&lt;p&gt;See also – &lt;a href=&quot;https://docs.mapflow.ai/faq.html&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#094fd1;&quot;&gt;*How to buy credits for using the platform? How much is it?*&lt;/span&gt;&lt;/a&gt;&lt;br/&gt;&lt;/p&gt;&lt;h3 style=&quot; margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Join the project on Github&lt;/span&gt;&lt;/h3&gt;&lt;p&gt;&lt;span style=&quot; font-weight:600;&quot;&gt;If you have a feature request or spotted a bug,&lt;br/&gt;create an issue on &lt;/span&gt;&lt;a href=&quot;https://github.com/Geoalert/mapflow-qgis&quot;&gt;&lt;span style=&quot; font-weight:600; text-decoration: underline; color:#0000ff;&quot;&gt;GitHub&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation type="obsolete">&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=&quot; margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#user-interface&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Руководство по интерфейсу пользователя&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow.html#how-to-upload-your-image&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Как обработать ваше изображение&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#how-to-use-other-imagery-services&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Как использовать сторонний тайловый сервис (XYZ или TMS)&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#how-to-connect-to-maxar-securewatch&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Как подключиться к Maxar SecureWatch&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=&quot; margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Цены&lt;/span&gt;&lt;/h3&gt;&lt;p align=&quot;center&quot;&gt;&lt;br/&gt;&lt;/p&gt;&lt;table border=&quot;0&quot; style=&quot; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;&quot; align=&quot;center&quot; cellspacing=&quot;2&quot; cellpadding=&quot;0&quot;&gt;&lt;thead&gt;&lt;tr&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:700;&quot;&gt;Тариф&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:700;&quot;&gt;$50&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:700;&quot;&gt;$90&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:700;&quot;&gt;$800&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/thead&gt;&lt;tr&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;Базовое покрытие или ваши данные, км²&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;50&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;100&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;1000&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;tr&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt; Снимки коммерческих провайдеров, км²&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;10&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;20&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;200&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/table&gt;&lt;p&gt;См. также – &lt;a href=&quot;https://docs.mapflow.ai/faq.html&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#094fd1;&quot;&gt;*Как купить кредиты? Сколько это стоит?*&lt;/span&gt;&lt;/a&gt;&lt;br/&gt;&lt;/p&gt;&lt;h3 style=&quot; margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Присоединиться к проекту на Github&lt;/span&gt;&lt;/h3&gt;&lt;p&gt;&lt;span style=&quot; font-weight:600;&quot;&gt;Если у вас есть предложение или сообщение об ошибке,&lt;br/&gt;создайте issue на &lt;/span&gt;&lt;a href=&quot;https://github.com/Geoalert/mapflow-qgis&quot;&gt;&lt;span style=&quot; font-weight:600; text-decoration: underline; color:#0000ff;&quot;&gt;GitHub&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1878"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=&quot; margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#user-interface&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;User Interface walkthrough&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow.html#how-to-upload-your-image&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;How to process your own image&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#how-to-use-other-imagery-services&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;How to use a different imagery tileset (XYZ or TMS)&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#how-to-connect-to-maxar-securewatch&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;How to connect to Maxar SecureWatch&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=&quot; margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow credits&lt;/span&gt;&lt;span style=&quot; font-size:large; font-weight:700;&quot;&gt;&lt;br/&gt;&lt;/span&gt;&lt;/h3&gt;&lt;table border=&quot;0&quot; style=&quot; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;&quot; align=&quot;center&quot; cellspacing=&quot;2&quot; cellpadding=&quot;0&quot;&gt;&lt;thead&gt;&lt;tr&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:600;&quot;&gt;Pay as you go&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:696;&quot;&gt;$50&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:696;&quot;&gt;$90&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:696;&quot;&gt;$800&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/thead&gt;&lt;tr&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;Credits for processing&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;500&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;1000&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;10000&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/table&gt;&lt;p&gt;See also – &lt;a href=&quot;https://docs.mapflow.ai/userguides/prices.html&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#094fd1;&quot;&gt;*How much do the processings and data cost?*&lt;/span&gt;&lt;/a&gt;&lt;br/&gt;&lt;/p&gt;&lt;h3 style=&quot; margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Join the project on &lt;a href=&quot;https://github.com/Geoalert/mapflow-qgis&quot;&gt;&lt;span style=&quot; font-weight:600; text-decoration: underline; color:#0000ff;&quot;&gt;GitHub&lt;/span&gt;&lt;/a&gt; or &lt;a href=&quot;https://github.com/Geoalert/mapflow-qgis/issues&quot;&gt;&lt;span style=&quot; font-weight:600; text-decoration: underline; color:#0000ff;&quot;&gt;report an issue&lt;/span&gt;&lt;/a&gt;&lt;/span&gt;&lt;/h3&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation type="obsolete">&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=&quot; margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#user-interface&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Описание пользовательского интерфейса&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow.html#how-to-upload-your-image&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Как загрузить и обработать свои данные&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#how-to-use-other-imagery-services&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Как использовать другие тайловые сервисы (XYZ или TMS)&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#how-to-connect-to-maxar-securewatch&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Как подключиться к Maxar SecureWatch&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=&quot; margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow credits&lt;/span&gt;&lt;span style=&quot; font-size:large; font-weight:700;&quot;&gt;&lt;br/&gt;&lt;/span&gt;&lt;/h3&gt;&lt;table border=&quot;0&quot; style=&quot; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;&quot; align=&quot;center&quot; cellspacing=&quot;2&quot; cellpadding=&quot;0&quot;&gt;&lt;thead&gt;&lt;tr&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:600;&quot;&gt;Единовременная покупка&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:696;&quot;&gt;$50&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:696;&quot;&gt;$90&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:696;&quot;&gt;$800&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/thead&gt;&lt;tr&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;Количество кредитов&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;500&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;1000&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;10000&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/table&gt;&lt;p&gt;См. также – &lt;a href=&quot;https://docs.mapflow.ai/userguides/prices.html&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#094fd1;&quot;&gt;*Сколько стоят данные и их обработка?*&lt;/span&gt;&lt;/a&gt;&lt;br/&gt;&lt;/p&gt;&lt;h3 style=&quot; margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Присоединяйтесь к проекту на  &lt;a href=&quot;https://github.com/Geoalert/mapflow-qgis&quot;&gt;&lt;span style=&quot; font-weight:600; text-decoration: underline; color:#0000ff;&quot;&gt;GitHub&lt;/span&gt;&lt;/a&gt; или &lt;a href=&quot;https://github.com/Geoalert/mapflow-qgis/issues&quot;&gt;&lt;span style=&quot; font-weight:600; text-decoration: underline; color:#0000ff;&quot;&gt;сообщите об ошибке&lt;/span&gt;&lt;/a&gt;&lt;/span&gt;&lt;/h3&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="713"/>
        <source>Accept</source>
        <translation>Принять</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1909"/>
        <source>Review</source>
        <translation>Статус отзыва</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1858"/>
        <source>Cost</source>
        <translation>Стоимость</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="975"/>
        <source>Review until</source>
        <translation>Отзыв до</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1442"/>
        <source>Add or edit imagery providers:</source>
        <translation>Добавить или изменить провайдеров данных:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1720"/>
        <source>Configure processings table:</source>
        <translation>Настроить таблицу обработок:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1781"/>
        <source>Id</source>
        <translation>Id</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1826"/>
        <source>Area</source>
        <translation>Площадь</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1842"/>
        <source>Progress</source>
        <translation>Прогресс</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="522"/>
        <source>Model options: </source>
        <translation>Опции: </translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="104"/>
        <source>See details</source>
        <translation>Подробности</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="284"/>
        <source>Search </source>
        <translation>Искать </translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1310"/>
        <source>Clear </source>
        <translation>Очистить </translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1935"/>
        <source>Use all vector layers as Areas Of Interest</source>
        <translation>Добавлять все векторные слои</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="102"/>
        <source>Save results</source>
        <translation>Сохранить результаты</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1945"/>
        <source>view results as a vector layer</source>
        <translation>просмотр результатов в виде векторного слоя</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1958"/>
        <source>save local gpkg file to view results</source>
        <translation>сохранять локальный файл gpkg для просмотра результатов</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2097"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=&quot; margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#user-interface&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;User Interface walkthrough&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow.html#how-to-upload-your-image&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;How to process your own image&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#how-to-use-other-imagery-services&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;How to use a different imagery tileset (XYZ or TMS)&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#how-to-connect-to-maxar-securewatch&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;How to connect to Maxar SecureWatch&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=&quot; margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow credits&lt;/span&gt;&lt;span style=&quot; font-size:large; font-weight:700;&quot;&gt;&lt;br/&gt;&lt;/span&gt;&lt;/h3&gt;&lt;table border=&quot;0&quot; style=&quot; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;&quot; align=&quot;center&quot; cellspacing=&quot;2&quot; cellpadding=&quot;0&quot;&gt;&lt;thead&gt;&lt;tr&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:600;&quot;&gt;Pay as you go&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:696;&quot;&gt;$50&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:696;&quot;&gt;$90&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:696;&quot;&gt;$800&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/thead&gt;&lt;tr&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;Credits for processing&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;500&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;1000&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;10000&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/table&gt;&lt;p&gt;See also – &lt;a href=&quot;https://docs.mapflow.ai/userguides/prices.html&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#094fd1;&quot;&gt;How much do the processings and data cost?&lt;/span&gt;&lt;/a&gt;&lt;br/&gt;&lt;/p&gt;&lt;h3 style=&quot; margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Join the project on &lt;a href=&quot;https://github.com/Geoalert/mapflow-qgis&quot;&gt;&lt;span style=&quot; font-weight:600; text-decoration: underline; color:#0000ff;&quot;&gt;GitHub&lt;/span&gt;&lt;/a&gt; or &lt;a href=&quot;https://github.com/Geoalert/mapflow-qgis/issues&quot;&gt;&lt;span style=&quot; font-weight:600; text-decoration: underline; color:#0000ff;&quot;&gt;report an issue&lt;/span&gt;&lt;/a&gt;&lt;/span&gt;&lt;/h3&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=&quot; margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#user-interface&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Описание пользовательского интерфейса&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow.html#how-to-upload-your-image&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Как загрузить и обработать свои данные&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#how-to-use-other-imagery-services&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Как использовать другие тайловые сервисы (XYZ или TMS)&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#how-to-connect-to-maxar-securewatch&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Как подключиться к Maxar SecureWatch&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=&quot; margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow credits&lt;/span&gt;&lt;span style=&quot; font-size:large; font-weight:700;&quot;&gt;&lt;br/&gt;&lt;/span&gt;&lt;/h3&gt;&lt;table border=&quot;0&quot; style=&quot; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;&quot; align=&quot;center&quot; cellspacing=&quot;2&quot; cellpadding=&quot;0&quot;&gt;&lt;thead&gt;&lt;tr&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:600;&quot;&gt;Единовременная покупка&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:696;&quot;&gt;$50&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:696;&quot;&gt;$90&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:696;&quot;&gt;$800&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/thead&gt;&lt;tr&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;Количество кредитов&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;500&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;1000&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;10000&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/table&gt;&lt;p&gt;См. также – &lt;a href=&quot;https://docs.mapflow.ai/userguides/prices.html&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#094fd1;&quot;&gt;Сколько стоят данные и их обработка?&lt;/span&gt;&lt;/a&gt;&lt;br/&gt;&lt;/p&gt;&lt;h3 style=&quot; margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Присоединяйтесь к проекту на  &lt;a href=&quot;https://github.com/Geoalert/mapflow-qgis&quot;&gt;&lt;span style=&quot; font-weight:600; text-decoration: underline; color:#0000ff;&quot;&gt;GitHub&lt;/span&gt;&lt;/a&gt; или &lt;a href=&quot;https://github.com/Geoalert/mapflow-qgis/issues&quot;&gt;&lt;span style=&quot; font-weight:600; text-decoration: underline; color:#0000ff;&quot;&gt;сообщите об ошибке&lt;/span&gt;&lt;/a&gt;&lt;/span&gt;&lt;/h3&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1623"/>
        <source>Select Mapflow project:</source>
        <translation>Выберите проект:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2121"/>
        <source>see_details_action</source>
        <translation>see_details_action</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="301"/>
        <source>
Price: {} credits per square km</source>
        <translation>
Цена: {} кредитов за кв.км</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="312"/>
        <source>Rate processing &lt;b&gt;{name}&lt;/b&gt;:</source>
        <translation>Оценить процессинг &lt;b&gt;{name}&lt;/b&gt;:</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="425"/>
        <source>You can&apos;t remove or modify default project</source>
        <translation>Нельзя удалять или менять проект по умолчанию</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="465"/>
        <source>Not enough rights to delete processing in a shared project ({})</source>
        <translation>Недостаточно прав для удаления проекта ({})</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="276"/>
        <source>Zoom</source>
        <translation type="unfinished">Масштабный уровень</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="289"/>
        <source> –</source>
        <translation></translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="294"/>
        <source>14</source>
        <translation></translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="299"/>
        <source>15</source>
        <translation></translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="304"/>
        <source>16</source>
        <translation></translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="309"/>
        <source>17</source>
        <translation></translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="314"/>
        <source>18</source>
        <translation></translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="319"/>
        <source>19</source>
        <translation></translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="324"/>
        <source>20</source>
        <translation></translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="103"/>
        <source>Download AOI</source>
        <translation>Скачать область интереса</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="105"/>
        <source>Rename</source>
        <translation>Переименовать</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="446"/>
        <source>Not enough rights to start processing in a shared project ({})</source>
        <translation>Недостаточно прав в проекте для запауска обработки ({})</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="459"/>
        <source>Not enough rights to rate processing in a shared project ({})</source>
        <translation>Недостаточно прав в проекте для оценивания обработки ({})</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="461"/>
        <source>Please select processing</source>
        <translation>Пожалуйста, выберите обработку</translation>
    </message>
</context>
<context>
    <name>Mapflow</name>
    <message>
        <location filename="../mapflow.py" line="277"/>
        <source>Currently, Mapflow doesn&apos;t support uploading own Sentinel-2 imagery. To process Sentinel-2, go to the Providers tab and either search for your image in the catalog or paste its ID in the Image ID field.</source>
        <translation type="obsolete">Mapflow пока не поддерживает загрузку пользовательских снимков Sentinel-2. Чтобы обработать Sentinel-2, пожалуйста, перейдите во вкладку &quot;Источники данных&quot; и либо найдите ваш снимок в каталоге либо вставьте его ID в поле &quot;ID Снимка&quot;.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="394"/>
        <source>Log in</source>
        <translation type="obsolete">Вход</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="833"/>
        <source>If you already know which {provider_name} image you want to process,
simply paste its ID here. Otherwise, search suitable images in the catalog below.</source>
        <translation>Если вы уже знаете ID снимка {provider_name} который вы хотите обработать,
просто вставьте его в это поле. Иначе, используйте каталог ниже чтобы найти подходящий снимок.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="825"/>
        <source>e.g. S2B_OPER_MSI_L1C_TL_VGS4_20220209T091044_A025744_T36SXA_N04_00</source>
        <translation>например S2B_OPER_MSI_L1C_TL_VGS4_20220209T091044_A025744_T36SXA_N04_00</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="837"/>
        <source>e.g. a3b154c40cc74f3b934c0ffc9b34ecd1</source>
        <translation>например a3b154c40cc74f3b934c0ffc9b34ecd1</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="464"/>
        <source>Leave this field empty for </source>
        <translation type="obsolete">Оставьте это поле пустым для </translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="466"/>
        <source> doesn&apos;t allow processing single images.</source>
        <translation type="obsolete"> не поддерживает обработку отдельных снимков.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="480"/>
        <source> Imagery Catalog</source>
        <translation type="obsolete"> - Каталог снимков</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="713"/>
        <source>Permanently remove {}?</source>
        <translation>Удалить {}?</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="866"/>
        <source>Select output directory</source>
        <translation>Выберите папку для сохранения данных</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="882"/>
        <source>Please, specify an existing output directory</source>
        <translation>Пожалуйста, выберите папку для сохранения данных</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="653"/>
        <source>Select GeoTIFF</source>
        <translation type="obsolete">Выберите GeoTIFF</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1643"/>
        <source>Please, select an area of interest</source>
        <translation type="obsolete">Пожалуйста, выберите слой с областью обработки</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1077"/>
        <source>Your area of interest is too large.</source>
        <translation>Слишком большая область запроса метаданных.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1180"/>
        <source>Please, check your credentials</source>
        <translation>Пожалуйста, проверьте реквизиты</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1330"/>
        <source>We couldn&apos;t fetch Sentinel metadata</source>
        <translation>Мы не смогли получить метаданные Сентинел</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1387"/>
        <source>No images match your criteria. Try relaxing the filters.</source>
        <translation>Нет подходящий снимков. Попробуйте изменить параметры поиска.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1297"/>
        <source>More</source>
        <translation>Еще</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1057"/>
        <source>We couldn&apos;t get metadata from Maxar</source>
        <translation type="obsolete">Мы не смогли получить метаданные от Максар</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1519"/>
        <source>A Sentinel image ID should look like S2B_OPER_MSI_L1C_TL_VGS4_20220209T091044_A025744_T36SXA_N04_00 or /36/S/XA/2022/02/09/0/</source>
        <translation>ID снимка Sentinel должен иметь формат S2B_OPER_MSI_L1C_TL_VGS4_20220209T091044_A025744_T36SXA_N04_00 или /36/S/XA/2022/02/09/0/</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1649"/>
        <source>Area: {:.2f} sq.km</source>
        <translation>Площадь: {:.2f} кв.км</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1716"/>
        <source>Delete selected processings?</source>
        <translation>Удалить выбранные обработки?</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1742"/>
        <source>Error deleting a processing</source>
        <translation>Ошибка при удалении обработки</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1806"/>
        <source>Please, specify a name for your processing</source>
        <translation>Пожалуйста, выберите название обработки</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1352"/>
        <source>GeoTIFF has invalid projection</source>
        <translation type="obsolete">Мы не смогли распознать проекцию снимка</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1354"/>
        <source>Processing area has invalid projection</source>
        <translation type="obsolete">Мы не смогли распознать проекцию области обработки</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1816"/>
        <source>Up to {} sq km can be processed at a time. Try splitting your area(s) into several processings.</source>
        <translation>За раз можно обработать не более {} кв км. Попробуйте разделить область обработки на части.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1583"/>
        <source>Click on the link below to send us an email</source>
        <translation type="obsolete">Нажмите на ссылку ниже чтобы отправить нам отчет об ошибке</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1583"/>
        <source>Upgrade your subscription to process Maxar imagery</source>
        <translation type="obsolete">Чтобы обрабатывать по Максар, нужно стать Премиум пользователем Mapflow</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1583"/>
        <source>I&apos;d like to upgrade my subscription to Mapflow Processing API to be able to process Maxar imagery.</source>
        <translation type="obsolete">Я хотел бы стать премиум пользователем Mapflow чтобы обрабатывать по Максар.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1810"/>
        <source>GeoTIFF is corrupted or has invalid projection</source>
        <translation>Geotiff файл повржден или имеет некорректную проекцию</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1863"/>
        <source>Bad AOI. AOI must be inside boundaries: 
[-180, 180] by longitude, [-90, 90] by latitude</source>
        <translation>Неверный AOI. AOI должен быть в пределах:
[-180, 180] по долготе, [-90, 90] по широте</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1984"/>
        <source>Starting the processing...</source>
        <translation>Создаем обработку...</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1782"/>
        <source>Uploading image to Mapflow...</source>
        <translation>Загружаем ваш снимок на Mapflow...</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2013"/>
        <source>We couldn&apos;t upload your GeoTIFF</source>
        <translation>Мы не смогли загрузить ваш снимок</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2063"/>
        <source>Processing creation failed</source>
        <translation>Мы не смогли создать обработку</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2035"/>
        <source>Success! We&apos;ll notify you when the processing has finished.</source>
        <translation>Обработка создана! Мы оповестим вас когда она завершится.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1523"/>
        <source>Processing limit: {} sq.km</source>
        <translation type="obsolete">Доступный лимит: {} кв.км</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2165"/>
        <source>Sorry, we couldn&apos;t load the image</source>
        <translation>Ошибка предпросмотра снимка</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2166"/>
        <source>Error previewing Sentinel imagery</source>
        <translation>Ошибка предпросмотра снимка</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2290"/>
        <source>Sorry, there&apos;s no preview for this image</source>
        <translation>К сожалению, для этого снимка нет предпросмотра</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2393"/>
        <source>We couldn&apos;t load a preview for this image</source>
        <translation>Мы не смогли осуществить предпросмотр этого снимка</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2305"/>
        <source>Please, select an image to preview</source>
        <translation>Пожалуйста, выберите снимок</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2408"/>
        <source>Error loading results. Error code: </source>
        <translation type="obsolete">Ошибка загрузки результатов. Код ошибки: </translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2148"/>
        <source>Error downloading results</source>
        <translation type="obsolete">Мы не смогли скачать результаты обработки</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1981"/>
        <source>Error loading results</source>
        <translation type="obsolete">Мы не смогли загрузить результаты</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1907"/>
        <source> failed.
</source>
        <translation type="obsolete"> завершилась с ошибкой.
</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2726"/>
        <source> finished. Double-click it in the table to download the results.</source>
        <translation> завершилась. Дважды кликните на нее в таблице чтобы загрузить результаты.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2019"/>
        <source>Can&apos;t log in to Mapflow</source>
        <translation type="obsolete">Мы не смогли подключиться к Mapflow</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2655"/>
        <source>Invalid token</source>
        <translation type="obsolete">Неверный токен</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2961"/>
        <source>Proxy error. Please, check your proxy settings.</source>
        <translation>Ошибка прокси. Пожалуйста, проверьте настройки прокси в QGIS.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2115"/>
        <source>Unknown error</source>
        <translation type="obsolete">Неизвестная ошибка</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3113"/>
        <source>A new version of Mapflow plugin {server_version} is released 
We recommend you to upgrade to get all the latest features
Go to Plugins -&gt; Manage and Install Plugins -&gt; Upgradable</source>
        <translation>Появилась новая версия mapflow {server_version}. Реомендуем обновить версию чтобы получить доступ к новым возможностям. Выберите меню Модули -&gt; Управление модулями -&gt; Обновляемые</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="444"/>
        <source>Select vector file</source>
        <translation>Выберите векторный файл</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="306"/>
        <source>Create new AOI layer from map extent</source>
        <translation>Создать новый слой области интереса из видимой области карты</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="307"/>
        <source>Add AOI from vector file</source>
        <translation>Загрузить область интереса из файла</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="456"/>
        <source>Your file is not valid vector data source!</source>
        <translation>Ваш файл не подходит как источник векторных данных!</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2773"/>
        <source>Please review or accept this processing until {}. Double click to add results to the map</source>
        <translation>Пожалуйста, оставьте отзыв или примите результаты до {}. Двойной клик для добавления результатов на карту</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="209"/>
        <source>Selected Image ID: {text}</source>
        <translation type="obsolete">Выберите ID снимка: {text}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="528"/>
        <source>This provider cannot be removed</source>
        <translation type="obsolete">Данный источник данных не может быть удален</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="704"/>
        <source>Provider {name} does not support metadata requests</source>
        <translation type="obsolete">Источник данных {name} не поддерживает запрос метаданных</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1390"/>
        <source>Provider {} requires selected Image ID</source>
        <translation type="obsolete">Провайдеру {} требуется выбранный ID снимка</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1995"/>
        <source>Could not launch processing! Error: {}.</source>
        <translation>Не удалось запустить обработку! Ошибка: {}.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2700"/>
        <source> failed with error:
</source>
        <translation> завершилась с ошибкой:
</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="206"/>
        <source>Error during loading the data providers: {e}</source>
        <translation>Ошибка при загрузке источников данных: {e}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="150"/>
        <source>We failed to import providers {errors} from the settings. Please add them again</source>
        <translation type="obsolete">Нам не удалось импортировать провайдеров из настроек {errors}. Пожалуйста, добавьте их снова</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="745"/>
        <source>Provider name must be unique. {name} already exists, select another or delete/edit existing</source>
        <translation>Название источника данных должен быть уникальным. {name} уже существует, выберите другое название или удалите/измените существующий</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1418"/>
        <source>We couldn&apos;t get metadata from Maxar, error {error}</source>
        <translation>Мы не смогли получить метаданные от Maxar, ошибка {error}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1975"/>
        <source>Processing limit exceeded. Visit &quot;&lt;a href=&quot;https://app.mapflow.ai/account/balance&quot;&gt;Mapflow&lt;/a&gt;&quot; to top up your balance</source>
        <translation>Превышен доступный лимит обработки. Посетите &quot;&lt;a href=&quot;https://app.mapflow.ai/account/balance&quot;&gt;Mapflow&lt;/a&gt;&quot; для пополнения баланса</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1525"/>
        <source>.  Project name: {}</source>
        <translation type="obsolete">. Название проекта: {}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2172"/>
        <source>Preview is unavailable for the provider {}</source>
        <translation type="obsolete">Просмотр недоступен для источника данных {}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2973"/>
        <source>This operation is forbidden for your account, contact us</source>
        <translation>Эта операция запрещена для вашего аккаунта, свяжитесь с нами</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2929"/>
        <source>Wrong token. Visit &quot;&lt;a href=&quot;https://app.mapflow.ai/account/api&quot;&gt;mapflow.ai&lt;/a&gt;&quot; to get a new one</source>
        <translation>Неправильный токен. Перейдите на &quot;&lt;a href=&quot;https://app.mapflow.ai/account/api&quot;&gt;mapflow.ai&lt;/a&gt;&quot; чтообы получить новый</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1812"/>
        <source>Processing area layer is corrupted or has invalid projection</source>
        <translation>Слой области обработки поврежден или имеет некорректную проекцию</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3103"/>
        <source>You must upgrade your plugin version to continue work with Mapflow. 
The server requires version {server_version}, your plugin is {local_version}
Go to Plugins -&gt; Manage and Install Plugins -&gt; Upgradable</source>
        <translation>Обновите версию плагина чтобы продолжить работать с Mapflow. Требуется версия {server_version}, установлена версия {local_version}. Выберите меню Модули -&gt; Управление модулями -&gt; Обновляемые</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="757"/>
        <source>Add new provider</source>
        <translation>Добавить новый источник данных</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="765"/>
        <source>This is a default provider, it cannot be edited</source>
        <translation>Этот источник данных встроен в mapflow, его нельзя редактировать</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2707"/>
        <source>{} processings failed: 
 {} 
 See tooltip over the processings table for error details</source>
        <translation>Завершено обработок с ошибкой: {} 
 {} 
 Наведите курсор мыши на обработку в таблице чтобы увидеть сообщение об ошибке</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2714"/>
        <source>{} processings failed: 
 See tooltip over the processings table for error details</source>
        <translation>Завершено с ошибкой {} обработок
 Наведите курсор мыши на обработку в таблице чтобы увидеть сообщение об ошибке</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2734"/>
        <source>{} processings finished: 
 {} 
 Double-click it in the table to download the results</source>
        <translation>Успешно завершено обработок: {}. 
 {} 
 Двойной клик по строке обработки в таблице скачает результаты</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2742"/>
        <source>{} processings finished. 
 Double-click it in the table to download the results</source>
        <translation>Завершено успешно {} обработок.
 Наведите курсор мыши на обработку в таблице чтобы увидеть сообщение об ошибке</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1659"/>
        <source>Set AOI to start processing</source>
        <translation>Задайте область интереса, чтобы запустить обработку</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1568"/>
        <source>Project name: {}</source>
        <translation type="obsolete">Название проекта: {}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1586"/>
        <source>Processing limit: {:.2f} sq.km</source>
        <translation type="obsolete">Лимит обработки: {:.2f} кв.км</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2524"/>
        <source>Only finished processings can be rated</source>
        <translation>Только законченные обработки могут быть оценены</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1789"/>
        <source>Please, provide feedback for rating. Thank you!</source>
        <translation type="obsolete">Пожалуйста, оставьте отзыв для оценки. Спасибо!</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2550"/>
        <source>Thank you! Your rating and feedback are submitted!</source>
        <translation>Спасибо! Ваша оценка и отзыв отправлены!</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2570"/>
        <source>Only correctly finished processings (status OK) can be rated</source>
        <translation>Только правильно завершенные обработки (состояние OK) могут быть оценены</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1877"/>
        <source>Providers are not initialized</source>
        <translation>Провайдеры данных не установлены</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2621"/>
        <source>Only the results of correctly finished processing can be loaded</source>
        <translation>Загружать можно только результаты корректно законченной обработки</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2978"/>
        <source>Error</source>
        <translation>Ошибка</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2543"/>
        <source>Thank you! Your rating is submitted!
We would appreciate if you add feedback as well.</source>
        <translation>Спасибо! Ваша оценка отправлена! Мы будем благодарны, если добавите комментарий к оценке.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="605"/>
        <source>Log in </source>
        <translation>Вход </translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="709"/>
        <source>This provider is default and cannot be removed</source>
        <translation>Этот провайдер встроен в плагин, его нельзя удалить</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="701"/>
        <source>{} doesn&apos;t allow processing single images.</source>
        <translation type="obsolete">{} не позволяет обрабатывать отдельные изображения.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1575"/>
        <source>AOI must contain not more than {} polygons</source>
        <translation>Область интереса не должна содержать более {} полигонов</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1671"/>
        <source>Processing cost is not available:
{error}</source>
        <translation>Стоимость обработки недоступна:
{error}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1696"/>
        <source>Processing cost is not available:
{message}</source>
        <translation>Стоимость обработки недоступна:
{message}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1703"/>
        <source>Processsing cost: {cost} credits</source>
        <translation>Стоимость обработки: {cost} кредитов</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1723"/>
        <source>Please select image in Search table for {}</source>
        <translation type="obsolete">Пожалуйста выберете изображение в таблице поиска для {}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2090"/>
        <source>Your balance: {} credits</source>
        <translation>Ваш баланс: {} кредитов</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2364"/>
        <source>Provider {name} requires image id for preview!</source>
        <translation>Чтобы открыть предпросмотр провайдера {name}, задайте ID изображения!</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2404"/>
        <source>This provider requires image ID!</source>
        <translation>Выберите ID изображения!</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2092"/>
        <source>Remaining limit: {:.2f} sq.km</source>
        <translation>Доступная площадь: {:.2f} кв.км</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1934"/>
        <source>Selected AOI does not intestect the selected image</source>
        <translation>Выбранные область и изображение не пересекаются</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1529"/>
        <source>A Maxar image ID should look like a3b154c40cc74f3b934c0ffc9b34ecd1</source>
        <translation>ID снимка Maxar должен выглядеть как a3b154c40cc74f3b934c0ffc9b34ecd1</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1662"/>
        <source>Error! Models are not initialized</source>
        <translation>Ошибка! Модели не инициализирваны</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1746"/>
        <source>Raster image is not acceptable.  It must be a Tiff file, have size less than {size} pixels and file size less than {memory} MB</source>
        <translation type="obsolete">Недопустимое изображение. Это должен быть файл Tiff , иметь размер растра меньше чем {size} пикселей, и размер файла менее чем {memory} МБ</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1919"/>
        <source>Processing must be in IN_REVIEW status</source>
        <translation type="obsolete">Обработка должна иметь статус &quot;Ожидается отзыв&quot;</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2527"/>
        <source>Processing must be in `Review required` status</source>
        <translation>Обработка должна быть в статусе &quot;Ожидается отзыв&quot;</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2559"/>
        <source>Only correctly finished processings (status OK) can be reviewed</source>
        <translation>Только на корректно завершенные обработки (статус Ок) можно оставить отзыв</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2572"/>
        <source>Please select rating to submit</source>
        <translation>Пожалуйста, выберите оценку</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2288"/>
        <source>Please review this processing until {}. Double click to add results to the map</source>
        <translation type="obsolete">Пожалуйста, оставьте отзыв до {}. Двойной клик для добавления результатов на карту</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="208"/>
        <source>We failed to import providers from the settings. Please add them again</source>
        <translation>Не получилось загрузить провайдеров данных из настроек. Пожалуйста, добавьте их заново</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2778"/>
        <source>Double click to add results to the map.</source>
        <translation>Двойной клик чтобы добавить результаты на карту.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2939"/>
        <source>Name: {name}
Status: {status}

Model: {model},</source>
        <translation type="obsolete">Имя: {name}
Статус: {status}

Модель: {model},</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2945"/>
        <source>
Model options: {options}</source>
        <translation type="obsolete">
Опции: {options}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2950"/>
        <source>

Data provider: {provider}</source>
        <translation type="obsolete">

Источник данных: {provider}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2954"/>
        <source>

Data source: uploaded file</source>
        <translation type="obsolete">

Источник данных: загруженный файл</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2956"/>
        <source>

Data source link {url}</source>
        <translation type="obsolete">

Источник данных: {url}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1020"/>
        <source>We couldn&apos;t get metadata from the Mapflow Imagery Catalog, error {error}</source>
        <translation>Мы не смогли получить метаданные из каталога изображений, ошибка {error}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1416"/>
        <source>Please, check your Maxar credentials</source>
        <translation>Пожалуйста проверьте реквизиты своего аккаунта Maxar</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2056"/>
        <source>Data provider with id is unavailable on your plan. 
 Upgrade your subscription to get access to the data. 
See pricing at &lt;a href=&quot;https://mapflow.ai/pricing&quot;&gt;mapflow.ai&lt;/a&gt;</source>
        <translation>Провайдер недоступен для вашего тарифного плана.
Купите подписку чтобы получить доступ к данным.
Тарифные планы на  &lt;a href=&quot;https://mapflow.ai/pricing&quot;&gt;mapflow.ai&lt;/a&gt;</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2171"/>
        <source>Preview is unavailable when metadata layer is removed</source>
        <translation>Предпросмотр недоступен когда слой с метаданными поиска удален</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2452"/>
        <source>Error downloading results, 
 try again later or report error</source>
        <translation type="obsolete">Ошибка при скачивании результатов
 попробуйте позже или сообщите нам об ошибке</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="308"/>
        <source>Draw AOI at the map</source>
        <translation>Нарисовать AOI на карте</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1814"/>
        <source>Please, select a valid area of interest</source>
        <translation>Пожалуйста, выберите допустимый слой с областью обработки</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1918"/>
        <source>Raster TIFF file must be georeferenced, have size less than {size} pixels and file size less than {memory} MB</source>
        <translation>Растровый TIFF файл должен быть с географической привязкой, иметь размер растра менее чем {size} пикселей и размер файла менее чем {memory} МБ</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1936"/>
        <source>This provider requires image ID. Use search tab to find imagery for you requirements, and select image in the table.</source>
        <translation>Этому провайдеру нужен ID снимка. Используйте вкладку &quot;Поиск&quot; чтобы найти изображения по вашим требованиям, и выберите изображение в таблице.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2842"/>
        <source>We have just set the authentication config for you. 
 You may need to restart QGIS to apply it so you could log in</source>
        <translation>Авторизация настроена. Может потребоваться перезагрузить QGIS чтобы применить конфигурацию и войти в систему</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2867"/>
        <source>Please restart QGIS before using OAuth2 login.</source>
        <translation>Пожалуйста перезагрузите QGIS перед использованием авторизации OAuth2.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3075"/>
        <source>No projects found! Contact us to resolve the issue</source>
        <translation>Проектов не найдено! Свяжитесь с нами чтобы решить проблему</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="303"/>
        <source>Save results</source>
        <translation type="obsolete">Сохранить результаты</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="304"/>
        <source>Download AOI</source>
        <translation type="obsolete">Скачать область интереса</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="305"/>
        <source>See details</source>
        <translation type="obsolete">Подробности</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="306"/>
        <source>Rename</source>
        <translation type="obsolete">Переименовать</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="694"/>
        <source>Do you really want to remove project {}? This action cannot be undone, all processings will be lost!</source>
        <translation>Вы действительно хотите удалить проект {}? Это действие нельзя отменить, все обработки будут потеряны!</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2368"/>
        <source>Preview is unavailable for the provider {}. 
OSM layer will be added instead.</source>
        <translation type="unfinished">Предпросмотр для источника {} недоступен.
Вместо этого будет добвален слой OSM.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3131"/>
        <source>&lt;b&gt;Name&lt;/b&gt;: {name}&lt;br&gt;&lt;b&gt;Status&lt;/b&gt;&lt;/br&gt;: {status}&lt;br&gt;&lt;b&gt;Model&lt;/b&gt;&lt;/br&gt;: {model}</source>
        <translation>&lt;b&gt;Название&lt;/b&gt;: {name}&lt;br&gt;&lt;b&gt;Статус&lt;/b&gt;&lt;/br&gt;: {status}&lt;br&gt;&lt;b&gt;Модель&lt;/b&gt;&lt;/br&gt;: {model}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3137"/>
        <source>&lt;br&gt;&lt;b&gt;Description&lt;/b&gt;&lt;/br&gt;: {description}</source>
        <translation>&lt;br&gt;&lt;b&gt;Описание&lt;/b&gt;&lt;/br&gt;: {description}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3140"/>
        <source>&lt;br&gt;&lt;b&gt;Model options:&lt;/b&gt;&lt;/br&gt; {options}</source>
        <translation>&lt;br&gt;&lt;b&gt;Опции:&lt;/b&gt;&lt;/br&gt; {options}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3145"/>
        <source>&lt;br&gt;&lt;b&gt;Model options:&lt;/b&gt;&lt;/br&gt; No options selected</source>
        <translation>&lt;br&gt;&lt;b&gt;Опции:&lt;/b&gt;&lt;/br&gt; Не выбраны</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3148"/>
        <source>&lt;br&gt;&lt;b&gt;Data provider&lt;/b&gt;&lt;/br&gt;: {provider}</source>
        <translation>&lt;br&gt;&lt;b&gt;Источник данных&lt;/b&gt;&lt;/br&gt;: {provider}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3152"/>
        <source>&lt;br&gt;&lt;b&gt;Data source&lt;/b&gt;&lt;/br&gt;: uploaded file</source>
        <translation>&lt;br&gt;&lt;b&gt;Источник данных&lt;/b&gt;&lt;/br&gt;: загруженный файл</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3154"/>
        <source>&lt;br&gt;&lt;b&gt;Data source link&lt;/b&gt;&lt;/br&gt; {url}</source>
        <translation>&lt;br&gt;&lt;b&gt;Ссылка на источник данных&lt;/b&gt;&lt;/br&gt; {url}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="673"/>
        <source>Not enough rights to delete or update shared project ({})</source>
        <translation>Недостаточно прав для удаления или изменения проекта ({})</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1694"/>
        <source>Not enough rights to start processing in a shared project ({})</source>
        <translation>Недостаточно прав в проекте для запауска обработки ({})</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2235"/>
        <source>Preview is unavailable</source>
        <translation type="unfinished">Предпросмотр недоступен</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2282"/>
        <source>Could not display preview</source>
        <translation type="unfinished">Неудалось осуществить предпросмотр</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2565"/>
        <source>Not enough rights to rate processing in a shared project ({})</source>
        <translation>Недостаточно прав в проекте для оценивания обработки ({})</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2568"/>
        <source>Please select processing</source>
        <translation>Пожалуйста, выберите обработку</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2965"/>
        <source>Not enough rights for this action
in a shared project &apos;{project_name}&apos; ({user_role})</source>
        <translation>Недостаточно прав для этого действия
в проекте &apos;{project_name}&apos; ({user_role})</translation>
    </message>
</context>
<context>
    <name>MapflowLoginDialog</name>
    <message>
        <location filename="../dialogs/login_dialog.py" line="32"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;You will be redirecrted to web browser &lt;br/&gt;to enter your Mapflow login and password&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;В браузере откроется страница входа в Mapflow &lt;br/&gt;введите своё имя пользователя и пароль&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/login_dialog.py" line="33"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;span style=&quot; color:#ff0000;&quot;&gt;Authorization is not completed! &lt;/span&gt;&lt;/p&gt;&lt;p&gt;&lt;br/&gt;1. Complete authorization in browser. &lt;br/&gt;&lt;br/&gt;2. If it does not help, restart QGIS. &lt;br/&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow.html#oauth2_setup&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#094fd1;&quot;&gt;See documentation for help &lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;span style=&quot; color:#ff0000;&quot;&gt;Авторизация не завершена! &lt;/span&gt;&lt;/p&gt;&lt;p&gt;&lt;br/&gt;1. Авторизуйтесь в браузере. &lt;br/&gt;&lt;br/&gt;2. Если это не помогло, перезапустите QGIS. &lt;br/&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow.html#oauth2_setup&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#094fd1;&quot;&gt;См. документацию &lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/login_dialog.py" line="38"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href=&quot;https://app.mapflow.ai/account/api&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Get token&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;a href=&quot;https://mapflow.ai/terms-of-use-en.pdf&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Terms of use&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;Register at &lt;a href=&quot;https://mapflow.ai&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;mapflow.ai&lt;/span&gt;&lt;/a&gt; to use the plugin&lt;/p&gt;&lt;p&gt;&lt;br/&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href=&quot;https://app.mapflow.ai/account/api&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Получить токен&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;a href=&quot;https://mapflow.ai/terms-of-use.pdf&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Условия использования&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;Зарегистрируйтесь на &lt;a href=&quot;https://mapflow.ai&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;mapflow.ai&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt; чтобы использовать плагин&lt;/p&gt;&lt;p&gt;&lt;br/&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/login_dialog.py" line="39"/>
        <source>Invalid credentials</source>
        <translation>Неправильные данные авторизации</translation>
    </message>
</context>
<context>
    <name>ProcessingErrors</name>
    <message>
        <location filename="../errors/processing_errors.py" line="10"/>
        <source>Task for source-validation must contain area of interest (`geometry` section)</source>
        <translation>Задача на проверку источника данных должна содержать область интереса (ключ `geometry`)</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="12"/>
        <source>We could not open and read the image you have uploaded</source>
        <translation>Мы не смогли открыть и прочитать загруженное изображение</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="13"/>
        <source>Image profile (metadata) must have keys {required_keys}, got profile {profile}</source>
        <translation>Метаданные изображения должны содержать следующие теги: {required_keys}, метаданные загруженного изображения: {profile}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="15"/>
        <source>AOI does not intersect the selected Sentinel-2 granule {actual_cell}</source>
        <translation>Области интереса не пересекает выбранное изображение Sentinel-2 (код ячейки {actual_cell} )</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="17"/>
        <source>Key &apos;url&apos; in your request must be a string, got {url_type} instead.</source>
        <translation>Ключ &apos;url&apos; в запросе должен быть строкой, не {url_type}.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="19"/>
        <source>The specified basemap {url} is forbidden for processing because it contains a map, not satellite image. Our models are suited for satellite imagery.</source>
        <translation>Указанная подложка {url} запрещена к обработке, так как содержит карту, а не спутниковый снимок. Наши модели предназначены для обработки спутниковых снимков.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="22"/>
        <source>Your URL must be a link starting with &quot;http://&quot; or &quot;https://&quot;.</source>
        <translation>URL должен начинаться с &quot;http://&quot; или &quot;https://&quot;.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="24"/>
        <source>Format of &apos;url&apos; is invalid and cannot be parsed. Error: {parse_error_message}</source>
        <translation>Невалидный формат URL. Ошибка {parse_error_message}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="26"/>
        <source>Zoom must be either empty, or integer, got {actual_zoom}</source>
        <translation>Поле „zoom“ должно быть либо пустым, либо целым числом. Получено {actual_zoom}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="28"/>
        <source>Zoom must be between 0 and 22, got {actual_zoom}</source>
        <translation>Значение поля „zoom“ в вашем запросе должно быть в интервале от 0 до 22. Получено {actual_zoom}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="29"/>
        <source>Zoom must be not lower than {min_zoom}, got {actual_zoom}</source>
        <translation>Значение поля „zoom“ в вашем запросе должно быть не менее {min_zoom}. Получено {actual_zoom}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="30"/>
        <source>Image metadata must be a dict (json)</source>
        <translation>Метаданные вашего изображения должны быть типа &quot;словарь&quot; (json)</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="31"/>
        <source>Image metadata must have keys: crs, transform, dtype, count</source>
        <translation>Метаданные вашего изображения должны содержать ключи: crs, transform, dtype, count</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="33"/>
        <source>URL of the image at s3 storage must be a string starting with s3://, got {actual_s3_link}</source>
        <translation>URL изображения на хранилище S3 должен быть строкой и начинаться с S3://. Получено {actual_s3_link}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="35"/>
        <source>Request must contain either &apos;profile&apos; or &apos;url&apos; keys</source>
        <translation>Запрос должен содержать либо „profile“, либо „url“</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="36"/>
        <source>Failed to read file from {s3_link}.</source>
        <translation>Ошибка чтения файла из {s3_link}.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="37"/>
        <source>Image data type (Dtype) must be one of {required_dtypes}, got {request_dtype}</source>
        <translation>Тип данных изображения (Dtype) должен быть одним из {required_dtypes}. Получено {request_dtype}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="39"/>
        <source>Number of channels in image must be one of {required_nchannels}. Got {real_nchannels}</source>
        <translation>Изображение имеет {real_nchannels} каналов, требуемое количество каналов {required_nchannels}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="41"/>
        <source>Spatial resolution of you image is too high: pixel size is {actual_res}, minimum allowed pixel size is {min_res}</source>
        <translation>Пространственное разрешение вашего изображения слишком высокое: размер пикселя {actual_res}, минимальный допустимый размер пикселя равен {min_res}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="44"/>
        <source>Spatial resolution of you image is too low: pixel size is {actual_res}, maximum allowed pixel size is {max_res}</source>
        <translation>Пространственное разрешение вашего изображения слишком низкое: размер пикселя равен {actual_res}, максимально допустимый размер пикселя равен {max_res}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="47"/>
        <source>Error occurred during image {checked_param} check: {message}. Image metadata = {metadata}.</source>
        <translation>Ошибка произошла во время проверки параметра {checked_param} изображения: {message}. Метаданные изображения = {metadata}.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="49"/>
        <source>Your &apos;url&apos; doesn&apos;t match the format, Quadkey basemap must be a link containing &quot;q&quot; placeholder.</source>
        <translation>Ссылка на Quadkey подложку не соответствует формату. Это должна быть ссылка, содержащая поле «q».</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="52"/>
        <source>Input string {input_string} is of unknown format. It must represent Sentinel-2 granule ID.</source>
        <translation>Строка {input_string} неизвестного формата. Она должна представлять собой ID гранулы снимка Sentinel-2.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="54"/>
        <source>Selected Sentinel-2 image cell is {actual_cell}, this model is for the cells: {allowed_cells}</source>
        <translation>Выбранная ячейка {actual_cell} не подходит для обработки, модель рассчитана на ячейки: {allowed_cells}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="56"/>
        <source>Selected Sentinel-2 image month is {actual_month}, this model is for: {allowed_months}</source>
        <translation>Выбранный месяц {actual_month} не подходит для обработки, модель рассчитана на месяцы: {allowed_months}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="58"/>
        <source>You request TMS basemap link doesn&apos;t match the format, it must be a link containing &quot;x&quot;, &quot;y&quot;, &quot;z&quot; placeholders, correct it and start processing again.</source>
        <translation>Ссылка на TMS подложку не соответствует формату. Это должна быть ссылка, содержащая поля &quot;x&quot;, &quot;y&quot;, &quot;z&quot;.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="61"/>
        <source>Requirements must be dict, got {requirements_type}.</source>
        <translation>Секция «requirements» в запросе должна быть словарем (dict), а не {requirements_type}.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="62"/>
        <source>Request must be dict, got {request_type}.</source>
        <translation>Секция «request» в запросе должна быть словарем (dict), а не {request_type}.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="63"/>
        <source>Request must contain &quot;source_type&quot; key</source>
        <translation>Запрос должен содержать тип источника спутниковых снимков (ключ «source_type»)</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="64"/>
        <source>Source type {source_type} is not allowed. Use one of: {allowed_sources}</source>
        <translation>Источник данных {source_type}, не поддерживется платформой. Ипользуйте один из разрешенных: {allowed_sources}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="66"/>
        <source>&quot;Required&quot; section of the requirements must contain dict, not {required_section_type}</source>
        <translation>Секция «Required» в требованиях к данным должна быть словарем (dict), а не {required_section_type}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="68"/>
        <source>&quot;Recommended&quot; section of the requirements must contain dict, not {recommended_section_type}</source>
        <translation>Секция «recommended» в требованиях к данным должна быть словарем (dict), а не {recommended_section_type}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="70"/>
        <source>You XYZ basemap link doesn&apos;t match the format, it must be a link containing &quot;x&quot;, &quot;y&quot;, &quot;z&quot;  placeholders.</source>
        <translation>Ссылка на XYZ подложку не соответствует формату. Это должна быть ссылка, содержащая поля &quot;x&quot;, &quot;y&quot;, &quot;z&quot;.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="75"/>
        <source>Internal error in process of data source validation. We are working on the fix, our support will contact you.</source>
        <translation>Произошла ошибка в процессе проверки источника данных. Мы работаем над исправлением и свяжемся с вами.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="96"/>
        <source>Internal error in process of loading data. We are working on the fix, our support will contact you.</source>
        <translation>Произошла ошибка в процессе загрузки данных. Мы работаем над исправлением и свяжемся с вами.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="79"/>
        <source>Wrong source type {real_source_type}. Specify one of the allowed types {allowed_source_types}.</source>
        <translation>Неправильный тип источника данных {real_source_type}. Используйте один из допустимых {allowed_source_types}.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="81"/>
        <source>Your data loading task requires {estimated_size} MB of memory, which exceeded allowed memory limit {allowed_size}</source>
        <translation>Ваш запрос на загрузку данных требует {estimated_size} MB, что превышает лимит в {allowed_size}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="83"/>
        <source>Dataloader argument {argument_name} has type {argument_type}, excpected to be {expected_type}</source>
        <translation>Функция загрузки данных {argument_name} имеет тип {argument_type}, допустимый тип {expected_type}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="85"/>
        <source>Loaded tile has {real_nchannels} channels, required number is {expected_nchannels}</source>
        <translation>Загруженное изображение имеет {real_nchannels} каналов, требуемое количество каналов {expected_nchannels}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="87"/>
        <source>Loaded tile has size {real_size}, expected tile size is {expected_size}</source>
        <translation>Загруженное изображение имеет размер {real_size}, допустимый размер {expected_size}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="89"/>
        <source>Tile at location {tile_location} cannot be loaded, server response is {status}</source>
        <translation>Изображение по адресу {tile_location} не может быть загружено, ответ сервера {status}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="91"/>
        <source>Response content at {tile_location} cannot be decoded as an image</source>
        <translation>Ответ сервера {tile_location} не представляет собой изображение</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="98"/>
        <source>Internal error in process of data preparation. We are working on the fix, our support will contact you.</source>
        <translation>Произошла ошибка в процессе предобработки данных. Мы работаем над исправлением и свяжемся с вами.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="100"/>
        <source>Internal error in process of data processing. We are working on the fix, our support will contact you.</source>
        <translation>Произошла ошибка в процессе обработки данных. Мы работаем над исправлением и свяжемся с вами.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="102"/>
        <source>Internal error in process of saving the results. We are working on the fix, our support will contact you.</source>
        <translation>Произошла ошибка в процессе сохранения результатов обработки. Мы работаем над исправлением и свяжемся с вами.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="8"/>
        <source>Folder `{s3_link}` selected for processing does not contain any images. </source>
        <translation>Папка `{s3_link}`, выбранная для обработки, не содержит изображений. </translation>
    </message>
</context>
<context>
    <name>ProviderDialog</name>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="93"/>
        <source>Name</source>
        <translation>Название</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="53"/>
        <source>Type</source>
        <translation>Тип</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="66"/>
        <source>Tile coordinate scheme. XYZ is the most popular format, use it if you are not sure</source>
        <translation>Тайловая схема. Самый популярный формат - XYZ, используйте его если не уверены</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="85"/>
        <source>Maxar WMTS</source>
        <translation></translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="117"/>
        <source>Login</source>
        <translation>Логин</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="127"/>
        <source>Password</source>
        <translation>Пароль</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="134"/>
        <source>CRS</source>
        <translation>CRS</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="159"/>
        <source>Projection of the tile layer. The most popular is Web Mercator, use it if you are not sure</source>
        <translation>Проекция тайлового слоя. Самая популярная - Web Mercator (EPSG:3857), используйте её если не уверены</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="163"/>
        <source>EPSG:3857</source>
        <translation>EPSG:3857</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="168"/>
        <source>EPSG:3395</source>
        <translation>EPSG:3395</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="176"/>
        <source>Warninig! Login and password, if saved, will be stored in QGIS settings without encryption!</source>
        <translation>Предупреждение! Логин и пароль, в случае сохранения, будут храниться в настройках QGIS без шифрования!</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="179"/>
        <source>Save login and password</source>
        <translation>Сохранить логин и пароль</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="35"/>
        <source>Provider</source>
        <translation>Источник данных</translation>
    </message>
</context>
<context>
    <name>QPlatformTheme</name>
    <message>
        <location filename="../mapflow.py" line="138"/>
        <source>Cancel</source>
        <translation>Отмена</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="139"/>
        <source>&amp;Yes</source>
        <translation>Да</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="140"/>
        <source>&amp;No</source>
        <translation>Нет</translation>
    </message>
</context>
<context>
    <name>ReviewDialog</name>
    <message>
        <location filename="../dialogs/dialogs.py" line="41"/>
        <source>Review {processing}</source>
        <translation>Отзыв на {processing}</translation>
    </message>
</context>
<context>
    <name>SentinelAuthDialog</name>
    <message>
        <location filename="../static/ui/sentinel_auth_dialog.ui" line="35"/>
        <source>SkyWatch API Key</source>
        <translation type="obsolete">Ключ для SkyWatch API</translation>
    </message>
    <message>
        <location filename="../static/ui/sentinel_auth_dialog.ui" line="43"/>
        <source>API key:</source>
        <translation type="obsolete">Ключ API:</translation>
    </message>
</context>
</TS>
