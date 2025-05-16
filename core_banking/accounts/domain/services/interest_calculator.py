"""
Interest Calculator Domain Service

This module provides services for calculating interest on bank accounts.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, Any

from ..entities.account import Account, AccountType


class InterestCalculator:
    """Service for calculating interest on accounts"""
    
    @staticmethod
    def calculate_savings_interest(
        account: Account,
        from_date: date,
        to_date: date,
        interest_rate: Decimal = None
    ) -> Dict[str, Any]:
        """
        Calculate interest for a savings account
        
        Args:
            account: The account to calculate interest for
            from_date: Start date for interest calculation
            to_date: End date for interest calculation
            interest_rate: Interest rate to use (overrides account's rate)
            
        Returns:
            Dictionary with interest calculation details
        """
        if account.account_type != AccountType.SAVINGS:
            return {
                "success": False,
                "message": "Account is not a savings account",
                "interest": Decimal('0.00')
            }
        
        # Use account's interest rate if not provided
        rate = interest_rate if interest_rate is not None else account.interest_rate
        
        if rate is None:
            return {
                "success": False,
                "message": "No interest rate specified",
                "interest": Decimal('0.00')
            }
        
        # Calculate number of days in period
        days = (to_date - from_date).days
        if days <= 0:
            return {
                "success": False,
                "message": "Invalid date range",
                "interest": Decimal('0.00')
            }
        
        # Simple interest calculation (can be enhanced for daily balance, etc.)
        yearly_rate = rate / Decimal('100')  # Convert percentage to decimal
        daily_rate = yearly_rate / Decimal('365')
        interest = account.balance * daily_rate * Decimal(str(days))
        interest = interest.quantize(Decimal('0.01'))  # Round to 2 decimal places
        
        return {
            "success": True,
            "message": "Interest calculated successfully",
            "interest": interest,
            "from_date": from_date,
            "to_date": to_date,
            "days": days,
            "rate": rate,
            "balance": account.balance
        }
    
    @staticmethod
    def calculate_fixed_deposit_interest(
        account: Account,
        maturity_date: date,
        interest_rate: Decimal = None
    ) -> Dict[str, Any]:
        """
        Calculate interest for a fixed deposit account
        
        Args:
            account: The account to calculate interest for
            maturity_date: Maturity date of the fixed deposit
            interest_rate: Interest rate to use (overrides account's rate)
            
        Returns:
            Dictionary with interest calculation details
        """
        if account.account_type != AccountType.FIXED_DEPOSIT:
            return {
                "success": False,
                "message": "Account is not a fixed deposit account",
                "interest": Decimal('0.00')
            }
        
        # Use account's interest rate if not provided
        rate = interest_rate if interest_rate is not None else account.interest_rate
        
        if rate is None:
            return {
                "success": False,
                "message": "No interest rate specified",
                "interest": Decimal('0.00')
            }
        
        # Calculate tenure in days
        start_date = account.created_at.date()
        days = (maturity_date - start_date).days
        
        if days <= 0:
            return {
                "success": False,
                "message": "Invalid maturity date",
                "interest": Decimal('0.00')
            }
        
        # Compound interest calculation
        yearly_rate = rate / Decimal('100')  # Convert percentage to decimal
        years = Decimal(str(days)) / Decimal('365')
        
        # Calculate interest using compound interest formula: P(1+r)^t - P
        principal = account.balance
        interest = principal * ((1 + yearly_rate) ** years - 1)
        interest = interest.quantize(Decimal('0.01'))  # Round to 2 decimal places
        
        return {
            "success": True,
            "message": "Interest calculated successfully",
            "interest": interest,
            "start_date": start_date,
            "maturity_date": maturity_date,
            "days": days,
            "rate": rate,
            "principal": principal,
            "maturity_amount": principal + interest
        }
