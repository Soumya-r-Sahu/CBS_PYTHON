# Code Maintenance Scripts

This directory contains utilities for maintaining and improving code quality.

## Scripts

- `fix_indentation.py` - Fixes indentation issues in Python code files
  - Automatically corrects inconsistent indentation
  - Standardizes tabs vs. spaces
  - Can be run on individual files or entire directories

## Usage

```bash
python fix_indentation.py --path="../path/to/file.py"
python fix_indentation.py --dir="../path/to/directory"
```

## Best Practices

- Always back up code before using automatic formatting tools
- Review changes after running the script
- Consider using this script as part of pre-commit hooks
