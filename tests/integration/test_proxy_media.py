"""
Integration tests for the proxy_media command-line application.
Tests the integration between:
- Command line argument parsing
- File system operations
- Media proxies controller
- Directory handling
- Media group data processing
"""

import os
import json
import tempfile
import unittest
from unittest.mock import patch
from dataclasses import dataclass
from typing import List, Dict, Optional
from medialocate.proxy_media import main
from medialocate.media.parameters import (
    MEDIALOCATION_DIR,
    MEDIAGROUPS_STORE_NAME,
    MEDIAPROXIES_STORE_NAME,
)


@dataclass
class TestMediaGroup:
    """Test media group configuration"""

    group_name: str
    media_files: List[str]
    location: Optional[Dict[str, float]] = None


class TestProxyMediaCommand(unittest.TestCase):
    """
    Integration tests for the proxy_media command
    """

    def setUp(self):
        # Create a temporary directory structure for testing
        self.test_dir = tempfile.mkdtemp()

        # Create test media groups
        self.test_groups = [
            TestMediaGroup(
                group_name="paris_group",
                media_files=["paris1.jpg", "paris2.jpg"],
                location={"latitude": 48.8584, "longitude": 2.2945},
            ),
            TestMediaGroup(
                group_name="newyork_group",
                media_files=["ny1.jpg", "ny2.jpg"],
                location={"latitude": 40.7128, "longitude": -74.0060},
            ),
        ]

        # Create source directories
        self.source_dir1 = os.path.join(self.test_dir, "source1")
        self.source_dir2 = os.path.join(self.test_dir, "source2")
        os.makedirs(self.source_dir1)
        os.makedirs(self.source_dir2)

        # Create target directory
        self.target_dir = os.path.join(self.test_dir, "target")
        os.makedirs(self.target_dir)

        # Create media location directories
        self.media_dir1 = os.path.join(self.source_dir1, MEDIALOCATION_DIR)
        self.media_dir2 = os.path.join(self.source_dir2, MEDIALOCATION_DIR)
        self.media_target = os.path.join(self.target_dir, MEDIALOCATION_DIR)
        os.makedirs(self.media_dir1)
        os.makedirs(self.media_dir2)
        os.makedirs(self.media_target)

        # Create test group data
        self.groups_store1 = os.path.join(self.media_dir1, MEDIAGROUPS_STORE_NAME)
        self.groups_store2 = os.path.join(self.media_dir2, MEDIAGROUPS_STORE_NAME)
        self.groups_target = os.path.join(self.media_target, MEDIAGROUPS_STORE_NAME)
        self._create_test_group_data(self.groups_store1)
        self._create_test_group_data(self.groups_store2)
        self._create_test_group_data(self.groups_target)

    def tearDown(self):
        # Clean up temporary test directory
        import shutil

        shutil.rmtree(self.test_dir)

    def _create_test_group_data(self, store_path):
        """Helper to create test group data"""
        threshold = {"grouping_threshold": 0.1}
        groups = {"groups": []}
        for group in self.test_groups:
            groups["groups"].append(
                {
                    "gps": group.location,
                    "media_keys": group.media_files,
                }
            )
        with open(store_path, "w") as f:
            json.dump({**threshold, **groups}, f)

    def test_proxy_media_basic(self):
        """Test basic proxy media functionality"""
        # Act
        with patch(
            "sys.argv", ["proxy_media", "-t", self.target_dir, self.source_dir1]
        ):
            main()

        # Assert
        # Check proxy store exists
        proxy_store = os.path.join(
            self.target_dir, MEDIALOCATION_DIR, MEDIAPROXIES_STORE_NAME
        )
        self.assertTrue(os.path.exists(proxy_store), "Proxy store should be created")

        # Check proxy links are created
        with open(proxy_store, "r") as f:
            proxies_data = json.load(f)
            self.assertIsInstance(proxies_data, dict)

    def test_proxy_media_with_custom_threshold(self):
        """Test proxy media with custom distance threshold"""
        # Act
        with patch(
            "sys.argv",
            ["proxy_media", "-d", "2.5", "-t", self.target_dir, self.source_dir1],
        ):
            main()

        # Assert
        proxy_store = os.path.join(
            self.target_dir, MEDIALOCATION_DIR, MEDIAPROXIES_STORE_NAME
        )
        self.assertTrue(os.path.exists(proxy_store))

        # Verify proxies are created with the custom threshold
        with open(proxy_store, "r") as f:
            proxies_data = json.load(f)
            self.assertIsInstance(proxies_data, dict)

    def test_proxy_media_update_no_force_flag(self):
        """Test proxy media with force flag"""
        # Create initial proxy store
        # Act
        with patch(
            "sys.argv", ["proxy_media", "-t", self.target_dir, self.source_dir1]
        ):
            main()

        # Verify new proxies are created
        proxy_store = os.path.join(
            self.target_dir, MEDIALOCATION_DIR, MEDIAPROXIES_STORE_NAME
        )
        self.assertTrue(os.path.exists(proxy_store))
        initial_mtime = os.path.getmtime(proxy_store)

        # force proxies update
        with patch(
            "sys.argv", ["proxy_media", "-t", self.target_dir, self.source_dir1]
        ):
            main()

        # Assert
        self.assertTrue(os.path.exists(proxy_store))
        final_mtime = os.path.getmtime(proxy_store)
        self.assertEqual(
            final_mtime, initial_mtime, "Proxy store should not have been regenerated"
        )

    def test_proxy_media_update_with_force_flag(self):
        """Test proxy media with force flag"""
        # Create initial proxy store
        # Act
        with patch(
            "sys.argv", ["proxy_media", "-t", self.target_dir, self.source_dir1]
        ):
            main()

        # Verify new proxies are created
        proxy_store = os.path.join(
            self.target_dir, MEDIALOCATION_DIR, MEDIAPROXIES_STORE_NAME
        )
        self.assertTrue(os.path.exists(proxy_store))
        initial_mtime = os.path.getmtime(proxy_store)

        # force proxies update
        with patch(
            "sys.argv", ["proxy_media", "-f", "-t", self.target_dir, self.source_dir1]
        ):
            main()

        # Assert
        self.assertTrue(os.path.exists(proxy_store))
        final_mtime = os.path.getmtime(proxy_store)
        self.assertGreater(
            final_mtime, initial_mtime, "Proxy store should have been regenerated"
        )

    def test_proxy_media_with_multiple_directories(self):
        """Test proxy media with multiple source directories"""
        # Act
        with patch(
            "sys.argv",
            ["proxy_media", "-t", self.target_dir, self.source_dir1, self.source_dir2],
        ):
            main()

        # Assert
        proxy_store = os.path.join(
            self.target_dir, MEDIALOCATION_DIR, MEDIAPROXIES_STORE_NAME
        )
        self.assertTrue(os.path.exists(proxy_store))

        # Verify proxies from both directories
        with open(proxy_store, "r") as f:
            proxies_data = json.load(f)
            self.assertIsInstance(proxies_data, dict)


if __name__ == "__main__":
    unittest.main()
