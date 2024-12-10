"""
Security Test Suite for MediaLocate Release Candidates

This module tests runtime security aspects complementing Bandit's static analysis.
Focuses on:
- Input validation
- Sensitive data protection
- Runtime security checks
"""

import os
import sys
import subprocess
import pytest
import importlib.util


def test_bandit_security_scan():
    """Run Bandit security scan and verify no high-severity issues."""
    try:
        # Run Bandit with XML output for parsing
        result = subprocess.run(
            [
                "bandit",
                "-r",
                "src/medialocate",
                "-f",
                "xml",
                "-lll",  # Only report high-severity issues
            ],
            capture_output=True,
            text=True,
        )

        # Parse XML output (simplified)
        assert (
            "issue" not in result.stdout
        ), f"Bandit detected security issues:\n{result.stdout}"
    except FileNotFoundError:
        pytest.skip("Bandit not installed")


def test_runtime_input_sanitization():
    """Verify input sanitization mechanisms."""
    from medialocate import process_files

    malicious_inputs = [
        "../../../etc/passwd",
        "$(command)",
        "`command`",
        "; rm -rf /",
        '<script>alert("XSS")</script>',
    ]

    for input_path in malicious_inputs:
        with pytest.raises(
            (ValueError, SecurityWarning), match="Invalid|Potential security risk"
        ):
            process_files.validate_file_path(input_path)


def test_sensitive_data_protection():
    """Ensure sensitive metadata is not exposed."""
    from medialocate import process_files

    mock_file = {
        "path": "test_sensitive.jpg",
        "metadata": {
            "gps": {"latitude": 40.7128, "longitude": -74.0060},
            "personal_info": "Sensitive data",
            "device_info": "Confidential hardware details",
        },
    }

    processed_file = process_files.sanitize_metadata(mock_file)

    # Verify sensitive information is stripped
    assert (
        "personal_info" not in processed_file["metadata"]
    ), "Personal information not stripped"
    assert (
        "device_info" not in processed_file["metadata"]
    ), "Device information not stripped"

    # Ensure critical location data remains
    assert "gps" in processed_file["metadata"], "Critical location data removed"


def test_file_permission_handling():
    """Verify secure file permission handling."""
    from medialocate import process_files

    # Create a test file with restricted permissions
    test_file = "test_restricted.txt"
    with open(test_file, "w") as f:
        f.write("Restricted content")

    try:
        # Set very restrictive permissions
        os.chmod(test_file, 0o400)  # Read-only for owner

        # Attempt to process the file
        result = process_files.process_media_files([test_file])
        assert result is not None, "Failed to handle restricted file"

    except PermissionError:
        pytest.fail("Unable to handle file with restricted permissions")

    finally:
        # Clean up
        try:
            os.unlink(test_file)
        except:
            pass


def test_dependency_security():
    """Check for known security vulnerabilities in dependencies."""
    try:
        import safety

        # Run safety check
        result = subprocess.run(
            ["safety", "check", "--full-report"], capture_output=True, text=True
        )

        # Verify no vulnerabilities
        assert (
            result.returncode == 0
        ), f"Dependency vulnerabilities detected:\n{result.stdout}"

    except ImportError:
        pytest.skip("Safety not installed for dependency vulnerability check")
