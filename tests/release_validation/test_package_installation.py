"""Package Installation Verification Test.

This module provides a comprehensive test to verify package installation
and basic functionality across different environments.
"""

import os
import sys
import subprocess
import pytest
import shutil
import venv


def create_test_venv(base_path):
    """Create a clean virtual environment for testing."""
    venv_path = os.path.join(base_path, "install_test_env")

    # Remove existing environment if it exists
    if os.path.exists(venv_path):
        shutil.rmtree(venv_path)

    # Create new virtual environment
    venv.create(venv_path, with_pip=True)
    return venv_path


def run_command(command, cwd=None, env=None):
    """Run a shell command and return its output."""
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        cwd=cwd,
        env=env,
    )
    stdout, stderr = process.communicate()
    return process.returncode, stdout.decode(), stderr.decode()


@pytest.fixture(scope="module")
def project_root():
    """Fixture to provide the project root directory."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def test_package_installation(project_root):
    """Verify package can be built, installed, and imported in a clean environment."""
    # Paths
    dist_dir = os.path.join(project_root, "dist")

    # Create virtual environment
    venv_path = create_test_venv(project_root)
    python_exe = os.path.join(venv_path, "Scripts", "python")
    pip_exe = os.path.join(venv_path, "Scripts", "pip")

    # Build package
    build_code, build_out, build_err = run_command("poetry build", cwd=project_root)
    assert build_code == 0, f"Package build failed: {build_err}"

    # Find the wheel file
    wheel_files = [f for f in os.listdir(dist_dir) if f.endswith(".whl")]
    assert wheel_files, "No wheel file found after build"
    wheel_path = os.path.join(dist_dir, wheel_files[0])

    # Install package
    install_code, install_out, install_err = run_command(
        f"{pip_exe} install {wheel_path}", cwd=project_root
    )
    assert install_code == 0, f"Package installation failed: {install_err}"

    # Verify package can be imported
    import_code, import_out, import_err = run_command(
        f'{python_exe} -c "import medialocate; print(medialocate.__version__)"',
        cwd=project_root,
    )
    assert import_code == 0, f"Package import failed: {import_err}"
    assert import_out.strip() == "0.1.0", f"Incorrect package version: {import_out}"


def test_package_modules(project_root):
    """Verify key modules can be imported."""
    venv_path = os.path.join(project_root, "install_test_env")
    python_exe = os.path.join(venv_path, "Scripts", "python")

    # List of modules to test
    modules_to_test = [
        "medialocate.locate_media",
        "medialocate.group_media",
        "medialocate.process_files",
        "medialocate.proxy_media",
    ]

    for module in modules_to_test:
        code, out, err = run_command(
            f'{python_exe} -c "import {module}"', cwd=project_root
        )
        assert code == 0, f"Failed to import {module}: {err}"


def test_cleanup(project_root):
    """
    Removed cleanup function to preserve the test environment
    for potential manual testing after the automated tests.

    The create_test_venv function will handle cleaning/recreating
    the environment at the start of each test run.
    """
    pass  # No-op function
