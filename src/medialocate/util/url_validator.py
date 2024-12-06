"""URL and path validation utilities for secure file access.

This module provides validation functions to ensure secure handling of URLs and file paths.
It implements various security checks including:
- UTF-8 encoding validation
- Control character detection
- Path traversal prevention
- URL format verification
"""

from urllib.parse import unquote, urlparse
from typing import Optional

PATH_TRAVERSAL_ATTEMPTS = ["../", "./", "//"]


def validate_query(query: str) -> tuple[bool, Optional[str], str]:
    """Validate a query string for safe usage.

    Performs security checks including:
    1. Valid UTF-8 encoding
    2. No control characters

    Args:
        query: The query string to validate

    Returns:
        tuple containing:
            - bool: True if valid, False otherwise
            - Optional[str]: Error message if invalid, None if valid
            - str: Sanitized query string
    """
    try:
        query = unquote(query, errors="strict")
    except UnicodeDecodeError:
        return (False, None, "Query contains invalid percent encoding")

    # Check for path traversal attempts
    if any(part in query for part in PATH_TRAVERSAL_ATTEMPTS):
        return (False, None, "Path traversal attempt detected")

    # Check for control characters
    if any(ord(c) < 32 for c in query):
        return (False, None, "Query contains control characters")

    return (True, query, "Valid query")


def validate_path(path: str) -> tuple[bool, Optional[str], str]:
    """Validate a file system path for secure access.

    Performs security checks including:
    1. Valid UTF-8 encoding
    2. No control characters
    3. No path traversal attempts

    Args:
        path: The file system path to validate

    Returns:
        tuple containing:
            - bool: True if valid, False otherwise
            - Optional[str]: Error message if invalid, None if valid
            - str: Sanitized path string
    """
    try:
        path = unquote(path, errors="strict")
    except UnicodeDecodeError:
        return (False, None, "Path contains invalid percent or UTF-8 encoding")

    # Check for control characters
    if any(ord(c) < 32 for c in path):
        return (False, None, "Path contains control characters")

    # Check for path traversal attempts
    if any(part in path for part in PATH_TRAVERSAL_ATTEMPTS):
        return (False, None, "Path traversal attempt detected")

    return (True, path, "Valid path")


def validate_url(url: str) -> tuple[bool, Optional[str], Optional[str], str]:
    """Validate a URL for secure usage.

    Performs comprehensive security checks including:
    1. Non-empty URL verification
    2. Valid percent encoding
    3. Valid UTF-8 encoding
    4. No control characters
    5. No path traversal attempts

    Args:
        url: The URL to validate

    Returns:
        tuple containing:
            - bool: True if valid, False otherwise
            - Optional[str]: Error message if invalid, None if valid
            - str: Sanitized URL string
    """
    try:
        # Check for empty URL
        if not url:
            return (False, None, None, "URL cannot be empty")

        # Parse URL
        parsed = urlparse(url)
        path = parsed.path
        query = parsed.query

        # Check percent encoding
        if path:
            is_valid, unquoted_path, message = validate_path(path)
            if not is_valid:
                return (is_valid, None, None, message)

        if query:
            is_valid, unquoted_query, message = validate_query(query)
            if not is_valid:
                return (is_valid, None, None, message)
            return (True, unquoted_path, unquoted_query, "Valid URL")
        else:
            return (True, unquoted_path, query, "Valid URL")

    except Exception as e:
        return (False, None, None, f"URL validation error: {str(e)}")
