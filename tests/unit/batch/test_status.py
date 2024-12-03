import time
import hashlib
import unittest
from unittest.mock import patch
from medialocate.batch.status import ProcessingStatus

STORE_DICT = "medialocate.store.dict"


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
        expected_states_list = [
            ProcessingStatus.State.DONE.value,
            ProcessingStatus.State.IGNORE.value,
            ProcessingStatus.State.ONGOING.value,
            ProcessingStatus.State.ERROR.value,
        ]

        # Act
        states_list = ProcessingStatus.State.values()

        # Assert
        self.assertSetEqual(set(states_list), set(expected_states_list))

    """
    __init__ unit tests
    """

    @patch(f"{STORE_DICT}.DictStore")
    def test_init_Status_instance_without_store(self, StoreMock):
        """ "Test init Status instance without store"""
        # Act
        storeMock = StoreMock.return_value
        status = ProcessingStatus(storeMock, "key", "status", "filename")

        # Assert
        self.assertEqual(status.store, storeMock)
        self.assertEqual(status.key, "key")
        self.assertEqual(status.state, "status")
        self.assertEqual(status.filename, "filename")
        self.assertTrue(status.time - time.time() < 0.1)
        self.assertEqual(status._isNew, True)
        self.assertEqual(status._isUpdated, False)

    def test_filename_hash_empty_string(self):
        """ "Test filename hash with empty string"""
        # Arrange
        # empty filename is converted to Posix path '.' to ensure hash is system independent
        hash = hashlib.md5(".".encode("utf-8")).hexdigest()

        # Act & Assert
        self.assertEqual(ProcessingStatus.filename_hash(""), hash)

    def test_filename_hash_with_ascii_string(self):
        """ "Test filename hash with ascii string"""
        # Arrange
        filename = "hello"
        hash = hashlib.md5(filename.encode("utf-8")).hexdigest()

        # Act & Assert
        self.assertEqual(ProcessingStatus.filename_hash(filename), hash)

    def test_filename_hash_with_non_ascii_string(self):
        """ "Test filename hash with non ascii string"""
        # Arrange
        filename = "hëllo"
        hash = hashlib.md5(filename.encode("utf-8")).hexdigest()

        # Act & Assert
        self.assertEqual(ProcessingStatus.filename_hash(filename), hash)

    def test_filename_hash_with_special_characters(self):
        """ "Test filename hash with special characters"""
        # Arrange
        filename = "hëllo!@#$"
        hash = hashlib.md5(filename.encode("utf-8")).hexdigest()

        # Act & Assert
        self.assertEqual(ProcessingStatus.filename_hash(filename), hash)

    def test_filename_hash_with_long_string(self):
        """ "Test filename hash with long string"""
        # Arrange
        filename = "a" * 1000
        hash = hashlib.md5(filename.encode("utf-8")).hexdigest()

        # Act & Assert
        self.assertEqual(ProcessingStatus.filename_hash(filename), hash)

    def test_filename_hash_with_posix_and_windows_pathnames(self):
        """ "Test with posix and windows pathnames"""
        # Arrange
        filename_posix = "hello/happy/taxpayer"
        filename_windows = "hello\\happy\\taxpayer"

        # Act
        hash_posix = ProcessingStatus.filename_hash(filename_posix)
        hash_windows = ProcessingStatus.filename_hash(filename_windows)

        # Assert
        self.assertEqual(hash_posix, hash_windows)

    @patch(f"{STORE_DICT}.DictStore")
    def test_getFromStore(self, StoreMock):
        """ "Test getFromStore"""
        # Arrange
        key = "key"
        filename = "filename"
        now = time.time()
        value = {
            ProcessingStatus._state_key: ProcessingStatus.State.DONE.value,
            ProcessingStatus._filename_key: filename,
            ProcessingStatus._time_key: now,
        }
        storeMock = StoreMock.return_value
        storeMock.get.return_value = value

        # Act
        status = ProcessingStatus.getFromStore(storeMock, key)

        # Assert
        self.assertIsInstance(status, ProcessingStatus)
        self.assertEqual(status.key, key)
        self.assertEqual(status.state, ProcessingStatus.State.DONE)
        self.assertEqual(status.time, now)
        self.assertEqual(status.filename, filename)

    @patch(f"{STORE_DICT}.DictStore")
    def test_getAllFromStore(self, StoreMock):
        """ "Test getAllFromStore"""
        # Arrange
        key1 = "key1"
        key2 = "key2"
        key3 = "key3"
        filename1 = "filename1"
        filename2 = "filename2"
        filename3 = "filename3"
        now = time.time()
        value1 = {
            ProcessingStatus._state_key: ProcessingStatus.State.DONE.value,
            ProcessingStatus._filename_key: filename1,
            ProcessingStatus._time_key: now,
        }
        value2 = {
            ProcessingStatus._state_key: ProcessingStatus.State.ERROR.value,
            ProcessingStatus._filename_key: filename2,
            ProcessingStatus._time_key: now,
        }
        value3 = {
            ProcessingStatus._state_key: ProcessingStatus.State.IGNORE.value,
            ProcessingStatus._filename_key: filename3,
            ProcessingStatus._time_key: now,
        }
        storeMock = StoreMock.return_value
        storeMock.items.return_value = [
            (key1, value1),
            (key2, value2),
            (key3, value3),
        ]

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

    @patch(f"{STORE_DICT}.DictStore")
    def test_deleteAll(self, StoreMock):
        """ "Test deleteAll"""
        # Arrange
        storeMock = StoreMock.return_value
        storeMock.clear.return_value = None

        # Act
        ProcessingStatus.deleteAll(storeMock)

        # Assert
        storeMock.clear.assert_called_once()

    @patch(f"{STORE_DICT}.DictStore")
    def test_getFilename(self, StoreMock):
        """ "Test getFilename"""
        # Arrange
        storeMock = StoreMock.return_value
        filename = "filename"
        state = ProcessingStatus.State.DONE
        now = time.time()
        status = ProcessingStatus(storeMock, "key", state, filename, now)

        # Act
        a_filename = status.getFilename()

        # Assert
        self.assertEqual(a_filename, filename)

    @patch(f"{STORE_DICT}.DictStore")
    def test_getState(self, StoreMock):
        """ "Test getState"""
        # Arrange
        storeMock = StoreMock.return_value
        filename = "filename"
        state = ProcessingStatus.State.DONE
        now = time.time()
        status = ProcessingStatus(storeMock, "key", state, filename, now)

        # Act
        a_state = status.getState()

        # Assert
        self.assertEqual(a_state, state)

    @patch(f"{STORE_DICT}.DictStore")
    def test_getTime(self, StoreMock):
        """ "Test getTime"""
        # Arrange
        storeMock = StoreMock.return_value
        filename = "filename"
        state = ProcessingStatus.State.DONE
        now = time.time()
        status = ProcessingStatus(storeMock, "key", state, filename, now)

        # Act
        a_time = status.getTime()

        # Assert
        self.assertEqual(a_time, now)

    @patch(f"{STORE_DICT}.DictStore")
    def test_update_new(self, StoreMock):
        """Test update on new store"""
        # Arrange
        storeMock = StoreMock.return_value
        filename = "filename"
        state = ProcessingStatus.State.DONE
        now = time.time()
        status = ProcessingStatus(storeMock, "key", state, filename, now)

        # Act
        status.update()

        # Assert
        storeMock.set.assert_called_once_with(
            status.key,
            {
                ProcessingStatus._state_key: state.value,
                ProcessingStatus._filename_key: filename,
                ProcessingStatus._time_key: now,
            },
        )

    @patch(f"{STORE_DICT}.DictStore")
    def test_update_get_from_store_modified(self, StoreMock):
        """Test update on modified store"""
        # Arrange
        key = "key"
        filename = "filename"
        now = time.time()
        value = {
            ProcessingStatus._state_key: ProcessingStatus.State.DONE.value,
            ProcessingStatus._filename_key: filename,
            ProcessingStatus._time_key: now,
        }
        storeMock = StoreMock.return_value
        storeMock.get.return_value = value
        status = ProcessingStatus.getFromStore(storeMock, key)

        # Act
        status.update()

        # Assert
        storeMock.set.assert_not_called()

    @patch(f"{STORE_DICT}.DictStore")
    def test_update_get_from_store_unmodified(self, StoreMock):
        """Test update on unmodified store"""
        # Arrange
        key = "key"
        filename = "filename"
        now = time.time()
        value = {
            ProcessingStatus._state_key: ProcessingStatus.State.DONE.value,
            ProcessingStatus._filename_key: filename,
            ProcessingStatus._time_key: now,
        }
        storeMock = StoreMock.return_value
        storeMock.get.return_value = value
        status = ProcessingStatus.getFromStore(storeMock, key)
        status.setState(ProcessingStatus.State.ERROR)

        # Act
        status.update()

        # Assert
        storeMock.set.assert_called_once_with(
            status.key,
            {
                ProcessingStatus._state_key: status.state.value,
                ProcessingStatus._filename_key: status.filename,
                ProcessingStatus._time_key: status.time,
            },
        )

    @patch(f"{STORE_DICT}.DictStore")
    def test_delete_new(self, StoreMock):
        """Test delete newly created item"""
        # Arrange
        storeMock = StoreMock.return_value
        filename = "filename"
        state = ProcessingStatus.State.DONE
        now = time.time()
        status = ProcessingStatus(storeMock, "key", state, filename, now)

        # Act
        status.delete()

        # Assert
        storeMock.set.assert_not_called()

    @patch(f"{STORE_DICT}.DictStore")
    def test_delete_get_from_store_unmodified(self, StoreMock):
        """Test delete item from unmodified store"""
        # Arrange
        key = "key"
        filename = "filename"
        now = time.time()
        value = {
            ProcessingStatus._state_key: ProcessingStatus.State.DONE.value,
            ProcessingStatus._filename_key: filename,
            ProcessingStatus._time_key: now,
        }
        storeMock = StoreMock.return_value
        storeMock.get.return_value = value
        status = ProcessingStatus.getFromStore(storeMock, key)

        # Act
        status.delete()

        # Assert
        storeMock.pop.assert_called_once_with(status.key)


if __name__ == "__main__":
    unittest.main()
