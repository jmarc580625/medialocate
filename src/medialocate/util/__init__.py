"""Utility package providing common functionality for MediaLocate.

This package contains various utility modules and functions used throughout the MediaLocate
application, including:
- Media type detection and handling (MediaTypeHelper, MediaType)
- File naming and path manipulation (get_extension, get_hash, to_posix, to_uri)
- URL validation and sanitization (validate_path, validate_query, validate_url)
"""

from typing import List

from medialocate.util.media_type import MediaTypeHelper
from medialocate.util.media_type import MediaType
from medialocate.util.media_type import MediaInfo
from medialocate.util.file_naming import get_extension
from medialocate.util.file_naming import get_hash
from medialocate.util.file_naming import to_posix
from medialocate.util.file_naming import to_uri
from medialocate.util.url_validator import validate_path
from medialocate.util.url_validator import validate_query
from medialocate.util.url_validator import validate_url


__all__: List[str] = [
    "MediaTypeHelper",
    "MediaType",
    "MediaInfo",
    "get_extension",
    "get_hash",
    "to_posix",
    "to_uri",
    "validate_path",
    "validate_query",
    "validate_url",
]  # Add your public exports here
