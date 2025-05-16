"""
Bond portfolio management for treasury operations.

This module provides functionality for managing bond portfolios,
including position tracking, performance monitoring, and portfolio analytics.
"""

import datetime
from dataclasses import dataclass
from typing import List, Dict, Optional, Union
from decimal import Decimal
import logging
import uuid

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class Bond:
    """Represents a bond instrument."""
    
    id: str
    isin: str
    cusip: Optional[str]
    issuer: str
    issue_date: datetime.date
    maturity_date: datetime.date
    coupon_rate: Decimal
    face_value: Decimal
    currency: str
    bond_type: str  # government, corporate, municipal, etc.
    payment_frequency: int  # payments per year
    day_count_convention: str  # 30/360, actual/365, etc.
    
    def __post_init__(self):
        """Validate bond data and set defaults."""
        if not self.id:
            self.id = str(uuid.uuid4())
            
        # Validate dates
        if self.maturity_date <= self.issue_date:
            raise ValueError("Maturity date must be after issue date")
            
        # Validate coupon rate
        if self.coupon_rate < 0:
            raise ValueError("Coupon rate cannot be negative")

@dataclass
class BondPosition:
    """Represents a position in a bond."""
    
    bond: Bond
    quantity: int
    acquisition_date: datetime.date
    acquisition_price: Decimal
    acquisition_yield: Decimal
    
    @property
    def face_value_position(self) -> Decimal:
        """Calculate the total face value of the position."""
        return self.bond.face_value * self.quantity
        
    @property
    def acquisition_cost(self) -> Decimal:
        """Calculate the acquisition cost of the position."""
        return self.acquisition_price * self.quantity / 100 * self.bond.face_value


class BondPortfolio:
    """Manages a portfolio of bond positions."""
    
    def __init__(self, name: str, base_currency: str = "USD"):
        """
        Initialize a bond portfolio.
        
        Args:
            name: Portfolio name
            base_currency: Portfolio base currency
        """
        self.name = name
        self.base_currency = base_currency
        self.positions: Dict[str, BondPosition] = {}
        self.historical_valuations: Dict[datetime.date, Decimal] = {}
        self._creation_date = datetime.date.today()
        
    def add_position(self, position: BondPosition) -> None:
        """
        Add a bond position to the portfolio.
        
        Args:
            position: The bond position to add
        """
        bond_id = position.bond.id
        
        if bond_id in self.positions:
            # Calculate weighted average price if adding to existing position
            existing = self.positions[bond_id]
            total_quantity = existing.quantity + position.quantity
            weighted_price = ((existing.acquisition_price * existing.quantity) + 
                             (position.acquisition_price * position.quantity)) / total_quantity
                             
            # Create a new position with updated quantity and weighted price
            self.positions[bond_id] = BondPosition(
                bond=position.bond,
                quantity=total_quantity,
                acquisition_date=existing.acquisition_date,  # Keep original date
                acquisition_price=weighted_price,
                acquisition_yield=position.acquisition_yield  # Use latest yield as an approximation
            )
            
            logger.info(f"Updated position in bond {bond_id}, new quantity: {total_quantity}")
        else:
            # Add new position
            self.positions[bond_id] = position
            logger.info(f"Added new position in bond {bond_id}, quantity: {position.quantity}")
            
    def remove_position(self, bond_id: str, quantity: int) -> Optional[BondPosition]:
        """
        Remove a bond position from the portfolio.
        
        Args:
            bond_id: The ID of the bond
            quantity: The quantity to remove
            
        Returns:
            The removed position or None if not found
        """
        if bond_id not in self.positions:
            logger.warning(f"Cannot remove position: Bond {bond_id} not in portfolio")
            return None
            
        position = self.positions[bond_id]
        
        if quantity >= position.quantity:
            # Remove entire position
            removed = self.positions.pop(bond_id)
            logger.info(f"Removed entire position in bond {bond_id}")
            return removed
        else:
            # Reduce position quantity
            position.quantity -= quantity
            logger.info(f"Reduced position in bond {bond_id}, new quantity: {position.quantity}")
            
            # Return a new position object representing the removed portion
            return BondPosition(
                bond=position.bond,
                quantity=quantity,
                acquisition_date=position.acquisition_date,
                acquisition_price=position.acquisition_price,
                acquisition_yield=position.acquisition_yield
            )
            
    def calculate_portfolio_value(self, valuation_date: datetime.date, 
                                 market_prices: Dict[str, Decimal]) -> Decimal:
        """
        Calculate the total market value of the portfolio.
        
        Args:
            valuation_date: Date of valuation
            market_prices: Dictionary of bond prices (as percentage of face value)
            
        Returns:
            Total portfolio value
        """
        total_value = Decimal('0')
        
        for bond_id, position in self.positions.items():
            if bond_id in market_prices:
                price = market_prices[bond_id]
                value = position.quantity * position.bond.face_value * price / 100
                total_value += value
            else:
                logger.warning(f"No market price available for bond {bond_id}")
                
        # Store historical valuation
        self.historical_valuations[valuation_date] = total_value
        
        return total_value
        
    def get_bond_exposure_by_issuer(self) -> Dict[str, Decimal]:
        """
        Calculate bond exposure by issuer.
        
        Returns:
            Dictionary mapping issuer name to total exposure
        """
        exposure = {}
        
        for position in self.positions.values():
            issuer = position.bond.issuer
            value = position.face_value_position
            
            if issuer in exposure:
                exposure[issuer] += value
            else:
                exposure[issuer] = value
                
        return exposure
        
    def get_maturity_distribution(self) -> Dict[str, Decimal]:
        """
        Calculate bond exposure by maturity bucket.
        
        Returns:
            Dictionary mapping maturity buckets to total exposure
        """
        buckets = {
            "0-1Y": Decimal('0'),
            "1-3Y": Decimal('0'),
            "3-5Y": Decimal('0'),
            "5-7Y": Decimal('0'),
            "7-10Y": Decimal('0'),
            "10Y+": Decimal('0')
        }
        
        today = datetime.date.today()
        
        for position in self.positions.values():
            maturity = position.bond.maturity_date
            years_to_maturity = (maturity.year - today.year) + (maturity.month - today.month) / 12
            
            value = position.face_value_position
            
            if years_to_maturity <= 1:
                buckets["0-1Y"] += value
            elif years_to_maturity <= 3:
                buckets["1-3Y"] += value
            elif years_to_maturity <= 5:
                buckets["3-5Y"] += value
            elif years_to_maturity <= 7:
                buckets["5-7Y"] += value
            elif years_to_maturity <= 10:
                buckets["7-10Y"] += value
            else:
                buckets["10Y+"] += value
                
        return buckets
        
    def get_performance_summary(self, current_prices: Dict[str, Decimal]) -> Dict[str, Union[Decimal, float]]:
        """
        Calculate portfolio performance metrics.
        
        Args:
            current_prices: Dictionary of current bond prices
            
        Returns:
            Dictionary of performance metrics
        """
        total_face_value = Decimal('0')
        total_market_value = Decimal('0')
        total_cost = Decimal('0')
        
        for bond_id, position in self.positions.items():
            face_value = position.face_value_position
            total_face_value += face_value
            
            cost = position.acquisition_cost
            total_cost += cost
            
            if bond_id in current_prices:
                price = current_prices[bond_id]
                market_value = position.quantity * position.bond.face_value * price / 100
                total_market_value += market_value
                
        # Calculate performance metrics
        unrealized_gain_loss = total_market_value - total_cost
        if total_cost > 0:
            return_on_investment = float((unrealized_gain_loss / total_cost) * 100)
        else:
            return_on_investment = 0.0
            
        return {
            "total_face_value": total_face_value,
            "total_market_value": total_market_value,
            "total_cost": total_cost,
            "unrealized_gain_loss": unrealized_gain_loss,
            "return_on_investment_pct": return_on_investment
        }

# Example usage
if __name__ == "__main__":
    # Create a bond
    govt_bond = Bond(
        id="GB001",
        isin="US912810TW33",
        cusip="912810TW3",
        issuer="US Treasury",
        issue_date=datetime.date(2022, 2, 15),
        maturity_date=datetime.date(2052, 2, 15),
        coupon_rate=Decimal('2.25'),
        face_value=Decimal('1000'),
        currency="USD",
        bond_type="government",
        payment_frequency=2,
        day_count_convention="actual/actual"
    )
    
    # Create a bond position
    position = BondPosition(
        bond=govt_bond,
        quantity=100,
        acquisition_date=datetime.date(2022, 2, 20),
        acquisition_price=Decimal('98.5'),
        acquisition_yield=Decimal('2.35')
    )
    
    # Create a portfolio and add the position
    portfolio = BondPortfolio("Government Bonds", "USD")
    portfolio.add_position(position)
    
    # Calculate portfolio value
    market_prices = {
        "GB001": Decimal('97.25')
    }
    
    value = portfolio.calculate_portfolio_value(datetime.date.today(), market_prices)
    print(f"Portfolio value: ${value}")
    
    # Get performance summary
    performance = portfolio.get_performance_summary(market_prices)
    print(f"Performance: {performance}")
