"""
Accounting Tasks

This module contains scheduled tasks related to accounting operations.
"""

import logging
from datetime import datetime, timedelta
import calendar
from decimal import Decimal

from app.lib.task_manager import task_manager
from database.connection import get_db_session
from app.models.models import Account, Transaction
from app.lib.notification_service import notification_service

logger = logging.getLogger(__name__)

@task_manager.celery_app.task
def calculate_interest():
    """
    Calculate and apply interest to savings accounts
    This task is typically scheduled to run at the end of each month
    """
    try:
        logger.info("Starting interest calculation")
        
        # Get the current date
        today = datetime.now()
        
        # Check if it's the last day of the month
        # If not, we still proceed for testing but log a warning
        last_day = calendar.monthrange(today.year, today.month)[1]
        if today.day != last_day:
            logger.warning(f"Interest calculation running on {today.day}, not the last day of the month ({last_day})")
        
        # Get database session
        session = get_db_session()
        
        # Get all savings accounts
        savings_accounts = session.query(Account).filter(
            Account.account_type == 'SAVINGS'
        ).all()
        
        logger.info(f"Calculating interest for {len(savings_accounts)} savings accounts")
        
        # Process each account
        for account in savings_accounts:
            try:
                # Get account interest rate (default to 3.5% annual)
                annual_rate = Decimal(str(account.interest_rate or '0.035'))
                
                # Calculate daily interest rate
                daily_rate = annual_rate / Decimal('365')
                
                # Determine how many days to calculate interest for
                # Typically this is for the entire month
                days_in_month = calendar.monthrange(today.year, today.month)[1]
                
                # Calculate interest amount
                interest_amount = account.balance * daily_rate * Decimal(str(days_in_month))
                interest_amount = interest_amount.quantize(Decimal('0.01'))  # Round to 2 decimal places
                
                if interest_amount > Decimal('0'):
                    # Create a transaction for the interest
                    interest_transaction = Transaction(
                        account_id=account.id,
                        transaction_type='INTEREST_CREDIT',
                        amount=interest_amount,
                        timestamp=datetime.now(),
                        status='COMPLETED',
                        description=f"Interest credit for {today.strftime('%B %Y')}",
                        balance_after=account.balance + interest_amount
                    )
                    
                    # Update account balance
                    account.balance += interest_amount
                    
                    # Add transaction to session
                    session.add(interest_transaction)
                    
                    # Send notification to account holder
                    if account.customer_id:
                        # Get customer details from the account relationship
                        customer = account.customer
                        
                        if customer:
                            notification_data = {
                                'email': customer.email,
                                'phone_number': customer.phone
                            }
                            
                            transaction_data = {
                                'account_number': account.account_number,
                                'type': 'Interest Credit',
                                'amount': float(interest_amount),
                                'timestamp': today.strftime('%Y-%m-%d'),
                                'balance': float(account.balance)
                            }
                            
                            notification_service.send_transaction_alert(
                                notification_data,
                                transaction_data
                            )
                    
                    logger.info(f"Applied interest of {interest_amount} to account {account.account_number}")
                
            except Exception as account_error:
                logger.error(f"Error processing interest for account {account.account_number}: {str(account_error)}")
        
        # Commit all changes
        session.commit()
        logger.info("Interest calculation completed successfully")
        
        return {
            'status': 'success',
            'accounts_processed': len(savings_accounts),
            'date': today.strftime('%Y-%m-%d')
        }
        
    except Exception as e:
        logger.error(f"Interest calculation failed: {str(e)}")
        
        # Make sure to rollback any pending changes
        if 'session' in locals():
            session.rollback()
            
        return {
            'status': 'error',
            'error': str(e)
        }


@task_manager.celery_app.task
def process_standing_orders():
    """
    Process standing orders and recurring payments
    This task is typically scheduled to run daily
    """
    from app.models.models import StandingOrder
    
    try:
        logger.info("Processing standing orders")
        
        # Get the current date
        today = datetime.now().date()
        
        # Get database session
        session = get_db_session()
        
        # Find standing orders due today
        standing_orders = session.query(StandingOrder).filter(
            StandingOrder.next_execution_date <= today,
            StandingOrder.status == 'ACTIVE'
        ).all()
        
        logger.info(f"Found {len(standing_orders)} standing orders to process")
        
        # Process each standing order
        for order in standing_orders:
            try:
                # Get source and destination accounts
                source_account = session.query(Account).filter(
                    Account.id == order.source_account_id
                ).first()
                
                destination_account = session.query(Account).filter(
                    Account.id == order.destination_account_id
                ).first()
                
                if not source_account:
                    logger.error(f"Source account {order.source_account_id} not found for standing order {order.id}")
                    continue
                    
                if not destination_account:
                    logger.error(f"Destination account {order.destination_account_id} not found for standing order {order.id}")
                    continue
                
                # Check if source account has sufficient funds
                if source_account.balance < order.amount:
                    logger.warning(f"Insufficient funds in account {source_account.account_number} for standing order {order.id}")
                    
                    # Create failed transaction record
                    failed_transaction = Transaction(
                        account_id=source_account.id,
                        transaction_type='STANDING_ORDER',
                        amount=-order.amount,
                        timestamp=datetime.now(),
                        status='FAILED',
                        description=f"Standing order payment to {destination_account.account_number} - Insufficient funds",
                        balance_after=source_account.balance
                    )
                    
                    session.add(failed_transaction)
                    continue
                
                # Process the transfer
                # Debit transaction for source account
                debit_transaction = Transaction(
                    account_id=source_account.id,
                    transaction_type='STANDING_ORDER',
                    amount=-order.amount,
                    timestamp=datetime.now(),
                    status='COMPLETED',
                    description=f"Standing order payment to {destination_account.account_number} - {order.description}",
                    balance_after=source_account.balance - order.amount
                )
                
                # Update source account balance
                source_account.balance -= order.amount
                
                # Credit transaction for destination account
                credit_transaction = Transaction(
                    account_id=destination_account.id,
                    transaction_type='STANDING_ORDER',
                    amount=order.amount,
                    timestamp=datetime.now(),
                    status='COMPLETED',
                    description=f"Standing order payment from {source_account.account_number} - {order.description}",
                    balance_after=destination_account.balance + order.amount
                )
                
                # Update destination account balance
                destination_account.balance += order.amount
                
                # Add transactions to session
                session.add(debit_transaction)
                session.add(credit_transaction)
                
                # Update the next execution date for the standing order
                if order.frequency == 'DAILY':
                    order.next_execution_date = today + timedelta(days=1)
                elif order.frequency == 'WEEKLY':
                    order.next_execution_date = today + timedelta(weeks=1)
                elif order.frequency == 'MONTHLY':
                    # Get the same day next month, handle month end cases
                    if today.day > 28:
                        # Move to next month and get the last day if needed
                        next_month = today.month + 1 if today.month < 12 else 1
                        next_year = today.year if today.month < 12 else today.year + 1
                        last_day = calendar.monthrange(next_year, next_month)[1]
                        order.next_execution_date = datetime.date(next_year, next_month, min(today.day, last_day))
                    else:
                        # Simply move to next month
                        next_month = today.month + 1 if today.month < 12 else 1
                        next_year = today.year if today.month < 12 else today.year + 1
                        order.next_execution_date = datetime.date(next_year, next_month, today.day)
                
                logger.info(f"Standing order {order.id} processed successfully")
                
            except Exception as order_error:
                logger.error(f"Error processing standing order {order.id}: {str(order_error)}")
        
        # Commit all changes
        session.commit()
        logger.info("Standing orders processing completed successfully")
        
        return {
            'status': 'success',
            'orders_processed': len(standing_orders),
            'date': today.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Standing orders processing failed: {str(e)}")
        
        # Make sure to rollback any pending changes
        if 'session' in locals():
            session.rollback()
            
        return {
            'status': 'error',
            'error': str(e)
        }
