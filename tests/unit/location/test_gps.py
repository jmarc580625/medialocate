import unittest
from medialocate.location.gps import GPS


class TestGPS(unittest.TestCase):
    def test_valid_coordinates(self):
        # Test valid coordinate creation
        gps = GPS(45.5, -122.6)
        self.assertEqual(gps.latitude, 45.5)
        self.assertEqual(gps.longitude, -122.6)

    def test_invalid_coordinate_types(self):
        # Test invalid coordinate types
        with self.assertRaises(TypeError):
            GPS("45.5", -122.6)
        with self.assertRaises(TypeError):
            GPS(45.5, "122.6")
        with self.assertRaises(TypeError):
            GPS(None, -122.6)
        with self.assertRaises(TypeError):
            GPS(45.5, None)

    def test_invalid_coordinate_values(self):
        # Test coordinates outside valid ranges
        with self.assertRaises(ValueError):
            GPS(91, 0)  # Invalid latitude (>90)
        with self.assertRaises(ValueError):
            GPS(-91, 0)  # Invalid latitude (<-90)
        with self.assertRaises(ValueError):
            GPS(0, 181)  # Invalid longitude (>180)
        with self.assertRaises(ValueError):
            GPS(0, -181)  # Invalid longitude (<-180)

    def test_distance_calculation(self):
        # Test distance calculation between two points
        point1 = GPS(45.5, -122.6)  # Portland, OR approximate
        point2 = GPS(47.6, -122.3)  # Seattle, WA approximate

        # Distance should be approximately 280 km
        distance = point1.distance_to(point2)
        self.assertGreater(distance, 200)  # At least 250 km
        self.assertLess(distance, 250)  # Less than 300 km

    def test_distance_to_same_point(self):
        # Test distance calculation to same point (should be 0)
        point = GPS(45.5, -122.6)
        self.assertEqual(point.distance_to(point), 0)

    def test_distance_to_antipode(self):
        # Test distance to antipode (opposite point on Earth)
        point1 = GPS(0, 0)
        point2 = GPS(0, 180)
        distance = point1.distance_to(point2)
        self.assertAlmostEqual(
            distance, 20015.1, delta=0.2
        )  # Half Earth's circumference in km

    def test_str_representation(self):
        # Test string representation
        gps = GPS(45.5, -122.6)
        expected_str = "GPS(45.5, -122.6)"
        self.assertEqual(str(gps), expected_str)


if __name__ == "__main__":
    unittest.main()
