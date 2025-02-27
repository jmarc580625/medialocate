# Release Management Workflow

## Overview
This document outlines the release process for MediaLocate, designed to work with a feature branch strategy and semantic versioning.

## Branching Strategy
- `main`: Stable, production-ready code
- `develop`: Integration branch for upcoming release
- `feature/*`: Individual feature development
- `release/vX.Y.Z`: Release preparation branches
- `hotfix/*`: Critical bug fixes for production

## Release Process

### 1. Preparation
1. Merge completed features into `develop` branch
2. Ensure all tests pass
3. Update CHANGELOG.md with notable changes

### 2. Release Candidate Creation
1. Create a `release/vX.Y.Z` branch from `develop`
   ```bash
   git checkout -b release/v0.2.0 develop
   ```

2. Version Increment Workflow
   - **PATCH (0.0.x)**: Bug fixes, small improvements
   - **MINOR (0.x.0)**: New features, non-breaking changes
   - **MAJOR (x.0.0)**: Breaking changes, significant rewrites

   Use Poetry to increment version:
   ```bash
   # For patch release
   poetry version patch

   # For minor release
   poetry version minor

   # For major release
   poetry version major
   ```

### 3. Release Validation
1. Run comprehensive test suite
   ```bash
   poetry run pytest
   ```

2. Package Build and Installation Test
   ```bash
   # Build package
   poetry build

   # Run package installation verification
   poetry run pytest tests/integration/test_package_installation.py
   ```

### 4. Release Finalization
1. Merge release branch to `main`
   ```bash
   git checkout main
   git merge --no-ff release/v0.2.0
   git tag -a v0.2.0 -m "Release version 0.2.0"
   ```

2. Merge back to `develop`
   ```bash
   git checkout develop
   git merge --no-ff release/v0.2.0
   ```

3. Publish to PyPI (optional)
   ```bash
   poetry publish
   ```

### 5. Post-Release
- Delete release branch
- Update documentation
- Communicate changes to stakeholders

## Automation Considerations
- Use GitHub Actions or similar CI/CD tool
- Automate tests, build, and potentially deployment
- Implement branch protection rules

## Version Naming Convention
- Pre-release: `0.Y.Z` (e.g., `0.1.0-alpha`)
- First stable release: `1.0.0`

## Exceptional Scenarios
- **Hotfix**: Create from `main`, merge back to `main` and `develop`
- **Critical Bug**: May skip minor validation steps

## Tools and Dependencies
- Poetry for version management
- Pytest for testing
- GitHub Actions (recommended for CI/CD)
