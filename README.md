# MediaLocate

## Project Overview

MediaLocate is a Python tool designed for analyzing and organizing media files based on geolocation data. It helps users manage and sort their media collections by leveraging GPS metadata embedded in photos and videos.

### Current Version

**Version**: 0.1.0 (Initial Release)
**Status**: Alpha Development

## Installation Instructions

### Prerequisites

- Python 3.9 or higher
- Poetry for package management

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/medialocate.git
   cd medialocate
   ```

2. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

## Versioning

MediaLocate follows Semantic Versioning (SemVer) 2.0.0:

- **MAJOR** (x.0.0): Incompatible API changes
- **MINOR** (0.x.0): Backward-compatible new features
- **PATCH** (0.0.x): Backward-compatible bug fixes

Current version: 0.1.0 (Alpha)

For detailed versioning guidelines, see [VERSIONING.md](VERSIONING.md)

### Version Increment Commands

```bash
# Increment patch version
poetry version patch

# Increment minor version
poetry version minor

# Increment major version
poetry version major
```

## Usage Examples

### Command-Line Usage

To group media files by location:
```bash
poetry run medialocate group --directory /path/to/media
```

### Python API

```python
from medialocate import group_media

group_media('/path/to/media', threshold=0.5)
```

## Configuration Options

- **Threshold**: Set the distance threshold for grouping media (default: 0.5 km).
- **Output Directory**: Specify a directory for organized output.

## Development Setup Guide

1. Set up a virtual environment:
   ```bash
   poetry shell
   ```

2. Run tests:
   ```bash
   pytest
   ```

3. Code formatting and linting:
   ```bash
   black .
   flake8
   ```

4. Contributing:
   - Fork the repository
   - Create a feature branch
   - Submit a pull request
