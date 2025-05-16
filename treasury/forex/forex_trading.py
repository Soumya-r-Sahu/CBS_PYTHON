"""
Foreign exchange trading operations for treasury module.

This module provides functionality for executing and managing foreign exchange
trading operations, including spot, forward, and swap transactions.
"""

import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Union, Tuple
from decimal import Decimal
import logging
import uuid

# Configure logging
logger = logging.getLogger(__name__)


class TradeStatus(Enum):
    """Status of a foreign exchange trade."""
    PENDING = "pending"
    EXECUTED = "executed"
    SETTLED = "settled"
    CANCELLED = "cancelled"
    FAILED = "failed"


class TradeType(Enum):
    """Type of foreign exchange trade."""
    SPOT = "spot"
    FORWARD = "forward"
    SWAP = "swap"
    NDF = "non-deliverable-forward"


@dataclass
class FxTrade:
    """Represents a foreign exchange trade."""
    
    id: str
    trade_date: datetime.date
    trade_type: TradeType
    buy_currency: str
    sell_currency: str
    buy_amount: Decimal
    sell_amount: Decimal
    exchange_rate: Decimal
    value_date: datetime.date  # Settlement date
    status: TradeStatus
    counterparty: str
    trader_id: str
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    notes: Optional[str] = None
    settlement_id: Optional[str] = None
    
    def __post_init__(self):
        """Validate trade data and set defaults."""
        if not self.id:
            self.id = str(uuid.uuid4())
            
        # Validate amounts
        if self.buy_amount <= 0:
            raise ValueError("Buy amount must be positive")
        if self.sell_amount <= 0:
            raise ValueError("Sell amount must be positive")
            
        # Validate dates
        if self.value_date < self.trade_date:
            raise ValueError("Value date must be on or after trade date")


class FxTradeManager:
    """
    Manager for foreign exchange trading operations.
    
    This class handles the execution, tracking, and settlement of
    foreign exchange trades.
    """
    
    def __init__(self):
        """Initialize the foreign exchange trade manager."""
        self.trades: Dict[str, FxTrade] = {}
        self.trade_history: List[Dict] = []
    
    def create_trade(self, 
                    trade_type: TradeType, 
                    buy_currency: str, 
                    sell_currency: str,
                    buy_amount: Decimal, 
                    sell_amount: Decimal, 
                    exchange_rate: Decimal,
                    value_date: datetime.date, 
                    counterparty: str, 
                    trader_id: str,
                    notes: Optional[str] = None) -> FxTrade:
        """
        Create a new foreign exchange trade.
        
        Args:
            trade_type: Type of trade (spot, forward, swap, NDF)
            buy_currency: Currency being purchased
            sell_currency: Currency being sold
            buy_amount: Amount of currency being purchased
            sell_amount: Amount of currency being sold
            exchange_rate: Exchange rate for the trade
            value_date: Settlement date for the trade
            counterparty: Name of the counterparty
            trader_id: ID of the trader executing the trade
            notes: Optional notes about the trade
            
        Returns:
            The created trade object
        """
        # Create trade object
        trade = FxTrade(
            id=str(uuid.uuid4()),
            trade_date=datetime.date.today(),
            trade_type=trade_type,
            buy_currency=buy_currency,
            sell_currency=sell_currency,
            buy_amount=buy_amount,
            sell_amount=sell_amount,
            exchange_rate=exchange_rate,
            value_date=value_date,
            status=TradeStatus.PENDING,
            counterparty=counterparty,
            trader_id=trader_id,
            notes=notes
        )
        
        # Store the trade
        self.trades[trade.id] = trade
        
        # Add to history
        self._add_trade_history(trade, "created", f"Trade created by {trader_id}")
        
        logger.info(f"Created {trade_type.value} trade {trade.id}: "
                  f"{sell_amount} {sell_currency} -> {buy_amount} {buy_currency}")
        
        return trade
    
    def execute_trade(self, trade_id: str, execution_notes: Optional[str] = None) -> bool:
        """
        Execute a pending trade.
        
        Args:
            trade_id: ID of the trade to execute
            execution_notes: Optional notes about the execution
            
        Returns:
            True if execution was successful, False otherwise
        """
        if trade_id not in self.trades:
            logger.warning(f"Trade {trade_id} not found")
            return False
            
        trade = self.trades[trade_id]
        
        if trade.status != TradeStatus.PENDING:
            logger.warning(f"Trade {trade_id} is not in pending status, current status: {trade.status.value}")
            return False
            
        # Update trade status
        trade.status = TradeStatus.EXECUTED
        
        # Add to history
        self._add_trade_history(trade, "executed", execution_notes or "Trade executed")
        
        logger.info(f"Executed trade {trade_id}")
        return True
    
    def settle_trade(self, trade_id: str, settlement_id: Optional[str] = None) -> bool:
        """
        Settle an executed trade.
        
        Args:
            trade_id: ID of the trade to settle
            settlement_id: Optional settlement reference ID
            
        Returns:
            True if settlement was successful, False otherwise
        """
        if trade_id not in self.trades:
            logger.warning(f"Trade {trade_id} not found")
            return False
            
        trade = self.trades[trade_id]
        
        if trade.status != TradeStatus.EXECUTED:
            logger.warning(f"Trade {trade_id} is not in executed status, current status: {trade.status.value}")
            return False
            
        # Update trade status
        trade.status = TradeStatus.SETTLED
        if settlement_id:
            trade.settlement_id = settlement_id
        
        # Add to history
        self._add_trade_history(
            trade, 
            "settled", 
            f"Trade settled{f' with reference {settlement_id}' if settlement_id else ''}"
        )
        
        logger.info(f"Settled trade {trade_id}")
        return True
    
    def cancel_trade(self, trade_id: str, reason: str) -> bool:
        """
        Cancel a trade.
        
        Args:
            trade_id: ID of the trade to cancel
            reason: Reason for cancellation
            
        Returns:
            True if cancellation was successful, False otherwise
        """
        if trade_id not in self.trades:
            logger.warning(f"Trade {trade_id} not found")
            return False
            
        trade = self.trades[trade_id]
        
        if trade.status in [TradeStatus.SETTLED, TradeStatus.CANCELLED, TradeStatus.FAILED]:
            logger.warning(f"Cannot cancel trade {trade_id}, current status: {trade.status.value}")
            return False
            
        # Update trade status
        trade.status = TradeStatus.CANCELLED
        
        # Add to history
        self._add_trade_history(trade, "cancelled", f"Trade cancelled: {reason}")
        
        logger.info(f"Cancelled trade {trade_id}: {reason}")
        return True
    
    def get_trade(self, trade_id: str) -> Optional[FxTrade]:
        """
        Get a trade by ID.
        
        Args:
            trade_id: ID of the trade to retrieve
            
        Returns:
            Trade object if found, None otherwise
        """
        return self.trades.get(trade_id)
    
    def get_trades_by_status(self, status: TradeStatus) -> List[FxTrade]:
        """
        Get all trades with a specific status.
        
        Args:
            status: Status to filter by
            
        Returns:
            List of matching trades
        """
        return [trade for trade in self.trades.values() if trade.status == status]
    
    def get_trades_by_date_range(self, 
                               start_date: datetime.date, 
                               end_date: datetime.date) -> List[FxTrade]:
        """
        Get all trades within a date range.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            List of matching trades
        """
        return [
            trade for trade in self.trades.values() 
            if start_date <= trade.trade_date <= end_date
        ]
    
    def get_trades_by_currency_pair(self, 
                                  currency_1: str, 
                                  currency_2: str) -> List[FxTrade]:
        """
        Get all trades involving a specific currency pair.
        
        Args:
            currency_1: First currency code
            currency_2: Second currency code
            
        Returns:
            List of matching trades
        """
        return [
            trade for trade in self.trades.values() 
            if ((trade.buy_currency == currency_1 and trade.sell_currency == currency_2) or 
                (trade.buy_currency == currency_2 and trade.sell_currency == currency_1))
        ]
    
    def get_pending_settlements(self, days_ahead: int = 5) -> List[FxTrade]:
        """
        Get trades with upcoming settlement dates.
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List of trades requiring settlement
        """
        today = datetime.date.today()
        end_date = today + datetime.timedelta(days=days_ahead)
        
        return [
            trade for trade in self.trades.values()
            if (trade.status == TradeStatus.EXECUTED and today <= trade.value_date <= end_date)
        ]
    
    def get_trade_history(self, trade_id: str) -> List[Dict]:
        """
        Get the history of a specific trade.
        
        Args:
            trade_id: ID of the trade
            
        Returns:
            List of historical events for the trade
        """
        return [event for event in self.trade_history if event["trade_id"] == trade_id]
    
    def _add_trade_history(self, trade: FxTrade, event_type: str, description: str) -> None:
        """
        Add an event to the trade history.
        
        Args:
            trade: The trade object
            event_type: Type of event (created, executed, settled, etc.)
            description: Description of the event
        """
        event = {
            "timestamp": datetime.datetime.now(),
            "trade_id": trade.id,
            "event_type": event_type,
            "description": description,
            "status": trade.status.value,
            "user_id": trade.trader_id
        }
        
        self.trade_history.append(event)
    
    def calculate_trade_metrics(self, 
                              start_date: Optional[datetime.date] = None, 
                              end_date: Optional[datetime.date] = None) -> Dict[str, Union[int, Decimal]]:
        """
        Calculate trading metrics for a period.
        
        Args:
            start_date: Start date (default: beginning of month)
            end_date: End date (default: today)
            
        Returns:
            Dictionary of trading metrics
        """
        # Set default dates
        if not end_date:
            end_date = datetime.date.today()
            
        if not start_date:
            # Default to beginning of month
            start_date = datetime.date(end_date.year, end_date.month, 1)
            
        # Filter trades in date range
        period_trades = self.get_trades_by_date_range(start_date, end_date)
        
        # Basic metrics
        total_trades = len(period_trades)
        executed_trades = len([t for t in period_trades if t.status in [TradeStatus.EXECUTED, TradeStatus.SETTLED]])
        cancelled_trades = len([t for t in period_trades if t.status == TradeStatus.CANCELLED])
        
        # Trading volume by currency
        buy_volume = {}
        sell_volume = {}
        
        for trade in period_trades:
            if trade.status in [TradeStatus.EXECUTED, TradeStatus.SETTLED]:
                # Track buy volume
                if trade.buy_currency in buy_volume:
                    buy_volume[trade.buy_currency] += trade.buy_amount
                else:
                    buy_volume[trade.buy_currency] = trade.buy_amount
                    
                # Track sell volume
                if trade.sell_currency in sell_volume:
                    sell_volume[trade.sell_currency] += trade.sell_amount
                else:
                    sell_volume[trade.sell_currency] = trade.sell_amount
        
        # Trade type distribution
        trade_types = {}
        for trade in period_trades:
            type_name = trade.trade_type.value
            if type_name in trade_types:
                trade_types[type_name] += 1
            else:
                trade_types[type_name] = 1
                
        return {
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "total_trades": total_trades,
            "executed_trades": executed_trades,
            "cancelled_trades": cancelled_trades,
            "buy_volume": {k: float(v) for k, v in buy_volume.items()},
            "sell_volume": {k: float(v) for k, v in sell_volume.items()},
            "trade_types": trade_types
        }
    
    def generate_trade_report(self, 
                            start_date: datetime.date, 
                            end_date: datetime.date,
                            format: str = 'dict') -> Union[Dict, str]:
        """
        Generate a comprehensive trade report.
        
        Args:
            start_date: Start date for the report
            end_date: End date for the report
            format: Output format ('dict', 'json', or 'text')
            
        Returns:
            Report in the specified format
        """
        import json
        
        # Get trades for the period
        trades = self.get_trades_by_date_range(start_date, end_date)
        
        # Calculate metrics
        metrics = self.calculate_trade_metrics(start_date, end_date)
        
        # Trading pairs summary
        pairs = {}
        for trade in trades:
            pair = f"{trade.sell_currency}/{trade.buy_currency}"
            if pair in pairs:
                pairs[pair] += 1
            else:
                pairs[pair] = 1
                
        # Counterparty summary
        counterparties = {}
        for trade in trades:
            if trade.counterparty in counterparties:
                counterparties[trade.counterparty] += 1
            else:
                counterparties[trade.counterparty] = 1
                
        # Build report
        report = {
            "report_title": f"FX Trading Report: {start_date.isoformat()} to {end_date.isoformat()}",
            "generated_at": datetime.datetime.now().isoformat(),
            "metrics": metrics,
            "currency_pairs": pairs,
            "counterparties": counterparties,
            "trades": [
                {
                    "id": t.id,
                    "trade_date": t.trade_date.isoformat(),
                    "trade_type": t.trade_type.value,
                    "buy_currency": t.buy_currency,
                    "sell_currency": t.sell_currency,
                    "buy_amount": float(t.buy_amount),
                    "sell_amount": float(t.sell_amount),
                    "exchange_rate": float(t.exchange_rate),
                    "value_date": t.value_date.isoformat(),
                    "status": t.status.value,
                    "counterparty": t.counterparty,
                    "trader_id": t.trader_id
                }
                for t in trades
            ]
        }
        
        # Format output
        if format.lower() == 'json':
            return json.dumps(report, indent=2)
        elif format.lower() == 'text':
            # Simple text format
            text = []
            text.append(report["report_title"])
            text.append("=" * len(report["report_title"]))
            text.append(f"Generated: {report['generated_at']}")
            text.append("")
            text.append("Summary:")
            text.append(f"- Period: {metrics['period_start']} to {metrics['period_end']}")
            text.append(f"- Total trades: {metrics['total_trades']}")
            text.append(f"- Executed trades: {metrics['executed_trades']}")
            text.append(f"- Cancelled trades: {metrics['cancelled_trades']}")
            text.append("")
            text.append("Top Currency Pairs:")
            for pair, count in sorted(pairs.items(), key=lambda x: x[1], reverse=True)[:5]:
                text.append(f"- {pair}: {count} trades")
            text.append("")
            text.append("Top Counterparties:")
            for cp, count in sorted(counterparties.items(), key=lambda x: x[1], reverse=True)[:5]:
                text.append(f"- {cp}: {count} trades")
            
            return "\n".join(text)
        else:  # dict
            return report


# Example usage
if __name__ == "__main__":
    # Create trade manager
    manager = FxTradeManager()
    
    # Create a spot trade
    spot_trade = manager.create_trade(
        trade_type=TradeType.SPOT,
        buy_currency="EUR",
        sell_currency="USD",
        buy_amount=Decimal("100000"),
        sell_amount=Decimal("108000"),
        exchange_rate=Decimal("1.08"),
        value_date=datetime.date.today() + datetime.timedelta(days=2),
        counterparty="Bank of Europe",
        trader_id="jsmith",
        notes="Regular liquidity management"
    )
    
    # Create a forward trade
    forward_trade = manager.create_trade(
        trade_type=TradeType.FORWARD,
        buy_currency="GBP",
        sell_currency="USD",
        buy_amount=Decimal("200000"),
        sell_amount=Decimal("250000"),
        exchange_rate=Decimal("1.25"),
        value_date=datetime.date.today() + datetime.timedelta(days=90),
        counterparty="London Financial",
        trader_id="jsmith",
        notes="Hedge for Q3 expenses"
    )
    
    # Execute the trades
    manager.execute_trade(spot_trade.id, "Executed at market")
    manager.execute_trade(forward_trade.id, "Executed as per dealing ticket #12345")
    
    # Settle the spot trade
    manager.settle_trade(spot_trade.id, "REF98765")
    
    # Generate a report
    today = datetime.date.today()
    start_of_month = datetime.date(today.year, today.month, 1)
    
    report = manager.generate_trade_report(start_of_month, today, format='text')
    print(report)
