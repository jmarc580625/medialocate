import unittest
from medialocate.util.media_type import MediaType, MediaTypeHelper


class TestMediaType(unittest.TestCase):
    def test_toString(self):
        # Act & Assert
        self.assertEqual(MediaType.MOVIE.toString(), "movie")
        self.assertEqual(MediaType.PICTURE.toString(), "image")
        self.assertEqual(MediaType.UNKNOWN.toString(), "unknown")

    def test_toDict(self):
        # Act & Assert
        self.assertEqual(MediaType.MOVIE.toDict(), "movie")
        self.assertEqual(MediaType.PICTURE.toDict(), "image")
        self.assertEqual(MediaType.UNKNOWN.toDict(), "unknown")


class TestMediaTypeHelper(unittest.TestCase):
    def setUp(self):
        self.movie_files = [
            "video.mp4",
            "movie.avi",
            "clip.mkv",
            "sample.mov",
            "test.3gp",
            "video.mpeg",
            "movie.mpg",
            "clip.wmv",
            "test.webm",
        ]
        self.picture_files = [
            "photo.jpg",
            "image.jpeg",
            "picture.png",
            "animation.gif",
            "scan.tiff",
            "photo.webp",
        ]
        self.unknown_files = [
            "document.pdf",
            "text.txt",
            "data.bin",
            "noextension",
            ".hidden",
        ]

    def test_get_expected_extensions(self):
        # Act
        extensions = MediaTypeHelper.get_expected_extensions()
        # Assert
        expected = [
            ".3gp", ".avi", ".mkv", ".mov", ".mp4", ".mpeg", ".mpg",
            ".wmv", ".webm", ".gif", ".jpeg", ".jpg", ".png", ".tiff", ".webp"
        ]
        self.assertCountEqual(extensions, expected)

    def test_get_media_type_movie_files(self):
        # Act & Assert
        for filename in self.movie_files:
            with self.subTest(filename=filename):
                self.assertEqual(
                    MediaTypeHelper.get_media_type(filename),
                    MediaType.MOVIE
                )

    def test_get_media_type_picture_files(self):
        # Act & Assert
        for filename in self.picture_files:
            with self.subTest(filename=filename):
                self.assertEqual(
                    MediaTypeHelper.get_media_type(filename),
                    MediaType.PICTURE
                )

    def test_get_media_type_unknown_files(self):
        # Act & Assert
        for filename in self.unknown_files:
            with self.subTest(filename=filename):
                self.assertEqual(
                    MediaTypeHelper.get_media_type(filename),
                    MediaType.UNKNOWN
                )

    def test_get_iana_media_type_movie_files(self):
        # Arrange
        expected_types = {
            "video.mp4": "movie/mp4",
            "video.mpeg": "movie/mpeg",
            "movie.mpg": "movie/mpeg",
            "test.3gp": "movie/3gpx",
            "movie.avi": "movie/xxx",
            "clip.mkv": "movie/xxx",
            "sample.mov": "movie/xxx",
            "clip.wmv": "movie/xxx",
            "test.webm": "movie/xxx",
        }
        # Act & Assert
        for filename, expected in expected_types.items():
            with self.subTest(filename=filename):
                self.assertEqual(
                    MediaTypeHelper.get_iana_media_type(filename),
                    expected
                )

    def test_get_iana_media_type_picture_files(self):
        # Arrange
        expected_types = {
            "photo.jpg": "image/jpeg",
            "image.jpeg": "image/jpeg",
            "picture.png": "image/png",
            "animation.gif": "image/gif",
            "scan.tiff": "image/tiff",
            "photo.webp": "image/webp",
        }
        # Act & Assert
        for filename, expected in expected_types.items():
            with self.subTest(filename=filename):
                self.assertEqual(
                    MediaTypeHelper.get_iana_media_type(filename),
                    expected
                )

    def test_get_iana_media_type_unknown_files(self):
        # Act & Assert
        for filename in self.unknown_files:
            with self.subTest(filename=filename):
                self.assertEqual(
                    MediaTypeHelper.get_iana_media_type(filename),
                    "unknown"
                )

    def test_get_media_type_case_sensitivity(self):
        # Test case sensitivity in file extensions
        test_cases = {
            "video.MP4": MediaType.MOVIE,
            "image.JPG": MediaType.PICTURE,
            "photo.Jpeg": MediaType.PICTURE,
            "movie.AVI": MediaType.MOVIE,
            "pic.PNG": MediaType.PICTURE,
        }
        for filename, expected in test_cases.items():
            with self.subTest(filename=filename):
                self.assertEqual(
                    MediaTypeHelper.get_media_type(filename),
                    expected
                )

    def test_get_media_type_multiple_dots(self):
        # Test files with multiple dots
        test_cases = {
            "my.favorite.video.mp4": MediaType.MOVIE,
            "image.backup.jpg": MediaType.PICTURE,
            "test.file.with.many.dots.png": MediaType.PICTURE,
        }
        for filename, expected in test_cases.items():
            with self.subTest(filename=filename):
                self.assertEqual(
                    MediaTypeHelper.get_media_type(filename),
                    expected
                )

    def test_get_media_type_edge_cases(self):
        # Test edge cases and invalid inputs
        test_cases = {
            "": MediaType.UNKNOWN,
            ".": MediaType.UNKNOWN,
            "..": MediaType.UNKNOWN,
            "file.": MediaType.UNKNOWN,
            ".gitignore": MediaType.UNKNOWN,
        }
        for filename, expected in test_cases.items():
            with self.subTest(filename=filename):
                self.assertEqual(
                    MediaTypeHelper.get_media_type(filename),
                    expected
                )

    def test_get_iana_media_type_case_sensitivity(self):
        # Test case sensitivity in IANA media types
        test_cases = {
            "video.MP4": "movie/mp4",
            "image.JPG": "image/jpeg",
            "photo.Jpeg": "image/jpeg",
            "movie.AVI": "movie/xxx",
            "pic.PNG": "image/png",
        }
        for filename, expected in test_cases.items():
            with self.subTest(filename=filename):
                self.assertEqual(
                    MediaTypeHelper.get_iana_media_type(filename),
                    expected
                )

    def test_get_iana_media_type_edge_cases(self):
        # Test edge cases for IANA media type resolution
        test_cases = {
            "": "unknown",
            ".": "unknown",
            "..": "unknown",
            "file.": "unknown",
            ".gitignore": "unknown",
            "file.unknown": "unknown",
            "video.invalid": "unknown",
        }
        for filename, expected in test_cases.items():
            with self.subTest(filename=filename):
                self.assertEqual(
                    MediaTypeHelper.get_iana_media_type(filename),
                    expected
                )


if __name__ == "__main__":
    unittest.main()
