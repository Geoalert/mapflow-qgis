<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="zh_CN" sourcelanguage="en_US">
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
    <message>
        <location filename="../errors/api_errors.py" line="13"/>
        <source>Up to {templateAreaLimit} sq km can be used for a planned processing. Try reducing your area of interest.</source>
        <translation>计划处理最多可使用 {templateAreaLimit} 平方公里。请尝试缩小感兴趣区。</translation>
    </message>
    <message>
        <location filename="../errors/api_errors.py" line="17"/>
        <source>The processing area is too large: {area} sq.m exceeds the {aoiAreaLimit} sq.m limit. Reduce the area of interest.</source>
        <translation>处理区域过大：{area} 平方米超过 {aoiAreaLimit} 平方米的上限。请缩小感兴趣区。</translation>
    </message>
    <message>
        <location filename="../errors/api_errors.py" line="23"/>
        <source>You don&apos;t have enough limit to create this planned processing. Please contact your administrator to increase the limit.</source>
        <translation>您的额度不足以创建此计划处理。请联系管理员提高额度。</translation>
    </message>
    <message>
        <location filename="../errors/api_errors.py" line="27"/>
        <source>You have reached the maximum number of active planned processings. Pause or delete another one before activating this template.</source>
        <translation>您已达到活动计划处理的最大数量。请先暂停或删除另一个，再激活此模板。</translation>
    </message>
</context>
<context>
    <name>AreaCalculatorService</name>
    <message>
        <location filename="../functional/service/area_calculator_service.py" line="66"/>
        <source>Not enough rights to start processing in a shared project ({})</source>
        <translation>权限不足，无法在共享项目（{}）中开始处理</translation>
    </message>
    <message>
        <location filename="../functional/service/area_calculator_service.py" line="43"/>
        <source>Set AOI to start processing</source>
        <translation>设置感兴趣区域以开始处理</translation>
    </message>
    <message>
        <location filename="../functional/service/area_calculator_service.py" line="68"/>
        <source>AOI must contain not more than {} polygons</source>
        <translation>感兴趣区域不能包含超过 {} 个多边形</translation>
    </message>
    <message>
        <location filename="../functional/service/area_calculator_service.py" line="108"/>
        <source>Use extent of &apos;{name}&apos;</source>
        <translation>使用 &apos;{name}&apos; 的范围</translation>
    </message>
    <message>
        <location filename="../functional/service/area_calculator_service.py" line="113"/>
        <source>Use imagery extent</source>
        <translation>使用影像范围</translation>
    </message>
    <message>
        <location filename="../functional/service/area_calculator_service.py" line="118"/>
        <source>Selected AOI does not intersect the selected imagery</source>
        <translation>选择的感兴趣区域与所选影像没有交集</translation>
    </message>
    <message>
        <location filename="../functional/service/area_calculator_service.py" line="186"/>
        <source>Area: {:.2f} sq.km</source>
        <translation>面积：{:.2f} 平方公里</translation>
    </message>
    <message>
        <location filename="../functional/service/area_calculator_service.py" line="195"/>
        <source>Bad AOI. AOI must be inside boundaries: 
[-180, 180] by longitude, [-90, 90] by latitude</source>
        <translation>无效的感兴趣区域。感兴趣区域必须在边界内： 
经度 [-180, 180]，纬度 [-90, 90]</translation>
    </message>
    <message>
        <location filename="../functional/service/area_calculator_service.py" line="200"/>
        <source>Providers are not initialized</source>
        <translation>提供商未初始化</translation>
    </message>
</context>
<context>
    <name>Config</name>
    <message>
        <location filename="../config.py" line="14"/>
        <source>Product Type</source>
        <translation>产品类型</translation>
    </message>
    <message>
        <location filename="../config.py" line="15"/>
        <source>Provider Name</source>
        <translation>提供商名称</translation>
    </message>
    <message>
        <location filename="../config.py" line="16"/>
        <source>Preview</source>
        <translation>预览</translation>
    </message>
    <message>
        <location filename="../config.py" line="17"/>
        <source>Sensor</source>
        <translation>传感器</translation>
    </message>
    <message>
        <location filename="../config.py" line="18"/>
        <source>Band Order</source>
        <translation>波段顺序</translation>
    </message>
    <message>
        <location filename="../config.py" line="100"/>
        <source>Cloud %</source>
        <translation>云量 %</translation>
    </message>
    <message>
        <location filename="../config.py" line="20"/>
        <source>Off Nadir</source>
        <translation>离天底角</translation>
    </message>
    <message>
        <location filename="../config.py" line="97"/>
        <source>Date &amp; Time</source>
        <translation>日期 &amp; 时间</translation>
    </message>
    <message>
        <location filename="../config.py" line="22"/>
        <source>Zoom level</source>
        <translation>缩放级别</translation>
    </message>
    <message>
        <location filename="../config.py" line="23"/>
        <source>Spatial Resolution, m</source>
        <translation>空间分辨率，米</translation>
    </message>
    <message>
        <location filename="../config.py" line="24"/>
        <source>Image ID</source>
        <translation>影像ID</translation>
    </message>
    <message>
        <location filename="../config.py" line="29"/>
        <source>Project</source>
        <translation>项目</translation>
    </message>
    <message>
        <location filename="../config.py" line="27"/>
        <source>Succeeded</source>
        <translation type="obsolete">成功</translation>
    </message>
    <message>
        <location filename="../config.py" line="28"/>
        <source>Failed</source>
        <translation type="obsolete">失败</translation>
    </message>
    <message>
        <location filename="../config.py" line="31"/>
        <source>Author</source>
        <translation>作者</translation>
    </message>
    <message>
        <location filename="../config.py" line="32"/>
        <source>Updated at</source>
        <translation>更新于</translation>
    </message>
    <message>
        <location filename="../config.py" line="33"/>
        <source>Created at</source>
        <translation>创建于</translation>
    </message>
    <message>
        <location filename="../config.py" line="30"/>
        <source>State</source>
        <translation>状态</translation>
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
        <location filename="../functional/api/data_catalog_api.py" line="277"/>
        <source>Error</source>
        <translation>错误</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="126"/>
        <source>Could not delete imagery collection &apos;{mosaic_name}&apos;</source>
        <translation>无法删除影像集 &apos;{mosaic_name}&apos;</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="128"/>
        <source>Error. Could not delete following imagery collections:</source>
        <translation>错误。无法删除以下影像集：</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="170"/>
        <source>Failed to load imagery collection. 
Please try again later or report error</source>
        <translation>加载影像集失败。 
请稍后重试或报告错误</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="231"/>
        <source>This operation is forbidden for your account, contact us</source>
        <translation>您的账户无权执行此操作，请联系我们</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="233"/>
        <source>Imagery collection &apos;{mosaic_name}&apos; does not exist</source>
        <translation>影像集 &apos;{mosaic_name}&apos; 不存在</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="235"/>
        <source>Authentication error. Please log in to your account</source>
        <translation>认证错误。请登录您的账户</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="237"/>
        <source>The image does not meet this imagery collection &apos;{mosaic_name}&apos; parameters. 
Either modify your image or upload it to a different collection</source>
        <translation>该影像不符合此影像集 &apos;{mosaic_name}&apos; 的参数要求。
请修改您的影像或上传到其他影像集</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="240"/>
        <source>Could not upload &apos;{image}&apos; to imagery collection</source>
        <translation>无法将 &apos;{image}&apos; 上传到影像集</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="242"/>
        <source>Could not upload following images:
{images}</source>
        <translation>无法上传以下影像：
{images}</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="278"/>
        <source>Could not delete &apos;{image}&apos; from imagery collection</source>
        <translation>无法从影像集中删除 &apos;{image}&apos;</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="280"/>
        <source>Error. Could not delete following images:</source>
        <translation>错误。无法删除以下影像：</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="227"/>
        <source>Request timed out or was canceled. 
Try increasing QGIS global timeout setting: 
Settings -&gt; Options -&gt; Network -&gt; Timeout</source>
        <translation>请求超时或已取消。 
请尝试增加QGIS全局超时设置： 
设置 -&gt; 选项 -&gt; 网络 -&gt; 超时</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="364"/>
        <source>Image not found or you don&apos;t have access to it</source>
        <translation>未找到影像或您无权访问该影像</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="366"/>
        <source>This image is not available for download</source>
        <translation>此影像无法下载</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="368"/>
        <source>Image data is not yet available. Please try again later</source>
        <translation>影像数据尚不可用，请稍后重试</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="374"/>
        <source>Download error</source>
        <translation>下载错误</translation>
    </message>
</context>
<context>
    <name>DataCatalogService</name>
    <message>
        <location filename="../functional/service/data_catalog.py" line="76"/>
        <source>Choose image to upload</source>
        <translation>选择要上传的影像</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="118"/>
        <source>&lt;center&gt;Creation of imagery collection &apos;{mosaic_name}&apos; failed&lt;br&gt;while trying to upload &apos;{image}&apos;</source>
        <translation>&lt;center&gt;创建影像集 &apos;{mosaic_name}&apos; 失败&lt;br&gt;尝试上传 &apos;{image}&apos; 时</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="199"/>
        <source>&lt;center&gt;Delete imagery collection &lt;b&gt;&apos;{name}&apos;&lt;/b&gt;?</source>
        <translation>&lt;center&gt;删除影像集 &lt;b&gt;&apos;{name}&apos;&lt;/b&gt;？</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="202"/>
        <source>&lt;center&gt;Delete following imagery collections:&lt;br&gt;&lt;b&gt;&apos;{names}&apos;&lt;/b&gt;?</source>
        <translation>&lt;center&gt;删除以下影像集：&lt;br&gt;&lt;b&gt;&apos;{names}&apos;&lt;/b&gt;？</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="205"/>
        <source>&lt;center&gt;Delete &lt;b&gt;{len}&lt;/b&gt; imagery collections?</source>
        <translation>&lt;center&gt;删除 &lt;b&gt;{len}&lt;/b&gt; 个影像集？</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="245"/>
        <source>Please, select existing imagery collection</source>
        <translation>请选择现有的影像集</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="247"/>
        <source>Choose images to upload</source>
        <translation>选择要上传的影像</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="296"/>
        <source>Raster TIFF file must be georeferenced, have size less than {size} pixels and file size less than {memory}</source>
        <translation>栅格TIFF文件必须经过地理配准，像素尺寸小于 {size} 且文件大小小于 {memory}</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="300"/>
        <source>&lt;center&gt;&lt;b&gt;Error uploading &apos;{name}&apos;&lt;/b&gt;</source>
        <translation>&lt;center&gt;&lt;b&gt;上传 &apos;{name}&apos; 时出错&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="305"/>
        <source>&lt;b&gt;Not enough storage space. &lt;/b&gt;You have {free_storage} left, but &apos;{name}&apos; is {image_size}</source>
        <translation>&lt;b&gt;存储空间不足。&lt;/b&gt;您剩余 {free_storage}，但 &apos;{name}&apos; 大小为 {image_size}</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="400"/>
        <source>&lt;center&gt;Delete image &lt;b&gt;&apos;{name}&apos;&lt;/b&gt; from &apos;{mosaic}&apos; imagery collection?</source>
        <translation>&lt;center&gt;从 &apos;{mosaic}&apos; 影像集中删除影像 &lt;b&gt;&apos;{name}&apos;&lt;/b&gt;？</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="403"/>
        <source>&lt;center&gt;Delete following images from &apos;{mosaic}&apos; imagery collection:&lt;br&gt;&lt;b&gt;&apos;{names}&apos;&lt;/b&gt;?</source>
        <translation>&lt;center&gt;从 &apos;{mosaic}&apos; 影像集中删除以下影像：&lt;br&gt;&lt;b&gt;&apos;{names}&apos;&lt;/b&gt;？</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="406"/>
        <source>&lt;center&gt;Delete &lt;b&gt;{len}&lt;/b&gt; images from &apos;{mosaic}&apos; imagery collection?</source>
        <translation>&lt;center&gt;从 &apos;{mosaic}&apos; 影像集中删除 &lt;b&gt;{len}&lt;/b&gt; 个影像？</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="462"/>
        <source>Please, select existing output directory in the Settings tab</source>
        <translation type="obsolete">请在设置选项卡中选择现有的输出目录</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="495"/>
        <source>Image name should be 1-255 characters long</source>
        <translation>影像名称应为 1-255 个字符</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="667"/>
        <source>Source imagery collection with id &apos;{}&apos; was not found </source>
        <translation>未找到ID为 &apos;{}&apos; 的源影像集</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="669"/>
        <source>Source image with id &apos;{}&apos; was not found in any of your imagery collections</source>
        <translation>未在任何影像集中找到ID为 &apos;{}&apos; 的源影像</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="515"/>
        <source>Download URL not available</source>
        <translation>下载URL不可用</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="517"/>
        <source>Save image as</source>
        <translation>将影像另存为</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="535"/>
        <source>Failed to download image: {}</source>
        <translation>下载影像失败：{}</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="542"/>
        <source>Image saved to {}</source>
        <translation>影像已保存至 {}</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="544"/>
        <source>Failed to save file: {}</source>
        <translation>保存文件失败：{}</translation>
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
        <location filename="../functional/view/data_catalog_view.py" line="45"/>
        <source>Add images</source>
        <translation>添加影像</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="46"/>
        <source>Show images</source>
        <translation>显示影像</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="49"/>
        <source>Preview</source>
        <translation>预览</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="48"/>
        <source>Edit</source>
        <translation>编辑</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="50"/>
        <source>Info</source>
        <translation>信息</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="51"/>
        <source>Rename</source>
        <translation>重命名</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="75"/>
        <source>A-Z</source>
        <translation>A-Z</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="75"/>
        <source>Z-A</source>
        <translation>Z-A</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="75"/>
        <source>Biggest first</source>
        <translation>最大优先</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="75"/>
        <source>Smallest first</source>
        <translation>最小优先</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="75"/>
        <source>Newest first</source>
        <translation>最新优先</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="75"/>
        <source>Oldest first</source>
        <translation>最旧优先</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="96"/>
        <source>More about My imagery</source>
        <translation>关于“我的影像”的更多信息</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="519"/>
        <source>Filter imagery collections by name or id</source>
        <translation>按名称或ID筛选影像集</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="130"/>
        <source>Imagery collections</source>
        <translation>影像集</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="293"/>
        <source>Size</source>
        <translation>大小</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="130"/>
        <source>Created</source>
        <translation>创建时间</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="469"/>
        <source>Double-click to show images</source>
        <translation>双击显示影像</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="178"/>
        <source>Number of images: {count} 
</source>
        <translation>影像数量：{count} 
</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="188"/>
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
        <location filename="../functional/view/data_catalog_view.py" line="197"/>
        <source>Created: {date} at {time} 
Tags: {tags}</source>
        <translation>创建时间：{date} {time} 
标签：{tags}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="249"/>
        <source>&lt;b&gt;Name&lt;/b&gt;: {filename}                              &lt;br&gt;&lt;b&gt;Uploaded&lt;/b&gt;&lt;/br&gt;: {date} at {time}                              &lt;br&gt;&lt;b&gt;Size&lt;/b&gt;&lt;/br&gt;: {file_size}                              &lt;br&gt;&lt;b&gt;CRS&lt;/b&gt;&lt;/br&gt;: {crs}                              &lt;br&gt;&lt;b&gt;Number of bands&lt;/br&gt;&lt;/b&gt;: {bands}                              &lt;br&gt;&lt;b&gt;Width&lt;/br&gt;&lt;/b&gt;: {width} pixels                              &lt;br&gt;&lt;b&gt;Height&lt;/br&gt;&lt;/b&gt;: {height} pixels                              &lt;br&gt;&lt;b&gt;Pixel size&lt;/br&gt;&lt;/b&gt;: {pixel_size}</source>
        <translation>&lt;b&gt;名称&lt;/b&gt;：{filename}                              &lt;br&gt;&lt;b&gt;上传时间&lt;/b&gt;&lt;/br&gt;：{date} {time}                              &lt;br&gt;&lt;b&gt;大小&lt;/b&gt;&lt;/br&gt;：{file_size}                              &lt;br&gt;&lt;b&gt;坐标系&lt;/b&gt;&lt;/br&gt;：{crs}                              &lt;br&gt;&lt;b&gt;波段数&lt;/br&gt;&lt;/b&gt;：{bands}                              &lt;br&gt;&lt;b&gt;宽度&lt;/br&gt;&lt;/b&gt;：{width} 像素                              &lt;br&gt;&lt;b&gt;高度&lt;/br&gt;&lt;/b&gt;：{height} 像素                              &lt;br&gt;&lt;b&gt;像素大小&lt;/br&gt;&lt;/b&gt;：{pixel_size}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="293"/>
        <source>Images</source>
        <translation>影像</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="293"/>
        <source>Uploaded</source>
        <translation>上传时间</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="349"/>
        <source>No imagery collection with id &apos;{mosaic_id}&apos; was found</source>
        <translation>未找到ID为 &apos;{mosaic_id}&apos; 的影像集</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="362"/>
        <source>No image with id &apos;{image_id}&apos; was found</source>
        <translation>未找到ID为 &apos;{image_id}&apos; 的影像</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="376"/>
        <source>Your data: {taken}. Free space: {free}</source>
        <translation>您的数据：{taken}。剩余空间：{free}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="392"/>
        <source>Selected imagery collection: &lt;b&gt;{mosaic_name}</source>
        <translation>已选影像集：&lt;b&gt;{mosaic_name}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="406"/>
        <source>No imagery collection selected</source>
        <translation>未选择影像集</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="428"/>
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
        <location filename="../functional/view/data_catalog_view.py" line="441"/>
        <source>Selected image: &lt;b&gt;{image_name}</source>
        <translation>已选影像：&lt;b&gt;{image_name}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="456"/>
        <source>No image selected</source>
        <translation>未选择影像</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="466"/>
        <source>&apos;Cmd&apos; + click to deselect</source>
        <translation>按住 &apos;Cmd&apos; 并点击以取消选择</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="466"/>
        <source>&apos;Ctrl&apos; + click to deselect</source>
        <translation>按住 &apos;Ctrl&apos; 并点击以取消选择</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="483"/>
        <source>Delete image</source>
        <translation>删除影像</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="484"/>
        <source>Add image</source>
        <translation>添加影像</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="497"/>
        <source>Filter images by name or id</source>
        <translation>按名称或ID筛选影像</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="504"/>
        <source>Delete collection</source>
        <translation>删除影像集</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="505"/>
        <source>Add collection</source>
        <translation>添加影像集</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="451"/>
        <source>Download</source>
        <translation>下载</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="449"/>
        <source>Image is not available for download</source>
        <translation>影像无法下载</translation>
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
    <name>ErrorDialog</name>
    <message>
        <location filename="../dialogs/static/ui/error_message.ui" line="64"/>
        <source>Error</source>
        <translation>错误</translation>
    </message>
</context>
<context>
    <name>ErrorMessageList</name>
    <message>
        <location filename="../errors/error_message_list.py" line="26"/>
        <source>Unknown error. Contact us to resolve the issue! help@geoalert.io</source>
        <translation>未知错误。请联系我们解决问题！help@geoalert.io</translation>
    </message>
</context>
<context>
    <name>ErrorMessageWidget</name>
    <message>
        <location filename="../dialogs/error_message_widget.py" line="22"/>
        <source>&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;Let us know&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;告诉我们&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
</context>
<context>
    <name>Header</name>
    <message>
        <location filename="../functional/helpers.py" line="158"/>
        <source> | Project: </source>
        <translation> | 项目：</translation>
    </message>
    <message>
        <location filename="../functional/helpers.py" line="161"/>
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
        <location filename="../dialogs/main_dialog.py" line="577"/>
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
        <location filename="../dialogs/main_dialog.py" line="513"/>
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
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3062"/>
        <source>Review</source>
        <translation>审核</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="398"/>
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
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2965"/>
        <source>Name</source>
        <translation>名称</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2984"/>
        <source>Model</source>
        <translation>模型</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2997"/>
        <source>Status</source>
        <translation>状态</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1208"/>
        <source>Progress %</source>
        <translation>进度 %</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1213"/>
        <source>Area, sq. km</source>
        <translation>面积，平方公里</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3036"/>
        <source>Cost</source>
        <translation>费用</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3049"/>
        <source>Created</source>
        <translation>创建时间</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1228"/>
        <source>Review until</source>
        <translation>审核截止时间</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1249"/>
        <source>View results</source>
        <translation>查看结果</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1353"/>
        <source>Delete</source>
        <translation>删除</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1379"/>
        <source>Filter processings by name</source>
        <translation>按名称筛选处理</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1434"/>
        <source>Project:</source>
        <translation>项目：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1493"/>
        <source>Imagery search</source>
        <translation>影像搜索</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1499"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Here, you can search imagery for your area and timespan.&lt;/p&gt;&lt;p&gt;Additional filters are also available below.&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;在此处，您可以为您的区域和时间范围搜索影像。&lt;/p&gt;&lt;p&gt;下方还提供其他筛选条件。&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1502"/>
        <source>Provider Imagery Catalog</source>
        <translation>提供商影像目录</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1513"/>
        <source>Earlier images won&apos;t be shown</source>
        <translation>较早的影像将不会显示</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1516"/>
        <source>From:</source>
        <translation>从：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1567"/>
        <source>Dates are inclusive</source>
        <translation>日期包含起止日</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1584"/>
        <source>yyyy-MM-dd</source>
        <translation>yyyy-MM-dd</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1557"/>
        <source>More recent images won&apos;t be shown</source>
        <translation>较新的影像将不会显示</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1560"/>
        <source>To:</source>
        <translation>至：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1614"/>
        <source>Mosaic</source>
        <translation>镶嵌</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1624"/>
        <source>Image</source>
        <translation>影像</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1693"/>
        <source>Click and wait for a few seconds until the table below is filled out</source>
        <translation>点击并等待几秒钟，直到下方表格填充完成</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="342"/>
        <source>Search </source>
        <translation>搜索</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1716"/>
        <source>Double-click on a row to preview its image</source>
        <translation>双击某行以预览其影像</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1767"/>
        <source>1/1</source>
        <translation>1/1</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1850"/>
        <source>Clear </source>
        <translation>清除</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1877"/>
        <source>Click to specify additional search criteria</source>
        <translation>点击以指定其他搜索条件</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1880"/>
        <source>Additional filters</source>
        <translation>其他筛选条件</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1934"/>
        <source>%</source>
        <translation>%</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1920"/>
        <source>Min intersection:</source>
        <translation>最小交集：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1927"/>
        <source>Cloud cover up to:</source>
        <translation>云量最高：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1956"/>
        <source>Images that cover fewer % of your area won&apos;t be shown</source>
        <translation>覆盖您区域少于指定百分比的影像将不会显示</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2008"/>
        <source>Providers: </source>
        <translation>提供商：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2053"/>
        <source>Search only through available providers</source>
        <translation>仅通过可用提供商搜索</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2091"/>
        <source>My imagery</source>
        <translation>我的影像</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2116"/>
        <source>Add collection</source>
        <translation>添加影像集</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2129"/>
        <source>Delete collection</source>
        <translation>删除影像集</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2194"/>
        <source>No current selection</source>
        <translation>当前无选择</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2297"/>
        <source>Sort by</source>
        <translation>排序方式</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2349"/>
        <source>Imagery data</source>
        <translation>影像数据</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2615"/>
        <source>Settings</source>
        <translation>设置</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2642"/>
        <source>Add or edit imagery providers:</source>
        <translation>添加或编辑影像提供商：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2687"/>
        <source>Add your own web imagery provider</source>
        <translation>添加您自己的网络影像提供商</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2801"/>
        <source>Use all vector layers as Areas Of Interest</source>
        <translation>将所有矢量图层用作感兴趣区域</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2811"/>
        <source>Confirm processing start</source>
        <translation>确认开始处理</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2823"/>
        <source>view results as a vector tiles</source>
        <translation>以矢量切片形式查看结果</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2836"/>
        <source>save results as a local vector file</source>
        <translation>将结果保存为本地矢量文件</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2885"/>
        <source>Configure search table:</source>
        <translation>配置搜索表格：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2892"/>
        <source>Configure processings table:</source>
        <translation>配置处理表格：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3010"/>
        <source>Progress</source>
        <translation>进度</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3023"/>
        <source>Area</source>
        <translation>面积</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3075"/>
        <source>ID</source>
        <translation>ID</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3151"/>
        <source>Product Type</source>
        <translation>产品类型</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3167"/>
        <source>Provider Name</source>
        <translation>提供商名称</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3183"/>
        <source>Sensor</source>
        <translation>传感器</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3199"/>
        <source>Band Order</source>
        <translation>波段顺序</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3215"/>
        <source>Cloud %</source>
        <translation>云量 %</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3231"/>
        <source>° Off Nadir</source>
        <translation>° 离天底角</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3247"/>
        <source>Date and Time</source>
        <translation>日期和时间</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3263"/>
        <source>Mosaic Zoom</source>
        <translation>镶嵌缩放级别</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3276"/>
        <source>Image Spatial Resolution</source>
        <translation>影像空间分辨率</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3289"/>
        <source>Image ID</source>
        <translation>影像ID</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3302"/>
        <source>Preview</source>
        <translation>预览</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3334"/>
        <source>Set up local working directory, where all the temporary files will be stored</source>
        <translation>设置本地工作目录，所有临时文件将存储于此</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3352"/>
        <source>Output directory:</source>
        <translation>输出目录：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3438"/>
        <source>Help</source>
        <translation>帮助</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3359"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=&quot; margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#user-interface&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;User Interface walkthrough&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow.html#how-to-upload-your-image&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;How to process your own image&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#how-to-use-other-imagery-services&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;How to use a different imagery tileset (XYZ or TMS)&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#how-to-connect-to-maxar-securewatch&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;How to connect to Maxar SecureWatch&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=&quot; margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow credits&lt;/span&gt;&lt;span style=&quot; font-size:large; font-weight:700;&quot;&gt;&lt;br/&gt;&lt;/span&gt;&lt;/h3&gt;&lt;table border=&quot;0&quot; style=&quot; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;&quot; align=&quot;center&quot; cellspacing=&quot;2&quot; cellpadding=&quot;0&quot;&gt;&lt;thead&gt;&lt;tr&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:600;&quot;&gt;Pay as you go&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:696;&quot;&gt;$50&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:696;&quot;&gt;$90&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:696;&quot;&gt;$800&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/thead&gt;&lt;tr&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;Credits for processing&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;500&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;1000&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;10000&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/table&gt;&lt;p&gt;See also – &lt;a href=&quot;https://docs.mapflow.ai/userguides/prices.html&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#094fd1;&quot;&gt;How much do the processings and data cost?&lt;/span&gt;&lt;/a&gt;&lt;br/&gt;&lt;/p&gt;&lt;h3 style=&quot; margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Join the project on &lt;a href=&quot;https://github.com/Geoalert/mapflow-qgis&quot;&gt;&lt;span style=&quot; font-weight:600; text-decoration: underline; color:#0000ff;&quot;&gt;GitHub&lt;/span&gt;&lt;/a&gt; or &lt;a href=&quot;https://github.com/Geoalert/mapflow-qgis/issues&quot;&gt;&lt;span style=&quot; font-weight:600; text-decoration: underline; color:#0000ff;&quot;&gt;report an issue&lt;/span&gt;&lt;/a&gt;&lt;/span&gt;&lt;/h3&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation type="obsolete">&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=&quot; margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#user-interface&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;用户界面导览&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow.html#how-to-upload-your-image&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;如何处理自己的影像&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#how-to-use-other-imagery-services&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;如何使用其他影像瓦片集（XYZ或TMS）&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#how-to-connect-to-maxar-securewatch&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;如何连接到Maxar SecureWatch&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=&quot; margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow点数&lt;/span&gt;&lt;span style=&quot; font-size:large; font-weight:700;&quot;&gt;&lt;br/&gt;&lt;/span&gt;&lt;/h3&gt;&lt;table border=&quot;0&quot; style=&quot; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;&quot; align=&quot;center&quot; cellspacing=&quot;2&quot; cellpadding=&quot;0&quot;&gt;&lt;thead&gt;&lt;tr&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:600;&quot;&gt;按需付费&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:696;&quot;&gt;$50&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:696;&quot;&gt;$90&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:696;&quot;&gt;$800&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/thead&gt;&lt;tr&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;处理点数&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;500&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;1000&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;10000&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/table&gt;&lt;p&gt;另请参阅 – &lt;a href=&quot;https://docs.mapflow.ai/userguides/prices.html&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#094fd1;&quot;&gt;处理和数据费用是多少？&lt;/span&gt;&lt;/a&gt;&lt;br/&gt;&lt;/p&gt;&lt;h3 style=&quot; margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;在 &lt;a href=&quot;https://github.com/Geoalert/mapflow-qgis&quot;&gt;&lt;span style=&quot; font-weight:600; text-decoration: underline; color:#0000ff;&quot;&gt;GitHub&lt;/span&gt;&lt;/a&gt; 上加入项目或在 &lt;a href=&quot;https://github.com/Geoalert/mapflow-qgis/issues&quot;&gt;&lt;span style=&quot; font-weight:600; text-decoration: underline; color:#0000ff;&quot;&gt;此报告问题&lt;/span&gt;&lt;/a&gt;&lt;/span&gt;&lt;/h3&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3474"/>
        <source>see_details_action</source>
        <translation>查看详情操作</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="132"/>
        <source>Save results</source>
        <translation>保存结果</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="133"/>
        <source>Download AOI</source>
        <translation>下载感兴趣区域</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="134"/>
        <source>See details</source>
        <translation>查看详情</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="141"/>
        <source>Rename</source>
        <translation>重命名</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="138"/>
        <source>Restart</source>
        <translation>重新开始</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="139"/>
        <source>Duplicate</source>
        <translation>复制</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="359"/>
        <source>
Price: {} credits per square km</source>
        <translation>
价格：每平方公里 {} 点数</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="370"/>
        <source>Rate processing &lt;b&gt;{name}&lt;/b&gt;:</source>
        <translation>评价处理 &lt;b&gt;{name}&lt;/b&gt;：</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="503"/>
        <source>Not enough rights to start processing in a shared project ({})</source>
        <translation>权限不足，无法在共享项目（{}）中开始处理</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="516"/>
        <source>Not enough rights to rate processing in a shared project ({})</source>
        <translation>权限不足，无法在共享项目（{}）中评价处理</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="518"/>
        <source>Please select processing</source>
        <translation>请选择处理</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="522"/>
        <source>Not enough rights to delete processing in a shared project ({})</source>
        <translation>权限不足，无法在共享项目（{}）中删除处理</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="555"/>
        <source>Delete project</source>
        <translation>删除项目</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="556"/>
        <source>Edit project</source>
        <translation>编辑项目</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="572"/>
        <source>Zoom is derived from found imagery resolution</source>
        <translation>缩放级别根据找到的影像分辨率推算</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="587"/>
        <source>Previous page</source>
        <translation>上一页</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="588"/>
        <source>Next page</source>
        <translation>下一页</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="589"/>
        <source>Page</source>
        <translation>页码</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="749"/>
        <source>&lt;b&gt;URL:&lt;/b&gt; {url}&lt;br&gt;&lt;b&gt;Source type:&lt;/b&gt; {type}</source>
        <translation>&lt;b&gt;URL：&lt;/b&gt; {url}&lt;br&gt;&lt;b&gt;源类型：&lt;/b&gt; {type}</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="753"/>
        <source>&lt;br&gt;&lt;b&gt;CRS:&lt;/b&gt; {crs}</source>
        <translation>&lt;br&gt;&lt;b&gt;坐标系：&lt;/b&gt; {crs}</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="755"/>
        <source>&lt;br&gt;&lt;b&gt;Zoom:&lt;/b&gt; {zoom}</source>
        <translation>&lt;br&gt;&lt;b&gt;缩放级别：&lt;/b&gt; {zoom}</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="757"/>
        <source>&lt;br&gt;&lt;b&gt;Raster login:&lt;/b&gt; {login}&lt;br&gt;&lt;b&gt;Raster password:&lt;/b&gt; {password}</source>
        <translation>&lt;br&gt;&lt;b&gt;栅格登录名：&lt;/b&gt; {login}&lt;br&gt;&lt;b&gt;栅格密码：&lt;/b&gt; {password}</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="167"/>
        <source>Project: &lt;b&gt;{}</source>
        <translation>项目：&lt;b&gt;{}</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1665"/>
        <source>Some current filters are wider than the last search. Click for details.</source>
        <translation>某些当前筛选器比上次搜索更宽。点击查看详情。</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1668"/>
        <source>(!)</source>
        <translation>(!)</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1812"/>
        <source>Save the current search filters to this template (replaces its stored search parameters)</source>
        <translation>将当前搜索筛选器保存到此模板（替换其已存储的搜索参数）</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1815"/>
        <source>Update search</source>
        <translation>更新搜索</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1828"/>
        <source>Seen</source>
        <translation>已查看</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2072"/>
        <source>Reset the filters to the parameters the current results were fetched with (search request or template)</source>
        <translation>将筛选器重置为获取当前结果时使用的参数（搜索请求或模板）</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2075"/>
        <source>Reset filters</source>
        <translation>重置筛选器</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3447"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=&quot; margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#user-interface&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;User Interface walkthrough&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow.html#how-to-upload-your-image&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;How to process your own image&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align=&quot;center&quot;&gt;&lt;a href=&quot;https://docs.mapflow.ai/api/qgis_mapflow#how-to-use-other-imagery-services&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0057ae;&quot;&gt;How to use a different imagery tileset (XYZ or TMS)&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=&quot; margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Mapflow credits&lt;/span&gt;&lt;span style=&quot; font-size:large; font-weight:700;&quot;&gt;&lt;br/&gt;&lt;/span&gt;&lt;/h3&gt;&lt;table border=&quot;0&quot; style=&quot; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;&quot; align=&quot;center&quot; cellspacing=&quot;2&quot; cellpadding=&quot;0&quot;&gt;&lt;thead&gt;&lt;tr&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:600;&quot;&gt;Pay as you go&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:696;&quot;&gt;$50&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:696;&quot;&gt;$90&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p align=&quot;center&quot;&gt;&lt;span style=&quot; font-weight:696;&quot;&gt;$800&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/thead&gt;&lt;tr&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;Credits for processing&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;500&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;1000&lt;/p&gt;&lt;/td&gt;&lt;td style=&quot; padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;&quot;&gt;&lt;p&gt;10000&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/table&gt;&lt;p&gt;See also – &lt;a href=&quot;https://docs.mapflow.ai/userguides/prices.html&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#094fd1;&quot;&gt;How much do the processings and data cost?&lt;/span&gt;&lt;/a&gt;&lt;br/&gt;&lt;/p&gt;&lt;h3 style=&quot; margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;&quot;&gt;&lt;span style=&quot; font-size:large; font-weight:600;&quot;&gt;Join the project on &lt;a href=&quot;https://github.com/Geoalert/mapflow-qgis&quot;&gt;&lt;span style=&quot; font-weight:600; text-decoration: underline; color:#0000ff;&quot;&gt;GitHub&lt;/span&gt;&lt;/a&gt; or &lt;a href=&quot;https://github.com/Geoalert/mapflow-qgis/issues&quot;&gt;&lt;span style=&quot; font-weight:600; text-decoration: underline; color:#0000ff;&quot;&gt;report an issue&lt;/span&gt;&lt;/a&gt;&lt;/span&gt;&lt;/h3&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="63"/>
        <source>Back</source>
        <translation>返回</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="65"/>
        <source>Open processings</source>
        <translation>打开处理</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="67"/>
        <source>Open selected template</source>
        <translation>打开所选模板</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="135"/>
        <source>See processings</source>
        <translation>查看处理</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="136"/>
        <source>See search results</source>
        <translation>查看搜索结果</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="142"/>
        <source>Pause</source>
        <translation>暂停</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="143"/>
        <source>Resume</source>
        <translation>恢复</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="145"/>
        <source>Rename AOI</source>
        <translation>重命名 AOI</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="146"/>
        <source>Delete AOI</source>
        <translation>删除 AOI</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="147"/>
        <source>Add AOI from layer…</source>
        <translation>从图层添加 AOI…</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="148"/>
        <source>Update selected AOI</source>
        <translation>更新所选 AOI</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="149"/>
        <source>Draw AOI on the map</source>
        <translation>在地图上绘制 AOI</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="150"/>
        <source>Exclude from search</source>
        <translation>从搜索中排除</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="667"/>
        <source>Off-Nadir °:</source>
        <translation>偏离天底角 °：</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="673"/>
        <source>Show only images within this off-nadir angle range</source>
        <translation>仅显示此偏离天底角范围内的图像</translation>
    </message>
</context>
<context>
    <name>Mapflow</name>
    <message>
        <location filename="../mapflow.py" line="275"/>
        <source>Error during loading the data providers: {e}</source>
        <translation>加载数据提供商时出错：{e}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="278"/>
        <source>We failed to import providers from the settings. Please add them again</source>
        <translation>我们从设置导入提供商失败。请重新添加</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="284"/>
        <source>Draw AOI at the map</source>
        <translation>在地图上绘制感兴趣区域</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="285"/>
        <source>Use imagery extent</source>
        <translation>使用影像范围</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="287"/>
        <source>Create AOI from map extent</source>
        <translation>从地图范围创建感兴趣区域</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="725"/>
        <source>Project: &lt;b&gt;{}</source>
        <translation type="obsolete">项目：&lt;b&gt;{}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1528"/>
        <source>Choose imagery collection or image to start processing</source>
        <translation>选择影像集或影像以开始处理</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2025"/>
        <source>Log in </source>
        <translation>登录</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="739"/>
        <source>No project selected</source>
        <translation type="obsolete">未选择项目</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="741"/>
        <source>You can&apos;t remove or modify default project</source>
        <translation type="obsolete">您不能删除或修改默认项目</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="744"/>
        <source>Not enough rights to delete or update shared project ({})</source>
        <translation type="obsolete">权限不足，无法删除或更新共享项目（{}）</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="763"/>
        <source>Do you really want to remove project {}? This action cannot be undone, all processings will be lost!</source>
        <translation type="obsolete">您确定要删除项目 {} 吗？此操作无法撤销，所有处理都将丢失！</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2097"/>
        <source>This provider is default and cannot be removed</source>
        <translation>此提供商为默认提供商，无法删除</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2101"/>
        <source>Permanently remove {}?</source>
        <translation>永久删除 {}？</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2133"/>
        <source>Provider name must be unique. {name} already exists, select another or delete/edit existing</source>
        <translation>提供商名称必须唯一。{name} 已存在，请选择其他名称或删除/编辑现有项</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2144"/>
        <source>Add new provider</source>
        <translation>添加新提供商</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2152"/>
        <source>This is a default provider, it cannot be edited</source>
        <translation>此为默认提供商，无法编辑</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2207"/>
        <source>If you already know which {provider_name} image you want to process,
simply paste its ID here. Otherwise, search suitable images in the catalog below.</source>
        <translation>如果您已确定要处理哪个 {provider_name} 影像，只需将其ID粘贴在此处。否则，请在下方目录中搜索合适的影像。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="773"/>
        <source>e.g. S2B_OPER_MSI_L1C_TL_VGS4_20220209T091044_A025744_T36SXA_N04_00</source>
        <translation type="obsolete">例如：S2B_OPER_MSI_L1C_TL_VGS4_20220209T091044_A025744_T36SXA_N04_00</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2211"/>
        <source>e.g. a3b154c40cc74f3b934c0ffc9b34ecd1</source>
        <translation>例如：a3b154c40cc74f3b934c0ffc9b34ecd1</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2243"/>
        <source>Select output directory</source>
        <translation>选择输出目录</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2266"/>
        <source>Please, specify an existing output directory</source>
        <translation>请指定一个现有的输出目录</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3031"/>
        <source>Please, select a valid area of interest</source>
        <translation>请选择有效的感兴趣区域</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2855"/>
        <source>We couldn&apos;t get metadata from the Mapflow Imagery Catalog</source>
        <translation>我们无法从Mapflow影像目录获取元数据</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2858"/>
        <source>. Error {error}</source>
        <translation>。错误 {error}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2893"/>
        <source>No images match your criteria. Try relaxing the filters.</source>
        <translation>没有符合您条件的影像。请尝试放宽筛选条件。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2909"/>
        <source>&lt;b&gt;Results could not be loaded &lt;/b&gt;&lt;br&gt;Please, make sure you chose the right output folder in the Settings tab                                 and you have access rights to this folder</source>
        <translation>&lt;b&gt;结果无法加载&lt;/b&gt;&lt;br&gt;请确保您在设置选项卡中选择了正确的输出文件夹，并且您有访问该文件夹的权限</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1061"/>
        <source>Your area of interest is too large.</source>
        <translation type="obsolete">您的感兴趣区域太大。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1164"/>
        <source>Please, check your credentials</source>
        <translation type="obsolete">请检查您的凭据</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1318"/>
        <source>We couldn&apos;t fetch Sentinel metadata</source>
        <translation type="obsolete">我们无法获取Sentinel元数据</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1285"/>
        <source>More</source>
        <translation type="obsolete">更多</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1404"/>
        <source>Please, check your Maxar credentials</source>
        <translation type="obsolete">请检查您的Maxar凭据</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1406"/>
        <source>We couldn&apos;t get metadata from Maxar, error {error}</source>
        <translation type="obsolete">我们无法从Maxar获取元数据，错误 {error}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1522"/>
        <source>A Sentinel image ID should look like S2B_OPER_MSI_L1C_TL_VGS4_20220209T091044_A025744_T36SXA_N04_00 or /36/S/XA/2022/02/09/0/</source>
        <translation type="obsolete">Sentinel影像ID应类似 S2B_OPER_MSI_L1C_TL_VGS4_20220209T091044_A025744_T36SXA_N04_00 或 /36/S/XA/2022/02/09/0/</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1530"/>
        <source>A Maxar image ID should look like a3b154c40cc74f3b934c0ffc9b34ecd1</source>
        <translation type="obsolete">Maxar影像ID应类似 a3b154c40cc74f3b934c0ffc9b34ecd1</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1577"/>
        <source>Not enough rights to start processing in a shared project ({})</source>
        <translation type="obsolete">权限不足，无法在共享项目（{}）中开始处理</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1554"/>
        <source>Set AOI to start processing</source>
        <translation type="obsolete">设置感兴趣区域以开始处理</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1579"/>
        <source>AOI must contain not more than {} polygons</source>
        <translation type="obsolete">感兴趣区域不能包含超过 {} 个多边形</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1621"/>
        <source>Use extent of &apos;{name}&apos;</source>
        <translation type="obsolete">使用 &apos;{name}&apos; 的范围</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1623"/>
        <source>Select AOI to start processing</source>
        <translation type="obsolete">选择感兴趣区域以开始处理</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1858"/>
        <source>Selected AOI does not intersect the selected imagery</source>
        <translation type="obsolete">选择的感兴趣区域与所选影像没有交集</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1699"/>
        <source>Area: {:.2f} sq.km</source>
        <translation type="obsolete">面积：{:.2f} 平方公里</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1833"/>
        <source>Error! Models are not initialized.
Please, make sure you have selected a project</source>
        <translation type="obsolete">错误！模型未初始化。
请确保您已选择项目</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1845"/>
        <source>Processing cost is not available:
{error}</source>
        <translation type="obsolete">处理费用不可用：
{error}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1860"/>
        <source>This provider requires image ID. Use search tab to find imagery for you requirements, and select image in the table.</source>
        <translation type="obsolete">此提供商需要影像ID。请使用搜索选项卡查找符合您要求的影像，并在表格中选择影像。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1854"/>
        <source>Choose imagery to start processing</source>
        <translation type="obsolete">选择影像以开始处理</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1880"/>
        <source>Sorry, there&apos;s no preview for this image</source>
        <translation type="obsolete">抱歉，此影像无预览</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1885"/>
        <source>Processsing cost: {cost} credits</source>
        <translation type="obsolete">处理费用：{cost} 点数</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1899"/>
        <source>Delete selected processings?</source>
        <translation type="obsolete">删除选中的处理？</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1925"/>
        <source>Error deleting a processing</source>
        <translation type="obsolete">删除处理时出错</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3026"/>
        <source>Please, specify a name for your processing</source>
        <translation>请为您的处理指定一个名称</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3029"/>
        <source>Processing area layer is corrupted or has invalid projection</source>
        <translation>处理区域图层已损坏或具有无效投影</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3033"/>
        <source>Up to {} sq km can be processed at a time. Try splitting your area(s) into several processings.</source>
        <translation>一次最多可处理 {} 平方公里。请尝试将您的区域分割为多个处理。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3049"/>
        <source>Providers are not initialized</source>
        <translation>提供商未初始化</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1755"/>
        <source>Bad AOI. AOI must be inside boundaries: 
[-180, 180] by longitude, [-90, 90] by latitude</source>
        <translation type="obsolete">无效的感兴趣区域。感兴趣区域必须在边界内： 
经度 [-180, 180]，纬度 [-90, 90]</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1865"/>
        <source>No project is selected</source>
        <translation type="obsolete">未选择项目</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1894"/>
        <source>Processing limit exceeded. Visit &quot;&lt;a href=&quot;https://app.mapflow.ai/account/balance&quot;&gt;Mapflow&lt;/a&gt;&quot; to top up your balance</source>
        <translation type="obsolete">超出处理限制。请访问 &quot;&lt;a href=&quot;https://app.mapflow.ai/account/balance&quot;&gt;Mapflow&lt;/a&gt;&quot; 充值余额</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1901"/>
        <source>Starting the processing...</source>
        <translation type="obsolete">正在开始处理...</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1906"/>
        <source>Product type(s) not searched: {extra}</source>
        <translation>未搜索的产品类型：{extra}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1920"/>
        <source>{cost} credits</source>
        <translation type="obsolete">{cost} 点数</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1953"/>
        <source> sq.km</source>
        <translation type="obsolete"> 平方公里</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2205"/>
        <source>We couldn&apos;t upload your GeoTIFF</source>
        <translation type="obsolete">我们无法上传您的GeoTIFF文件</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2227"/>
        <source>Success! We&apos;ll notify you when the processing has finished.</source>
        <translation type="obsolete">成功！处理完成后我们将通知您。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1992"/>
        <source>The selected data provider is unavailable on your plan. 
 Upgrade your subscription to get access to the data. 
See pricing at &lt;a href=&quot;https://mapflow.ai/pricing&quot;&gt;mapflow.ai&lt;/a&gt;</source>
        <translation type="obsolete">所选数据提供商在您的订阅计划中不可用。
升级订阅以获取数据访问权限。
请查看 &lt;a href=&quot;https://mapflow.ai/pricing&quot;&gt;mapflow.ai&lt;/a&gt; 的定价</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2003"/>
        <source>Processing creation failed</source>
        <translation type="obsolete">处理创建失败</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3082"/>
        <source>Your balance: {} credits</source>
        <translation>您的余额：{} 点数</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3084"/>
        <source>Remaining limit: {:.2f} sq.km</source>
        <translation>剩余限制：{:.2f} 平方公里</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3153"/>
        <source>Show all</source>
        <translation>显示全部</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1694"/>
        <source>Sorry, we couldn&apos;t load the image</source>
        <translation type="obsolete">抱歉，我们无法加载该影像</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1695"/>
        <source>Error previewing Sentinel imagery</source>
        <translation type="obsolete">预览Sentinel影像时出错</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3169"/>
        <source>Preview is unavailable when metadata layer is removed</source>
        <translation>元数据图层被移除时预览不可用</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3221"/>
        <source>Selected imagery has no preview</source>
        <translation>所选影像无预览</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3226"/>
        <source>Preview with such URL is unavailable</source>
        <translation>该URL的预览不可用</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3234"/>
        <source>Preview for &apos;{iid}&apos; is unavailable</source>
        <translation>&apos;{iid}&apos; 的预览不可用</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3345"/>
        <source>Could not display preview</source>
        <translation>无法显示预览</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3441"/>
        <source>We couldn&apos;t load a preview for this image</source>
        <translation>我们无法加载此影像的预览</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1895"/>
        <source>Please, select an image to preview</source>
        <translation type="obsolete">请选择要预览的影像</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3418"/>
        <source>Provider {name} requires image id for preview!</source>
        <translation>提供商 {name} 需要影像ID才能预览！</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3422"/>
        <source>Preview is unavailable for the provider {}. 
OSM layer will be added instead.</source>
        <translation>提供商 {} 的预览不可用。
将添加OSM图层作为替代。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3453"/>
        <source>This provider requires image ID!</source>
        <translation>此提供商需要影像ID！</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3704"/>
        <source>Only finished processings can be rated</source>
        <translation>仅完成处理可被评价</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3707"/>
        <source>Processing must be in `Review required` status</source>
        <translation>处理必须处于“需要审核”状态</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3723"/>
        <source>Thank you! Your rating is submitted!
We would appreciate if you add feedback as well.</source>
        <translation>谢谢！您的评价已提交！
如能同时提供反馈我们将不胜感激。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3730"/>
        <source>Thank you! Your rating and feedback are submitted!</source>
        <translation>谢谢！您的评价和反馈已提交！</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2570"/>
        <source>Only correctly finished processings (status OK) can be reviewed</source>
        <translation type="obsolete">仅正确完成（状态为OK）的处理可被审核</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3745"/>
        <source>Not enough rights to rate processing in a shared project ({})</source>
        <translation>权限不足，无法在共享项目（{}）中评价处理</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3748"/>
        <source>Please select processing</source>
        <translation>请选择处理</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3750"/>
        <source>Only correctly finished processings (status OK) can be rated</source>
        <translation>仅正确完成（状态为OK）的处理可被评价</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3752"/>
        <source>Please select rating to submit</source>
        <translation>请选择要提交的评分</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3968"/>
        <source>Only the results of correctly finished processing can be loaded</source>
        <translation>仅正确完成的处理结果可被加载</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2221"/>
        <source>Directory &apos;{}&apos; does not exist</source>
        <translation type="obsolete">目录 &apos;{}&apos; 不存在</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2221"/>
        <source>&lt;br&gt;Using Settings tab, change the output directory to an existing one to download the results</source>
        <translation type="obsolete">&lt;br&gt;请使用设置选项卡，将输出目录更改为现有目录以下载结果</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3050"/>
        <source> failed with error:
</source>
        <translation type="obsolete"> 失败，错误：
</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3057"/>
        <source>{} processings failed: 
 {} 
 See tooltip over the processings table for error details</source>
        <translation type="obsolete">{} 个处理失败： 
 {} 
 请查看处理表格上的工具提示以获取错误详情</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3064"/>
        <source>{} processings failed: 
 See tooltip over the processings table for error details</source>
        <translation type="obsolete">{} 个处理失败： 
 请查看处理表格上的工具提示以获取错误详情</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3076"/>
        <source> finished. Double-click it in the table to download the results.</source>
        <translation type="obsolete"> 已完成。双击表格中的该项以下载结果。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3084"/>
        <source>{} processings finished: 
 {} 
 Double-click it in the table to download the results</source>
        <translation type="obsolete">{} 个处理完成： 
 {} 
 双击表格中的该项以下载结果</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3092"/>
        <source>{} processings finished. 
 Double-click it in the table to download the results</source>
        <translation type="obsolete">{} 个处理完成。 
 双击表格中的该项以下载结果</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3123"/>
        <source>Please review or accept this processing until {}. Double click to add results to the map</source>
        <translation type="obsolete">请在 {} 前审核或接受此处理。双击以将结果添加到地图</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3128"/>
        <source>Double click to add results to the map.</source>
        <translation type="obsolete">双击以将结果添加到地图。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4040"/>
        <source>We have just set the authentication config for you. 
 You may need to restart QGIS to apply it so you could log in</source>
        <translation>我们已为您设置认证配置。
您可能需要重启QGIS以应用配置，然后才能登录</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4065"/>
        <source>Please restart QGIS before using OAuth2 login.</source>
        <translation>使用OAuth2登录前请重启QGIS。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4127"/>
        <source>Wrong token. Visit &quot;&lt;a href=&quot;https://app.mapflow.ai/account/api&quot;&gt;mapflow.ai&lt;/a&gt;&quot; to get a new one</source>
        <translation>令牌错误。请访问 &quot;&lt;a href=&quot;https://app.mapflow.ai/account/api&quot;&gt;mapflow.ai&lt;/a&gt;&quot; 获取新令牌</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4159"/>
        <source>Proxy error. Please, check your proxy settings.</source>
        <translation>代理错误。请检查您的代理设置。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4163"/>
        <source>Not enough rights for this action
in a shared project &apos;{project_name}&apos; ({user_role})</source>
        <translation>在共享项目 &apos;{project_name}&apos;（{user_role}）中权限不足，无法执行此操作</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4169"/>
        <source>This operation is forbidden for your account, contact us</source>
        <translation>您的账户无权执行此操作，请联系我们</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4174"/>
        <source>Error</source>
        <translation>错误</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3427"/>
        <source>No project that meets specified criteria was found</source>
        <translation type="obsolete">未找到符合指定条件的项目</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3431"/>
        <source>Project</source>
        <translation type="obsolete">项目</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4282"/>
        <source>You must upgrade your plugin version to continue work with Mapflow. 
The server requires version {server_version}, your plugin is {local_version}
Go to Plugins -&gt; Manage and Install Plugins -&gt; Upgradable</source>
        <translation>您必须升级插件版本才能继续使用Mapflow。
服务器要求版本 {server_version}，您的插件版本为 {local_version}
请转到插件 -&gt; 管理和安装插件 -&gt; 可升级</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4292"/>
        <source>A new version of Mapflow plugin {server_version} is released 
We recommend you to upgrade to get all the latest features
Go to Plugins -&gt; Manage and Install Plugins -&gt; Upgradable</source>
        <translation>Mapflow插件新版本 {server_version} 已发布
我们建议您升级以获取所有最新功能
请转到插件 -&gt; 管理和安装插件 -&gt; 可升级</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3043"/>
        <source>You can launch multiple image processing only if they have the same provider</source>
        <translation type="obsolete">仅当多个影像处理使用相同提供商时，您才能启动它们</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3072"/>
        <source>Selected search results must have the same zoom level</source>
        <translation type="obsolete">选中的搜索结果必须具有相同的缩放级别</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3722"/>
        <source>Duplication failed on copying data source</source>
        <translation type="obsolete">复制数据源时复制失败</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3737"/>
        <source>Duplication failed on copying model</source>
        <translation type="obsolete">复制模型时复制失败</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3759"/>
        <source>The following options no longer exist, so they have not been duplicated: {}</source>
        <translation type="obsolete">以下选项已不存在，因此未被复制：{}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3764"/>
        <source>Duplication failed on copying model options</source>
        <translation type="obsolete">复制模型选项时复制失败</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3773"/>
        <source>Provider &apos;{provider}&apos; is not enabled for your account</source>
        <translation type="obsolete">提供商 &apos;{provider}&apos; 对您的账户未启用</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3848"/>
        <source>Duplicated user provider</source>
        <translation type="obsolete">已复制用户提供商</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3739"/>
        <source>Only correctly finished processings with &apos;Review required&apos; status can be reviewed</source>
        <translation>只有正确完成且状态为“需要审核”的处理才可以进行审核</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="220"/>
        <source>The working directory &apos;{dir}&apos; is unavailable:&lt;br&gt;{error}&lt;br&gt;&lt;br&gt;It is needed to save processing results on your computer.</source>
        <translation>工作目录“{dir}”不可用：&lt;br&gt;{error}&lt;br&gt;&lt;br&gt;需要它才能将处理结果保存到您的计算机。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="585"/>
        <source>Restart</source>
        <translation>重启</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="625"/>
        <source>Start planned processing</source>
        <translation>开始计划处理</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="627"/>
        <source>Start processing</source>
        <translation>开始处理</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="639"/>
        <source>Select one or more images in search results to start planned processing</source>
        <translation>在搜索结果中选择一张或多张图像以开始计划处理</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="670"/>
        <source>No images was found</source>
        <translation>未找到图像</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="827"/>
        <source>AOI: {name}</source>
        <translation>AOI：{name}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="849"/>
        <source>No AOI</source>
        <translation>无 AOI</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1101"/>
        <source>There are no polygon layers to add as AOIs. Draw one on the map or load a vector layer first.</source>
        <translation>没有可作为 AOI 添加的多边形图层。请先在地图上绘制一个，或加载一个矢量图层。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1121"/>
        <source>The selected layer(s) have no polygon features to add.</source>
        <translation>所选图层没有可添加的多边形要素。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1185"/>
        <source>This AOI has no id yet and cannot be updated. Reopen the template and try again.</source>
        <translation>此 AOI 尚无 id，无法更新。请重新打开模板后再试。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1190"/>
        <source>Could not find this AOI&apos;s layer on the map. Reopen the template and try again.</source>
        <translation>在地图上找不到此 AOI 的图层。请重新打开模板后再试。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1193"/>
        <source>Editing AOI &apos;{name}&apos;: move its vertices on the map, then Save AOI.</source>
        <translation>正在编辑 AOI“{name}”：在地图上移动其顶点，然后保存 AOI。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1204"/>
        <source>New AOI</source>
        <translation>新建 AOI</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1207"/>
        <source>Draw the AOI polygon on the map, then Save AOI.</source>
        <translation>在地图上绘制 AOI 多边形，然后保存 AOI。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1245"/>
        <source>Save AOI</source>
        <translation>保存 AOI</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1246"/>
        <source>Cancel</source>
        <translation>取消</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1315"/>
        <source>The AOI has no geometry — draw or keep at least one polygon.</source>
        <translation>AOI 没有几何图形 — 请绘制或至少保留一个多边形。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1322"/>
        <source>The edited AOI has no valid geometry.</source>
        <translation>编辑后的 AOI 没有有效的几何图形。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1344"/>
        <source>Draw at least one polygon before saving.</source>
        <translation>保存前请至少绘制一个多边形。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1346"/>
        <source>Name the AOI</source>
        <translation>为 AOI 命名</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1346"/>
        <source>AOI name:</source>
        <translation>AOI 名称：</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1352"/>
        <source>AOI name must not exceed {limit} characters.</source>
        <translation>AOI 名称不得超过 {limit} 个字符。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1421"/>
        <source>Selected AOIs</source>
        <translation>已选 AOI</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1879"/>
        <source>Start date {cur} is earlier than searched ({base})</source>
        <translation>开始日期 {cur} 早于已搜索的日期（{base}）</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1882"/>
        <source>End date {cur} is later than searched ({base})</source>
        <translation>结束日期 {cur} 晚于已搜索的日期（{base}）</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1887"/>
        <source>Max cloud cover {cur}% is higher than searched ({base}%)</source>
        <translation>最大云量 {cur}% 高于已搜索的值（{base}%）</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1892"/>
        <source>Min intersection {cur}% is lower than searched ({base}%)</source>
        <translation>最小交集 {cur}% 低于已搜索的值（{base}%）</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1899"/>
        <source>Off-nadir range {lo}-{hi}° is wider than searched ({blo}-{bhi}°)</source>
        <translation>偏离天底角范围 {lo}-{hi}° 比已搜索的范围更宽（{blo}-{bhi}°）</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1912"/>
        <source>Showing all providers, but search was limited to: {base}</source>
        <translation>正在显示所有提供商，但搜索仅限于：{base}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1917"/>
        <source>Provider(s) not searched: {extra}</source>
        <translation>未搜索的提供商：{extra}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1923"/>
        <source>These filters are wider than the last search, so they will not bring more images. Run a new Search to fetch them:</source>
        <translation>这些筛选器比上次搜索更宽，因此不会带来更多图像。请重新搜索以获取它们：</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2254"/>
        <source>Cannot use &apos;{dir}&apos; as the working directory:
{error}

Please choose another directory.</source>
        <translation>无法将“{dir}”用作工作目录：
{error}

请选择其他目录。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2278"/>
        <source>Select directory…</source>
        <translation>选择目录…</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2279"/>
        <source>Later</source>
        <translation>稍后</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2346"/>
        <source>Search</source>
        <translation>搜索</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2346"/>
        <source>Plan search</source>
        <translation>计划搜索</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2336"/>
        <source>Seen</source>
        <translation>已查看</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2337"/>
        <source>Seen all</source>
        <translation>全部已查看</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2350"/>
        <source>Select a project to create a template</source>
        <translation>选择一个项目以创建模板</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2381"/>
        <source>Searching {datetime}</source>
        <translation>正在搜索 {datetime}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2388"/>
        <source>The search area is too large for immediate processing. The Planned Search will be created and run in the background. You will be notified when results are available.</source>
        <translation>搜索区域过大，无法立即处理。将创建计划搜索并在后台运行。结果就绪后会通知您。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2397"/>
        <source>Plan Search</source>
        <translation>计划搜索</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2447"/>
        <source>AOI name &apos;{name}&apos; exceeds {limit} characters</source>
        <translation>AOI 名称“{name}”超过 {limit} 个字符</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2517"/>
        <source>Please, specify a name for your search</source>
        <translation>请为您的搜索指定名称</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2533"/>
        <source>Creating planned search...</source>
        <translation>正在创建计划搜索…</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2532"/>
        <source>Planned search created successfully.</source>
        <translation type="obsolete">计划搜索创建成功。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2561"/>
        <source>Template creation failed</source>
        <translation>创建模板失败</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2601"/>
        <source>Updating template search parameters...</source>
        <translation>正在更新模板搜索参数…</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2611"/>
        <source>Template updated.</source>
        <translation>模板已更新。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2617"/>
        <source>Template update failed</source>
        <translation>更新模板失败</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2661"/>
        <source>This processing is not linked to any AOI geometry.</source>
        <translation>此处理未关联任何 AOI 几何图形。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2664"/>
        <source>Exclude this processing&apos;s area from the template&apos;s search? The already-processed area will be removed from the AOI(s).</source>
        <translation>从模板搜索中排除此次处理的区域？已处理的区域将从 AOI 中移除。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3539"/>
        <source>Could not mark image(s) as seen, please try again.</source>
        <translation>无法将图像标记为已查看，请重试。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3604"/>
        <source>Planned processing</source>
        <translation>计划处理</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3606"/>
        <source>Planned processing. New images: {count}</source>
        <translation>计划处理。新图像：{count}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3953"/>
        <source>A working directory is required to save the processing results on your computer.</source>
        <translation>需要一个工作目录才能将处理结果保存到您的计算机。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3979"/>
        <source>A working directory is required to save the area of interest on your computer.</source>
        <translation>需要一个工作目录才能将感兴趣区保存到您的计算机。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2552"/>
        <source>The template has been created, but is inactive.

You have reached the maximum number of active planned processings. Pause or delete another one before activating this template.</source>
        <translation>模板已创建，但处于未激活状态。

您已达到活动计划处理的最大数量。请先暂停或删除另一个，再激活此模板。</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="793"/>
        <source>&lt;b&gt;{name}&lt;/b&gt;&lt;br/&gt;&lt;b&gt;Status:&lt;/b&gt; {status}&lt;br/&gt;&lt;b&gt;Created:&lt;/b&gt; {created}&lt;br/&gt;&lt;b&gt;Active Until:&lt;/b&gt; {active_until}&lt;br/&gt;&lt;b&gt;Linked processings:&lt;/b&gt; {linked}&lt;br/&gt;&lt;b&gt;New images:&lt;/b&gt; {new_images}</source>
        <translation>&lt;b&gt;{name}&lt;/b&gt;&lt;br/&gt;&lt;b&gt;状态：&lt;/b&gt; {status}&lt;br/&gt;&lt;b&gt;创建时间：&lt;/b&gt; {created}&lt;br/&gt;&lt;b&gt;有效期至：&lt;/b&gt; {active_until}&lt;br/&gt;&lt;b&gt;关联的处理：&lt;/b&gt; {linked}&lt;br/&gt;&lt;b&gt;新图像：&lt;/b&gt; {new_images}</translation>
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
        <location filename="../dialogs/processing_details_dialog.py" line="47"/>
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
        <translation>请求中的键 &apos;url&apos; 必须是字符串，实际为 {url_type}。</translation>
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
        <translation>&apos;url&apos; 的格式无效且无法解析。错误：{parse_error_message}</translation>
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
        <translation>请求必须包含 &apos;profile&apos; 或 &apos;url&apos; 键</translation>
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
        <translation>您的 &apos;url&apos; 格式不匹配，Quadkey底图必须是包含 &quot;q&quot; 占位符的链接。</translation>
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
    <name>ProcessingService</name>
    <message>
        <location filename="../functional/service/processing_service.py" line="137"/>
        <source>Specify processing parameters</source>
        <translation>指定处理参数</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="142"/>
        <source>Please, specify a name for your processing</source>
        <translation>请为您的处理指定一个名称</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="147"/>
        <source>Processing area layer is corrupted or has invalid projection</source>
        <translation>处理区域图层已损坏或具有无效投影</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="149"/>
        <source>Please, select a valid area of interest</source>
        <translation>请选择有效的感兴趣区域</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="102"/>
        <source>Up to {} sq km can be processed at a time. Try splitting your area(s) into several processings.</source>
        <translation type="obsolete">一次最多可处理 {} 平方公里。请尝试将您的区域分割为多个处理。</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="189"/>
        <source>Selected AOI does not intersect the selected imagery</source>
        <translation>选择的感兴趣区域与所选影像没有交集</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="191"/>
        <source>This provider requires image ID. Use search tab to find imagery for you requirements, and select image in the table.</source>
        <translation>此提供商需要影像ID。请使用搜索选项卡查找符合您要求的影像，并在表格中选择影像。</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1112"/>
        <source>Not enough rights to start processing in a shared project ({})</source>
        <translation>权限不足，无法在共享项目（{}）中开始处理</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="248"/>
        <source>Set AOI to start processing</source>
        <translation>设置感兴趣区域以开始处理</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="250"/>
        <source>Error! Models are not initialized.
Please, make sure you have selected a project</source>
        <translation>错误！模型未初始化。
请确保您已选择项目</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="322"/>
        <source>Processing limit exceeded. Visit &quot;&lt;a href=&quot;https://app.mapflow.ai/account/balance&quot;&gt;Mapflow&lt;/a&gt;&quot; to top up your balance</source>
        <translation>超出处理限制。请访问 &quot;&lt;a href=&quot;https://app.mapflow.ai/account/balance&quot;&gt;Mapflow&lt;/a&gt;&quot; 充值余额</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="351"/>
        <source>Starting the processing...</source>
        <translation>正在开始处理...</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="361"/>
        <source>Could not launch processing! Error: {}.</source>
        <translation>无法启动处理！错误：{}。</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="405"/>
        <source>{cost} credits</source>
        <translation>{cost} 点数</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="409"/>
        <source> sq.km</source>
        <translation> 平方公里</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="460"/>
        <source>Success! We&apos;ll notify you when the processing has finished.</source>
        <translation>成功！处理完成后我们将通知您。</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="260"/>
        <source>Failed to start processing</source>
        <translation type="obsolete">启动处理失败</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="947"/>
        <source>Processing completed</source>
        <translation>处理完成</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="947"/>
        <source>Processing &apos;{name}&apos; has finished successfully</source>
        <translation>处理 &apos;{name}&apos; 已成功完成</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="957"/>
        <source>Processing failed</source>
        <translation>处理失败</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="957"/>
        <source>Processing &apos;{name}&apos; has failed</source>
        <translation>处理 &apos;{name}&apos; 失败</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1114"/>
        <source>Processing cost is not available:
{message}</source>
        <translation>处理费用不可用：
{message}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="496"/>
        <source>Delete selected processings?</source>
        <translation type="obsolete">删除选中的处理？</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="511"/>
        <source>Failed to remove processings with following ids: &lt;center&gt; {failed_ids}</source>
        <translation type="obsolete">无法删除以下ID的处理：&lt;center&gt; {failed_ids}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="517"/>
        <source>The selected data provider is unavailable on your plan. 
 Upgrade your subscription to get access to the data. 
See pricing at &lt;a href=&quot;https://mapflow.ai/pricing&quot;&gt;mapflow.ai&lt;/a&gt;</source>
        <translation>所选数据提供商在您的订阅计划中不可用。
升级订阅以获取数据访问权限。
请查看 &lt;a href=&quot;https://mapflow.ai/pricing&quot;&gt;mapflow.ai&lt;/a&gt; 的定价</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="528"/>
        <source>Processing creation failed</source>
        <translation>处理创建失败</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="157"/>
        <source>The processing area is {area} sq km, over the {limit} sq km limit. Try splitting your area(s) into several processings.</source>
        <translation>处理区域为 {area} 平方公里，超过 {limit} 平方公里的上限。请尝试将区域拆分为多次处理。</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="170"/>
        <source>An AOI is too large: its bounding box is {area} sq km, over the {limit} sq km limit. Reduce the area of interest.</source>
        <translation>某个 AOI 过大：其边界框为 {area} 平方公里，超过 {limit} 平方公里的上限。请缩小感兴趣区。</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="180"/>
        <source>the selected</source>
        <translation>所选</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="288"/>
        <source>Select one or more images in search results to start planned processing</source>
        <translation>在搜索结果中选择一张或多张图像以开始计划处理</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="340"/>
        <source>Starting planned processing...</source>
        <translation>正在开始计划处理…</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="989"/>
        <source>Rename template</source>
        <translation>重命名模板</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="989"/>
        <source>Template name:</source>
        <translation>模板名称：</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1000"/>
        <source>Please, specify template name</source>
        <translation>请指定模板名称</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1045"/>
        <source>Error renaming template: {}</source>
        <translation>重命名模板时出错：{}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1232"/>
        <source>Unknown server error</source>
        <translation>未知的服务器错误</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1129"/>
        <source>Delete selected items?</source>
        <translation>删除所选项目？</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1144"/>
        <source>Failed to remove items with following ids: &lt;center&gt; {failed_ids}</source>
        <translation>无法删除以下 id 的项目：&lt;center&gt; {failed_ids}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1210"/>
        <source>Template is not active</source>
        <translation>模板未激活</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1216"/>
        <source>Template paused successfully</source>
        <translation>模板暂停成功</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1218"/>
        <source>Failed to pause template: {}</source>
        <translation>暂停模板失败：{}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1236"/>
        <source>Error pausing template: {}</source>
        <translation>暂停模板时出错：{}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1254"/>
        <source>Template is already active</source>
        <translation>模板已处于激活状态</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1285"/>
        <source>Template resumed successfully</source>
        <translation>模板恢复成功</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1287"/>
        <source>Failed to resume template: {}</source>
        <translation>恢复模板失败：{}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1292"/>
        <source>Error resuming template: {}</source>
        <translation>恢复模板时出错：{}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1301"/>
        <source>Only failed templates can be restarted</source>
        <translation>只有失败的模板才能重启</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1313"/>
        <source>Template restarted successfully</source>
        <translation>模板重启成功</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1315"/>
        <source>Failed to restart template: {}</source>
        <translation>重启模板失败：{}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1319"/>
        <source>Error restarting template: {}</source>
        <translation>重启模板时出错：{}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1328"/>
        <source>Delete Template</source>
        <translation>删除模板</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1328"/>
        <source>Are you sure you want to delete the template &apos;{}&apos;?</source>
        <translation>确定要删除模板“{}”吗？</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1346"/>
        <source>Template deleted successfully</source>
        <translation>模板删除成功</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1348"/>
        <source>Failed to delete template: {}</source>
        <translation>删除模板失败：{}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1352"/>
        <source>Error deleting template: {}</source>
        <translation>删除模板时出错：{}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1364"/>
        <source>This AOI has no id yet and cannot be renamed. Reopen the template and try again.</source>
        <translation>此 AOI 尚无 id，无法重命名。请重新打开模板后再试。</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1368"/>
        <source>Rename AOI</source>
        <translation>重命名 AOI</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1368"/>
        <source>AOI name:</source>
        <translation>AOI 名称：</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1378"/>
        <source>Please, specify AOI name</source>
        <translation>请指定 AOI 名称</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1381"/>
        <source>AOI name must not exceed {limit} characters</source>
        <translation>AOI 名称不得超过 {limit} 个字符</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1403"/>
        <source>Delete selected AOI(s)?</source>
        <translation>删除所选 AOI？</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1441"/>
        <source>AOI update failed: {}</source>
        <translation>更新 AOI 失败：{}</translation>
    </message>
</context>
<context>
    <name>ProcessingTable</name>
    <message>
        <location filename="../dialogs/static/ui/review_dialog.ui" line="25"/>
        <source>(unnamed)</source>
        <translation type="obsolete">(未命名)</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/review_dialog.ui" line="25"/>
        <source>AOI</source>
        <translation type="obsolete">AOI</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/review_dialog.ui" line="25"/>
        <source>Created</source>
        <translation type="obsolete">已创建</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/review_dialog.ui" line="25"/>
        <source>Failed</source>
        <translation type="obsolete">失败</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/review_dialog.ui" line="25"/>
        <source>Failed ({ok}/{total})</source>
        <translation type="obsolete">失败（{ok}/{total}）</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/review_dialog.ui" line="25"/>
        <source>In progress ({ok}/{total})</source>
        <translation type="obsolete">进行中（{ok}/{total}）</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/review_dialog.ui" line="25"/>
        <source>Inactive</source>
        <translation type="obsolete">未激活</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/review_dialog.ui" line="25"/>
        <source>No AOI</source>
        <translation type="obsolete">无 AOI</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/review_dialog.ui" line="25"/>
        <source>OK ({ok}/{total})</source>
        <translation type="obsolete">完成（{ok}/{total}）</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/review_dialog.ui" line="25"/>
        <source>OK ({total})</source>
        <translation type="obsolete">完成（{total}）</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/review_dialog.ui" line="25"/>
        <source>Planned</source>
        <translation type="obsolete">计划</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/review_dialog.ui" line="25"/>
        <source>Searching</source>
        <translation type="obsolete">搜索中</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/review_dialog.ui" line="25"/>
        <source>Updated</source>
        <translation type="obsolete">已更新</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/review_dialog.ui" line="25"/>
        <source>Updated ({count})</source>
        <translation type="obsolete">已更新（{count}）</translation>
    </message>
</context>
<context>
    <name>ProcessingView</name>
    <message>
        <location filename="../functional/view/processing_view.py" line="230"/>
        <source>Please review or accept this processing until {}. Double click to add results to the map</source>
        <translation>请在 {} 前审核或接受此处理。双击以将结果添加到地图</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="235"/>
        <source>Double click to add results to the map.</source>
        <translation>双击以将结果添加到地图。</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="321"/>
        <source>Loading...</source>
        <translation>加载中...</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="322"/>
        <source>Fetching your processings from server, please wait</source>
        <translation>正在从服务器获取您的处理，请稍候</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="379"/>
        <source>Processing cost: {cost} credits</source>
        <translation>处理费用：{cost} 点数</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="388"/>
        <source> failed with error:
</source>
        <translation> 失败，错误：
</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="395"/>
        <source>{} processings failed: 
 {} 
 See tooltip over the processings table for error details</source>
        <translation>{} 个处理失败： 
 {} 
 请查看处理表格上的工具提示以获取错误详情</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="402"/>
        <source>{} processings failed: 
 See tooltip over the processings table for error details</source>
        <translation>{} 个处理失败： 
 请查看处理表格上的工具提示以获取错误详情</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="414"/>
        <source> finished. Double-click it in the table to download the results.</source>
        <translation> 已完成。双击表格中的该项以下载结果。</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="422"/>
        <source>{} processings finished: 
 {} 
 Double-click it in the table to download the results</source>
        <translation>{} 个处理完成： 
 {} 
 双击表格中的该项以下载结果</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="430"/>
        <source>{} processings finished. 
 Double-click it in the table to download the results</source>
        <translation>{} 个处理完成。 
 双击表格中的该项以下载结果</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="36"/>
        <source>Newest first</source>
        <translation>最新优先</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="36"/>
        <source>Oldest first</source>
        <translation>最旧优先</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="36"/>
        <source>A-Z</source>
        <translation>从A到Z</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="36"/>
        <source>Z-A</source>
        <translation>从Z到A</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="36"/>
        <source>Status A-Z</source>
        <translation>状态 从A到Z</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="36"/>
        <source>Status Z-A</source>
        <translation>状态 从Z到A</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="45"/>
        <source>Filter processings</source>
        <translation>筛选处理</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="140"/>
        <source>Open Details</source>
        <translation>打开详情</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="142"/>
        <source>Pause Template</source>
        <translation>暂停模板</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="143"/>
        <source>Resume Template</source>
        <translation>恢复模板</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="145"/>
        <source>Delete Template</source>
        <translation>删除模板</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="212"/>
        <source>Planned processing</source>
        <translation>计划处理</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="214"/>
        <source>Planned processing. New images: {count}</source>
        <translation>计划处理。新图像：{count}</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="219"/>
        <source>Template AOI</source>
        <translation>模板 AOI</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="221"/>
        <source>Template AOI with new images</source>
        <translation>含新图像的模板 AOI</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="224"/>
        <source>Processing from this AOI. Double-click to load results.</source>
        <translation>此 AOI 的处理。双击以加载结果。</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="226"/>
        <source>Processings not intersecting any AOI</source>
        <translation>与任何 AOI 都不相交的处理</translation>
    </message>
</context>
<context>
    <name>ProjectDialog</name>
    <message>
        <location filename="../dialogs/static/ui/project_dialog.ui" line="14"/>
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
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="82"/>
        <source>Name:</source>
        <translation>名称：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="132"/>
        <source>Data source:</source>
        <translation>数据源：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="216"/>
        <source>Zoom:</source>
        <translation>缩放级别：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="232"/>
        <source>Model options:</source>
        <translation>模型选项：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="248"/>
        <source>Price:</source>
        <translation>价格：</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="332"/>
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
    <name>ProjectProcessingController</name>
    <message>
        <location filename="../functional/controller/processing_controller.py" line="213"/>
        <source>Do you really want to remove project {}? This action cannot be undone, all processings will be lost!</source>
        <translation>您确定要删除项目 {} 吗？此操作无法撤销，所有处理都将丢失！</translation>
    </message>
    <message>
        <location filename="../functional/controller/processing_controller.py" line="107"/>
        <source>Processing</source>
        <translation>处理</translation>
    </message>
</context>
<context>
    <name>ProjectService</name>
    <message>
        <location filename="../functional/service/project_service.py" line="238"/>
        <source>Project: &lt;b&gt;{}</source>
        <translation>项目：&lt;b&gt;{}</translation>
    </message>
    <message>
        <location filename="../functional/service/project_service.py" line="256"/>
        <source>No project selected</source>
        <translation>未选择项目</translation>
    </message>
    <message>
        <location filename="../functional/service/project_service.py" line="258"/>
        <source>You can&apos;t remove or modify default project</source>
        <translation>您不能删除或修改默认项目</translation>
    </message>
    <message>
        <location filename="../functional/service/project_service.py" line="261"/>
        <source>Not enough rights to delete or update shared project ({})</source>
        <translation>权限不足，无法删除或更新共享项目（{}）</translation>
    </message>
</context>
<context>
    <name>ProjectView</name>
    <message>
        <location filename="../functional/view/project_view.py" line="59"/>
        <source>See projects</source>
        <translation>查看项目</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="61"/>
        <source>See processings</source>
        <translation>查看处理</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="63"/>
        <source>Filter projects by name</source>
        <translation>按名称筛选项目</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="64"/>
        <source>Create project</source>
        <translation>创建项目</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="66"/>
        <source>A-Z</source>
        <translation>A-Z</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="66"/>
        <source>Z-A</source>
        <translation>Z-A</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="66"/>
        <source>Newest first</source>
        <translation>最新优先</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="66"/>
        <source>Oldest first</source>
        <translation>最旧优先</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="66"/>
        <source>Updated recently</source>
        <translation>最近更新</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="66"/>
        <source>Updated long ago</source>
        <translation>很久前更新</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="164"/>
        <source>Project</source>
        <translation>项目</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="170"/>
        <source>Processing</source>
        <translation>处理</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="145"/>
        <source>No project that meets specified criteria was found</source>
        <translation>未找到符合指定条件的项目</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="118"/>
        <source>Succeeded: {ok} · Failed: {failed} · Planned: {templates}</source>
        <translation>成功：{ok} · 失败：{failed} · 计划：{templates}</translation>
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
        <translation type="obsolete">Maxar WMTS</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="88"/>
        <source>Name</source>
        <translation>名称</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="112"/>
        <source>Login</source>
        <translation>登录名</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="122"/>
        <source>Password</source>
        <translation>密码</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="129"/>
        <source>CRS</source>
        <translation>坐标系</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="154"/>
        <source>Projection of the tile layer. The most popular is Web Mercator, use it if you are not sure</source>
        <translation>瓦片图层的投影。最流行的是Web墨卡托投影，如果不确定请使用它</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="158"/>
        <source>EPSG:3857</source>
        <translation>EPSG:3857</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="163"/>
        <source>EPSG:3395</source>
        <translation>EPSG:3395</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="171"/>
        <source>Warninig! Login and password, if saved, will be stored in QGIS settings without encryption!</source>
        <translation>警告！登录名和密码（如果保存）将以未加密形式存储在QGIS设置中！</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="174"/>
        <source>Save login and password</source>
        <translation>保存登录名和密码</translation>
    </message>
</context>
<context>
    <name>ProviderService</name>
    <message>
        <location filename="../functional/service/provider_service.py" line="109"/>
        <source>Providers are not initialized</source>
        <translation>提供商未初始化</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="191"/>
        <source>Choose imagery collection or image to start processing</source>
        <translation>选择影像集或影像以开始处理</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="197"/>
        <source>This provider requires image ID. Use search tab to find imagery for you requirements, and select image in the table.</source>
        <translation>此提供商需要影像ID。请使用搜索选项卡查找符合您要求的影像，并在表格中选择影像。</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="316"/>
        <source>You can launch multiple image processing only if it has the same provider of mosaic type</source>
        <translation>仅当多个影像处理使用相同提供商（影像集类型）时，您才能启动它们</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="346"/>
        <source>Duplication failed on copying data source</source>
        <translation>复制数据源时复制失败</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="354"/>
        <source>Model &apos;{wd}&apos; is not enabled for your account</source>
        <translation>模型 &apos;{wd}&apos; 对您的账户未启用</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="383"/>
        <source>The following options no longer exist, so they have not been duplicated: {}</source>
        <translation>以下选项已不存在，因此未被复制：{}</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="388"/>
        <source>Duplication failed on copying model options</source>
        <translation>复制模型选项时复制失败</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="397"/>
        <source>Provider &apos;{provider}&apos; is not enabled for your account</source>
        <translation>提供商 &apos;{provider}&apos; 对您的账户未启用</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="495"/>
        <source>Duplicated user provider</source>
        <translation>已复制用户提供商</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="217"/>
        <source>Selected search results must be of the same product type</source>
        <translation>选中的搜索结果必须是相同的产品类型</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="227"/>
        <source>Selected search results must have the same zoom level</source>
        <translation>选中的搜索结果必须具有相同的缩放级别</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="361"/>
        <source>Duplication failed on copying model</source>
        <translation>复制模型时复制失败</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="268"/>
        <source>Geometry area is {aoiArea:.2f} sq km, which is smaller than the minimum required area for {providerName} data provider ({providerMinArea} sq km)</source>
        <translation>几何面积为 {aoiArea:.2f} 平方公里，小于数据提供商 {providerName} 所需的最小面积（{providerMinArea} 平方公里）</translation>
    </message>
</context>
<context>
    <name>QPlatformTheme</name>
    <message>
        <location filename="../mapflow.py" line="163"/>
        <source>Cancel</source>
        <translation>取消</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="164"/>
        <source>&amp;Yes</source>
        <translation>&amp;是</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="165"/>
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
    <name>ReviewDialog</name>
    <message>
        <location filename="../dialogs/review_dialog.py" line="25"/>
        <source>Review {processing}</source>
        <translation>审核 {processing}</translation>
    </message>
</context>
<context>
    <name>SelectAoiLayersDialog</name>
    <message>
        <location filename="../dialogs/select_aoi_layers_dialog.py" line="22"/>
        <source>Choose polygon layers to add as AOIs</source>
        <translation>选择要添加为 AOI 的多边形图层</translation>
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
        <location filename="../dialogs/processing_dialog.py" line="26"/>
        <source>Processing name must not be empty!</source>
        <translation>处理名称不能为空！</translation>
    </message>
    <message>
        <location filename="../dialogs/processing_dialog.py" line="34"/>
        <source>Edit processing {}</source>
        <translation>编辑处理 {}</translation>
    </message>
</context>
<context>
    <name>UploadRasterLayersDialog</name>
    <message>
        <location filename="../dialogs/upload_raster_layer_dialog.py" line="17"/>
        <source>Choose raster layers to upload to imagery collection</source>
        <translation>选择要上传到影像集的栅格图层</translation>
    </message>
</context>
<context>
    <name>raterLayerSelection</name>
    <message>
        <location filename="../dialogs/static/ui/raster_layers_dialog.ui" line="14"/>
        <source>Multiple selection</source>
        <translation>多项选择</translation>
    </message>
</context>
<context>
    <name>reviewDialog</name>
    <message>
        <location filename="../dialogs/static/ui/review_dialog.ui" line="14"/>
        <source>Dialog</source>
        <translation>对话框</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/review_dialog.ui" line="25"/>
        <source>Map layer with review</source>
        <translation>带有审核结果的地图图层</translation>
    </message>
</context>
</TS>
