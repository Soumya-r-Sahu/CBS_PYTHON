/*
 * File: banking_id_generation.sql
 * Description: SQL functions for generating banking IDs
 * Created: May 19, 2025
 * 
 * This file contains functions for generating various banking IDs in accordance 
 * with Indian and international standards.
 */

DELIMITER $$

-- -----------------------------------------------------
-- Function: generate_customer_id
-- -----------------------------------------------------
DROP FUNCTION IF EXISTS `generate_customer_id` $$
CREATE FUNCTION `generate_customer_id`(branch_code VARCHAR(5)) 
RETURNS VARCHAR(20)
NOT DETERMINISTIC
COMMENT 'Generates customer ID in format YYDDD-BBBBB-SSSS'
BEGIN
    DECLARE new_id VARCHAR(20);
    DECLARE year_part VARCHAR(2);
    DECLARE day_part VARCHAR(3);
    DECLARE sequence_part VARCHAR(4);
    
    -- Get year and day parts from current date
    SET year_part = RIGHT(YEAR(CURDATE()), 2);
    SET day_part = LPAD(DAYOFYEAR(CURDATE()), 3, '0');
    
    -- Get next sequence number for today
    SET @seq := 0;
    SELECT IFNULL(MAX(RIGHT(customer_id, 4)), '0000') INTO sequence_part
    FROM cbs_customers
    WHERE customer_id LIKE CONCAT(year_part, day_part, '-%');
    
    -- Increment sequence
    SET sequence_part = LPAD(CAST(sequence_part AS UNSIGNED) + 1, 4, '0');
    
    -- Construct new ID
    SET new_id = CONCAT(year_part, day_part, '-', LPAD(branch_code, 5, '0'), '-', sequence_part);
    
    RETURN new_id;
END$$

-- -----------------------------------------------------
-- Function: generate_account_number
-- -----------------------------------------------------
DROP FUNCTION IF EXISTS `generate_account_number` $$
CREATE FUNCTION `generate_account_number`(
    branch_code VARCHAR(5),
    account_type VARCHAR(2)
) 
RETURNS VARCHAR(20)
NOT DETERMINISTIC
COMMENT 'Generates account number in format BBBBB-AATT-CCCCCC-CC'
BEGIN
    DECLARE new_number VARCHAR(20);
    DECLARE base_part VARCHAR(17);
    DECLARE checksum INT;
    DECLARE current_year VARCHAR(2);
    DECLARE sequence_part VARCHAR(6);
    
    -- Get current year
    SET current_year = RIGHT(YEAR(CURDATE()), 2);
    
    -- Get next sequence number
    SELECT IFNULL(MAX(SUBSTRING_INDEX(SUBSTRING_INDEX(account_number, '-', 3), '-', -1)), '000000')
    INTO sequence_part
    FROM cbs_accounts
    WHERE account_number LIKE CONCAT(LPAD(branch_code, 5, '0'), '-', account_type, current_year, '-%');
    
    -- Increment sequence
    SET sequence_part = LPAD(CAST(sequence_part AS UNSIGNED) + 1, 6, '0');
    
    -- Construct base part
    SET base_part = CONCAT(LPAD(branch_code, 5, '0'), account_type, current_year, sequence_part);
    
    -- Calculate checksum (simple algorithm)
    SET checksum = 0;
    SET @i = 1;
    WHILE @i <= LENGTH(base_part) DO
        SET checksum = checksum + (CAST(SUBSTRING(base_part, @i, 1) AS UNSIGNED) * @i);
        SET @i = @i + 1;
    END WHILE;
    
    SET checksum = checksum % 100;
    
    -- Format account number with dashes
    SET new_number = CONCAT(
        LPAD(branch_code, 5, '0'), '-',
        account_type, current_year, '-',
        sequence_part, '-',
        LPAD(checksum, 2, '0')
    );
    
    RETURN new_number;
END$$

-- -----------------------------------------------------
-- Function: generate_card_number
-- -----------------------------------------------------
DROP FUNCTION IF EXISTS `generate_card_number` $$
CREATE FUNCTION `generate_card_number`(
    card_type ENUM('DEBIT', 'CREDIT', 'PREPAID')
) 
RETURNS VARCHAR(16)
NOT DETERMINISTIC
COMMENT 'Generates card number with Luhn algorithm checksum'
BEGIN
    DECLARE new_number VARCHAR(16);
    DECLARE bin VARCHAR(6);
    DECLARE account_part VARCHAR(9);
    DECLARE check_digit INT;
    DECLARE card_sum INT;
    DECLARE i INT;
    
    -- Set BIN based on card type
    IF card_type = 'DEBIT' THEN
        SET bin = '558642';
    ELSEIF card_type = 'CREDIT' THEN
        SET bin = '468921';
    ELSE
        SET bin = '608372';
    END IF;
    
    -- Generate random account part
    SET account_part = '';
    SET i = 1;
    WHILE i <= 9 DO
        SET account_part = CONCAT(account_part, FLOOR(RAND() * 10));
        SET i = i + 1;
    END WHILE;
    
    -- Calculate Luhn algorithm check digit
    SET new_number = CONCAT(bin, account_part, '0');
    SET card_sum = 0;
    SET i = 1;
    
    WHILE i <= 16 DO
        DECLARE digit INT;
        DECLARE position_value INT;
        
        SET digit = CAST(SUBSTRING(new_number, i, 1) AS UNSIGNED);
        
        IF i % 2 = 0 THEN
            SET position_value = digit;
        ELSE
            SET position_value = digit * 2;
            IF position_value > 9 THEN
                SET position_value = position_value - 9;
            END IF;
        END IF;
        
        SET card_sum = card_sum + position_value;
        SET i = i + 1;
    END WHILE;
    
    SET check_digit = (10 - (card_sum % 10)) % 10;
    
    -- Apply check digit
    SET new_number = CONCAT(bin, account_part, check_digit);
    
    RETURN new_number;
END$$

DELIMITER ;
