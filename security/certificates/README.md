# SSL/TLS certs, encryption keys

"""
This folder is for storing SSL/TLS certificates used by the Core Banking System.

How to Implement:
- Place your .crt, .key, and .pem files here for HTTPS and secure communication.
- Reference these files in your application configuration (e.g., app/config/settings.yaml).

Schema Example:
- server.crt: Public certificate
- server.key: Private key
- ca_bundle.pem: Certificate authority chain

Sample settings.yaml reference:
ssl:
  certfile: security/certificates/server.crt
  keyfile: security/certificates/server.key
  cafile: security/certificates/ca_bundle.pem
"""
