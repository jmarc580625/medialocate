"""Unit tests for URL validation utilities."""

import unittest
from urllib.parse import quote
from medialocate.util.url_validator import (
    validate_path,
    validate_query,
    validate_url,
)


class TestUrlValidator(unittest.TestCase):
    """Test cases for URL validation utilities."""

    def setUp(self):
        self.query_test_cases = [
            # data                          expected    path    url
            # ----------------------------- test without url ----------
            ("unicode=été", True, True, False),
            ("한글", True, True, False),  # Hangul
            ("emoji=🌍", True, True, False),
            # ----------------------------- test common ------------
            ("space=value a", True, True, True),
            ("percent=%20value", True, True, True),
            ("q1=v1&q2=v2", True, True, True),
            ("control_char=\x03", False, True, True),
            ("invalid_utf8=%ffvalue", False, True, True),
        ]

        self.path_test_cases = [
            # data                          expected    path    url
            # ----------------------------- test with url ------------
            (b"Hello World", True, False, True),
            (quote("Hello World"), True, False, True),
            (quote("unicode/été.jpg"), True, False, True),
            (quote("emoji/path/🌍.jpg"), True, False, True),  # emoji
            # Invalid UTF-8 and percent encoding
            (b"invalid_utf8_\xff.jpg", False, False, True),  # Invalid UTF-8
            (b"invalid_utf8_\xc3.jpg", False, False, True),  # Incomplete UTF-8
            (
                "aa/\rx\ny\tz",
                True,
                False,
                True,
            ),  # spacing characters must be removed by urlparse
            ("/absolute/path/file.jpg", True, True, False),  # absolute path
            # ----------------------------- test without url ----------
            ("LF\nLF", False, True, False),  # spacing characters
            ("CR\rCR", False, True, False),  # spacing characters
            ("TAB\tTAB", False, True, False),  # spacing characters
            # ----------------------------- test common ---------------
            ("path/to/file.jpg", True, True, True),
            ("path with spaces/file.jpg", True, True, True),  # spaces
            ("unicode/saison/été.jpg", True, True, True),  # unicode
            ("emoji/path/🌍.jpg", True, True, True),  # emoji
            ("file.jpg", True, True, True),
            # Valid percent encoding
            ("path/to/Hello%20World", True, True, True),
            ("path/to/%E2%82%AC", True, True, True),  # €
            ("path/to/%C3%A9cu", True, True, True),  # é
            # Control characters
            ("path/to/\x03/file.jpg", False, True, True),
            ("path/to/%03/file.jpg", False, True, True),
            # Path traversal attempts
            ("../secret/file.jpg", False, True, True),
            ("./config/file.jpg", False, True, True),
            ("//etc/passwd", False, True, True),
            ("%2E%2E%2Ftosecretplace", False, True, True),  # Encoded ../
            # Invalid UTF-8 and percent encoding
            ("invalid_utf8_%ff.jpg", False, True, True),  # Invalid UTF-8
            ("invalid_utf8_%c3.jpg", False, True, True),  # Incomplete UTF-8
            ("invalid_utf8_%gg.jpg", True, True, True),  # Invalid hex but valid
            ("%", True, True, True),  # Incomplete but valid
            ("%2", True, True, True),  # Incomplete but valid
            # Null bytes
            ("test\x00.jpg", False, True, True),
            ("test%00.jpg", False, True, True),
            # Mixed issues
            ("../path\x00/file.jpg", False, True, True),  # Traversal + null byte
            ("../path%00/file.jpg", False, True, True),  # Traversal + null byte
        ]

    def _check_result(self, expected, result, message, component, value):
        value = (
            value.decode("utf-8", errors="replace")
            if isinstance(value, bytes)
            else value
        )
        if expected:
            self.assertTrue(
                result, f"{component} should be valid: {value}, got error: {message}"
            )
        else:
            self.assertFalse(
                result, f"{component} should be invalid: {value}, but was marked valid"
            )
            self.assertTrue(
                message, f"Error message should not be empty for invalid URL: {value}"
            )

    def test_path_validation(self):
        """Test file system path validation."""

        path_test_cases = [
            test_case for test_case in self.path_test_cases if test_case[2]
        ]
        for path, expected_result, _, _ in path_test_cases:
            is_valid, _, message = validate_path(path)
            self._check_result(expected_result, is_valid, message, "Path", path)

    def test_query_validation(self):
        """Test file system path validation."""

        query_test_cases = [
            test_case for test_case in self.query_test_cases if test_case[2]
        ]
        for query, expected_result, _, _ in query_test_cases:
            is_valid, _, message = validate_query(query)
            self._check_result(expected_result, is_valid, message, "Query", query)

    def test_url_validation_with_path_and_query(self):
        """Test URL validation."""

        # test_cases = self.path_test_cases_for_url
        path_test_cases = [
            test_case for test_case in self.path_test_cases if test_case[3]
        ]
        for path, path_expected_result, _, _ in path_test_cases:
            if isinstance(path, bytes):
                url = b"http://test.org/" + path
            else:
                url = "http://test.org/" + path
            is_valid, _, _, message = validate_url(url)
            self._check_result(path_expected_result, is_valid, message, "Url", url)

            query_test_cases = [
                test_case for test_case in self.query_test_cases if test_case[3]
            ]
            for query, query_expected_result, _, _ in query_test_cases:
                if isinstance(url, bytes):
                    url_w_query = url + b"?" + query.encode("utf-8")
                else:
                    url_w_query = url + "?" + query
                expected = path_expected_result and query_expected_result
                is_valid, _, _, message = validate_url(url_w_query)
                self._check_result(expected, is_valid, message, "Url", url_w_query)

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""

        # Empty inputs
        is_valid, _, _, _ = validate_url("")
        self.assertFalse(is_valid, "Empty URL should be invalid")

        is_valid, _, _ = validate_path("")
        self.assertTrue(is_valid, "Empty path should be valid")

        # Very long inputs
        long_path = "/path/" + "x" * 2000
        is_valid, _, _ = validate_path(long_path)
        self.assertTrue(is_valid, "Path with 2000 characters should be valid")

        long_url = "http://example.com/" + "x" * 2000
        is_valid, _, _, _ = validate_url(long_url)
        self.assertTrue(is_valid, "URL with 2000 characters should be valid")


if __name__ == "__main__":
    unittest.main()
