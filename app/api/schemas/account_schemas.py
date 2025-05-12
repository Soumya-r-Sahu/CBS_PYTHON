"""
Account Schema for Mobile Banking API

Defines the schemas for account-related endpoints
"""

from marshmallow import Schema, fields, validate, validates, ValidationError


class BalanceInquirySchema(Schema):
    """
    Schema for balance inquiry requests
    """
    account_number = fields.String(required=True, validate=validate.Length(min=8, max=20))


class AccountDetailsSchema(Schema):
    """
    Schema for account details response
    """
    account_number = fields.String(required=True)
    account_type = fields.String(required=True)
    balance = fields.Float(required=True)
    currency = fields.String(required=True)
    holder_name = fields.String(required=True)
    status = fields.String(required=True)
    branch_code = fields.String(required=True)
    opening_date = fields.Date(required=True)
    last_transaction_date = fields.DateTime(allow_none=True)
    linked_services = fields.List(fields.String(), required=True)


class AccountStatementRequestSchema(Schema):
    """
    Schema for account statement request
    """
    account_number = fields.String(required=True, validate=validate.Length(min=8, max=20))
    from_date = fields.Date(required=True)
    to_date = fields.Date(required=True)
    format = fields.String(validate=validate.OneOf(['PDF', 'CSV', 'JSON']), default='JSON')

    @validates('to_date')
    def validate_date_range(self, to_date):
        from_date = self.context.get('from_date')
        if from_date and to_date < from_date:
            raise ValidationError('To date must be after from date')


class LinkAccountRequestSchema(Schema):
    """
    Schema for linking accounts
    """
    primary_account = fields.String(required=True, validate=validate.Length(min=8, max=20))
    secondary_account = fields.String(required=True, validate=validate.Length(min=8, max=20))
    link_type = fields.String(required=True, validate=validate.OneOf(['PRIMARY', 'SECONDARY', 'JOINT']))


class AccountLimitUpdateSchema(Schema):
    """
    Schema for updating account limits
    """
    account_number = fields.String(required=True, validate=validate.Length(min=8, max=20))
    limit_type = fields.String(required=True, validate=validate.OneOf([
        'WITHDRAWAL_DAILY', 'TRANSFER_DAILY', 'UPI_DAILY', 'ATM_DAILY', 'POS_DAILY'
    ]))
    limit_amount = fields.Float(required=True, validate=validate.Range(min=0))
