# Encryption Security

This directory contains components for data encryption and certificate management.

## Components

- `encryption.py` - Core encryption utilities using AES-256-CBC
- `certificates/` - SSL/TLS certificate management
  - `certificate_manager.py` - Certificate operations and lifecycle management
  - `tls_config.py` - TLS security settings and cipher configurations
  - `revocation_manager.py` - Certificate revocation management
  - `certs/` - Certificate storage
  - `private/` - Private key storage (sensitive)
  - `crl/` - Certificate revocation lists
  - `csr/` - Certificate signing requests

## Usage

```python
# Basic encryption
from security.encryption.encryption import encrypt_data, decrypt_data

# Certificate management
from security.encryption.certificates.certificate_manager import get_certificate, create_self_signed_cert

# Example encryption
encrypted_data = encrypt_data("sensitive information", encryption_key)
decrypted_data = decrypt_data(encrypted_data, encryption_key)
```

## Best Practices

1. Use strong encryption algorithms (AES-256-CBC or better)
2. Secure storage of encryption keys
3. Implement proper key rotation policies
4. Regularly update and maintain certificates
5. Support for secure cipher suites in TLS configurations
