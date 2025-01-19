"""
Unit tests for the media_server module.
Tests the functionality of:
- MediaServer class
- ServiceHandler class
- HTTP request handling
"""

import os
import json
import shutil
import logging
import unittest
import tempfile
from urllib.parse import urlparse
from urllib.error import URLError
from unittest.mock import MagicMock, patch
from medialocate.util.file_naming import relative_path_to_posix
from medialocate.web.media_server import (
    MediaServer,
    ServiceHandler,
    MEDIASERVER_UX_DIR,
    MEDIALOCATION_STORE_NAME,
)


class TestMediaServer(unittest.TestCase):
    """Test cases for MediaServer class"""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.media_server = MediaServer(
            port=8080, data_root_dir=self.test_dir, log=logging.getLogger("test_logger")
        )

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)

    def test_initialization(self):
        """Test MediaServer initialization"""
        self.assertEqual(self.media_server.port, 8080)
        self.assertEqual(
            self.media_server.data_root_dir, os.path.normpath(self.test_dir)
        )
        self.assertTrue(
            self.media_server.working_directory.endswith(MEDIASERVER_UX_DIR)
        )
        self.assertEqual(self.media_server.items_dict, {})
        self.assertIsNone(self.media_server.httpd)

    def test_get_media_sources(self) -> None:
        """Test scanning for media sources.

        Verifies that the media server correctly identifies and returns media sources
        from the filesystem.
        """
        # Create test media files
        album_dir = os.path.join(self.test_dir, "album1")
        os.makedirs(album_dir)
        album_data_dir = os.path.join(album_dir, ".data")
        os.makedirs(album_data_dir)
        test_data_file = os.path.join(album_data_dir, MEDIALOCATION_STORE_NAME)
        with open(test_data_file, "w") as f:
            json.dump({"location": {"latitude": 48.8584, "longitude": 2.2945}}, f)

        # Get media sources and save them
        self.media_server.items_dict = self.media_server.get_media_sources(
            self.test_dir
        )
        self.assertEqual(len(self.media_server.items_dict), 1)

        # Verify the path is correct
        album_path = next(iter(self.media_server.items_dict.values()))
        expected_path = os.path.join(".data", MEDIALOCATION_STORE_NAME)
        self.assertEqual(album_path, relative_path_to_posix(expected_path))

    def test_save_and_retrieve_media_sources(self):
        """Test saving and retrieving media sources from cache"""
        test_items = {"hash1": "path1", "hash2": "path2"}
        self.media_server.items_dict = test_items

        # Save to cache
        self.media_server.save_media_sources(test_items)

        # Clear and reload
        self.media_server.items_dict = {}
        self.media_server.retrieve_media_sources()

        self.assertEqual(self.media_server.items_dict, test_items)


class TestServiceHandler(unittest.TestCase):
    """Test cases for ServiceHandler class"""

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)

    def setUp(self):
        """Set up test environment."""
        # Create mock server
        self.test_dir = tempfile.mkdtemp()
        self.server = MagicMock()
        self.server.working_directory = os.path.abspath("test_dir")
        self.server.data_root_dir = os.path.join(self.test_dir, "test_data")
        os.makedirs(self.server.data_root_dir)

        self.server.items_dict = {}

        # Create test handler
        class TestHandler(ServiceHandler):
            def __init__(self, server):
                self.server = server
                self.headers = {}
                self.wfile = MagicMock()
                self.rfile = MagicMock()
                # Add required attributes for HTTP request handling
                self.requestline = "GET / HTTP/1.1"
                self.client_address = ("127.0.0.1", 12345)
                self.directory = os.path.abspath(server.working_directory)
                self.command = "GET"
                self.path = "/"
                self.response_sent = False
                self.headers_sent = False
                self.response_code = None
                self.response_headers = {}

            def send_response(self, code, message=None):
                """Mock send_response."""
                self.response_code = code
                self.response_sent = True

            def send_header(self, keyword, value):
                """Mock send_header."""
                self.response_headers[keyword] = value
                self.headers_sent = True

            def end_headers(self):
                """Mock end_headers."""
                pass

            def log_message(self, format, *args):
                """Suppress logging."""
                pass

            def _validate_url_scheme(self, url: str) -> bool:
                """Override URL validation for testing."""
                parsed = urlparse(url)
                return parsed.scheme in ["http", "https"]

        self.handler = TestHandler(self.server)

    def test_translate_path(self) -> None:
        """Test URL path translation.

        Verifies that URLs are correctly translated to filesystem paths.
        """
        # Set up default directory
        self.handler.directory = os.path.abspath("test_dir")

        # Test media paths
        media_path = "/media/test.jpg"
        expected_media_path = os.path.join(
            self.handler.server.data_root_dir, "test.jpg"
        )
        with open(expected_media_path, "wb") as f:
            f.write(b"test image data")
        result = self.handler.translate_path(media_path)
        self.assertEqual(
            os.path.normpath(result), os.path.normpath(expected_media_path)
        )

        # Test regular paths (should be relative to directory)
        test_paths = {
            "/": os.path.join(self.handler.directory),
            "/test.html": os.path.join(self.handler.directory, "test.html"),
        }

        for path, expected in test_paths.items():
            result = self.handler.translate_path(path)
            self.assertEqual(os.path.normpath(result), os.path.normpath(expected))

    def test_validate_url(self) -> None:
        """Test URL validation.

        Verifies that URLs are properly validated according to security rules.
        """
        valid_urls = [
            "http://example.com/test.jpg",
            "https://example.com/test.jpg",
            "https://example.com/path/to/image.jpg",
        ]
        invalid_urls = [
            "ftp://example.com/test.jpg",
            "file:///test.jpg",
            "invalid_url",
            "javascript:alert(1)",
            "data:image/jpeg;base64,/9j/4AAQ",
        ]

        for url in valid_urls:
            self.assertTrue(
                self.handler._validate_url_scheme(url), f"URL should be valid: {url}"
            )

        for url in invalid_urls:
            self.assertFalse(
                self.handler._validate_url_scheme(url), f"URL should be invalid: {url}"
            )

    def test_handle_media(self) -> None:
        """Test media request handling.

        Verifies that media requests are handled correctly and responses are
        properly forwarded.
        """
        # Set up test data
        test_album = "test_album"
        test_file = "test.jpg"
        test_dir = os.path.join(self.handler.server.data_root_dir, test_album)
        os.makedirs(test_dir, exist_ok=True)

        # Create test file and store relative path in items_dict
        test_file_path = os.path.join(test_dir, test_file)
        with open(test_file_path, "wb") as f:
            f.write(b"test image data")
        image_size = os.path.getsize(test_file_path)

        self.handler.server.items_dict = {
            test_album: os.path.join(test_album, test_file)
        }

        # Test successful request
        self.handler.path = f"/api/media?{test_album}/{test_file}"
        self.handler.do_GET()

        # Verify successful response
        self.assertTrue(self.handler.response_sent)
        self.assertEqual(self.handler.response_code, 200)
        self.assertTrue(self.handler.headers_sent)
        self.assertEqual(
            self.handler.response_headers.get("Content-Type"), "image/jpeg"
        )
        self.assertEqual(
            self.handler.response_headers.get("Content-Length"), f"{image_size}"
        )

        # Test error handling for invalid album
        self.handler.path = "/api/media?nonexistent_album/test.jpg"
        self.handler.do_GET()
        self.assertEqual(self.handler.response_code, 404)

        # Test error handling for invalid URL
        self.handler.path = f"/api/media?{test_album}/../test.jpg"
        self.handler.do_GET()
        self.assertEqual(self.handler.response_code, 400)

    def test_handle_albums(self):
        """Test albums API endpoint."""
        # Setup test data
        test_items = {
            "hash1": "path1/image1.jpg",
            "hash2": "path2/image2.jpg",
        }
        self.handler.server.items_dict = test_items

        # Mock the response writing
        self.handler.wfile = MagicMock()
        self.handler._handle_album_list()

        # Verify response
        self.assertTrue(self.handler.response_sent)
        self.assertEqual(self.handler.response_code, 200)
        self.assertTrue(self.handler.headers_sent)
        self.assertEqual(
            self.handler.response_headers.get("Content-Type"), "application/json"
        )

        # Verify response data
        write_call_args = self.handler.wfile.write.call_args[0][0]
        response_data = json.loads(write_call_args.decode())
        self.assertEqual(response_data, test_items)


if __name__ == "__main__":
    unittest.main()
