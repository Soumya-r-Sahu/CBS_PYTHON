"""
TLS Configuration for Core Banking System

This module provides functions to configure secure TLS settings
for HTTPS and other secure connections.
"""

import ssl
import logging
from typing import Dict, Any

# Configure logger
logger = logging.getLogger(__name__)


def get_secure_ssl_context() -> ssl.SSLContext:
    """
    Create a secure SSL context with modern settings.
    
    Returns:
        ssl.SSLContext: Configured SSL context
    """
    # Create SSL context with strong protocol
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    
    # Set secure cipher suites (TLS 1.3 and strong TLS 1.2 ciphers)
    # These are secure as of 2023, but should be reviewed periodically
    context.set_ciphers(
        'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:'
        'ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:'
        'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256'
    )
    
    # Use server's certificate and private key
    try:
        context.load_cert_chain(
            certfile='security/certificates/server.crt',
            keyfile='security/certificates/server.key'
        )
    except FileNotFoundError:
        logger.error("Certificate files not found. Generate certificates first.")
        raise
    
    # Enforce TLS v1.2 and v1.3 only
    context.options |= (
        ssl.OP_NO_SSLv2 | 
        ssl.OP_NO_SSLv3 |
        ssl.OP_NO_TLSv1 |
        ssl.OP_NO_TLSv1_1
    )
    
    # Enable OCSP stapling (if available in Python version)
    if hasattr(ssl, "VERIFY_OCSP_STAPLED"):
        context.verify_mode = ssl.CERT_REQUIRED
        context.verify_flags = ssl.VERIFY_OCSP_STAPLED
    
    # Verify peer certificate
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    
    return context


def get_flask_ssl_context() -> Dict[str, Any]:
    """
    Get SSL context configuration for Flask application.
    
    Returns:
        Dict[str, Any]: Flask SSL configuration
    """
    return {
        'certfile': 'security/certificates/server.crt',
        'keyfile': 'security/certificates/server.key',
        'ssl_version': ssl.PROTOCOL_TLS_SERVER,
        'ciphers': (
            'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:'
            'ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:'
            'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256'
        )
    }


def configure_ssl_for_database(connection_parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Configure SSL parameters for database connections.
    
    Args:
        connection_parameters (Dict[str, Any]): Existing connection parameters
        
    Returns:
        Dict[str, Any]: Updated connection parameters with SSL settings
    """
    # Create a copy of the connection parameters to avoid modifying the original
    params = connection_parameters.copy()
    
    # Add SSL parameters
    params['ssl_ca'] = 'security/certificates/ca_chain.crt'
    params['ssl_verify_cert'] = True
    
    return params
