#!/bin/bash

# Version Increment Script for MediaLocate

# Check if the correct number of arguments is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 [patch|minor|major]"
    exit 1
fi

# Determine version increment type
case "$1" in
    patch)
        poetry version patch
        ;;
    minor)
        poetry version minor
        ;;
    major)
        poetry version major
        ;;
    *)
        echo "Invalid version increment type. Use patch, minor, or major."
        exit 1
        ;;
esac

# Get the new version
NEW_VERSION=$(poetry version -s)

# Update version in other files if needed
sed -i "s/__version__ = \".*\"/__version__ = \"$NEW_VERSION\"/g" src/medialocate/__init__.py

# Optional: Update CHANGELOG.md
echo "## [$NEW_VERSION] - $(date +%Y-%m-%d)" | cat - CHANGELOG.md > temp && mv temp CHANGELOG.md

echo "Version incremented to $NEW_VERSION"
