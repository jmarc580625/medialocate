"""Media handling module for processing media files and metadata."""

from typing import List

from medialocate.media.group_proxy import MediaProxiesControler
from medialocate.media.location_grouping import MediaGroups
from medialocate.media.locator import MediaLocateAction

__all__: List[str] = [
    "MediaProxiesControler",
    "MediaGroups",
    "MediaLocateAction",
]  # Add your public exports here
