"""
Authentication Schema for Mobile Banking API

Defines the schemas for authentication-related endpoints
"""

from marshmallow import Schema, fields, validate, validates, ValidationError
import re



# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
class DeviceInfoSchema(Schema):
    """
    Schema for device information
    """
    device_model = fields.String(required=True)
    os_version = fields.String(required=True)
    app_version = fields.String(required=True)


class LoginSchema(Schema):
    """
    Schema for user login
    """
    customer_id = fields.String(required=True, validate=validate.Length(min=6, max=20))
    password = fields.String(required=True, validate=validate.Length(min=8))
    device_id = fields.String(required=True)
    device_info = fields.Nested(DeviceInfoSchema, required=True)


class MPINSetupSchema(Schema):
    """
    Schema for MPIN setup
    """
    customer_id = fields.String(required=True, validate=validate.Length(min=6, max=20))
    password = fields.String(required=True, validate=validate.Length(min=8))
    mpin = fields.String(required=True, validate=[
        validate.Length(equal=6),
        validate.Regexp(r'^[0-9]{6}$', error='MPIN must be a 6-digit number')
    ])
    confirm_mpin = fields.String(required=True, validate=[
        validate.Length(equal=6),
        validate.Regexp(r'^[0-9]{6}$', error='MPIN must be a 6-digit number')
    ])
    
    @validates('confirm_mpin')
    def validate_mpin_match(self, confirm_mpin):
        if confirm_mpin != self.context.get('mpin'):
            raise ValidationError('MPIN and confirm MPIN must match')


class MPINLoginSchema(Schema):
    """
    Schema for login with MPIN
    """
    customer_id = fields.String(required=True, validate=validate.Length(min=6, max=20))
    mpin = fields.String(required=True, validate=[
        validate.Length(equal=6),
        validate.Regexp(r'^[0-9]{6}$', error='MPIN must be a 6-digit number')
    ])
    device_id = fields.String(required=True)
    device_info = fields.Nested(DeviceInfoSchema, required=True)


class PasswordChangeSchema(Schema):
    """
    Schema for password change
    """
    current_password = fields.String(required=True, validate=validate.Length(min=8))
    new_password = fields.String(required=True, validate=validate.Length(min=8))
    confirm_password = fields.String(required=True, validate=validate.Length(min=8))
    
    @validates('new_password')
    def validate_new_password(self, new_password):
        # Password complexity validation
        if not re.search(r'[A-Z]', new_password):
            raise ValidationError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', new_password):
            raise ValidationError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', new_password):
            raise ValidationError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', new_password):
            raise ValidationError('Password must contain at least one special character')
        if new_password == self.context.get('current_password'):
            raise ValidationError('New password cannot be the same as current password')
    
    @validates('confirm_password')
    def validate_confirm_password(self, confirm_password):
        if confirm_password != self.context.get('new_password'):
            raise ValidationError('Passwords do not match')


class ForgotPasswordSchema(Schema):
    """
    Schema for forgot password request
    """
    customer_id = fields.String(required=True, validate=validate.Length(min=6, max=20))
    registered_email = fields.Email(required=True)
    registered_phone = fields.String(required=True, validate=validate.Length(min=10, max=15))


class OTPVerificationSchema(Schema):
    """
    Schema for OTP verification
    """
    customer_id = fields.String(required=True, validate=validate.Length(min=6, max=20))
    otp = fields.String(required=True, validate=[
        validate.Length(equal=6),
        validate.Regexp(r'^[0-9]{6}$', error='OTP must be a 6-digit number')
    ])
    request_id = fields.String(required=True)
