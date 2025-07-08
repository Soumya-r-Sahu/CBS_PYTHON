"""
CLI interface for UPI payments.
"""
import cmd
import uuid
from datetime import date
from typing import Optional

from ...application.use_cases.send_money_use_case import SendMoneyUseCase, SendMoneyRequest
from ...application.use_cases.complete_transaction_use_case import CompleteTransactionUseCase, CompleteTransactionRequest
from ...domain.entities.upi_transaction import UpiTransactionStatus


class UpiCli(cmd.Cmd):
    """Command-line interface for UPI payments."""
    
    intro = """
    ╔════════════════════════════════════════╗
    ║         🚀 UPI Payment System          ║
    ╚════════════════════════════════════════╝
    
    Type 'help' or '?' to list commands.
    Type 'exit' or 'quit' to exit.
    """
    
    prompt = "UPI > "
    
    def __init__(
        self,
        send_money_use_case: SendMoneyUseCase,
        complete_transaction_use_case: CompleteTransactionUseCase
    ):
        """
        Initialize with required use cases.
        
        Args:
            send_money_use_case: Use case for sending money
            complete_transaction_use_case: Use case for completing transactions
        """
        super().__init__()
        self.send_money_use_case = send_money_use_case
        self.complete_transaction_use_case = complete_transaction_use_case
        
        # Store last transaction for convenience
        self.last_transaction_id = None
    
    def do_send(self, arg):
        """
        Send money via UPI.
        
        Usage: send <sender_vpa> <receiver_vpa> <amount> [remarks]
        Example: send john@oksbi jane@okicici 1000 "Birthday gift"
        """
        args = arg.split(maxsplit=3)
        
        # Check arguments
        if len(args) < 3:
            print("Error: Not enough arguments. See 'help send' for usage.")
            return
        
        sender_vpa = args[0]
        receiver_vpa = args[1]
        
        # Parse amount
        try:
            amount = float(args[2])
        except ValueError:
            print("Error: Amount must be a number.")
            return
        
        # Get remarks if provided
        remarks = args[3] if len(args) > 3 else None
        
        # Strip quotes from remarks if present
        if remarks and (
            (remarks.startswith('"') and remarks.endswith('"')) or
            (remarks.startswith("'") and remarks.endswith("'"))
        ):
            remarks = remarks[1:-1]
        
        # Create request
        request = SendMoneyRequest(
            sender_vpa=sender_vpa,
            receiver_vpa=receiver_vpa,
            amount=amount,
            remarks=remarks
        )
        
        # Execute use case
        response = self.send_money_use_case.execute(request)
        
        # Display response
        if response.success:
            self.last_transaction_id = response.transaction_id
            print(f"\n✅ {response.message}")
            print(f"Transaction ID: {response.transaction_id}\n")
        else:
            print(f"\n❌ Error: {response.message}")
            if response.error_code:
                print(f"Error code: {response.error_code}\n")
    
    def do_complete(self, arg):
        """
        Complete a UPI transaction.
        
        Usage: complete <transaction_id> <reference_id>
        Example: complete 550e8400-e29b-41d4-a716-446655440000 REF123456789
        
        If no transaction_id is provided, the last transaction will be used.
        """
        args = arg.split()
        
        # Check arguments
        if len(args) < 1:
            print("Error: Not enough arguments. See 'help complete' for usage.")
            return
        
        # Get transaction ID
        if args[0].lower() == 'last' and self.last_transaction_id:
            transaction_id = self.last_transaction_id
            reference_id = args[1] if len(args) > 1 else f"REF{uuid.uuid4().hex[:10]}"
        elif len(args) < 2:
            print("Error: Reference ID is required. See 'help complete' for usage.")
            return
        else:
            # Parse transaction ID
            try:
                transaction_id = uuid.UUID(args[0])
            except ValueError:
                print("Error: Invalid transaction ID format.")
                return
            
            reference_id = args[1]
        
        # Create request
        request = CompleteTransactionRequest(
            transaction_id=transaction_id,
            reference_id=reference_id
        )
        
        # Execute use case
        response = self.complete_transaction_use_case.execute(request)
        
        # Display response
        if response.success:
            print(f"\n✅ {response.message}")
            print(f"Reference ID: {reference_id}\n")
        else:
            print(f"\n❌ Error: {response.message}")
            if response.error_code:
                print(f"Error code: {response.error_code}\n")
    
    def do_exit(self, arg):
        """Exit the UPI CLI."""
        print("\nThank you for using UPI Payment System. Goodbye!")
        return True
    
    def do_quit(self, arg):
        """Exit the UPI CLI."""
        return self.do_exit(arg)
    
    def emptyline(self):
        """Do nothing on empty line."""
        pass
