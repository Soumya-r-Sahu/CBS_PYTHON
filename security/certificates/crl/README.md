# Certificate Revocation Lists (CRLs)

This directory contains Certificate Revocation Lists (CRLs) used to track
revoked certificates in the Core Banking System.

## Contents

- `revoked.crl`: Main CRL file containing all revoked certificates

## Security Notes

- CRLs should be regularly updated and published
- CRL verification should be part of the TLS handshake process
- Consider implementing OCSP (Online Certificate Status Protocol) for real-time validation
