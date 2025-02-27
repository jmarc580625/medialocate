"""
Integration tests for the media_server web application.
Tests the integration between:
- HTTP server setup and request handling
- File system operations
- Media source management
- API endpoints
- Session handling
"""

import os
import json
import tempfile
import unittest
import threading
from http.client import HTTPConnection
from urllib.parse import urlencode
from unittest.mock import patch, MagicMock
from medialocate.util.file_naming import (
    relative_path_to_posix,
    get_hash_from_relative_path,
)
from medialocate.media.parameters import (
    MEDIALOCATION_DIR,
    MEDIALOCATION_STORE_NAME,
    MEDIALOCATION_STORE_PATH,
)
from medialocate.web.media_server import (
    MediaServer,
    MEDIASERVER_UX,
    MEDIASERVER_SESSION_DIR,
)


class TestMediaServer(unittest.TestCase):
    # Integration tests for the MediaServer web application

    @classmethod
    def setUpClass(cls):
        # Set up logging
        import logging

        cls.logger = logging.getLogger("test_media_server")
        cls.logger.setLevel(logging.INFO)

    def setUp(self):
        # Set up test environment before each test
        # Create a temporary directory structure for testing
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.test_dir, "data")
        os.makedirs(self.data_dir)

        # Create some test media files and location data
        self.create_test_data(self.data_dir, "album1")
        self.create_test_data(self.data_dir, "album2")

        # Use a random port for each test to avoid conflicts
        import socket

        sock = socket.socket()
        sock.bind(("", 0))
        self.port = sock.getsockname()[1]
        sock.close()

        # Initialize the server
        self.server = MediaServer(self.port, self.data_dir, log=self.logger)

        # Start server in a separate thread
        self.server_thread = threading.Thread(target=self.server.start)
        self.server_thread.daemon = True
        self.server_thread.start()

        # Wait for server to start
        import time

        time.sleep(1)

    def tearDown(self):
        # Clean up after each test
        # Stop the server
        if self.server.httpd:
            self.server.httpd.shutdown()
            self.server.httpd.server_close()

        # Remove test directory
        import shutil

        shutil.rmtree(self.test_dir)

        # Clean up session cache
        cache_dir = os.path.join(os.path.expanduser("~"), MEDIASERVER_SESSION_DIR)
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)

    def create_test_data(self, data_dir, album_name):
        # Create test media files and location data
        # Create album directories
        album_dir = os.path.join(data_dir, album_name)
        os.makedirs(album_dir)

        # Create media files
        open(os.path.join(album_dir, "photo1.jpg"), "w").close()
        open(os.path.join(album_dir, "photo2.jpg"), "w").close()
        open(os.path.join(album_dir, "photo3.jpg"), "w").close()

        # create medialocate directory
        media_dir = os.path.join(album_dir, MEDIALOCATION_DIR)
        os.makedirs(media_dir)

        # Create location data
        location_data = {
            "photo1.jpg": {
                "gps": {"latitude": 40.7128, "longitude": -74.0060}
            },  # New York
            "photo2.jpg": {
                "gps": {"latitude": 34.0522, "longitude": -118.2437}
            },  # Los Angeles
            "photo3.jpg": {
                "gps": {"latitude": 51.5074, "longitude": -0.1278}
            },  # London,
        }

        media_location = {}
        for media_file, location in location_data.items():
            hash = get_hash_from_relative_path(media_file)
            thumbnail_name = hash + ".jpg"
            thumbnail_path = os.path.join(MEDIALOCATION_DIR, thumbnail_name)
            thumbnail_fullpath = os.path.join(album_dir, thumbnail_path)
            with open(thumbnail_fullpath, "w") as f:
                f.write(f"<html><body>{media_file} thumbnail</body></html>")
            media_desc = {
                "media": relative_path_to_posix(media_file),
                "thumbnail": relative_path_to_posix(thumbnail_path),
                **location,
            }
            media_location[hash] = media_desc

        media_store = os.path.join(media_dir, MEDIALOCATION_STORE_NAME)
        with open(media_store, "w") as f:
            json.dump(media_location, f, indent=2)

    def test_server_startup(self):
        # Test that server starts up correctly
        conn = HTTPConnection("localhost", self.port)
        conn.request("GET", "/")
        response = conn.getresponse()
        self.assertEqual(response.status, 200)
        conn.close()

    def test_albums_endpoint(self):
        # Test the /api/albums endpoint
        conn = HTTPConnection("localhost", self.port)
        conn.request("GET", "/api/albums")
        response = conn.getresponse()
        self.assertEqual(response.status, 200)
        data = json.loads(response.read().decode())
        self.assertIn("album1", str(data))
        self.assertIn("album2", str(data))
        conn.close()

    def test_album_endpoint(self):
        # Test the /api/album endpoint for a specific album
        conn = HTTPConnection("localhost", self.port)
        conn.request("GET", "/api/album?album1")
        response = conn.getresponse()
        self.assertEqual(response.status, 200)
        data = response.read().decode("utf-8")
        self.assertIn("photo1.jpg", data)
        self.assertIn("photo2.jpg", data)
        conn.close()

    def test_proxy_endpoint(self):
        test_data = b"<html><body>test data</body></html>"
        test_file = os.path.join(self.data_dir, "album1", "test.txt")
        with open(test_file, "wb") as f:
            f.write(test_data)

        # Test the proxy endpoint for media files
        conn = HTTPConnection("localhost", self.port)
        conn.request("GET", f"/media/album1/test.txt")
        response = conn.getresponse()
        self.assertEqual(response.status, 200)
        self.assertEqual(response.read(), test_data)
        conn.close()

    def test_nonexistent_album(self):
        # Test requesting a non-existent album
        conn = HTTPConnection("localhost", self.port)
        conn.request("GET", "/api/album?nonexistent")
        response = conn.getresponse()
        self.assertEqual(response.status, 404)
        conn.close()

    def test_invalid_media_path(self):
        # Test requesting an invalid proxy path
        conn = HTTPConnection("localhost", self.port)
        conn.request("GET", "/media/../invalid.jpg")
        response = conn.getresponse()
        self.assertEqual(response.status, 400)
        conn.close()

    def test_concurrent_requests(self):
        # Test handling of concurrent requests
        import concurrent.futures

        def make_request():
            conn = HTTPConnection("localhost", self.port)
            try:
                conn.request("GET", "/api/albums")
                response = conn.getresponse()
                status = response.status
                response.read()  # Need to read the response to free the connection
                return status
            finally:
                conn.close()

        make_request()

        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            statuses = [f.result() for f in futures]

        # All requests should succeed
        for status in statuses:
            self.assertEqual(status, 200)

    def test_malformed_requests(self):
        # Test handling of malformed requests
        test_cases = [
            # Missing path parameter
            ("/api/album", 400),
            # Invalid URL encoding, TODO: needs to check it is actually invalid
            ("/api/album?%FF", 400),
            # Path traversal attempt
            ("/api/album?../../../etc/passwd", 400),
            # Very long path
            (f'/api/album?{"x" * 1000}', 404),
        ]

        conn = HTTPConnection("localhost", self.port)
        for path, expected_status in test_cases:
            try:
                conn.request("GET", path)
                response = conn.getresponse()
                self.assertEqual(
                    response.status, expected_status, f"Failed for path: {path}"
                )
                response.read()  # Need to read the response to free the connection
            except Exception as e:
                conn.close()
                conn = HTTPConnection("localhost", self.port)
                raise e
        conn.close()

    def test_server_shutdown(self):
        # Test server shutdown endpoint
        conn = HTTPConnection("localhost", self.port)
        conn.request("GET", "/api/shutdown")
        response = conn.getresponse()
        self.assertEqual(response.status, 200)
        conn.close()

        # Give server time to shut down
        import time

        time.sleep(1)  # Give server time to shut down

        # Try to make another request - should fail
        conn = HTTPConnection("localhost", self.port)
        with self.assertRaises(ConnectionRefusedError):
            conn.request("GET", "/")
            conn.getresponse()

    def test_session_cache(self):
        # Test that session cache is created and used
        # Start server to create cache
        self.server.initiate()

        # Check that cache file exists
        cache_dir = os.path.join(os.path.expanduser("~"), MEDIASERVER_SESSION_DIR)
        self.assertTrue(os.path.exists(cache_dir))

        # Check cache contents
        cache_files = os.listdir(cache_dir)
        self.assertTrue(any(file.endswith(".json") for file in cache_files))


if __name__ == "__main__":
    unittest.main()
