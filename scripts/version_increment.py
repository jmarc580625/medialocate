#!/usr/bin/env python3
"""
Cross-platform version increment script for MediaLocate.

Supports both Windows and Linux environments.
Usage: python version_increment.py [patch|minor|major]
"""

import os
import sys
import subprocess
import re


def update_version_in_file(filepath, new_version):
    """Update version in a specific file."""
    with open(filepath, "r") as f:
        content = f.read()

    # Replace version string
    updated_content = re.sub(
        r'__version__\s*=\s*[\'"].*[\'"]', f'__version__ = "{new_version}"', content
    )

    with open(filepath, "w") as f:
        f.write(updated_content)


def update_changelog(new_version):
    """Update CHANGELOG.md with new version."""
    from datetime import date

    changelog_path = os.path.join(os.path.dirname(__file__), "..", "CHANGELOG.md")

    today = date.today().isoformat()
    new_entry = f"## [{new_version}] - {today}\n\n"

    try:
        with open(changelog_path, "r") as f:
            existing_content = f.read()

        with open(changelog_path, "w") as f:
            f.write(new_entry + existing_content)
    except Exception as e:
        print(f"Warning: Could not update CHANGELOG.md: {e}")


def main():
    # Validate input
    if len(sys.argv) != 2 or sys.argv[1] not in ["patch", "minor", "major"]:
        print("Usage: python version_increment.py [patch|minor|major]")
        sys.exit(1)

    version_type = sys.argv[1]

    # Project root (assuming script is in scripts directory)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # Run Poetry version command
    try:
        result = subprocess.run(
            ["poetry", "version", version_type],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            sys.exit(1)

        # Get the new version
        new_version = result.stdout.strip().split()[-1]
        print(f"New version: {new_version}")

        # Update version in __init__.py
        init_path = os.path.join(project_root, "src", "medialocate", "__init__.py")
        update_version_in_file(init_path, new_version)

        # Update CHANGELOG
        update_changelog(new_version)

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
