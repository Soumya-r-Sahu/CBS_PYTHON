"""
Monitoring Tasks

This module contains scheduled tasks for system monitoring and health checks.
"""

import logging
import psutil
import socket
import requests
from datetime import datetime
import os
import json
from pathlib import Path

from app.lib.task_manager import task_manager
from app.config.config_loader import config
from database.connection import test_database_connection

logger = logging.getLogger(__name__)

@task_manager.celery_app.task
def system_health_check():
    """
    Check system health and log results
    
    Checks:
    - CPU usage
    - Memory usage
    - Disk usage
    - Database connectivity
    - API endpoints
    """
    try:
        logger.info("Running system health check")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'system': {
                'hostname': socket.gethostname(),
                'cpu_usage_percent': psutil.cpu_percent(interval=1),
                'memory_usage_percent': psutil.virtual_memory().percent,
                'disk_usage_percent': psutil.disk_usage('/').percent,
            },
            'services': {}
        }
        
        # Check database connectivity
        db_result = test_database_connection()
        results['services']['database'] = {
            'status': 'healthy' if db_result['connected'] else 'unhealthy',
            'response_time_ms': db_result.get('response_time_ms'),
            'message': db_result.get('message', '')
        }
        
        # Check API endpoints
        api_endpoints = config.get('monitoring.api_endpoints', [])
        for endpoint in api_endpoints:
            try:
                start_time = datetime.now()
                response = requests.get(
                    endpoint['url'], 
                    timeout=endpoint.get('timeout', 5)
                )
                response_time = (datetime.now() - start_time).total_seconds() * 1000
                
                results['services'][endpoint['name']] = {
                    'status': 'healthy' if response.status_code < 400 else 'unhealthy',
                    'response_time_ms': response_time,
                    'status_code': response.status_code
                }
            except Exception as api_error:
                results['services'][endpoint['name']] = {
                    'status': 'unhealthy',
                    'error': str(api_error)
                }
        
        # Log results
        if results['system']['cpu_usage_percent'] > 80:
            logger.warning(f"High CPU usage: {results['system']['cpu_usage_percent']}%")
        
        if results['system']['memory_usage_percent'] > 80:
            logger.warning(f"High memory usage: {results['system']['memory_usage_percent']}%")
        
        if results['system']['disk_usage_percent'] > 80:
            logger.warning(f"High disk usage: {results['system']['disk_usage_percent']}%")
        
        # Save results to file
        monitoring_dir = Path('monitoring/reports')
        monitoring_dir.mkdir(exist_ok=True, parents=True)
        
        report_file = monitoring_dir / f"health_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Return results
        return {
            'status': 'success',
            'healthy': all(service['status'] == 'healthy' for service in results['services'].values()),
            'results': results
        }
        
    except Exception as e:
        logger.error(f"System health check failed: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


@task_manager.celery_app.task
def check_failed_transactions():
    """
    Check for failed transactions and alert administrators
    """
    from app.models.models import Transaction
    from database.connection import get_db_session
    from app.lib.notification_service import notification_service
    
    try:
        logger.info("Checking for failed transactions")
        
        # Get database session
        session = get_db_session()
        
        # Find transactions that failed in the last hour
        one_hour_ago = datetime.now() - datetime.timedelta(hours=1)
        failed_transactions = session.query(Transaction).filter(
            Transaction.status == 'FAILED',
            Transaction.timestamp >= one_hour_ago
        ).all()
        
        if failed_transactions:
            # Prepare notification
            admin_emails = config.get('alerts.admin_emails', [])
            
            message = (
                f"There were {len(failed_transactions)} failed transactions in the last hour.\n\n"
                f"Transaction IDs:\n"
            )
            
            for transaction in failed_transactions[:10]:  # Show first 10
                message += f"- {transaction.transaction_id}: {transaction.amount} "
                message += f"({transaction.transaction_type})\n"
            
            if len(failed_transactions) > 10:
                message += f"... and {len(failed_transactions) - 10} more.\n"
            
            # Send email alerts
            for admin_email in admin_emails:
                notification_service.send_email(
                    recipient=admin_email,
                    subject=f"ALERT: {len(failed_transactions)} Failed Transactions",
                    message=message
                )
            
            logger.info(f"Alerted admins about {len(failed_transactions)} failed transactions")
        else:
            logger.info("No failed transactions found")
            
        return {
            'status': 'success',
            'failed_transaction_count': len(failed_transactions) if 'failed_transactions' in locals() else 0
        }
        
    except Exception as e:
        logger.error(f"Failed transactions check failed: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }
