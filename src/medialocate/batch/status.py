import time
import pathlib
from enum import Enum
from typing import Iterator, ClassVar, Dict, Any, List, Optional
from medialocate.store.dict import DictStore
from medialocate.util.file_naming import get_hash, to_posix


class ProcessingStatus:
    # inner class
    class State(Enum):
        # ProcessingStatus values (immutable)
        DONE = "done"
        IGNORE = "ignore"
        ONGOING = "tmp"
        ERROR = "error"

        def __str__(self) -> str:
            return self.value

        @classmethod
        def values(cls) -> List[str]:
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

    # instance attributes
    store: DictStore  # remanent storage manager
    key: str  # hash of the file name
    filename: str  # name of the file (immutable)
    state: State  # state of the file processing, take a value among ProcessingStatus.State (mutable)
    time: float  # last modification time of the ProcessingStatus (self calculated)
    _isNew: bool  # indicates if ProcessingStatus is a new one
    _isUpdated: bool  # indicates if ProcessingStatus has been modified since its creation or its retrieval

    def __init__(
        self,
        store: DictStore,
        key: str,
        state: State,
        filename: str,
        time_val: Optional[float] = None,
    ) -> None:
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
        return get_hash(filename)

    @classmethod
    def getFromStore(
        cls,
        store: DictStore,
        key: str,
    ) -> Optional["ProcessingStatus"]:
        dict_data = store.getItem(key)
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
        store.drop()

    # instance methods

    def getFilename(self) -> str:
        return self.filename

    def getState(self) -> State:
        return self.state

    def getTime(self) -> float:
        return self.time

    def setState(self, state: State) -> None:
        self.state = state
        self._isUpdated = True

    def delete(self) -> None:
        if not self._isNew:
            self.store.popItem(self.key)

    def update(self) -> None:
        if self._isUpdated or self._isNew:
            self.time = time.time()
            self.store.updateItem(
                self.key,
                {
                    self._state_key: self.state.value,
                    self._filename_key: self.filename,
                    self._time_key: self.time,
                },
            )
            self._isNew = False
            self._isUpdated = False
