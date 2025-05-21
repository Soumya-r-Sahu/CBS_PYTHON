-- Triggers for Core Banking System
-- Contains all database triggers for various tables
-- Created: May 19, 2025

DELIMITER $$

-- Trigger: After update on accounts
DROP TRIGGER IF EXISTS cbs_accounts_after_update$$
CREATE TRIGGER cbs_accounts_after_update
AFTER UPDATE ON cbs_accounts
FOR EACH ROW
BEGIN
    -- Log account balance changes
    IF OLD.balance != NEW.balance THEN
        INSERT INTO cbs_audit_logs (
            log_id,
            action,
            entity_type,
            entity_id,
            user_id,
            action_timestamp,
            old_value,
            new_value,
            status,
            module,
            criticality
        ) VALUES (
            UUID(),
            'UPDATE',
            'ACCOUNT',
            NEW.account_number,
            COALESCE(@current_user_id, 'SYSTEM'),
            NOW(),
            CONCAT('{"balance": ', OLD.balance, '}'),
            CONCAT('{"balance": ', NEW.balance, '}'),
            'SUCCESS',
            'CORE_BANKING',
            CASE 
                WHEN ABS(NEW.balance - OLD.balance) > 100000 THEN 'HIGH'
                WHEN ABS(NEW.balance - OLD.balance) > 10000 THEN 'MEDIUM'
                ELSE 'LOW'
            END
        );
    END IF;
      -- Log status changes
    IF OLD.status != NEW.status THEN
        INSERT INTO cbs_audit_logs (
            log_id,
            action,
            entity_type,
            entity_id,
            user_id,
            action_timestamp,
            old_value,
            new_value,
            status,
            module,
            criticality
        ) VALUES (
            UUID(),
            'UPDATE',
            'ACCOUNT',
            NEW.account_number,
            COALESCE(@current_user_id, 'SYSTEM'),
            NOW(),
            CONCAT('{"status": "', OLD.status, '"}'),
            CONCAT('{"status": "', NEW.status, '"}'),
            'SUCCESS',
            'CORE_BANKING',
            'MEDIUM'
        );
    END IF;
END$$

-- Trigger: After insert on customers
DROP TRIGGER IF EXISTS cbs_customers_after_insert$$
CREATE TRIGGER cbs_customers_after_insert
AFTER INSERT ON cbs_customers
FOR EACH ROW
BEGIN
    -- Log new customer creation
    INSERT INTO cbs_audit_logs (
        log_id,
        action,
        entity_type,
        entity_id,
        user_id,
        action_timestamp,
        new_value,
        status,
        module,
        sub_module,
        criticality
    ) VALUES (
        UUID(),
        'CREATE',
        'CUSTOMER',
        NEW.customer_id,
        COALESCE(@current_user_id, 'SYSTEM'),
        NOW(),
        JSON_OBJECT(
            'first_name', NEW.first_name,
            'last_name', NEW.last_name,
            'email', NEW.email,
            'mobile', NEW.mobile,
            'status', NEW.status
        ),
        'SUCCESS',
        'CRM',
        'CUSTOMER_ONBOARDING',
        'MEDIUM'
    );
      -- Send welcome notification
    INSERT INTO cbs_notifications (
        notification_id,
        user_id,
        user_type,
        title,
        message,
        notification_type,
        status,
        created_at
    ) VALUES (
        UUID(),
        NEW.customer_id,
        'CUSTOMER',
        'Welcome to Core Banking System',
        CONCAT('Dear ', COALESCE(NEW.first_name, ''), ' ', COALESCE(NEW.last_name, ''), ', welcome to our banking services. Your customer ID is ', NEW.customer_id, '.'),
        'INFO',
        'UNREAD',
        NOW()
    );
END$$

-- Trigger: After insert on bill payments
DROP TRIGGER IF EXISTS cbs_bill_payments_after_insert$$
CREATE TRIGGER cbs_bill_payments_after_insert
AFTER INSERT ON cbs_bill_payments
FOR EACH ROW
BEGIN
    -- Create notification for bill payment
    INSERT INTO cbs_notifications (
        notification_id,
        user_id,
        user_type,
        title,
        message,
        notification_type,
        status,
        created_at
    ) VALUES (
        UUID(),
        NEW.customer_id,
        'CUSTOMER',
        CONCAT('Bill payment of ₹', FORMAT(NEW.amount, 2)),
        CONCAT('Your bill payment of ₹', FORMAT(NEW.amount, 2), ' to ', NEW.biller_name, ' was successful.'),
        'INFO',
        'UNREAD',
        NOW()
    );
END$$

-- Trigger: After update on kyc_documents
DROP TRIGGER IF EXISTS cbs_kyc_documents_after_update$$
CREATE TRIGGER cbs_kyc_documents_after_update
AFTER UPDATE ON cbs_kyc_documents
FOR EACH ROW
BEGIN
    -- If verification status changed, create notification
    IF NEW.verification_status != OLD.verification_status THEN
        INSERT INTO cbs_notifications (
            notification_id,
            user_id,
            user_type,
            title,
            message,
            notification_type,
            status,
            created_at
        ) VALUES (
            UUID(),
            NEW.customer_id,
            'CUSTOMER',
            CONCAT('KYC Document ', NEW.verification_status),
            CASE 
                WHEN NEW.verification_status = 'VERIFIED' THEN 
                    CONCAT('Your ', NEW.document_type, ' document has been verified.')
                WHEN NEW.verification_status = 'REJECTED' THEN
                    CONCAT('Your ', NEW.document_type, ' document was rejected. Reason: ', IFNULL(NEW.verification_remarks, 'Please contact the branch.'))
                ELSE
                    CONCAT('Your ', NEW.document_type, ' document status is now ', NEW.verification_status)
            END,
            CASE 
                WHEN NEW.verification_status = 'VERIFIED' THEN 'INFO'
                WHEN NEW.verification_status = 'REJECTED' THEN 'ALERT'
                ELSE 'INFO'
            END,
            'UNREAD',
            NOW()
        );
    END IF;
END$$

-- Trigger: After insert on atm_transactions
DROP TRIGGER IF EXISTS cbs_atm_transactions_after_insert$$
CREATE TRIGGER cbs_atm_transactions_after_insert
AFTER INSERT ON cbs_atm_transactions
FOR EACH ROW
BEGIN
    -- Create security notification for ATM transactions
    IF NEW.transaction_type = 'WITHDRAWAL' AND NEW.amount > 10000 THEN
        INSERT INTO cbs_notifications (
            notification_id,
            user_id,
            user_type,
            title,
            message,
            notification_type,
            status,
            created_at
        ) VALUES (
            UUID(),
            (SELECT customer_id FROM cbs_accounts WHERE account_number = NEW.account_number),
            'CUSTOMER',
            'High-value ATM Transaction',
            CONCAT('A high-value ATM withdrawal of ₹', FORMAT(NEW.amount, 2), ' was made from your account at ', DATE_FORMAT(NEW.transaction_date, '%h:%i %p'), ' on ', DATE_FORMAT(NEW.transaction_date, '%d-%b-%Y'), '. If this was not you, please contact us immediately.'),
            'SECURITY',
            'UNREAD',
            NOW()
        );
    END IF;
END$$

-- Trigger: After insert on mobile_banking_users
DROP TRIGGER IF EXISTS cbs_mobile_banking_users_after_insert$$
CREATE TRIGGER cbs_mobile_banking_users_after_insert
AFTER INSERT ON cbs_mobile_banking_users
FOR EACH ROW
BEGIN
    -- Log audit entry for new mobile banking device registration
    INSERT INTO cbs_audit_trail (
        audit_id,
        entity,
        entity_id,
        action,
        performed_by,
        performed_at,
        old_value,
        new_value,
        ip_address
    ) VALUES (
        UUID(),
        'MOBILE_BANKING',
        NEW.mb_user_id,
        'REGISTER',
        NEW.customer_id,
        NOW(),
        NULL,
        CONCAT('{"device_id":"', NEW.device_id, '","device_model":"', NEW.device_model, '","device_os":"', NEW.device_os, '"}'),
        NULL
    );
END$$

-- Trigger: After insert on transactions for high value amounts
DROP TRIGGER IF EXISTS cbs_transactions_high_value_insert$$
CREATE TRIGGER cbs_transactions_high_value_insert
AFTER INSERT ON cbs_transactions
FOR EACH ROW
BEGIN
    -- Create security notification for high-value transactions
    IF NEW.amount > 50000 AND NEW.transaction_type IN ('TRANSFER', 'WITHDRAWAL') THEN
        -- Security notification for customer
        INSERT INTO cbs_notifications (
            notification_id,
            user_id,
            user_type,
            title,
            message,
            notification_type,
            status,
            created_at
        ) VALUES (
            UUID(),
            (SELECT customer_id FROM cbs_accounts WHERE account_number = NEW.account_number),
            'CUSTOMER',
            'High-value Transaction Alert',
            CONCAT('A high-value transaction of ₹', FORMAT(NEW.amount, 2), ' was processed on your account at ', 
                  DATE_FORMAT(NEW.transaction_date, '%h:%i %p'), ' on ', DATE_FORMAT(NEW.transaction_date, '%d-%b-%Y'), 
                  ' via ', NEW.transaction_mode, '. If this was not you, please contact us immediately.'),
            'SECURITY',
            'UNREAD',
            NOW()
        );
        
        -- Also log to audit trail for administrative review
        INSERT INTO cbs_audit_logs (
            log_id,
            action,
            entity_type,
            entity_id,
            user_id,
            action_timestamp,
            new_value,
            status,
            module,
            criticality
        ) VALUES (
            UUID(),
            'HIGH_VALUE_TRANSACTION',
            'TRANSACTION',
            NEW.transaction_id,
            NEW.initiated_by,
            NOW(),
            JSON_OBJECT(
                'amount', NEW.amount,
                'account_number', NEW.account_number,
                'transaction_type', NEW.transaction_type,
                'transaction_mode', NEW.transaction_mode
            ),
            'SUCCESS',
            'TRANSACTIONS',
            'HIGH'
        );
    END IF;
END$$

DELIMITER ;
