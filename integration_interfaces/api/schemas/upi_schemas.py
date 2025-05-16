"""
UPI Schema for Mobile Banking API

Defines the schemas for UPI-related endpoints
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
    device_id = fields.String(required=True)
    device_model = fields.String()
    os_version = fields.String()


class UPIRegistrationSchema(Schema):
    """
    Schema for UPI registration
    """
    account_number = fields.String(required=True, validate=validate.Length(min=8, max=20))
    username = fields.String(required=True, validate=validate.Length(min=3, max=50))
    device_info = fields.Nested(DeviceInfoSchema, required=True)
    upi_pin = fields.String(required=True, validate=[
        validate.Length(equal=6), 
        validate.Regexp(r'^[0-9]{6}$', error="UPI PIN must be a 6-digit number")
    ])


class UPITransactionSchema(Schema):
    """
    Schema for UPI transactions
    """
    sender_upi_id = fields.String(required=True, validate=validate.Regexp(
        r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9]+$', 
        error="Invalid UPI ID format"
    ))
    receiver_upi_id = fields.String(required=True, validate=validate.Regexp(
        r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9]+$', 
        error="Invalid UPI ID format"
    ))
    amount = fields.Float(required=True, validate=validate.Range(min=0.01))
    purpose = fields.String(validate=validate.Length(max=100))
    upi_pin = fields.String(required=True, validate=[
        validate.Length(equal=6), 
        validate.Regexp(r'^[0-9]{6}$', error="UPI PIN must be a 6-digit number")
    ])
    
    @validates('receiver_upi_id')
    def validate_different_upi_ids(self, receiver_upi_id):
        if receiver_upi_id == self.context.get('sender_upi_id'):
            raise ValidationError('Sender and receiver UPI IDs cannot be the same')


class UPIPinChangeSchema(Schema):
    """
    Schema for changing UPI PIN
    """
    upi_id = fields.String(required=True, validate=validate.Regexp(
        r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9]+$', 
        error="Invalid UPI ID format"
    ))
    old_pin = fields.String(required=True, validate=[
        validate.Length(equal=6), 
        validate.Regexp(r'^[0-9]{6}$', error="UPI PIN must be a 6-digit number")
    ])
    new_pin = fields.String(required=True, validate=[
        validate.Length(equal=6), 
        validate.Regexp(r'^[0-9]{6}$', error="UPI PIN must be a 6-digit number")
    ])
    confirm_pin = fields.String(required=True, validate=[
        validate.Length(equal=6), 
        validate.Regexp(r'^[0-9]{6}$', error="UPI PIN must be a 6-digit number")
    ])
    
    @validates('new_pin')
    def validate_new_pin(self, new_pin):
        old_pin = self.context.get('old_pin')
        if old_pin and new_pin == old_pin:
            raise ValidationError('New PIN cannot be the same as the old PIN')
            
    @validates('confirm_pin')
    def validate_confirm_pin(self, confirm_pin):
        new_pin = self.context.get('new_pin')
        if new_pin and confirm_pin != new_pin:
            raise ValidationError('Confirm PIN must match the new PIN')


class UPIBalanceSchema(Schema):
    """
    Schema for UPI balance inquiry
    """
    upi_id = fields.String(required=True, validate=validate.Regexp(
        r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9]+$', 
        error="Invalid UPI ID format"
    ))


class QRCodeGenerationSchema(Schema):
    """
    Schema for QR code generation
    """
    upi_id = fields.String(required=True, validate=validate.Regexp(
        r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9]+$', 
        error="Invalid UPI ID format"
    ))
    amount = fields.Float(validate=validate.Range(min=0))
    purpose = fields.String(validate=validate.Length(max=100))
    qr_type = fields.String(validate=validate.OneOf(['STATIC', 'DYNAMIC']), default='STATIC')


class UPICollectRequestSchema(Schema):
    """
    Schema for UPI collect request
    """
    requester_upi_id = fields.String(required=True, validate=validate.Regexp(
        r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9]+$', 
        error="Invalid UPI ID format"
    ))
    payer_upi_id = fields.String(required=True, validate=validate.Regexp(
        r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9]+$', 
        error="Invalid UPI ID format"
    ))
    amount = fields.Float(required=True, validate=validate.Range(min=0.01))
    purpose = fields.String(validate=validate.Length(max=100))
    
    @validates('requester_upi_id')
    def validate_different_upi_ids(self, requester_upi_id):
        if 'payer_upi_id' in self.context and requester_upi_id == self.context['payer_upi_id']:
            raise ValidationError("Requester and payer UPI IDs cannot be the same")


class UPICollectResponseSchema(Schema):
    """
    Schema for responding to UPI collect requests
    """
    collect_id = fields.String(required=True)
    action = fields.String(required=True, validate=validate.OneOf(['ACCEPT', 'REJECT']))
    upi_pin = fields.String(validate=[
        validate.Length(equal=6), 
        validate.Regexp(r'^[0-9]{6}$', error="UPI PIN must be a 6-digit number")
    ])
    
    @validates('upi_pin')
    def validate_pin_for_accept(self, upi_pin):
        if 'action' in self.context and self.context['action'] == 'ACCEPT' and not upi_pin:
            raise ValidationError("UPI PIN is required when accepting a collect request")
