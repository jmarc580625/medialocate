import os
import time
import json
import shutil
import tempfile
import unittest
from medialocate.media.group_proxy import MediaProxies, MediaProxiesControler, Proxy, MEDIALOCATION_DIR, MEDIAGROUPS_STORE_NAME, MEDIAPROXIES_STORE_PATH
from medialocate.location.gps import GPS
from medialocate.media.location_grouping import MediaGroups

class TestMediaProxiesProxy(unittest.TestCase):
    def setUp(self):
        self.gps1 = GPS(45.5, -122.6)
        self.gps2 = GPS(45.51, -122.61)
        self.gps3 = GPS(45.52, -122.62)
        self.proxy_threshold = 0.1

    def test_proxy_creation_no_matches(self):
        # Test basic creation
        proxy = Proxy(self.proxy_threshold, [])
        self.assertEqual(proxy.proxy_threshold, self.proxy_threshold)
        self.assertEqual(proxy.proxy_matches, [])
        
    def test_proxy_creation_with_matches(self):
        # Test creation with matches
        my_matches = [(self.gps1, [self.gps2, self.gps3])]
        proxy = Proxy(self.proxy_threshold, my_matches)
        self.assertEqual(proxy.proxy_matches, my_matches)

    def test_proxy_to_dict(self):
        matches = [(self.gps1, [self.gps2, self.gps3])]
        proxy = Proxy(self.proxy_threshold, matches)
        proxy_dict = proxy.toDict()
        
        self.assertEqual(proxy_dict["proxy_threshold"], self.proxy_threshold)
        self.assertEqual(len(proxy_dict["proxy_matches"]), 1)
        self.assertIsInstance(proxy_dict["last_update"], float)

    def test_proxy_from_dict(self):
        matches = [(self.gps1, [self.gps2, self.gps3])]
        original = Proxy(self.proxy_threshold, matches)
        proxy_dict = original.toDict()
        
        restored = Proxy.fromDict(proxy_dict)
        self.assertEqual(restored.proxy_threshold, original.proxy_threshold)
        self.assertEqual(len(restored.proxy_matches), len(original.proxy_matches))
        self.assertEqual(restored.last_update, original.last_update)

class TestMediaProxies(unittest.TestCase):
    def setUp(self):
        self.gps1 = GPS(45.5, -122.6)
        self.gps2 = GPS(45.51, -122.61)
        self.gps3 = GPS(45.52, -122.62)
        self.proxy_threshold = 0.5
        self.proxies = MediaProxies("test_group", [self.gps1, self.gps2, self.gps3])

    def test_proxies_initialization(self):
        self.assertEqual(self.proxies.label, "test_group")
        self.assertEqual(self.proxies.group_locations, [self.gps1, self.gps2, self.gps3])
        self.assertEqual(self.proxies.proxies, {})

    def test_proxies_matching(self):
        # Find proxies
        found = self.proxies.find_proxies(
            "other_group",
            self.proxy_threshold,
            [self.gps2, self.gps3],
            time.time()
        )
        
        # Verify proxies were found
        self.assertEqual(found, 2)
        self.assertIn("other_group", self.proxies.proxies)
        proxy = self.proxies.proxies["other_group"]
        self.assertEqual(proxy.proxy_threshold, self.proxy_threshold)

    def test_proxies_serialization(self):
        # Add a proxy to test serialization
        proxy = Proxy(
            self.proxy_threshold,
            [(self.gps1, [self.gps2, self.gps3])]
        )
        self.proxies.proxies["test_proxy"] = proxy
        
        # Convert to dict
        proxies_dict = self.proxies.toDict()
        
        # Create new instance from dict
        restored = MediaProxies.fromDict(proxies_dict)
        
        # Verify data consistency
        self.assertEqual(restored.label, self.proxies.label)
        self.assertIn("test_proxy", restored.proxies)
        restored_proxy = restored.proxies["test_proxy"]
        self.assertEqual(restored_proxy.proxy_threshold, self.proxy_threshold)
        self.assertEqual(len(restored_proxy.proxy_matches), 1)

class TestMediaProxiesController(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.controller = MediaProxiesControler(self.temp_dir)
        
        # Create test GPS points
        self.gps1 = GPS(45.5, -122.6)
        self.gps2 = GPS(45.5, -122.6)
        self.proxy_threshold = 0.1

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_controller_initialization(self):
        self.assertEqual(self.controller.working_directory, self.temp_dir)
        self.assertIsNone(self.controller.proxies)

    def test_proxy_finding(self):
        # Create controller's MediaGroups
        controller_groups = MediaGroups(grouping_threshold=self.proxy_threshold)
        controller_groups.groups = [
            MediaGroups.Group(self.gps1, ["file1.jpg"])
        ]
        
        # Create the directory structure for controller
        medialocation_dir = os.path.join(self.temp_dir, MEDIALOCATION_DIR)
        os.makedirs(medialocation_dir, exist_ok=True)
        groups_path = os.path.join(medialocation_dir, MEDIAGROUPS_STORE_NAME)
        with open(groups_path, 'w') as f:
            json.dump(controller_groups.toDict(), f)

        # Create another MediaGroups to test proximity
        source_groups = MediaGroups(grouping_threshold=self.proxy_threshold)
        source_groups.groups = [
            MediaGroups.Group(self.gps2, ["file2.jpg"])
        ]
        
        # Create a separate directory for source groups
        source_dir = tempfile.mkdtemp()
        try:
            # Create the directory structure for source groups
            source_medialocation = os.path.join(source_dir, MEDIALOCATION_DIR)
            os.makedirs(source_medialocation, exist_ok=True)
            source_groups_path = os.path.join(source_medialocation, MEDIAGROUPS_STORE_NAME)
            with open(source_groups_path, 'w') as f:
                json.dump(source_groups.toDict(), f)
            
            # Use the controller with a context manager
            with self.controller as controller:
                # Find proxies using the source directory
                proxy_count = controller.find_proxies(source_dir, self.proxy_threshold)
                self.assertGreater(proxy_count, 0)
                
            self.assertIsNotNone(self.controller.proxies)
        finally:
            shutil.rmtree(source_dir)

    def test_store_operations(self):
        # Create controller's MediaGroups
        controller_groups = MediaGroups(grouping_threshold=self.proxy_threshold)
        controller_groups.groups = [
            MediaGroups.Group(self.gps1, ["file1.jpg"])
        ]
        
        # Create the directory structure for controller
        medialocation_dir = os.path.join(self.temp_dir, MEDIALOCATION_DIR)
        os.makedirs(medialocation_dir, exist_ok=True)
        groups_path = os.path.join(medialocation_dir, MEDIAGROUPS_STORE_NAME)
        with open(groups_path, 'w') as f:
            json.dump(controller_groups.toDict(), f)

        # Create another MediaGroups to test proximity
        source_groups = MediaGroups(grouping_threshold=self.proxy_threshold)
        source_groups.groups = [
            MediaGroups.Group(self.gps2, ["file2.jpg"])
        ]
        
        # Create a separate directory for source groups
        source_dir = tempfile.mkdtemp()
        try:
            # Create the directory structure for source groups
            source_medialocation = os.path.join(source_dir, MEDIALOCATION_DIR)
            os.makedirs(source_medialocation, exist_ok=True)
            source_groups_path = os.path.join(source_medialocation, MEDIAGROUPS_STORE_NAME)
            with open(source_groups_path, 'w') as f:
                json.dump(source_groups.toDict(), f)
            
            # Test open and commit operations
            with self.controller:
                # First find proxies
                proxy_count = self.controller.find_proxies(source_dir, self.proxy_threshold)
                self.assertGreater(proxy_count, 0)
                
                # Then commit the changes
                self.controller.commit()
            
            # Verify file was created
            store_path = os.path.join(self.temp_dir, MEDIAPROXIES_STORE_PATH)
            self.assertTrue(os.path.exists(store_path))
            
            # Verify data can be loaded
            with open(store_path, 'r') as f:
                data = json.load(f)
            self.assertIn("label", data)
            self.assertEqual(data["label"], os.path.basename(os.path.realpath(self.temp_dir)))
        finally:
            shutil.rmtree(source_dir)

if __name__ == '__main__':
    unittest.main()
