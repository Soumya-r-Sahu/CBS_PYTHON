"""
Transaction Schema for Mobile Banking API

Defines the schemas for transaction-related endpoints
"""

from marshmallow import Schema, fields, validate, validates, ValidationError
import datetime


class TransferRequestSchema(Schema):
    """
    Schema for fund transfer requests
    """
    from_account = fields.String(required=True, validate=validate.Length(min=8, max=20))
    to_account = fields.String(required=True, validate=validate.Length(min=8, max=20))
    amount = fields.Float(required=True, validate=validate.Range(min=1))
    currency = fields.String(default="INR", validate=validate.Length(equal=3))
    remarks = fields.String(validate=validate.Length(max=100))
    transfer_type = fields.String(required=True, validate=validate.OneOf([
        'WITHIN_BANK', 'IMPS', 'NEFT', 'RTGS'
    ]))
    schedule_time = fields.DateTime(allow_none=True)
    
    @validates('to_account')
    def validate_different_accounts(self, to_account):
        from_account = self.context.get('from_account')
        if from_account and to_account == from_account:
            raise ValidationError('Source and destination accounts cannot be the same')
            
    @validates('schedule_time')
    def validate_schedule_time(self, schedule_time):
        if schedule_time:
            now = datetime.datetime.now()
            if schedule_time < now:
                raise ValidationError('Schedule time cannot be in the past')


class TransactionHistoryRequestSchema(Schema):
    """
    Schema for transaction history request
    """
    account_number = fields.String(required=True, validate=validate.Length(min=8, max=20))
    from_date = fields.Date(allow_none=True)
    to_date = fields.Date(allow_none=True)
    transaction_type = fields.String(allow_none=True, validate=validate.OneOf([
        'CREDIT', 'DEBIT', 'ALL'
    ]), default='ALL')
    sort_by = fields.String(validate=validate.OneOf(['DATE', 'AMOUNT']), default='DATE')
    sort_order = fields.String(validate=validate.OneOf(['ASC', 'DESC']), default='DESC')
    page = fields.Integer(validate=validate.Range(min=1), default=1)
    limit = fields.Integer(validate=validate.Range(min=1, max=100), default=20)
    
    @validates('to_date')
    def validate_date_range(self, to_date):
        from_date = self.context.get('from_date')
        if from_date and to_date and to_date < from_date:
            raise ValidationError('To date must be after from date')


class TransactionDetailsRequestSchema(Schema):
    """
    Schema for transaction details request
    """
    transaction_id = fields.String(required=True)


class RecurringTransferSchema(Schema):
    """
    Schema for recurring transfer setup
    """
    from_account = fields.String(required=True, validate=validate.Length(min=8, max=20))
    to_account = fields.String(required=True, validate=validate.Length(min=8, max=20))
    amount = fields.Float(required=True, validate=validate.Range(min=1))
    frequency = fields.String(required=True, validate=validate.OneOf([
        'DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'YEARLY'
    ]))
    start_date = fields.Date(required=True)
    end_date = fields.Date(allow_none=True)
    remarks = fields.String(validate=validate.Length(max=100))
    max_occurrences = fields.Integer(validate=validate.Range(min=1), allow_none=True)
    
    @validates('start_date')
    def validate_start_date(self, start_date):
        today = datetime.date.today()
        if start_date < today:
            raise ValidationError('Start date cannot be in the past')
            
    @validates('end_date')
    def validate_end_date(self, end_date):
        if end_date:
            start_date = self.context.get('start_date')
            if start_date and end_date <= start_date:
                raise ValidationError('End date must be after start date')


class StopChequeRequestSchema(Schema):
    """
    Schema for stop cheque request
    """
    account_number = fields.String(required=True, validate=validate.Length(min=8, max=20))
    cheque_number = fields.String(required=True, validate=validate.Length(min=6, max=10))
    reason = fields.String(required=True, validate=validate.Length(min=5, max=100))
