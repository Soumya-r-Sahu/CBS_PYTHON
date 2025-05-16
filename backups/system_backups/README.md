# Core Banking System - Full System Backup Solution

This directory contains scripts to perform comprehensive system backups for the Core Banking System. These scripts handle code files, database, and logs backups with configurable settings and automation options.

## 🚀 Features

- **Complete Backup System**: Code files, MySQL database, and logs
- **Configurable Settings**: Customize backup locations, retention policy, etc.
- **Scheduled Automation**: Set up daily, weekly, or monthly backups
- **Database Utilities**: Full, structure-only, and data-only backups
- **Recovery Tools**: Browse and restore from previous backups
- **Retention Management**: Automatically clean up old backups

## 📂 Structure

- `backup_manager.py` - Main backup utility
- `backup_scheduler.py` - Task scheduling for automated backups
- `db_backup.py` - Database-specific backup utility
- `recovery_manager.py` - Backup restoration tool
- `backup_config.ini` - Configuration settings

## 🛠️ Setup Instructions

1. **Configure Backup Settings**:
   
   Edit `backup_config.ini` to set your preferences:
   
   ```ini
   [Backup]
   # Directory to store backups
   backup_dir = D:\CBS_Backups
   
   # MySQL binary directory 
   mysql_bin_dir = C:\Program Files\MySQL\MySQL Server 8.0\bin
   
   # Other settings...
   ```

2. **Test the Backup Process**:
   
   Run a manual backup:
   
   ```
   python backup_manager.py
   ```

3. **Set Up Automated Backups**:
   
   Schedule daily backups at 2:00 AM:
   
   ```
   python backup_scheduler.py setup --freq DAILY --time 02:00
   ```

## 📚 Usage Guide

### Backup Manager

The `backup_manager.py` script is the main utility for creating backups:

```
python backup_manager.py [options]

Options:
  --config CONFIG    Path to config file
  --backup-dir DIR   Directory to store backups
  --mysql-bin DIR    MySQL bin directory
  --retention DAYS   Retention period in days
  --no-compress      Disable backup compression
  --no-code          Skip code backup
  --no-database      Skip database backup
  --no-logs          Skip logs backup
```

### Backup Scheduler

The `backup_scheduler.py` script sets up automated backups using Windows Task Scheduler:

```
python backup_scheduler.py <command> [options]

Commands:
  setup     Set up scheduled backups
  remove    Remove scheduled backups
  list      List configured backup schedules
  backup    Run a backup manually

Options (for setup):
  --freq {DAILY,WEEKLY,MONTHLY}  Backup frequency
  --time TIME                    Start time (HH:MM)
  --name NAME                    Task name
```

### Database Backup

The `db_backup.py` script provides advanced database backup options:

```
python db_backup.py <command> [options]

Commands:
  backup        Perform database backup
  restore       Restore from backup
  list-tables   List database tables
  list-backups  List available backups

Options (for backup):
  --type {full,structure,data,tables}  Type of backup
  --tables TABLE [TABLE ...]           Tables to backup
  --no-compress                        Disable compression
```

### Recovery Manager

The `recovery_manager.py` script helps restore files from backups:

```
python recovery_manager.py <command> [options]

Commands:
  list          List available backups
  show          Show backup details
  extract       Extract a backup
  restore-db    Restore database
  restore-code  Restore code files
```

## 🔄 Backup Types

1. **Full System Backup**: Code, database, and logs
2. **Code-only Backup**: Just application source code
3. **Database-only Backup**: Just the MySQL database
4. **Structure-only Database Backup**: Schema without data
5. **Data-only Database Backup**: Data without schema

## 🔐 Best Practices

- Store backups on a separate physical drive or network location
- Test restore process regularly to ensure backups are valid
- Use encryption for sensitive data backups 
- Implement off-site backup copies for disaster recovery
- Monitor the backup process and set up alerts for failures

## ⚠️ Troubleshooting

- **Database Backup Fails**: Check MySQL credentials and paths
  - Verify MySQL binary directory in `backup_config.ini`
  - Ensure database user has backup privileges
  
- **Scheduled Backup Not Running**: Check Task Scheduler
  - Open Windows Task Scheduler to check task status
  - Verify user credentials used for the task

- **Restore Process Fails**: Check backup file integrity
  - Try extracting the backup manually
  - Check database connection settings

## 📅 Maintenance Tasks

- Review and purge old backups regularly
- Update MySQL paths after database server updates
- Test recovery scenarios quarterly
