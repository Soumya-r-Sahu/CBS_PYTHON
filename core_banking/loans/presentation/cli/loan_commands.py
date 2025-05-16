"""
Loan Commands CLI

This module provides a command-line interface for loan operations.
"""
import click
import decimal
from datetime import datetime
from typing import Optional

from ...domain.entities.loan import LoanType, LoanStatus, RepaymentFrequency
from ...application.use_cases.loan_application_use_case import LoanApplicationUseCase, LoanApplicationError
from ...application.use_cases.loan_approval_use_case import LoanApprovalUseCase, LoanApprovalError
from ...application.use_cases.loan_disbursement_use_case import LoanDisbursementUseCase, LoanDisbursementError
from ...application.services.loan_calculator_service import LoanCalculatorService
from ...di_container import (
    get_loan_application_use_case,
    get_loan_approval_use_case,
    get_loan_disbursement_use_case,
    get_loan_calculator_service,
    get_loan_repository
)


@click.group()
def loan_cli():
    """Loan management commands."""
    pass


@loan_cli.command("apply")
@click.option("--customer-id", required=True, help="Customer ID")
@click.option("--loan-type", required=True, 
              type=click.Choice([t.value for t in LoanType]), 
              help="Type of loan")
@click.option("--amount", required=True, type=float, help="Loan amount")
@click.option("--term-months", required=True, type=int, help="Loan term in months")
@click.option("--interest-rate", required=True, type=float, help="Annual interest rate (e.g., 12.5 for 12.5%)")
@click.option("--repayment-frequency", required=True,
              type=click.Choice([f.value for f in RepaymentFrequency]),
              help="Repayment frequency")
@click.option("--purpose", required=True, help="Purpose of the loan")
@click.option("--collateral-description", help="Description of collateral (if applicable)")
@click.option("--collateral-value", type=float, help="Value of collateral (if applicable)")
@click.option("--cosigner-id", help="Cosigner ID (if applicable)")
@click.option("--grace-period-days", type=int, default=0, help="Grace period in days")
def apply_for_loan(
    customer_id: str,
    loan_type: str,
    amount: float,
    term_months: int,
    interest_rate: float,
    repayment_frequency: str,
    purpose: str,
    collateral_description: Optional[str] = None,
    collateral_value: Optional[float] = None,
    cosigner_id: Optional[str] = None,
    grace_period_days: int = 0
):
    """Apply for a new loan."""
    try:
        # Convert string values to enum types
        loan_type_enum = LoanType(loan_type)
        repayment_frequency_enum = RepaymentFrequency(repayment_frequency)
        
        # Convert numeric values to Decimal
        amount_decimal = decimal.Decimal(str(amount))
        interest_rate_decimal = decimal.Decimal(str(interest_rate))
        collateral_value_decimal = decimal.Decimal(str(collateral_value)) if collateral_value else None
        
        # Get the use case from DI container
        loan_application_use_case = get_loan_application_use_case()
        
        # Execute the use case
        loan = loan_application_use_case.execute(
            customer_id=customer_id,
            loan_type=loan_type_enum,
            amount=amount_decimal,
            term_months=term_months,
            interest_rate=interest_rate_decimal,
            repayment_frequency=repayment_frequency_enum,
            purpose=purpose,
            collateral_description=collateral_description,
            collateral_value=collateral_value_decimal,
            cosigner_id=cosigner_id,
            grace_period_days=grace_period_days
        )
        
        # Display success message
        click.echo(f"Loan application submitted successfully!")
        click.echo(f"Loan ID: {loan.id}")
        click.echo(f"Status: {loan.status.value}")
        click.echo(f"Amount: {loan.amount}")
        click.echo(f"Term: {loan.terms.term_months} months")
        click.echo(f"Interest Rate: {loan.terms.interest_rate}%")
        
        # Calculate and show EMI
        calculator = get_loan_calculator_service()
        emi = calculator.calculate_emi(loan.amount, loan.terms.interest_rate, loan.terms.term_months)
        total_payment = calculator.calculate_total_payment(loan.amount, loan.terms.interest_rate, loan.terms.term_months)
        total_interest = calculator.calculate_total_interest(loan.amount, loan.terms.interest_rate, loan.terms.term_months)
        
        click.echo(f"Monthly Payment (EMI): {emi}")
        click.echo(f"Total Payment: {total_payment}")
        click.echo(f"Total Interest: {total_interest}")
        
    except LoanApplicationError as e:
        click.echo(f"Error: {str(e)}", err=True)
    except ValueError as e:
        click.echo(f"Invalid input: {str(e)}", err=True)
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}", err=True)


@loan_cli.command("approve")
@click.option("--loan-id", required=True, help="Loan ID")
@click.option("--approved-by", required=True, help="Staff ID of approver")
@click.option("--approved-amount", type=float, help="Approved loan amount (if different)")
@click.option("--approved-interest-rate", type=float, help="Approved interest rate (if different)")
@click.option("--notes", help="Approval notes")
def approve_loan(
    loan_id: str,
    approved_by: str,
    approved_amount: Optional[float] = None,
    approved_interest_rate: Optional[float] = None,
    notes: Optional[str] = None
):
    """Approve a loan application."""
    try:
        # Convert numeric values to Decimal if provided
        approved_amount_decimal = decimal.Decimal(str(approved_amount)) if approved_amount else None
        approved_interest_rate_decimal = decimal.Decimal(str(approved_interest_rate)) if approved_interest_rate else None
        
        # Get the use case from DI container
        loan_approval_use_case = get_loan_approval_use_case()
        
        # Execute the use case
        loan = loan_approval_use_case.approve(
            loan_id=loan_id,
            approved_by=approved_by,
            approved_amount=approved_amount_decimal,
            approved_interest_rate=approved_interest_rate_decimal,
            approval_notes=notes
        )
        
        # Display success message
        click.echo(f"Loan application approved successfully!")
        click.echo(f"Loan ID: {loan.id}")
        click.echo(f"Status: {loan.status.value}")
        click.echo(f"Approved Amount: {loan.amount}")
        click.echo(f"Approved Interest Rate: {loan.terms.interest_rate}%")
        click.echo(f"Approved Date: {loan.approved_date}")
        
    except LoanApprovalError as e:
        click.echo(f"Error: {str(e)}", err=True)
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}", err=True)


@loan_cli.command("deny")
@click.option("--loan-id", required=True, help="Loan ID")
@click.option("--denied-by", required=True, help="Staff ID of person denying the loan")
@click.option("--reason", required=True, help="Reason for denial")
@click.option("--notes", help="Additional notes")
def deny_loan(
    loan_id: str,
    denied_by: str,
    reason: str,
    notes: Optional[str] = None
):
    """Deny a loan application."""
    try:
        # Get the use case from DI container
        loan_approval_use_case = get_loan_approval_use_case()
        
        # Execute the use case
        loan = loan_approval_use_case.deny(
            loan_id=loan_id,
            denied_by=denied_by,
            denial_reason=reason,
            denial_notes=notes
        )
        
        # Display success message
        click.echo(f"Loan application denied!")
        click.echo(f"Loan ID: {loan.id}")
        click.echo(f"Status: {loan.status.value}")
        click.echo(f"Denial Reason: {loan.denial_reason}")
        click.echo(f"Denial Date: {loan.denial_date}")
        
    except LoanApprovalError as e:
        click.echo(f"Error: {str(e)}", err=True)
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}", err=True)


@loan_cli.command("disburse")
@click.option("--loan-id", required=True, help="Loan ID")
@click.option("--disbursed-by", required=True, help="Staff ID of person disbursing the loan")
@click.option("--account-number", required=True, help="Account number to receive funds")
@click.option("--reference-number", help="Reference number for the transaction")
@click.option("--notes", help="Additional notes")
def disburse_loan(
    loan_id: str,
    disbursed_by: str,
    account_number: str,
    reference_number: Optional[str] = None,
    notes: Optional[str] = None
):
    """Disburse funds for an approved loan."""
    try:
        # Get the use case from DI container
        loan_disbursement_use_case = get_loan_disbursement_use_case()
        
        # Execute the use case
        loan = loan_disbursement_use_case.execute(
            loan_id=loan_id,
            disbursed_by=disbursed_by,
            account_number=account_number,
            reference_number=reference_number,
            disbursement_notes=notes
        )
        
        # Display success message
        click.echo(f"Loan funds disbursed successfully!")
        click.echo(f"Loan ID: {loan.id}")
        click.echo(f"Status: {loan.status.value}")
        click.echo(f"Disbursed Amount: {loan.amount}")
        click.echo(f"Disbursement Date: {loan.disbursement_date}")
        click.echo(f"Account Number: {loan.account_number}")
        click.echo(f"Reference: {loan.disbursement_reference}")
        click.echo(f"Maturity Date: {loan.maturity_date}")
        
    except LoanDisbursementError as e:
        click.echo(f"Error: {str(e)}", err=True)
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}", err=True)


@loan_cli.command("list")
@click.option("--customer-id", help="Filter by customer ID")
@click.option("--status", type=click.Choice([s.value for s in LoanStatus]), help="Filter by loan status")
@click.option("--loan-type", type=click.Choice([t.value for t in LoanType]), help="Filter by loan type")
@click.option("--limit", type=int, default=10, help="Maximum number of results")
def list_loans(
    customer_id: Optional[str] = None,
    status: Optional[str] = None,
    loan_type: Optional[str] = None,
    limit: int = 10
):
    """List loans with optional filtering."""
    try:
        # Get the repository from DI container
        loan_repository = get_loan_repository()
        
        # Prepare filters
        filters = {}
        if customer_id:
            filters['customer_id'] = customer_id
        if status:
            filters['status'] = LoanStatus(status)
        if loan_type:
            filters['loan_type'] = LoanType(loan_type)
        
        # Get loans
        loans = loan_repository.find_by(filters, limit=limit)
        
        # Display results
        if not loans:
            click.echo("No loans found matching the criteria.")
            return
        
        click.echo(f"Found {len(loans)} loan(s):")
        click.echo("-" * 80)
        
        for loan in loans:
            click.echo(f"Loan ID: {loan.id}")
            click.echo(f"Customer ID: {loan.customer_id}")
            click.echo(f"Type: {loan.loan_type.value}")
            click.echo(f"Amount: {loan.amount}")
            click.echo(f"Status: {loan.status.value}")
            click.echo(f"Application Date: {loan.application_date}")
            
            if loan.status == LoanStatus.APPROVED:
                click.echo(f"Approved Date: {loan.approved_date}")
            
            if loan.status == LoanStatus.ACTIVE:
                click.echo(f"Disbursement Date: {loan.disbursement_date}")
                click.echo(f"Maturity Date: {loan.maturity_date}")
            
            click.echo("-" * 80)
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)


@loan_cli.command("calculator")
@click.option("--amount", required=True, type=float, help="Loan amount")
@click.option("--interest-rate", required=True, type=float, help="Annual interest rate (e.g., 12.5 for 12.5%)")
@click.option("--term-months", required=True, type=int, help="Loan term in months")
def calculator(
    amount: float,
    interest_rate: float,
    term_months: int
):
    """Calculate loan EMI and payment details."""
    try:
        # Convert numeric values to Decimal
        amount_decimal = decimal.Decimal(str(amount))
        interest_rate_decimal = decimal.Decimal(str(interest_rate))
        
        # Get the calculator service
        calculator = get_loan_calculator_service()
        
        # Calculate loan details
        emi = calculator.calculate_emi(amount_decimal, interest_rate_decimal, term_months)
        total_payment = calculator.calculate_total_payment(amount_decimal, interest_rate_decimal, term_months)
        total_interest = calculator.calculate_total_interest(amount_decimal, interest_rate_decimal, term_months)
        
        # Display results
        click.echo(f"Loan Amount: {amount_decimal}")
        click.echo(f"Interest Rate: {interest_rate_decimal}%")
        click.echo(f"Term: {term_months} months")
        click.echo(f"Monthly Payment (EMI): {emi}")
        click.echo(f"Total Payment: {total_payment}")
        click.echo(f"Total Interest: {total_interest}")
        click.echo(f"Interest to Principal Ratio: {(total_interest / amount_decimal * 100).quantize(decimal.Decimal('0.01'))}%")
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)


if __name__ == "__main__":
    loan_cli()
