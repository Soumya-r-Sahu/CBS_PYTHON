import unittest
from decimal import Decimal
from unittest.mock import Mock

from ..application.use_cases.withdraw_cash import WithdrawCashUseCase
from ..domain.entities.transaction import Transaction


class TestWithdrawCashUseCase(unittest.TestCase):
    def setUp(self):
        self.mock_repository = Mock()
        self.mock_notification_service = Mock()
        self.use_case = WithdrawCashUseCase(
            atm_repository=self.mock_repository,
            notification_service=self.mock_notification_service,
            withdrawal_fee=Decimal('2.5'),
            daily_withdrawal_limit=Decimal('1000'),
            min_withdrawal=Decimal('10'),
            max_withdrawal=Decimal('500')
        )

    def test_withdraw_success(self):
        # Arrange
        self.mock_repository.get_account_balance.return_value = Decimal('1000')
        self.mock_repository.create_transaction.return_value = Transaction(
            id=1, amount=Decimal('100'), fee=Decimal('2.5'), total=Decimal('102.5'), balance=Decimal('897.5')
        )

        # Act
        result = self.use_case.execute(session_token='test_token', amount=Decimal('100'))

        # Assert
        self.assertTrue(result['success'])
        self.assertEqual(result['data']['amount'], Decimal('100'))
        self.assertEqual(result['data']['fee'], Decimal('2.5'))
        self.assertEqual(result['data']['balance'], Decimal('897.5'))

    def test_withdraw_insufficient_balance(self):
        # Arrange
        self.mock_repository.get_account_balance.return_value = Decimal('50')

        # Act
        result = self.use_case.execute(session_token='test_token', amount=Decimal('100'))

        # Assert
        self.assertFalse(result['success'])
        self.assertEqual(result['message'], 'Insufficient balance')


if __name__ == '__main__':
    unittest.main()
