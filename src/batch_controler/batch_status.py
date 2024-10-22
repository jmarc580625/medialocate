import time
import hashlib
from enum import Enum
import pathlib
from collections.abc import Iterator
from dict_store import DictStore

class ProcessingStatus:

    # inner class
    class State(Enum):
    # ProcessingStatus values (immutable)
        DONE = "done"
        IGNORE = "ignore"
        ONGOING = "tmp"
        ERROR = "error"

        def __str__(self : 'ProcessingStatus.State') -> str:
            return self.name.lower()
        
        @classmethod
        def values(cls : 'ProcessingStatus.State'):
            return list(map(lambda x: x.value, cls))

    # class attributes
    _state_key = 'state'
    _filename_key = 'filename'
    _time_key = 'time'
    _dict_keys = [_state_key, _filename_key, _time_key]
    _dict_template = {_state_key: '', _filename_key: '', _time_key: 0.0}

    # instance attributes
    store : 'DictStore'             # remanent storage manager
    key : str                   # hash of the file name (see filename_hash)
    filename : str              # name of the file (immutable)
    state : State               # state of the file processing, take a value among ProcessingStatus.State (mutable)
    time : float                # last modification time of the ProcessingStatus (self calculated) 
    _isNew : bool               # indicates if ProcessingStatus is a new one
    _isUpdated : bool           # indicates if ProcessingStatus has been modified since its creation or its retrieval

    def __init__(
            self : 'ProcessingStatus', 
            store : 'DictStore',
            key: str, 
            state: State, 
            filename : str, 
            time : float = time.time()
            ) -> None:
        self.store = store
        self.key = key
        self.state = state
        self.filename = filename
        self.time = time
        self._isNew = True
        self._isUpdated = False

    # class methods

    @classmethod
    def filename_hash(cls : 'ProcessingStatus', filepath: str) -> str:
        """
        Calculate the MD5 hash of a file  path
        on Windows system, prio to hash calculation, filename path is convert to unix style (i.e using '/' separator) to ensure hash is system independent
        """
        posix_filename = pathlib.PurePath(r"{}".format(filepath)).as_posix()
        return hashlib.md5(posix_filename.encode('utf-8')).hexdigest()

    @classmethod
    def getFromStore(cls : 'ProcessingStatus', store : 'DictStore', key: str) -> 'ProcessingStatus':
        dict = store.getItem(key)
        if dict:
            status = cls(store,
                         key,
                         ProcessingStatus.State(dict[cls._state_key]),
                         dict[cls._filename_key],
                         dict[cls._time_key])
            status._isNew = False
            return status
        else:
            return None

    @classmethod
    def getAllFromStore(cls : 'ProcessingStatus', store : 'DictStore') -> Iterator['ProcessingStatus']:
        for key, dict in store.walkItems():
            status = cls(store,
                         key,
                         ProcessingStatus.State(dict[cls._state_key]),
                         dict[cls._filename_key],
                         dict[cls._time_key])
            status._isNew = False
            yield status

    @classmethod
    def deleteAll(cls : 'ProcessingStatus', store : 'DictStore') -> None:
        store.clean()

    # instance methods
    
    def getFilename(self : 'ProcessingStatus') -> str:
        return self.filename

    def getState(self : 'ProcessingStatus') -> State:
        return self.state

    def getTime(self : 'ProcessingStatus') -> float:
        return self.time

    def setState(self : 'ProcessingStatus', state: str) -> None:
        self.state = state
        self._isUpdated = True

    def delete(self : 'ProcessingStatus') -> None:
        if not self._isNew:
            self.store.popItem(self.key)

    def update(self : 'ProcessingStatus') -> None:
        if self._isUpdated or self._isNew:
            self.time = time.time()
            self.store.updateItem(self.key, 
                                  {ProcessingStatus._state_key: self.state.value,
                                   ProcessingStatus._filename_key: self.filename, 
                                   ProcessingStatus._time_key: self.time})
            self._isNew = False
            self._isUpdated = False
