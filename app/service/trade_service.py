import datetime

from app.db import db
from app.models import Investment, Portfolio, Security, Transaction


class TradeExecutionException(Exception):
    def __init__(self, message: str, code: int = 500):
        super().__init__(message)
        self.code = code


class InsufficientFundsError(Exception):
    def __init__(self, message: str, code: int = 400):
        super().__init__(message)
        self.code = code


def execute_purchase_order(portfolio_id: int, ticker: str, quantity: int):
    """
    Execute a purchase order for a given portfolio, security ticker, and quantity.

    Args:
        portfolio_id (int): The ID of the portfolio.
        ticker (str): The ticker symbol of the security to purchase.
        quantity (int): The number of shares to purchase.

    Raises:
        TradeExecutionException: If there is an error during the trade execution.
        InsufficientFundsError: If the user has insufficient funds to complete the purchase.
    """
    if portfolio_id is None or not ticker or not quantity or quantity <= 0:
        raise TradeExecutionException(
            f'Invalid purchase order parameters [portfolio_id={portfolio_id}, ticker={ticker}, quantity={quantity}]', 400
        )
    portfolio = db.session.query(Portfolio).filter_by(id=portfolio_id).one_or_none()
    if not portfolio:
        raise TradeExecutionException(f'Portfolio with id {portfolio_id} does not exist.', 400)
    user = portfolio.user
    if not user:
        raise TradeExecutionException(f'User associated with the portfolio ({portfolio_id}) does not exist.', 400)

    security = db.session.query(Security).filter_by(ticker=ticker).one_or_none()
    if not security:
        raise TradeExecutionException(f'Security with ticker {ticker} does not exist.', 400)
    total_cost = security.price * quantity
    if user.balance < total_cost:
        raise InsufficientFundsError('Insufficient funds to complete the purchase.', 400)
    
    try: 
        existing_investment = next((inv for inv in portfolio.investments if inv.ticker == ticker), None)
        if existing_investment:
            existing_investment.quantity += quantity
        else:
            portfolio.investments.append(Investment(ticker=ticker, quantity=quantity, security=security))

        user.balance -= total_cost
        db.session.add(
            Transaction(
                portfolio_id=portfolio.id,
                username=user.username,
                ticker=ticker,
                quantity=quantity,
                price=security.price,
                transaction_type='BUY',
                date_time=datetime.datetime.now(),
            )
        )
        db.session.flush()
    except InsufficientFundsError:
        db.session.rollback()
        raise
    except TradeExecutionException:
        db.session.rollback()
        raise
    except Exception as e:
        db.session.rollback()
        raise TradeExecutionException(f'Failed to execute purchase order due to error: {str(e)}', 500)


def liquidate_investment(portfolio_id: int, ticker: str, quantity: int, sale_price: float):
    """
    Liquidate shares of a security from a portfolio at a given sale price.

    Args:
        portfolio_id (int): The ID of the portfolio to sell from.
        ticker (str): The ticker symbol of the security to sell.
        quantity (int): The number of shares to sell.
        sale_price (float): The price per share to use for the sale.

    Raises:
        TradeExecutionException: If the portfolio, investment, or quantity is invalid,
            or if a database error occurs while recording the sale.
    """
    try:
        portfolio = db.session.query(Portfolio).filter_by(id=portfolio_id).one_or_none()
        if not portfolio:
            raise TradeExecutionException(f'Portfolio with id {portfolio_id} does not exist', 400)
        user = portfolio.user
        investment = db.session.query(Investment).filter_by(portfolio_id=portfolio_id, ticker=ticker).one_or_none()
        if not investment:
            raise TradeExecutionException(
                f'No investment with ticker {ticker} exists in portfolio with id {portfolio_id}', 400
            )
        if investment.quantity < quantity:
            raise TradeExecutionException(
                f'Cannot liquidate {quantity} shares of {ticker}. Only {investment.quantity} shares available in portfolio', 400
            )
        total_proceeds = sale_price * quantity
        user.balance += total_proceeds
        investment.quantity -= quantity
        if investment.quantity == 0:
            db.session.delete(investment)
        db.session.add(
            Transaction(
                portfolio_id=portfolio.id,
                username=user.username,
                ticker=ticker,
                quantity=quantity,
                price=sale_price,
                transaction_type='SELL',
                date_time=datetime.datetime.now(),
            )
        )
        db.session.flush()
    except TradeExecutionException:
        db.session.rollback()
        raise
    except Exception as e:
        db.session.rollback()
        raise TradeExecutionException(f'Failed to liquidate investment due to error: {str(e)}', 500) from e
