import unittest
import hashlib
from medialocate.util.file_naming import (
    relative_path_to_posix,
    relative_path_to_uri,
    get_hash_from_relative_path,
    get_extension,
)


class TestFileNaming(unittest.TestCase):
    def setUp(self):
        self.windows_relative_path = "Users\\test\\file.txt"
        self.posix_relative_path = "Users/test/file.txt"
        self.mixed_relative_path = "Users\\test/file.txt"
        self.expected_relative_path = self.posix_relative_path
        self.expected_relative_uri = self.posix_relative_path
        self.expected_relative_hash = hashlib.md5(
            self.posix_relative_path.encode("utf-8"), usedforsecurity=False
        ).hexdigest()
        self.absolute_paths = [
            "C:\\Users\\test\\file.txt",
            "\\Users\\test\\file.txt",
            "/users/test/file.txt",
        ]
        self.drive_letter_paths = [
            "C:\\Users\\test\\file.txt",
            "D:\\Users\\test\\file.txt",
            "C:Users\\test\\file.txt",
            "D:Users\\test\\file.txt",
            "C:",
            "C:.",
            "C:..",
            "C:\\",
        ]
        self.edge_case_paths = [
            "",
            ".",
            "..",
            "/",
            "\\",
        ]
        self.special_char_paths = {
            "path with spaces/file.txt": "path%20with%20spaces/file.txt",
            "path_with_underscore/file.txt": "path_with_underscore/file.txt",
            "path-with-dash/file.txt": "path-with-dash/file.txt",
            "pathWithEqualSign=/file.txt": "pathWithEqualSign%3D/file.txt",
            "pathWithAmpersandSign&/file.txt": "pathWithAmpersandSign%26/file.txt",
            "pathWithArobaseSign@/file.txt": "pathWithArobaseSign%40/file.txt",
            "pathWithEmojis🌍/file.txt": "pathWithEmojis%F0%9F%8C%8D/file.txt",
            "pathWithKanjis🇯🇵/file.txt": "pathWithKanjis%F0%9F%87%AF%F0%9F%87%B5/file.txt",
        }
        self.filename_no_ext = "testfile"
        self.filename_with_ext = "testfile.jpg"
        self.filename_multiple_dots = "test.file.jpg"
        self.filename_hidden = ".hidden"

    def test_relative_path_to_posix_from_windows_relative_path(self):
        # Test relative_path_to_posix with windows relative paths
        # Act
        result = relative_path_to_posix(self.windows_relative_path)
        # Assert
        self.assertEqual(result, self.posix_relative_path)

    def test_relative_path_to_posix_from_posix_relative_path(self):
        # Test relative_path_to_posix with posix relative paths
        # Act
        result = relative_path_to_posix(self.posix_relative_path)
        # Assert
        self.assertEqual(result, self.posix_relative_path)

    def test_relative_path_to_posix_from_mixed_relative_path(self):
        # Test relative_path_to_posix with mixed relative paths
        # Act
        result = relative_path_to_posix(self.mixed_relative_path)
        # Assert
        self.assertEqual(result, self.posix_relative_path)

    def test_relative_path_to_posix_with_absolute_path(self):
        # Test relative_path_to_posix with absolute paths
        for input_path in self.absolute_paths:
            with self.subTest(input_path=input_path):
                with self.assertRaises(
                    ValueError,
                    msg=f"relative_path_to_posix({input_path}) should raise ValueError",
                ):
                    relative_path_to_posix(input_path)

    def test_relative_path_to_posix_with_drive_letter(self):
        # Test relative_path_to_posix with drive letters
        for input_path in self.drive_letter_paths:
            with self.subTest(input_path=input_path):
                with self.assertRaises(
                    ValueError,
                    msg=f"relative_path_to_posix({input_path}) should raise ValueError",
                ):
                    relative_path_to_posix(input_path)

    def test_relative_path_to_posix_with_edge_cases(self):
        # Test relative_path_to_posix with edge cases
        for input_path in self.edge_case_paths:
            with self.subTest(input_path=input_path):
                with self.assertRaises(
                    ValueError,
                    msg=f"relative_path_to_posix({input_path}) should raise ValueError",
                ):
                    relative_path_to_posix(input_path)

    def test_get_hash_from_relative_path_with_windows_relative_path(self):
        # Test hash generation with Windows relative paths
        # Act
        result = get_hash_from_relative_path(self.windows_relative_path)
        # Assert
        self.assertEqual(result, self.expected_relative_hash)

    def test_get_hash_from_relative_path_with_posix_relative_path(self):
        # Test hash generation with POSIX relative paths
        # Act
        result = get_hash_from_relative_path(self.posix_relative_path)
        # Assert
        self.assertEqual(result, self.expected_relative_hash)

    def test_get_hash_from_relative_path_with_mixed_relative_path(self):
        # Test hash generation with mixed relative paths
        # Act
        result = get_hash_from_relative_path(self.mixed_relative_path)
        # Assert
        self.assertEqual(result, self.expected_relative_hash)

    def test_get_hash_from_relative_path_with_special_chars(self):
        # Test hash generation with special characters in relative paths
        for path, expected in self.special_char_paths.items():
            with self.subTest(path=path):
                expected_hash = hashlib.md5(
                    path.encode("utf-8"), usedforsecurity=False
                ).hexdigest()
                self.assertEqual(get_hash_from_relative_path(path), expected_hash)

    def test_get_hash_from_relative_path_with_absolute_path(self):
        # Test hash generation with absolute paths
        for input_path in self.absolute_paths:
            with self.subTest(input_path=input_path):
                with self.assertRaises(
                    ValueError,
                    msg=f"get_hash_from_relative_path({input_path}) should raise ValueError",
                ):
                    get_hash_from_relative_path(input_path)

    def test_get_hash_from_relative_path_with_drive_letter(self):
        # Test hash generation with drive letters in paths
        for input_path in self.drive_letter_paths:
            with self.subTest(input_path=input_path):
                with self.assertRaises(
                    ValueError,
                    msg=f"get_hash_from_relative_path({input_path}) should raise ValueError",
                ):
                    get_hash_from_relative_path(input_path)

    def test_get_hash_from_relative_path_with_edge_cases(self):
        # Test hash generation with edge cases
        for input_path in self.edge_case_paths:
            with self.subTest(input_path=input_path):
                with self.assertRaises(
                    ValueError,
                    msg=f"get_hash_from_relative_path({input_path}) should raise ValueError",
                ):
                    get_hash_from_relative_path(input_path)

    def test_relative_path_to_uri_with_windows_relative_path(self):
        # Test URI conversion with Windows relative paths
        # Act
        result = relative_path_to_uri(self.windows_relative_path)
        # Assert
        self.assertEqual(result, self.expected_relative_uri)

    def test_relative_path_to_uri_with_posix_relative_path(self):
        # Test URI conversion with POSIX relative paths
        # Act
        result = relative_path_to_uri(self.posix_relative_path)
        # Assert
        self.assertEqual(result, self.expected_relative_uri)

    def test_relative_path_to_uri_with_mixed_relative_path(self):
        # Test URI conversion with mixed relative paths
        # Act
        result = relative_path_to_uri(self.mixed_relative_path)
        # Assert
        self.assertEqual(result, self.expected_relative_uri)

    def test_relative_path_to_uri_with_absolute_path(self):
        # Test URI conversion with Windows absolute paths
        for path in self.absolute_paths:
            with self.subTest(path=path):
                with self.assertRaises(
                    ValueError,
                    msg=f"relative_path_to_uri({path}) should raise ValueError",
                ):
                    relative_path_to_uri(path)

    def test_relative_path_to_uri_with_special_chars(self):
        # Test URI conversion with special characters
        for input_path, expected in self.special_char_paths.items():
            with self.subTest(input_path=input_path):
                self.assertEqual(relative_path_to_uri(input_path), expected)

    def test_relative_path_to_uri_with_drive_letter_paths(self):
        # Test URI conversion with Windows absolute paths
        for path in self.drive_letter_paths:
            with self.subTest(path=path):
                with self.assertRaises(
                    ValueError,
                    msg=f"relative_path_to_uri({path}) should raise ValueError",
                ):
                    relative_path_to_uri(path)

    def test_relative_path_to_uri_with_edge_cases(self):
        # Test URI conversion with edge cases
        for input_path in self.edge_case_paths:
            with self.subTest(input_path=input_path):
                with self.assertRaises(
                    ValueError,
                    msg=f"relative_path_to_uri({input_path}) should raise ValueError",
                ):
                    relative_path_to_uri(input_path)

    def test_get_extension_with_normal_file(self):
        # Test extension extraction with a normal file
        # Act
        result = get_extension(self.filename_with_ext)
        # Assert
        self.assertEqual(result, "jpg")

    def test_get_extension_with_no_extension(self):
        # Test extension extraction with no extension
        # Act
        result = get_extension(self.filename_no_ext)
        # Assert
        self.assertEqual(result, "")

    def test_get_extension_with_multiple_dots(self):
        # Test extension extraction with multiple dots in the filename
        # Act
        result = get_extension(self.filename_multiple_dots)
        # Assert
        self.assertEqual(result, "jpg")

    def test_get_extension_with_hidden_file(self):
        # Test extension extraction with a hidden file
        # Act
        result = get_extension(self.filename_hidden)
        # Assert
        self.assertEqual(result, "")

    def test_get_extension_with_edge_cases(self):
        # Test extension extraction with edge cases
        # Prepare
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


if __name__ == "__main__":
    unittest.main()
