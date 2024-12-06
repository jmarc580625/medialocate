"""
Integration tests for the locate_media command-line application.
Tests the integration between:
- Command line argument parsing
- File system operations
- Media location action
- Browser launching
- Directory handling
"""

import os
import json
import tempfile
import unittest
from dataclasses import dataclass
from typing import Optional, Dict, Any
from unittest.mock import patch, MagicMock
from medialocate.locate_media import main
from medialocate.media.parameters import MEDIALOCATION_DIR, MEDIALOCATION_STORE_NAME
from medialocate.location.gps import GPS
from medialocate.media.locator import MediaLocateAction, MediaType
from medialocate.util.file_naming import get_hash


@dataclass
class MediaFileFixture:
    """Test media file configuration data container."""

    filename: str
    content: bytes = b""  # Optional binary content
    media_type: MediaType = MediaType.PICTURE
    gps: Optional[GPS] = None


class TestLocateMediaCommand(unittest.TestCase):
    """Integration tests for the locate_media command"""

    def setUp(self):
        """Create test environment with controlled directory structure"""
        self.test_dir = tempfile.mkdtemp()
        self.media_dir = os.path.join(self.test_dir, "media")
        os.makedirs(self.media_dir)

        # Test scenarios
        self.test_files = [
            MediaFileFixture(
                filename="photo1.jpg",
                content=b"test_jpg_content",
                gps=GPS(47.6062, -122.3321),  # Seattle coordinates
            ),
            MediaFileFixture(
                filename="photo2.jpg",
                content=b"test_jpg_content",
                gps=None,  # No GPS data
                media_type=MediaType.PICTURE,
            ),
            MediaFileFixture(
                filename="video1.mp4",
                content=b"test_mp4_content",
                media_type=MediaType.MOVIE,
                gps=GPS(48.8566, 2.3522),  # Paris coordinates
            ),
            MediaFileFixture(
                filename="corrupted.jpg",
                content=b"corrupted_content",
                gps=GPS(48.8566, 2.3522),  # Paris coordinates
            ),
        ]

        # Create test files
        for test_file in self.test_files:
            file_path = os.path.join(self.media_dir, test_file.filename)
            with open(file_path, "wb") as f:
                f.write(test_file.content)

    def tearDown(self):
        """Clean up temporary test directory"""
        import shutil

        shutil.rmtree(self.test_dir)

    def _mock_gps_data(self, test_file: str) -> Optional[GPS]:
        """Helper to return mock GPS data based on test file"""
        for test_case in self.test_files:
            if test_file.endswith(test_case.filename):
                if test_case.gps is None:
                    raise MediaLocateAction.GPSExtractionError("No GPS data found")
                return test_case.gps
        return None

    def _mock_thumbnail(self, input_file: str, output_file: str) -> bool:
        """Helper to simulate thumbnail generation success/failure"""
        for test_case in self.test_files:
            if input_file.endswith(test_case.filename):
                if (
                    test_case.filename == "photo1.jpg"
                    or test_case.filename == "video1.mp4"
                ):
                    # Create a dummy thumbnail file
                    os.makedirs(os.path.dirname(output_file), exist_ok=True)
                    with open(output_file, "wb") as f:
                        f.write(b"dummy_thumbnail")
                    return True
                return False
        return False

    @patch("medialocate.media.locator.MediaLocateAction.get_gps_data")
    @patch("medialocate.media.locator.MediaLocateAction.generate_thumbnail")
    def test_basic_media_location(self, mock_thumbnail, mock_gps):
        """Test basic media location with various file types"""
        # Setup mocks
        mock_gps.side_effect = self._mock_gps_data
        mock_thumbnail.side_effect = self._mock_thumbnail

        # Run locate_media
        with patch("sys.argv", ["locate_media", self.media_dir]):
            result = main()
            self.assertEqual(result, 0)

        # Verify results
        media_output_dir = os.path.join(self.media_dir, MEDIALOCATION_DIR)
        self.assertTrue(os.path.exists(media_output_dir))

        # Verify thumbnails were created/not created as expected
        for test_file in self.test_files:
            thumb_name = f"{get_hash(test_file.filename)}.jpg"
            thumb_path = os.path.join(media_output_dir, thumb_name)
            if test_file.filename == "photo1.jpg" or test_file.filename == "video1.mp4":
                self.assertTrue(
                    os.path.exists(thumb_path),
                    f"Thumbnail not found for {test_file.filename}",
                )
            else:
                self.assertFalse(
                    os.path.exists(thumb_path),
                    f"Unexpected thumbnail found for {test_file.filename}",
                )

        # Verify GPS data was properly handled
        data_file = os.path.join(media_output_dir, MEDIALOCATION_STORE_NAME)
        self.assertTrue(os.path.exists(data_file))
        with open(data_file, "r") as f:
            data = json.load(f)
            self.assertIsInstance(data, dict)

    @patch("medialocate.media.locator.MediaLocateAction.get_gps_data")
    @patch("medialocate.media.locator.MediaLocateAction.generate_thumbnail")
    def test_force_regeneration(self, mock_thumbnail, mock_gps):
        # Test force regeneration of thumbnails and location data
        # Setup mocks
        mock_gps.side_effect = self._mock_gps_data
        mock_thumbnail.side_effect = self._mock_thumbnail

        # First run to create initial files
        with patch("sys.argv", ["locate_media", self.media_dir]):
            main()

        # Modify a test file to simulate changes
        modified_file = os.path.join(self.media_dir, "photo1.jpg")
        with open(modified_file, "wb") as f:
            f.write(b"modified_content")

        # Run with force option
        with patch("sys.argv", ["locate_media", "-f", self.media_dir]):
            result = main()
            self.assertEqual(result, 0)

        # Verify thumbnails were regenerated
        media_output_dir = os.path.join(self.media_dir, MEDIALOCATION_DIR)
        for test_file in self.test_files:
            if test_file.filename == "photo1.jpg" or test_file.filename == "video1.mp4":
                thumb_name = f"{get_hash(test_file.filename)}.jpg"
                thumb_path = os.path.join(media_output_dir, thumb_name)
                self.assertTrue(os.path.exists(thumb_path))

    @patch("medialocate.media.locator.MediaLocateAction.get_gps_data")
    @patch("medialocate.media.locator.MediaLocateAction.generate_thumbnail")
    def test_current_directory_only(self, mock_thumbnail, mock_gps):
        """Test processing only files in the current directory using -d flag"""
        # Setup mocks
        mock_gps.side_effect = self._mock_gps_data
        mock_thumbnail.side_effect = self._mock_thumbnail

        # Create a subdirectory with media files that should be ignored
        subdir = os.path.join(self.media_dir, "subdir")
        os.makedirs(subdir)
        with open(os.path.join(subdir, "ignored.jpg"), "wb") as f:
            f.write(b"ignored_content")

        # Run locate_media with -d flag to process only current directory
        with patch("sys.argv", ["locate_media", "-d", self.media_dir]):
            result = main()
            self.assertEqual(result, 0)

        # Verify only top-level files were processed
        media_output_dir = os.path.join(self.media_dir, MEDIALOCATION_DIR)
        ignored_thumb = f"{get_hash('subdir/ignored.jpg')}.jpg"
        self.assertFalse(os.path.exists(os.path.join(media_output_dir, ignored_thumb)))

        # Verify main directory files were processed
        for test_file in self.test_files:
            if test_file.filename == "photo1.jpg" or test_file.filename == "video1.mp4":
                thumb_name = f"{get_hash(test_file.filename)}.jpg"
                thumb_path = os.path.join(media_output_dir, thumb_name)
                self.assertTrue(os.path.exists(thumb_path))

    @patch("medialocate.media.locator.MediaLocateAction.get_gps_data")
    @patch("medialocate.media.locator.MediaLocateAction.generate_thumbnail")
    def test_multiple_directories(self, mock_thumbnail, mock_gps):
        # Test processing multiple directories
        # Setup mocks
        mock_gps.side_effect = self._mock_gps_data
        mock_thumbnail.side_effect = self._mock_thumbnail

        # Create a second directory with media files
        dir2 = os.path.join(self.test_dir, "dir2")
        os.makedirs(dir2)
        with open(os.path.join(dir2, "extra.jpg"), "wb") as f:
            f.write(b"extra_content")

        # Run with multiple directories
        with patch("sys.argv", ["locate_media", self.media_dir, dir2]):
            result = main()
            self.assertEqual(result, 0)

        # Verify both directories were processed
        self.assertTrue(os.path.exists(os.path.join(self.media_dir, MEDIALOCATION_DIR)))
        self.assertTrue(os.path.exists(os.path.join(dir2, MEDIALOCATION_DIR)))


if __name__ == "__main__":
    unittest.main()
