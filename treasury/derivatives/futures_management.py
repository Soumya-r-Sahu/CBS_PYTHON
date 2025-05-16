"""
Futures contract management module for treasury operations.

This module provides functionality for managing futures contracts,
including tracking positions, valuations, and risk metrics.
"""

import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Union, Tuple
from decimal import Decimal
import logging
import uuid
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)


class FuturesType(Enum):
    """Types of futures contracts."""
    INTEREST_RATE = "interest_rate"
    CURRENCY = "currency"
    EQUITY_INDEX = "equity_index"
    COMMODITY = "commodity"
    BOND = "bond"


class MarginType(Enum):
    """Types of margins for futures."""
    INITIAL = "initial"
    VARIATION = "variation"
    MAINTENANCE = "maintenance"


@dataclass
class FuturesContract:
    """Represents a futures contract."""
    
    ticker: str  # Exchange ticker symbol
    contract_month: str  # Format: MMM-YY (e.g., "DEC-23")
    futures_type: FuturesType
    exchange: str
    tick_size: Decimal  # Minimum price movement
    tick_value: Decimal  # Value of one tick
    contract_size: int  # Size of one contract
    currency: str
    expiry_date: datetime.date
    first_notice_date: Optional[datetime.date] = None
    last_trading_date: Optional[datetime.date] = None
    delivery_type: str = "Cash"  # "Cash" or "Physical"
    
    @property
    def days_to_expiry(self) -> int:
        """Calculate days until expiration."""
        return max(0, (self.expiry_date - datetime.date.today()).days)
    
    @property
    def contract_code(self) -> str:
        """Generate the full contract code."""
        return f"{self.ticker} {self.contract_month}"
    
    @property
    def is_expired(self) -> bool:
        """Check if the contract is expired."""
        return datetime.date.today() > self.expiry_date
    
    @property
    def is_approaching_notice(self) -> bool:
        """Check if contract is approaching notice date."""
        if not self.first_notice_date:
            return False
            
        days_to_notice = (self.first_notice_date - datetime.date.today()).days
        return 0 < days_to_notice <= 5  # Within 5 days of notice
    
    @property
    def is_approaching_expiry(self) -> bool:
        """Check if contract is approaching expiry date."""
        days = self.days_to_expiry
        return 0 < days <= 5  # Within 5 days of expiry


@dataclass
class FuturesPosition:
    """Represents a position in a futures contract."""
    
    id: str
    contract: FuturesContract
    quantity: int  # Positive for long, negative for short
    average_entry_price: Decimal
    current_price: Decimal
    initial_margin: Decimal
    variation_margin: Decimal = Decimal("0")
    trade_date: datetime.date = field(default_factory=datetime.date.today)
    last_updated: datetime.datetime = field(default_factory=datetime.datetime.now)
    notes: Optional[str] = None
    
    def __post_init__(self):
        """Initialize with defaults if needed."""
        if not self.id:
            self.id = str(uuid.uuid4())
    
    @property
    def direction(self) -> str:
        """Get the position direction."""
        return "Long" if self.quantity > 0 else "Short" if self.quantity < 0 else "Flat"
    
    @property
    def notional_value(self) -> Decimal:
        """Calculate notional value of the position."""
        return abs(self.quantity) * self.contract.contract_size * self.current_price
    
    @property
    def unrealized_pnl(self) -> Decimal:
        """Calculate unrealized profit/loss."""
        price_diff = self.current_price - self.average_entry_price
        contract_value = self.contract.contract_size * price_diff
        return self.quantity * contract_value
    
    @property
    def margin_requirement(self) -> Decimal:
        """Calculate total margin requirement."""
        return self.initial_margin + self.variation_margin
    
    def update_price(self, price: Decimal) -> None:
        """
        Update current price and timestamp.
        
        Args:
            price: Current market price
        """
        self.current_price = price
        self.last_updated = datetime.datetime.now()


@dataclass
class MarginCall:
    """Represents a margin call for a futures position."""
    
    id: str
    position_id: str
    call_date: datetime.date
    call_type: MarginType
    amount: Decimal
    due_date: datetime.date
    is_satisfied: bool = False
    satisfied_date: Optional[datetime.date] = None
    notes: Optional[str] = None


class FuturesManager:
    """
    Futures contract manager.
    
    This class provides functionality for tracking and managing
    futures contracts and positions.
    """
    
    def __init__(self):
        """Initialize the futures manager."""
        self.contracts: Dict[str, FuturesContract] = {}
        self.positions: Dict[str, FuturesPosition] = {}
        self.margin_calls: Dict[str, MarginCall] = {}
        self.trades: List[Dict] = []
        
    def add_contract(self, contract: FuturesContract) -> None:
        """
        Add a futures contract.
        
        Args:
            contract: Futures contract
        """
        key = contract.contract_code
        self.contracts[key] = contract
        logger.info(f"Added futures contract {key} expiring on {contract.expiry_date}")
        
    def get_contract(self, contract_code: str) -> Optional[FuturesContract]:
        """
        Get a futures contract by code.
        
        Args:
            contract_code: Contract code
            
        Returns:
            Futures contract if found, None otherwise
        """
        return self.contracts.get(contract_code)
        
    def add_position(self, position: FuturesPosition) -> None:
        """
        Add a futures position.
        
        Args:
            position: Futures position
        """
        self.positions[position.id] = position
        
        # Record trade in history
        self.trades.append({
            "timestamp": datetime.datetime.now(),
            "position_id": position.id,
            "contract_code": position.contract.contract_code,
            "quantity": position.quantity,
            "price": float(position.average_entry_price),
            "action": "Open",
            "notional_value": float(position.notional_value)
        })
        
        logger.info(f"Added {position.direction} position of {abs(position.quantity)} " +
                    f"{position.contract.contract_code} contracts at {position.average_entry_price}")
        
    def get_position(self, position_id: str) -> Optional[FuturesPosition]:
        """
        Get a position by ID.
        
        Args:
            position_id: Position ID
            
        Returns:
            Futures position if found, None otherwise
        """
        return self.positions.get(position_id)
        
    def close_position(self, position_id: str, exit_price: Decimal) -> Optional[Decimal]:
        """
        Close a futures position.
        
        Args:
            position_id: Position ID
            exit_price: Exit price
            
        Returns:
            Realized profit/loss or None if position not found
        """
        position = self.get_position(position_id)
        
        if not position:
            logger.warning(f"Position {position_id} not found")
            return None
            
        # Calculate P&L
        price_diff = exit_price - position.average_entry_price
        contract_value = position.contract.contract_size * price_diff
        realized_pnl = position.quantity * contract_value
        
        # Record trade in history
        self.trades.append({
            "timestamp": datetime.datetime.now(),
            "position_id": position_id,
            "contract_code": position.contract.contract_code,
            "quantity": -position.quantity,  # Opposite sign to close
            "price": float(exit_price),
            "action": "Close",
            "realized_pnl": float(realized_pnl),
            "notional_value": float(abs(position.quantity) * position.contract.contract_size * exit_price)
        })
        
        # Remove position
        del self.positions[position_id]
        
        logger.info(f"Closed position {position_id} at {exit_price}, " +
                    f"realized P&L: {realized_pnl}")
        
        return realized_pnl
        
    def update_position_price(self, position_id: str, price: Decimal) -> Optional[Decimal]:
        """
        Update the current price of a position.
        
        Args:
            position_id: Position ID
            price: Current market price
            
        Returns:
            New unrealized P&L or None if position not found
        """
        position = self.get_position(position_id)
        
        if not position:
            logger.warning(f"Position {position_id} not found")
            return None
            
        old_pnl = position.unrealized_pnl
        position.update_price(price)
        new_pnl = position.unrealized_pnl
        
        # Calculate variation margin
        pnl_change = new_pnl - old_pnl
        position.variation_margin += pnl_change
        
        return new_pnl
        
    def register_margin_call(self, 
                           position_id: str,
                           call_type: MarginType,
                           amount: Decimal,
                           due_date: Optional[datetime.date] = None) -> Optional[str]:
        """
        Register a margin call for a position.
        
        Args:
            position_id: Position ID
            call_type: Type of margin call
            amount: Amount required
            due_date: Due date (defaults to next business day)
            
        Returns:
            Margin call ID or None if position not found
        """
        position = self.get_position(position_id)
        
        if not position:
            logger.warning(f"Position {position_id} not found")
            return None
            
        # Set default due date to next business day
        if not due_date:
            due_date = self._get_next_business_day(datetime.date.today())
            
        # Create margin call
        call_id = str(uuid.uuid4())
        call = MarginCall(
            id=call_id,
            position_id=position_id,
            call_date=datetime.date.today(),
            call_type=call_type,
            amount=amount,
            due_date=due_date
        )
        
        self.margin_calls[call_id] = call
        
        logger.info(f"Registered {call_type.value} margin call for {amount} on position {position_id}")
        
        return call_id
        
    def satisfy_margin_call(self, call_id: str) -> bool:
        """
        Mark a margin call as satisfied.
        
        Args:
            call_id: Margin call ID
            
        Returns:
            True if successful, False if call not found
        """
        if call_id not in self.margin_calls:
            logger.warning(f"Margin call {call_id} not found")
            return False
            
        call = self.margin_calls[call_id]
        call.is_satisfied = True
        call.satisfied_date = datetime.date.today()
        
        # Update position's variation margin if applicable
        if call.call_type == MarginType.VARIATION:
            position = self.get_position(call.position_id)
            if position:
                position.variation_margin = Decimal("0")  # Reset variation margin
                
        logger.info(f"Satisfied margin call {call_id}")
        
        return True
        
    def get_open_positions(self) -> List[FuturesPosition]:
        """
        Get all open positions.
        
        Returns:
            List of open positions
        """
        return list(self.positions.values())
        
    def get_open_positions_by_type(self, futures_type: FuturesType) -> List[FuturesPosition]:
        """
        Get open positions by futures type.
        
        Args:
            futures_type: Type of futures contract
            
        Returns:
            List of matching positions
        """
        return [p for p in self.positions.values() 
                if p.contract.futures_type == futures_type]
        
    def get_open_margin_calls(self) -> List[MarginCall]:
        """
        Get all unsatisfied margin calls.
        
        Returns:
            List of open margin calls
        """
        return [call for call in self.margin_calls.values() if not call.is_satisfied]
        
    def get_margin_calls_by_position(self, position_id: str) -> List[MarginCall]:
        """
        Get all margin calls for a position.
        
        Args:
            position_id: Position ID
            
        Returns:
            List of margin calls
        """
        return [call for call in self.margin_calls.values() 
                if call.position_id == position_id]
        
    def calculate_portfolio_margin(self) -> Dict[str, Decimal]:
        """
        Calculate total margin requirements for the portfolio.
        
        Returns:
            Dictionary with margin totals by type
        """
        totals = {
            "initial": Decimal("0"),
            "variation": Decimal("0"),
            "total": Decimal("0")
        }
        
        for position in self.positions.values():
            totals["initial"] += position.initial_margin
            totals["variation"] += position.variation_margin
            
        totals["total"] = totals["initial"] + totals["variation"]
        
        return totals
        
    def calculate_portfolio_value(self) -> Dict[str, Union[Decimal, float]]:
        """
        Calculate total portfolio value and metrics.
        
        Returns:
            Dictionary with portfolio metrics
        """
        totals = {
            "notional_value": Decimal("0"),
            "unrealized_pnl": Decimal("0"),
            "position_count": len(self.positions),
            "long_value": Decimal("0"),
            "short_value": Decimal("0")
        }
        
        for position in self.positions.values():
            totals["notional_value"] += position.notional_value
            totals["unrealized_pnl"] += position.unrealized_pnl
            
            if position.quantity > 0:
                totals["long_value"] += position.notional_value
            else:
                totals["short_value"] += position.notional_value
                
        return totals
        
    def calculate_portfolio_exposure(self) -> Dict[str, Dict[str, Decimal]]:
        """
        Calculate portfolio exposure by futures type and contract.
        
        Returns:
            Dictionary mapping futures types to exposure details
        """
        exposures = {}
        
        for position in self.positions.values():
            futures_type = position.contract.futures_type.value
            contract_code = position.contract.contract_code
            
            if futures_type not in exposures:
                exposures[futures_type] = {
                    "notional_value": Decimal("0"),
                    "long_value": Decimal("0"),
                    "short_value": Decimal("0"),
                    "contracts": {}
                }
                
            exposure = exposures[futures_type]
            exposure["notional_value"] += position.notional_value
            
            if position.quantity > 0:
                exposure["long_value"] += position.notional_value
            else:
                exposure["short_value"] += position.notional_value
                
            if contract_code not in exposure["contracts"]:
                exposure["contracts"][contract_code] = {
                    "notional_value": Decimal("0"),
                    "quantity": 0
                }
                
            exposure["contracts"][contract_code]["notional_value"] += position.notional_value
            exposure["contracts"][contract_code]["quantity"] += position.quantity
            
        return exposures
        
    def calculate_portfolio_risk(self, price_changes: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate portfolio risk given price changes.
        
        Args:
            price_changes: Dictionary mapping contract codes to price changes (as percentages)
            
        Returns:
            Dictionary with risk metrics
        """
        base_value = sum(float(p.notional_value) for p in self.positions.values())
        new_value = 0.0
        
        for position in self.positions.values():
            contract_code = position.contract.contract_code
            current_price = float(position.current_price)
            
            # Apply price change if specified, otherwise assume no change
            if contract_code in price_changes:
                change = price_changes[contract_code]
                new_price = current_price * (1 + change)
            else:
                new_price = current_price
                
            # Calculate new position value
            new_position_value = abs(position.quantity) * position.contract.contract_size * new_price
            new_value += new_position_value
            
        # Calculate impact
        value_change = new_value - base_value
        percentage_change = value_change / base_value if base_value > 0 else 0.0
        
        return {
            "base_value": base_value,
            "stressed_value": new_value,
            "absolute_change": value_change,
            "percentage_change": percentage_change * 100  # Convert to percentage
        }
        
    def get_expiring_contracts(self, days_threshold: int = 30) -> List[FuturesContract]:
        """
        Get contracts expiring within a specified number of days.
        
        Args:
            days_threshold: Number of days threshold
            
        Returns:
            List of contracts expiring within the threshold
        """
        today = datetime.date.today()
        threshold = today + datetime.timedelta(days=days_threshold)
        
        return [c for c in self.contracts.values() 
                if c.expiry_date <= threshold]
        
    def find_hedge_opportunity(self, 
                             target_exposure: Dict[FuturesType, Decimal]) -> Dict[str, any]:
        """
        Find opportunities to hedge exposures based on target.
        
        Args:
            target_exposure: Dictionary mapping futures types to target exposures
            
        Returns:
            Dictionary with hedge recommendations
        """
        # Calculate current exposures
        current_exposure = {}
        for position in self.positions.values():
            futures_type = position.contract.futures_type
            exposure = position.notional_value * (1 if position.quantity > 0 else -1)
            
            if futures_type in current_exposure:
                current_exposure[futures_type] += exposure
            else:
                current_exposure[futures_type] = exposure
                
        # Find differences and recommend hedges
        recommendations = {
            "hedges_needed": [],
            "current_exposure": {k.value: float(v) for k, v in current_exposure.items()}
        }
        
        for futures_type, target in target_exposure.items():
            current = current_exposure.get(futures_type, Decimal("0"))
            diff = target - current
            
            if abs(diff) > Decimal("0.01"):  # Material difference
                # Find suitable contracts for hedging
                suitable_contracts = [
                    c for c in self.contracts.values()
                    if c.futures_type == futures_type and not c.is_expired
                ]
                
                # Sort by days to expiry (ascending)
                suitable_contracts.sort(key=lambda c: c.days_to_expiry)
                
                if suitable_contracts:
                    contract = suitable_contracts[0]
                    
                    # Calculate required position
                    contract_value = contract.contract_size * contract.tick_value * 100  # Approximate
                    quantity_needed = int(diff / Decimal(str(contract_value)))
                    
                    if quantity_needed != 0:
                        recommendations["hedges_needed"].append({
                            "futures_type": futures_type.value,
                            "current_exposure": float(current),
                            "target_exposure": float(target),
                            "exposure_gap": float(diff),
                            "recommended_contract": contract.contract_code,
                            "quantity_needed": quantity_needed,
                            "direction": "Long" if quantity_needed > 0 else "Short",
                            "approximate_value": float(abs(diff))
                        })
        
        return recommendations
    
    def create_position(self,
                      contract_code: str,
                      quantity: int,
                      entry_price: Decimal,
                      initial_margin: Decimal) -> Optional[FuturesPosition]:
        """
        Create a new futures position.
        
        Args:
            contract_code: Contract code
            quantity: Position quantity (positive for long, negative for short)
            entry_price: Entry price
            initial_margin: Initial margin requirement
            
        Returns:
            Created position or None if contract not found
        """
        contract = self.get_contract(contract_code)
        
        if not contract:
            logger.warning(f"Contract {contract_code} not found")
            return None
            
        # Create position
        position = FuturesPosition(
            id=str(uuid.uuid4()),
            contract=contract,
            quantity=quantity,
            average_entry_price=entry_price,
            current_price=entry_price,
            initial_margin=initial_margin
        )
        
        self.add_position(position)
        
        return position
    
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


# Example usage
if __name__ == "__main__":
    # Create futures manager
    manager = FuturesManager()
    
    # Create some futures contracts
    today = datetime.date.today()
    
    # Treasury futures
    tn_future = FuturesContract(
        ticker="ZT",
        contract_month="MAR-24",
        futures_type=FuturesType.INTEREST_RATE,
        exchange="CBOT",
        tick_size=Decimal("0.0078125"),  # 1/128 of a point
        tick_value=Decimal("15.625"),    # Value of one tick
        contract_size=100000,            # $100,000 face value
        currency="USD",
        expiry_date=datetime.date(2024, 3, 20)
    )
    
    manager.add_contract(tn_future)
    
    # Eurodollar futures
    euro_future = FuturesContract(
        ticker="GE",
        contract_month="JUN-24",
        futures_type=FuturesType.INTEREST_RATE,
        exchange="CME",
        tick_size=Decimal("0.0025"),    # 1/4 of a basis point
        tick_value=Decimal("6.25"),     # $6.25 per tick
        contract_size=1000000,          # $1,000,000 face value
        currency="USD",
        expiry_date=datetime.date(2024, 6, 17)
    )
    
    manager.add_contract(euro_future)
    
    # Create positions
    position1 = manager.create_position(
        contract_code="ZT MAR-24",
        quantity=10,  # Long 10 contracts
        entry_price=Decimal("108.25"),
        initial_margin=Decimal("5000")  # $5,000 initial margin
    )
    
    position2 = manager.create_position(
        contract_code="GE JUN-24",
        quantity=-5,  # Short 5 contracts
        entry_price=Decimal("97.50"),
        initial_margin=Decimal("2500")  # $2,500 initial margin
    )
    
    # Update prices (simulate market movement)
    manager.update_position_price(position1.id, Decimal("108.50"))  # Price up
    manager.update_position_price(position2.id, Decimal("97.45"))   # Price down (good for short)
    
    # Calculate portfolio metrics
    portfolio_value = manager.calculate_portfolio_value()
    print(f"Portfolio value: {float(portfolio_value['notional_value']):,.2f}")
    print(f"Unrealized P&L: {float(portfolio_value['unrealized_pnl']):,.2f}")
    
    # Calculate exposures
    exposures = manager.calculate_portfolio_exposure()
    print("\nExposures by type:")
    for futures_type, data in exposures.items():
        print(f"  {futures_type}: {float(data['notional_value']):,.2f} " +
              f"(Long: {float(data['long_value']):,.2f}, Short: {float(data['short_value']):,.2f})")
        
    # Register a margin call
    if float(position1.unrealized_pnl) < 0:
        call_id = manager.register_margin_call(
            position1.id,
            MarginType.VARIATION,
            abs(position1.unrealized_pnl)
        )
        
        # Later satisfy the call
        if call_id:
            manager.satisfy_margin_call(call_id)
    
    # Close position
    pnl = manager.close_position(position2.id, Decimal("97.40"))
    if pnl:
        print(f"\nClosed position with realized P&L: {float(pnl):,.2f}")
    
    # Calculate portfolio margin
    margin = manager.calculate_portfolio_margin()
    print(f"\nMargin requirements: Initial={float(margin['initial']):,.2f}, " +
          f"Variation={float(margin['variation']):,.2f}, Total={float(margin['total']):,.2f}")
    
    # Calculate portfolio risk
    risk = manager.calculate_portfolio_risk({"ZT MAR-24": 0.01})  # 1% increase
    print(f"\nRisk analysis (1% price increase):")
    print(f"  Base value: {risk['base_value']:,.2f}")
    print(f"  Stressed value: {risk['stressed_value']:,.2f}")
    print(f"  Value change: {risk['absolute_change']:,.2f} ({risk['percentage_change']:.2f}%)")
