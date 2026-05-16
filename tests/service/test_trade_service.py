import pytest

from app.models import Investment, Portfolio, Security, User
from app.service.alpha_vantage_client import SecurityQuote
from app.service import transaction_service
from app.service.trade_service import InsufficientFundsError, TradeExecutionException, execute_purchase_order, liquidate_investment
from app.service.user_service import create_user


@pytest.fixture(autouse=True)
def setup(db_session):
    user = User(username="testuser", firstname="Test", lastname="User", balance=1000.0)
    db_session.add(user)
    db_session.commit()
    portfolio1 = Portfolio(name="Portfolio 1", description="First portfolio", user=user)
    portfolio2 = Portfolio(name="Portfolio 2", description="Second portfolio", user=user)
    db_session.add_all([portfolio1, portfolio2])
    portfolio1.investments.append(Investment(ticker="AAPL", quantity=10))
    db_session.commit()
    return {
        "user": user,
        "portfolio1": portfolio1,
        "portfolio2": portfolio2
    }


@pytest.fixture(autouse=True)
def mock_get_quote(monkeypatch):
    mock_quotes = {
        "AAPL": SecurityQuote(ticker="AAPL", date="2024-01-01", price=150.0, issuer="Apple Inc."),
        "MSFT": SecurityQuote(ticker="MSFT", date="2024-01-01", price=300.0, issuer="Microsoft Corp."),
    }
    monkeypatch.setattr("app.service.trade_service.get_quote", lambda ticker: mock_quotes.get(ticker))

def test_execute_purchase_order(setup, db_session):
    portfolio = setup["portfolio1"]
    transactions = transaction_service.get_transactions_by_portfolio_id(portfolio.id)
    assert len(transactions) == 0
    user = db_session.query(User).filter_by(username="testuser").one()
    assert user.balance == 1000.00
    execute_purchase_order(portfolio.id, "AAPL", 2)
    user = db_session.query(User).filter_by(username="testuser").one()
    assert user.balance == 700.00
    user_portfolio = user.portfolios[0]
    assert user_portfolio.investments is not None
    investments = user_portfolio.investments
    assert len(investments) == 1
    investment = investments[0]
    assert investment.security.ticker == "AAPL"
    assert investment.quantity == 12
    transactions = transaction_service.get_transactions_by_portfolio_id(portfolio.id)
    assert len(transactions) == 1
    assert transactions[0].ticker == "AAPL"
    assert transactions[0].quantity == 2
    assert transactions[0].price == 150.00
    assert transactions[0].transaction_type == "BUY"

def test_execute_purchase_order_insufficient_funds(setup, db_session):
    portfolio = setup["portfolio1"]
    with pytest.raises(InsufficientFundsError) as e:
        execute_purchase_order(portfolio.id, "AAPL", 100)
    assert str(e.value) == "Insufficient funds to complete the purchase."

def test_execute_order_for_nonexistent_portfolio(db_session):
    with pytest.raises(TradeExecutionException) as e:
        execute_purchase_order(999, "AAPL", 1)
    assert "Portfolio with id 999 does not exist." in str(e.value)

def test_execute_order_for_nonexistent_security(setup, db_session):
    portfolio = setup["portfolio1"]
    with pytest.raises(TradeExecutionException) as e:
        execute_purchase_order(portfolio.id, "INVALID", 1)
    assert "Security with ticker INVALID does not exist." in str(e.value)

def test_liquidate_investment(setup, db_session):
    portfolio = setup["portfolio1"]
    liquidate_investment(portfolio.id, "AAPL", 5)
    portfolio = db_session.query(Portfolio).filter_by(id=portfolio.id).one()
    updated_investment = next((inv for inv in portfolio.investments if inv.ticker == "AAPL"), None)
    assert updated_investment is not None
    assert updated_investment.quantity == 5
    user = db_session.query(User).filter_by(username="testuser").one()
    assert user.balance == 1000.0 + (5 * 150.0)
    assert len(portfolio.investments) == 1
    assert portfolio.investments[0].ticker == "AAPL"
    assert portfolio.investments[0].quantity == 5

def test_liquidate_entire_investment(setup, db_session):
    portfolio = setup["portfolio1"]
    liquidate_investment(portfolio.id, "AAPL", 10)
    portfolio = db_session.query(Portfolio).filter_by(id=portfolio.id).one()
    updated_investment = db_session.query(Investment).filter_by(portfolio_id=portfolio.id, ticker="AAPL").one_or_none()
    assert updated_investment is None
    user = db_session.query(User).filter_by(username="testuser").one()
    assert user.balance == 1000.0 + (10 * 150.0)

def test_liquidate_investment_invalid_portfolio(db_session):
    with pytest.raises(TradeExecutionException):
        liquidate_investment(9999, "AAPL", 5)

def test_liquidate_non_existing_investment(setup, db_session):
    portfolio = setup["portfolio1"]
    with pytest.raises(TradeExecutionException):
        liquidate_investment(portfolio.id, "MSFT", 5)

def test_liquidate_investment_insufficient_quantity(setup, db_session):
    portfolio = setup["portfolio1"]
    with pytest.raises(TradeExecutionException) as e:
        liquidate_investment(portfolio.id, "AAPL", 1000)
    assert "Cannot liquidate 1000 shares of AAPL. Only 10 shares available in portfolio" in str(e.value)
    