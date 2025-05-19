# 🛠️ Development Tools

CBS_PYTHON provides several tools to help maintain code quality and consistency. These tools are located in the `scripts/` directory:

## Code Structure Tools

- **sanitize_codebase.py** - Main script to check and fix common issues
  ```bash
  python scripts/sanitize_codebase.py
  ```

- **import_checker.py** - Check for import issues throughout the codebase
  ```bash
  python scripts/import_checker.py [directory]
  ```

- **standardize_imports.py** - Standardize imports in a single file
  ```bash
  python scripts/standardize_imports.py path/to/file.py
  ```

## Requirements Management

- **check_requirements_files.py** - Verify there are no duplicate requirement files
  ```bash
  python scripts/check_requirements_files.py
  ```

- **manage_requirements.py** - Add new dependencies correctly
  ```bash
  # List available sections
  python scripts/manage_requirements.py sections

  # List all current requirements
  python scripts/manage_requirements.py list

  # Add a new package
  python scripts/manage_requirements.py add "package_name" ">=1.0.0" "Core Dependencies" "Optional comment"
  ```

## Using the Tools

These tools can help maintain code quality and enforce best practices:

1. **For New Code**: Run `standardize_imports.py` on new files to ensure they use the centralized import system.

2. **For Dependency Management**: Always use `manage_requirements.py` to add new dependencies to maintain consistent formatting.

3. **For Code Reviews**: Run `sanitize_codebase.py` before submitting pull requests to catch common issues.

4. **For Continuous Integration**: Add `check_requirements_files.py` to your CI pipeline to prevent duplicate requirement files.

## Documentation

See the following documentation files for more information on best practices:

- [Import System Guide](documentation/technical/standards/import_system_guide.md)
- [Requirements Management](documentation/technical/standards/requirements_management.md)
