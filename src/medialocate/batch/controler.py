"""Process files with a given action.

This module provides functionality to process files with configurable actions,
tracking their status and maintaining counters for various processing states.
"""

import os
import logging
from typing import Dict, Optional, Callable, Any

from medialocate.batch.status import ProcessingStatus
from medialocate.store.dict import DictStore


class ActionControler:
    """Process files with a given action.

    This class provides functionality to process files with configurable actions,
    tracking their status and maintaining counters for various processing states.
    """

    # Counter names
    RECOVERED = "recovered"  # number of files with a recorded status
    RECIEVED = "recieved"  # number of files to process
    RECORDED = "recorded"  # number of files with a recorded status
    REPAIRED = (
        "repaired"  # number of files with a recorded status "error", action performed
    )
    PROCESSED = "processed"  # number of files processed
    IGNORED = "ignored"  # number of files ignored
    SUCCEEDED = "succeeded"  # number of files processed with success
    FAILED = "failed"  # number of files processed with error
    DELETED = "deleted"  # number of files deleted
    SAVED = "saved"  # number of files saved
    _COUNTER_LIST = {
        RECOVERED,
        RECIEVED,
        RECORDED,
        REPAIRED,
        PROCESSED,
        IGNORED,
        SUCCEEDED,
        FAILED,
        DELETED,
        SAVED,
    }

    LOGGER_NAME = "ProcessMemory"
    STATUS_STORE_NAME = "pmstatus.json"

    # Whitelist of allowed shell commands that can be executed with shell=True
    ALLOWED_SHELL_COMMANDS = {
        "echo",  # Basic output testing
        "type",  # Windows equivalent of cat
        "dir",  # Windows directory listing
        "copy",  # File copy operations
        "move",  # File move operations
        "del",  # File deletion
        "mkdir",  # Create directory
        "rmdir",  # Remove directory
    }

    # instance attributes
    log: logging.Logger
    working_directory: str
    force_option: bool
    store: DictStore
    counters: Dict[str, int]
    action: Callable[[str, str], int]  # Will always be a callable after init

    def __init__(
        self,
        working_directory: str,
        action: Optional[Callable[[str, str], int]] = None,
        force_option: bool = False,
        parent_logger: Optional[str] = None,
    ) -> None:
        """Initialize the action controller.

        Args:
            working_directory: Directory for storing status files
            action: Action to perform on files.
                    Must be a callable taking (file_path, hash) and returning int
            force_option: Force processing even if file is older than status
            parent_logger: Parent logger name for hierarchical logging
        """
        self.counters = {}
        for counter in ActionControler._COUNTER_LIST:
            self.counters[counter] = 0

        # Normalize working directory
        self.working_directory = os.path.abspath(working_directory)
        if not os.path.exists(self.working_directory):
            os.makedirs(self.working_directory)

        # Initialize status store
        self.store = DictStore(
            self.working_directory, ActionControler.STATUS_STORE_NAME
        )
        self.store.open()
        self.counters[ActionControler.RECOVERED] = len(self.store)

        self.log = logging.getLogger(
            ".".join(filter(None, [parent_logger, ActionControler.LOGGER_NAME]))
        )

        """
        Forces action to be performed even when a file is older than its corresponding status file
        """
        self.force_option = force_option

        """
        self.action is used to process files with the given action.
        The action MUST accept two str parameters: the file to process and its status file.
        The action MUST return a success status code (0) or an error status code (1).
        """
        # Handle action
        if action is None:
            self.log.info("Using default action")
            self.action = lambda file_to_process, filename_hash: (
                print(f'"{file_to_process}" "{filename_hash}"') or 0
            )
        else:
            if not callable(action):
                raise ValueError("Non-shell action must be callable")
            self.action = action

    def __enter__(self) -> "ActionControler":
        """Enter the context manager."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit the context manager."""
        self.counters[ActionControler.SAVED] = len(self.store)
        self.store.close()

    def get_counters(self) -> Dict[str, int]:
        """Return the current counter values."""
        return self.counters

    def clean(self) -> None:
        """Clean up resources and reset counters."""
        to_remove = []
        for status in ProcessingStatus.getAllFromStore(self.store):
            if not os.path.isfile(status.getFilename()):
                to_remove.append(status)
        for status in to_remove:
            status.delete()
            self.counters[ActionControler.DELETED] += 1

    def drop(self) -> None:
        """Remove all status."""
        self.store.clear()

    def process(self, file_to_process: str) -> None:
        """Process a file using the configured action.

        Args:
            file_to_process: Path to the file to process
        """
        proceed_action = False
        self.counters[ActionControler.RECIEVED] += 1

        key = ProcessingStatus.filename_hash(file_to_process)
        status = ProcessingStatus.getFromStore(self.store, key)

        if status is None:
            status = ProcessingStatus(
                self.store, key, ProcessingStatus.State.ONGOING, file_to_process
            )
            proceed_action = True
            self.counters[ActionControler.RECORDED] += 1
        else:
            state = status.getState()
            if state == ProcessingStatus.State.DONE:
                proceed_action = (
                    self.force_option
                    or os.path.getmtime(file_to_process) > status.getTime()
                )
            elif state == ProcessingStatus.State.ERROR:
                self.counters[ActionControler.REPAIRED] += 1
                proceed_action = True
            elif state == ProcessingStatus.State.ONGOING:
                proceed_action = True

        if proceed_action:
            self.counters[ActionControler.PROCESSED] += 1
            rc = self.action(file_to_process, status.key)
            if rc > 9:
                status.setState(ProcessingStatus.State.ERROR)
                self.counters[ActionControler.FAILED] += 1
            elif rc == 0:
                status.setState(ProcessingStatus.State.DONE)
                self.counters[ActionControler.SUCCEEDED] += 1
            else:
                status.setState(ProcessingStatus.State.IGNORE)
                self.counters[ActionControler.IGNORED] += 1

            status.update()
