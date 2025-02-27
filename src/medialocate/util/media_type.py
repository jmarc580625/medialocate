"""Media type classification and handling utilities.

This module provides enums, types and helper classes for working with different
media types (images, videos) and their associated formats. It includes utilities
for determining media types from file extensions and generating IANA media type strings.
"""

from enum import Enum
from typing import Dict, TypedDict
from medialocate.util.file_naming import get_extension


class MediaType(Enum):
    """Enumeration of supported media types.

    Defines the main categories of media files that can be handled by the application.
    """

    MOVIE = "movie"
    PICTURE = "image"
    UNKNOWN = "unknown"

    def toString(self) -> str:
        """Convert the media type to its string representation.

        Returns:
            str: Lowercase string representation of the media type
        """
        return self.value.lower()

    def toDict(self) -> str:
        """Convert the media type to a dictionary-friendly string.

        Returns:
            str: String representation suitable for dictionary serialization
        """
        return self.toString()


class MediaInfo(TypedDict):
    """Type definition for media information.

    Attributes:
        media_type: The type of media (movie, image, etc.)
        media_format: The specific format of the media file
    """

    media_type: MediaType
    media_format: str


class MediaTypeHelper:
    """Helper class for media type operations and lookups.

    Provides utilities for working with media types, including file extension mapping
    and IANA media type string generation.
    """

    media_types: Dict[str, MediaInfo] = {
        "3gp": {"media_type": MediaType.MOVIE, "media_format": "3gpx"},
        "avi": {"media_type": MediaType.MOVIE, "media_format": "xxx"},
        "mkv": {"media_type": MediaType.MOVIE, "media_format": "xxx"},
        "mov": {"media_type": MediaType.MOVIE, "media_format": "xxx"},
        "mp4": {"media_type": MediaType.MOVIE, "media_format": "mp4"},
        "mpeg": {"media_type": MediaType.MOVIE, "media_format": "mpeg"},
        "mpg": {"media_type": MediaType.MOVIE, "media_format": "mpeg"},
        "wmv": {"media_type": MediaType.MOVIE, "media_format": "xxx"},
        "webm": {"media_type": MediaType.MOVIE, "media_format": "xxx"},
        "gif": {"media_type": MediaType.PICTURE, "media_format": "gif"},
        "jpeg": {"media_type": MediaType.PICTURE, "media_format": "jpeg"},
        "jpg": {"media_type": MediaType.PICTURE, "media_format": "jpeg"},
        "png": {"media_type": MediaType.PICTURE, "media_format": "png"},
        "tiff": {"media_type": MediaType.PICTURE, "media_format": "tiff"},
        "webp": {"media_type": MediaType.PICTURE, "media_format": "webp"},
    }

    @classmethod
    def get_expected_extensions(cls) -> list[str]:
        """Get a list of all supported file extensions.

        Returns:
            list[str]: List of supported file extensions with leading dots
        """
        return [f".{ext}" for ext, _ in MediaTypeHelper.media_types.items()]

    @classmethod
    def get_media_type(cls, filename: str) -> MediaType:
        """Determine the media type of a file based on its extension.

        Args:
            filename: Name of the file to check

        Returns:
            MediaType: The determined media type, or UNKNOWN if not recognized
        """
        try:
            media_info = MediaTypeHelper.media_types[get_extension(filename).lower()]
            return media_info["media_type"]
        except KeyError:
            return MediaType.UNKNOWN

    @classmethod
    def get_iana_media_type(cls, filename: str) -> str:
        """Generate an IANA media type string for a file.

        Args:
            filename: Name of the file to generate media type for

        Returns:
            str: IANA media type string in format "type/format"
        """
        try:
            media_type = MediaTypeHelper.get_media_type(filename).toString()
            media_format = MediaTypeHelper.media_types[get_extension(filename).lower()][
                "media_format"
            ]
            return f"{media_type}/{media_format}"
        except (KeyError, AttributeError):
            return MediaType.UNKNOWN.toString()
