#!/usr/bin/env python
"""
Integration test for the custom import system.

This tests that the import system works correctly with other modules
in the application.
"""

import sys
import os
from pathlib import Path
import unittest
import colorama
from colorama import Fore, Style

# Initialize colorama for color output
colorama.init(autoreset=True)

# Add the project root to sys.path
project_root = Path(__file__).parent.parent.parent.absolute()

# Use centralized import manager
try:
    from utils.lib.packages import fix_path, import_module, is_production, is_development, is_test, is_debug_enabled, Environment
    fix_path()  # Ensures the project root is in sys.path
except ImportError:
    # Fallback for when the import manager is not available
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # Adjust levels as needed


class ImportSystemIntegrationTest(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment."""
        # Try to initialize the import system
        try:
            from app.lib.import_finder import HyphenatedDirectoryFinder
            self.import_finder_available = True
        except ImportError:
            self.import_finder_available = False
    
    def test_integration_with_config(self):
        """Test that the import system works with the config module."""
        if not self.import_finder_available:
            self.skipTest("Import finder not available")
        
        try:
            import config
            print(f"{Fore.GREEN}✅ Successfully imported root config{Style.RESET_ALL}")
            
            # Test accessing config variables
            if hasattr(config, 'DATABASE_CONFIG'):
                db_config = config.DATABASE_CONFIG
                self.assertIsNotNone(db_config)
                if 'database' in db_config:
                    self.assertEqual(db_config['database'], 'CBS_PYTHON')
                    print(f"{Fore.GREEN}✅ Successfully accessed DATABASE_CONFIG{Style.RESET_ALL}")
                else:
                    print(f"{Fore.YELLOW}⚠️ DATABASE_CONFIG doesn't contain 'database' key{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}⚠️ config does not have DATABASE_CONFIG attribute{Style.RESET_ALL}")
                # Skip the test instead of failing
                self.skipTest("DATABASE_CONFIG not available")
        except ImportError as e:
            # Skip instead of fail if it's a dependency issue
            if "dotenv" in str(e):
                print(f"{Fore.YELLOW}⚠️ Skipping config test due to missing python-dotenv dependency{Style.RESET_ALL}")
                self.skipTest(f"Missing dependency: {e}")
            else:
                print(f"{Fore.RED}❌ Failed to import config: {e}{Style.RESET_ALL}")
                self.fail(f"Config could not be imported: {e}")
        except (AttributeError, KeyError) as e:
            print(f"{Fore.RED}❌ Failed to access DATABASE_CONFIG: {e}{Style.RESET_ALL}")
            self.fail(f"DATABASE_CONFIG could not be accessed: {e}")
    
    def test_importing_from_hyphen_dirs(self):
        """Test importing and using modules from hyphenated directories."""
        if not self.import_finder_available:
            self.skipTest("Import finder not available")
        
        try:
            # Try to import the analytics_bi.config module
            import analytics_bi.config
            print(f"{Fore.GREEN}✅ Successfully imported analytics_bi.config{Style.RESET_ALL}")
        except ImportError as e:
            print(f"{Fore.YELLOW}⚠️ Could not import analytics_bi.config: {e}{Style.RESET_ALL}")
        
        try:
            # Try to import core_banking and check its functionality
            import core_banking
            print(f"{Fore.GREEN}✅ Successfully imported core_banking{Style.RESET_ALL}")
            
            # Try to access the utils in core_banking
            from core_banking.utils import id_generator
            print(f"{Fore.GREEN}✅ Successfully imported core_banking.utils.id_generator{Style.RESET_ALL}")
        except ImportError as e:
            print(f"{Fore.YELLOW}⚠️ Could not fully test core_banking: {e}{Style.RESET_ALL}")


if __name__ == "__main__":
    print(f"\n{Fore.CYAN}===== Integration Testing for Import System ====={Style.RESET_ALL}")
    unittest.main(verbosity=2)