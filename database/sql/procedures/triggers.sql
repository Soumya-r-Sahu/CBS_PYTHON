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
            user_id,
            action,
            entity_type,
            entity_id,
            previous_value,
            new_value,
            details,
            status
        ) VALUES (
            COALESCE(@current_user_id, 'SYSTEM'),
            'UPDATE',
            'ACCOUNT',
            NEW.account_number,
            CONCAT('{"balance": ', OLD.balance, '}'),
            CONCAT('{"balance": ', NEW.balance, '}'),
            CONCAT('Account balance changed by ', (NEW.balance - OLD.balance)),
            'SUCCESS'
        );
    END IF;
    
    -- Log status changes
    IF OLD.status != NEW.status THEN
        INSERT INTO cbs_audit_logs (
            user_id,
            action,
            entity_type,
            entity_id,
            previous_value,
            new_value,
            details,
            status
        ) VALUES (
            COALESCE(@current_user_id, 'SYSTEM'),
            'UPDATE',
            'ACCOUNT',
            NEW.account_number,
            CONCAT('{"status": "', OLD.status, '"}'),
            CONCAT('{"status": "', NEW.status, '"}'),
            CONCAT('Account status changed from ', OLD.status, ' to ', NEW.status),
            'SUCCESS'
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
        user_id,
        action,
        entity_type,
        entity_id,
        new_value,
        details,
        status
    ) VALUES (
        COALESCE(@current_user_id, 'SYSTEM'),
        'CREATE',
        'CUSTOMER',
        NEW.customer_id,
        JSON_OBJECT(
            'name', NEW.name,
            'email', NEW.email,
            'phone', NEW.phone,
            'status', NEW.status
        ),
        'New customer record created',
        'SUCCESS'
    );
    
    -- Send welcome notification (placeholder)
    INSERT INTO cbs_notifications (
        notification_type,
        recipient_id,
        subject,
        message,
        priority,
        status
    ) VALUES (
        'WELCOME',
        NEW.customer_id,
        'Welcome to our bank',
        CONCAT('Dear ', NEW.name, ', welcome to our banking services.'),
        'HIGH',
        'PENDING'
    );
END$$

DELIMITER ;
