"""
Debug Core Banking Account Controller Import
"""

import importlib
import sys
import traceback

def test_import(module_name):
    print(f"Attempting to import {module_name}")
    try:
        module = importlib.import_module(module_name)
        print(f"SUCCESS: Imported {module_name}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to import {module_name}")
        print(f"Exception: {type(e).__name__}: {str(e)}")
        print("Traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Test core_banking utilities
    test_import("core_banking.utils.core_banking_utils")
    
    # Test account entities
    test_import("core_banking.accounts.domain.entities.account")
    
    # Test account service
    test_import("core_banking.accounts.application.services.account_service")
    
    # Finally test the controller
    test_import("core_banking.accounts.presentation.controllers.account_controller")
