<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="pt_BR">
<context>
    <name>ApiErrors</name>
    <message>
        <location filename="../errors/api_errors.py" line="8" />
        <source>Upgrade your subscription to get access to Maxar imagery</source>
        <translation>Atualize a sua subscrição para ter acesso às imagens Maxar</translation>
    </message>
    <message>
        <location filename="../errors/api_errors.py" line="9" />
        <source>Geometry area is {aoiArea} sq km, which is smaller than the minimum required area for {providerName} data provider ({providerMinArea} sq km)</source>
        <translation>A área da geometria é de {aoiArea} km², que é menor do que a área mínima exigida pelo fornecedor de dados {providerName} ({providerMinArea} km²)</translation>
    </message>
    <message>
        <location filename="../errors/api_errors.py" line="13" />
        <source>Up to {templateAreaLimit} sq km can be used for a planned processing. Try reducing your area of interest.</source>
        <translation>Podem ser usados até {templateAreaLimit} km² para um processamento planeado. Tente reduzir a sua área de interesse.</translation>
    </message>
    <message>
        <location filename="../errors/api_errors.py" line="17" />
        <source>The processing area is too large: {area} sq.m exceeds the {aoiAreaLimit} sq.m limit. Reduce the area of interest.</source>
        <translation>A área de processamento é demasiado grande: {area} m² excede o limite de {aoiAreaLimit} m². Reduza a área de interesse.</translation>
    </message>
    <message>
        <location filename="../errors/api_errors.py" line="23" />
        <source>You don't have enough limit to create this planned processing. Please contact your administrator to increase the limit.</source>
        <translation>Não tem limite suficiente para criar este processamento planeado. Contacte o seu administrador para aumentar o limite.</translation>
    </message>
    <message>
        <location filename="../errors/api_errors.py" line="27" />
        <source>You have reached the maximum number of active planned processings. Pause or delete another one before activating this template.</source>
        <translation>Atingiu o número máximo de processamentos planeados ativos. Pause ou elimine outro antes de ativar este modelo.</translation>
    </message>
</context>
<context>
    <name>AreaCalculatorService</name>
    <message>
        <location filename="../functional/service/area_calculator_service.py" line="66" />
        <source>Not enough rights to start processing in a shared project ({})</source>
        <translation>Permissões insuficientes para iniciar processamento num projeto partilhado ({})</translation>
    </message>
    <message>
        <location filename="../functional/service/area_calculator_service.py" line="43" />
        <source>Set AOI to start processing</source>
        <translation>Definir AOI para iniciar processamento</translation>
    </message>
    <message>
        <location filename="../functional/service/area_calculator_service.py" line="68" />
        <source>AOI must contain not more than {} polygons</source>
        <translation>A AOI não deve conter mais do que {} polígonos</translation>
    </message>
    <message>
        <location filename="../functional/service/area_calculator_service.py" line="108" />
        <source>Use extent of '{name}'</source>
        <translation>Usar extensão de '{name}'</translation>
    </message>
    <message>
        <location filename="../functional/service/area_calculator_service.py" line="113" />
        <source>Use imagery extent</source>
        <translation>Usar extensão da imagem</translation>
    </message>
    <message>
        <location filename="../functional/service/area_calculator_service.py" line="118" />
        <source>Selected AOI does not intersect the selected imagery</source>
        <translation>A AOI selecionada não intersecta a imagem selecionada</translation>
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
        <translation>AOI inválida. A AOI deve estar dentro dos limites: 
[-180, 180] por longitude, [-90, 90] por latitude</translation>
    </message>
    <message>
        <location filename="../functional/service/area_calculator_service.py" line="200" />
        <source>Providers are not initialized</source>
        <translation>Fornecedores não estão inicializados</translation>
    </message>
</context>
<context>
    <name>Config</name>
    <message>
        <location filename="../config.py" line="14" />
        <source>Product Type</source>
        <translation>Tipo de Produto</translation>
    </message>
    <message>
        <location filename="../config.py" line="15" />
        <source>Provider Name</source>
        <translation>Nome do Fornecedor</translation>
    </message>
    <message>
        <location filename="../config.py" line="16" />
        <source>Preview</source>
        <translation>Pré-visualização</translation>
    </message>
    <message>
        <location filename="../config.py" line="17" />
        <source>Sensor</source>
        <translation>Sensor</translation>
    </message>
    <message>
        <location filename="../config.py" line="18" />
        <source>Band Order</source>
        <translation>Ordem das Bandas</translation>
    </message>
    <message>
        <location filename="../config.py" line="100" />
        <source>Cloud %</source>
        <translation>Nuvens %</translation>
    </message>
    <message>
        <location filename="../config.py" line="20" />
        <source>Off Nadir</source>
        <translation>Fora de Nadir</translation>
    </message>
    <message>
        <location filename="../config.py" line="97" />
        <source>Date &amp; Time</source>
        <translation>Data &amp; Hora</translation>
    </message>
    <message>
        <location filename="../config.py" line="22" />
        <source>Zoom level</source>
        <translation>Nível de zoom</translation>
    </message>
    <message>
        <location filename="../config.py" line="23" />
        <source>Spatial Resolution, m</source>
        <translation>Resolução Espacial, m</translation>
    </message>
    <message>
        <location filename="../config.py" line="24" />
        <source>Image ID</source>
        <translation>ID da Imagem</translation>
    </message>
    <message>
        <location filename="../config.py" line="29" />
        <source>Project</source>
        <translation>Projeto</translation>
    </message>
    <message>
        <location filename="../config.py" line="27" />
        <source>Succeeded</source>
        <translation type="obsolete">Bem-sucedido</translation>
    </message>
    <message>
        <location filename="../config.py" line="28" />
        <source>Failed</source>
        <translation type="obsolete">Falhou</translation>
    </message>
    <message>
        <location filename="../config.py" line="31" />
        <source>Author</source>
        <translation>Autor</translation>
    </message>
    <message>
        <location filename="../config.py" line="32" />
        <source>Updated at</source>
        <translation>Atualizado em</translation>
    </message>
    <message>
        <location filename="../config.py" line="33" />
        <source>Created at</source>
        <translation>Criado em</translation>
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
        <translation>Confirmar início do processamento</translation>
    </message>
    <message>
        <location filename="../dialogs/confirm_processing_start_dialog.py" line="32" />
        <source>No zoom selected</source>
        <translation>Nenhum zoom selecionado</translation>
    </message>
    <message>
        <location filename="../dialogs/confirm_processing_start_dialog.py" line="42" />
        <source>No options selected</source>
        <translation>Nenhuma opção selecionada</translation>
    </message>
</context>
<context>
    <name>CreateMosaicDialog</name>
    <message>
        <location filename="../dialogs/mosaic_dialog.py" line="30" />
        <source>Imagery collection</source>
        <translation>Coleção de imagens</translation>
    </message>
    <message>
        <location filename="../dialogs/mosaic_dialog.py" line="37" />
        <source>Imagery collection name must not be empty!</source>
        <translation>O nome da coleção de imagens não pode estar vazio!</translation>
    </message>
</context>
<context>
    <name>CreateProjectDialog</name>
    <message>
        <location filename="../dialogs/project_dialog.py" line="36" />
        <source>Create project</source>
        <translation>Criar projeto</translation>
    </message>
</context>
<context>
    <name>DataCatalogApi</name>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="277" />
        <source>Error</source>
        <translation>Erro</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="126" />
        <source>Could not delete imagery collection '{mosaic_name}'</source>
        <translation>Não foi possível eliminar a coleção de imagens '{mosaic_name}'</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="128" />
        <source>Error. Could not delete following imagery collections:</source>
        <translation>Erro. Não foi possível eliminar as seguintes coleções de imagens:</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="170" />
        <source>Failed to load imagery collection. 
Please try again later or report error</source>
        <translation>Falha ao carregar coleção de imagens.
Por favor, tente novamente mais tarde ou reporte o erro</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="231" />
        <source>This operation is forbidden for your account, contact us</source>
        <translation>Esta operação é proibida para a sua conta, contacte-nos</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="233" />
        <source>Imagery collection '{mosaic_name}' does not exist</source>
        <translation>A coleção de imagens '{mosaic_name}' não existe</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="235" />
        <source>Authentication error. Please log in to your account</source>
        <translation>Erro de autenticação. Por favor, faça login na sua conta</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="237" />
        <source>The image does not meet this imagery collection '{mosaic_name}' parameters. 
Either modify your image or upload it to a different collection</source>
        <translation>A imagem não cumpre os parâmetros da coleção de imagens '{mosaic_name}'.
Modifique a sua imagem ou faça o upload para uma coleção diferente</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="240" />
        <source>Could not upload '{image}' to imagery collection</source>
        <translation>Não foi possível fazer o upload de '{image}' para a coleção de imagens</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="242" />
        <source>Could not upload following images:
{images}</source>
        <translation>Não foi possível fazer o upload das seguintes imagens:
{images}</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="278" />
        <source>Could not delete '{image}' from imagery collection</source>
        <translation>Não foi possível eliminar '{image}' da coleção de imagens</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="280" />
        <source>Error. Could not delete following images:</source>
        <translation>Erro. Não foi possível eliminar as seguintes imagens:</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="227" />
        <source>Request timed out or was canceled. 
Try increasing QGIS global timeout setting: 
Settings -&gt; Options -&gt; Network -&gt; Timeout</source>
        <translation>O pedido expirou ou foi cancelado.
Tente aumentar a definição de tempo limite global do QGIS:
Definições -&gt; Opções -&gt; Rede -&gt; Tempo limite</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="364" />
        <source>Image not found or you don't have access to it</source>
        <translation>Imagem não encontrada ou não tem acesso a ela</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="366" />
        <source>This image is not available for download</source>
        <translation>Esta imagem não está disponível para descarregar</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="368" />
        <source>Image data is not yet available. Please try again later</source>
        <translation>Os dados da imagem ainda não estão disponíveis. Por favor, tente novamente mais tarde</translation>
    </message>
    <message>
        <location filename="../functional/api/data_catalog_api.py" line="374" />
        <source>Download error</source>
        <translation>Erro ao descarregar</translation>
    </message>
</context>
<context>
    <name>DataCatalogService</name>
    <message>
        <location filename="../functional/service/data_catalog.py" line="76" />
        <source>Choose image to upload</source>
        <translation>Escolha a imagem para fazer upload</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="118" />
        <source>&lt;center&gt;Creation of imagery collection '{mosaic_name}' failed&lt;br&gt;while trying to upload '{image}'</source>
        <translation>&lt;center&gt;Criação da coleção de imagens '{mosaic_name}' falhou&lt;br&gt;ao tentar fazer upload de '{image}'</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="199" />
        <source>&lt;center&gt;Delete imagery collection &lt;b&gt;'{name}'&lt;/b&gt;?</source>
        <translation>&lt;center&gt;Eliminar coleção de imagens &lt;b&gt;'{name}'&lt;/b&gt;?</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="202" />
        <source>&lt;center&gt;Delete following imagery collections:&lt;br&gt;&lt;b&gt;'{names}'&lt;/b&gt;?</source>
        <translation>&lt;center&gt;Eliminar as seguintes coleções de imagens:&lt;br&gt;&lt;b&gt;'{names}'&lt;/b&gt;?</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="205" />
        <source>&lt;center&gt;Delete &lt;b&gt;{len}&lt;/b&gt; imagery collections?</source>
        <translation>&lt;center&gt;Eliminar &lt;b&gt;{len}&lt;/b&gt; coleções de imagens?</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="245" />
        <source>Please, select existing imagery collection</source>
        <translation>Por favor, selecione uma coleção de imagens existente</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="247" />
        <source>Choose images to upload</source>
        <translation>Escolha imagens para fazer upload</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="296" />
        <source>Raster TIFF file must be georeferenced, have size less than {size} pixels and file size less than {memory}</source>
        <translation>O ficheiro raster TIFF deve estar georreferenciado, ter tamanho inferior a {size} píxeis e tamanho de ficheiro inferior a {memory}</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="300" />
        <source>&lt;center&gt;&lt;b&gt;Error uploading '{name}'&lt;/b&gt;</source>
        <translation>&lt;center&gt;&lt;b&gt;Erro ao fazer upload de '{name}'&lt;/b&gt;</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="305" />
        <source>&lt;b&gt;Not enough storage space. &lt;/b&gt;You have {free_storage} left, but '{name}' is {image_size}</source>
        <translation>&lt;b&gt;Espaço de armazenamento insuficiente. &lt;/b&gt;Tem {free_storage} disponíveis, mas '{name}' ocupa {image_size}</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="400" />
        <source>&lt;center&gt;Delete image &lt;b&gt;'{name}'&lt;/b&gt; from '{mosaic}' imagery collection?</source>
        <translation>&lt;center&gt;Eliminar imagem &lt;b&gt;'{name}'&lt;/b&gt; da coleção de imagens '{mosaic}'?</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="403" />
        <source>&lt;center&gt;Delete following images from '{mosaic}' imagery collection:&lt;br&gt;&lt;b&gt;'{names}'&lt;/b&gt;?</source>
        <translation>&lt;center&gt;Eliminar as seguintes imagens da coleção de imagens '{mosaic}':&lt;br&gt;&lt;b&gt;'{names}'&lt;/b&gt;?</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="406" />
        <source>&lt;center&gt;Delete &lt;b&gt;{len}&lt;/b&gt; images from '{mosaic}' imagery collection?</source>
        <translation>&lt;center&gt;Eliminar &lt;b&gt;{len}&lt;/b&gt; imagens da coleção de imagens '{mosaic}'?</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="495" />
        <source>Image name should be 1-255 characters long</source>
        <translation>O nome da imagem deve ter entre 1 e 255 caracteres</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="667" />
        <source>Source imagery collection with id '{}' was not found </source>
        <translation>Coleção de imagens fonte com id '{}' não foi encontrada</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="669" />
        <source>Source image with id '{}' was not found in any of your imagery collections</source>
        <translation>Imagem fonte com id '{}' não foi encontrada em nenhuma das suas coleções de imagens</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="515" />
        <source>Download URL not available</source>
        <translation>URL de descarga não disponível</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="517" />
        <source>Save image as</source>
        <translation>Guardar imagem como</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="535" />
        <source>Failed to download image: {}</source>
        <translation>Falha ao descarregar a imagem: {}</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="542" />
        <source>Image saved to {}</source>
        <translation>Imagem guardada em {}</translation>
    </message>
    <message>
        <location filename="../functional/service/data_catalog.py" line="544" />
        <source>Failed to save file: {}</source>
        <translation>Falha ao guardar o ficheiro: {}</translation>
    </message>
</context>
<context>
    <name>DataCatalogView</name>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="24" />
        <source>Upload from file</source>
        <translation>Upload a partir de ficheiro</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="25" />
        <source>Choose raster layer</source>
        <translation>Escolha camada raster</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="45" />
        <source>Add images</source>
        <translation>Adicionar imagens</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="46" />
        <source>Show images</source>
        <translation>Mostrar imagens</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="49" />
        <source>Preview</source>
        <translation>Pré-visualização</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="48" />
        <source>Edit</source>
        <translation>Editar</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="50" />
        <source>Info</source>
        <translation>Informação</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="51" />
        <source>Rename</source>
        <translation>Renomear</translation>
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
        <translation>Maiores primeiro</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="75" />
        <source>Smallest first</source>
        <translation>Menores primeiro</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="75" />
        <source>Newest first</source>
        <translation>Mais recentes primeiro</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="75" />
        <source>Oldest first</source>
        <translation>Mais antigos primeiro</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="96" />
        <source>More about My imagery</source>
        <translation>Mais sobre As minhas imagens</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="519" />
        <source>Filter imagery collections by name or id</source>
        <translation>Filtrar coleções de imagens por nome ou id</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="130" />
        <source>Imagery collections</source>
        <translation>Coleções de imagens</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="293" />
        <source>Size</source>
        <translation>Tamanho</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="130" />
        <source>Created</source>
        <translation>Criado</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="469" />
        <source>Double-click to show images</source>
        <translation>Duplo clique para mostrar imagens</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="178" />
        <source>Number of images: {count} 
</source>
        <translation>Número de imagens: {count}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="188" />
        <source>Size: {mosaic_size} 
Pixel size: {pixel_size} 
CRS: {crs} 
Number of bands: {count} 
</source>
        <translation>Tamanho: {mosaic_size}
Tamanho do pixel: {pixel_size}
CRS: {crs}
Número de bandas: {count}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="197" />
        <source>Created: {date} at {time} 
Tags: {tags}</source>
        <translation>Criado: {date} às {time}
Etiquetas: {tags}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="249" />
        <source>&lt;b&gt;Name&lt;/b&gt;: {filename}                              &lt;br&gt;&lt;b&gt;Uploaded&lt;/b&gt;&lt;/br&gt;: {date} at {time}                              &lt;br&gt;&lt;b&gt;Size&lt;/b&gt;&lt;/br&gt;: {file_size}                              &lt;br&gt;&lt;b&gt;CRS&lt;/b&gt;&lt;/br&gt;: {crs}                              &lt;br&gt;&lt;b&gt;Number of bands&lt;/br&gt;&lt;/b&gt;: {bands}                              &lt;br&gt;&lt;b&gt;Width&lt;/br&gt;&lt;/b&gt;: {width} pixels                              &lt;br&gt;&lt;b&gt;Height&lt;/br&gt;&lt;/b&gt;: {height} pixels                              &lt;br&gt;&lt;b&gt;Pixel size&lt;/br&gt;&lt;/b&gt;: {pixel_size}</source>
        <translation>&lt;b&gt;Nome&lt;/b&gt;: {filename}&lt;br&gt;&lt;b&gt;Carregado&lt;/b&gt;: {date} às {time}&lt;br&gt;&lt;b&gt;Tamanho&lt;/b&gt;: {file_size}&lt;br&gt;&lt;b&gt;CRS&lt;/b&gt;: {crs}&lt;br&gt;&lt;b&gt;Número de bandas&lt;/b&gt;: {bands}&lt;br&gt;&lt;b&gt;Largura&lt;/b&gt;: {width} píxeis&lt;br&gt;&lt;b&gt;Altura&lt;/b&gt;: {height} píxeis&lt;br&gt;&lt;b&gt;Tamanho do pixel&lt;/b&gt;: {pixel_size}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="293" />
        <source>Images</source>
        <translation>Imagens</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="293" />
        <source>Uploaded</source>
        <translation>Carregado</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="349" />
        <source>No imagery collection with id '{mosaic_id}' was found</source>
        <translation>Nenhuma coleção de imagens com id '{mosaic_id}' foi encontrada</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="362" />
        <source>No image with id '{image_id}' was found</source>
        <translation>Nenhuma imagem com id '{image_id}' foi encontrada</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="376" />
        <source>Your data: {taken}. Free space: {free}</source>
        <translation>Os seus dados: {taken}. Espaço livre: {free}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="392" />
        <source>Selected imagery collection: &lt;b&gt;{mosaic_name}</source>
        <translation>Coleção de imagens selecionada: &lt;b&gt;{mosaic_name}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="406" />
        <source>No imagery collection selected</source>
        <translation>Nenhuma coleção de imagens selecionada</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="428" />
        <source>Uploaded: {date} at {time} 
File size: {size} 
Pixel size: {pixel_size} 
CRS: {crs} 
Bands: {count}</source>
        <translation>Carregado: {date} às {time}
Tamanho do ficheiro: {size}
Tamanho do pixel: {pixel_size}
CRS: {crs}
Bandas: {count}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="441" />
        <source>Selected image: &lt;b&gt;{image_name}</source>
        <translation>Imagem selecionada: &lt;b&gt;{image_name}</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="456" />
        <source>No image selected</source>
        <translation>Nenhuma imagem selecionada</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="466" />
        <source>'Cmd' + click to deselect</source>
        <translation>'Cmd' + clique para desmarcar</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="466" />
        <source>'Ctrl' + click to deselect</source>
        <translation>'Ctrl' + clique para desmarcar</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="483" />
        <source>Delete image</source>
        <translation>Eliminar imagem</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="484" />
        <source>Add image</source>
        <translation>Adicionar imagem</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="497" />
        <source>Filter images by name or id</source>
        <translation>Filtrar imagens por nome ou id</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="504" />
        <source>Delete collection</source>
        <translation>Eliminar coleção</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="505" />
        <source>Add collection</source>
        <translation>Adicionar coleção</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="451" />
        <source>Download</source>
        <translation>Descarregar</translation>
    </message>
    <message>
        <location filename="../functional/view/data_catalog_view.py" line="449" />
        <source>Image is not available for download</source>
        <translation>A imagem não está disponível para descarregar</translation>
    </message>
</context>
<context>
    <name>DataErrors</name>
    <message>
        <location filename="../errors/data_errors.py" line="8" />
        <source>File {filename} cannot be processed. Parameters {bad_parameters} are incompatible with our catalog. See the documentation for more info.</source>
        <translation>O ficheiro {filename} não pode ser processado. Os parâmetros {bad_parameters} são incompatíveis com o nosso catálogo. Consulte a documentação para mais informações.</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="11" />
        <source>Your file has size {memory_requested} bytes, but you have only {available_memory} left. Upgrade your subscription or remove older imagery from your catalog</source>
        <translation>O seu ficheiro tem tamanho {memory_requested} bytes, mas só tem {available_memory} disponíveis. Atualize a sua subscrição ou remova imagens antigas do seu catálogo</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="14" />
        <source>Max file size allowed to upload is {max_file_size} bytes, your file is {actual_file_size} bytes instead. Compress your file or cut it into smaller parts</source>
        <translation>O tamanho máximo de ficheiro permitido para upload é {max_file_size} bytes, o seu ficheiro tem {actual_file_size} bytes. Comprima o seu ficheiro ou divida-o em partes menores</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="17" />
        <source>{instance_type} with id: {uid} can't be found</source>
        <translation>{instance_type} com id: {uid} não foi encontrado</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="18" />
        <source>You do not have access to {instance_type} with id {uid}</source>
        <translation>Não tem acesso a {instance_type} com id {uid}</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="19" />
        <source>File {filename} cannot be uploaded to imagery collection: {mosaic_id}. {param_name} of the file is {got_param}, it should be {expected_param} to fit the collection. Fix your file, or upload it to another imagery collection</source>
        <translation>O ficheiro {filename} não pode ser carregado para a coleção de imagens: {mosaic_id}. {param_name} do ficheiro é {got_param}, deveria ser {expected_param} para se adequar à coleção. Corrija o seu ficheiro, ou faça o upload para outra coleção de imagens</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="23" />
        <source>File can't be uploaded, because its extent is out of coordinate range.Check please CRS and transform of the image, they may be invalid</source>
        <translation>O ficheiro não pode ser carregado porque a sua extensão está fora do intervalo de coordenadas. Verifique o CRS e a transformação da imagem, podem ser inválidos</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="25" />
        <source>File cannot be opened as a GeoTIFF file. Only valid geotiff files are allowed for uploading. You can use Raster-&gt;Conversion-&gt;Translate to change your file type to GeoTIFF</source>
        <translation>O ficheiro não pode ser aberto como um ficheiro GeoTIFF. Apenas ficheiros geotiff válidos são permitidos para upload. Pode usar Raster-&amp;gt;Conversão-&amp;gt;Traduzir para alterar o tipo de ficheiro para GeoTIFF</translation>
    </message>
    <message>
        <location filename="../errors/data_errors.py" line="28" />
        <source>File can't be uploaded, because the geometry of the image is too big, we will not be able to process it properly.Make sure that your image has valid CRS and transform, or cut the image into parts</source>
        <translation>O ficheiro não pode ser carregado porque a geometria da imagem é muito grande, não conseguiremos processá-la adequadamente. Certifique-se de que a sua imagem tem CRS e transformação válidos, ou corte a imagem em partes</translation>
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
        <translation>Nome</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_dialog.ui" line="34" />
        <source>Description</source>
        <translation>Descrição</translation>
    </message>
</context>
<context>
    <name>ErrorDialog</name>
    <message>
        <location filename="../dialogs/static/ui/error_message.ui" line="64" />
        <source>Error</source>
        <translation>Erro</translation>
    </message>
</context>
<context>
    <name>ErrorMessageList</name>
    <message>
        <location filename="../errors/error_message_list.py" line="26" />
        <source>Unknown error. Contact us to resolve the issue! help@geoalert.io</source>
        <translation>Erro desconhecido. Contacte-nos para resolver o problema! help@geoalert.io</translation>
    </message>
</context>
<context>
    <name>ErrorMessageWidget</name>
    <message>
        <location filename="../dialogs/error_message_widget.py" line="22" />
        <source>"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Let us know&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Informe-nos&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
</context>
<context>
    <name>Header</name>
    <message>
        <location filename="../functional/helpers.py" line="158" />
        <source> | Project: </source>
        <translation> | Projeto: </translation>
    </message>
    <message>
        <location filename="../functional/helpers.py" line="161" />
        <source>owner: </source>
        <translation>proprietário: </translation>
    </message>
</context>
<context>
    <name>LoginDialog</name>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="32" />
        <source>Mapflow - Log In</source>
        <translation>Mapflow - Iniciar Sessão</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="53" />
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;span style=" color:#ff0000;"&gt;Authorization is not configured! &lt;/span&gt;&lt;/p&gt;&lt;p&gt;&lt;br/&gt;Setup authorization config &lt;br/&gt;and restart QGIS before login. &lt;br/&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#oauth2_setup"&gt;&lt;span style=" text-decoration: underline; color:#094fd1;"&gt;See documentation for help &lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;span style=" color:#ff0000;"&gt;Autorização não configurada! &lt;/span&gt;&lt;/p&gt;&lt;p&gt;&lt;br/&gt;Configure a autorização &lt;br/&gt;e reinicie o QGIS antes de fazer login. &lt;br/&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#oauth2_setup"&gt;&lt;span style=" text-decoration: underline; color:#094fd1;"&gt;Consulte a documentação para ajuda &lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="68" />
        <source>Token</source>
        <translation>Token</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="75" />
        <source>This plugin is an interface to to the Mapflow.ai satellite image processing platform. You need to register an account to use it. </source>
        <translation>Este plugin é uma interface para a plataforma de processamento de imagens de satélite Mapflow.ai. Precisa de registar uma conta para o usar.</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/login_dialog.ui" line="90" />
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href="https://app.mapflow.ai/account/api"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Get token&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;a href="https://mapflow.ai/terms-of-use-en.pdf"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Terms of use&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;Register at &lt;a href="https://mapflow.ai"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;mapflow.ai&lt;/span&gt;&lt;/a&gt; to use the plugin&lt;/p&gt;&lt;p&gt;&lt;br/&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href="https://app.mapflow.ai/account/api"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Obter token&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;a href="https://mapflow.ai/terms-of-use-en.pdf"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Termos de uso&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;Registe-se em &lt;a href="https://mapflow.ai"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;mapflow.ai&lt;/span&gt;&lt;/a&gt; para usar o plugin&lt;/p&gt;&lt;p&gt;&lt;br/&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
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
        <translation>Iniciar sessão</translation>
    </message>
</context>
<context>
    <name>MainDialog</name>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="106" />
        <source>Name:</source>
        <translation>Nome:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="139" />
        <source>Area:</source>
        <translation>Área:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="146" />
        <source>Create or load vector layer with your area of interest</source>
        <translation>Criar ou carregar camada vetorial com a sua área de interesse</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="249" />
        <source>Data source:</source>
        <translation>Fonte de dados:</translation>
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
        <translation>Preço do processamento por km²</translation>
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
        <translation>Opções do modelo: </translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="587" />
        <source>Start processing</source>
        <translation>Iniciar processamento</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="513" />
        <source>Rate processing:</source>
        <translation>Avaliar processamento:</translation>
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
        <translation>Partilhe as suas opiniões sobre quais aspetos deste processamento de dados funcionam bem ou podem ser melhorados</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="727" />
        <source>Accept</source>
        <translation>Aceitar</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3062" />
        <source>Review</source>
        <translation>Rever</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="398" />
        <source>Please select processing and rating to submit</source>
        <translation>Por favor, selecione processamento e avaliação para enviar</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="764" />
        <source>Submit feedback</source>
        <translation>Enviar feedback</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="811" />
        <source>Your balance:</source>
        <translation>O seu saldo:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="824" />
        <source> Top up balance </source>
        <translation> Recarregar saldo </translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="841" />
        <source>Open billing history</source>
        <translation>Abrir histórico de faturas</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="870" />
        <source>Log out</source>
        <translation>Terminar sessão</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="902" />
        <source>Processing</source>
        <translation>Processamento</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="976" />
        <source>Sort by:</source>
        <translation>Ordenar por:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2965" />
        <source>Name</source>
        <translation>Nome</translation>
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
        <translation>Progresso %</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1213" />
        <source>Area, sq. km</source>
        <translation>Área, km²</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3036" />
        <source>Cost</source>
        <translation>Custo</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3049" />
        <source>Created</source>
        <translation>Criado</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1228" />
        <source>Review until</source>
        <translation>Rever até</translation>
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
        <translation>Filtrar processamentos por nome</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1434" />
        <source>Project:</source>
        <translation>Projeto:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1493" />
        <source>Imagery search</source>
        <translation>Pesquisa de imagens</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1499" />
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Here, you can search imagery for your area and timespan.&lt;/p&gt;&lt;p&gt;Additional filters are also available below.&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Aqui pode pesquisar imagens para a sua área e período de tempo.&lt;/p&gt;&lt;p&gt;Filtros adicionais também estão disponíveis abaixo.&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1502" />
        <source>Provider Imagery Catalog</source>
        <translation>Catálogo de Imagens do Fornecedor</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1513" />
        <source>Earlier images won't be shown</source>
        <translation>Imagens anteriores não serão mostradas</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1516" />
        <source>From:</source>
        <translation>De:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1567" />
        <source>Dates are inclusive</source>
        <translation>As datas são inclusivas</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1584" />
        <source>yyyy-MM-dd</source>
        <translation>aaaa-MM-dd</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1557" />
        <source>More recent images won't be shown</source>
        <translation>Imagens mais recentes não serão mostradas</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1560" />
        <source>To:</source>
        <translation>Até:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1614" />
        <source>Mosaic</source>
        <translation>Mosaico</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1624" />
        <source>Image</source>
        <translation>Imagem</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1693" />
        <source>Click and wait for a few seconds until the table below is filled out</source>
        <translation>Clique e aguarde alguns segundos até que a tabela abaixo seja preenchida</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="342" />
        <source>Search </source>
        <translation>Pesquisar </translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1716" />
        <source>Double-click on a row to preview its image</source>
        <translation>Duplo clique numa linha para pré-visualizar a sua imagem</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1767" />
        <source>1/1</source>
        <translation>1/1</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1850" />
        <source>Clear </source>
        <translation>Limpar </translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1877" />
        <source>Click to specify additional search criteria</source>
        <translation>Clique para especificar critérios de pesquisa adicionais</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1880" />
        <source>Additional filters</source>
        <translation>Filtros adicionais</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1934" />
        <source>%</source>
        <translation>%</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1920" />
        <source>Min intersection:</source>
        <translation>Interseção mínima:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1927" />
        <source>Cloud cover up to:</source>
        <translation>Cobertura de nuvens até:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1956" />
        <source>Images that cover fewer % of your area won't be shown</source>
        <translation>Imagens que cobrem menos % da sua área não serão mostradas</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2008" />
        <source>Providers: </source>
        <translation>Fornecedores: </translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2053" />
        <source>Search only through available providers</source>
        <translation>Pesquisar apenas através de fornecedores disponíveis</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2091" />
        <source>My imagery</source>
        <translation>As minhas imagens</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2116" />
        <source>Add collection</source>
        <translation>Adicionar coleção</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2129" />
        <source>Delete collection</source>
        <translation>Eliminar coleção</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2194" />
        <source>No current selection</source>
        <translation>Nenhuma seleção atual</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2297" />
        <source>Sort by</source>
        <translation>Ordenar por</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2349" />
        <source>Imagery data</source>
        <translation>Dados de imagens</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2615" />
        <source>Settings</source>
        <translation>Definições</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2642" />
        <source>Add or edit imagery providers:</source>
        <translation>Adicionar ou editar fornecedores de imagens:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2687" />
        <source>Add your own web imagery provider</source>
        <translation>Adicionar o seu próprio fornecedor de imagens web</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2801" />
        <source>Use all vector layers as Areas Of Interest</source>
        <translation>Usar todas as camadas vetoriais como Áreas de Interesse</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2811" />
        <source>Confirm processing start</source>
        <translation>Confirmar início do processamento</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2823" />
        <source>view results as a vector tiles</source>
        <translation>ver resultados como vetor tiles</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2836" />
        <source>save results as a local vector file</source>
        <translation>guardar resultados como ficheiro vetorial local</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2885" />
        <source>Configure search table:</source>
        <translation>Configurar tabela de pesquisa:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2892" />
        <source>Configure processings table:</source>
        <translation>Configurar tabela de processamentos:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3010" />
        <source>Progress</source>
        <translation>Progresso</translation>
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
        <translation>Tipo de Produto</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3167" />
        <source>Provider Name</source>
        <translation>Nome do Fornecedor</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3183" />
        <source>Sensor</source>
        <translation>Sensor</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3199" />
        <source>Band Order</source>
        <translation>Ordem das Bandas</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3215" />
        <source>Cloud %</source>
        <translation>Nuvens %</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3231" />
        <source>° Off Nadir</source>
        <translation>° Fora de Nadir</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3247" />
        <source>Date and Time</source>
        <translation>Data e Hora</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3263" />
        <source>Mosaic Zoom</source>
        <translation>Zoom do Mosaico</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3276" />
        <source>Image Spatial Resolution</source>
        <translation>Resolução Espacial da Imagem</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3289" />
        <source>Image ID</source>
        <translation>ID da Imagem</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3302" />
        <source>Preview</source>
        <translation>Pré-visualização</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3334" />
        <source>Set up local working directory, where all the temporary files will be stored</source>
        <translation>Configurar diretório de trabalho local, onde todos os ficheiros temporários serão armazenados</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3352" />
        <source>Output directory:</source>
        <translation>Diretório de saída:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3438" />
        <source>Help</source>
        <translation>Ajuda</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3359" />
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=" margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#user-interface"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;User Interface walkthrough&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#how-to-upload-your-image"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;How to process your own image&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#how-to-use-other-imagery-services"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;How to use a different imagery tileset (XYZ or TMS)&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#how-to-connect-to-maxar-securewatch"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;How to connect to Maxar SecureWatch&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=" margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow credits&lt;/span&gt;&lt;span style=" font-size:large; font-weight:700;"&gt;&lt;br/&gt;&lt;/span&gt;&lt;/h3&gt;&lt;table border="0" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;" align="center" cellspacing="2" cellpadding="0"&gt;&lt;thead&gt;&lt;tr&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:600;"&gt;Pay as you go&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:696;"&gt;$50&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:696;"&gt;$90&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:696;"&gt;$800&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/thead&gt;&lt;tr&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;Credits for processing&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;500&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;1000&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;10000&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/table&gt;&lt;p&gt;See also – &lt;a href="https://docs.mapflow.ai/userguides/prices.html"&gt;&lt;span style=" text-decoration: underline; color:#094fd1;"&gt;How much do the processings and data cost?&lt;/span&gt;&lt;/a&gt;&lt;br/&gt;&lt;/p&gt;&lt;h3 style=" margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Join the project on &lt;a href="https://github.com/Geoalert/mapflow-qgis"&gt;&lt;span style=" font-weight:600; text-decoration: underline; color:#0000ff;"&gt;GitHub&lt;/span&gt;&lt;/a&gt; or &lt;a href="https://github.com/Geoalert/mapflow-qgis/issues"&gt;&lt;span style=" font-weight:600; text-decoration: underline; color:#0000ff;"&gt;report an issue&lt;/span&gt;&lt;/a&gt;&lt;/span&gt;&lt;/h3&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation type="obsolete">&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=" margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#user-interface"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Visita guiada à Interface do Utilizador&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#how-to-upload-your-image"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Como processar a sua própria imagem&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#how-to-use-other-imagery-services"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Como usar um conjunto de tiles de imagens diferente (XYZ ou TMS)&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#how-to-connect-to-maxar-securewatch"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Como conectar ao Maxar SecureWatch&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=" margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Créditos Mapflow&lt;/span&gt;&lt;span style=" font-size:large; font-weight:700;"&gt;&lt;br/&gt;&lt;/span&gt;&lt;/h3&gt;&lt;table border="0" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;" align="center" cellspacing="2" cellpadding="0"&gt;&lt;thead&gt;&lt;tr&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:600;"&gt;Pagar conforme usa&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:696;"&gt;$50&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:696;"&gt;$90&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:696;"&gt;$800&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/thead&gt;&lt;tr&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;Créditos para processamento&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;500&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;1000&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;10000&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/table&gt;&lt;p&gt;Veja também – &lt;a href="https://docs.mapflow.ai/userguides/prices.html"&gt;&lt;span style=" text-decoration: underline; color:#094fd1;"&gt;Quanto custam os processamentos e dados?&lt;/span&gt;&lt;/a&gt;&lt;br/&gt;&lt;/p&gt;&lt;h3 style=" margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Junte-se ao projeto no &lt;a href="https://github.com/Geoalert/mapflow-qgis"&gt;&lt;span style=" font-weight:600; text-decoration: underline; color:#0000ff;"&gt;GitHub&lt;/span&gt;&lt;/a&gt; ou &lt;a href="https://github.com/Geoalert/mapflow-qgis/issues"&gt;&lt;span style=" font-weight:600; text-decoration: underline; color:#0000ff;"&gt;reporte um problema&lt;/span&gt;&lt;/a&gt;&lt;/span&gt;&lt;/h3&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3474" />
        <source>see_details_action</source>
        <translation>ver_detalhes_ação</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="132" />
        <source>Save results</source>
        <translation>Guardar resultados</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="133" />
        <source>Download AOI</source>
        <translation>Descarregar AOI</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="134" />
        <source>See details</source>
        <translation>Ver detalhes</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="141" />
        <source>Rename</source>
        <translation>Renomear</translation>
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
        <translation>Preço: {} créditos por km²</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="370" />
        <source>Rate processing &lt;b&gt;{name}&lt;/b&gt;:</source>
        <translation>Avaliar processamento &lt;b&gt;{name}&lt;/b&gt;:</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="503" />
        <source>Not enough rights to start processing in a shared project ({})</source>
        <translation>Permissões insuficientes para iniciar processamento num projeto partilhado ({})</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="516" />
        <source>Not enough rights to rate processing in a shared project ({})</source>
        <translation>Permissões insuficientes para avaliar processamento num projeto partilhado ({})</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="518" />
        <source>Please select processing</source>
        <translation>Por favor, selecione processamento</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="522" />
        <source>Not enough rights to delete processing in a shared project ({})</source>
        <translation>Permissões insuficientes para eliminar processamento num projeto partilhado ({})</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="555" />
        <source>Delete project</source>
        <translation>Eliminar projeto</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="556" />
        <source>Edit project</source>
        <translation>Editar projeto</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="572" />
        <source>Zoom is derived from found imagery resolution</source>
        <translation>O zoom é derivado da resolução das imagens encontradas</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="587" />
        <source>Previous page</source>
        <translation>Página anterior</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="588" />
        <source>Next page</source>
        <translation>Próxima página</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="589" />
        <source>Page</source>
        <translation>Página</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="749" />
        <source>&lt;b&gt;URL:&lt;/b&gt; {url}&lt;br&gt;&lt;b&gt;Source type:&lt;/b&gt; {type}</source>
        <translation>&lt;b&gt;URL:&lt;/b&gt; {url}&lt;br&gt;&lt;b&gt;Tipo de fonte:&lt;/b&gt; {type}</translation>
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
        <translation>&lt;br&gt;&lt;b&gt;Login raster:&lt;/b&gt; {login}&lt;br&gt;&lt;b&gt;Password raster:&lt;/b&gt; {password}</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="167" />
        <source>Project: &lt;b&gt;{}</source>
        <translation>Projeto: &lt;b&gt;{}</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1665" />
        <source>Some current filters are wider than the last search. Click for details.</source>
        <translation>Alguns filtros atuais são mais amplos do que a última pesquisa. Clique para ver detalhes.</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1668" />
        <source>(!)</source>
        <translation>(!)</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1812" />
        <source>Save the current search filters to this template (replaces its stored search parameters)</source>
        <translation>Guarda os filtros de pesquisa atuais neste modelo (substitui os seus parâmetros de pesquisa guardados)</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1815" />
        <source>Update search</source>
        <translation>Atualizar pesquisa</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="1828" />
        <source>Seen</source>
        <translation>Vista</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2072" />
        <source>Reset the filters to the parameters the current results were fetched with (search request or template)</source>
        <translation>Repõe os filtros para os parâmetros com que os resultados atuais foram obtidos (pedido de pesquisa ou modelo)</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="2075" />
        <source>Reset filters</source>
        <translation>Repor filtros</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/main_dialog.ui" line="3447" />
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;h3 style=" margin-top:30px; margin-bottom:20px; margin-left:30px; margin-right:30px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow&lt;/span&gt;&lt;/h3&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#user-interface"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;User Interface walkthrough&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#how-to-upload-your-image"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;How to process your own image&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p align="center"&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow#how-to-use-other-imagery-services"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;How to use a different imagery tileset (XYZ or TMS)&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;h3 style=" margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Mapflow credits&lt;/span&gt;&lt;span style=" font-size:large; font-weight:700;"&gt;&lt;br/&gt;&lt;/span&gt;&lt;/h3&gt;&lt;table border="0" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;" align="center" cellspacing="2" cellpadding="0"&gt;&lt;thead&gt;&lt;tr&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:600;"&gt;Pay as you go&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:696;"&gt;$50&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:696;"&gt;$90&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p align="center"&gt;&lt;span style=" font-weight:696;"&gt;$800&lt;/span&gt;&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/thead&gt;&lt;tr&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;Credits for processing&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;500&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;1000&lt;/p&gt;&lt;/td&gt;&lt;td style=" padding-left:10; padding-right:10; padding-top:10; padding-bottom:10; border-top:1px; border-right:1px; border-bottom:1px; border-left:1px; border-top-color:#8f8f8f; border-right-color:#8f8f8f; border-bottom-color:#8f8f8f; border-left-color:#8f8f8f; border-top-style:solid; border-right-style:solid; border-bottom-style:solid; border-left-style:solid;"&gt;&lt;p&gt;10000&lt;/p&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/table&gt;&lt;p&gt;See also – &lt;a href="https://docs.mapflow.ai/userguides/prices.html"&gt;&lt;span style=" text-decoration: underline; color:#094fd1;"&gt;How much do the processings and data cost?&lt;/span&gt;&lt;/a&gt;&lt;br/&gt;&lt;/p&gt;&lt;h3 style=" margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"&gt;&lt;span style=" font-size:large; font-weight:600;"&gt;Join the project on &lt;a href="https://github.com/Geoalert/mapflow-qgis"&gt;&lt;span style=" font-weight:600; text-decoration: underline; color:#0000ff;"&gt;GitHub&lt;/span&gt;&lt;/a&gt; or &lt;a href="https://github.com/Geoalert/mapflow-qgis/issues"&gt;&lt;span style=" font-weight:600; text-decoration: underline; color:#0000ff;"&gt;report an issue&lt;/span&gt;&lt;/a&gt;&lt;/span&gt;&lt;/h3&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation type="unfinished" />
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="63" />
        <source>Back</source>
        <translation>Voltar</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="65" />
        <source>Open processings</source>
        <translation>Abrir processamentos</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="67" />
        <source>Open selected template</source>
        <translation>Abrir o modelo selecionado</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="135" />
        <source>See processings</source>
        <translation>Ver processamentos</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="136" />
        <source>See search results</source>
        <translation>Ver resultados da pesquisa</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="142" />
        <source>Pause</source>
        <translation>Pausar</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="143" />
        <source>Resume</source>
        <translation>Retomar</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="145" />
        <source>Rename AOI</source>
        <translation>Renomear AOI</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="146" />
        <source>Delete AOI</source>
        <translation>Eliminar AOI</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="147" />
        <source>Add AOI from layer…</source>
        <translation>Adicionar AOI a partir de uma camada…</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="148" />
        <source>Update selected AOI</source>
        <translation>Atualizar a AOI selecionada</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="149" />
        <source>Draw AOI on the map</source>
        <translation>Desenhar AOI no mapa</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="150" />
        <source>Exclude from search</source>
        <translation>Excluir da pesquisa</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="667" />
        <source>Off-Nadir °:</source>
        <translation>Off-Nadir °:</translation>
    </message>
    <message>
        <location filename="../dialogs/main_dialog.py" line="673" />
        <source>Show only images within this off-nadir angle range</source>
        <translation>Mostrar apenas as imagens dentro deste intervalo de ângulo off-nadir</translation>
    </message>
</context>
<context>
    <name>Mapflow</name>
    <message>
        <location filename="../mapflow.py" line="275" />
        <source>Error during loading the data providers: {e}</source>
        <translation>Erro durante o carregamento dos fornecedores de dados: {e}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="278" />
        <source>We failed to import providers from the settings. Please add them again</source>
        <translation>Falhamos ao importar fornecedores das definições. Por favor, adicione-os novamente</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="284" />
        <source>Draw AOI at the map</source>
        <translation>Desenhar AOI no mapa</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="285" />
        <source>Use imagery extent</source>
        <translation>Usar extensão da imagem</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="287" />
        <source>Create AOI from map extent</source>
        <translation>Criar AOI a partir da extensão do mapa</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1518" />
        <source>Choose imagery collection or image to start processing</source>
        <translation>Escolha coleção de imagens ou imagem para iniciar processamento</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2015" />
        <source>Log in </source>
        <translation>Iniciar sessão </translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2087" />
        <source>This provider is default and cannot be removed</source>
        <translation>Este fornecedor é padrão e não pode ser removido</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2091" />
        <source>Permanently remove {}?</source>
        <translation>Remover permanentemente {}?</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2123" />
        <source>Provider name must be unique. {name} already exists, select another or delete/edit existing</source>
        <translation>O nome do fornecedor deve ser único. {name} já existe, selecione outro ou elimine/edite o existente</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2134" />
        <source>Add new provider</source>
        <translation>Adicionar novo fornecedor</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2142" />
        <source>This is a default provider, it cannot be edited</source>
        <translation>Este é um fornecedor padrão, não pode ser editado</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2197" />
        <source>If you already know which {provider_name} image you want to process,
simply paste its ID here. Otherwise, search suitable images in the catalog below.</source>
        <translation>Se já sabe qual imagem {provider_name} deseja processar,
basta colar o seu ID aqui. Caso contrário, procure imagens adequadas no catálogo abaixo.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="773" />
        <source>e.g. S2B_OPER_MSI_L1C_TL_VGS4_20220209T091044_A025744_T36SXA_N04_00</source>
        <translation type="obsolete">ex: S2B_OPER_MSI_L1C_TL_VGS4_20220209T091044_A025744_T36SXA_N04_00</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2201" />
        <source>e.g. a3b154c40cc74f3b934c0ffc9b34ecd1</source>
        <translation>ex: a3b154c40cc74f3b934c0ffc9b34ecd1</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2233" />
        <source>Select output directory</source>
        <translation>Selecionar diretório de saída</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2256" />
        <source>Please, specify an existing output directory</source>
        <translation>Por favor, especifique um diretório de saída existente</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3007" />
        <source>Please, select a valid area of interest</source>
        <translation>Por favor, selecione uma área de interesse válida</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2831" />
        <source>We couldn't get metadata from the Mapflow Imagery Catalog</source>
        <translation>Não conseguimos obter metadados do Catálogo de Imagens Mapflow</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2834" />
        <source>. Error {error}</source>
        <translation>. Erro {error}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2869" />
        <source>No images match your criteria. Try relaxing the filters.</source>
        <translation>Nenhuma imagem corresponde aos seus critérios. Tente relaxar os filtros.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2885" />
        <source>&lt;b&gt;Results could not be loaded &lt;/b&gt;&lt;br&gt;Please, make sure you chose the right output folder in the Settings tab                                 and you have access rights to this folder</source>
        <translation>&lt;b&gt;Resultados não puderam ser carregados &lt;/b&gt;&lt;br&gt;Por favor, certifique-se de que escolheu a pasta de saída correta no separador Definições e que tem direitos de acesso a esta pasta</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1061" />
        <source>Your area of interest is too large.</source>
        <translation type="obsolete">A sua área de interesse é muito grande.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1164" />
        <source>Please, check your credentials</source>
        <translation type="obsolete">Por favor, verifique as suas credenciais</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1318" />
        <source>We couldn't fetch Sentinel metadata</source>
        <translation type="obsolete">Não conseguimos obter metadados do Sentinel</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1285" />
        <source>More</source>
        <translation type="obsolete">Mais</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1404" />
        <source>Please, check your Maxar credentials</source>
        <translation type="obsolete">Por favor, verifique as suas credenciais Maxar</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1406" />
        <source>We couldn't get metadata from Maxar, error {error}</source>
        <translation type="obsolete">Não conseguimos obter metadados da Maxar, erro {error}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1522" />
        <source>A Sentinel image ID should look like S2B_OPER_MSI_L1C_TL_VGS4_20220209T091044_A025744_T36SXA_N04_00 or /36/S/XA/2022/02/09/0/</source>
        <translation type="obsolete">Um ID de imagem Sentinel deve parecer-se com S2B_OPER_MSI_L1C_TL_VGS4_20220209T091044_A025744_T36SXA_N04_00 ou /36/S/XA/2022/02/09/0/</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1530" />
        <source>A Maxar image ID should look like a3b154c40cc74f3b934c0ffc9b34ecd1</source>
        <translation type="obsolete">Um ID de imagem Maxar deve parecer-se com a3b154c40cc74f3b934c0ffc9b34ecd1</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1577" />
        <source>Not enough rights to start processing in a shared project ({})</source>
        <translation type="obsolete">Permissões insuficientes para iniciar processamento num projeto partilhado ({})</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1554" />
        <source>Set AOI to start processing</source>
        <translation type="obsolete">Definir AOI para iniciar processamento</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1579" />
        <source>AOI must contain not more than {} polygons</source>
        <translation type="obsolete">A AOI não deve conter mais do que {} polígonos</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1621" />
        <source>Use extent of '{name}'</source>
        <translation type="obsolete">Usar extensão de '{name}'</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1623" />
        <source>Select AOI to start processing</source>
        <translation type="obsolete">Selecionar AOI para iniciar processamento</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1858" />
        <source>Selected AOI does not intersect the selected imagery</source>
        <translation type="obsolete">A AOI selecionada não intersecta a imagem selecionada</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1699" />
        <source>Area: {:.2f} sq.km</source>
        <translation type="obsolete">Área: {:.2f} km²</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1860" />
        <source>This provider requires image ID. Use search tab to find imagery for you requirements, and select image in the table.</source>
        <translation type="obsolete">Este fornecedor requer ID da imagem. Use o separador de pesquisa para encontrar imagens conforme os seus requisitos e selecione a imagem na tabela.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3002" />
        <source>Please, specify a name for your processing</source>
        <translation>Por favor, especifique um nome para o seu processamento</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3005" />
        <source>Processing area layer is corrupted or has invalid projection</source>
        <translation>A camada da área de processamento está corrompida ou tem projeção inválida</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3009" />
        <source>Up to {} sq km can be processed at a time. Try splitting your area(s) into several processings.</source>
        <translation>Até {} km² podem ser processados de cada vez. Tente dividir a(s) sua(s) área(s) em vários processamentos.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3025" />
        <source>Providers are not initialized</source>
        <translation>Fornecedores não estão inicializados</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1755" />
        <source>Bad AOI. AOI must be inside boundaries: 
[-180, 180] by longitude, [-90, 90] by latitude</source>
        <translation type="obsolete">AOI inválida. A AOI deve estar dentro dos limites: 
[-180, 180] por longitude, [-90, 90] por latitude</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1865" />
        <source>No project is selected</source>
        <translation type="obsolete">Nenhum projeto está selecionado</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1894" />
        <source>Processing limit exceeded. Visit "&lt;a href="https://app.mapflow.ai/account/balance"&gt;Mapflow&lt;/a&gt;" to top up your balance</source>
        <translation type="obsolete">Limite de processamento excedido. Visite "&lt;a href="https://app.mapflow.ai/account/balance"&gt;Mapflow&lt;/a&gt;" para recarregar o seu saldo</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1901" />
        <source>Starting the processing...</source>
        <translation type="obsolete">A iniciar o processamento...</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1906" />
        <source>Could not launch processing! Error: {}.</source>
        <translation type="obsolete">Não foi possível lançar o processamento! Erro: {}.</translation>
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
        <location filename="../mapflow.py" line="1992" />
        <source>The selected data provider is unavailable on your plan. 
 Upgrade your subscription to get access to the data. 
See pricing at &lt;a href="https://mapflow.ai/pricing"&gt;mapflow.ai&lt;/a&gt;</source>
        <translation type="obsolete">O fornecedor de dados selecionado não está disponível no seu plano.
Atualize a sua subscrição para ter acesso aos dados.
Veja os preços em &lt;a href="https://mapflow.ai/pricing"&gt;mapflow.ai&lt;/a&gt;</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2003" />
        <source>Processing creation failed</source>
        <translation type="obsolete">Criação do processamento falhou</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3058" />
        <source>Your balance: {} credits</source>
        <translation>O seu saldo: {} créditos</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3060" />
        <source>Remaining limit: {:.2f} sq.km</source>
        <translation>Limite restante: {:.2f} km²</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3129" />
        <source>Show all</source>
        <translation>Mostrar todos</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1694" />
        <source>Sorry, we couldn't load the image</source>
        <translation type="obsolete">Desculpe, não conseguimos carregar a imagem</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1695" />
        <source>Error previewing Sentinel imagery</source>
        <translation type="obsolete">Erro ao pré-visualizar imagens Sentinel</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3145" />
        <source>Preview is unavailable when metadata layer is removed</source>
        <translation>A pré-visualização não está disponível quando a camada de metadados é removida</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3197" />
        <source>Selected imagery has no preview</source>
        <translation>A imagem selecionada não tem pré-visualização</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3202" />
        <source>Preview with such URL is unavailable</source>
        <translation>Pré-visualização com tal URL não está disponível</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3210" />
        <source>Preview for '{iid}' is unavailable</source>
        <translation>Pré-visualização para '{iid}' não está disponível</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3321" />
        <source>Could not display preview</source>
        <translation>Não foi possível mostrar a pré-visualização</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1880" />
        <source>Sorry, there's no preview for this image</source>
        <translation type="obsolete">Desculpe, não há pré-visualização para esta imagem</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3417" />
        <source>We couldn't load a preview for this image</source>
        <translation>Não conseguimos carregar uma pré-visualização para esta imagem</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1895" />
        <source>Please, select an image to preview</source>
        <translation type="obsolete">Por favor, selecione uma imagem para pré-visualizar</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3394" />
        <source>Provider {name} requires image id for preview!</source>
        <translation>O fornecedor {name} requer id da imagem para pré-visualização!</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3398" />
        <source>Preview is unavailable for the provider {}. 
OSM layer will be added instead.</source>
        <translation>Pré-visualização não está disponível para o fornecedor {}.
Camada OSM será adicionada em vez disso.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3429" />
        <source>This provider requires image ID!</source>
        <translation>Este fornecedor requer ID da imagem!</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3680" />
        <source>Only finished processings can be rated</source>
        <translation>Apenas processamentos terminados podem ser avaliados</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3683" />
        <source>Processing must be in `Review required` status</source>
        <translation>O processamento deve estar no estado `Revisão necessária`</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3699" />
        <source>Thank you! Your rating is submitted!
We would appreciate if you add feedback as well.</source>
        <translation>Obrigado! A sua avaliação foi enviada!
Agradeceríamos se também adicionasse feedback.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3706" />
        <source>Thank you! Your rating and feedback are submitted!</source>
        <translation>Obrigado! A sua avaliação e feedback foram enviados!</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2570" />
        <source>Only correctly finished processings (status OK) can be reviewed</source>
        <translation type="obsolete">Apenas processamentos corretamente terminados (estado OK) podem ser revistos</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3721" />
        <source>Not enough rights to rate processing in a shared project ({})</source>
        <translation>Permissões insuficientes para avaliar processamento num projeto partilhado ({})</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3724" />
        <source>Please select processing</source>
        <translation>Por favor, selecione processamento</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3726" />
        <source>Only correctly finished processings (status OK) can be rated</source>
        <translation>Apenas processamentos corretamente terminados (estado OK) podem ser avaliados</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3728" />
        <source>Please select rating to submit</source>
        <translation>Por favor, selecione avaliação para enviar</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3944" />
        <source>Only the results of correctly finished processing can be loaded</source>
        <translation>Apenas os resultados de processamento corretamente terminado podem ser carregados</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2221" />
        <source>Directory '{}' does not exist</source>
        <translation type="obsolete">Diretório '{}' não existe</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2221" />
        <source>&lt;br&gt;Using Settings tab, change the output directory to an existing one to download the results</source>
        <translation type="obsolete">&lt;br&gt;Usando o separador Definições, altere o diretório de saída para um existente para descarregar os resultados</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4016" />
        <source>We have just set the authentication config for you. 
 You may need to restart QGIS to apply it so you could log in</source>
        <translation>Acabámos de configurar a autenticação para si.
Pode precisar de reiniciar o QGIS para aplicá-la e poder fazer login</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4041" />
        <source>Please restart QGIS before using OAuth2 login.</source>
        <translation>Por favor, reinicie o QGIS antes de usar o login OAuth2.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4103" />
        <source>Wrong token. Visit "&lt;a href="https://app.mapflow.ai/account/api"&gt;mapflow.ai&lt;/a&gt;" to get a new one</source>
        <translation>Token incorreto. Visite "&lt;a href="https://app.mapflow.ai/account/api"&gt;mapflow.ai&lt;/a&gt;" para obter um novo</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4135" />
        <source>Proxy error. Please, check your proxy settings.</source>
        <translation>Erro de proxy. Por favor, verifique as suas definições de proxy.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4139" />
        <source>Not enough rights for this action
in a shared project '{project_name}' ({user_role})</source>
        <translation>Permissões insuficientes para esta ação
num projeto partilhado '{project_name}' ({user_role})</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4145" />
        <source>This operation is forbidden for your account, contact us</source>
        <translation>Esta operação é proibida para a sua conta, contacte-nos</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4150" />
        <source>Error</source>
        <translation>Erro</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4256" />
        <source>You must upgrade your plugin version to continue work with Mapflow. 
The server requires version {server_version}, your plugin is {local_version}
Go to Plugins -&gt; Manage and Install Plugins -&gt; Upgradable</source>
        <translation>Deve atualizar a versão do seu plugin para continuar a trabalhar com o Mapflow.
O servidor requer versão {server_version}, o seu plugin é {local_version}
Vá a Plugins -&amp;gt; Gerir e Instalar Plugins -&amp;gt; Atualizáveis</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="4266" />
        <source>A new version of Mapflow plugin {server_version} is released 
We recommend you to upgrade to get all the latest features
Go to Plugins -&gt; Manage and Install Plugins -&gt; Upgradable</source>
        <translation>Uma nova versão do plugin Mapflow {server_version} foi lançada
Recomendamos que atualize para obter todas as funcionalidades mais recentes
Vá a Plugins -&amp;gt; Gerir e Instalar Plugins -&amp;gt; Atualizáveis</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3043" />
        <source>You can launch multiple image processing only if they have the same provider</source>
        <translation type="obsolete">Pode lançar múltiplos processamentos de imagem apenas se tiverem o mesmo fornecedor</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3072" />
        <source>Selected search results must have the same zoom level</source>
        <translation type="obsolete">Os resultados de pesquisa selecionados devem ter o mesmo nível de zoom</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3715" />
        <source>Only correctly finished processings with 'Review required' status can be reviewed</source>
        <translation>Apenas processamentos concluídos corretamente com status 'Revisão necessária' podem ser revisados</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="220" />
        <source>The working directory '{dir}' is unavailable:&lt;br&gt;{error}&lt;br&gt;&lt;br&gt;It is needed to save processing results on your computer.</source>
        <translation>O diretório de trabalho '{dir}' não está disponível:&lt;br&gt;{error}&lt;br&gt;&lt;br&gt;É necessário para guardar os resultados do processamento no seu computador.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="582" />
        <source>Restart</source>
        <translation>Reiniciar</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="622" />
        <source>Start planned processing</source>
        <translation>Iniciar processamento planeado</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="624" />
        <source>Start processing</source>
        <translation>Iniciar processamento</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="636" />
        <source>Select one or more images in search results to start planned processing</source>
        <translation>Selecione uma ou mais imagens nos resultados da pesquisa para iniciar o processamento planeado</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="667" />
        <source>No images was found</source>
        <translation>Não foram encontradas imagens</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="817" />
        <source>AOI: {name}</source>
        <translation>AOI: {name}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="839" />
        <source>No AOI</source>
        <translation>Sem AOI</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1091" />
        <source>There are no polygon layers to add as AOIs. Draw one on the map or load a vector layer first.</source>
        <translation>Não há camadas poligonais para adicionar como AOI. Desenhe uma no mapa ou carregue primeiro uma camada vetorial.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1111" />
        <source>The selected layer(s) have no polygon features to add.</source>
        <translation>A(s) camada(s) selecionada(s) não têm feições poligonais para adicionar.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1175" />
        <source>This AOI has no id yet and cannot be updated. Reopen the template and try again.</source>
        <translation>Esta AOI ainda não tem id e não pode ser atualizada. Reabra o modelo e tente novamente.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1180" />
        <source>Could not find this AOI's layer on the map. Reopen the template and try again.</source>
        <translation>Não foi possível encontrar a camada desta AOI no mapa. Reabra o modelo e tente novamente.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1183" />
        <source>Editing AOI '{name}': move its vertices on the map, then Save AOI.</source>
        <translation>A editar a AOI '{name}': mova os seus vértices no mapa e depois Guardar AOI.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1194" />
        <source>New AOI</source>
        <translation>Nova AOI</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1197" />
        <source>Draw the AOI polygon on the map, then Save AOI.</source>
        <translation>Desenhe o polígono da AOI no mapa e depois Guardar AOI.</translation>
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
        <translation>A AOI não tem geometria — desenhe ou mantenha pelo menos um polígono.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1312" />
        <source>The edited AOI has no valid geometry.</source>
        <translation>A AOI editada não tem uma geometria válida.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1334" />
        <source>Draw at least one polygon before saving.</source>
        <translation>Desenhe pelo menos um polígono antes de guardar.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1336" />
        <source>Name the AOI</source>
        <translation>Nomear a AOI</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1336" />
        <source>AOI name:</source>
        <translation>Nome da AOI:</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1342" />
        <source>AOI name must not exceed {limit} characters.</source>
        <translation>O nome da AOI não deve exceder {limit} caracteres.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1411" />
        <source>Selected AOIs</source>
        <translation>AOI selecionadas</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1869" />
        <source>Start date {cur} is earlier than searched ({base})</source>
        <translation>A data inicial {cur} é anterior à pesquisada ({base})</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1872" />
        <source>End date {cur} is later than searched ({base})</source>
        <translation>A data final {cur} é posterior à pesquisada ({base})</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1877" />
        <source>Max cloud cover {cur}% is higher than searched ({base}%)</source>
        <translation>A cobertura de nuvens máxima {cur}% é superior à pesquisada ({base}%)</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1882" />
        <source>Min intersection {cur}% is lower than searched ({base}%)</source>
        <translation>A interseção mínima {cur}% é inferior à pesquisada ({base}%)</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1889" />
        <source>Off-nadir range {lo}-{hi}° is wider than searched ({blo}-{bhi}°)</source>
        <translation>O intervalo de off-nadir {lo}-{hi}° é mais amplo do que o pesquisado ({blo}-{bhi}°)</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1896" />
        <source>Product type(s) not searched: {extra}</source>
        <translation>Tipo(s) de produto não pesquisados: {extra}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1902" />
        <source>Showing all providers, but search was limited to: {base}</source>
        <translation>A mostrar todos os fornecedores, mas a pesquisa foi limitada a: {base}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1907" />
        <source>Provider(s) not searched: {extra}</source>
        <translation>Fornecedor(es) não pesquisados: {extra}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="1913" />
        <source>These filters are wider than the last search, so they will not bring more images. Run a new Search to fetch them:</source>
        <translation>Estes filtros são mais amplos do que a última pesquisa, por isso não trarão mais imagens. Execute uma nova pesquisa para as obter:</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2244" />
        <source>Cannot use '{dir}' as the working directory:
{error}

Please choose another directory.</source>
        <translation>Não é possível usar '{dir}' como diretório de trabalho:
{error}

Escolha outro diretório.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2268" />
        <source>Select directory…</source>
        <translation>Selecionar diretório…</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2269" />
        <source>Later</source>
        <translation>Mais tarde</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2336" />
        <source>Search</source>
        <translation>Pesquisar</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2336" />
        <source>Plan search</source>
        <translation>Planear pesquisa</translation>
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
        <translation>Selecione um projeto para criar um modelo</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2371" />
        <source>Searching {datetime}</source>
        <translation>A pesquisar {datetime}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2378" />
        <source>The search area is too large for immediate processing. The Planned Search will be created and run in the background. You will be notified when results are available.</source>
        <translation>A área de pesquisa é demasiado grande para processamento imediato. Será criada uma Pesquisa planeada que será executada em segundo plano. Será notificado quando os resultados estiverem disponíveis.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2387" />
        <source>Plan Search</source>
        <translation>Planear pesquisa</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2437" />
        <source>AOI name '{name}' exceeds {limit} characters</source>
        <translation>O nome da AOI '{name}' excede {limit} caracteres</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2507" />
        <source>Please, specify a name for your search</source>
        <translation>Especifique um nome para a sua pesquisa</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2523" />
        <source>Creating planned search...</source>
        <translation>A criar pesquisa planeada...</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2532" />
        <source>Planned search created successfully.</source>
        <translation>Pesquisa planeada criada com sucesso.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2537" />
        <source>Template creation failed</source>
        <translation>Falha ao criar o modelo</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2577" />
        <source>Updating template search parameters...</source>
        <translation>A atualizar os parâmetros de pesquisa do modelo...</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2587" />
        <source>Template updated.</source>
        <translation>Modelo atualizado.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2593" />
        <source>Template update failed</source>
        <translation>Falha ao atualizar o modelo</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2637" />
        <source>This processing is not linked to any AOI geometry.</source>
        <translation>Este processamento não está associado a nenhuma geometria de AOI.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="2640" />
        <source>Exclude this processing's area from the template's search? The already-processed area will be removed from the AOI(s).</source>
        <translation>Excluir a área deste processamento da pesquisa do modelo? A área já processada será removida das AOI.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3515" />
        <source>Could not mark image(s) as seen, please try again.</source>
        <translation>Não foi possível marcar a(s) imagem(ns) como vista(s), tente novamente.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3580" />
        <source>Planned processing</source>
        <translation>Processamento planeado</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3582" />
        <source>Planned processing. New images: {count}</source>
        <translation>Processamento planeado. Novas imagens: {count}</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3929" />
        <source>A working directory is required to save the processing results on your computer.</source>
        <translation>É necessário um diretório de trabalho para guardar os resultados do processamento no seu computador.</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="3955" />
        <source>A working directory is required to save the area of interest on your computer.</source>
        <translation>É necessário um diretório de trabalho para guardar a área de interesse no seu computador.</translation>
    </message>
<message><source>The template has been created, but is inactive.

You have reached the maximum number of active planned processings. Pause or delete another one before activating this template.</source><translation>O modelo foi criado, mas está inativo.

Atingiu o número máximo de processamentos planeados ativos. Pause ou elimine outro antes de ativar este modelo.</translation></message></context>
<context>
    <name>MapflowLoginDialog</name>
    <message>
        <location filename="../dialogs/login_dialog.py" line="32" />
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;You will be redirecrted to web browser &lt;br/&gt;to enter your Mapflow login and password&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Será redirecionado para o navegador web &lt;br/&gt;para inserir o seu login e password do Mapflow&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/login_dialog.py" line="33" />
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;span style=" color:#ff0000;"&gt;Authorization is not completed! &lt;/span&gt;&lt;/p&gt;&lt;p&gt;&lt;br/&gt;1. Complete authorization in browser. &lt;br/&gt;&lt;br/&gt;2. If it does not help, restart QGIS. &lt;br/&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#oauth2_setup"&gt;&lt;span style=" text-decoration: underline; color:#094fd1;"&gt;See documentation for help &lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;span style=" color:#ff0000;"&gt;Autorização não concluída! &lt;/span&gt;&lt;/p&gt;&lt;p&gt;&lt;br/&gt;1. Complete a autorização no navegador. &lt;br/&gt;&lt;br/&gt;2. Se não ajudar, reinicie o QGIS. &lt;br/&gt;&lt;a href="https://docs.mapflow.ai/api/qgis_mapflow.html#oauth2_setup"&gt;&lt;span style=" text-decoration: underline; color:#094fd1;"&gt;Consulte a documentação para ajuda &lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/login_dialog.py" line="38" />
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href="https://app.mapflow.ai/account/api"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Get token&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;a href="https://mapflow.ai/terms-of-use-en.pdf"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Terms of use&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;Register at &lt;a href="https://mapflow.ai"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;mapflow.ai&lt;/span&gt;&lt;/a&gt; to use the plugin&lt;/p&gt;&lt;p&gt;&lt;br/&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;&lt;a href="https://app.mapflow.ai/account/api"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Obter token&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;&lt;a href="https://mapflow.ai/terms-of-use-en.pdf"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;Termos de uso&lt;/span&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;Registe-se em &lt;a href="https://mapflow.ai"&gt;&lt;span style=" text-decoration: underline; color:#0057ae;"&gt;mapflow.ai&lt;/span&gt;&lt;/a&gt; para usar o plugin&lt;/p&gt;&lt;p&gt;&lt;br/&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../dialogs/login_dialog.py" line="39" />
        <source>Invalid credentials</source>
        <translation>Credenciais inválidas</translation>
    </message>
</context>
<context>
    <name>MosaicDialog</name>
    <message>
        <location filename="../dialogs/mosaic_dialog.py" line="19" />
        <source>Imagery collection name must not be empty!</source>
        <translation>O nome da coleção de imagens não pode estar vazio!</translation>
    </message>
</context>
<context>
    <name>ProcessingDetailsDialog</name>
    <message>
        <location filename="../dialogs/processing_details_dialog.py" line="15" />
        <source>Processing details</source>
        <translation>Detalhes do processamento</translation>
    </message>
    <message>
        <location filename="../dialogs/processing_details_dialog.py" line="47" />
        <source>My imagery</source>
        <translation>As minhas imagens</translation>
    </message>
</context>
<context>
    <name>ProcessingErrors</name>
    <message>
        <location filename="../errors/processing_errors.py" line="8" />
        <source>Folder `{s3_link}` selected for processing does not contain any images. </source>
        <translation>A pasta `{s3_link}` selecionada para processamento não contém nenhuma imagem.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="10" />
        <source>Task for source-validation must contain area of interest (`geometry` section)</source>
        <translation>A tarefa para validação de fonte deve conter área de interesse (secção `geometry`)</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="12" />
        <source>We could not open and read the image you have uploaded</source>
        <translation>Não conseguimos abrir e ler a imagem que carregou</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="13" />
        <source>Image profile (metadata) must have keys {required_keys}, got profile {profile}</source>
        <translation>O perfil da imagem (metadados) deve ter as chaves {required_keys}, obteve perfil {profile}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="15" />
        <source>AOI does not intersect the selected Sentinel-2 granule {actual_cell}</source>
        <translation>A AOI não intersecta o grânulo Sentinel-2 selecionado {actual_cell}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="17" />
        <source>Key 'url' in your request must be a string, got {url_type} instead.</source>
        <translation>A chave 'url' no seu pedido deve ser uma string, obteve {url_type} em vez disso.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="19" />
        <source>The specified basemap {url} is forbidden for processing because it contains a map, not satellite image. Our models are suited for satellite imagery.</source>
        <translation>O mapa base especificado {url} é proibido para processamento porque contém um mapa, não imagem de satélite. Os nossos modelos são adequados para imagens de satélite.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="22" />
        <source>Your URL must be a link starting with "http://" or "https://".</source>
        <translation>O seu URL deve ser uma ligação começando com "http://" ou "https://".</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="24" />
        <source>Format of 'url' is invalid and cannot be parsed. Error: {parse_error_message}</source>
        <translation>O formato de 'url' é inválido e não pode ser analisado. Erro: {parse_error_message}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="26" />
        <source>Zoom must be either empty, or integer, got {actual_zoom}</source>
        <translation>O zoom deve estar vazio ou ser inteiro, obteve {actual_zoom}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="28" />
        <source>Zoom must be between 0 and 22, got {actual_zoom}</source>
        <translation>O zoom deve estar entre 0 e 22, obteve {actual_zoom}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="29" />
        <source>Zoom must be not lower than {min_zoom}, got {actual_zoom}</source>
        <translation>O zoom não deve ser inferior a {min_zoom}, obteve {actual_zoom}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="30" />
        <source>Image metadata must be a dict (json)</source>
        <translation>Os metadados da imagem devem ser um dict (json)</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="31" />
        <source>Image metadata must have keys: crs, transform, dtype, count</source>
        <translation>Os metadados da imagem devem ter as chaves: crs, transform, dtype, count</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="33" />
        <source>URL of the image at s3 storage must be a string starting with s3://, got {actual_s3_link}</source>
        <translation>O URL da imagem no armazenamento s3 deve ser uma string começando com s3://, obteve {actual_s3_link}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="35" />
        <source>Request must contain either 'profile' or 'url' keys</source>
        <translation>O pedido deve conter as chaves 'profile' ou 'url'</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="36" />
        <source>Failed to read file from {s3_link}.</source>
        <translation>Falha ao ler ficheiro de {s3_link}.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="37" />
        <source>Image data type (Dtype) must be one of {required_dtypes}, got {request_dtype}</source>
        <translation>O tipo de dados da imagem (Dtype) deve ser um de {required_dtypes}, obteve {request_dtype}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="39" />
        <source>Number of channels in image must be one of {required_nchannels}. Got {real_nchannels}</source>
        <translation>O número de canais na imagem deve ser um de {required_nchannels}. Obteve {real_nchannels}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="41" />
        <source>Spatial resolution of you image is too high: pixel size is {actual_res}, minimum allowed pixel size is {min_res}</source>
        <translation>A resolução espacial da sua imagem é muito alta: o tamanho do pixel é {actual_res}, o tamanho mínimo permitido do pixel é {min_res}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="44" />
        <source>Spatial resolution of you image is too low: pixel size is {actual_res}, maximum allowed pixel size is {max_res}</source>
        <translation>A resolução espacial da sua imagem é muito baixa: o tamanho do pixel é {actual_res}, o tamanho máximo permitido do pixel é {max_res}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="47" />
        <source>Error occurred during image {checked_param} check: {message}. Image metadata = {metadata}.</source>
        <translation>Ocorreu um erro durante a verificação do {checked_param} da imagem: {message}. Metadados da imagem = {metadata}.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="49" />
        <source>Your 'url' doesn't match the format, Quadkey basemap must be a link containing "q" placeholder.</source>
        <translation>O seu 'url' não corresponde ao formato, o mapa base Quadkey deve ser uma ligação contendo o marcador "q".</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="52" />
        <source>Input string {input_string} is of unknown format. It must represent Sentinel-2 granule ID.</source>
        <translation>A string de entrada {input_string} tem formato desconhecido. Deve representar o ID do grânulo Sentinel-2.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="54" />
        <source>Selected Sentinel-2 image cell is {actual_cell}, this model is for the cells: {allowed_cells}</source>
        <translation>A célula da imagem Sentinel-2 selecionada é {actual_cell}, este modelo é para as células: {allowed_cells}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="56" />
        <source>Selected Sentinel-2 image month is {actual_month}, this model is for: {allowed_months}</source>
        <translation>O mês da imagem Sentinel-2 selecionada é {actual_month}, este modelo é para: {allowed_months}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="58" />
        <source>You request TMS basemap link doesn't match the format, it must be a link containing "x", "y", "z" placeholders, correct it and start processing again.</source>
        <translation>A sua ligação de mapa base TMS não corresponde ao formato, deve ser uma ligação contendo os marcadores "x", "y", "z", corrija e inicie o processamento novamente.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="61" />
        <source>Requirements must be dict, got {requirements_type}.</source>
        <translation>Os requisitos devem ser dict, obteve {requirements_type}.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="62" />
        <source>Request must be dict, got {request_type}.</source>
        <translation>O pedido deve ser dict, obteve {request_type}.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="63" />
        <source>Request must contain "source_type" key</source>
        <translation>O pedido deve conter a chave "source_type"</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="64" />
        <source>Source type {source_type} is not allowed. Use one of: {allowed_sources}</source>
        <translation>O tipo de fonte {source_type} não é permitido. Use um de: {allowed_sources}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="66" />
        <source>"Required" section of the requirements must contain dict, not {required_section_type}</source>
        <translation>A secção "Required" dos requisitos deve conter dict, não {required_section_type}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="68" />
        <source>"Recommended" section of the requirements must contain dict, not {recommended_section_type}</source>
        <translation>A secção "Recommended" dos requisitos deve conter dict, não {recommended_section_type}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="70" />
        <source>You XYZ basemap link doesn't match the format, it must be a link containing "x", "y", "z"  placeholders.</source>
        <translation>A sua ligação de mapa base XYZ não corresponde ao formato, deve ser uma ligação contendo os marcadores "x", "y", "z".</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="75" />
        <source>Internal error in process of data source validation. We are working on the fix, our support will contact you.</source>
        <translation>Erro interno no processo de validação da fonte de dados. Estamos a trabalhar na correção, o nosso suporte entrará em contacto consigo.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="96" />
        <source>Internal error in process of loading data. We are working on the fix, our support will contact you.</source>
        <translation>Erro interno no processo de carregamento de dados. Estamos a trabalhar na correção, o nosso suporte entrará em contacto consigo.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="79" />
        <source>Wrong source type {real_source_type}. Specify one of the allowed types {allowed_source_types}.</source>
        <translation>Tipo de fonte errado {real_source_type}. Especifique um dos tipos permitidos {allowed_source_types}.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="81" />
        <source>Your data loading task requires {estimated_size} MB of memory, which exceeded allowed memory limit {allowed_size}</source>
        <translation>A sua tarefa de carregamento de dados requer {estimated_size} MB de memória, o que excedeu o limite de memória permitido {allowed_size}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="83" />
        <source>Dataloader argument {argument_name} has type {argument_type}, excpected to be {expected_type}</source>
        <translation>O argumento Dataloader {argument_name} tem tipo {argument_type}, esperado ser {expected_type}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="85" />
        <source>Loaded tile has {real_nchannels} channels, required number is {expected_nchannels}</source>
        <translation>O tile carregado tem {real_nchannels} canais, o número requerido é {expected_nchannels}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="87" />
        <source>Loaded tile has size {real_size}, expected tile size is {expected_size}</source>
        <translation>O tile carregado tem tamanho {real_size}, o tamanho esperado do tile é {expected_size}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="89" />
        <source>Tile at location {tile_location} cannot be loaded, server response is {status}</source>
        <translation>O tile na localização {tile_location} não pode ser carregado, a resposta do servidor é {status}</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="91" />
        <source>Response content at {tile_location} cannot be decoded as an image</source>
        <translation>O conteúdo da resposta em {tile_location} não pode ser decodificado como uma imagem</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="98" />
        <source>The data provider contains no data for your area of interest (returned NoData tiles). Try other the data sources to get the results.</source>
        <translation>O fornecedor de dados não contém dados para a sua área de interesse (retornou tiles NoData). Tente outras fontes de dados para obter os resultados.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="100" />
        <source>Internal error in process of data preparation. We are working on the fix, our support will contact you.</source>
        <translation>Erro interno no processo de preparação de dados. Estamos a trabalhar na correção, o nosso suporte entrará em contacto consigo.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="102" />
        <source>Internal error in process of data processing. We are working on the fix, our support will contact you.</source>
        <translation>Erro interno no processo de processamento de dados. Estamos a trabalhar na correção, o nosso suporte entrará em contacto consigo.</translation>
    </message>
    <message>
        <location filename="../errors/processing_errors.py" line="104" />
        <source>Internal error in process of saving the results. We are working on the fix, our support will contact you.</source>
        <translation>Erro interno no processo de guardar os resultados. Estamos a trabalhar na correção, o nosso suporte entrará em contacto consigo.</translation>
    </message>
</context>
<context>
    <name>ProcessingService</name>
    <message>
        <location filename="../functional/service/processing_service.py" line="137" />
        <source>Specify processing parameters</source>
        <translation>Especifique os parâmetros do processamento</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="142" />
        <source>Please, specify a name for your processing</source>
        <translation>Por favor, especifique um nome para o seu processamento</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="147" />
        <source>Processing area layer is corrupted or has invalid projection</source>
        <translation>A camada da área de processamento está corrompida ou tem projeção inválida</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="149" />
        <source>Please, select a valid area of interest</source>
        <translation>Por favor, selecione uma área de interesse válida</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="102" />
        <source>Up to {} sq km can be processed at a time. Try splitting your area(s) into several processings.</source>
        <translation type="obsolete">Até {} km² podem ser processados de cada vez. Tente dividir a(s) sua(s) área(s) em vários processamentos.</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="189" />
        <source>Selected AOI does not intersect the selected imagery</source>
        <translation>A AOI selecionada não intersecta a imagem selecionada</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="191" />
        <source>This provider requires image ID. Use search tab to find imagery for you requirements, and select image in the table.</source>
        <translation>Este fornecedor requer ID da imagem. Use o separador de pesquisa para encontrar imagens conforme os seus requisitos e selecione a imagem na tabela.</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1112" />
        <source>Not enough rights to start processing in a shared project ({})</source>
        <translation>Permissões insuficientes para iniciar processamento num projeto partilhado ({})</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="248" />
        <source>Set AOI to start processing</source>
        <translation>Definir AOI para iniciar processamento</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="250" />
        <source>Error! Models are not initialized.
Please, make sure you have selected a project</source>
        <translation>Erro! Modelos não estão inicializados.
Por favor, certifique-se de que selecionou um projeto</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="322" />
        <source>Processing limit exceeded. Visit "&lt;a href="https://app.mapflow.ai/account/balance"&gt;Mapflow&lt;/a&gt;" to top up your balance</source>
        <translation>Limite de processamento excedido. Visite "&lt;a href="https://app.mapflow.ai/account/balance"&gt;Mapflow&lt;/a&gt;" para recarregar o seu saldo</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="351" />
        <source>Starting the processing...</source>
        <translation>A iniciar o processamento...</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="361" />
        <source>Could not launch processing! Error: {}.</source>
        <translation>Não foi possível lançar o processamento! Erro: {}.</translation>
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
        <translation>Sucesso! Vamos notificá-lo quando o processamento terminar.</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="260" />
        <source>Failed to start processing</source>
        <translation type="obsolete">Falha ao iniciar o processamento</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="947" />
        <source>Processing completed</source>
        <translation>Processamento concluído</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="947" />
        <source>Processing '{name}' has finished successfully</source>
        <translation>O processamento '{name}' foi concluído com sucesso</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="957" />
        <source>Processing failed</source>
        <translation>Processamento falhou</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="957" />
        <source>Processing '{name}' has failed</source>
        <translation>O processamento '{name}' falhou</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1114" />
        <source>Processing cost is not available:
{message}</source>
        <translation>Custo do processamento não está disponível:
{message}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="496" />
        <source>Delete selected processings?</source>
        <translation type="obsolete">Eliminar processamentos selecionados?</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="511" />
        <source>Failed to remove processings with following ids: &lt;center&gt; {failed_ids}</source>
        <translation type="obsolete">Falha ao remover processamentos com os seguintes ids: &lt;center&gt; {failed_ids}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="517" />
        <source>The selected data provider is unavailable on your plan. 
 Upgrade your subscription to get access to the data. 
See pricing at &lt;a href="https://mapflow.ai/pricing"&gt;mapflow.ai&lt;/a&gt;</source>
        <translation>O fornecedor de dados selecionado não está disponível no seu plano.
Atualize a sua subscrição para ter acesso aos dados.
Veja os preços em &lt;a href="https://mapflow.ai/pricing"&gt;mapflow.ai&lt;/a&gt;</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="528" />
        <source>Processing creation failed</source>
        <translation>Criação do processamento falhou</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="157" />
        <source>The processing area is {area} sq km, over the {limit} sq km limit. Try splitting your area(s) into several processings.</source>
        <translation>A área de processamento é de {area} km², acima do limite de {limit} km². Tente dividir a(s) sua(s) área(s) em vários processamentos.</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="170" />
        <source>An AOI is too large: its bounding box is {area} sq km, over the {limit} sq km limit. Reduce the area of interest.</source>
        <translation>Uma AOI é demasiado grande: a sua caixa delimitadora tem {area} km², acima do limite de {limit} km². Reduza a área de interesse.</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="180" />
        <source>the selected</source>
        <translation>o selecionado</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="288" />
        <source>Select one or more images in search results to start planned processing</source>
        <translation>Selecione uma ou mais imagens nos resultados da pesquisa para iniciar o processamento planeado</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="340" />
        <source>Starting planned processing...</source>
        <translation>A iniciar processamento planeado...</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="989" />
        <source>Rename template</source>
        <translation>Renomear modelo</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="989" />
        <source>Template name:</source>
        <translation>Nome do modelo:</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1000" />
        <source>Please, specify template name</source>
        <translation>Especifique o nome do modelo</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1045" />
        <source>Error renaming template: {}</source>
        <translation>Erro ao renomear o modelo: {}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1232" />
        <source>Unknown server error</source>
        <translation>Erro desconhecido do servidor</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1129" />
        <source>Delete selected items?</source>
        <translation>Eliminar os itens selecionados?</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1144" />
        <source>Failed to remove items with following ids: &lt;center&gt; {failed_ids}</source>
        <translation>Falha ao remover os itens com os seguintes ids: &lt;center&gt; {failed_ids}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1210" />
        <source>Template is not active</source>
        <translation>O modelo não está ativo</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1216" />
        <source>Template paused successfully</source>
        <translation>Modelo pausado com sucesso</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1218" />
        <source>Failed to pause template: {}</source>
        <translation>Falha ao pausar o modelo: {}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1236" />
        <source>Error pausing template: {}</source>
        <translation>Erro ao pausar o modelo: {}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1254" />
        <source>Template is already active</source>
        <translation>O modelo já está ativo</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1285" />
        <source>Template resumed successfully</source>
        <translation>Modelo retomado com sucesso</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1287" />
        <source>Failed to resume template: {}</source>
        <translation>Falha ao retomar o modelo: {}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1292" />
        <source>Error resuming template: {}</source>
        <translation>Erro ao retomar o modelo: {}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1301" />
        <source>Only failed templates can be restarted</source>
        <translation>Apenas os modelos com falha podem ser reiniciados</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1313" />
        <source>Template restarted successfully</source>
        <translation>Modelo reiniciado com sucesso</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1315" />
        <source>Failed to restart template: {}</source>
        <translation>Falha ao reiniciar o modelo: {}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1319" />
        <source>Error restarting template: {}</source>
        <translation>Erro ao reiniciar o modelo: {}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1328" />
        <source>Delete Template</source>
        <translation>Eliminar modelo</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1328" />
        <source>Are you sure you want to delete the template '{}'?</source>
        <translation>Tem a certeza de que pretende eliminar o modelo '{}'?</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1346" />
        <source>Template deleted successfully</source>
        <translation>Modelo eliminado com sucesso</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1348" />
        <source>Failed to delete template: {}</source>
        <translation>Falha ao eliminar o modelo: {}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1352" />
        <source>Error deleting template: {}</source>
        <translation>Erro ao eliminar o modelo: {}</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1364" />
        <source>This AOI has no id yet and cannot be renamed. Reopen the template and try again.</source>
        <translation>Esta AOI ainda não tem id e não pode ser renomeada. Reabra o modelo e tente novamente.</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1368" />
        <source>Rename AOI</source>
        <translation>Renomear AOI</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1368" />
        <source>AOI name:</source>
        <translation>Nome da AOI:</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1378" />
        <source>Please, specify AOI name</source>
        <translation>Especifique o nome da AOI</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1381" />
        <source>AOI name must not exceed {limit} characters</source>
        <translation>O nome da AOI não deve exceder {limit} caracteres</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1403" />
        <source>Delete selected AOI(s)?</source>
        <translation>Eliminar a(s) AOI selecionada(s)?</translation>
    </message>
    <message>
        <location filename="../functional/service/processing_service.py" line="1441" />
        <source>AOI update failed: {}</source>
        <translation>Falha ao atualizar a AOI: {}</translation>
    </message>
</context>
<context>
    <name>ProcessingView</name>
    <message>
        <location filename="../functional/view/processing_view.py" line="230" />
        <source>Please review or accept this processing until {}. Double click to add results to the map</source>
        <translation>Por favor, reveja ou aceite este processamento até {}. Duplo clique para adicionar resultados ao mapa</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="235" />
        <source>Double click to add results to the map.</source>
        <translation>Duplo clique para adicionar resultados ao mapa.</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="321" />
        <source>Loading...</source>
        <translation>A carregar...</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="322" />
        <source>Fetching your processings from server, please wait</source>
        <translation>A obter os seus processamentos do servidor, por favor aguarde</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="379" />
        <source>Processing cost: {cost} credits</source>
        <translation>Custo do processamento: {cost} créditos</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="388" />
        <source> failed with error:
</source>
        <translation> falhou com erro:</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="395" />
        <source>{} processings failed: 
 {} 
 See tooltip over the processings table for error details</source>
        <translation>{} processamentos falharam:
{}
Consulte a dica de contexto sobre a tabela de processamentos para detalhes do erro</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="402" />
        <source>{} processings failed: 
 See tooltip over the processings table for error details</source>
        <translation>{} processamentos falharam:
Consulte a dica de contexto sobre a tabela de processamentos para detalhes do erro</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="414" />
        <source> finished. Double-click it in the table to download the results.</source>
        <translation> terminado. Duplo clique na tabela para descarregar os resultados.</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="422" />
        <source>{} processings finished: 
 {} 
 Double-click it in the table to download the results</source>
        <translation>{} processamentos terminados:
{}
Duplo clique na tabela para descarregar os resultados</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="430" />
        <source>{} processings finished. 
 Double-click it in the table to download the results</source>
        <translation>{} processamentos terminados.
Duplo clique na tabela para descarregar os resultados</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="36" />
        <source>Newest first</source>
        <translation>Mais recentes primeiro</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="36" />
        <source>Oldest first</source>
        <translation>Mais antigos primeiro</translation>
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
        <translation>Filtrar processamentos</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="140" />
        <source>Open Details</source>
        <translation>Abrir detalhes</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="142" />
        <source>Pause Template</source>
        <translation>Pausar modelo</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="143" />
        <source>Resume Template</source>
        <translation>Retomar modelo</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="145" />
        <source>Delete Template</source>
        <translation>Eliminar modelo</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="212" />
        <source>Planned processing</source>
        <translation>Processamento planeado</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="214" />
        <source>Planned processing. New images: {count}</source>
        <translation>Processamento planeado. Novas imagens: {count}</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="219" />
        <source>Template AOI</source>
        <translation>AOI do modelo</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="221" />
        <source>Template AOI with new images</source>
        <translation>AOI do modelo com novas imagens</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="224" />
        <source>Processing from this AOI. Double-click to load results.</source>
        <translation>Processamento desta AOI. Faça duplo clique para carregar os resultados.</translation>
    </message>
    <message>
        <location filename="../functional/view/processing_view.py" line="226" />
        <source>Processings not intersecting any AOI</source>
        <translation>Processamentos que não intersetam nenhuma AOI</translation>
    </message>
</context>
<context>
    <name>ProjectDialog</name>
    <message>
        <location filename="../dialogs/static/ui/project_dialog.ui" line="14" />
        <source>Project</source>
        <translation>Projeto</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/project_dialog.ui" line="20" />
        <source>Name</source>
        <translation>Nome</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/mosaic_dialog.ui" line="34" />
        <source>Tags</source>
        <translation>Etiquetas</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/mosaic_dialog.ui" line="51" />
        <source>Note: separate tags with comma (", ") </source>
        <translation>Nota: separe as etiquetas com vírgula (", ")</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/mosaic_dialog.ui" line="75" />
        <source>Create empty mosaic</source>
        <translation>Criar mosaico vazio</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/mosaic_dialog.ui" line="80" />
        <source>Upload from files</source>
        <translation>Upload a partir de ficheiros</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/mosaic_dialog.ui" line="85" />
        <source>Choose raster layers</source>
        <translation>Escolha camadas raster</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/project_dialog.ui" line="34" />
        <source>Description</source>
        <translation>Descrição</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="26" />
        <source>Start processing with specified parameters?</source>
        <translation>Iniciar processamento com os parâmetros especificados?</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="66" />
        <source>Area:</source>
        <translation>Área:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="82" />
        <source>Name:</source>
        <translation>Nome:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="132" />
        <source>Data source:</source>
        <translation>Fonte de dados:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="216" />
        <source>Zoom:</source>
        <translation>Zoom:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="232" />
        <source>Model options:</source>
        <translation>Opções do modelo:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="248" />
        <source>Price:</source>
        <translation>Preço:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="332" />
        <source>Model:</source>
        <translation>Modelo:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_start_confirmation.ui" line="428" />
        <source>Don't show this message again</source>
        <translation>Não mostrar esta mensagem novamente</translation>
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
        <translation>Descrição:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_details.ui" line="444" />
        <source>Data provider:</source>
        <translation>Fornecedor de dados:</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/processing_details.ui" line="492" />
        <source>Error:</source>
        <translation>Erro:</translation>
    </message>
    <message>
        <location filename="../dialogs/project_dialog.py" line="25" />
        <source>Project name must not be empty!</source>
        <translation>O nome do projeto não pode estar vazio!</translation>
    </message>
    <message>
        <location filename="../dialogs/project_dialog.py" line="55" />
        <source>Edit project </source>
        <translation>Editar projeto </translation>
    </message>
</context>
<context>
    <name>ProjectProcessingController</name>
    <message>
        <location filename="../functional/controller/processing_controller.py" line="205" />
        <source>Do you really want to remove project {}? This action cannot be undone, all processings will be lost!</source>
        <translation>Deseja realmente remover o projeto {}? Esta ação não pode ser desfeita, todos os processamentos serão perdidos!</translation>
    </message>
    <message>
        <location filename="../functional/controller/processing_controller.py" line="107" />
        <source>Processing</source>
        <translation>Processamento</translation>
    </message>
</context>
<context>
    <name>ProjectService</name>
    <message>
        <location filename="../functional/service/project_service.py" line="227" />
        <source>Project: &lt;b&gt;{}</source>
        <translation>Projeto: &lt;b&gt;{}</translation>
    </message>
    <message>
        <location filename="../functional/service/project_service.py" line="244" />
        <source>No project selected</source>
        <translation>Nenhum projeto selecionado</translation>
    </message>
    <message>
        <location filename="../functional/service/project_service.py" line="246" />
        <source>You can't remove or modify default project</source>
        <translation>Não pode remover ou modificar o projeto padrão</translation>
    </message>
    <message>
        <location filename="../functional/service/project_service.py" line="249" />
        <source>Not enough rights to delete or update shared project ({})</source>
        <translation>Permissões insuficientes para eliminar ou atualizar projeto partilhado ({})</translation>
    </message>
</context>
<context>
    <name>ProjectView</name>
    <message>
        <location filename="../functional/view/project_view.py" line="59" />
        <source>See projects</source>
        <translation>Ver projetos</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="61" />
        <source>See processings</source>
        <translation>Ver processamentos</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="63" />
        <source>Filter projects by name</source>
        <translation>Filtrar projetos por nome</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="64" />
        <source>Create project</source>
        <translation>Criar projeto</translation>
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
        <translation>Mais recentes primeiro</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="66" />
        <source>Oldest first</source>
        <translation>Mais antigos primeiro</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="66" />
        <source>Updated recently</source>
        <translation>Atualizados recentemente</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="66" />
        <source>Updated long ago</source>
        <translation>Atualizados há muito tempo</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="164" />
        <source>Project</source>
        <translation>Projeto</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="170" />
        <source>Processing</source>
        <translation>Processamento</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="145" />
        <source>No project that meets specified criteria was found</source>
        <translation>Nenhum projeto que cumpra os critérios especificados foi encontrado</translation>
    </message>
    <message>
        <location filename="../functional/view/project_view.py" line="118" />
        <source>Succeeded: {ok} · Failed: {failed} · Planned: {templates}</source>
        <translation>Concluídos: {ok} · Falhados: {failed} · Planeados: {templates}</translation>
    </message>
</context>
<context>
    <name>ProviderDialog</name>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="35" />
        <source>Provider</source>
        <translation>Fornecedor</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="53" />
        <source>Type</source>
        <translation>Tipo</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="66" />
        <source>Tile coordinate scheme. XYZ is the most popular format, use it if you are not sure</source>
        <translation>Esquema de coordenadas de tile. XYZ é o formato mais popular, use-o se não tiver a certeza</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="85" />
        <source>Maxar WMTS</source>
        <translation type="obsolete">Maxar WMTS</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="88" />
        <source>Name</source>
        <translation>Nome</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="112" />
        <source>Login</source>
        <translation>Login</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="122" />
        <source>Password</source>
        <translation>Password</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="129" />
        <source>CRS</source>
        <translation>CRS</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="154" />
        <source>Projection of the tile layer. The most popular is Web Mercator, use it if you are not sure</source>
        <translation>Projeção da camada de tile. A mais popular é Web Mercator, use-a se não tiver a certeza</translation>
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
        <translation>Aviso! Login e password, se guardados, serão armazenados nas definições do QGIS sem encriptação!</translation>
    </message>
    <message>
        <location filename="../dialogs/static/ui/provider_dialog.ui" line="174" />
        <source>Save login and password</source>
        <translation>Guardar login e password</translation>
    </message>
</context>
<context>
    <name>ProviderService</name>
    <message>
        <location filename="../functional/service/provider_service.py" line="109" />
        <source>Providers are not initialized</source>
        <translation>Fornecedores não estão inicializados</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="191" />
        <source>Choose imagery collection or image to start processing</source>
        <translation>Escolha coleção de imagens ou imagem para iniciar processamento</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="197" />
        <source>This provider requires image ID. Use search tab to find imagery for you requirements, and select image in the table.</source>
        <translation>Este fornecedor requer ID da imagem. Use o separador de pesquisa para encontrar imagens conforme os seus requisitos e selecione a imagem na tabela.</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="316" />
        <source>You can launch multiple image processing only if it has the same provider of mosaic type</source>
        <translation>Só pode lançar múltiplos processamentos de imagem se estes tiverem o mesmo fornecedor de tipo mosaico</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="346" />
        <source>Duplication failed on copying data source</source>
        <translation>Duplicação falhou ao copiar fonte de dados</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="354" />
        <source>Model '{wd}' is not enabled for your account</source>
        <translation>O modelo '{wd}' não está ativado para a sua conta</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="383" />
        <source>The following options no longer exist, so they have not been duplicated: {}</source>
        <translation>As seguintes opções já não existem, por isso não foram duplicadas: {}</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="388" />
        <source>Duplication failed on copying model options</source>
        <translation>Duplicação falhou ao copiar opções do modelo</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="397" />
        <source>Provider '{provider}' is not enabled for your account</source>
        <translation>O fornecedor '{provider}' não está ativado para a sua conta</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="495" />
        <source>Duplicated user provider</source>
        <translation>Fornecedor de utilizador duplicado</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="217" />
        <source>Selected search results must be of the same product type</source>
        <translation>Os resultados de pesquisa selecionados devem ser do mesmo tipo de produto</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="227" />
        <source>Selected search results must have the same zoom level</source>
        <translation>Os resultados de pesquisa selecionados devem ter o mesmo nível de zoom</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="361" />
        <source>Duplication failed on copying model</source>
        <translation>A duplicação falhou ao copiar o modelo</translation>
    </message>
    <message>
        <location filename="../functional/service/provider_service.py" line="268" />
        <source>Geometry area is {aoiArea:.2f} sq km, which is smaller than the minimum required area for {providerName} data provider ({providerMinArea} sq km)</source>
        <translation>A área da geometria é {aoiArea:.2f} km², inferior à área mínima exigida para o fornecedor de dados {providerName} ({providerMinArea} km²)</translation>
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
        <translation>&amp;Sim</translation>
    </message>
    <message>
        <location filename="../mapflow.py" line="165" />
        <source>&amp;No</source>
        <translation>&amp;Não</translation>
    </message>
</context>
<context>
    <name>RenameImageDialog</name>
    <message>
        <location filename="../dialogs/image_dialog.py" line="18" />
        <source>Dialog requires current image</source>
        <translation>O diálogo requer imagem atual</translation>
    </message>
    <message>
        <location filename="../dialogs/image_dialog.py" line="19" />
        <source>Rename image {}</source>
        <translation>Renomear imagem {}</translation>
    </message>
    <message>
        <location filename="../dialogs/image_dialog.py" line="34" />
        <source>Image name must not be empty!</source>
        <translation>O nome da imagem não pode estar vazio!</translation>
    </message>
</context>
<context>
    <name>ReviewDialog</name>
    <message>
        <location filename="../dialogs/review_dialog.py" line="25" />
        <source>Review {processing}</source>
        <translation>Rever {processing}</translation>
    </message>
</context>
<context>
    <name>UpdateMosaicDialog</name>
    <message>
        <location filename="../dialogs/mosaic_dialog.py" line="49" />
        <source>UpdateMosaicDialog requires a imagery collection to update</source>
        <translation>UpdateMosaicDialog requer uma coleção de imagens para atualizar</translation>
    </message>
    <message>
        <location filename="../dialogs/mosaic_dialog.py" line="50" />
        <source>Edit imagery collection {}</source>
        <translation>Editar coleção de imagens {}</translation>
    </message>
    <message>
        <location filename="../dialogs/mosaic_dialog.py" line="62" />
        <source>Imagery collection name must not be empty!</source>
        <translation>O nome da coleção de imagens não pode estar vazio!</translation>
    </message>
</context>
<context>
    <name>UpdateProcessingDialog</name>
    <message>
        <location filename="../dialogs/processing_dialog.py" line="26" />
        <source>Processing name must not be empty!</source>
        <translation>O nome do processamento não pode estar vazio!</translation>
    </message>
    <message>
        <location filename="../dialogs/processing_dialog.py" line="34" />
        <source>Edit processing {}</source>
        <translation>Editar processamento {}</translation>
    </message>
</context>
<context>
    <name>UploadRasterLayersDialog</name>
    <message>
        <location filename="../dialogs/upload_raster_layer_dialog.py" line="17" />
        <source>Choose raster layers to upload to imagery collection</source>
        <translation>Escolha camadas raster para fazer upload para a coleção de imagens</translation>
    </message>
</context>
<context>
    <name>raterLayerSelection</name>
    <message>
        <location filename="../dialogs/static/ui/raster_layers_dialog.ui" line="14" />
        <source>Multiple selection</source>
        <translation>Seleção múltipla</translation>
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
        <translation>Camada de mapa com revisão</translation>
    </message>
</context>
<context><name>ProcessingTable</name><message><source>(unnamed)</source><translation>(sem nome)</translation></message><message><source>AOI</source><translation>AOI</translation></message><message><source>Created</source><translation>Criado</translation></message><message><source>Failed</source><translation>Falhado</translation></message><message><source>Failed ({ok}/{total})</source><translation>Falhados ({ok}/{total})</translation></message><message><source>In progress ({ok}/{total})</source><translation>Em curso ({ok}/{total})</translation></message><message><source>Inactive</source><translation>Inativo</translation></message><message><source>No AOI</source><translation>Sem AOI</translation></message><message><source>OK ({ok}/{total})</source><translation>OK ({ok}/{total})</translation></message><message><source>OK ({total})</source><translation>OK ({total})</translation></message><message><source>Planned</source><translation>Planeado</translation></message><message><source>Searching</source><translation>A pesquisar</translation></message><message><source>Updated</source><translation>Atualizado</translation></message><message><source>Updated ({count})</source><translation>Atualizado ({count})</translation></message></context></TS>