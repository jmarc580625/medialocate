# Contributing to MediaLocate

## Branch Protection Guidelines

### Main Branch Protection Rules

1. **Pull Requests Required**
   - All changes to the `main` branch must be made through pull requests
   - Direct commits to `main` are not allowed

2. **Commit Signature**
   - All commits must be signed
   - Unsigned commits will be rejected

3. **Automated Checks**
   Before a pull request can be merged, the following checks must pass:
   - Continuous Integration (CI) workflow
   - Code coverage threshold (80%)
   - Linting checks
   - Type checking
   - Security scans

4. **Linear History**
   - Merge commits are not allowed
   - Use rebase or squash when merging

### Workflow for Contributors

1. Create a feature branch from `main`
2. Make your changes
3. Sign your commits
4. Open a pull request
5. Ensure all automated checks pass
6. Request review if needed
7. Merge using squash or rebase

### Commit Signing

To sign your commits:

```bash
# Configure Git to use your GPG key
git config --global user.signingkey YOUR_GPG_KEY
git config --global commit.gpgsign true

# Or sign individual commits
git commit -S -m "Your commit message"
```

### Recommended Tools

- Use `pre-commit` hooks to catch issues early
- Configure your IDE to show linting and type checking warnings
