"""
Configuration module for Treasury operations.

This module provides centralized configuration management for all treasury functions,
including API endpoints, market data sources, risk limits, and operational parameters.
"""

import os
import json
import yaml
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_CONFIG = {
    "market_data": {
        "api_endpoint": "https://market-data.example.com/api/v1/",
        "api_key_env": "MARKET_DATA_API_KEY", 
        "update_frequency_seconds": 300,
        "providers": ["bloomberg", "refinitiv", "marketwatch"]
    },
    "bonds": {
        "pricing_model": "yield_curve",
        "risk_limits": {
            "duration_max": 15,
            "concentration_pct_max": 25
        }
    },
    "derivatives": {
        "pricing_models": {
            "options": "black_scholes",
            "futures": "cost_of_carry",
            "swaps": "zero_curve"
        },
        "risk_limits": {
            "var_confidence": 0.99,
            "var_horizon_days": 10
        }
    },
    "forex": {
        "default_base_currency": "USD",
        "position_limits": {
            "intraday_max_exposure": 10000000,
            "overnight_max_exposure": 5000000
        }
    },
    "liquidity": {
        "target_lcr": 1.2,
        "target_nsfr": 1.1,
        "minimum_cash_reserves_pct": 15
    }
}

def load_config(config_path=None):
    """
    Load configuration from file with fallback to default values.
    
    Args:
        config_path: Path to configuration file (JSON or YAML)
        
    Returns:
        dict: Configuration dictionary
    """
    config = DEFAULT_CONFIG.copy()
    
    # Try to load configuration from file if provided
    if config_path:
        path = Path(config_path)
        
        if not path.exists():
            logger.warning(f"Configuration file not found: {config_path}")
            return config
            
        try:
            if path.suffix.lower() in ['.yaml', '.yml']:
                with open(path, 'r') as file:
                    file_config = yaml.safe_load(file)
            elif path.suffix.lower() == '.json':
                with open(path, 'r') as file:
                    file_config = json.load(file)
            else:
                logger.warning(f"Unsupported configuration file format: {path.suffix}")
                return config
                
            # Update configuration with values from file
            _update_dict_recursive(config, file_config)
            logger.info(f"Configuration loaded from {config_path}")
            
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {str(e)}")
            
    # Check for environment variables and override configuration
    for section in config:
        for key in config[section]:
            env_var = f"TREASURY_{section.upper()}_{key.upper()}"
            if env_var in os.environ:
                try:
                    # Handle nested dictionaries differently
                    if isinstance(config[section][key], dict):
                        continue
                    
                    # Convert environment variable to appropriate type
                    value = os.environ[env_var]
                    if isinstance(config[section][key], bool):
                        config[section][key] = value.lower() in ['true', '1', 'yes', 'y']
                    elif isinstance(config[section][key], int):
                        config[section][key] = int(value)
                    elif isinstance(config[section][key], float):
                        config[section][key] = float(value)
                    else:
                        config[section][key] = value
                        
                    logger.debug(f"Configuration overridden by environment: {env_var}")
                    
                except Exception as e:
                    logger.warning(f"Error processing environment variable {env_var}: {str(e)}")
    
    return config

def _update_dict_recursive(base_dict, update_dict):
    """
    Update a nested dictionary recursively.
    
    Args:
        base_dict: Dictionary to update
        update_dict: Dictionary with new values
    """
    for key, value in update_dict.items():
        if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
            _update_dict_recursive(base_dict[key], value)
        else:
            base_dict[key] = value

# Global configuration object - will be initialized when first accessed
_config = None

def get_config(config_path=None):
    """
    Get the configuration object, initializing it if necessary.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        dict: Configuration dictionary
    """
    global _config
    if _config is None:
        _config = load_config(config_path)
    return _config
