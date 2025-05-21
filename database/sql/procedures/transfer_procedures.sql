-- Transfer Procedures for Core Banking System
-- Contains stored procedures related to transfer operations
-- Created: May 19, 2025

DELIMITER $$

-- Procedure: Process fund transfer 
DROP PROCEDURE IF EXISTS process_fund_transfer$$
CREATE PROCEDURE process_fund_transfer(
    IN p_source_account VARCHAR(20),
    IN p_destination_account VARCHAR(20),
    IN p_amount DECIMAL(12,2),
    IN p_transfer_type VARCHAR(20),
    IN p_remarks VARCHAR(255),
    IN p_channel VARCHAR(20),
    IN p_user_id VARCHAR(50),
    OUT p_transaction_id VARCHAR(30),
    OUT p_status VARCHAR(10),
    OUT p_message VARCHAR(255)
)
BEGIN
    DECLARE v_source_balance DECIMAL(12,2);
    DECLARE v_minimum_balance DECIMAL(10,2);
    DECLARE v_source_status VARCHAR(20);
    DECLARE v_dest_status VARCHAR(20);
    DECLARE v_transaction_date DATETIME;
    DECLARE v_reference_number VARCHAR(20);
    -- Initialize outputs
    SET p_transaction_id = CONCAT('TRX', DATE_FORMAT(NOW(), '%Y%m%d'), LPAD(FLOOR(RAND() * 1000000), 6, '0'));
    SET p_status = 'FAILED';
    SET p_message = 'Transfer failed';
    SET v_transaction_date = NOW();
    
    -- Generate unique reference number
    SET v_reference_number = CONCAT('TRF', DATE_FORMAT(NOW(), '%Y%m%d%H%i%s'), FLOOR(RAND()*1000));
    
    -- Start transaction
    START TRANSACTION;
    
    -- Check if accounts exist and are active
    SELECT balance, minimum_balance, status INTO v_source_balance, v_minimum_balance, v_source_status
    FROM cbs_accounts WHERE account_number = p_source_account FOR UPDATE;
    
    SELECT status INTO v_dest_status
    FROM cbs_accounts WHERE account_number = p_destination_account FOR UPDATE;
    
    -- Validate accounts
    IF v_source_status IS NULL THEN
        SET p_message = 'Source account does not exist';
        ROLLBACK;
    ELSEIF v_dest_status IS NULL THEN
        SET p_message = 'Destination account does not exist';
        ROLLBACK;
    ELSEIF v_source_status != 'ACTIVE' THEN
        SET p_message = CONCAT('Source account is ', v_source_status);
        ROLLBACK;
    ELSEIF v_dest_status != 'ACTIVE' THEN
        SET p_message = CONCAT('Destination account is ', v_dest_status);
        ROLLBACK;
    ELSEIF p_amount <= 0 THEN
        SET p_message = 'Invalid transfer amount';
        ROLLBACK;
    ELSEIF (v_source_balance - p_amount) < v_minimum_balance THEN
        SET p_message = 'Insufficient balance';
        ROLLBACK;
    ELSE
        -- Update source account
        UPDATE cbs_accounts 
        SET balance = balance - p_amount, 
            last_transaction = v_transaction_date
        WHERE account_number = p_source_account;
        
        -- Update destination account
        UPDATE cbs_accounts 
        SET balance = balance + p_amount, 
            last_transaction = v_transaction_date
        WHERE account_number = p_destination_account;
        -- Insert into transactions table
        INSERT INTO cbs_transactions (
            transaction_id, 
            transaction_type, 
            account_number, 
            counter_account, 
            amount, 
            currency,
            transaction_date, 
            description, 
            reference_number, 
            transaction_status, 
            transaction_mode, 
            remarks, 
            initiated_by,
            branch_code,
            created_at
        ) VALUES (
            p_transaction_id, 
            'TRANSFER', 
            p_source_account, 
            p_destination_account, 
            p_amount, 
            'INR',
            v_transaction_date, 
            CONCAT('Fund transfer to account ', p_destination_account), 
            v_reference_number, 
            'COMPLETED', 
            p_channel, 
            p_remarks, 
            p_user_id,
            (SELECT branch_code FROM cbs_accounts WHERE account_number = p_source_account),
            v_transaction_date
        );
        -- Create notification for transfer
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
            (SELECT customer_id FROM cbs_accounts WHERE account_number = p_source_account),
            'CUSTOMER',
            CONCAT('Fund transfer of ₹', FORMAT(p_amount, 2), ' completed'),
            CONCAT('Your fund transfer of ₹', FORMAT(p_amount, 2), ' to account ', p_destination_account, ' was successful. Ref: ', v_reference_number),
            'INFO',
            'UNREAD',
            v_transaction_date
        );
        
        -- Notification for recipient
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
            (SELECT customer_id FROM cbs_accounts WHERE account_number = p_destination_account),
            'CUSTOMER',
            CONCAT('₹', FORMAT(p_amount, 2), ' credited to your account'),
            CONCAT('Your account has been credited with ₹', FORMAT(p_amount, 2), '. Ref: ', v_reference_number),
            'INFO',
            'UNREAD',
            v_transaction_date
        );
        
        -- Set success response
        SET p_status = 'SUCCESS';
        SET p_message = 'Transfer completed successfully';
        
        COMMIT;
    END IF;
END$$

DELIMITER ;
