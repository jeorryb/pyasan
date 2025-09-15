#!/usr/bin/env python3
"""
Release script for PyASAN.

This script helps automate the release process by:
1. Updating version numbers in all relevant files
2. Creating a git tag
3. Pushing to GitHub (which triggers PyPI publication)
"""

import os
import re
import sys
import subprocess
from pathlib import Path


def get_current_version():
    """Get the current version from pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        print("Error: pyproject.toml not found")
        sys.exit(1)
    
    content = pyproject_path.read_text()
    match = re.search(r'version = "([^"]+)"', content)
    if not match:
        print("Error: Could not find version in pyproject.toml")
        sys.exit(1)
    
    return match.group(1)


def update_version_in_file(file_path, old_version, new_version):
    """Update version in a specific file."""
    if not Path(file_path).exists():
        print(f"Warning: {file_path} not found, skipping")
        return
    
    content = Path(file_path).read_text()
    updated_content = content.replace(old_version, new_version)
    
    if content != updated_content:
        Path(file_path).write_text(updated_content)
        print(f"Updated version in {file_path}")
    else:
        print(f"No version found to update in {file_path}")


def run_command(cmd, check=True):
    """Run a shell command."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if check and result.returncode != 0:
        print(f"Error running command: {cmd}")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
        sys.exit(1)
    
    return result


def main():
    """Main release function."""
    if len(sys.argv) != 2:
        print("Usage: python scripts/release.py <new_version>")
        print("Example: python scripts/release.py 0.3.0")
        sys.exit(1)
    
    new_version = sys.argv[1]
    
    # Validate version format (basic check)
    if not re.match(r'^\d+\.\d+\.\d+$', new_version):
        print("Error: Version must be in format X.Y.Z (e.g., 0.3.0)")
        sys.exit(1)
    
    # Get current version
    current_version = get_current_version()
    print(f"Current version: {current_version}")
    print(f"New version: {new_version}")
    
    # Confirm with user
    response = input("Continue with release? (y/N): ")
    if response.lower() != 'y':
        print("Release cancelled")
        sys.exit(0)
    
    # Update version in files
    files_to_update = [
        "pyproject.toml",
        "pyasan/__init__.py",
    ]
    
    for file_path in files_to_update:
        update_version_in_file(file_path, current_version, new_version)
    
    # Run tests
    print("\nRunning tests...")
    run_command("python -m pytest tests/ -v")
    
    # Check if git is clean
    result = run_command("git status --porcelain", check=False)
    if result.stdout.strip():
        print("\nGit working directory is not clean. Staging version changes...")
        run_command("git add pyproject.toml pyasan/__init__.py")
        run_command(f'git commit -m "Bump version to {new_version}"')
    
    # Create and push tag
    tag_name = f"v{new_version}"
    print(f"\nCreating tag: {tag_name}")
    run_command(f'git tag -a {tag_name} -m "Release {new_version}"')
    
    print(f"\nPushing tag to GitHub...")
    run_command("git push origin main")  # or master, depending on your default branch
    run_command(f"git push origin {tag_name}")
    
    print(f"""
✅ Release {new_version} completed!

The GitHub Action will now:
1. Run tests on multiple Python versions
2. Build the package
3. Publish to PyPI automatically

You can monitor the progress at:
https://github.com/yourusername/pyasan/actions

The package should be available on PyPI shortly at:
https://pypi.org/project/pyasan/
""")


if __name__ == "__main__":
    main()
