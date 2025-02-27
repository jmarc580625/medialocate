"""Media group proxy management and location-based grouping.

This module provides functionality for managing media group proxies and their
location-based relationships. It includes classes for handling proxy thresholds,
GPS matches, and group location data.
"""

import os
import json
import time
import logging
from typing import Optional, Dict, List, Tuple, Any
from medialocate.media.parameters import (
    MEDIALOCATION_DIR,
    MEDIAPROXIES_STORE_PATH,
    MEDIAGROUPS_STORE_NAME,
    MEDIAGROUPS_STORE_PATH,
)
from medialocate.location.gps import GPS
from medialocate.media.location_grouping import MediaGroups


class Proxy:
    """A proxy representation for location-based media grouping.

    This class manages proxy thresholds and GPS location matches for media groups,
    tracking the relationships between different GPS coordinates within the
    threshold distance.

    Attributes:
        proxy_threshold: Maximum distance for considering locations as proximate
        proxy_matches: List of tuples containing a GPS point and its matching points
        last_update: Timestamp of the last proxy update
    """

    proxy_threshold: float
    proxy_matches: List[Tuple[GPS, List[GPS]]]
    last_update: float

    def __init__(
        self,
        proxy_threshold: float,
        matches: List[Tuple[GPS, List[GPS]]] = [],
        timestamp: Optional[float] = None,
    ) -> None:
        """Initialize a new Proxy instance.

        Args:
            proxy_threshold: Maximum distance for proximity matching
            matches: Initial list of GPS matches
            timestamp: Optional timestamp for last update
        """
        self.proxy_threshold = proxy_threshold
        self.proxy_matches = matches
        self.last_update = time.time() if timestamp is None else timestamp

    def toDict(self) -> Dict[str, Any]:
        """Convert proxy data to dictionary format.

        Returns:
            Dictionary containing proxy threshold, matches, and timestamp
        """
        return {
            "proxy_threshold": self.proxy_threshold,
            "proxy_matches": [
                (gps.toDict(), [gps.toDict() for gps in gps_list])
                for gps, gps_list in self.proxy_matches
            ],
            "last_update": self.last_update,
        }

    @classmethod
    def fromDict(cls, d: Dict[str, Any]) -> "Proxy":
        """Create a Proxy instance from dictionary data.

        Args:
            d: Dictionary containing proxy data

        Returns:
            New Proxy instance
        """
        return Proxy(
            d["proxy_threshold"],
            matches=[
                (GPS.fromDict(gps), [GPS.fromDict(gps) for gps in gps_list])
                for gps, gps_list in d["proxy_matches"]
            ],
            timestamp=d["last_update"],
        )


class MediaProxies:
    """Container for managing multiple media proxies.

    Handles the storage and retrieval of proxy relationships between different
    media groups based on their GPS locations.

    Attributes:
        label: Identifier for the media proxy group
        proxies: Dictionary mapping labels to Proxy instances
        group_locations: List of GPS coordinates for the group

    TODO:
        refresh proxies when gps list changes (remember last gps list update)
    """

    def __init__(
        self,
        label: str,
        group_locations: List[GPS] = [],
        proxies: Dict[str, Proxy] = {},
    ) -> None:
        """Initialize a new MediaProxies instance.

        Args:
            label: Group identifier
            group_locations: List of GPS coordinates
            proxies: Dictionary of proxy relationships
        """
        self.label = label
        self.proxies = proxies
        self.group_locations = group_locations  # transient field

    def toDict(self) -> Dict[str, Any]:
        """Convert media proxies data to dictionary format.

        Returns:
            Dictionary containing label and proxy data
        """
        return {
            "label": self.label,
            # 'group_locations' is not duplicated, it must be retrieved from its own store
            "proxies": {label: proxy.toDict() for label, proxy in self.proxies.items()},
        }

    @classmethod
    def fromDict(cls, d: Dict[str, Any]) -> "MediaProxies":
        """Create a MediaProxies instance from dictionary data.

        Args:
            d: Dictionary containing media proxies data

        Returns:
            New MediaProxies instance
        """
        return MediaProxies(
            d["label"],
            proxies={
                label: Proxy.fromDict(proxy) for label, proxy in d["proxies"].items()
            },
        )

    def find_proxies(
        self,
        label: str,
        proxy_threshold: float,
        gps_list: List[GPS],
        last_update: float,
        force: float = False,
    ) -> int:
        """Find proximate GPS locations within threshold distance.

        Args:
            label: Group identifier to search for
            proxy_threshold: Maximum distance for proximity
            gps_list: List of GPS coordinates to check
            last_update: Timestamp of last update
            force: Force update regardless of timestamp

        Returns:
            Number of proximate locations found, or negative values for special cases:
            -2: no proxy for self
            -1: GPS list unmodified since last search
        """
        if label == self.label:
            return -2  # no proxy for self
        else:
            if (
                label in self.proxies
                and last_update < self.proxies[label].last_update
                and not force
            ):
                return -1  # gps list unmodified since last proxy search

        proxy = Proxy(proxy_threshold)
        found_number = 0
        for one_of_my_group in self.group_locations:
            found = [
                gps
                for gps in gps_list
                if gps.distance_to(one_of_my_group) < proxy_threshold
            ]
            if found:
                proxy.proxy_matches.append((one_of_my_group, found))
                found_number += len(found)

        self.proxies[label] = proxy

        return found_number


class MediaProxiesControler:
    """Controller for managing media proxies persistence and operations.

    Handles the loading, saving, and manipulation of media proxies data,
    including file-based storage and proxy relationship calculations.

    Attributes:
        working_directory: Base directory for data storage
        log: Logger instance
        proxy_store_name: Path to proxy data storage
        proxies: Current MediaProxies instance
        updated: Flag indicating if data has been modified
    """

    LOGGER_NAME = "MediaProxiesControler"

    def __init__(
        self,
        working_directory: str,
        parent_logger: Optional[str] = None,
    ) -> None:
        """Initialize a new MediaProxiesControler instance.

        Args:
            working_directory: Base directory for data storage
            parent_logger: Optional parent logger name
        """
        self.working_directory = working_directory
        self.log = logging.getLogger(
            ".".join(filter(None, [parent_logger, MediaProxiesControler.LOGGER_NAME]))
        )
        self.proxy_store_name = os.path.join(
            self.working_directory, MEDIAPROXIES_STORE_PATH
        )
        self.proxies: Optional[MediaProxies] = None
        self.updated = False

    def __enter__(self) -> "MediaProxiesControler":
        """Enter context manager and open proxy data.

        Returns:
            Self instance
        """
        self.open()
        return self

    def __exit__(self, *args) -> None:
        """Exit context manager and commit changes."""
        self.commit()

    def open(self) -> None:
        """Load proxy data from storage.

        Raises:
            Exception: If error occurs during data loading
        """
        working_directory = os.path.join(self.working_directory, MEDIALOCATION_DIR)
        if not os.path.exists(working_directory):
            self.log.info(f"{working_directory} does not exist, ignored")
            return
        elif not os.path.isdir(working_directory):
            self.log.info(f"{working_directory} is not a directory, ignored")
            return

        try:
            groups_store = os.path.join(working_directory, MEDIAGROUPS_STORE_NAME)
            with open(groups_store, "r") as f:
                media_groups = MediaGroups.fromDict(json.load(f))
        except Exception as e:
            raise Exception(f"Error while loading groups store {groups_store}: {e}")

        name = os.path.basename(os.path.realpath(self.working_directory))
        if not os.path.exists(self.proxy_store_name):
            self.log.info(f"{name} no proxy data available, creating new one")
            self.proxies = MediaProxies(name)
            self.proxies.group_locations = media_groups.get_groups_gps()
        else:
            try:
                with open(self.proxy_store_name, "r") as f:
                    self.proxies = MediaProxies.fromDict(json.load(f))
                self.proxies.group_locations = media_groups.get_groups_gps()
            except Exception as e:
                raise Exception(
                    f"Error while loading proxies store {self.proxy_store_name}: {e}"
                )

    def commit(self) -> bool:
        """Save proxy data to storage if modified.

        Returns:
            True if data was saved, False otherwise
        """
        if self.proxies is not None and self.updated:
            with open(self.proxy_store_name, "w") as f:
                json.dump(self.proxies.toDict(), f, indent=2)
            return True
        return False

    def find_proxies(
        self, groups_path: str, proxy_threshold: float, force: bool = False
    ) -> int:
        """Find proximate media groups within threshold distance.

        Args:
            groups_path: Path to media groups data
            proxy_threshold: Maximum distance for proximity
            force: Force update regardless of timestamp

        Returns:
            Number of proximate groups found
        """
        if self.proxies is None:
            return 0

        try:
            source_path = os.path.join(groups_path, MEDIAGROUPS_STORE_PATH)
            with open(source_path, "r") as input_file:
                mediagroups = MediaGroups.fromDict(json.load(input_file))
                name = os.path.basename(os.path.realpath(groups_path))
                proxy_number = self.proxies.find_proxies(
                    name,
                    proxy_threshold,
                    mediagroups.get_groups_gps(),
                    os.path.getmtime(source_path),
                    force,
                )
                if proxy_number == -1:
                    self.log.info(
                        f"{self.proxies.label} : gps list unmodified since last proxy search"
                    )
                elif proxy_number == -2:
                    self.log.info(f"{self.proxies.label} : no proxy search for self")
                else:
                    self.updated = True
                    self.log.info(
                        f"{self.proxies.label} : find {proxy_number} proxy with {name} "
                    )
                return proxy_number
        except Exception as e:
            self.log.error(f"Error while loading groups data {groups_path}: {e}")
            return 0
