from math import radians, cos, sin, sqrt, atan2, pi
from typing import Dict, List, Any


class GPS:
    __slots__ = ("latitude_", "longitude_")

    def __init__(self, latitude: float, longitude: float) -> None:
        if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
            raise TypeError("Latitude and longitude must be numbers")
        if -90 <= latitude <= 90 and -180 <= longitude <= 180:
            self.latitude_ = latitude
            self.longitude_ = longitude
        else:
            raise ValueError("Invalid GPS coordinates")

    def __str__(self) -> str:
        return f"GPS({self.latitude}, {self.longitude})"

    @property
    def latitude(self) -> float:
        return self.latitude_

    @property
    def longitude(self) -> float:
        return self.longitude_

    def toDict(self) -> Dict[str, float]:
        return {"latitude": self.latitude, "longitude": self.longitude}

    @classmethod
    def fromDict(cls, d: Dict[str, Any]) -> "GPS":
        return cls(d["latitude"], d["longitude"])

    def distance_to(self, gps: "GPS") -> float:
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

    def midpoint_to(self, gps: "GPS") -> "GPS":
        lat1, lon1, lat2, lon2 = map(
            radians, [self.latitude, self.longitude, gps.latitude, gps.longitude]
        )
        dlon = lon2 - lon1

        Bx = cos(lat2) * cos(dlon)
        By = cos(lat2) * sin(dlon)
        lat_mid = atan2(sin(lat1) + sin(lat2), sqrt((cos(lat1) + Bx) ** 2 + By**2))
        lon_mid = lon1 + atan2(By, cos(lat1) + Bx)

        return GPS(lat_mid * 180 / pi, lon_mid * 180 / pi)

    def barycenter_to(self, gps: "GPS", weight: float) -> "GPS":
        lat = self.latitude + ((self.latitude - gps.latitude) / (1 + weight))
        lon = self.longitude + ((self.longitude - gps.longitude) / (1 + weight))
        return GPS(lat, lon)

    @classmethod
    def barycenter(cls, points: List["GPS"]) -> "GPS":
        x = 0.0
        y = 0.0
        z = 0.0

        for point in points:
            lat, lon = radians(point.latitude), radians(point.longitude)
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
