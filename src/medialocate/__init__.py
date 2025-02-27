"""MediaLocate - A tool for analyzing and grouping media files based on geolocation data.

This package provides independent command-line tools for:
1. Locating media files in a directory structure
2. Grouping media files based on location
3. Processing media files
4. Proxy media operations
"""

__version__ = "0.1.0"

# Expose modules, avoiding direct function imports that might cause issues
from . import locate_media, group_media, process_files, proxy_media


# Optional: Provide a way to access main functions if needed
def get_module_main(module_name):
    """
    Retrieve the main function for a given module.

    Args:
        module_name (str): Name of the module to get main function from.

    Returns:
        function: The main function of the specified module.
    """
    module = {
        "locate_media": locate_media,
        "group_media": group_media,
        "process_files": process_files,
        "proxy_media": proxy_media,
    }.get(module_name)

    if module and hasattr(module, "main"):
        return module.main
    return None
