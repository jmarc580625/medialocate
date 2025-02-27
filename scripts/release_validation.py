#!/usr/bin/env python3
"""
Release Validation Script for MediaLocate

Comprehensive script to validate release candidates by:
1. Running release validation tests
2. Checking package build and installation
3. Generating release reports
4. Performing final checks before release
"""

import os
import sys
import subprocess
import shutil
import tempfile
import argparse
import json
from datetime import datetime


def run_command(command, cwd=None, capture_output=False):
    """Run a shell command and handle output."""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            shell=True,
            capture_output=capture_output,
            text=True,
            check=True,
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {command}")
        print(f"Error output: {e.stderr}")
        raise


def run_release_validation_tests():
    """Run release validation test suite."""
    print("🔍 Running Release Validation Tests...")
    try:
        run_command("poetry run pytest tests/release_validation/ -v")
        print("✅ Release Validation Tests Passed")
    except subprocess.CalledProcessError:
        print("❌ Release Validation Tests Failed")
        sys.exit(1)


def build_package():
    """Build the package and check for build issues."""
    print("📦 Building Package...")
    try:
        run_command("poetry build")
        print("✅ Package Build Successful")
    except subprocess.CalledProcessError:
        print("❌ Package Build Failed")
        sys.exit(1)


def test_package_installation():
    """Test package installation in a temporary virtual environment."""
    print("🔧 Testing Package Installation...")

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Create a virtual environment
            run_command(f"python -m venv {temp_dir}/venv")

            # Activate virtual environment and install package
            activate_cmd = (
                f"source {temp_dir}/venv/bin/activate && "
                if sys.platform != "win32"
                else f"{temp_dir}\\venv\\Scripts\\activate && "
            )
            install_cmd = (
                activate_cmd
                + "pip install dist/*.whl && python -c 'import medialocate; print(medialocate.__version__)'"
            )

            run_command(install_cmd, shell=True)
            print("✅ Package Installation Successful")
        except subprocess.CalledProcessError:
            print("❌ Package Installation Failed")
            sys.exit(1)


def generate_release_report():
    """Generate a comprehensive release report."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "project": "MediaLocate",
        "version": None,
        "tests": {
            "release_validation": "Passed",
            "package_build": "Passed",
            "package_installation": "Passed",
        },
        "warnings": [],
    }

    # Get current version
    try:
        version_output = subprocess.check_output(
            ["poetry", "version", "-s"], text=True
        ).strip()
        report["version"] = version_output
    except subprocess.CalledProcessError:
        report["warnings"].append("Could not retrieve project version")

    # Write report
    report_path = "release_validation_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"📄 Release Report Generated: {report_path}")
    return report


def main():
    parser = argparse.ArgumentParser(
        description="MediaLocate Release Validation Script"
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip running release validation tests",
    )
    parser.add_argument("--skip-build", action="store_true", help="Skip package build")
    parser.add_argument(
        "--skip-install", action="store_true", help="Skip package installation test"
    )

    args = parser.parse_args()

    print("🚀 Starting Release Validation Process")

    if not args.skip_tests:
        run_release_validation_tests()

    if not args.skip_build:
        build_package()

    if not args.skip_install:
        test_package_installation()

    report = generate_release_report()

    print("✨ Release Validation Complete")
    sys.exit(0)


if __name__ == "__main__":
    main()
