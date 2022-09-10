from typing import Dict
from .translate import tr
"""
["messages":[{"code":"source-validator.PixelSizeTooHigh","parameters":{"max_res":"1.2","level":"error","actual_res":"5.620983603290215"}}]}]
"""

error_descriptions = {
    "source-validator.UrlMustBeString":  tr("Key \'url\' in your request must be a string, got {url_type} instead."),
    "source-validator.UrlMustBeLink": tr("Your URL must be a link starting with \"http://\" or \"https://\"."),
    "source-validator.UrlFormatInvalid": tr("Format of \'url\' is invalid and cannot be parsed. Error: {parse_error_message}"),
    "source-validator.ZoomMustBeInteger": tr("Zoom must be either empty, or integer, got {actual_zoom}"),
    "source-validator.InvalidZoomValue": tr("Zoom must be between 0 and 22, got {actual_zoom}"),
    "source-validator.TooHighZoom": tr("Zoom must be between 0 and 22, got {actual_zoom}"),
    "source-validator.TooLowZoom": tr("Zoom must be not lower than {min_zoom}, got {actual_zoom}"),
    "source-validator.ImageMetadataMustBeDict": tr("Image metadata must be a dict (json)"),
    "source-validator.ImageMetadataKeyError": tr("Image metadata must have keys: crs, transform, dtype, count"),
    "source-validator.S3URLError": tr("URL of the image at s3 storage must be a string starting with s3://, got {actual_s3_link}"),
    "source-validator.LocalRequestKeyError": tr("Request must contain either 'profile' or 'url' keys"),
    "source-validator.ReadFromS3Failed": tr("Failed to read file from {s3_link}."),
    "source-validator.DtypeNotAllowed": tr("Image data type (Dtype) must be one of {required_dtypes}, got {request_dtype}"),
    "source-validator.NChannelsNotAllowed": tr("Number of channels in image must be one of {required_nchannels}. Got {real_nchannels}"),
    "source-validator.PixelSizeTooLow": tr("Spatial resolution of you image is too high: pixel size is {actual_res}, minimum allowed pixel size is {min_res}"),
    "source-validator.PixelSizeTooHigh": tr("Spatial resolution of you image is too low: pixel size is {actual_res}, maximum allowed pixel size is {max_res}"),
    "source-validator.ImageCheckError": tr("Error occurred during image {checked_param} check: {message}. Image metadata = {metadata}."),
    "source-validator.QuadkeyLinkFormatError": tr("Your 'url' doesn't match the format, Quadkey basemap must be a link containing \"q\" placeholder."),
    "source-validator.SentinelInputStringKeyError": tr("Input string {input_string} is of unknown format. It must represent Sentinel-2 granule ID."),
    "source-validator.GridCellOutOfBound": tr("Selected Sentinel-2 image cell is {actual_cell}, this model is for the cells: {allowed_cells}"),
    "source-validator.MonthOutOfBounds": tr("Selected Sentinel-2 image month is {actual_month}, this model is for: {allowed_months}"),
    "source-validator.TMSLinkFormatError": tr("You request TMS basemap link doesn't match the format, it must be a link containing '{x}', '{y}', '{z}' placeholders, correct it and start processing again."),
    "source-validator.RequirementsMustBeDict": tr("Requirements must be dict, got {requirements_type}."),
    "source-validator.RequestMustBeDict": tr("Request must be dict, got {request_type}."),
    "source-validator.RequestMustHaveSourceType": tr("Request must contain \"source_type\" key"),
    "source-validator.SourceTypeIsNotAllowed": tr("Source type {source_type} is not allowed. Use one of: {allowed_sources}"),
    "source-validator.RequiredSectionMustBeDict": tr("\"Required\" section of the requirements must contain dict, not {required_section_type}"),
    "source-validator.RecommendedSectionMustBeDict": tr("\"Recommended\" section of the requirements must contain dict, not {recommended_section_type}"),
    "source-validator.XYZLinkFormatError": tr("You XYZ basemap link doesn't match the format, it must be a link containing '{x}', '{y}', '{z}' placeholders."),
    "source-validator.UnhandledException": tr("Internal error in process of data source validation. We are working on the fix, our support will contact you."),
    "source-validator.internalError": tr("Internal error in process of data source validation. We are working on the fix, our support will contact you."),
    "dataloader.internalError": tr("Internal error in process of loading data. We are working on the fix, our support will contact you."),
    "dataloader.UnknownSourceType": tr("Wrong source type {real_source_type}. Specify one of the allowed types {allowed_source_types}."),
    "dataloader.MemoryLimitExceeded": tr("Your data loading task requires {estimated_size} MB of memory, which exceeded allowed memory limit {allowed_size}"),
    "dataloader.LoaderArgsError": tr("Dataloader argument {argument_name} has type {argument_type}, excpected to be {expected_type}"),
    "dataloader.WrongChannelsNum": tr("Loaded tile has {real_nchannels} channels, required number is {expected_nchannels}"),
    "dataloader.WrongTileSize": tr("Loaded tile has size {real_size}, expected tile size is {expected_size}"),
    "dataloader.TileNotLoaded": tr("Tile at location {tilSSe_location} cannot be loaded, server response is {status}"),
    "dataloader.TileNotReadable": tr("Response content at {tile_location} cannot be decoded as an image"),
    "dataloader.CrsIsNotSupported": tr("Internal error in process of loading data. We are working on the fix, our support will contact you."),
    "dataloader.MaploaderInternalError": tr("Internal error in process of loading data. We are working on the fix, our support will contact you."),
    "dataloader.SentinelLoaderInternalError": tr("Internal error in process of loading data. We are working on the fix, our support will contact you."),
    "raster-processor.internalError": tr("Internal error in process of data preparation. We are working on the fix, our support will contact you."),
    "inference.internalError": tr("Internal error in process of data processing. We are working on the fix, our support will contact you."),
    "vector-processor.internalError": tr("Internal error in process of saving the results. We are working on the fix, our support will contact you.")
}


class ErrorMessage:
    def __init__(self, code: str, parameters: Dict[str, str]):
        self.code = code
        self.parameters = parameters
        self.message = error_descriptions.get(code, "Unknown error. Contact us to resolve the issue!")

    @classmethod
    def from_response(cls, response: Dict):
        return cls(response["code"], response["parameters"])

    def __str__(self):
        return self.message.format(**self.parameters)
