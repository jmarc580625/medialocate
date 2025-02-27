# MediaLocate Scripts

## Changelog Generation Script

### Overview
`generate_changelog.py` is a Python script that automatically generates a changelog based on Git commit history.

### Features
- Categorizes commits into:
  * Features
  * Bug Fixes
  * Documentation
  * Performance
  * Refactoring
  * Other changes
- Supports conventional commit message format
- Preserves existing changelog content
- Generates version-based or date-based changelog

### Usage
```bash
# Run the script
python generate_changelog.py

# Optional: Specify a version
python generate_changelog.py --version v0.2.0
```

### Commit Message Guidelines
To maximize changelog effectiveness, use conventional commit prefixes:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `perf:` for performance improvements
- `refactor:` for code refactoring

Example:
```
feat(media-parser): Add support for HEIC image format
fix(geolocation): Resolve coordinate parsing error
```
