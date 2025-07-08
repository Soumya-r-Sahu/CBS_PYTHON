"""
Partner File Exchange - Main Module

This is the entry point for the partner file exchange functionality.
"""
import logging
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any

# Use relative imports instead of modifying sys.path
from .controllers import PartnerFileController


# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('partner_file_exchange.log')
    ]
)

logger = logging.getLogger(__name__)


def process_file_command(args):
    """Handle the process-file command"""
    result = PartnerFileController.process_incoming_file(
        filename=args.filename,
        file_format=args.format
    )
    
    if result["status"] == "success":
        logger.info(result["message"])
        print(f"Successfully processed file: {args.filename}")
        print(f"Processed {result['processed_entries']} entries")
    else:
        logger.error(result["message"])
        print(f"Error processing file: {result['error']}")
        sys.exit(1)


def generate_file_command(args):
    """Handle the generate-file command"""
    # In a real implementation, we might load entries from a database
    # For this example, we'll just use dummy data
    entries = [
        {
            "transaction_id": f"TX{i+1:06d}",
            "amount": 1000.00 + (i * 100),
            "status": "SUCCESS",
            "timestamp": "2025-05-13T10:00:00Z"
        }
        for i in range(args.count)
    ]
    
    result = PartnerFileController.generate_partner_file(
        partner_id=args.partner,
        entries=entries,
        file_type=args.type,
        file_format=args.format
    )
    
    if result["status"] == "success":
        logger.info(result["message"])
        print(f"Successfully generated file: {result['filename']}")
        print(f"Generated file contains {result['entry_count']} entries")
    else:
        logger.error(result["message"])
        print(f"Error generating file: {result['error']}")
        sys.exit(1)


def main():
    """Main entry point for the partner file exchange CLI"""
    parser = argparse.ArgumentParser(
        description="Partner File Exchange Tool - Process and generate partner exchange files"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Process file command
    process_parser = subparsers.add_parser("process", help="Process an incoming partner file")
    process_parser.add_argument("filename", help="Name of the file to process")
    process_parser.add_argument(
        "--format", "-f",
        choices=["csv", "json"],
        default="csv",
        help="Format of the file (default: csv)"
    )
    
    # Generate file command
    generate_parser = subparsers.add_parser("generate", help="Generate a partner file")
    generate_parser.add_argument("partner", help="Partner ID for the file")
    generate_parser.add_argument(
        "--type", "-t",
        default="settlement",
        help="Type of file to generate (default: settlement)"
    )
    generate_parser.add_argument(
        "--format", "-f",
        choices=["csv", "json"],
        default="csv",
        help="Format of the file (default: csv)"
    )
    generate_parser.add_argument(
        "--count", "-c",
        type=int,
        default=10,
        help="Number of entries to generate (default: 10)"
    )
    
    args = parser.parse_args()
    
    if args.command == "process":
        process_file_command(args)
    elif args.command == "generate":
        generate_file_command(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
