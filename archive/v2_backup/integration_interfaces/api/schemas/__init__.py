"""
Schema definitions for validating API requests

This module imports all schema objects from individual schema files
"""

# Use centralized import system first
import os
import sys
from pathlib import Path

# Add project root to path to enable imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path

# Authentication schemas
from .auth_schemas import (
    LoginSchema,
    MPINSetupSchema,
    MPINLoginSchema, 
    PasswordChangeSchema,
    ForgotPasswordSchema,
    OTPVerificationSchema
)

# UPI schemas
from .upi_schemas import (
    UPIRegistrationSchema,
    UPITransactionSchema,
    UPIPinChangeSchema,
    UPIBalanceSchema,
    QRCodeGenerationSchema,
    DeviceInfoSchema
)

# Card schemas
from .card_schemas import (
    CardActivationSchema,
    CardPINSetSchema,
    CardPINChangeSchema,
    CardBlockSchema,
    CardLimitUpdateSchema
)

# Account schemas
from .account_schemas import (
    BalanceInquirySchema,
    AccountDetailsSchema,
    AccountStatementRequestSchema,
    LinkAccountRequestSchema,
    AccountLimitUpdateSchema
)

# Transaction schemas
from .transaction_schemas import (
    TransferRequestSchema,
    TransactionHistoryRequestSchema,
    TransactionDetailsRequestSchema,
    RecurringTransferSchema,
    StopChequeRequestSchema
)

# Customer schemas
from .customer_schemas import (
    CustomerProfileSchema,
    ProfileUpdateRequestSchema,
    ContactDetailsUpdateSchema,
    NotificationPreferencesSchema
)
