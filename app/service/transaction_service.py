from typing import List

from app.db import db
from app.models import Transaction

class TransactionOperationError(Exception):
    def __init__(self, message: str, code: int = 500):
        super().__init__(message)
        self.code = code

def get_transactions_by_user(username: str) -> List[Transaction]:
    try:
        transactions = db.session.query(Transaction).filter(Transaction.username == username).all()
        return transactions
    except Exception as e:
        db.session.rollback()
        raise TransactionOperationError(f'Failed to retrieve transactions due to error: {str(e)}', 500)


def get_transactions_by_portfolio_id(portfolio_id: int) -> List[Transaction]:
    try:
        transactions = db.session.query(Transaction).filter(Transaction.portfolio_id == portfolio_id).all()
        return transactions
    except Exception as e:
        db.session.rollback()
        raise TransactionOperationError(f'Failed to retrieve transactions due to error: {str(e)}', 500)


def get_transactions_by_ticker(ticker: str) -> List[Transaction]:
    try:
        transactions = db.session.query(Transaction).filter(Transaction.ticker == ticker).all()
        return transactions
    except Exception as e:
        db.session.rollback()
        raise TransactionOperationError(f'Failed to retrieve transactions due to error: {str(e)}', 500)
