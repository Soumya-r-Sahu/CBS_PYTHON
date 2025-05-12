-- Fixed version of the check_daily_withdrawal_limit stored procedure

DROP PROCEDURE IF EXISTS check_daily_withdrawal_limit;

DELIMITER $$

-- Create stored procedure to check daily withdrawal limits
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
    
    -- Set default channel if NULL
    IF p_channel IS NULL THEN
        SET p_channel = 'ATM';
    END IF;
    
    -- Get today's date
    SET v_today = CURDATE();
    
    -- Check card status
    SELECT c.status, c.account_id, a.status 
    INTO v_card_status, v_account_number, v_account_status
    FROM cbs_cards c
    LEFT JOIN cbs_accounts a ON c.account_id = a.account_number
    WHERE c.card_number = p_card_number;
    
    -- Validate card and account status
    IF v_card_status IS NULL THEN
        SET p_can_withdraw = FALSE;
        SET p_remaining_limit = 0;
        SET p_message = 'Invalid card number';
        
        -- Log attempted operation with invalid card (commented out for simplicity)
        /*INSERT INTO cbs_system_logs (log_level, component, module, message, details)
        VALUES ('WARNING', 'CARD_OPERATIONS', 'WITHDRAWAL_CHECK', 
                CONCAT('Invalid card: ', p_card_number),
                CONCAT('Amount: ', p_amount, ', Channel: ', p_channel));*/
                
        RETURN;
    ELSEIF v_card_status != 'ACTIVE' THEN
        SET p_can_withdraw = FALSE;
        SET p_remaining_limit = 0;
        SET p_message = CONCAT('Card is ', v_card_status);
        
        -- Log commented out for simplicity
        
        RETURN;
    ELSEIF v_account_status != 'ACTIVE' THEN
        SET p_can_withdraw = FALSE;
        SET p_remaining_limit = 0;
        SET p_message = CONCAT('Account is ', v_account_status);
        
        -- Log commented out for simplicity
                
        RETURN;
    END IF;
    
    -- Get card's daily limit based on channel
    IF p_channel = 'ATM' THEN
        SELECT daily_atm_limit INTO v_daily_limit
        FROM cbs_cards
        WHERE card_number = p_card_number;
    ELSEIF p_channel = 'POS' THEN
        SELECT daily_pos_limit INTO v_daily_limit
        FROM cbs_cards
        WHERE card_number = p_card_number;
    ELSE
        SELECT daily_online_limit INTO v_daily_limit
        FROM cbs_cards
        WHERE card_number = p_card_number;
    END IF;
    
    -- Get total withdrawals today
    SELECT COALESCE(SUM(amount), 0) INTO v_total_today
    FROM cbs_daily_withdrawals
    WHERE card_number = p_card_number 
    AND withdrawal_date = v_today;
    
    -- Calculate remaining limit
    SET p_remaining_limit = v_daily_limit - v_total_today;
    
    -- Check if withdrawal is allowed
    IF (v_total_today + p_amount) <= v_daily_limit THEN
        SET p_can_withdraw = TRUE;
        SET p_message = 'Withdrawal allowed';
    ELSE
        SET p_can_withdraw = FALSE;
        SET p_message = CONCAT('Exceeds daily limit. Remaining limit: ', p_remaining_limit);
        
        -- Log commented out for simplicity
    END IF;
END$$

DELIMITER ;
