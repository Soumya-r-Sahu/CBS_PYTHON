-- Core Banking System Database Setup Script
-- This script creates the database and imports all components
-- Created: May 21, 2025

-- Create database
CREATE DATABASE IF NOT EXISTS cbs_python CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE cbs_python;

-- Import schema
SOURCE schema/main_schema.sql;

-- Import stored procedures
SOURCE procedures/withdrawal_procedures.sql;
SOURCE procedures/transfer_procedures.sql;
SOURCE procedures/bill_payment_procedures.sql;
SOURCE procedures/mobile_banking_procedures.sql;
SOURCE procedures/notification_procedures.sql;
SOURCE procedures/triggers.sql;

-- Import ID standards
SOURCE id_standards/banking_id_validation.sql;
SOURCE id_standards/banking_id_generation.sql;
SOURCE id_standards/international_id_standards.sql;

-- Create an admin user with default credentials (for initial setup only)
-- Note: This should be changed immediately after first login
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
    password_expiry_date
)
SELECT 
    'ADMIN001', 
    'admin', 
    '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', -- SHA256 hash of 'admin'
    'cbs_initial_salt', 
    'System Administrator', 
    'admin@cbspython.local', 
    '9999999999', 
    'IT', 
    'BR0001', 
    'EMP0001', 
    'ADMIN', 
    'ACTIVE', 
    DATE_ADD(CURRENT_DATE, INTERVAL 30 DAY)
WHERE NOT EXISTS (
    SELECT 1 FROM cbs_admin_users WHERE admin_id = 'ADMIN001'
);

PRINT 'Database setup completed successfully.';
PRINT 'WARNING: Please change the default admin password immediately after first login.';
