"""
Fraud Detection System for Core Banking System

This module provides real-time and batch fraud detection capabilities
for transactions and other banking operations.
"""

import os
import time
import logging
import datetime
import json
from typing import Dict, Any, List, Optional, Tuple
import uuid
import math

# Try to import optional dependencies
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

# Initialize logger
logger = logging.getLogger(__name__)

# Import configuration
import os
import sys

# Try to use local config if available
try:
    # First try relative import from parent directory
    from ..config import get_config, get_environment
except ImportError:
    # Fallback to system config
    try:
        from config import get_config, get_environment
    except ImportError:
        # Use stub functions if all else fails
        def get_environment():
            return os.environ.get("CBS_ENVIRONMENT", "DEVELOPMENT").upper()
            
        def get_config(module_name):
            return {
                "enable_rules": True,
                "enable_ml": False
            }


class FraudDetectionSystem:
    """Comprehensive fraud detection system for banking operations"""
    
    def __init__(self):
        """Initialize the fraud detection system"""
        self.environment = get_environment()
        self.config = get_config("fraud_detection")
        
        # Environment-specific settings
        self._configure_environment_settings()
        
        # Initialize rule engines and models
        self._initialize_detection_components()
        
        logger.info(f"Fraud Detection System initialized in {self.environment} environment")
    
    def _configure_environment_settings(self):
        """Configure environment-specific settings"""
        # Default thresholds
        self.thresholds = {
            "transaction_amount": 10000,
            "velocity_threshold": 5,
            "velocity_window_minutes": 60,
            "location_change_km": 500,
            "location_change_hours": 24,
            "new_beneficiary_amount": 5000,
            "ml_anomaly_score": 0.8
        }
        
        # Override with environment-specific thresholds
        if self.environment == "PRODUCTION":
            # Production has stricter thresholds
            env_thresholds = self.config.get("production_thresholds", {})
        elif self.environment == "TEST":
            # Test has moderate thresholds
            env_thresholds = self.config.get("test_thresholds", {})
        else:
            # Development has relaxed thresholds
            env_thresholds = self.config.get("development_thresholds", {})
            
        # Update thresholds
        self.thresholds.update(env_thresholds)
        
        # Cache for velocity checking
        self.transaction_cache = {}
        self.cache_expiry_minutes = self.thresholds["velocity_window_minutes"] * 2
        
        logger.info(f"Configured fraud detection thresholds for {self.environment} environment")
    
    def _initialize_detection_components(self):
        """Initialize rule engines and ML models"""
        self.rules_enabled = self.config.get("enable_rules", True)
        self.ml_enabled = self.config.get("enable_ml", False)
        
        # Initialize ML models if enabled and available
        if self.ml_enabled and ML_AVAILABLE:
            self._initialize_ml_models()
        elif self.ml_enabled:
            logger.warning("ML detection enabled but required packages not available")
            self.ml_enabled = False
    
    def _initialize_ml_models(self):
        """Initialize machine learning models for fraud detection"""
        try:
            # For transactions anomaly detection
            self.transaction_model = IsolationForest(
                contamination=0.05,  # Assuming 5% anomalies
                random_state=42
            )
            
            # For login behavior anomaly detection
            self.login_model = IsolationForest(
                contamination=0.03,  # Assuming 3% anomalies
                random_state=42
            )
            
            # Check if we have model files to load
            model_dir = self.config.get("model_directory", "models/fraud")
            
            if os.path.exists(f"{model_dir}/transaction_model.pkl"):
                self._load_models(model_dir)
            else:
                logger.warning("No pre-trained ML models found. Will train on new data.")
            
            logger.info("ML models initialized for fraud detection")
        except Exception as e:
            logger.error(f"Failed to initialize ML models: {str(e)}")
            self.ml_enabled = False
    
    def _load_models(self, model_dir):
        """Load pre-trained models from files"""
        import joblib
        try:
            self.transaction_model = joblib.load(f"{model_dir}/transaction_model.pkl")
            self.login_model = joblib.load(f"{model_dir}/login_model.pkl")
            self.transaction_scaler = joblib.load(f"{model_dir}/transaction_scaler.pkl")
            self.login_scaler = joblib.load(f"{model_dir}/login_scaler.pkl")
            logger.info("Loaded pre-trained fraud detection models")
        except Exception as e:
            logger.error(f"Failed to load pre-trained models: {str(e)}")
            # Fall back to untrained models
    
    def check_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check a transaction for potential fraud
        
        Args:
            transaction_data (Dict): Transaction details including:
                - user_id: ID of the user initiating the transaction
                - amount: Transaction amount
                - transaction_type: Type of transaction (transfer, deposit, etc.)
                - recipient_id: ID of the recipient (for transfers)
                - channel: Channel used (ATM, UPI, internet banking, etc.)
                - location: Dictionary with lat/long or IP address
                - device_id: ID of the device used
                
        Returns:
            Dict: Fraud check result with:
                - is_suspicious: Whether the transaction is suspicious
                - risk_score: Risk score from 0-100
                - risk_factors: List of detected risk factors
                - action: Recommended action (ALLOW, REVIEW, BLOCK)
        """
        # Initialize result
        result = {
            "is_suspicious": False,
            "risk_score": 0,
            "risk_factors": [],
            "action": "ALLOW"
        }
        
        # Apply rule-based checks if enabled
        if self.rules_enabled:
            self._apply_transaction_rules(transaction_data, result)
        
        # Apply ML-based checks if enabled
        if self.ml_enabled and ML_AVAILABLE:
            self._apply_transaction_ml(transaction_data, result)
        
        # Update transaction cache for velocity checks
        self._update_transaction_cache(transaction_data)
        
        # Determine overall action based on risk score
        if result["risk_score"] >= 80:
            result["action"] = "BLOCK"
        elif result["risk_score"] >= 50:
            result["action"] = "REVIEW"
        
        return result
    
    def _apply_transaction_rules(self, transaction_data: Dict[str, Any], result: Dict[str, Any]):
        """Apply rule-based fraud checks to transaction"""
        user_id = transaction_data.get("user_id")
        amount = float(transaction_data.get("amount", 0))
        transaction_type = transaction_data.get("transaction_type", "")
        recipient_id = transaction_data.get("recipient_id")
        channel = transaction_data.get("channel", "")
        
        # High amount check
        if amount > self.thresholds["transaction_amount"]:
            result["risk_factors"].append("HIGH_AMOUNT")
            result["risk_score"] += 30
        
        # Velocity check (multiple transactions in short time)
        if user_id in self.transaction_cache:
            user_transactions = self.transaction_cache[user_id]
            recent_count = len([tx for tx in user_transactions 
                             if time.time() - tx["timestamp"] < self.thresholds["velocity_window_minutes"] * 60])
            
            if recent_count > self.thresholds["velocity_threshold"]:
                result["risk_factors"].append("HIGH_VELOCITY")
                result["risk_score"] += 25
        
        # New recipient check for transfers
        if transaction_type == "TRANSFER" and recipient_id:
            # Check if recipient is new and amount is significant
            if not self._is_known_recipient(user_id, recipient_id) and amount > self.thresholds["new_beneficiary_amount"]:
                result["risk_factors"].append("NEW_RECIPIENT_HIGH_AMOUNT")
                result["risk_score"] += 20
        
        # Unusual location check
        if "location" in transaction_data:
            location = transaction_data["location"]
            if self._is_location_change_suspicious(user_id, location):
                result["risk_factors"].append("UNUSUAL_LOCATION")
                result["risk_score"] += 35
        
        # Update suspicious flag if score exceeds threshold
        result["is_suspicious"] = result["risk_score"] >= 50
    
    def _apply_transaction_ml(self, transaction_data: Dict[str, Any], result: Dict[str, Any]):
        """Apply machine learning checks to transaction"""
        try:
            # Extract and prepare features
            features = [
                float(transaction_data.get("amount", 0)),
                self._encode_channel(transaction_data.get("channel", "")),
                self._encode_transaction_type(transaction_data.get("transaction_type", "")),
                self._get_hour_of_day(transaction_data.get("timestamp", time.time())),
                self._get_day_of_week(transaction_data.get("timestamp", time.time()))
            ]
            
            # Add historical features if available
            if hasattr(self, "transaction_scaler"):
                # Scale features
                features_scaled = self.transaction_scaler.transform([features])
                
                # Get anomaly score
                anomaly_score = self.transaction_model.decision_function([features_scaled[0]])[0]
                normalized_score = 1.0 - (anomaly_score + 0.5)  # Convert to 0-1 range
                
                if normalized_score > self.thresholds["ml_anomaly_score"]:
                    result["risk_factors"].append("ML_ANOMALY_DETECTED")
                    result["risk_score"] += 40
                    result["is_suspicious"] = True
        except Exception as e:
            logger.error(f"Error in ML fraud detection: {str(e)}")
    
    def _update_transaction_cache(self, transaction_data: Dict[str, Any]):
        """Update transaction cache for velocity checks"""
        user_id = transaction_data.get("user_id")
        if not user_id:
            return
            
        # Add timestamp if not present
        if "timestamp" not in transaction_data:
            transaction_data["timestamp"] = time.time()
        
        # Initialize user cache if needed
        if user_id not in self.transaction_cache:
            self.transaction_cache[user_id] = []
        
        # Add transaction to cache
        self.transaction_cache[user_id].append(transaction_data)
        
        # Clean old transactions from cache
        self._clean_transaction_cache()
    
    def _clean_transaction_cache(self):
        """Remove old transactions from cache"""
        current_time = time.time()
        expiry_seconds = self.cache_expiry_minutes * 60
        
        for user_id in list(self.transaction_cache.keys()):
            # Filter out expired transactions
            self.transaction_cache[user_id] = [
                tx for tx in self.transaction_cache[user_id]
                if current_time - tx["timestamp"] < expiry_seconds
            ]
            
            # Remove empty user entries
            if not self.transaction_cache[user_id]:
                del self.transaction_cache[user_id]
    
    def _is_known_recipient(self, user_id: str, recipient_id: str) -> bool:
        """Check if recipient is known based on transaction history"""
        # In a real system, this would query a database
        if user_id in self.transaction_cache:
            for tx in self.transaction_cache[user_id]:
                if tx.get("recipient_id") == recipient_id:
                    return True
        return False
    
    def _is_location_change_suspicious(self, user_id: str, location: Dict[str, Any]) -> bool:
        """Check if location change is suspicious"""
        if user_id not in self.transaction_cache:
            return False
            
        # Get last known transaction location
        last_tx = None
        for tx in reversed(sorted(self.transaction_cache[user_id], key=lambda x: x.get("timestamp", 0))):
            if "location" in tx:
                last_tx = tx
                break
                
        if not last_tx:
            return False
        
        # Check time difference
        time_diff_hours = (time.time() - last_tx["timestamp"]) / 3600
        
        # If both locations have lat/long, calculate distance
        if ("lat" in location and "long" in location and 
            "lat" in last_tx["location"] and "long" in last_tx["location"]):
            
            distance_km = self._calculate_distance(
                location["lat"], location["long"],
                last_tx["location"]["lat"], last_tx["location"]["long"]
            )
            
            # Calculate maximum reasonable travel speed (km/h)
            max_speed = 1000  # Airplane speed
            if time_diff_hours > 0:
                implied_speed = distance_km / time_diff_hours
                
                # If distance is large but time is short, it's suspicious
                if implied_speed > max_speed:
                    return True
                    
                # If distance exceeds threshold and time is short
                if (distance_km > self.thresholds["location_change_km"] and 
                    time_diff_hours < self.thresholds["location_change_hours"]):
                    return True
        
        # If IP-based location, compare country/city
        elif "ip" in location and "ip" in last_tx["location"]:
            # In a production system, this would use geolocation
            # For now, just compare IP addresses
            if location["ip"] != last_tx["location"]["ip"]:
                if time_diff_hours < self.thresholds["location_change_hours"]:
                    return True
        
        return False
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in kilometers"""
        # Haversine formula
        earth_radius = 6371  # km
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Differences
        dlon = lon2_rad - lon1_rad
        dlat = lat2_rad - lat1_rad
        
        # Haversine formula
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        distance = earth_radius * c
        
        return distance
    
    def _encode_channel(self, channel: str) -> int:
        """Encode transaction channel as a numeric value"""
        channel_map = {
            "ATM": 1,
            "UPI": 2,
            "INTERNET_BANKING": 3,
            "MOBILE_BANKING": 4,
            "BRANCH": 5
        }
        return channel_map.get(channel, 0)
    
    def _encode_transaction_type(self, tx_type: str) -> int:
        """Encode transaction type as a numeric value"""
        type_map = {
            "TRANSFER": 1,
            "WITHDRAWAL": 2,
            "DEPOSIT": 3,
            "PAYMENT": 4,
            "REFUND": 5
        }
        return type_map.get(tx_type, 0)
    
    def _get_hour_of_day(self, timestamp: float) -> int:
        """Get hour of day from timestamp"""
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.hour
    
    def _get_day_of_week(self, timestamp: float) -> int:
        """Get day of week from timestamp"""
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.weekday()
    
    def check_login_activity(self, login_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check a login attempt for potential fraud
        
        Args:
            login_data (Dict): Login details including:
                - user_id: ID of the user logging in
                - timestamp: Time of login attempt
                - ip_address: IP address of login
                - device_id: ID of the device used
                - success: Whether login was successful
                - location: Dictionary with location info
                - user_agent: Browser/app user agent string
                
        Returns:
            Dict: Fraud check result with:
                - is_suspicious: Whether the login is suspicious
                - risk_score: Risk score from 0-100
                - risk_factors: List of detected risk factors
                - action: Recommended action (ALLOW, ALERT, BLOCK)
        """
        # Similar structure to check_transaction, but focused on login security
        # Implementation details omitted for brevity
        result = {
            "is_suspicious": False,
            "risk_score": 0,
            "risk_factors": [],
            "action": "ALLOW"
        }
        
        # Implement login security checks here
        # (Similar structure to transaction checks, but with login-specific rules)
        
        return result
    
    def batch_analyze(self, date_range: Optional[Tuple[datetime.datetime, datetime.datetime]] = None) -> Dict[str, Any]:
        """
        Perform batch analysis of transactions for fraud patterns
        
        Args:
            date_range (Tuple, optional): Start and end date for analysis
            
        Returns:
            Dict: Analysis results and detected patterns
        """
        # Implementation would query transaction database and perform batch analysis
        # This would typically use more complex algorithms than real-time checks
        return {"status": "not_implemented"}
    
    def train_models(self, training_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Train/update ML models with new data
        
        Args:
            training_data (Dict, optional): Training data or None to use DB data
            
        Returns:
            bool: Success status
        """
        if not ML_AVAILABLE or not PANDAS_AVAILABLE:
            logger.error("ML libraries not available for model training")
            return False
            
        # Implementation would fetch historical data and train models
        # In a real system, this would use a mix of labeled and unlabeled data
        return False


# Create a singleton instance
fraud_detection = FraudDetectionSystem()

# Export main functions for easy access
check_transaction = fraud_detection.check_transaction
check_login_activity = fraud_detection.check_login_activity
batch_analyze = fraud_detection.batch_analyze
train_models = fraud_detection.train_models
