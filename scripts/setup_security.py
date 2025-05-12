"""
Setup script for installing security-related dependencies for the Core Banking System.
"""

import os
import sys
import subprocess
import argparse

# Define required packages for security features
BASIC_PACKAGES = [
    "cryptography>=39.0.0",  # For encryption
    "pyjwt>=2.6.0",         # For JWT tokens
    "flask-limiter>=3.3.0",  # For rate limiting
    "bcrypt>=4.0.1",        # For password hashing
]

MFA_PACKAGES = [
    "pyotp>=2.8.0",         # For TOTP-based MFA
    "qrcode>=7.4.2",        # For QR code generation
    "pillow>=9.5.0",        # Required by qrcode
]

ADVANCED_PACKAGES = [
    "argon2-cffi>=21.3.0",  # For more secure password hashing
    "flask-talisman>=1.0.0", # For security headers
    "bleach>=6.0.0",        # For HTML sanitization
]


def install_packages(packages, upgrade=False):
    """
    Install Python packages using pip
    
    Args:
        packages (list): List of packages to install
        upgrade (bool): Whether to upgrade existing packages
    """
    cmd = [sys.executable, "-m", "pip", "install"]
    
    if upgrade:
        cmd.append("--upgrade")
    
    cmd.extend(packages)
    
    print(f"Installing packages: {', '.join(packages)}")
    subprocess.check_call(cmd)


def main():
    """Main function to install security dependencies"""
    parser = argparse.ArgumentParser(description="Install security dependencies for Core Banking System")
    parser.add_argument("--all", action="store_true", help="Install all security packages")
    parser.add_argument("--basic", action="store_true", help="Install only basic security packages")
    parser.add_argument("--mfa", action="store_true", help="Install MFA-related packages")
    parser.add_argument("--advanced", action="store_true", help="Install advanced security packages")
    parser.add_argument("--upgrade", action="store_true", help="Upgrade existing packages")
    
    args = parser.parse_args()
    
    # If no arguments provided, install basic packages
    if not (args.all or args.basic or args.mfa or args.advanced):
        args.basic = True
    
    # Install selected package groups
    if args.all or args.basic:
        install_packages(BASIC_PACKAGES, args.upgrade)
    
    if args.all or args.mfa:
        install_packages(MFA_PACKAGES, args.upgrade)
    
    if args.all or args.advanced:
        install_packages(ADVANCED_PACKAGES, args.upgrade)
    
    print("\nSecurity dependencies installed successfully!")
    
    # Check if environment variables are set
    if not os.environ.get("JWT_SECRET_KEY") and (args.all or args.basic):
        print("\nWARNING: JWT_SECRET_KEY environment variable not set.")
        print("For production use, set a secure JWT secret key:")
        print("  - Windows: $env:JWT_SECRET_KEY = 'your-secure-secret-key'")
        print("  - Linux/macOS: export JWT_SECRET_KEY='your-secure-secret-key'")
    
    print("\nRecommended security settings:")
    print("1. Set CBS_ENVIRONMENT to 'production' for production deployments")
    print("2. Configure password policy in security/config.py")
    print("3. Set up regular certificate rotation")
    print("4. Configure audit logging")


if __name__ == "__main__":
    main()
