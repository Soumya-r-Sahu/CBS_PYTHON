"""
Reporting Tasks

This module contains scheduled tasks related to report generation.
"""

import logging
from datetime import datetime, timedelta
import csv
import os
from pathlib import Path

from app.lib.task_manager import task_manager
from app.models.models import Account, Transaction
from database.connection import get_db_session

logger = logging.getLogger(__name__)

@task_manager.celery_app.task
def generate_daily_account_summary():
    """
    Generate daily account summary report
    """
    try:
        logger.info("Generating daily account summary")
        
        # Get session
        session = get_db_session()
        
        # Get yesterday's date
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_str = yesterday.strftime('%Y-%m-%d')
        
        # Query accounts and transactions
        accounts = session.query(Account).all()
        
        # Prepare report data
        report_data = []
        for account in accounts:
            # Get transactions for this account from yesterday
            transactions = session.query(Transaction).filter(
                Transaction.account_id == account.id,
                Transaction.timestamp >= yesterday.replace(hour=0, minute=0, second=0),
                Transaction.timestamp < yesterday.replace(hour=0, minute=0, second=0) + timedelta(days=1)
            ).all()
            
            # Calculate metrics
            total_credits = sum(t.amount for t in transactions if t.amount > 0)
            total_debits = sum(abs(t.amount) for t in transactions if t.amount < 0)
            transaction_count = len(transactions)
            
            # Add to report data
            report_data.append({
                'account_number': account.account_number,
                'customer_id': account.customer_id,
                'account_type': account.account_type,
                'balance': account.balance,
                'transaction_count': transaction_count,
                'total_credits': total_credits,
                'total_debits': total_debits,
                'date': yesterday_str
            })
        
        # Create reports directory if it doesn't exist
        reports_dir = Path('app/reports')
        reports_dir.mkdir(exist_ok=True)
        
        # Write CSV report
        report_path = reports_dir / f"account_summary_{yesterday_str}.csv"
        with open(report_path, 'w', newline='') as csvfile:
            fieldnames = ['account_number', 'customer_id', 'account_type', 
                          'balance', 'transaction_count', 'total_credits', 
                          'total_debits', 'date']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in report_data:
                writer.writerow(row)
        
        logger.info(f"Daily account summary generated: {report_path}")
        return {'status': 'success', 'report_path': str(report_path)}
        
    except Exception as e:
        logger.error(f"Failed to generate daily account summary: {str(e)}")
        return {'status': 'error', 'error': str(e)}


@task_manager.celery_app.task
def monthly_transaction_report(year=None, month=None):
    """
    Generate monthly transaction report
    
    Args:
        year (int, optional): Year to generate report for. Defaults to current year.
        month (int, optional): Month to generate report for. Defaults to current month.
    """
    try:
        # Default to previous month if not specified
        today = datetime.now()
        if year is None or month is None:
            # Default to previous month
            if today.month == 1:
                year = today.year - 1
                month = 12
            else:
                year = today.year
                month = today.month - 1
        
        logger.info(f"Generating monthly transaction report for {year}-{month:02d}")
        
        # Get session
        session = get_db_session()
        
        # Define date range for the month
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        # Query transactions for the month
        transactions = session.query(Transaction).filter(
            Transaction.timestamp >= start_date,
            Transaction.timestamp < end_date
        ).all()
        
        # Prepare report data
        report_data = []
        for transaction in transactions:
            report_data.append({
                'transaction_id': transaction.transaction_id,
                'account_id': transaction.account_id,
                'transaction_type': transaction.transaction_type,
                'amount': transaction.amount,
                'timestamp': transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'status': transaction.status,
                'description': transaction.description
            })
        
        # Create reports directory if it doesn't exist
        reports_dir = Path('app/reports')
        reports_dir.mkdir(exist_ok=True)
        
        # Write CSV report
        report_path = reports_dir / f"transaction_report_{year}_{month:02d}.csv"
        with open(report_path, 'w', newline='') as csvfile:
            fieldnames = ['transaction_id', 'account_id', 'transaction_type',
                          'amount', 'timestamp', 'status', 'description']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in report_data:
                writer.writerow(row)
        
        logger.info(f"Monthly transaction report generated: {report_path}")
        return {'status': 'success', 'report_path': str(report_path)}
        
    except Exception as e:
        logger.error(f"Failed to generate monthly transaction report: {str(e)}")
        return {'status': 'error', 'error': str(e)}
