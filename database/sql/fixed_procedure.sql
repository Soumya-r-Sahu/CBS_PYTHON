# Fixed SQL Stored Procedures

## Issue: Syntax errors in stored procedures
## Description: Fixed MySQL syntax issues in stored procedures for the Core Banking System

DELIMITER $$

DROP PROCEDURE IF EXISTS `check_withdrawal_eligibility` $$
CREATE PROCEDURE `check_withdrawal_eligibility`(
    IN p_card_number VARCHAR(16),
    IN p_requested_amount DECIMAL(10,2),
    OUT p_can_withdraw BOOLEAN,
    OUT p_message VARCHAR(100),
    OUT p_available_balance DECIMAL(10,2)
)
BEGIN
    DECLARE v_account_id INT;
    DECLARE v_card_status VARCHAR(20);
    DECLARE v_current_balance DECIMAL(10,2);
    DECLARE v_daily_limit DECIMAL(10,2);
    DECLARE v_daily_used DECIMAL(10,2);
    DECLARE v_min_balance DECIMAL(10,2);
    
    -- Initialize output parameters
    SET p_can_withdraw = FALSE;
    SET p_message = NULL;
    SET p_available_balance = 0;
    
    -- Check if card exists and get account details
    SELECT 
        c.account_id, 
        c.status, 
        a.balance,
        a.minimum_balance,
        c.daily_withdrawal_limit
    INTO 
        v_account_id, 
        v_card_status, 
        v_current_balance,
        v_min_balance,
        v_daily_limit
    FROM 
        cards c
    JOIN 
        accounts a ON c.account_id = a.id
    WHERE 
        c.card_number = p_card_number;
        
    -- Check if card exists
    IF v_account_id IS NULL THEN
        SET p_can_withdraw = FALSE;
        SET p_message = 'Card does not exist';
        SET p_available_balance = 0;
        RETURN;
    ELSEIF v_card_status != 'ACTIVE' THEN
        SET p_can_withdraw = FALSE;
        SET p_message = CONCAT('Card is not active. Current status: ', v_card_status);
        SET p_available_balance = 0;
        RETURN;
    END IF;
    
    -- Get daily used amount
    SELECT 
        COALESCE(SUM(amount), 0) 
    INTO 
        v_daily_used
    FROM 
        transactions
    WHERE 
        account_id = v_account_id
        AND transaction_type = 'WITHDRAWAL'
        AND transaction_date >= CURDATE()
        AND transaction_date < CURDATE() + INTERVAL 1 DAY;
    
    -- Calculate available balance (respecting minimum balance)
    SET p_available_balance = v_current_balance - v_min_balance;
    
    -- Check if withdrawal amount exceeds available balance
    IF p_requested_amount > p_available_balance THEN
        SET p_can_withdraw = FALSE;
        SET p_message = 'Insufficient balance';
        RETURN;
    END IF;
    
    -- Check if withdrawal exceeds daily limit
    IF (v_daily_used + p_requested_amount) > v_daily_limit THEN
        SET p_can_withdraw = FALSE;
        SET p_message = CONCAT('Daily withdrawal limit exceeded. Remaining limit: ', (v_daily_limit - v_daily_used));
        RETURN;
    END IF;
    
    -- If all checks pass
    SET p_can_withdraw = TRUE;
    SET p_message = 'Withdrawal allowed';
    RETURN;
END$$

DROP PROCEDURE IF EXISTS `process_withdrawal` $$
CREATE PROCEDURE `process_withdrawal`(
    IN p_card_number VARCHAR(16),
    IN p_amount DECIMAL(10,2),
    IN p_atm_id VARCHAR(20),
    OUT p_transaction_id VARCHAR(36),
    OUT p_status VARCHAR(20),
    OUT p_message VARCHAR(100)
)
BEGIN
    DECLARE v_account_id INT;
    DECLARE v_can_withdraw BOOLEAN;
    DECLARE v_available_balance DECIMAL(10,2);
    DECLARE v_error_message VARCHAR(100);
    
    -- Check withdrawal eligibility
    CALL check_withdrawal_eligibility(
        p_card_number, 
        p_amount, 
        v_can_withdraw, 
        v_error_message, 
        v_available_balance
    );
    
    -- If withdrawal is not allowed
    IF v_can_withdraw = FALSE THEN
        SET p_transaction_id = NULL;
        SET p_status = 'FAILED';
        SET p_message = v_error_message;
        RETURN;
    END IF;
    
    -- Get account ID for the card
    SELECT account_id INTO v_account_id
    FROM cards
    WHERE card_number = p_card_number;
    
    -- Generate transaction ID
    SET p_transaction_id = UUID();
    
    -- Process withdrawal
    UPDATE accounts
    SET balance = balance - p_amount
    WHERE id = v_account_id;
    
    -- Record transaction
    INSERT INTO transactions (
        transaction_id,
        account_id,
        transaction_type,
        amount,
        transaction_date,
        description,
        status,
        reference
    ) VALUES (
        p_transaction_id,
        v_account_id,
        'WITHDRAWAL',
        p_amount,
        NOW(),
        CONCAT('ATM Withdrawal - ', p_atm_id),
        'SUCCESS',
        p_atm_id
    );
    
    -- Set output parameters
    SET p_status = 'SUCCESS';
    SET p_message = CONCAT('Withdrawal successful. New balance: ', (v_available_balance - p_amount + v_min_balance));
    
    -- Audit log entry would be created here in a real system
END$$

DELIMITER ;
