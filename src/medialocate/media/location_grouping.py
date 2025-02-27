"""Media file grouping based on geolocation data.

This module provides functionality for grouping media files based on their GPS coordinates.
It implements clustering algorithms to group nearby media files together, allowing for
organization of media collections by location.
"""

import logging
from typing import Optional
from medialocate.location.gps import GPS


class MediaGroups:
    """Container for managing groups of media files based on location data.

    This class provides functionality to:
    - Create and manage groups of media files
    - Group media files based on GPS proximity
    - Convert groups to/from dictionary format for serialization
    """

    class Group:
        """Represents a group of media files sharing a common location.

        Attributes:
            gps: GPS coordinates representing the group's location
            media_keys: List of media file identifiers in this group
        """

        gps: GPS
        media_keys: list[str]

        def __init__(self, gps: GPS, keys: list[str]) -> None:
            """Initialize a new media group.

            Args:
                gps: GPS coordinates for the group
                keys: List of media file identifiers
            """
            self.gps = gps
            self.media_keys = keys

        def toDict(self) -> dict:
            """Convert group data to dictionary format.

            Returns:
                Dictionary containing GPS coordinates and media keys
            """
            return {"gps": self.gps.toDict(), "media_keys": self.media_keys}

        @classmethod
        def fromDict(cls, d: dict) -> "MediaGroups.Group":
            """Create a Group instance from dictionary data.

            Args:
                d: Dictionary containing group data

            Returns:
                New Group instance
            """
            gps = GPS.fromDict(d["gps"])
            media_keys = d["media_keys"]
            return cls(gps, media_keys)

    grouping_threshold: (
        float  # threshold distance to group media locations expressed in km
    )
    groups: list["MediaGroups.Group"]  # list of gps coordinates representing groups
    log = logging.getLogger(__name__)

    def __init__(
        self,
        grouping_threshold: float,
        groups: Optional[list["MediaGroups.Group"]] = None,
    ) -> None:
        """Initialize a new MediaGroups instance.

        Args:
            grouping_threshold: Maximum distance in km for grouping media
            groups: Optional list of existing groups
        """
        self.grouping_threshold = grouping_threshold
        self.groups = groups if groups is not None else []

    def toDict(self) -> dict:
        """Convert media groups data to dictionary format.

        Returns:
            Dictionary containing grouping threshold and groups data
        """
        return {
            "grouping_threshold": self.grouping_threshold,
            "groups": [group.toDict() for group in self.groups],
        }

    @classmethod
    def fromDict(cls, d: dict) -> "MediaGroups":
        """Create a MediaGroups instance from dictionary data.

        Args:
            d: Dictionary containing media groups data

        Returns:
            New MediaGroups instance
        """
        return cls(
            grouping_threshold=d["grouping_threshold"],
            groups=[MediaGroups.Group.fromDict(group) for group in d["groups"]],
        )

    def add_locations(self, locations: dict[str, dict]) -> None:
        """Add new media locations to existing groups.

        Groups media locations based on GPS proximity using the grouping threshold.
        Updates group barycenters when new locations are added to existing groups.

        Args:
            locations: Dictionary mapping location keys to location data
        """
        for location_key, location_desc in locations.items():
            try:
                location_gps = GPS(
                    location_desc["gps"]["latitude"], location_desc["gps"]["longitude"]
                )
            except (ValueError, TypeError, KeyError) as e:
                self.log.warning(
                    "Invalid GPS coordinates for media location "
                    f"{location_key}: {e.__class__.__name__} {e}"
                )
                continue
            groups_found = [
                i
                for i in range(len(self.groups))
                if self.groups[i].gps.distance_to(location_gps)
                < self.grouping_threshold
            ]

            if groups_found:
                for i in groups_found:
                    barycenter = self.groups[i].gps.barycenter_to(
                        location_gps, len(self.groups[i].media_keys)
                    )
                    media_keys = self.groups[i].media_keys.copy()
                    media_keys.append(location_key)
                    del self.groups[i]
                    self.groups.append(MediaGroups.Group(barycenter, media_keys))
            else:
                self.groups.append(MediaGroups.Group(location_gps, [location_key]))

    def get_groups_gps(self) -> list[GPS]:
        """Get list of GPS coordinates for all groups.

        Returns:
            List of GPS coordinates representing group locations
        """
        return [group.gps for group in self.groups] if self.groups else []
