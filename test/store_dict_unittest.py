import os
import json
import shutil
import unittest
import tempfile
from store.dict import DictStore

class TestStore(unittest.TestCase):

    def setUp(self):
        self.working_directory = tempfile.mkdtemp()
        self.store_path = os.path.join(self.working_directory, 'store')
        self.store_filename = 'test.json'
        self.store_file = os.path.join(self.store_path, self.store_filename)

        os.makedirs(self.store_path)

    def tearDown(self):
        shutil.rmtree(self.working_directory)

    """
    __init__ unit tests
    """
    def test_init(self):
        # Arrange
        pass

        # Act
        pm = DictStore( self.store_path, self.store_filename)

        # Assert
        self.assertEqual(pm.directory, self.store_path)
        self.assertEqual(pm.touched, False)
        self.assertEqual(pm.opened, False)
        self.assertEqual(pm.data, None)

    """
    open unit tests
    """
    def test_open_with_non_existing_store_directory(self):
        # Arrange
        store_dirname = 'donotexist'
        non_existent_directory = os.path.join(self.working_directory, store_dirname)
        store_file = os.path.join(non_existent_directory, self.store_filename)
        pm = DictStore(non_existent_directory, self.store_filename)

        # Act
        pm.open()

        # Assert
        self.assertEqual(os.path.exists(non_existent_directory), True)
        self.assertEqual(os.path.exists(store_file), True)
        self.assertEqual(pm.data, {})
        with open(store_file, 'r') as f:
            self.assertEqual(len(json.load(f)), 0)

    def test_open_with_existing_store_file(self):
        # Arrange
        pm = DictStore(self.store_path, self.store_filename)

        # Act
        pm.open()

        # Assert
        self.assertEqual(os.path.exists(self.store_file), True)
        self.assertEqual(pm.data, {})
        with open(self.store_file, 'r') as f:
            self.assertEqual(len(json.load(f)), 0)

    def test_open_with_existing_empty_store_file(self):
        # Arrange
        with open(self.store_file, 'w') as f:
            json.dump({}, f)
        pm = DictStore(self.store_path, self.store_filename)

        # Act
        pm.open()

        # Assert
        self.assertEqual(pm.data, {})

    def test_open_with_malformed_store_file_content(self):
        # Arrange
        with open(self.store_file, 'w') as f:
            f.write('{"key1": "value1", "key2": "value2", "key3":') 
        pm = DictStore(self.store_path, self.store_filename)

        # Act & Assert
        with self.assertRaises(Exception):
            pm.open()

    def test_open_with_existing_non_empty_store_file(self):
        # Arrange
        item1_key = 'key1'
        item1_value = {'value': 'value1'}
        item2_key = 'key2'
        item2_value = {'value': 'value2'}
        item3_key = 'key3'
        item3_value = {'value': 'value3'}
        data = {item1_key: item1_value, item2_key: item2_value, item3_key: item3_value}
        with open(self.store_file, 'w') as f:
                json.dump(data, f)
        pm = DictStore(self.store_path, self.store_filename)

        # Act
        pm.open()

        # Assert
        self.assertEqual(pm.data, data)

    """
    updateItem unit tests
    """
    
    def test_updateItem_with_non_existing_store_file(self):
        # Arrange
        item1_key = 'key1'
        item1_value = {'value': 'value1'}
        item2_key = 'key2'
        item2_value = {'value': 'value2'}
        pm = DictStore(self.store_path, self.store_filename)
        pm.open()

        # Act
        pm.updateItem(item1_key, item1_value)
        pm.updateItem(item2_key, item2_value)

        # Assert
        self.assertEqual(pm.touched, True)
        self.assertEqual(pm.data[item1_key], item1_value)
        self.assertEqual(pm.data[item2_key], item2_value)
    
    def test_updateItem_with_existing_store_file(self):
        # Arrange
        item1_key = 'key1'
        item1_value = {'value': 'value1'}
        item2_key = 'key2'
        item2_value = {'value': 'value2'}
        item3_key = 'key3'
        item3_value = {'value': 'value3'}
        data = {item1_key: item1_value, item2_key: item2_value}
        with open(self.store_file, 'w') as f:
                json.dump(data, f)
        pm = DictStore(self.store_path, self.store_filename)
        pm.open()

        # Act
        pm.updateItem(item3_key, item3_value)

        # Assert
        self.assertEqual(pm.data[item1_key], item1_value)
        self.assertEqual(pm.data[item2_key], item2_value)
        self.assertEqual(pm.data[item3_key], item3_value)
        self.assertEqual(pm.touched, True)


    def test_updateItem_twice_with_existing_store_file(self):
        # Arrange
        item1_key = 'key1'
        item1_value = {'value': 'value1'}
        item2_key = 'key2'
        item2_value = {'value': 'value2'}
        item3_key = 'key3'
        item3_value = {'value': 'value3'}
        item3_valueX = {'value': 'value3X'}
        item3_valueY = {'value': 'value3Y'}
        data = {item1_key: item1_value, item2_key: item2_value}
        with open(self.store_file, 'w') as f:
                json.dump(data, f)
        pm = DictStore(self.store_path, self.store_filename)
        pm.open()

        # Act
        pm.updateItem(item3_key, item3_valueX)
        pm.updateItem(item3_key, item3_valueY)

        # Assert
        self.assertEqual(pm.data[item1_key], item1_value)
        self.assertEqual(pm.data[item2_key], item2_value)
        self.assertEqual(pm.data[item3_key], item3_valueY)
        self.assertEqual(pm.touched, True)


    """
    commit unit tests
    """

    def test_commit_without_update(self):
        # Arrange
        item1_key = 'key1'
        item1_value = {'value': 'value1'}
        item2_key = 'key2'
        item2_value = {'value': 'value2'}
        data = {item1_key: item1_value, item2_key: item2_value}
        with open(self.store_file, 'w') as f:
                json.dump(data, f)
        time_before = os.path.getmtime(self.store_file)  
        pm = DictStore(self.store_path, self.store_filename)
        pm.open()

        # Act
        pm.commit()

        # Assert
        self.touched = False
        self.assertEqual(os.path.getmtime(self.store_file), time_before)

    def test_commit_with_update(self):
        # Arrange
        item1_key = 'key1'
        item1_value = {'value': 'value1'}
        item2_key = 'key2'
        item2_value = {'value': 'value2'}
        item3_key = 'key3'
        item3_value = {'value': 'value3'}
        data_before = {item1_key: item1_value, item2_key: item2_value}
        data_after = {item1_key: item1_value, item2_key: item2_value, item3_key: item3_value}
        with open(self.store_file, 'w') as f:
                json.dump(data_before, f)
        time_before = os.path.getmtime(self.store_file)  
        pm = DictStore(self.store_path, self.store_filename)
        pm.open()

        # Act

        pm.updateItem(item3_key, item3_value)
        pm.commit()

        # Assert
        self.touched = False
        self.assertNotEqual(os.path.getmtime(self.store_file), time_before)
        with open(self.store_file, 'r') as f:
            self.assertEqual(json.load(f), data_after)

    """
    drop unit tests
    """

    def test_drop(self):
        # Arrange
        item1_key = 'key1'
        item1_value = {'value': 'value1'}
        item2_key = 'key2'
        item2_value = {'value': 'value2'}
        data = {item1_key: item1_value, item2_key: item2_value}
        with open(self.store_file, 'w') as f:
                json.dump(data, f)
        time_before = os.path.getmtime(self.store_file)  
        pm = DictStore(self.store_path, self.store_filename)

        # Act
        pm.drop()

        # Assert
        self.assertEqual(pm.data, {})

    """
    popItem unit tests
    """
    def test_popItem_with_existing_item(self):
        # Arrange
        item1_key = 'key1'
        item1_value = {'value': 'value1'}
        item2_key = 'key2'
        item2_value = {'value': 'value2'}
        item3_key = 'key3'
        item3_value = {'value': 'value3'}
        data_before = {item1_key: item1_value, item2_key: item2_value, item3_key: item3_value}
        data_after = {item1_key: item1_value, item3_key: item3_value}
        with open(self.store_file, 'w') as f:
                json.dump(data_before, f)
        pm = DictStore(self.store_path, self.store_filename)
        pm.open()

        # Act
        val = pm.popItem(item2_key)

        # Assert
        self.assertEqual(val, item2_value)
        self.assertEqual(pm.touched, True)
        self.assertEqual(pm.data, data_after)

    def test_popItem_with_non_existing_item(self):
        # Arrange
        item1_key = 'key1'
        item1_value = {'value': 'value1'}
        item2_key = 'key2'
        item3_key = 'key3'
        item3_value = {'value': 'value3'}
        data = {item1_key: item1_value, item3_key: item3_value}
        with open(self.store_file, 'w') as f:
                json.dump(data, f)
        pm = DictStore(self.store_path, self.store_filename)
        pm.open()

        # Act
        val = pm.popItem(item2_key)

        # Assert
        self.assertEqual(val, None)
        self.assertEqual(pm.touched, False)
        self.assertEqual(pm.data, data)

    """
    getItem unit tests
    """
    def test_getItem_with_existing_item(self):
        # Arrange
        item1_key = 'key1'
        item1_value = {'value': 'value1'}
        item2_key = 'key2'
        item2_value = {'value': 'value2'}
        item3_key = 'key3'
        item3_value = {'value': 'value3'}
        data = {item1_key: item1_value, item2_key: item2_value, item3_key: item3_value}
        with open(self.store_file, 'w') as f:
                json.dump(data, f)
        pm = DictStore(self.store_path, self.store_filename)
        pm.open()

        # Act
        val = pm.getItem(item2_key)

        # Assert
        self.assertEqual(val, item2_value)
        self.assertEqual(pm.touched, False)
        self.assertEqual(pm.data, data)

    def test_getItem_with_non_existing_item(self):
        # Arrange
        item1_key = 'key1'
        item1_value = {'value': 'value1'}
        item2_key = 'key2'
        item3_key = 'key3'
        item3_value = {'value': 'value3'}
        data = {item1_key: item1_value, item3_key: item3_value}
        with open(self.store_file, 'w') as f:
                json.dump(data, f)
        pm = DictStore(self.store_path, self.store_filename)
        pm.open()

        # Act
        val = pm.popItem(item2_key)

        # Assert
        self.assertEqual(val, None)
        self.assertEqual(pm.touched, False)
        self.assertEqual(pm.data, data)

    """
    items unit tests
    """
    def test_getItem_with_existing_item(self):
        # Arrange
        item1_key = 'key1'
        item1_value = {'value': 'value1'}
        item2_key = 'key2'
        item2_value = {'value': 'value2'}
        item3_key = 'key3'
        item3_value = {'value': 'value3'}
        data = {item1_key: item1_value, item2_key: item2_value, item3_key: item3_value}
        expected_keys = [item1_key, item2_key, item3_key]
        expected_values = [item1_value, item2_value, item3_value]
        actual_keys = []
        actual_values = []
        with open(self.store_file, 'w') as f:
                json.dump(data, f)
        pm = DictStore(self.store_path, self.store_filename)
        pm.open()

        # Act
        for key, val in pm.items():
            actual_keys.append(key)
            actual_values.append(val)

        # Assert
        self.assertEqual(pm.touched, False)
        self.assertEqual(actual_keys, expected_keys)
        self.assertEqual(actual_values, expected_values)

    """
    unit tests with closed store
    """
    def test_open_with_closed_store(self):
        # Arrange
        pm = DictStore( self.store_path, self.store_filename)

        # Act & Assert
        with self.assertRaises(Exception):
            pm.commit()

        with self.assertRaises(Exception):
            pm.updateItem('key', {'value': 'value'})

        with self.assertRaises(Exception):
            rec = pm.getItem('key')

        with self.assertRaises(Exception):
            rec = pm.popItem('key')

        with self.assertRaises(Exception):
            for key, val in pm.items():
                pass

    """
    "with" usage unit tests 
    """
    def test_open_with_closed_store(self):
        # Arrange
        item1_key = 'key1'
        item1_value = {'value': 'value1'}
        item1_valueX = {'value': 'valueX'}
        item2_key = 'key2'
        item2_value = {'value': 'value2'}
        item3_key = 'key3'
        item3_value = {'value': 'value3'}
        initial_data = {item1_key: item1_value, item2_key: item2_value, item3_key: item3_value}
        expected_data = {item1_key: item1_valueX, item3_key: item3_value}

        with open(self.store_file, 'w') as f:
            json.dump(initial_data, f)

        # Act
        with DictStore(self.store_path, self.store_filename) as pm:
                for key, val in pm.items():
                    pass
                pm.updateItem(item1_key, item1_valueX)
                pm.popItem(item2_key)

        # Assert
        self.assertEqual(pm.opened, False)
        with open(self.store_file, 'r') as f:
            self.assertEqual(json.load(f), expected_data)

    """
    object_to_dict unit tests 
    """
    def test_object_to_dict(self):
        #TODO: implement
        # Arrange
        # Act
        # Assert
        pass

    """
    size unit tests 
    """
    def test_size(self):
        #TODO: implement
        # Arrange
        # Act
        # Assert
        pass

    """
    is_touched unit tests 
    """
    def test_is_touched(self):
        #TODO: implement
        # Arrange
        # Act
        # Assert
        pass

if __name__ == '__main__':
    unittest.main()