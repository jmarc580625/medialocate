import json
from math import radians, cos, sin, sqrt, atan2, pi


class GPS:
    __slots__ = ("latitude_", "longitude_")

    def __init__(self: "GPS", latitude: float, longitude: float) -> "GPS":
        self.latitude_ = latitude
        self.longitude_ = longitude

    @property
    def latitude(self: "GPS") -> float:
        return self.latitude_

    @property
    def longitude(self: "GPS") -> float:
        return self.longitude_

    def toDict(self) -> dict:
        return {"latitude": self.latitude, "longitude": self.longitude}

    @classmethod
    def fromDict(cls: "GPS", d: dict) -> "GPS":
        return GPS(d["latitude"], d["longitude"])

    def distance_to(self: "GPS", gps: "GPS") -> float:
        # Haversine formula
        R = 6371  # heartstone radius in kilometers
        phi1 = radians(self.latitude)
        phi2 = radians(gps.latitude)
        delta_phi = radians(gps.latitude - self.latitude)
        delta_lambda = radians(gps.longitude - self.longitude)

        a = sin(delta_phi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(delta_lambda / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        distance = R * c  # result in kilometers
        return distance

    def midpoint_to(self: "GPS", gps: "GPS"):
        self.latitude, self.longitude, gps.latitude, gps.longitude = map(
            radians, [self.latitude, self.longitude, gps.latitude, gps.longitude]
        )
        dlon = gps.longitude - self.longitude

        Bx = cos(gps.latitude) * cos(dlon)
        By = cos(gps.latitude) * sin(dlon)
        lat_mid = atan2(
            sin(self.latitude) + sin(gps.latitude), sqrt((cos(self.latitude) + Bx) ** 2 + By**2)
        )
        lon_mid = self.longitude + atan2(By, cos(self.latitude) + Bx)

        return GPS(lat_mid * 180 / pi, lon_mid * 180 / pi)

    def barycenter_to(self: "GPS", gps: "GPS", weight: int) -> "GPS":
        lat = self.latitude + ((self.latitude - gps.latitude) / (1 + weight))
        lon = self.longitude + ((self.longitude - gps.longitude) / (1 + weight))
        return GPS(lat, lon)

    @classmethod
    def barycenter(cls: "GPS", points: list["GPS"]) -> "GPS":
        x = 0
        y = 0
        z = 0

        for lat, lon in points:
            lat, lon = radians(lat), radians(lon)
            x += cos(lat) * cos(lon)
            y += cos(lat) * sin(lon)
            z += sin(lat)

        total = len(points)
        x /= total
        y /= total
        z /= total

        lon_center = atan2(y, x)
        hyp = sqrt(x * x + y * y)
        lat_center = atan2(z, hyp)

        return cls(lat_center * 180 / pi, lon_center * 180 / pi)
