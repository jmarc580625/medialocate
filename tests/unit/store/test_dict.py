"""Unit tests for the DictStore class."""

import os
import json
import shutil
import tempfile
import unittest


from medialocate.store.dict import DictStore


class TestDictStore(unittest.TestCase):
    """Test suite for DictStore class."""

    def setUp(self) -> None:
        """Set up test environment."""
        self.store_dir = tempfile.mkdtemp()
        self.store_name = "test_store.json"
        self.store_path = os.path.join(self.store_dir, self.store_name)

    def tearDown(self) -> None:
        """Clean up test environment."""
        shutil.rmtree(self.store_dir, ignore_errors=True)

    def test_init_creates_empty_store(self) -> None:
        """Test DictStore initialization with non existing store file"""
        # Arrange
        self.assertFalse(os.path.exists(self.store_path))

        # Act
        store = DictStore(self.store_dir, self.store_name)

        # Assert
        self.assertFalse(os.path.exists(self.store_path))
        self.assertFalse(store._is_open)
        self.assertEqual(store._store, {})

    def test_init_with_non_existing_directory(self) -> None:
        """Test DictStore initialization with non existing directory"""
        # Arrange
        store_dirname = "donotexist"
        non_existent_directory = os.path.join(self.store_dir, store_dirname)
        store_file = os.path.join(non_existent_directory, "test.json")
        self.assertFalse(os.path.exists(store_file))

        # Act
        with self.assertRaises(FileNotFoundError):
            _ = DictStore(non_existent_directory, self.store_name)

    def test_open_with_non_existing_store_file(self) -> None:
        """Test open with non existing store file"""
        # Arrange
        self.assertFalse(os.path.exists(self.store_path))
        store = DictStore(self.store_dir, self.store_name)

        # Act
        store.open()

        # Assert
        self.assertFalse(os.path.exists(self.store_path))
        self.assertTrue(store._is_open)
        self.assertEqual(store._store, {})

    def test_open_with_existing_store_file(self):
        """Test open with existing store file"""
        # Arrange
        dict = {"key1": "value1", "key2": "value2", "key3": "value3"}
        with open(self.store_path, "w") as f:
            json.dump(dict, f)
        store = DictStore(self.store_dir, self.store_name)

        # Act
        store.open()

        # Assert
        self.assertEqual(os.path.exists(self.store_path), True)
        self.assertEqual(store._store, dict)

    def test_open_with_existing_empty_store_file(self):
        """Test open with existing empty store file"""
        # Arrange
        with open(self.store_path, "w") as f:
            f.write("")
        store = DictStore(self.store_dir, self.store_name)

        # Act
        with self.assertRaises(ValueError):
            store.open()

    def test_open_with_malformed_store_file_content(self):
        """Test open with malformed store file content"""
        # Arrange
        str = '"key1": "value1", "key2": "value2", "key3":}'
        with open(self.store_path, "w") as f:
            f.write(str)
        store = DictStore(self.store_dir, self.store_name)

        # Act & Assert
        with self.assertRaises(Exception):
            store.open()

    def test_update_item_with_non_existing_store_file(self):
        """Test update item with non existing store file"""
        # Arrange
        item1_key = "key1"
        item1_value = {"value": "value1"}
        store = DictStore(self.store_dir, self.store_name)
        store.open()

        # Act
        store.set(item1_key, item1_value)

        # Assert
        self.assertEqual(store._touched, True)
        self.assertEqual(store._store[item1_key], item1_value)

    def test_update_item_with_existing_store_file(self):
        """Test update item with existing store file"""
        # Arrange
        item1_key = "key1"
        item1_value = {"value": "value1"}
        item2_key = "key2"
        item2_value = {"value": "value2"}
        item3_key = "key3"
        item3_value = {"value": "value3"}
        data = {item1_key: item1_value, item2_key: item2_value}
        with open(self.store_path, "w") as f:
            json.dump(data, f)
        store = DictStore(self.store_dir, self.store_name)
        store.open()

        # Act
        store.set(item3_key, item3_value)

        # Assert
        self.assertEqual(store._store[item1_key], item1_value)
        self.assertEqual(store._store[item2_key], item2_value)
        self.assertEqual(store._store[item3_key], item3_value)
        self.assertEqual(store._touched, True)

    def test_update_item_twice_with_existing_store_file(self):
        """Test update item twice with existing store file"""
        # Arrange
        item1_key = "key1"
        item1_value = {"value": "value1"}
        item2_key = "key2"
        item2_value = {"value": "value2"}
        item3_key = "key3"
        item3_value_x = {"value": "value3X"}
        item3_value_y = {"value": "value3Y"}
        data = {item1_key: item1_value, item2_key: item2_value}
        with open(self.store_path, "w") as f:
            json.dump(data, f)
        store = DictStore(self.store_dir, self.store_name)
        store.open()

        # Act
        store.set(item3_key, item3_value_x)
        store.set(item3_key, item3_value_y)

        # Assert
        self.assertEqual(store._store[item1_key], item1_value)
        self.assertEqual(store._store[item2_key], item2_value)
        self.assertEqual(store._store[item3_key], item3_value_y)
        self.assertEqual(store._touched, True)

    def test_commit_without_update(self):
        """Test commit without update"""
        # Arrange
        item1_key = "key1"
        item1_value = {"value": "value1"}
        item2_key = "key2"
        item2_value = {"value": "value2"}
        data = {item1_key: item1_value, item2_key: item2_value}
        with open(self.store_path, "w") as f:
            json.dump(data, f)
        time_before = os.path.getmtime(self.store_path)
        store = DictStore(self.store_dir, self.store_name)
        store.open()

        # Act
        store.sync()

        # Assert
        self.assertEqual(store._touched, False)
        self.assertEqual(os.path.getmtime(self.store_path), time_before)

    def test_commit_with_update(self):
        """Test commit with update"""
        # Arrange
        item1_key = "key1"
        item1_value = {"value": "value1"}
        item2_key = "key2"
        item2_value = {"value": "value2"}
        item3_key = "key3"
        item3_value = {"value": "value3"}
        data_before = {item1_key: item1_value, item2_key: item2_value}
        data_after = {
            item1_key: item1_value,
            item2_key: item2_value,
            item3_key: item3_value,
        }
        with open(self.store_path, "w") as f:
            json.dump(data_before, f)
        time_before = os.path.getmtime(self.store_path)
        store = DictStore(self.store_dir, self.store_name)
        store.open()

        # Act
        store.set(item3_key, item3_value)
        store.sync()

        # Assert
        self.assertEqual(store._touched, False)
        self.assertNotEqual(os.path.getmtime(self.store_path), time_before)
        with open(self.store_path, "r") as f:
            self.assertEqual(json.load(f), data_after)

    def test_clear(self):
        """Test clear"""
        # Arrange
        item1_key = "key1"
        item1_value = {"value": "value1"}
        item2_key = "key2"
        item2_value = {"value": "value2"}
        data = {item1_key: item1_value, item2_key: item2_value}
        with open(self.store_path, "w") as f:
            json.dump(data, f)
        store = DictStore(self.store_dir, self.store_name)
        store.open()

        # Act
        store.clear()

        # Assert
        self.assertEqual(store._store, {})

    def test_pop_item_with_existing_item(self):
        """Test pop item with existing item"""
        # Arrange
        item1_key = "key1"
        item1_value = {"value": "value1"}
        item2_key = "key2"
        item2_value = {"value": "value2"}
        item3_key = "key3"
        item3_value = {"value": "value3"}
        data_before = {
            item1_key: item1_value,
            item2_key: item2_value,
            item3_key: item3_value,
        }
        data_after = {item1_key: item1_value, item3_key: item3_value}
        with open(self.store_path, "w") as f:
            json.dump(data_before, f)
        store = DictStore(self.store_dir, self.store_name)
        store.open()

        # Act
        val = store.pop(item2_key)

        # Assert
        self.assertEqual(val, item2_value)
        self.assertEqual(store._touched, True)
        self.assertEqual(store._store, data_after)

    def test_pop_item_with_non_existing_item(self):
        """Test pop item with non existing item"""
        # Arrange
        item1_key = "key1"
        item1_value = {"value": "value1"}
        item2_key = "key2"
        item3_key = "key3"
        item3_value = {"value": "value3"}
        data = {item1_key: item1_value, item3_key: item3_value}
        with open(self.store_path, "w") as f:
            json.dump(data, f)
        store = DictStore(self.store_dir, self.store_name)
        store.open()

        # Act
        val = store.pop(item2_key)

        # Assert
        self.assertEqual(val, None)
        self.assertEqual(store._touched, False)
        self.assertEqual(store._store, data)

    def test_get_item_with_non_existing_item(self):
        """Test get item with non existing item"""
        # Arrange
        item1_key = "key1"
        item1_value = {"value": "value1"}
        item2_key = "key2"
        item3_key = "key3"
        item3_value = {"value": "value3"}
        data = {item1_key: item1_value, item3_key: item3_value}
        with open(self.store_path, "w") as f:
            json.dump(data, f)
        store = DictStore(self.store_dir, self.store_name)
        store.open()

        # Act
        val = store.pop(item2_key)

        # Assert
        self.assertEqual(val, None)
        self.assertEqual(store._touched, False)
        self.assertEqual(store._store, data)

    def test_get_item_with_existing_item(self):
        """Test get item with existing item"""
        # Arrange
        item1_key = "key1"
        item1_value = {"value": "value1"}
        item2_key = "key2"
        item2_value = {"value": "value2"}
        item3_key = "key3"
        item3_value = {"value": "value3"}
        data = {item1_key: item1_value, item2_key: item2_value, item3_key: item3_value}
        with open(self.store_path, "w") as f:
            json.dump(data, f)
        store = DictStore(self.store_dir, self.store_name)
        store.open()

        # Act
        val = store.get(item2_key)

        # Assert
        self.assertEqual(val, item2_value)
        self.assertEqual(store._touched, False)
        self.assertEqual(store._store, data)

    def test_get_all_items_with_existing_item2(self):
        """Test get item with existing item"""
        # Arrange
        item1_key = "key1"
        item1_value = {"value": "value1"}
        item2_key = "key2"
        item2_value = {"value": "value2"}
        item3_key = "key3"
        item3_value = {"value": "value3"}
        data = {item1_key: item1_value, item2_key: item2_value, item3_key: item3_value}
        expected_keys = [item1_key, item2_key, item3_key]
        expected_values = [item1_value, item2_value, item3_value]
        actual_keys = []
        actual_values = []
        with open(self.store_path, "w") as f:
            json.dump(data, f)
        store = DictStore(self.store_dir, self.store_name)
        store.open()

        # Act
        for key, val in store.items():
            actual_keys.append(key)
            actual_values.append(val)

        # Assert
        self.assertEqual(store._touched, False)
        self.assertEqual(actual_keys, expected_keys)
        self.assertEqual(actual_values, expected_values)

    def test_actions_with_closed_store(self):
        """Test actions with closed store"""
        # Arrange
        store = DictStore(self.store_dir, self.store_name)

        # Act & Assert
        with self.assertRaises(DictStore.StoreNotOpenError):
            store.sync()

        with self.assertRaises(DictStore.StoreNotOpenError):
            store.set("key", {"value": "value"})

        with self.assertRaises(DictStore.StoreNotOpenError):
            _ = store.get("key")

        with self.assertRaises(DictStore.StoreNotOpenError):
            _ = store.pop("key")

        with self.assertRaises(DictStore.StoreNotOpenError):
            for key, val in store.items():
                pass

    def test_with_usage(self):
        """Test "with" usage"""
        # Arrange
        item1_key = "key1"
        item1_value = {"value": "value1"}
        item1_value_x = {"value": "valueX"}
        item2_key = "key2"
        item2_value = {"value": "value2"}
        item3_key = "key3"
        item3_value = {"value": "value3"}
        initial_data = {
            item1_key: item1_value,
            item2_key: item2_value,
            item3_key: item3_value,
        }
        expected_data = {item1_key: item1_value_x, item3_key: item3_value}

        with open(self.store_path, "w") as f:
            json.dump(initial_data, f)

        # Act
        with DictStore(self.store_dir, self.store_name) as store:
            for key, val in store.items():
                pass
            store.set(item1_key, item1_value_x)
            store.pop(item2_key)

        # Assert
        self.assertEqual(store._is_open, False)
        with open(self.store_path, "r") as f:
            self.assertEqual(json.load(f), expected_data)

    def test_object_to_dict(self):
        """Test object_to_dict"""
        # TODO: implement
        # Arrange
        # Act
        # Assert
        pass

    def test_size(self):
        """Test size"""
        # Arrange
        dict = {"key1": "value1", "key2": "value2", "key3": "value3"}
        with open(self.store_path, "w") as f:
            json.dump(dict, f)
        store = DictStore(self.store_dir, self.store_name)
        store.open()

        # Act
        size = len(store)

        # Assert
        self.assertEqual(size, 3)


if __name__ == "__main__":
    unittest.main()
