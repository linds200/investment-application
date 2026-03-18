import pytest
from pydantic import ValidationError

from app import cache
from app.db import db
from app.models import PortfolioSecurity, User, Investment, Portfolio
from app.routes.trade_routes import ExecutePurchaseOrderRequestSchema, LiquidateInvestmentRequestSchema
from app.service.trade_service import InsufficientFundsError

class FakeValidator:
    def __init__(self, username: str = "admin"):
        self.username = username

    def validate_token(self, token: str):
        return {
            "sub": "123",
            "username": self.username,
            "given_name": "Admin",
            "family_name": "User",
        }


@pytest.fixture(autouse=True)
def setup_validator(app):
    app.config["COGNITO_VALIDATOR"] = FakeValidator("admin")
    with app.app_context():
        cache.clear()


@pytest.fixture
def setup(app):
    with app.app_context():
        admin = db.session.get(User, "admin")
        if not admin:
            admin = User(
                username="admin",
                firstname="Admin",
                lastname="User",
                balance=10000.0,
            )
            db.session.add(admin)

        other_user = db.session.get(User, "otheruser")
        if not other_user:
            other_user = User(username="otheruser", firstname="Other", lastname="User", balance=500.0)
            db.session.add(other_user)
        db.session.commit()

        portfolio = Portfolio(
            name="Test Portfolio",
            description="Trade route tests",
            owner="admin",
        )
        db.session.add(portfolio)
        db.session.flush()

        portfolio_id = portfolio.id
        db.session.commit()

    yield {"portfolio_id": portfolio_id}

    with app.app_context():
        db.session.query(PortfolioSecurity).delete()
        db.session.query(Investment).delete()
        db.session.query(Portfolio).delete()
        db.session.query(User).filter(User.username.in_(["admin", "otheruser"])).delete()
        db.session.commit()

# Schema tests

def test_execute_purchase_order_request_schema():
    data = {
        'portfolio_id': 1,
        'ticker': 'AAPL',
        'quantity': 10,
    }
    schema = ExecutePurchaseOrderRequestSchema(**data)
    assert schema.portfolio_id == data['portfolio_id']
    assert schema.ticker == data['ticker']
    assert schema.quantity == data['quantity']


def test_execute_purchase_order_request_schema_invalid():
    with pytest.raises(ValidationError):
        data = {
            'portfolio_id': 1,
            'ticker': 'AAPL',
            'quantity': -10,  # Invalid quantity
        }
        ExecutePurchaseOrderRequestSchema(**data)


def test_execute_purchase_order_request_schema_extra_field():
    with pytest.raises(ValidationError):
        data = {
            'portfolio_id': 1,
            'ticker': 'AAPL',
            'quantity': 10,
            'extra_field': 'This field is not defined in the schema',  # Extra field
        }
        ExecutePurchaseOrderRequestSchema(**data)


def test_liquidate_investment_request_schema():
    data = {
        'portfolio_id': 1,
        'ticker': 'AAPL',
        'quantity': 10,
        'sale_price': 150.0,
    }
    schema = LiquidateInvestmentRequestSchema(**data)
    assert schema.portfolio_id == data['portfolio_id']
    assert schema.ticker == data['ticker']
    assert schema.quantity == data['quantity']
    assert schema.sale_price == data['sale_price']


def test_liquidate_investment_request_schema_invalid():
    with pytest.raises(ValidationError):
        data = {
            'portfolio_id': 1,
            'ticker': 'AAPL',
            'quantity': 10,
            'sale_price': -150.0,  # Invalid sale price
        }
        LiquidateInvestmentRequestSchema(**data)


def test_liquidate_investment_request_schema_invalid_quantity():
    with pytest.raises(ValidationError):
        data = {
            'portfolio_id': 1,
            'ticker': 'AAPL',
            'quantity': -10,  # Invalid quantity
            'sale_price': 150.0,
        }
        LiquidateInvestmentRequestSchema(**data)


def test_liquidate_investment_request_schema_extra_field():
    with pytest.raises(ValidationError):
        data = {
            'portfolio_id': 1,
            'ticker': 'AAPL',
            'quantity': 10,
            'sale_price': 150.0,
            'extra_field': 'This field is not defined in the schema',  # Extra field
        }
        LiquidateInvestmentRequestSchema(**data)

# Route tests

def test_execute_purchase_order_success(client, setup, monkeypatch):
    def mock_execute_purchase_order(portfolio_id, ticker, quantity):
        return {
            "message": "Purchase order executed",
            "portfolio_id": portfolio_id,
            "ticker": ticker,
            "quantity": quantity,
        }

    monkeypatch.setattr(
        "app.routes.trade_routes.trade_service.execute_purchase_order",
        mock_execute_purchase_order,
    )

    response = client.post(
        "/trades/buy",
        headers={"Authorization": "Bearer fake.token.value"},
        json={"portfolio_id": setup["portfolio_id"], "ticker": "AAPL", "quantity": 2},
    )

    assert response.status_code == 201
    assert response.get_json() == {"message": "Purchase order executed successfully"}

def test_execute_purchase_order_insufficient_funds(client, setup, monkeypatch):
    def mock_execute_purchase_order(portfolio_id, ticker, quantity):
        raise InsufficientFundsError("Insufficient funds", 400)

    monkeypatch.setattr(
        "app.routes.trade_routes.trade_service.execute_purchase_order",
        mock_execute_purchase_order,
    )

    response = client.post(
        "/trades/buy",
        headers={"Authorization": "Bearer fake.token.value"},
        json={"portfolio_id": setup["portfolio_id"], "ticker": "AAPL", "quantity": 1000},
    )

    assert response.status_code == 400
    assert "Insufficient funds" in response.get_json()["error"]

def test_execute_purchase_order_missing_field(client, setup):
    response = client.post(
        "/trades/buy",
        headers={"Authorization": "Bearer fake.token.value"},
        json={"portfolio_id": setup["portfolio_id"], "ticker": "AAPL"},
    )
    assert response.status_code == 422
    assert "quantity" in response.get_json()["error"]


def test_execute_purchase_order_extra_field(client, setup):
    response = client.post(
        "/trades/buy",
        headers={"Authorization": "Bearer fake.token.value"},
        json={
            "portfolio_id": setup["portfolio_id"],
            "ticker": "AAPL",
            "quantity": 2,
            "extra_field": "bad",
        },
    )
    assert response.status_code == 422
    assert "extra_field" in response.get_json()["error"]


def test_liquidate_investment_success(client, setup, monkeypatch):
    def mock_liquidate_investment(portfolio_id, ticker, quantity, sale_price):
        return {
            "message": "Investment liquidated",
            "portfolio_id": portfolio_id,
            "ticker": ticker,
            "quantity": quantity,
            "sale_price": sale_price,
        }

    monkeypatch.setattr(
        "app.routes.trade_routes.trade_service.liquidate_investment",
        mock_liquidate_investment,
    )

    response = client.post(
        "/trades/sell",
        headers={"Authorization": "Bearer fake.token.value"},
        json={
            "portfolio_id": setup["portfolio_id"],
            "ticker": "AAPL",
            "quantity": 2,
            "sale_price": 180.0,
        },
    )

    assert response.status_code == 200
    assert response.get_json() == {"message": "Investment liquidated successfully"}
    
def test_liquidate_investment_missing_field(client, setup):
    response = client.post(
        "/trades/sell",
        headers={"Authorization": "Bearer fake.token.value"},
        json={"portfolio_id": setup["portfolio_id"], "ticker": "AAPL", "quantity": 1},
    )
    assert response.status_code == 422
    assert "sale_price" in response.get_json()["error"]


def test_liquidate_investment_invalid_quantity(client, setup):
    response = client.post(
        "/trades/sell",
        headers={"Authorization": "Bearer fake.token.value"},
        json={
            "portfolio_id": setup["portfolio_id"],
            "ticker": "AAPL",
            "quantity": -1,
            "sale_price": 180.0,
        },
    )
    assert response.status_code == 422
    assert "quantity" in response.get_json()["error"]


def test_liquidate_investment_insufficient_quantity(client, setup):
    # Ensure the investment exists, but with too few shares
    investment = Investment(
        portfolio_id=setup["portfolio_id"],
        ticker="AAPL",
        quantity=1,
        # add any other required Investment fields here if your model requires them
    )
    db.session.add(investment)
    db.session.commit()

    response = client.post(
        "/trades/sell",
        headers={"Authorization": "Bearer fake.token.value"},
        json={
            "portfolio_id": setup["portfolio_id"],
            "ticker": "AAPL",
            "quantity": 1000,   # more than owned
            "sale_price": 180.0,
        },
    )
    assert response.status_code == 400
    assert "Cannot liquidate" in response.get_json()["error"]


def test_execute_purchase_order_no_permission(client, setup, app):
    app.config["COGNITO_VALIDATOR"] = FakeValidator("otheruser")
    response = client.post(
        "/trades/buy",
        headers={"Authorization": "Bearer fake.token.value"},
        json={"portfolio_id": setup["portfolio_id"], "ticker": "AAPL", "quantity": 1},
    )
    assert response.status_code == 403
    assert "does not have permission" in response.get_json()["error"]

def test_liquidate_investment_no_permission(client, setup, app):
    app.config["COGNITO_VALIDATOR"] = FakeValidator("otheruser")
    response = client.post(
        "/trades/sell",
        headers={"Authorization": "Bearer fake.token.value"},
        json={"portfolio_id": setup["portfolio_id"], "ticker": "AAPL", "quantity": 1, "sale_price": 180.0},
    )
    assert response.status_code == 403
    assert "does not have permission" in response.get_json()["error"]

def test_viewer_execute_purchase_order_no_permission(client, setup, app, monkeypatch):
    # If this gets called, authorization failed to block correctly.
    def should_not_be_called(*args, **kwargs):
        pytest.fail("trade_service.execute_purchase_order should not be called for viewer")

    monkeypatch.setattr(
        "app.routes.trade_routes.trade_service.execute_purchase_order",
        should_not_be_called,
    )

    with app.app_context():
        portfolio = db.session.get(Portfolio, setup["portfolio_id"])
        portfolio.portfolio_securities.append(
            PortfolioSecurity(username="otheruser", role="viewer")
        )
        db.session.commit()

    app.config["COGNITO_VALIDATOR"] = FakeValidator("otheruser")
    response = client.post(
        "/trades/buy",
        headers={"Authorization": "Bearer fake.token.value"},
        json={"portfolio_id": setup["portfolio_id"], "ticker": "AAPL", "quantity": 1},
    )

    assert response.status_code == 403
    assert "does not have permission" in response.get_json()["error"]

def test_viewer_liquidate_investment_no_permission(client, setup, app, monkeypatch):
    # If this gets called, authorization failed to block correctly.
    def should_not_be_called(*args, **kwargs):
        pytest.fail("trade_service.liquidate_investment should not be called for viewer")

    monkeypatch.setattr(
        "app.routes.trade_routes.trade_service.liquidate_investment",
        should_not_be_called,
    )

    with app.app_context():
        portfolio = db.session.get(Portfolio, setup["portfolio_id"])
        portfolio.portfolio_securities.append(
            PortfolioSecurity(username="otheruser", role="viewer")
        )
        db.session.commit()

    app.config["COGNITO_VALIDATOR"] = FakeValidator("otheruser")
    response = client.post(
        "/trades/sell",
        headers={"Authorization": "Bearer fake.token.value"},
        json={
            "portfolio_id": setup["portfolio_id"],
            "ticker": "AAPL",
            "quantity": 1,
            "sale_price": 180.0,
        },
    )

    assert response.status_code == 403
    assert "does not have permission" in response.get_json()["error"]

def test_manager_execute_purchase_order(client, setup, app, monkeypatch):
    # First, add otheruser as a manager to the portfolio
    with app.app_context():
        portfolio = db.session.get(Portfolio, setup["portfolio_id"])
        portfolio.portfolio_securities.append(
            PortfolioSecurity(username="otheruser", role="manager")
        )
        db.session.commit()

    monkeypatch.setattr(
        "app.routes.trade_routes.trade_service.execute_purchase_order",
        lambda portfolio_id, ticker, quantity: None,
    )

    app.config["COGNITO_VALIDATOR"] = FakeValidator("otheruser")
    response = client.post(
        "/trades/buy",
        headers={"Authorization": "Bearer fake.token.value"},
        json={"portfolio_id": setup["portfolio_id"], "ticker": "AAPL", "quantity": 1},
    )
    assert response.status_code == 201
    assert response.get_json() == {"message": "Purchase order executed successfully"}

def test_manager_liquidate_investment(client, setup, app, monkeypatch):
    with app.app_context():
        portfolio = db.session.get(Portfolio, setup["portfolio_id"])
        portfolio.portfolio_securities.append(
            PortfolioSecurity(username="otheruser", role="manager")
        )
        db.session.commit()

    monkeypatch.setattr(
        "app.routes.trade_routes.trade_service.liquidate_investment",
        lambda portfolio_id, ticker, quantity, sale_price: None,
    )

    app.config["COGNITO_VALIDATOR"] = FakeValidator("otheruser")
    response = client.post(
        "/trades/sell",
        headers={"Authorization": "Bearer fake.token.value"},
        json={
            "portfolio_id": setup["portfolio_id"],
            "ticker": "AAPL",
            "quantity": 1,
            "sale_price": 180.0,
        },
    )

    assert response.status_code == 200
    assert response.get_json() == {"message": "Investment liquidated successfully"}
