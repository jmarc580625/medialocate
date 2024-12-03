import os
import json
from typing import Dict, Any, Iterator, Tuple, Optional


class DictStore:
    # instance attributes
    directory: str
    store_path: str
    data: Dict[str, Any]
    touched: bool
    opened: bool

    def __init__(
        self,
        directory: str,
        filename: str,
    ) -> None:
        self.directory = directory
        self.store_path = os.path.join(self.directory, filename)
        self.data = None
        self.touched = False
        self.opened = False

    def __enter__(self) -> "DictStore":
        self.open()
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def _createIfDoesNotExist(self) -> None:
        if not os.path.exists(self.store_path):
            os.makedirs(self.directory, exist_ok=True)
            with open(self.store_path, "w") as f:
                json.dump({}, f)

    def _load(self) -> None:
        try:
            with open(self.store_path, "r") as f:
                self.data = json.load(f)
        except Exception as e:
            raise Exception(f"Error while loading store {self.store_path}: {e}")

    def _assertIsOpen(self) -> None:
        if not self.opened:
            raise Exception(f"DictStore {self.store_path} is not open")

    # public instance methods

    # DictStore operations

    def open(self) -> None:
        if not self.opened:
            self._createIfDoesNotExist()
            self._load()
            self.opened = True

    def close(self) -> None:
        if len(self.data) == 0:
            os.remove(self.store_path)
        else:
            self.commit()
        self.data = {}
        self.opened = False
        self.touched = False

    def commit(self) -> None:
        self._assertIsOpen()
        if self.touched:
            with open(self.store_path, "w") as f:
                json.dump(self.data, f, indent=2)
            self.touched = False

    def is_touched(self) -> bool:
        return self.touched

    def drop(self) -> None:
        self.touched = True
        self.data = {}

    def size(self) -> int:
        return len(self.data)

    # Item operations

    def getItem(self, key: str) -> Optional[Dict[str, Any]]:
        self._assertIsOpen()
        return self.data.get(key)

    def updateItem(self, key: str, record: Dict[str, Any]) -> None:
        self._assertIsOpen()
        if key not in self.data or self.data[key] != record:
            self.touched = True
            self.data[key] = record

    def popItem(self, key: str) -> Optional[Dict[str, Any]]:
        self._assertIsOpen()
        record = self.data.pop(key, None)
        if record is not None:
            self.touched = True
        return record

    def items(self: "DictStore"):
        self._assertIsOpen()
        return iter(self.data.items())

    def dict(self) -> Dict[str, Any]:
        self._assertIsOpen()
        return self.data.copy()

    def getPath(self) -> str:
        return self.store_path
