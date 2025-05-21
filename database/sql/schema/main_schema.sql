-- Active: 1747581008183@@127.0.0.1@3307@cbs_python
-- Main Schema File for Core Banking System
-- Contains all table definitions consolidated from various schema files
-- Created: May 19, 2025
-- Updated: May 21, 2025 - Added Digital Banking Tables (v1.1.2)

-- Enable strict mode for better data integrity
SET sql_mode = 'STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION';

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

-- Database creation (uncomment if needed)
-- CREATE DATABASE IF NOT EXISTS cbs_python CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
-- USE cbs_python;

-- =============================================
-- CORE DATA TABLES
-- =============================================

--
-- Table structure for table `cbs_accounts`
--

DROP TABLE IF EXISTS `cbs_accounts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cbs_accounts` (
  `account_number` varchar(20) NOT NULL,
  `customer_id` varchar(20) NOT NULL,
  `account_type` enum('SAVINGS','CURRENT','FIXED_DEPOSIT','RECURRING_DEPOSIT','LOAN','SALARY','NRI','PENSION','CORPORATE','JOINT') NOT NULL,
  `branch_code` varchar(20) NOT NULL,
  `ifsc_code` varchar(20) NOT NULL,
  `opening_date` datetime DEFAULT NULL,
  `balance` decimal(12,2) NOT NULL,
  `interest_rate` decimal(5,2) DEFAULT NULL,
  `status` enum('ACTIVE','DORMANT','FROZEN','CLOSED','SUSPENDED','ONHOLD') NOT NULL,
  `last_transaction` datetime DEFAULT NULL,
  `nominee_name` varchar(100) DEFAULT NULL,
  `nominee_relation` varchar(50) DEFAULT NULL,
  `service_charges_applicable` tinyint(1) DEFAULT NULL,
  `minimum_balance` decimal(10,2) DEFAULT NULL,
  `overdraft_limit` decimal(12,2) DEFAULT NULL,
  `joint_holders` varchar(255) DEFAULT NULL,
  `account_category` enum('REGULAR','PREMIUM','ZERO_BALANCE','SENIOR_CITIZEN','STUDENT','MINOR') DEFAULT NULL,
  `account_manager` varchar(50) DEFAULT NULL,
  `sweep_in_facility` tinyint(1) DEFAULT NULL,
  `sweep_out_facility` tinyint(1) DEFAULT NULL,
  `sweep_account` varchar(20) DEFAULT NULL,
  `auto_renewal` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `closing_date` datetime DEFAULT NULL,
  `closing_reason` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`account_number`),
  KEY `customer_id` (`customer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cbs_admin_users`
--

DROP TABLE IF EXISTS `cbs_admin_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cbs_admin_users` (
  `admin_id` varchar(20) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password_hash` varchar(128) NOT NULL,
  `salt` varchar(64) NOT NULL,
  `full_name` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `mobile` varchar(20) NOT NULL,
  `department` varchar(50) NOT NULL,
  `branch_code` varchar(20) NOT NULL,
  `employee_id` varchar(20) NOT NULL,
  `role` varchar(50) NOT NULL,
  `status` varchar(50) NOT NULL,
  `password_expiry_date` date NOT NULL,
  `account_locked` tinyint(1) DEFAULT NULL,
  `failed_login_attempts` int DEFAULT NULL,
  `last_login` datetime DEFAULT NULL,
  `last_password_change` datetime DEFAULT NULL,
  `access_level` int DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `created_by` varchar(20) DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `updated_by` varchar(20) DEFAULT NULL,
  `requires_2fa` tinyint(1) DEFAULT NULL,
  `two_fa_method` varchar(20) DEFAULT NULL,
  `two_fa_secret` varchar(128) DEFAULT NULL,
  `direct_reports` varchar(255) DEFAULT NULL,
  `permissions` text,
  `session_timeout_minutes` int DEFAULT NULL,
  `ip_restriction` varchar(255) DEFAULT NULL,
  `allowed_login_times` varchar(255) DEFAULT NULL,
  `last_security_training` date DEFAULT NULL,
  `security_questions_answered` tinyint(1) DEFAULT NULL,
  `out_of_office` tinyint(1) DEFAULT NULL,
  `delegate_to` varchar(20) DEFAULT NULL,
  `biometric_registered` tinyint(1) DEFAULT NULL,
  `profile_picture` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`admin_id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `employee_id` (`employee_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cbs_customers`
--

DROP TABLE IF EXISTS `cbs_customers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cbs_customers` (
  `customer_id` varchar(20) NOT NULL,
  `customer_type` enum('INDIVIDUAL','BUSINESS','CORPORATE','TRUST','PARTNERSHIP','ASSOCIATION','GOVERNMENT') NOT NULL,
  `first_name` varchar(50) DEFAULT NULL,
  `middle_name` varchar(50) DEFAULT NULL,
  `last_name` varchar(50) DEFAULT NULL,
  `business_name` varchar(100) DEFAULT NULL,
  `date_of_birth` date DEFAULT NULL,
  `date_of_incorporation` date DEFAULT NULL,
  `kyc_status` enum('COMPLETE','INCOMPLETE','PENDING','EXPIRED') NOT NULL,
  `pan_number` varchar(20) DEFAULT NULL,
  `aadhaar_number` varchar(20) DEFAULT NULL,
  `passport_number` varchar(20) DEFAULT NULL,
  `gstin` varchar(20) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `mobile` varchar(20) NOT NULL,
  `address_line1` varchar(100) NOT NULL,
  `address_line2` varchar(100) DEFAULT NULL,
  `city` varchar(50) NOT NULL,
  `state` varchar(50) NOT NULL,
  `postal_code` varchar(20) NOT NULL,
  `country` varchar(50) NOT NULL DEFAULT 'India',
  `occupation` varchar(100) DEFAULT NULL,
  `annual_income` decimal(12,2) DEFAULT NULL,
  `income_source` varchar(100) DEFAULT NULL,
  `customer_segment` varchar(50) DEFAULT NULL,
  `risk_profile` enum('LOW','MEDIUM','HIGH') DEFAULT NULL,
  `relationship_manager` varchar(50) DEFAULT NULL,
  `customer_since` date DEFAULT NULL,
  `status` enum('ACTIVE','DORMANT','CLOSED','SUSPENDED','DECEASED','BLACKLISTED') NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`customer_id`),
  KEY `idx_mobile` (`mobile`),
  KEY `idx_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cbs_transactions`
--

DROP TABLE IF EXISTS `cbs_transactions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cbs_transactions` (
  `transaction_id` varchar(30) NOT NULL,
  `transaction_type` enum('DEPOSIT','WITHDRAWAL','TRANSFER','PAYMENT','LOAN_DISBURSEMENT','LOAN_REPAYMENT','INTEREST_CREDIT','CHARGE','REVERSAL','ADJUSTMENT') NOT NULL,
  `account_number` varchar(20) NOT NULL,
  `counter_account` varchar(20) DEFAULT NULL,
  `amount` decimal(12,2) NOT NULL,
  `currency` varchar(3) NOT NULL DEFAULT 'INR',
  `transaction_date` datetime NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  `reference_number` varchar(50) DEFAULT NULL,
  `transaction_status` enum('INITIATED','PENDING','COMPLETED','FAILED','REVERSED','SUSPENDED') NOT NULL,
  `transaction_mode` enum('CASH','CHEQUE','NEFT','RTGS','IMPS','UPI','ATM','POS','INTERNET_BANKING','MOBILE_BANKING','AUTO_DEBIT','STANDING_INSTRUCTION') DEFAULT NULL,
  `cheque_number` varchar(20) DEFAULT NULL,
  `transaction_charges` decimal(10,2) DEFAULT NULL,
  `balance_after_transaction` decimal(12,2) DEFAULT NULL,
  `initiated_by` varchar(50) DEFAULT NULL,
  `authorized_by` varchar(50) DEFAULT NULL,
  `remarks` varchar(255) DEFAULT NULL,
  `branch_code` varchar(20) NOT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`transaction_id`),
  KEY `idx_account_number` (`account_number`),
  KEY `idx_transaction_date` (`transaction_date`),
  KEY `idx_counter_account` (`counter_account`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cbs_branches`
--

DROP TABLE IF EXISTS `cbs_branches`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cbs_branches` (
  `branch_code` varchar(20) NOT NULL,
  `branch_name` varchar(100) NOT NULL,
  `ifsc_code` varchar(20) NOT NULL,
  `micr_code` varchar(20) DEFAULT NULL,
  `address_line1` varchar(100) NOT NULL,
  `address_line2` varchar(100) DEFAULT NULL,
  `city` varchar(50) NOT NULL,
  `state` varchar(50) NOT NULL,
  `postal_code` varchar(20) NOT NULL,
  `country` varchar(50) NOT NULL DEFAULT 'India',
  `phone` varchar(20) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `manager` varchar(100) DEFAULT NULL,
  `branch_type` enum('HEAD_OFFICE','REGIONAL_OFFICE','FULL_SERVICE','SATELLITE','EXTENSION_COUNTER','DIGITAL') NOT NULL,
  `opening_hours` varchar(100) DEFAULT NULL,
  `holiday_schedule` varchar(255) DEFAULT NULL,
  `services_offered` text DEFAULT NULL,
  `status` enum('ACTIVE','CLOSED','RENOVATING','RELOCATING') NOT NULL DEFAULT 'ACTIVE',
  `established_date` date DEFAULT NULL,
  `zone` varchar(50) DEFAULT NULL,
  `region` varchar(50) DEFAULT NULL,
  `latitude` decimal(10,8) DEFAULT NULL,
  `longitude` decimal(11,8) DEFAULT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`branch_code`),
  UNIQUE KEY `ifsc_code` (`ifsc_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cbs_loans`
--

DROP TABLE IF EXISTS `cbs_loans`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cbs_loans` (
  `loan_id` varchar(20) NOT NULL,
  `account_number` varchar(20) NOT NULL,
  `customer_id` varchar(20) NOT NULL,
  `loan_type` enum('HOME','VEHICLE','PERSONAL','EDUCATION','BUSINESS','AGRICULTURE','GOLD','OVERDRAFT') NOT NULL,
  `loan_amount` decimal(12,2) NOT NULL,
  `interest_rate` decimal(5,2) NOT NULL,
  `term_months` int NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `disbursement_date` date DEFAULT NULL,
  `disbursement_amount` decimal(12,2) DEFAULT NULL,
  `disbursed_account` varchar(20) DEFAULT NULL,
  `emi_amount` decimal(10,2) DEFAULT NULL,
  `emi_date` int DEFAULT NULL,
  `outstanding_principal` decimal(12,2) DEFAULT NULL,
  `outstanding_interest` decimal(12,2) DEFAULT NULL,
  `last_payment_date` date DEFAULT NULL,
  `next_payment_date` date DEFAULT NULL,
  `collateral_details` text DEFAULT NULL,
  `guarantor_id` varchar(20) DEFAULT NULL,
  `loan_purpose` varchar(255) DEFAULT NULL,
  `status` enum('APPLIED','APPROVED','REJECTED','DISBURSED','ACTIVE','CLOSED','DEFAULT','WRITTEN_OFF','RESTRUCTURED') NOT NULL,
  `processing_fee` decimal(10,2) DEFAULT NULL,
  `prepayment_penalty` decimal(5,2) DEFAULT NULL,
  `late_payment_fee` decimal(10,2) DEFAULT NULL,
  `approved_by` varchar(50) DEFAULT NULL,
  `approval_date` date DEFAULT NULL,
  `rejection_reason` varchar(255) DEFAULT NULL,
  `credit_score` int DEFAULT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`loan_id`),
  KEY `idx_customer_id` (`customer_id`),
  KEY `idx_account_number` (`account_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cbs_loan_payments`
--

DROP TABLE IF EXISTS `cbs_loan_payments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cbs_loan_payments` (
  `payment_id` varchar(30) NOT NULL,
  `loan_id` varchar(20) NOT NULL,
  `payment_date` date NOT NULL,
  `payment_amount` decimal(12,2) NOT NULL,
  `principal_component` decimal(12,2) NOT NULL,
  `interest_component` decimal(12,2) NOT NULL,
  `penalty_amount` decimal(10,2) DEFAULT NULL,
  `payment_mode` enum('CASH','CHEQUE','NEFT','RTGS','IMPS','UPI','AUTO_DEBIT') NOT NULL,
  `transaction_id` varchar(30) DEFAULT NULL,
  `payment_status` enum('PENDING','COMPLETED','FAILED','REVERSED') NOT NULL,
  `remarks` varchar(255) DEFAULT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`payment_id`),
  KEY `idx_loan_id` (`loan_id`),
  KEY `idx_payment_date` (`payment_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cbs_cards`
--

DROP TABLE IF EXISTS `cbs_cards`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cbs_cards` (
  `card_id` varchar(20) NOT NULL,
  `card_number` varchar(16) NOT NULL,
  `customer_id` varchar(20) NOT NULL,
  `account_number` varchar(20) NOT NULL,
  `card_type` enum('DEBIT','CREDIT','PREPAID','VIRTUAL') NOT NULL,
  `card_network` enum('VISA','MASTERCARD','RUPAY','AMEX','DINERS') NOT NULL,
  `card_category` enum('CLASSIC','GOLD','PLATINUM','SIGNATURE','INFINITE','BUSINESS') NOT NULL,
  `name_on_card` varchar(100) NOT NULL,
  `expiry_date` date NOT NULL,
  `cvv` varchar(3) NOT NULL,
  `pin_hash` varchar(128) DEFAULT NULL,
  `issue_date` date NOT NULL,
  `activation_date` date DEFAULT NULL,
  `daily_limit` decimal(10,2) DEFAULT NULL,
  `atm_limit` decimal(10,2) DEFAULT NULL,
  `pos_limit` decimal(10,2) DEFAULT NULL,
  `online_limit` decimal(10,2) DEFAULT NULL,
  `international_usage` tinyint(1) DEFAULT '0',
  `contactless_enabled` tinyint(1) DEFAULT '0',
  `virtual_card` tinyint(1) DEFAULT '0',
  `status` enum('ISSUED','ACTIVE','INACTIVE','BLOCKED','EXPIRED','CLOSED') NOT NULL,
  `blocked_reason` varchar(255) DEFAULT NULL,
  `reissue_reason` varchar(255) DEFAULT NULL,
  `reissued_card_id` varchar(20) DEFAULT NULL,
  `replacement_for` varchar(20) DEFAULT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`card_id`),
  UNIQUE KEY `card_number` (`card_number`),
  KEY `idx_customer_id` (`customer_id`),
  KEY `idx_account_number` (`account_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cbs_beneficiaries`
--

DROP TABLE IF EXISTS `cbs_beneficiaries`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cbs_beneficiaries` (
  `beneficiary_id` varchar(20) NOT NULL,
  `customer_id` varchar(20) NOT NULL,
  `account_number` varchar(20) NOT NULL,
  `beneficiary_name` varchar(100) NOT NULL,
  `beneficiary_account_number` varchar(20) NOT NULL,
  `beneficiary_ifsc` varchar(20) NOT NULL,
  `beneficiary_bank` varchar(100) NOT NULL,
  `beneficiary_branch` varchar(100) DEFAULT NULL,
  `account_type` enum('SAVINGS','CURRENT','LOAN','OTHERS') NOT NULL,
  `nickname` varchar(50) DEFAULT NULL,
  `transfer_limit` decimal(12,2) DEFAULT NULL,
  `beneficiary_email` varchar(100) DEFAULT NULL,
  `beneficiary_mobile` varchar(20) DEFAULT NULL,
  `status` enum('ACTIVE','INACTIVE','PENDING','DELETED') NOT NULL DEFAULT 'PENDING',
  `verification_code` varchar(10) DEFAULT NULL,
  `verification_status` enum('PENDING','VERIFIED','REJECTED') DEFAULT 'PENDING',
  `last_transaction_date` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL,
  `verified_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`beneficiary_id`),
  KEY `idx_customer_id` (`customer_id`),
  KEY `idx_account_number` (`account_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cbs_fixed_deposits`
--

DROP TABLE IF EXISTS `cbs_fixed_deposits`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cbs_fixed_deposits` (
  `fd_id` varchar(20) NOT NULL,
  `account_number` varchar(20) NOT NULL,
  `customer_id` varchar(20) NOT NULL,
  `principal_amount` decimal(12,2) NOT NULL,
  `interest_rate` decimal(5,2) NOT NULL,
  `tenure_months` int NOT NULL,
  `start_date` date NOT NULL,
  `maturity_date` date NOT NULL,
  `maturity_amount` decimal(12,2) NOT NULL,
  `interest_payout` enum('MONTHLY','QUARTERLY','ANNUALLY','MATURITY') NOT NULL,
  `interest_payout_account` varchar(20) DEFAULT NULL,
  `auto_renewal` tinyint(1) DEFAULT '0',
  `renewal_type` enum('PRINCIPAL','PRINCIPAL_WITH_INTEREST') DEFAULT NULL,
  `loan_allowed` tinyint(1) DEFAULT '0',
  `loan_percentage` decimal(5,2) DEFAULT NULL,
  `premature_withdrawal_allowed` tinyint(1) DEFAULT '1',
  `premature_withdrawal_penalty` decimal(5,2) DEFAULT NULL,
  `tax_deduction_applicable` tinyint(1) DEFAULT '1',
  `nominee_name` varchar(100) DEFAULT NULL,
  `nominee_relation` varchar(50) DEFAULT NULL,
  `status` enum('ACTIVE','MATURED','CLOSED','PREMATURE_WITHDRAWAL') NOT NULL DEFAULT 'ACTIVE',
  `created_at` datetime NOT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`fd_id`),
  KEY `idx_account_number` (`account_number`),
  KEY `idx_customer_id` (`customer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cbs_audit_logs`
--

DROP TABLE IF EXISTS `cbs_audit_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cbs_audit_logs` (
  `log_id` varchar(36) NOT NULL,
  `action` varchar(50) NOT NULL,
  `entity_type` varchar(50) NOT NULL,
  `entity_id` varchar(50) NOT NULL,
  `user_id` varchar(50) NOT NULL,
  `action_timestamp` datetime NOT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  `user_agent` varchar(255) DEFAULT NULL,
  `session_id` varchar(100) DEFAULT NULL,
  `old_value` text DEFAULT NULL,
  `new_value` text DEFAULT NULL,
  `status` enum('SUCCESS','FAILURE') NOT NULL,
  `failure_reason` varchar(255) DEFAULT NULL,
  `request_id` varchar(50) DEFAULT NULL,
  `branch_code` varchar(20) DEFAULT NULL,
  `device_id` varchar(100) DEFAULT NULL,
  `module` varchar(50) DEFAULT NULL,
  `sub_module` varchar(50) DEFAULT NULL,
  `criticality` enum('LOW','MEDIUM','HIGH','CRITICAL') DEFAULT 'LOW',
  PRIMARY KEY (`log_id`),
  KEY `idx_entity_id` (`entity_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_action_timestamp` (`action_timestamp`),
  KEY `idx_action` (`action`),
  KEY `idx_entity_type` (`entity_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cbs_standing_instructions`
--

DROP TABLE IF EXISTS `cbs_standing_instructions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cbs_standing_instructions` (
  `instruction_id` varchar(20) NOT NULL,
  `customer_id` varchar(20) NOT NULL,
  `source_account` varchar(20) NOT NULL,
  `destination_account` varchar(20) NOT NULL,
  `destination_ifsc` varchar(20) DEFAULT NULL,
  `amount` decimal(12,2) NOT NULL,
  `frequency` enum('DAILY','WEEKLY','MONTHLY','QUARTERLY','HALF_YEARLY','YEARLY') NOT NULL,
  `execution_day` int DEFAULT NULL,
  `execution_weekday` enum('MONDAY','TUESDAY','WEDNESDAY','THURSDAY','FRIDAY','SATURDAY','SUNDAY') DEFAULT NULL,
  `start_date` date NOT NULL,
  `end_date` date DEFAULT NULL,
  `next_execution_date` date NOT NULL,
  `last_execution_date` date DEFAULT NULL,
  `last_execution_status` enum('SUCCESS','FAILED','PENDING') DEFAULT NULL,
  `failure_reason` varchar(255) DEFAULT NULL,
  `retry_count` int DEFAULT '0',
  `max_retries` int DEFAULT '3',
  `description` varchar(255) DEFAULT NULL,
  `status` enum('ACTIVE','PAUSED','COMPLETED','TERMINATED') NOT NULL DEFAULT 'ACTIVE',
  `created_at` datetime NOT NULL,
  `created_by` varchar(50) DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `updated_by` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`instruction_id`),
  KEY `idx_customer_id` (`customer_id`),
  KEY `idx_source_account` (`source_account`),
  KEY `idx_next_execution_date` (`next_execution_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cbs_user_sessions`
--

DROP TABLE IF EXISTS `cbs_user_sessions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cbs_user_sessions` (
  `session_id` varchar(100) NOT NULL,
  `user_id` varchar(20) NOT NULL,
  `user_type` enum('CUSTOMER','ADMIN','EMPLOYEE') NOT NULL,
  `login_time` datetime NOT NULL,
  `logout_time` datetime DEFAULT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  `user_agent` varchar(255) DEFAULT NULL,
  `device_type` enum('DESKTOP','MOBILE','TABLET','OTHER') DEFAULT NULL,
  `browser` varchar(50) DEFAULT NULL,
  `os` varchar(50) DEFAULT NULL,
  `location` varchar(100) DEFAULT NULL,
  `status` enum('ACTIVE','EXPIRED','LOGGED_OUT','TERMINATED') NOT NULL,
  `last_activity` datetime DEFAULT NULL,
  `expiry_time` datetime DEFAULT NULL,
  `jwt_token` varchar(500) DEFAULT NULL,
  `refresh_token` varchar(100) DEFAULT NULL,
  `channel` enum('INTERNET_BANKING','MOBILE_BANKING','BRANCH','ATM','API') NOT NULL,
  `two_fa_verified` tinyint(1) DEFAULT '0',
  `device_id` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`session_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_login_time` (`login_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cbs_notifications`
--

DROP TABLE IF EXISTS `cbs_notifications`;
CREATE TABLE `cbs_notifications` (
  `notification_id` varchar(36) NOT NULL,
  `user_id` varchar(20) NOT NULL,
  `user_type` enum('CUSTOMER','ADMIN','EMPLOYEE') NOT NULL,
  `title` varchar(255) NOT NULL,
  `message` text NOT NULL,
  `notification_type` enum('INFO','ALERT','WARNING','PROMOTION','SECURITY') NOT NULL,
  `status` enum('UNREAD','READ','ARCHIVED') NOT NULL DEFAULT 'UNREAD',
  `created_at` datetime NOT NULL,
  `read_at` datetime DEFAULT NULL,
  PRIMARY KEY (`notification_id`),
  KEY `idx_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Table structure for table `cbs_document_uploads`
--

DROP TABLE IF EXISTS `cbs_document_uploads`;
CREATE TABLE `cbs_document_uploads` (
  `document_id` varchar(36) NOT NULL,
  `customer_id` varchar(20) NOT NULL,
  `document_type` enum('AADHAAR','PAN','PASSPORT','PHOTO','ADDRESS_PROOF','OTHER') NOT NULL,
  `file_path` varchar(255) NOT NULL,
  `uploaded_at` datetime NOT NULL,
  `verified` tinyint(1) DEFAULT '0',
  `verified_by` varchar(20) DEFAULT NULL,
  `verified_at` datetime DEFAULT NULL,
  PRIMARY KEY (`document_id`),
  KEY `idx_customer_id` (`customer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Table structure for table `cbs_support_tickets`
--

DROP TABLE IF EXISTS `cbs_support_tickets`;
CREATE TABLE `cbs_support_tickets` (
  `ticket_id` varchar(36) NOT NULL,
  `customer_id` varchar(20) NOT NULL,
  `subject` varchar(255) NOT NULL,
  `description` text NOT NULL,
  `status` enum('OPEN','IN_PROGRESS','RESOLVED','CLOSED') NOT NULL DEFAULT 'OPEN',
  `priority` enum('LOW','MEDIUM','HIGH','CRITICAL') NOT NULL DEFAULT 'LOW',
  `created_at` datetime NOT NULL,
  `updated_at` datetime DEFAULT NULL,
  `resolved_at` datetime DEFAULT NULL,
  `assigned_to` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`ticket_id`),
  KEY `idx_customer_id` (`customer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Table structure for table `cbs_audit_trail`
--

DROP TABLE IF EXISTS `cbs_audit_trail`;
CREATE TABLE `cbs_audit_trail` (
  `audit_id` varchar(36) NOT NULL,
  `entity` varchar(50) NOT NULL,
  `entity_id` varchar(50) NOT NULL,
  `action` varchar(50) NOT NULL,
  `performed_by` varchar(20) NOT NULL,
  `performed_at` datetime NOT NULL,
  `old_value` text DEFAULT NULL,
  `new_value` text DEFAULT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`audit_id`),
  KEY `idx_entity_id` (`entity_id`),
  KEY `idx_performed_by` (`performed_by`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Table structure for table `cbs_mobile_banking_users`
--

DROP TABLE IF EXISTS `cbs_mobile_banking_users`;
CREATE TABLE `cbs_mobile_banking_users` (
  `mb_user_id` varchar(36) NOT NULL,
  `customer_id` varchar(20) NOT NULL,
  `device_id` varchar(100) NOT NULL,
  `device_model` varchar(100) DEFAULT NULL,
  `device_os` varchar(50) DEFAULT NULL,
  `os_version` varchar(20) DEFAULT NULL,
  `app_version` varchar(20) DEFAULT NULL,
  `fcm_token` varchar(255) DEFAULT NULL,
  `biometric_enabled` tinyint(1) DEFAULT '0',
  `face_id_enabled` tinyint(1) DEFAULT '0',
  `last_login` datetime DEFAULT NULL,
  `status` enum('ACTIVE','INACTIVE','BLOCKED','PENDING_ACTIVATION') NOT NULL DEFAULT 'PENDING_ACTIVATION',
  `registered_at` datetime NOT NULL,
  `activation_code` varchar(10) DEFAULT NULL,
  `activation_code_expiry` datetime DEFAULT NULL,
  `notification_preferences` text DEFAULT NULL,
  PRIMARY KEY (`mb_user_id`),
  UNIQUE KEY `uk_customer_device` (`customer_id`, `device_id`),
  KEY `idx_customer_id` (`customer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Table structure for table `cbs_internet_banking_users`
--

DROP TABLE IF EXISTS `cbs_internet_banking_users`;
CREATE TABLE `cbs_internet_banking_users` (
  `ib_user_id` varchar(36) NOT NULL,
  `customer_id` varchar(20) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password_hash` varchar(128) NOT NULL,
  `salt` varchar(64) NOT NULL,
  `security_question1` varchar(255) DEFAULT NULL,
  `security_answer1_hash` varchar(128) DEFAULT NULL,
  `security_question2` varchar(255) DEFAULT NULL,
  `security_answer2_hash` varchar(128) DEFAULT NULL,
  `last_login` datetime DEFAULT NULL,
  `failed_login_attempts` int DEFAULT '0',
  `account_locked` tinyint(1) DEFAULT '0',
  `lock_reason` varchar(255) DEFAULT NULL,
  `password_change_required` tinyint(1) DEFAULT '0',
  `last_password_change` datetime DEFAULT NULL,
  `two_fa_enabled` tinyint(1) DEFAULT '1',
  `two_fa_method` enum('SMS','EMAIL','AUTHENTICATOR_APP') DEFAULT 'SMS',
  `status` enum('ACTIVE','INACTIVE','BLOCKED','PENDING_ACTIVATION') NOT NULL DEFAULT 'PENDING_ACTIVATION',
  `registered_at` datetime NOT NULL,
  `activation_code` varchar(10) DEFAULT NULL,
  `activation_code_expiry` datetime DEFAULT NULL,
  `transaction_limit` decimal(12,2) DEFAULT '50000.00',
  PRIMARY KEY (`ib_user_id`),
  UNIQUE KEY `username` (`username`),
  KEY `idx_customer_id` (`customer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Table structure for table `cbs_bill_payments`
--

DROP TABLE IF EXISTS `cbs_bill_payments`;
CREATE TABLE `cbs_bill_payments` (
  `payment_id` varchar(36) NOT NULL,
  `customer_id` varchar(20) NOT NULL,
  `account_number` varchar(20) NOT NULL,
  `biller_id` varchar(50) NOT NULL,
  `biller_name` varchar(100) NOT NULL,
  `biller_category` enum('ELECTRICITY','WATER','GAS','TELECOM','INTERNET','CABLE_TV','INSURANCE','CREDIT_CARD','LOAN','TAX','EDUCATION','OTHER') NOT NULL,
  `consumer_number` varchar(50) NOT NULL,
  `amount` decimal(12,2) NOT NULL,
  `payment_date` datetime NOT NULL,
  `payment_status` enum('INITIATED','PROCESSING','COMPLETED','FAILED','REVERSED') NOT NULL,
  `transaction_id` varchar(30) DEFAULT NULL,
  `reference_number` varchar(50) DEFAULT NULL,
  `failure_reason` varchar(255) DEFAULT NULL,
  `remarks` varchar(255) DEFAULT NULL,
  `receipt_generated` tinyint(1) DEFAULT '0',
  `created_at` datetime NOT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`payment_id`),
  KEY `idx_customer_id` (`customer_id`),
  KEY `idx_account_number` (`account_number`),
  KEY `idx_payment_date` (`payment_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Table structure for table `cbs_customer_billers`
--

DROP TABLE IF EXISTS `cbs_customer_billers`;
CREATE TABLE `cbs_customer_billers` (
  `id` varchar(36) NOT NULL,
  `customer_id` varchar(20) NOT NULL,
  `biller_id` varchar(50) NOT NULL,
  `biller_name` varchar(100) NOT NULL,
  `biller_category` enum('ELECTRICITY','WATER','GAS','TELECOM','INTERNET','CABLE_TV','INSURANCE','CREDIT_CARD','LOAN','TAX','EDUCATION','OTHER') NOT NULL,
  `consumer_number` varchar(50) NOT NULL,
  `consumer_name` varchar(100) DEFAULT NULL,
  `auto_pay_enabled` tinyint(1) DEFAULT '0',
  `auto_pay_limit` decimal(12,2) DEFAULT NULL,
  `auto_pay_account` varchar(20) DEFAULT NULL,
  `nickname` varchar(50) DEFAULT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_customer_biller_consumer` (`customer_id`, `biller_id`, `consumer_number`),
  KEY `idx_customer_id` (`customer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Table structure for table `cbs_recurring_deposits`
--

DROP TABLE IF EXISTS `cbs_recurring_deposits`;
CREATE TABLE `cbs_recurring_deposits` (
  `rd_id` varchar(20) NOT NULL,
  `account_number` varchar(20) NOT NULL,
  `customer_id` varchar(20) NOT NULL,
  `monthly_installment` decimal(12,2) NOT NULL,
  `tenure_months` int NOT NULL,
  `interest_rate` decimal(5,2) NOT NULL,
  `start_date` date NOT NULL,
  `maturity_date` date NOT NULL,
  `maturity_amount` decimal(12,2) NOT NULL,
  `installment_day` int NOT NULL,
  `source_account` varchar(20) NOT NULL,
  `auto_debit_enabled` tinyint(1) DEFAULT '1',
  `grace_period_days` int DEFAULT '5',
  `missed_installments` int DEFAULT '0',
  `last_installment_date` date DEFAULT NULL,
  `next_installment_date` date DEFAULT NULL,
  `nominee_name` varchar(100) DEFAULT NULL,
  `nominee_relation` varchar(50) DEFAULT NULL,
  `premature_withdrawal_allowed` tinyint(1) DEFAULT '1',
  `premature_withdrawal_penalty` decimal(5,2) DEFAULT NULL,
  `status` enum('ACTIVE','MATURED','CLOSED','DEFAULTED') NOT NULL DEFAULT 'ACTIVE',
  `created_at` datetime NOT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`rd_id`),
  KEY `idx_account_number` (`account_number`),
  KEY `idx_customer_id` (`customer_id`),
  KEY `idx_source_account` (`source_account`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Table structure for table `cbs_atm_transactions`
--

DROP TABLE IF EXISTS `cbs_atm_transactions`;
CREATE TABLE `cbs_atm_transactions` (
  `atm_txn_id` varchar(36) NOT NULL,
  `card_id` varchar(20) NOT NULL,
  `account_number` varchar(20) NOT NULL,
  `transaction_type` enum('WITHDRAWAL','BALANCE_INQUIRY','MINI_STATEMENT','PIN_CHANGE','FUND_TRANSFER','BILL_PAYMENT','DEPOSIT') NOT NULL,
  `amount` decimal(12,2) DEFAULT NULL,
  `transaction_date` datetime NOT NULL,
  `atm_id` varchar(20) NOT NULL,
  `location` varchar(100) DEFAULT NULL,
  `status` enum('SUCCESS','FAILURE','CANCELLED','TIMEOUT','REVERSED') NOT NULL,
  `response_code` varchar(10) DEFAULT NULL,
  `failure_reason` varchar(255) DEFAULT NULL,
  `reference_number` varchar(50) DEFAULT NULL,
  `transaction_id` varchar(30) DEFAULT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`atm_txn_id`),
  KEY `idx_card_id` (`card_id`),
  KEY `idx_account_number` (`account_number`),
  KEY `idx_transaction_date` (`transaction_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Table structure for table `cbs_atm_terminals`
--

DROP TABLE IF EXISTS `cbs_atm_terminals`;
CREATE TABLE `cbs_atm_terminals` (
  `atm_id` varchar(20) NOT NULL,
  `terminal_id` varchar(20) NOT NULL,
  `location` varchar(255) NOT NULL,
  `branch_code` varchar(20) DEFAULT NULL,
  `address_line1` varchar(100) NOT NULL,
  `address_line2` varchar(100) DEFAULT NULL,
  `city` varchar(50) NOT NULL,
  `state` varchar(50) NOT NULL,
  `postal_code` varchar(20) NOT NULL,
  `country` varchar(50) NOT NULL DEFAULT 'India',
  `atm_type` enum('ONSITE','OFFSITE','MOBILE','BIOMETRIC','CASH_RECYCLER') NOT NULL,
  `status` enum('ACTIVE','INACTIVE','MAINTENANCE','OFFLINE','CASH_OUT','OUT_OF_SERVICE') NOT NULL DEFAULT 'ACTIVE',
  `cash_status` decimal(12,2) DEFAULT NULL,
  `last_cash_refill` datetime DEFAULT NULL,
  `last_maintenance` datetime DEFAULT NULL,
  `latitude` decimal(10,8) DEFAULT NULL,
  `longitude` decimal(11,8) DEFAULT NULL,
  `features` varchar(255) DEFAULT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`atm_id`),
  UNIQUE KEY `terminal_id` (`terminal_id`),
  KEY `idx_branch_code` (`branch_code`),
  KEY `idx_location` (`city`, `state`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Table structure for table `cbs_kyc_documents`
--

DROP TABLE IF EXISTS `cbs_kyc_documents`;
CREATE TABLE `cbs_kyc_documents` (
  `kyc_id` varchar(36) NOT NULL,
  `customer_id` varchar(20) NOT NULL,
  `document_type` enum('PAN_CARD','AADHAAR_CARD','PASSPORT','VOTER_ID','DRIVING_LICENSE','UTILITY_BILL','BANK_STATEMENT','RENT_AGREEMENT','BUSINESS_PROOF','OTHER') NOT NULL,
  `document_number` varchar(50) NOT NULL,
  `issue_date` date DEFAULT NULL,
  `expiry_date` date DEFAULT NULL,
  `issued_by` varchar(100) DEFAULT NULL,
  `document_url` varchar(255) DEFAULT NULL,
  `verification_status` enum('PENDING','VERIFIED','REJECTED','EXPIRED') NOT NULL DEFAULT 'PENDING',
  `verification_date` datetime DEFAULT NULL,
  `verified_by` varchar(20) DEFAULT NULL,
  `verification_remarks` varchar(255) DEFAULT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`kyc_id`),
  UNIQUE KEY `uk_customer_document_type` (`customer_id`, `document_type`),
  KEY `idx_customer_id` (`customer_id`),
  KEY `idx_document_number` (`document_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 
-- Include remaining tables from cbs_python_schema.sql
-- Note: This file should be completed by copying all table definitions from cbs_python_schema.sql
-- and other schema files in the project
--

/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
