"""
Fraud Detection Service for UPI transactions.

This service uses rule-based and AI patterns to detect potentially fraudulent transactions.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from uuid import UUID

from ...domain.entities.upi_transaction import UpiTransaction, UpiTransactionStatus
from ...application.interfaces.upi_transaction_repository_interface import UpiTransactionRepositoryInterface


class FraudDetectionService:
    """Service for detecting potentially fraudulent UPI transactions."""
    
    def __init__(self, transaction_repository: UpiTransactionRepositoryInterface):
        """
        Initialize with required dependencies.
        
        Args:
            transaction_repository: Repository for UPI transactions
        """
        self.transaction_repository = transaction_repository
        self.logger = logging.getLogger(__name__)
        
        # Initialize risk score thresholds
        self.medium_risk_threshold = 50
        self.high_risk_threshold = 80
    
    def analyze_transaction(self, transaction: UpiTransaction) -> Dict[str, Any]:
        """
        Analyze a transaction for fraud indicators.
        
        Args:
            transaction: The UPI transaction to analyze
            
        Returns:
            Dictionary with fraud analysis results
        """
        self.logger.info(f"Analyzing transaction {transaction.transaction_id} for fraud indicators")
        
        # Initialize risk score and fraud indicators
        risk_score = 0
        fraud_indicators = []
        
        # Get transaction history for the sender
        sender_history = self.transaction_repository.get_by_sender_vpa(
            transaction.sender_vpa, 
            limit=50
        )
        
        # Analyze transaction amount against sender history
        amount_risk = self._analyze_transaction_amount(transaction, sender_history)
        risk_score += amount_risk['risk_score']
        if amount_risk['is_suspicious']:
            fraud_indicators.append(amount_risk['indicator'])
        
        # Analyze transaction velocity
        velocity_risk = self._analyze_transaction_velocity(transaction, sender_history)
        risk_score += velocity_risk['risk_score']
        if velocity_risk['is_suspicious']:
            fraud_indicators.append(velocity_risk['indicator'])
        
        # Analyze receiver VPA
        receiver_risk = self._analyze_receiver_vpa(transaction, sender_history)
        risk_score += receiver_risk['risk_score']
        if receiver_risk['is_suspicious']:
            fraud_indicators.append(receiver_risk['indicator'])
        
        # Determine risk level
        risk_level = "LOW"
        if risk_score >= self.high_risk_threshold:
            risk_level = "HIGH"
        elif risk_score >= self.medium_risk_threshold:
            risk_level = "MEDIUM"
        
        # Prepare result
        result = {
            'transaction_id': str(transaction.transaction_id),
            'risk_score': risk_score,
            'risk_level': risk_level,
            'fraud_indicators': fraud_indicators,
            'recommended_action': self._get_recommended_action(risk_level)
        }
        
        self.logger.info(
            f"Fraud analysis for {transaction.transaction_id}: "
            f"Risk level={risk_level}, Score={risk_score}, Indicators={len(fraud_indicators)}"
        )
        
        return result
    
    def _analyze_transaction_amount(
        self, 
        transaction: UpiTransaction, 
        sender_history: List[UpiTransaction]
    ) -> Dict[str, Any]:
        """Analyze the transaction amount for suspicious patterns."""
        
        # Skip analysis if no history
        if not sender_history:
            return {
                'risk_score': 0,
                'is_suspicious': False,
                'indicator': None
            }
        
        # Calculate average and max transaction amounts from history
        completed_transactions = [t for t in sender_history if t.status == UpiTransactionStatus.COMPLETED]
        
        if not completed_transactions:
            return {
                'risk_score': 10,  # Some baseline risk for new users
                'is_suspicious': False,
                'indicator': None
            }
        
        amounts = [t.amount for t in completed_transactions]
        avg_amount = sum(amounts) / len(amounts)
        max_amount = max(amounts)
        
        # Define thresholds
        high_multiplier = 5  # 5x average is suspicious
        very_high_multiplier = 10  # 10x average is very suspicious
        
        # Analyze current transaction
        if transaction.amount > very_high_multiplier * avg_amount and transaction.amount > 10000:
            return {
                'risk_score': 40,
                'is_suspicious': True,
                'indicator': {
                    'type': 'UNUSUALLY_HIGH_AMOUNT',
                    'details': {
                        'transaction_amount': transaction.amount,
                        'average_amount': avg_amount,
                        'max_previous_amount': max_amount,
                        'multiplier': transaction.amount / avg_amount
                    }
                }
            }
        elif transaction.amount > high_multiplier * avg_amount and transaction.amount > 5000:
            return {
                'risk_score': 20,
                'is_suspicious': True,
                'indicator': {
                    'type': 'HIGH_AMOUNT',
                    'details': {
                        'transaction_amount': transaction.amount,
                        'average_amount': avg_amount,
                        'max_previous_amount': max_amount,
                        'multiplier': transaction.amount / avg_amount
                    }
                }
            }
        
        return {
            'risk_score': 0,
            'is_suspicious': False,
            'indicator': None
        }
    
    def _analyze_transaction_velocity(
        self, 
        transaction: UpiTransaction, 
        sender_history: List[UpiTransaction]
    ) -> Dict[str, Any]:
        """Analyze transaction velocity (frequency) for suspicious patterns."""
        
        # Skip analysis if no history
        if not sender_history:
            return {
                'risk_score': 0,
                'is_suspicious': False,
                'indicator': None
            }
        
        # Count recent transactions (last hour)
        one_hour_ago = transaction.transaction_date - timedelta(hours=1)
        recent_transactions = [
            t for t in sender_history 
            if t.transaction_date >= one_hour_ago
        ]
        
        if len(recent_transactions) >= 10:
            return {
                'risk_score': 30,
                'is_suspicious': True,
                'indicator': {
                    'type': 'HIGH_VELOCITY',
                    'details': {
                        'transactions_last_hour': len(recent_transactions)
                    }
                }
            }
        elif len(recent_transactions) >= 5:
            return {
                'risk_score': 15,
                'is_suspicious': True,
                'indicator': {
                    'type': 'MEDIUM_VELOCITY',
                    'details': {
                        'transactions_last_hour': len(recent_transactions)
                    }
                }
            }
        
        return {
            'risk_score': 0,
            'is_suspicious': False,
            'indicator': None
        }
    
    def _analyze_receiver_vpa(
        self, 
        transaction: UpiTransaction, 
        sender_history: List[UpiTransaction]
    ) -> Dict[str, Any]:
        """Analyze the receiver VPA for suspicious patterns."""
        
        # Skip analysis if no history
        if not sender_history:
            return {
                'risk_score': 0,
                'is_suspicious': False,
                'indicator': None
            }
        
        # Check if this is a new receiver
        receiver_vpa = transaction.receiver_vpa
        previous_receivers = {t.receiver_vpa for t in sender_history}
        
        if receiver_vpa not in previous_receivers and transaction.amount > 10000:
            return {
                'risk_score': 25,
                'is_suspicious': True,
                'indicator': {
                    'type': 'NEW_RECEIVER_HIGH_AMOUNT',
                    'details': {
                        'receiver_vpa': receiver_vpa,
                        'amount': transaction.amount
                    }
                }
            }
        
        # Check for suspicious VPA patterns (simplified example)
        suspicious_patterns = [
            # Random-looking VPAs with numbers and special chars might be suspicious
            '@ybl',  # Common for fraud as Ybl is popular
            'payment@',
            'verify@',
            'refund@',
            'support@'
        ]
        
        for pattern in suspicious_patterns:
            if pattern in receiver_vpa.lower():
                return {
                    'risk_score': 15,
                    'is_suspicious': True,
                    'indicator': {
                        'type': 'SUSPICIOUS_VPA_PATTERN',
                        'details': {
                            'receiver_vpa': receiver_vpa,
                            'matched_pattern': pattern
                        }
                    }
                }
        
        return {
            'risk_score': 0,
            'is_suspicious': False,
            'indicator': None
        }
    
    def _get_recommended_action(self, risk_level: str) -> Dict[str, Any]:
        """Get recommended action based on risk level."""
        if risk_level == "HIGH":
            return {
                'action': 'BLOCK',
                'description': 'Block the transaction and flag for manual review'
            }
        elif risk_level == "MEDIUM":
            return {
                'action': 'STEP_UP_AUTH',
                'description': 'Request additional authentication from the user'
            }
        else:
            return {
                'action': 'ALLOW',
                'description': 'Allow the transaction to proceed'
            }
    
    def get_daily_fraud_report(self) -> Dict[str, Any]:
        """
        Generate a daily fraud report.
        
        Returns:
            Dictionary with fraud statistics for the day
        """
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        # Get yesterday's transactions
        transactions = self.transaction_repository.get_by_date(yesterday)
        
        # Analyze each transaction
        analyzed_transactions = [self.analyze_transaction(t) for t in transactions]
        
        # Compile statistics
        high_risk = [t for t in analyzed_transactions if t['risk_level'] == 'HIGH']
        medium_risk = [t for t in analyzed_transactions if t['risk_level'] == 'MEDIUM']
        
        # Categorize fraud indicators
        indicators = {}
        for t in analyzed_transactions:
            for indicator in t['fraud_indicators']:
                if indicator and 'type' in indicator:
                    indicator_type = indicator['type']
                    if indicator_type not in indicators:
                        indicators[indicator_type] = 0
                    indicators[indicator_type] += 1
        
        # Sort indicators by frequency
        sorted_indicators = sorted(
            [{'type': k, 'count': v} for k, v in indicators.items()],
            key=lambda x: x['count'],
            reverse=True
        )
        
        report = {
            'date': yesterday.isoformat(),
            'total_transactions': len(transactions),
            'high_risk_transactions': len(high_risk),
            'medium_risk_transactions': len(medium_risk),
            'low_risk_transactions': len(transactions) - len(high_risk) - len(medium_risk),
            'high_risk_percentage': (len(high_risk) / len(transactions) * 100) if transactions else 0,
            'fraud_indicators': sorted_indicators,
            'high_risk_transaction_ids': [t['transaction_id'] for t in high_risk]
        }
        
        self.logger.info(f"Generated fraud report for {yesterday.isoformat()}")
        return report
