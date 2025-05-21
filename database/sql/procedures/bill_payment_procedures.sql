-- Bill Payment Procedures for Core Banking System
-- Contains stored procedures related to bill payment operations
-- Created: May 21, 2025

DELIMITER $$

-- Procedure: Process bill payment
DROP PROCEDURE IF EXISTS process_bill_payment$$
CREATE PROCEDURE process_bill_payment(
    IN p_customer_id VARCHAR(20),
    IN p_account_number VARCHAR(20),
    IN p_biller_id VARCHAR(50),
    IN p_consumer_number VARCHAR(50),
    IN p_amount DECIMAL(12,2),
    IN p_remarks VARCHAR(255),
    OUT p_payment_id VARCHAR(36),
    OUT p_status VARCHAR(20),
    OUT p_message VARCHAR(255)
)
BEGIN
    DECLARE v_balance DECIMAL(12,2);
    DECLARE v_account_status VARCHAR(50);
    DECLARE v_biller_name VARCHAR(100);
    DECLARE v_biller_category VARCHAR(50);
    DECLARE v_transaction_id VARCHAR(30);
    DECLARE v_transaction_date DATETIME;
    DECLARE v_new_balance DECIMAL(12,2);
    
    -- For transaction handling
    DECLARE EXIT HANDLER FOR SQLEXCEPTION 
    BEGIN
        ROLLBACK;
        SET p_status = 'FAILED';
        SET p_message = 'Database error occurred during bill payment';
    END;
    
    START TRANSACTION;
    
    -- Set transaction date to current timestamp
    SET v_transaction_date = NOW();
    SET p_payment_id = UUID();
    SET v_transaction_id = CONCAT('TXN', DATE_FORMAT(NOW(), '%Y%m%d'), LPAD(FLOOR(RAND() * 1000000), 6, '0'));
    
    -- Get biller information
    SELECT biller_name, biller_category
    INTO v_biller_name, v_biller_category
    FROM cbs_customer_billers 
    WHERE customer_id = p_customer_id 
    AND biller_id = p_biller_id 
    AND consumer_number = p_consumer_number;
    
    -- If biller not found in saved billers, use provided values
    IF v_biller_name IS NULL THEN
        SET v_biller_name = CONCAT('Biller ', p_biller_id);
        SET v_biller_category = 'OTHER';
    END IF;
    
    -- Check account status and balance
    SELECT balance, status INTO v_balance, v_account_status
    FROM cbs_accounts 
    WHERE account_number = p_account_number 
    AND customer_id = p_customer_id
    FOR UPDATE;
    
    -- Validate account
    IF v_account_status IS NULL THEN
        SET p_status = 'FAILED';
        SET p_message = 'Account does not exist or does not belong to customer';
        ROLLBACK;
    ELSEIF v_account_status != 'ACTIVE' THEN
        SET p_status = 'FAILED';
        SET p_message = CONCAT('Account is ', v_account_status, '. Bill payment not allowed');
        ROLLBACK;
    ELSEIF v_balance < p_amount THEN
        SET p_status = 'FAILED';
        SET p_message = 'Insufficient balance';
        ROLLBACK;
    ELSE
        -- Calculate new balance
        SET v_new_balance = v_balance - p_amount;
        
        -- Update account balance
        UPDATE cbs_accounts 
        SET 
            balance = v_new_balance,
            last_transaction = v_transaction_date 
        WHERE account_number = p_account_number;
        
        -- Record bill payment
        INSERT INTO cbs_bill_payments (
            payment_id,
            customer_id,
            account_number,
            biller_id,
            biller_name,
            biller_category,
            consumer_number,
            amount,
            payment_date,
            payment_status,
            transaction_id,
            reference_number,
            remarks,
            created_at
        ) VALUES (
            p_payment_id,
            p_customer_id,
            p_account_number,
            p_biller_id,
            v_biller_name,
            v_biller_category,
            p_consumer_number,
            p_amount,
            v_transaction_date,
            'COMPLETED',
            v_transaction_id,
            v_transaction_id,
            p_remarks,
            v_transaction_date
        );
        
        -- Record in main transactions table
        INSERT INTO cbs_transactions (
            transaction_id,
            transaction_type,
            account_number,
            amount,
            currency,
            transaction_date,
            description,
            reference_number,
            transaction_status,
            transaction_mode,
            balance_after_transaction,
            remarks,
            branch_code,
            created_at
        ) VALUES (
            v_transaction_id,
            'PAYMENT',
            p_account_number,
            p_amount,
            'INR',
            v_transaction_date,
            CONCAT('Bill payment to ', v_biller_name),
            v_transaction_id,
            'COMPLETED',
            'INTERNET_BANKING',
            v_new_balance,
            CONCAT('Consumer No: ', p_consumer_number),
            (SELECT branch_code FROM cbs_accounts WHERE account_number = p_account_number),
            v_transaction_date
        );
        
        -- Set output parameters for success
        SET p_status = 'SUCCESS';
        SET p_message = CONCAT('Bill payment of ', p_amount, ' to ', v_biller_name, ' completed successfully');
        
        COMMIT;
    END IF;
END$$

-- Procedure: Setup Auto Bill Payment
DROP PROCEDURE IF EXISTS setup_auto_bill_payment$$
CREATE PROCEDURE setup_auto_bill_payment(
    IN p_customer_id VARCHAR(20),
    IN p_biller_id VARCHAR(50),
    IN p_consumer_number VARCHAR(50),
    IN p_auto_pay_limit DECIMAL(12,2),
    IN p_auto_pay_account VARCHAR(20),
    OUT p_status VARCHAR(20),
    OUT p_message VARCHAR(255)
)
BEGIN
    DECLARE v_count INT DEFAULT 0;
    DECLARE v_account_status VARCHAR(50);
    
    -- Check if account exists and belongs to customer
    SELECT COUNT(*) INTO v_count
    FROM cbs_accounts 
    WHERE account_number = p_auto_pay_account 
    AND customer_id = p_customer_id;
    
    IF v_count = 0 THEN
        SET p_status = 'FAILED';
        SET p_message = 'Account does not exist or does not belong to customer';
        LEAVE proc_exit;
    END IF;
    
    -- Check if biller exists
    SELECT COUNT(*) INTO v_count
    FROM cbs_customer_billers
    WHERE customer_id = p_customer_id
    AND biller_id = p_biller_id
    AND consumer_number = p_consumer_number;
    
    -- Update existing biller
    IF v_count > 0 THEN
        UPDATE cbs_customer_billers
        SET 
            auto_pay_enabled = 1,
            auto_pay_limit = p_auto_pay_limit,
            auto_pay_account = p_auto_pay_account,
            updated_at = NOW()
        WHERE 
            customer_id = p_customer_id
            AND biller_id = p_biller_id
            AND consumer_number = p_consumer_number;
            
        SET p_status = 'SUCCESS';
        SET p_message = 'Auto bill payment setup updated successfully';
    ELSE
        SET p_status = 'FAILED';
        SET p_message = 'Biller not found. Please add the biller first';
    END IF;
    
    proc_exit: BEGIN
    END;
END$$

DELIMITER ;
