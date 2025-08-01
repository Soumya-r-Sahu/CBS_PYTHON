# CBS_PYTHON Requirements Management

This document explains how dependencies are managed in the CBS_PYTHON project.

## Requirements Files

The project uses a single requirements file located at the project root:

- `requirements.txt` - Main requirements file with all project dependencies

### Removed Legacy Requirements Files

The following legacy requirements files have been removed to avoid duplication:

- `database/requirements.txt` (replaced with README.requirements.md)
- `app/Portals/Admin/requirements.txt` (replaced with README.requirements.md)
- `consolidated_requirements.txt` (merged into main requirements.txt)

## How to Install Dependencies

To install all dependencies for the project, run:

```bash
pip install -r requirements.txt
```

## Dependency Management Guidelines

1. **All Changes Go to requirements.txt**: All dependency changes should be made to the main requirements.txt file at the project root.

2. **Version Specifiers**: Use `>=` version specifiers to allow compatible upgrades.

3. **Categorization**: Dependencies are categorized by their function (Core, Database, Web, etc.)

4. **Comments**: Use comments to explain the purpose of optional or specialized dependencies.

## Adding New Dependencies

When adding new dependencies:

1. Add them to the appropriate section in `requirements.txt`
2. Include a comment if the dependency is for a specific use case
3. Run `pip install -r requirements.txt` to update your environment

## Last Updated

May 18, 2025
