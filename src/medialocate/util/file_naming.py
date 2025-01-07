"""File naming utilities for consistent path handling and file identification.

This module provides utility functions for:
- Converting file paths between different formats (Windows, POSIX, URI)
- Generating consistent file hashes for identification
- Handling file extensions
"""

import os
import hashlib
from pathlib import Path


def to_posix(path: str) -> str:
    """Convert a file path to POSIX format.

    Args:
        filename: File path to convert

    Returns:
        str: POSIX-formatted file path
    """
    path_obj = Path(path)
    # Convertit le chemin en format POSIX
    posix_path = path_obj.as_posix()
    return posix_path


def to_uri(path: str) -> str:
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
    if path in ["", ".", "..", "c:", "C:"]:
        return ""
    if not os.path.isabs(path):
        uri = Path(path).resolve().as_uri()
        uri = uri[len(Path(".").resolve().as_uri()) + 1 :]
    else:
        uri = Path(path).resolve().as_uri()
    return uri


def get_hash(path: str) -> str:
    """Generate a SHA-256 hash of a file path.

    Args:
        filename: File path to hash

    Returns:
        str: Hexadecimal representation of the SHA-256 hash
    """
    return hashlib.md5(
        to_posix(path).encode("utf-8"), usedforsecurity=False
    ).hexdigest()


def get_extension(path: str) -> str:
    """Get the file extension from a file path.

    Args:
        filename: File path to extract extension from

    Returns:
        str: File extension including the dot (e.g., '.txt')
    """
    return Path(path).suffix[1:]
