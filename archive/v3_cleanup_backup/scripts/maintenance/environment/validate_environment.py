#!/usr/bin/env python
"""
Enhanced Environment Validator Script

This script validates the environment configuration across the Core Banking System.
It checks that all components are properly configured for the current environment,
provides recommendations for missing or incorrect configurations, and includes
robust fallback mechanisms for mixed environment detection.
"""

import os
import sys
import socket
import platform
import argparse
from pathlib import Path
import importlib.util
import traceback
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Primary environment detection from config module
PRIMARY_ENV = None
try:
    from app.config.environment import (
        Environment, get_environment_name, is_production, is_development, is_test,
        is_debug_enabled, env_aware
    )
    
    PRIMARY_ENV = {
        "name": get_environment_name(),
        "is_production": is_production(),
        "is_development": is_development(),
        "is_test": is_test(),
        "debug_enabled": is_debug_enabled(),
        "source": "app.config.environment"
    }
except ImportError:
    print(f"{Fore.YELLOW}Cannot import primary environment module. Using fallback detection.{Style.RESET_ALL}")

# Multi-layered fallback environment detection
def detect_environment():
    """
    Detect the environment using multiple methods and reconcile any conflicts
    
    Returns:
        dict: Environment information with confidence score
    """
    detection_methods = []
    
    # Method 1: Primary environment module
    if PRIMARY_ENV:
        detection_methods.append({
            "name": PRIMARY_ENV["name"],
            "is_production": PRIMARY_ENV["is_production"], 
            "is_development": PRIMARY_ENV["is_development"],
            "is_test": PRIMARY_ENV["is_test"],
            "confidence": 0.9,  # High confidence in configured value
            "source": "config_module"
        })
    
    # Method 2: Environment variables
    env_var = os.environ.get("CBS_ENVIRONMENT", "").lower()
    if env_var:
        is_prod = env_var == "production"
        is_dev = env_var == "development"
        is_test = env_var == "test"
        
        detection_methods.append({
            "name": env_var,
            "is_production": is_prod,
            "is_development": is_dev,
            "is_test": is_test,
            "confidence": 0.8,  # High confidence but slightly less than config
            "source": "environment_variable"
        })
    
    # Method 3: Hostname-based detection
    hostname = socket.gethostname().lower()
    if hostname:
        is_prod = any(p in hostname for p in ["prod", "prd", "production"])
        is_dev = any(d in hostname for d in ["dev", "development"])
        is_test = any(t in hostname for t in ["test", "tst", "qa", "stage", "staging"])
        
        name = "production" if is_prod else "test" if is_test else "development"
        
        detection_methods.append({
            "name": name,
            "is_production": is_prod,
            "is_development": is_dev,
            "is_test": is_test, 
            "confidence": 0.6,  # Medium confidence
            "source": "hostname"
        })
    
    # Method 4: Database connection existence
    try:
        # Check for production database connection
        # Commented out direct sys.path modification
        # sys.path.insert(0, str(Path(__file__)
        from utils.lib.packages import fix_path
        fix_path()
        from utils.lib.packages import import_module
        DatabaseConnection = import_module("database.python.connection").DatabaseConnection
        
        db = DatabaseConnection()
        conn = db.get_connection()
        if conn:
            # Test if this is a production database by checking tables
            cursor = conn.cursor()
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                LIMIT 10
            """)
            tables = cursor.fetchall()
            
            # Check table naming patterns to guess environment
            table_names = [t[0] for t in tables if t[0]]
            
            # Production tables typically don't have prefixes
            has_prod_pattern = all(not t.startswith(("dev_", "test_")) for t in table_names if t)
            has_test_pattern = any(t.startswith("test_") for t in table_names if t)
            has_dev_pattern = any(t.startswith("dev_") for t in table_names if t)
            
            # Check for specific system tables that might indicate environment
            has_prod_users = any(t == "users" or t == "accounts" for t in table_names)
            has_prod_transactions = any(t == "transactions" for t in table_names)
            has_additional_prod_indicators = has_prod_users and has_prod_transactions
            
            # Better detection with multiple signals
            name = "production" if (has_prod_pattern and not has_dev_pattern and not has_test_pattern) or has_additional_prod_indicators else \
                   "test" if has_test_pattern else \
                   "development" if has_dev_pattern else \
                   "unknown"
                   
            if name != "unknown":
                detection_methods.append({
                    "name": name,
                    "is_production": name == "production",
                    "is_development": name == "development",
                    "is_test": name == "test",
                    "confidence": 0.75 if has_additional_prod_indicators else 0.7,  # Higher confidence with more indicators
                    "source": "database_pattern"
                })
            
            cursor.close()
            conn.close()
    except ImportError:
        # Database module not available
        pass
    except Exception as e:
        # Log the error for debugging but continue with other detection methods
        if "--verbose" in sys.argv:
            print(f"{Fore.YELLOW}Database detection failed: {str(e)}{Style.RESET_ALL}")
        pass  # Continue with other detection methods
    
    # Method 5: Fallback to default (development) if nothing else works
    if not detection_methods:
        detection_methods.append({
            "name": "development",  # Default to development as safest option
            "is_production": False,
            "is_development": True,
            "is_test": False,
            "confidence": 0.3,  # Low confidence
            "source": "default_fallback"
        })
    
    # Reconcile multiple detections by weighted confidence
    if len(detection_methods) > 1:
        # Check for conflicts
        env_names = set(m["name"] for m in detection_methods)
        
        if len(env_names) == 1:
            # No conflict - all methods agree
            result = detection_methods[0].copy()
            result["confidence"] = 1.0  # Perfect confidence when all agree
            result["sources"] = [m["source"] for m in detection_methods]
            return result
        else:
            # Conflict detected - use weighted confidence
            weighted_prod = sum(m["confidence"] * (1 if m["is_production"] else 0) for m in detection_methods)
            weighted_dev = sum(m["confidence"] * (1 if m["is_development"] else 0) for m in detection_methods)
            weighted_test = sum(m["confidence"] * (1 if m["is_test"] else 0) for m in detection_methods)
            
            total_weight = sum(m["confidence"] for m in detection_methods)
            
            if total_weight == 0:
                # Failsafe if all weights are 0
                return {
                    "name": "development",
                    "is_production": False,
                    "is_development": True,
                    "is_test": False,
                    "confidence": 0.1,
                    "source": "failsafe",
                    "sources": ["failsafe"]
                }
            
            # Normalize weights
            weighted_prod /= total_weight
            weighted_dev /= total_weight
            weighted_test /= total_weight
            
            # Select environment with highest weighted score
            max_weight = max(weighted_prod, weighted_dev, weighted_test)
            name = "production" if weighted_prod == max_weight else \
                   "test" if weighted_test == max_weight else "development"
            
            # Calculate confidence as agreement level
            confidence = max_weight
            
            return {
                "name": name,
                "is_production": name == "production",
                "is_development": name == "development",
                "is_test": name == "test",
                "confidence": confidence,
                "source": "weighted_consensus",
                "sources": [m["source"] for m in detection_methods],
                "conflicting_environments": sorted(env_names)
            }
    
    # Single detection method case
    return detection_methods[0]


class EnhancedEnvironmentValidator:
    """Tool to validate environment configuration across the system with enhanced detection"""
    
    def __init__(self):
        # Use enhanced environment detection
        self.detected_env = detect_environment()
        self.env_name = self.detected_env["name"]
        self.issues = []
        self.passed = []
        self.warnings = []
        
        # Set environment-specific colors
        if self.detected_env["is_production"]:
            self.env_color = Fore.GREEN
        elif self.detected_env["is_test"]:
            self.env_color = Fore.YELLOW
        else:  # development
            self.env_color = Fore.BLUE
            
        # Add warning if environment detection has low confidence
        if self.detected_env.get("confidence", 1.0) < 0.7:
            self.warnings.append(
                f"Environment detection confidence is low ({self.detected_env.get('confidence', 0)*100:.0f}%). "
                f"Consider setting CBS_ENVIRONMENT explicitly."
            )
            
        # Add warning if environment detection found conflicts
        if "conflicting_environments" in self.detected_env and len(self.detected_env["conflicting_environments"]) > 1:
            self.warnings.append(
                f"Conflicting environment detections: {', '.join(self.detected_env['conflicting_environments'])}. "
                f"Using '{self.env_name}' based on confidence weighting."
            )
    
    def print_header(self):
        """Print validator header"""
        confidence_percent = int(self.detected_env.get("confidence", 1.0) * 100)
        confidence_display = f"(Confidence: {confidence_percent}%)" if confidence_percent < 100 else ""
        
        # Format the environment name with proper padding
        env_display = self.env_name.upper().ljust(20)
        
        # Add warning symbol for low confidence
        confidence_indicator = "⚠️ " if confidence_percent < 70 else ""
        
        header = f"""
{self.env_color}╔════════════════════════════════════════════════════╗
║ ENVIRONMENT VALIDATOR                              ║
║ Environment: {env_display}                   ║
║ {confidence_indicator}{confidence_display.ljust(46)}║
╚════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
        print(header)
        
        # Print detection sources
        if "sources" in self.detected_env:
            sources = self.detected_env["sources"]
            if len(sources) > 1:
                print(f"{self.env_color}Environment detected from multiple sources: {', '.join(sources)}{Style.RESET_ALL}")
            else:
                print(f"{self.env_color}Environment detected from: {sources[0]}{Style.RESET_ALL}")
        
        # Display date and time of validation
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Validation run at: {current_time}")
        
        # Show Python version
        print(f"Python version: {platform.python_version()}")
        
        # Add separator line for clarity
        print(f"{self.env_color}{'─' * 52}{Style.RESET_ALL}")
    
    def check_environment_variables(self):
        """Check required environment variables"""
        print(f"\n{self.env_color}Checking Environment Variables...{Style.RESET_ALL}")
        
        # Define required variables per environment
        required_vars = {
            "production": [
                "CBS_ENVIRONMENT",
                "CBS_SECRET_KEY",
                "CBS_DB_HOST",
                "CBS_DB_USER",
                "CBS_DB_PASSWORD"
            ],
            "test": [
                "CBS_ENVIRONMENT"
            ],
            "development": [
                # No strict requirements for dev
            ]
        }
        
        # Check for current environment
        current_env = self.env_name
        required_for_env = required_vars.get(current_env, [])
        
        for var in required_for_env:
            if var not in os.environ:
                self.issues.append(f"Missing required environment variable: {var}")
            else:
                self.passed.append(f"Environment variable present: {var}")
        
        # Check for conflicting variables
        if "CBS_DEBUG" in os.environ and self.detected_env["is_production"]:
            if os.environ["CBS_DEBUG"].lower() == "true":
                self.issues.append("Debug mode is enabled in production environment")
        
        # Check environment variable consistency
        if "CBS_ENVIRONMENT" in os.environ:
            env_var = os.environ["CBS_ENVIRONMENT"].lower()
            if env_var != self.env_name:
                self.issues.append(
                    f"Environment variable CBS_ENVIRONMENT='{env_var}' doesn't match detected environment '{self.env_name}'"
                )
    
    def check_database_config(self):
        """Check database configuration"""
        print(f"\n{self.env_color}Checking Database Configuration...{Style.RESET_ALL}")
        
        # Try to import database connection
        try:
            from utils.lib.packages import import_module
            DatabaseConnection = import_module("database.python.connection").DatabaseConnection
            
            # Create instance to check if connection works
            db = DatabaseConnection()
            conn = db.get_connection()
            
            if conn:
                self.passed.append("Database connection successful")
                
                # Check table prefixing
                if not self.detected_env["is_production"]:
                    try:
                        cursor = conn.cursor()
                        cursor.execute("SHOW TABLES")
                        tables = cursor.fetchall()
                        
                        # Extract table names from the result
                        table_names = []
                        for table_row in tables:
                            table_names.append(table_row[0])
                        
                        # Check for environment prefix in non-production
                        prefix = f"{self.env_name}_"
                        prefixed_tables = [t for t in table_names if t.startswith(prefix)]
                        unprefixed_tables = [t for t in table_names if not t.startswith(prefix) and not t.startswith(("dev_", "test_", "prod_"))]
                        
                        if not prefixed_tables and unprefixed_tables:
                            self.issues.append(f"No tables with environment prefix '{prefix}' found")
                        elif prefixed_tables:
                            self.passed.append(f"Found {len(prefixed_tables)} tables with correct environment prefix")
                        
                        # In test/dev, warn about production-like unprefixed tables
                        if not self.detected_env["is_production"] and unprefixed_tables:
                            self.warnings.append(
                                f"Found {len(unprefixed_tables)} tables without environment prefix in non-production environment. "
                                f"This could indicate a mixed environment."
                            )
                        
                        cursor.close()
                    except Exception as e:
                        self.issues.append(f"Error checking table prefixes: {str(e)}")
                conn.close()
            else:
                self.issues.append("Could not establish database connection")
                
        except ImportError:
            self.issues.append("Could not import database connection module")
        except Exception as e:
            self.issues.append(f"Database connection error: {str(e)}")
    
    def check_model_environment_awareness(self):
        """Check if models are environment-aware"""
        print(f"\n{self.env_color}Checking Model Environment Awareness...{Style.RESET_ALL}")
        
        try:
            # Import models module
            from app.models import models
            
            # Check if table names have correct prefix
            for attr_name in dir(models):
                attr = getattr(models, attr_name)
                
                # Check if it's a SQLAlchemy model class
                if hasattr(attr, '__tablename__'):
                    table_name = attr.__tablename__
                    
                    # In non-production, tables should be prefixed
                    if not self.detected_env["is_production"] and not table_name.startswith(f"{self.env_name}_"):
                        self.issues.append(f"Model {attr_name} table is not environment-prefixed: {table_name}")
                    else:
                        if self.detected_env["is_production"] and not table_name.startswith(f"{self.env_name}_"):
                            self.passed.append(f"Model {attr_name} correctly unprefixed in production: {table_name}")
                        elif not self.detected_env["is_production"] and table_name.startswith(f"{self.env_name}_"):
                            self.passed.append(f"Model {attr_name} correctly prefixed: {table_name}")
            
        except ImportError:
            self.warnings.append("Could not import models module - skipping model checks")
        except Exception as e:
            self.issues.append(f"Error checking model environment awareness: {str(e)}")
    
    def check_environment_config(self):
        """Check environment configuration file"""
        print(f"\n{self.env_color}Checking Environment Configuration...{Style.RESET_ALL}")
        
        config_paths = [
            "app/config/settings.yaml",
            "app/config/environment.py"
        ]
        
        for path in config_paths:
            full_path = Path(path)
            if full_path.exists():
                self.passed.append(f"Found configuration file: {path}")
            else:
                self.issues.append(f"Missing configuration file: {path}")
                
        # Check if environment module is properly set up
        try:
            # Check if environment functions are working
            from app.config.environment import (
                get_environment_name, is_production, is_development, is_test
            )
            
            env_name = get_environment_name()
            is_prod = is_production()
            is_dev = is_development()
            is_testing = is_test()
            
            # Make sure only one environment is active
            active_count = sum([is_prod, is_dev, is_testing])
            if active_count != 1:
                self.issues.append(f"Invalid environment state: {active_count} environments active simultaneously")
            else:
                self.passed.append("Environment detection is properly configured")
                
            # Check if configured environment matches our detected environment
            if env_name.lower() != self.env_name:
                self.issues.append(f"Environment module reports '{env_name}' but detected environment is '{self.env_name}'")
                
        except ImportError:
            # Already handled earlier, no need to report twice
            pass
        except Exception as e:
            self.issues.append(f"Environment module error: {str(e)}")
    
    def check_transaction_processor(self):
        """Check transaction processor environment settings"""
        print(f"\n{self.env_color}Checking Transaction Processor...{Style.RESET_ALL}")
        
        try:
            # Try to import transaction processor
            from transactions.transaction_processor import TransactionProcessor
            
            # Create instance
            processor = TransactionProcessor()
            
            # Check environment attributes
            if hasattr(processor, 'env_name'):
                if processor.env_name.lower() == self.env_name:
                    self.passed.append("Transaction processor has correct environment name")
                else:
                    self.issues.append(f"Transaction processor environment mismatch: {processor.env_name} vs {self.env_name}")
            else:
                self.issues.append("Transaction processor missing environment name")
                
            # Check transaction limits
            if hasattr(processor, 'max_transaction_amount'):
                limit = processor.max_transaction_amount
                if self.detected_env["is_production"] and limit < 100000:
                    self.issues.append(f"Production transaction limit too low: {limit}")
                elif self.detected_env["is_test"] and limit > 100000:
                    self.issues.append(f"Test transaction limit too high: {limit}")
                else:
                    self.passed.append(f"Transaction processor has appropriate limits for {self.env_name}")
            else:
                self.issues.append("Transaction processor missing max_transaction_amount")
                
        except ImportError:
            self.issues.append("Could not import transaction processor module")
        except Exception as e:
            self.issues.append(f"Transaction processor error: {str(e)}")
    
    def check_file_paths(self):
        """Check environment-specific file paths"""
        print(f"\n{self.env_color}Checking Environment-Specific Paths...{Style.RESET_ALL}")
        
        # Define paths that should exist
        env_paths = {
            "logs": f"logs/{self.env_name}",
            "transactions_inbound": f"transactions/inbound/{self.env_name}",
            "transactions_outbound": f"transactions/outbound/{self.env_name}"
        }
        
        for name, path in env_paths.items():
            if os.path.exists(path):
                self.passed.append(f"Found environment path: {path}")
            else:
                # Only issue warning if not in production (production uses default paths)
                if not self.detected_env["is_production"]:
                    self.issues.append(f"Missing environment path: {path}")

    def check_conflicting_environments(self):
        """Check for signs of mixed environments"""
        print(f"\n{self.env_color}Checking for Mixed Environment Issues...{Style.RESET_ALL}")

        # Check for mixed directories (e.g., both dev and test directories exist)
        env_dirs = {
            "development": ["logs/development", "transactions/inbound/development", "data/development"],
            "test": ["logs/test", "transactions/inbound/test", "data/test"],
            "production": ["logs/production", "transactions/inbound/production", "data/production"]
        }

        # Count how many environment-specific directories exist
        env_dir_counts = {}
        for env_name, dirs in env_dirs.items():
            env_dir_counts[env_name] = sum(1 for d in dirs if os.path.exists(d))

        # If multiple environments have directories, this could indicate confusion
        active_envs = [env for env, count in env_dir_counts.items() if count > 0]
        if len(active_envs) > 1:
            self.warnings.append(
                f"Found directories for multiple environments: {', '.join(active_envs)}. "
                f"This may indicate a mixed environment setup."
            )

        # Check for environment detection consistency
        if PRIMARY_ENV:
            primary_env_name = PRIMARY_ENV["name"].lower()
            if primary_env_name != self.env_name:
                self.issues.append(
                    f"Primary environment module reports '{primary_env_name}' but detected environment is '{self.env_name}'. "
                    f"This inconsistency could cause system errors."
                )
        
        # Check configuration files for conflicting environment settings
        config_files = [
            "app/config/settings.yaml",
            "app/config/environment.py",
            "app/config/database.py"
        ]
        
        env_keys = ["environment", "env", "ENV_NAME", "ENVIRONMENT", "ENVIRONMENT_NAME"]
        conflicting_files = []
        
        for config_file in config_files:
            if not os.path.exists(config_file):
                continue
                
            try:
                if config_file.endswith(".py"):
                    # Read Python file line by line looking for environment
                    with open(config_file, "r") as f:
                        content = f.read()
                        
                    # Look for direct environment assignments
                    for env_key in env_keys:
                        for env_name in ["production", "development", "test"]:
                            if f"{env_key} = ['\"]?{env_name}['\"]?" in content or f"{env_key}=['\"]?{env_name}['\"]?" in content:
                                if env_name != self.env_name:
                                    conflicting_files.append((config_file, env_name))
                                    break
                elif config_file.endswith(".yaml") or config_file.endswith(".yml"):
                    # Check yaml files
                    import yaml
                    with open(config_file, "r") as f:
                        try:
                            config = yaml.safe_load(f)
                            for env_key in env_keys:
                                if env_key in config and isinstance(config[env_key], str):
                                    if config[env_key].lower() != self.env_name:
                                        conflicting_files.append((config_file, config[env_key].lower()))
                        except yaml.YAMLError:
                            pass
            except Exception:
                pass
        
        # Report conflicting environment settings in config files
        if conflicting_files:
            for file_path, env_name in conflicting_files:
                self.issues.append(
                    f"Conflicting environment in {file_path}: found '{env_name}' but detected environment is '{self.env_name}'."
                )
                
        # Check environment variables for conflicts
        env_var_keys = ["CBS_ENVIRONMENT", "APP_ENV", "FLASK_ENV", "DJANGO_ENV"]
        conflicting_env_vars = []
        
        for key in env_var_keys:
            if key in os.environ and os.environ[key].lower() != self.env_name:
                conflicting_env_vars.append((key, os.environ[key]))
                
        if conflicting_env_vars:
            for key, value in conflicting_env_vars:
                self.issues.append(
                    f"Environment variable '{key}={value}' conflicts with detected environment '{self.env_name}'."
                )
    
    def run_all_checks(self):
        """Run all environment validation checks"""
        self.print_header()
        
        print(f"Running environment validation for: {self.env_color}{self.env_name.upper()}{Style.RESET_ALL}")
        
        # Run all checks
        self.check_environment_variables()
        self.check_environment_config()
        self.check_database_config()
        self.check_model_environment_awareness()
        self.check_transaction_processor()
        self.check_file_paths()
        self.check_conflicting_environments()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print validation summary"""
        print(f"\n{self.env_color}====== VALIDATION SUMMARY ======{Style.RESET_ALL}")
        print(f"Environment: {self.env_color}{self.env_name.upper()}{Style.RESET_ALL}")
        print(f"Total Checks: {len(self.passed) + len(self.issues) + len(self.warnings)}")
        print(f"Passed: {Fore.GREEN}{len(self.passed)}{Style.RESET_ALL}")
        print(f"Warnings: {Fore.YELLOW}{len(self.warnings)}{Style.RESET_ALL}")
        print(f"Issues: {Fore.RED if self.issues else Fore.GREEN}{len(self.issues)}{Style.RESET_ALL}")
        
        if self.warnings:
            print(f"\n{Fore.YELLOW}Warnings:{Style.RESET_ALL}")
            for i, warning in enumerate(self.warnings, 1):
                print(f"{Fore.YELLOW}{i}. {warning}{Style.RESET_ALL}")
        
        if self.issues:
            print(f"\n{Fore.RED}Issues Found:{Style.RESET_ALL}")
            for i, issue in enumerate(self.issues, 1):
                print(f"{Fore.RED}{i}. {issue}{Style.RESET_ALL}")
            
            # Print recommendations
            self.print_recommendations()
        else:
            print(f"\n{Fore.GREEN}✓ All essential checks passed! Environment appears to be correctly configured.{Style.RESET_ALL}")
            if self.warnings:
                print(f"{Fore.YELLOW}Please review warnings for potential improvements.{Style.RESET_ALL}")
    
    def print_recommendations(self):
        """Print recommendations for fixing issues"""
        print(f"\n{Fore.YELLOW}Recommendations:{Style.RESET_ALL}")
        
        for issue in self.issues:
            if "Missing required environment variable" in issue:
                var_name = issue.split(": ")[1]
                print(f"• Set the environment variable: {var_name}")
                print(f"  {Fore.BLUE}$env:CBS_{var_name}='value'  # PowerShell{Style.RESET_ALL}")
                print(f"  {Fore.BLUE}export CBS_{var_name}=value  # Bash{Style.RESET_ALL}")
            
            elif "Database connection" in issue:
                print(f"• Check database credentials in config.py or environment variables")
                print(f"• Ensure database server is running and accessible")
            
            elif "table is not environment-prefixed" in issue:
                print(f"• Update model class with environment-aware base class")
                print(f"• Check app/models/models.py for correct inheritance")
            
            elif "Missing configuration file" in issue:
                path = issue.split(": ")[1]
                print(f"• Create the missing configuration file: {path}")
            
            elif "Missing environment path" in issue:
                path = issue.split(": ")[1]
                print(f"• Create the directory: {Fore.BLUE}mkdir -p {path}{Style.RESET_ALL}")
                
            elif "environment module reports" in issue and "detected environment is" in issue:
                print(f"• Ensure CBS_ENVIRONMENT is consistently set across all configuration sources")
                print(f"• Update app/config/environment.py to use the correct environment detection logic")
                print(f"• Restart all application services to ensure consistent environment")


def main():
    """Main function to run environment validation"""
    parser = argparse.ArgumentParser(description="Validate CBS Environment Configuration")
    parser.add_argument("--env", type=str, choices=["development", "test", "production"],
                       help="Override environment for validation")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Show detailed validation information")
    parser.add_argument("--fix", action="store_true", 
                       help="Attempt to automatically fix common issues")
    parser.add_argument("--force-detect", action="store_true",
                       help="Force environment detection using all available methods")
    
    args = parser.parse_args()
    
    # Override environment if specified
    if args.env:
        os.environ["CBS_ENVIRONMENT"] = args.env
        print(f"Overriding environment to: {args.env}")
    
    # Print system information in verbose mode
    if args.verbose:
        print(f"\n{Fore.CYAN}System Information:{Style.RESET_ALL}")
        print(f"Python Version: {platform.python_version()}")
        print(f"Platform: {platform.platform()}")
        print(f"Hostname: {socket.gethostname()}")
        print(f"Working Directory: {os.getcwd()}")
        
        if args.force_detect:
            env_details = detect_environment()
            print(f"\n{Fore.CYAN}Detected Environment Details:{Style.RESET_ALL}")
            for key, value in env_details.items():
                if key != "sources":
                    print(f"- {key}: {value}")
    
    # Run validator
    validator = EnhancedEnvironmentValidator()
    validator.run_all_checks()
    
    # If --fix flag is provided, try to fix common issues
    if args.fix:
        print(f"\n{Fore.CYAN}Attempting to fix issues...{Style.RESET_ALL}")
        # Create missing directories
        for issue in validator.issues:
            if "Missing environment path" in issue:
                path = issue.split(": ")[1]
                try:
                    print(f"Creating directory: {path}")
                    os.makedirs(path, exist_ok=True)
                    print(f"{Fore.GREEN}✓ Created successfully{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{Fore.RED}Failed: {str(e)}{Style.RESET_ALL}")
    
    # Exit with error code if issues found
    if validator.issues:
        sys.exit(1)
    

if __name__ == "__main__":
    main()
