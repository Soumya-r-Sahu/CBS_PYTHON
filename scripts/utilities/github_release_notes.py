"""
GitHub Release Notes Generator for CBS_PYTHON v1.1.1

This script generates the release notes for the v1.1.1 release on GitHub.
"""
import datetime
import sys
from pathlib import Path

def generate_release_notes():
    """Generate release notes for GitHub based on CHANGELOG.md."""
    
    project_root = Path(__file__).resolve().parent.parent.parent
    changelog_path = project_root / "CHANGELOG.md"
    
    # Check if CHANGELOG.md exists
    if not changelog_path.exists():
        print(f"Error: CHANGELOG.md not found at {changelog_path}")
        sys.exit(1)
    
    # Read changelog content
    with open(changelog_path, 'r', encoding='utf-8') as f:
        changelog_content = f.read()
    
    # Find the v1.1.1 section
    start_marker = "## [1.1.1]"
    end_marker = "## [1.1.0]"
    
    start_index = changelog_content.find(start_marker)
    end_index = changelog_content.find(end_marker)
    
    if start_index == -1:
        print("Error: Could not find v1.1.1 section in CHANGELOG.md")
        sys.exit(1)
    
    # Extract the v1.1.1 section
    v111_notes = changelog_content[start_index:end_index].strip()
    
    # Generate GitHub release notes
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    release_title = f"Version 1.1.1 Release ({today})"
    
    print("\n" + "=" * 80)
    print(f"GitHub Release: {release_title}")
    print("=" * 80)
    print("\nCreate a new release on GitHub with the following information:")
    print("\nTag: v1.1.1")
    print(f"Title: {release_title}")
    print("\nDescription:")
    print("=" * 80)
    print(v111_notes)
    print("=" * 80)
    
    # Generate additional instructions
    summary_path = project_root / "v1.1.1_final_release_summary.md"
    if summary_path.exists():
        print("\nAdditional Information:")
        print("For a detailed summary of all changes and improvements, see:")
        print("- v1.1.1_final_release_summary.md")

if __name__ == "__main__":
    generate_release_notes()
