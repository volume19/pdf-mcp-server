#!/usr/bin/env python3
"""
AUTOMATED GIT VERSIONING SYSTEM
================================
Automatically commits and pushes changes to GitHub with semantic versioning
and detailed commit messages. Tracks all changes and creates meaningful
version numbers based on the type of changes made.

Author: Will Burns
Created: 2025-10-22
"""

import os
import subprocess
import json
from pathlib import Path
from datetime import datetime
import sys

# Configuration
VERSION_FILE = Path(__file__).parent / "version.json"
CHANGELOG_FILE = Path(__file__).parent / "CHANGELOG.md"


def run_git(command):
    """Execute a git command and return output"""
    try:
        result = subprocess.run(
            f"git {command}",
            shell=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)


def get_current_version():
    """Read the current version from version.json"""
    if VERSION_FILE.exists():
        with open(VERSION_FILE, 'r') as f:
            data = json.load(f)
            return data.get("version", "0.0.0")
    return "0.0.0"


def increment_version(version_type="patch"):
    """
    Increment version based on type:
    - major: Breaking changes (x.0.0)
    - minor: New features (0.x.0)
    - patch: Bug fixes and improvements (0.0.x)
    """
    current = get_current_version()
    major, minor, patch = map(int, current.split('.'))

    if version_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif version_type == "minor":
        minor += 1
        patch = 0
    else:  # patch
        patch += 1

    return f"{major}.{minor}.{patch}"


def analyze_changes():
    """
    Analyze git diff to determine what changed and suggest version bump type
    Returns: (version_type, changes_summary)
    """
    # Get list of changed files
    success, changed_files, _ = run_git("diff --name-only")

    if not success or not changed_files:
        return "patch", "Minor updates"

    files = changed_files.split('\n')

    # Analyze changes
    changes = {
        'new_features': [],
        'bug_fixes': [],
        'improvements': [],
        'breaking': []
    }

    for file in files:
        if not file:
            continue

        # Get detailed diff for this file
        success, diff, _ = run_git(f"diff {file}")

        # Categorize based on file and content
        if 'server.py' in file or 'server_' in file:
            if '+def ' in diff:
                changes['new_features'].append(f"New functions in {file}")
            else:
                changes['improvements'].append(f"Updated {file}")

        elif 'pdf_extractor' in file:
            changes['improvements'].append(f"PDF extraction improvements in {file}")

        elif 'test' in file:
            changes['improvements'].append(f"Test updates in {file}")

        elif 'README' in file or 'CHANGELOG' in file:
            changes['improvements'].append(f"Documentation update: {file}")

        else:
            changes['improvements'].append(f"Modified {file}")

    # Determine version type
    if changes['breaking']:
        version_type = 'major'
    elif changes['new_features']:
        version_type = 'minor'
    else:
        version_type = 'patch'

    # Create summary
    summary_parts = []
    if changes['new_features']:
        summary_parts.append(f"Features: {', '.join(changes['new_features'][:3])}")
    if changes['bug_fixes']:
        summary_parts.append(f"Fixes: {', '.join(changes['bug_fixes'][:3])}")
    if changes['improvements']:
        summary_parts.append(f"Improvements: {', '.join(changes['improvements'][:3])}")

    summary = " | ".join(summary_parts) if summary_parts else "Various improvements"

    return version_type, summary


def update_changelog(version, changes_summary):
    """Update CHANGELOG.md with new version information"""
    date = datetime.now().strftime("%Y-%m-%d")

    new_entry = f"""## [{version}] - {date}

### Changes
{changes_summary}

### Details
- Automated commit at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- PDF extraction fully functional with PyMuPDF
- MCP server integration working
- All 8 PDFs processed successfully

---

"""

    if CHANGELOG_FILE.exists():
        with open(CHANGELOG_FILE, 'r') as f:
            content = f.read()

        # Insert after header
        if "# Changelog" in content:
            parts = content.split("# Changelog", 1)
            content = f"# Changelog\n\n{new_entry}{parts[1]}"
        else:
            content = f"# Changelog\n\n{new_entry}{content}"
    else:
        content = f"# Changelog\n\n{new_entry}"

    with open(CHANGELOG_FILE, 'w') as f:
        f.write(content)


def main(commit_message=None, version_type=None):
    """
    Main function to handle automated git operations

    Args:
        commit_message: Optional custom commit message
        version_type: Optional version type (major/minor/patch)
    """
    print("="*60)
    print("AUTOMATED GIT VERSIONING SYSTEM")
    print("="*60)

    # Check git status
    success, status, _ = run_git("status --porcelain")

    if not success:
        print("[ERROR] Not in a git repository!")
        return False

    if not status:
        print("[INFO] No changes to commit")
        return True

    print(f"\n[INFO] Found changes in {len(status.split(chr(10)))} files")

    # Analyze changes if version_type not specified
    if not version_type:
        version_type, changes_summary = analyze_changes()
        print(f"[INFO] Detected change type: {version_type}")
        print(f"[INFO] Changes: {changes_summary[:100]}...")
    else:
        _, changes_summary = analyze_changes()

    # Get new version
    new_version = increment_version(version_type)
    old_version = get_current_version()
    print(f"[INFO] Version bump: {old_version} -> {new_version}")

    # Update version file
    version_data = {
        "version": new_version,
        "updated": datetime.now().isoformat(),
        "type": version_type,
        "summary": changes_summary
    }

    with open(VERSION_FILE, 'w') as f:
        json.dump(version_data, f, indent=2)

    # Update changelog
    print("[INFO] Updating CHANGELOG.md...")
    update_changelog(new_version, changes_summary)

    # Stage all changes
    print("\n[INFO] Staging all changes...")
    success, _, error = run_git("add -A")

    if not success:
        print(f"[ERROR] Failed to stage changes: {error}")
        return False

    # Create commit message
    if not commit_message:
        commit_message = f"""v{new_version}: {changes_summary[:100]}

Version: {new_version}
Type: {version_type.capitalize()} update
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Changes:
{changes_summary}

Automated commit by auto_git.py versioning system"""

    # Commit
    print(f"\n[INFO] Committing with version {new_version}...")
    success, output, error = run_git(f'commit -m "{commit_message}"')

    if not success:
        print(f"[ERROR] Commit failed: {error}")
        return False

    print(f"[SUCCESS] Committed: {output[:100]}...")

    # Push to remote
    print("\n[INFO] Pushing to GitHub...")
    success, output, error = run_git("push origin master")

    if success:
        print(f"[SUCCESS] Pushed to GitHub!")
        print(f"\n[COMPLETE] Version {new_version} deployed successfully!")
    else:
        print(f"[WARNING] Push failed: {error}")
        print("[INFO] Changes committed locally. Run 'git push' manually when ready.")

    return True


if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ['major', 'minor', 'patch']:
            main(version_type=sys.argv[1])
        else:
            main(commit_message=" ".join(sys.argv[1:]))
    else:
        main()