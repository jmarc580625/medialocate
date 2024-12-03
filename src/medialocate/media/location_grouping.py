import logging
from typing import Optional
from medialocate.location.gps import GPS


class MediaGroups:
    class Group:
        gps: GPS
        media_keys: list[str]

        def __init__(self, gps: GPS, keys: list[str]) -> None:
            self.gps = gps
            self.media_keys = keys

        def toDict(self) -> dict:
            return {"gps": self.gps.toDict(), "media_keys": self.media_keys}

        @classmethod
        def fromDict(cls, d: dict) -> "MediaGroups.Group":
            gps = GPS.fromDict(d["gps"])
            media_keys = d["media_keys"]
            return cls(gps, media_keys)

    grouping_threshold: float  # threshold distance to group media locations expressed in km
    groups: list["MediaGroups.Group"]  # list of gps coordinates representing groups
    log = logging.getLogger(__name__)

    def __init__(
        self,
        grouping_threshold: float,
        groups: Optional[list["MediaGroups.Group"]] = None,
    ) -> None:
        self.grouping_threshold = grouping_threshold
        self.groups = groups if groups is not None else []

    def toDict(self) -> dict:
        return {
            "grouping_threshold": self.grouping_threshold,
            "groups": [group.toDict() for group in self.groups],
        }

    @classmethod
    def fromDict(cls, d: dict) -> "MediaGroups":
        return cls(
            grouping_threshold=d["grouping_threshold"],
            groups=[MediaGroups.Group.fromDict(group) for group in d["groups"]],
        )

    def add_locations(self, locations: dict[str, dict]) -> None:
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
        return [group.gps for group in self.groups] if self.groups else []
