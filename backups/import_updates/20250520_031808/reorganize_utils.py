"""
Script to reorganize the utils directory according to the recommended structure.

Usage:
    python scripts/reorganize_utils.py
"""

import os
import shutil
import logging
from datetime import datetime
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
UTILS_DIR = os.path.join(PROJECT_ROOT, 'utils')
DUMP_DIR = os.path.join(PROJECT_ROOT, 'dump')

# Ensure dump directory exists
if not os.path.exists(DUMP_DIR):
    os.makedirs(DUMP_DIR)
    logger.info(f"Created dump directory at {DUMP_DIR}")

# Create a subfolder with timestamp for this run
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
current_dump_dir = os.path.join(DUMP_DIR, f"utils_reorganize_{timestamp}")
os.makedirs(current_dump_dir)
logger.info(f"Created timestamped dump directory at {current_dump_dir}")

# Define the recommended structure
recommended_structure = {
    "root": [
        "error_handling.py",
        "validators.py", 
        "logging.py",
        "__init__.py"
    ],
    "lib": [
        "service_registry.py",
        "module_interface.py",
        "packages.py",
        "error_handling.py", 
        "logging_utils.py"
    ],
    "config": [
        "database_config.py",
        "app_config.py",
        "environment.py"
    ],
    "examples": [
        "module_usage_examples.py",
        "validation_examples.py",
        "error_handling_examples.py"
    ]
}

def backup_file(file_path):
    """Create a backup of a file in the dump directory."""
    rel_path = os.path.relpath(file_path, PROJECT_ROOT)
    backup_path = os.path.join(current_dump_dir, rel_path)
    
    # Create the directory structure
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    
    # Copy the file
    try:
        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup of {rel_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to backup {rel_path}: {str(e)}")
        return False

def create_utils_structure():
    """Create the recommended utils directory structure."""
    logger.info("Creating recommended utils directory structure")
    
    # First, create a backup of the entire utils directory
    utils_backup_dir = os.path.join(current_dump_dir, "utils_backup")
    shutil.copytree(UTILS_DIR, utils_backup_dir)
    logger.info(f"Created backup of entire utils directory at {utils_backup_dir}")
    
    # Ensure all required directories exist
    for subdir in ["lib", "config", "examples"]:
        subdir_path = os.path.join(UTILS_DIR, subdir)
        if not os.path.exists(subdir_path):
            os.makedirs(subdir_path)
            logger.info(f"Created directory {subdir_path}")

def generate_reorganization_plan():
    """Generate a plan for how to reorganize the utils directory."""
    logger.info("Generating reorganization plan")
    
    plan_file = os.path.join(current_dump_dir, "reorganization_plan.md")
    
    with open(plan_file, 'w') as f:
        f.write("# Utils Directory Reorganization Plan\n\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Recommended Structure\n\n")
        f.write("```\n")
        f.write("utils/\n")
        for file in recommended_structure["root"]:
            f.write(f"  ├── {file}\n")
        
        for subdir, files in recommended_structure.items():
            if subdir == "root":
                continue
                
            f.write(f"  ├── {subdir}/\n")
            for file in files:
                f.write(f"  │   ├── {file}\n")
            f.write(f"  │   └── ...\n")
        
        f.write("```\n\n")
        
        f.write("## Actions to Take\n\n")
        
        f.write("### 1. File Relocation\n\n")
        f.write("| Current Location | Target Location | Reason |\n")
        f.write("|------------------|----------------|--------|\n")
        
        # Root utils files to keep in place
        root_files = [f for f in os.listdir(UTILS_DIR) if os.path.isfile(os.path.join(UTILS_DIR, f)) and f.endswith('.py')]
        for file in root_files:
            if file in recommended_structure["root"]:
                f.write(f"| utils/{file} | utils/{file} | Keep in place (core utility) |\n")
            else:
                # Suggest destination based on file content/name
                if "config" in file.lower():
                    f.write(f"| utils/{file} | utils/config/{file} | Move to config directory |\n")
                elif any(keyword in file.lower() for keyword in ["example", "demo", "sample"]):
                    f.write(f"| utils/{file} | utils/examples/{file} | Move to examples directory |\n")
                else:
                    f.write(f"| utils/{file} | utils/lib/{file} | Move to lib directory |\n")
        
        f.write("\n### 2. Common Directory Consolidation\n\n")
        
        common_dir = os.path.join(UTILS_DIR, "common")
        if os.path.exists(common_dir):
            common_files = [f for f in os.listdir(common_dir) if os.path.isfile(os.path.join(common_dir, f)) and f.endswith('.py')]
            for file in common_files:
                if file == "__init__.py":
                    continue
                    
                if file in recommended_structure["root"]:
                    f.write(f"| utils/common/{file} | utils/{file} | Merge with root utility |\n")
                else:
                    # Suggest destination based on file content/name
                    if "config" in file.lower():
                        f.write(f"| utils/common/{file} | utils/config/{file} | Move to config directory |\n")
                    elif any(keyword in file.lower() for keyword in ["example", "demo", "sample"]):
                        f.write(f"| utils/common/{file} | utils/examples/{file} | Move to examples directory |\n")
                    else:
                        f.write(f"| utils/common/{file} | utils/lib/{file} | Move to lib directory |\n")
        
        f.write("\n### 3. Import Updates\n\n")
        f.write("After relocating files, imports across the project will need to be updated. Here's a guide:\n\n")
        f.write("1. Root utilities should be imported directly from `utils`:\n")
        f.write("   ```python\n")
        f.write("   from utils import validators, error_handling\n")
        f.write("   ```\n\n")
        
        f.write("2. Library utilities should be imported from `utils.lib`:\n")
        f.write("   ```python\n")
        f.write("   from utils.lib import service_registry, module_interface\n")
        f.write("   ```\n\n")
        
        f.write("3. Configuration utilities should be imported from `utils.config`:\n")
        f.write("   ```python\n")
        f.write("   from utils.config import database_config, app_config\n")
        f.write("   ```\n\n")
        
        f.write("4. Example code should be imported from `utils.examples`:\n")
        f.write("   ```python\n")
        f.write("   from utils.examples import module_usage_examples\n")
        f.write("   ```\n")
        
        f.write("\n## Implementation Steps\n\n")
        f.write("1. Backup the entire utils directory (already done in dump)\n")
        f.write("2. Ensure all required directories exist\n")
        f.write("3. Move files to their designated locations\n")
        f.write("4. Update imports throughout the codebase\n")
        f.write("5. Remove any redundant or obsolete files\n")
        f.write("6. Test the system to ensure everything works correctly\n")
    
    logger.info(f"Created reorganization plan at {plan_file}")
    return plan_file

def main():
    """Main function to execute the utils directory reorganization."""
    logger.info("Starting utils directory reorganization planning")
    
    # Create structure if needed
    create_utils_structure()
    
    # Generate reorganization plan
    plan_file = generate_reorganization_plan()
    
    logger.info("Utils directory reorganization planning completed")
    logger.info(f"Reorganization plan generated at {plan_file}")
    logger.info("Please review the plan before making any changes")

if __name__ == "__main__":
    main()
