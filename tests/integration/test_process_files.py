"""Integration tests for process_files command."""

import os
import time
import shutil
import logging
import tempfile
import unittest
from pathlib import Path
from typing import List, Dict, Optional

from medialocate.process_files import main
from medialocate.batch.status import ProcessingStatus
from medialocate.store.dict import DictStore
from medialocate.util.file_naming import to_posix


class TestProcessFiles(unittest.TestCase):
    """Integration tests for process_files command"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.purge_mode = False
        self.clear_mode = False
        self.force_option = False
        self.verbose_level = 0
        logging.basicConfig(level=logging.NOTSET)
        self.log = logging.getLogger("TestDriver")

        """Create test environment with controlled directory structure"""
        # Create test root directory for test files
        self.test_root = self.test_dir

        # changes working directory for test root
        self.cwd = os.getcwd()
        os.chdir(self.test_root)

        # Create memory directory for test files
        self.memory_dir = os.path.join(self.test_root, ".process_store")
        os.makedirs(self.memory_dir, exist_ok=True)

    def tearDown(self):
        # Clean up test environment
        os.chdir(self.cwd)
        shutil.rmtree(self.test_root)

    def create_test_file(
        self, name: str, content: str = "", mtime: Optional[float] = None
    ) -> None:
        """Create a test file with given content and modification time"""
        file_path = os.path.join(self.test_root, name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w") as f:
            f.write(content)

        if mtime:
            os.utime(file_path, (mtime, mtime))

    def create_status(
        self,
        filename: str,
        state: ProcessingStatus.State,
        timestamp: Optional[float] = None,
    ) -> None:
        """Create a status entry for a file"""
        store = DictStore(self.memory_dir, "pmstatus.json")
        store.open()
        file_hash = ProcessingStatus.filename_hash(filename)
        store.set(
            file_hash,
            {
                "state": state.value,
                "filename": filename,
                "time": timestamp or time.time(),
            },
        )
        store.close()

    def get_status(self, filename: str) -> Optional[Dict]:
        """Get current status store contents"""
        store = DictStore(self.memory_dir, "pmstatus.json")
        store.open()
        file_hash = ProcessingStatus.filename_hash(filename)
        status = store.get(file_hash)
        store.close()
        return status

    def test_basic_processing(self):
        """Test basic file processing with no existing status"""
        # Create test files
        filename1 = "file1.txt"
        dirname1 = "dir1"
        path1 = os.path.join(dirname1, filename1)
        path1_posix = to_posix(path1)
        filename2 = "file2.txt"

        self.create_test_file(path1, "test1")
        self.create_test_file(filename2, "test2")

        # Run process_files
        result = main(
            self.memory_dir,
            self.purge_mode,
            self.clear_mode,
            self.force_option,
            self.verbose_level,
            self.log,
        )
        self.assertEqual(result, 0)

        # Verify both files were processed
        status1 = self.get_status(path1_posix)
        status2 = self.get_status(filename2)
        self.assertEqual(status1["state"], ProcessingStatus.State.DONE.value)
        self.assertEqual(status2["state"], ProcessingStatus.State.DONE.value)

    def test_force_processing(self):
        """Test force processing of files regardless of status"""
        # Create test file with old status
        now = time.time()
        old_time = now - 3600  # 1 hour ago

        self.create_test_file("file1.txt", "test1")
        self.create_status("file1.txt", ProcessingStatus.State.DONE, old_time)

        # Run process_files with force option
        self.force_option = True
        result = main(
            self.memory_dir,
            self.purge_mode,
            self.clear_mode,
            self.force_option,
            self.verbose_level,
            self.log,
        )
        self.assertEqual(result, 0)

        # Verify file was reprocessed
        status = self.get_status("file1.txt")
        self.assertEqual(status["state"], ProcessingStatus.State.DONE.value)
        self.assertGreater(status["time"], old_time)

    def test_clear_status(self):
        """Test clearing all status entries"""
        # Create test file with status
        self.create_test_file("file1.txt", "test1")
        self.create_status("file1.txt", ProcessingStatus.State.DONE)

        # Run process_files with clear option
        self.clear_mode = True
        result = main(
            self.memory_dir,
            self.purge_mode,
            self.clear_mode,
            self.force_option,
            self.verbose_level,
            self.log,
        )
        self.assertEqual(result, 0)

        # Verify status was cleared
        self.assertIsNone(self.get_status("file1.txt"))

    def test_purge_orphaned(self):
        """Test purging orphaned status entries"""
        # Create one file with status and one orphaned status
        self.create_test_file("file1.txt", "test1")
        self.create_status("file1.txt", ProcessingStatus.State.DONE)
        self.create_status("file2.txt", ProcessingStatus.State.DONE)  # Orphaned status

        # Run process_files with purge option
        self.purge_mode = True
        result = main(
            self.memory_dir,
            self.purge_mode,
            self.clear_mode,
            self.force_option,
            self.verbose_level,
            self.log,
        )
        self.assertEqual(result, 0)

        # Verify orphaned status was removed but valid status remains
        self.assertIsNotNone(self.get_status("file1.txt"))
        self.assertIsNone(self.get_status("file2.txt"))

    def test_error_handling(self):
        """Test processing files with error status"""
        # Create test file with error status
        self.create_test_file("file1.txt", "test1")
        self.create_status("file1.txt", ProcessingStatus.State.ERROR)

        # Run process_files
        result = main(
            self.memory_dir,
            self.purge_mode,
            self.clear_mode,
            self.force_option,
            self.verbose_level,
            self.log,
        )
        self.assertEqual(result, 0)

        # Verify file was reprocessed
        status = self.get_status("file1.txt")
        self.assertEqual(status["state"], ProcessingStatus.State.DONE.value)


if __name__ == "__main__":
    unittest.main()
