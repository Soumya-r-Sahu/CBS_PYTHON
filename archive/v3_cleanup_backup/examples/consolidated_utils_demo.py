"""
Example script showing how to use the consolidated utilities.

This script demonstrates how to use the common utilities and the benefits of
centralizing duplicated functions.
"""

from utils import (
    # Common ID formatters
    generate_reference_id,
    mask_account_number,
    mask_mobile_number,
    format_ifsc_code,
    sanitize_account_number,
    standardize_mobile_number,
    
    # Common validators
    validate_upi_id,
    validate_mobile_number,
    validate_account_number,
    
    # Payment utilities
    generate_neft_reference,
    generate_rtgs_reference,
    generate_imps_reference,
    generate_upi_reference,
    generate_purpose_code_description,
    
    # Encryption utilities
    encrypt_data,
    decrypt_data
)
from payments.upi.utils.qr_code_generator import (
    QRCodeGenerator,
    generate_upi_transaction_reference,
    mask_upi_id
)

def demonstrate_common_utilities():
    """Demonstrate the use of common utilities."""
    print("=== Common Utilities Demo ===")
    
    # Account formatting and masking
    account_number = "1234-5678-9012-34"
    sanitized_account = sanitize_account_number(account_number)
    masked_account = mask_account_number(account_number)
    print(f"Original account: {account_number}")
    print(f"Sanitized account: {sanitized_account}")
    print(f"Masked account:   {masked_account}")
    
    # Mobile formatting and masking
    mobile_number = "+91 9876-543210"
    standardized_mobile = standardize_mobile_number(mobile_number)
    masked_mobile = mask_mobile_number(mobile_number)
    print(f"Original mobile: {mobile_number}")
    print(f"Standardized mobile: {standardized_mobile}")
    print(f"Masked mobile:   {masked_mobile}")
    
    # IFSC code formatting
    ifsc_code = "SBIN 0001234"
    formatted_ifsc = format_ifsc_code(ifsc_code)
    print(f"Original IFSC: {ifsc_code}")
    print(f"Formatted IFSC: {formatted_ifsc}")
    
    # UPI ID masking
    upi_id = "myusername@okbank"
    masked_upi = mask_upi_id(upi_id)
    print(f"Original UPI ID: {upi_id}")
    print(f"Masked UPI ID: {masked_upi}")
    
    # Validation
    print("\n=== Validation Demo ===")
    upi_id = "user@okbank"
    valid_upi, message = validate_upi_id(upi_id)
    print(f"UPI ID '{upi_id}' valid: {valid_upi}")
    
    account = "12345678901234"
    valid_account, message = validate_account_number(account)
    print(f"Account '{account}' valid: {valid_account}")
    
    mobile = "9876543210"
    valid_mobile, message = validate_mobile_number(mobile)
    print(f"Mobile '{mobile}' valid: {valid_mobile}")
    
    # Reference ID generation
    print("\n=== Reference ID Generation Demo ===")
    neft_ref = generate_neft_reference("12345678901234", 1000.0)
    rtgs_ref = generate_rtgs_reference("12345678901234", 5000.0)
    imps_ref = generate_imps_reference("9876543210", "12345678901234", 500.0)
    upi_ref = generate_upi_reference("user@okbank", 200.0)
    
    print(f"NEFT Reference: {neft_ref}")
    print(f"RTGS Reference: {rtgs_ref}")
    print(f"IMPS Reference: {imps_ref}")
    print(f"UPI Reference:  {upi_ref}")
    
    # RTGS purpose codes
    purpose_code = "CORT"
    description = generate_purpose_code_description(purpose_code)
    print(f"Purpose code '{purpose_code}' description: {description}")
    
    # UPI QR Code generation
    print("\n=== UPI QR Code Generation Demo ===")
    upi_ref = generate_upi_transaction_reference("user@okbank", 150.0)
    qr_result = QRCodeGenerator.generate_upi_qr_code(
        upi_id="merchant@okbank",
        name="Test Merchant",
        amount=150.0,
        note="Payment for services",
        reference=upi_ref
    )
    print(f"UPI QR Code Data: {qr_result['qr_data']}")
    print(f"UPI ID (masked): {qr_result['upi_id']}")
    
    # Encryption/Decryption
    print("\n=== Encryption Demo ===")
    sensitive_data = "My sensitive data"
    encrypted = encrypt_data(sensitive_data)
    print(f"Original data: {sensitive_data}")
    print(f"Encrypted data: {encrypted['encrypted_data'][:30]}...")
    
    decrypted = decrypt_data(encrypted)
    print(f"Decrypted data: {decrypted.decode()}")

if __name__ == "__main__":
    demonstrate_common_utilities()
