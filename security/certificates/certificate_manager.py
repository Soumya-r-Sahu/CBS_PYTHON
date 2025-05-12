"""
Certificate Manager for Core Banking System

This module handles SSL/TLS certificate operations,
including loading, validation, and renewal.
"""

import os
import time
import logging
import datetime
import subprocess
from typing import Dict, Optional, Tuple
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

# Configure logger
logger = logging.getLogger(__name__)

# Certificate paths
CERT_DIR = "security/certificates"
CERT_FILE = os.path.join(CERT_DIR, "server.crt")
KEY_FILE = os.path.join(CERT_DIR, "server.key")
CA_CHAIN_FILE = os.path.join(CERT_DIR, "ca_chain.crt")


def load_certificate() -> Optional[x509.Certificate]:
    """
    Load the server certificate.
    
    Returns:
        Optional[x509.Certificate]: The loaded certificate, or None if it doesn't exist
    """
    try:
        if not os.path.exists(CERT_FILE):
            logger.warning(f"Certificate file not found: {CERT_FILE}")
            return None
        
        with open(CERT_FILE, "rb") as f:
            cert_data = f.read()
            
        cert = x509.load_pem_x509_certificate(
            cert_data,
            default_backend()
        )
        
        return cert
    except Exception as e:
        logger.error(f"Error loading certificate: {str(e)}")
        return None


def check_certificate_expiration() -> Tuple[bool, Optional[datetime.datetime]]:
    """
    Check if the certificate is valid and not about to expire.
    
    Returns:
        Tuple[bool, Optional[datetime.datetime]]: (is_valid, expiration_date)
    """
    cert = load_certificate()
    if not cert:
        return False, None
    
    # Get current time
    now = datetime.datetime.utcnow()
    
    # Get certificate expiration
    expiry = cert.not_valid_after
    
    # Check if cert is valid
    is_valid = now < expiry
    
    # Log warning if certificate is about to expire (in less than 30 days)
    thirty_days = datetime.timedelta(days=30)
    if is_valid and (expiry - now) < thirty_days:
        days_left = (expiry - now).days
        logger.warning(f"Certificate is about to expire in {days_left} days")
    
    return is_valid, expiry


def generate_self_signed_cert(
    common_name: str = "localhost",
    days_valid: int = 365
) -> bool:
    """
    Generate a self-signed certificate.
    
    Args:
        common_name (str): The domain name for the certificate
        days_valid (int): Number of days the certificate should be valid
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create certificates directory if it doesn't exist
        os.makedirs(CERT_DIR, exist_ok=True)
        
        # Generate self-signed certificate using OpenSSL
        cmd = [
            'openssl', 'req', '-x509', '-newkey', 'rsa:4096',
            '-keyout', KEY_FILE,
            '-out', CERT_FILE,
            '-days', str(days_valid),
            '-nodes',  # No password
            '-subj', f'/CN={common_name}'
        ]
        
        subprocess.run(cmd, check=True)
        logger.info(f"Generated self-signed certificate for {common_name} valid for {days_valid} days")
        
        return True
    except Exception as e:
        logger.error(f"Error generating self-signed certificate: {str(e)}")
        return False


def get_certificate_info() -> Dict[str, str]:
    """
    Get information about the current certificate.
    
    Returns:
        Dict[str, str]: Certificate information
    """
    cert = load_certificate()
    if not cert:
        return {"error": "No certificate found"}
    
    try:
        subject = cert.subject
        issuer = cert.issuer
        
        # Extract common name
        subject_cn = subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)[0].value
        issuer_cn = issuer.get_attributes_for_oid(x509.NameOID.COMMON_NAME)[0].value
        
        return {
            "subject": subject_cn,
            "issuer": issuer_cn,
            "valid_from": cert.not_valid_before.strftime("%Y-%m-%d %H:%M:%S"),
            "valid_to": cert.not_valid_after.strftime("%Y-%m-%d %H:%M:%S"),
            "serial_number": format(cert.serial_number, 'x'),
            "is_self_signed": subject_cn == issuer_cn
        }
    except Exception as e:
        logger.error(f"Error getting certificate info: {str(e)}")
        return {"error": str(e)}


def auto_renew_certificate(min_days_left: int = 30) -> bool:
    """
    Auto-renew certificate if it's about to expire.
    
    Args:
        min_days_left (int): Minimum days left before renewal
        
    Returns:
        bool: True if renewed, False otherwise
    """
    is_valid, expiry = check_certificate_expiration()
    
    if not is_valid or not expiry:
        logger.warning("Certificate is invalid or not found, generating new one")
        return generate_self_signed_cert()
    
    # Check if certificate needs to be renewed
    now = datetime.datetime.utcnow()
    days_left = (expiry - now).days
    
    if days_left < min_days_left:
        logger.info(f"Certificate is about to expire in {days_left} days, renewing")
        return generate_self_signed_cert()
    
    logger.info(f"Certificate is still valid for {days_left} days, no need to renew")
    return True


if __name__ == "__main__":
    # Example usage
    print("Certificate Manager Test")
    
    # Check if certificate exists
    cert = load_certificate()
    if cert:
        print("Certificate found")
        info = get_certificate_info()
        for key, value in info.items():
            print(f"{key}: {value}")
    else:
        print("No certificate found")
        
        # Generate a self-signed certificate
        print("Generating self-signed certificate...")
        if generate_self_signed_cert():
            print("Certificate generated successfully")
            
            # Check the new certificate
            cert = load_certificate()
            if cert:
                info = get_certificate_info()
                for key, value in info.items():
                    print(f"{key}: {value}")
        else:
            print("Failed to generate certificate")
