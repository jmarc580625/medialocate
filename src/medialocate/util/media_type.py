from enum import Enum
from typing import Dict, TypedDict
from medialocate.util.file_naming import get_extension


class MediaType(Enum):
    MOVIE = "movie"
    PICTURE = "image"
    UNKNOWN = "unknown"

    def toString(self) -> str:
        return self.value.lower()

    def toDict(self) -> str:
        return self.toString()


class MediaInfo(TypedDict):
    media_type: MediaType
    media_format: str


class MediaTypeHelper:
    media_types: Dict[str, MediaInfo] = {
        "3gp": {"media_type": MediaType.MOVIE, "media_format": "3gpx"},
        "avi": {"media_type": MediaType.MOVIE, "media_format": "xxx"},
        "mkv": {"media_type": MediaType.MOVIE, "media_format": "xxx"},
        "mov": {"media_type": MediaType.MOVIE, "media_format": "xxx"},
        "mp4": {"media_type": MediaType.MOVIE, "media_format": "mp4"},
        "mpeg": {"media_type": MediaType.MOVIE, "media_format": "mpeg"},
        "mpg": {"media_type": MediaType.MOVIE, "media_format": "mpeg"},
        "wmv": {"media_type": MediaType.MOVIE, "media_format": "xxx"},
        "webm": {"media_type": MediaType.MOVIE, "media_format": "xxx"},
        "gif": {"media_type": MediaType.PICTURE, "media_format": "gif"},
        "jpeg": {"media_type": MediaType.PICTURE, "media_format": "jpeg"},
        "jpg": {"media_type": MediaType.PICTURE, "media_format": "jpeg"},
        "png": {"media_type": MediaType.PICTURE, "media_format": "png"},
        "tiff": {"media_type": MediaType.PICTURE, "media_format": "tiff"},
        "webp": {"media_type": MediaType.PICTURE, "media_format": "webp"},
    }

    @classmethod
    def get_expected_extensions(cls) -> list[str]:
        return [f".{ext}" for ext, _ in MediaTypeHelper.media_types.items()]

    @classmethod
    def get_media_type(cls, filename: str) -> MediaType:
        try:
            media_info = MediaTypeHelper.media_types[get_extension(filename).lower()]
            return media_info["media_type"]
        except KeyError:
            return MediaType.UNKNOWN

    @classmethod
    def get_iana_media_type(cls, filename: str) -> str:
        try:
            media_type = MediaTypeHelper.get_media_type(filename).toString()
            media_format = MediaTypeHelper.media_types[get_extension(filename).lower()][
                "media_format"
            ]
            return f"{media_type}/{media_format}"
        except (KeyError, AttributeError):
            return MediaType.UNKNOWN.toString()
