from .error_message_list import ErrorMessageList
from ..config import Config


class DataErrors(ErrorMessageList):
    def __init__(self):
        super().__init__()
        self.error_descriptions = {
            "FileCheckFailed": self.tr("File {filename} cannot be processed. "
                                       "Parameters {bad_parameters} are incompatible with our catalog. "
                                       "See the documentation for more info."),
            "MemoryLimitExceeded": self.tr("Your file has size {memory_requested} bytes, "
                                           "but you have only {available_memory} left. "
                                           "Upgrade your subscription or remove older imagery from your catalog"),
            "FileTooBig": self.tr("Max file size allowed to upload is {max_file_size} bytes, "
                                  "your file is {actual_file_size} bytes instead. "
                                  "Compress your file or cut it into smaller parts"),
            "ItemNotFound": self.tr("{instance_type} with id: {uid} can't be found"),
            "AccessDenied": self.tr("You do not have access to {instance_type} with id {uid}"),
            "FileValidationFailed": self.tr("File {filename} cannot be uploaded to mosaic: {mosaic_id}. "
                                            "{param_name} of the file is {got_param}, "
                                            "it should be {expected_param} to fit the mosaic. "
                                            "Fix your file, or upload it to another mosaic"),
            "ImageOutOfBounds": self.tr("File can't be uploaded, because its extent is out of coordinate range."
                                        "Check please CRS and transform of the image, they may be invalid"),
            "FileOpenError": self.tr("File cannot be opened as a GeoTIFF file. "
                                     "Only valid geotiff files are allowed for uploading. "
                                     "You can use Raster->Conversion->Translate to change your file type to GeoTIFF"),
            "ImageExtentTooBig": self.tr("File can't be uploaded, because the geometry of the image is too big,"
                                         " we will not be able to process it properly."
                                         "Make sure that your image has valid CRS and transform, "
                                         "or cut the image into parts"
                                         )


        }