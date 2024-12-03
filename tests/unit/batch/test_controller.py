import os
import time
import tempfile
import unittest
from enum import Enum
from unittest.mock import patch
from medialocate.batch.controler import ActionControler

BATCH_CONTROLER = "medialocate.batch.controler"


class TestProcessMemory(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    """
    ProcessingOrchestrator.__init__ unit tests
    """

    def test_init_with_None_action(self):
        # Arrange
        action = None
        working_directory = "dummy_directory_name"

        # Act
        with patch(f"{BATCH_CONTROLER}.ProcessingStatus") as StatusMock:
            with patch(f"{BATCH_CONTROLER}.DictStore") as StoreMock:
                orchestrator = ActionControler(
                    working_directory,
                    action,
                )

        # Assert
        self.assertTrue(callable(orchestrator.action))

    def test_init_with_function_action(self):
        # Arrange
        def myAction(file, file_hash):
            return 0

        working_directory = "dummy_directory_name"

        # Act
        with patch(f"{BATCH_CONTROLER}.ProcessingStatus") as StatusMock:
            with patch(f"{BATCH_CONTROLER}.DictStore") as StoreMock:
                orchestrator = ActionControler(
                    working_directory,
                    myAction,
                )

        # Assert
        self.assertTrue(callable(orchestrator.action))

    def test_init_with_callable_object(self):
        # Arrange
        class MyCallable:
            def __call__(self, file, file_hash):
                return 0

        myAction = MyCallable()
        working_directory = "dummy_directory_name"

        # Act
        with patch(f"{BATCH_CONTROLER}.ProcessingStatus") as StatusMock:
            with patch(f"{BATCH_CONTROLER}.DictStore") as StoreMock:
                orchestrator = ActionControler(
                    working_directory,
                    myAction,
                )

        # Assert
        self.assertTrue(callable(orchestrator.action))

    """
    ProcessingOrchestrator.process unit tests
    """

    def test_process_a_new_file(self):
        # Arrange
        filename = "my_file.txt"
        working_directory = "dummy_directory_name"
        key = "key"
        states = Enum(
            "State",
            [
                ("DONE", "done"),
                ("ONGOING", "tmp"),
                ("IGNORE", "ignore"),
                ("ERROR", "error"),
            ],
        )

        with patch(f"{BATCH_CONTROLER}.ProcessingStatus") as StatusMock:
            StatusMock.filename_hash.return_value = key
            StatusMock.getFromStore.return_value = None
            StatusMock.return_value.update.return_value = None
            StatusMock.State.DONE = states.DONE
            StatusMock.State.ONGOING = states.ONGOING
            StatusMock.State.IGNORE = states.IGNORE
            StatusMock.State.ERROR = states.ERROR
            with patch(f"{BATCH_CONTROLER}.DictStore") as StoreMock:
                StoreMock.return_value.get.return_value = None
                orchestrator = ActionControler(
                    working_directory,
                    None,
                    True,
                )

                # Act
                orchestrator.process(filename)

                # Assert
                StatusMock.filename_hash.assert_called_once_with(filename)
                StatusMock.getFromStore.assert_called_once_with(
                    StoreMock.return_value, key
                )
                StatusMock.return_value.setState.assert_called_once_with(states.DONE)
                StatusMock.return_value.update.assert_called_once()

    def test_process_for_ignore_status(self):
        # Arrange
        working_directory = "dummy_directory_name"
        filename = "my_file.txt"
        key = "key"
        now = time.time()
        states = Enum(
            "State",
            [
                ("DONE", "done"),
                ("ONGOING", "tmp"),
                ("IGNORE", "ignore"),
                ("ERROR", "error"),
            ],
        )

        with patch(f"{BATCH_CONTROLER}.ProcessingStatus") as StatusMock:
            StatusMock.filename_hash.return_value = key
            StatusMock.getFromStore.return_value = StatusMock.return_value
            StatusMock.return_value.getState.return_value = states.IGNORE
            StatusMock.return_value.update.return_value = None
            StatusMock.State.DONE = states.DONE
            StatusMock.State.ONGOING = states.ONGOING
            StatusMock.State.IGNORE = states.IGNORE
            StatusMock.State.ERROR = states.ERROR
            with patch(f"{BATCH_CONTROLER}.DictStore") as StoreMock:
                orchestrator = ActionControler(
                    working_directory,
                    None,
                    True,
                )

                # Act
                orchestrator.process(filename)

                # Assert
                StatusMock.filename_hash.assert_called_once_with(filename)
                StatusMock.getFromStore.assert_called_once_with(
                    StoreMock.return_value, key
                )
                StatusMock.return_value.getState.assert_called()
                StatusMock.return_value.setState.assert_not_called()
                StatusMock.return_value.update.assert_not_called()

    @patch(f"{BATCH_CONTROLER}.os")
    def test_process_for_done_status(self, OsMock):
        # Arrange
        working_directory = "dummy_directory_name"
        filename = "my_file.txt"
        key = "key"
        now = time.time()
        states = Enum(
            "State",
            [
                ("DONE", "done"),
                ("ONGOING", "tmp"),
                ("IGNORE", "ignore"),
                ("ERROR", "error"),
            ],
        )

        OsMock.path.getmtime.return_value = 0.0

        with patch(f"{BATCH_CONTROLER}.ProcessingStatus") as StatusMock:
            StatusMock.filename_hash.return_value = key
            StatusMock.getFromStore.return_value = StatusMock.return_value
            StatusMock.return_value.getState.return_value = states.DONE
            StatusMock.return_value.getTime.return_value = now
            StatusMock.return_value.update.return_value = None
            StatusMock.State.DONE = states.DONE
            StatusMock.State.ONGOING = states.ONGOING
            StatusMock.State.IGNORE = states.IGNORE
            StatusMock.State.ERROR = states.ERROR
            # TODO : mock os.path.getmtime()
            with patch(f"{BATCH_CONTROLER}.DictStore") as StoreMock:
                orchestrator = ActionControler(
                    working_directory,
                    None,
                    True,
                )

                # Act
                orchestrator.process(filename)

                # Assert
                StatusMock.filename_hash.assert_called_once_with(filename)
                StatusMock.getFromStore.assert_called_once_with(
                    StoreMock.return_value, key
                )
                StatusMock.return_value.getState.assert_called()
                StatusMock.return_value.setState.assert_not_called()
                StatusMock.return_value.update.assert_not_called()

    def test_process_forced_for_done_status(self):
        # Arrange
        working_directory = "dummy_directory_name"
        filename = "my_file.txt"
        key = "key"
        now = time.time()
        states = Enum(
            "State",
            [
                ("DONE", "done"),
                ("ONGOING", "tmp"),
                ("IGNORE", "ignore"),
                ("ERROR", "error"),
            ],
        )

        with patch(f"{BATCH_CONTROLER}.ProcessingStatus") as StatusMock:
            StatusMock.filename_hash.return_value = key
            StatusMock.getFromStore.return_value = StatusMock.return_value
            StatusMock.return_value.getState.return_value = states.DONE
            StatusMock.return_value.getTime.return_value = now
            StatusMock.return_value.update.return_value = None
            StatusMock.State.DONE = states.DONE
            StatusMock.State.ONGOING = states.ONGOING
            StatusMock.State.IGNORE = states.IGNORE
            StatusMock.State.ERROR = states.ERROR
            # TODO : mock os.path.getmtime()
            with patch(f"{BATCH_CONTROLER}.DictStore") as StoreMock:
                orchestrator = ActionControler(
                    working_directory,
                    None,
                    True,
                    force_option=True,
                )

                # Act
                orchestrator.process(filename)

                # Assert
                StatusMock.filename_hash.assert_called_once_with(filename)
                StatusMock.getFromStore.assert_called_once_with(
                    StoreMock.return_value, key
                )
                StatusMock.return_value.getState.assert_called()
                StatusMock.return_value.setState.assert_called_once_with(states.DONE)
                StatusMock.return_value.update.assert_called_once()

    def test_process_for_ongoing_status(self):
        # Arrange
        working_directory = "dummy_directory_name"
        filename = "my_file.txt"
        key = "key"
        now = time.time()
        states = Enum(
            "State",
            [
                ("DONE", "done"),
                ("ONGOING", "tmp"),
                ("IGNORE", "ignore"),
                ("ERROR", "error"),
            ],
        )

        with patch(f"{BATCH_CONTROLER}.ProcessingStatus") as StatusMock:
            StatusMock.filename_hash.return_value = key
            StatusMock.getFromStore.return_value = StatusMock.return_value
            StatusMock.return_value.getState.return_value = states.ONGOING
            StatusMock.return_value.getTime.return_value = now
            StatusMock.return_value.update.return_value = None
            StatusMock.State.DONE = states.DONE
            StatusMock.State.ONGOING = states.ONGOING
            StatusMock.State.IGNORE = states.IGNORE
            StatusMock.State.ERROR = states.ERROR
            # TODO : mock os.path.getmtime()
            with patch(f"{BATCH_CONTROLER}.DictStore") as StoreMock:
                orchestrator = ActionControler(
                    working_directory,
                    None,
                    True,
                    force_option=True,
                )

                # Act
                orchestrator.process(filename)

                # Assert
                StatusMock.filename_hash.assert_called_once_with(filename)
                StatusMock.getFromStore.assert_called_once_with(
                    StoreMock.return_value, key
                )
                StatusMock.return_value.getState.assert_called()
                StatusMock.return_value.setState.assert_called_once_with(states.DONE)
                StatusMock.return_value.update.assert_called_once()

    def test_process_with_ignore_from_action(self):
        # Arrange
        def ignore_from_action(file, file_hash):
            return 1

        filename = "my_file.txt"
        working_directory = "dummy_directory_name"
        key = "key"
        states = Enum(
            "State",
            [
                ("DONE", "done"),
                ("ONGOING", "tmp"),
                ("IGNORE", "ignore"),
                ("ERROR", "error"),
            ],
        )

        with patch(f"{BATCH_CONTROLER}.ProcessingStatus") as StatusMock:
            StatusMock.filename_hash.return_value = key
            StatusMock.getFromStore.return_value = None
            StatusMock.State.DONE = states.DONE
            StatusMock.State.ONGOING = states.ONGOING
            StatusMock.State.IGNORE = states.IGNORE
            StatusMock.State.ERROR = states.ERROR
            with patch(f"{BATCH_CONTROLER}.DictStore") as StoreMock:
                StoreMock.return_value.get.return_value = None
                orchestrator = ActionControler(
                    working_directory,
                    ignore_from_action,
                    False,
                )

                # Act
                orchestrator.process(filename)

                # Assert
                StatusMock.filename_hash.assert_called_once_with(filename)
                StatusMock.getFromStore.assert_called_once_with(
                    StoreMock.return_value, key
                )
                StatusMock.return_value.setState.assert_called_once_with(states.IGNORE)
                StatusMock.return_value.update.assert_called_once()

    def test_process_with_error_from_action(self):
        # Arrange
        def error_from_action(file, file_hash):
            return 11

        filename = "my_file.txt"
        working_directory = "dummy_directory_name"
        key = "key"
        states = Enum(
            "State",
            [
                ("DONE", "done"),
                ("ONGOING", "tmp"),
                ("IGNORE", "ignore"),
                ("ERROR", "error"),
            ],
        )

        with patch(f"{BATCH_CONTROLER}.ProcessingStatus") as StatusMock:
            StatusMock.filename_hash.return_value = key
            StatusMock.getFromStore.return_value = None
            StatusMock.State.DONE = states.DONE
            StatusMock.State.ONGOING = states.ONGOING
            StatusMock.State.IGNORE = states.IGNORE
            StatusMock.State.ERROR = states.ERROR
            with patch(f"{BATCH_CONTROLER}.DictStore") as StoreMock:
                StoreMock.return_value.get.return_value = None
                orchestrator = ActionControler(
                    working_directory,
                    error_from_action,
                    False,
                )

                # Act
                orchestrator.process(filename)

                # Assert
                StatusMock.filename_hash.assert_called_once_with(filename)
                StatusMock.getFromStore.assert_called_once_with(
                    StoreMock.return_value, key
                )
                StatusMock.return_value.setState.assert_called_once_with(states.ERROR)
                StatusMock.return_value.update.assert_called_once()

    """
    ProcessingOrchestrator.clean unit tests
    """

    @patch(f"{BATCH_CONTROLER}.os")
    def test_clean(self, OsMock):
        filename = "my_file.txt"
        working_directory = "dummy_directory_name"

        OsMock.path.isfile.return_value = False

        with patch(f"{BATCH_CONTROLER}.ProcessingStatus") as StatusMock:
            StatusMock.getAllFromStore.return_value = [
                StatusMock.return_value for _ in range(10)
            ]
            StatusMock.return_value.getFilename.return_value = filename
            with patch(f"{BATCH_CONTROLER}.DictStore") as StoreMock:
                StoreMock.return_value.get.return_value = None
                orchestrator = ActionControler(
                    working_directory,
                    None,
                    False,
                )

                # Act
                orchestrator.clean()

                # Assert
                StatusMock.getAllFromStore.assert_called_once_with(
                    StoreMock.return_value
                )
                StatusMock.return_value.getFilename.assert_called()
                StatusMock.return_value.delete.assert_called()

    """
    ProcessingOrchestrator.drop unit tests
    """

    def test_drop(self):
        # Arrange
        working_directory = "dummy_directory_name"
        with patch(f"{BATCH_CONTROLER}.DictStore") as StoreMock:
            orchestrator = ActionControler(
                working_directory,
                None,
                False,
            )

            # Act
            orchestrator.drop()

            # Assert
            StoreMock.return_value.clear.assert_called_once()

    """
    ProcessingOrchestrator.get_counters unit tests

    """

    @patch(f"{BATCH_CONTROLER}.os")
    def test_get_counters_with_combination_of_file_state_and_action_results(
        self, OsMock
    ):
        """+------------------------------------------------+
        | 5 file states and 3 action results = 15 cases  |
        +--------+-----+------+---------+--------+-------+
        |        | new | done | ongoing | ignore | error |
        +--------+-----+------+---------+--------+-------+
        |     ok |  x  |   x  |    x    |    x   |   x   |
        | ignore |  x  |   x  |    x    |    x   |   x   |
        |  error |  x  |   x  |    x    |    x   |   x   |
        +--------+-----+------+---------+--------+-------+"""
        # Arrange
        now = time.time()
        OsMock.path.getmtime.return_value = now

        expected_counters = {
            ActionControler.RECOVERED: 0,
            ActionControler.RECIEVED: 15,
            ActionControler.RECORDED: 3,
            ActionControler.REPAIRED: 3,
            ActionControler.PROCESSED: 9,
            ActionControler.SUCCEEDED: 3,
            ActionControler.IGNORED: 3,
            ActionControler.FAILED: 3,
            ActionControler.DELETED: 0,
            ActionControler.SAVED: 0,
        }

        class MockRC:
            def __init__(self, rc_values=[0, 1, 11]):
                self.rc_values = rc_values
                self.max = len(rc_values) - 1
                self.i = 0

            def __call__(self, file, hash):
                self.i = self.i + 1 if self.i < self.max else 0
                return self.rc_values[self.i]

            def size(self) -> int:
                return len(self.rc_values)

        mock_rc = MockRC()
        filename_template = "my_file-{}-{}.txt"
        working_directory = "dummy_directory_name"
        key = "key"
        states = Enum(
            "State",
            [
                ("DONE", "done"),
                ("ONGOING", "tmp"),
                ("IGNORE", "ignore"),
                ("SUCCESS", "success"),
                ("ERROR", "error"),
                ("NEW", "new"),
            ],
        )
        with patch(f"{BATCH_CONTROLER}.ProcessingStatus") as StatusMock:
            StatusMock.State.DONE = states.DONE
            StatusMock.State.ONGOING = states.ONGOING
            StatusMock.State.SUCCESS = states.SUCCESS
            StatusMock.State.IGNORE = states.IGNORE
            StatusMock.State.ERROR = states.ERROR
            mock_matrix = [
                [None, states.NEW],
                [StatusMock.return_value, states.DONE],
                [StatusMock.return_value, states.ONGOING],
                [StatusMock.return_value, states.IGNORE],
                [StatusMock.return_value, states.ERROR],
            ]
            mock_size = len(mock_matrix)
            StatusMock.getFromStore.side_effect = lambda x, y: mock_matrix[mock_index][
                0
            ]
            StatusMock.return_value.getState.side_effect = lambda: mock_matrix[
                mock_index
            ][1]
            StatusMock.return_value.getTime.return_value = now
            StatusMock.filename_hash.return_value = key

            orchestrator = ActionControler(
                working_directory,
                mock_rc,
                False,
            )
            cnt = 0
            for i in range(mock_size):
                mock_index = i
                for j in range(mock_rc.size()):
                    cnt += 1
                    st = mock_matrix[mock_index][1].value
                    filename = filename_template.format(cnt, st)
                    orchestrator.process(filename)
            # Act
            counters = orchestrator.get_counters()
            # Assert
            self.assertEqual(counters, expected_counters)

    def test_get_counters_cases_for_restored_and_saved(self):
        # TODO : implement
        # counters are equals to zero for empty & non-existing store
        # counters are equals when no changes occurs
        # counters are equals when no changes occurs
        # Arrange
        # Act
        # Assert
        pass

    def test_failure_handling(self):
        # TODO : implement
        # invalid characters in shell
        # non existing file to process
        # invalid hash format
        # non callable action
        # command timeout
        # command fails with error code
        # command fails with unhandled exception
        # Arrange
        # Act
        # Assert
        pass


if __name__ == "__main__":
    unittest.main()
