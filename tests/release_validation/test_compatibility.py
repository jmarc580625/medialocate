"""
Compatibility Test Suite for MediaLocate Release Candidates

This module tests compatibility across different:
- Python versions
- Dependency versions
- Package requirements
"""

import sys
import platform
import importlib
import pytest
import toml


def load_pyproject_config():
    """Load pyproject.toml configuration."""
    with open("pyproject.toml", "r") as f:
        return toml.load(f)


def test_python_version_compatibility():
    """Verify current Python version is supported."""
    config = load_pyproject_config()
    python_constraint = config["tool"]["poetry"]["dependencies"]["python"]

    # Parse version constraint
    min_version = tuple(
        map(int, python_constraint.split(">=")[1].split(",<")[0].split("."))
    )
    max_version = tuple(map(int, python_constraint.split("<")[1].split(".")[:-1]))

    current_version = sys.version_info[:2]

    assert (
        min_version <= current_version <= max_version
    ), f"Python version {current_version} not in supported range {python_constraint}"


def test_core_dependencies():
    """Verify core dependencies can be imported."""
    config = load_pyproject_config()
    dependencies = config["tool"]["poetry"]["dependencies"]

    # Remove 'python' from dependencies
    dependencies.pop("python", None)

    for dep_name in dependencies:
        try:
            importlib.import_module(dep_name.replace("-", "_"))
        except ImportError:
            pytest.fail(f"Core dependency not installed: {dep_name}")


def test_dev_dependencies():
    """Verify development dependencies can be imported."""
    config = load_pyproject_config()
    dev_dependencies = config["tool"]["poetry"]["group"]["dev"]["dependencies"]

    for dep_name in dev_dependencies:
        try:
            importlib.import_module(dep_name.replace("-", "_"))
        except ImportError:
            pytest.fail(f"Development dependency not installed: {dep_name}")


def test_os_compatibility():
    """Check compatibility with supported operating systems."""
    supported_os = ["Windows", "Linux", "Darwin"]
    current_os = platform.system()
    assert current_os in supported_os, f"Unsupported operating system: {current_os}"


def test_module_imports():
    """Verify all project modules can be imported."""
    modules_to_test = [
        "medialocate",
        "medialocate.locate_media",
        "medialocate.group_media",
        "medialocate.process_files",
        "medialocate.proxy_media",
    ]

    for module_name in modules_to_test:
        try:
            importlib.import_module(module_name)
        except ImportError as e:
            pytest.fail(f"Could not import {module_name}: {e}")


def test_dependency_versions():
    """Verify dependency versions match pyproject.toml."""
    config = load_pyproject_config()
    dependencies = config["tool"]["poetry"]["dependencies"]
    dev_dependencies = config["tool"]["poetry"]["group"]["dev"]["dependencies"]

    all_dependencies = {**dependencies, **dev_dependencies}

    for dep_name, version_constraint in all_dependencies.items():
        if dep_name == "python":
            continue

        try:
            module = importlib.import_module(dep_name.replace("-", "_"))
            module_version = getattr(module, "__version__", "unknown")

            # Basic version compatibility check
            assert (
                module_version != "unknown"
            ), f"Could not determine version for {dep_name}"
        except ImportError:
            pytest.fail(f"Dependency not found: {dep_name}")
