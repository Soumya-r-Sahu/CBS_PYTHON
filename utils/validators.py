"""
Core Banking System - Data Validation Utilities
"""

import re
import datetime
try:
    from dateutil.relativedelta import relativedelta
except ImportError:
    pass  # Fallback handling is provided in validate_age function

# Keep backward compatibility with legacy code
def is_valid_email(email):
    return validate_email(email)

def is_valid_phone(phone):
    return validate_phone(phone)

def is_valid_account_number(account_number):
    return validate_account_number(account_number)

def is_valid_amount(amount):
    try:
        amount = float(amount)
        return amount > 0
    except ValueError:
        return False

def is_valid_pin(pin):
    return validate_pin(pin)

# Enhanced validation functions
def validate_email(email):
    """Validate an email address format."""
    email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    return bool(email_pattern.match(email))

def validate_phone(phone):
    """Validate a phone number format."""
    # Remove any spaces, dashes, or parentheses
    stripped_phone = re.sub(r"[\s\-\(\)]", "", phone)
    
    # Check if the result is a valid phone number
    # Accept 10-11 digits (as in legacy code) but allow for country codes
    return stripped_phone.isdigit() and 10 <= len(stripped_phone) <= 15

def validate_pan(pan_number):
    """Validate an Indian PAN card number."""
    pan_pattern = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")
    return bool(pan_pattern.match(pan_number))

def validate_aadhar(aadhar_number):
    """Validate an Indian Aadhar number."""
    # Remove any spaces
    stripped_aadhar = re.sub(r"\s", "", aadhar_number)
    
    # Check if the result is a 12-digit number
    aadhar_pattern = re.compile(r"^\d{12}$")
    return bool(aadhar_pattern.match(stripped_aadhar))

def validate_ifsc(ifsc_code):
    """Validate an Indian IFSC code."""
    ifsc_pattern = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")
    return bool(ifsc_pattern.match(ifsc_code))

def validate_date_format(date_str, format="%Y-%m-%d"):
    """Validate a date string format."""
    try:
        datetime.datetime.strptime(date_str, format)
        return True
    except ValueError:
        return False

def validate_age(dob, min_age=18):
    """Validate if a person is above the minimum age."""
    try:
        # Try to use dateutil if available
        from dateutil.relativedelta import relativedelta
        today = datetime.date.today()
        age = relativedelta(today, dob).years
        return age >= min_age
    except ImportError:
        # Fallback to approximate calculation
        today = datetime.date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age >= min_age

def validate_card_number(card_number):
    """Validate a credit/debit card number using the Luhn algorithm."""
    # Remove spaces and dashes
    card_number = re.sub(r"[\s\-]", "", card_number)
    
    # Check if the input contains only digits
    if not card_number.isdigit():
        return False
    
    # Check length (most card numbers are between 13 and 19 digits)
    if not 13 <= len(card_number) <= 19:
        return False
    
    # Apply Luhn algorithm
    digits = [int(d) for d in card_number]
    checksum = 0
    
    for i, digit in enumerate(reversed(digits)):
        if i % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    
    return checksum % 10 == 0

def validate_cvv(cvv):
    """Validate a CVV/CVC code."""
    # CVV should be 3 or 4 digits
    cvv_pattern = re.compile(r"^\d{3,4}$")
    return bool(cvv_pattern.match(cvv))

def validate_account_number(account_number):
    """Validate a bank account number."""
    # Maintain backward compatibility with legacy code
    return account_number.isdigit() and len(account_number) in [10, 12, 14, 16, 18]

def validate_password_strength(password):
    """Validate password strength."""
    issues = []
    
    if len(password) < 8:
        issues.append("Password must be at least 8 characters long")
    
    if not re.search(r"[A-Z]", password):
        issues.append("Password must include at least one uppercase letter")
    
    if not re.search(r"[a-z]", password):
        issues.append("Password must include at least one lowercase letter")
    
    if not re.search(r"[0-9]", password):
        issues.append("Password must include at least one digit")
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        issues.append("Password must include at least one special character")
    
    if issues:
        return False, issues
    
    return True, ["Password meets strength requirements"]

def validate_pin(pin):
    """Validate a PIN."""
    # PIN should be 4 or 6 digits
    return pin.isdigit() and len(pin) in [4, 6]

def validate_transaction_amount(amount, min_amount=1.0, max_amount=None):
    """Validate a transaction amount."""
    try:
        amount = float(amount)
        
        if amount < min_amount:
            return False
        
        if max_amount is not None and amount > max_amount:
            return False
        
        return True
    except (ValueError, TypeError):
        return False

def is_valid_user_input(user_input, input_type):
    if input_type == 'email':
        return is_valid_email(user_input)
    elif input_type == 'phone':
        return is_valid_phone(user_input)
    elif input_type == 'account_number':
        return is_valid_account_number(user_input)
    elif input_type == 'amount':
        return is_valid_amount(user_input)
    elif input_type == 'pin':
        return is_valid_pin(user_input)
    return False