"""Dictionary-based storage module for MediaLocate.

This module provides a persistent dictionary-based storage implementation.
"""

from typing import Dict, Any, Optional, Iterator
import json
import os


class DictStore:
    """A persistent dictionary-based storage implementation.

    This class provides a dictionary-like interface with persistence to a JSON file.
    All operations are synchronized with the file system to ensure data consistency.
    """

    class StoreNotOpenError(RuntimeError):
        """Raised when attempting to access a closed store."""

        pass

    def __init__(self, store_dir: str, store_name: str) -> None:
        """Initialize the dictionary store.

        Args:
            store_dir: Directory path for persistent storage
            store_name: Name of the JSON file for persistent storage
        """
        if not os.path.exists(store_dir):
            raise FileNotFoundError(f"Store path '{store_dir}' does not exist")
        self._store_path = os.path.join(store_dir, store_name)
        self._store: Dict[str, Any] = {}
        self._is_open = False
        self._touched = False

    def __enter__(self) -> "DictStore":
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def __len__(self) -> int:
        """Return the number of items in the store.

        Returns:
            Number of items in the store
        """
        return len(self._store)

    def __iter__(self) -> Iterator[str]:
        """Return an iterator over the store keys.

        Returns:
            Iterator over store keys
        """
        return iter(self._store)

    def open(self) -> None:
        """Open the store and load data from disk.

        If the store file exists, loads its contents. Otherwise, creates an empty store.
        """
        if not self._is_open:
            if os.path.exists(self._store_path):
                with open(self._store_path, "r", encoding="utf-8") as f:
                    self._store = json.load(f)
            else:
                self._store = {}
            self._is_open = True
            self._touched = False

    def close(self) -> None:
        """Close the store and sync to disk."""
        self.sync()
        self._is_open = False

    def sync(self) -> None:
        """Synchronize store contents to disk."""
        if not self._is_open:
            raise DictStore.StoreNotOpenError("Cannot sync: store is not open")
        if self._is_open and self._touched:
            with open(self._store_path, "w", encoding="utf-8") as f:
                json.dump(self._store, f, indent=2)
            self._touched = False

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the store with a default if not found.

        Args:
            key: Key to look up
            default: Value to return if key not found

        Returns:
            Value associated with key or default if not found
        """
        if not self._is_open:
            raise DictStore.StoreNotOpenError("Cannot get item: store is not open")
        return self._store.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a value in the store.

        Args:
            key: Key to set
            value: Value to associate with key
        """
        if not self._is_open:
            raise DictStore.StoreNotOpenError("Cannot set item: store is not open")
        if key in self._store and self._store[key] == value:
            return
        self._store[key] = value
        self._touched = True

    def pop(self, key: str) -> Optional[Any]:
        """Remove and return an item from the store.

        Args:
            key: Key to remove

        Returns:
            Value associated with key or None if not found
        """
        if not self._is_open:
            raise DictStore.StoreNotOpenError("Cannot pop item: store is not open")
        if key not in self._store:
            return None
        val = self._store.pop(key)
        self._touched = True
        return val

    def clear(self) -> None:
        """Clear all items from the store."""
        if not self._is_open:
            raise DictStore.StoreNotOpenError("Cannot clear: store is not open")
        if len(self._store) > 0:
            self._store.clear()
            self._touched = True

    def keys(self) -> Iterator[str]:
        """Return an iterator over store keys.

        Returns:
            Iterator over store keys
        """
        if not self._is_open:
            raise DictStore.StoreNotOpenError("Cannot get keys: store is not open")
        return iter(self._store.keys())

    def values(self) -> Iterator[Any]:
        """Return an iterator over store values.

        Returns:
            Iterator over store values
        """
        if not self._is_open:
            raise DictStore.StoreNotOpenError("Cannot get values: store is not open")
        return iter(self._store.values())

    def items(self) -> Iterator[tuple[str, Any]]:
        """Return an iterator over store items.

        Returns:
            Iterator over (key, value) pairs
        """
        if not self._is_open:
            raise DictStore.StoreNotOpenError("Cannot iterate: store is not open")
        return iter(self._store.items())

    def dict(self) -> Dict[str, Any]:
        """Get a copy of the store dictionary.

        Returns:
            Copy of the store dictionary
        """
        if not self._is_open:
            raise DictStore.StoreNotOpenError("Cannot get dict: store is not open")
        return self._store.copy()

    def contains(self, key: str) -> bool:
        """Check if a key exists in the store.

        Args:
            key: Key to check

        Returns:
            True if key exists, False otherwise
        """
        if not self._is_open:
            raise DictStore.StoreNotOpenError("Cannot check key: store is not open")
        return key in self._store

    def is_open(self) -> bool:
        """Check if the store is open.

        Returns:
            True if store is open, False otherwise
        """
        return self._is_open

    def get_path(self) -> str:
        """Get the path to the store file.

        Returns:
            Path to the store file
        """
        return self._store_path
