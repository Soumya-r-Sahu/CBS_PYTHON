from cryptography.fernet import Fernet
import hashlib
import os

def generate_key():
    """Generate a new encryption key."""
    return Fernet.generate_key()

def encrypt_data(data, key):
    """Encrypt the given data using the provided key."""
    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(data.encode())
    return encrypted_data

def decrypt_data(encrypted_data, key):
    """Decrypt the given encrypted data using the provided key."""
    fernet = Fernet(key)
    decrypted_data = fernet.decrypt(encrypted_data).decode()
    return decrypted_data

def hash_password(password, salt=None):
    """Hash a password using SHA-256 with an optional salt.
    
    Args:
        password (str): The password to hash
        salt (str, optional): Salt to use for hashing. If None, a new salt is generated.
        
    Returns:
        tuple or str: If salt is None, returns (hashed_password, salt), else returns just the hashed_password
    """
    if salt is None:
        salt = os.urandom(32).hex()
        
    # Combine password and salt
    salted_password = password.encode() + salt.encode()
    
    # Hash the salted password
    hashed = hashlib.sha256(salted_password).hexdigest()
    
    if salt is None:
        return hashed, salt
    else:
        return hashed

def verify_password(password, stored_hash, salt):
    """Verify a password against a stored hash.
    
    Args:
        password (str): The password to verify
        stored_hash (str): The stored hash to compare against
        salt (str): The salt used for the stored hash
        
    Returns:
        bool: True if the password matches, False otherwise
    """
    # Hash the password with the provided salt
    password_hash = hash_password(password, salt)
    
    # Compare with stored hash
    return password_hash == stored_hash

def encrypt_card_data(card_number, cvv, pin):
    """Encrypt sensitive card data.
    
    Args:
        card_number (str): The card number to encrypt
        cvv (str): The CVV to encrypt
        pin (str): The PIN to encrypt
        
    Returns:
        dict: Dictionary containing encrypted data
    """
    # Generate a key for this encryption session
    key = generate_key()
    
    # Encrypt each piece of data
    encrypted_card = encrypt_data(card_number, key)
    encrypted_cvv = encrypt_data(cvv, key)
    encrypted_pin = encrypt_data(pin, key)
    
    return {
        'card_number': encrypted_card,
        'cvv': encrypted_cvv,
        'pin': encrypted_pin,
        'key': key  # The key should be stored securely
    }
    """Hash a password with a salt for storage"""
    # Create a salt
    salt = os.urandom(32)
    
    # Create the hashed password
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000,  # Number of iterations
        dklen=128
    )
    
    # Return salt + key as a hexadecimal string
    return (salt + key).hex()

def verify_password(stored_password, provided_password):
    """Verify a provided password against a stored hash"""
    # Convert stored password from hex to bytes
    stored_bytes = bytes.fromhex(stored_password)
    
    # Extract the salt (first 32 bytes)
    salt = stored_bytes[:32]
    
    # Extract the stored key
    stored_key = stored_bytes[32:]
    
    # Hash the provided password with the extracted salt
    key = hashlib.pbkdf2_hmac(
        'sha256',
        provided_password.encode('utf-8'),
        salt,
        100000,  # Number of iterations (must match hash_password)
        dklen=128
    )
    
    # Compare the generated key with the stored key
    return key == stored_key