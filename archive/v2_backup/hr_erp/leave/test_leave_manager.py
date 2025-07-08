"""
Test script to verify leave_manager.py functionality

This script imports the LeaveManager class and tests its basic functionality.
"""

# Ensure we can access the project root
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Now use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path

# Import the LeaveManager class
from hr_erp.leave.leave_manager import LeaveManager, get_leave_manager

# Create an instance and test functionality
def test_leave_manager():
    print("Testing LeaveManager class...")
    
    # Get the singleton instance
    lm = get_leave_manager()
    print(f"Singleton instance created: {lm}")
    
    # Create a new instance for testing
    leave_manager = LeaveManager()
    print(f"New instance created: {leave_manager}")
    
    # Test initializing leave balances for current year
    print("\nTesting initialize_leave_balances...")
    # Uncomment to actually run the initialization (requires database connection)
    # result = leave_manager.initialize_leave_balances()
    # print(f"Initialize leave balances result: {result}")
    
    # Print available leave types
    print("\nAvailable leave types:")
    for code, info in leave_manager.leave_types.items():
        quota = info.get('annual_quota', 0)
        gender = info.get('gender_specific', 'All')
        print(f"  - {code}: Quota={quota}, Gender={gender}")
    
    print("\nLeave manager test completed successfully!")

if __name__ == "__main__":
    test_leave_manager()
