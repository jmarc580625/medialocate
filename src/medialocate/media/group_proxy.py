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
    proxy_threshold: float
    proxy_matches: List[Tuple[GPS, List[GPS]]]
    last_update: float

    def __init__(
        self,
        proxy_threshold: float,
        matches: List[Tuple[GPS, List[GPS]]] = [],
        timestamp: Optional[float] = None,
    ) -> None:
        self.proxy_threshold = proxy_threshold
        self.proxy_matches = matches
        self.last_update = time.time() if timestamp is None else timestamp

    def toDict(self) -> Dict[str, Any]:
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
        return Proxy(
            d["proxy_threshold"],
            matches=[
                (GPS.fromDict(gps), [GPS.fromDict(gps) for gps in gps_list])
                for gps, gps_list in d["proxy_matches"]
            ],
            timestamp=d["last_update"],
        )


class MediaProxies:
    # TODO: refresh proxies when gps list changes (remember last gps list update)

    label: str
    proxies: Dict[str, Proxy]
    group_locations: List[GPS]

    def __init__(
        self,
        label: str,
        group_locations: List[GPS] = [],
        proxies: Dict[str, Proxy] = {},
    ) -> None:
        self.label = label
        self.proxies = proxies
        self.group_locations = group_locations  # transcient field

    def toDict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            # 'group_locations' is not duplicated, it must be retrieved from its own store
            "proxies": {label: proxy.toDict() for label, proxy in self.proxies.items()},
        }

    @classmethod
    def fromDict(cls, d: Dict[str, Any]) -> "MediaProxies":
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
    LOGGER_NAME = "MediaProxiesControler"

    working_directory: str
    log: logging.Logger
    proxy_store_name: str
    proxies: Optional[MediaProxies]
    updated: bool

    def __init__(
        self,
        working_directory: str,
        parent_logger: Optional[str] = None,
    ) -> None:
        self.working_directory = working_directory
        self.log = logging.getLogger(
            ".".join(filter(None, [parent_logger, MediaProxiesControler.LOGGER_NAME]))
        )
        self.proxy_store_name = os.path.join(
            self.working_directory, MEDIAPROXIES_STORE_PATH
        )
        self.proxies = None
        self.updated = False

    def __enter__(self) -> "MediaProxiesControler":
        self.open()
        return self

    def __exit__(self, *args) -> None:
        self.commit()

    def open(self) -> None:
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
        if self.proxies is not None and self.updated:
            with open(self.proxy_store_name, "w") as f:
                json.dump(self.proxies.toDict(), f, indent=2)
            return True
        return False

    def find_proxies(
        self, groups_path: str, proxy_threshold: float, force: bool = False
    ) -> int:
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
