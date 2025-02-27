# MediaLocate Versioning Strategy

## Semantic Versioning (SemVer)

We follow Semantic Versioning (SemVer) 2.0.0 for version management.

### Version Format: MAJOR.MINOR.PATCH

- **MAJOR** (x.0.0): Incompatible API changes
  - Breaking changes in functionality
  - Significant architectural redesigns
  - Removal of deprecated features

- **MINOR** (0.x.0): Backward-compatible new features
  - New functionality
  - Non-breaking improvements
  - New optional features or enhancements

- **PATCH** (0.0.x): Backward-compatible bug fixes
  - Bug fixes
  - Performance improvements
  - Small optimizations that don't add new features

### Current Version: 0.1.0 (Alpha)

### Version Increment Commands

Use Poetry to manage version increments:

```bash
# Increment patch version (0.0.x)
poetry version patch

# Increment minor version (0.x.0)
poetry version minor

# Increment major version (x.0.0)
poetry version major
```

### Release Process

1. Update CHANGELOG.md with changes
2. Run tests and ensure all checks pass
3. Commit changes with version bump commit message
4. Create a git tag for the new version
5. Push changes and tags to repository

### Development Status Classifiers

- 0.x.x: Alpha - Experimental, may change significantly
- 1.0.0: Beta - Feature-complete, stable API
- 2.0.0+: Stable release with potential major changes
