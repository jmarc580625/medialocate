import os
import time
import unittest
import tempfile
from typing import Optional
from medialocate.finder.file import FileFinder


class TestFileFinder(unittest.TestCase):
    # class variables
    working_directory: Optional[str] = None
    root_dirname = "root"

    file_prefix = "test"
    dir_prefix = "depth"

    sufix_ignore_1 = "1-i"
    sufix_ignore_4 = "4-i"
    sufix_exclude_1 = "1-x"
    sufix_11 = "1-a"
    sufix_12 = "1-b"
    sufix_2 = "2-1-a"
    sufix_3 = "3-2-1-a"

    ext_txt = ".txt"
    ext_py = ".py"
    ext_json = ".json"
    file_extensions = [ext_txt, ext_py, ext_json]

    min_age = 0

    # instance variables
    filters: dict
    expected_files_count: dict

    def setUp(self):
        """
        directory tree structure for testing:              + no filter + in ext + in dir + in depth + in age +  all +
        root directory: rwxrwxrwxrwx                       |           |        |          |        |        |      |
        |---test.txt file: rwxrwxrwxrwx                    |     x     |    x   |     x    |    x   |   o    |   x  |
        |---test.py file: rwxrwxrwxrwx                     |     x     |    o   |     x    |    x   |   o    |   o  |
        |---test.json file: rwxrwxrwxrwx                   |     x     |    x   |     x    |    x   |   o    |   x  |
        |---depth1-x directory: rwx------                  |           |        |          |        |        |      |
        |   |---test1-x.txt file: rwxrwxrwxrwx             |     x     |    x   |     x    |    x   |   o    |   x  |
        |---depth1-i directory: rwxrwxrwxrwx               |           |        |          |        |        |      |
        |   |---test1-i.txt file: rwxrwxrwxrwx             |     x     |    x   |     o    |    x   |   o    |   o  |
        |   |---test1-i.py file: rwxrwxrwxrwx              |     x     |    o   |     o    |    x   |   o    |   o  |
        |---depth1-a directory: rwxrwxrwxrwx               |           |        |          |        |        |      |
        |   |---test1-a.txt file: rwxrwxrwxrwx             |     x     |    x   |     x    |    x   |   o    |   x  |
        |   |---test1-a.py file: rwxrwxrwxrwx              |     x     |    o   |     x    |    x   |   o    |   o  |
        |   |---test1-a.json file: rwxrwxrwxrwx            |     x     |    x   |     x    |    x   |   o    |   x  |
        |---depth1-b directory: rwxrwxrwxrwx   => min age  |           |        |          |        |        |      |
        |   |---test1-b.txt file: rwxrwxrwxrwx             |     x     |    x   |     x    |    x   |   x    |   x  |
        |   |---test1-b.py file: rwxrwxrwxrwx              |     x     |    o   |     x    |    x   |   x    |   o  |
        |   |---test1-b.json file: rwxrwxrwxrwx            |     x     |    x   |     x    |    x   |   x    |   x  |
        |   |---depth2-1-a directory: rwxrwxrwxrwx         |           |        |          |        |        |      |
        |   |   |---test2-1-a.txt file: rwxrwxrwxrwx       |     x     |    x   |     x    |    x   |   x    |   x  |
        |   |   |---test2-1-a.py file: rwxrwxrwxrwx        |     x     |    o   |     x    |    x   |   x    |   o  |
        |   |   |---test2-1-a.json file: rwxrwxrwxrwx      |     x     |    x   |     x    |    x   |   x    |   x  |
        |   |   |---depth3-2-1-b directory: rwxrwxrwxrwx   |           |        |          |        |        |      |
        |   |   |   |---test3-2-1-b.txt file: rwxrwxrwxrwx |     x     |    x   |     x    |    o   |   x    |   o  |
        |   |   |   |---depth4-i directory: rwxrwxrwxrwx   |           |        |          |        |        |      |
        |   |   |   |   |---test4-i.txt file: rwxrwxrwxrwx |     x     |    x   |     o    |    o   |   x    |   o  |
                                                           |           |        |          |        |        |      |
                                                           |    17     +   12   +    14    +   15   +   8    |   4  |     <= total by filter
                                                                 V          V         V         V       V        V
        """
        self.expected_files_count = {
            "no filter": 17,  #        V         V         V       V        V
            "extension filter": 12,  #       V         V       V        V
            "prune filter": 14,  #       V       V        V
            "depth filter": 15,  #     V        V
            "age filter": 8,  #      V
            "all filters": 4,
        }
        self.filters = {
            "extension filter": [TestFileFinder.ext_txt, TestFileFinder.ext_json],
            "prune filter": [
                f"{TestFileFinder.dir_prefix}{TestFileFinder.sufix_ignore_1}",
                f"{TestFileFinder.dir_prefix}{TestFileFinder.sufix_ignore_4}",
            ],
            "depth filter": 2,
            "age filter": 0,
        }

        self.expected_counters = {
            "no filter": {"dirs": 8, "files": 17, "depth": 4, "found": 17},
            "all filters": {"dirs": 5, "files": 13, "depth": 2, "found": 4},
        }

        if TestFileFinder.working_directory is None:
            TestFileFinder.working_directory = tempfile.mkdtemp()

            self.working_directory = TestFileFinder.working_directory

            # root directory: rwxrwxrwxrwx
            root_path = os.path.join(self.working_directory, self.root_dirname)
            os.makedirs(root_path)
            # |---test.txt file: rwxrwxrwxrwx
            # |---test.py file: rwxrwxrwxrwx
            # |---test.json file: rwxrwxrwxrwx
            for ext in TestFileFinder.file_extensions:
                with open(
                    os.path.join(root_path, f"{TestFileFinder.file_prefix}{ext}"), "w"
                ) as f:
                    f.write("")
            # |---depth1-x directory: rwx------
            dir_path = os.path.join(
                root_path,
                f"{TestFileFinder.dir_prefix}{TestFileFinder.sufix_exclude_1}",
            )
            os.makedirs(dir_path)
            # |   |---test1-x.txt file: rwxrwxrwxrwx
            with open(
                os.path.join(
                    dir_path,
                    f"{TestFileFinder.file_prefix}{TestFileFinder.sufix_exclude_1}{TestFileFinder.ext_txt}",
                ),
                "w",
            ) as f:
                f.write("")
            # |---depth1-i directory: rwxrwxrwxrwx
            dir_path = os.path.join(
                root_path, f"{TestFileFinder.dir_prefix}{TestFileFinder.sufix_ignore_1}"
            )
            os.makedirs(dir_path)
            # |   |---test1-i.txt file: rwxrwxrwxrwx
            # |   |---test1-i.py file: rwxrwxrwxrwx
            with open(
                os.path.join(
                    dir_path,
                    f"{TestFileFinder.file_prefix}{TestFileFinder.sufix_ignore_1}{TestFileFinder.ext_txt}",
                ),
                "w",
            ) as f:
                f.write("")
            with open(
                os.path.join(
                    dir_path,
                    f"{TestFileFinder.file_prefix}{TestFileFinder.sufix_ignore_1}{TestFileFinder.ext_py}",
                ),
                "w",
            ) as f:
                f.write("")
            # |---depth1-a directory: rwxrwxrwxrwx
            dir_path = os.path.join(
                root_path, f"{TestFileFinder.dir_prefix}{TestFileFinder.sufix_11}"
            )
            os.makedirs(dir_path)
            # |   |---test1-a.txt file: rwxrwxrwxrwx
            # |   |---test1-a.py file: rwxrwxrwxrwx
            # |   |---test1-a.json file: rwxrwxrwxrwx
            for ext in TestFileFinder.file_extensions:
                with open(
                    os.path.join(
                        dir_path,
                        f"{TestFileFinder.file_prefix}{TestFileFinder.sufix_11}{ext}",
                    ),
                    "w",
                ) as f:
                    f.write("")
            # |---depth1-b directory: rwxrwxrwxrwx
            dir_path = os.path.join(
                root_path, f"{TestFileFinder.dir_prefix}{TestFileFinder.sufix_12}"
            )
            os.makedirs(dir_path)

            time.sleep(0.1)
            TestFileFinder.min_age = os.path.getmtime(dir_path)

            # |   |---test1-b.txt file: rwxrwxrwxrwx
            # |   |---test1-b.py file: rwxrwxrwxrwx
            # |   |---test1-b.json file: rwxrwxrwxrwx
            for ext in TestFileFinder.file_extensions:
                with open(
                    os.path.join(
                        dir_path,
                        f"{TestFileFinder.file_prefix}{TestFileFinder.sufix_12}{ext}",
                    ),
                    "w",
                ) as f:
                    f.write("")
            # |   |---depth2-1-a directory: rwxrwxrwxrwx
            dir_path = os.path.join(
                root_path,
                f"{TestFileFinder.dir_prefix}{TestFileFinder.sufix_12}",
                f"{TestFileFinder.dir_prefix}{TestFileFinder.sufix_2}",
            )
            os.makedirs(dir_path)
            # |   |   |---test2-1-a.txt file: rwxrwxrwxrwx
            # |   |   |---test2-1-a.py file: rwxrwxrwxrwx
            # |   |   |---test2-1-a.json file: rwxrwxrwxrwx
            for ext in TestFileFinder.file_extensions:
                with open(
                    os.path.join(
                        dir_path,
                        f"{TestFileFinder.file_prefix}{TestFileFinder.sufix_2}{ext}",
                    ),
                    "w",
                ) as f:
                    f.write("")
            # |   |   |---depth3-2-1-b directory: rwxrwxrwxrwx
            dir_path = os.path.join(
                dir_path, f"{TestFileFinder.dir_prefix}{TestFileFinder.sufix_3}"
            )
            os.makedirs(dir_path)
            # |   |   |   |---test3-2-1-b.txt file: rwxrwxrwxrwx
            with open(
                os.path.join(
                    dir_path,
                    f"{TestFileFinder.file_prefix}{TestFileFinder.sufix_3}{TestFileFinder.ext_txt}",
                ),
                "w",
            ) as f:
                f.write("")
            # |   |   |   |---depth4-i directory: rwxrwxrwxrwx
            dir_path = os.path.join(
                dir_path, f"{TestFileFinder.dir_prefix}{TestFileFinder.sufix_ignore_4}"
            )
            os.makedirs(dir_path)
            # |   |   |   |   |---test4-i.txt file: rwxrwxrwxrwx
            with open(
                os.path.join(
                    dir_path,
                    f"{TestFileFinder.file_prefix}{TestFileFinder.sufix_ignore_4}{TestFileFinder.ext_txt}",
                ),
                "w",
            ) as f:
                f.write("")

        else:
            self.working_directory = TestFileFinder.working_directory

        self.filters["age filter"] = TestFileFinder.min_age

    def tearDown(self):
        # shutil.rmtree(self.working_directory)
        pass

    """
    __init__ unit tests
    """

    def test_init_with_non_existing_root_path(self):
        # Arrange
        root_path = os.path.join(self.working_directory, "non-existing")

        # Act & Assert
        with self.assertRaises(FileNotFoundError):
            FileFinder(root_path)

    def test_init_with_existing_root_path(self):
        # Arrange
        root_path = os.path.join(self.working_directory, self.root_dirname)

        # Act
        finder = FileFinder(root_path)

        # Assert
        self.assertEqual(finder.root_path, root_path)

    """
    find unit tests
    """

    def test_find_with_no_filter(self):
        # Arrange
        root_path = os.path.join(self.working_directory, self.root_dirname)
        finder = FileFinder(root_path)

        # Act
        files = list(finder.find())

        # Assert
        self.assertEqual(len(files), self.expected_files_count["no filter"])

    def test_find_with_extension_filter(self):
        # Arrange
        root_path = os.path.join(self.working_directory, self.root_dirname)
        finder = FileFinder(root_path, extensions=self.filters["extension filter"])

        # Act
        files = list(finder.find())

        # Assert
        self.assertEqual(len(files), self.expected_files_count["extension filter"])

    def test_find_with_directory_filter(self):
        # Arrange
        root_path = os.path.join(self.working_directory, self.root_dirname)
        finder = FileFinder(root_path, prune=self.filters["prune filter"])

        # Act
        files = list(finder.find())

        # Assert
        self.assertEqual(len(files), self.expected_files_count["prune filter"])

    def test_find_with_depth_filter(self):
        # Arrange
        root_path = os.path.join(self.working_directory, self.root_dirname)
        finder = FileFinder(root_path, max_depth=self.filters["depth filter"])

        # Act
        files = list(finder.find())

        # Assert
        self.assertEqual(len(files), self.expected_files_count["depth filter"])

    def test_find_with_age_filter(self):
        # Arrange
        root_path = os.path.join(self.working_directory, self.root_dirname)
        finder = FileFinder(root_path, min_age=self.filters["age filter"])

        # Act
        files = list(finder.find())

        # Assert
        self.assertEqual(len(files), self.expected_files_count["age filter"])

    def test_find_with_all_filters(self):
        # Arrange
        root_path = os.path.join(self.working_directory, self.root_dirname)
        finder = FileFinder(
            root_path,
            extensions=self.filters["extension filter"],
            prune=self.filters["prune filter"],
            max_depth=self.filters["depth filter"],
            min_age=self.filters["age filter"],
        )

        # Act
        files = list(finder.find())

        # Assert
        self.assertEqual(len(files), self.expected_files_count["all filters"])

    """
    get_counters unit tests
    """

    def test_get_counters_with_no_filters(self):
        # Arrange
        root_path = os.path.join(self.working_directory, self.root_dirname)
        finder = FileFinder(root_path)
        files = list(finder.find())

        # Act
        counters = finder.get_counters()

        # Assert
        self.assertEqual(counters["dirs"], self.expected_counters["no filter"]["dirs"])
        self.assertEqual(
            counters["files"], self.expected_counters["no filter"]["files"]
        )
        self.assertEqual(
            counters["depth"], self.expected_counters["no filter"]["depth"]
        )
        self.assertEqual(
            counters["found"], self.expected_counters["no filter"]["found"]
        )

    def test_get_counters_with_all_filters(self):
        # Arrange
        root_path = os.path.join(self.working_directory, self.root_dirname)
        finder = FileFinder(
            root_path,
            extensions=self.filters["extension filter"],
            prune=self.filters["prune filter"],
            max_depth=self.filters["depth filter"],
            min_age=self.filters["age filter"],
        )
        files = list(finder.find())

        # Act
        counters = finder.get_counters()

        # Assert
        self.assertEqual(
            counters["dirs"], self.expected_counters["all filters"]["dirs"]
        )
        self.assertEqual(
            counters["files"], self.expected_counters["all filters"]["files"]
        )
        self.assertEqual(
            counters["depth"], self.expected_counters["all filters"]["depth"]
        )
        self.assertEqual(
            counters["found"], self.expected_counters["all filters"]["found"]
        )


if __name__ == "__main__":
    unittest.main()
