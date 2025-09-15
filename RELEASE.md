# Release Guide for PyASAN

This guide explains how to automatically publish PyASAN to PyPI when you push to GitHub.

## Setup (One-time)

### 1. Create PyPI API Token

1. Go to [PyPI Account Settings](https://pypi.org/manage/account/)
2. Scroll to "API tokens" section
3. Click "Add API token"
4. Give it a name like "PyASAN GitHub Actions"
5. Select "Entire account" scope (or limit to just pyasan project if it exists)
6. Copy the token (starts with `pypi-`)

### 2. Add Token to GitHub Secrets

1. Go to your GitHub repository
2. Click Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Name: `PYPI_API_TOKEN`
5. Value: Paste your PyPI token
6. Click "Add secret"

### 3. Push the GitHub Actions Workflows

The workflows are already created in `.github/workflows/`:
- `test.yml` - Runs tests on every push/PR
- `publish.yml` - Publishes to PyPI on version tags

```bash
git add .github/
git commit -m "Add GitHub Actions for testing and PyPI publishing"
git push origin main
```

## How to Release

### Option 1: Using the Release Script (Recommended)

```bash
# Make sure you're on the main branch and it's clean
git checkout main
git pull origin main

# Run the release script with the new version
python scripts/release.py 0.3.0

# The script will:
# 1. Update version numbers in pyproject.toml and __init__.py
# 2. Run tests to make sure everything works
# 3. Commit the version changes
# 4. Create and push a git tag
# 5. GitHub Actions will automatically publish to PyPI
```

### Option 2: Manual Release

```bash
# 1. Update version in pyproject.toml and pyasan/__init__.py
# From: version = "0.2.0"
# To:   version = "0.3.0"

# 2. Commit the changes
git add pyproject.toml pyasan/__init__.py
git commit -m "Bump version to 0.3.0"

# 3. Create and push tag
git tag -a v0.3.0 -m "Release 0.3.0"
git push origin main
git push origin v0.3.0

# 4. GitHub Actions will automatically publish to PyPI
```

## What Happens Automatically

When you push a version tag (like `v0.3.0`):

1. **GitHub Actions Triggers**: The `publish.yml` workflow runs
2. **Tests Run**: All tests run on Python 3.8-3.12
3. **Code Quality**: Linting and type checking
4. **Package Build**: Creates wheel and source distribution
5. **PyPI Upload**: Automatically uploads to PyPI using your token

## Monitoring

- **GitHub Actions**: Check the Actions tab in your repo
- **PyPI**: New version appears at https://pypi.org/project/pyasan/
- **Installation**: Users can install with `pip install pyasan`

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **Patch** (0.2.0 → 0.2.1): Bug fixes, small improvements
- **Minor** (0.2.0 → 0.3.0): New features, backward compatible
- **Major** (0.2.0 → 1.0.0): Breaking changes

## Troubleshooting

### Build Fails
- Check the Actions tab for error details
- Common issues: test failures, linting errors, missing dependencies

### PyPI Upload Fails
- Verify `PYPI_API_TOKEN` secret is set correctly
- Make sure the version number is unique (can't re-upload same version)
- Check PyPI token permissions

### Version Already Exists
- You can't overwrite a version on PyPI
- Increment to the next version number
- Delete the tag locally and remotely if needed:
  ```bash
  git tag -d v0.3.0
  git push origin --delete v0.3.0
  ```

## Testing Before Release

Always test locally before releasing:

```bash
# Run tests
pytest tests/ -v

# Check code quality
black --check pyasan tests
flake8 pyasan tests --max-line-length=88

# Test build
python -m build
twine check dist/*

# Test CLI
pyasan --version
pyasan apod get --help
pyasan mars --help
```

## Emergency Rollback

If you need to remove a bad release:

1. **PyPI**: You can't delete versions, but you can "yank" them
2. **GitHub**: Delete the tag and create a new patch version
3. **Users**: They'll need to upgrade to the fixed version

## Example Release Flow

```bash
# Current version: 0.2.0
# Adding new feature, so minor version bump

# 1. Make your changes and commit them
git add .
git commit -m "Add new NASA API endpoint"

# 2. Release
python scripts/release.py 0.3.0

# 3. Monitor
# Check GitHub Actions: https://github.com/yourusername/pyasan/actions
# Check PyPI: https://pypi.org/project/pyasan/

# 4. Announce
# Update README, social media, etc.
```

This automated setup ensures that every release is:
- ✅ Tested on multiple Python versions
- ✅ Code quality checked
- ✅ Properly built and validated
- ✅ Automatically published to PyPI
- ✅ Tagged and documented in Git
