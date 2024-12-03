import unittest
import pathlib
import hashlib
from medialocate.util.file_naming import to_posix, to_uri, get_hash, get_extension


class TestFileNaming(unittest.TestCase):
    def setUp(self):
        self.windows_path = "C:\\Users\\test\\file.txt"
        self.posix_path = "/home/user/file.txt"
        self.mixed_path = "C:/Users\\test/file.txt"
        self.windows_relative_path = "C:Users\\test\\file.txt"
        self.posix_relative_path = "home/user/file.txt"
        self.filename_no_ext = "testfile"
        self.filename_with_ext = "testfile.jpg"
        self.filename_multiple_dots = "test.file.jpg"
        self.filename_hidden = ".hidden"

    def test_to_posix_windows_path(self):
        # Act
        result = to_posix(self.windows_path)
        # Assert
        self.assertEqual(result, "C:/Users/test/file.txt")

    def test_to_posix_posix_path(self):
        # Act
        result = to_posix(self.posix_path)
        # Assert
        self.assertEqual(result, self.posix_path)

    def test_to_posix_mixed_path(self):
        # Act
        result = to_posix(self.mixed_path)
        # Assert
        self.assertEqual(result, "C:/Users/test/file.txt")

    def test_get_extension_normal_file(self):
        # Act
        result = get_extension(self.filename_with_ext)
        # Assert
        self.assertEqual(result, "jpg")

    def test_get_extension_no_extension(self):
        # Act
        result = get_extension(self.filename_no_ext)
        # Assert
        self.assertEqual(result, "")

    def test_get_extension_multiple_dots(self):
        # Act
        result = get_extension(self.filename_multiple_dots)
        # Assert
        self.assertEqual(result, "jpg")

    def test_get_extension_hidden_file(self):
        # Act
        result = get_extension(self.filename_hidden)
        # Assert
        self.assertEqual(result, "")

    def test_get_hash_windows_path(self):
        # Arrange
        expected_hash = hashlib.md5(
            "C:/Users/test/file.txt".encode("utf-8"), 
            usedforsecurity=False
        ).hexdigest()
        # Act
        result = get_hash(self.windows_path)
        # Assert
        self.assertEqual(result, expected_hash)

    def test_get_hash_posix_path(self):
        # Arrange
        expected_hash = hashlib.md5(
            self.posix_path.encode("utf-8"), 
            usedforsecurity=False
        ).hexdigest()
        # Act
        result = get_hash(self.posix_path)
        # Assert
        self.assertEqual(result, expected_hash)

    def test_get_hash_mixed_path(self):
        # Arrange
        expected_hash = hashlib.md5(
            "C:/Users/test/file.txt".encode("utf-8"), 
            usedforsecurity=False
        ).hexdigest()
        # Act
        result = get_hash(self.mixed_path)
        # Assert
        self.assertEqual(result, expected_hash)

    def test_to_uri_windows_absolute_path(self):
        # Act
        result = to_uri(self.windows_path)
        # Assert
        self.assertEqual(result, "file:///C:/Users/test/file.txt")

    def test_to_uri_windows_relative_path(self):
        # Act
        result = to_uri(self.windows_relative_path)
        # Assert
        self.assertEqual(result, "Users/test/file.txt")

    def test_to_uri_mixed_absolute_path(self):
        # Act
        result = to_uri(self.mixed_path)
        # Assert
        self.assertEqual(result, "file:///C:/Users/test/file.txt")

    def test_to_uri_posix_absolute_path(self):
        # Act
        result = to_uri(self.posix_path)
        # Assert
        self.assertEqual(result, "file:///C:/home/user/file.txt")

    def test_to_uri_posix_relative_path(self):
        # Act
        result = to_uri(self.posix_relative_path)
        # Assert
        self.assertEqual(result, "home/user/file.txt")

    def test_to_posix_special_chars(self):
        # Test paths with special characters
        test_cases = {
            "C:\\Users\\test user\\my file.txt": "C:/Users/test user/my file.txt",
            "C:\\Users\\test\\path with spaces\\file.txt": "C:/Users/test/path with spaces/file.txt",
            "C:\\Users\\test\\path_with_underscore\\file.txt": "C:/Users/test/path_with_underscore/file.txt",
            "C:\\Users\\test\\path-with-dash\\file.txt": "C:/Users/test/path-with-dash/file.txt",
        }
        for input_path, expected in test_cases.items():
            with self.subTest(input_path=input_path):
                self.assertEqual(to_posix(input_path), expected)

    def test_to_posix_edge_cases(self):
        # Test edge cases for path conversion
        test_cases = {
            "": ".",
            ".": ".",
            "..": "..",
            "/": "/",
            "\\": "/",
            "C:": "C:",
            "C:\\": "C:/",
        }
        for input_path, expected in test_cases.items():
            with self.subTest(input_path=input_path):
                self.assertEqual(to_posix(input_path), expected)

    def test_to_uri_special_chars(self):
        # Test URI conversion with special characters
        special_paths = {
            "C:\\Users\\test user\\file.txt": "file:///C:/Users/test%20user/file.txt",
            "C:\\Users\\test\\my documents\\file.txt": "file:///C:/Users/test/my%20documents/file.txt",
            "C:\\Program Files\\My App\\file.txt": "file:///C:/Program%20Files/My%20App/file.txt",
        }
        for input_path, expected in special_paths.items():
            with self.subTest(input_path=input_path):
                self.assertEqual(to_uri(input_path), expected)

    def test_to_uri_edge_cases(self):
        # Test edge cases for URI conversion
        test_cases = {
            "C:\\": "file:///C:/",
            "C:": "",
            ".": "",
            "..": "",
        }
        for input_path, expected in test_cases.items():
            with self.subTest(input_path=input_path):
                self.assertEqual(to_uri(input_path), expected)

    def test_get_extension_edge_cases(self):
        # Test edge cases for extension extraction
        test_cases = {
            "": "",
            ".": "",
            "..": "",
            "file": "",
            ".gitignore": "",
            "file.": "",
            "file..": "",
            "file...txt": "txt",
            ".hidden.txt": "txt",
        }
        for input_path, expected in test_cases.items():
            with self.subTest(input_path=input_path):
                self.assertEqual(get_extension(input_path), expected)

    def test_get_hash_special_chars(self):
        # Test hash generation with special characters
        test_cases = [
            "C:\\Users\\test user\\file.txt",
            "C:\\Program Files\\My App\\file.txt",
            "path with spaces/file.txt",
            "path_with_underscore/file.txt",
            "path-with-dash/file.txt",
        ]
        for path in test_cases:
            with self.subTest(path=path):
                expected_hash = hashlib.md5(
                    to_posix(path).encode("utf-8"),
                    usedforsecurity=False
                ).hexdigest()
                self.assertEqual(get_hash(path), expected_hash)

    def test_get_hash_edge_cases(self):
        # Test edge cases for hash generation
        test_cases = ["", ".", "..", "/", "\\"]
        for path in test_cases:
            with self.subTest(path=path):
                expected_hash = hashlib.md5(
                    to_posix(path).encode("utf-8"),
                    usedforsecurity=False
                ).hexdigest()
                self.assertEqual(get_hash(path), expected_hash)

if __name__ == "__main__":
    unittest.main()
