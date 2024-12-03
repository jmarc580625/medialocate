"""URL validation utilities."""

from urllib.parse import quote, unquote, urlparse
import re

def validate_query(query: str) -> tuple[bool, str]:
    """
    Validate query for:
    1. Valid UTF-8 encoding
    2. No control characters
    
    Args:
        query: The file system path to validate
        
    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """

    try:
        query = unquote(query, errors='strict')
    except UnicodeDecodeError:
        return False, "Query contains invalid percent encoding"

    # Check for path traversal attempts
    if any(part in query for part in ['..', './', '//']):
        return False, "Path traversal attempt detected"
        
    # Check for control characters
    if any(ord(c) < 32 for c in query):
        return False, "Query contains control characters"

    return True, "Valid query"

def validate_path(path: str) -> tuple[bool, str]:
    """
    Validate a file system path for:
    1. Valid UTF-8 encoding
    2. No control characters
    3. No path traversal attempts
    
    Args:
        path: The file system path to validate
        
    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    try:
        path = unquote(path, errors='strict')
    except UnicodeDecodeError:
        return False, "Path contains invalid percent or UTF-8 encoding"

    # Check for control characters
    if any(ord(c) < 32 for c in path):
        return False, "Path contains control characters"

    # Check for path traversal attempts
    if any(part in path for part in ['..', './', '//']):
        return False, "Path traversal attempt detected"
        
    return True, "Valid path"

def validate_url(url: str) -> tuple[bool, str]:
    """
    Validate a URL for:
    1. Not empty
    2. Valid percent encoding
    3. Valid UTF-8 encoding
    4. No control characters
    5. No path traversal attempts
    
    Args:
        url: The URL to validate
        
    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    try:
        # Check for empty URL
        if not url:
            return False, "URL cannot be empty"
            
        # Parse URL
        parsed = urlparse(url)
        path = parsed.path
        query = parsed.query
            
        # Check percent encoding
        if path:
            is_valid, message = validate_path(path)
            if not is_valid:
                return is_valid, message

        if query:
            is_valid, message = validate_query(query)
            if not is_valid:
                return is_valid, message
                
        return True, "Valid URL"
        
    except Exception as e:
        return False, f"URL validation error: {str(e)}"

