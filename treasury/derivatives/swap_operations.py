"""
Swaps management module for treasury operations.

This module provides functionality for managing interest rate swaps,
currency swaps, and other swap derivatives, including valuation,
cash flow calculation, and risk assessment.
"""

import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Union, Tuple
from decimal import Decimal
import logging
import math
import numpy as np
from scipy import stats

# Configure logging
logger = logging.getLogger(__name__)


class SwapType(Enum):
    """Types of swap contracts."""
    INTEREST_RATE = "interest_rate"
    CURRENCY = "currency"
    CROSS_CURRENCY = "cross_currency"
    TOTAL_RETURN = "total_return"
    CREDIT_DEFAULT = "credit_default"
    COMMODITY = "commodity"
    EQUITY = "equity"


class PaymentFrequency(Enum):
    """Payment frequencies for swap contracts."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUALLY = "semi_annually"
    ANNUALLY = "annually"


class DayCountConvention(Enum):
    """Day count conventions for calculating interest payments."""
    ACT_360 = "actual/360"
    ACT_365 = "actual/365"
    THIRTY_360 = "30/360"
    ACT_ACT = "actual/actual"


@dataclass
class SwapLeg:
    """Represents a leg of a swap contract."""
    
    notional_amount: Decimal
    currency: str
    start_date: datetime.date
    end_date: datetime.date
    payment_frequency: PaymentFrequency
    day_count_convention: DayCountConvention
    is_fixed: bool
    rate: Union[Decimal, str]  # Fixed rate or reference rate (e.g., "SOFR", "EURIBOR")
    spread: Optional[Decimal] = None  # Spread over reference rate for floating legs
    payment_dates: List[datetime.date] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize payment dates if not provided."""
        if not self.payment_dates:
            self.payment_dates = self._generate_payment_dates()
    
    def _generate_payment_dates(self) -> List[datetime.date]:
        """Generate payment dates based on frequency."""
        dates = []
        current_date = self.start_date
        
        while current_date < self.end_date:
            # Add appropriate time based on frequency
            if self.payment_frequency == PaymentFrequency.MONTHLY:
                next_date = self._add_months(current_date, 1)
            elif self.payment_frequency == PaymentFrequency.QUARTERLY:
                next_date = self._add_months(current_date, 3)
            elif self.payment_frequency == PaymentFrequency.SEMI_ANNUALLY:
                next_date = self._add_months(current_date, 6)
            elif self.payment_frequency == PaymentFrequency.ANNUALLY:
                next_date = self._add_months(current_date, 12)
            elif self.payment_frequency == PaymentFrequency.WEEKLY:
                next_date = current_date + datetime.timedelta(days=7)
            elif self.payment_frequency == PaymentFrequency.DAILY:
                next_date = current_date + datetime.timedelta(days=1)
            else:
                next_date = self._add_months(current_date, 3)  # Default to quarterly
            
            # Ensure we don't go beyond end date
            if next_date > self.end_date:
                next_date = self.end_date
                
            if next_date > current_date:  # Avoid adding the same date twice
                dates.append(next_date)
                
            if next_date == self.end_date:
                break
                
            current_date = next_date
            
        return dates
    
    @staticmethod
    def _add_months(date: datetime.date, months: int) -> datetime.date:
        """Add specified number of months to a date."""
        month = date.month - 1 + months
        year = date.year + month // 12
        month = month % 12 + 1
        
        # Handle potential issues with days in month
        try:
            return date.replace(year=year, month=month)
        except ValueError:
            # Handle case where day is out of range for month
            # (e.g., January 31 + 1 month would be February 31, which doesn't exist)
            last_day = [31, 29 if SwapLeg._is_leap_year(year) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
            return date.replace(year=year, month=month, day=min(date.day, last_day[month-1]))
    
    @staticmethod
    def _is_leap_year(year: int) -> bool:
        """Check if a year is a leap year."""
        return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    
    def calculate_day_count_factor(self, start_date: datetime.date, end_date: datetime.date) -> float:
        """
        Calculate day count factor based on convention.
        
        Args:
            start_date: Start date for the period
            end_date: End date for the period
            
        Returns:
            Day count factor
        """
        days = (end_date - start_date).days
        
        if self.day_count_convention == DayCountConvention.ACT_360:
            return days / 360.0
        elif self.day_count_convention == DayCountConvention.ACT_365:
            return days / 365.0
        elif self.day_count_convention == DayCountConvention.THIRTY_360:
            # 30/360 convention calculation
            day1 = min(start_date.day, 30)
            day2 = min(end_date.day, 30) if day1 == 30 else end_date.day
            
            days_360 = (360 * (end_date.year - start_date.year) + 
                       30 * (end_date.month - start_date.month) + 
                       (day2 - day1))
            return days_360 / 360.0
        else:  # ACT_ACT
            # For actual/actual, consider leap years
            if start_date.year == end_date.year:
                return days / (366.0 if SwapLeg._is_leap_year(start_date.year) else 365.0)
            else:
                # Split calculation for days in different years
                result = 0
                current_date = start_date
                while current_date.year < end_date.year:
                    year_end = datetime.date(current_date.year, 12, 31)
                    days_in_year = (year_end - current_date).days + 1
                    result += days_in_year / (366.0 if SwapLeg._is_leap_year(current_date.year) else 365.0)
                    current_date = datetime.date(current_date.year + 1, 1, 1)
                    
                # Add days in final year
                if current_date <= end_date:
                    days_in_final_year = (end_date - current_date).days + 1
                    result += days_in_final_year / (366.0 if SwapLeg._is_leap_year(current_date.year) else 365.0)
                
                return result


@dataclass
class SwapContract:
    """Represents a swap contract."""
    
    id: str
    swap_type: SwapType
    effective_date: datetime.date
    maturity_date: datetime.date
    counterparty: str
    legs: List[SwapLeg]
    is_active: bool = True
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    
    @property
    def tenor(self) -> str:
        """Calculate tenor of the swap in years and months."""
        delta = self.maturity_date - self.effective_date
        years = delta.days // 365
        remaining_days = delta.days % 365
        months = round(remaining_days / 30)
        
        if months == 12:
            years += 1
            months = 0
            
        if years > 0 and months > 0:
            return f"{years}Y{months}M"
        elif years > 0:
            return f"{years}Y"
        else:
            return f"{months}M"
    
    @property
    def remaining_tenor(self) -> str:
        """Calculate remaining tenor of the swap."""
        today = datetime.date.today()
        
        if today > self.maturity_date:
            return "Expired"
            
        if today < self.effective_date:
            return self.tenor + " (Forward Start)"
            
        delta = self.maturity_date - today
        years = delta.days // 365
        remaining_days = delta.days % 365
        months = round(remaining_days / 30)
        
        if months == 12:
            years += 1
            months = 0
            
        if years > 0 and months > 0:
            return f"{years}Y{months}M"
        elif years > 0:
            return f"{years}Y"
        else:
            return f"{months}M"
    
    def get_next_payment_date(self) -> Optional[datetime.date]:
        """Get the next payment date across all legs."""
        today = datetime.date.today()
        next_dates = []
        
        for leg in self.legs:
            future_dates = [d for d in leg.payment_dates if d >= today]
            if future_dates:
                next_dates.append(min(future_dates))
                
        return min(next_dates) if next_dates else None
    
    def get_all_future_payment_dates(self) -> List[datetime.date]:
        """Get all future payment dates across all legs in ascending order."""
        today = datetime.date.today()
        future_dates = set()
        
        for leg in self.legs:
            future_dates.update([d for d in leg.payment_dates if d >= today])
                
        return sorted(future_dates)


class SwapPricingModel:
    """Base class for swap pricing models."""
    
    @staticmethod
    def calculate_interest_rate_swap_price(
        fixed_leg: SwapLeg,
        floating_leg: SwapLeg,
        yield_curve: Dict[str, float],
        current_floating_rate: float
    ) -> float:
        """
        Calculate the price (present value) of an interest rate swap.
        
        Args:
            fixed_leg: Fixed leg of the swap
            floating_leg: Floating leg of the swap
            yield_curve: Dictionary mapping tenors to yields
            current_floating_rate: Current value of the floating rate index
            
        Returns:
            Present value of the swap
        """
        if not fixed_leg.is_fixed or floating_leg.is_fixed:
            raise ValueError("Invalid leg configuration: first leg must be fixed, second must be floating")
            
        fixed_rate = float(fixed_leg.rate)
        notional = float(fixed_leg.notional_amount)
        
        # Calculate present values of both legs
        fixed_pv = SwapPricingModel._calculate_fixed_leg_pv(
            fixed_leg, yield_curve, notional, fixed_rate)
        
        floating_pv = SwapPricingModel._calculate_floating_leg_pv(
            floating_leg, yield_curve, notional, current_floating_rate, 
            float(floating_leg.spread or 0))
            
        # Return difference (from perspective of fixed rate payer)
        return floating_pv - fixed_pv
    
    @staticmethod
    def _calculate_fixed_leg_pv(
        leg: SwapLeg,
        yield_curve: Dict[str, float],
        notional: float,
        fixed_rate: float
    ) -> float:
        """Calculate present value of fixed leg payments."""
        today = datetime.date.today()
        pv = 0.0
        
        payment_dates = [d for d in leg.payment_dates if d >= today]
        previous_date = leg.start_date
        
        for payment_date in payment_dates:
            # Calculate days and discount factor
            days_in_period = (payment_date - previous_date).days
            years_to_payment = (payment_date - today).days / 365.0
            
            # Get discount factor from yield curve
            discount_factor = SwapPricingModel._get_discount_factor(yield_curve, years_to_payment)
            
            # Calculate payment amount
            day_count_factor = leg.calculate_day_count_factor(previous_date, payment_date)
            payment = notional * fixed_rate * day_count_factor
            
            # Calculate present value of this payment
            pv += payment * discount_factor
            
            previous_date = payment_date
            
        return pv
    
    @staticmethod
    def _calculate_floating_leg_pv(
        leg: SwapLeg,
        yield_curve: Dict[str, float],
        notional: float,
        current_rate: float,
        spread: float = 0.0
    ) -> float:
        """Calculate present value of floating leg payments."""
        today = datetime.date.today()
        pv = 0.0
        
        payment_dates = [d for d in leg.payment_dates if d >= today]
        previous_date = leg.start_date
        
        if not payment_dates:
            return 0.0
            
        # For first payment, we know the rate
        first_payment_date = payment_dates[0]
        years_to_payment = (first_payment_date - today).days / 365.0
        discount_factor = SwapPricingModel._get_discount_factor(yield_curve, years_to_payment)
        
        day_count_factor = leg.calculate_day_count_factor(previous_date, first_payment_date)
        payment = notional * (current_rate + spread) * day_count_factor
        pv += payment * discount_factor
        
        previous_date = first_payment_date
        
        # For remaining payments, derive from yield curve
        for i in range(1, len(payment_dates)):
            payment_date = payment_dates[i]
            
            # Derive forward rate from yield curve
            period_start_years = (previous_date - today).days / 365.0
            period_end_years = (payment_date - today).days / 365.0
            
            discount_start = SwapPricingModel._get_discount_factor(yield_curve, period_start_years)
            discount_end = SwapPricingModel._get_discount_factor(yield_curve, period_end_years)
            
            day_count_factor = leg.calculate_day_count_factor(previous_date, payment_date)
            
            # Calculate implied forward rate
            forward_rate = (discount_start / discount_end - 1) / day_count_factor
            
            # Calculate payment
            payment = notional * (forward_rate + spread) * day_count_factor
            
            # Calculate present value of this payment
            pv += payment * discount_end
            
            previous_date = payment_date
            
        return pv
    
    @staticmethod
    def _get_discount_factor(yield_curve: Dict[str, float], years: float) -> float:
        """
        Get discount factor from yield curve.
        
        Args:
            yield_curve: Dictionary mapping tenors (in years) to yields
            years: Target tenor
            
        Returns:
            Discount factor for the specified tenor
        """
        # Convert tenor keys to floats
        tenors = sorted([float(t) for t in yield_curve.keys()])
        
        if years <= 0:
            return 1.0
            
        # If exact tenor exists
        if years in tenors:
            rate = yield_curve[str(years)]
            return math.exp(-rate * years)
            
        # Linear interpolation
        lower_tenor = max([t for t in tenors if t < years], default=tenors[0])
        upper_tenor = min([t for t in tenors if t >= years], default=tenors[-1])
        
        lower_rate = yield_curve[str(lower_tenor)]
        upper_rate = yield_curve[str(upper_tenor)]
        
        # Interpolate rate
        if upper_tenor == lower_tenor:
            rate = lower_rate
        else:
            rate = lower_rate + (upper_rate - lower_rate) * (years - lower_tenor) / (upper_tenor - lower_tenor)
            
        # Calculate discount factor
        return math.exp(-rate * years)
    
    @staticmethod
    def calculate_par_swap_rate(
        start_date: datetime.date,
        maturity_date: datetime.date,
        payment_frequency: PaymentFrequency,
        day_count_convention: DayCountConvention,
        yield_curve: Dict[str, float]
    ) -> float:
        """
        Calculate the par swap rate.
        
        Args:
            start_date: Effective date of the swap
            maturity_date: Maturity date of the swap
            payment_frequency: Payment frequency
            day_count_convention: Day count convention
            yield_curve: Dictionary mapping tenors to yields
            
        Returns:
            Par swap rate
        """
        today = datetime.date.today()
        
        # Create a dummy swap leg to generate payment dates
        dummy_leg = SwapLeg(
            notional_amount=Decimal("1000000"),
            currency="USD",
            start_date=start_date,
            end_date=maturity_date,
            payment_frequency=payment_frequency,
            day_count_convention=day_count_convention,
            is_fixed=True,
            rate=Decimal("0.01")  # Dummy rate
        )
        
        # Calculate PV of a basis point (PVBP)
        payment_dates = [d for d in dummy_leg.payment_dates if d >= today]
        previous_date = start_date
        
        pvbp = 0.0
        annuity = 0.0
        
        for payment_date in payment_dates:
            years_to_payment = (payment_date - today).days / 365.0
            discount_factor = SwapPricingModel._get_discount_factor(yield_curve, years_to_payment)
            
            day_count_factor = dummy_leg.calculate_day_count_factor(previous_date, payment_date)
            pvbp += day_count_factor * discount_factor
            
            previous_date = payment_date
            
        # Calculate par swap rate
        years_to_maturity = (maturity_date - today).days / 365.0
        final_discount = SwapPricingModel._get_discount_factor(yield_curve, years_to_maturity)
        
        if pvbp == 0:
            return 0.0
            
        par_rate = (1 - final_discount) / pvbp
        
        return par_rate


class SwapManager:
    """
    Manager for swap contracts.
    
    This class provides functionality for creating, valuing, and managing
    swap contracts.
    """
    
    def __init__(self):
        """Initialize the swap manager."""
        self.swaps: Dict[str, SwapContract] = {}
        self.yield_curves: Dict[str, Dict[str, float]] = {}
        self.reference_rates: Dict[str, float] = {}
    
    def add_swap(self, swap: SwapContract) -> None:
        """
        Add a swap contract to the manager.
        
        Args:
            swap: Swap contract
        """
        self.swaps[swap.id] = swap
        logger.info(f"Added swap {swap.id} ({swap.swap_type.value}) with {len(swap.legs)} legs")
    
    def get_swap(self, swap_id: str) -> Optional[SwapContract]:
        """
        Get a swap contract by ID.
        
        Args:
            swap_id: Swap ID
            
        Returns:
            Swap contract if found, None otherwise
        """
        return self.swaps.get(swap_id)
    
    def update_yield_curve(self, currency: str, curve_data: Dict[str, float]) -> None:
        """
        Update yield curve data for a currency.
        
        Args:
            currency: Currency code
            curve_data: Dictionary mapping tenors (in years as strings) to yields
        """
        self.yield_curves[currency] = curve_data.copy()
        logger.info(f"Updated yield curve for {currency} with {len(curve_data)} points")
    
    def update_reference_rate(self, rate_name: str, value: float) -> None:
        """
        Update a reference interest rate.
        
        Args:
            rate_name: Name of the reference rate (e.g., "SOFR", "EURIBOR")
            value: Current value of the rate
        """
        self.reference_rates[rate_name] = value
        logger.info(f"Updated reference rate {rate_name}: {value:.4f}")
    
    def value_swap(self, swap_id: str) -> Dict[str, float]:
        """
        Calculate the current value of a swap.
        
        Args:
            swap_id: Swap ID
            
        Returns:
            Dictionary with valuation details
        """
        swap = self.get_swap(swap_id)
        
        if not swap:
            logger.warning(f"Swap {swap_id} not found")
            return {"error": "Swap not found"}
            
        if swap.swap_type == SwapType.INTEREST_RATE:
            return self._value_interest_rate_swap(swap)
        elif swap.swap_type == SwapType.CURRENCY:
            return self._value_currency_swap(swap)
        else:
            logger.warning(f"Valuation not implemented for swap type: {swap.swap_type.value}")
            return {"error": f"Valuation not implemented for {swap.swap_type.value} swaps"}
    
    def _value_interest_rate_swap(self, swap: SwapContract) -> Dict[str, float]:
        """Value an interest rate swap."""
        if len(swap.legs) != 2:
            return {"error": "Interest rate swap must have exactly 2 legs"}
            
        # Identify fixed and floating legs
        fixed_leg = None
        floating_leg = None
        
        for leg in swap.legs:
            if leg.is_fixed:
                fixed_leg = leg
            else:
                floating_leg = leg
                
        if not fixed_leg or not floating_leg:
            return {"error": "Interest rate swap must have one fixed and one floating leg"}
            
        # Get yield curve and reference rate
        currency = fixed_leg.currency
        
        if currency not in self.yield_curves:
            return {"error": f"No yield curve available for {currency}"}
            
        rate_name = str(floating_leg.rate)
        
        if rate_name not in self.reference_rates:
            return {"error": f"No data for reference rate {rate_name}"}
            
        current_rate = self.reference_rates[rate_name]
        
        # Calculate swap value
        value = SwapPricingModel.calculate_interest_rate_swap_price(
            fixed_leg,
            floating_leg,
            self.yield_curves[currency],
            current_rate
        )
        
        # Determine if we are receiving or paying fixed
        position = "Receive Fixed" if fixed_leg == swap.legs[0] else "Pay Fixed"
        fixed_rate = float(fixed_leg.rate)
        
        # Calculate par swap rate
        par_rate = SwapPricingModel.calculate_par_swap_rate(
            swap.effective_date,
            swap.maturity_date,
            fixed_leg.payment_frequency,
            fixed_leg.day_count_convention,
            self.yield_curves[currency]
        )
        
        return {
            "value": value,
            "position": position,
            "notional": float(fixed_leg.notional_amount),
            "fixed_rate": fixed_rate,
            "current_floating_rate": current_rate,
            "par_swap_rate": par_rate,
            "currency": currency
        }
    
    def _value_currency_swap(self, swap: SwapContract) -> Dict[str, float]:
        """Value a currency swap."""
        # TODO: Implement currency swap valuation
        return {"error": "Currency swap valuation not yet implemented"}
    
    def get_payment_schedule(self, swap_id: str) -> List[Dict[str, any]]:
        """
        Get payment schedule for a swap.
        
        Args:
            swap_id: Swap ID
            
        Returns:
            List of payment events with details
        """
        swap = self.get_swap(swap_id)
        
        if not swap:
            logger.warning(f"Swap {swap_id} not found")
            return []
            
        today = datetime.date.today()
        payments = []
        
        # Process each leg
        for leg_index, leg in enumerate(swap.legs):
            leg_type = "Fixed" if leg.is_fixed else "Floating"
            previous_date = leg.start_date
            
            for payment_date in leg.payment_dates:
                if payment_date < today:
                    previous_date = payment_date
                    continue
                    
                day_count_factor = leg.calculate_day_count_factor(previous_date, payment_date)
                
                # Calculate estimated payment
                if leg.is_fixed:
                    rate = float(leg.rate)
                    amount = float(leg.notional_amount) * rate * day_count_factor
                else:
                    # For floating leg, use current rate as estimate for future payments
                    rate_name = str(leg.rate)
                    if rate_name in self.reference_rates:
                        rate = self.reference_rates[rate_name]
                        if leg.spread:
                            rate += float(leg.spread)
                    else:
                        rate = 0.0
                        
                    amount = float(leg.notional_amount) * rate * day_count_factor
                
                payments.append({
                    "date": payment_date,
                    "leg": leg_index + 1,
                    "leg_type": leg_type,
                    "currency": leg.currency,
                    "notional": float(leg.notional_amount),
                    "rate": rate,
                    "amount": amount,
                    "day_count_factor": day_count_factor
                })
                
                previous_date = payment_date
                
        # Sort by date
        payments.sort(key=lambda x: x["date"])
        
        return payments
    
    def calculate_swap_risk(self, swap_id: str) -> Dict[str, float]:
        """
        Calculate risk metrics for a swap.
        
        Args:
            swap_id: Swap ID
            
        Returns:
            Dictionary with risk metrics
        """
        swap = self.get_swap(swap_id)
        
        if not swap:
            logger.warning(f"Swap {swap_id} not found")
            return {"error": "Swap not found"}
            
        # Initialize results
        results = {
            "dv01": 0.0,  # Dollar value of 1 basis point change
            "duration": 0.0,  # Modified duration
            "convexity": 0.0,  # Convexity
        }
        
        if swap.swap_type == SwapType.INTEREST_RATE:
            # Calculate current value
            base_value = self._value_interest_rate_swap(swap).get("value", 0)
            
            # Calculate value with rates +1bp
            for currency in self.yield_curves:
                bumped_curve = {}
                for tenor, rate in self.yield_curves[currency].items():
                    bumped_curve[tenor] = rate + 0.0001  # +1bp
                
                # Store original curve
                original_curve = self.yield_curves[currency].copy()
                
                # Set bumped curve
                self.yield_curves[currency] = bumped_curve
                
                # Calculate bumped value
                bumped_value = self._value_interest_rate_swap(swap).get("value", 0)
                
                # Calculate DV01
                dv01 = bumped_value - base_value
                results["dv01"] = dv01
                
                # Calculate duration (per $100 notional)
                notional = float(swap.legs[0].notional_amount)
                if notional > 0:
                    results["duration"] = -dv01 * 10000 / notional  # Convert to percent
                
                # Restore original curve
                self.yield_curves[currency] = original_curve
        
        return results
    
    def create_interest_rate_swap(self,
                               id: str,
                               effective_date: datetime.date,
                               maturity_date: datetime.date,
                               fixed_rate: Decimal,
                               floating_rate_index: str,
                               notional: Decimal,
                               currency: str,
                               payment_frequency: PaymentFrequency,
                               day_count_convention: DayCountConvention,
                               floating_spread: Optional[Decimal] = None,
                               counterparty: str = "Internal",
                               pay_fixed: bool = True) -> SwapContract:
        """
        Create a standard interest rate swap.
        
        Args:
            id: Swap ID
            effective_date: Start date of the swap
            maturity_date: End date of the swap
            fixed_rate: Fixed interest rate (as a decimal)
            floating_rate_index: Reference rate for floating leg (e.g., "SOFR")
            notional: Notional amount
            currency: Currency code
            payment_frequency: Payment frequency
            day_count_convention: Day count convention
            floating_spread: Spread over reference rate for floating leg
            counterparty: Name of counterparty
            pay_fixed: If True, we pay fixed and receive floating; otherwise the reverse
            
        Returns:
            Created swap contract
        """
        # Create fixed leg
        fixed_leg = SwapLeg(
            notional_amount=notional,
            currency=currency,
            start_date=effective_date,
            end_date=maturity_date,
            payment_frequency=payment_frequency,
            day_count_convention=day_count_convention,
            is_fixed=True,
            rate=fixed_rate
        )
        
        # Create floating leg
        floating_leg = SwapLeg(
            notional_amount=notional,
            currency=currency,
            start_date=effective_date,
            end_date=maturity_date,
            payment_frequency=payment_frequency,
            day_count_convention=day_count_convention,
            is_fixed=False,
            rate=floating_rate_index,
            spread=floating_spread
        )
        
        # Create legs in the correct order based on pay/receive fixed
        legs = [fixed_leg, floating_leg] if pay_fixed else [floating_leg, fixed_leg]
        
        # Create and add swap
        swap = SwapContract(
            id=id,
            swap_type=SwapType.INTEREST_RATE,
            effective_date=effective_date,
            maturity_date=maturity_date,
            counterparty=counterparty,
            legs=legs
        )
        
        self.add_swap(swap)
        return swap
    
    def create_currency_swap(self,
                          id: str,
                          effective_date: datetime.date,
                          maturity_date: datetime.date,
                          leg1_notional: Decimal,
                          leg1_currency: str,
                          leg1_rate: Union[Decimal, str],
                          leg1_is_fixed: bool,
                          leg2_notional: Decimal,
                          leg2_currency: str,
                          leg2_rate: Union[Decimal, str],
                          leg2_is_fixed: bool,
                          payment_frequency: PaymentFrequency,
                          day_count_convention: DayCountConvention,
                          counterparty: str = "Internal") -> SwapContract:
        """
        Create a currency swap.
        
        Args:
            id: Swap ID
            effective_date: Start date of the swap
            maturity_date: End date of the swap
            leg1_notional: Notional amount for first leg
            leg1_currency: Currency code for first leg
            leg1_rate: Rate for first leg (fixed rate or reference rate)
            leg1_is_fixed: Whether first leg has fixed rate
            leg2_notional: Notional amount for second leg
            leg2_currency: Currency code for second leg
            leg2_rate: Rate for second leg
            leg2_is_fixed: Whether second leg has fixed rate
            payment_frequency: Payment frequency
            day_count_convention: Day count convention
            counterparty: Name of counterparty
            
        Returns:
            Created swap contract
        """
        # Create legs
        leg1 = SwapLeg(
            notional_amount=leg1_notional,
            currency=leg1_currency,
            start_date=effective_date,
            end_date=maturity_date,
            payment_frequency=payment_frequency,
            day_count_convention=day_count_convention,
            is_fixed=leg1_is_fixed,
            rate=leg1_rate
        )
        
        leg2 = SwapLeg(
            notional_amount=leg2_notional,
            currency=leg2_currency,
            start_date=effective_date,
            end_date=maturity_date,
            payment_frequency=payment_frequency,
            day_count_convention=day_count_convention,
            is_fixed=leg2_is_fixed,
            rate=leg2_rate
        )
        
        # Determine swap type
        swap_type = SwapType.CROSS_CURRENCY if leg1_currency != leg2_currency else SwapType.INTEREST_RATE
        
        # Create and add swap
        swap = SwapContract(
            id=id,
            swap_type=swap_type,
            effective_date=effective_date,
            maturity_date=maturity_date,
            counterparty=counterparty,
            legs=[leg1, leg2]
        )
        
        self.add_swap(swap)
        return swap


# Example usage
if __name__ == "__main__":
    # Create swap manager
    manager = SwapManager()
    
    # Set up yield curve
    usd_curve = {
        "0.25": 0.0425,  # 3 month
        "0.5": 0.0440,   # 6 month
        "1": 0.0455,     # 1 year
        "2": 0.0465,     # 2 year
        "3": 0.0470,     # 3 year
        "5": 0.0480,     # 5 year
        "7": 0.0485,     # 7 year
        "10": 0.0490     # 10 year
    }
    manager.update_yield_curve("USD", usd_curve)
    
    # Set up reference rates
    manager.update_reference_rate("SOFR", 0.0430)
    manager.update_reference_rate("LIBOR3M", 0.0435)
    
    # Create a 5-year interest rate swap
    today = datetime.date.today()
    swap = manager.create_interest_rate_swap(
        id="SWAP123",
        effective_date=today,
        maturity_date=today.replace(year=today.year + 5),
        fixed_rate=Decimal("0.0465"),  # 4.65%
        floating_rate_index="SOFR",
        notional=Decimal("10000000"),  # 10 million
        currency="USD",
        payment_frequency=PaymentFrequency.QUARTERLY,
        day_count_convention=DayCountConvention.THIRTY_360,
        floating_spread=Decimal("0.0010"),  # 10 basis points
        pay_fixed=True
    )
    
    # Value the swap
    value = manager.value_swap("SWAP123")
    print(f"Swap value: {value}")
    
    # Get payment schedule
    schedule = manager.get_payment_schedule("SWAP123")
    print(f"Next {len(schedule)} payments:")
    for payment in schedule[:3]:  # Show first 3 payments
        print(f"  {payment['date']}: {payment['leg_type']} leg payment of " +
              f"{payment['amount']:.2f} {payment['currency']} (rate: {payment['rate']:.4f})")
        
    # Calculate risk metrics
    risk = manager.calculate_swap_risk("SWAP123")
    print(f"Risk metrics: DV01={risk['dv01']:.2f}, Duration={risk['duration']:.4f}")
