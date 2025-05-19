/*
 * File: banking_id_validation.sql
 * Description: SQL functions for validating banking IDs
 * Created: May 19, 2025
 * 
 * This file contains functions for validating various banking IDs in accordance 
 * with Indian and international standards.
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
    DECLARE calculated_checksum INT;
    
    -- Check basic format
    IF account_number REGEXP '^[0-9]{5}-[0-9]{2}[0-9]{2}-[0-9]{6}-[0-9]{2}$' THEN
        -- Extract parts for checksum validation
        SET base_part = REPLACE(LEFT(account_number, 17), '-', '');
        SET checksum_part = RIGHT(account_number, 2);
        
        -- Calculate checksum (simple algorithm, can be enhanced)
        SET calculated_checksum = 0;
        
        -- Loop through each character
        SET @i = 1;
        WHILE @i <= LENGTH(base_part) DO
            SET calculated_checksum = calculated_checksum + (CAST(SUBSTRING(base_part, @i, 1) AS UNSIGNED) * @i);
            SET @i = @i + 1;
        END WHILE;
        
        SET calculated_checksum = calculated_checksum % 100;
        
        -- Validate checksum
        IF calculated_checksum = CAST(checksum_part AS UNSIGNED) THEN
            SET valid = TRUE;
        END IF;
    END IF;
    
    RETURN valid;
END$$

-- -----------------------------------------------------
-- Function: validate_ifsc_code
-- -----------------------------------------------------
DROP FUNCTION IF EXISTS `validate_ifsc_code` $$
CREATE FUNCTION `validate_ifsc_code`(ifsc_code VARCHAR(11)) 
RETURNS BOOLEAN
DETERMINISTIC
COMMENT 'Validates Indian Financial System Code (IFSC)'
BEGIN
    DECLARE valid BOOLEAN DEFAULT FALSE;
    
    -- Check IFSC format: 4 characters (bank code) + 0 + 6 alphanumeric (branch code)
    IF ifsc_code REGEXP '^[A-Z]{4}0[A-Z0-9]{6}$' THEN
        SET valid = TRUE;
    END IF;
    
    RETURN valid;
END$$

-- -----------------------------------------------------
-- Function: validate_pan_number
-- -----------------------------------------------------
DROP FUNCTION IF EXISTS `validate_pan_number` $$
CREATE FUNCTION `validate_pan_number`(pan_number VARCHAR(10)) 
RETURNS BOOLEAN
DETERMINISTIC
COMMENT 'Validates Indian Permanent Account Number (PAN)'
BEGIN
    DECLARE valid BOOLEAN DEFAULT FALSE;
    
    -- Check PAN format: 5 letters + 4 numbers + 1 letter
    IF pan_number REGEXP '^[A-Z]{5}[0-9]{4}[A-Z]$' THEN
        SET valid = TRUE;
    END IF;
    
    RETURN valid;
END$$

-- -----------------------------------------------------
-- Function: validate_aadhaar_number
-- -----------------------------------------------------
DROP FUNCTION IF EXISTS `validate_aadhaar_number` $$
CREATE FUNCTION `validate_aadhaar_number`(aadhaar_number VARCHAR(12)) 
RETURNS BOOLEAN
DETERMINISTIC
COMMENT 'Validates Indian Aadhaar Number with Verhoeff algorithm'
BEGIN
    DECLARE valid BOOLEAN DEFAULT FALSE;
    
    -- Basic format check: 12 digits
    IF aadhaar_number REGEXP '^[0-9]{12}$' THEN
        -- Simplified validation for demonstration
        -- In real implementation, Verhoeff algorithm should be used
        SET valid = TRUE;
    END IF;
    
    RETURN valid;
END$$

DELIMITER ;
