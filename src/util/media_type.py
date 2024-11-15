from enum import Enum
from util.file_naming import get_extension


class MediaType(Enum):
    MOVIE = "movie"
    PICTURE = "image"
    UNKNOWN = "unknown"

    def toString(self) -> str:
        return self.value.lower()

    def toDict(self) -> str:
        return self.toString()


class MediaTypeHelper:

    media_types = {
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
    def get_expected_extensions(cls: "MediaTypeHelper") -> list[str]:
        return [f".{ext}" for ext, _ in MediaTypeHelper.media_types.items()]

    @classmethod
    def get_media_type(cls: "MediaTypeHelper", filename: str) -> MediaType:
        try:
            return MediaTypeHelper.media_types[get_extension(filename)]["media_type"]
        except:
            return MediaType.UNKNOWN

    @classmethod
    def get_iana_media_type(cls: "MediaTypeHelper", filename: str) -> str:
        try:
            return f"{MediaTypeHelper.get_media_type(filename).toString()}/{MediaTypeHelper.media_types[get_extension(filename)]['media_format']}"
        except:
            return MediaType.UNKNOWN
