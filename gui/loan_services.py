class LoanServices:
    def __init__(self):
        self.loans = []

    def apply_for_loan(self, user_id, amount, loan_type, duration):
        loan = {
            'user_id': user_id,
            'amount': amount,
            'loan_type': loan_type,
            'duration': duration,
            'status': 'Pending'
        }
        self.loans.append(loan)
        return loan

    def approve_loan(self, loan_id):
        if loan_id < len(self.loans):
            self.loans[loan_id]['status'] = 'Approved'
            return self.loans[loan_id]
        return None

    def reject_loan(self, loan_id):
        if loan_id < len(self.loans):
            self.loans[loan_id]['status'] = 'Rejected'
            return self.loans[loan_id]
        return None

    def get_loan_status(self, loan_id):
        if loan_id < len(self.loans):
            return self.loans[loan_id]['status']
        return None

    def list_loans(self):
        return self.loans