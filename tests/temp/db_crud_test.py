"""
Temporary test script for testing data operations (CRUD) on database
Created: May 13, 2025
"""
import sys
import os
import uuid
import datetime

# Add the project root to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.db_manager import get_db_session
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

class DatabaseTester:
    """Class for testing database CRUD operations"""
    
    def __init__(self):
        """Initialize the tester"""
        self.session = None
        self.test_data = {}
    
    def connect(self):
        """Connect to the database"""
        print("🔌 Connecting to database...")
        try:
            self.session = get_db_session()
            db_name = self.session.execute(text("SELECT DATABASE()")).scalar()
            print(f"✅ Connected to database: {db_name}")
            return True
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def disconnect(self):
        """Close the database connection"""
        if self.session:
            self.session.close()
            print("🔌 Database connection closed")
    
    def test_create(self):
        """Test creating records"""
        print("\n🔍 Testing CREATE operations")
        
        if not self.session:
            print("❌ No database session")
            return
        
        try:
            # Create a test customer
            customer_id = f"TST{uuid.uuid4().hex[:8].upper()}"
            current_date = datetime.datetime.now().strftime("%Y-%m-%d")
            
            # Check if the customer already exists
            check_query = text("SELECT COUNT(*) FROM cbs_customers WHERE customer_id = :cid")
            count = self.session.execute(check_query, {"cid": customer_id}).scalar()
            
            if count > 0:
                print(f"⚠️ Customer {customer_id} already exists!")
                return
            
            # Create customer query
            query = text("""
                INSERT INTO cbs_customers (
                    customer_id, name, dob, address, email, phone, 
                    status, registration_date, kyc_status, customer_segment, gender
                ) VALUES (
                    :cid, :name, :dob, :addr, :email, :phone,
                    :status, :reg_date, :kyc, :segment, :gender
                )
            """)
            
            # Execute query
            self.session.execute(query, {
                "cid": customer_id,
                "name": "Test Customer",
                "dob": "1990-01-01",
                "addr": "123 Test Street, Test City",
                "email": f"test{uuid.uuid4().hex[:8]}@example.com",
                "phone": "9876543210",
                "status": "ACTIVE",
                "reg_date": current_date,
                "kyc": "PENDING",
                "segment": "RETAIL",
                "gender": "OTHER"
            })
            
            self.session.commit()
            print(f"✅ Created test customer: {customer_id}")
            
            # Store test data for later use
            self.test_data["customer_id"] = customer_id
            
            # Create a test account for the customer
            account_number = f"ACC{uuid.uuid4().hex[:10].upper()}"
            
            # Create account query
            query = text("""
                INSERT INTO cbs_accounts (
                    account_number, customer_id, account_type, branch_code, ifsc_code,
                    opening_date, balance, interest_rate, status, last_transaction,
                    minimum_balance, account_category
                ) VALUES (
                    :acc_num, :cid, :acc_type, :branch, :ifsc,
                    :open_date, :balance, :interest, :status, :last_txn,
                    :min_bal, :category
                )
            """)
            
            # Execute query
            self.session.execute(query, {
                "acc_num": account_number,
                "cid": customer_id,
                "acc_type": "SAVINGS",
                "branch": "BR001",
                "ifsc": "CBSPYTHON001",
                "open_date": current_date,
                "balance": 1000.00,
                "interest": 3.5,
                "status": "ACTIVE",
                "last_txn": current_date,
                "min_bal": 500.00,
                "category": "REGULAR"
            })
            
            self.session.commit()
            print(f"✅ Created test account: {account_number}")
            
            # Store test data for later use
            self.test_data["account_number"] = account_number
            
            return True
            
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"❌ Error creating test records: {e}")
            return False
    
    def test_read(self):
        """Test reading records"""
        print("\n🔍 Testing READ operations")
        
        if not self.session or not self.test_data:
            print("❌ No database session or test data")
            return
        
        try:
            # Read customer by ID
            customer_id = self.test_data.get("customer_id")
            if customer_id:
                query = text("SELECT * FROM cbs_customers WHERE customer_id = :cid")
                customer = self.session.execute(query, {"cid": customer_id}).fetchone()
                
                if customer:
                    print(f"✅ Found customer: {customer_id}")
                    print(f"  - Name: {customer.name}")
                    print(f"  - Email: {customer.email}")
                    print(f"  - Status: {customer.status}")
                else:
                    print(f"❌ Customer not found: {customer_id}")
            
            # Read account by account number
            account_number = self.test_data.get("account_number")
            if account_number:
                query = text("SELECT * FROM cbs_accounts WHERE account_number = :acc_num")
                account = self.session.execute(query, {"acc_num": account_number}).fetchone()
                
                if account:
                    print(f"✅ Found account: {account_number}")
                    print(f"  - Type: {account.account_type}")
                    print(f"  - Balance: {account.balance}")
                    print(f"  - Status: {account.status}")
                else:
                    print(f"❌ Account not found: {account_number}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error reading records: {e}")
            return False
    
    def test_update(self):
        """Test updating records"""
        print("\n🔍 Testing UPDATE operations")
        
        if not self.session or not self.test_data:
            print("❌ No database session or test data")
            return
        
        try:
            # Update customer name
            customer_id = self.test_data.get("customer_id")
            if customer_id:
                query = text("""
                    UPDATE cbs_customers 
                    SET name = :name, last_updated = :updated
                    WHERE customer_id = :cid
                """)
                
                result = self.session.execute(query, {
                    "name": "Updated Test Customer",
                    "updated": datetime.datetime.now(),
                    "cid": customer_id
                })
                
                self.session.commit()
                print(f"✅ Updated customer name: {customer_id} (Rows affected: {result.rowcount})")
            
            # Update account balance
            account_number = self.test_data.get("account_number")
            if account_number:
                # First get current balance
                query = text("SELECT balance FROM cbs_accounts WHERE account_number = :acc_num")
                current_balance = self.session.execute(query, {"acc_num": account_number}).scalar()
                
                # Update balance
                new_balance = current_balance + 500.00
                query = text("""
                    UPDATE cbs_accounts 
                    SET balance = :balance, last_transaction = :updated
                    WHERE account_number = :acc_num
                """)
                
                result = self.session.execute(query, {
                    "balance": new_balance,
                    "updated": datetime.datetime.now(),
                    "acc_num": account_number
                })
                
                self.session.commit()
                print(f"✅ Updated account balance: {account_number} (New balance: {new_balance})")
            
            return True
            
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"❌ Error updating records: {e}")
            return False
    
    def test_delete(self):
        """Test deleting records (or marking as deleted)"""
        print("\n🔍 Testing DELETE operations")
        
        if not self.session or not self.test_data:
            print("❌ No database session or test data")
            return
        
        try:
            # Instead of actually deleting, mark account as CLOSED
            account_number = self.test_data.get("account_number")
            if account_number:
                query = text("""
                    UPDATE cbs_accounts 
                    SET status = 'CLOSED', closing_date = :close_date
                    WHERE account_number = :acc_num
                """)
                
                result = self.session.execute(query, {
                    "close_date": datetime.datetime.now(),
                    "acc_num": account_number
                })
                
                self.session.commit()
                print(f"✅ Marked account as CLOSED: {account_number}")
            
            # Mark customer as INACTIVE
            customer_id = self.test_data.get("customer_id")
            if customer_id:
                query = text("""
                    UPDATE cbs_customers 
                    SET status = 'INACTIVE', last_updated = :updated
                    WHERE customer_id = :cid
                """)
                
                result = self.session.execute(query, {
                    "updated": datetime.datetime.now(),
                    "cid": customer_id
                })
                
                self.session.commit()
                print(f"✅ Marked customer as INACTIVE: {customer_id}")
            
            return True
            
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"❌ Error in delete operations: {e}")
            return False

    def run_all_tests(self):
        """Run all database tests"""
        print("\n" + "="*60)
        print("RUNNING DATABASE CRUD OPERATION TESTS")
        print("="*60)
        
        try:
            # Connect to database
            if not self.connect():
                return
            
            # Run tests
            create_success = self.test_create()
            if create_success:
                self.test_read()
                self.test_update()
                self.test_delete()
            
            # Verify final state
            if create_success:
                self.test_read()
                
        finally:
            # Close connection
            self.disconnect()
            
        print("\n" + "="*60)
        print("CRUD TESTS COMPLETED")
        print("="*60)

if __name__ == "__main__":
    tester = DatabaseTester()
    tester.run_all_tests()
