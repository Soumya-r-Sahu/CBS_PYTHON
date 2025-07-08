"""
Forex Settlement module for treasury operations.

This module provides functionality for managing the settlement process
for foreign exchange transactions, including netting, confirmation,
and settlement tracking.
"""

import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from decimal import Decimal
import logging
import uuid

# Configure logging
logger = logging.getLogger(__name__)


class SettlementStatus(Enum):
    """Status of a settlement."""
    PENDING = "pending"
    CONFIRMED = "confirmed" 
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Settlement:
    """Represents a forex settlement."""
    
    id: str
    settlement_date: datetime.date
    counterparty: str
    trade_ids: List[str]
    settlements_by_currency: Dict[str, Decimal]
    status: SettlementStatus
    reference_number: Optional[str] = None
    confirmation_id: Optional[str] = None
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    notes: Optional[str] = None

    def __post_init__(self):
        """Initialize with defaults if needed."""
        if not self.id:
            self.id = str(uuid.uuid4())
    
    @property
    def net_settlement_value(self) -> Decimal:
        """Calculate sum of absolute settlement values across all currencies."""
        return sum(abs(amount) for amount in self.settlements_by_currency.values())
    
    @property
    def currency_count(self) -> int:
        """Get the number of currencies in this settlement."""
        return len(self.settlements_by_currency)


class FxSettlementManager:
    """
    Manager for foreign exchange settlements.
    
    This class handles the process of settlement for forex trades,
    including netting, confirmation, and settlement tracking.
    """
    
    def __init__(self):
        """Initialize the forex settlement manager."""
        self.settlements: Dict[str, Settlement] = {}
        self.settlement_history: List[Dict] = []
        
    def create_settlement(self,
                        settlement_date: datetime.date,
                        counterparty: str,
                        trade_ids: List[str],
                        settlements_by_currency: Dict[str, Decimal],
                        reference_number: Optional[str] = None,
                        notes: Optional[str] = None) -> Settlement:
        """
        Create a new settlement.
        
        Args:
            settlement_date: Date of settlement
            counterparty: Name of counterparty
            trade_ids: List of trade IDs involved
            settlements_by_currency: Dictionary mapping currency codes to net amounts
            reference_number: Optional external reference number
            notes: Optional notes
            
        Returns:
            The created settlement
        """
        settlement = Settlement(
            id=str(uuid.uuid4()),
            settlement_date=settlement_date,
            counterparty=counterparty,
            trade_ids=trade_ids.copy(),
            settlements_by_currency=settlements_by_currency.copy(),
            status=SettlementStatus.PENDING,
            reference_number=reference_number,
            notes=notes
        )
        
        self.settlements[settlement.id] = settlement
        
        self._add_settlement_history(
            settlement, 
            "created", 
            f"Settlement created for {len(trade_ids)} trades with {counterparty}"
        )
        
        logger.info(f"Created settlement {settlement.id} for {counterparty} on {settlement_date}")
        return settlement
        
    def confirm_settlement(self, settlement_id: str, 
                         confirmation_id: str) -> bool:
        """
        Confirm a pending settlement.
        
        Args:
            settlement_id: ID of the settlement to confirm
            confirmation_id: Confirmation ID from counterparty
            
        Returns:
            True if confirmation was successful
        """
        if settlement_id not in self.settlements:
            logger.warning(f"Settlement {settlement_id} not found")
            return False
            
        settlement = self.settlements[settlement_id]
        
        if settlement.status != SettlementStatus.PENDING:
            logger.warning(f"Settlement {settlement_id} is not pending (status: {settlement.status.value})")
            return False
            
        # Update settlement
        settlement.status = SettlementStatus.CONFIRMED
        settlement.confirmation_id = confirmation_id
        settlement.updated_at = datetime.datetime.now()
        
        self._add_settlement_history(
            settlement, 
            "confirmed", 
            f"Settlement confirmed with ID: {confirmation_id}"
        )
        
        logger.info(f"Confirmed settlement {settlement_id} with confirmation ID {confirmation_id}")
        return True
        
    def start_settlement_processing(self, settlement_id: str) -> bool:
        """
        Start processing a confirmed settlement.
        
        Args:
            settlement_id: ID of the settlement to process
            
        Returns:
            True if processing was started successfully
        """
        if settlement_id not in self.settlements:
            logger.warning(f"Settlement {settlement_id} not found")
            return False
            
        settlement = self.settlements[settlement_id]
        
        if settlement.status != SettlementStatus.CONFIRMED:
            logger.warning(f"Settlement {settlement_id} is not confirmed (status: {settlement.status.value})")
            return False
            
        # Update settlement
        settlement.status = SettlementStatus.IN_PROGRESS
        settlement.updated_at = datetime.datetime.now()
        
        self._add_settlement_history(
            settlement, 
            "processing_started", 
            "Settlement processing initiated"
        )
        
        logger.info(f"Started processing settlement {settlement_id}")
        return True
        
    def complete_settlement(self, settlement_id: str, notes: Optional[str] = None) -> bool:
        """
        Mark a settlement as completed.
        
        Args:
            settlement_id: ID of the settlement to complete
            notes: Optional notes about completion
            
        Returns:
            True if completion was successful
        """
        if settlement_id not in self.settlements:
            logger.warning(f"Settlement {settlement_id} not found")
            return False
            
        settlement = self.settlements[settlement_id]
        
        if settlement.status != SettlementStatus.IN_PROGRESS:
            logger.warning(f"Settlement {settlement_id} is not in progress (status: {settlement.status.value})")
            return False
            
        # Update settlement
        settlement.status = SettlementStatus.COMPLETED
        settlement.updated_at = datetime.datetime.now()
        
        if notes:
            settlement.notes = (settlement.notes or "") + "\n" + notes if settlement.notes else notes
        
        self._add_settlement_history(
            settlement, 
            "completed", 
            f"Settlement completed{f': {notes}' if notes else ''}"
        )
        
        logger.info(f"Completed settlement {settlement_id}")
        return True
        
    def fail_settlement(self, settlement_id: str, reason: str) -> bool:
        """
        Mark a settlement as failed.
        
        Args:
            settlement_id: ID of the settlement that failed
            reason: Reason for failure
            
        Returns:
            True if failure was recorded successfully
        """
        if settlement_id not in self.settlements:
            logger.warning(f"Settlement {settlement_id} not found")
            return False
            
        settlement = self.settlements[settlement_id]
        
        if settlement.status in [SettlementStatus.COMPLETED, SettlementStatus.FAILED, SettlementStatus.CANCELLED]:
            logger.warning(f"Settlement {settlement_id} cannot be failed (status: {settlement.status.value})")
            return False
            
        # Update settlement
        settlement.status = SettlementStatus.FAILED
        settlement.updated_at = datetime.datetime.now()
        settlement.notes = (settlement.notes or "") + f"\nFAILURE: {reason}" if settlement.notes else f"FAILURE: {reason}"
        
        self._add_settlement_history(
            settlement, 
            "failed", 
            f"Settlement failed: {reason}"
        )
        
        logger.info(f"Settlement {settlement_id} failed: {reason}")
        return True
        
    def cancel_settlement(self, settlement_id: str, reason: str) -> bool:
        """
        Cancel a settlement.
        
        Args:
            settlement_id: ID of the settlement to cancel
            reason: Reason for cancellation
            
        Returns:
            True if cancellation was successful
        """
        if settlement_id not in self.settlements:
            logger.warning(f"Settlement {settlement_id} not found")
            return False
            
        settlement = self.settlements[settlement_id]
        
        if settlement.status in [SettlementStatus.COMPLETED, SettlementStatus.FAILED, SettlementStatus.CANCELLED]:
            logger.warning(f"Settlement {settlement_id} cannot be cancelled (status: {settlement.status.value})")
            return False
            
        # Update settlement
        settlement.status = SettlementStatus.CANCELLED
        settlement.updated_at = datetime.datetime.now()
        settlement.notes = (settlement.notes or "") + f"\nCANCELLED: {reason}" if settlement.notes else f"CANCELLED: {reason}"
        
        self._add_settlement_history(
            settlement, 
            "cancelled", 
            f"Settlement cancelled: {reason}"
        )
        
        logger.info(f"Cancelled settlement {settlement_id}: {reason}")
        return True
        
    def get_settlement(self, settlement_id: str) -> Optional[Settlement]:
        """
        Get a settlement by ID.
        
        Args:
            settlement_id: ID of the settlement
            
        Returns:
            Settlement if found, None otherwise
        """
        return self.settlements.get(settlement_id)
        
    def get_settlements_by_status(self, status: SettlementStatus) -> List[Settlement]:
        """
        Get all settlements with a specific status.
        
        Args:
            status: Status to filter by
            
        Returns:
            List of matching settlements
        """
        return [s for s in self.settlements.values() if s.status == status]
        
    def get_settlements_by_date_range(self,
                                    start_date: datetime.date,
                                    end_date: datetime.date) -> List[Settlement]:
        """
        Get all settlements within a date range.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            List of matching settlements
        """
        return [
            s for s in self.settlements.values()
            if start_date <= s.settlement_date <= end_date
        ]
        
    def get_settlements_by_counterparty(self, counterparty: str) -> List[Settlement]:
        """
        Get all settlements with a specific counterparty.
        
        Args:
            counterparty: Counterparty name
            
        Returns:
            List of matching settlements
        """
        return [
            s for s in self.settlements.values()
            if s.counterparty == counterparty
        ]
        
    def get_settlements_by_trade(self, trade_id: str) -> List[Settlement]:
        """
        Get all settlements that include a specific trade.
        
        Args:
            trade_id: Trade ID
            
        Returns:
            List of matching settlements
        """
        return [
            s for s in self.settlements.values()
            if trade_id in s.trade_ids
        ]
        
    def get_settlement_history(self, settlement_id: str) -> List[Dict]:
        """
        Get the history of a settlement.
        
        Args:
            settlement_id: Settlement ID
            
        Returns:
            List of historical events
        """
        return [
            event for event in self.settlement_history
            if event["settlement_id"] == settlement_id
        ]
        
    def _add_settlement_history(self, 
                              settlement: Settlement, 
                              event_type: str, 
                              description: str) -> None:
        """
        Add an event to the settlement history.
        
        Args:
            settlement: Settlement object
            event_type: Type of event
            description: Event description
        """
        event = {
            "timestamp": datetime.datetime.now(),
            "settlement_id": settlement.id,
            "event_type": event_type,
            "description": description,
            "status": settlement.status.value
        }
        
        self.settlement_history.append(event)
        
    def create_netted_settlement(self, 
                               trade_ids: List[str],
                               trade_details: List[Dict],
                               counterparty: str,
                               settlement_date: Optional[datetime.date] = None) -> Optional[Settlement]:
        """
        Create a settlement with netted amounts across trades.
        
        Args:
            trade_ids: List of trade IDs to include
            trade_details: List of trade details with currency and amounts
                           [{"currency": "USD", "amount": Decimal("1000")}, ...]
            counterparty: Counterparty name
            settlement_date: Settlement date (default: next business day)
            
        Returns:
            Created settlement or None if no trades provided
        """
        if not trade_ids or not trade_details:
            logger.warning("No trades provided for settlement")
            return None
            
        # Set default settlement date to next business day
        if not settlement_date:
            settlement_date = self._get_next_business_day(datetime.date.today())
            
        # Net amounts by currency
        net_by_currency = {}
        
        for trade in trade_details:
            currency = trade["currency"]
            amount = trade["amount"]
            
            if currency in net_by_currency:
                net_by_currency[currency] += amount
            else:
                net_by_currency[currency] = amount
                
        # Remove zero balances
        net_by_currency = {curr: amt for curr, amt in net_by_currency.items() if amt != 0}
        
        if not net_by_currency:
            logger.warning("All amounts net to zero, no settlement needed")
            return None
            
        # Create the settlement
        settlement = self.create_settlement(
            settlement_date=settlement_date,
            counterparty=counterparty,
            trade_ids=trade_ids,
            settlements_by_currency=net_by_currency,
            notes=f"Netted settlement for {len(trade_ids)} trades"
        )
        
        logger.info(f"Created netted settlement {settlement.id} with {len(net_by_currency)} currencies")
        return settlement
        
    def _get_next_business_day(self, date: datetime.date) -> datetime.date:
        """
        Get the next business day after the given date.
        
        Args:
            date: Starting date
            
        Returns:
            Next business day
        """
        # Simple implementation - just skips weekends
        # In a real implementation, would also check holidays
        next_day = date + datetime.timedelta(days=1)
        
        # Skip weekend
        while next_day.weekday() >= 5:  # 5 is Saturday, 6 is Sunday
            next_day += datetime.timedelta(days=1)
            
        return next_day
        
    def generate_settlement_instructions(self, settlement_id: str) -> Dict:
        """
        Generate settlement instructions for a specific settlement.
        
        Args:
            settlement_id: Settlement ID
            
        Returns:
            Dictionary with settlement instructions
        """
        if settlement_id not in self.settlements:
            logger.warning(f"Settlement {settlement_id} not found")
            return {"error": "Settlement not found"}
            
        settlement = self.settlements[settlement_id]
        
        # Generate instructions
        instructions = {
            "settlement_id": settlement.id,
            "counterparty": settlement.counterparty,
            "settlement_date": settlement.settlement_date.isoformat(),
            "reference_number": settlement.reference_number,
            "confirmation_id": settlement.confirmation_id,
            "status": settlement.status.value,
            "payments": []
        }
        
        # Add payment instructions for each currency
        for currency, amount in settlement.settlements_by_currency.items():
            # Determine if this is a payment or receipt
            direction = "PAY" if amount < 0 else "RECEIVE"
            
            instructions["payments"].append({
                "currency": currency,
                "amount": abs(float(amount)),
                "direction": direction
            })
            
        return instructions
        
    def generate_settlement_report(self, 
                                 start_date: datetime.date,
                                 end_date: datetime.date,
                                 format: str = 'dict') -> Dict:
        """
        Generate a settlement report for a date range.
        
        Args:
            start_date: Start date
            end_date: End date
            format: Output format ('dict' or 'text')
            
        Returns:
            Settlement report
        """
        # Get settlements in date range
        settlements = self.get_settlements_by_date_range(start_date, end_date)
        
        # Count by status
        status_counts = {}
        for status in SettlementStatus:
            count = len([s for s in settlements if s.status == status])
            status_counts[status.value] = count
            
        # Sum by currency
        currencies = {}
        for settlement in settlements:
            for currency, amount in settlement.settlements_by_currency.items():
                if currency in currencies:
                    currencies[currency] += abs(amount)  # Use absolute value for volume
                else:
                    currencies[currency] = abs(amount)
                    
        # Counterparty summary
        counterparties = {}
        for settlement in settlements:
            cp = settlement.counterparty
            if cp in counterparties:
                counterparties[cp] += 1
            else:
                counterparties[cp] = 1
                
        # Build report
        report = {
            "report_title": f"FX Settlement Report: {start_date.isoformat()} to {end_date.isoformat()}",
            "generated_at": datetime.datetime.now().isoformat(),
            "total_settlements": len(settlements),
            "status_summary": status_counts,
            "currency_volume": {curr: float(amt) for curr, amt in currencies.items()},
            "counterparty_summary": counterparties,
            "settlements": [
                {
                    "id": s.id,
                    "date": s.settlement_date.isoformat(),
                    "counterparty": s.counterparty,
                    "status": s.status.value,
                    "trades": len(s.trade_ids),
                    "currencies": len(s.settlements_by_currency),
                    "value": float(s.net_settlement_value)
                }
                for s in settlements
            ]
        }
        
        if format.lower() == 'text':
            # Simple text format
            text = []
            text.append(report["report_title"])
            text.append("=" * len(report["report_title"]))
            text.append(f"Generated: {report['generated_at']}")
            text.append("")
            text.append(f"Total Settlements: {report['total_settlements']}")
            text.append("")
            text.append("Status Summary:")
            for status, count in report["status_summary"].items():
                if count > 0:
                    text.append(f"- {status.upper()}: {count}")
            text.append("")
            text.append("Currency Volume:")
            for curr, amount in sorted(report["currency_volume"].items(), key=lambda x: x[1], reverse=True):
                text.append(f"- {curr}: {amount:,.2f}")
            text.append("")
            text.append("Top Counterparties:")
            for cp, count in sorted(counterparties.items(), key=lambda x: x[1], reverse=True)[:5]:
                text.append(f"- {cp}: {count} settlements")
                
            return "\n".join(text)
        else:
            return report


# Example usage
if __name__ == "__main__":
    # Create settlement manager
    manager = FxSettlementManager()
    
    # Create some sample settlements
    today = datetime.date.today()
    
    # Settlement 1: Single currency
    settlement1 = manager.create_settlement(
        settlement_date=today + datetime.timedelta(days=2),
        counterparty="Bank of Europe",
        trade_ids=["trade1", "trade2"],
        settlements_by_currency={"EUR": Decimal("100000")},
        reference_number="REF123456"
    )
    
    # Settlement 2: Multiple currencies
    settlement2 = manager.create_settlement(
        settlement_date=today + datetime.timedelta(days=2),
        counterparty="London Financial",
        trade_ids=["trade3", "trade4", "trade5"],
        settlements_by_currency={
            "USD": Decimal("-50000"),
            "GBP": Decimal("40000")
        }
    )
    
    # Confirm and complete first settlement
    manager.confirm_settlement(settlement1.id, "CONF987654")
    manager.start_settlement_processing(settlement1.id)
    manager.complete_settlement(settlement1.id, "Settled via SWIFT")
    
    # Confirm second settlement
    manager.confirm_settlement(settlement2.id, "CONF654321")
    
    # Generate settlement instructions
    instructions = manager.generate_settlement_instructions(settlement2.id)
    print(f"Settlement instructions for {settlement2.id}:")
    for payment in instructions["payments"]:
        print(f"  {payment['direction']} {payment['amount']} {payment['currency']}")
    
    # Generate report
    report = manager.generate_settlement_report(
        today,
        today + datetime.timedelta(days=7),
        format='text'
    )
    print("\n" + report)
