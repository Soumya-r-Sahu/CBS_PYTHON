-- Core Banking System - Main Database Setup Script
-- Created: May 19, 2025
-- 
-- This script sets up the entire database structure including:
-- 1. Tables (schema)
-- 2. ID validation and generation functions
-- 3. Stored procedures
-- 4. Triggers
--
-- Execute this script to set up a new CBS_PYTHON database instance

-- Enable strict mode for better data integrity
SET sql_mode = 'STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION';

-- Create and use the database
CREATE DATABASE IF NOT EXISTS cbs_python CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE cbs_python;

-- =============================================
-- SCHEMA: Import all table definitions
-- =============================================
SOURCE schema/main_schema.sql;

-- =============================================
-- ID STANDARDS: Import ID validation and generation functions
-- =============================================
SOURCE id_standards/banking_id_validation.sql;
SOURCE id_standards/banking_id_generation.sql;
SOURCE id_standards/international_id_standards.sql;

-- =============================================
-- PROCEDURES: Import all stored procedures
-- =============================================
SOURCE procedures/withdrawal_procedures.sql;
SOURCE procedures/transfer_procedures.sql;
SOURCE procedures/triggers.sql;

-- Log successful database setup
SELECT 'CBS_PYTHON database setup completed successfully.' AS 'Setup Status';

-- Provide summary of database objects
SELECT 'Tables' AS Object_Type, COUNT(*) AS Count FROM information_schema.tables WHERE table_schema = 'cbs_python' AND table_type = 'BASE TABLE'
UNION
SELECT 'Views' AS Object_Type, COUNT(*) AS Count FROM information_schema.views WHERE table_schema = 'cbs_python'
UNION
SELECT 'Stored Procedures' AS Object_Type, COUNT(*) AS Count FROM information_schema.routines WHERE routine_schema = 'cbs_python' AND routine_type = 'PROCEDURE'
UNION
SELECT 'Functions' AS Object_Type, COUNT(*) AS Count FROM information_schema.routines WHERE routine_schema = 'cbs_python' AND routine_type = 'FUNCTION'
UNION
SELECT 'Triggers' AS Object_Type, COUNT(*) AS Count FROM information_schema.triggers WHERE trigger_schema = 'cbs_python';
