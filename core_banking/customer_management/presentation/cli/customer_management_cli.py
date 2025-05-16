"""
Customer Management CLI

Command-line interface for the Customer Management module.
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

from ...di_container import get_create_customer_use_case, get_verify_customer_kyc_use_case
from ...application.use_cases.create_customer import CreateCustomerRequest
from ...application.use_cases.verify_customer_kyc import VerifyCustomerKycRequest


class CustomerManagementCli:
    """Command-line interface for Customer Management module"""
    
    def __init__(self):
        """Initialize the CLI with the required use cases"""
        self.create_customer_use_case = get_create_customer_use_case()
        self.verify_customer_kyc_use_case = get_verify_customer_kyc_use_case()
    
    def create_customer(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new customer from command-line arguments.
        
        Args:
            args: Dictionary of command-line arguments
            
        Returns:
            Response dictionary with results
        """
        # Parse addresses from JSON string if provided
        addresses = []
        if args.get('addresses'):
            try:
                addresses = json.loads(args['addresses'])
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "message": "Invalid JSON format for addresses",
                    "error_code": "invalid_format"
                }
        
        # Parse documents from JSON string if provided
        documents = []
        if args.get('documents'):
            try:
                documents = json.loads(args['documents'])
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "message": "Invalid JSON format for documents",
                    "error_code": "invalid_format"
                }
        
        # Parse custom fields from JSON string if provided
        custom_fields = {}
        if args.get('custom_fields'):
            try:
                custom_fields = json.loads(args['custom_fields'])
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "message": "Invalid JSON format for custom fields",
                    "error_code": "invalid_format"
                }
        
        # Create the request object
        request = CreateCustomerRequest(
            customer_type=args['customer_type'],
            first_name=args.get('first_name'),
            last_name=args.get('last_name'),
            middle_name=args.get('middle_name'),
            date_of_birth=args.get('date_of_birth'),
            company_name=args.get('company_name'),
            registration_number=args.get('registration_number'),
            tax_id=args.get('tax_id'),
            email=args.get('email'),
            primary_phone=args.get('primary_phone'),
            secondary_phone=args.get('secondary_phone'),
            addresses=addresses,
            documents=documents,
            custom_fields=custom_fields
        )
        
        # Execute the use case
        response = self.create_customer_use_case.execute(request)
        
        # Convert response to dictionary
        return {
            "success": response.success,
            "customer_id": response.customer_id,
            "message": response.message,
            "error_code": response.error_code,
            "validation_errors": response.validation_errors
        }
    
    def verify_customer_kyc(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify customer KYC from command-line arguments.
        
        Args:
            args: Dictionary of command-line arguments
            
        Returns:
            Response dictionary with results
        """
        # Parse documents from JSON string if provided
        documents_verified = []
        if args.get('documents_verified'):
            try:
                documents_verified = json.loads(args['documents_verified'])
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "message": "Invalid JSON format for documents_verified",
                    "error_code": "invalid_format"
                }
        
        # Create the request object
        request = VerifyCustomerKycRequest(
            customer_id=args['customer_id'],
            verify_kyc=args.get('verify_kyc', False),
            verify_aml=args.get('verify_aml', False),
            documents_verified=documents_verified,
            notes=args.get('notes')
        )
        
        # Execute the use case
        response = self.verify_customer_kyc_use_case.execute(request)
        
        # Convert response to dictionary
        return {
            "success": response.success,
            "is_fully_compliant": response.is_fully_compliant,
            "missing_documents": response.missing_documents,
            "expired_documents": response.expired_documents,
            "message": response.message,
            "error_code": response.error_code
        }
    
    def get_verification_requirements(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get verification requirements for a customer.
        
        Args:
            args: Dictionary of command-line arguments
            
        Returns:
            Response dictionary with results
        """
        return self.verify_customer_kyc_use_case.get_verification_requirements(args['customer_id'])


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description='Customer Management CLI')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Create customer command
    create_parser = subparsers.add_parser('create', help='Create a new customer')
    create_parser.add_argument('--customer_type', required=True, choices=['individual', 'corporate', 'joint', 'minor'],
                              help='Type of customer')
    create_parser.add_argument('--first_name', help='First name (required for individual customers)')
    create_parser.add_argument('--last_name', help='Last name (required for individual customers)')
    create_parser.add_argument('--middle_name', help='Middle name')
    create_parser.add_argument('--date_of_birth', help='Date of birth (YYYY-MM-DD, required for individual customers)')
    create_parser.add_argument('--company_name', help='Company name (required for corporate customers)')
    create_parser.add_argument('--registration_number', help='Registration number (required for corporate customers)')
    create_parser.add_argument('--tax_id', help='Tax ID or SSN')
    create_parser.add_argument('--email', help='Email address')
    create_parser.add_argument('--primary_phone', help='Primary phone number')
    create_parser.add_argument('--secondary_phone', help='Secondary phone number')
    create_parser.add_argument('--addresses', help='JSON array of address objects')
    create_parser.add_argument('--documents', help='JSON array of document objects')
    create_parser.add_argument('--custom_fields', help='JSON object of custom fields')
    
    # Verify KYC command
    verify_parser = subparsers.add_parser('verify', help='Verify customer KYC')
    verify_parser.add_argument('--customer_id', required=True, help='Customer ID')
    verify_parser.add_argument('--verify_kyc', action='store_true', help='Mark KYC as verified')
    verify_parser.add_argument('--verify_aml', action='store_true', help='Mark AML as cleared')
    verify_parser.add_argument('--documents_verified', help='JSON array of verified document objects')
    verify_parser.add_argument('--notes', help='Verification notes')
    
    # Get verification requirements command
    requirements_parser = subparsers.add_parser('requirements', help='Get verification requirements')
    requirements_parser.add_argument('--customer_id', required=True, help='Customer ID')
    
    return parser.parse_args()


def main():
    """Main entry point for the CLI"""
    args = parse_args()
    cli = CustomerManagementCli()
    
    try:
        if args.command == 'create':
            result = cli.create_customer(vars(args))
        elif args.command == 'verify':
            result = cli.verify_customer_kyc(vars(args))
        elif args.command == 'requirements':
            result = cli.get_verification_requirements(vars(args))
        else:
            result = {
                "success": False,
                "message": "Invalid command. Use 'create', 'verify', or 'requirements'."
            }
        
        # Output result as JSON
        print(json.dumps(result, indent=2, default=str))
        
        # Set exit code based on success
        sys.exit(0 if result.get("success", False) else 1)
        
    except Exception as e:
        print(json.dumps({
            "success": False,
            "message": f"An error occurred: {str(e)}",
            "error_code": "system_error"
        }, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
