-- UPI Module Schema

-- UPI Accounts
CREATE TABLE IF NOT EXISTS upi_accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    account_id INT NOT NULL,
    upi_id VARCHAR(100) NOT NULL UNIQUE,
    pin_hash VARCHAR(255) NOT NULL,
    pin_salt VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (account_id) REFERENCES accounts(id)
);

-- UPI Transactions
CREATE TABLE IF NOT EXISTS upi_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id VARCHAR(100) NOT NULL UNIQUE,
    upi_transaction_id VARCHAR(100) NOT NULL UNIQUE,
    sender_upi_id VARCHAR(100) NOT NULL,
    receiver_upi_id VARCHAR(100) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    purpose VARCHAR(255),
    reference_number VARCHAR(100) NOT NULL,
    status ENUM('PENDING', 'SUCCESS', 'FAILED', 'REVERSED') DEFAULT 'PENDING',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (sender_upi_id) REFERENCES upi_accounts(upi_id),
    INDEX (sender_upi_id),
    INDEX (receiver_upi_id),
    INDEX (reference_number)
);

-- UPI Device Information
CREATE TABLE IF NOT EXISTS upi_devices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    upi_account_id INT NOT NULL,
    device_id VARCHAR(255) NOT NULL,
    device_model VARCHAR(255),
    os_version VARCHAR(100),
    app_version VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    last_login_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (upi_account_id) REFERENCES upi_accounts(id),
    UNIQUE KEY (upi_account_id, device_id)
);

-- UPI QR Codes
CREATE TABLE IF NOT EXISTS upi_qr_codes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    upi_account_id INT NOT NULL,
    reference_id VARCHAR(100) NOT NULL UNIQUE,
    qr_payload TEXT NOT NULL,
    amount DECIMAL(15, 2) DEFAULT 0,
    purpose VARCHAR(255),
    expiry DATETIME,
    is_used BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (upi_account_id) REFERENCES upi_accounts(id)
);

-- Security Events Table
CREATE TABLE IF NOT EXISTS security_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    event_type ENUM(
        'LOGIN_SUCCESS', 
        'LOGIN_FAILURE', 
        'LOGOUT', 
        'PASSWORD_CHANGE', 
        'UPI_PIN_CHANGE', 
        'UPI_REGISTRATION',
        'SUSPICIOUS_ACTIVITY'
    ) NOT NULL,
    event_description TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- Notifications Table
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    channel VARCHAR(20) NOT NULL,
    data JSON,
    status ENUM('PENDING', 'SENT', 'FAILED', 'READ') DEFAULT 'PENDING',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    sent_at DATETIME,
    read_at DATETIME,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- UPI Collect Requests Table
CREATE TABLE IF NOT EXISTS upi_collect_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    collect_id VARCHAR(100) NOT NULL UNIQUE,
    requester_upi_id VARCHAR(100) NOT NULL,
    payer_upi_id VARCHAR(100) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    purpose VARCHAR(255),
    reference_number VARCHAR(100) NOT NULL,
    transaction_id VARCHAR(100),
    status ENUM('PENDING', 'ACCEPTED', 'REJECTED', 'FAILED', 'EXPIRED') DEFAULT 'PENDING',
    failure_reason VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    expire_at DATETIME DEFAULT (NOW() + INTERVAL 24 HOUR),
    FOREIGN KEY (requester_upi_id) REFERENCES upi_accounts(upi_id),
    FOREIGN KEY (payer_upi_id) REFERENCES upi_accounts(upi_id),
    INDEX (requester_upi_id),
    INDEX (payer_upi_id),
    INDEX (status)
);
