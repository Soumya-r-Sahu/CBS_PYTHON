/*
 * File: international_id_standards.sql
 * Description: SQL functions for international banking ID standards
 * Created: May 19, 2025
 * 
 * This file contains functions for validating and generating international
 * banking identifiers like IBAN, SWIFT/BIC, etc.
 */

DELIMITER $$

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
    DECLARE length_valid BOOLEAN;
    
    -- Basic validation and length check
    IF iban IS NOT NULL AND LENGTH(iban) >= 5 THEN
        SET country_code = LEFT(iban, 2);
        
        -- Check expected length by country (some examples)
        CASE country_code
            WHEN 'AL' THEN SET length_valid = LENGTH(iban) = 28;
            WHEN 'AT' THEN SET length_valid = LENGTH(iban) = 20;
            WHEN 'BE' THEN SET length_valid = LENGTH(iban) = 16;
            WHEN 'DE' THEN SET length_valid = LENGTH(iban) = 22;
            WHEN 'ES' THEN SET length_valid = LENGTH(iban) = 24;
            WHEN 'FR' THEN SET length_valid = LENGTH(iban) = 27;
            WHEN 'GB' THEN SET length_valid = LENGTH(iban) = 22;
            WHEN 'GR' THEN SET length_valid = LENGTH(iban) = 27;
            WHEN 'IT' THEN SET length_valid = LENGTH(iban) = 27;
            WHEN 'NL' THEN SET length_valid = LENGTH(iban) = 18;
            WHEN 'PT' THEN SET length_valid = LENGTH(iban) = 25;
            WHEN 'CH' THEN SET length_valid = LENGTH(iban) = 21;
            ELSE SET length_valid = TRUE; -- For other countries
        END CASE;
        
        -- Check format: 2 letters + 2 digits + basic format check
        IF length_valid AND iban REGEXP '^[A-Z]{2}[0-9]{2}[A-Z0-9]+$' THEN
            -- For a complete validation, we would implement the MOD-97 check
            -- This is a simplified version
            SET valid = TRUE;
        END IF;
    END IF;
    
    RETURN valid;
END$$

-- -----------------------------------------------------
-- Function: validate_swift_bic
-- -----------------------------------------------------
DROP FUNCTION IF EXISTS `validate_swift_bic` $$
CREATE FUNCTION `validate_swift_bic`(bic VARCHAR(11)) 
RETURNS BOOLEAN
DETERMINISTIC
COMMENT 'Validates SWIFT/BIC code'
BEGIN
    DECLARE valid BOOLEAN DEFAULT FALSE;
    
    -- Check BIC format: 4 bank code + 2 country code + 2 location code + [3 branch code]
    IF bic REGEXP '^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?$' THEN
        SET valid = TRUE;
    END IF;
    
    RETURN valid;
END$$

-- -----------------------------------------------------
-- Function: validate_routing_number
-- -----------------------------------------------------
DROP FUNCTION IF EXISTS `validate_routing_number` $$
CREATE FUNCTION `validate_routing_number`(routing_number VARCHAR(9)) 
RETURNS BOOLEAN
DETERMINISTIC
COMMENT 'Validates US ABA Routing Transit Number'
BEGIN
    DECLARE valid BOOLEAN DEFAULT FALSE;
    DECLARE checksum INT;
    
    -- Check basic format: 9 digits
    IF routing_number REGEXP '^[0-9]{9}$' THEN
        -- Calculate checksum (3-3-1-3 algorithm)
        SET checksum = 
            (CAST(SUBSTRING(routing_number, 1, 1) AS UNSIGNED) * 3) +
            (CAST(SUBSTRING(routing_number, 2, 1) AS UNSIGNED) * 7) +
            (CAST(SUBSTRING(routing_number, 3, 1) AS UNSIGNED) * 1) +
            (CAST(SUBSTRING(routing_number, 4, 1) AS UNSIGNED) * 3) +
            (CAST(SUBSTRING(routing_number, 5, 1) AS UNSIGNED) * 7) +
            (CAST(SUBSTRING(routing_number, 6, 1) AS UNSIGNED) * 1) +
            (CAST(SUBSTRING(routing_number, 7, 1) AS UNSIGNED) * 3) +
            (CAST(SUBSTRING(routing_number, 8, 1) AS UNSIGNED) * 7) +
            (CAST(SUBSTRING(routing_number, 9, 1) AS UNSIGNED) * 1);
        
        -- Check if divisible by 10
        IF checksum % 10 = 0 THEN
            SET valid = TRUE;
        END IF;
    END IF;
    
    RETURN valid;
END$$

-- -----------------------------------------------------
-- Function: generate_iban
-- -----------------------------------------------------
DROP FUNCTION IF EXISTS `generate_iban` $$
CREATE FUNCTION `generate_iban`(
    country_code CHAR(2),
    bank_code VARCHAR(10),
    account_number VARCHAR(20)
) 
RETURNS VARCHAR(34)
DETERMINISTIC
COMMENT 'Generates an IBAN from components (simplified)'
BEGIN
    DECLARE iban VARCHAR(34);
    
    -- Format varies by country - this is a simplified example
    SET iban = CONCAT(
        UPPER(country_code),
        '00', -- Placeholder for check digits
        bank_code,
        account_number
    );
    
    -- In a real implementation, calculate MOD-97 check digits here
    
    RETURN iban;
END$$

DELIMITER ;
