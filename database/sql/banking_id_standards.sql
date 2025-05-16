/*
 * File: banking_id_standards.sql
 * Description: SQL implementation of Indian and international banking standards for ID formats
 * Date: May 13, 2025
 * 
 * This file contains functions, procedures, and triggers for validating and generating
 * banking IDs in accordance with Indian and international standards.
 */

DELIMITER $$

-- -----------------------------------------------------
-- Function: validate_customer_id
-- -----------------------------------------------------
DROP FUNCTION IF EXISTS `validate_customer_id` $$
CREATE FUNCTION `validate_customer_id`(customer_id VARCHAR(20)) 
RETURNS BOOLEAN
DETERMINISTIC
COMMENT 'Validates customer ID in format YYDDD-BBBBB-SSSS'
BEGIN
    DECLARE valid BOOLEAN DEFAULT FALSE;
    DECLARE year_part VARCHAR(2);
    DECLARE day_part VARCHAR(3);
    
    -- Check format: YYDDD-BBBBB-SSSS
    IF customer_id REGEXP '^[0-9]{2}[0-9]{3}-[0-9]{5}-[0-9]{4}$' THEN
        -- Extract parts for additional validation
        SET year_part = SUBSTRING(customer_id, 1, 2);
        SET day_part = SUBSTRING(customer_id, 3, 3);
        
        -- Validate day of year (1-366)
        IF CAST(day_part AS UNSIGNED) BETWEEN 1 AND 366 THEN
            SET valid = TRUE;
        END IF;
    END IF;
    
    RETURN valid;
END$$

-- -----------------------------------------------------
-- Function: validate_account_number
-- -----------------------------------------------------
DROP FUNCTION IF EXISTS `validate_account_number` $$
CREATE FUNCTION `validate_account_number`(account_number VARCHAR(20)) 
RETURNS BOOLEAN
DETERMINISTIC
COMMENT 'Validates account number in format BBBBB-AATT-CCCCCC-CC'
BEGIN
    DECLARE valid BOOLEAN DEFAULT FALSE;
    DECLARE base_part VARCHAR(17);
    DECLARE checksum_part VARCHAR(2);
    DECLARE calculated_checksum VARCHAR(2);
    
    -- Check format: BBBBB-AATT-CCCCCC-CC
    IF account_number REGEXP '^[0-9]{5}-[0-9]{2}[0-9]{2}-[0-9]{6}-[0-9]{2}$' THEN
        -- Extract parts for luhn algorithm validation
        SET base_part = CONCAT(
            SUBSTRING(account_number, 1, 5),  -- Branch code
            SUBSTRING(account_number, 7, 2),  -- Account type
            SUBSTRING(account_number, 9, 2),  -- Account subtype
            SUBSTRING(account_number, 12, 6)  -- Customer part
        );
        SET checksum_part = SUBSTRING(account_number, 19, 2);
        
        -- Call algorithm to calculate checksum (simplified for SQL)
        -- In a real implementation, you'd have a more complex function
        -- For now, we'll accept any checksum
        SET valid = TRUE;
    END IF;
    
    RETURN valid;
END$$

-- -----------------------------------------------------
-- Function: validate_transaction_id
-- -----------------------------------------------------
DROP FUNCTION IF EXISTS `validate_transaction_id` $$
CREATE FUNCTION `validate_transaction_id`(transaction_id VARCHAR(20)) 
RETURNS BOOLEAN
DETERMINISTIC
COMMENT 'Validates transaction ID in format TRX-YYYYMMDD-SSSSSS'
BEGIN
    DECLARE valid BOOLEAN DEFAULT FALSE;
    DECLARE date_part VARCHAR(8);
    DECLARE year_part VARCHAR(4);
    DECLARE month_part VARCHAR(2);
    DECLARE day_part VARCHAR(2);
    
    -- Check format: TRX-YYYYMMDD-SSSSSS
    IF transaction_id REGEXP '^TRX-[0-9]{8}-[0-9]{6}$' THEN
        -- Extract date part for validation
        SET date_part = SUBSTRING(transaction_id, 5, 8);
        SET year_part = SUBSTRING(date_part, 1, 4);
        SET month_part = SUBSTRING(date_part, 5, 2);
        SET day_part = SUBSTRING(date_part, 7, 2);
        
        -- Validate date components
        IF CAST(month_part AS UNSIGNED) BETWEEN 1 AND 12 AND
           CAST(day_part AS UNSIGNED) BETWEEN 1 AND 31 AND
           CAST(year_part AS UNSIGNED) BETWEEN 2000 AND 2100 THEN
            
            -- Additional validation for specific month lengths
            IF (month_part IN ('04', '06', '09', '11') AND day_part <= '30') OR
               (month_part != '02') OR
               (month_part = '02' AND 
                ((day_part <= '29' AND year_part % 4 = 0 AND (year_part % 100 != 0 OR year_part % 400 = 0)) OR
                 (day_part <= '28'))) THEN
                SET valid = TRUE;
            END IF;
        END IF;
    END IF;
    
    RETURN valid;
END$$

-- -----------------------------------------------------
-- Function: validate_employee_id
-- -----------------------------------------------------
DROP FUNCTION IF EXISTS `validate_employee_id` $$
CREATE FUNCTION `validate_employee_id`(employee_id VARCHAR(12)) 
RETURNS BOOLEAN
DETERMINISTIC
COMMENT 'Validates employee ID in format ZZBB-DD-EEEE'
BEGIN
    DECLARE valid BOOLEAN DEFAULT FALSE;
    
    -- Check format: ZZBB-DD-EEEE
    IF employee_id REGEXP '^[0-9]{2}[0-9]{2}-[0-9]{2}-[0-9]{4}$' THEN
        -- For simplicity, we'll just validate the format
        -- In a real implementation, you might validate zone codes, etc.
        SET valid = TRUE;
    END IF;
    
    RETURN valid;
END$$

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
    DECLARE seq_part VARCHAR(4);
    
    -- Get current date components
    SET year_part = DATE_FORMAT(CURDATE(), '%y');  -- Last 2 digits of year
    SET day_part = LPAD(DAYOFYEAR(CURDATE()), 3, '0');  -- Day of year (001-366)
    
    -- Get next sequence number - in a real system this would come from a sequence table
    -- For this example, we'll generate a random 4-digit number
    SET seq_part = LPAD(FLOOR(RAND() * 9000) + 1000, 4, '0');
    
    -- Format branch code to 5 digits
    SET branch_code = LPAD(branch_code, 5, '0');
    
    -- Assemble the ID
    SET new_id = CONCAT(year_part, day_part, '-', branch_code, '-', seq_part);
    
    RETURN new_id;
END$$

-- -----------------------------------------------------
-- Function: generate_account_number
-- -----------------------------------------------------
DROP FUNCTION IF EXISTS `generate_account_number` $$
CREATE FUNCTION `generate_account_number`(
    branch_code VARCHAR(5),
    account_type VARCHAR(2),
    sub_type VARCHAR(2),
    customer_seq VARCHAR(6)
) 
RETURNS VARCHAR(20)
NOT DETERMINISTIC
COMMENT 'Generates account number in format BBBBB-AATT-CCCCCC-CC'
BEGIN
    DECLARE new_account_number VARCHAR(20);
    DECLARE base_part VARCHAR(17);
    DECLARE checksum_part VARCHAR(2);
    
    -- Format inputs to ensure correct length
    SET branch_code = LPAD(branch_code, 5, '0');
    SET account_type = LPAD(account_type, 2, '0');
    SET sub_type = LPAD(sub_type, 2, '0');
    SET customer_seq = LPAD(customer_seq, 6, '0');
    
    -- Create base part for checksum calculation
    SET base_part = CONCAT(branch_code, account_type, sub_type, customer_seq);
    
    -- Calculate checksum (simplified for this example)
    -- In a real implementation, this would implement the Luhn algorithm
    SET checksum_part = RIGHT(CONCAT('00', (
        (CAST(SUBSTRING(base_part, 1, 1) AS UNSIGNED) * 1 + 
         CAST(SUBSTRING(base_part, 2, 1) AS UNSIGNED) * 2 +
         CAST(SUBSTRING(base_part, 3, 1) AS UNSIGNED) * 1 +
         CAST(SUBSTRING(base_part, 4, 1) AS UNSIGNED) * 2 +
         CAST(SUBSTRING(base_part, 5, 1) AS UNSIGNED) * 1 +
         CAST(SUBSTRING(base_part, 6, 1) AS UNSIGNED) * 2 +
         CAST(SUBSTRING(base_part, 7, 1) AS UNSIGNED) * 1 +
         CAST(SUBSTRING(base_part, 8, 1) AS UNSIGNED) * 2 +
         CAST(SUBSTRING(base_part, 9, 1) AS UNSIGNED) * 1 +
         CAST(SUBSTRING(base_part, 10, 1) AS UNSIGNED) * 2 +
         CAST(SUBSTRING(base_part, 11, 1) AS UNSIGNED) * 1 +
         CAST(SUBSTRING(base_part, 12, 1) AS UNSIGNED) * 2 +
         CAST(SUBSTRING(base_part, 13, 1) AS UNSIGNED) * 1 +
         CAST(SUBSTRING(base_part, 14, 1) AS UNSIGNED) * 2 +
         CAST(SUBSTRING(base_part, 15, 1) AS UNSIGNED) * 1
        ) % 97)), 2);
    
    -- Assemble the account number
    SET new_account_number = CONCAT(
        branch_code, '-',
        account_type, sub_type, '-',
        customer_seq, '-',
        checksum_part
    );
    
    RETURN new_account_number;
END$$

-- -----------------------------------------------------
-- Function: generate_transaction_id
-- -----------------------------------------------------
DROP FUNCTION IF EXISTS `generate_transaction_id` $$
CREATE FUNCTION `generate_transaction_id`() 
RETURNS VARCHAR(20)
NOT DETERMINISTIC
COMMENT 'Generates transaction ID in format TRX-YYYYMMDD-SSSSSS'
BEGIN
    DECLARE new_transaction_id VARCHAR(20);
    DECLARE date_part VARCHAR(8);
    DECLARE seq_part VARCHAR(6);
    
    -- Get current date in YYYYMMDD format
    SET date_part = DATE_FORMAT(NOW(), '%Y%m%d');
    
    -- Get next sequence number - in a real system this would come from a sequence table
    -- For this example, we'll generate a random 6-digit number
    SET seq_part = LPAD(FLOOR(RAND() * 900000) + 100000, 6, '0');
    
    -- Assemble the transaction ID
    SET new_transaction_id = CONCAT('TRX-', date_part, '-', seq_part);
    
    RETURN new_transaction_id;
END$$

-- -----------------------------------------------------
-- Function: generate_employee_id
-- -----------------------------------------------------
DROP FUNCTION IF EXISTS `generate_employee_id` $$
CREATE FUNCTION `generate_employee_id`(
    zone_code VARCHAR(2),
    branch_code VARCHAR(2),
    designation_code VARCHAR(2)
) 
RETURNS VARCHAR(12)
NOT DETERMINISTIC
COMMENT 'Generates employee ID in format ZZBB-DD-EEEE'
BEGIN
    DECLARE new_employee_id VARCHAR(12);
    DECLARE seq_part VARCHAR(4);
    
    -- Format inputs to ensure correct length
    SET zone_code = LPAD(zone_code, 2, '0');
    SET branch_code = LPAD(branch_code, 2, '0');
    SET designation_code = LPAD(designation_code, 2, '0');
    
    -- Get next sequence number - in a real system this would come from a sequence table
    -- For this example, we'll generate a random 4-digit number
    SET seq_part = LPAD(FLOOR(RAND() * 9000) + 1000, 4, '0');
    
    -- Assemble the employee ID
    SET new_employee_id = CONCAT(zone_code, branch_code, '-', designation_code, '-', seq_part);
    
    RETURN new_employee_id;
END$$

DELIMITER ;
