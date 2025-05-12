"""
Customer Schema for Mobile Banking API

Defines the schemas for customer-related endpoints
"""

from marshmallow import Schema, fields, validate, validates, ValidationError
import re


class CustomerProfileSchema(Schema):
    """
    Schema for customer profile
    """
    customer_id = fields.String(required=True)
    first_name = fields.String(required=True, validate=validate.Length(min=2, max=50))
    middle_name = fields.String(allow_none=True, validate=validate.Length(max=50))
    last_name = fields.String(required=True, validate=validate.Length(min=2, max=50))
    date_of_birth = fields.Date(required=True)
    gender = fields.String(validate=validate.OneOf(['MALE', 'FEMALE', 'OTHER']))
    email = fields.Email(required=True)
    phone = fields.String(required=True, validate=validate.Length(min=10, max=15))
    address_line1 = fields.String(required=True, validate=validate.Length(min=5, max=100))
    address_line2 = fields.String(allow_none=True, validate=validate.Length(max=100))
    city = fields.String(required=True, validate=validate.Length(min=2, max=50))
    state = fields.String(required=True, validate=validate.Length(min=2, max=50))
    country = fields.String(required=True, validate=validate.Length(min=2, max=50))
    postal_code = fields.String(required=True, validate=validate.Length(min=5, max=10))
    profile_image_url = fields.URL(allow_none=True)
    kyc_status = fields.String(validate=validate.OneOf(['PENDING', 'VERIFIED', 'REJECTED']))
    occupation = fields.String(allow_none=True)
    annual_income = fields.Float(allow_none=True)


class ProfileUpdateRequestSchema(Schema):
    """
    Schema for profile update request
    """
    email = fields.Email(allow_none=True)
    phone = fields.String(allow_none=True, validate=validate.Length(min=10, max=15))
    address_line1 = fields.String(allow_none=True, validate=validate.Length(min=5, max=100))
    address_line2 = fields.String(allow_none=True, validate=validate.Length(max=100))
    city = fields.String(allow_none=True, validate=validate.Length(min=2, max=50))
    state = fields.String(allow_none=True, validate=validate.Length(min=2, max=50))
    country = fields.String(allow_none=True, validate=validate.Length(min=2, max=50))
    postal_code = fields.String(allow_none=True, validate=validate.Length(min=5, max=10))
    occupation = fields.String(allow_none=True)
    annual_income = fields.Float(allow_none=True)
    
    @validates('phone')
    def validate_phone(self, phone):
        if phone and not re.match(r'^\+?[0-9]{10,15}$', phone):
            raise ValidationError('Invalid phone number format')


class ContactDetailsUpdateSchema(Schema):
    """
    Schema for contact details update
    """
    email = fields.Email(allow_none=True)
    phone = fields.String(allow_none=True, validate=validate.Length(min=10, max=15))
    alt_email = fields.Email(allow_none=True)
    alt_phone = fields.String(allow_none=True, validate=validate.Length(min=10, max=15))
    
    @validates('phone')
    def validate_phone(self, phone):
        if phone and not re.match(r'^\+?[0-9]{10,15}$', phone):
            raise ValidationError('Invalid phone number format')
            
    @validates('alt_phone')
    def validate_alt_phone(self, alt_phone):
        if alt_phone and not re.match(r'^\+?[0-9]{10,15}$', alt_phone):
            raise ValidationError('Invalid alternate phone number format')


class NotificationPreferencesSchema(Schema):
    """
    Schema for notification preferences
    """
    sms_enabled = fields.Boolean(default=True)
    email_enabled = fields.Boolean(default=True)
    push_enabled = fields.Boolean(default=True)
    transaction_alerts = fields.Boolean(default=True)
    login_alerts = fields.Boolean(default=True)
    promotional_alerts = fields.Boolean(default=False)
    security_alerts = fields.Boolean(default=True)
    account_updates = fields.Boolean(default=True)
