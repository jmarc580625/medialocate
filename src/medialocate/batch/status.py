"""Module for managing file processing status in batch operations.

This module provides functionality to track and manage the processing state of files,
including their current status, timestamps, and related metadata.
"""

import time
from enum import Enum
from typing import Iterator, ClassVar, Dict, Any, List, Optional
from medialocate.store.dict import DictStore
from medialocate.util.file_naming import get_hash, to_posix


class ProcessingStatus:
    """Manages the processing status of a file in the batch system.

    This class tracks the state, timestamp, and metadata of a file being processed,
    providing methods to update and query its status.
    """

    class State(Enum):
        """Enumeration of possible processing states for a file."""

        # ProcessingStatus values (immutable)
        DONE = "done"
        IGNORE = "ignore"
        ONGOING = "tmp"
        ERROR = "error"

        def __str__(self) -> str:
            """Convert state to string representation."""
            return self.value

        @classmethod
        def values(cls) -> List[str]:
            """Get list of all state values as strings."""
            return [state.value for state in cls]

    # class attributes
    _state_key: ClassVar[str] = "state"
    _filename_key: ClassVar[str] = "filename"
    _time_key: ClassVar[str] = "time"
    _dict_keys: ClassVar[List[str]] = [_state_key, _filename_key, _time_key]
    _dict_template: ClassVar[Dict[str, Any]] = {
        _state_key: "",
        _filename_key: "",
        _time_key: 0.0,
    }

    def __init__(
        self,
        store: DictStore,
        key: str,
        state: State,
        filename: str,
        time_val: Optional[float] = None,
    ) -> None:
        """Initialize a new ProcessingStatus instance.

        Args:
            store: Storage manager for status information
            key: File name hash
            state: Initial processing state
            filename: Name of the file being processed
            time_val: Last modification time (defaults to current time)
        """
        self.store = store
        self.key = key
        self.filename = to_posix(filename)
        self.state = state
        self.time = time_val if time_val is not None else time.time()
        self._isNew = True
        self._isUpdated = False

    # class methods

    @classmethod
    def filename_hash(cls, filename: str) -> str:
        """Compute the hash of a file name."""
        return get_hash(filename)

    @classmethod
    def getFromStore(
        cls,
        store: DictStore,
        key: str,
    ) -> Optional["ProcessingStatus"]:
        """Retrieve a ProcessingStatus instance from storage.

        Args:
            store: Storage manager
            key: File name hash

        Returns:
            ProcessingStatus instance if found, otherwise None
        """
        dict_data = store.get(key)
        if dict_data:
            status = cls(
                store,
                key,
                cls.State(dict_data[cls._state_key]),
                dict_data[cls._filename_key],
                dict_data[cls._time_key],
            )
            status._isNew = False
            return status
        return None

    @classmethod
    def getAllFromStore(
        cls,
        store: DictStore,
    ) -> Iterator["ProcessingStatus"]:
        """Retrieve all ProcessingStatus instances from storage.

        Args:
            store: Storage manager

        Yields:
            ProcessingStatus instances
        """
        for key, dict_data in store.items():
            status = cls(
                store,
                key,
                cls.State(dict_data[cls._state_key]),
                dict_data[cls._filename_key],
                dict_data[cls._time_key],
            )
            status._isNew = False
            yield status

    @classmethod
    def deleteAll(cls, store: DictStore) -> None:
        """Remove all ProcessingStatus instances from storage.

        Args:
            store: Storage manager
        """
        store.clear()

    # instance methods

    def getFilename(self) -> str:
        """Get the name of the file being processed."""
        return self.filename

    def getState(self) -> State:
        """Get the current processing state."""
        return self.state

    def getTime(self) -> float:
        """Get the last modification time."""
        return self.time

    def setState(self, state: State) -> None:
        """Update the processing state.

        Args:
            state: New processing state
        """
        self.state = state
        self._isUpdated = True

    def delete(self) -> None:
        """Remove this ProcessingStatus instance from storage."""
        if not self._isNew:
            self.store.pop(self.key)

    def update(self) -> None:
        """Update this ProcessingStatus instance in storage."""
        if self._isUpdated or self._isNew:
            self.time = time.time()
            self.store.set(
                self.key,
                {
                    self._state_key: self.state.value,
                    self._filename_key: self.filename,
                    self._time_key: self.time,
                },
            )
            self._isNew = False
            self._isUpdated = False
