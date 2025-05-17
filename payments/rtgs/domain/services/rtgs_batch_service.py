"""
RTGS Batch Management domain service.
This service handles business rules for RTGS batch processing.
"""
from datetime import datetime, time, timedelta
from typing import List


class RTGSBatchService:
    """Domain service for RTGS batch operations."""
    
    def __init__(self, operating_window: tuple = None, cutoff_time: str = None):
        """
        Initialize the batch service.
        
        Args:
            operating_window: Tuple of (start_hour, end_hour) for RTGS operating hours
            cutoff_time: Cutoff time for same-day processing in HH:MM format
        """
        # RTGS typically operates in a specific window (e.g., 9AM to 4:30PM)
        self.operating_window = operating_window or (9, 16, 30)  # 9AM to 4:30PM
        self.cutoff_time = cutoff_time or "16:00"  # 4PM cutoff
    
    def is_within_operating_hours(self, current_time: datetime = None) -> bool:
        """
        Check if current time is within RTGS operating hours.
        
        Args:
            current_time: Time to check (defaults to current time)
            
        Returns:
            bool: True if within operating hours, False otherwise
        """
        if not current_time:
            current_time = datetime.utcnow()
        
        # RTGS operates on weekdays only
        if current_time.weekday() > 4:  # 5=Saturday, 6=Sunday
            return False
        
        start_hour = self.operating_window[0]
        end_hour = self.operating_window[1]
        end_minute = self.operating_window[2] if len(self.operating_window) > 2 else 0
        
        # Check if current time is within operating window
        if current_time.hour < start_hour:
            return False
        
        if current_time.hour > end_hour or (current_time.hour == end_hour and current_time.minute > end_minute):
            return False
        
        return True
    
    def is_before_cutoff(self, current_time: datetime = None) -> bool:
        """
        Check if current time is before the cutoff for same-day processing.
        
        Args:
            current_time: Time to check (defaults to current time)
            
        Returns:
            bool: True if before cutoff, False otherwise
        """
        if not current_time:
            current_time = datetime.utcnow()
        
        cutoff_hour, cutoff_minute = map(int, self.cutoff_time.split(":"))
        cutoff_dt = datetime.combine(current_time.date(), time(cutoff_hour, cutoff_minute))
        
        return current_time < cutoff_dt
    
    def calculate_expected_settlement_time(self, transaction_time: datetime = None) -> datetime:
        """
        Calculate the expected settlement time for a transaction.
        
        Args:
            transaction_time: Time of transaction (defaults to current time)
            
        Returns:
            datetime: Expected settlement time
        """
        if not transaction_time:
            transaction_time = datetime.utcnow()
        
        # If within operating hours and before cutoff, settlement should be within 30 minutes
        if self.is_within_operating_hours(transaction_time) and self.is_before_cutoff(transaction_time):
            return transaction_time + timedelta(minutes=30)
        
        # If outside operating hours or after cutoff, calculate next business day
        next_business_day = transaction_time.date()
        
        # If after cutoff or weekend, move to next business day
        if not self.is_before_cutoff(transaction_time) or transaction_time.weekday() > 4:
            next_business_day += timedelta(days=1)
            
            # Skip weekends
            while next_business_day.weekday() > 4:
                next_business_day += timedelta(days=1)
        
        # Default to 10:00 AM of next business day
        return datetime.combine(next_business_day, time(10, 0))
    
    def generate_batch_number(self, batch_time: datetime) -> str:
        """
        Generate a batch number based on the batch time.
        
        Args:
            batch_time: The batch processing time
            
        Returns:
            str: Batch number
        """
        return f"RTGS{batch_time.strftime('%Y%m%d%H%M')}"
