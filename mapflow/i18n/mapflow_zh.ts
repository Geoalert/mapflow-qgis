<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="zh_CN" sourcelanguage="en">
<context>
    <name>ApiErrors</name>
    <message>
        <location filename="../errors/api_errors.py" line="8"/>
        <source>Upgrade your subscription to get access to Maxar imagery</source>
        <translation>升级订阅以获取Maxar影像访问权限</translation>
    </message>
    <message>
        <location filename="../errors/api_errors.py" line="9"/>
        <source>Geometry area is {aoiArea} sq km, which is smaller than the minimum required area for {providerName} data provider ({providerMinArea} sq km)</source>
        <translation>几何区域面积为 {aoiArea} 平方公里，小于 {providerName} 数据提供商要求的最小面积 ({providerMinArea} 平方公里)</translation>
    </message>
</context>
<context>
    <name>Config</name>
    <message>
        <location filename="../config.py" line="11"/>
        <source>Product Type</source>
        <translation>产品类型</translation>
    </message>
    <message>
        <location filename="../config.py" line="12"/>
        <source>Provider Name</source>
        <translation>提供商名称</translation>
    </message>
    <message>
        <location filename="../config.py" line="13"/>
        <source>Preview</source>
        <translation>预览</translation>
    </message>
    <message>
        <location filename="../config.py" line="14"/>
        <source>Sensor</source>
        <translation>传感器</translation>
    </message>
    <message>
        <location filename="../config.py" line="15"/>
        <source>Band Order</source>
        <translation>波段顺序</translation>
    </message>
    <message>
        <location filename="../config.py" line="84"/>
        <source>Cloud %</source>
        <translation>云量 %</translation>
    </message>
    <message>
        <location filename="../config.py" line="17"/>
        <source>Off Nadir</source>
        <translation>离天底角</translation>
    </message>
    <message>
        <location filename="../config.py" line="83"/>
        <source>Date &amp; Time</source>
        <translation>日期 &amp; 时间</translation>
    </message>
    <message>
        <location filename="../config.py" line="19"/>
        <source>Zoom level</source>
        <translation>缩放级别</translation>
    </message>
    <message>
        <location filename="../config.py" line="20"/>
        <source>Spatial Resolution, m</source>
        <translation>空间分辨率，米</translation>
    </message>
    <message>
        <location filename="../config.py" line="21"/>
        <source>Image ID</source>
        <translation>影像ID</translation>
    </message>
    <message>
        <location filename="../config.py" line="26"/>
        <source>Project</source>
        <translation>项目</translation>
    </message>
    <message>
        <location filename="../config.py" line="27"/>
        <source>Succeeded</source>
        <translation>成功</translation>
    </message>
    <message>
        <location filename="../config.py" line="28"/>
        <source>Failed</source>
        <translation>失败</translation>
    </message>
    <message>
        <location filename="../config.py" line="29"/>
        <source>Author</source>
        <translation>作者</translation>
    </message>
    <message>
        <location filename="../config.py" line="30"/>
        <source>Updated at</source>
        <translation>更新于</translation>
    </message>
    <message>
        <location filename="../config.py" line="31"/>
        <source>Created at</source>
        <translation>创建于</translation>
    </message>
</context>
<context>
    <name>ConfirmProcessingStartDialog</name>
    <message>
        <location filename="../dialogs/confirm_processing_start_dialog.py" line="17"/>
        <source>Confirm processing start</source>
        <translation>确认开始处理</translation>
    </message>
    <message>
        <location filename="../dialogs/confirm_processing_start_dialog.py" line="32"/>
        <source>No zoom selected</source>
        <translation>未选择缩放级别</translation>
    </message>
    <message>
        <location filename="../dialogs/confirm_processing_start_dialog.py" line="42"/>
        <source>No options selected</source>
        <translation>未选择选项</translation>
    </message>
</context>
<context>
    <name>CreateMosaicDialog</name>
    <message>
        <location filename="../dialogs/mosaic_dialog.py" line="30"/>
        <source>Imagery collection</source>
        <translation>影像集</translation>
    </message>
    <message>
        <location filename="../dialogs/mosaic_dialog.py" line="37"/>
        <source>Imagery collection name must not be empty!</source>
        <translation>影像集名称不能为空！</translation>
    </message>
</context>
<context>
    <name>CreateProjectDialog</name>
    <message>
        <location filename="../dialogs/project_dialog.py" line="36"/>
        <source>Create project</source>
        <translation>创建项目</translation>
    </message>
</context>
<context>
    <name>DataCatalogApi</name>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="274"/>
        <source>Error</source>
        <translation>错误</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="127"/>
        <source>Could not delete imagery collection &apos;{mosaic_name}&apos;</source>
        <translation>无法删除影像集 '{mosaic_name}'</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="129"/>
        <source>Error. Could not delete following imagery collections:</source>
        <translation>错误。无法删除以下影像集：</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="171"/>
        <source>Failed to load imagery collection. 
Please try again later or report error</source>
        <translation>加载影像集失败。请稍后重试或报告错误</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="228"/>
        <source>This operation is forbidden for your account, contact us</source>
        <translation>您的账户无权执行此操作，请联系我们</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="230"/>
        <source>Imagery collection &apos;{mosaic_name}&apos; does not exist</source>
        <translation>影像集 '{mosaic_name}' 不存在</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="232"/>
        <source>Authentication error. Please log in to your account</source>
        <translation>认证错误。请登录您的账户</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="234"/>
        <source>The image does not meet this imagery collection &apos;{mosaic_name}&apos; parameters. 
Either modify your image or upload it to a different collection</source>
        <translation>该影像不符合此影像集 '{mosaic_name}' 的参数要求。请修改您的影像或上传到其他影像集</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="237"/>
        <source>Could not upload &apos;{image}&apos; to imagery collection</source>
        <translation>无法将 '{image}' 上传到影像集</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="239"/>
        <source>Could not upload following images:
{images}</source>
        <translation>无法上传以下影像：
{images}</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="275"/>
        <source>Could not delete &apos;{image}&apos; from imagery collection</source>
        <translation>无法从影像集中删除 '{image}'</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="277"/>
        <source>Error. Could not delete following images:</source>
        <translation>错误。无法删除以下影像：</translation>
    </message>
</context>
<context>
    <name>DataCatalogService</name>
    <message>
        <location filename="../functional/service/data_catalog.py" line="80"/>
        <source>Choose image to upload</source>
        <translation>选择要上传的影像</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="122"/>
        <source>&lt;center&gt;Creation of imagery collection &apos;{mosaic_name}&apos; failed&lt;br&gt;while trying to upload &apos;{image}&apos;</source>
        <translation>&lt;center&gt;创建影像集 '{mosaic_name}' 失败&lt;br&gt;尝试上传 '{image}' 时</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="201"/>
        <source>&lt;center&gt;Delete imagery collection &lt;b&gt;&apos;{name}&apos;&lt;/b&gt;?</source>
        <translation>&lt;center&gt;删除影像集 &lt;b&gt;'{name}'&lt;/b&gt;？</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="204"/>
        <source>&lt;center&gt;Delete following imagery collections:&lt;br&gt;&lt;b&gt;&apos;{names}&apos;&lt;/b&gt;?</source>
        <translation>&lt;center&gt;删除以下影像集：&lt;br&gt;&lt;b&gt;'{names}'&lt;/b&gt;？</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="207"/>
        <source>&lt;center&gt;Delete &lt;b&gt;{len}&lt;/b&gt; imagery collections?</source>
        <translation>&lt;center&gt;删除 &lt;b&gt;{len}&lt;/b&gt; 个影像集？</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="247"/>
        <source>Please, select existing imagery collection</source>
        <translation>请选择现有的影像集</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="249"/>
        <source>Choose images to upload</source>
        <translation>选择要上传的影像</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="298"/>
        <source>Raster TIFF file must be georeferenced, have size less than {size} pixels and file size less than {memory}</source>
        <translation>栅格TIFF文件必须经过地理配准，像素尺寸小于 {size} 且文件大小小于 {memory}</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="302"/>
        <source>&lt;center&gt;&lt;b&gt;Error uploading &apos;{name}&apos;&lt;/b&gt;</source>
        <translation>&lt;center&gt;&lt;b&gt;上传 '{name}' 时出错&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="307"/>
        <source>&lt;b&gt;Not enough storage space. &lt;/b&gt;You have {free_storage} left, but &apos;{name}&apos; is {image_size}</source>
        <translation>&lt;b&gt;存储空间不足。&lt;/b&gt;您剩余 {free_storage}，但 '{name}' 大小为 {image_size}</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="401"/>
        <source>&lt;center&gt;Delete image &lt;b&gt;&apos;{name}&apos;&lt;/b&gt; from &apos;{mosaic}&apos; imagery collection?</source>
        <translation>&lt;center&gt;从 '{mosaic}' 影像集中删除影像 &lt;b&gt;'{name}'&lt;/b&gt;？</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="404"/>
        <source>&lt;center&gt;Delete following images from &apos;{mosaic}&apos; imagery collection:&lt;br&gt;&lt;b&gt;&apos;{names}&apos;&lt;/b&gt;?</source>
        <translation>&lt;center&gt;从 '{mosaic}' 影像集中删除以下影像：&lt;br&gt;&lt;b&gt;'{names}'&lt;/b&gt;？</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="407"/>
        <source>&lt;center&gt;Delete &lt;b&gt;{len}&lt;/b&gt; images from &apos;{mosaic}&apos; imagery collection?</source>
        <translation>&lt;center&gt;从 '{mosaic}' 影像集中删除 &lt;b&gt;{len}&lt;/b&gt; 个影像？</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="462"/>
        <source>Please, select existing output directory in the Settings tab</source>
        <translation>请在设置选项卡中选择现有的输出目录</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="505"/>
        <source>Image name should be 1-255 characters long</source>
        <translation>影像名称应为 1-255 个字符</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="631"/>
        <source>Source imagery collection with id &apos;{}&apos; was not found </source>
        <translation>未找到ID为 '{}' 的源影像集</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="633"/>
        <source>Source image with id &apos;{}&apos; was not found in any of your imagery collections</source>
        <translation>未在任何影像集中找到ID为 '{}' 的源影像</translation>
    </message>
</context>
<context>
    <name>DataCatalogView</name>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="24"/>
        <source>Upload from file</source>
        <translation>从文件上传</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="25"/>
        <source>Choose raster layer</source>
        <translation>选择栅格图层</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="44"/>
        <source>Add images</source>
        <translation>添加影像</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="45"/>
        <source>Show images</source>
        <translation>显示影像</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="48"/>
        <source>Preview</source>
        <translation>预览</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="47"/>
        <source>Edit</source>
        <translation>编辑</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="49"/>
        <source>Info</source>
        <translation>信息</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="50"/>
        <source>Rename</source>
        <translation>重命名</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="72"/>
        <source>A-Z</source>
        <translation>A-Z</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="72"/>
        <source>Z-A</source>
        <translation>Z-A</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="72"/>
        <source>Biggest first</source>
        <translation>最大优先</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="72"/>
        <source>Smallest first</source>
        <translation>最小优先</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="72"/>
        <source>Newest first</source>
        <translation>最新优先</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="72"/>
        <source>Oldest first</source>
        <translation>最旧优先</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="93"/>
        <source>More about My imagery</source>
        <translation>关于“我的影像”的更多信息</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="508"/>
        <source>Filter imagery collections by name or id</source>
        <translation>按名称或ID筛选影像集</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="127"/>
        <source>Imagery collections</source>
        <translation>影像集</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="288"/>
        <source>Size</source>
        <translation>大小</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="127"/>
        <source>Created</source>
        <translation>创建时间</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="458"/>
        <source>Double-click to show images</source>
        <translation>双击显示影像</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="175"/>
        <source>Number of images: {count} 
</source>
        <translation>影像数量：{count} 
</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="185"/>
        <source>Size: {mosaic_size} 
Pixel size: {pixel_size} 
CRS: {crs} 
Number of bands: {count} 
</source>
        <translation>大小：{mosaic_size} 
像素大小：{pixel_size} 
坐标系：{crs} 
波段数：{count} 
</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="193"/>
        <source>Created: {date} at {time} 
Tags: {tags}</source>
        <translation>创建时间：{date} {time} 
标签：{tags}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="244"/>
        <source>&lt;b&gt;Name&lt;/b&gt;: {filename}                              &lt;br&gt;&lt;b&gt;Uploaded&lt;/b&gt;&lt;/br&gt;: {date} at {time}                              &lt;br&gt;&lt;b&gt;Size&lt;/b&gt;&lt;/br&gt;: {file_size}                              &lt;br&gt;&lt;b&gt;CRS&lt;/b&gt;&lt;/br&gt;: {crs}                              &lt;br&gt;&lt;b&gt;Number of bands&lt;/br&gt;&lt;/b&gt;: {bands}                              &lt;br&gt;&lt;b&gt;Width&lt;/br&gt;&lt;/b&gt;: {width} pixels                              &lt;br&gt;&lt;b&gt;Height&lt;/br&gt;&lt;/b&gt;: {height} pixels                              &lt;br&gt;&lt;b&gt;Pixel size&lt;/br&gt;&lt;/b&gt;: {pixel_size}</source>
        <translation>&lt;b&gt;名称&lt;/b&gt;：{filename}                              &lt;br&gt;&lt;b&gt;上传时间&lt;/b&gt;&lt;/br&gt;：{date} {time}                              &lt;br&gt;&lt;b&gt;大小&lt;/b&gt;&lt;/br&gt;：{file_size}                              &lt;br&gt;&lt;b&gt;坐标系&lt;/b&gt;&lt;/br&gt;：{crs}                              &lt;br&gt;&lt;b&gt;波段数&lt;/br&gt;&lt;/b&gt;：{bands}                              &lt;br&gt;&lt;b&gt;宽度&lt;/br&gt;&lt;/b&gt;：{width} 像素                              &lt;br&gt;&lt;b&gt;高度&lt;/br&gt;&lt;/b&gt;：{height} 像素                              &lt;br&gt;&lt;b&gt;像素大小&lt;/br&gt;&lt;/b&gt;：{pixel_size}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="288"/>
        <source>Images</source>
        <translation>影像</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="288"/>
        <source>Uploaded</source>
        <translation>上传时间</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="344"/>
        <source>No imagery collection with id &apos;{mosaic_id}&apos; was found</source>
        <translation>未找到ID为 '{mosaic_id}' 的影像集</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="357"/>
        <source>No image with id &apos;{image_id}&apos; was found</source>
        <translation>未找到ID为 '{image_id}' 的影像</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="371"/>
        <source>Your data: {taken}. Free space: {free}</source>
        <translation>您的数据：{taken}。剩余空间：{free}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="387"/>
        <source>Selected imagery collection: &lt;b&gt;{mosaic_name}</source>
        <translation>已选影像集：&lt;b&gt;{mosaic_name}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="401"/>
        <source>No imagery collection selected</source>
        <translation>未选择影像集</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="422"/>
        <source>Uploaded: {date} at {time} 
File size: {size} 
Pixel size: {pixel_size} 
CRS: {crs} 
Bands: {count}</source>
        <translation>上传时间：{date} {time} 
文件大小：{size} 
像素大小：{pixel_size} 
坐标系：{crs} 
波段数：{count}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="435"/>
        <source>Selected image: &lt;b&gt;{image_name}</source>
        <translation>已选影像：&lt;b&gt;{image_name}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="445"/>
        <source>No image selected</source>
        <translation>未选择影像</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="455"/>
        <source>&apos;Cmd&apos; + click to deselect</source>
        <translation>按住 'Cmd' 并点击以取消选择</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="455"/>
        <source>&apos;Ctrl&apos; + click to deselect</source>
        <translation>按住 'Ctrl' 并点击以取消选择</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="472"/>
        <source>Delete image</source>
        <translation>删除影像</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="473"/>
        <source>Add image</source>
        <translation>添加影像</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="486"/>
        <source>Filter images by name or id</source>
        <translation>按名称或ID筛选影像</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="493"/>
        <source>Delete collection</source>
        <translation>删除影像集</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="494"/>
        <source>Add collection</source>
        <translation>添加影像集</translation>
    </message>
</context>
<context>
    <name>DataErrors</name>
    <message>
        <location filename="../errors/data_errors.py" line="8"/>
        <source>File {filename} cannot be processed. Parameters {bad_parameters} are incompatible with our catalog. See the documentation for more info.</source>
        <translation>文件 {filename} 无法处理。参数 {bad_parameters} 与我们的目录不兼容。请参阅文档获取更多信息。</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="11"/>
        <source>Your file has size {memory_requested} bytes, but you have only {available_memory} left. Upgrade your subscription or remove older imagery from your catalog</source>
        <translation>您的文件大小为 {memory_requested} 字节，但您仅剩 {available_memory} 空间。请升级订阅或从目录中删除旧影像</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="14"/>
        <source>Max file size allowed to upload is {max_file_size} bytes, your file is {actual_file_size} bytes instead. Compress your file or cut it into smaller parts</source>
        <translation>允许上传的最大文件大小为 {max_file_size} 字节，但您的文件大小为 {actual_file_size} 字节。请压缩文件或将其分割为更小的部分</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="17"/>
        <source>{instance_type} with id: {uid} can&apos;t be found</source>
        <translation>未找到ID为 {uid} 的 {instance_type}</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="18"/>
        <source>You do not have access to {instance_type} with id {uid}</source>
        <translation>您无权访问ID为 {uid} 的 {instance_type}</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="19"/>
        <source>File {filename} cannot be uploaded to imagery collection: {mosaic_id}. {param_name} of the file is {got_param}, it should be {expected_param} to fit the collection. Fix your file, or upload it to another imagery collection</source>
        <translation>文件 {filename} 无法上传到影像集：{mosaic_id}。文件的 {param_name} 为 {got_param}，应为 {expected_param} 以匹配该影像集。请修复您的文件，或上传到其他影像集</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="23"/>
        <source>File can&apos;t be uploaded, because its extent is out of coordinate range.Check please CRS and transform of the image, they may be invalid</source>
        <translation>文件无法上传，因为其范围超出坐标范围。请检查影像的坐标系和变换参数，它们可能无效</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="25"/>
        <source>File cannot be opened as a GeoTIFF file. Only valid geotiff files are allowed for uploading. You can use Raster-&gt;Conversion-&gt;Translate to change your file type to GeoTIFF</source>
        <translation>文件无法作为GeoTIFF文件打开。仅允许上传有效的geotiff文件。您可以使用栅格-&gt;转换-&gt;平移将文件类型更改为GeoTIFF</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="28"/>
        <source>File can&apos;t be uploaded, because the geometry of the image is too big, we will not be able to process it properly.Make sure that your image has valid CRS and transform, or cut the image into parts</source>
        <translation>文件无法上传，因为影像的几何范围太大，我们无法正确处理。请确保您的影像具有有效的坐标系和变换参数，或将影像分割为多个部分</translation>
    </message>
</context>
<context>
    <name>Dialog</name>
    <message>
        <location filename="../dialogs/static/ui/processing_dialog.ui" line="14"/>
        <source>Dialog</source>
        <translation>对话框</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_dialog.ui" line="20"/>
        <source>Name</source>
        <translation>名称</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_dialog.ui" line="34"/>
        <source>Description</source>
        <translation>描述</translation>
    </message>
</context>
<context>
    <name>ErrorMessageList</name>
    <message>
        <location filename="../errors/error_message_list.py" line="16"/>
        <source>Unknown error. Contact us to resolve the issue! help@geoalert.io</source>
        <translation>未知错误。请联系我们解决问题！help@geoalert.io</translation>
    </message>
</context>
<context>
    <name>Header</name>
    <message>
        <location filename="../functional/helpers.py" line="162"/>
        <source> | Project: </source>
        <translation> | 项目：</translation>
    </message>
    <message>
        <location filename="../functional/helpers.py" line="165"/>
        <source>owner: </source>
        <translation>所有者：</translation>
    </message>
</context>
<context>
    <name>LoginDialog</name>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="32"/>
        <source>Mapflow - Log In</source>
        <translation>Mapflow - 登录</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="53"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;span style=&quot; color:#ff0000;&quot;&gt;Authorization is not configured! &lt;/span&gt;&lt;/p&gt;&lt;p&gt;&lt;br/&gt;Setup authorization config &lt;br/&gt;and restart QGIS before login. &lt;br/&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow.html#oauth2_setup&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#094fd1;&quot;&gt;See documentation for help &lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;span style=&quot; color:#ff0000;&quot;&gt;授权未配置！&lt;/span&gt;&lt;/p&gt;&lt;p&gt;&lt;br/&gt;请设置授权配置&lt;br/&gt;并在登录前重启QGIS。&lt;br/&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow.html#oauth2_setup&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#094fd1;&quot;&gt;查看文档获取帮助&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="68"/>
        <source>Token</source>
        <translation>令牌</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="75"/>
        <source>This plugin is an interface to to the Mapflow.ai satellite image processing platform. You need to register an account to use it. </source>
        <translation>本插件是Mapflow.ai卫星影像处理平台的界面。您需要注册账户才能使用。</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="90"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href=&quot;https://app.mapflow.ai/account/api&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Get token&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;a href=&quot;https://mapflow.ai/terms-of-use-en.pdf&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Terms of use&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;Register at &lt;a href=&quot;https://mapflow.ai&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;mapflow.ai&lt;/span&gt;&lt;/a&gt; to use the plugin&lt;/p&gt;&lt;p&gt;&lt;br/&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href=&quot;https://app.mapflow.ai/account/api&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;获取令牌&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;a href=&quot;https://mapflow.ai/terms-of-use-en.pdf&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;使用条款&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;请到 &lt;a href=&quot;https://mapflow.ai&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;mapflow.ai&lt;/span&gt;&lt;/a&gt; 注册以使用插件&lt;/p&gt;&lt;p&gt;&lt;br/&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="111"/>
        <source>Use Oauth2</source>
        <translation>使用 Oauth2</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="131"/>
        <source>Cancel</source>
        <translation>取消</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="138"/>
        <source>Log in</source>
        <translation>登录</translation>
    </message>
</context>
<context>
    <name>MainDialog</name>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="106"/>
        <source>Name:</source>
        <translation>名称：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="139"/>
        <source>Area:</source>
        <translation>区域：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="146"/>
        <source>Create or load vector layer with your area of interest</source>
        <translation>创建或加载包含您感兴趣区域的矢量图层</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="249"/>
        <source>Data source:</source>
        <translation>数据源：</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="533"/>
        <source>Zoom</source>
        <translation>缩放级别</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="303"/>
        <source> –</source>
        <translation> –</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="308"/>
        <source>14</source>
        <translation>14</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="313"/>
        <source>15</source>
        <translation>15</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="318"/>
        <source>16</source>
        <translation>16</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="323"/>
        <source>17</source>
        <translation>17</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="328"/>
        <source>18</source>
        <translation>18</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="333"/>
        <source>19</source>
        <translation>19</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="338"/>
        <source>20</source>
        <translation>20</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="403"/>
        <source>AI model:</source>
        <translation>AI模型：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="450"/>
        <source>Price of the processing per sq.km</source>
        <translation>每平方公里处理价格</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="431"/>
        <source>CC</source>
        <translation>CC</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="453"/>
        <source>10</source>
        <translation>10</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="522"/>
        <source>Ctrl+S</source>
        <translation>Ctrl+S</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="536"/>
        <source>Model options: </source>
        <translation>模型选项：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="587"/>
        <source>Start processing</source>
        <translation>开始处理</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="469"/>
        <source>Rate processing:</source>
        <translation>评价处理：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="662"/>
        <source>...</source>
        <translation>...</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="667"/>
        <source>⭐⭐⭐⭐⭐</source>
        <translation>⭐⭐⭐⭐⭐</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="672"/>
        <source>⭐⭐⭐⭐</source>
        <translation>⭐⭐⭐⭐</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="677"/>
        <source>⭐⭐⭐</source>
        <translation>⭐⭐⭐</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="682"/>
        <source>⭐⭐</source>
        <translation>⭐⭐</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="687"/>
        <source>⭐</source>
        <translation>⭐</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="715"/>
        <source>Share your thoughts on what aspects of this data processing work well or could be improved</source>
        <translation>请分享您对本次数据处理表现良好或可改进方面的看法</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="727"/>
        <source>Accept</source>
        <translation>接受</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2954"/>
        <source>Review</source>
        <translation>审核</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="358"/>
        <source>Please select processing and rating to submit</source>
        <translation>请选择要提交的处理和评分</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="764"/>
        <source>Submit feedback</source>
        <translation>提交反馈</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="811"/>
        <source>Your balance:</source>
        <translation>您的余额：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="824"/>
        <source> Top up balance </source>
        <translation> 充值余额 </translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="841"/>
        <source>Open billing history</source>
        <translation>打开账单历史</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="870"/>
        <source>Log out</source>
        <translation>退出登录</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="902"/>
        <source>Processing</source>
        <translation>处理</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="976"/>
        <source>Sort by:</source>
        <translation>排序方式：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2857"/>
        <source>Name</source>
        <translation>名称</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2876"/>
        <source>Model</source>
        <translation>模型</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2889"/>
        <source>Status</source>
        <translation>状态</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1209"/>
        <source>Progress %</source>
        <translation>进度 %</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1214"/>
        <source>Area, sq. km</source>
        <translation>面积，平方公里</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2928"/>
        <source>Cost</source>
        <translation>费用</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2941"/>
        <source>Created</source>
        <translation>创建时间</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1229"/>
        <source>Review until</source>
        <translation>审核截止时间</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1250"/>
        <source>View results</source>
        <translation>查看结果</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1316"/>
        <source>Delete</source>
        <translation>删除</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1342"/>
        <source>Filter processings by name</source>
        <translation>按名称筛选处理</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1414"/>
        <source>Project:</source>
        <translation>项目：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1476"/>
        <source>Imagery search</source>
        <translation>影像搜索</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1482"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Here, you can search imagery for your area and timespan.&lt;/p&gt;&lt;p&gt;Additional filters are also available below.&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;在此处，您可以为您的区域和时间范围搜索影像。&lt;/p&gt;&lt;p&gt;下方还提供其他筛选条件。&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1485"/>
        <source>Provider Imagery Catalog</source>
        <translation>提供商影像目录</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1496"/>
        <source>Earlier images won&apos;t be shown</source>
        <translation>较早的影像将不会显示</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1499"/>
        <source>From:</source>
        <translation>从：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1550"/>
        <source>Dates are inclusive</source>
        <translation>日期包含起止日</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1567"/>
        <source>yyyy-MM-dd</source>
        <translation>yyyy-MM-dd</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1540"/>
        <source>More recent images won&apos;t be shown</source>
        <translation>较新的影像将不会显示</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1543"/>
        <source>To:</source>
        <translation>至：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1597"/>
        <source>Mosaic</source>
        <translation>镶嵌</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1607"/>
        <source>Image</source>
        <translation>影像</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1651"/>
        <source>Click and wait for a few seconds until the table below is filled out</source>
        <translation>点击并等待几秒钟，直到下方表格填充完成</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="302"/>
        <source>Search </source>
        <translation>搜索</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1671"/>
        <source>Double-click on a row to preview its image</source>
        <translation>双击某行以预览其影像</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1722"/>
        <source>1/1</source>
        <translation>1/1</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1764"/>
        <source>Clear </source>
        <translation>清除</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1791"/>
        <source>Click to specify additional search criteria</source>
        <translation>点击以指定其他搜索条件</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1794"/>
        <source>Additional filters</source>
        <translation>其他筛选条件</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1848"/>
        <source>%</source>
        <translation>%</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1834"/>
        <source>Min intersection:</source>
        <translation>最小交集：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1841"/>
        <source>Cloud cover up to:</source>
        <translation>云量最高：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1870"/>
        <source>Images that cover fewer % of your area won&apos;t be shown</source>
        <translation>覆盖您区域少于指定百分比的影像将不会显示</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1922"/>
        <source>Providers: </source>
        <translation>提供商：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1967"/>
        <source>Search only through available providers</source>
        <translation>仅通过可用提供商搜索</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1983"/>
        <source>My imagery</source>
        <translation>我的影像</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2008"/>
        <source>Add collection</source>
        <translation>添加影像集</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2021"/>
        <source>Delete collection</source>
        <translation>删除影像集</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2086"/>
        <source>No current selection</source>
        <translation>当前无选择</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2189"/>
        <source>Sort by</source>
        <translation>排序方式</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2241"/>
        <source>Imagery data</source>
        <translation>影像数据</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2507"/>
        <source>Settings</source>
        <translation>设置</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2534"/>
        <source>Add or edit imagery providers:</source>
        <translation>添加或编辑影像提供商：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2579"/>
        <source>Add your own web imagery provider</source>
        <translation>添加您自己的网络影像提供商</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2693"/>
        <source>Use all vector layers as Areas Of Interest</source>
        <translation>将所有矢量图层用作感兴趣区域</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2703"/>
        <source>Confirm processing start</source>
        <translation>确认开始处理</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2715"/>
        <source>view results as a vector tiles</source>
        <translation>以矢量切片形式查看结果</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2728"/>
        <source>save results as a local vector file</source>
        <translation>将结果保存为本地矢量文件</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2777"/>
        <source>Configure search table:</source>
        <translation>配置搜索表格：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2784"/>
        <source>Configure processings table:</source>
        <translation>配置处理表格：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2902"/>
        <source>Progress</source>
        <translation>进度</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2915"/>
        <source>Area</source>
        <translation>面积</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2967"/>
        <source>ID</source>
        <translation>ID</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3043"/>
        <source>Product Type</source>
        <translation>产品类型</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3059"/>
        <source>Provider Name</source>
        <translation>提供商名称</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3075"/>
        <source>Sensor</source>
        <translation>传感器</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3091"/>
        <source>Band Order</source>
        <translation>波段顺序</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3107"/>
        <source>Cloud %</source>
        <translation>云量 %</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3123"/>
        <source>° Off Nadir</source>
        <translation>° 离天底角</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3139"/>
        <source>Date and Time</source>
        <translation>日期和时间</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3155"/>
        <source>Mosaic Zoom</source>
        <translation>镶嵌缩放级别</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3168"/>
        <source>Image Spatial Resolution</source>
        <translation>影像空间分辨率</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3181"/>
        <source>Image ID</source>
        <translation>影像ID</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3194"/>
        <source>Preview</source>
        <translation>预览</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3226"/>
        <source>Set up local working directory, where all the temporary files will be stored</source>
        <translation>设置本地工作目录，所有临时文件将存储于此</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3244"/>
        <source>Output directory:</source>
        <translation>输出目录：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3330"/>
        <source>Help</source>
        <translation>帮助</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3339"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=&quot; margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#user-interface&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;User Interface walkthrough&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow.html#how-to-upload-your-image&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;How to process your own image&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#how-to-use-other-imagery-services&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;How to use a different imagery tileset (XYZ or TMS)&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#how-to-connect-to-maxar-securewatch&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;How to connect to Maxar SecureWatch&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=&quot; margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow credits&lt;/span&gt;&lt;span style=&quot; font-size:large; font-weight:700;&quot;&gt;&lt;br/&gt;&lt;/span&gt;&lt;/h3&gt;&lt;table border=&quot;0&quot; style=&quot; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;&quot; align=&quot;center&quot; cellspacing=&quot;2&quot; cellpadding=&quot;0&quot;&gt;&lt;thead&gt;&lt;tr&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:600;&quot;&gt;Pay as you go&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:696;&quot;&gt;$50&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:696;&quot;&gt;$90&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:696;&quot;&gt;$800&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/thead&gt;&lt;tr&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;Credits for processing&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;500&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;1000&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;10000&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/table&gt;&lt;p&gt;See also – &lt;a href=&quot;https://docs.mapflow.ai/userguides/prices.html&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#094fd1;&quot;&gt;How much do the processings and data cost?&lt;/span&gt;&lt;/a&gt;&lt;br/&gt;&lt;/p&gt;&lt;h3 style=&quot; margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Join the project on &lt;a href=&quot;https://github.com/Geoalert/mapflow-qgis&quot;&gt;&lt;span style=&quot; font-weight:600; text-decoration: underline; color:#0000ff;&quot;&gt;GitHub&lt;/span&gt;&lt;/a&gt; or &lt;a href=&quot;https://github.com/Geoalert/mapflow-qgis/issues&quot;&gt;&lt;span style=&quot; font-weight:600; text-decoration: underline; color:#0000ff;&quot;&gt;report an issue&lt;/span&gt;&lt;/a&gt;&lt;/span&gt;&lt;/h3&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=&quot; margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#user-interface&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;用户界面导览&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow.html#how-to-upload-your-image&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;如何处理自己的影像&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#how-to-use-other-imagery-services&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;如何使用其他影像瓦片集（XYZ或TMS）&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#how-to-connect-to-maxar-securewatch&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;如何连接到Maxar SecureWatch&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=&quot; margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow点数&lt;/span&gt;&lt;span style=&quot; font-size:large; font-weight:700;&quot;&gt;&lt;br/&gt;&lt;/span&gt;&lt;/h3&gt;&lt;table border=&quot;0&quot; style=&quot; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;&quot; align=&quot;center&quot; cellspacing=&quot;2&quot; cellpadding=&quot;0&quot;&gt;&lt;thead&gt;&lt;tr&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:600;&quot;&gt;按需付费&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:696;&quot;&gt;$50&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:696;&quot;&gt;$90&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:696;&quot;&gt;$800&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/thead&gt;&lt;tr&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;处理点数&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;500&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;1000&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;10000&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/table&gt;&lt;p&gt;另请参阅 – &lt;a href=&quot;https://docs.mapflow.ai/userguides/prices.html&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#094fd1;&quot;&gt;处理和数据费用是多少？&lt;/span&gt;&lt;/a&gt;&lt;br/&gt;&lt;/p&gt;&lt;h3 style=&quot; margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;在 &lt;a href=&quot;https://github.com/Geoalert/mapflow-qgis&quot;&gt;&lt;span style=&quot; font-weight:600; text-decoration: underline; color:#0000ff;&quot;&gt;GitHub&lt;/span&gt;&lt;/a&gt; 上加入项目或在 &lt;a href=&quot;https://github.com/Geoalert/mapflow-qgis/issues&quot;&gt;&lt;span style=&quot; font-weight:600; text-decoration: underline; color:#0000ff;&quot;&gt;此报告问题&lt;/span&gt;&lt;/a&gt;&lt;/span&gt;&lt;/h3&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3366"/>
        <source>see_details_action</source>
        <translation>查看详情操作</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="129"/>
        <source>Save results</source>
        <translation>保存结果</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="130"/>
        <source>Download AOI</source>
        <translation>下载感兴趣区域</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="131"/>
        <source>See details</source>
        <translation>查看详情</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="132"/>
        <source>Rename</source>
        <translation>重命名</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="133"/>
        <source>Restart</source>
        <translation>重新开始</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="134"/>
        <source>Duplicate</source>
        <translation>复制</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="319"/>
        <source>
Price: {} credits per square km</source>
        <translation>
价格：每平方公里 {} 点数</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="330"/>
        <source>Rate processing &lt;b&gt;{name}&lt;/b&gt;:</source>
        <translation>评价处理 &lt;b&gt;{name}&lt;/b&gt;：</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="459"/>
        <source>Not enough rights to start processing in a shared project ({})</source>
        <translation>权限不足，无法在共享项目（{}）中开始处理</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="472"/>
        <source>Not enough rights to rate processing in a shared project ({})</source>
        <translation>权限不足，无法在共享项目（{}）中评价处理</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="474"/>
        <source>Please select processing</source>
        <translation>请选择处理</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="478"/>
        <source>Not enough rights to delete processing in a shared project ({})</source>
        <translation>权限不足，无法在共享项目（{}）中删除处理</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="511"/>
        <source>Delete project</source>
        <translation>删除项目</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="512"/>
        <source>Edit project</source>
        <translation>编辑项目</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="528"/>
        <source>Zoom is derived from found imagery resolution</source>
        <translation>缩放级别根据找到的影像分辨率推算</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="543"/>
        <source>Previous page</source>
        <translation>上一页</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="544"/>
        <source>Next page</source>
        <translation>下一页</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="545"/>
        <source>Page</source>
        <translation>页码</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="623"/>
        <source>&lt;b&gt;URL:&lt;/b&gt; {url}&lt;br&gt;&lt;b&gt;Source type:&lt;/b&gt; {type}</source>
        <translation>&lt;b&gt;URL：&lt;/b&gt; {url}&lt;br&gt;&lt;b&gt;源类型：&lt;/b&gt; {type}</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="627"/>
        <source>&lt;br&gt;&lt;b&gt;CRS:&lt;/b&gt; {crs}</source>
        <translation>&lt;br&gt;&lt;b&gt;坐标系：&lt;/b&gt; {crs}</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="629"/>
        <source>&lt;br&gt;&lt;b&gt;Zoom:&lt;/b&gt; {zoom}</source>
        <translation>&lt;br&gt;&lt;b&gt;缩放级别：&lt;/b&gt; {zoom}</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="631"/>
        <source>&lt;br&gt;&lt;b&gt;Raster login:&lt;/b&gt; {login}&lt;br&gt;&lt;b&gt;Raster password:&lt;/b&gt; {password}</source>
        <translation>&lt;br&gt;&lt;b&gt;栅格登录名：&lt;/b&gt; {login}&lt;br&gt;&lt;b&gt;栅格密码：&lt;/b&gt; {password}</translation>
    </message>
</context>
<context>
    <name>Mapflow</name>
    <message>
        <location filename="../mapflow.py" line="228"/>
        <source>Error during loading the data providers: {e}</source>
        <translation>加载数据提供商时出错：{e}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="230"/>
        <source>We failed to import providers from the settings. Please add them again</source>
        <translation>我们从设置导入提供商失败。请重新添加</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="323"/>
        <source>Draw AOI at the map</source>
        <translation>在地图上绘制感兴趣区域</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1752"/>
        <source>Use imagery extent</source>
        <translation>使用影像范围</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="326"/>
        <source>Create AOI from map extent</source>
        <translation>从地图范围创建感兴趣区域</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="725"/>
        <source>Project: &lt;b&gt;{}</source>
        <translation>项目：&lt;b&gt;{}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="470"/>
        <source>Choose imagery collection or image to start processing</source>
        <translation>选择影像集或影像以开始处理</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="639"/>
        <source>Log in </source>
        <translation>登录</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="739"/>
        <source>No project selected</source>
        <translation>未选择项目</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="741"/>
        <source>You can&apos;t remove or modify default project</source>
        <translation>您不能删除或修改默认项目</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="744"/>
        <source>Not enough rights to delete or update shared project ({})</source>
        <translation>权限不足，无法删除或更新共享项目（{}）</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="763"/>
        <source>Do you really want to remove project {}? This action cannot be undone, all processings will be lost!</source>
        <translation>您确定要删除项目 {} 吗？此操作无法撤销，所有处理都将丢失！</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="782"/>
        <source>This provider is default and cannot be removed</source>
        <translation>此提供商为默认提供商，无法删除</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="786"/>
        <source>Permanently remove {}?</source>
        <translation>永久删除 {}？</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="818"/>
        <source>Provider name must be unique. {name} already exists, select another or delete/edit existing</source>
        <translation>提供商名称必须唯一。{name} 已存在，请选择其他名称或删除/编辑现有项</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="830"/>
        <source>Add new provider</source>
        <translation>添加新提供商</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="838"/>
        <source>This is a default provider, it cannot be edited</source>
        <translation>此为默认提供商，无法编辑</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="897"/>
        <source>If you already know which {provider_name} image you want to process,
simply paste its ID here. Otherwise, search suitable images in the catalog below.</source>
        <translation>如果您已确定要处理哪个 {provider_name} 影像，只需将其ID粘贴在此处。否则，请在下方目录中搜索合适的影像。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="889"/>
        <source>e.g. S2B_OPER_MSI_L1C_TL_VGS4_20220209T091044_A025744_T36SXA_N04_00</source>
        <translation>例如：S2B_OPER_MSI_L1C_TL_VGS4_20220209T091044_A025744_T36SXA_N04_00</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="901"/>
        <source>e.g. a3b154c40cc74f3b934c0ffc9b34ecd1</source>
        <translation>例如：a3b154c40cc74f3b934c0ffc9b34ecd1</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="930"/>
        <source>Select output directory</source>
        <translation>选择输出目录</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="948"/>
        <source>Please, specify an existing output directory</source>
        <translation>请指定一个现有的输出目录</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1936"/>
        <source>Please, select a valid area of interest</source>
        <translation>请选择有效的感兴趣区域</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1102"/>
        <source>We couldn&apos;t get metadata from the Mapflow Imagery Catalog</source>
        <translation>我们无法从Mapflow影像目录获取元数据</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1105"/>
        <source>. Error {error}</source>
        <translation>。错误 {error}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1506"/>
        <source>No images match your criteria. Try relaxing the filters.</source>
        <translation>没有符合您条件的影像。请尝试放宽筛选条件。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1149"/>
        <source>&lt;b&gt;Results could not be loaded &lt;/b&gt;&lt;br&gt;Please, make sure you chose the right output folder in the Settings tab                                 and you have access rights to this folder</source>
        <translation>&lt;b&gt;结果无法加载&lt;/b&gt;&lt;br&gt;请确保您在设置选项卡中选择了正确的输出文件夹，并且您有访问该文件夹的权限</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1192"/>
        <source>Your area of interest is too large.</source>
        <translation>您的感兴趣区域太大。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1295"/>
        <source>Please, check your credentials</source>
        <translation>请检查您的凭据</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1449"/>
        <source>We couldn&apos;t fetch Sentinel metadata</source>
        <translation>我们无法获取Sentinel元数据</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1416"/>
        <source>More</source>
        <translation>更多</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1535"/>
        <source>Please, check your Maxar credentials</source>
        <translation>请检查您的Maxar凭据</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1537"/>
        <source>We couldn&apos;t get metadata from Maxar, error {error}</source>
        <translation>我们无法从Maxar获取元数据，错误 {error}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1640"/>
        <source>A Sentinel image ID should look like S2B_OPER_MSI_L1C_TL_VGS4_20220209T091044_A025744_T36SXA_N04_00 or /36/S/XA/2022/02/09/0/</source>
        <translation>Sentinel影像ID应类似 S2B_OPER_MSI_L1C_TL_VGS4_20220209T091044_A025744_T36SXA_N04_00 或 /36/S/XA/2022/02/09/0/</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1648"/>
        <source>A Maxar image ID should look like a3b154c40cc74f3b934c0ffc9b34ecd1</source>
        <translation>Maxar影像ID应类似 a3b154c40cc74f3b934c0ffc9b34ecd1</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1876"/>
        <source>Not enough rights to start processing in a shared project ({})</source>
        <translation>权限不足，无法在共享项目（{}）中开始处理</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1830"/>
        <source>Set AOI to start processing</source>
        <translation>设置感兴趣区域以开始处理</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1688"/>
        <source>AOI must contain not more than {} polygons</source>
        <translation>感兴趣区域不能包含超过 {} 个多边形</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1742"/>
        <source>Use extent of &apos;{name}&apos;</source>
        <translation>使用 '{name}' 的范围</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1744"/>
        <source>Select AOI to start processing</source>
        <translation>选择感兴趣区域以开始处理</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2081"/>
        <source>Selected AOI does not intersect the selected imagery</source>
        <translation>选择的感兴趣区域与所选影像没有交集</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1820"/>
        <source>Area: {:.2f} sq.km</source>
        <translation>面积：{:.2f} 平方公里</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1833"/>
        <source>Error! Models are not initialized.
Please, make sure you have selected a project</source>
        <translation>错误！模型未初始化。
请确保您已选择项目</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1845"/>
        <source>Processing cost is not available:
{error}</source>
        <translation>处理费用不可用：
{error}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2083"/>
        <source>This provider requires image ID. Use search tab to find imagery for you requirements, and select image in the table.</source>
        <translation>此提供商需要影像ID。请使用搜索选项卡查找符合您要求的影像，并在表格中选择影像。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1854"/>
        <source>Choose imagery to start processing</source>
        <translation>选择影像以开始处理</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1878"/>
        <source>Processing cost is not available:
{message}</source>
        <translation>处理费用不可用：
{message}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1885"/>
        <source>Processsing cost: {cost} credits</source>
        <translation>处理费用：{cost} 点数</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1899"/>
        <source>Delete selected processings?</source>
        <translation>删除选中的处理？</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1925"/>
        <source>Error deleting a processing</source>
        <translation>删除处理时出错</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1931"/>
        <source>Please, specify a name for your processing</source>
        <translation>请为您的处理指定一个名称</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1934"/>
        <source>Processing area layer is corrupted or has invalid projection</source>
        <translation>处理区域图层已损坏或具有无效投影</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1938"/>
        <source>Up to {} sq km can be processed at a time. Try splitting your area(s) into several processings.</source>
        <translation>一次最多可处理 {} 平方公里。请尝试将您的区域分割为多个处理。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1983"/>
        <source>Providers are not initialized</source>
        <translation>提供商未初始化</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1978"/>
        <source>Bad AOI. AOI must be inside boundaries: 
[-180, 180] by longitude, [-90, 90] by latitude</source>
        <translation>无效的感兴趣区域。感兴趣区域必须在边界内： 
经度 [-180, 180]，纬度 [-90, 90]</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2088"/>
        <source>No project is selected</source>
        <translation>未选择项目</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2117"/>
        <source>Processing limit exceeded. Visit &quot;&lt;a href=&quot;https://app.mapflow.ai/account/balance&quot;&gt;Mapflow&lt;/a&gt;&quot; to top up your balance</source>
        <translation>超出处理限制。请访问 &quot;&lt;a href=&quot;https://app.mapflow.ai/account/balance&quot;&gt;Mapflow&lt;/a&gt;&quot; 充值余额</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2124"/>
        <source>Starting the processing...</source>
        <translation>正在开始处理...</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2129"/>
        <source>Could not launch processing! Error: {}.</source>
        <translation>无法启动处理！错误：{}。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2143"/>
        <source>{cost} credits</source>
        <translation>{cost} 点数</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2176"/>
        <source> sq.km</source>
        <translation> 平方公里</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2205"/>
        <source>We couldn&apos;t upload your GeoTIFF</source>
        <translation>我们无法上传您的GeoTIFF文件</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2227"/>
        <source>Success! We&apos;ll notify you when the processing has finished.</source>
        <translation>成功！处理完成后我们将通知您。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2249"/>
        <source>The selected data provider is unavailable on your plan. 
 Upgrade your subscription to get access to the data. 
See pricing at &lt;a href=&quot;https://mapflow.ai/pricing&quot;&gt;mapflow.ai&lt;/a&gt;</source>
        <translation>所选数据提供商在您的订阅计划中不可用。
升级订阅以获取数据访问权限。
请查看 &lt;a href=&quot;https://mapflow.ai/pricing&quot;&gt;mapflow.ai&lt;/a&gt; 的定价</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2260"/>
        <source>Processing creation failed</source>
        <translation>处理创建失败</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2290"/>
        <source>Your balance: {} credits</source>
        <translation>您的余额：{} 点数</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2292"/>
        <source>Remaining limit: {:.2f} sq.km</source>
        <translation>剩余限制：{:.2f} 平方公里</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2338"/>
        <source>Show all</source>
        <translation>显示全部</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2388"/>
        <source>Sorry, we couldn&apos;t load the image</source>
        <translation>抱歉，我们无法加载该影像</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2389"/>
        <source>Error previewing Sentinel imagery</source>
        <translation>预览Sentinel影像时出错</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2394"/>
        <source>Preview is unavailable when metadata layer is removed</source>
        <translation>元数据图层被移除时预览不可用</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2427"/>
        <source>Selected imagery has no preview</source>
        <translation>所选影像无预览</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2432"/>
        <source>Preview with such URL is unavailable</source>
        <translation>该URL的预览不可用</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2439"/>
        <source>Preview for &apos;{iid}&apos; is unavailable</source>
        <translation>'{iid}' 的预览不可用</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2572"/>
        <source>Could not display preview</source>
        <translation>无法显示预览</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2606"/>
        <source>Sorry, there&apos;s no preview for this image</source>
        <translation>抱歉，此影像无预览</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2710"/>
        <source>We couldn&apos;t load a preview for this image</source>
        <translation>我们无法加载此影像的预览</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2621"/>
        <source>Please, select an image to preview</source>
        <translation>请选择要预览的影像</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2681"/>
        <source>Provider {name} requires image id for preview!</source>
        <translation>提供商 {name} 需要影像ID才能预览！</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2685"/>
        <source>Preview is unavailable for the provider {}. 
OSM layer will be added instead.</source>
        <translation>提供商 {} 的预览不可用。
将添加OSM图层作为替代。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2722"/>
        <source>This provider requires image ID!</source>
        <translation>此提供商需要影像ID！</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2847"/>
        <source>Only finished processings can be rated</source>
        <translation>仅完成处理可被评价</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2850"/>
        <source>Processing must be in `Review required` status</source>
        <translation>处理必须处于“需要审核”状态</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2866"/>
        <source>Thank you! Your rating is submitted!
We would appreciate if you add feedback as well.</source>
        <translation>谢谢！您的评价已提交！
如能同时提供反馈我们将不胜感激。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2873"/>
        <source>Thank you! Your rating and feedback are submitted!</source>
        <translation>谢谢！您的评价和反馈已提交！</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2882"/>
        <source>Only correctly finished processings (status OK) can be reviewed</source>
        <translation>仅正确完成（状态为OK）的处理可被审核</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2888"/>
        <source>Not enough rights to rate processing in a shared project ({})</source>
        <translation>权限不足，无法在共享项目（{}）中评价处理</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2891"/>
        <source>Please select processing</source>
        <translation>请选择处理</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2893"/>
        <source>Only correctly finished processings (status OK) can be rated</source>
        <translation>仅正确完成（状态为OK）的处理可被评价</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2895"/>
        <source>Please select rating to submit</source>
        <translation>请选择要提交的评分</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2955"/>
        <source>Only the results of correctly finished processing can be loaded</source>
        <translation>仅正确完成的处理结果可被加载</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2939"/>
        <source>Directory &apos;{}&apos; does not exist</source>
        <translation>目录 '{}' 不存在</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2939"/>
        <source>&lt;br&gt;Using Settings tab, change the output directory to an existing one to download the results</source>
        <translation>&lt;br&gt;请使用设置选项卡，将输出目录更改为现有目录以下载结果</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3050"/>
        <source> failed with error:
</source>
        <translation> 失败，错误：
</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3057"/>
        <source>{} processings failed: 
 {} 
 See tooltip over the processings table for error details</source>
        <translation>{} 个处理失败： 
 {} 
 请查看处理表格上的工具提示以获取错误详情</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3064"/>
        <source>{} processings failed: 
 See tooltip over the processings table for error details</source>
        <translation>{} 个处理失败： 
 请查看处理表格上的工具提示以获取错误详情</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3076"/>
        <source> finished. Double-click it in the table to download the results.</source>
        <translation> 已完成。双击表格中的该项以下载结果。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3084"/>
        <source>{} processings finished: 
 {} 
 Double-click it in the table to download the results</source>
        <translation>{} 个处理完成： 
 {} 
 双击表格中的该项以下载结果</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3092"/>
        <source>{} processings finished. 
 Double-click it in the table to download the results</source>
        <translation>{} 个处理完成。 
 双击表格中的该项以下载结果</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3123"/>
        <source>Please review or accept this processing until {}. Double click to add results to the map</source>
        <translation>请在 {} 前审核或接受此处理。双击以将结果添加到地图</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3128"/>
        <source>Double click to add results to the map.</source>
        <translation>双击以将结果添加到地图。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3190"/>
        <source>We have just set the authentication config for you. 
 You may need to restart QGIS to apply it so you could log in</source>
        <translation>我们已为您设置认证配置。
您可能需要重启QGIS以应用配置，然后才能登录</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3215"/>
        <source>Please restart QGIS before using OAuth2 login.</source>
        <translation>使用OAuth2登录前请重启QGIS。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3277"/>
        <source>Wrong token. Visit &quot;&lt;a href=&quot;https://app.mapflow.ai/account/api&quot;&gt;mapflow.ai&lt;/a&gt;&quot; to get a new one</source>
        <translation>令牌错误。请访问 &quot;&lt;a href=&quot;https://app.mapflow.ai/account/api&quot;&gt;mapflow.ai&lt;/a&gt;&quot; 获取新令牌</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3309"/>
        <source>Proxy error. Please, check your proxy settings.</source>
        <translation>代理错误。请检查您的代理设置。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3313"/>
        <source>Not enough rights for this action
in a shared project &apos;{project_name}&apos; ({user_role})</source>
        <translation>在共享项目 '{project_name}'（{user_role}）中权限不足，无法执行此操作</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3319"/>
        <source>This operation is forbidden for your account, contact us</source>
        <translation>您的账户无权执行此操作，请联系我们</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3324"/>
        <source>Error</source>
        <translation>错误</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3427"/>
        <source>No project that meets specified criteria was found</source>
        <translation>未找到符合指定条件的项目</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3431"/>
        <source>Project</source>
        <translation>项目</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3472"/>
        <source>You must upgrade your plugin version to continue work with Mapflow. 
The server requires version {server_version}, your plugin is {local_version}
Go to Plugins -&gt; Manage and Install Plugins -&gt; Upgradable</source>
        <translation>您必须升级插件版本才能继续使用Mapflow。
服务器要求版本 {server_version}，您的插件版本为 {local_version}
请转到插件 -&gt; 管理和安装插件 -&gt; 可升级</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3482"/>
        <source>A new version of Mapflow plugin {server_version} is released 
We recommend you to upgrade to get all the latest features
Go to Plugins -&gt; Manage and Install Plugins -&gt; Upgradable</source>
        <translation>Mapflow插件新版本 {server_version} 已发布
我们建议您升级以获取所有最新功能
请转到插件 -&gt; 管理和安装插件 -&gt; 可升级</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3597"/>
        <source>You can launch multiple image processing only if they have the same provider</source>
        <translation>仅当多个影像处理使用相同提供商时，您才能启动它们</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3626"/>
        <source>Selected search results must have the same zoom level</source>
        <translation>选中的搜索结果必须具有相同的缩放级别</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3722"/>
        <source>Duplication failed on copying data source</source>
        <translation>复制数据源时复制失败</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3730"/>
        <source>Model &apos;{wd}&apos; is not enabled for your account</source>
        <translation>模型 '{wd}' 对您的账户未启用</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3737"/>
        <source>Duplication failed on copying model</source>
        <translation>复制模型时复制失败</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3759"/>
        <source>The following options no longer exist, so they have not been duplicated: {}</source>
        <translation>以下选项已不存在，因此未被复制：{}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3764"/>
        <source>Duplication failed on copying model options</source>
        <translation>复制模型选项时复制失败</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3773"/>
        <source>Provider &apos;{provider}&apos; is not enabled for your account</source>
        <translation>提供商 '{provider}' 对您的账户未启用</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3848"/>
        <source>Duplicated user provider</source>
        <translation>已复制用户提供商</translation>
    </message>
</context>
<context>
    <name>MapflowLoginDialog</name>
    <message>
        <location filename="../dialogs/login_dialog.py" line="32"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;You will be redirecrted to web browser &lt;br/&gt;to enter your Mapflow login and password&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;您将被重定向到网页浏览器&lt;br/&gt;以输入您的Mapflow登录名和密码&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/login_dialog.py" line="33"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;span style=&quot; color:#ff0000;&quot;&gt;Authorization is not completed! &lt;/span&gt;&lt;/p&gt;&lt;p&gt;&lt;br/&gt;1. Complete authorization in browser. &lt;br/&gt;&lt;br/&gt;2. If it does not help, restart QGIS. &lt;br/&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow.html#oauth2_setup&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#094fd1;&quot;&gt;See documentation for help &lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;span style=&quot; color:#ff0000;&quot;&gt;授权未完成！&lt;/span&gt;&lt;/p&gt;&lt;p&gt;&lt;br/&gt;1. 在浏览器中完成授权。&lt;br/&gt;&lt;br/&gt;2. 如果无效，请重启QGIS。&lt;br/&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow.html#oauth2_setup&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#094fd1;&quot;&gt;查看文档获取帮助&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/login_dialog.py" line="38"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href=&quot;https://app.mapflow.ai/account/api&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Get token&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;a href=&quot;https://mapflow.ai/terms-of-use-en.pdf&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Terms of use&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;Register at &lt;a href=&quot;https://mapflow.ai&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;mapflow.ai&lt;/span&gt;&lt;/a&gt; to use the plugin&lt;/p&gt;&lt;p&gt;&lt;br/&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href=&quot;https://app.mapflow.ai/account/api&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;获取令牌&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;a href=&quot;https://mapflow.ai/terms-of-use-en.pdf&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;使用条款&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;请到 &lt;a href=&quot;https://mapflow.ai&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;mapflow.ai&lt;/span&gt;&lt;/a&gt; 注册以使用插件&lt;/p&gt;&lt;p&gt;&lt;br/&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/login_dialog.py" line="39"/>
        <source>Invalid credentials</source>
        <translation>无效凭据</translation>
    </message>
</context>
<context>
    <name>MosaicDialog</name>
    <message>
        <location filename="../dialogs/mosaic_dialog.py" line="19"/>
        <source>Imagery collection name must not be empty!</source>
        <translation>影像集名称不能为空！</translation>
    </message>
</context>
<context>
    <name>ProcessingDetailsDialog</name>
    <message>
        <location filename="../dialogs/processing_details_dialog.py" line="15"/>
        <source>Processing details</source>
        <translation>处理详情</translation>
    </message>
    <message>
        <location filename="../dialogs/processing_details_dialog.py" line="49"/>
        <source>My imagery</source>
        <translation>我的影像</translation>
    </message>
</context>
<context>
    <name>ProcessingErrors</name>
    <message>
        <location filename="../errors/processing_errors.py" line="8"/>
        <source>Folder `{s3_link}` selected for processing does not contain any images. </source>
        <translation>选择用于处理的文件夹 `{s3_link}` 不包含任何影像。</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="10"/>
        <source>Task for source-validation must contain area of interest (`geometry` section)</source>
        <translation>源验证任务必须包含感兴趣区域（`geometry`部分）</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="12"/>
        <source>We could not open and read the image you have uploaded</source>
        <translation>我们无法打开并读取您上传的影像</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="13"/>
        <source>Image profile (metadata) must have keys {required_keys}, got profile {profile}</source>
        <translation>影像配置文件（元数据）必须包含键 {required_keys}，实际配置为 {profile}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="15"/>
        <source>AOI does not intersect the selected Sentinel-2 granule {actual_cell}</source>
        <translation>感兴趣区域与选定的Sentinel-2数据块 {actual_cell} 不相交</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="17"/>
        <source>Key &apos;url&apos; in your request must be a string, got {url_type} instead.</source>
        <translation>请求中的键 'url' 必须是字符串，实际为 {url_type}。</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="19"/>
        <source>The specified basemap {url} is forbidden for processing because it contains a map, not satellite image. Our models are suited for satellite imagery.</source>
        <translation>指定的底图 {url} 因包含地图而非卫星影像而被禁止处理。我们的模型适用于卫星影像。</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="22"/>
        <source>Your URL must be a link starting with &quot;http://&quot; or &quot;https://&quot;.</source>
        <translation>您的URL必须是以 &quot;http://&quot; 或 &quot;https://&quot; 开头的链接。</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="24"/>
        <source>Format of &apos;url&apos; is invalid and cannot be parsed. Error: {parse_error_message}</source>
        <translation>'url' 的格式无效且无法解析。错误：{parse_error_message}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="26"/>
        <source>Zoom must be either empty, or integer, got {actual_zoom}</source>
        <translation>缩放级别必须为空或整数，实际为 {actual_zoom}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="28"/>
        <source>Zoom must be between 0 and 22, got {actual_zoom}</source>
        <translation>缩放级别必须在0到22之间，实际为 {actual_zoom}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="29"/>
        <source>Zoom must be not lower than {min_zoom}, got {actual_zoom}</source>
        <translation>缩放级别不能低于 {min_zoom}，实际为 {actual_zoom}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="30"/>
        <source>Image metadata must be a dict (json)</source>
        <translation>影像元数据必须是字典（json）</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="31"/>
        <source>Image metadata must have keys: crs, transform, dtype, count</source>
        <translation>影像元数据必须包含键：crs, transform, dtype, count</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="33"/>
        <source>URL of the image at s3 storage must be a string starting with s3://, got {actual_s3_link}</source>
        <translation>s3存储中影像的URL必须是以 s3:// 开头的字符串，实际为 {actual_s3_link}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="35"/>
        <source>Request must contain either &apos;profile&apos; or &apos;url&apos; keys</source>
        <translation>请求必须包含 'profile' 或 'url' 键</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="36"/>
        <source>Failed to read file from {s3_link}.</source>
        <translation>无法从 {s3_link} 读取文件。</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="37"/>
        <source>Image data type (Dtype) must be one of {required_dtypes}, got {request_dtype}</source>
        <translation>影像数据类型（Dtype）必须是 {required_dtypes} 之一，实际为 {request_dtype}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="39"/>
        <source>Number of channels in image must be one of {required_nchannels}. Got {real_nchannels}</source>
        <translation>影像中的通道数必须是 {required_nchannels} 之一。实际为 {real_nchannels}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="41"/>
        <source>Spatial resolution of you image is too high: pixel size is {actual_res}, minimum allowed pixel size is {min_res}</source>
        <translation>您的影像空间分辨率过高：像素大小为 {actual_res}，允许的最小像素大小为 {min_res}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="44"/>
        <source>Spatial resolution of you image is too low: pixel size is {actual_res}, maximum allowed pixel size is {max_res}</source>
        <translation>您的影像空间分辨率过低：像素大小为 {actual_res}，允许的最大像素大小为 {max_res}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="47"/>
        <source>Error occurred during image {checked_param} check: {message}. Image metadata = {metadata}.</source>
        <translation>影像 {checked_param} 检查期间发生错误：{message}。影像元数据 = {metadata}。</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="49"/>
        <source>Your &apos;url&apos; doesn&apos;t match the format, Quadkey basemap must be a link containing &quot;q&quot; placeholder.</source>
        <translation>您的 'url' 格式不匹配，Quadkey底图必须是包含 &quot;q&quot; 占位符的链接。</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="52"/>
        <source>Input string {input_string} is of unknown format. It must represent Sentinel-2 granule ID.</source>
        <translation>输入字符串 {input_string} 格式未知。它必须表示Sentinel-2数据块ID。</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="54"/>
        <source>Selected Sentinel-2 image cell is {actual_cell}, this model is for the cells: {allowed_cells}</source>
        <translation>选定的Sentinel-2影像单元为 {actual_cell}，此模型适用于以下单元：{allowed_cells}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="56"/>
        <source>Selected Sentinel-2 image month is {actual_month}, this model is for: {allowed_months}</source>
        <translation>选定的Sentinel-2影像月份为 {actual_month}，此模型适用于以下月份：{allowed_months}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="58"/>
        <source>You request TMS basemap link doesn&apos;t match the format, it must be a link containing &quot;x&quot;, &quot;y&quot;, &quot;z&quot; placeholders, correct it and start processing again.</source>
        <translation>您请求的TMS底图链接格式不匹配，它必须是包含 &quot;x&quot;、&quot;y&quot;、&quot;z&quot; 占位符的链接，请修正后重新开始处理。</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="61"/>
        <source>Requirements must be dict, got {requirements_type}.</source>
        <translation>要求必须是字典，实际为 {requirements_type}。</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="62"/>
        <source>Request must be dict, got {request_type}.</source>
        <translation>请求必须是字典，实际为 {request_type}。</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="63"/>
        <source>Request must contain &quot;source_type&quot; key</source>
        <translation>请求必须包含 &quot;source_type&quot; 键</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="64"/>
        <source>Source type {source_type} is not allowed. Use one of: {allowed_sources}</source>
        <translation>源类型 {source_type} 不被允许。请使用以下之一：{allowed_sources}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="66"/>
        <source>&quot;Required&quot; section of the requirements must contain dict, not {required_section_type}</source>
        <translation>要求的 &quot;Required&quot; 部分必须是字典，实际为 {required_section_type}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="68"/>
        <source>&quot;Recommended&quot; section of the requirements must contain dict, not {recommended_section_type}</source>
        <translation>要求的 &quot;Recommended&quot; 部分必须是字典，实际为 {recommended_section_type}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="70"/>
        <source>You XYZ basemap link doesn&apos;t match the format, it must be a link containing &quot;x&quot;, &quot;y&quot;, &quot;z&quot;  placeholders.</source>
        <translation>您的XYZ底图链接格式不匹配，它必须是包含 &quot;x&quot;、&quot;y&quot;、&quot;z&quot; 占位符的链接。</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="75"/>
        <source>Internal error in process of data source validation. We are working on the fix, our support will contact you.</source>
        <translation>数据源验证过程中发生内部错误。我们正在修复，我们的支持团队将联系您。</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="96"/>
        <source>Internal error in process of loading data. We are working on the fix, our support will contact you.</source>
        <translation>数据加载过程中发生内部错误。我们正在修复，我们的支持团队将联系您。</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="79"/>
        <source>Wrong source type {real_source_type}. Specify one of the allowed types {allowed_source_types}.</source>
        <translation>错误的源类型 {real_source_type}。请指定允许的类型之一 {allowed_source_types}。</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="81"/>
        <source>Your data loading task requires {estimated_size} MB of memory, which exceeded allowed memory limit {allowed_size}</source>
        <translation>您的数据加载任务需要 {estimated_size} MB 内存，超过了允许的内存限制 {allowed_size}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="83"/>
        <source>Dataloader argument {argument_name} has type {argument_type}, excpected to be {expected_type}</source>
        <translation>数据加载器参数 {argument_name} 的类型为 {argument_type}，预期为 {expected_type}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="85"/>
        <source>Loaded tile has {real_nchannels} channels, required number is {expected_nchannels}</source>
        <translation>加载的瓦片具有 {real_nchannels} 个通道，要求通道数为 {expected_nchannels}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="87"/>
        <source>Loaded tile has size {real_size}, expected tile size is {expected_size}</source>
        <translation>加载的瓦片大小为 {real_size}，预期瓦片大小为 {expected_size}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="89"/>
        <source>Tile at location {tile_location} cannot be loaded, server response is {status}</source>
        <translation>无法加载位置 {tile_location} 的瓦片，服务器响应为 {status}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="91"/>
        <source>Response content at {tile_location} cannot be decoded as an image</source>
        <translation>{tile_location} 的响应内容无法解码为影像</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="98"/>
        <source>The data provider contains no data for your area of interest (returned NoData tiles). Try other the data sources to get the results.</source>
        <translation>数据提供商在您的感兴趣区域没有数据（返回无数据瓦片）。请尝试其他数据源以获取结果。</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="100"/>
        <source>Internal error in process of data preparation. We are working on the fix, our support will contact you.</source>
        <translation>数据准备过程中发生内部错误。我们正在修复，我们的支持团队将联系您。</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="102"/>
        <source>Internal error in process of data processing. We are working on the fix, our support will contact you.</source>
        <translation>数据处理过程中发生内部错误。我们正在修复，我们的支持团队将联系您。</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="104"/>
        <source>Internal error in process of saving the results. We are working on the fix, our support will contact you.</source>
        <translation>结果保存过程中发生内部错误。我们正在修复，我们的支持团队将联系您。</translation>
    </message>
</context>
<context>
    <name>ProjectDialog</name>
    <message>
        <location filename="../dialogs/static/ui/processing_details.ui" line="14"/>
        <source>Project</source>
        <translation>项目</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/project_dialog.ui" line="20"/>
        <source>Name</source>
        <translation>名称</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/mosaic_dialog.ui" line="34"/>
        <source>Tags</source>
        <translation>标签</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/mosaic_dialog.ui" line="51"/>
        <source>Note: separate tags with comma (&quot;, &quot;) </source>
        <translation>注意：使用逗号（&quot;, &quot;）分隔标签</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/mosaic_dialog.ui" line="75"/>
        <source>Create empty mosaic</source>
        <translation>创建空影像集</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/mosaic_dialog.ui" line="80"/>
        <source>Upload from files</source>
        <translation>从文件上传</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/mosaic_dialog.ui" line="85"/>
        <source>Choose raster layers</source>
        <translation>选择栅格图层</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/project_dialog.ui" line="34"/>
        <source>Description</source>
        <translation>描述</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="26"/>
        <source>Start processing with specified parameters?</source>
        <translation>是否使用指定参数开始处理？</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="66"/>
        <source>Area:</source>
        <translation>区域：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_details.ui" line="336"/>
        <source>Name:</source>
        <translation>名称：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="132"/>
        <source>Data source:</source>
        <translation>数据源：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_details.ui" line="460"/>
        <source>Zoom:</source>
        <translation>缩放级别：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_details.ui" line="476"/>
        <source>Model options:</source>
        <translation>模型选项：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="248"/>
        <source>Price:</source>
        <translation>价格：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_details.ui" line="124"/>
        <source>Model:</source>
        <translation>模型：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="428"/>
        <source>Don&apos;t show this message again</source>
        <translation>不再显示此消息</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_details.ui" line="177"/>
        <source>ID:</source>
        <translation>ID：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_details.ui" line="193"/>
        <source>Status:</source>
        <translation>状态：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_details.ui" line="209"/>
        <source>Description:</source>
        <translation>描述：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_details.ui" line="444"/>
        <source>Data provider:</source>
        <translation>数据提供商：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_details.ui" line="492"/>
        <source>Error:</source>
        <translation>错误：</translation>
    </message>
    <message>
        <location filename="../dialogs/project_dialog.py" line="25"/>
        <source>Project name must not be empty!</source>
        <translation>项目名称不能为空！</translation>
    </message>
    <message>
        <location filename="../dialogs/project_dialog.py" line="55"/>
        <source>Edit project </source>
        <translation>编辑项目</translation>
    </message>
</context>
<context>
    <name>ProjectView</name>
    <message>
        <location filename="../functional/view/project_view.py" line="23"/>
        <source>See projects</source>
        <translation>查看项目</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="25"/>
        <source>See processings</source>
        <translation>查看处理</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="27"/>
        <source>Filter projects by name</source>
        <translation>按名称筛选项目</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="28"/>
        <source>Create project</source>
        <translation>创建项目</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="30"/>
        <source>A-Z</source>
        <translation>A-Z</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="30"/>
        <source>Z-A</source>
        <translation>Z-A</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="30"/>
        <source>Newest first</source>
        <translation>最新优先</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="30"/>
        <source>Oldest first</source>
        <translation>最旧优先</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="30"/>
        <source>Updated recently</source>
        <translation>最近更新</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="30"/>
        <source>Updated long ago</source>
        <translation>很久前更新</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="111"/>
        <source>Project</source>
        <translation>项目</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="117"/>
        <source>Processing</source>
        <translation>处理</translation>
    </message>
</context>
<context>
    <name>ProviderDialog</name>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="35"/>
        <source>Provider</source>
        <translation>提供商</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="53"/>
        <source>Type</source>
        <translation>类型</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="66"/>
        <source>Tile coordinate scheme. XYZ is the most popular format, use it if you are not sure</source>
        <translation>瓦片坐标方案。XYZ是最流行的格式，如果不确定请使用它</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="85"/>
        <source>Maxar WMTS</source>
        <translation>Maxar WMTS</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="93"/>
        <source>Name</source>
        <translation>名称</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="117"/>
        <source>Login</source>
        <translation>登录名</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="127"/>
        <source>Password</source>
        <translation>密码</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="134"/>
        <source>CRS</source>
        <translation>坐标系</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="159"/>
        <source>Projection of the tile layer. The most popular is Web Mercator, use it if you are not sure</source>
        <translation>瓦片图层的投影。最流行的是Web墨卡托投影，如果不确定请使用它</translation>
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
        <translation>警告！登录名和密码（如果保存）将以未加密形式存储在QGIS设置中！</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="179"/>
        <source>Save login and password</source>
        <translation>保存登录名和密码</translation>
    </message>
</context>
<context>
    <name>QPlatformTheme</name>
    <message>
        <location filename="../mapflow.py" line="145"/>
        <source>Cancel</source>
        <translation>取消</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="146"/>
        <source>&amp;Yes</source>
        <translation>&amp;是</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="147"/>
        <source>&amp;No</source>
        <translation>&amp;否</translation>
    </message>
</context>
<context>
    <name>RenameImageDialog</name>
    <message>
        <location filename="../dialogs/image_dialog.py" line="18"/>
        <source>Dialog requires current image</source>
        <translation>对话框需要当前影像</translation>
    </message>
    <message>
        <location filename="../dialogs/image_dialog.py" line="19"/>
        <source>Rename image {}</source>
        <translation>重命名影像 {}</translation>
    </message>
    <message>
        <location filename="../dialogs/image_dialog.py" line="34"/>
        <source>Image name must not be empty!</source>
        <translation>影像名称不能为空！</translation>
    </message>
</context>
<context>
    <name>UpdateMosaicDialog</name>
    <message>
        <location filename="../dialogs/mosaic_dialog.py" line="49"/>
        <source>UpdateMosaicDialog requires a imagery collection to update</source>
        <translation>UpdateMosaicDialog需要更新的影像集</translation>
    </message>
    <message>
        <location filename="../dialogs/mosaic_dialog.py" line="50"/>
        <source>Edit imagery collection {}</source>
        <translation>编辑影像集 {}</translation>
    </message>
    <message>
        <location filename="../dialogs/mosaic_dialog.py" line="62"/>
        <source>Imagery collection name must not be empty!</source>
        <translation>影像集名称不能为空！</translation>
    </message>
</context>
<context>
    <name>UpdateProcessingDialog</name>
    <message>
        <location filename="../dialogs/processing_dialog.py" line="24"/>
        <source>Processing name must not be empty!</source>
        <translation>处理名称不能为空！</translation>
    </message>
    <message>
        <location filename="../dialogs/processing_dialog.py" line="32"/>
        <source>Edit processing {}</source>
        <translation>编辑处理 {}</translation>
    </message>
</context>
</TS>
