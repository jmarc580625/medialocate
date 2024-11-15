import unittest
from unittest.mock import patch
import time
import hashlib
from batch.status import ProcessingStatus

class TestProcessingStatus(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass


    """
    State inner class unit tests
    """

    def test_init_State_instance(self):
        # Arrange
        expected_states_list = [ProcessingStatus.State.DONE.value, ProcessingStatus.State.IGNORE.value, ProcessingStatus.State.ONGOING.value, ProcessingStatus.State.ERROR.value]

        # Act 
        states_list = ProcessingStatus.State.values()

        # Assert
        self.assertSetEqual(set(states_list), set(expected_states_list))


    """
    __init__ unit tests
    """

    @patch('store.dict.DictStore')
    def test_init_Status_instance_without_store(self, StoreMock):
        # Act
        storeMock = StoreMock.return_value
        status = ProcessingStatus(storeMock, 'key', 'status', 'filename')

        # Assert
        self.assertEqual(status.store, storeMock)
        self.assertEqual(status.key, 'key')
        self.assertEqual(status.state, 'status')
        self.assertEqual(status.filename, 'filename')
        self.assertTrue(status.time -  time.time() < 0.1)
        self.assertEqual(status._isNew, True)
        self.assertEqual(status._isUpdated, False)

    """
    hash unit tests
    """

    def test_filename_hash_empty_string(self):
        # Arrange
        # empty filename is converted to Posix path '.' to ensure hash is system independent
        hash = hashlib.md5(".".encode('utf-8')).hexdigest()

        # Act & Assert
        self.assertEqual(ProcessingStatus.filename_hash(""), hash)

    def test_filename_hash_with_ascii_string(self):
        # Arrange
        filename="hello"
        hash = hashlib.md5(filename.encode('utf-8')).hexdigest()

        # Act & Assert
        self.assertEqual(ProcessingStatus.filename_hash(filename), hash)

    def test_filename_hash_with_non_ascii_string(self):
        # Arrange
        filename="hëllo"
        hash = hashlib.md5(filename.encode('utf-8')).hexdigest()

        # Act & Assert
        self.assertEqual(ProcessingStatus.filename_hash(filename), hash)

    def test_filename_hash_with_special_characters(self):
        # Arrange
        filename="hëllo!@#$"
        hash = hashlib.md5(filename.encode('utf-8')).hexdigest()

        # Act & Assert
        self.assertEqual(ProcessingStatus.filename_hash(filename), hash)

    def test_filename_hash_with_long_string(self):
        # Arrange
        filename="a" * 1000
        hash = hashlib.md5(filename.encode('utf-8')).hexdigest()

        # Act & Assert
        self.assertEqual(ProcessingStatus.filename_hash(filename), hash)

    def test_filename_hash_with_posix_and_windows_pathnames(self):
        # Arrange
        filename_posix="hello/happy/taxpayer"
        filename_windows="hello\\happy\\taxpayer"

        # Act 
        hash_posix = ProcessingStatus.filename_hash(filename_posix)
        hash_windows = ProcessingStatus.filename_hash(filename_windows)

        # Assert
        self.assertEqual(hash_posix, hash_windows)

    """
    getFromStore unit tests
    """

    @patch('store.dict.DictStore')
    def test_getFromStore(self, StoreMock):
        # Arrange
        key = "key"
        filename = "filename"
        now = time.time()
        value = {ProcessingStatus._state_key: ProcessingStatus.State.DONE.value, 
                 ProcessingStatus._filename_key: filename, 
                 ProcessingStatus._time_key: now}
        storeMock = StoreMock.return_value
        storeMock.getItem.return_value = value
        
        # Act 
        status = ProcessingStatus.getFromStore(storeMock, key)
        
        # Assert
        self.assertIsInstance(status, ProcessingStatus)
        self.assertEqual(status.key, key)
        self.assertEqual(status.state, ProcessingStatus.State.DONE)
        self.assertEqual(status.time, now)
        self.assertEqual(status.filename, filename)

    """
    unit tests
    """

    @patch('store.dict.DictStore')
    def test_getAllFromStore(self, StoreMock):
        # Arrange
        key1 = "key1"
        key2 = "key2"
        key3 = "key3"
        filename1 = "filename1"
        filename2 = "filename2"
        filename3 = "filename3"
        now = time.time()
        value1 = {ProcessingStatus._state_key: ProcessingStatus.State.DONE.value, ProcessingStatus._filename_key: filename1, ProcessingStatus._time_key: now}
        value2 = {ProcessingStatus._state_key: ProcessingStatus.State.ERROR.value, ProcessingStatus._filename_key: filename2, ProcessingStatus._time_key: now}
        value3 = {ProcessingStatus._state_key: ProcessingStatus.State.IGNORE.value, ProcessingStatus._filename_key: filename3, ProcessingStatus._time_key: now}
        storeMock = StoreMock.return_value
        storeMock.walkItems.return_value = [(key1, value1), (key2, value2), (key3, value3)]
        
        # Act 
        statuses = list(ProcessingStatus.getAllFromStore(storeMock))
        
        # Assert
        self.assertEqual(len(statuses), 3)
        self.assertIsInstance(statuses[0], ProcessingStatus)
        self.assertEqual(statuses[0].key, key1)
        self.assertEqual(statuses[0].state, ProcessingStatus.State.DONE)
        self.assertEqual(statuses[0].time, now)
        self.assertEqual(statuses[0].filename, filename1)
        self.assertIsInstance(statuses[1], ProcessingStatus)
        self.assertEqual(statuses[1].key, key2)
        self.assertEqual(statuses[1].state, ProcessingStatus.State.ERROR)
        self.assertEqual(statuses[1].time, now)
        self.assertEqual(statuses[1].filename, filename2)
        self.assertIsInstance(statuses[2], ProcessingStatus)
        self.assertEqual(statuses[2].key, key3)
        self.assertEqual(statuses[2].state, ProcessingStatus.State.IGNORE)
        self.assertEqual(statuses[2].time, now)
        self.assertEqual(statuses[2].filename, filename3)

    """
    deleteAll unit tests
    """

    @patch('store.dict.DictStore')
    def test_deleteAll(self, StoreMock):
        # Arrange
        storeMock = StoreMock.return_value
        storeMock.clean.return_value = None

        # Act
        ProcessingStatus.deleteAll(storeMock)

        # Assert
        storeMock.clean.assert_called_once()

    """
    getter methods unit tests
    """

    @patch('store.dict.DictStore')
    def test_getFilename(self, StoreMock):
        # Arrange
        storeMock = StoreMock.return_value
        filename = "filename"
        state = ProcessingStatus.State.DONE
        now = time.time()
        status = ProcessingStatus(storeMock, 'key', state, filename, now)

        # Act 
        a_filename = status.getFilename()

        # Assert
        self.assertEqual(a_filename, filename)

    @patch('store.dict.DictStore')
    def test_getState(self, StoreMock):
        # Arrange
        storeMock = StoreMock.return_value
        filename = "filename"
        state = ProcessingStatus.State.DONE
        now = time.time()
        status = ProcessingStatus(storeMock, 'key', state, filename, now)

        # Act 
        a_state = status.getState()

        # Assert
        self.assertEqual(a_state, state)

    @patch('store.dict.DictStore')
    def test_getTime(self, StoreMock):
        # Arrange
        storeMock = StoreMock.return_value
        filename = "filename"
        state = ProcessingStatus.State.DONE
        now = time.time()
        status = ProcessingStatus(storeMock, 'key', state, filename, now)

        # Act 
        a_time = status.getTime()

        # Assert
        self.assertEqual(a_time, now)

    """
    ProcessingProcessingStatus.update unit tests
    """

    @patch('store.dict.DictStore')
    def test_update_new(self, StoreMock):
        # Arrange
        storeMock = StoreMock.return_value
        filename = "filename"
        state = ProcessingStatus.State.DONE
        now = time.time()
        status = ProcessingStatus(storeMock, 'key', state, filename, now)

        # Act 
        status.update()

        # Assert
        storeMock.updateItem.assert_called_once_with(status.key, 
                                                    {ProcessingStatus._state_key: state.value, 
                                                     ProcessingStatus._filename_key: filename, 
                                                     ProcessingStatus._time_key: now})

    @patch('store.dict.DictStore')
    def test_update_get_from_store_modified(self, StoreMock):
        # Arrange
        key = "key"
        filename = "filename"
        now = time.time()
        value = {ProcessingStatus._state_key: ProcessingStatus.State.DONE.value, 
                 ProcessingStatus._filename_key: filename, 
                 ProcessingStatus._time_key: now}
        storeMock = StoreMock.return_value
        storeMock.getItem.return_value = value
        status = ProcessingStatus.getFromStore(storeMock, key)
        
        # Act 
        status.update()

        # Assert
        storeMock.updateItem.assert_not_called() 

    @patch('store.dict.DictStore')
    def test_update_get_from_store_unmodified(self, StoreMock):
        # Arrange
        key = "key"
        filename = "filename"
        now = time.time()
        value = {ProcessingStatus._state_key: ProcessingStatus.State.DONE.value, 
                 ProcessingStatus._filename_key: filename, 
                 ProcessingStatus._time_key: now}
        storeMock = StoreMock.return_value
        storeMock.getItem.return_value = value
        status = ProcessingStatus.getFromStore(storeMock, key)
        status.setState(ProcessingStatus.State.ERROR)
        
        # Act 
        status.update()

        # Assert
        storeMock.updateItem.assert_called_once_with(status.key, 
                                                    {ProcessingStatus._state_key: status.state.value, 
                                                     ProcessingStatus._filename_key: status.filename, 
                                                     ProcessingStatus._time_key: status.time})

    """
    ProcessingProcessingStatus.delete unit tests
    """

    @patch('store.dict.DictStore')
    def test_delete_new(self, StoreMock):
        # Arrange
        storeMock = StoreMock.return_value
        filename = "filename"
        state = ProcessingStatus.State.DONE
        now = time.time()
        status = ProcessingStatus(storeMock, 'key', state, filename, now)

        # Act 
        status.delete()

        # Assert
        storeMock.updateItem.assert_not_called()

    @patch('store.dict.DictStore')
    def test_delete_get_from_store_unmodified(self, StoreMock):
        # Arrange
        key = "key"
        filename = "filename"
        now = time.time()
        value = {ProcessingStatus._state_key: ProcessingStatus.State.DONE.value, 
                 ProcessingStatus._filename_key: filename, 
                 ProcessingStatus._time_key: now}
        storeMock = StoreMock.return_value
        storeMock.getItem.return_value = value
        status = ProcessingStatus.getFromStore(storeMock, key)
        
        # Act 
        status.delete()

        # Assert
        storeMock.popItem.assert_called_once_with(status.key)

if __name__ == '__main__':
    unittest.main()