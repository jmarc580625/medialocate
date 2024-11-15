import os
import json

class DictStore:

    # instance attributes
    directory : str
    store_path : str
    data : dict
    touched : bool

    def __init__(
            self : 'DictStore', 
            directory: str,
            filename: str,
            ) -> None:
        
        self.directory = directory
        self.store_path = os.path.join(self.directory, filename)
        self.data = None
        self.touched = False
        self.opened = False

    def __enter__(self : 'DictStore'):

        self.open()
        return self

    def __exit__(self : 'DictStore', *args : str):
        self.close()
        
    def _createIfDoesNotExist(self : 'DictStore') -> None:
        if not os.path.exists(self.store_path):
            if not os.path.exists(self.directory):
                os.makedirs(self.directory)
            with open(self.store_path, 'w') as f:
                json.dump({}, f)

    def _load(self : 'DictStore') -> None:
        try:
            with open(self.store_path, 'r') as f:
                self.data = json.load(f)
        except Exception as e:
            raise Exception(f"Error while loading store {self.store_path}: {e}")

    def _assertIsOpen(self : 'DictStore') -> None:
        if not self.opened:
            raise Exception(f"DictStore {self.store_path} is not open")

    # public instance methods

    # DictStore operations

    def open(self : 'DictStore') -> None:
        self._createIfDoesNotExist()
        self._load()
        self.opened = True

    def close(self : 'DictStore') -> None:
        if len(self.data) == 0:
            os.remove(self.store_path)
        else:
            self.commit()
        self.data = {}
        self.opened = False
        self.touched = False

    def commit(self : 'DictStore') -> None:
        self._assertIsOpen()
        if self.touched:
            with open(self.store_path, 'w') as f:
                json.dump(self.data, f, indent=2)
            self.touched = False

    def is_touched(self : 'DictStore') -> None:
        return self.touched

    def drop(self : 'DictStore') -> None:
        self.touched = True
        self.data = {}

    def size(self : 'DictStore') -> int:
        return len(self.data)

    # Item operations

    def updateItem(self : 'DictStore', key : str, record : dict) -> None:
        self._assertIsOpen()
        if key not in self.data or self.data[key] != record:
            self.touched = True
            self.data[key] = record

    def popItem(self : 'DictStore', key: str) -> dict:
        self._assertIsOpen()
        record = self.data.pop(key, None)
        if record is not None:
            self.touched = True
        return record

    def getItem(self : 'DictStore', key : str) -> dict :
        self._assertIsOpen()
        return self.data.get(key, None)

    def items(self : 'DictStore'):
        self._assertIsOpen()
        return iter(self.data.items())

    def dict(self : 'DictStore') -> dict: 
        self._assertIsOpen()
        return self.data.copy()

    def getPath(self : 'DictStore') -> str:
        return self.store_path
    