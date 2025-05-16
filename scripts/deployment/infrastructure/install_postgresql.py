#!/usr/bin/env python
"""
PostgreSQL Installation Helper for Windows

This script helps download and set up PostgreSQL for Windows development environment.
"""

import os
import sys
import tempfile
import urllib.request
import webbrowser
import subprocess
import winreg
import ctypes
from pathlib import Path

# PostgreSQL download URL (version 14.1 for Windows x64)
PG_DOWNLOAD_URL = "https://get.enterprisedb.com/postgresql/postgresql-14.1-1-windows-x64.exe"
DOWNLOAD_FILENAME = "postgresql-14.1-1-windows-x64.exe"

def is_admin():
    """Check if the current process has admin rights."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def download_postgresql():
    """Download PostgreSQL installer."""
    print("Downloading PostgreSQL installer...")
    downloads_dir = str(Path.home() / "Downloads")
    
    # Create downloads directory if it doesn't exist
    os.makedirs(downloads_dir, exist_ok=True)
    
    # Full path for the download
    download_path = os.path.join(downloads_dir, DOWNLOAD_FILENAME)
    
    # Check if the file already exists
    if os.path.exists(download_path):
        print(f"Installer already exists at {download_path}")
        return download_path
    
    try:
        print(f"Downloading from {PG_DOWNLOAD_URL}...")
        # Show a simple progress indicator
        def report_hook(blocknum, blocksize, totalsize):
            readsofar = blocknum * blocksize
            if totalsize > 0:
                percent = readsofar * 1e2 / totalsize
                s = f"\r{percent:5.1f}% ({readsofar / (1024*1024):.1f} MB / {totalsize / (1024*1024):.1f} MB)"
                sys.stderr.write(s)
                if readsofar >= totalsize: 
                    sys.stderr.write("\n")
            else:
                sys.stderr.write(f"Downloaded {readsofar / 1024:.1f} KB\r")
        
        urllib.request.urlretrieve(PG_DOWNLOAD_URL, download_path, report_hook)
        print(f"Downloaded PostgreSQL installer to {download_path}")
        return download_path
    except Exception as e:
        print(f"Error downloading PostgreSQL: {e}")
        return None

def setup_postgresql(installer_path):
    """Set up PostgreSQL with the installer."""
    if not installer_path or not os.path.exists(installer_path):
        print("Error: PostgreSQL installer not found.")
        return False
    
    print("\nPostgreSQL Installation Instructions:")
    print("1. When the installer launches, follow the setup wizard")
    print("2. Use the default installation directory")
    print("3. Choose the components you need (at minimum: server, pgAdmin, command-line tools)")
    print("4. Use 'postgres' as the password for the database superuser")
    print("5. Use the default port (5432)")
    print("6. Choose the default locale")
    
    input("\nPress Enter to launch the installer...")
    
    # Launch the installer
    try:
        if is_admin():
            # Already running as admin, launch directly
            subprocess.Popen([installer_path])
        else:
            # Need to elevate privileges
            ctypes.windll.shell32.ShellExecuteW(None, "runas", installer_path, "", None, 1)
        
        print("\nPlease complete the installation wizard.")
        return True
    except Exception as e:
        print(f"Error launching installer: {e}")
        return False

def configure_path():
    """Configure PATH environment variable to include PostgreSQL bin directory."""
    try:
        # Common PostgreSQL installation paths
        possible_paths = [
            r"C:\Program Files\PostgreSQL\14\bin",
            r"C:\Program Files\PostgreSQL\13\bin",
            r"C:\Program Files\PostgreSQL\12\bin"
        ]
        
        # Find the first path that exists
        pg_bin_path = None
        for path in possible_paths:
            if os.path.exists(path):
                pg_bin_path = path
                break
        
        if not pg_bin_path:
            print("PostgreSQL bin directory not found.")
            print("Please add the PostgreSQL bin directory to your PATH manually.")
            return False
        
        # Check if the path is already in PATH
        env_path = os.environ['PATH']
        if pg_bin_path.lower() in env_path.lower():
            print(f"PostgreSQL bin directory is already in PATH: {pg_bin_path}")
            return True
            
        print(f"Adding PostgreSQL bin directory to PATH: {pg_bin_path}")
        
        # Open a guide on how to add to PATH
        answer = input("Would you like to see instructions on how to add PostgreSQL to your PATH? (y/n): ")
        if answer.lower() == 'y':
            print("\nTo add PostgreSQL to your PATH:")
            print("1. Right-click on 'This PC' or 'My Computer' and select 'Properties'")
            print("2. Click on 'Advanced system settings'")
            print("3. Click the 'Environment Variables' button")
            print("4. In the 'System variables' section, find the 'Path' variable and click 'Edit'")
            print("5. Click 'New' and add the following path:")
            print(f"   {pg_bin_path}")
            print("6. Click 'OK' on all dialogs to save the changes")
            print("7. Restart any open command prompts for the change to take effect")
        
        return True
    except Exception as e:
        print(f"Error configuring PATH: {e}")
        return False

def main():
    """Main function."""
    print("=" * 80)
    print(" PostgreSQL Setup Helper for CBS_PYTHON")
    print("=" * 80)
    
    # Step 1: Download PostgreSQL
    installer_path = download_postgresql()
    
    # Step 2: Run the installer
    if installer_path:
        setup_postgresql(installer_path)
    
    # Step 3: Configure PATH
    configure_path()
    
    print("\nPostgreSQL setup process completed.")
    print("To verify the installation, restart your terminal and run:")
    print("> psql --version")
    
    print("\nTo create a database for development:")
    print("> psql -U postgres")
    print("postgres=# CREATE DATABASE cbs_development;")
    print("postgres=# \\q")

if __name__ == "__main__":
    main()
