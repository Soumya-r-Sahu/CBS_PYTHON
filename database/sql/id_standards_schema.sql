/*
 * File: id_standards_schema.sql
 * Description: Database schema adjustments for Indian and international banking standards compliance
 * Date: May 13, 2025
 * 
 * This file contains schema adjustments and constraints to enforce banking ID standards
 */

-- -----------------------------------------------------
-- Table structure modifications to support ID standards
-- -----------------------------------------------------

-- Create sequence tables to generate sequential IDs
CREATE TABLE IF NOT EXISTS `id_sequences` (
    `sequence_name` VARCHAR(50) NOT NULL PRIMARY KEY,
    `current_value` INT UNSIGNED NOT NULL DEFAULT 1000,
    `increment` INT UNSIGNED NOT NULL DEFAULT 1,
    `min_value` INT UNSIGNED NOT NULL DEFAULT 1000,
    `max_value` INT UNSIGNED NOT NULL DEFAULT 9999999999,
    `cycle` BOOLEAN NOT NULL DEFAULT FALSE,
    `description` VARCHAR(255),
    `last_updated` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Sequences for ID generation';

-- Insert initial sequences
INSERT INTO `id_sequences` 
    (`sequence_name`, `current_value`, `description`) 
VALUES 
    ('customer_seq', 1000, 'Sequence for customer IDs'),
    ('account_seq', 100000, 'Sequence for account numbers'),
    ('transaction_seq', 100000, 'Sequence for transaction IDs'),
    ('employee_seq', 1000, 'Sequence for employee IDs')
ON DUPLICATE KEY UPDATE `description` = VALUES(`description`);

-- Create function to get next sequence value
DELIMITER $$

DROP FUNCTION IF EXISTS `next_sequence_value` $$
CREATE FUNCTION `next_sequence_value`(sequence_name VARCHAR(50)) 
RETURNS INT UNSIGNED
NOT DETERMINISTIC
MODIFIES SQL DATA
BEGIN
    DECLARE next_val INT UNSIGNED;
    
    -- Lock the sequence row for update
    SELECT current_value INTO next_val 
    FROM id_sequences 
    WHERE sequence_name = sequence_name 
    FOR UPDATE;
    
    -- Update the sequence value
    UPDATE id_sequences
    SET current_value = 
        CASE 
            WHEN (current_value + increment) > max_value AND cycle = TRUE 
                THEN min_value
            WHEN (current_value + increment) > max_value AND cycle = FALSE 
                THEN max_value
            ELSE current_value + increment
        END
    WHERE sequence_name = sequence_name;
    
    RETURN next_val;
END$$

DELIMITER ;

-- -----------------------------------------------------
-- Modify tables to use new ID formats 
-- -----------------------------------------------------

-- Note: In a production system, these would be applied through careful migration
-- Here we are showing the target schema structure

-- Add check constraints for ID formats
DELIMITER $$

DROP PROCEDURE IF EXISTS `add_id_constraints` $$
CREATE PROCEDURE `add_id_constraints`()
BEGIN
    -- Check for constraint existence and add if not exists
    -- Note: MySQL doesn't provide simple "IF NOT EXISTS" for constraints
    
    -- Customer ID constraint - format YYDDD-BBBBB-SSSS
    SET @constraint_exists = (
        SELECT COUNT(*) FROM information_schema.table_constraints 
        WHERE constraint_name = 'chk_customer_id_format'
        AND table_name = 'cbs_customers'
        AND table_schema = DATABASE()
    );
    
    IF @constraint_exists = 0 THEN
        SET @sql = 'ALTER TABLE cbs_customers ADD CONSTRAINT chk_customer_id_format 
                    CHECK (validate_customer_id(customer_id))';
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
    
    -- Account number constraint - format BBBBB-AATT-CCCCCC-CC
    SET @constraint_exists = (
        SELECT COUNT(*) FROM information_schema.table_constraints 
        WHERE constraint_name = 'chk_account_number_format'
        AND table_name = 'cbs_accounts'
        AND table_schema = DATABASE()
    );
    
    IF @constraint_exists = 0 THEN
        SET @sql = 'ALTER TABLE cbs_accounts ADD CONSTRAINT chk_account_number_format 
                    CHECK (validate_account_number(account_number))';
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
    
    -- Transaction ID constraint - format TRX-YYYYMMDD-SSSSSS
    SET @constraint_exists = (
        SELECT COUNT(*) FROM information_schema.table_constraints 
        WHERE constraint_name = 'chk_transaction_id_format'
        AND table_name = 'cbs_transactions'
        AND table_schema = DATABASE()
    );
    
    IF @constraint_exists = 0 THEN
        SET @sql = 'ALTER TABLE cbs_transactions ADD CONSTRAINT chk_transaction_id_format 
                    CHECK (validate_transaction_id(transaction_id))';
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
    
    -- Employee ID constraint - format ZZBB-DD-EEEE
    SET @constraint_exists = (
        SELECT COUNT(*) FROM information_schema.table_constraints 
        WHERE constraint_name = 'chk_employee_id_format'
        AND table_name = 'cbs_admin_users'
        AND table_schema = DATABASE()
    );
    
    IF @constraint_exists = 0 THEN
        SET @sql = 'ALTER TABLE cbs_admin_users ADD CONSTRAINT chk_employee_id_format 
                    CHECK (validate_employee_id(employee_id))';
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
    
END$$

DELIMITER ;

-- Execute the procedure to add constraints
CALL add_id_constraints();

-- Update table comments to reflect new ID formats
ALTER TABLE cbs_customers MODIFY COLUMN customer_id VARCHAR(20) NOT NULL PRIMARY KEY 
    COMMENT 'Format: YYDDD-BBBBB-SSSS (YY=year, DDD=day of year, BBBBB=branch, SSSS=sequence)';

ALTER TABLE cbs_accounts MODIFY COLUMN account_number VARCHAR(20) NOT NULL PRIMARY KEY 
    COMMENT 'Format: BBBBB-AATT-CCCCCC-CC (BBBBB=branch, AA=account type, TT=subtype, CCCCCC=customer, CC=checksum)';

ALTER TABLE cbs_transactions MODIFY COLUMN transaction_id VARCHAR(20) NOT NULL PRIMARY KEY 
    COMMENT 'Format: TRX-YYYYMMDD-SSSSSS (YYYYMMDD=date, SSSSSS=sequence)';

ALTER TABLE cbs_admin_users MODIFY COLUMN employee_id VARCHAR(12) NOT NULL 
    COMMENT 'Format: ZZBB-DD-EEEE (ZZ=zone code, BB=branch code, DD=designation, EEEE=sequence)';

-- -----------------------------------------------------
-- Create stored procedures for generating IDs
-- -----------------------------------------------------

DELIMITER $$

DROP PROCEDURE IF EXISTS `generate_next_customer_id` $$
CREATE PROCEDURE `generate_next_customer_id`(
    IN p_branch_code VARCHAR(5),
    OUT p_customer_id VARCHAR(20)
)
BEGIN
    DECLARE branch_code VARCHAR(5);
    DECLARE year_part VARCHAR(2);
    DECLARE day_part VARCHAR(3);
    DECLARE seq_next INT;
    
    -- Format branch code
    SET branch_code = LPAD(p_branch_code, 5, '0');
    
    -- Get current date components
    SET year_part = DATE_FORMAT(CURDATE(), '%y');  -- Last 2 digits of year
    SET day_part = LPAD(DAYOFYEAR(CURDATE()), 3, '0');  -- Day of year (001-366)
    
    -- Get next sequence value
    SET seq_next = next_sequence_value('customer_seq');
    
    -- Assemble the ID
    SET p_customer_id = CONCAT(year_part, day_part, '-', branch_code, '-', LPAD(seq_next, 4, '0'));
END$$

DROP PROCEDURE IF EXISTS `generate_next_account_number` $$
CREATE PROCEDURE `generate_next_account_number`(
    IN p_branch_code VARCHAR(5),
    IN p_account_type VARCHAR(2),
    IN p_sub_type VARCHAR(2),
    OUT p_account_number VARCHAR(20)
)
BEGIN
    DECLARE branch_code VARCHAR(5);
    DECLARE account_type VARCHAR(2);
    DECLARE sub_type VARCHAR(2);
    DECLARE customer_seq VARCHAR(6);
    DECLARE seq_next INT;
    
    -- Format inputs
    SET branch_code = LPAD(p_branch_code, 5, '0');
    SET account_type = LPAD(p_account_type, 2, '0');
    SET sub_type = LPAD(p_sub_type, 2, '0');
    
    -- Get next sequence value
    SET seq_next = next_sequence_value('account_seq');
    SET customer_seq = LPAD(seq_next, 6, '0');
    
    -- Generate the account number using our function
    SET p_account_number = generate_account_number(branch_code, account_type, sub_type, customer_seq);
END$$

DROP PROCEDURE IF EXISTS `generate_next_transaction_id` $$
CREATE PROCEDURE `generate_next_transaction_id`(
    OUT p_transaction_id VARCHAR(20)
)
BEGIN
    DECLARE date_part VARCHAR(8);
    DECLARE seq_next INT;
    
    -- Get current date in YYYYMMDD format
    SET date_part = DATE_FORMAT(NOW(), '%Y%m%d');
    
    -- Get next sequence value
    SET seq_next = next_sequence_value('transaction_seq');
    
    -- Assemble the transaction ID
    SET p_transaction_id = CONCAT('TRX-', date_part, '-', LPAD(seq_next, 6, '0'));
END$$

DROP PROCEDURE IF EXISTS `generate_next_employee_id` $$
CREATE PROCEDURE `generate_next_employee_id`(
    IN p_zone_code VARCHAR(2),
    IN p_branch_code VARCHAR(2),
    IN p_designation_code VARCHAR(2),
    OUT p_employee_id VARCHAR(12)
)
BEGIN
    DECLARE zone_code VARCHAR(2);
    DECLARE branch_code VARCHAR(2);
    DECLARE designation_code VARCHAR(2);
    DECLARE seq_next INT;
    
    -- Format inputs
    SET zone_code = LPAD(p_zone_code, 2, '0');
    SET branch_code = LPAD(p_branch_code, 2, '0');
    SET designation_code = LPAD(p_designation_code, 2, '0');
    
    -- Get next sequence value
    SET seq_next = next_sequence_value('employee_seq');
    
    -- Assemble the employee ID
    SET p_employee_id = CONCAT(zone_code, branch_code, '-', designation_code, '-', LPAD(seq_next, 4, '0'));
END$$

DELIMITER ;
