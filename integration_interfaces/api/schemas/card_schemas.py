"""
Card Schema for Mobile Banking API

Defines the schemas for card-related endpoints
"""

from marshmallow import Schema, fields, validate, validates, ValidationError
import re



# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
class CardActivationSchema(Schema):
    """
    Schema for card activation
    """
    card_number = fields.String(required=True, validate=[
        validate.Length(equal=16),
        validate.Regexp(r'^[0-9]{16}$', error='Card number must be 16 digits')
    ])
    expiry_date = fields.String(required=True, validate=validate.Regexp(
        r'^(0[1-9]|1[0-2])/[0-9]{2}$', 
        error='Expiry date must be in MM/YY format'
    ))
    cvv = fields.String(required=True, validate=[
        validate.Length(equal=3),
        validate.Regexp(r'^[0-9]{3}$', error='CVV must be 3 digits')
    ])


class CardPINSetSchema(Schema):
    """
    Schema for setting card PIN
    """
    card_number = fields.String(required=True, validate=[
        validate.Length(equal=16),
        validate.Regexp(r'^[0-9]{16}$', error='Card number must be 16 digits')
    ])
    pin = fields.String(required=True, validate=[
        validate.Length(equal=4),
        validate.Regexp(r'^[0-9]{4}$', error='PIN must be 4 digits')
    ])
    confirm_pin = fields.String(required=True, validate=[
        validate.Length(equal=4),
        validate.Regexp(r'^[0-9]{4}$', error='PIN must be 4 digits')
    ])
    
    @validates('confirm_pin')
    def validate_pin_match(self, confirm_pin):
        if confirm_pin != self.context.get('pin'):
            raise ValidationError('PIN and confirm PIN must match')


class CardPINChangeSchema(Schema):
    """
    Schema for changing card PIN
    """
    card_number = fields.String(required=True, validate=[
        validate.Length(equal=16),
        validate.Regexp(r'^[0-9]{16}$', error='Card number must be 16 digits')
    ])
    current_pin = fields.String(required=True, validate=[
        validate.Length(equal=4),
        validate.Regexp(r'^[0-9]{4}$', error='PIN must be 4 digits')
    ])
    new_pin = fields.String(required=True, validate=[
        validate.Length(equal=4),
        validate.Regexp(r'^[0-9]{4}$', error='PIN must be 4 digits')
    ])
    confirm_pin = fields.String(required=True, validate=[
        validate.Length(equal=4),
        validate.Regexp(r'^[0-9]{4}$', error='PIN must be 4 digits')
    ])
    
    @validates('new_pin')
    def validate_different_pin(self, new_pin):
        if new_pin == self.context.get('current_pin'):
            raise ValidationError('New PIN cannot be the same as current PIN')
    
    @validates('confirm_pin')
    def validate_pin_match(self, confirm_pin):
        if confirm_pin != self.context.get('new_pin'):
            raise ValidationError('New PIN and confirm PIN must match')


class CardBlockSchema(Schema):
    """
    Schema for blocking a card
    """
    card_number = fields.String(required=True, validate=[
        validate.Length(equal=16),
        validate.Regexp(r'^[0-9]{16}$', error='Card number must be 16 digits')
    ])
    reason = fields.String(required=True, validate=validate.OneOf([
        'LOST', 'STOLEN', 'DAMAGED', 'FRAUD', 'OTHER'
    ]))
    additional_info = fields.String(validate=validate.Length(max=200))


class CardLimitUpdateSchema(Schema):
    """
    Schema for updating card limits
    """
    card_number = fields.String(required=True, validate=[
        validate.Length(equal=16),
        validate.Regexp(r'^[0-9]{16}$', error='Card number must be 16 digits')
    ])
    daily_atm_limit = fields.Float(validate=validate.Range(min=0))
    daily_pos_limit = fields.Float(validate=validate.Range(min=0))
    daily_online_limit = fields.Float(validate=validate.Range(min=0))
    domestic_usage = fields.Boolean()
    international_usage = fields.Boolean()
    contactless_enabled = fields.Boolean()
