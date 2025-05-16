# Example of how to use the centralized configuration with proper environment-aware settings

"""
Example Module with Production Safe Configuration

This module demonstrates how to use the centralized configuration system safely,
considering the different environments (development, test, production).
Follow this pattern for all new code.
"""

# Import environment detection first
import os
import sys
from pathlib import Path

# Add parent directory to path if needed
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    # Commented out direct sys.path modification
    # sys.path.insert(0, parent_dir)
    from utils.lib.packages import fix_path
fix_path()

# Import environment module
try:
    from app.config.environment import (
        is_production, is_development, is_test, is_debug_enabled,
        Environment, env_aware
    )
except ImportError:
    # Fallback environment detection (simplified)
    env_str = os.environ.get("CBS_ENVIRONMENT", "development").lower()
    def is_production(): return env_str == "production"
    def is_development(): return env_str == "development"
    def is_test(): return env_str == "test"
    def is_debug_enabled(): return os.environ.get("CBS_DEBUG", "false").lower() == "true" and not is_production()
    
    def env_aware(development=None, test=None, production=None):
        if is_production():
            return production
        elif is_test():
            return test
        else:
            return development

# Import config with environment context
from config import DATABASE_CONFIG, EMAIL_CONFIG, UPI_CONFIG
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Environment-aware debug setting - NEVER debug in production
DEBUG_MODE = is_debug_enabled()

def connect_to_database():
    """Example function that uses the database configuration"""
    host = DATABASE_CONFIG['host']
    port = DATABASE_CONFIG['port']
    user = DATABASE_CONFIG['user']
    password = DATABASE_CONFIG['password']  # Securely stored in config
    
    print(f"{Fore.CYAN}🔌 Connecting to database at {host}:{port} as {user}{Style.RESET_ALL}")
    # In real code, you would use these values to establish a database connection
    
def send_notification(recipient, message):
    """Example function that uses email configuration"""
    smtp_host = EMAIL_CONFIG['host']
    smtp_port = EMAIL_CONFIG['port']
    sender = EMAIL_CONFIG['default_sender']
    
    print(f"{Fore.GREEN}📧 Sending email to {recipient} via {smtp_host}:{smtp_port}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}📧 From: {sender}{Style.RESET_ALL}")
    
    # Environment-aware behavior for message content
    if is_production():
        # Production - no revealing details
        print(f"{Fore.GREEN}📧 Message: {message}{Style.RESET_ALL}")
    else:
        # Non-production - add environment marker to message
        env_tag = "[TEST]" if is_test() else "[DEV]"
        print(f"{Fore.GREEN}📧 Message: {env_tag} {message}{Style.RESET_ALL}")
        
    # Safe debugging - never runs in production due to is_debug_enabled() implementation
    if DEBUG_MODE:
        # This will never execute in production
        print(f"{Fore.YELLOW}⚠️ Debug mode is on, logging extra information{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}⚠️ SMTP details: {smtp_host}:{smtp_port}, auth: {EMAIL_CONFIG.get('use_auth', False)}{Style.RESET_ALL}")
        
def process_upi_payment(upi_id, amount):
    """Example function that uses UPI configuration with environment awareness"""
    # Use environment-aware configuration
    provider = UPI_CONFIG['provider']
    api_key = UPI_CONFIG['api_key']  # Securely stored in config
    
    # Use environment-specific payment limits
    max_amount = env_aware(
        development=1000.00,  # Low limit for development
        test=10000.00,        # Medium limit for testing
        production=50000.00    # Higher limit for production
    )
    
    if amount > max_amount:
        print(f"{Fore.RED}❌ Payment amount exceeds maximum for this environment: ₹{max_amount}{Style.RESET_ALL}")
        return False
        
    # Only use sandbox in non-production environments
    use_sandbox = not is_production()
    endpoint = UPI_CONFIG.get('sandbox_endpoint' if use_sandbox else 'production_endpoint')
    
    print(f"{Fore.CYAN}💸 Processing UPI payment of {Fore.GREEN}₹{amount}{Fore.CYAN} to {upi_id}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}💸 Using provider: {provider} ({('Sandbox' if use_sandbox else 'Production')}){Style.RESET_ALL}")
    print(f"{Fore.CYAN}💸 Endpoint: {endpoint}{Style.RESET_ALL}")
    
    # In real code, you would use the API key to authenticate with the UPI service
    return True
    
if __name__ == "__main__":
    # Environment-aware example usage
    env_name = "PRODUCTION" if is_production() else "TEST" if is_test() else "DEVELOPMENT"
    print(f"{Fore.YELLOW}Running in {env_name} environment{Style.RESET_ALL}")
    
    # Example usage
    connect_to_database()
    
    # Environment-specific recipients
    recipient = env_aware(
        development="dev@example.com", 
        test="test@example.com", 
        production="customer@example.com"
    )
    
    send_notification(recipient, "Hello from CBS!")
    
    # Use environment-appropriate UPI ID and amount
    sample_upi = env_aware(
        development="dev@upi", 
        test="test@upi", 
        production="user@upi"
    )
    
    sample_amount = env_aware(
        development=10.00,  # Small amount in development
        test=100.00,       # Medium amount in test
        production=1000.00  # Larger amount in production
    )
    
    process_upi_payment(sample_upi, sample_amount)
