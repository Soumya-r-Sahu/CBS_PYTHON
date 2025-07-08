'''
Dependency Injection Container

This module sets up the dependency injection container for the ATM-Switch module.
'''

import os
from decimal import Decimal
from typing import Dict, Any

from dependency_injector import containers, providers
from decimal import Decimal

from .domain.services.pin_service import PinService
from .domain.services.transaction_rules import TransactionRules
from .domain.services.card_security import CardSecurityService

from .application.use_cases.withdraw_cash import WithdrawCashUseCase
from .application.use_cases.check_balance import CheckBalanceUseCase
from .application.use_cases.change_pin import ChangePinUseCase
from .application.use_cases.get_mini_statement import GetMiniStatementUseCase
from .application.use_cases.validate_card import ValidateCardUseCase
from .application.services.atm_service import AtmService

from .infrastructure.repositories.sql_atm_repository import SqlAtmRepository
from .infrastructure.services.email_notification_service import EmailNotificationService
from .infrastructure.services.sms_notification_service import SmsNotificationService

from .presentation.api.atm_controller import AtmController

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class AtmSwitchContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    # Domain services
    pin_service = providers.Factory(PinService)
    transaction_rules = providers.Factory(TransactionRules)
    card_security = providers.Factory(CardSecurityService)

    # Infrastructure
    atm_repository = providers.Singleton(SqlAtmRepository)
    email_notification_service = providers.Singleton(EmailNotificationService)
    sms_notification_service = providers.Singleton(SmsNotificationService)

    # Application use cases
    withdraw_cash_use_case = providers.Factory(
        WithdrawCashUseCase,
        atm_repository=atm_repository,
        notification_service=email_notification_service
    )
    check_balance_use_case = providers.Factory(
        CheckBalanceUseCase,
        atm_repository=atm_repository
    )
    change_pin_use_case = providers.Factory(
        ChangePinUseCase,
        atm_repository=atm_repository,
        card_security_service=card_security
    )
    get_mini_statement_use_case = providers.Factory(
        GetMiniStatementUseCase,
        atm_repository=atm_repository
    )
    validate_card_use_case = providers.Factory(
        ValidateCardUseCase,
        atm_repository=atm_repository
    )

    # Application service
    atm_service = providers.Factory(
        AtmService,
        withdraw_cash=withdraw_cash_use_case,
        check_balance=check_balance_use_case,
        change_pin=change_pin_use_case,
        get_mini_statement=get_mini_statement_use_case,
        validate_card=validate_card_use_case
    )

    # Presentation
    atm_controller = providers.Factory(
        AtmController,
        withdraw_cash_use_case=withdraw_cash_use_case,
        check_balance_use_case=check_balance_use_case,
        change_pin_use_case=change_pin_use_case,
        get_mini_statement_use_case=get_mini_statement_use_case,
        validate_card_use_case=validate_card_use_case
    )


container = AtmSwitchContainer()


def get_atm_controller():
    return container.atm_controller()


def get_atm_service():
    return container.atm_service()
