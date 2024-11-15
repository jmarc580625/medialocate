# -------------------------------------------------------------------------------
# python modules
# -------------------------------------------------------------------------------
import os
from enum import Enum
from pathlib import PurePath, Path
import logging
import subprocess

# -------------------------------------------------------------------------------
# home made modules
# -------------------------------------------------------------------------------
from media.parameters import (
    MEDIALOCATION_STORE_NAME,
    MEDIALOCATION_PAGE_DATA,
    MEDIALOCATION_RES_DIR,
    MEDIALOCATION_PAGE_PROLOG,
    MEDIALOCATION_PAGE_EPILOG,
)
from store.dict import DictStore
from location.gps import GPS
from util.file_naming import to_posix, to_uri

# -------------------------------------------------------------------------------
# utility classes
# -------------------------------------------------------------------------------


class MediaType(Enum):
    MOVIE = "movie"
    PICTURE = "picture"
    UNKNOWN = "unknown"

    def toString(self) -> str:
        return self.name.lower()

    def toDict(self) -> str:
        return self.toString()


class DataTag:
    #    id : str
    mediasource: str
    mediathumbnail: str
    mediaformat: str
    mediatype: MediaType
    gps: GPS

    def toDict(self) -> str:
        return {
            "mediasource": self.mediasource,
            "mediathumbnail": self.mediathumbnail,
            "mediaformat": self.mediaformat,
            "mediatype": self.mediatype.toString(),
            "gps": self.gps.toDict(),
        }


class ExifKey(Enum):
    LATITUDE = "Composite:GPSLatitude"
    LONGITUDE = "Composite:GPSLongitude"

    def toString(self) -> str:
        return self.value

    def toDict(self) -> str:
        return self.toString()


# -------------------------------------------------------------------------------
# core class
# -------------------------------------------------------------------------------
class MediaLocateAction:

    LOGGER_NAME = "MediaLocateAction"
    STORE_NAME = MEDIALOCATION_STORE_NAME
    RESSOURCE_DIR_NAME = MEDIALOCATION_RES_DIR
    PROLOG_RESSOURCE_NAME = MEDIALOCATION_PAGE_PROLOG
    EPILOG_RESSOURCE_NAME = MEDIALOCATION_PAGE_EPILOG
    DATA_APPENDIX_NAME = MEDIALOCATION_PAGE_DATA

    def __init__(
        self: "MediaLocateAction", working_directory: str, outfile: str, parent_logger: str = None
    ):
        self.working_directory = working_directory
        self.out_file = outfile
        self.log = logging.getLogger(
            ".".join(filter(None, [parent_logger, MediaLocateAction.LOGGER_NAME]))
        )
        self.store = DictStore(self.working_directory, MediaLocateAction.STORE_NAME)
        self.store.open()
        self.ressources_path = os.path.join(
            os.path.dirname(__file__), MediaLocateAction.RESSOURCE_DIR_NAME
        )
        self.prolog_resource_path = os.path.join(
            self.ressources_path, MediaLocateAction.PROLOG_RESSOURCE_NAME
        )
        self.epilog_resource_path = os.path.join(
            self.ressources_path, MediaLocateAction.EPILOG_RESSOURCE_NAME
        )
        self.data_appendix_path = os.path.join(
            self.working_directory, MediaLocateAction.DATA_APPENDIX_NAME
        )
        self.installed_packages = {}
        self.exiftool = None

    def __call__(self: "MediaLocateAction", file_to_process: str, file_status: str):
        return self.process(file_to_process, file_status)

    def __enter__(self: "MediaLocateAction"):
        return self

    def __exit__(self: "MediaLocateAction", *args):
        self.store.close()
        if self.exiftool is not None:
            self.exiftool.terminate()

    def assert_package_is_installed(self: "MediaLocateAction", params: list[str]):
        package_name = params[0]
        if not package_name in self.installed_packages:
            try:
                if (
                    subprocess.check_call(
                        params, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                    == 0
                ):
                    self.installed_packages[package_name] = True
                    self.log.info(f"{package_name} is installed")
            except FileNotFoundError:
                raise Exception(f"{package_name} is not installed")

    def get_gps_data(self: "MediaLocateAction", file_to_process: str):
        self.assert_package_is_installed(["exiftool", "-ver"])

        from exiftool import ExifToolHelper

        if self.exiftool is None:
            self.exiftool = ExifToolHelper()

        tags = self.exiftool.get_tags(
            file_to_process, tags=[ExifKey.LATITUDE.value, ExifKey.LONGITUDE.value], params=["-n"]
        )
        gps = None
        # self.log.info(f"{file_to_process} : {', '.join(f'{k} : {v}' for k, v in tags[0].items())}")

        if ExifKey.LATITUDE.value in tags[0] and ExifKey.LONGITUDE.value in tags[0]:
            gps = GPS(
                latitude=tags[0][ExifKey.LATITUDE.value], longitude=tags[0][ExifKey.LONGITUDE.value]
            )
            self.log.info(
                f"{file_to_process} : (latitude={gps.latitude}, longitude={gps.longitude})"
            )
            if gps.latitude + gps.longitude == 0:
                gps = None
        else:
            self.log.info(f"{file_to_process} : no GPS data found")

        return gps

    media_types = {
        "3gp": MediaType.MOVIE,
        "avi": MediaType.MOVIE,
        "mkv": MediaType.MOVIE,
        "mov": MediaType.MOVIE,
        "mp4": MediaType.MOVIE,
        "mpeg": MediaType.MOVIE,
        "mpg": MediaType.MOVIE,
        "wmv": MediaType.MOVIE,
        "webm": MediaType.MOVIE,
        "gif": MediaType.PICTURE,
        "jpeg": MediaType.PICTURE,
        "jpg": MediaType.PICTURE,
        "png": MediaType.PICTURE,
        "tiff": MediaType.PICTURE,
        "webp": MediaType.PICTURE,
    }

    @classmethod
    def get_expected_extensions(cls: "MediaLocateAction") -> list[str]:
        return [f".{ext}" for ext in MediaLocateAction.media_types]

    @classmethod
    def get_filename_extension(cls: "MediaLocateAction", filename: str) -> str:
        return os.path.splitext(filename)[1][1:].lower()

    @classmethod
    def get_media_type(cls: "MediaLocateAction", extension: str) -> MediaType:
        try:
            return MediaLocateAction.media_types[extension]
        except:
            return MediaType.UNKNOWN

    def thumb_from_video_with_python_av_packages(
        self: "MediaLocateAction", filename: str, thumbnail_name: str
    ) -> bool:
        # TODO: to be tested
        # import av
        # container = av.open(filename)
        # video_stream = container.streams.video[0]
        return True

    def thumb_from_video_with_ffmpeg_shell(
        self: "MediaLocateAction", filename: str, thumbnail_name: str
    ) -> bool:
        self.assert_package_is_installed(["ffmpeg", "-version"])
        return (
            subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-v",
                    "quiet",
                    "-nostdin",
                    "-i",
                    filename,
                    "-vf",
                    "thumbnail,scale = w = 128:h = -1",
                    "-frames:v",
                    "1",
                    thumbnail_name,
                ]
            ).returncode
            == 0
        )

    def thumb_from_picture_with_ffmpeg_shell(
        self: "MediaLocateAction", filename: str, thumbnail_name: str
    ) -> bool:
        self.assert_package_is_installed(["ffmpeg", "-version"])
        # TODO: to be tested
        return (
            subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-v",
                    "quiet",
                    "-nostdin",
                    "-i",
                    filename,
                    "-vf",
                    "thumbnail,scale = w = 128:h = -1",
                    thumbnail_name,
                ]
            ).returncode
            == 0
        )

    def thumb_from_picture_with_python_PIL_package(
        self: "MediaLocateAction", filename: str, thumbnail_name: str
    ) -> bool:
        from PIL import Image

        # TODO: to be tested
        with Image.open(filename) as img:
            img.thumbnail((128, 128))
            img.save(thumbnail_name, "JPEG")
        return True

    def thumb_from_picture_with_convert_shell(
        self: "MediaLocateAction", filename: str, thumbnail_name: str
    ) -> bool:
        self.assert_package_is_installed(["convert", "-version"])
        # TODO: to be tested
        return (
            subprocess.run(
                ["convert", "-quiet", "-resize", "128x", filename, thumbnail_name]
            ).returncode
            == 0
        )

    def create_thumb_from_media(
        self: "MediaLocateAction", filename: str, media_type: MediaType, thumbnail_name: str
    ) -> bool:
        if media_type == MediaType.MOVIE:
            return self.thumb_from_video_with_ffmpeg_shell(filename, thumbnail_name)
        elif media_type == MediaType.PICTURE:
            return self.thumb_from_picture_with_ffmpeg_shell(filename, thumbnail_name)
        else:
            return False

    def copy_location_page_appendices_and_get_associated_html_links(
        self: "MediaLocateAction", file_extension: str, template: str
    ) -> str:
        snippet = ""
        for source in os.listdir(self.ressources_path):
            if source.endswith(file_extension):
                target_path = os.path.join(self.working_directory, source)
                source_path = os.path.join(self.ressources_path, source)
                snippet += template.format(path=PurePath(target_path).as_posix())
                if not os.path.exists(target_path) or os.path.getmtime(
                    target_path
                ) < os.path.getmtime(source_path):
                    with open(target_path, "w") as f_out:
                        with open(source_path, "r") as f_in:
                            f_out.write(f_in.read())
        return snippet

    def create_location_page(self: "MediaLocateAction"):
        if self.store.size() > 0 and self.store.is_touched():

            # copy a fresh version of the stylesheet and script appendices files if needed
            stylesheet_link_template = """<link rel = "stylesheet" href = "{path}">"""
            html_stylesheet_snippet = (
                self.copy_location_page_appendices_and_get_associated_html_links(
                    ".css", stylesheet_link_template
                )
            )
            script_link_template = """<script src = "{path}"></script>"""
            html_script_snippet = self.copy_location_page_appendices_and_get_associated_html_links(
                ".js", script_link_template
            )

            # generates medialocation data/script appendix file if needed
            data_link_template = (
                """<script type="text/javascript" src="{path}" class="json"></script>"""
            )
            html_script_snippet += data_link_template.format(
                path=PurePath(self.data_appendix_path).as_posix()
            )
            if self.store.is_touched():
                self.store.commit()
                with open(self.data_appendix_path, "w") as destination:
                    with open(self.store.getPath(), "r") as source:
                        destination.write("medialocate_data=")
                        destination.write(source.read())
                        destination.write(";")

            # generates the location page if needed
            if (
                not os.path.exists(self.out_file)
                or os.path.getmtime(self.out_file) < os.path.getmtime(self.prolog_resource_path)
                or os.path.getmtime(self.out_file) < os.path.getmtime(self.epilog_resource_path)
            ):

                with open(self.out_file, "w") as f:
                    with open(self.prolog_resource_path, "r") as html_prolog:
                        html_prolog_template = html_prolog.read()
                        f.write(
                            html_prolog_template.format(
                                stylesheets=html_stylesheet_snippet, scripts=html_script_snippet
                            )
                        )
                    with open(self.epilog_resource_path, "r") as html_epilog:
                        f.write(html_epilog.read())

            return self.out_file
        else:
            return None

    def process(self: "MediaLocateAction", file_to_process: str, hash: str) -> int:
        try:

            gps = self.get_gps_data(file_to_process)
            if gps:

                media_format = MediaLocateAction.get_filename_extension(file_to_process)
                media_type = MediaLocateAction.media_types.get(media_format)
                thumb_filename = os.path.join(self.working_directory, f"{hash}.jpg")

                if self.create_thumb_from_media(file_to_process, media_type, thumb_filename):

                    data_tag = DataTag()

                    data_tag.mediasource = to_posix(file_to_process)
                    data_tag.mediasource = to_uri(file_to_process)
                    data_tag.mediathumbnail = to_uri(thumb_filename)

                    data_tag.mediaformat = media_format
                    data_tag.mediatype = media_type
                    data_tag.gps = gps

                    self.store.updateItem(hash, data_tag.toDict())

                    return 0
                else:
                    raise Exception(f"{file_to_process} : thumbnail creation failed")
            else:
                return 1

        except Exception as e:
            self.log.error(f"{file_to_process} : processing failed {e}")
            return 10
