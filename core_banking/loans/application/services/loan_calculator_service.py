"""
Loan Calculator Service

This service provides calculations for loans, including EMI, interest, amortization schedules, etc.
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional
import math

from ...domain.entities.loan import Loan, RepaymentFrequency


class LoanCalculatorService:
    """
    Service for performing loan-related calculations.
    
    This service provides methods for calculating various aspects of loans,
    such as EMI, total interest, amortization schedules, etc.
    """
    
    def calculate_emi(
        self, 
        principal: Decimal, 
        annual_interest_rate: Decimal, 
        term_months: int
    ) -> Decimal:
        """
        Calculate the Equated Monthly Installment (EMI) for a loan.
        
        Args:
            principal: The loan amount
            annual_interest_rate: Annual interest rate (in percentage)
            term_months: Loan term in months
            
        Returns:
            The EMI amount
        """
        # Convert annual interest rate to monthly rate
        monthly_rate = annual_interest_rate / Decimal('100') / Decimal('12')
        
        if monthly_rate == Decimal('0'):
            # If interest rate is 0, just divide principal by term
            return principal / Decimal(term_months)
        
        # EMI formula: P * r * (1+r)^n / ((1+r)^n - 1)
        numerator = monthly_rate * (Decimal('1') + monthly_rate) ** Decimal(term_months)
        denominator = (Decimal('1') + monthly_rate) ** Decimal(term_months) - Decimal('1')
        
        emi = principal * (numerator / denominator)
        
        # Round to 2 decimal places
        return emi.quantize(Decimal('0.01'))
    
    def calculate_total_payment(
        self, 
        principal: Decimal, 
        annual_interest_rate: Decimal, 
        term_months: int
    ) -> Decimal:
        """
        Calculate the total payment over the life of the loan.
        
        Args:
            principal: The loan amount
            annual_interest_rate: Annual interest rate (in percentage)
            term_months: Loan term in months
            
        Returns:
            The total payment amount
        """
        emi = self.calculate_emi(principal, annual_interest_rate, term_months)
        total_payment = emi * Decimal(term_months)
        
        return total_payment.quantize(Decimal('0.01'))
    
    def calculate_total_interest(
        self, 
        principal: Decimal, 
        annual_interest_rate: Decimal, 
        term_months: int
    ) -> Decimal:
        """
        Calculate the total interest paid over the life of the loan.
        
        Args:
            principal: The loan amount
            annual_interest_rate: Annual interest rate (in percentage)
            term_months: Loan term in months
            
        Returns:
            The total interest amount
        """
        total_payment = self.calculate_total_payment(principal, annual_interest_rate, term_months)
        total_interest = total_payment - principal
        
        return total_interest.quantize(Decimal('0.01'))
    
    def generate_amortization_schedule(
        self, 
        loan: Loan
    ) -> List[Dict[str, Any]]:
        """
        Generate an amortization schedule for a loan.
        
        Args:
            loan: The loan entity
            
        Returns:
            A list of dictionaries with payment details
        """
        principal = loan.amount
        annual_interest_rate = loan.terms.interest_rate
        term_months = loan.terms.term_months
        start_date = loan.disbursement_date or datetime.now().date()
        
        # Calculate payment amount based on frequency
        monthly_payment = self.calculate_emi(principal, annual_interest_rate, term_months)
        
        # Determine payment frequency and adjust payment amount
        payment_multiplier = self._get_payment_multiplier(loan.terms.repayment_frequency)
        payment_interval_months = 12 // payment_multiplier
        
        # Adjust payment for frequency
        payment_amount = monthly_payment * Decimal(payment_interval_months)
        
        # Generate schedule
        schedule = []
        remaining_principal = principal
        monthly_rate = annual_interest_rate / Decimal('100') / Decimal('12')
        
        payment_date = self._get_first_payment_date(
            start_date, 
            loan.terms.grace_period_days,
            loan.terms.repayment_frequency
        )
        
        for payment_number in range(1, math.ceil(term_months / payment_interval_months) + 1):
            # Calculate interest for this period
            interest_payment = remaining_principal * monthly_rate * Decimal(payment_interval_months)
            
            # For the last payment, adjust to pay off the loan exactly
            if payment_number == math.ceil(term_months / payment_interval_months):
                principal_payment = remaining_principal
                payment_amount = principal_payment + interest_payment
            else:
                principal_payment = payment_amount - interest_payment
            
            # In case of rounding errors causing negative principal
            principal_payment = max(principal_payment, Decimal('0'))
            
            # Update remaining principal
            remaining_principal -= principal_payment
            
            # Ensure we don't have negative remaining principal due to rounding
            if remaining_principal < Decimal('0.01'):
                remaining_principal = Decimal('0')
            
            # Add to schedule
            schedule.append({
                'payment_number': payment_number,
                'date': payment_date,
                'amount': payment_amount.quantize(Decimal('0.01')),
                'principal': principal_payment.quantize(Decimal('0.01')),
                'interest': interest_payment.quantize(Decimal('0.01')),
                'remaining_principal': remaining_principal.quantize(Decimal('0.01'))
            })
            
            # Update date for next payment
            payment_date = self._get_next_payment_date(
                payment_date, 
                loan.terms.repayment_frequency
            )
            
            # If the loan is paid off, stop
            if remaining_principal <= Decimal('0'):
                break
        
        return schedule
    
    def _get_payment_multiplier(self, frequency: RepaymentFrequency) -> int:
        """
        Get the payment multiplier for a frequency (how many payments per year).
        
        Args:
            frequency: The repayment frequency
            
        Returns:
            Number of payments per year
        """
        frequency_map = {
            RepaymentFrequency.DAILY: 365,
            RepaymentFrequency.WEEKLY: 52,
            RepaymentFrequency.BIWEEKLY: 26,
            RepaymentFrequency.MONTHLY: 12,
            RepaymentFrequency.QUARTERLY: 4,
            RepaymentFrequency.SEMIANNUALLY: 2,
            RepaymentFrequency.ANNUALLY: 1
        }
        
        return frequency_map.get(frequency, 12)
    
    def _get_first_payment_date(
        self, 
        start_date: date, 
        grace_period_days: int,
        frequency: RepaymentFrequency
    ) -> date:
        """
        Calculate the first payment date based on start date and grace period.
        
        Args:
            start_date: The loan start date
            grace_period_days: Number of days in the grace period
            frequency: The repayment frequency
            
        Returns:
            The first payment date
        """
        # Add grace period
        payment_date = start_date + timedelta(days=grace_period_days)
        
        # Adjust to the next payment date based on frequency
        if frequency == RepaymentFrequency.MONTHLY:
            # For monthly, set to the same day of the next month
            month = payment_date.month + 1
            year = payment_date.year
            
            if month > 12:
                month = 1
                year += 1
            
            # Handle month-end edge cases (e.g., Jan 31 -> Feb 28)
            day = min(payment_date.day, self._get_days_in_month(year, month))
            
            payment_date = date(year, month, day)
        elif frequency == RepaymentFrequency.QUARTERLY:
            # For quarterly, add 3 months
            month = payment_date.month + 3
            year = payment_date.year
            
            if month > 12:
                month = month - 12
                year += 1
            
            day = min(payment_date.day, self._get_days_in_month(year, month))
            
            payment_date = date(year, month, day)
        # Add more frequency adjustments as needed
        
        return payment_date
    
    def _get_next_payment_date(
        self, 
        current_date: date, 
        frequency: RepaymentFrequency
    ) -> date:
        """
        Calculate the next payment date based on the current date and frequency.
        
        Args:
            current_date: The current payment date
            frequency: The repayment frequency
            
        Returns:
            The next payment date
        """
        if frequency == RepaymentFrequency.DAILY:
            return current_date + timedelta(days=1)
        elif frequency == RepaymentFrequency.WEEKLY:
            return current_date + timedelta(days=7)
        elif frequency == RepaymentFrequency.BIWEEKLY:
            return current_date + timedelta(days=14)
        elif frequency == RepaymentFrequency.MONTHLY:
            month = current_date.month + 1
            year = current_date.year
            
            if month > 12:
                month = 1
                year += 1
            
            day = min(current_date.day, self._get_days_in_month(year, month))
            
            return date(year, month, day)
        elif frequency == RepaymentFrequency.QUARTERLY:
            month = current_date.month + 3
            year = current_date.year
            
            if month > 12:
                month = month - 12
                year += 1
            
            day = min(current_date.day, self._get_days_in_month(year, month))
            
            return date(year, month, day)
        elif frequency == RepaymentFrequency.SEMIANNUALLY:
            month = current_date.month + 6
            year = current_date.year
            
            if month > 12:
                month = month - 12
                year += 1
            
            day = min(current_date.day, self._get_days_in_month(year, month))
            
            return date(year, month, day)
        elif frequency == RepaymentFrequency.ANNUALLY:
            return date(current_date.year + 1, current_date.month, min(current_date.day, 28))
        
        # Default to monthly if unknown frequency
        return self._get_next_payment_date(current_date, RepaymentFrequency.MONTHLY)
    
    def _get_days_in_month(self, year: int, month: int) -> int:
        """
        Get the number of days in a month.
        
        Args:
            year: The year
            month: The month (1-12)
            
        Returns:
            Number of days in the month
        """
        # Use the fact that the day before the 1st of next month is the last day of this month
        if month == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month + 1, 1)
        
        last_day = next_month - timedelta(days=1)
        return last_day.day
