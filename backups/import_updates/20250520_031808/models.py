from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, create_engine, Boolean, Date, Enum, Text, DECIMAL
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from utils.config import DATABASE_CONFIG
import enum
import datetime

# Create Base class for SQLAlchemy models
Base = declarative_base()

# Create MySQL connection URL from config
# Handle special characters in password with URL encoding
import urllib.parse

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path

password = urllib.parse.quote_plus(DATABASE_CONFIG['password'])
DB_URL = f"mysql+mysqlconnector://{DATABASE_CONFIG['user']}:{password}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"

# Create engine with proper error handling
try:
    engine = create_engine(DB_URL)
    print(f"Database engine created for {DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}")
except Exception as e:
    print(f"Error creating database engine: {e}")
    engine = None

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Enum classes for typed columns
class CustomerStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"

class KYCStatus(enum.Enum):
    PENDING = "PENDING"
    PARTIAL = "PARTIAL" 
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

class CustomerSegment(enum.Enum):
    RETAIL = "RETAIL"
    CORPORATE = "CORPORATE"
    PRIORITY = "PRIORITY"
    NRI = "NRI"
    SENIOR = "SENIOR"
    MINOR = "MINOR"
    STUDENT = "STUDENT"

class RiskCategory(enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class Gender(enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"
    PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY"

class AccountType(enum.Enum):
    SAVINGS = "SAVINGS"
    CURRENT = "CURRENT"
    FIXED_DEPOSIT = "FIXED_DEPOSIT"
    RECURRING_DEPOSIT = "RECURRING_DEPOSIT"
    LOAN = "LOAN"
    SALARY = "SALARY"
    NRI = "NRI"
    PENSION = "PENSION"
    CORPORATE = "CORPORATE" 
    JOINT = "JOINT"

class AccountStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    DORMANT = "DORMANT"
    FROZEN = "FROZEN"
    CLOSED = "CLOSED"
    SUSPENDED = "SUSPENDED"
    ONHOLD = "ONHOLD"

class AccountCategory(enum.Enum):
    REGULAR = "REGULAR"
    PREMIUM = "PREMIUM"
    ZERO_BALANCE = "ZERO_BALANCE"
    SENIOR_CITIZEN = "SENIOR_CITIZEN"
    STUDENT = "STUDENT"
    MINOR = "MINOR"

class CardType(enum.Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"
    PREPAID = "PREPAID"
    INTERNATIONAL = "INTERNATIONAL"
    VIRTUAL = "VIRTUAL"
    CORPORATE = "CORPORATE"
    TRAVEL = "TRAVEL"
    GIFT = "GIFT"
    COMMERCIAL = "COMMERCIAL"

class CardNetwork(enum.Enum):
    VISA = "VISA"
    MASTERCARD = "MASTERCARD"
    RUPAY = "RUPAY"
    AMEX = "AMEX"
    DINERS = "DINERS"
    JCB = "JCB"
    UNIONPAY = "UNIONPAY"
    DISCOVER = "DISCOVER"

class CardStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    BLOCKED = "BLOCKED"
    EXPIRED = "EXPIRED"
    HOTLISTED = "HOTLISTED"
    PENDING_ACTIVATION = "PENDING_ACTIVATION"
    SUSPENDED = "SUSPENDED"

class ChipType(enum.Enum):
    EMV = "EMV"
    CONTACTLESS = "CONTACTLESS"
    MAGSTRIPE = "MAGSTRIPE"

class TransactionType(enum.Enum):
    WITHDRAWAL = "WITHDRAWAL"
    DEPOSIT = "DEPOSIT"
    TRANSFER = "TRANSFER"
    PAYMENT = "PAYMENT"
    BALANCE_INQUIRY = "BALANCE_INQUIRY"
    MINI_STATEMENT = "MINI_STATEMENT"
    PIN_CHANGE = "PIN_CHANGE"
    CHEQUE_DEPOSIT = "CHEQUE_DEPOSIT"
    INTEREST_CREDIT = "INTEREST_CREDIT"
    FEE_DEBIT = "FEE_DEBIT"
    REVERSAL = "REVERSAL"
    REFUND = "REFUND"
    EMI_PAYMENT = "EMI_PAYMENT"
    BILL_PAYMENT = "BILL_PAYMENT"
    LOAN_DISBURSEMENT = "LOAN_DISBURSEMENT"
    GST_TAX = "GST_TAX"
    TDS_DEDUCTION = "TDS_DEDUCTION"
    DIVIDEND = "DIVIDEND"
    CASHBACK = "CASHBACK"
    REWARD_REDEMPTION = "REWARD_REDEMPTION"
    CHARGEBACK = "CHARGEBACK"
    EXCHANGE = "EXCHANGE"

class TransactionChannel(enum.Enum):
    ATM = "ATM"
    BRANCH = "BRANCH"
    INTERNET = "INTERNET"
    MOBILE = "MOBILE"
    POS = "POS"
    UPI = "UPI"
    IMPS = "IMPS"
    NEFT = "NEFT"
    RTGS = "RTGS"
    CHEQUE = "CHEQUE"
    CASH = "CASH"
    STANDING_INSTRUCTION = "STANDING_INSTRUCTION"
    API = "API"
    PHONE_BANKING = "PHONE_BANKING"
    BILLDESK = "BILLDESK"
    AUTO_DEBIT = "AUTO_DEBIT"
    POS_INTERNATIONAL = "POS_INTERNATIONAL"
    E_COMMERCE = "E_COMMERCE"
    BULK_UPLOAD = "BULK_UPLOAD"

class TransactionStatus(enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REVERSED = "REVERSED"
    DISPUTED = "DISPUTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    SETTLED = "SETTLED"
    AUTHORIZED = "AUTHORIZED"
    CANCELLED = "CANCELLED"
    TIMEOUT = "TIMEOUT"
    SCHEDULED = "SCHEDULED"

# Enhanced models for the new schema
class Customer(Base):
    __tablename__ = 'cbs_customers'
    
    customer_id = Column(String(20), primary_key=True, 
                       comment="Format: YYDDD-BBBBB-SSSS (YY=year, DDD=day of year, BBBBB=branch, SSSS=sequence)")
    name = Column(String(100), nullable=False)
    dob = Column(Date, nullable=False)
    address = Column(String(255), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    phone = Column(String(20), nullable=False)
    status = Column(Enum(CustomerStatus), nullable=False, default=CustomerStatus.ACTIVE)
    registration_date = Column(DateTime, default=datetime.datetime.utcnow())
    kyc_status = Column(Enum(KYCStatus), nullable=False, default=KYCStatus.PENDING)
    kyc_expiry_date = Column(Date)
    pan_number = Column(String(10))
    aadhar_number = Column(String(12))
    customer_segment = Column(Enum(CustomerSegment), nullable=False, default=CustomerSegment.RETAIL)
    credit_score = Column(Integer)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow(), onupdate=datetime.datetime.utcnow())
    risk_category = Column(Enum(RiskCategory), default=RiskCategory.MEDIUM)
    fatca_compliance = Column(Boolean, default=False)
    consent_marketing = Column(Boolean, default=False)
    gender = Column(Enum(Gender), nullable=False)
    nationality = Column(String(50), default="Indian")
    occupation = Column(String(100))
    annual_income = Column(DECIMAL(14,2))
    
    # Relationships
    accounts = relationship("Account", back_populates="customer")
    mobile_users = relationship("MobileUser", back_populates="customer")

class Account(Base):
    __tablename__ = 'cbs_accounts'
    
    account_number = Column(String(20), primary_key=True, 
                          comment="Format: BBBBB-AATT-CCCCCC-CC (BBBBB=branch, AA=account type, TT=subtype, CCCCCC=customer, CC=checksum)")
    customer_id = Column(String(20), ForeignKey('cbs_customers.customer_id'), nullable=False)
    account_type = Column(Enum(AccountType), nullable=False)
    branch_code = Column(String(20), nullable=False)
    ifsc_code = Column(String(20), nullable=False, 
                     comment="Format: AAAA0CCDDD (AAAA=bank code, 0=reserved, CC=city code, DDD=branch code)")
    opening_date = Column(DateTime, default=datetime.datetime.utcnow())
    balance = Column(DECIMAL(12,2), nullable=False, default=0.00)
    interest_rate = Column(DECIMAL(5,2))
    status = Column(Enum(AccountStatus), nullable=False, default=AccountStatus.ACTIVE)
    last_transaction = Column(DateTime, default=datetime.datetime.utcnow())
    nominee_name = Column(String(100))
    nominee_relation = Column(String(50))
    service_charges_applicable = Column(Boolean, default=True)
    minimum_balance = Column(DECIMAL(10,2), default=1000.00)
    overdraft_limit = Column(DECIMAL(12,2), default=0.00)
    joint_holders = Column(String(255))
    account_category = Column(Enum(AccountCategory), default=AccountCategory.REGULAR)
    account_manager = Column(String(50))
    sweep_in_facility = Column(Boolean, default=False)
    sweep_out_facility = Column(Boolean, default=False)
    sweep_account = Column(String(20))
    auto_renewal = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow())
    closing_date = Column(DateTime)
    closing_reason = Column(String(255))
    
    # Relationships
    customer = relationship("Customer", back_populates="accounts")
    cards = relationship("Card", back_populates="account")
    transactions = relationship("Transaction", back_populates="account")

class Card(Base):
    __tablename__ = 'cbs_cards'
    
    card_id = Column(String(20), primary_key=True)
    account_id = Column(String(20), ForeignKey('cbs_accounts.account_number'), nullable=False)
    card_number = Column(String(20), nullable=False, unique=True)
    card_type = Column(Enum(CardType), nullable=False)
    card_network = Column(Enum(CardNetwork), nullable=False)
    expiry_date = Column(Date, nullable=False)
    cvv = Column(String(3), nullable=False)
    pin_hash = Column(String(128), nullable=False)
    status = Column(Enum(CardStatus), nullable=False, default=CardStatus.PENDING_ACTIVATION)
    issue_date = Column(Date, nullable=False)
    daily_atm_limit = Column(DECIMAL(10,2), nullable=False, default=10000.00)
    daily_pos_limit = Column(DECIMAL(10,2), nullable=False, default=50000.00)
    daily_online_limit = Column(DECIMAL(10,2), nullable=False, default=30000.00)
    primary_user_name = Column(String(100), nullable=False)
    international_usage_enabled = Column(Boolean, default=False)
    contactless_enabled = Column(Boolean, default=True)
    credit_limit = Column(DECIMAL(12,2))
    available_credit = Column(DECIMAL(12,2))
    reward_points = Column(Integer, default=0)
    billing_date = Column(Integer)
    due_date_offset = Column(Integer)
    card_variant = Column(String(50))
    chip_type = Column(Enum(ChipType), default=ChipType.EMV)
    virtual_card_linked = Column(Boolean, default=False)
    activation_date = Column(DateTime)
    otp_enabled = Column(Boolean, default=True)
    
    # Relationships
    account = relationship("Account", back_populates="cards")
    transactions = relationship("Transaction", back_populates="card")
    withdrawals = relationship("DailyWithdrawal", back_populates="card")

class Transaction(Base):
    __tablename__ = 'cbs_transactions'
    
    transaction_id = Column(String(36), primary_key=True, 
                          comment="Format: TRX-YYYYMMDD-SSSSSS (TRX=prefix, YYYYMMDD=date, SSSSSS=sequence)")
    card_number = Column(String(20), ForeignKey('cbs_cards.card_number'), nullable=True)
    account_number = Column(String(20), ForeignKey('cbs_accounts.account_number'), nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    channel = Column(Enum(TransactionChannel), nullable=False)
    amount = Column(DECIMAL(12,2), nullable=False, default=0.00)
    currency = Column(String(3), default="INR")
    balance_before = Column(DECIMAL(12,2), nullable=False)
    balance_after = Column(DECIMAL(12,2), nullable=False)
    transaction_date = Column(DateTime, default=datetime.datetime.utcnow())
    value_date = Column(Date, nullable=False)
    status = Column(Enum(TransactionStatus), nullable=False, default=TransactionStatus.PENDING)
    reference_number = Column(String(50),
                            comment="Format: REF-YYMMDD-NNNNNNNN (YYMMDD=date, NNNNNNNN=sequence)")
    remarks = Column(String(255))
    transaction_location = Column(String(255))
    merchant_category_code = Column(String(4))
    merchant_name = Column(String(100))
    sender_details = Column(String(255))
    receiver_details = Column(String(255))
    transaction_fee = Column(DECIMAL(10,2), default=0.00)
    tax_amount = Column(DECIMAL(10,2), default=0.00)
    exchange_rate = Column(DECIMAL(12,6))
    original_amount = Column(DECIMAL(12,2))
    original_currency = Column(String(3))
    batch_id = Column(String(50))
    response_code = Column(String(10))
    processing_time = Column(Integer)
    device_id = Column(String(100))
    ip_address = Column(String(45))
    
    # Relationships
    card = relationship("Card", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")
    bill_payments = relationship("BillPayment", back_populates="transaction")
    transfers = relationship("Transfer", back_populates="transaction")

class DailyWithdrawal(Base):
    __tablename__ = 'cbs_daily_withdrawals'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    card_number = Column(String(20), ForeignKey('cbs_cards.card_number'), nullable=False)
    amount = Column(DECIMAL(10,2), nullable=False)
    withdrawal_date = Column(Date, nullable=False)
    withdrawal_time = Column(DateTime, default=datetime.datetime.utcnow())
    atm_id = Column(String(20))
    location = Column(String(255))
    status = Column(String(20), nullable=False, default='COMPLETED')
    suspicious_flag = Column(Boolean, default=False)
    response_code = Column(String(10))
    balance_after_withdrawal = Column(DECIMAL(12,2))
    
    # Relationships
    card = relationship("Card", back_populates="withdrawals")

class BillPayment(Base):
    __tablename__ = 'cbs_bill_payments'
    
    payment_id = Column(String(36), primary_key=True)
    transaction_id = Column(String(36), ForeignKey('cbs_transactions.transaction_id'), nullable=False)
    customer_id = Column(String(20), ForeignKey('cbs_customers.customer_id'), nullable=False)
    biller_id = Column(String(50), nullable=False)
    biller_name = Column(String(100), nullable=False)
    biller_category = Column(String(20), nullable=False)
    consumer_id = Column(String(50), nullable=False)
    bill_amount = Column(DECIMAL(12,2), nullable=False)
    due_date = Column(Date)
    payment_date = Column(DateTime, default=datetime.datetime.utcnow())
    payment_channel = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default='PENDING')
    receipt_number = Column(String(50))
    convenience_fee = Column(DECIMAL(10,2), default=0.00)
    bill_period_from = Column(Date)
    bill_period_to = Column(Date)
    bill_number = Column(String(50))
    autopay_enabled = Column(Boolean, default=False)
    autopay_limit = Column(DECIMAL(12,2))
    retry_count = Column(Integer, default=0)
    next_retry_date = Column(DateTime)
    
    # Relationships
    transaction = relationship("Transaction", back_populates="bill_payments")
    customer = relationship("Customer")

class Transfer(Base):
    __tablename__ = 'cbs_transfers'
    
    transfer_id = Column(String(36), primary_key=True)
    transaction_id = Column(String(36), ForeignKey('cbs_transactions.transaction_id'), nullable=False)
    source_account = Column(String(20), ForeignKey('cbs_accounts.account_number'), nullable=False)
    destination_account = Column(String(20), nullable=False)
    beneficiary_name = Column(String(100))
    beneficiary_bank = Column(String(100))
    beneficiary_ifsc = Column(String(20))
    transfer_type = Column(String(20), nullable=False)
    amount = Column(DECIMAL(12,2), nullable=False)
    transfer_date = Column(DateTime, default=datetime.datetime.utcnow())
    processing_date = Column(DateTime)
    status = Column(String(20), nullable=False, default='INITIATED')
    reference_number = Column(String(50))
    purpose_code = Column(String(4))
    remarks = Column(String(255))
    charges = Column(DECIMAL(10,2), default=0.00)
    scheduled_transfer = Column(Boolean, default=False)
    recurring_transfer = Column(Boolean, default=False)
    frequency = Column(String(20))
    next_execution_date = Column(Date)
    max_attempts = Column(Integer, default=3)
    current_attempt = Column(Integer, default=0)
    remitter_to_beneficiary_info = Column(String(255))
    regulatory_info = Column(String(255))
    foreign_exchange_rate = Column(DECIMAL(12,6))
    intermediary_bank = Column(String(100))
    correspondence_charges = Column(String(3), default='SHA')
    
    # Relationships
    transaction = relationship("Transaction", back_populates="transfers")

class AdminUser(Base):
    __tablename__ = 'cbs_admin_users'
    
    admin_id = Column(String(20), primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    password_hash = Column(String(128), nullable=False)
    salt = Column(String(64), nullable=False)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    mobile = Column(String(20), nullable=False)
    department = Column(String(50), nullable=False)
    branch_code = Column(String(20), nullable=False)
    employee_id = Column(String(12), nullable=False, unique=True, 
                       comment="Format: ZZBB-DD-EEEE (ZZ=zone code, BB=branch code, DD=designation, EEEE=sequence)")
    role = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default='PENDING_ACTIVATION')
    password_expiry_date = Column(Date, nullable=False)
    account_locked = Column(Boolean, default=False)
    failed_login_attempts = Column(Integer, default=0)
    last_login = Column(DateTime)
    last_password_change = Column(DateTime)
    access_level = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.datetime.utcnow())
    created_by = Column(String(20))
    updated_at = Column(DateTime, default=datetime.datetime.utcnow(), onupdate=datetime.datetime.utcnow())
    updated_by = Column(String(20))
    requires_2fa = Column(Boolean, default=True)
    two_fa_method = Column(String(20), default='SMS')
    two_fa_secret = Column(String(128))
    direct_reports = Column(String(255))
    permissions = Column(Text)
    session_timeout_minutes = Column(Integer, default=15)
    ip_restriction = Column(String(255))
    allowed_login_times = Column(String(255))
    last_security_training = Column(Date)
    security_questions_answered = Column(Boolean, default=False)
    out_of_office = Column(Boolean, default=False)
    delegate_to = Column(String(20))
    biometric_registered = Column(Boolean, default=False)
    profile_picture = Column(String(255))

class MobileUser(Base):
    __tablename__ = 'cbs_mobile_users'
    
    mobile_user_id = Column(String(36), primary_key=True)
    customer_id = Column(String(20), ForeignKey('cbs_customers.customer_id'), nullable=False)
    username = Column(String(50), unique=True)
    password_hash = Column(String(128), nullable=False)
    salt = Column(String(64), nullable=False)
    device_id = Column(String(100))
    device_model = Column(String(100))
    os_type = Column(String(20), nullable=False)
    os_version = Column(String(20))
    app_version = Column(String(20), nullable=False)
    fcm_token = Column(String(255))
    biometric_enabled = Column(Boolean, default=False)
    pin_enabled = Column(Boolean, default=False)
    pin_hash = Column(String(128))
    status = Column(String(20), default='PENDING_ACTIVATION')
    failed_login_attempts = Column(Integer, default=0)
    last_login = Column(DateTime)
    registered_at = Column(DateTime, default=datetime.datetime.utcnow())
    last_activity = Column(DateTime)
    preferred_language = Column(String(10), default='en')
    notification_preferences = Column(Text)
    two_fa_enabled = Column(Boolean, default=True)
    two_fa_type = Column(String(20), default='SMS')
    two_fa_secret = Column(String(128))
    location_services_enabled = Column(Boolean, default=False)
    last_password_change = Column(DateTime)
    activated_at = Column(DateTime)
    activated_by = Column(String(20))
    account_limit_override = Column(Text)
    
    # Relationships
    customer = relationship("Customer", back_populates="mobile_users")

# Maintain compatibility with legacy code that might still use old model names
User = Customer
ATMCard = Card


def initialize_database():
    """Initialize the database and create tables if they don't exist"""
    try:
        # Create all tables defined in the models
        Base.metadata.create_all(engine)
        print("Database tables created successfully")
        # Create an admin user if it doesn't exist
        session = SessionLocal()
        admin_exists = session.query(AdminUser).filter_by(username="admin").first()
        
        if not admin_exists:
            # Create default admin account
            from utils.encryption import hash_password
            import uuid
            import hashlib
            
            # Generate a salt for password hashing
            salt = hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()
            
            # Create a default admin user
            admin = AdminUser(
                admin_id=str(uuid.uuid4())[:20],
                username="admin",
                password_hash=hash_password("admin123"),  # Default password, should be changed
                salt=salt,
                full_name="System Administrator",
                email="admin@cbs.local",
                mobile="9999999999",
                department="IT",
                branch_code="HO001",
                employee_id="EMP001",
                role="super_admin",
                status="ACTIVE",
                password_expiry_date=datetime.datetime.now() + datetime.timedelta(days=90)
            )
            session.add(admin)
            session.commit()
            print("Default admin user created")
        
        session.close()
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False
