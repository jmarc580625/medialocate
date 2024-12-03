import os
from typing import Iterator


class FileFinder:
    # instance variables
    root_path: str
    root_depth: int
    extensions: tuple[str, ...]
    matches: list[str]
    excluded_directories: list[str]
    min_age: float
    max_depth: int
    counters: dict

    def __init__(
        self: "FileFinder",
        root_path: str,
        extensions: list[str] = [],
        matches: list[str] = [],
        prune: list[str] = [],
        min_age: float = 0,
        max_depth: int = -1,
    ) -> None:
        if not os.path.isdir(root_path):
            raise FileNotFoundError(f"Path '{root_path}' is not a directory")

        self.root_path = root_path
        self.root_depth = len(self.root_path.split(os.sep))
        self.extensions = tuple([e.lower() for e in extensions])
        self.matches = matches
        self.excluded_directories = prune
        self.min_age = min_age
        self.max_depth = max_depth
        self.counters = {
            "dirs": 0,
            "files": 0,
            "depth": 0,
            "found": 0,
        }

    def find(
        self: "FileFinder",
    ) -> Iterator[str]:
        """
        Recursively search for files in the specified root_path that end with the specified
        extensions (case insensitive).

        Parameters:
            . root_path (str): the directory to start the search in
            . extensions (list of str): the filename extensions to search for
            . excluded_directories (list of str): the directories to exclude from the search
            . min_age (int): the minimum age of the files to be searched (unix timestamp)
            . max_depth (int): the maximum depth of the search (-1 for all subdirectories,
              0 for the current directory)
        """
        for root, _, files in os.walk(self.root_path):
            path_elements = root.split(os.sep)
            curent_depth = len(path_elements) - self.root_depth
            depth_overflows = curent_depth > self.max_depth

            if path_elements[-1] in self.excluded_directories or (
                self.max_depth >= 0 and depth_overflows
            ):
                continue

            self.counters["dirs"] += 1
            self.counters["depth"] = max(curent_depth, self.counters["depth"])

            self.counters["files"] += len(files)
            filtered_files = [
                f
                for f in files
                if not self.extensions or f.lower().endswith(self.extensions)
            ]
            filtered_files = [
                f
                for f in filtered_files
                if self.min_age == 0
                or os.path.getmtime(os.path.join(root, f)) > self.min_age
            ]
            filtered_files = [
                f for f in filtered_files if not self.matches or f in self.matches
            ]
            self.counters["found"] += len(filtered_files)

            # yield the filtered files
            for file in filtered_files:
                yield os.path.join(root, file)

    def get_counters(self: "FileFinder") -> dict:
        return self.counters
