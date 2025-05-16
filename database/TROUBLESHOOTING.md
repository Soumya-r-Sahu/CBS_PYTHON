# 🛠️ Troubleshooting Guide: Core Banking System Database Setup

This guide will help you resolve common issues with the Core Banking System database setup.

## 📋 Table of Contents
- [🔄 Stored Procedures Issues](#stored-procedures-issues)
- [📊 Table Structure Issues](#table-structure-issues)
- [🔌 Connection Errors](#connection-errors)
- [⚙️ SQL Syntax Errors](#sql-syntax-errors)
- [🐞 Common Errors](#common-errors)
- [🆘 Additional Help](#additional-help)

## 🔄 Stored Procedures Issues <a name="stored-procedures-issues"></a>

If the validation script shows tables exist but stored procedures are missing, follow these steps:

### Solution 1: Import Using phpMyAdmin 🌐

1. **Open phpMyAdmin**: Go to http://localhost/phpmyadmin
2. **Select Database**: Click on "core_banking_system" in the left sidebar
3. **Import Procedures**: Click the "Import" tab
   - Click "Choose File" and select `database/import_procedures.sql`
   - Click "Go" at the bottom

### Solution 2: Use Import Helper 📤

1. **Copy Helper Script**: Copy `import_helper.php` to your XAMPP/WAMP web directory
   - For XAMPP: `C:\xampp\htdocs\`
   - For WAMP: `C:\wamp64\www\`
2. **Run Helper**: Open http://localhost/import_helper.php in your browser
   - Click "Stored Procedures Only" link
3. **Verify**: After import, run the check_procedures.py script to verify:
   ```powershell
   python database/check_procedures.py
   ```

### Solution 3: Direct MySQL Import 💻

If phpMyAdmin is causing issues, try direct MySQL command:

```powershell
cd C:\xampp\mysql\bin
mysql -u root -p core_banking_system < "d:\vs code\github\CBS-python\database\import_procedures.sql"
```

## 📊 Table Structure Issues <a name="table-structure-issues"></a>

If you're having issues with table structures:

| 🔢 Step | 📝 Action | 📋 Details |
|---------|----------|-----------|
| 1 | **Drop Database** | In phpMyAdmin, select the database and click "Operations" tab, then "Drop" |
| 2 | **Recreate Database** | Create a new database named "core_banking_system" |
| 3 | **Import Clean** | Import the full `setup_database.sql` file |

## 🔌 Connection Errors <a name="connection-errors"></a>

If you're having connection issues:

| 🔢 Step | 📝 Action | 📋 Details |
|---------|----------|-----------|
| 1 | **Check Services** | Ensure MySQL service is running in XAMPP/WAMP Control Panel |
| 2 | **Verify Settings** | Check credentials in `utils/config.py` match your MySQL setup |

## ⚙️ SQL Syntax Errors <a name="sql-syntax-errors"></a>

If you encounter syntax errors when importing or executing stored procedures, such as:

```
You have an error in your SQL syntax; check the manual that corresponds to your MariaDB server version for the right syntax to use near ';
    ELSEIF v_card_status != 'ACTIVE' THEN
        SET p_can_withdraw = FA...' at line 44
```

### Solution 1: Use the Fixed Procedure 🔧

1. **Import Fixed Version**: Use the fixed version of the procedure:
   ```powershell
   cd "path_to_xampp\mysql\bin"
   mysql -u root -p core_banking_system < "d:\vs code\github\CBS-python\database\fixed_procedure.sql"
   ```

### Solution 2: Fix the Syntax Manually 🔍

1. **Common Errors**:
   - Extra semicolons (`;`) inside procedure body - Remove them (except at the END statement)
   - Missing or mismatched `DELIMITER` statements
   - Issues with `ENUM` default values - Change to `VARCHAR` and handle defaults in procedure body

2. **Testing Your Fix**:
   ```powershell
   python database/test_withdrawal_procedure.py
   ```
3. **Test Connection**: Run the test connection script:
   ```powershell
   python test_db_connection.py
   ```

## ✅ Final Validation

After resolving issues, validate your setup:

```powershell
python database/validate_setup.py
```

All tables and procedures should be reported as existing and valid.

## 🐞 Common Errors <a name="common-errors"></a>

| ❌ Error | 📝 Description | 🔧 Solution |
|---------|--------------|-----------|
| **"Unread result found"** | MySQL results aren't fully processed | Our scripts have been updated to handle this |
| **"MySQL server has gone away"** | Connection timeout or server issue | Increase MySQL timeout settings |
| **"Table already exists"** | Attempting to create existing tables | Use DROP TABLE IF EXISTS statements |
| **"Stored procedure already exists"** | Trying to create duplicate procedures | Use DROP PROCEDURE IF EXISTS statements |

### For "MySQL server has gone away" errors:
Increase the MySQL timeout and packet size in your my.ini file:
```
max_allowed_packet = 128M
wait_timeout = 600
```

## 🆘 Need More Help? <a name="additional-help"></a>

If you're still having issues, try:

1. 📋 **Check MySQL Error Logs**
   - XAMPP: `C:\xampp\mysql\data\mysql_error.log`
   - WAMP: `C:\wamp64\logs\mysql.log`

2. 🔍 **Run MySQL in Verbose Mode**
   ```powershell
   cd C:\xampp\mysql\bin
   .\mysqld --console --verbose
   ```

3. 📊 **Import in Sections**
   - Try importing the SQL script in smaller chunks
   - Isolate and fix each error individually

4. 📱 **Contact Support**
   - Share specific error messages
   - Include details about your environment
