"""User-facing texts for Mapflow error codes, carried over from the current plugin.

Codes come from the processing pipeline (`messages` on a processing), the data catalog and the API.
Templates use `{param}` placeholders filled from the error parameters.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

GENERIC = "Something went wrong on our side. Contact us at help@geoalert.io and we will sort it out."

CODES: Dict[str, str] = {
    'vector-processor.EmptyFolder': 'Folder `{s3_link}` selected for processing does not contain any images. ',
    'source-validator.TaskMustContainAoi': 'Task for source-validation must contain area of interest (`geometry` '
                                           'section)',
    'source-validator.ImageReadError': 'We could not open and read the image you have uploaded',
    'source-validator.BadImageProfile': 'Image profile (metadata) must have keys {required_keys}, got profile '
                                        '{profile}',
    'source-validator.AOINotInCell': 'AOI does not intersect the selected Sentinel-2 granule {actual_cell}',
    'source-validator.UrlMustBeString': "Key 'url' in your request must be a string, got {url_type} instead.",
    'source-validator.UrlBlacklisted': 'The specified basemap {url} is forbidden for processing because it contains a '
                                       'map, not satellite image. Our models are suited for satellite imagery.',
    'source-validator.UrlMustBeLink': 'Your URL must be a link starting with "http://" or "https://".',
    'source-validator.UrlFormatInvalid': "Format of 'url' is invalid and cannot be parsed. Error: "
                                         "{parse_error_message}",
    'source-validator.ZoomMustBeInteger': 'Zoom must be either empty, or integer, got {actual_zoom}',
    'source-validator.InvalidZoomValue': 'Zoom must be between 0 and 22, got {actual_zoom}',
    'source-validator.TooHighZoom': 'Zoom must be between 0 and 22, got {actual_zoom}',
    'source-validator.TooLowZoom': 'Zoom must be not lower than {min_zoom}, got {actual_zoom}',
    'source-validator.ImageMetadataMustBeDict': 'Image metadata must be a dict (json)',
    'source-validator.ImageMetadataKeyError': 'Image metadata must have keys: crs, transform, dtype, count',
    'source-validator.S3URLError': 'URL of the image at s3 storage must be a string starting with s3://, got '
                                   '{actual_s3_link}',
    'source-validator.LocalRequestKeyError': "Request must contain either 'profile' or 'url' keys",
    'source-validator.ReadFromS3Failed': 'Failed to read file from {s3_link}.',
    'source-validator.DtypeNotAllowed': 'Image data type (Dtype) must be one of {required_dtypes}, got {request_dtype}',
    'source-validator.NChannelsNotAllowed': 'Number of channels in image must be one of {required_nchannels}. Got '
                                            '{real_nchannels}',
    'source-validator.PixelSizeTooLow': 'Spatial resolution of you image is too high: pixel size is {actual_res}, '
                                        'minimum allowed pixel size is {min_res}',
    'source-validator.PixelSizeTooHigh': 'Spatial resolution of you image is too low: pixel size is {actual_res}, '
                                         'maximum allowed pixel size is {max_res}',
    'source-validator.ImageCheckError': 'Error occurred during image {checked_param} check: {message}. Image metadata '
                                        '= {metadata}.',
    'source-validator.QuadkeyLinkFormatError': 'Your \'url\' doesn\'t match the format, Quadkey basemap must be a '
                                               'link containing "q" placeholder.',
    'source-validator.SentinelInputStringKeyError': 'Input string {input_string} is of unknown format. It must '
                                                    'represent Sentinel-2 granule ID.',
    'source-validator.GridCellOutOfBound': 'Selected Sentinel-2 image cell is {actual_cell}, this model is for the '
                                           'cells: {allowed_cells}',
    'source-validator.MonthOutOfBounds': 'Selected Sentinel-2 image month is {actual_month}, this model is for: '
                                         '{allowed_months}',
    'source-validator.TMSLinkFormatError': 'You request TMS basemap link doesn\'t match the format, it must be a link '
                                           'containing "x", "y", "z" placeholders, correct it and start processing '
                                           'again.',
    'source-validator.RequirementsMustBeDict': 'Requirements must be dict, got {requirements_type}.',
    'source-validator.RequestMustBeDict': 'Request must be dict, got {request_type}.',
    'source-validator.RequestMustHaveSourceType': 'Request must contain "source_type" key',
    'source-validator.SourceTypeIsNotAllowed': 'Source type {source_type} is not allowed. Use one of: '
                                               '{allowed_sources}',
    'source-validator.RequiredSectionMustBeDict': '"Required" section of the requirements must contain dict, not '
                                                  '{required_section_type}',
    'source-validator.RecommendedSectionMustBeDict': '"Recommended" section of the requirements must contain dict, '
                                                     'not {recommended_section_type}',
    'source-validator.XYZLinkFormatError': 'You XYZ basemap link doesn\'t match the format, it must be a link '
                                           'containing "x", "y", "z"  placeholders.',
    'source-validator.UnhandledException': 'Internal error in process of data source validation. We are working on '
                                           'the fix, our support will contact you.',
    'source-validator.internalError': 'Internal error in process of data source validation. We are working on the '
                                      'fix, our support will contact you.',
    'dataloader.internalError': 'Internal error in process of loading data. We are working on the fix, our support '
                                'will contact you.',
    'dataloader.UnknownSourceType': 'Wrong source type {real_source_type}. Specify one of the allowed types '
                                    '{allowed_source_types}.',
    'dataloader.MemoryLimitExceeded': 'Your data loading task requires {estimated_size} MB of memory, which exceeded '
                                      'allowed memory limit {allowed_size}',
    'dataloader.LoaderArgsError': 'Dataloader argument {argument_name} has type {argument_type}, excpected to be '
                                  '{expected_type}',
    'dataloader.WrongChannelsNum': 'Loaded tile has {real_nchannels} channels, required number is {expected_nchannels}',
    'dataloader.WrongTileSize': 'Loaded tile has size {real_size}, expected tile size is {expected_size}',
    'dataloader.TileNotLoaded': 'Tile at location {tile_location} cannot be loaded, server response is {status}',
    'dataloader.TileNotReadable': 'Response content at {tile_location} cannot be decoded as an image',
    'dataloader.CrsIsNotSupported': 'Internal error in process of loading data. We are working on the fix, our '
                                    'support will contact you.',
    'dataloader.MaploaderInternalError': 'Internal error in process of loading data. We are working on the fix, our '
                                         'support will contact you.',
    'dataloader.SentinelLoaderInternalError': 'Internal error in process of loading data. We are working on the fix, '
                                              'our support will contact you.',
    'dataloader.NoDataTile': 'The data provider contains no data for your area of interest (returned NoData tiles). '
                             'Try other the data sources to get the results.',
    'raster-processor.internalError': 'Internal error in process of data preparation. We are working on the fix, our '
                                      'support will contact you.',
    'inference.internalError': 'Internal error in process of data processing. We are working on the fix, our support '
                               'will contact you.',
    'vector-processor.internalError': 'Internal error in process of saving the results. We are working on the fix, '
                                      'our support will contact you.',
    'FileCheckFailed': 'File {filename} cannot be processed. Parameters {bad_parameters} are incompatible with our '
                       'catalog. See the documentation for more info.',
    'MemoryLimitExceeded': 'Your file has size {memory_requested} bytes, but you have only {available_memory} left. '
                           'Upgrade your subscription or remove older imagery from your catalog',
    'FileTooBig': 'Max file size allowed to upload is {max_file_size} bytes, your file is {actual_file_size} bytes '
                  'instead. Compress your file or cut it into smaller parts',
    'ItemNotFound': "{instance_type} with id: {uid} can't be found",
    'AccessDenied': 'You do not have access to {instance_type} with id {uid}',
    'FileValidationFailed': 'File {filename} cannot be uploaded to imagery collection: {mosaic_id}. {param_name} of '
                            'the file is {got_param}, it should be {expected_param} to fit the collection. Fix your '
                            'file, or upload it to another imagery collection',
    'ImageOutOfBounds': "File can't be uploaded, because its extent is out of coordinate range.Check please CRS and "
                        "transform of the image, they may be invalid",
    'FileOpenError': 'File cannot be opened as a GeoTIFF file. Only valid geotiff files are allowed for uploading. '
                     'You can use Raster->Conversion->Translate to change your file type to GeoTIFF',
    'ImageExtentTooBig': "File can't be uploaded, because the geometry of the image is too big, we will not be able "
                         "to process it properly.Make sure that your image has valid CRS and transform, or cut the "
                         "image into parts",
    'MAXAR_PROVIDERS_UNAVAILABLE': 'Upgrade your subscription to get access to Maxar imagery',
    'ProviderMinAreaError': 'Geometry area is {aoiArea} sq km, which is smaller than the minimum required area for '
                            '{providerName} data provider ({providerMinArea} sq km)',
    'TOO_LARGE_PROCESSING': 'The processing area is too large: {area} sq.m exceeds the {aoiAreaLimit} sq.m limit. '
                            'Reduce the area of interest.',
}

BY_MESSAGE: Dict[str, str] = {
    "You don't have enough limit, please contact admin!": "You don't have enough limit to create this planned "
                                                          "processing. Please contact your administrator to increase "
                                                          "the limit.",
}


class _Default(dict):
    def __missing__(self, key):
        return "?"


def describe(code: Optional[str], params: Optional[Dict[str, Any]] = None, message: Optional[str] = None) -> str:
    """A readable sentence for an error: the known template filled with its parameters, else the
    backend's own message with its parameters, else a generic line."""
    params = dict(params or {})
    if code == "TOO_LARGE_PROCESSING":
        # The backend reports square metres; people think in km²
        for key in ("area", "aoiAreaLimit"):
            try:
                params[key] = f"{float(params[key]) / 1e6:,.2f}"
            except (KeyError, TypeError, ValueError):
                pass
        return ("The area is too large: {area} km² is over the {aoiAreaLimit} km² limit of your plan. "
                "Reduce the area of interest.").format_map(_Default(params))
    template = CODES.get(code or "") or BY_MESSAGE.get(message or "")
    if template:
        try:
            return template.format(**params)
        except (KeyError, IndexError, ValueError):
            pass
    details = ", ".join(f"{key}: {value}" for key, value in params.items())
    if message and details:
        return f"{message} ({details})"
    return message or details or GENERIC
