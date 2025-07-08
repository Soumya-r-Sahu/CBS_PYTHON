"""
Currency Position Management for treasury operations.

This module provides functionality for tracking and managing currency positions,
monitoring foreign exchange risk, and generating position reports.
"""

import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union
from decimal import Decimal
import logging

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class CurrencyPosition:
    """Represents a position in a specific currency."""
    
    currency_code: str  # ISO currency code (e.g., USD, EUR)
    amount: Decimal     # Amount in the currency
    value_in_base: Decimal  # Value in base currency
    exchange_rate: Decimal  # Exchange rate to base currency
    last_updated: datetime.datetime = field(default_factory=datetime.datetime.now)
    
    @property
    def is_long(self) -> bool:
        """Whether the position is long (positive amount)."""
        return self.amount > 0
    
    @property
    def is_short(self) -> bool:
        """Whether the position is short (negative amount)."""
        return self.amount < 0


class CurrencyPositionManager:
    """
    Manages currency positions for the bank.
    
    This class tracks positions in different currencies, calculates
    exposure, and monitors compliance with position limits.
    """
    
    def __init__(self, base_currency: str = "USD"):
        """
        Initialize the currency position manager.
        
        Args:
            base_currency: The base currency for calculations
        """
        self.base_currency = base_currency
        self.positions: Dict[str, CurrencyPosition] = {}
        self.position_history: Dict[datetime.date, Dict[str, Decimal]] = {}
        self.position_limits: Dict[str, Dict[str, Decimal]] = {}
        self._last_updated = datetime.datetime.now()
        
    def set_position_limit(self, currency_code: str, 
                          intraday_limit: Decimal, 
                          overnight_limit: Decimal) -> None:
        """
        Set position limits for a currency.
        
        Args:
            currency_code: The currency code
            intraday_limit: Maximum intraday position (absolute value)
            overnight_limit: Maximum overnight position (absolute value)
        """
        self.position_limits[currency_code] = {
            "intraday": intraday_limit,
            "overnight": overnight_limit
        }
        logger.info(f"Set position limits for {currency_code}: "
                   f"Intraday={intraday_limit}, Overnight={overnight_limit}")
    
    def update_position(self, currency_code: str, 
                       amount: Decimal, 
                       exchange_rate: Decimal) -> None:
        """
        Update the position for a currency.
        
        Args:
            currency_code: The currency code
            amount: The amount to add to the position (can be negative)
            exchange_rate: Current exchange rate to base currency
        """
        if currency_code == self.base_currency:
            # For base currency, exchange rate is always 1
            exchange_rate = Decimal('1')
        
        # Calculate value in base currency
        value_in_base = amount * exchange_rate
        
        if currency_code in self.positions:
            # Update existing position
            old_position = self.positions[currency_code]
            new_amount = old_position.amount + amount
            new_value = old_position.value_in_base + value_in_base
            
            self.positions[currency_code] = CurrencyPosition(
                currency_code=currency_code,
                amount=new_amount,
                value_in_base=new_value,
                exchange_rate=exchange_rate
            )
        else:
            # Create new position
            self.positions[currency_code] = CurrencyPosition(
                currency_code=currency_code,
                amount=amount,
                value_in_base=value_in_base,
                exchange_rate=exchange_rate
            )
        
        self._last_updated = datetime.datetime.now()
        logger.debug(f"Updated {currency_code} position: {amount} "
                    f"(new total: {self.positions[currency_code].amount})")
        
        # Check for limit breaches
        self._check_limit_breach(currency_code)
        
    def set_position(self, currency_code: str, 
                    amount: Decimal, 
                    exchange_rate: Decimal) -> None:
        """
        Set the absolute position for a currency.
        
        Args:
            currency_code: The currency code
            amount: The total position amount
            exchange_rate: Current exchange rate to base currency
        """
        if currency_code == self.base_currency:
            # For base currency, exchange rate is always 1
            exchange_rate = Decimal('1')
        
        # Calculate value in base currency
        value_in_base = amount * exchange_rate
        
        self.positions[currency_code] = CurrencyPosition(
            currency_code=currency_code,
            amount=amount,
            value_in_base=value_in_base,
            exchange_rate=exchange_rate
        )
        
        self._last_updated = datetime.datetime.now()
        logger.debug(f"Set {currency_code} position to: {amount}")
        
        # Check for limit breaches
        self._check_limit_breach(currency_code)
    
    def _check_limit_breach(self, currency_code: str) -> Optional[Dict[str, Union[str, Decimal]]]:
        """
        Check if a position breaches defined limits.
        
        Args:
            currency_code: The currency code to check
            
        Returns:
            Breach information if limit breached, None otherwise
        """
        if currency_code not in self.positions or currency_code not in self.position_limits:
            return None
            
        position = self.positions[currency_code]
        limits = self.position_limits[currency_code]
        
        # Check against absolute value of position
        abs_position = abs(position.amount)
        
        # Check intraday limit
        if abs_position > limits["intraday"]:
            breach = {
                "currency": currency_code,
                "limit_type": "intraday",
                "position": position.amount,
                "limit": limits["intraday"],
                "breach_amount": abs_position - limits["intraday"]
            }
            logger.warning(f"POSITION LIMIT BREACH: {currency_code} "
                          f"intraday limit exceeded by {breach['breach_amount']}")
            return breach
            
        # Check overnight limit if it's end of day
        current_hour = datetime.datetime.now().hour
        if 18 <= current_hour <= 23:  # Assuming end of day is between 6pm and 11pm
            if abs_position > limits["overnight"]:
                breach = {
                    "currency": currency_code,
                    "limit_type": "overnight",
                    "position": position.amount,
                    "limit": limits["overnight"],
                    "breach_amount": abs_position - limits["overnight"]
                }
                logger.warning(f"POSITION LIMIT BREACH: {currency_code} "
                              f"overnight limit exceeded by {breach['breach_amount']}")
                return breach
        
        return None
    
    def record_daily_positions(self) -> None:
        """Record current positions for historical tracking."""
        today = datetime.date.today()
        daily_positions = {curr: pos.amount for curr, pos in self.positions.items()}
        self.position_history[today] = daily_positions
        logger.info(f"Recorded daily positions for {today}")
    
    def get_net_position(self) -> Decimal:
        """
        Get net position across all currencies in base currency.
        
        Returns:
            Net position in base currency
        """
        return sum(pos.value_in_base for pos in self.positions.values())
    
    def get_position_by_currency(self, currency_code: str) -> Optional[CurrencyPosition]:
        """
        Get position for a specific currency.
        
        Args:
            currency_code: The currency code
            
        Returns:
            Currency position or None if not found
        """
        return self.positions.get(currency_code)
    
    def get_all_positions(self) -> Dict[str, CurrencyPosition]:
        """
        Get all currency positions.
        
        Returns:
            Dictionary mapping currency codes to positions
        """
        return self.positions.copy()
    
    def get_position_summary(self) -> Dict[str, Union[str, Decimal, Dict]]:
        """
        Get a summary of current positions.
        
        Returns:
            Dictionary with position summary information
        """
        long_positions = {k: v for k, v in self.positions.items() if v.is_long}
        short_positions = {k: v for k, v in self.positions.items() if v.is_short}
        
        total_long = sum(pos.value_in_base for pos in long_positions.values())
        total_short = sum(pos.value_in_base for pos in short_positions.values())
        net_position = self.get_net_position()
        
        return {
            "base_currency": self.base_currency,
            "net_position": net_position,
            "total_long": total_long,
            "total_short": total_short,
            "last_updated": self._last_updated.isoformat(),
            "currencies": {
                curr: {
                    "amount": float(pos.amount),
                    "value_in_base": float(pos.value_in_base),
                    "exchange_rate": float(pos.exchange_rate)
                }
                for curr, pos in self.positions.items()
            }
        }

# Example usage
if __name__ == "__main__":
    # Create a position manager with USD as the base currency
    manager = CurrencyPositionManager("USD")
    
    # Set position limits
    manager.set_position_limit("EUR", Decimal("1000000"), Decimal("500000"))
    manager.set_position_limit("GBP", Decimal("800000"), Decimal("400000"))
    manager.set_position_limit("JPY", Decimal("50000000"), Decimal("25000000"))
    
    # Update positions
    manager.update_position("EUR", Decimal("200000"), Decimal("1.08"))
    manager.update_position("GBP", Decimal("150000"), Decimal("1.25"))
    manager.update_position("JPY", Decimal("20000000"), Decimal("0.0068"))
    
    # Print position summary
    summary = manager.get_position_summary()
    print(f"Net position in {summary['base_currency']}: {summary['net_position']}")
    
    for curr, details in summary["currencies"].items():
        print(f"{curr}: {details['amount']} (value: {details['value_in_base']} {summary['base_currency']})")
