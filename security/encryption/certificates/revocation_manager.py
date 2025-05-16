"""
Certificate Revocation Manager for Core Banking System

This module handles certificate revocation including CRL (Certificate Revocation List)
and OCSP (Online Certificate Status Protocol) operations.
"""

import os
import time
import logging
import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Try to import cryptography modules
try:
    from cryptography import x509
    from cryptography.x509.oid import ExtensionOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.x509.extensions import Extension
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logging.warning("Cryptography module not available. Limited certificate functionality.")

# Import configuration
from security.config import CERTIFICATE_CONFIG

# Configure logger
logger = logging.getLogger(__name__)


class RevocationManager:
    """Manager for certificate revocation operations"""
    
    def __init__(self, crl_dir: Optional[str] = None):
        """
        Initialize the revocation manager
        
        Args:
            crl_dir (str, optional): Directory to store CRL files
        """
        # Set CRL directory
        if crl_dir:
            self.crl_dir = Path(crl_dir)
        else:
            base_dir = Path(CERTIFICATE_CONFIG["cert_dir"]).parent
            self.crl_dir = base_dir / "crl"
        
        # Create CRL directory if it doesn't exist
        os.makedirs(self.crl_dir, exist_ok=True)
        
        # Initialize revoked certificates storage
        self.revoked_certs = {}
        self.crl_file = self.crl_dir / "revoked.crl"
        
        # Load existing revoked certificates
        self._load_revoked_certs()
    
    def _load_revoked_certs(self):
        """Load revoked certificates from storage"""
        if not CRYPTO_AVAILABLE:
            logger.warning("Cannot load CRL without cryptography module")
            return
        
        if not self.crl_file.exists():
            logger.info(f"No existing CRL file at {self.crl_file}")
            return
        
        try:
            with open(self.crl_file, "rb") as f:
                crl_data = f.read()
                
            crl = x509.load_der_x509_crl(crl_data)
            
            # Extract revoked certificates
            for revoked_cert in crl:
                serial = revoked_cert.serial_number
                reason = None
                
                # Try to get revocation reason
                for extension in revoked_cert.extensions:
                    if extension.oid == ExtensionOID.CRL_REASON:
                        reason = extension.value.reason.name
                        break
                
                self.revoked_certs[serial] = {
                    "serial": str(serial),
                    "revocation_date": revoked_cert.revocation_date,
                    "reason": reason
                }
            
            logger.info(f"Loaded {len(self.revoked_certs)} revoked certificates from CRL")
        
        except Exception as e:
            logger.error(f"Error loading CRL: {str(e)}")
            self.revoked_certs = {}
    
    def revoke_certificate(
        self,
        cert_path: str,
        reason: str = "unspecified",
        ca_cert_path: Optional[str] = None,
        ca_key_path: Optional[str] = None
    ) -> bool:
        """
        Revoke a certificate and update the CRL
        
        Args:
            cert_path (str): Path to the certificate to revoke
            reason (str): Revocation reason
            ca_cert_path (str, optional): Path to the CA certificate
            ca_key_path (str, optional): Path to the CA private key
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not CRYPTO_AVAILABLE:
            logger.error("Cannot revoke certificate without cryptography module")
            return False
        
        try:
            # Load certificate to revoke
            with open(cert_path, "rb") as f:
                cert_data = f.read()
                cert = x509.load_pem_x509_certificate(cert_data)
            
            # Add to revoked certificates list
            serial = cert.serial_number
            revocation_date = datetime.datetime.utcnow()
            
            self.revoked_certs[serial] = {
                "serial": str(serial),
                "revocation_date": revocation_date,
                "reason": reason
            }
            
            # Update CRL if CA certificate and key are provided
            if ca_cert_path and ca_key_path:
                self._generate_crl(ca_cert_path, ca_key_path)
            
            logger.info(f"Certificate {cert.subject} revoked. Reason: {reason}")
            return True
        
        except Exception as e:
            logger.error(f"Error revoking certificate: {str(e)}")
            return False
    
    def _generate_crl(self, ca_cert_path: str, ca_key_path: str) -> bool:
        """
        Generate a Certificate Revocation List
        
        Args:
            ca_cert_path (str): Path to the CA certificate
            ca_key_path (str): Path to the CA private key
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not CRYPTO_AVAILABLE:
            logger.error("Cannot generate CRL without cryptography module")
            return False
        
        try:
            # Load CA certificate
            with open(ca_cert_path, "rb") as f:
                ca_cert_data = f.read()
                ca_cert = x509.load_pem_x509_certificate(ca_cert_data)
            
            # Load CA private key
            with open(ca_key_path, "rb") as f:
                ca_key_data = f.read()
                ca_key = serialization.load_pem_private_key(
                    ca_key_data,
                    password=None
                )
            
            # Prepare builder
            builder = x509.CertificateRevocationListBuilder()
            
            # Set issuer
            builder = builder.issuer_name(ca_cert.subject)
            
            # Set this update and next update times
            now = datetime.datetime.utcnow()
            next_update = now + datetime.timedelta(days=30)  # Update CRL monthly
            builder = builder.last_update(now)
            builder = builder.next_update(next_update)
            
            # Add all revoked certificates
            for serial, details in self.revoked_certs.items():
                revoked_cert_builder = x509.RevokedCertificateBuilder()
                revoked_cert_builder = revoked_cert_builder.serial_number(serial)
                revoked_cert_builder = revoked_cert_builder.revocation_date(
                    details["revocation_date"]
                )
                
                # Add reason extension if available
                if details["reason"]:
                    # Convert string reason to enum
                    try:
                        reason_enum = getattr(
                            x509.ReasonFlags,
                            details["reason"].upper(),
                            x509.ReasonFlags.unspecified
                        )
                        
                        extension = x509.CRLReason(reason_enum)
                        revoked_cert_builder = revoked_cert_builder.add_extension(
                            extension, critical=False
                        )
                    except Exception as e:
                        logger.warning(f"Failed to add reason extension: {str(e)}")
                
                builder = builder.add_revoked_certificate(revoked_cert_builder.build())
            
            # Sign the CRL
            crl = builder.sign(
                private_key=ca_key,
                algorithm=hashes.SHA256()
            )
            
            # Save CRL
            with open(self.crl_file, "wb") as f:
                f.write(crl.public_bytes(serialization.Encoding.DER))
            
            logger.info(f"Generated CRL with {len(self.revoked_certs)} revoked certificates")
            return True
        
        except Exception as e:
            logger.error(f"Error generating CRL: {str(e)}")
            return False
    
    def is_certificate_revoked(self, cert_path: str) -> Tuple[bool, Optional[Dict]]:
        """
        Check if a certificate is revoked
        
        Args:
            cert_path (str): Path to the certificate to check
            
        Returns:
            Tuple[bool, Optional[Dict]]: (is_revoked, revocation_details)
        """
        if not CRYPTO_AVAILABLE:
            logger.error("Cannot check certificate revocation without cryptography module")
            return False, None
        
        try:
            # Load certificate
            with open(cert_path, "rb") as f:
                cert_data = f.read()
                cert = x509.load_pem_x509_certificate(cert_data)
            
            serial = cert.serial_number
            
            # Check if certificate is in revoked list
            if serial in self.revoked_certs:
                return True, self.revoked_certs[serial]
            
            return False, None
        
        except Exception as e:
            logger.error(f"Error checking certificate revocation: {str(e)}")
            return False, None
    
    def get_revoked_certificates(self) -> List[Dict]:
        """
        Get list of all revoked certificates
        
        Returns:
            List[Dict]: List of revoked certificate details
        """
        return list(self.revoked_certs.values())


# Create a singleton RevocationManager instance
revocation_manager = RevocationManager()

# Export main functions for easy access
revoke_certificate = revocation_manager.revoke_certificate
is_certificate_revoked = revocation_manager.is_certificate_revoked
get_revoked_certificates = revocation_manager.get_revoked_certificates
