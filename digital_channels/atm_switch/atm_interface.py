# Import necessary components
import os
import sys
from pathlib import Path
from app.atm.card_validation import CardValidation
from app.atm.cash_withdrawal import CashWithdrawal
from app.atm.balance_inquiry import BalanceInquiry
from app.atm.pin_change import PinChange
from colorama import init, Fore, Style

# Add parent directory to path if needed

# Use centralized import manager
try:
    from utils.lib.packages import fix_path, import_module, is_production, is_development, is_test, is_debug_enabled, Environment
    fix_path()  # Ensures the project root is in sys.path
except ImportError:
    # Fallback for when the import manager is not available
    import sys
    from pathlib import Path
    # Removed: # Removed: # Removed: sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # Adjust levels as needed


# Try to import environment module
try:
    from utils.config import (
        get_environment_name, is_production, is_development, 
        is_test, is_debug_enabled
    )
except ImportError:
    # Fallback environment detection
    env_str = os.environ.get("CBS_ENVIRONMENT", "development").lower()
    def is_production(): return env_str == "production"
    def is_development(): return env_str == "development"
    def is_test(): return env_str == "test"
    def is_debug_enabled(): return os.environ.get("CBS_DEBUG", "true").lower() in ("true", "1", "yes")
    def get_environment_name(): return env_str

# Initialize colorama
init(autoreset=True)

class AtmInterface:
    def __init__(self):
        self.card_validator = CardValidation()
        self.cash_withdrawal = CashWithdrawal()
        self.balance_inquiry = BalanceInquiry()
        self.pin_change = PinChange()
        
        # Environment settings
        self.env_name = get_environment_name().upper()
        self.env_color = Fore.RED if is_production() else Fore.YELLOW if is_test() else Fore.GREEN
        self.is_test_mode = is_test()

    def start(self):
        # Display ATM header with environment indicator
        print(f"{Fore.CYAN}🌟 Welcome to the ATM Interface {Style.RESET_ALL}{self.env_color}[{self.env_name}]{Style.RESET_ALL}")
        
        # Show additional debug info in non-production environments
        if not is_production() and is_debug_enabled():
            print(f"{Fore.YELLOW}🔍 Debug Mode: ENABLED{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}🔧 Environment: {self.env_name}{Style.RESET_ALL}")
        
        # Different behavior based on environment
        if is_test():
            print(f"{Fore.YELLOW}⚠️ TEST MODE: No real transactions will be processed{Style.RESET_ALL}")
        
        # TODO: Replace this CLI with a PyQt5-based GUI for ATM operations
        while True:
            print(f"\n{Fore.CYAN}💳 Please select an option:{Style.RESET_ALL}")
            print(f"{Fore.GREEN}1️⃣  Cash Withdrawal{Style.RESET_ALL}")
            print(f"{Fore.GREEN}2️⃣  Balance Inquiry{Style.RESET_ALL}")
            print(f"{Fore.GREEN}3️⃣  Change PIN{Style.RESET_ALL}")
            print(f"{Fore.GREEN}4️⃣  Exit{Style.RESET_ALL}")
              # Show environment options in non-production modes
            if not is_production():
                print(f"{Fore.YELLOW}5️⃣  Show Environment Info{Style.RESET_ALL}")
                
            choice = input("Enter your choice: ")

            if choice == '1':
                print(f"{Fore.YELLOW}💵 Processing Cash Withdrawal...{Style.RESET_ALL}")
                # Add environment-specific behavior for test mode
                if self.is_test_mode:
                    print(f"{Fore.YELLOW}⚠️ TEST MODE: This is a simulated withdrawal only{Style.RESET_ALL}")
                self.cash_withdrawal.process_withdrawal()
            elif choice == '2':
                print(f"{Fore.YELLOW}📊 Checking Balance...{Style.RESET_ALL}")
                # Add environment-specific behavior for test mode
                if self.is_test_mode:
                    print(f"{Fore.YELLOW}⚠️ TEST MODE: Balance data is simulated{Style.RESET_ALL}")
                self.balance_inquiry.check_balance()
            elif choice == '3':
                print(f"{Fore.YELLOW}🔑 Changing PIN...{Style.RESET_ALL}")
                # Add environment-specific behavior for test mode
                if self.is_test_mode:
                    print(f"{Fore.YELLOW}⚠️ TEST MODE: PIN changes are not permanently stored{Style.RESET_ALL}")
                self.pin_change.change_pin()
            elif choice == '4':
                print(f"{Fore.CYAN}🙏 Thank you for using the ATM. Goodbye! 👋{Style.RESET_ALL}")
                break
            elif choice == '5' and not is_production():
                # Show environment details - only available in non-production
                self.show_environment_info()
            else:
                print(f"{Fore.RED}❌ Invalid choice. Please try again.{Style.RESET_ALL}")

    def show_environment_info(self):
        """Display detailed environment information (only available in non-production)"""
        # Environment banner
        print(f"\n{self.env_color}====== ENVIRONMENT INFORMATION ======{Style.RESET_ALL}")
        print(f"Environment: {self.env_color}{self.env_name}{Style.RESET_ALL}")
        print(f"Debug Mode: {'ENABLED' if is_debug_enabled() else 'DISABLED'}")
        
        # Additional information
        if is_development():
            print("\nDevelopment Environment Details:")
            print(" - Transactions are saved to the development database")
            print(" - Debug mode is enabled for detailed logging")
            print(" - Encryption is using development keys")
        elif is_test():
            print("\nTest Environment Details:")
            print(" - Transactions are simulated and not processed for real")
            print(" - Test accounts are used with mock data")
            print(" - External services are mocked")
        
        # Database connection info (simplified for security)
        try:
            from utils.config import DATABASE_CONFIG
            db_info = DATABASE_CONFIG.copy()
            # Hide sensitive information
            if 'password' in db_info:
                db_info['password'] = '********'
            
            print(f"\nDatabase Configuration:")
            for key, value in db_info.items():
                print(f" - {key}: {value}")
        except ImportError:
            print("\nCould not load database configuration")
        
        # Show system paths (useful for debugging)
        print("\nSystem Information:")
        print(f" - Python executable: {sys.executable}")
        print(f" - Working directory: {os.getcwd()}")
        
        # Environment variables (only CBS-related ones)
        print("\nEnvironment Variables:")
        for key, value in os.environ.items():
            if key.startswith('CBS_'):
                if any(sensitive in key.lower() for sensitive in ['password', 'secret', 'key']):
                    print(f" - {key}: ********")
                else:
                    print(f" - {key}: {value}")
        
        input("\nPress Enter to continue...")