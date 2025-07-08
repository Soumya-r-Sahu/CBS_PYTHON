"""
Transaction Reconciliation Service for UPI transactions.

This service handles reconciliation of UPI transactions with the bank's core system
and the NPCI gateway to ensure transaction consistency and accuracy.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from uuid import UUID

from ...domain.entities.upi_transaction import UpiTransaction, UpiTransactionStatus
from ...application.interfaces.upi_transaction_repository_interface import UpiTransactionRepositoryInterface
from ...application.interfaces.external_payment_gateway_interface import ExternalPaymentGatewayInterface


class TransactionReconciliationService:
    """Service for reconciling UPI transactions."""
    
    def __init__(
        self,
        transaction_repository: UpiTransactionRepositoryInterface,
        gateway_service: ExternalPaymentGatewayInterface
    ):
        """
        Initialize with required dependencies.
        
        Args:
            transaction_repository: Repository for UPI transactions
            gateway_service: Service for communicating with the payment gateway
        """
        self.transaction_repository = transaction_repository
        self.gateway_service = gateway_service
        self.logger = logging.getLogger(__name__)
    
    def reconcile_pending_transactions(self) -> Dict[str, Any]:
        """
        Reconcile all pending transactions.
        
        Returns:
            Dictionary with reconciliation statistics
        """
        self.logger.info("Starting reconciliation of pending UPI transactions")
        
        # Get all pending transactions
        pending_transactions = self.transaction_repository.get_by_status(UpiTransactionStatus.PENDING)
        
        stats = {
            'total_pending': len(pending_transactions),
            'resolved': 0,
            'still_pending': 0,
            'failed': 0,
            'succeeded': 0
        }
        
        for transaction in pending_transactions:
            try:
                # Check if transaction is too old to reconcile
                if (datetime.now() - transaction.transaction_date) > timedelta(days=7):
                    # Mark very old pending transactions as failed
                    transaction.status = UpiTransactionStatus.FAILED
                    transaction.failure_reason = "Reconciliation timeout - transaction was pending for too long"
                    self.transaction_repository.save(transaction)
                    stats['failed'] += 1
                    continue
                
                # Verify transaction status with gateway
                gateway_status = self.gateway_service.verify_transaction(transaction.transaction_id)
                
                if gateway_status['status'] == 'SUCCESS':
                    # Update transaction based on gateway status
                    if gateway_status.get('transaction_status') == 'COMPLETED':
                        transaction.status = UpiTransactionStatus.COMPLETED
                        transaction.reference_id = gateway_status.get('reference_id', transaction.reference_id)
                        stats['succeeded'] += 1
                    elif gateway_status.get('transaction_status') == 'FAILED':
                        transaction.status = UpiTransactionStatus.FAILED
                        transaction.failure_reason = gateway_status.get('message', 'Unknown failure reason')
                        stats['failed'] += 1
                    else:
                        # Still pending
                        stats['still_pending'] += 1
                        continue
                else:
                    # Gateway error - leave transaction as pending for now
                    self.logger.warning(
                        f"Gateway error during reconciliation for transaction {transaction.transaction_id}: "
                        f"{gateway_status.get('message', 'Unknown error')}"
                    )
                    stats['still_pending'] += 1
                    continue
                
                # Save the updated transaction
                self.transaction_repository.save(transaction)
                stats['resolved'] += 1
                
            except Exception as e:
                self.logger.error(f"Error reconciling transaction {transaction.transaction_id}: {str(e)}")
                stats['still_pending'] += 1
        
        self.logger.info(f"Completed reconciliation of pending UPI transactions: {stats}")
        return stats
    
    def reconcile_daily_summary(self) -> Dict[str, Any]:
        """
        Generate daily reconciliation summary.
        
        Returns:
            Dictionary with daily reconciliation statistics
        """
        today = datetime.now().date()
        
        # Get today's transactions
        today_transactions = self.transaction_repository.get_by_date(today)
        
        # Calculate statistics
        stats = {
            'date': today.isoformat(),
            'total_transactions': len(today_transactions),
            'successful_transactions': sum(1 for t in today_transactions if t.status == UpiTransactionStatus.COMPLETED),
            'failed_transactions': sum(1 for t in today_transactions if t.status == UpiTransactionStatus.FAILED),
            'pending_transactions': sum(1 for t in today_transactions if t.status == UpiTransactionStatus.PENDING),
            'total_amount': sum(t.amount for t in today_transactions),
            'successful_amount': sum(t.amount for t in today_transactions if t.status == UpiTransactionStatus.COMPLETED),
            'abnormal_transactions': []
        }
        
        # Identify abnormal transactions (e.g., unusually high amounts)
        average_amount = (stats['total_amount'] / stats['total_transactions']) if stats['total_transactions'] > 0 else 0
        threshold = average_amount * 5  # 5x the average amount is considered abnormal
        
        abnormal_transactions = [
            {
                'transaction_id': str(t.transaction_id),
                'amount': t.amount,
                'sender': t.sender_vpa,
                'receiver': t.receiver_vpa,
                'status': t.status.value,
                'time': t.transaction_date.isoformat()
            }
            for t in today_transactions
            if t.amount > threshold and t.amount > 10000  # At least ₹10,000 and 5x average
        ]
        
        stats['abnormal_transactions'] = abnormal_transactions
        stats['abnormal_count'] = len(abnormal_transactions)
        
        self.logger.info(f"Generated daily reconciliation summary for {today.isoformat()}")
        return stats
    
    def detect_suspicious_activities(self) -> List[Dict[str, Any]]:
        """
        Detect suspicious transaction activities.
        
        Returns:
            List of suspicious transactions with their details
        """
        suspicious_activities = []
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        # Get recent transactions
        recent_transactions = self.transaction_repository.get_by_date_range(yesterday, today)
        
        # Organize transactions by VPA
        vpa_transactions = {}
        for transaction in recent_transactions:
            sender_vpa = transaction.sender_vpa
            if sender_vpa not in vpa_transactions:
                vpa_transactions[sender_vpa] = []
            vpa_transactions[sender_vpa].append(transaction)
        
        # Analyze patterns for each VPA
        for vpa, transactions in vpa_transactions.items():
            # Check for unusually high frequency
            if len(transactions) > 20:  # More than 20 transactions in 24 hours
                suspicious_activities.append({
                    'vpa': vpa,
                    'type': 'HIGH_FREQUENCY',
                    'count': len(transactions),
                    'transactions': [str(t.transaction_id) for t in transactions]
                })
            
            # Check for multiple failed transactions
            failed_transactions = [t for t in transactions if t.status == UpiTransactionStatus.FAILED]
            if len(failed_transactions) >= 5:  # 5 or more failed transactions
                suspicious_activities.append({
                    'vpa': vpa,
                    'type': 'MULTIPLE_FAILURES',
                    'count': len(failed_transactions),
                    'transactions': [str(t.transaction_id) for t in failed_transactions]
                })
            
            # Check for large transactions immediately after small ones (testing pattern)
            if len(transactions) >= 3:
                sorted_transactions = sorted(transactions, key=lambda t: t.transaction_date)
                for i in range(len(sorted_transactions) - 1):
                    current = sorted_transactions[i]
                    next_transaction = sorted_transactions[i+1]
                    time_diff = (next_transaction.transaction_date - current.transaction_date).total_seconds()
                    
                    # If small amount followed quickly by large amount
                    if (time_diff < 300  # Less than 5 minutes apart
                            and current.amount < 100  # Small amount
                            and next_transaction.amount > 5000  # Large amount
                            and current.status == UpiTransactionStatus.COMPLETED):
                        suspicious_activities.append({
                            'vpa': vpa,
                            'type': 'TEST_THEN_LARGE',
                            'test_transaction': str(current.transaction_id),
                            'large_transaction': str(next_transaction.transaction_id),
                            'time_diff_seconds': time_diff,
                            'small_amount': current.amount,
                            'large_amount': next_transaction.amount
                        })
        
        self.logger.info(f"Detected {len(suspicious_activities)} suspicious activities")
        return suspicious_activities
