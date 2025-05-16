/*
 * File: international_id_standards.sql
 * Description: SQL implementation of international banking ID standards
 * Date: May 13, 2025
 * 
 * This file contains functions and procedures for validating international
 * banking identifiers such as IBAN, SWIFT/BIC, IFSC, etc.
 */

DELIMITER $$

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
    
    -- IFSC format: AAAA0123456
    -- First 4 characters: Bank code (alphabets)
    -- 5th character: 0 (reserved for future use)
    -- Last 6 characters: Branch code (alphanumeric)
    
    IF ifsc_code REGEXP '^[A-Z]{4}0[A-Z0-9]{6}$' THEN
        SET valid = TRUE;
    END IF;
    
    RETURN valid;
END$$

-- -----------------------------------------------------
-- Function: validate_iban
-- -----------------------------------------------------
DROP FUNCTION IF EXISTS `validate_iban` $$
CREATE FUNCTION `validate_iban`(iban VARCHAR(34)) 
RETURNS BOOLEAN
DETERMINISTIC
COMMENT 'Validates International Bank Account Number (IBAN)'
BEGIN
    DECLARE valid BOOLEAN DEFAULT FALSE;
    DECLARE country_code VARCHAR(2);
    DECLARE length_valid BOOLEAN DEFAULT FALSE;
    
    -- Basic format validation - IBAN should be 5-34 characters
    IF LENGTH(iban) BETWEEN 5 AND 34 THEN
        -- Extract country code
        SET country_code = LEFT(iban, 2);
        
        -- Validate country code consists of letters
        IF country_code REGEXP '^[A-Z]{2}$' THEN
            -- For this implementation, we'll just check the basic format
            -- A complete implementation would check:
            -- 1. Country-specific length
            -- 2. MOD-97 validation
            
            -- Different countries have different IBAN lengths
            CASE country_code
                WHEN 'AL' THEN SET length_valid = (LENGTH(iban) = 28); -- Albania
                WHEN 'AD' THEN SET length_valid = (LENGTH(iban) = 24); -- Andorra
                WHEN 'AT' THEN SET length_valid = (LENGTH(iban) = 20); -- Austria
                WHEN 'BE' THEN SET length_valid = (LENGTH(iban) = 16); -- Belgium
                WHEN 'DE' THEN SET length_valid = (LENGTH(iban) = 22); -- Germany
                WHEN 'FR' THEN SET length_valid = (LENGTH(iban) = 27); -- France
                WHEN 'GB' THEN SET length_valid = (LENGTH(iban) = 22); -- United Kingdom
                WHEN 'IN' THEN SET length_valid = (LENGTH(iban) = 22); -- India
                WHEN 'IT' THEN SET length_valid = (LENGTH(iban) = 27); -- Italy
                -- Add more countries as needed
                ELSE SET length_valid = TRUE; -- For other countries, assume valid for now
            END CASE;
            
            -- Check basic format: country code + 2 digits + alphanumeric basic bank account number
            IF length_valid AND iban REGEXP '^[A-Z]{2}[0-9]{2}[A-Z0-9]+$' THEN
                SET valid = TRUE;
            END IF;
        END IF;
    END IF;
    
    RETURN valid;
END$$

-- -----------------------------------------------------
-- Function: validate_swift_bic
-- -----------------------------------------------------
DROP FUNCTION IF EXISTS `validate_swift_bic` $$
CREATE FUNCTION `validate_swift_bic`(swift_bic VARCHAR(11)) 
RETURNS BOOLEAN
DETERMINISTIC
COMMENT 'Validates SWIFT/BIC code'
BEGIN
    DECLARE valid BOOLEAN DEFAULT FALSE;
    
    -- BIC/SWIFT format:
    -- 4 letters: Institution code
    -- 2 letters: ISO 3166-1 country code
    -- 2 letters or digits: Location code
    -- 3 letters or digits: Branch code (optional)
    
    IF swift_bic REGEXP '^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?$' THEN
        IF LENGTH(swift_bic) = 8 OR LENGTH(swift_bic) = 11 THEN
            SET valid = TRUE;
        END IF;
    END IF;
    
    RETURN valid;
END$$

-- -----------------------------------------------------
-- Function: validate_upi_id
-- -----------------------------------------------------
DROP FUNCTION IF EXISTS `validate_upi_id` $$
CREATE FUNCTION `validate_upi_id`(upi_id VARCHAR(50)) 
RETURNS BOOLEAN
DETERMINISTIC
COMMENT 'Validates Unified Payment Interface (UPI) ID'
BEGIN
    DECLARE valid BOOLEAN DEFAULT FALSE;
    
    -- UPI ID format: username@psp (e.g., johndoe@okicici)
    -- username can include alphanumeric characters, dots, underscores, and hyphens
    -- psp (Payment Service Provider) should be a valid UPI handle
    
    IF upi_id REGEXP '^[A-Za-z0-9._-]+@[A-Za-z0-9]+$' THEN
        SET valid = TRUE;
    END IF;
    
    RETURN valid;
END$$

-- -----------------------------------------------------
-- Function: validate_micr_code
-- -----------------------------------------------------
DROP FUNCTION IF EXISTS `validate_micr_code` $$
CREATE FUNCTION `validate_micr_code`(micr_code VARCHAR(9)) 
RETURNS BOOLEAN
DETERMINISTIC
COMMENT 'Validates Magnetic Ink Character Recognition (MICR) code'
BEGIN
    DECLARE valid BOOLEAN DEFAULT FALSE;
    
    -- MICR code format: 9 digits divided into 3 parts of 3 digits each
    -- 1st part: City code
    -- 2nd part: Bank code
    -- 3rd part: Branch code
    
    IF micr_code REGEXP '^[0-9]{9}$' THEN
        SET valid = TRUE;
    END IF;
    
    RETURN valid;
END$$

-- -----------------------------------------------------
-- Function: validate_mmid
-- -----------------------------------------------------
DROP FUNCTION IF EXISTS `validate_mmid` $$
CREATE FUNCTION `validate_mmid`(mmid VARCHAR(7)) 
RETURNS BOOLEAN
DETERMINISTIC
COMMENT 'Validates Mobile Money Identifier (MMID)'
BEGIN
    DECLARE valid BOOLEAN DEFAULT FALSE;
    
    -- MMID format: 7 digits
    
    IF mmid REGEXP '^[0-9]{7}$' THEN
        SET valid = TRUE;
    END IF;
    
    RETURN valid;
END$$

-- -----------------------------------------------------
-- Function: validate_pan_card
-- -----------------------------------------------------
DROP FUNCTION IF EXISTS `validate_pan_card` $$
CREATE FUNCTION `validate_pan_card`(pan_no VARCHAR(10)) 
RETURNS BOOLEAN
DETERMINISTIC
COMMENT 'Validates Permanent Account Number (PAN) card'
BEGIN
    DECLARE valid BOOLEAN DEFAULT FALSE;
    
    -- PAN format: AAAAA1234A
    -- 1st 5 characters: Letters
    -- Next 4 characters: Digits
    -- Last character: Letter
    
    IF pan_no REGEXP '^[A-Z]{5}[0-9]{4}[A-Z]$' THEN
        SET valid = TRUE;
    END IF;
    
    RETURN valid;
END$$

-- -----------------------------------------------------
-- Function: validate_gstin
-- -----------------------------------------------------
DROP FUNCTION IF EXISTS `validate_gstin` $$
CREATE FUNCTION `validate_gstin`(gstin VARCHAR(15)) 
RETURNS BOOLEAN
DETERMINISTIC
COMMENT 'Validates Goods and Services Tax Identification Number (GSTIN)'
BEGIN
    DECLARE valid BOOLEAN DEFAULT FALSE;
    DECLARE pan_part VARCHAR(10);
    DECLARE state_code VARCHAR(2);
    
    -- GSTIN format: 15 characters
    -- First 2 characters: State code
    -- Next 10 characters: PAN number
    -- 13th character: Entity number
    -- 14th character: Z (default)
    -- 15th character: Checksum
    
    IF gstin REGEXP '^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z][Z][0-9A-Z]$' THEN
        -- Extract state code
        SET state_code = LEFT(gstin, 2);
        
        -- Extract PAN part
        SET pan_part = SUBSTRING(gstin, 3, 10);
        
        -- Check if state code is valid (01-37)
        IF CAST(state_code AS UNSIGNED) BETWEEN 1 AND 37 THEN
            -- Check if PAN part is valid
            IF validate_pan_card(pan_part) THEN
                SET valid = TRUE;
            END IF;
        END IF;
    END IF;
    
    RETURN valid;
END$$

-- -----------------------------------------------------
-- Example usage queries
-- -----------------------------------------------------

/*
-- Test IFSC Code validation
SELECT validate_ifsc_code('HDFC0001234') AS is_valid_ifsc;

-- Test IBAN validation
SELECT validate_iban('GB29NWBK60161331926819') AS is_valid_iban;

-- Test SWIFT/BIC validation
SELECT validate_swift_bic('DEUTDEFF') AS is_valid_swift_bic_8;
SELECT validate_swift_bic('DEUTDEFFXXX') AS is_valid_swift_bic_11;

-- Test UPI ID validation
SELECT validate_upi_id('john.doe@okaxis') AS is_valid_upi_id;

-- Test MICR Code validation
SELECT validate_micr_code('400002345') AS is_valid_micr_code;

-- Test MMID validation
SELECT validate_mmid('1234567') AS is_valid_mmid;

-- Test PAN Card validation
SELECT validate_pan_card('ABCDE1234F') AS is_valid_pan;

-- Test GSTIN validation
SELECT validate_gstin('27AAAAA0000A1Z5') AS is_valid_gstin;
*/

DELIMITER ;
