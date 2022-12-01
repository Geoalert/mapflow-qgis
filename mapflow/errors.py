from typing import Dict
from PyQt5.QtCore import QObject

"""
["messages":[{"code":"source-validator.PixelSizeTooHigh","parameters":{"max_res":"1.2","level":"error","actual_res":"5.620983603290215"}}]}]
"""


class ErrorMessageList(QObject):
    def __init__(self):
        super().__init__()
        self.error_descriptions = {
            "source-validator.TaskMustContainAoi": self.tr("Task for source-validation must contain area of interest "
                                                           "(`geometry` section)"),
            "source-validator.ImageReadError": self.tr("We could not open and read the image you have uploaded"),
            "source-validator.BadImageProfile": self.tr("Image profile (metadata) must have keys "
                                                        "{required_keys}, got profile {profile}"),
            "source-validator.AOINotInCell": self.tr(
                "AOI does not intersect the selected Sentinel-2 granule {actual_cell}"),
            "source-validator.UrlMustBeString": self.tr("Key \'url\' in your request must be a string, "
                                                        "got {url_type} instead."),
            "source-validator.UrlBlacklisted": self.tr("The specified basemap {url} is forbidden for processing"
                                                       " because it contains a map, not satellite image. "
                                                       "Our models are suited for satellite imagery."),
            "source-validator.UrlMustBeLink": self.tr("Your URL must be a link "
                                                      "starting with \"http://\" or \"https://\"."),
            "source-validator.UrlFormatInvalid": self.tr("Format of \'url\' is invalid and cannot be parsed. "
                                                         "Error: {parse_error_message}"),
            "source-validator.ZoomMustBeInteger": self.tr("Zoom must be either empty, or integer, got {actual_zoom}"),
            "source-validator.InvalidZoomValue": self.tr("Zoom must be between 0 and 22, got {actual_zoom}"),
            "source-validator.TooHighZoom": self.tr("Zoom must be between 0 and 22, got {actual_zoom}"),
            "source-validator.TooLowZoom": self.tr("Zoom must be not lower than {min_zoom}, got {actual_zoom}"),
            "source-validator.ImageMetadataMustBeDict": self.tr("Image metadata must be a dict (json)"),
            "source-validator.ImageMetadataKeyError": self.tr("Image metadata must have keys: "
                                                              "crs, transform, dtype, count"),
            "source-validator.S3URLError": self.tr("URL of the image at s3 storage must be a string "
                                                   "starting with s3://, got {actual_s3_link}"),
            "source-validator.LocalRequestKeyError": self.tr("Request must contain either 'profile' or 'url' keys"),
            "source-validator.ReadFromS3Failed": self.tr("Failed to read file from {s3_link}."),
            "source-validator.DtypeNotAllowed": self.tr("Image data type (Dtype) must be one of "
                                                        "{required_dtypes}, got {request_dtype}"),
            "source-validator.NChannelsNotAllowed": self.tr("Number of channels in image must be one of "
                                                            "{required_nchannels}. Got {real_nchannels}"),
            "source-validator.PixelSizeTooLow": self.tr("Spatial resolution of you image is too high: "
                                                        "pixel size is {actual_res}, "
                                                        "minimum allowed pixel size is {min_res}"),
            "source-validator.PixelSizeTooHigh": self.tr("Spatial resolution of you image is too low:"
                                                         " pixel size is {actual_res}, "
                                                         "maximum allowed pixel size is {max_res}"),
            "source-validator.ImageCheckError": self.tr("Error occurred during image {checked_param} check: {message}. "
                                                        "Image metadata = {metadata}."),
            "source-validator.QuadkeyLinkFormatError": self.tr("Your \'url\' doesn't match the format, "
                                                               "Quadkey basemap must be a link "
                                                               "containing \"q\" placeholder."),
            "source-validator.SentinelInputStringKeyError": self.tr("Input string {input_string} is of unknown format. "
                                                                    "It must represent Sentinel-2 granule ID."),
            "source-validator.GridCellOutOfBound": self.tr("Selected Sentinel-2 image cell is {actual_cell}, "
                                                           "this model is for the cells: {allowed_cells}"),
            "source-validator.MonthOutOfBounds": self.tr("Selected Sentinel-2 image month is {actual_month}, "
                                                         "this model is for: {allowed_months}"),
            "source-validator.TMSLinkFormatError": self.tr("You request TMS basemap link doesn't match the format, "
                                                           "it must be a link containing '{x}', '{y}', '{z}' "
                                                           "placeholders, correct it and start processing again."),
            "source-validator.RequirementsMustBeDict": self.tr("Requirements must be dict, got {requirements_type}."),
            "source-validator.RequestMustBeDict": self.tr("Request must be dict, got {request_type}."),
            "source-validator.RequestMustHaveSourceType": self.tr("Request must contain \"source_type\" key"),
            "source-validator.SourceTypeIsNotAllowed": self.tr("Source type {source_type} is not allowed. "
                                                               "Use one of: {allowed_sources}"),
            "source-validator.RequiredSectionMustBeDict": self.tr("\"Required\" section of the requirements "
                                                                  "must contain dict, not {required_section_type}"),
            "source-validator.RecommendedSectionMustBeDict": self.tr("\"Recommended\" section of the requirements "
                                                                     "must contain dict, not {recommended_section_type}"),
            "source-validator.XYZLinkFormatError": self.tr("You XYZ basemap link doesn't match the format, "
                                                           "it must be a link "
                                                           "containing '{x}', '{y}', '{z}' placeholders."),
            "source-validator.UnhandledException": self.tr("Internal error in process of data source validation."
                                                           " We are working on the fix, our support will contact you."),
            "source-validator.internalError": self.tr("Internal error in process of data source validation."
                                                      " We are working on the fix, our support will contact you."),
            "dataloader.internalError": self.tr("Internal error in process of loading data. "
                                                "We are working on the fix, our support will contact you."),
            "dataloader.UnknownSourceType": self.tr("Wrong source type {real_source_type}."
                                                    " Specify one of the allowed types {allowed_source_types}."),
            "dataloader.MemoryLimitExceeded": self.tr("Your data loading task requires {estimated_size} MB of memory, "
                                                      "which exceeded allowed memory limit {allowed_size}"),
            "dataloader.LoaderArgsError": self.tr("Dataloader argument {argument_name} has type {argument_type},"
                                                  " excpected to be {expected_type}"),
            "dataloader.WrongChannelsNum": self.tr("Loaded tile has {real_nchannels} channels, "
                                                   "required number is {expected_nchannels}"),
            "dataloader.WrongTileSize": self.tr("Loaded tile has size {real_size}, expected tile size "
                                                "is {expected_size}"),
            "dataloader.TileNotLoaded": self.tr("Tile at location {tile_location} cannot be loaded, "
                                                "server response is {status}"),
            "dataloader.TileNotReadable": self.tr("Response content at {tile_location} cannot be decoded as an image"),
            "dataloader.CrsIsNotSupported": self.tr("Internal error in process of loading data. "
                                                    "We are working on the fix, our support will contact you."),
            "dataloader.MaploaderInternalError": self.tr("Internal error in process of loading data. "
                                                         "We are working on the fix, our support will contact you."),
            "dataloader.SentinelLoaderInternalError": self.tr("Internal error in process of loading data. "
                                                              "We are working on the fix, our support will contact you."),
            "raster-processor.internalError": self.tr("Internal error in process of data preparation. "
                                                      "We are working on the fix, our support will contact you."),
            "inference.internalError": self.tr("Internal error in process of data processing. "
                                               "We are working on the fix, our support will contact you."),
            "vector-processor.internalError": self.tr("Internal error in process of saving the results. "
                                                      "We are working on the fix, our support will contact you."),
            # todo: change when we normalize data-catalog errors
            "data-catalog.MemoryLimitExceeded": self.tr("You have exceeded your available memory limit. "
                                                        "Your file takes {memory_requested} bytes, "
                                                        "while your available memory is {available_memory} bytes"
                                                        " Upgrade to Mapflow Premium"
                                                        " to get more memory or delete unused data"),
            "data-catalog.FileTooBig": self.tr("Max upload file size limit exceeded."
                                               "Max upload file size = {max_file_size} bytes, "
                                               "got file size = {actual_file_size} bytes)"),
            "data-catalog.FileCheckFailed": self.tr("File {filename} can't be processed."),
            "data-catalog.ItemNotFound": self.tr("{instance_type} with ID={uid} not found"),
            "data-catalog.AccessDenied": self.tr("Access to {instance_type} with ID={uid} denied!"),
            "data-catalog.PreviewNotFound": self.tr("Preview not found for image: {image_id}")
        }

    def get(self, key, default=None):
        if not default:
            default = self.tr("Unknown error. Contact us to resolve the issue! help@geoalert.io")
        return self.error_descriptions.get(key, default)


class ErrorMessage(QObject):
    def __init__(self, code: str, parameters: Dict[str, str]):
        super().__init__()
        self.code = code
        self.parameters = parameters

    @classmethod
    def from_response(cls, response: Dict):
        return cls(response["code"], response["parameters"])

    def to_str(self, message_list):
        message = message_list.get(self.code)
        try:
            message = message.format(**self.parameters)
        except KeyError as e:
            message = message \
                      + self.tr("\n Warning: some error parameters were not loaded : {}!").format(str(e))
        except Exception as e:
            message = self.tr('Unknown error while fetching processing errors: {exception}'
                              '\n Error code: {code}'
                              '\n Contact us to resolve the issue! help@geoalert.io').format(exception=str(e),
                                                                                             code=self.code)
        return message
