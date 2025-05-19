-- Main Schema File for Core Banking System
-- Contains all table definitions consolidated from various schema files
-- Created: May 19, 2025

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
