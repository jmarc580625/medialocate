"""Media file location and metadata handling module.

This module provides functionality for locating media files, extracting their GPS
metadata using ExifTool, and managing media file types. It supports various media
formats including pictures and movies, with capabilities for GPS data extraction
and media type classification.
"""

import os
import shutil
import logging
import subprocess  # nosec B404 - subprocess usage is required and secured
from enum import Enum
from typing import Optional, Any
from pathlib import PurePath
from exiftool import ExifToolHelper  # type: ignore[import-untyped]
from medialocate.media.parameters import (
    MEDIALOCATION_STORE_NAME,
    MEDIALOCATION_STORE_PATH,
    MEDIALOCATION_RES_DIR,
    MEDIALOCATION_PAGE_DATA,
)
from medialocate.store.dict import DictStore
from medialocate.location.gps import GPS
from medialocate.util.file_naming import relative_path_to_uri


class MediaType(Enum):
    """Enumeration of supported media file types.

    Attributes:
        MOVIE: Video media files
        PICTURE: Image media files
        UNKNOWN: Unrecognized media types
    """

    MOVIE = "movie"
    PICTURE = "picture"
    UNKNOWN = "unknown"

    def toString(self) -> str:
        """Convert media type to lowercase string.

        Returns:
            String representation of the media type
        """
        return self.name.lower()

    def toDict(self) -> str:
        """Convert media type to dictionary format.

        Returns:
            String representation for dictionary storage
        """
        return self.toString()


class DataTag:
    """Container for media file metadata and location information.

    Attributes:
        mediasource: Source path of the media file
        mediathumbnail: Path to the media thumbnail
        mediaformat: Format/extension of the media file
        mediatype: Type of media (movie, picture, etc.)
        gps: GPS coordinates of the media location
    """

    def __init__(self):
        """Initialize DataTag instance."""
        self.mediasource = ""
        self.mediathumbnail = ""
        self.mediaformat = ""
        self.mediatype = MediaType.UNKNOWN
        self.gps = GPS(0, 0)

    def toDict(self) -> dict[str, Any]:
        """Convert data tag to dictionary format.

        Returns:
            Dictionary containing all metadata fields
        """
        return {
            "mediasource": self.mediasource,
            "mediathumbnail": self.mediathumbnail,
            "mediaformat": self.mediaformat,
            "mediatype": self.mediatype.toString(),
            "gps": self.gps.toDict(),
        }


class ExifKey(Enum):
    """Enumeration of EXIF metadata keys for GPS data.

    Attributes:
        LATITUDE: EXIF key for GPS latitude
        LONGITUDE: EXIF key for GPS longitude
    """

    LATITUDE = "Composite:GPSLatitude"
    LONGITUDE = "Composite:GPSLongitude"

    def toString(self) -> str:
        """Convert EXIF key to string.

        Returns:
            String representation of the EXIF key
        """
        return self.value

    def toDict(self) -> str:
        """Convert EXIF key to dictionary format.

        Returns:
            String representation for dictionary storage
        """
        return self.toString()


class MediaLocateAction:
    """Core class for media file location and metadata processing.

    Handles media file processing, GPS data extraction, and resource management.
    Uses ExifTool for metadata extraction and supports various media formats.

    Attributes:
        working_directory: Base directory for processing
        out_file: Output file path
        log: Logger instance
        store: Dictionary store for data
        ressources_path: Path to resource files
        exiftool: ExifTool helper instance
    """

    LOGGER_NAME = "MediaLocateAction"
    STORE_NAME = MEDIALOCATION_STORE_NAME
    RESSOURCE_DIR_NAME = MEDIALOCATION_RES_DIR
    PROLOG_RESSOURCE_NAME = "prolog.html"
    EPILOG_RESSOURCE_NAME = "epilog.html"
    DATA_APPENDIX_NAME = MEDIALOCATION_STORE_PATH

    class GPSExtractionError(Exception):
        """Exception raised when GPS data extraction fails.

        This exception is raised when GPS coordinates cannot be extracted
        from a media file's EXIF data, either due to missing data or
        invalid coordinates.
        """

    def __init__(
        self,
        working_directory: str,
        outfile: str,
        parent_logger: Optional[str] = None,
    ) -> None:
        """Initialize MediaLocateAction instance.

        Args:
            working_directory: Base directory for processing
            outfile: Output file path
            parent_logger: Optional parent logger name
        """
        self.working_directory = working_directory
        self.out_file = outfile
        self.log = logging.getLogger(
            ".".join(filter(None, [parent_logger, MediaLocateAction.LOGGER_NAME]))
        )
        self.store = DictStore(self.working_directory, MediaLocateAction.STORE_NAME)
        self.store.open()
        self.ressources_path = os.path.join(
            os.path.dirname(__file__), MediaLocateAction.RESSOURCE_DIR_NAME
        )
        self.prolog_resource_path = os.path.join(
            self.ressources_path, MediaLocateAction.PROLOG_RESSOURCE_NAME
        )
        self.epilog_resource_path = os.path.join(
            self.ressources_path, MediaLocateAction.EPILOG_RESSOURCE_NAME
        )
        self.data_appendix_path = os.path.join(
            self.working_directory, MEDIALOCATION_PAGE_DATA
        )
        self.thrird_party_path: dict[str, str] = {}
        self.exiftool: Optional[ExifToolHelper] = None

    def __call__(self, file_to_process: str, file_status: str) -> int:
        """Process a media file when instance is called as a function.

        Args:
            file_to_process: Path to media file
            file_status: Status file path

        Returns:
            Processing result code
        """
        return self.process(file_to_process, file_status)

    def __enter__(self) -> "MediaLocateAction":
        """Enter context manager.

        Returns:
            Self instance
        """
        return self

    def __exit__(self, *args) -> None:
        """Exit context manager and cleanup resources."""
        self.store.close()
        if self.exiftool is not None:
            self.exiftool.terminate()

    def terminate(self) -> None:
        """Terminate the action."""
        self.__exit__()

    def get_gps_data(self, file_to_process: str) -> GPS:
        """Extract GPS coordinates from media file's EXIF data.

        Args:
            file_to_process: Path to media file

        Returns:
            GPS coordinates from EXIF data

        Raises:
            GPSExtractionError: If GPS data is missing or invalid
        """
        # Validate exiftool is installed
        # Ignore return value, only need side effect of setting thrird_party_path
        _ = self._get_third_party_path("exiftool")

        if self.exiftool is None:
            self.exiftool = ExifToolHelper()

        try:
            metadata = self.exiftool.get_tags(
                file_to_process, tags=[ExifKey.LATITUDE.value, ExifKey.LONGITUDE.value]
            )
            if metadata and len(metadata) > 0:
                data = metadata[0]
                if ExifKey.LATITUDE.value in data and ExifKey.LONGITUDE.value in data:
                    latitude = float(data[ExifKey.LATITUDE.value])
                    longitude = float(data[ExifKey.LONGITUDE.value])
                    if latitude == 0 and longitude == 0:
                        raise MediaLocateAction.GPSExtractionError(
                            "Invalid GPS coordinates (0,0)"
                        )
                    self.log.info(f"GPS coordinates found: {latitude}, {longitude}")
                    return GPS(latitude, longitude)
            raise MediaLocateAction.GPSExtractionError("No GPS data found")
        except Exception as e:
            raise MediaLocateAction.GPSExtractionError(
                f"Failed to extract GPS data: {str(e)}"
            )

    media_types = {
        "3gp": MediaType.MOVIE,
        "avi": MediaType.MOVIE,
        "mkv": MediaType.MOVIE,
        "mov": MediaType.MOVIE,
        "mp4": MediaType.MOVIE,
        "mpeg": MediaType.MOVIE,
        "mpg": MediaType.MOVIE,
        "wmv": MediaType.MOVIE,
        "webm": MediaType.MOVIE,
        "gif": MediaType.PICTURE,
        "jpeg": MediaType.PICTURE,
        "jpg": MediaType.PICTURE,
        "png": MediaType.PICTURE,
        "tiff": MediaType.PICTURE,
        "webp": MediaType.PICTURE,
    }

    @classmethod
    def get_expected_extensions(cls) -> list[str]:
        """Get list of supported media file extensions.

        Returns:
            List of supported file extensions with leading dot
        """
        return [f".{ext}" for ext in cls.media_types.keys()]

    @classmethod
    def get_filename_extension(cls, filename: str) -> str:
        """Extract file extension from filename.

        Args:
            filename: Name of the file

        Returns:
            Lowercase extension without leading dot
        """
        return os.path.splitext(filename)[1][1:].lower()

    @classmethod
    def get_media_type(cls, extension: str) -> MediaType:
        """Determine media type from file extension.

        Args:
            extension: File extension to check

        Returns:
            MediaType enum value for the extension
        """
        return cls.media_types.get(extension, MediaType.UNKNOWN)

    def _get_third_party_path(self, package_name: str) -> Optional[str]:
        """Get the full path to a third-party executable.

        Args:
            package_name: Name of the executable to find

        Returns:
            Full path to executable or None if not found
        """
        if package_name in self.thrird_party_path:
            return self.thrird_party_path[package_name]

        try:
            # Use shutil.which for cross-platform path resolution
            package_path = shutil.which(package_name)
            if package_path:
                # Validate path exists and is executable
                abs_path = os.path.abspath(package_path)
                if os.path.isfile(abs_path) and os.access(abs_path, os.X_OK):
                    self.thrird_party_path[package_name] = abs_path
                    return abs_path

            self.log.error(f"{package_name} not found in PATH or not executable")
            return None

        except Exception as e:
            self.log.error(f"Error finding {package_name}: {str(e)}")
            return None

    def generate_thumbnail(self, filename: str, thumbnail_name: str) -> bool:
        """Generate a thumbnail for a video or picture file.

        Args:
            filename: Path to media file
            thumbnail_name: Path to output thumbnail

        Returns:
            True if thumbnail was generated, False otherwise
        """
        try:
            # Get and validate ffmpeg path
            ffmpeg_path = self._get_third_party_path("ffmpeg")
            if not ffmpeg_path:
                self.log.error("ffmpeg not found or not executable")
                return False

            # Validate input and output paths
            abs_filename = os.path.abspath(filename)
            abs_thumbnail = os.path.abspath(thumbnail_name)
            if not os.path.isfile(abs_filename):
                self.log.error(f"Input file does not exist: {abs_filename}")
                return False

            # Ensure output directory exists
            os.makedirs(os.path.dirname(abs_thumbnail), exist_ok=True)

            # Build ffmpeg command with security measures
            result = subprocess.run(  # nosec B603 - command args are validated
                [
                    ffmpeg_path,
                    "-hide_banner",
                    "-v",
                    "quiet",
                    "-nostdin",
                    "-i",
                    abs_filename,
                    "-vf",
                    "thumbnail,scale=w=128:h=-1",
                    "-frames:v",
                    "1",
                    abs_thumbnail,
                ],
                check=True,
                capture_output=True,
                text=True,
                shell=False,
                timeout=30,  # 30 second timeout for thumbnail generation
            )
            return result.returncode == 0

        except subprocess.TimeoutExpired:
            self.log.error("Thumbnail generation timed out")
            return False
        except subprocess.CalledProcessError as e:
            self.log.error(f"Failed to generate thumbnail: {e.stderr}")
            return False
        except Exception as e:
            self.log.error(f"Unexpected error generating thumbnail: {str(e)}")
            return False

    def create_thumb_from_media(
        self,
        filename: str,
        media_type: MediaType,
        thumbnail_name: str,
    ) -> bool:
        """Create thumbnail for media file.

        Args:
            filename: Path to media file
            media_type: Type of media
            thumbnail_name: Path to output thumbnail

        Returns:
            True if thumbnail was generated, False otherwise
        """
        if media_type in [MediaType.MOVIE, MediaType.PICTURE]:
            return self.generate_thumbnail(filename, thumbnail_name)
        return False

    def copy_location_page_appendices_and_get_associated_html_links(
        self, file_extension: str, template: str
    ) -> str:
        """Copy location page appendices and generate HTML links.

        Args:
            file_extension: File extension to process
            template: HTML template for links

        Returns:
            HTML snippet with links to appended files
        """
        snippet = ""
        for source in os.listdir(self.ressources_path):
            if source.endswith(file_extension):
                target_path = os.path.join(self.working_directory, source)
                source_path = os.path.join(self.ressources_path, source)
                snippet += template.format(path=PurePath(target_path).as_posix())
                if not os.path.exists(target_path) or os.path.getmtime(
                    target_path
                ) < os.path.getmtime(source_path):
                    with open(target_path, "w") as f_out:
                        with open(source_path, "r") as f_in:
                            f_out.write(f_in.read())
        return snippet

    def create_location_page(self) -> Optional[str]:
        """Create location page from processed media data.

        Returns:
            Path to generated location page or None if not created
        """
        if len(self.store) > 0 and self.store._touched:
            # copy a fresh version of the stylesheet and script appendices files if needed
            stylesheet_link_template = """<link rel = "stylesheet" href = "{path}">"""
            html_stylesheet_snippet = (
                self.copy_location_page_appendices_and_get_associated_html_links(
                    ".css", stylesheet_link_template
                )
            )
            script_link_template = """<script src = "{path}"></script>"""
            html_script_snippet = (
                self.copy_location_page_appendices_and_get_associated_html_links(
                    ".js", script_link_template
                )
            )

            # generates medialocation data/script appendix file if needed
            data_link_template = (
                """<script type="text/javascript" src="{path}" class="json"></script>"""
            )
            html_script_snippet += data_link_template.format(
                path=PurePath(self.data_appendix_path).as_posix()
            )
            if self.store._touched:
                self.store.sync()
                with open(self.data_appendix_path, "w") as destination:
                    with open(self.store.get_path(), "r") as source:
                        destination.write("medialocate_data=")
                        destination.write(source.read())
                        destination.write(";")

            # generates the location page if needed
            if (
                not os.path.exists(self.out_file)
                or os.path.getmtime(self.out_file)
                < os.path.getmtime(self.prolog_resource_path)
                or os.path.getmtime(self.out_file)
                < os.path.getmtime(self.epilog_resource_path)
            ):
                with open(self.out_file, "w") as f:
                    with open(self.prolog_resource_path, "r") as html_prolog:
                        html_prolog_template = html_prolog.read()
                        f.write(
                            html_prolog_template.format(
                                stylesheets=html_stylesheet_snippet,
                                scripts=html_script_snippet,
                            )
                        )
                    with open(self.epilog_resource_path, "r") as html_epilog:
                        f.write(html_epilog.read())

            return self.out_file
        else:
            return None

    def process(self, file_to_process: str, hash: str) -> int:
        """Process a media file to extract and store its metadata.

        Args:
            file_to_process: Path to media file
            hash: Hash value for media file

        Returns:
            0 on success, non-zero on error
        """
        try:
            gps = self.get_gps_data(file_to_process)

            media_format = MediaLocateAction.get_filename_extension(file_to_process)
            media_type = MediaLocateAction.get_media_type(media_format)
            thumb_filename = os.path.join(self.working_directory, f"{hash}.jpg")

            if self.create_thumb_from_media(
                file_to_process, media_type, thumb_filename
            ):
                data_tag = DataTag()

                data_tag.mediasource = relative_path_to_uri(file_to_process)
                data_tag.mediathumbnail = relative_path_to_uri(thumb_filename)

                data_tag.mediaformat = media_format
                data_tag.mediatype = media_type
                data_tag.gps = gps

                self.store.set(hash, data_tag.toDict())
                return 0

            else:
                raise Exception(f"{file_to_process} : thumbnail creation failed")

        except MediaLocateAction.GPSExtractionError as e:
            self.log.warning(f"{file_to_process} : {e}")
            return 1

        except Exception as e:
            self.log.error(f"{file_to_process} : processing failed {e}")
            return 10
