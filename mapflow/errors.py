from typing import Dict
from PyQt5.QtCore import QT_TR_NOOP, QObject

"""
["messages":[{"code":"source-validator.PixelSizeTooHigh","parameters":{"max_res":"1.2","level":"error","actual_res":"5.620983603290215"}}]}]
"""

error_descriptions = {
            "source-validator.UrlMustBeString":  QT_TR_NOOP("Key \'url\' in your request must be a string, got {url_type} instead."),
            "source-validator.UrlMustBeLink": QT_TR_NOOP("Your URL must be a link starting with \"http://\" or \"https://\"."),
            "source-validator.UrlFormatInvalid": QT_TR_NOOP("Format of \'url\' is invalid and cannot be parsed. Error: {parse_error_message}"),
            "source-validator.ZoomMustBeInteger": QT_TR_NOOP("Zoom must be either empty, or integer, got {actual_zoom}"),
            "source-validator.InvalidZoomValue": QT_TR_NOOP("Zoom must be between 0 and 22, got {actual_zoom}"),
            "source-validator.TooHighZoom": QT_TR_NOOP("Zoom must be between 0 and 22, got {actual_zoom}"),
            "source-validator.TooLowZoom": QT_TR_NOOP("Zoom must be not lower than {min_zoom}, got {actual_zoom}"),
            "source-validator.ImageMetadataMustBeDict": QT_TR_NOOP("Image metadata must be a dict (json)"),
            "source-validator.ImageMetadataKeyError": QT_TR_NOOP("Image metadata must have keys: crs, transform, dtype, count"),
            "source-validator.S3URLError": QT_TR_NOOP("URL of the image at s3 storage must be a string starting with s3://, got {actual_s3_link}"),
            "source-validator.LocalRequestKeyError": QT_TR_NOOP("Request must contain either 'profile' or 'url' keys"),
            "source-validator.ReadFromS3Failed": QT_TR_NOOP("Failed to read file from {s3_link}."),
            "source-validator.DtypeNotAllowed": QT_TR_NOOP("Image data type (Dtype) must be one of {required_dtypes}, got {request_dtype}"),
            "source-validator.NChannelsNotAllowed": QT_TR_NOOP("Number of channels in image must be one of {required_nchannels}. Got {real_nchannels}"),
            "source-validator.PixelSizeTooLow": QT_TR_NOOP("Spatial resolution of you image is too high: pixel size is {actual_res}, minimum allowed pixel size is {min_res}"),
            "source-validator.PixelSizeTooHigh": QT_TR_NOOP("Spatial resolution of you image is too low: pixel size is {actual_res}, maximum allowed pixel size is {max_res}"),
            "source-validator.ImageCheckError": QT_TR_NOOP("Error occurred during image {checked_param} check: {message}. Image metadata = {metadata}."),
            "source-validator.QuadkeyLinkFormatError": QT_TR_NOOP("Your \'url\' doesn't match the format, Quadkey basemap must be a link containing \"q\" placeholder."),
            "source-validator.SentinelInputStringKeyError": QT_TR_NOOP("Input string {input_string} is of unknown format. It must represent Sentinel-2 granule ID."),
            "source-validator.GridCellOutOfBound": QT_TR_NOOP("Selected Sentinel-2 image cell is {actual_cell}, this model is for the cells: {allowed_cells}"),
            "source-validator.MonthOutOfBounds": QT_TR_NOOP("Selected Sentinel-2 image month is {actual_month}, this model is for: {allowed_months}"),
            "source-validator.TMSLinkFormatError": QT_TR_NOOP("You request TMS basemap link doesn't match the format, it must be a link containing '{x}', '{y}', '{z}' placeholders, correct it and start processing again."),
            "source-validator.RequirementsMustBeDict": QT_TR_NOOP("Requirements must be dict, got {requirements_type}."),
            "source-validator.RequestMustBeDict": QT_TR_NOOP("Request must be dict, got {request_type}."),
            "source-validator.RequestMustHaveSourceType": QT_TR_NOOP("Request must contain \"source_type\" key"),
            "source-validator.SourceTypeIsNotAllowed": QT_TR_NOOP("Source type {source_type} is not allowed. Use one of: {allowed_sources}"),
            "source-validator.RequiredSectionMustBeDict": QT_TR_NOOP("\"Required\" section of the requirements must contain dict, not {required_section_type}"),
            "source-validator.RecommendedSectionMustBeDict": QT_TR_NOOP("\"Recommended\" section of the requirements must contain dict, not {recommended_section_type}"),
            "source-validator.XYZLinkFormatError": QT_TR_NOOP("You XYZ basemap link doesn't match the format, it must be a link containing '{x}', '{y}', '{z}' placeholders."),
            "source-validator.UnhandledException": QT_TR_NOOP("Internal error in process of data source validation. We are working on the fix, our support will contact you."),
            "source-validator.internalError": QT_TR_NOOP("Internal error in process of data source validation. We are working on the fix, our support will contact you."),
            "dataloader.internalError": QT_TR_NOOP("Internal error in process of loading data. We are working on the fix, our support will contact you."),
            "dataloader.UnknownSourceType": QT_TR_NOOP("Wrong source type {real_source_type}. Specify one of the allowed types {allowed_source_types}."),
            "dataloader.MemoryLimitExceeded": QT_TR_NOOP("Your data loading task requires {estimated_size} MB of memory, which exceeded allowed memory limit {allowed_size}"),
            "dataloader.LoaderArgsError": QT_TR_NOOP("Dataloader argument {argument_name} has type {argument_type}, excpected to be {expected_type}"),
            "dataloader.WrongChannelsNum": QT_TR_NOOP("Loaded tile has {real_nchannels} channels, required number is {expected_nchannels}"),
            "dataloader.WrongTileSize": QT_TR_NOOP("Loaded tile has size {real_size}, expected tile size is {expected_size}"),
            "dataloader.TileNotLoaded": QT_TR_NOOP("Tile at location {tile_location} cannot be loaded, server response is {status}"),
            "dataloader.TileNotReadable": QT_TR_NOOP("Response content at {tile_location} cannot be decoded as an image"),
            "dataloader.CrsIsNotSupported": QT_TR_NOOP("Internal error in process of loading data. We are working on the fix, our support will contact you."),
            "dataloader.MaploaderInternalError": QT_TR_NOOP("Internal error in process of loading data. We are working on the fix, our support will contact you."),
            "dataloader.SentinelLoaderInternalError": QT_TR_NOOP("Internal error in process of loading data. We are working on the fix, our support will contact you."),
            "raster-processor.internalError": QT_TR_NOOP("Internal error in process of data preparation. We are working on the fix, our support will contact you."),
            "inference.internalError": QT_TR_NOOP("Internal error in process of data processing. We are working on the fix, our support will contact you."),
            "vector-processor.internalError": QT_TR_NOOP("Internal error in process of saving the results. We are working on the fix, our support will contact you.")
        }


class ErrorMessage(QObject):
    def __init__(self, code: str, parameters: Dict[str, str]):
        super().__init__()
        self.code = code
        self.parameters = parameters
        self.message = error_descriptions.get(code,
                                              QT_TR_NOOP("Unknown error. Contact us to resolve the issue! help@geoalert.io"))

    @classmethod
    def from_response(cls, response: Dict):
        return cls(response["code"], response["parameters"])

    def __str__(self):
        return self.tr(self.message).format(**self.parameters)
