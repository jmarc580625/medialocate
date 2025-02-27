#!/usr/bin/env python3
import os
import re
import subprocess
from datetime import datetime
from typing import List, Dict, Tuple


def run_git_command(command: List[str]) -> str:
    """Run a git command and return its output."""
    try:
        return subprocess.check_output(command, text=True).strip()
    except subprocess.CalledProcessError:
        return ""


def get_commits_since_last_tag() -> List[str]:
    """Retrieve commits since the last tagged version."""
    # Get the last tag
    last_tag = run_git_command(["git", "describe", "--tags", "--abbrev=0"])

    # If no tag exists, get all commits
    if not last_tag:
        commits = run_git_command(["git", "log", "--pretty=format:%s"])
    else:
        commits = run_git_command(
            ["git", "log", f"{last_tag}..HEAD", "--pretty=format:%s"]
        )

    return commits.split("\n")


def categorize_commits(commits: List[str]) -> Dict[str, List[str]]:
    """Categorize commits into different sections."""
    categories = {
        "Features": [],
        "Bug Fixes": [],
        "Documentation": [],
        "Performance": [],
        "Refactoring": [],
        "Other": [],
    }

    commit_patterns = [
        (r"^feat(\(.*\))?:", "Features"),
        (r"^fix(\(.*\))?:", "Bug Fixes"),
        (r"^docs(\(.*\))?:", "Documentation"),
        (r"^perf(\(.*\))?:", "Performance"),
        (r"^refactor(\(.*\))?:", "Refactoring"),
    ]

    for commit in commits:
        categorized = False
        for pattern, category in commit_patterns:
            if re.match(pattern, commit.lower()):
                categories[category].append(commit.strip())
                categorized = True
                break

        if not categorized:
            categories["Other"].append(commit.strip())

    return {k: v for k, v in categories.items() if v}


def generate_changelog(version: str = None) -> str:
    """Generate a comprehensive changelog."""
    if not version:
        # Use current date if no version provided
        version = datetime.now().strftime("v0.1.0-%Y%m%d")

    commits = get_commits_since_last_tag()
    categorized_commits = categorize_commits(commits)

    changelog = (
        f"# Changelog\n\n## {version} - {datetime.now().strftime('%Y-%m-%d')}\n\n"
    )

    for category, commits in categorized_commits.items():
        if commits:
            changelog += f"### {category}\n"
            for commit in commits:
                changelog += f"- {commit}\n"
            changelog += "\n"

    return changelog


def write_changelog(changelog: str, filename: str = "CHANGELOG.md"):
    """Write changelog to file, preserving existing content."""
    try:
        with open(filename, "r") as f:
            existing_content = f.read()
    except FileNotFoundError:
        existing_content = ""

    with open(filename, "w") as f:
        f.write(changelog + "\n" + existing_content)


def main():
    changelog = generate_changelog()
    write_changelog(changelog)
    print("Changelog generated successfully!")


if __name__ == "__main__":
    main()
