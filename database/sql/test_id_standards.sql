/*
 * File: test_id_standards.sql
 * Description: Test SQL functions and procedures for banking ID standards
 * Date: May 13, 2025
 * 
 * This file contains test cases for validating the SQL implementation
 * of banking ID standards.
 */

-- -----------------------------------------------------
-- Test Customer ID validation
-- -----------------------------------------------------
SELECT 'Testing Customer ID validation' AS Test;

SELECT '23145-12345-1234' AS customer_id, 
       IF(validate_customer_id('23145-12345-1234'), 'VALID', 'INVALID') AS validation_result,
       'Valid format YYDDD-BBBBB-SSSS' AS test_description;

SELECT '23450-12345-1234' AS customer_id, 
       IF(validate_customer_id('23450-12345-1234'), 'VALID', 'INVALID') AS validation_result,
       'Invalid day (450 > 366)' AS test_description;

SELECT '2314512345-1234' AS customer_id, 
       IF(validate_customer_id('2314512345-1234'), 'VALID', 'INVALID') AS validation_result,
       'Invalid format (missing hyphen)' AS test_description;

SELECT '23145-123456-1234' AS customer_id, 
       IF(validate_customer_id('23145-123456-1234'), 'VALID', 'INVALID') AS validation_result,
       'Invalid format (branch code too long)' AS test_description;

-- -----------------------------------------------------
-- Test Account Number validation
-- -----------------------------------------------------
SELECT 'Testing Account Number validation' AS Test;

SELECT '12345-0101-123456-01' AS account_number, 
       IF(validate_account_number('12345-0101-123456-01'), 'VALID', 'INVALID') AS validation_result,
       'Valid format BBBBB-AATT-CCCCCC-CC' AS test_description;

SELECT '1234-0101-123456-01' AS account_number, 
       IF(validate_account_number('1234-0101-123456-01'), 'VALID', 'INVALID') AS validation_result,
       'Invalid format (branch code too short)' AS test_description;

SELECT '12345-01-01-123456-01' AS account_number, 
       IF(validate_account_number('12345-01-01-123456-01'), 'VALID', 'INVALID') AS validation_result,
       'Invalid format (extra hyphen)' AS test_description;

-- -----------------------------------------------------
-- Test Transaction ID validation
-- -----------------------------------------------------
SELECT 'Testing Transaction ID validation' AS Test;

SELECT 'TRX-20250513-123456' AS transaction_id, 
       IF(validate_transaction_id('TRX-20250513-123456'), 'VALID', 'INVALID') AS validation_result,
       'Valid format TRX-YYYYMMDD-SSSSSS' AS test_description;

SELECT 'TRX-20251332-123456' AS transaction_id, 
       IF(validate_transaction_id('TRX-20251332-123456'), 'VALID', 'INVALID') AS validation_result,
       'Invalid date (month > 12)' AS test_description;

SELECT 'TRX-20250229-123456' AS transaction_id, 
       IF(validate_transaction_id('TRX-20250229-123456'), 'VALID', 'INVALID') AS validation_result,
       'Invalid date (Feb 29 in non-leap year)' AS test_description;

SELECT 'TX-20250513-123456' AS transaction_id, 
       IF(validate_transaction_id('TX-20250513-123456'), 'VALID', 'INVALID') AS validation_result,
       'Invalid format (wrong prefix)' AS test_description;

-- -----------------------------------------------------
-- Test Employee ID validation
-- -----------------------------------------------------
SELECT 'Testing Employee ID validation' AS Test;

SELECT '0101-04-1234' AS employee_id, 
       IF(validate_employee_id('0101-04-1234'), 'VALID', 'INVALID') AS validation_result,
       'Valid format ZZBB-DD-EEEE' AS test_description;

SELECT '01-01-04-1234' AS employee_id, 
       IF(validate_employee_id('01-01-04-1234'), 'VALID', 'INVALID') AS validation_result,
       'Invalid format (extra hyphen)' AS test_description;

SELECT '0101044-1234' AS employee_id, 
       IF(validate_employee_id('0101044-1234'), 'VALID', 'INVALID') AS validation_result,
       'Invalid format (missing hyphen)' AS test_description;

-- -----------------------------------------------------
-- Test ID Generation Procedures
-- -----------------------------------------------------
SELECT 'Testing ID Generation Procedures' AS Test;

-- Test customer ID generation
CALL generate_next_customer_id('12345', @new_customer_id);
SELECT @new_customer_id AS generated_customer_id,
       IF(validate_customer_id(@new_customer_id), 'VALID', 'INVALID') AS validation_result;

-- Test account number generation
CALL generate_next_account_number('12345', '01', '01', @new_account_number);
SELECT @new_account_number AS generated_account_number,
       IF(validate_account_number(@new_account_number), 'VALID', 'INVALID') AS validation_result;

-- Test transaction ID generation
CALL generate_next_transaction_id(@new_transaction_id);
SELECT @new_transaction_id AS generated_transaction_id,
       IF(validate_transaction_id(@new_transaction_id), 'VALID', 'INVALID') AS validation_result;

-- Test employee ID generation
CALL generate_next_employee_id('01', '01', '04', @new_employee_id);
SELECT @new_employee_id AS generated_employee_id,
       IF(validate_employee_id(@new_employee_id), 'VALID', 'INVALID') AS validation_result;

-- -----------------------------------------------------
-- Test Direct Function Calls for ID Generation
-- -----------------------------------------------------
SELECT 'Testing Direct Function Calls for ID Generation' AS Test;

SELECT generate_customer_id('12345') AS generated_customer_id,
       validate_customer_id(generate_customer_id('12345')) AS is_valid;

SELECT generate_account_number('12345', '01', '01', '123456') AS generated_account_number,
       validate_account_number(generate_account_number('12345', '01', '01', '123456')) AS is_valid;

SELECT generate_transaction_id() AS generated_transaction_id,
       validate_transaction_id(generate_transaction_id()) AS is_valid;

SELECT generate_employee_id('01', '01', '04') AS generated_employee_id,
       validate_employee_id(generate_employee_id('01', '01', '04')) AS is_valid;
