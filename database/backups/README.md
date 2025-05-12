# Periodic database backups

## How to Implement
- Store periodic (scheduled) database backup files in this folder.
- Use scripts or database tools to export the database to `.sql` or compressed formats (e.g., `.zip`, `.gz`).
- Name backup files with the date and time for easy tracking (e.g., `backup_2025-05-12_1200.sql`).

## Example Backup Script (Windows PowerShell)
```powershell
# Replace <user>, <password>, <database> as needed
$timestamp = Get-Date -Format "yyyy-MM-dd_HHmm"
$backupFile = "backup_${timestamp}.sql"
mysqldump -u <user> -p<password> <database> > $backupFile
```

## Schema/Format
- Each backup file is a full SQL dump of the database at a point in time.
- Optionally, compress backups for storage efficiency.

### Example File Naming
- `backup_2025-05-12_1200.sql`
- `backup_2025-05-12_1200.sql.gz`

### Example SQL Dump (Excerpt)
```sql
-- MySQL dump 10.13  Distrib 8.0.23, for Win64 (x86_64)
-- Host: localhost    Database: core_banking_system
-- ------------------------------------------------------
-- Server version	8.0.23

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
-- ...
CREATE TABLE `users` (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`user_id`)
);
-- ...
```

## Best Practices
- Automate backups using scheduled tasks or cron jobs.
- Store backups securely and test restore procedures regularly.
- Retain backups according to your organization's data retention policy.
