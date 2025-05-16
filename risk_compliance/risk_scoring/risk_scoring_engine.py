"""
Risk Scoring Engine for Core Banking System

This module provides risk assessment and scoring capabilities for customers,
accounts, transactions, and other banking entities.
"""

import os
import time
import logging
import datetime
import json
import math
from typing import Dict, Any, List, Optional, Union, Tuple

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
            return {}


class RiskScoringEngine:
    """Risk scoring engine for banking entities"""
    
    def __init__(self):
        """Initialize the risk scoring engine"""
        self.environment = get_environment()
        self.config = get_config("risk_scoring")
        
        # Environment-specific settings
        self._configure_environment_settings()
        
        # Initialize scoring components
        self._initialize_scoring_components()
        
        logger.info(f"Risk Scoring Engine initialized in {self.environment} environment")
    
    def _configure_environment_settings(self):
        """Configure environment-specific settings"""
        # Risk factor weights (default values)
        self.customer_risk_weights = {
            "age": 0.05,
            "credit_score": 0.20,
            "employment_stability": 0.10,
            "income_stability": 0.15,
            "address_stability": 0.05,
            "past_delinquencies": 0.25,
            "banking_history": 0.10,
            "kyc_status": 0.10
        }
        
        self.account_risk_weights = {
            "account_type": 0.10,
            "account_age": 0.15,
            "balance_volatility": 0.15,
            "overdraft_frequency": 0.20,
            "customer_risk_score": 0.40
        }
        
        self.transaction_risk_weights = {
            "amount": 0.25,
            "transaction_type": 0.10,
            "recipient_risk": 0.20,
            "sender_risk": 0.20,
            "channel": 0.10,
            "time_of_day": 0.05,
            "location": 0.10
        }
        
        self.loan_risk_weights = {
            "loan_amount": 0.15,
            "loan_term": 0.05,
            "interest_rate": 0.10,
            "loan_purpose": 0.10,
            "collateral_value": 0.15,
            "customer_risk_score": 0.25,
            "debt_to_income": 0.20
        }
        
        # Environment-specific overrides
        if self.environment == "PRODUCTION":
            # Production uses standard weights
            pass
        elif self.environment == "TEST":
            # Test adjusts weights for testing scenarios
            self.customer_risk_weights["past_delinquencies"] = 0.30
            self.customer_risk_weights["credit_score"] = 0.15
        else:
            # Development uses simplified weights for easier testing
            for weights in [self.customer_risk_weights, self.account_risk_weights, 
                          self.transaction_risk_weights, self.loan_risk_weights]:
                keys = list(weights.keys())
                equal_weight = 1.0 / len(keys)
                for key in keys:
                    weights[key] = equal_weight
        
        logger.info(f"Configured risk scoring weights for {self.environment} environment")
    
    def _initialize_scoring_components(self):
        """Initialize scoring components and models"""
        # Set risk thresholds
        self.risk_thresholds = {
            "low": 30,
            "medium": 60,
            "high": 80
        }
        
        # Initialize risk score cache
        self.score_cache = {
            "customer": {},
            "account": {},
            "transaction": {},
            "loan": {}
        }
        
        # Cache expiry in seconds
        self.cache_expiry = 3600  # 1 hour
        
        # Cache timestamps for expiry checking
        self.cache_timestamps = {
            "customer": {},
            "account": {},
            "transaction": {},
            "loan": {}
        }
    
    def score_customer(self, customer_data: Dict[str, Any], 
                     force_refresh: bool = False) -> Dict[str, Any]:
        """
        Calculate risk score for a customer
        
        Args:
            customer_data (Dict): Customer details including:
                - customer_id: Unique identifier
                - age: Customer age
                - credit_score: Credit bureau score
                - employment_status: Current employment status
                - employment_years: Years at current employment
                - income: Annual income
                - address_years: Years at current address
                - past_delinquencies: Count of past delinquencies
                - banking_history_years: Years of banking relationship
                - kyc_status: KYC verification status
            force_refresh (bool): If True, ignore cached score
                
        Returns:
            Dict: Risk assessment result with:
                - risk_score: Score from 0-100
                - risk_level: LOW, MEDIUM, HIGH, VERY HIGH
                - risk_factors: List of key risk factors
                - score_details: Detailed scoring breakdown
        """
        customer_id = customer_data.get("customer_id")
        
        # Check cache if not forcing refresh
        if not force_refresh and customer_id in self.score_cache["customer"]:
            cache_time = self.cache_timestamps["customer"].get(customer_id, 0)
            if time.time() - cache_time < self.cache_expiry:
                return self.score_cache["customer"][customer_id]
        
        # Initialize score components and risk factors
        score_components = {}
        risk_factors = []
        
        # Score: Age factor
        age = customer_data.get("age", 35)
        if age < 25:
            score_components["age"] = 70  # Young customers are higher risk
            risk_factors.append("YOUNG_CUSTOMER")
        elif age > 65:
            score_components["age"] = 40  # Seniors are moderate risk
        else:
            score_components["age"] = 20  # Middle-age is lowest risk
        
        # Score: Credit score factor
        credit_score = customer_data.get("credit_score", 700)
        if credit_score < 600:
            score_components["credit_score"] = 90
            risk_factors.append("POOR_CREDIT_SCORE")
        elif credit_score < 700:
            score_components["credit_score"] = 60
        elif credit_score < 800:
            score_components["credit_score"] = 30
        else:
            score_components["credit_score"] = 10
        
        # Score: Employment stability
        employment_status = customer_data.get("employment_status", "EMPLOYED")
        employment_years = customer_data.get("employment_years", 3)
        
        if employment_status == "UNEMPLOYED":
            score_components["employment_stability"] = 90
            risk_factors.append("UNEMPLOYED")
        elif employment_status == "SELF_EMPLOYED":
            score_components["employment_stability"] = 60
        elif employment_years < 1:
            score_components["employment_stability"] = 70
            risk_factors.append("NEW_EMPLOYMENT")
        elif employment_years < 3:
            score_components["employment_stability"] = 40
        else:
            score_components["employment_stability"] = 20
        
        # Score: Income stability
        income = customer_data.get("income", 50000)
        if income < 15000:
            score_components["income_stability"] = 80
            risk_factors.append("LOW_INCOME")
        elif income < 30000:
            score_components["income_stability"] = 60
        elif income < 100000:
            score_components["income_stability"] = 40
        else:
            score_components["income_stability"] = 20
        
        # Score: Address stability
        address_years = customer_data.get("address_years", 3)
        if address_years < 1:
            score_components["address_stability"] = 70
            risk_factors.append("NEW_ADDRESS")
        elif address_years < 2:
            score_components["address_stability"] = 50
        else:
            score_components["address_stability"] = 20
        
        # Score: Past delinquencies
        delinquencies = customer_data.get("past_delinquencies", 0)
        if delinquencies >= 3:
            score_components["past_delinquencies"] = 95
            risk_factors.append("MULTIPLE_DELINQUENCIES")
        elif delinquencies == 2:
            score_components["past_delinquencies"] = 80
            risk_factors.append("RECENT_DELINQUENCIES")
        elif delinquencies == 1:
            score_components["past_delinquencies"] = 60
        else:
            score_components["past_delinquencies"] = 10
        
        # Score: Banking history
        banking_years = customer_data.get("banking_history_years", 5)
        if banking_years < 1:
            score_components["banking_history"] = 80
            risk_factors.append("NEW_BANKING_CUSTOMER")
        elif banking_years < 3:
            score_components["banking_history"] = 50
        else:
            score_components["banking_history"] = 20
        
        # Score: KYC status
        kyc_status = customer_data.get("kyc_status", "VERIFIED")
        if kyc_status == "UNVERIFIED":
            score_components["kyc_status"] = 100
            risk_factors.append("KYC_UNVERIFIED")
        elif kyc_status == "PARTIAL":
            score_components["kyc_status"] = 70
            risk_factors.append("KYC_INCOMPLETE")
        else:
            score_components["kyc_status"] = 10
        
        # Calculate final score
        risk_score = 0
        for component, score in score_components.items():
            weight = self.customer_risk_weights.get(component, 0.1)
            weighted_score = score * weight
            risk_score += weighted_score
        
        # Determine risk level
        risk_level = self._get_risk_level(risk_score)
        
        # Prepare result
        result = {
            "customer_id": customer_id,
            "risk_score": round(risk_score, 2),
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "score_details": {
                "components": score_components,
                "weights": self.customer_risk_weights
            },
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        # Cache the result
        if customer_id:
            self.score_cache["customer"][customer_id] = result
            self.cache_timestamps["customer"][customer_id] = time.time()
        
        return result
    
    def score_account(self, account_data: Dict[str, Any], 
                    customer_risk_score: Optional[float] = None,
                    force_refresh: bool = False) -> Dict[str, Any]:
        """
        Calculate risk score for an account
        
        Args:
            account_data (Dict): Account details
            customer_risk_score (float, optional): Pre-calculated customer risk score
            force_refresh (bool): If True, ignore cached score
                
        Returns:
            Dict: Risk assessment result
        """
        account_id = account_data.get("account_id")
        
        # Check cache if not forcing refresh
        if not force_refresh and account_id in self.score_cache["account"]:
            cache_time = self.cache_timestamps["account"].get(account_id, 0)
            if time.time() - cache_time < self.cache_expiry:
                return self.score_cache["account"][account_id]
        
        # Initialize score components and risk factors
        score_components = {}
        risk_factors = []
        
        # Score: Account type factor
        account_type = account_data.get("account_type", "SAVINGS")
        if account_type == "CHECKING":
            score_components["account_type"] = 40
        elif account_type == "SAVINGS":
            score_components["account_type"] = 30
        elif account_type == "FIXED_DEPOSIT":
            score_components["account_type"] = 10
        else:
            score_components["account_type"] = 50
        
        # Score: Account age
        account_age_days = account_data.get("account_age_days", 365)
        if account_age_days < 30:
            score_components["account_age"] = 80
            risk_factors.append("NEW_ACCOUNT")
        elif account_age_days < 180:
            score_components["account_age"] = 60
        elif account_age_days < 365:
            score_components["account_age"] = 40
        else:
            score_components["account_age"] = 20
        
        # Score: Balance volatility
        balance_volatility = account_data.get("balance_volatility", 0.2)  # As percentage
        if balance_volatility > 0.5:
            score_components["balance_volatility"] = 80
            risk_factors.append("HIGH_BALANCE_VOLATILITY")
        elif balance_volatility > 0.3:
            score_components["balance_volatility"] = 60
        elif balance_volatility > 0.1:
            score_components["balance_volatility"] = 40
        else:
            score_components["balance_volatility"] = 20
        
        # Score: Overdraft frequency
        overdraft_count = account_data.get("overdraft_count_90days", 0)
        if overdraft_count >= 3:
            score_components["overdraft_frequency"] = 90
            risk_factors.append("FREQUENT_OVERDRAFTS")
        elif overdraft_count == 2:
            score_components["overdraft_frequency"] = 70
            risk_factors.append("MULTIPLE_OVERDRAFTS")
        elif overdraft_count == 1:
            score_components["overdraft_frequency"] = 50
        else:
            score_components["overdraft_frequency"] = 10
        
        # Score: Customer risk
        if customer_risk_score is None:
            # If no customer score provided, use a default or calculate
            customer_id = account_data.get("customer_id")
            if customer_id and customer_id in self.score_cache["customer"]:
                cached_customer = self.score_cache["customer"][customer_id]
                customer_risk_score = cached_customer.get("risk_score", 50)
            else:
                customer_risk_score = 50  # Default moderate risk
        
        score_components["customer_risk_score"] = customer_risk_score
        if customer_risk_score >= 70:
            risk_factors.append("HIGH_RISK_CUSTOMER")
        
        # Calculate final score
        risk_score = 0
        for component, score in score_components.items():
            weight = self.account_risk_weights.get(component, 0.1)
            weighted_score = score * weight
            risk_score += weighted_score
        
        # Determine risk level
        risk_level = self._get_risk_level(risk_score)
        
        # Prepare result
        result = {
            "account_id": account_id,
            "risk_score": round(risk_score, 2),
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "score_details": {
                "components": score_components,
                "weights": self.account_risk_weights
            },
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        # Cache the result
        if account_id:
            self.score_cache["account"][account_id] = result
            self.cache_timestamps["account"][account_id] = time.time()
        
        return result
    
    def score_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate risk score for a transaction
        
        Args:
            transaction_data (Dict): Transaction details
                
        Returns:
            Dict: Risk assessment result
        """
        # Implementation similar to score_customer and score_account
        # Scores based on transaction amount, type, participants, channel, etc.
        transaction_id = transaction_data.get("transaction_id", 
                                           f"TX-{int(time.time())}")
        
        # Initialize score components and risk factors
        score_components = {}
        risk_factors = []
        
        # Score: Transaction amount
        amount = float(transaction_data.get("amount", 0))
        avg_transaction = float(transaction_data.get("average_tx_amount", 500))
        
        amount_ratio = amount / avg_transaction if avg_transaction > 0 else 1
        
        if amount_ratio > 10:
            score_components["amount"] = 90
            risk_factors.append("UNUSUALLY_LARGE_AMOUNT")
        elif amount_ratio > 5:
            score_components["amount"] = 70
            risk_factors.append("LARGE_AMOUNT")
        elif amount_ratio > 2:
            score_components["amount"] = 50
        else:
            score_components["amount"] = 20
        
        # Score: Transaction type
        tx_type = transaction_data.get("transaction_type", "TRANSFER")
        if tx_type == "INTERNATIONAL_WIRE":
            score_components["transaction_type"] = 80
            risk_factors.append("INTERNATIONAL_TRANSACTION")
        elif tx_type in ["CASH_WITHDRAWAL", "CASH_DEPOSIT"]:
            score_components["transaction_type"] = 60
        elif tx_type == "TRANSFER":
            score_components["transaction_type"] = 40
        else:
            score_components["transaction_type"] = 30
        
        # Calculate final score (partial implementation)
        risk_score = 0
        for component, score in score_components.items():
            weight = self.transaction_risk_weights.get(component, 0.1)
            weighted_score = score * weight
            risk_score += weighted_score
        
        # Fill in missing components with defaults
        for component in self.transaction_risk_weights:
            if component not in score_components:
                score_components[component] = 50  # Default moderate risk
                risk_score += 50 * self.transaction_risk_weights[component]
        
        # Determine risk level
        risk_level = self._get_risk_level(risk_score)
        
        return {
            "transaction_id": transaction_id,
            "risk_score": round(risk_score, 2),
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "score_details": {
                "components": score_components,
                "weights": self.transaction_risk_weights
            },
            "timestamp": datetime.datetime.now().isoformat()
        }
    
    def score_loan(self, loan_data: Dict[str, Any],
                 customer_risk_score: Optional[float] = None) -> Dict[str, Any]:
        """
        Calculate risk score for a loan application or active loan
        
        Args:
            loan_data (Dict): Loan details
            customer_risk_score (float, optional): Pre-calculated customer risk score
                
        Returns:
            Dict: Risk assessment result
        """
        # Implementation would score loan based on amount, term, purpose, collateral, etc.
        return {"loan_id": loan_data.get("loan_id"), "risk_score": 50, "risk_level": "MEDIUM"}
    
    def _get_risk_level(self, score: float) -> str:
        """Convert risk score to risk level"""
        if score >= self.risk_thresholds["high"]:
            return "HIGH"
        elif score >= self.risk_thresholds["medium"]:
            return "MEDIUM"
        elif score >= self.risk_thresholds["low"]:
            return "LOW"
        else:
            return "VERY LOW"
    
    def clear_cache(self, entity_type: Optional[str] = None, 
                  entity_id: Optional[str] = None) -> bool:
        """
        Clear risk score cache
        
        Args:
            entity_type (str, optional): Type to clear ('customer', 'account', etc.)
            entity_id (str, optional): Specific entity ID to clear
            
        Returns:
            bool: Success status
        """
        try:
            if not entity_type:
                # Clear all caches
                for cache_type in self.score_cache:
                    self.score_cache[cache_type] = {}
                    self.cache_timestamps[cache_type] = {}
            elif entity_type in self.score_cache:
                if not entity_id:
                    # Clear specific type
                    self.score_cache[entity_type] = {}
                    self.cache_timestamps[entity_type] = {}
                else:
                    # Clear specific entity
                    if entity_id in self.score_cache[entity_type]:
                        del self.score_cache[entity_type][entity_id]
                    
                    if entity_id in self.cache_timestamps[entity_type]:
                        del self.cache_timestamps[entity_type][entity_id]
            
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False
    
    def get_scoring_stats(self) -> Dict[str, Any]:
        """Get statistics about risk scoring operations"""
        stats = {
            "cache_size": {
                "customer": len(self.score_cache["customer"]),
                "account": len(self.score_cache["account"]),
                "transaction": len(self.score_cache["transaction"]),
                "loan": len(self.score_cache["loan"])
            },
            "environment": self.environment,
            "risk_thresholds": self.risk_thresholds
        }
        
        return stats


# Create a singleton instance
risk_scoring = RiskScoringEngine()

# Export main functions for easy access
score_customer = risk_scoring.score_customer
score_account = risk_scoring.score_account
score_transaction = risk_scoring.score_transaction
score_loan = risk_scoring.score_loan
clear_cache = risk_scoring.clear_cache
get_scoring_stats = risk_scoring.get_scoring_stats
