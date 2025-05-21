"""
Admin Console for Core Banking System

This module provides a command-line interface for system administration.
It allows administrators to manage the system, monitor performance,
and run administrative tasks through a terminal interface.

Tags: admin, console, cli, system_management
AI-Metadata:
    component_type: admin_console
    criticality: high
    purpose: system_administration
    versioning: semantic
"""

import cmd
import os
import sys
import logging
import datetime
import json
from typing import Dict, List, Any, Optional, Union

# Import the admin dashboard
from admin_panel.admin_dashboard import AdminDashboard

# Configure logger
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdminConsole(cmd.Cmd):
    """
    Interactive console for CBS_PYTHON system administration.
    
    This class provides a command-line interface for administrators to
    interact with the system, check statuses, and perform administrative tasks.
    
    Features:
    - Module management (activate/deactivate)
    - System monitoring and health checks
    - User management
    - Configuration updates
    - Database maintenance
    - Log viewing and management
    
    AI-Metadata:
        purpose: provide administrative command interface
        criticality: high
        error_handling: comprehensive
        last_reviewed: 2025-05-20
    """
    
    intro = '''
    ========================================================
     CBS_PYTHON Core Banking System - Admin Console v1.1.2
    ========================================================
    
    Type 'help' or '?' to list commands.
    Type 'exit' or 'quit' to exit the console.
    '''
    
    prompt = 'CBS_ADMIN> '
    
    def __init__(self):
        """Initialize the admin console with required components"""
        super().__init__()
        self.admin_dashboard = AdminDashboard()
        self.current_directory = os.getcwd()
        self.last_command_time = datetime.datetime.now()
        logger.info("Admin console initialized")

    def do_status(self, arg):
        """
        Display system status information
        
        Usage: status [component]
        
        Examples:
          status            - Show overall system status
          status modules    - Show status of all modules
          status database   - Show database status
          status security   - Show security status
        """
        components = arg.strip().lower() if arg else "all"
        
        if components in ["all", ""]:
            print("\n=== System Status ===")
            print(f"System uptime: {self._get_uptime()}")
            self._print_modules_status()
            self._print_system_info()
            
        elif components == "modules":
            self._print_modules_status()
            
        elif components == "database":
            print("\n=== Database Status ===")
            db_status = self.admin_dashboard.get_database_status() if hasattr(self.admin_dashboard, 'get_database_status') else {"status": "Unknown"}
            self._print_dict_as_table(db_status)
            
        elif components == "security":
            print("\n=== Security Status ===")
            security_status = self.admin_dashboard.get_security_status() if hasattr(self.admin_dashboard, 'get_security_status') else {"status": "Unknown"}
            self._print_dict_as_table(security_status)
            
        else:
            print(f"Unknown component: {components}")
            print("Available components: all, modules, database, security")
    
    def do_module(self, arg):
        """
        Manage system modules
        
        Usage: module <command> [module_name]
        
        Commands:
          list              - List all available modules
          status [name]     - Show status of module
          activate <name>   - Activate a module
          deactivate <name> - Deactivate a module
          reload <name>     - Reload a module
        
        Examples:
          module list
          module status core_banking
          module activate payments
          module deactivate digital_channels
          module reload risk_compliance
        """
        args = arg.strip().split()
        if not args:
            print("Error: No command specified")
            print("Use 'help module' for usage information")
            return
            
        command = args[0].lower()
        module_name = args[1] if len(args) > 1 else None
        
        if command == "list":
            self._list_modules()
        elif command == "status":
            self._show_module_status(module_name)
        elif command == "activate":
            if not module_name:
                print("Error: Module name required")
                return
            self._activate_module(module_name)
        elif command == "deactivate":
            if not module_name:
                print("Error: Module name required")
                return
            self._deactivate_module(module_name)
        elif command == "reload":
            if not module_name:
                print("Error: Module name required")
                return
            self._reload_module(module_name)
        else:
            print(f"Unknown command: {command}")
            print("Use 'help module' for usage information")
    
    def do_user(self, arg):
        """
        Manage system users
        
        Usage: user <command> [username] [options]
        
        Commands:
          list              - List all users
          add <username>    - Add a new user
          delete <username> - Delete a user
          lock <username>   - Lock a user account
          unlock <username> - Unlock a user account
          roles <username>  - Show user roles
          
        Examples:
          user list
          user add john_doe
          user delete jane_smith
          user lock inactive_user
          user unlock john_doe
          user roles admin_user
        """
        args = arg.strip().split()
        if not args:
            print("Error: No command specified")
            print("Use 'help user' for usage information")
            return
            
        command = args[0].lower()
        username = args[1] if len(args) > 1 else None
        
        if command == "list":
            self._list_users()
        elif command == "add":
            if not username:
                print("Error: Username required")
                return
            self._add_user(username)
        elif command == "delete":
            if not username:
                print("Error: Username required")
                return
            self._delete_user(username)
        elif command == "lock":
            if not username:
                print("Error: Username required")
                return
            self._lock_user(username)
        elif command == "unlock":
            if not username:
                print("Error: Username required")
                return
            self._unlock_user(username)
        elif command == "roles":
            if not username:
                print("Error: Username required")
                return
            self._show_user_roles(username)
        else:
            print(f"Unknown command: {command}")
            print("Use 'help user' for usage information")
    
    def do_config(self, arg):
        """
        Manage system configuration
        
        Usage: config <command> [section] [key] [value]
        
        Commands:
          list [section]          - List configuration (all or specific section)
          get <section> <key>     - Get specific configuration value
          set <section> <key> <value> - Set configuration value
          reload                  - Reload configuration from files
          save                    - Save current configuration to files
          
        Examples:
          config list
          config list database
          config get database host
          config set database host localhost
          config reload
          config save
        """
        args = arg.strip().split()
        if not args:
            print("Error: No command specified")
            print("Use 'help config' for usage information")
            return
            
        command = args[0].lower()
        
        if command == "list":
            section = args[1] if len(args) > 1 else None
            self._list_config(section)
        elif command == "get":
            if len(args) < 3:
                print("Error: Section and key required")
                return
            section, key = args[1], args[2]
            self._get_config(section, key)
        elif command == "set":
            if len(args) < 4:
                print("Error: Section, key and value required")
                return
            section, key, value = args[1], args[2], args[3]
            self._set_config(section, key, value)
        elif command == "reload":
            self._reload_config()
        elif command == "save":
            self._save_config()
        else:
            print(f"Unknown command: {command}")
            print("Use 'help config' for usage information")
    
    def do_log(self, arg):
        """
        View and manage system logs
        
        Usage: log <command> [options]
        
        Commands:
          view [lines] [level]    - View last N lines of logs at specified level
          search <pattern>        - Search logs for pattern
          clear                   - Clear log display (not log files)
          rotate                  - Rotate log files
          
        Examples:
          log view 20 error       - View last 20 error logs
          log view 50             - View last 50 logs (all levels)
          log search "database error"
          log clear
          log rotate
        """
        args = arg.strip().split()
        if not args:
            print("Error: No command specified")
            print("Use 'help log' for usage information")
            return
            
        command = args[0].lower()
        
        if command == "view":
            lines = int(args[1]) if len(args) > 1 and args[1].isdigit() else 10
            level = args[2].upper() if len(args) > 2 else None
            self._view_logs(lines, level)
        elif command == "search":
            if len(args) < 2:
                print("Error: Search pattern required")
                return
            pattern = " ".join(args[1:])
            self._search_logs(pattern)
        elif command == "clear":
            self._clear_logs()
        elif command == "rotate":
            self._rotate_logs()
        else:
            print(f"Unknown command: {command}")
            print("Use 'help log' for usage information")
    
    def do_health(self, arg):
        """
        Check system health
        
        Usage: health [component]
        
        Examples:
          health                - Check overall system health
          health database       - Check database health
          health modules        - Check all modules health
          health core_banking   - Check core_banking module health
        """
        component = arg.strip().lower() if arg else "all"
        
        if component in ["all", ""]:
            print("\n=== System Health Check ===")
            self._check_overall_health()
        elif component == "database":
            print("\n=== Database Health Check ===")
            self._check_database_health()
        elif component == "modules":
            print("\n=== Modules Health Check ===")
            self._check_all_modules_health()
        else:
            print(f"\n=== {component.title()} Module Health Check ===")
            self._check_specific_module_health(component)
    
    def do_backup(self, arg):
        """
        Manage system backups
        
        Usage: backup <command> [options]
        
        Commands:
          list              - List available backups
          create [name]     - Create a new backup
          restore <name>    - Restore from a backup
          delete <name>     - Delete a backup
          
        Examples:
          backup list
          backup create pre_upgrade_backup
          backup restore daily_backup_20250520
          backup delete old_backup
        """
        args = arg.strip().split()
        if not args:
            print("Error: No command specified")
            print("Use 'help backup' for usage information")
            return
            
        command = args[0].lower()
        name = args[1] if len(args) > 1 else None
        
        if command == "list":
            self._list_backups()
        elif command == "create":
            backup_name = name if name else f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self._create_backup(backup_name)
        elif command == "restore":
            if not name:
                print("Error: Backup name required")
                return
            self._restore_backup(name)
        elif command == "delete":
            if not name:
                print("Error: Backup name required")
                return
            self._delete_backup(name)
        else:
            print(f"Unknown command: {command}")
            print("Use 'help backup' for usage information")
    
    def do_exit(self, arg):
        """Exit the admin console"""
        print("Exiting admin console...")
        logger.info("Admin console terminated")
        return True
        
    def do_quit(self, arg):
        """Exit the admin console"""
        return self.do_exit(arg)
        
    def do_clear(self, arg):
        """Clear the console screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def do_pwd(self, arg):
        """Print current working directory"""
        print(os.getcwd())
    
    def do_version(self, arg):
        """Show system version information"""
        print("\n=== CBS_PYTHON Version Information ===")
        print("Core System Version: 1.1.2")
        print("Admin Console Version: 1.0.0")
        print("Release Date: May 20, 2025")
        print("Python Version:", sys.version)
    
    def emptyline(self):
        """Do nothing on empty line"""
        pass
    
    def default(self, line):
        """Handle unknown commands"""
        print(f"Unknown command: {line}")
        print("Type 'help' or '?' to list available commands")
    
    # Helper methods
    
    def _get_uptime(self) -> str:
        """Get system uptime"""
        uptime = datetime.datetime.now() - self.admin_dashboard.start_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds"
    
    def _print_modules_status(self):
        """Print the status of all modules"""
        print("\n=== Modules Status ===")
        module_status = self.admin_dashboard.get_modules_status() if hasattr(self.admin_dashboard, 'get_modules_status') else self.admin_dashboard.modules_status
        self._print_dict_as_table(module_status)
    
    def _print_system_info(self):
        """Print system information"""
        print("\n=== System Information ===")
        system_info = self.admin_dashboard.system_info
        self._print_dict_as_table(system_info)
    
    def _print_dict_as_table(self, data: Dict[str, Any]):
        """Print dictionary as formatted table"""
        if not data:
            print("No data available")
            return
            
        # Find the longest key for formatting
        max_key_length = max(len(str(key)) for key in data.keys())
        
        # Print each key-value pair
        for key, value in data.items():
            # Format nested dictionaries
            if isinstance(value, dict):
                print(f"{str(key):{max_key_length}} : ")
                for sub_key, sub_value in value.items():
                    print(f"  {sub_key}: {sub_value}")
            # Format lists
            elif isinstance(value, list):
                print(f"{str(key):{max_key_length}} : {', '.join(str(item) for item in value)}")
            # Format everything else
            else:
                print(f"{str(key):{max_key_length}} : {value}")
    
    def _list_modules(self):
        """List all available modules"""
        print("\n=== Available Modules ===")
        # This would be implemented to list modules from the system
        modules = self.admin_dashboard.get_available_modules() if hasattr(self.admin_dashboard, 'get_available_modules') else [
            "core_banking", "payments", "digital_channels", 
            "risk_compliance", "security", "crm"
        ]
        
        for module in modules:
            print(f"- {module}")
    
    def _show_module_status(self, module_name):
        """Show status of a specific module"""
        if not module_name:
            print("Showing status for all modules:")
            self._print_modules_status()
            return
            
        print(f"\n=== {module_name} Module Status ===")
        # This would be implemented to show specific module status
        module_status = self.admin_dashboard.get_module_status(module_name) if hasattr(self.admin_dashboard, 'get_module_status') else {"status": "Unknown"}
        self._print_dict_as_table(module_status)
    
    def _activate_module(self, module_name):
        """Activate a module"""
        print(f"Activating module: {module_name}")
        # This would be implemented to activate the module
        success = self.admin_dashboard.activate_module(module_name) if hasattr(self.admin_dashboard, 'activate_module') else False
        
        if success:
            print(f"Module {module_name} activated successfully")
        else:
            print(f"Failed to activate module {module_name}")
    
    def _deactivate_module(self, module_name):
        """Deactivate a module"""
        print(f"Deactivating module: {module_name}")
        # This would be implemented to deactivate the module
        success = self.admin_dashboard.deactivate_module(module_name) if hasattr(self.admin_dashboard, 'deactivate_module') else False
        
        if success:
            print(f"Module {module_name} deactivated successfully")
        else:
            print(f"Failed to deactivate module {module_name}")
    
    def _reload_module(self, module_name):
        """Reload a module"""
        print(f"Reloading module: {module_name}")
        # This would be implemented to reload the module
        success = self.admin_dashboard.reload_module(module_name) if hasattr(self.admin_dashboard, 'reload_module') else False
        
        if success:
            print(f"Module {module_name} reloaded successfully")
        else:
            print(f"Failed to reload module {module_name}")
    
    def _list_users(self):
        """List all system users"""
        print("\n=== System Users ===")
        # This would be implemented to list system users
        users = self.admin_dashboard.get_users() if hasattr(self.admin_dashboard, 'get_users') else [
            {"username": "admin", "role": "administrator", "status": "active"},
            {"username": "operator", "role": "operator", "status": "active"},
            {"username": "auditor", "role": "auditor", "status": "inactive"}
        ]
        
        # Print user information
        print(f"{'Username':<15} {'Role':<15} {'Status':<10}")
        print("-" * 40)
        for user in users:
            print(f"{user['username']:<15} {user['role']:<15} {user['status']:<10}")
    
    # Additional methods would be implemented for other commands
    def _add_user(self, username):
        """Add a new user"""
        print(f"Adding user: {username}")
        # Mock implementation
        print(f"User {username} added successfully")
    
    def _delete_user(self, username):
        """Delete a user"""
        print(f"Deleting user: {username}")
        # Mock implementation
        print(f"User {username} deleted successfully")
    
    def _lock_user(self, username):
        """Lock a user account"""
        print(f"Locking user account: {username}")
        # Mock implementation
        print(f"User account {username} locked successfully")
    
    def _unlock_user(self, username):
        """Unlock a user account"""
        print(f"Unlocking user account: {username}")
        # Mock implementation
        print(f"User account {username} unlocked successfully")
    
    def _show_user_roles(self, username):
        """Show user roles"""
        print(f"\n=== Roles for User {username} ===")
        # Mock implementation
        roles = ["operator", "reports_viewer"]
        for role in roles:
            print(f"- {role}")
    
    def _list_config(self, section=None):
        """List configuration settings"""
        if section:
            print(f"\n=== Configuration for {section} ===")
        else:
            print("\n=== System Configuration ===")
        
        # Mock implementation
        config = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "user": "db_user"
            },
            "security": {
                "login_attempts": 3,
                "session_timeout": 30
            }
        }
        
        if section:
            if section in config:
                self._print_dict_as_table(config[section])
            else:
                print(f"Section {section} not found in configuration")
        else:
            for section_name, section_config in config.items():
                print(f"\n[{section_name}]")
                self._print_dict_as_table(section_config)
    
    def _get_config(self, section, key):
        """Get a specific configuration value"""
        print(f"Getting config: {section}.{key}")
        # Mock implementation
        value = "config_value"
        print(f"{section}.{key} = {value}")
    
    def _set_config(self, section, key, value):
        """Set a configuration value"""
        print(f"Setting config: {section}.{key} = {value}")
        # Mock implementation
        print(f"Configuration updated: {section}.{key} = {value}")
    
    def _reload_config(self):
        """Reload configuration from files"""
        print("Reloading configuration from files...")
        # Mock implementation
        print("Configuration reloaded successfully")
    
    def _save_config(self):
        """Save configuration to files"""
        print("Saving configuration to files...")
        # Mock implementation
        print("Configuration saved successfully")
    
    def _view_logs(self, lines, level):
        """View system logs"""
        level_str = f" at {level} level" if level else ""
        print(f"\n=== Last {lines} Log Entries{level_str} ===")
        # Mock implementation
        print("2025-05-20 10:15:30 INFO     System started successfully")
        print("2025-05-20 10:15:35 INFO     Database connection established")
        print("2025-05-20 10:15:40 WARNING  Slow query detected in core_banking module")
    
    def _search_logs(self, pattern):
        """Search logs for pattern"""
        print(f"\n=== Logs Matching '{pattern}' ===")
        # Mock implementation
        print("2025-05-20 10:15:40 WARNING  Slow query detected in core_banking module")
    
    def _clear_logs(self):
        """Clear log display"""
        print("Clearing log display...")
        # In a real implementation, this would clear the display, not the actual logs
        self.do_clear("")
    
    def _rotate_logs(self):
        """Rotate log files"""
        print("Rotating log files...")
        # Mock implementation
        print("Log rotation initiated successfully")
    
    def _check_overall_health(self):
        """Check overall system health"""
        print("Checking overall system health...")
        # Mock implementation
        health_checks = [
            ("Database Connection", "OK"),
            ("Module Registration", "OK"),
            ("Security Services", "OK"),
            ("File System Access", "OK"),
            ("Memory Usage", "Normal (45%)"),
            ("CPU Usage", "Normal (30%)")
        ]
        
        for check, status in health_checks:
            print(f"{check:.<30} {status}")
    
    def _check_database_health(self):
        """Check database health"""
        print("Checking database health...")
        # Mock implementation
        health_checks = [
            ("Connection Pool", "OK (8/10 connections)"),
            ("Response Time", "Normal (15ms)"),
            ("Disk Space", "OK (65% used)"),
            ("Replication Lag", "None"),
            ("Backup Status", "Latest backup: 2025-05-20 03:00 AM")
        ]
        
        for check, status in health_checks:
            print(f"{check:.<30} {status}")
    
    def _check_all_modules_health(self):
        """Check health of all modules"""
        print("Checking all modules health...")
        # Mock implementation
        modules = ["core_banking", "payments", "digital_channels", "risk_compliance", "security"]
        
        for module in modules:
            status = "Healthy" if module != "payments" else "Degraded"
            print(f"{module:.<20} {status}")
            
        print("\nDetails for degraded modules:")
        print("payments: Transaction processor responding slowly (150ms)")
    
    def _check_specific_module_health(self, module):
        """Check health of a specific module"""
        print(f"Checking {module} module health...")
        # Mock implementation
        health_checks = [
            ("Service Registration", "OK"),
            ("Dependencies", "All Available"),
            ("API Endpoints", "Responding"),
            ("Error Rate", "Normal (<0.1%)")
        ]
        
        for check, status in health_checks:
            print(f"{check:.<30} {status}")
    
    def _list_backups(self):
        """List available backups"""
        print("\n=== Available Backups ===")
        # Mock implementation
        backups = [
            {"name": "daily_backup_20250520", "date": "2025-05-20 03:00:00", "size": "256 MB", "type": "Full"},
            {"name": "weekly_backup_20250518", "date": "2025-05-18 02:00:00", "size": "512 MB", "type": "Full"},
            {"name": "pre_upgrade_backup", "date": "2025-05-15 18:30:00", "size": "498 MB", "type": "Full"}
        ]
        
        print(f"{'Name':<25} {'Date':<20} {'Size':<10} {'Type':<10}")
        print("-" * 65)
        for backup in backups:
            print(f"{backup['name']:<25} {backup['date']:<20} {backup['size']:<10} {backup['type']:<10}")
    
    def _create_backup(self, name):
        """Create a new backup"""
        print(f"Creating backup: {name}")
        # Mock implementation
        print(f"Backup {name} created successfully")
    
    def _restore_backup(self, name):
        """Restore from a backup"""
        print(f"Restoring from backup: {name}")
        print("WARNING: This will replace current data. Are you sure? (yes/no)")
        confirmation = input()
        if confirmation.lower() == "yes":
            # Mock implementation
            print(f"Restored from backup {name} successfully")
        else:
            print("Restore operation cancelled")
    
    def _delete_backup(self, name):
        """Delete a backup"""
        print(f"Deleting backup: {name}")
        print("Are you sure? (yes/no)")
        confirmation = input()
        if confirmation.lower() == "yes":
            # Mock implementation
            print(f"Backup {name} deleted successfully")
        else:
            print("Delete operation cancelled")

def main():
    """Main function to run the admin console"""
    console = AdminConsole()
    try:
        console.cmdloop()
    except KeyboardInterrupt:
        print("\nExiting due to keyboard interrupt...")
    except Exception as e:
        logger.error(f"Error in admin console: {str(e)}")
        print(f"An error occurred: {str(e)}")
        print("Check the logs for more details.")

if __name__ == "__main__":
    main()
