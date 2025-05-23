"""
Automated Stability Issue Fixer for CBS_PYTHON project
"""

import os
import sys
import re
import importlib
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("StabilityFixer")

def fix_security_imports():
    """Fix imports in security module's user entity"""
    try:
        # Fix user entity imports
        user_entity_path = os.path.join('security', 'authentication', 'domain', 'entities', 'user.py')
        
        if not os.path.exists(user_entity_path):
            logger.error(f"Could not find {user_entity_path}")
            return False
            
        with open(user_entity_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Fix relative imports for value objects
        fixed_content = content.replace(
            "from .value_objects.user_id import UserId\nfrom .value_objects.credential import Credential\nfrom .value_objects.user_status import UserStatus",
            "from ..value_objects.user_id import UserId\nfrom ..value_objects.credential import Credential\nfrom ..value_objects.user_status import UserStatus"
        )
        
        if fixed_content != content:
            with open(user_entity_path, 'w', encoding='utf-8') as file:
                file.write(fixed_content)
            logger.info(f"Fixed imports in {user_entity_path}")
        else:
            logger.info(f"No changes needed in {user_entity_path}")
            
        return True
    except Exception as e:
        logger.error(f"Error fixing security imports: {str(e)}")
        return False

def fix_credential_datetime_issues():
    """Fix datetime syntax errors in credential value object"""
    try:
        credential_path = os.path.join('security', 'authentication', 'domain', 'value_objects', 'credential.py')
        
        if not os.path.exists(credential_path):
            logger.error(f"Could not find {credential_path}")
            return False
            
        with open(credential_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Add datetime import if needed
        if 'from datetime import datetime' not in content:
            content = re.sub(
                r'from typing import Optional',
                'from datetime import datetime\nfrom typing import Optional',
                content
            )
        
        # Fix the inline datetime issue in update_password
        content = re.sub(
            r"object\.__setattr__\(self, 'last_changed',\s+import datetime; datetime\.datetime\.now\(\)\.isoformat\(\)\)",
            "object.__setattr__(self, 'last_changed', datetime.now().isoformat())",
            content
        )
        
        # Fix datetime reference in create method
        content = re.sub(
            r"last_changed=datetime\.datetime\.now\(\)\.isoformat\(\)",
            "last_changed=datetime.now().isoformat()",
            content
        )
        
        with open(credential_path, 'w', encoding='utf-8') as file:
            file.write(content)
            
        logger.info(f"Fixed datetime issues in {credential_path}")
        return True
    except Exception as e:
        logger.error(f"Error fixing credential datetime issues: {str(e)}")
        return False

def check_controllers_imports():
    """Validate imports in controller files"""
    controllers_to_check = [
        os.path.join('core_banking', 'accounts', 'presentation', 'controllers', 'account_controller.py'),
        os.path.join('security', 'authentication', 'presentation', 'controllers', 'authentication_controller.py'),
        os.path.join('security', 'authentication', 'presentation', 'controllers', 'user_management_controller.py'),
    ]
    
    for controller_path in controllers_to_check:
        try:
            if not os.path.exists(controller_path):
                logger.warning(f"Could not find {controller_path}")
                continue
                
            # Try importing the module (this would catch import errors)
            module_path = controller_path.replace(os.sep, '.').replace('.py', '')
            try:
                importlib.import_module(module_path)
                logger.info(f"Successfully imported {module_path}")
            except ImportError as e:
                logger.error(f"Import error in {controller_path}: {str(e)}")
        except Exception as e:
            logger.error(f"Error checking controller {controller_path}: {str(e)}")

def verify_fixes():
    """Verify fixes by importing key modules"""
    modules_to_check = [
        'security.authentication.domain.entities.user',
        'security.authentication.domain.value_objects.credential',
        'security.authentication.domain.value_objects.user_id',
        'security.authentication.infrastructure.repositories.sqlite_user_repository'
    ]
    
    success_count = 0
    for module_path in modules_to_check:
        try:
            importlib.import_module(module_path)
            logger.info(f"Successfully imported {module_path}")
            success_count += 1
        except Exception as e:
            logger.error(f"Error importing {module_path}: {str(e)}")
    
    logger.info(f"Successfully imported {success_count}/{len(modules_to_check)} modules")
    return success_count == len(modules_to_check)

def main():
    """Main function to fix stability issues"""
    logger.info("Starting stability issue fixes")
    
    # Execute fixes
    fix_security_imports()
    fix_credential_datetime_issues()
    check_controllers_imports()
    
    # Verify fixes
    if verify_fixes():
        logger.info("All fixes applied and verified successfully")
    else:
        logger.warning("Some fixes could not be verified")
    
    logger.info("Stability fixes completed")

if __name__ == "__main__":
    main()
