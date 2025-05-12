-- Core Banking System Enhanced Database Schema
-- Generated: May 10, 2025
-- Modified for improved phpMyAdmin compatibility with new features

-- Enable strict mode for better data integrity
SET sql_mode = 'STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION';

-- Start transaction for atomic execution
START TRANSACTION;

-- Database creation (comment out if creating through phpMyAdmin interface)
CREATE DATABASE IF NOT EXISTS core_banking_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE core_banking_system;

-- =============================================
-- CORE DATA TABLES
-- =============================================

-- Create customers table with enhanced KYC support
CREATE TABLE cbs_customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    dob DATE NOT NULL,
    address VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL,
    status ENUM('ACTIVE', 'INACTIVE', 'SUSPENDED', 'CLOSED') NOT NULL DEFAULT 'ACTIVE',
    registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    kyc_status ENUM('PENDING', 'PARTIAL', 'COMPLETED', 'REJECTED', 'EXPIRED') NOT NULL DEFAULT 'PENDING',
    kyc_expiry_date DATE, -- NEW: KYC document expiry tracking
    pan_number VARCHAR(10),
    aadhar_number VARCHAR(12),
    customer_segment ENUM('RETAIL', 'CORPORATE', 'PRIORITY', 'NRI', 'SENIOR', 'MINOR', 'STUDENT') NOT NULL DEFAULT 'RETAIL', -- ENHANCED: more segments
    credit_score INT, -- NEW: Credit scoring
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    risk_category ENUM('LOW', 'MEDIUM', 'HIGH') DEFAULT 'MEDIUM', -- NEW: Risk categorization
    fatca_compliance BOOLEAN DEFAULT FALSE, -- NEW: FATCA compliance flag
    consent_marketing BOOLEAN DEFAULT FALSE, -- NEW: Marketing consent
    gender ENUM('MALE', 'FEMALE', 'OTHER', 'PREFER_NOT_TO_SAY') NOT NULL, -- NEW: Gender field
    nationality VARCHAR(50) DEFAULT 'Indian', -- NEW: Nationality
    occupation VARCHAR(100), -- NEW: Occupation details
    annual_income DECIMAL(14,2), -- NEW: Annual income
    INDEX idx_customer_status (status),
    INDEX idx_customer_email (email),
    INDEX idx_customer_phone (phone),
    INDEX idx_customer_segment (customer_segment),
    INDEX idx_customer_kyc (kyc_status),
    INDEX idx_customer_risk (risk_category)
) ENGINE=InnoDB;

-- Create accounts table with enhanced features
CREATE TABLE cbs_accounts (
    account_number VARCHAR(20) PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL,
    account_type ENUM('SAVINGS', 'CURRENT', 'FIXED_DEPOSIT', 'RECURRING_DEPOSIT', 'LOAN', 'SALARY', 'NRI', 'PENSION', 'CORPORATE', 'JOINT') NOT NULL, -- ENHANCED: more account types
    branch_code VARCHAR(20) NOT NULL,
    ifsc_code VARCHAR(20) NOT NULL,
    opening_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    balance DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    interest_rate DECIMAL(5,2),
    status ENUM('ACTIVE', 'DORMANT', 'FROZEN', 'CLOSED', 'SUSPENDED', 'ONHOLD') NOT NULL DEFAULT 'ACTIVE', -- ENHANCED: more statuses
    last_transaction DATETIME DEFAULT CURRENT_TIMESTAMP,
    nominee_name VARCHAR(100),
    nominee_relation VARCHAR(50),
    service_charges_applicable BOOLEAN DEFAULT TRUE,
    minimum_balance DECIMAL(10,2) DEFAULT 1000.00, -- NEW: Minimum balance requirement
    overdraft_limit DECIMAL(12,2) DEFAULT 0.00, -- NEW: Overdraft limit for eligible accounts
    joint_holders VARCHAR(255), -- NEW: For joint accounts
    account_category ENUM('REGULAR', 'PREMIUM', 'ZERO_BALANCE', 'SENIOR_CITIZEN', 'STUDENT', 'MINOR') DEFAULT 'REGULAR', -- NEW: Account categories
    account_manager VARCHAR(50), -- NEW: Relationship manager assignment
    sweep_in_facility BOOLEAN DEFAULT FALSE, -- NEW: Sweep-in feature
    sweep_out_facility BOOLEAN DEFAULT FALSE, -- NEW: Sweep-out feature
    sweep_account VARCHAR(20), -- NEW: Linked sweep account
    auto_renewal BOOLEAN DEFAULT FALSE, -- NEW: Auto-renewal for deposits
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    closing_date DATETIME, -- NEW: Account closing date
    closing_reason VARCHAR(255), -- NEW: Reason for closing
    FOREIGN KEY (customer_id) REFERENCES cbs_customers(customer_id),
    INDEX idx_account_customer (customer_id),
    INDEX idx_account_status (status),
    INDEX idx_account_type (account_type),
    INDEX idx_branch_code (branch_code),
    INDEX idx_account_category (account_category)
) ENGINE=InnoDB;

-- Create cards table with enhanced security
CREATE TABLE cbs_cards (
    card_id VARCHAR(20) PRIMARY KEY,
    account_id VARCHAR(20) NOT NULL,
    card_number VARCHAR(20) NOT NULL UNIQUE,
    card_type ENUM('DEBIT', 'CREDIT', 'PREPAID', 'INTERNATIONAL', 'VIRTUAL', 'CORPORATE', 'TRAVEL', 'GIFT', 'COMMERCIAL') NOT NULL, -- ENHANCED: more card types
    card_network ENUM('VISA', 'MASTERCARD', 'RUPAY', 'AMEX', 'DINERS', 'JCB', 'UNIONPAY', 'DISCOVER') NOT NULL, -- ENHANCED: more networks
    expiry_date DATE NOT NULL,
    cvv VARCHAR(3) NOT NULL,
    pin_hash VARCHAR(128) NOT NULL,
    status ENUM('ACTIVE', 'INACTIVE', 'BLOCKED', 'EXPIRED', 'HOTLISTED', 'PENDING_ACTIVATION', 'SUSPENDED') NOT NULL DEFAULT 'PENDING_ACTIVATION', -- ENHANCED: more statuses
    issue_date DATE NOT NULL,
    daily_atm_limit DECIMAL(10,2) NOT NULL DEFAULT 10000.00,
    daily_pos_limit DECIMAL(10,2) NOT NULL DEFAULT 50000.00,
    daily_online_limit DECIMAL(10,2) NOT NULL DEFAULT 30000.00,
    primary_user_name VARCHAR(100) NOT NULL,
    international_usage_enabled BOOLEAN DEFAULT FALSE,
    contactless_enabled BOOLEAN DEFAULT TRUE,
    credit_limit DECIMAL(12,2), -- NEW: For credit cards
    available_credit DECIMAL(12,2), -- NEW: Available credit
    reward_points INT DEFAULT 0, -- NEW: Loyalty reward points
    billing_date INT, -- NEW: For credit cards (day of month)
    due_date_offset INT, -- NEW: Days after billing date
    card_variant VARCHAR(50), -- NEW: Card variant (Gold, Platinum, etc)
    chip_type ENUM('EMV', 'CONTACTLESS', 'MAGSTRIPE') DEFAULT 'EMV', -- NEW: Card technology
    virtual_card_linked BOOLEAN DEFAULT FALSE, -- NEW: Virtual card linkage
    activation_date DATETIME, -- NEW: When card was activated
    otp_enabled BOOLEAN DEFAULT TRUE, -- NEW: OTP for transactions
    FOREIGN KEY (account_id) REFERENCES cbs_accounts(account_number),
    INDEX idx_card_number (card_number),
    INDEX idx_card_status (status),
    INDEX idx_card_account (account_id),
    INDEX idx_card_type_network (card_type, card_network),
    INDEX idx_card_expiry (expiry_date)
) ENGINE=InnoDB;

-- Create transactions table with enhanced tracking
CREATE TABLE cbs_transactions (
    transaction_id VARCHAR(36) PRIMARY KEY,
    card_number VARCHAR(20),
    account_number VARCHAR(20) NOT NULL,
    transaction_type ENUM('WITHDRAWAL', 'DEPOSIT', 'TRANSFER', 'PAYMENT', 'BALANCE_INQUIRY', 'MINI_STATEMENT', 'PIN_CHANGE', 
                         'CHEQUE_DEPOSIT', 'INTEREST_CREDIT', 'FEE_DEBIT', 'REVERSAL', 'REFUND', 'EMI_PAYMENT', 'BILL_PAYMENT',
                         'LOAN_DISBURSEMENT', 'GST_TAX', 'TDS_DEDUCTION', 'DIVIDEND', 'CASHBACK', 'REWARD_REDEMPTION', 
                         'CHARGEBACK', 'EXCHANGE') NOT NULL, -- ENHANCED: more transaction types
    channel ENUM('ATM', 'BRANCH', 'INTERNET', 'MOBILE', 'POS', 'UPI', 'IMPS', 'NEFT', 'RTGS', 'CHEQUE', 'CASH', 
                'STANDING_INSTRUCTION', 'API', 'PHONE_BANKING', 'BILLDESK', 'AUTO_DEBIT', 'POS_INTERNATIONAL', 
                'E_COMMERCE', 'BULK_UPLOAD') NOT NULL, -- ENHANCED: more channels
    amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    currency VARCHAR(3) DEFAULT 'INR', -- NEW: Currency code support
    balance_before DECIMAL(12,2) NOT NULL,
    balance_after DECIMAL(12,2) NOT NULL,
    transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    value_date DATE NOT NULL,
    status ENUM('PENDING', 'SUCCESS', 'FAILED', 'REVERSED', 'DISPUTED', 'UNDER_REVIEW', 'SETTLED', 
               'AUTHORIZED', 'CANCELLED', 'TIMEOUT', 'SCHEDULED') NOT NULL DEFAULT 'PENDING', -- ENHANCED: more statuses
    reference_number VARCHAR(50),
    remarks VARCHAR(255),
    transaction_location VARCHAR(255),
    merchant_category_code VARCHAR(4),
    merchant_name VARCHAR(100),
    sender_details VARCHAR(255),
    receiver_details VARCHAR(255),
    transaction_fee DECIMAL(10,2) DEFAULT 0.00, -- NEW: Transaction fees
    tax_amount DECIMAL(10,2) DEFAULT 0.00, -- NEW: Tax component
    exchange_rate DECIMAL(12,6), -- NEW: For foreign currency transactions
    original_amount DECIMAL(12,2), -- NEW: Original amount in foreign currency
    original_currency VARCHAR(3), -- NEW: Original currency code
    batch_id VARCHAR(50), -- NEW: For batch processing
    response_code VARCHAR(10), -- NEW: Response code from processor
    processing_time INT, -- NEW: Transaction processing time in ms
    device_id VARCHAR(100), -- NEW: Device ID for the transaction
    ip_address VARCHAR(45), -- NEW: IP address (supports IPv6)
    FOREIGN KEY (card_number) REFERENCES cbs_cards(card_number) ON DELETE SET NULL,
    FOREIGN KEY (account_number) REFERENCES cbs_accounts(account_number),
    INDEX idx_transaction_date (transaction_date),
    INDEX idx_transaction_card (card_number),
    INDEX idx_transaction_account (account_number),
    INDEX idx_transaction_type (transaction_type),
    INDEX idx_transaction_channel (channel),
    INDEX idx_transaction_status (status),
    INDEX idx_transaction_reference (reference_number),
    INDEX idx_transaction_batch (batch_id),
    INDEX idx_transaction_device (device_id)
) ENGINE=InnoDB;

-- Additional tables from original schema
-- Include all the tables from the original schema with enhancements
CREATE TABLE cbs_daily_withdrawals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    card_number VARCHAR(20) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    withdrawal_date DATE NOT NULL,
    withdrawal_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atm_id VARCHAR(20),
    location VARCHAR(255),
    status ENUM('COMPLETED', 'FAILED', 'REVERSED', 'SUSPECTED_FRAUD') NOT NULL DEFAULT 'COMPLETED', -- ENHANCED: added fraud flag
    suspicious_flag BOOLEAN DEFAULT FALSE, -- NEW: Flag for suspicious activity
    response_code VARCHAR(10), -- NEW: ATM response code
    balance_after_withdrawal DECIMAL(12,2), -- NEW: Balance after withdrawal
    FOREIGN KEY (card_number) REFERENCES cbs_cards(card_number),
    INDEX idx_withdrawal_card_date (card_number, withdrawal_date),
    INDEX idx_withdrawal_status (status),
    INDEX idx_withdrawal_suspicious (suspicious_flag)
) ENGINE=InnoDB;

-- Create bill payments table with enhanced tracking
CREATE TABLE cbs_bill_payments (
    payment_id VARCHAR(36) PRIMARY KEY,
    transaction_id VARCHAR(36) NOT NULL,
    customer_id VARCHAR(20) NOT NULL,
    biller_id VARCHAR(50) NOT NULL,
    biller_name VARCHAR(100) NOT NULL,
    biller_category ENUM('ELECTRICITY', 'WATER', 'GAS', 'TELEPHONE', 'MOBILE', 'INTERNET', 'INSURANCE', 'TAX', 'EDUCATION', 
                        'CREDIT_CARD', 'LOAN_REPAYMENT', 'DTH', 'SUBSCRIPTION', 'DONATION', 'MUNICIPAL', 'HOSPITAL', 'OTHER') NOT NULL, -- ENHANCED: more categories
    consumer_id VARCHAR(50) NOT NULL,
    bill_amount DECIMAL(12,2) NOT NULL,
    due_date DATE,
    payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    payment_channel ENUM('ATM', 'NET_BANKING', 'MOBILE_APP', 'BRANCH', 'AUTO_DEBIT', 'UPI', 'KIOSK', 'THIRD_PARTY_APP') NOT NULL, -- ENHANCED: more channels
    status ENUM('PENDING', 'SUCCESS', 'FAILED', 'REVERSED', 'SCHEDULED', 'PARTIALLY_PAID') NOT NULL DEFAULT 'PENDING', -- ENHANCED: more statuses
    receipt_number VARCHAR(50),
    convenience_fee DECIMAL(10,2) DEFAULT 0.00, -- NEW: Convenience fee
    bill_period_from DATE, -- NEW: Bill period start
    bill_period_to DATE, -- NEW: Bill period end
    bill_number VARCHAR(50), -- NEW: Bill reference number
    autopay_enabled BOOLEAN DEFAULT FALSE, -- NEW: Autopay status
    autopay_limit DECIMAL(12,2), -- NEW: Maximum autopay amount
    retry_count INT DEFAULT 0, -- NEW: Payment retry count
    next_retry_date DATETIME, -- NEW: Next retry timestamp
    FOREIGN KEY (transaction_id) REFERENCES cbs_transactions(transaction_id),
    FOREIGN KEY (customer_id) REFERENCES cbs_customers(customer_id),
    INDEX idx_payment_biller (biller_id),
    INDEX idx_payment_consumer (consumer_id),
    INDEX idx_payment_date (payment_date),
    INDEX idx_payment_customer (customer_id),
    INDEX idx_payment_autopay (autopay_enabled),
    INDEX idx_payment_status (status)
) ENGINE=InnoDB;

-- Create transfer table for enhanced inter-account transfers
CREATE TABLE cbs_transfers (
    transfer_id VARCHAR(36) PRIMARY KEY,
    transaction_id VARCHAR(36) NOT NULL,
    source_account VARCHAR(20) NOT NULL,
    destination_account VARCHAR(20) NOT NULL,
    beneficiary_name VARCHAR(100),
    beneficiary_bank VARCHAR(100),
    beneficiary_ifsc VARCHAR(20),
    transfer_type ENUM('INTERNAL', 'NEFT', 'RTGS', 'IMPS', 'UPI', 'SWIFT', 'ACH', 'BULK_TRANSFER', 'INWARD_REMITTANCE') NOT NULL, -- ENHANCED: more types
    amount DECIMAL(12,2) NOT NULL,
    transfer_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    processing_date DATETIME,
    status ENUM('INITIATED', 'PROCESSING', 'SUCCESS', 'FAILED', 'REVERSED', 'RETURNED', 'CANCELLED', 'ON_HOLD', 'SCHEDULED') NOT NULL DEFAULT 'INITIATED', -- ENHANCED: more statuses
    reference_number VARCHAR(50),
    purpose_code VARCHAR(4),
    remarks VARCHAR(255),
    charges DECIMAL(10,2) DEFAULT 0.00,
    scheduled_transfer BOOLEAN DEFAULT FALSE,
    recurring_transfer BOOLEAN DEFAULT FALSE,
    frequency ENUM('DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'HALF_YEARLY', 'YEARLY') DEFAULT NULL,
    next_execution_date DATE, -- NEW: Next execution date for recurring
    max_attempts INT DEFAULT 3, -- NEW: Max retry attempts
    current_attempt INT DEFAULT 0, -- NEW: Current attempt count
    remitter_to_beneficiary_info VARCHAR(255), -- NEW: Payment details 
    regulatory_info VARCHAR(255), -- NEW: Regulatory information
    foreign_exchange_rate DECIMAL(12,6), -- NEW: Exchange rate for international
    intermediary_bank VARCHAR(100), -- NEW: Intermediary bank for SWIFT
    correspondence_charges ENUM('OUR', 'BEN', 'SHA') DEFAULT 'SHA', -- NEW: SWIFT charge options
    FOREIGN KEY (transaction_id) REFERENCES cbs_transactions(transaction_id),
    FOREIGN KEY (source_account) REFERENCES cbs_accounts(account_number),
    INDEX idx_transfer_source (source_account),
    INDEX idx_transfer_dest (destination_account),
    INDEX idx_transfer_date (transfer_date),
    INDEX idx_transfer_type (transfer_type),
    INDEX idx_transfer_status (status),
    INDEX idx_transfer_next_exec (next_execution_date)
) ENGINE=InnoDB;

-- =============================================
-- AUDIT AND LOGGING TABLES
-- =============================================

-- Create audit logs table with enhanced compliance features
CREATE TABLE cbs_audit_logs (
    log_id BIGINT NOT NULL AUTO_INCREMENT,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(50),
    action ENUM('LOGIN', 'LOGOUT', 'CREATE', 'UPDATE', 'DELETE', 'VIEW',
                'PIN_CHANGE', 'PASSWORD_CHANGE', 'CARD_BLOCK', 'CARD_UNBLOCK', 'CARD_ISSUE',
                'ACCOUNT_FREEZE', 'ACCOUNT_UNFREEZE', 'LIMIT_CHANGE', 'KYC_UPDATE',
                'BENEFICIARY_ADD', 'BENEFICIARY_DELETE', 'PERMISSION_CHANGE', 'EXPORT_DATA',
                'ADMIN_ACCESS', 'PARAMETER_CHANGE', 'RATE_CHANGE', 'BATCH_PROCESSING', 
                'SCHEDULE_TASK', 'SYSTEM_CONFIGURATION', 'API_ACCESS', 'REPORT_GENERATION') NOT NULL, -- ENHANCED: more actions
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(50) NOT NULL,
    previous_value TEXT,
    new_value TEXT,
    details TEXT,
    ip_address VARCHAR(50),
    user_agent VARCHAR(255),
    channel VARCHAR(50),
    session_id VARCHAR(64),
    status ENUM('SUCCESS', 'FAILURE', 'WARNING', 'BLOCKED', 'PENDING_APPROVAL') NOT NULL DEFAULT 'SUCCESS', -- ENHANCED: more statuses
    approval_status ENUM('NA', 'PENDING', 'APPROVED', 'REJECTED') DEFAULT 'NA', -- NEW: For maker-checker
    approved_by VARCHAR(50), -- NEW: Approver ID
    approval_timestamp DATETIME, -- NEW: Approval time
    request_id VARCHAR(36), -- NEW: Request correlation
    compliance_category ENUM('GENERAL', 'AML', 'KYC', 'REGULATORY', 'SECURITY', 'FINANCIAL', 'OPERATIONAL') DEFAULT 'GENERAL', -- NEW: Compliance categorization
    severity ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') DEFAULT 'MEDIUM', -- NEW: Severity level
    PRIMARY KEY (log_id, timestamp),
    INDEX idx_audit_timestamp (timestamp),
    INDEX idx_audit_user (user_id),
    INDEX idx_audit_action (action),
    INDEX idx_audit_entity (entity_type, entity_id),
    INDEX idx_audit_status (status),
    INDEX idx_audit_compliance (compliance_category),
    INDEX idx_audit_severity (severity),
    INDEX idx_audit_session (session_id),
    INDEX idx_audit_request (request_id)
) ENGINE=InnoDB
-- Using a simpler, fixed-value partitioning scheme
PARTITION BY RANGE (MONTH(timestamp)) (
    PARTITION p_jan VALUES LESS THAN (2),
    PARTITION p_feb VALUES LESS THAN (3),
    PARTITION p_mar VALUES LESS THAN (4),
    PARTITION p_apr VALUES LESS THAN (5),
    PARTITION p_may VALUES LESS THAN (6),
    PARTITION p_jun VALUES LESS THAN (7),
    PARTITION p_jul VALUES LESS THAN (8),
    PARTITION p_aug VALUES LESS THAN (9),
    PARTITION p_sep VALUES LESS THAN (10),
    PARTITION p_oct VALUES LESS THAN (11),
    PARTITION p_nov VALUES LESS THAN (12),
    PARTITION p_dec VALUES LESS THAN (13)
);

-- Create system logs table with enhanced diagnostics
CREATE TABLE cbs_system_logs (
    log_id BIGINT NOT NULL AUTO_INCREMENT,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    log_level ENUM('DEBUG', 'INFO', 'NOTICE', 'WARNING', 'ERROR', 'CRITICAL', 'ALERT', 'EMERGENCY') NOT NULL,
    component VARCHAR(50) NOT NULL,
    module VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    details TEXT,
    stack_trace TEXT,
    request_id VARCHAR(64),
    server_name VARCHAR(100),
    severity INT NOT NULL DEFAULT 1,
    environment ENUM('DEVELOPMENT', 'TESTING', 'STAGING', 'PRODUCTION') NOT NULL DEFAULT 'PRODUCTION', -- NEW: Environment tracker
    correlation_id VARCHAR(64), -- NEW: For tracing related events
    execution_time_ms INT, -- NEW: Performance metric
    memory_usage_mb DECIMAL(10,2), -- NEW: Resource usage
    thread_id VARCHAR(36), -- NEW: Thread identifier
    transaction_id VARCHAR(64), -- NEW: Business transaction ID
    user_id VARCHAR(50), -- NEW: User context
    PRIMARY KEY (log_id, timestamp),
    INDEX idx_log_timestamp (timestamp),
    INDEX idx_log_level (log_level),
    INDEX idx_log_component (component),
    INDEX idx_log_module (module),
    INDEX idx_log_severity (severity),
    INDEX idx_log_correlation (correlation_id),
    INDEX idx_log_transaction (transaction_id),
    INDEX idx_log_request (request_id),
    INDEX idx_log_user (user_id)
) ENGINE=InnoDB 
-- Using fixed date partitioning (not dynamic expressions)
PARTITION BY RANGE (YEAR(timestamp)) (
    PARTITION p_2024 VALUES LESS THAN (2025),
    PARTITION p_2025 VALUES LESS THAN (2026),
    PARTITION p_2026 VALUES LESS THAN (2027),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- =============================================
-- USER AND AUTHENTICATION TABLES
-- =============================================

-- Create enhanced admin users table with advanced security
CREATE TABLE cbs_admin_users (
    admin_id VARCHAR(20) PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(128) NOT NULL,
    salt VARCHAR(64) NOT NULL, -- NEW: Salt for password
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    mobile VARCHAR(20) NOT NULL,
    department VARCHAR(50) NOT NULL,
    branch_code VARCHAR(20) NOT NULL,
    employee_id VARCHAR(20) NOT NULL UNIQUE,
    role ENUM('TELLER', 'CLERK', 'OFFICER', 'MANAGER', 'REGIONAL_MANAGER', 'AUDITOR', 
              'IT_ADMIN', 'SUPER_ADMIN', 'COMPLIANCE_OFFICER', 'RISK_MANAGER', 'SUPPORT', 
              'TREASURY', 'LOAN_OFFICER', 'RELATIONSHIP_MANAGER') NOT NULL, -- ENHANCED: more roles
    status ENUM('ACTIVE', 'INACTIVE', 'SUSPENDED', 'LOCKED', 'TERMINATED', 'PASSWORD_EXPIRED', 
                'PENDING_ACTIVATION', 'FORCE_RESET') NOT NULL DEFAULT 'PENDING_ACTIVATION', -- ENHANCED: more statuses
    password_expiry_date DATE NOT NULL,
    account_locked BOOLEAN DEFAULT FALSE,
    failed_login_attempts INT DEFAULT 0,
    last_login DATETIME,
    last_password_change DATETIME, -- NEW: Track password changes
    access_level INT DEFAULT 1, -- NEW: Numeric access level
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(20),
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    updated_by VARCHAR(20),
    requires_2fa BOOLEAN DEFAULT TRUE,
    two_fa_method ENUM('SMS', 'EMAIL', 'APP', 'HARDWARE_TOKEN') DEFAULT 'SMS', -- NEW: 2FA method
    two_fa_secret VARCHAR(128), -- NEW: 2FA secret key
    direct_reports VARCHAR(255), -- NEW: Staff reporting structure
    permissions TEXT, -- NEW: JSON permissions
    session_timeout_minutes INT DEFAULT 15, -- NEW: Session timeout
    ip_restriction VARCHAR(255), -- NEW: Allowed IP ranges
    allowed_login_times VARCHAR(255), -- NEW: Time restrictions
    last_security_training DATE, -- NEW: Security training date
    security_questions_answered BOOLEAN DEFAULT FALSE, -- NEW: Security questions set
    out_of_office BOOLEAN DEFAULT FALSE, -- NEW: Out of office status
    delegate_to VARCHAR(20), -- NEW: Work delegation
    biometric_registered BOOLEAN DEFAULT FALSE, -- NEW: Biometric auth
    profile_picture VARCHAR(255), -- NEW: Profile picture path
    INDEX idx_admin_username (username),
    INDEX idx_admin_role (role),
    INDEX idx_admin_status (status),
    INDEX idx_admin_branch (branch_code),
    INDEX idx_admin_dept (department),
    INDEX idx_admin_access (access_level),
    INDEX idx_admin_delegate (delegate_to)
) ENGINE=InnoDB;

-- NEW TABLE: Mobile banking users
CREATE TABLE cbs_mobile_users (
    mobile_user_id VARCHAR(36) PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL,
    username VARCHAR(50) UNIQUE,
    password_hash VARCHAR(128) NOT NULL,
    salt VARCHAR(64) NOT NULL,
    device_id VARCHAR(100),
    device_model VARCHAR(100),
    os_type ENUM('ANDROID', 'IOS', 'WINDOWS', 'OTHER') NOT NULL,
    os_version VARCHAR(20),
    app_version VARCHAR(20) NOT NULL,
    fcm_token VARCHAR(255), -- For push notifications
    biometric_enabled BOOLEAN DEFAULT FALSE,
    pin_enabled BOOLEAN DEFAULT FALSE,
    pin_hash VARCHAR(128),
    status ENUM('ACTIVE', 'INACTIVE', 'BLOCKED', 'PENDING_ACTIVATION', 'SUSPENDED') DEFAULT 'PENDING_ACTIVATION',
    failed_login_attempts INT DEFAULT 0,
    last_login DATETIME,
    registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_activity DATETIME,
    preferred_language VARCHAR(10) DEFAULT 'en',
    notification_preferences TEXT, -- Stores notification settings (changed from JSON for compatibility)
    two_fa_enabled BOOLEAN DEFAULT TRUE,
    two_fa_type ENUM('SMS', 'EMAIL', 'APP') DEFAULT 'SMS',
    two_fa_secret VARCHAR(128),
    location_services_enabled BOOLEAN DEFAULT FALSE,
    last_password_change DATETIME,
    activated_at DATETIME,
    activated_by VARCHAR(20),
    account_limit_override TEXT, -- For custom transaction limits (changed from JSON for compatibility)
    FOREIGN KEY (customer_id) REFERENCES cbs_customers(customer_id),
    INDEX idx_mobile_customer (customer_id),
    INDEX idx_mobile_username (username),
    INDEX idx_mobile_status (status),
    INDEX idx_mobile_device (device_id)
) ENGINE=InnoDB;

-- NEW TABLE: API credentials for third-party integration
CREATE TABLE cbs_api_credentials (
    api_key_id VARCHAR(36) PRIMARY KEY,
    api_key VARCHAR(64) NOT NULL UNIQUE,
    api_secret_hash VARCHAR(128) NOT NULL,
    client_id VARCHAR(36) NOT NULL,
    client_name VARCHAR(100) NOT NULL,
    client_type ENUM('FINTECH', 'MERCHANT', 'PARTNER', 'INTERNAL', 'REGULATOR', 'SERVICE_PROVIDER') NOT NULL,
    status ENUM('ACTIVE', 'INACTIVE', 'SUSPENDED', 'EXPIRED') NOT NULL DEFAULT 'ACTIVE',
    ip_whitelist TEXT, -- Comma-separated list of allowed IPs
    rate_limit_per_second INT DEFAULT 10,
    rate_limit_per_day INT DEFAULT 10000,
    access_scope TEXT, -- JSON array of allowed scopes
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    last_used DATETIME,
    created_by VARCHAR(20) NOT NULL,
    approval_status ENUM('PENDING', 'APPROVED', 'REJECTED') DEFAULT 'PENDING',
    approved_by VARCHAR(20),
    approval_date DATETIME,
    callback_url VARCHAR(255),
    webhook_url VARCHAR(255),
    webhook_secret VARCHAR(64),
    INDEX idx_api_client (client_id),
    INDEX idx_api_status (status),
    INDEX idx_api_expiry (expires_at)
) ENGINE=InnoDB;

-- =============================================
-- INFRASTRUCTURE TABLES
-- =============================================

-- Enhanced ATM machines table
CREATE TABLE cbs_atm_machines (
    atm_id VARCHAR(20) PRIMARY KEY,
    atm_type ENUM('ONSITE', 'OFFSITE', 'DRIVE_THROUGH', 'MOBILE', 'KIOSK', 'RECYCLER', 
                  'CASH_DEPOSIT', 'MULTI_FUNCTION', 'PASSBOOK', 'COIN_DISPENSER') NOT NULL DEFAULT 'ONSITE', -- ENHANCED: more types
    location VARCHAR(255) NOT NULL,
    address VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    pin_code VARCHAR(10) NOT NULL,
    geo_coordinates VARCHAR(50),
    branch_code VARCHAR(20) NOT NULL,
    manufacturer VARCHAR(100),
    model VARCHAR(100),
    serial_number VARCHAR(100) NOT NULL UNIQUE,
    ip_address VARCHAR(15),
    status ENUM('ONLINE', 'OFFLINE', 'MAINTENANCE', 'OUT_OF_CASH', 'PARTIAL_SERVICE', 
               'VANDALIZED', 'PLANNED_DOWNTIME', 'SECURITY_ISSUE', 'SOFTWARE_UPDATE') NOT NULL DEFAULT 'ONLINE', -- ENHANCED: more statuses
    cash_balance DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    cash_limit DECIMAL(12,2) NOT NULL DEFAULT 1000000.00,
    last_maintenance DATETIME,
    next_maintenance_due DATETIME,
    last_cash_refill DATETIME,
    installation_date DATE NOT NULL,
    is_accessible BOOLEAN DEFAULT TRUE,
    supports_deposit BOOLEAN DEFAULT FALSE,
    supports_cardless BOOLEAN DEFAULT FALSE,
    supports_cheque_deposit BOOLEAN DEFAULT FALSE, -- NEW: Cheque deposit
    supports_cash_recycling BOOLEAN DEFAULT FALSE, -- NEW: Cash recycling
    supports_bill_payment BOOLEAN DEFAULT FALSE, -- NEW: Bill payments
    supports_passbook_update BOOLEAN DEFAULT FALSE, -- NEW: Passbook update
    network_bandwidth VARCHAR(20), -- NEW: Network information
    os_version VARCHAR(50), -- NEW: OS information
    app_version VARCHAR(50), -- NEW: ATM software version
    last_reboot DATETIME, -- NEW: Last reboot time
    camera_enabled BOOLEAN DEFAULT TRUE, -- NEW: Security camera
    alarm_system_status ENUM('ACTIVE', 'INACTIVE', 'FAULT') DEFAULT 'ACTIVE', -- NEW: Alarm system
    ups_battery_status VARCHAR(20), -- NEW: UPS status
    temperature VARCHAR(10), -- NEW: Environmental monitoring
    hardware_hash VARCHAR(64), -- NEW: Hardware signature for security
    service_contract VARCHAR(50), -- NEW: Service contract reference
    service_provider VARCHAR(100), -- NEW: Service company
    customer_feedback_rating DECIMAL(3,1), -- NEW: Customer satisfaction metric
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_atm_status (status),
    INDEX idx_atm_location (location),
    INDEX idx_atm_branch (branch_code),
    INDEX idx_atm_city (city),
    INDEX idx_atm_state (state),
    INDEX idx_atm_pincode (pin_code),
    INDEX idx_atm_model (model, manufacturer)
) ENGINE=InnoDB;

-- Enhanced cash operations for ATM loading/unloading
CREATE TABLE cbs_atm_cash_operations (
    operation_id VARCHAR(36) PRIMARY KEY,
    atm_id VARCHAR(20) NOT NULL,
    operation_type ENUM('LOAD', 'UNLOAD', 'AUDIT', 'MAINTENANCE', 'RECYCLER_ADJUSTMENT', 
                       'EMERGENCY_REPLENISHMENT', 'RECONCILIATION', 'CALIBRATION') NOT NULL, -- ENHANCED: more operation types
    denomination_2000 INT DEFAULT 0,
    denomination_500 INT DEFAULT 0,
    denomination_200 INT DEFAULT 0,
    denomination_100 INT DEFAULT 0,
    denomination_50 INT DEFAULT 0, -- NEW: Additional denomination
    denomination_20 INT DEFAULT 0, -- NEW: Additional denomination
    denomination_10 INT DEFAULT 0, -- NEW: Additional denomination
    denomination_5 INT DEFAULT 0, -- NEW: Additional denomination
    denomination_2 INT DEFAULT 0, -- NEW: Additional denomination
    denomination_1 INT DEFAULT 0, -- NEW: Additional denomination
    coin_replenishment BOOLEAN DEFAULT FALSE, -- NEW: Coin handling
    amount DECIMAL(12,2) NOT NULL,
    performed_by VARCHAR(20) NOT NULL,
    verified_by VARCHAR(20),
    custodian VARCHAR(100),
    balance_before DECIMAL(12,2) NOT NULL,
    balance_after DECIMAL(12,2) NOT NULL,
    operation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    completion_date DATETIME,
    discrepancy_amount DECIMAL(10,2) DEFAULT 0.00,
    status ENUM('INITIATED', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'CANCELLED', 
               'PENDING_VERIFICATION', 'RECONCILED', 'DISPUTED') NOT NULL DEFAULT 'INITIATED', -- ENHANCED: more statuses
    notes TEXT,
    sealed_bag_numbers TEXT, -- NEW: Security seal tracking
    vehicle_number VARCHAR(20), -- NEW: CIT van details
    route_code VARCHAR(20), -- NEW: Cash management route
    otp_verification VARCHAR(10), -- NEW: OTP for operation
    video_recording_id VARCHAR(36), -- NEW: CCTV recording reference
    cash_management_company VARCHAR(100), -- NEW: Outsourced company
    recycled_cash_amount DECIMAL(12,2) DEFAULT 0.00, -- NEW: For cash recyclers
    rejected_notes INT DEFAULT 0, -- NEW: Damaged note count
    damaged_notes_value DECIMAL(10,2) DEFAULT 0.00, -- NEW: Damaged note value
    start_time DATETIME, -- NEW: Operation start time
    end_time DATETIME, -- NEW: Operation end time
    transaction_log_verified BOOLEAN DEFAULT FALSE, -- NEW: Log verification
    FOREIGN KEY (atm_id) REFERENCES cbs_atm_machines(atm_id),
    FOREIGN KEY (performed_by) REFERENCES cbs_admin_users(admin_id),
    FOREIGN KEY (verified_by) REFERENCES cbs_admin_users(admin_id),
    INDEX idx_operation_atm (atm_id),
    INDEX idx_operation_date (operation_date),
    INDEX idx_operation_status (status),
    INDEX idx_operation_performer (performed_by),
    INDEX idx_operation_type (operation_type)
) ENGINE=InnoDB;

-- Enhanced app sessions table with security features
CREATE TABLE cbs_sessions (
    session_id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    user_type ENUM('CUSTOMER', 'ADMIN', 'API', 'MOBILE', 'CORPORATE', 'PARTNER') NOT NULL, -- ENHANCED: more user types
    login_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    expiry_time DATETIME NOT NULL,
    last_activity_time DATETIME NOT NULL,
    ip_address VARCHAR(50),
    device_info VARCHAR(255),
    browser VARCHAR(100),
    operating_system VARCHAR(100),
    location VARCHAR(255),
    geo_coordinates VARCHAR(50), -- NEW: Precise location
    user_agent VARCHAR(512),
    auth_method ENUM('PASSWORD', 'OTP', 'BIOMETRIC', '2FA', 'SSO', 'TOKEN', 'CERTIFICATE', 'SOCIAL') NOT NULL,
    mfa_verified BOOLEAN DEFAULT FALSE,
    status ENUM('ACTIVE', 'EXPIRED', 'TERMINATED', 'SUSPICIOUS', 'CONCURRENT_LOGIN', 'IDLE', 'LOCKED') NOT NULL DEFAULT 'ACTIVE', -- ENHANCED: more statuses
    reason_for_termination VARCHAR(255),
    jwt_token_id VARCHAR(255), -- NEW: JWT reference
    refresh_token_id VARCHAR(255), -- NEW: Refresh token reference
    session_data TEXT, -- NEW: Session data (changed from JSON for compatibility)
    risk_score INT DEFAULT 50, -- NEW: Session risk scoring (0-100)
    channel ENUM('WEB', 'MOBILE', 'API', 'ATM', 'BRANCH', 'PARTNER', 'KIOSK') NOT NULL DEFAULT 'WEB', -- NEW: Access channel
    permissions_hash VARCHAR(64), -- NEW: Permission verification
    feature_access TEXT, -- NEW: Available features for session (changed from JSON for compatibility)
    parent_session_id VARCHAR(64), -- NEW: For linked sessions
    impersonated_by VARCHAR(50), -- NEW: For admin impersonation
    session_tags VARCHAR(255), -- NEW: For session categorization
    INDEX idx_session_user (user_id, user_type),
    INDEX idx_session_status (status),
    INDEX idx_session_expiry (expiry_time),
    INDEX idx_session_last_activity (last_activity_time),
    INDEX idx_session_ip (ip_address),
    INDEX idx_session_risk (risk_score),
    INDEX idx_session_channel (channel),
    INDEX idx_session_parent (parent_session_id)
) ENGINE=InnoDB;

-- =============================================
-- NEW FEATURE: SECURITY AND COMPLIANCE
-- =============================================

-- NEW TABLE: Security Incidents
CREATE TABLE cbs_security_incidents (
    incident_id VARCHAR(36) PRIMARY KEY,
    incident_type ENUM('UNAUTHORIZED_ACCESS', 'DATA_BREACH', 'SUSPICIOUS_TRANSACTION', 'DDoS', 
                       'MALWARE', 'PHISHING', 'INSIDER_THREAT', 'PHYSICAL_SECURITY', 'CARD_SKIMMING',
                       'SOCIAL_ENGINEERING', 'ACCOUNT_TAKEOVER', 'API_ABUSE', 'SESSION_HIJACKING', 'OTHER') NOT NULL,
    severity ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL,
    status ENUM('DETECTED', 'INVESTIGATING', 'CONTAINED', 'RESOLVED', 'FALSE_POSITIVE', 'CLOSED', 'ESCALATED') NOT NULL DEFAULT 'DETECTED',
    detection_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolution_time DATETIME,
    affected_systems VARCHAR(255),
    affected_customers INT DEFAULT 0,
    affected_accounts TEXT,
    incident_description TEXT NOT NULL,
    detection_method VARCHAR(100) NOT NULL,
    reported_by VARCHAR(50),
    assigned_to VARCHAR(50),
    containment_actions TEXT,
    resolution_actions TEXT,
    lessons_learned TEXT,
    preventive_measures TEXT,
    reported_to_regulator BOOLEAN DEFAULT FALSE,
    regulatory_report_date DATETIME,
    regulatory_reference VARCHAR(50),
    financial_impact DECIMAL(14,2) DEFAULT 0.00,
    related_incident_id VARCHAR(36),
    evidence_links TEXT,
    INDEX idx_incident_type (incident_type),
    INDEX idx_incident_status (status),
    INDEX idx_incident_severity (severity),
    INDEX idx_incident_detection (detection_time),
    INDEX idx_incident_assigned (assigned_to)
) ENGINE=InnoDB;

-- NEW TABLE: Fraud Detection Rules
CREATE TABLE cbs_fraud_rules (
    rule_id VARCHAR(36) PRIMARY KEY,
    rule_name VARCHAR(100) NOT NULL,
    rule_description TEXT NOT NULL,
    rule_type ENUM('TRANSACTION', 'LOGIN', 'ACCOUNT', 'CUSTOMER', 'CARD', 'DEVICE', 'PATTERN', 'BEHAVIORAL') NOT NULL,
    rule_condition TEXT NOT NULL, -- JSON or SQL condition
    risk_score INT NOT NULL DEFAULT 50, -- 0-100
    action ENUM('MONITOR', 'FLAG', 'ALERT', 'BLOCK', 'VERIFY', 'ESCALATE', 'OTP', 'STEP_UP') NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(20) NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    updated_by VARCHAR(20),
    version INT DEFAULT 1,
    priority INT DEFAULT 5, -- 1-10, higher is more important
    execution_order INT, -- Rule processing sequence
    cooldown_minutes INT DEFAULT 0, -- Time between repeated triggers
    false_positive_rate DECIMAL(5,2) DEFAULT 0.00, -- Tracked false positive rate
    success_rate DECIMAL(5,2) DEFAULT 0.00, -- Historical success rate
    applicable_channels VARCHAR(255), -- Which channels this applies to
    INDEX idx_rule_type (rule_type),
    INDEX idx_rule_enabled (enabled),
    INDEX idx_rule_priority (priority)
) ENGINE=InnoDB;

-- NEW TABLE: Fraud Cases
CREATE TABLE cbs_fraud_cases (
    case_id VARCHAR(36) PRIMARY KEY,
    customer_id VARCHAR(20),
    account_number VARCHAR(20),
    card_number VARCHAR(20),
    transaction_id VARCHAR(36),
    detection_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    fraud_type ENUM('UNAUTHORIZED_TRANSACTION', 'ACCOUNT_TAKEOVER', 'IDENTITY_THEFT', 
                  'COUNTERFEIT_CARD', 'CARD_NOT_PRESENT', 'APPLICATION_FRAUD',
                  'SOCIAL_ENGINEERING', 'INTERNAL_FRAUD', 'FIRST_PARTY', 'SYNTHETIC_IDENTITY', 'MERCHANT', 'OTHER') NOT NULL,
    fraud_channel ENUM('ATM', 'POS', 'ONLINE', 'MOBILE', 'BRANCH', 'PHONE', 'MAIL', 'SOCIAL_MEDIA', 'EMAIL', 'OTHER') NOT NULL,
    fraud_amount DECIMAL(12,2),
    detected_by ENUM('SYSTEM', 'CUSTOMER', 'STAFF', 'THIRD_PARTY', 'LAW_ENFORCEMENT') NOT NULL,
    status ENUM('NEW', 'INVESTIGATING', 'CONFIRMED', 'DISPUTED', 'RESOLVED', 'FALSE_POSITIVE', 'RECOVERED', 'CLOSED', 'LEGAL_ACTION') NOT NULL DEFAULT 'NEW',
    description TEXT,
    evidence TEXT,
    action_taken TEXT,
    recovery_amount DECIMAL(12,2) DEFAULT 0.00,
    assigned_to VARCHAR(20),
    reported_date DATETIME,
    resolution_date DATETIME,
    customer_notified BOOLEAN DEFAULT FALSE,
    regulatory_reported BOOLEAN DEFAULT FALSE,
    modus_operandi VARCHAR(255),
    related_cases VARCHAR(255), -- Comma-separated list of related cases
    case_notes TEXT,
    police_report_number VARCHAR(50),
    suspicious_ip VARCHAR(50),
    suspicious_device VARCHAR(100),
    location_of_fraud VARCHAR(255),
    FOREIGN KEY (customer_id) REFERENCES cbs_customers(customer_id) ON DELETE SET NULL,
    FOREIGN KEY (account_number) REFERENCES cbs_accounts(account_number) ON DELETE SET NULL,
    FOREIGN KEY (card_number) REFERENCES cbs_cards(card_number) ON DELETE SET NULL,
    FOREIGN KEY (transaction_id) REFERENCES cbs_transactions(transaction_id) ON DELETE SET NULL,
    INDEX idx_fraud_customer (customer_id),
    INDEX idx_fraud_account (account_number),
    INDEX idx_fraud_card (card_number),
    INDEX idx_fraud_transaction (transaction_id),
    INDEX idx_fraud_status (status),
    INDEX idx_fraud_type (fraud_type),
    INDEX idx_fraud_channel (fraud_channel),
    INDEX idx_fraud_detection_time (detection_time),
    INDEX idx_fraud_assigned (assigned_to)
) ENGINE=InnoDB;

-- =============================================
-- NEW FEATURE: REPORTING AND ANALYTICS
-- =============================================

-- NEW TABLE: Reports Configuration
CREATE TABLE cbs_report_definitions (
    report_id VARCHAR(36) PRIMARY KEY,
    report_name VARCHAR(100) NOT NULL,
    report_description TEXT,
    report_category ENUM('FINANCIAL', 'OPERATIONAL', 'REGULATORY', 'CUSTOMER', 'AUDIT', 'SECURITY', 
                         'PERFORMANCE', 'RISK', 'EXECUTIVE', 'MARKETING', 'COMPLIANCE', 'TREND_ANALYSIS') NOT NULL,
    report_query TEXT NOT NULL,
    parameters TEXT, -- Required parameters (changed from JSON for compatibility)
    output_format ENUM('PDF', 'CSV', 'EXCEL', 'HTML', 'JSON', 'XML') NOT NULL DEFAULT 'PDF',
    created_by VARCHAR(20) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(20),
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    access_level INT DEFAULT 1, -- Who can run this report
    schedule ENUM('ON_DEMAND', 'DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'YEARLY') DEFAULT 'ON_DEMAND',
    schedule_details VARCHAR(255), -- Cron expression or specific times
    last_run_time DATETIME,
    last_run_status ENUM('SUCCESS', 'FAILED', 'PARTIAL') DEFAULT NULL,
    average_execution_time INT, -- In seconds
    version INT DEFAULT 1,
    regulatory_requirement VARCHAR(255), -- Compliance requirement this fulfills
    INDEX idx_report_category (report_category),
    INDEX idx_report_active (is_active),
    INDEX idx_report_schedule (schedule),
    INDEX idx_report_access (access_level)
) ENGINE=InnoDB;

-- NEW TABLE: Report Execution History
CREATE TABLE cbs_report_executions (
    execution_id VARCHAR(36) PRIMARY KEY,
    report_id VARCHAR(36) NOT NULL,
    executed_by VARCHAR(20) NOT NULL,
    execution_start DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    execution_end DATETIME,
    status ENUM('RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', 'TIMEOUT') NOT NULL DEFAULT 'RUNNING',
    parameters TEXT, -- Parameters used in this execution (changed from JSON for compatibility)
    row_count INT, -- Number of records returned
    file_size INT, -- Size of output in KB
    output_format ENUM('PDF', 'CSV', 'EXCEL', 'HTML', 'JSON', 'XML') NOT NULL,
    output_location VARCHAR(255), -- File path or URL where report is stored
    execution_notes TEXT,
    error_message TEXT,
    execution_time INT, -- Seconds taken
    scheduled_execution BOOLEAN DEFAULT FALSE, -- Was this scheduled or manual
    sent_to VARCHAR(255), -- Email or other distribution
    ip_address VARCHAR(50),
    FOREIGN KEY (report_id) REFERENCES cbs_report_definitions(report_id),
    INDEX idx_execution_report (report_id),
    INDEX idx_execution_status (status),
    INDEX idx_execution_start (execution_start),
    INDEX idx_execution_by (executed_by)
) ENGINE=InnoDB;

-- =============================================
-- STORED PROCEDURES, FUNCTIONS AND TRIGGERS
-- =============================================

-- All procedures, triggers, and functions have been moved to procedures.sql for MariaDB compatibility.
-- To load them, run the following after all tables and data are created:
SOURCE procedures.sql;

-- Insert default admin user with strong password hash
INSERT INTO cbs_admin_users (
    admin_id, 
    username, 
    password_hash, 
    salt,
    full_name, 
    email, 
    mobile, 
    department, 
    branch_code, 
    employee_id,
    role,
    status, 
    password_expiry_date,
    created_at,
    requires_2fa
)
VALUES (
    'ADM00001', 
    'admin',
    '$2b$12$tJLKV8QFH2W2XCsl3XKR3OXV5XM.EqWei2h63MrjcSXHIkZxGkkH.', -- hash for 'admin123'
    'f85e617698a2948d4fcc065dd55419b5',
    'System Administrator',
    'admin@corebanking.local',
    '9876543210',
    'IT',
    'HO001',
    'EMP00001',
    'SUPER_ADMIN',
    'ACTIVE',
    DATE_ADD(CURDATE(), INTERVAL 90 DAY),
    NOW(),
    TRUE
) ON DUPLICATE KEY UPDATE username=username;

-- Insert sample customer data
INSERT INTO cbs_customers (
    customer_id,
    name,
    dob,
    address,
    email,
    phone,
    gender,
    occupation,
    annual_income,
    kyc_status,
    customer_segment
) VALUES
    ('CUS10001', 'John Doe', '1985-05-15', '123 Main Street, Mumbai', 'john.doe@example.com', '9876543210', 'MALE', 'Software Engineer', 1200000.00, 'COMPLETED', 'RETAIL'),
    ('CUS10002', 'Jane Smith', '1990-08-22', '456 Park Avenue, Delhi', 'jane.smith@example.com', '8765432109', 'FEMALE', 'Doctor', 2500000.00, 'COMPLETED', 'PRIORITY')
ON DUPLICATE KEY UPDATE email=email;

-- Insert sample account data
INSERT INTO cbs_accounts (
    account_number,
    customer_id,
    account_type,
    branch_code,
    ifsc_code,
    balance,
    interest_rate,
    status,
    minimum_balance,
    account_category
) VALUES
    ('ACC100000001', 'CUS10001', 'SAVINGS', 'BR001', 'CBSN0000001', 10000.00, 3.50, 'ACTIVE', 1000.00, 'REGULAR'),
    ('ACC100000002', 'CUS10002', 'CURRENT', 'BR001', 'CBSN0000001', 25000.00, 0.00, 'ACTIVE', 5000.00, 'PREMIUM')
ON DUPLICATE KEY UPDATE account_number=account_number;

-- Commit transaction
COMMIT;
