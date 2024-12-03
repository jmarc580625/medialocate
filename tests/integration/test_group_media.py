"""
Integration tests for the group_media command-line application.
Tests the integration between:
- Command line argument parsing
- File system operations
- Media location store
- Media groups store
- GPS location grouping
"""

import os
import tempfile
import unittest
from unittest.mock import patch
from medialocate.group_media import main
from medialocate.media.parameters import (
    MEDIALOCATION_DIR,
    MEDIALOCATION_STORE_NAME,
    MEDIAGROUPS_STORE_NAME,
)
import json


class TestGroupMediaCommand(unittest.TestCase):
    """
    Integration tests for the group_media command
    """

    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.media_dir = os.path.join(self.test_dir, MEDIALOCATION_DIR)
        os.makedirs(self.media_dir, exist_ok=True)

        # Create test media location data
        self.location_store = os.path.join(self.media_dir, MEDIALOCATION_STORE_NAME)
        self.groups_store = os.path.join(self.media_dir, MEDIAGROUPS_STORE_NAME)

    def tearDown(self):
        # Clean up temporary test directory
        import shutil

        shutil.rmtree(self.test_dir)

    def test_group_media_with_default_args(self):
        """Test grouping media with default arguments"""
        # Arrange
        # Create test media location data
        with open(self.location_store, "w") as f:
            f.write(
                '{"media1.jpg": {"gps":{"latitude": 48.8584, "longitude": 2.2945}}}'
            )

        # Act
        with patch("os.getcwd") as mock_getcwd:
            mock_getcwd.return_value = self.test_dir
            with patch("sys.argv", ["group_media"]):
                main()

        # Assert
        self.assertTrue(os.path.exists(self.groups_store))
        with open(self.groups_store, "r") as f:
            groups_data = f.read()
            self.assertIn("media1.jpg", groups_data)

    def test_group_media_with_custom_threshold(self):
        """Test grouping media with custom distance threshold"""
        # Arrange
        # Create test media location data
        with open(self.location_store, "w") as f:
            f.write(
                """
            {
                "media1.jpg": {"gps":{"latitude": 48.8584, "longitude": 2.2945}},
                "media2.jpg": {"gps":{"latitude": 48.8591, "longitude": 2.2950}}
            }
            """
            )

        # Act
        with patch("os.getcwd") as mock_getcwd:
            mock_getcwd.return_value = self.test_dir
            with patch("sys.argv", ["group_mediax", "-d", "2.5"]):
                main()

        # Assert
        self.assertTrue(os.path.exists(self.groups_store))
        with open(self.groups_store, "r") as f:
            groups_data = f.read()
            self.assertIn("media1.jpg", groups_data)
            self.assertIn("media2.jpg", groups_data)

    def test_group_media_without_force_flag(self):
        """Test grouping media without force flag"""
        # Arrange
        # Create test media location data
        with open(self.location_store, "w") as f:
            f.write(
                '{"media1.jpg": {"gps":{"latitude": 48.8584, "longitude": 2.2945}}}'
            )
        ls_initial_mtime = os.path.getmtime(self.location_store)

        # Create existing groups data
        with open(self.groups_store, "w") as f:
            f.write('{"group1": ["media1.jpg"]}')

        # Store the initial modification time
        initial_mtime = os.path.getmtime(self.groups_store)

        # Act
        with patch("os.getcwd") as mock_getcwd:
            mock_getcwd.return_value = self.test_dir
            with patch("sys.argv", ["group_mediax"]):
                main()

        # Assert
        self.assertTrue(os.path.exists(self.groups_store))

        # Verify the file was actually regenerated
        final_mtime = os.path.getmtime(self.groups_store)
        self.assertEqual(
            final_mtime, initial_mtime, "Groups file should not have been regenerated"
        )

    def test_group_media_with_force_flag(self):
        """Test grouping media with force flag"""
        # Arrange
        # Create test media location data
        with open(self.location_store, "w") as f:
            f.write(
                '{"media1.jpg": {"gps":{"latitude": 48.8584, "longitude": 2.2945}}}'
            )

        # Create existing groups data
        with open(self.groups_store, "w") as f:
            f.write('{"group1": ["old_media.jpg"]}')

        # Store the initial modification time
        initial_mtime = os.path.getmtime(self.groups_store)

        # Act
        with patch("os.getcwd") as mock_getcwd:
            mock_getcwd.return_value = self.test_dir
            with patch("sys.argv", ["group_mediax", "-f"]):
                main()

        # Assert
        self.assertTrue(os.path.exists(self.groups_store))

        # Verify the file was actually regenerated
        final_mtime = os.path.getmtime(self.groups_store)
        self.assertGreater(
            final_mtime, initial_mtime, "Groups file should have been regenerated"
        )

        with open(self.groups_store, "r") as f:
            groups_data = f.read()
            self.assertIn("media1.jpg", groups_data)

    def test_group_media_with_multiple_directories(self):
        """Test grouping media from multiple directories"""
        # Arrange
        dir1 = os.path.join(self.test_dir, "dir1")
        dir2 = os.path.join(self.test_dir, "dir2")
        os.makedirs(dir1)
        os.makedirs(dir2)

        # Create test media location data in both directories
        data = {
            "media1.jpg": {"gps": {"latitude": 48.8584, "longitude": 2.2945}},  # Paris
            "media2.jpg": {
                "gps": {"latitude": 48.8583, "longitude": 2.2946}
            },  # Near location 1
        }

        # Create media location data files in both directories
        for directory in [dir1, dir2]:
            media_dir = os.path.join(directory, MEDIALOCATION_DIR)
            os.makedirs(media_dir)
            with open(os.path.join(media_dir, MEDIALOCATION_STORE_NAME), "w") as f:
                json.dump(data, f)

        # Act
        with patch("os.getcwd") as mock_getcwd:
            mock_getcwd.return_value = self.test_dir
            with patch("sys.argv", ["group_mediax", dir1, dir2]):
                main()

        # Assert - Each directory should have its own groups file
        # Check dir1 groups
        for directory in [dir1, dir2]:
            groups_file = os.path.join(
                directory, MEDIALOCATION_DIR, MEDIAGROUPS_STORE_NAME
            )
            self.assertTrue(
                os.path.exists(groups_file),
                f"{directory} should have its own groups file",
            )
            with open(groups_file, "r") as f:
                dir_groups = json.load(f)
                # Verify media are grouped together (since they're close)
                self.assertTrue(
                    sorted(dir_groups["groups"][0]["media_keys"])
                    == sorted(["media1.jpg", "media2.jpg"]),
                    "media should be grouped together",
                )


if __name__ == "__main__":
    unittest.main()
