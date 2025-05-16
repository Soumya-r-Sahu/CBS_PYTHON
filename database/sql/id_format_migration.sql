/*
 * File: id_format_migration.sql
 * Description: SQL migration script for converting existing IDs to new standard formats
 * Date: May 13, 2025
 * 
 * This file contains migration procedures to convert existing IDs in the database
 * to the new standardized formats.
 */

DELIMITER $$

-- -----------------------------------------------------
-- Migration procedure for customer IDs
-- -----------------------------------------------------
DROP PROCEDURE IF EXISTS `migrate_customer_ids` $$
CREATE PROCEDURE `migrate_customer_ids`()
COMMENT 'Migrate existing customer IDs to format YYDDD-BBBBB-SSSS'
BEGIN
    DECLARE total_records INT;
    DECLARE processed INT DEFAULT 0;
    DECLARE old_customer_id VARCHAR(20);
    DECLARE new_customer_id VARCHAR(20);
    DECLARE customer_branch_code VARCHAR(5);
    DECLARE done INT DEFAULT FALSE;
    
    -- Create temporary table for migration mapping
    DROP TABLE IF EXISTS temp_customer_id_mapping;
    CREATE TEMPORARY TABLE temp_customer_id_mapping (
        old_customer_id VARCHAR(20) NOT NULL,
        new_customer_id VARCHAR(20) NOT NULL,
        PRIMARY KEY (old_customer_id)
    );
    
    -- Cursor to iterate through customer records
    DECLARE cur CURSOR FOR 
        SELECT customer_id, branch_code 
        FROM cbs_customers;
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    -- Count total records for progress reporting
    SELECT COUNT(*) INTO total_records FROM cbs_customers;
    
    -- Start migration
    SELECT 'Starting customer ID migration' AS status;
    
    OPEN cur;
    
    migration_loop: LOOP
        FETCH cur INTO old_customer_id, customer_branch_code;
        IF done THEN
            LEAVE migration_loop;
        END IF;
        
        -- Generate new format customer ID
        SET new_customer_id = generate_customer_id(customer_branch_code);
        
        -- Store mapping
        INSERT INTO temp_customer_id_mapping (old_customer_id, new_customer_id)
        VALUES (old_customer_id, new_customer_id);
        
        SET processed = processed + 1;
        
        IF processed % 1000 = 0 THEN
            SELECT CONCAT('Processed ', processed, ' of ', total_records, ' customer records') AS progress;
        END IF;
    END LOOP;
    
    CLOSE cur;
    
    -- Update references in foreign key tables first (example - can be expanded)
    UPDATE cbs_accounts a
    JOIN temp_customer_id_mapping m ON a.customer_id = m.old_customer_id
    SET a.customer_id = m.new_customer_id;
    
    -- Update customer table
    UPDATE cbs_customers c
    JOIN temp_customer_id_mapping m ON c.customer_id = m.old_customer_id
    SET c.customer_id = m.new_customer_id;
    
    SELECT CONCAT('Migration complete. ', processed, ' customer IDs migrated.') AS result;
    
    -- Clean up
    DROP TABLE IF EXISTS temp_customer_id_mapping;
END$$

-- -----------------------------------------------------
-- Migration procedure for account numbers
-- -----------------------------------------------------
DROP PROCEDURE IF EXISTS `migrate_account_numbers` $$
CREATE PROCEDURE `migrate_account_numbers`()
COMMENT 'Migrate existing account numbers to format BBBBB-AATT-CCCCCC-CC'
BEGIN
    DECLARE total_records INT;
    DECLARE processed INT DEFAULT 0;
    DECLARE old_account_number VARCHAR(20);
    DECLARE new_account_number VARCHAR(20);
    DECLARE account_branch_code VARCHAR(5);
    DECLARE account_type VARCHAR(2);
    DECLARE account_subtype VARCHAR(2);
    DECLARE customer_seq VARCHAR(6);
    DECLARE done INT DEFAULT FALSE;
    
    -- Create temporary table for migration mapping
    DROP TABLE IF EXISTS temp_account_number_mapping;
    CREATE TEMPORARY TABLE temp_account_number_mapping (
        old_account_number VARCHAR(20) NOT NULL,
        new_account_number VARCHAR(20) NOT NULL,
        PRIMARY KEY (old_account_number)
    );
    
    -- Cursor to iterate through account records
    DECLARE cur CURSOR FOR 
        SELECT account_number, branch_code, account_type, account_subtype 
        FROM cbs_accounts;
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    -- Count total records for progress reporting
    SELECT COUNT(*) INTO total_records FROM cbs_accounts;
    
    -- Start migration
    SELECT 'Starting account number migration' AS status;
    
    OPEN cur;
    
    migration_loop: LOOP
        FETCH cur INTO old_account_number, account_branch_code, account_type, account_subtype;
        IF done THEN
            LEAVE migration_loop;
        END IF;
        
        -- Generate customer sequence from old account number or other logic
        SET customer_seq = LPAD(SUBSTRING(old_account_number, -6), 6, '0');
        
        -- Generate new format account number
        SET new_account_number = generate_account_number(
            account_branch_code, 
            account_type, 
            account_subtype, 
            customer_seq
        );
        
        -- Store mapping
        INSERT INTO temp_account_number_mapping (old_account_number, new_account_number)
        VALUES (old_account_number, new_account_number);
        
        SET processed = processed + 1;
        
        IF processed % 1000 = 0 THEN
            SELECT CONCAT('Processed ', processed, ' of ', total_records, ' account records') AS progress;
        END IF;
    END LOOP;
    
    CLOSE cur;
    
    -- Update references in foreign key tables first (example - can be expanded)
    UPDATE cbs_transactions t
    JOIN temp_account_number_mapping m ON t.account_number = m.old_account_number
    SET t.account_number = m.new_account_number;
    
    -- Update account table
    UPDATE cbs_accounts a
    JOIN temp_account_number_mapping m ON a.account_number = m.old_account_number
    SET a.account_number = m.new_account_number;
    
    SELECT CONCAT('Migration complete. ', processed, ' account numbers migrated.') AS result;
    
    -- Clean up
    DROP TABLE IF EXISTS temp_account_number_mapping;
END$$

-- -----------------------------------------------------
-- Migration procedure for transaction IDs
-- -----------------------------------------------------
DROP PROCEDURE IF EXISTS `migrate_transaction_ids` $$
CREATE PROCEDURE `migrate_transaction_ids`()
COMMENT 'Migrate existing transaction IDs to format TRX-YYYYMMDD-SSSSSS'
BEGIN
    DECLARE total_records INT;
    DECLARE processed INT DEFAULT 0;
    DECLARE old_transaction_id VARCHAR(20);
    DECLARE new_transaction_id VARCHAR(20);
    DECLARE transaction_date DATE;
    DECLARE done INT DEFAULT FALSE;
    
    -- Create temporary table for migration mapping
    DROP TABLE IF EXISTS temp_transaction_id_mapping;
    CREATE TEMPORARY TABLE temp_transaction_id_mapping (
        old_transaction_id VARCHAR(20) NOT NULL,
        new_transaction_id VARCHAR(20) NOT NULL,
        PRIMARY KEY (old_transaction_id)
    );
    
    -- Cursor to iterate through transaction records
    DECLARE cur CURSOR FOR 
        SELECT transaction_id, transaction_date 
        FROM cbs_transactions;
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    -- Count total records for progress reporting
    SELECT COUNT(*) INTO total_records FROM cbs_transactions;
    
    -- Start migration
    SELECT 'Starting transaction ID migration' AS status;
    
    OPEN cur;
    
    migration_loop: LOOP
        FETCH cur INTO old_transaction_id, transaction_date;
        IF done THEN
            LEAVE migration_loop;
        END IF;
        
        -- Generate new format transaction ID
        SET new_transaction_id = CONCAT(
            'TRX-',
            DATE_FORMAT(transaction_date, '%Y%m%d'),
            '-',
            LPAD(SUBSTRING(old_transaction_id, -6), 6, '0')
        );
        
        -- Store mapping
        INSERT INTO temp_transaction_id_mapping (old_transaction_id, new_transaction_id)
        VALUES (old_transaction_id, new_transaction_id);
        
        SET processed = processed + 1;
        
        IF processed % 1000 = 0 THEN
            SELECT CONCAT('Processed ', processed, ' of ', total_records, ' transaction records') AS progress;
        END IF;
    END LOOP;
    
    CLOSE cur;
    
    -- Update transaction table (and any foreign key references if needed)
    UPDATE cbs_transactions t
    JOIN temp_transaction_id_mapping m ON t.transaction_id = m.old_transaction_id
    SET t.transaction_id = m.new_transaction_id;
    
    SELECT CONCAT('Migration complete. ', processed, ' transaction IDs migrated.') AS result;
    
    -- Clean up
    DROP TABLE IF EXISTS temp_transaction_id_mapping;
END$$

-- -----------------------------------------------------
-- Migration procedure for employee IDs
-- -----------------------------------------------------
DROP PROCEDURE IF EXISTS `migrate_employee_ids` $$
CREATE PROCEDURE `migrate_employee_ids`()
COMMENT 'Migrate existing employee IDs to format ZZBB-DD-EEEE'
BEGIN
    DECLARE total_records INT;
    DECLARE processed INT DEFAULT 0;
    DECLARE old_employee_id VARCHAR(15);
    DECLARE new_employee_id VARCHAR(12);
    DECLARE zone_code VARCHAR(2);
    DECLARE branch_code VARCHAR(2);
    DECLARE designation_code VARCHAR(2);
    DECLARE done INT DEFAULT FALSE;
    
    -- Create temporary table for migration mapping
    DROP TABLE IF EXISTS temp_employee_id_mapping;
    CREATE TEMPORARY TABLE temp_employee_id_mapping (
        old_employee_id VARCHAR(15) NOT NULL,
        new_employee_id VARCHAR(12) NOT NULL,
        PRIMARY KEY (old_employee_id)
    );
    
    -- Cursor to iterate through employee records
    DECLARE cur CURSOR FOR 
        SELECT employee_id, zone_code, branch_code, designation_code 
        FROM cbs_admin_users;
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    -- Count total records for progress reporting
    SELECT COUNT(*) INTO total_records FROM cbs_admin_users;
    
    -- Start migration
    SELECT 'Starting employee ID migration' AS status;
    
    OPEN cur;
    
    migration_loop: LOOP
        FETCH cur INTO old_employee_id, zone_code, branch_code, designation_code;
        IF done THEN
            LEAVE migration_loop;
        END IF;
        
        -- Generate new format employee ID
        SET new_employee_id = generate_employee_id(zone_code, branch_code, designation_code);
        
        -- Store mapping
        INSERT INTO temp_employee_id_mapping (old_employee_id, new_employee_id)
        VALUES (old_employee_id, new_employee_id);
        
        SET processed = processed + 1;
        
        IF processed % 1000 = 0 THEN
            SELECT CONCAT('Processed ', processed, ' of ', total_records, ' employee records') AS progress;
        END IF;
    END LOOP;
    
    CLOSE cur;
    
    -- Update references in foreign key tables first (example - can be expanded)
    UPDATE cbs_employee_leaves l
    JOIN temp_employee_id_mapping m ON l.employee_id = m.old_employee_id
    SET l.employee_id = m.new_employee_id;
    
    -- Update employee table
    UPDATE cbs_admin_users e
    JOIN temp_employee_id_mapping m ON e.employee_id = m.old_employee_id
    SET e.employee_id = m.new_employee_id;
    
    SELECT CONCAT('Migration complete. ', processed, ' employee IDs migrated.') AS result;
    
    -- Clean up
    DROP TABLE IF EXISTS temp_employee_id_mapping;
END$$

-- -----------------------------------------------------
-- Master migration procedure to run all migrations
-- -----------------------------------------------------
DROP PROCEDURE IF EXISTS `migrate_all_ids` $$
CREATE PROCEDURE `migrate_all_ids`()
COMMENT 'Run all ID migration procedures in the correct order'
BEGIN
    -- First backup the database (this should be done externally for safety)
    SELECT 'WARNING: Ensure you have backed up the database before proceeding!' AS warning;
    
    -- Create migration log table
    CREATE TABLE IF NOT EXISTS migration_log (
        log_id INT AUTO_INCREMENT PRIMARY KEY,
        migration_type VARCHAR(50) NOT NULL,
        start_time DATETIME NOT NULL,
        end_time DATETIME NULL,
        status VARCHAR(20) NOT NULL,
        records_processed INT NULL,
        notes TEXT
    );
    
    -- Log start of employee migration
    INSERT INTO migration_log (migration_type, start_time, status)
    VALUES ('employee_ids', NOW(), 'IN_PROGRESS');
    
    -- Migrate employee IDs first
    CALL migrate_employee_ids();
    
    -- Update log
    UPDATE migration_log
    SET end_time = NOW(),
        status = 'COMPLETED'
    WHERE migration_type = 'employee_ids'
      AND end_time IS NULL;
    
    -- Log start of customer migration
    INSERT INTO migration_log (migration_type, start_time, status)
    VALUES ('customer_ids', NOW(), 'IN_PROGRESS');
    
    -- Migrate customer IDs
    CALL migrate_customer_ids();
    
    -- Update log
    UPDATE migration_log
    SET end_time = NOW(),
        status = 'COMPLETED'
    WHERE migration_type = 'customer_ids'
      AND end_time IS NULL;
    
    -- Log start of account migration
    INSERT INTO migration_log (migration_type, start_time, status)
    VALUES ('account_numbers', NOW(), 'IN_PROGRESS');
    
    -- Migrate account numbers
    CALL migrate_account_numbers();
    
    -- Update log
    UPDATE migration_log
    SET end_time = NOW(),
        status = 'COMPLETED'
    WHERE migration_type = 'account_numbers'
      AND end_time IS NULL;
    
    -- Log start of transaction migration
    INSERT INTO migration_log (migration_type, start_time, status)
    VALUES ('transaction_ids', NOW(), 'IN_PROGRESS');
    
    -- Migrate transaction IDs
    CALL migrate_transaction_ids();
    
    -- Update log
    UPDATE migration_log
    SET end_time = NOW(),
        status = 'COMPLETED'
    WHERE migration_type = 'transaction_ids'
      AND end_time IS NULL;
    
    SELECT 'All ID migrations completed successfully' AS result;
END$$

DELIMITER ;

-- Execute all migrations (uncomment when ready to run)
-- CALL migrate_all_ids();
