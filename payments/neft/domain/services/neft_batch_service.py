"""
NEFT Batch Management domain service.
This service handles business rules for NEFT batch processing.
"""
from datetime import datetime, time, timedelta
from typing import List


class NEFTBatchService:
    """Domain service for NEFT batch operations."""
    
    def __init__(self, batch_times: List[str] = None, hold_minutes: int = 10):
        """
        Initialize the batch service.
        
        Args:
            batch_times: List of batch times in format HH:MM (24-hour format)
            hold_minutes: Minutes to hold transactions before including in a batch
        """
        self.batch_times = batch_times or ["00:30", "10:30", "13:30", "16:30"]
        self.hold_minutes = hold_minutes
    
    def calculate_next_batch_time(self) -> datetime:
        """
        Calculate the next available NEFT batch time.
        
        Returns:
            datetime: Next batch processing time
        """
        now = datetime.utcnow()
        hold_minutes = self.hold_minutes
        
        # Convert time strings to datetime objects for today
        batch_datetimes = []
        for batch_time_str in self.batch_times:
            hours, minutes = map(int, batch_time_str.split(":"))
            batch_dt = datetime.combine(now.date(), time(hours, minutes))
            
            # If batch time is in the past, use tomorrow
            if batch_dt <= now:
                batch_dt += timedelta(days=1)
                
            batch_datetimes.append(batch_dt)
        
        # Sort and find the next available time
        batch_datetimes.sort()
        next_time = batch_datetimes[0]
        
        # Add hold time
        effective_time = now + timedelta(minutes=hold_minutes)
        
        # If effective time is after the first batch, find the next one
        for batch_time in batch_datetimes:
            if batch_time >= effective_time:
                next_time = batch_time
                break
        
        return next_time
    
    def generate_batch_number(self, batch_time: datetime) -> str:
        """
        Generate a batch number based on the batch time.
        
        Args:
            batch_time: The batch processing time
            
        Returns:
            str: Batch number
        """
        return f"NEFT{batch_time.strftime('%Y%m%d%H%M')}"
