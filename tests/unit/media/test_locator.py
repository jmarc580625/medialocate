import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from medialocate.media.locator import MediaType, DataTag, MediaLocateAction
from medialocate.location.gps import GPS


class TestMediaType(unittest.TestCase):
    def test_media_type_enum_values(self):
        self.assertEqual(MediaType.MOVIE.value, "movie")
        self.assertEqual(MediaType.PICTURE.value, "picture")
        self.assertEqual(MediaType.UNKNOWN.value, "unknown")

    def test_media_type_to_string(self):
        self.assertEqual(MediaType.MOVIE.toString(), "movie")
        self.assertEqual(MediaType.PICTURE.toString(), "picture")
        self.assertEqual(MediaType.UNKNOWN.toString(), "unknown")

    def test_media_type_to_dict(self):
        self.assertEqual(MediaType.MOVIE.toDict(), "movie")
        self.assertEqual(MediaType.PICTURE.toDict(), "picture")
        self.assertEqual(MediaType.UNKNOWN.toDict(), "unknown")


class TestDataTag(unittest.TestCase):
    def setUp(self):
        self.gps = GPS(latitude=45.5, longitude=-122.6)
        self.tag = DataTag()
        self.tag.mediasource = "test.jpg"
        self.tag.mediathumbnail = "thumb.jpg"
        self.tag.mediaformat = "jpeg"
        self.tag.mediatype = MediaType.PICTURE
        self.tag.gps = self.gps

    def test_data_tag_to_dict(self):
        expected = {
            "mediasource": "test.jpg",
            "mediathumbnail": "thumb.jpg",
            "mediaformat": "jpeg",
            "mediatype": "picture",
            "gps": self.gps.toDict(),
        }
        self.assertEqual(self.tag.toDict(), expected)

    def test_data_tag_with_different_media_types(self):
        self.tag.mediatype = MediaType.MOVIE
        self.assertEqual(self.tag.toDict()["mediatype"], "movie")

        self.tag.mediatype = MediaType.UNKNOWN
        self.assertEqual(self.tag.toDict()["mediatype"], "unknown")


class TestMediaLocateAction(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.cwd = os.getcwd()
        os.chdir(self.temp_dir)

        self.out_filename = "out.html"

        self.test_working_dirname = ".test_working"
        os.makedirs(self.test_working_dirname, exist_ok=True)

        self.test_files_dirname = "test_files"
        os.makedirs(self.test_files_dirname, exist_ok=True)

        # Create test files
        self.test_files = {
            "movie.mp4": MediaType.MOVIE,
            "picture.jpg": MediaType.PICTURE,
            "unknown.txt": MediaType.UNKNOWN,
        }
        for filename in self.test_files:
            Path(os.path.join(self.test_files_dirname, filename)).touch()

        self.action = MediaLocateAction(self.test_working_dirname, self.out_filename)

    def tearDown(self):
        self.action.terminate()
        os.chdir(self.cwd)
        shutil.rmtree(self.temp_dir)

    def test_get_media_type(self):
        test_cases = {
            "video.mp4": MediaType.MOVIE,
            "video.MP4": MediaType.MOVIE,
            "image.jpg": MediaType.PICTURE,
            "image.JPG": MediaType.PICTURE,
            "unknown.txt": MediaType.UNKNOWN,
            "": MediaType.UNKNOWN,
            "no_extension": MediaType.UNKNOWN,
            ".hidden": MediaType.UNKNOWN,
        }
        for filename, expected_type in test_cases.items():
            with self.subTest(filename=filename):
                extension = self.action.get_filename_extension(filename)
                self.assertEqual(self.action.get_media_type(extension), expected_type)

    @patch("medialocate.media.locator.ExifToolHelper")
    def test_get_gps_data(self, mock_exiftool_class):
        # Setup mock ExifTool instance
        mock_exiftool_instance = Mock()
        mock_exiftool_instance.get_tags.return_value = [
            {
                "file": "test.jpg",
                "Composite:GPSLatitude": 45.5,
                "Composite:GPSLongitude": -122.6,
            }
        ]
        mock_exiftool_class.return_value = mock_exiftool_instance

        test_file = os.path.join(self.test_files_dirname, "picture.jpg")
        gps = self.action.get_gps_data(test_file)

        self.assertIsNotNone(gps)
        self.assertEqual(gps.latitude, 45.5)
        self.assertEqual(gps.longitude, -122.6)

        # Verify ExifTool was called correctly
        mock_exiftool_instance.get_tags.assert_called_once_with(
            test_file, tags=["Composite:GPSLatitude", "Composite:GPSLongitude"]
        )

    @patch("medialocate.media.locator.ExifToolHelper")
    def test_get_gps_data_no_coords(self, mock_exiftool_class):
        # Setup mock ExifTool instance
        mock_exiftool_instance = Mock()
        mock_exiftool_instance.get_tags.return_value = [{"file": "test.jpg"}]
        mock_exiftool_class.return_value = mock_exiftool_instance

        test_file = os.path.join(self.test_files_dirname, "picture.jpg")
        with self.assertRaises(MediaLocateAction.GPSExtractionError):
            _ = self.action.get_gps_data(test_file)

        # Verify ExifTool was called
        mock_exiftool_instance.get_tags.assert_called_once_with(
            test_file, tags=["Composite:GPSLatitude", "Composite:GPSLongitude"]
        )

    def test_get_expected_extensions(self):
        extensions = self.action.get_expected_extensions()
        expected = [
            ".mp4",
            ".avi",
            ".mkv",
            ".mov",
            ".3gp",
            ".mpeg",
            ".mpg",
            ".wmv",
            ".webm",
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".tiff",
            ".webp",
        ]
        self.assertEqual(sorted(extensions), sorted(expected))

    @patch("subprocess.run")
    def test_generate_thumbnail_picture(self, mock_run):
        mock_run.return_value = Mock(returncode=0)

        source = os.path.join(self.test_files_dirname, "picture.jpg")
        thumb = os.path.join(self.test_working_dirname, "thumb.jpg")

        self.action.generate_thumbnail(source, thumb)
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_generate_thumbnail_movie(self, mock_run):
        mock_run.return_value = Mock(returncode=0)

        source = os.path.join(self.test_files_dirname, "movie.mp4")
        thumb = os.path.join(self.test_working_dirname, "thumb.jpg")

        self.action.generate_thumbnail(source, thumb)
        mock_run.assert_called_once()

    def test_process_valid_file(self):
        test_file = os.path.join(self.test_files_dirname, "picture.jpg")
        with patch.object(self.action, "generate_thumbnail") as mock_thumb:
            with patch.object(self.action, "get_gps_data") as mock_gps:
                mock_gps.return_value = GPS(45.5, -122.6)
                self.action.process(test_file, "test_hash")
                mock_thumb.assert_called_once()

    def test_process_invalid_file(self):
        test_file = "unknown.txt"
        result = self.action.process(test_file, "test_hash")
        self.assertEqual(result, 1)
        # Clean up potential subprocess
        if hasattr(self.action, "_process"):
            self.action._process.terminate()


if __name__ == "__main__":
    unittest.main()
