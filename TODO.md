# MediaLocate Project TODOs

## CI/CD Implementation Goals

### GitHub Actions Setup
1. Workflow for automated testing and quality checks:
   - Run pre-commit hooks
   - Execute pytest suite with coverage
   - Publish coverage reports
   - Set up automated PyPI publishing
   - Multi-platform support (Windows & Ubuntu)
   - Multi-Python version testing (3.9-3.12)

### Current Project Status
- Poetry setup complete
- Test coverage configuration in place (80% minimum)
- Pre-commit hooks configured
- Development tools configured:
  - Black (formatting)
  - Flake8 (linting)
  - MyPy (type checking)
  - Bandit (security)

### Next Steps
1. GitHub repository settings:
   - Set up branch protection rules
   - Add PR templates
   - Add Issue templates
2. Documentation:
   - Add contributing guidelines (CONTRIBUTING.md)
   - Update installation instructions
   - Add development setup guide
3. Release Management:
   - Create release strategy document
   - Define versioning scheme
   - Set up changelog automation

### Reference Commands
```bash
# Run tests with coverage
poetry run pytest

# Coverage reports will be generated in:
# - htmlcov/ (HTML report)
# - coverage.xml (XML report)
# - Terminal output (missing lines)
```

### Future Improvements
1. Testing Enhancements:
   - Fix failing unit tests (7 failures identified):
     * TestProcessingStatus.test_update_new
     * TestMediaProxies.test_proxies_initialization
     * 5 tests in TestMediaServer/TestServiceHandler
   - Increase coverage in low-coverage modules:
     * location/gps.py (64% → 80%)
     * locate_media.py (78% → 85%)
     * web/media_server.py (81% → 90%)
   - Add more integration tests
   - Improve test isolation and mocking

2. Documentation:
   - Add API documentation:
     * Module documentation
     * Class/function documentation
     * Usage examples
   - Improve README with:
     * Installation instructions
     * Quick start guide
     * Configuration options
     * Development setup
   - Add contributing guidelines:
     * Code style guide
     * PR process
     * Testing requirements

3. Code Quality:
   - Resolve remaining type hints issues
   - Address security scan findings
   - Improve error handling:
     * Add custom exceptions
     * Better error messages
     * Proper error propagation
   - Add more comprehensive logging:
     * Structured logging
     * Log levels
     * Log rotation

### Security Improvements
1. URL Validation Enhancement:
   - Improve URL scheme validation in `media_server.py`
   - Add network location validation for http(s) URLs
   - Add path validation for file:// URLs
   - Integrate with existing `validate_url` function
   - Add detailed logging for validation failures
2. General Security:
   - Review and update all `# nosec` directives
   - Add Content Security Policy headers
   - Implement request rate limiting
   - Add session management for web interface
