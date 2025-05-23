# ID Format Standards 📜

This document outlines the standards for formatting IDs in CBS_PYTHON.

## Guidelines 📋

1. **Unique Identifiers**: Ensure all IDs are unique.
2. **Consistent Format**: Use UUIDs or a predefined pattern.
3. **Validation**: Implement validation for all IDs.

_Last updated: May 23, 2025_

# Banking ID Format Standards

This document outlines the standardized ID formats used throughout the Core Banking System in accordance with Indian and international banking standards.

## Customer ID Format

The universal customer ID format follows the pattern:

```
YYDDD-BBBBB-SSSS
```

Where:
- **YY**: Year of account creation (2 digits)
- **DDD**: Day of year (001-366)
- **BBBBB**: Branch code (5 digits)
- **SSSS**: Customer sequence number (4 digits)

Example: `23132-10001-0042` represents a customer created on the 132nd day of 2023 at branch 10001, with sequence number 42.

## Account Number Format

The universal account number format follows the Bank of Baroda style:

```
BBBBB-AATT-CCCCCC-CC
```

Where:
- **BBBBB**: Branch code (5 digits)
- **AA**: Account type (01=Savings, 02=Current, etc.)
- **TT**: Account sub-type/product code (2 digits)
- **CCCCCC**: Customer serial number (6 digits)
- **CC**: Checksum (2 digits, Luhn algorithm)

### Account Types (AA)
- 01: Savings Account
- 02: Current Account
- 03: Term Deposit (Fixed Deposit)
- 04: Recurring Deposit
- 05: Loan Account
- 06: Overdraft Account
- 07: Cash Credit
- 08: Corporate Account
- 09: Government Account
- 10: Special Account Types

### Account Sub-types (TT)
Values depend on the account type. Examples for Savings (01):
- 01: Basic Savings
- 02: Premium Savings
- 03: Senior Citizen Savings
- 04: Student Savings
- 05: Rural Savings

Example: `10001-0101-123456-42` represents an account at branch 10001, basic savings account type, customer serial 123456, with checksum 42.

## Transaction ID Format

The transaction ID format follows the pattern:

```
TRX-YYYYMMDD-SSSSSS
```

Where:
- **TRX**: Fixed prefix
- **YYYY**: Year (4 digits)
- **MM**: Month (2 digits, 01-12)
- **DD**: Day (2 digits, 01-31)
- **SSSSSS**: Sequence number (6 digits)

Example: `TRX-20251105-000123` represents the 123rd transaction on November 5, 2025.

## Employee ID Format

The employee ID format follows the Bank of Baroda style:

```
ZZBB-DD-EEEE
```

Where:
- **ZZ**: Zone code (2 digits, e.g., North = 01)
- **BB**: Branch or Department code (2 digits)
- **DD**: Designation code (2 digits)
- **EEEE**: Employee sequence number (4 digits)

### Zone Codes (ZZ)
- 01: North Zone
- 02: South Zone
- 03: East Zone
- 04: West Zone
- 05: Central Zone
- 06: Northeast Zone
- 07: Corporate Office

### Designation Codes (DD)
- 01: Teller
- 02: Clerk
- 03: Officer Scale I
- 04: Officer Scale II
- 05: Branch Manager
- 06: Zonal Manager
- 07: Department Head
- 08: General Manager
- 09: Executive Director
- 10: Chairman/CEO
- 90: Internal Auditor
- 99: IT Administrator

Example: `0102-05-1234` represents employee #1234 with Branch Manager designation at branch 02 in the North Zone.

## IFSC Code Format

Indian Financial System Code (IFSC) follows the standard format:

```
AAAABCCDDD
```

Where:
- **AAAA**: Bank code (4 characters)
- **B**: Reserved (0 for now)
- **CC**: Bank branch location city code (2 characters)
- **DDD**: Branch code (3 characters)

Example: `SBIN0123456` for State Bank of India branch.

## International Formats

### IBAN
International Bank Account Number format varies by country but follows the general pattern:
```
CC##AAAAAAAAAAAAAAAAAAAA
```

Where:
- **CC**: Country code (2 letters)
- **##**: Check digits (2 digits)
- **A...**: Account identifier (up to 30 alphanumeric characters)

Example: `GB29NWBK60161331926819` for a UK account.

### SWIFT/BIC
Bank Identifier Code format:
```
AAAABBCC[DDD]
```

Where:
- **AAAA**: Bank code (4 letters)
- **BB**: Country code (2 letters)
- **CC**: Location code (2 characters)
- **DDD**: Optional branch code (3 characters)

Example: `DEUTDEFF` for Deutsche Bank in Frankfurt.

## UPI ID Format

Unified Payments Interface ID format:
```
username@bankhandle
```

Where:
- **username**: User-defined ID or mobile number
- **bankhandle**: Bank's UPI handle

Example: `johndoe@sbi` or `9876543210@upi`.

---

## Checksum Calculation

Account numbers use a Luhn algorithm checksum:

1. Starting from the rightmost digit (excluding the checksum), double the value of every second digit
2. Sum all the digits (not the resultant products)
3. If a doubled value is greater than 9, sum its digits (e.g., 7×2=14 → 1+4=5)
4. Multiply the sum by 9
5. Take the last digit of the result as the check digit

This ensures that any single digit error or transposition error (e.g., 12 → 21) will be caught.
