"""
Security policy service for Mobile Banking domain.
Contains security-related business rules and validations.
"""
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

from ..entities.mobile_user import MobileBankingUser, DeviceStatus
from ..entities.mobile_session import MobileBankingSession
from ..entities.mobile_transaction import MobileTransaction, MobileTransactionType

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class MobileSecurityPolicyService:
    """Domain service for security policy rules and validations."""
    
    @staticmethod
    def is_secure_password(password: str) -> tuple[bool, str]:
        """
        Check if a password meets security requirements.
        
        Args:
            password: The password to check
            
        Returns:
            Tuple of (is_secure, reason)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not any(char.isupper() for char in password):
            return False, "Password must contain at least one uppercase letter"
            
        if not any(char.islower() for char in password):
            return False, "Password must contain at least one lowercase letter"
            
        if not any(char.isdigit() for char in password):
            return False, "Password must contain at least one number"
            
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?/"
        if not any(char in special_chars for char in password):
            return False, "Password must contain at least one special character"
            
        return True, ""
    
    @staticmethod
    def is_secure_mpin(mpin: str) -> tuple[bool, str]:
        """
        Check if an MPIN meets security requirements.
        
        Args:
            mpin: The MPIN to check
            
        Returns:
            Tuple of (is_secure, reason)
        """
        if not mpin.isdigit():
            return False, "MPIN must contain only digits"
            
        if len(mpin) != 6:
            return False, "MPIN must be exactly 6 digits"
            
        # Check for sequential digits (e.g., 123456, 654321)
        if mpin in ['123456', '234567', '345678', '456789', '987654', '876543', '765432', '654321']:
            return False, "MPIN must not be a sequence of digits"
            
        # Check for repeating digits (e.g., 111111, 222222)
        if len(set(mpin)) == 1:
            return False, "MPIN must not contain only one repeating digit"
            
        return True, ""
    
    @staticmethod
    def detect_suspicious_activity(
        user: MobileBankingUser, 
        session: MobileBankingSession,
        location: Optional[str] = None
    ) -> tuple[bool, str]:
        """
        Detect suspicious activity based on user behavior.
        
        Args:
            user: The user to check
            session: The current session
            location: Current location (optional)
            
        Returns:
            Tuple of (is_suspicious, reason)
        """
        # Check if device is registered
        device_registered = False
        device_status = None
        
        for device in user.registered_devices:
            if device.device_id == session.device_id:
                device_registered = True
                device_status = device.status
                break
        
        # If device is not registered, that's suspicious
        if not device_registered:
            return True, "Unregistered device detected"
        
        # If device is blacklisted or suspended, that's suspicious
        if device_status in [DeviceStatus.BLACKLISTED, DeviceStatus.SUSPENDED]:
            return True, f"Login attempt from {device_status.value} device"
        
        # Check for app version mismatch (potential security update bypassing)
        for device in user.registered_devices:
            if device.device_id == session.device_id and device.app_version != session.app_version:
                return True, "App version mismatch detected"
        
        # Check for location change if location is provided
        if location and session.location and location != session.location:
            # Calculate a simple distance heuristic (in a real system, use proper geolocation)
            # For example, a login from a different city/country in a short time period
            return True, "Unusual location change detected"
            
        return False, ""
    
    @staticmethod
    def assess_transaction_risk(
        transaction: MobileTransaction,
        user: MobileBankingUser,
        transaction_history: List[MobileTransaction]
    ) -> tuple[str, str]:
        """
        Assess the risk level of a transaction.
        
        Args:
            transaction: The transaction to assess
            user: The user making the transaction
            transaction_history: User's previous transactions
            
        Returns:
            Tuple of (risk_level, reason)
        """
        # High-risk transaction types
        high_risk_types = [
            MobileTransactionType.FUNDS_TRANSFER,
            MobileTransactionType.QR_PAYMENT,
            MobileTransactionType.UPI_PAYMENT
        ]
        
        # Determine if transaction amount is unusually high
        if transaction.amount:
            # Get the user's average transaction amount for this type
            similar_transactions = [
                t for t in transaction_history 
                if t.transaction_type == transaction.transaction_type and t.amount is not None
            ]
            
            if similar_transactions:
                avg_amount = sum(t.amount for t in similar_transactions) / len(similar_transactions)
                if transaction.amount > avg_amount * 3:  # Amount is 3x the average
                    return "high", "Transaction amount significantly higher than usual"
        
        # Check if the transaction type is high risk
        if transaction.transaction_type in high_risk_types:
            # Check if the destination account is new (not in transaction history)
            if transaction.destination_account:
                dest_account_seen_before = any(
                    t.destination_account == transaction.destination_account
                    for t in transaction_history
                )
                
                if not dest_account_seen_before:
                    return "medium", "First transaction to this destination account"
        
        # Check transaction frequency
        recent_transactions = [
            t for t in transaction_history 
            if (datetime.now() - t.transaction_date).total_seconds() < 3600  # Within last hour
        ]
        
        if len(recent_transactions) > 5:  # More than 5 transactions in an hour
            return "medium", "Unusually high transaction frequency"
        
        # Default risk level
        return "low", "No unusual patterns detected"
    
    @staticmethod
    def get_transaction_limits(user: MobileBankingUser, transaction_type: MobileTransactionType) -> dict:
        """
        Get transaction limits for a user and transaction type.
        
        Args:
            user: The user
            transaction_type: The transaction type
            
        Returns:
            Dictionary with limit information
        """
        # Base limits by transaction type
        base_limits = {
            MobileTransactionType.FUNDS_TRANSFER: 50000.0,
            MobileTransactionType.BILL_PAYMENT: 10000.0,
            MobileTransactionType.RECHARGE: 2000.0,
            MobileTransactionType.QR_PAYMENT: 10000.0,
            MobileTransactionType.UPI_PAYMENT: 25000.0,
            MobileTransactionType.WITHDRAWAL: 25000.0,
        }
        
        # Get the base limit for this transaction type
        per_transaction_limit = base_limits.get(transaction_type, 10000.0)
        daily_limit = per_transaction_limit * 5  # Default daily limit is 5x per-transaction limit
        
        # In a real implementation, adjust limits based on user profile, history, etc.
        
        return {
            "per_transaction_limit": per_transaction_limit,
            "daily_limit": daily_limit
        }
