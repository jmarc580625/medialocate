"""File naming utilities for consistent path handling and file identification.

This module provides utility functions for:
- Converting file paths between different formats (Windows, POSIX, URI)
- Generating consistent file hashes for identification
- Handling file extensions
"""

import os
import hashlib
import urllib.parse
from pathlib import Path


def relative_path_to_posix(path: str) -> str:
    """Convert a relative path to POSIX format.

    Uses pathlib.Path to handle path conversion in a platform-independent way.

    Args:
        path: File path to convert. must be a relative path

    Returns:
        str: POSIX-formatted file path with forward slashes

    Raises:
        ValueError: If path is absolute, empty, or a special path
    """
    if path in ["", ".", "..", "/", "\\"]:
        raise ValueError("Path must contain filename")

    if os.path.isabs(path) or path.startswith("/") or path.startswith("\\"):
        raise ValueError("Path must be relative")

    drive, path = os.path.splitdrive(path)
    if drive:
        raise ValueError("Path must not contain drive letter")

    path_obj = Path(path)
    return path_obj.as_posix()


def to_posix(path: str) -> str:
    """Convert a file path to POSIX format.

    DEPRECATED - USE relativepath_to_posix AND relativepath_to_uri INSTEAD
    Uses pathlib.Path to handle path conversion in a platform-independent way.
    Always returns forward slashes, regardless of the operating system.
    For Windows paths, keeps the drive letter (e.g., 'C:/Users/test').

    Args:
        path: File path to convert

    Returns:
        str: POSIX-formatted file path with forward slashes
    """
    path_obj = Path(path)
    return path_obj.as_posix()


def relative_path_to_uri(path: str) -> str:
    """Encode a file path for use in a URI.

    Args:
        path: File path to encode

    Returns:
        str: Encoded file path
    """
    normalized_path = relative_path_to_posix(path)

    unreserved_characters = "/"

    # encode each character except unreserved characters
    encoded_path = "".join(
        urllib.parse.quote(char) if char not in unreserved_characters else char
        for char in normalized_path
    )

    return encoded_path


def to_uri(path: str) -> str:
    """Convert a file path to URI format.

    DEPRECATED - USE relativepath_to_uri INSTEAD
    Special cases:
    - Empty strings and special paths ('', '.', '..', 'c:', 'C:') return empty string
    - Relative paths are resolved relative to current directory
    - Absolute paths are converted directly

    Args:
        path: File path to convert

    Returns:
        str: URI-formatted file path
    """
    if path in ["", ".", "..", "c:", "C:"]:
        return ""
    if not os.path.isabs(path):
        uri = Path(path).resolve().as_uri()
        uri = uri[len(Path(".").resolve().as_uri()) + 1 :]
    else:
        uri = Path(path).resolve().as_uri()

    return uri


def get_hash_from_relative_path(path: str) -> str:
    """Generate a SHA-256 hash of a file path.

    This function generates a SHA-256 hash of a file path, which is useful for
    generating unique identifiers for files and directories in a consistent manner, even
    across different operating systems.
    To ensure cross-platform compatibility, the relative path is required.

    Args:
        path: File path to hash

    Returns:
        str: Hexadecimal representation of the SHA-256 hash
    """
    normalized_path = relative_path_to_posix(path)
    return hashlib.md5(
        normalized_path.encode("utf-8"), usedforsecurity=False
    ).hexdigest()


def get_hash_from_native_path(path: str) -> str:
    """Generate a SHA-256 hash of a file path.

    This function generates a SHA-256 hash of a file path, which is useful for
    generating unique identifiers for files and directories in a consistent manner,
    in a given operating systems.

    Args:
        path: File path to hash

    Returns:
        str: Hexadecimal representation of the SHA-256 hash
    """
    return hashlib.md5(path.encode("utf-8"), usedforsecurity=False).hexdigest()


def get_extension(path: str) -> str:
    """Get the file extension from a file path.

    Args:
        filename: File path to extract extension from

    Returns:
        str: File extension including the dot (e.g., '.txt')
    """
    return Path(path).suffix[1:]
