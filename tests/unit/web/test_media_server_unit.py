"""
Unit tests for the media_server module.
Tests the functionality of:
- MediaServer class
- ServiceHandler class
- HTTP request handling
"""

import os
import json
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from http.client import HTTPResponse
from urllib.error import URLError
from medialocate.web.media_server import (
    MediaServer,
    ServiceHandler,
    MediaHTTPServer,
    MEDIASERVER_PORT,
    MEDIASERVER_UX_DIR,
    MEDIALOCATION_STORE_NAME
)

class TestMediaServer(unittest.TestCase):
    """Test cases for MediaServer class"""

    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        
        # Initialize the media server
        self.media_server = MediaServer(
            port=MEDIASERVER_PORT,
            data_root_dir=self.test_dir,
            log=None
        )

    def tearDown(self):
        # Clean up temporary test directory
        import shutil
        shutil.rmtree(self.test_dir)

    def test_initialization(self):
        """Test MediaServer initialization"""
        self.assertEqual(self.media_server.port, MEDIASERVER_PORT)
        self.assertEqual(self.media_server.data_root_dir, os.path.normpath(self.test_dir))
        self.assertTrue(self.media_server.working_directory.endswith(MEDIASERVER_UX_DIR))
        self.assertEqual(self.media_server.items_dict, {})
        self.assertIsNone(self.media_server.httpd)

    def test_get_media_sources(self):
        """Test scanning for media sources"""
        # Create test media files
        test_dir = os.path.join(self.test_dir, "album1")
        os.makedirs(test_dir)
        test_file = os.path.join(test_dir, MEDIALOCATION_STORE_NAME)
        with open(test_file, "w") as f:
            json.dump({"location": {"latitude": 48.8584, "longitude": 2.2945}}, f)

        self.media_server.get_media_sources(self.test_dir)
        self.assertEqual(len(self.media_server.items_dict), 1)
        self.assertTrue(any("album1" in path for path in self.media_server.items_dict.values()))

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

    def setUp(self):
        # Create mock server
        self.server = MagicMock()
        self.server.working_directory = "test_dir"
        self.server.data_root_dir = "test_data"
        self.server.items_dict = {}
        
        # Create test handler
        class TestHandler(ServiceHandler):
            def __init__(self, server):
                self.server = server
                self.headers = {}
                self.wfile = MagicMock()
                self.rfile = MagicMock()
        
        self.handler = TestHandler(self.server)

    def test_translate_path(self):
        """Test URL path translation"""
        test_paths = {
            "/": os.path.join("test_dir", "index.html"),
            "/test.html": os.path.join("test_dir", "test.html"),
            "/media/test.jpg": os.path.join("test_data", "test.jpg")
        }
        
        for path, expected in test_paths.items():
            result = self.handler.translate_path(path)
            self.assertEqual(os.path.normpath(result), os.path.normpath(expected))

    def test_validate_url(self):
        """Test URL validation"""
        valid_urls = [
            "http://example.com/test.jpg",
            "https://example.com/test.jpg"
        ]
        invalid_urls = [
            "ftp://example.com/test.jpg",
            "file:///test.jpg",
            "invalid_url"
        ]
        
        for url in valid_urls:
            self.assertTrue(self.handler._validate_url_scheme(url))
        
        for url in invalid_urls:
            self.assertFalse(self.handler._validate_url_scheme(url))

    @patch("medialocate.web.media_server.urlopen")
    def test_handle_proxy(self, mock_urlopen):
        """Test proxy request handling"""
        # Mock response
        mock_response = MagicMock(spec=HTTPResponse)
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "image/jpeg", "Content-Length": "1000"}
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Test successful request
        self.handler._handle_proxy("test.jpg")

        # Test error handling
        mock_urlopen.side_effect = URLError("Test error")
        with self.assertRaises(URLError):
            self.handler._handle_proxy("http://example.com/error.jpg")

    def test_handle_albums(self):
        """Test albums API endpoint"""
        self.handler.server.items_dict = {
            "hash1": "path1/image1.jpg",
            "hash2": "path2/image2.jpg"
        }
        
        # Mock the response writing
        self.handler.wfile = MagicMock()
        
        self.handler._handle_albums()
        
        # Get the written response data
        write_call_args = self.handler.wfile.write.call_args[0][0]
        response_data = json.loads(write_call_args.decode())
        
        self.assertIn("albums", response_data)
        self.assertEqual(len(response_data["albums"]), 2)

if __name__ == '__main__':
    unittest.main()