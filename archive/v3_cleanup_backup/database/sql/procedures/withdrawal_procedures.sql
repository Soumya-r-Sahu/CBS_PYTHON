-- Withdrawal Procedures for Core Banking System
-- Contains stored procedures related to withdrawal operations
-- Created: May 19, 2025

DELIMITER $$

-- Procedure: Check daily withdrawal limit
DROP PROCEDURE IF EXISTS check_daily_withdrawal_limit$$
CREATE PROCEDURE check_daily_withdrawal_limit(
    IN p_card_number VARCHAR(20),
    IN p_amount DECIMAL(10,2),
    IN p_channel VARCHAR(10),
    OUT p_can_withdraw BOOLEAN,
    OUT p_remaining_limit DECIMAL(10,2),
    OUT p_message VARCHAR(255)
)
BEGIN
    DECLARE v_total_today DECIMAL(10,2);
    DECLARE v_daily_limit DECIMAL(10,2);
    DECLARE v_today DATE;
    DECLARE v_card_status VARCHAR(20);
    DECLARE v_account_status VARCHAR(20);
    DECLARE v_account_number VARCHAR(20);

    IF p_channel IS NULL THEN
        SET p_channel = 'ATM';
    END IF;
    SET v_today = CURDATE();
    SELECT c.status, c.account_id, a.status 
        INTO v_card_status, v_account_number, v_account_status
        FROM cbs_cards c
        LEFT JOIN cbs_accounts a ON c.account_id = a.account_number
        WHERE c.card_number = p_card_number;
    IF v_card_status IS NULL THEN
        SET p_can_withdraw = FALSE;
        SET p_remaining_limit = 0;
        SET p_message = 'Invalid card number';
        RETURN;
    ELSEIF v_card_status != 'ACTIVE' THEN
        SET p_can_withdraw = FALSE;
        SET p_remaining_limit = 0;
        SET p_message = CONCAT('Card is ', v_card_status);
        RETURN;
    ELSEIF v_account_status != 'ACTIVE' THEN
        SET p_can_withdraw = FALSE;
        SET p_remaining_limit = 0;
        SET p_message = CONCAT('Account is ', v_account_status);
        RETURN;
    END IF;
    IF p_channel = 'ATM' THEN
        SELECT daily_atm_limit INTO v_daily_limit FROM cbs_cards WHERE card_number = p_card_number;
    ELSEIF p_channel = 'POS' THEN
        SELECT daily_pos_limit INTO v_daily_limit FROM cbs_cards WHERE card_number = p_card_number;
    ELSE
        SELECT daily_online_limit INTO v_daily_limit FROM cbs_cards WHERE card_number = p_card_number;
    END IF;
    SELECT COALESCE(SUM(amount), 0) INTO v_total_today FROM cbs_daily_withdrawals WHERE card_number = p_card_number AND withdrawal_date = v_today;
    SET p_remaining_limit = v_daily_limit - v_total_today;
    IF (v_total_today + p_amount) <= v_daily_limit THEN
        SET p_can_withdraw = TRUE;
        SET p_message = 'Withdrawal allowed';
    ELSE
        SET p_can_withdraw = FALSE;
        SET p_message = CONCAT('Exceeds daily limit. Remaining limit: ', p_remaining_limit);
    END IF;
END$$

-- Procedure: Check withdrawal eligibility (fixed version)
DROP PROCEDURE IF EXISTS check_withdrawal_eligibility$$
CREATE PROCEDURE check_withdrawal_eligibility(
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
        SET p_message = 'Invalid card number';
        RETURN;
    END IF;
    
    -- Check card status
    IF v_card_status != 'ACTIVE' THEN
        SET p_can_withdraw = FALSE;
        SET p_message = CONCAT('Card is ', v_card_status);
        RETURN;
    END IF;
    
    -- Get daily used amount
    SELECT COALESCE(SUM(amount), 0) 
    INTO v_daily_used 
    FROM transactions 
    WHERE 
        card_number = p_card_number 
        AND transaction_type = 'WITHDRAWAL'
        AND DATE(transaction_date) = CURRENT_DATE();
    
    -- Check available balance after minimum balance
    SET p_available_balance = v_current_balance - v_min_balance;
    
    -- Check if withdrawal is possible
    IF p_requested_amount > p_available_balance THEN
        SET p_can_withdraw = FALSE;
        SET p_message = 'Insufficient balance';
    ELSEIF (v_daily_used + p_requested_amount) > v_daily_limit THEN
        SET p_can_withdraw = FALSE;
        SET p_message = CONCAT('Daily limit exceeded. Available: ', (v_daily_limit - v_daily_used));
    ELSE
        SET p_can_withdraw = TRUE;
        SET p_message = 'Withdrawal allowed';
    END IF;
END$$

DELIMITER ;
