"""
Bond valuation and pricing module for treasury operations.

This module provides functionality for bond valuation, pricing, and yield calculations,
including yield curve modeling and interest rate risk assessment.
"""

import datetime
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from decimal import Decimal
import math
import numpy as np
from scipy import optimize
import logging

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class CashFlow:
    """Represents a future cash flow from a bond."""
    
    date: datetime.date
    amount: Decimal
    
    @property
    def years_from_now(self) -> float:
        """Calculate years between today and the cash flow date."""
        today = datetime.date.today()
        days = (self.date - today).days
        return days / 365.0

@dataclass
class YieldCurvePoint:
    """Point on a yield curve with maturity and yield."""
    
    maturity_years: float
    yield_rate: Decimal


class YieldCurve:
    """Represents the yield curve for a specific currency and date."""
    
    def __init__(self, currency: str, valuation_date: datetime.date):
        """
        Initialize a yield curve.
        
        Args:
            currency: Currency code (e.g., USD, EUR)
            valuation_date: Date for which the curve is valid
        """
        self.currency = currency
        self.valuation_date = valuation_date
        self.points: List[YieldCurvePoint] = []
        
    def add_point(self, maturity_years: float, yield_rate: Decimal) -> None:
        """
        Add a point to the yield curve.
        
        Args:
            maturity_years: Time to maturity in years
            yield_rate: Yield rate at the given maturity
        """
        point = YieldCurvePoint(maturity_years=maturity_years, yield_rate=yield_rate)
        self.points.append(point)
        # Sort points by maturity to ensure interpolation works correctly
        self.points.sort(key=lambda p: p.maturity_years)
    
    def get_yield(self, maturity_years: float) -> Decimal:
        """
        Get the yield for a specific maturity by interpolation.
        
        Args:
            maturity_years: Time to maturity in years
            
        Returns:
            Interpolated yield at the given maturity
        """
        if not self.points:
            raise ValueError("Yield curve contains no points")
            
        # Check if maturity is below the shortest point
        if maturity_years <= self.points[0].maturity_years:
            return self.points[0].yield_rate
            
        # Check if maturity is beyond the longest point
        if maturity_years >= self.points[-1].maturity_years:
            return self.points[-1].yield_rate
            
        # Find surrounding points for interpolation
        for i in range(len(self.points) - 1):
            point1 = self.points[i]
            point2 = self.points[i + 1]
            
            if point1.maturity_years <= maturity_years <= point2.maturity_years:
                # Linear interpolation
                t = (maturity_years - point1.maturity_years) / (point2.maturity_years - point1.maturity_years)
                interpolated = point1.yield_rate + t * (point2.yield_rate - point1.yield_rate)
                return interpolated
                
        # Fallback (should not reach here)
        return self.points[-1].yield_rate


class BondValuation:
    """Bond pricing and valuation functionality."""
    
    @staticmethod
    def calculate_cash_flows(
        issue_date: datetime.date,
        maturity_date: datetime.date,
        face_value: Decimal,
        coupon_rate: Decimal,
        payment_frequency: int
    ) -> List[CashFlow]:
        """
        Calculate all future cash flows for a bond.
        
        Args:
            issue_date: Bond issue date
            maturity_date: Bond maturity date
            face_value: Bond face value
            coupon_rate: Annual coupon rate as a percentage
            payment_frequency: Number of coupon payments per year
            
        Returns:
            List of cash flows
        """
        cash_flows = []
        
        # Coupon payment amount
        coupon_payment = (face_value * coupon_rate / 100) / payment_frequency
        
        # Calculate period between payments in months
        months_per_period = 12 // payment_frequency
        
        # Start from next coupon date after today
        today = datetime.date.today()
        next_coupon_date = issue_date
        
        # Find first coupon date after or on issue date
        while next_coupon_date < issue_date:
            next_coupon_date = BondValuation._add_months(next_coupon_date, months_per_period)
            
        # Find first coupon date after today
        while next_coupon_date < today:
            next_coupon_date = BondValuation._add_months(next_coupon_date, months_per_period)
        
        # Generate all future cash flows
        while next_coupon_date <= maturity_date:
            # Add coupon payment
            cash_flows.append(CashFlow(date=next_coupon_date, amount=coupon_payment))
            next_coupon_date = BondValuation._add_months(next_coupon_date, months_per_period)
            
        # Add final principal repayment (replace the last coupon payment with coupon + principal)
        if cash_flows:
            last_flow = cash_flows[-1]
            if last_flow.date == maturity_date:
                # Last flow is on maturity date, add principal to it
                cash_flows[-1] = CashFlow(date=last_flow.date, amount=last_flow.amount + face_value)
            else:
                # Add principal repayment
                cash_flows.append(CashFlow(date=maturity_date, amount=face_value))
        else:
            # No coupon payments, just principal
            cash_flows.append(CashFlow(date=maturity_date, amount=face_value))
            
        return cash_flows
            
    @staticmethod
    def _add_months(date: datetime.date, months: int) -> datetime.date:
        """Add months to a date, handling month end correctly."""
        month = date.month - 1 + months
        year = date.year + month // 12
        month = month % 12 + 1
        
        # Handle month end correctly
        last_day = BondValuation._last_day_of_month(year, month)
        day = min(date.day, last_day)
        
        return datetime.date(year, month, day)
        
    @staticmethod
    def _last_day_of_month(year: int, month: int) -> int:
        """Get the last day of the given month."""
        if month == 12:
            next_month = datetime.date(year + 1, 1, 1)
        else:
            next_month = datetime.date(year, month + 1, 1)
            
        return (next_month - datetime.timedelta(days=1)).day
    
    @staticmethod
    def price_bond_from_yield(
        cash_flows: List[CashFlow],
        yield_rate: Decimal,
        settlement_date: Optional[datetime.date] = None
    ) -> Decimal:
        """
        Calculate the price of a bond given its yield to maturity.
        
        Args:
            cash_flows: List of future cash flows
            yield_rate: Annual yield rate as a percentage
            settlement_date: Settlement date for the valuation (default: today)
            
        Returns:
            Bond price as a percentage of face value
        """
        if not cash_flows:
            return Decimal('0')
            
        settlement = settlement_date or datetime.date.today()
        total_pv = Decimal('0')
        
        # Convert yield to decimal form
        ytm = float(yield_rate) / 100
        
        # Calculate present value of each cash flow
        for cf in cash_flows:
            if cf.date < settlement:
                continue
                
            years = (cf.date - settlement).days / 365.0
            discount_factor = 1 / ((1 + ytm) ** years)
            pv = float(cf.amount) * discount_factor
            total_pv += Decimal(str(pv))
            
        # Normalize to percentage of face value (assuming last cash flow includes principal)
        face_value = cash_flows[-1].amount
        price_pct = (total_pv / face_value) * 100
        
        return price_pct.quantize(Decimal('0.01'))
        
    @staticmethod
    def calculate_yield_to_maturity(
        cash_flows: List[CashFlow],
        price: Decimal,
        face_value: Decimal,
        settlement_date: Optional[datetime.date] = None
    ) -> Decimal:
        """
        Calculate the yield to maturity of a bond given its price.
        
        Args:
            cash_flows: List of future cash flows
            price: Bond price as a percentage of face value
            face_value: Bond face value
            settlement_date: Settlement date for the valuation (default: today)
            
        Returns:
            Yield to maturity as a percentage
        """
        if not cash_flows:
            return Decimal('0')
            
        settlement = settlement_date or datetime.date.today()
        
        # Convert price to absolute value
        price_absolute = price * face_value / 100
        
        def npv_function(ytm):
            """Calculate NPV given a yield rate."""
            total = 0
            for cf in cash_flows:
                if cf.date < settlement:
                    continue
                
                years = (cf.date - settlement).days / 365.0
                discount_factor = 1 / ((1 + ytm) ** years)
                total += float(cf.amount) * discount_factor
            
            return total - float(price_absolute)
            
        # Find the yield that gives NPV = 0, starting with initial guess of 5%
        try:
            result = optimize.newton(npv_function, 0.05)
            # Convert to percentage
            ytm = Decimal(str(result * 100)).quantize(Decimal('0.001'))
            return ytm
        except:
            # Fallback to bisection method if Newton fails
            try:
                result = optimize.bisect(npv_function, -0.5, 1.0)
                ytm = Decimal(str(result * 100)).quantize(Decimal('0.001'))
                return ytm
            except:
                logger.error("Failed to calculate yield to maturity")
                return Decimal('0')
    
    @staticmethod
    def calculate_duration(
        cash_flows: List[CashFlow],
        yield_rate: Decimal,
        settlement_date: Optional[datetime.date] = None
    ) -> Tuple[Decimal, Decimal]:
        """
        Calculate Macaulay and Modified duration of a bond.
        
        Args:
            cash_flows: List of future cash flows
            yield_rate: Annual yield rate as a percentage
            settlement_date: Settlement date for the valuation (default: today)
            
        Returns:
            Tuple of (Macaulay duration, Modified duration)
        """
        if not cash_flows:
            return Decimal('0'), Decimal('0')
            
        settlement = settlement_date or datetime.date.today()
        
        # Convert yield to decimal
        ytm = float(yield_rate) / 100
        
        # Calculate price and weighted cash flows for duration
        price = 0
        weighted_time = 0
        
        for cf in cash_flows:
            if cf.date < settlement:
                continue
                
            years = (cf.date - settlement).days / 365.0
            discount_factor = 1 / ((1 + ytm) ** years)
            pv = float(cf.amount) * discount_factor
            
            price += pv
            weighted_time += pv * years
            
        if price == 0:
            return Decimal('0'), Decimal('0')
            
        # Macaulay duration
        macaulay_duration = Decimal(str(weighted_time / price))
        
        # Modified duration
        modified_duration = macaulay_duration / (1 + Decimal(str(ytm)))
        
        return macaulay_duration, modified_duration
        
    @staticmethod
    def calculate_convexity(
        cash_flows: List[CashFlow],
        yield_rate: Decimal,
        settlement_date: Optional[datetime.date] = None
    ) -> Decimal:
        """
        Calculate the convexity of a bond.
        
        Args:
            cash_flows: List of future cash flows
            yield_rate: Annual yield rate as a percentage
            settlement_date: Settlement date for the valuation (default: today)
            
        Returns:
            Bond convexity
        """
        if not cash_flows:
            return Decimal('0')
            
        settlement = settlement_date or datetime.date.today()
        
        # Convert yield to decimal
        ytm = float(yield_rate) / 100
        
        # Calculate price and weighted cash flows for convexity
        price = 0
        weighted_convexity = 0
        
        for cf in cash_flows:
            if cf.date < settlement:
                continue
                
            years = (cf.date - settlement).days / 365.0
            discount_factor = 1 / ((1 + ytm) ** years)
            pv = float(cf.amount) * discount_factor
            
            price += pv
            weighted_convexity += pv * years * (years + 1)
            
        if price == 0:
            return Decimal('0')
            
        # Calculate convexity
        convexity = Decimal(str(weighted_convexity / price / ((1 + ytm) ** 2)))
        
        return convexity
        
    @staticmethod
    def estimate_price_change(
        yield_change: Decimal,
        duration: Decimal,
        convexity: Decimal,
        price: Decimal
    ) -> Decimal:
        """
        Estimate the price change given a change in yield.
        
        Args:
            yield_change: Change in yield in percentage points
            duration: Modified duration
            convexity: Convexity
            price: Current price
            
        Returns:
            Estimated price change as a percentage
        """
        # Convert yield change to decimal (e.g., 0.01 for 1%)
        dy = float(yield_change) / 100
        
        # First-order approximation (duration effect)
        duration_effect = -float(duration) * dy
        
        # Second-order approximation (convexity effect)
        convexity_effect = 0.5 * float(convexity) * (dy ** 2)
        
        # Total price change as a percentage
        price_change_pct = Decimal(str(duration_effect + convexity_effect)) * 100
        
        return price_change_pct

# Example usage
if __name__ == "__main__":
    # Create a sample yield curve
    curve = YieldCurve("USD", datetime.date.today())
    curve.add_point(0.25, Decimal("3.95"))
    curve.add_point(0.50, Decimal("4.05"))
    curve.add_point(1.0, Decimal("4.15"))
    curve.add_point(2.0, Decimal("4.25"))
    curve.add_point(3.0, Decimal("4.30"))
    curve.add_point(5.0, Decimal("4.40"))
    curve.add_point(7.0, Decimal("4.45"))
    curve.add_point(10.0, Decimal("4.50"))
    curve.add_point(20.0, Decimal("4.60"))
    curve.add_point(30.0, Decimal("4.65"))
    
    # Calculate cash flows for a bond
    issue_date = datetime.date(2023, 1, 15)
    maturity_date = datetime.date(2033, 1, 15)
    face_value = Decimal("1000")
    coupon_rate = Decimal("4.50")
    
    cash_flows = BondValuation.calculate_cash_flows(
        issue_date, maturity_date, face_value, coupon_rate, 2
    )
    
    # Get yield from the curve
    maturity_years = (maturity_date - datetime.date.today()).days / 365
    bond_yield = curve.get_yield(maturity_years)
    print(f"Bond yield: {bond_yield}%")
    
    # Calculate bond price
    price = BondValuation.price_bond_from_yield(cash_flows, bond_yield)
    print(f"Bond price: {price}% of face value")
    
    # Calculate duration and convexity
    macaulay_duration, modified_duration = BondValuation.calculate_duration(
        cash_flows, bond_yield
    )
    convexity = BondValuation.calculate_convexity(cash_flows, bond_yield)
    
    print(f"Macaulay Duration: {macaulay_duration} years")
    print(f"Modified Duration: {modified_duration}")
    print(f"Convexity: {convexity}")
    
    # Estimate price change for a 0.25% yield increase
    price_change = BondValuation.estimate_price_change(
        Decimal("0.25"), modified_duration, convexity, price
    )
    print(f"Estimated price change for +0.25% yield: {price_change}%")
