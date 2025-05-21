#!/usr/bin/env python
"""
Temporary File Cleanup Script for CBS_PYTHON

This script cleans up temporary files across the codebase such as:
1. Dump directories
2. Multiple database import reports
3. Backup files
4. Temporary logs

It also consolidates reports into an archive while keeping the most recent ones accessible.

Usage:
    python cleanup_temp_files.py [--dry-run]

Options:
    --dry-run    Only show what would be cleaned up without making actual changes
"""

import os
import sys
import shutil
import argparse
import logging
from pathlib import Path
from datetime import datetime
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"temp_files_cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

# File patterns to clean up
CLEANUP_PATTERNS = [
    # Pattern, Description, Max files to keep (None = delete all)
    (r"database_imports_update_report_.*\.md", "Database import update reports", 1),
    (r"security_references_update_report_.*\.md", "Security references update reports", 1),
    (r".*\.bak", "Backup files", None),
    (r".*\.tmp", "Temporary files", None),
    (r".*_temp_.*", "Temporary files with '_temp_' in name", None),
    (r".*\.log", "Log files older than 7 days", None),  # Special handling for logs
]

# Directories to clean up
CLEANUP_DIRECTORIES = [
    # Directory path, Description, Action (clean/archive/delete)
    ("dump", "Dump directory", "archive"),
]

# Exclude directories from scanning
EXCLUDED_DIRS = [
    '__pycache__',
    'venv',
    'env',
    '.git',
    '.idea',
    '.vscode',
    'node_modules',
]

def find_files_by_pattern(base_dir: Path, pattern: str) -> list[Path]:
    """
    Find files matching a pattern in the codebase
    
    Args:
        base_dir: Base directory to search
        pattern: Regex pattern to match files
    
    Returns:
        List of matching file paths
    """
    matching_files = []
    pattern_regex = re.compile(pattern)
    
    for root, dirs, files in os.walk(base_dir):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        
        for file in files:
            if pattern_regex.match(file):
                file_path = Path(root) / file
                matching_files.append(file_path)
    
    return matching_files

def clean_dump_directory(base_dir: Path, dry_run: bool = False) -> int:
    """
    Clean the dump directory by archiving old dumps
    
    Args:
        base_dir: Base directory (project root)
        dry_run: If True, only show what would be done
    
    Returns:
        Number of directories processed
    """
    dump_dir = base_dir / "dump"
    if not dump_dir.exists():
        logger.info(f"Dump directory not found at {dump_dir}")
        return 0
    
    # Find all dump session directories (they typically have timestamp in name)
    dump_sessions = []
    for item in dump_dir.iterdir():
        if item.is_dir() and re.search(r'\d{8}_\d{6}', item.name):
            dump_sessions.append(item)
    
    # Sort by name (which includes timestamp)
    dump_sessions.sort()
    
    # Keep only the 3 most recent sessions, archive the rest
    sessions_to_archive = dump_sessions[:-3] if len(dump_sessions) > 3 else []
    
    if not sessions_to_archive:
        logger.info("No dump sessions to archive")
        return 0
    
    # Create archive directory
    archive_dir = dump_dir / "archived_dumps"
    if not dry_run:
        archive_dir.mkdir(exist_ok=True)
    
    # Move old sessions to archive
    for session_dir in sessions_to_archive:
        archive_path = archive_dir / session_dir.name
        logger.info(f"Archiving dump session: {session_dir.name}")
        
        if not dry_run:
            try:
                if archive_path.exists():
                    shutil.rmtree(archive_path)
                shutil.move(session_dir, archive_path)
            except Exception as e:
                logger.error(f"Error archiving {session_dir}: {str(e)}")
    
    # Update dump summary
    if not dry_run:
        try:
            with open(dump_dir / "dump_summary.txt", "w") as f:
                f.write(f"Dump Directory Summary\n")
                f.write(f"====================\n")
                f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                
                active_sessions = [d for d in dump_dir.iterdir() if d.is_dir() and d.name != "archived_dumps"]
                f.write(f"Number of active dump sessions: {len(active_sessions)}\n\n")
                
                for session in active_sessions:
                    num_files = sum(1 for _ in session.glob('**/*') if _.is_file())
                    num_dirs = sum(1 for _ in session.glob('**/*') if _.is_dir())
                    f.write(f"{session.name}: {num_files} files, {num_dirs} directories\n")
                
                f.write(f"\nTotal: {sum(1 for _ in dump_dir.glob('**/*') if _.is_file())} files, ")
                f.write(f"{sum(1 for _ in dump_dir.glob('**/*') if _.is_dir())} directories\n\n")
                
                if archive_dir.exists():
                    num_archived = len(list(archive_dir.iterdir()))
                    f.write(f"Archived dump sessions: {num_archived}\n\n")
                
                f.write(f"You can review these files and delete them manually if they are no longer needed.\n")
        except Exception as e:
            logger.error(f"Error updating dump summary: {str(e)}")
    
    return len(sessions_to_archive)

def clean_report_files(base_dir: Path, pattern: str, max_to_keep: int = 1, dry_run: bool = False) -> int:
    """
    Clean report files that match a pattern, keeping only the most recent ones
    
    Args:
        base_dir: Base directory (project root)
        pattern: Regex pattern to match files
        max_to_keep: Maximum number of files to keep
        dry_run: If True, only show what would be done
    
    Returns:
        Number of files deleted
    """
    matching_files = find_files_by_pattern(base_dir, pattern)
    
    # Sort by modification time (newest first)
    matching_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    # Keep only the specified number of most recent files
    files_to_delete = matching_files[max_to_keep:] if max_to_keep else matching_files
    
    for file_path in files_to_delete:
        logger.info(f"Deleting old report: {file_path.relative_to(base_dir)}")
        
        if not dry_run:
            try:
                os.remove(file_path)
            except Exception as e:
                logger.error(f"Error deleting {file_path}: {str(e)}")
    
    return len(files_to_delete)

def clean_temporary_files(base_dir: Path, dry_run: bool = False) -> dict:
    """
    Clean up temporary files across the codebase
    
    Args:
        base_dir: Base directory (project root)
        dry_run: If True, only show what would be done
    
    Returns:
        Summary of cleanup results
    """
    logger.info(f"Starting temporary file cleanup in {base_dir}")
    logger.info(f"Dry run: {dry_run}")
    
    results = {
        "total_files_deleted": 0,
        "dump_sessions_archived": 0,
        "patterns_cleaned": {}
    }
    
    # Clean dump directory
    results["dump_sessions_archived"] = clean_dump_directory(base_dir, dry_run)
    
    # Clean up files matching patterns
    for pattern, description, max_to_keep in CLEANUP_PATTERNS:
        # Special handling for log files (keep recent ones)
        if pattern == ".*\\.log":
            # TODO: Implement log file age-based cleanup
            continue
        
        num_deleted = clean_report_files(base_dir, pattern, max_to_keep, dry_run)
        results["patterns_cleaned"][description] = num_deleted
        results["total_files_deleted"] += num_deleted
    
    return results

def generate_report(results: dict, dry_run: bool = False) -> str:
    """
    Generate a report of the cleanup process
    
    Args:
        results: Results of the cleanup
        dry_run: Whether this was a dry run
    
    Returns:
        Report as string
    """
    report = f"""
# Temporary Files Cleanup Report

## Summary

- **Mode**: {"Dry Run (no changes applied)" if dry_run else "Live Run (changes applied)"}
- **Total Files Processed**: {results["total_files_deleted"]}
- **Dump Sessions Archived**: {results["dump_sessions_archived"]}
- **Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Details

| Category | Files Processed |
|----------|----------------|
"""
    
    for category, count in results["patterns_cleaned"].items():
        if count > 0:
            report += f"| {category} | {count} |\n"
    
    report += """
## Recommendations

1. Review the archived dump sessions to ensure no important information was archived
2. Run the test suite to verify system functionality after cleanup
3. Consider setting up a scheduled task for regular temporary file cleanup

"""
    return report

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Clean up temporary files across the codebase")
    parser.add_argument('--dry-run', action='store_true', help="Only show what would be cleaned up without making actual changes")
    args = parser.parse_args()
    
    # Get base directory (project root)
    base_dir = Path(__file__).parent.parent
    
    # Clean temporary files
    results = clean_temporary_files(base_dir, args.dry_run)
    
    # Generate report
    report = generate_report(results, args.dry_run)
    report_path = Path(f"temp_files_cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"Report generated: {report_path}")
    
    # Print summary
    logger.info(f"Summary: {results['total_files_deleted']} files processed, {results['dump_sessions_archived']} dump sessions archived")
    
    if args.dry_run:
        logger.info("This was a dry run. Run without --dry-run to apply changes.")

if __name__ == "__main__":
    main()
