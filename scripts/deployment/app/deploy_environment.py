"""
Environment-specific Deployment Script

This script handles the deployment process for different environments.
It sets up the appropriate configuration, database, and services based on the target environment.
"""

import os
import sys
import argparse
import subprocess
import shutil
from pathlib import Path
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Add the project root to the path

# Use centralized import manager
try:
    from utils.lib.packages import fix_path, import_module, is_production, is_development, is_test, is_debug_enabled, Environment
    fix_path()  # Ensures the project root is in sys.path
except ImportError:
    # Fallback for when the import manager is not available
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # Adjust levels as needed


# Try to import environment module
try:
    from app.config.environment import (
        Environment, get_environment_name, is_production, is_development, is_test
    )
except ImportError:
    print(f"{Fore.RED}Error: Could not import environment module. Make sure the application is correctly installed.{Style.RESET_ALL}")
    sys.exit(1)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Core Banking System - Environment Deployment Script")
    parser.add_argument('--env', '-e', type=str, default=None, 
                        choices=['development', 'test', 'production'],
                        help='Target environment for deployment')
    parser.add_argument('--skip-db', action='store_true', help='Skip database setup')
    parser.add_argument('--skip-config', action='store_true', help='Skip configuration setup')
    parser.add_argument('--force', '-f', action='store_true', help='Force deployment without confirmation')
    parser.add_argument('--backup', '-b', action='store_true', help='Create a backup before deployment')
    return parser.parse_args()

def backup_environment(env_name):
    """Create a backup of the current environment"""
    timestamp = subprocess.check_output(['date', '+%Y%m%d_%H%M%S']).decode('utf-8').strip()
    backup_dir = f"backups/app_backups/{env_name}_{timestamp}"
    
    print(f"{Fore.YELLOW}Creating backup at: {backup_dir}{Style.RESET_ALL}")
    os.makedirs(backup_dir, exist_ok=True)
    
    # Copy configuration files
    print(f"{Fore.BLUE}Backing up configuration...{Style.RESET_ALL}")
    config_backup_dir = os.path.join(backup_dir, "config")
    os.makedirs(config_backup_dir, exist_ok=True)
    shutil.copy("app/config/settings.yaml", os.path.join(config_backup_dir, "settings.yaml"))
    
    # Backup database if available
    print(f"{Fore.BLUE}Backing up database...{Style.RESET_ALL}")
    try:
        subprocess.run([
            "python", "scripts/database_scripts/backup_db.py", 
            "--output", os.path.join(backup_dir, f"db_{env_name}.sql")
        ])
    except Exception as e:
        print(f"{Fore.RED}Database backup failed: {e}{Style.RESET_ALL}")
    
    print(f"{Fore.GREEN}Backup completed: {backup_dir}{Style.RESET_ALL}")
    return backup_dir

def setup_environment(env_name, skip_db=False, skip_config=False):
    """Set up the environment-specific configuration and database"""
    print(f"{Fore.BLUE}Setting up {env_name.upper()} environment...{Style.RESET_ALL}")
    
    # Set environment variable
    os.environ["CBS_ENVIRONMENT"] = env_name
    
    # Setup configuration
    if not skip_config:
        print(f"{Fore.BLUE}Setting up configuration...{Style.RESET_ALL}")
        try:
            subprocess.run(["python", "scripts/setup_config.py", "--env", env_name], check=True)
        except subprocess.CalledProcessError:
            print(f"{Fore.RED}Configuration setup failed!{Style.RESET_ALL}")
            return False
    
    # Setup database
    if not skip_db:
        print(f"{Fore.BLUE}Setting up database...{Style.RESET_ALL}")
        try:
            if env_name != "production":
                # Allow reset for non-production environments
                subprocess.run(["python", "scripts/database_scripts/setup_db.py", "--env", env_name, "--reset"], check=True)
            else:
                # No reset for production
                subprocess.run(["python", "scripts/database_scripts/setup_db.py", "--env", env_name], check=True)
        except subprocess.CalledProcessError:
            print(f"{Fore.RED}Database setup failed!{Style.RESET_ALL}")
            return False
    
    print(f"{Fore.GREEN}Environment setup completed for: {env_name.upper()}{Style.RESET_ALL}")
    return True

def deploy_environment(env_name):
    """Deploy the application to the specified environment"""
    print(f"{Fore.BLUE}Deploying to {env_name.upper()}...{Style.RESET_ALL}")
    
    # Different deployment steps based on environment
    if env_name == "production":
        print(f"{Fore.YELLOW}Running production deployment checks...{Style.RESET_ALL}")
        try:
            # Run tests
            subprocess.run(["python", "tests/run_tests.py", "--env", "test"], check=True)
            
            # Check security
            subprocess.run(["python", "scripts/setup_security.py", "--check"], check=True)
            
        except subprocess.CalledProcessError as e:
            print(f"{Fore.RED}Deployment checks failed: {e}{Style.RESET_ALL}")
            return False
    
    # Deploy the application
    print(f"{Fore.BLUE}Updating application files...{Style.RESET_ALL}")
    
    # Different actions based on environment
    if env_name == "development":
        print(f"{Fore.GREEN}Development deployment complete!{Style.RESET_ALL}")
    elif env_name == "test":
        print(f"{Fore.GREEN}Test deployment complete!{Style.RESET_ALL}")
    elif env_name == "production":
        print(f"{Fore.GREEN}Production deployment complete!{Style.RESET_ALL}")
    
    # Create environment info file
    with open(f".env_info_{env_name}", "w") as f:
        f.write(f"CBS_ENVIRONMENT={env_name}\n")
        f.write(f"DEPLOYED_AT={subprocess.check_output(['date']).decode('utf-8').strip()}\n")
    
    return True

def main():
    """Main deployment function"""
    args = parse_args()
    
    # Determine target environment
    env_name = args.env or get_environment_name().lower()
    
    # Display banner
    env_color = Fore.GREEN if env_name == "production" else (Fore.YELLOW if env_name == "test" else Fore.BLUE)
    print(f"{env_color}╔════════════════════════════════════════════════════╗")
    print(f"║ CORE BANKING SYSTEM - DEPLOYMENT                  ║")
    print(f"║ Target Environment: {env_name.upper().ljust(20)}              ║")
    print(f"╚════════════════════════════════════════════════════╝{Style.RESET_ALL}")
    
    # Confirm deployment to production
    if env_name == "production" and not args.force:
        confirm = input(f"{Fore.RED}You are about to deploy to PRODUCTION. Are you sure? (type 'yes' to confirm): {Style.RESET_ALL}")
        if confirm.lower() != "yes":
            print(f"{Fore.YELLOW}Deployment cancelled.{Style.RESET_ALL}")
            return
    
    # Create backup if requested
    if args.backup:
        backup_dir = backup_environment(env_name)
        print(f"{Fore.GREEN}Backup created at: {backup_dir}{Style.RESET_ALL}")
    
    # Setup environment
    if not setup_environment(env_name, args.skip_db, args.skip_config):
        print(f"{Fore.RED}Environment setup failed. Deployment aborted.{Style.RESET_ALL}")
        return
    
    # Deploy the application
    if deploy_environment(env_name):
        print(f"{env_color}Deployment to {env_name.upper()} completed successfully!{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Deployment to {env_name.upper()} failed!{Style.RESET_ALL}")

if __name__ == "__main__":
    main()