import unittest
from medialocate.media.location_grouping import MediaGroups
from medialocate.location.gps import GPS

class TestMediaGroupsGroup(unittest.TestCase):
    def setUp(self):
        self.gps = GPS(45.5, -122.6)
        self.media_keys = ["file1.jpg", "file2.jpg"]

    def test_group_creation(self):
        group = MediaGroups.Group(self.gps, self.media_keys)
        self.assertEqual(group.gps, self.gps)
        self.assertEqual(group.media_keys, self.media_keys)

    def test_group_to_dict(self):
        group = MediaGroups.Group(self.gps, self.media_keys)
        group_dict = group.toDict()
        
        self.assertEqual(group_dict["gps"], self.gps.toDict())
        self.assertEqual(group_dict["media_keys"], self.media_keys)

    def test_group_from_dict(self):
        original = MediaGroups.Group(self.gps, self.media_keys)
        group_dict = original.toDict()
        
        restored = MediaGroups.Group.fromDict(group_dict)
        self.assertEqual(restored.gps.latitude, original.gps.latitude)
        self.assertEqual(restored.gps.longitude, original.gps.longitude)
        self.assertEqual(restored.media_keys, original.media_keys)

class TestMediaGroups(unittest.TestCase):
    def setUp(self):
        self.threshold = 0.1  # 100 meters
        self.groups = MediaGroups(self.threshold)
        
        # Create test GPS points
        self.gps1 = GPS(45.5, -122.6)  # Portland
        self.gps2 = GPS(45.51, -122.61)  # ~150m away
        self.gps3 = GPS(45.52, -122.62)  # ~300m away
        self.gps4 = GPS(47.6, -122.3)  # Seattle - far away
        
        # Create test location data
        self.locations = {
            "file1.jpg": {"gps": {"latitude": 45.5, "longitude": -122.6}},
            "file2.jpg": {"gps": {"latitude": 45.51, "longitude": -122.61}},
            "file3.jpg": {"gps": {"latitude": 45.52, "longitude": -122.62}},
            "file4.jpg": {"gps": {"latitude": 47.6, "longitude": -122.3}},
        }

    def test_groups_initialization(self):
        self.assertEqual(self.groups.grouping_threshold, self.threshold)
        self.assertEqual(len(self.groups.groups), 0)

    def test_add_locations_new_group(self):
        # Add a single location
        single_location = {
            "file1.jpg": {"gps": {"latitude": 45.5, "longitude": -122.6}}
        }
        self.groups.add_locations(single_location)
        
        self.assertEqual(len(self.groups.groups), 1)
        self.assertEqual(len(self.groups.groups[0].media_keys), 1)
        self.assertEqual(self.groups.groups[0].media_keys[0], "file1.jpg")

    def test_add_locations_merge_groups(self):
        # Add locations that should be merged based on threshold
        close_locations = {
            "file1.jpg": {"gps": {"latitude": 45.5, "longitude": -122.6}},
            "file2.jpg": {"gps": {"latitude": 45.5, "longitude": -122.601}}  # Very close
        }
        self.groups.add_locations(close_locations)
        
        self.assertEqual(len(self.groups.groups), 1)
        self.assertEqual(len(self.groups.groups[0].media_keys), 2)

    def test_add_locations_separate_groups(self):
        # Add locations that should create separate groups
        self.groups.add_locations(self.locations)
        
        # Should create at least 2 groups (nearby locations and Seattle)
        self.assertGreater(len(self.groups.groups), 1)

    def test_add_locations_empty_input(self):
        # Test with empty input
        self.groups.add_locations({})
        self.assertEqual(len(self.groups.groups), 0)

    def test_serialization(self):
        # Add some test data
        self.groups.add_locations(self.locations)
        
        # Convert to dict
        groups_dict = self.groups.toDict()
        
        # Create new instance from dict
        restored = MediaGroups.fromDict(groups_dict)
        
        # Verify data consistency
        self.assertEqual(restored.grouping_threshold, self.groups.grouping_threshold)
        self.assertEqual(len(restored.groups), len(self.groups.groups))
        
        # Verify group contents
        for orig_group, rest_group in zip(self.groups.groups, restored.groups):
            self.assertEqual(orig_group.gps.latitude, rest_group.gps.latitude)
            self.assertEqual(orig_group.gps.longitude, rest_group.gps.longitude)
            self.assertEqual(orig_group.media_keys, rest_group.media_keys)

    def test_add_locations_with_invalid_gps(self):
        # Test with invalid GPS coordinates
        invalid_locations = {
            "file1.jpg": {"gps": {"latitude": 91, "longitude": 181}},  # Invalid coordinates
            "file2.jpg": {"gps": {"latitude": "invalid", "longitude": "invalid"}},  # Invalid types
            "file3.jpg": {"gps": {}},  # Missing coordinates
            "file4.jpg": {},  # Missing GPS
        }
        
        # Should handle invalid data gracefully
        self.groups.add_locations(invalid_locations)
        self.assertEqual(len(self.groups.groups), 0)

    def test_add_locations_invalid_gps(self):
        # Test with invalid GPS data
        invalid_locations = {
            "file1.jpg": {"gps": {"latitude": "invalid", "longitude": -122.6}},
            "file2.jpg": {"gps": {"latitude": 45.5, "longitude": -122.6}},
            "file3.jpg": {"gps": {"latitude": 91, "longitude": -122.6}},  # Invalid latitude
            "file4.jpg": {},  # Missing GPS data
            "file5.jpg": {"gps": {}}  # Empty GPS data
        }
        
        # Should not raise exception and should only add valid location
        self.groups.add_locations(invalid_locations)
        
        # Only file2.jpg should be added successfully
        self.assertEqual(len(self.groups.groups), 1)
        self.assertEqual(len(self.groups.groups[0].media_keys), 1)
        self.assertEqual(self.groups.groups[0].media_keys[0], "file2.jpg")

    def test_add_locations_zero_coordinates(self):
        # Test with zero coordinates
        zero_locations = {
            "file1.jpg": {"gps": {"latitude": 0, "longitude": 0}},
        }
        
        # Should handle zero coordinates gracefully
        self.groups.add_locations(zero_locations)
        
        # Should create a group at (0,0)
        self.assertEqual(len(self.groups.groups), 1)
        self.assertEqual(self.groups.groups[0].gps.latitude, 0)
        self.assertEqual(self.groups.groups[0].gps.longitude, 0)

if __name__ == '__main__':
    unittest.main()
