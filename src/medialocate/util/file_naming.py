"""File naming utilities for consistent path handling and file identification.

This module provides utility functions for:
- Converting file paths between different formats (Windows, POSIX, URI)
- Generating consistent file hashes for identification
- Handling file extensions
"""

import os
import hashlib
import pathlib


def to_posix(filename: str) -> str:
    """Convert a file path to POSIX format.

    Args:
        filename: File path to convert

    Returns:
        str: POSIX-formatted file path
    """
    return pathlib.PurePath(r"{}".format(filename)).as_posix()


def to_uri(filename: str) -> str:
    """Convert a file path to URI format.

    Special cases:
    - Empty strings and special paths ('', '.', '..', 'c:', 'C:') return empty string
    - Relative paths are resolved relative to current directory
    - Absolute paths are converted directly

    Args:
        filename: File path to convert

    Returns:
        str: URI-formatted file path
    """
    if filename in ["", ".", "..", "c:", "C:"]:
        return ""
    if not os.path.isabs(filename):
        uri = pathlib.Path(filename).resolve().as_uri()
        uri = uri[len(pathlib.Path(".").resolve().as_uri()) + 1 :]
    else:
        uri = pathlib.Path(filename).resolve().as_uri()
    return uri


def get_hash(filename: str) -> str:
    """Generate a SHA-256 hash of a file path.

    Args:
        filename: File path to hash

    Returns:
        str: Hexadecimal representation of the SHA-256 hash
    """
    return hashlib.md5(
        to_posix(filename).encode("utf-8"), usedforsecurity=False
    ).hexdigest()


def get_extension(filename: str) -> str:
    """Get the file extension from a file path.

    Args:
        filename: File path to extract extension from

    Returns:
        str: File extension including the dot (e.g., '.txt')
    """
    return pathlib.Path(filename).suffix[1:]
