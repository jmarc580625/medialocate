"""Common test fixtures and configuration."""
import os
import pytest
import tempfile
import shutil


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files.

    Yields:
        str: Path to temporary directory
    """
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_data_dir():
    """Get the path to the test data directory.

    Returns:
        str: Path to test data directory
    """
    return os.path.join(os.path.dirname(__file__), "data")
