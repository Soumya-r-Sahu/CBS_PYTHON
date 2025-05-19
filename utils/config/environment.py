"""
Environment configuration for the CBS_PYTHON system.

This module provides access to environment settings and helper functions
to check which environment the system is running in.
"""

import os
import sys
from enum import Enum
from pathlib import Path

# Define environment types
class Environment(Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

# Read environment from environment variables
def get_environment() -> str:
    """
    Get the current environment name from CBS_ENVIRONMENT env var
    
    Returns:
        String name of the environment (lowercase)
    """
    env = os.environ.get("CBS_ENVIRONMENT", "development").lower()
    
    # Validate environment is a recognized value
    if env not in [e.value for e in Environment]:
        print(f"Warning: Unknown environment '{env}', defaulting to 'development'")
        env = "development"
    
    return env

def get_environment_name() -> str:
    """
    Get the current environment name with proper capitalization
    
    Returns:
        String name of the environment (capitalized)
    """
    return get_environment().capitalize()

def is_production() -> bool:
    """Check if the system is running in production environment"""
    return get_environment() == Environment.PRODUCTION.value

def is_development() -> bool:
    """Check if the system is running in development environment"""
    return get_environment() == Environment.DEVELOPMENT.value

def is_testing() -> bool:
    """Check if the system is running in testing environment"""
    return get_environment() == Environment.TESTING.value

# Alias for is_testing for compatibility
def is_test() -> bool:
    """Alias for is_testing()"""
    return is_testing()

def is_staging() -> bool:
    """Check if the system is running in staging environment"""
    return get_environment() == Environment.STAGING.value

def is_debug_enabled() -> bool:
    """
    Check if debug mode is enabled
    
    Debug is enabled by default in development and testing environments,
    but can be overridden with CBS_DEBUG environment variable
    """
    if os.environ.get("CBS_DEBUG", "").lower() in ["true", "1", "yes"]:
        return True
    if os.environ.get("CBS_DEBUG", "").lower() in ["false", "0", "no"]:
        return False
    
    # Default based on environment
    return is_development() or is_testing()

def get_config_file_path() -> Path:
    """
    Get the path to the appropriate config file for the current environment
    
    Returns:
        Path object to the config file
    """
    env = get_environment()
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    
    # Look for environment-specific config file first
    config_file = project_root / f"config_{env}.py"
    if config_file.exists():
        return config_file
    
    # Fall back to default config
    return project_root / "config.py"

def load_environment_variables(env_file: str = None) -> None:
    """
    Load environment variables from a .env file
    
    Args:
        env_file: Path to the .env file (default: project_root/.env)
    """
    if env_file is None:
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        env_file = project_root / ".env"
    
    if not os.path.exists(env_file):
        return
    
    print(f"Loading environment variables from {env_file}")
    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
                
            key, value = line.split("=", 1)
            os.environ[key.strip()] = value.strip()

# Load environment variables when module is imported
load_environment_variables()
