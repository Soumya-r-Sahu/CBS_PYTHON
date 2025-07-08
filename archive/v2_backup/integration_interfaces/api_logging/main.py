"""
API Logging Module - Main Entry Point

This module provides CLI and programmatic access to API logging functionality.
"""
import argparse
import json
import sys
from datetime import datetime, timedelta
import logging
from pathlib import Path

# Use relative imports instead of modifying sys.path
from .services import api_logger_service
from .utils import group_errors_by_type, cleanup_old_logs, export_logs_to_json


# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('api_logging_cli.log')
    ]
)

logger = logging.getLogger(__name__)


def get_logs_command(args):
    """Handle the get-logs command"""
    logs = api_logger_service.get_logs(
        start_date=args.start_date,
        end_date=args.end_date,
        status=args.status,
        endpoint=args.endpoint,
        limit=args.limit
    )
    
    print(f"Retrieved {len(logs)} logs")
    
    if args.output:
        if export_logs_to_json(logs, args.output):
            print(f"Logs exported to {args.output}")
        else:
            print(f"Failed to export logs to {args.output}")
            sys.exit(1)
    elif logs:
        for log in logs[:10]:  # Show only first 10
            print(f"{log.timestamp} - {log.endpoint} - {log.status}")
        if len(logs) > 10:
            print(f"... and {len(logs) - 10} more (use --output to export all)")


def get_summary_command(args):
    """Handle the summary command"""
    summary = api_logger_service.get_log_summary(
        start_date=args.start_date,
        end_date=args.end_date
    )
    
    print("\n=== API Log Summary ===")
    print(f"Period: {summary.period_start.strftime('%Y-%m-%d %H:%M:%S')} to {summary.period_end.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Requests: {summary.total_requests}")
    print(f"Success Rate: {summary.success_count}/{summary.total_requests} ({summary.success_count/summary.total_requests*100:.1f}% success)" if summary.total_requests else "Success Rate: N/A")
    print(f"Average Response Time: {summary.avg_duration_ms:.2f}ms")
    print(f"Min/Max Response Time: {summary.min_duration_ms}ms / {summary.max_duration_ms}ms")
    
    print("\n=== Top Endpoints ===")
    for ep in summary.endpoints[:5]:
        print(f"{ep['endpoint']}: {ep['count']} requests ({ep['success_count']} success, {ep['error_count']} errors)")
        
    if args.output:
        try:
            with open(args.output, 'w') as f:
                json.dump({
                    "period_start": summary.period_start.isoformat(),
                    "period_end": summary.period_end.isoformat(),
                    "total_requests": summary.total_requests,
                    "success_count": summary.success_count,
                    "error_count": summary.error_count,
                    "avg_duration_ms": summary.avg_duration_ms,
                    "min_duration_ms": summary.min_duration_ms,
                    "max_duration_ms": summary.max_duration_ms,
                    "endpoints": summary.endpoints
                }, f, indent=2)
            print(f"\nFull summary exported to {args.output}")
        except Exception as e:
            print(f"Failed to export summary: {str(e)}")


def errors_command(args):
    """Handle the errors command"""
    # Get logs with error status
    logs = api_logger_service.get_logs(
        start_date=args.start_date,
        end_date=args.end_date,
        status="error",
        limit=args.limit
    )
    
    error_groups = group_errors_by_type(logs)
    
    print(f"\n=== API Error Groups ({len(logs)} total errors) ===")
    for group in error_groups:
        print(f"\n{group.error_type}: {group.count} occurrences")
        print(f"Time Range: {group.first_occurrence.strftime('%Y-%m-%d %H:%M:%S')} to {group.last_occurrence.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Affected Endpoints: {', '.join(group.endpoints)}")
        
        if args.verbose:
            print("\nSample Errors:")
            for sample in group.sample_errors:
                print(f"  {sample['timestamp']} - {sample['endpoint']}: {sample['error']}")
        
    if args.output:
        try:
            with open(args.output, 'w') as f:
                json.dump([{
                    "error_type": group.error_type,
                    "count": group.count,
                    "first_occurrence": group.first_occurrence.isoformat(),
                    "last_occurrence": group.last_occurrence.isoformat(),
                    "endpoints": group.endpoints,
                    "sample_errors": group.sample_errors
                } for group in error_groups], f, indent=2)
            print(f"\nError groups exported to {args.output}")
        except Exception as e:
            print(f"Failed to export error groups: {str(e)}")


def cleanup_command(args):
    """Handle the cleanup command"""
    days = args.days if args.days is not None else None
    files_deleted = cleanup_old_logs(days)
    print(f"Deleted {files_deleted} old log files")


def main():
    """Main entry point for the API logging CLI"""
    parser = argparse.ArgumentParser(
        description="API Logging Tool - Analyze and manage API logs"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Get logs command
    logs_parser = subparsers.add_parser("get-logs", help="Retrieve API logs")
    logs_parser.add_argument("--start-date", help="Start date (ISO format)")
    logs_parser.add_argument("--end-date", help="End date (ISO format)")
    logs_parser.add_argument("--status", choices=["success", "error"], help="Filter by status")
    logs_parser.add_argument("--endpoint", help="Filter by endpoint")
    logs_parser.add_argument("--limit", type=int, default=100, help="Maximum number of logs to retrieve")
    logs_parser.add_argument("--output", help="Output file for logs (JSON format)")
    
    # Summary command
    summary_parser = subparsers.add_parser("summary", help="Get API log summary")
    summary_parser.add_argument("--start-date", help="Start date (ISO format)")
    summary_parser.add_argument("--end-date", help="End date (ISO format)")
    summary_parser.add_argument("--output", help="Output file for summary (JSON format)")
    
    # Errors command
    errors_parser = subparsers.add_parser("errors", help="Analyze API errors")
    errors_parser.add_argument("--start-date", help="Start date (ISO format)")
    errors_parser.add_argument("--end-date", help="End date (ISO format)")
    errors_parser.add_argument("--limit", type=int, default=1000, help="Maximum number of logs to analyze")
    errors_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed error information")
    errors_parser.add_argument("--output", help="Output file for error analysis (JSON format)")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Delete old log files")
    cleanup_parser.add_argument("--days", type=int, help="Number of days to keep logs (defaults to config value)")
    
    args = parser.parse_args()
    
    if args.command == "get-logs":
        get_logs_command(args)
    elif args.command == "summary":
        get_summary_command(args)
    elif args.command == "errors":
        errors_command(args)
    elif args.command == "cleanup":
        cleanup_command(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
