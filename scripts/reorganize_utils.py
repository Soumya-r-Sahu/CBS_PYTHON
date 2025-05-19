# Utils Directory Organizer for CBS_PYTHON
# This script organizes the utils directory into a more structured format
# with proper subdirectories

import os
import shutil
from pathlib import Path

# Define the root directory
root_dir = Path("d:/Vs code/CBS_PYTHON")
utils_dir = root_dir / "utils"

# Define subdirectories structure
subdirs = {
    "common": ["id_formatters.py", "validators.py", "encryption.py", "date_format.py"],
    "config": ["config.py", "config_manager.py", "database_type_manager.py"],
    "security": ["xss_protection.py", "sql_security.py", "gdpr_compliance.py"],
    "design": ["design_patterns.py"],
    "logs": ["logging.py"],
    "payments": ["payment_utils.py", "id_generation.py"],
    "cross_cutting": ["cross_cutting.py", "framework_compatibility.py"]
}

# Create subdirectories if they don't exist
for subdir in subdirs:
    os.makedirs(utils_dir / subdir, exist_ok=True)
    print(f"Ensuring directory exists: {utils_dir / subdir}")

# Move files to appropriate subdirectories
for subdir, files in subdirs.items():
    for file in files:
        src = utils_dir / file
        dst = utils_dir / subdir / file
        
        if src.exists() and not dst.exists():
            print(f"Moving {src} to {dst}")
            # Uncomment to actually move files
            # shutil.copy2(src, dst)
        elif not src.exists():
            print(f"Source file doesn't exist: {src}")
        elif dst.exists():
            print(f"Destination file already exists: {dst}")

print("\nFile reorganization plan completed!")

# Database Python Directory Organizer
db_python_dir = root_dir / "database" / "python"

# Define subdirectories for database/python
db_subdirs = {
    "models": ["models.py", "international_models.py"],
    "connection": ["connection.py", "db_manager.py"],
    "utilities": ["compare_databases.py"]
}

# Create subdirectories if they don't exist
for subdir in db_subdirs:
    os.makedirs(db_python_dir / subdir, exist_ok=True)
    print(f"Ensuring directory exists: {db_python_dir / subdir}")

# Move files to appropriate subdirectories
for subdir, files in db_subdirs.items():
    for file in files:
        src = db_python_dir / file
        dst = db_python_dir / subdir / file
        
        if src.exists() and not dst.exists():
            print(f"Moving {src} to {dst}")
            # Uncomment to actually move files
            # shutil.copy2(src, dst)
        elif not src.exists():
            print(f"Source file doesn't exist: {src}")
        elif dst.exists():
            print(f"Destination file already exists: {dst}")

print("\nDatabase python directory reorganization plan completed!")
