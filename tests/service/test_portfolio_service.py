import pytest
import app.service.portfolio_service as portfolio_service
from app.models import Investment, Portfolio, User, PortfolioSecurity

@pytest.fixture(autouse=True)
def setup(db_session):
    user = User(username="testuser", firstname="Test", lastname="User", balance=1000.0)
    viewer = User(username="viewer", firstname="Viewer", lastname="User", balance=500.0)
    db_session.add_all([user, viewer])
    db_session.commit()
    
    portfolio1 = Portfolio(name="Portfolio 1", description="First portfolio", user=user)
    portfolio2 = Portfolio(name="Portfolio 2", description="Second portfolio", user=user)
    db_session.add_all([portfolio1, portfolio2])
    db_session.flush()
    
    portfolio1.investments.append(Investment(ticker="AAPL", quantity=10))
    portfolio_security = PortfolioSecurity(portfolio_id=portfolio1.id, username="testuser", role="manager")
    db_session.add(portfolio_security)
    db_session.commit()
    return {
        "user": user,
        "viewer": viewer,
        "portfolio1": portfolio1,
        "portfolio2": portfolio2,
        "portfolio_security": portfolio_security
    }

def test_get_portfolios_by_user_db_failure(db_session, monkeypatch):
    def failing_query(_):
        raise Exception("Database query error")
    monkeypatch.setattr(db_session, 'query', failing_query)
    with pytest.raises(Exception) as e:
        portfolio_service.get_portfolios_by_user(User(username="testuser", firstname="Test", lastname="User", balance=1000.0))
    assert "Failed to retrieve portfolios due to error: Database query error" in str(e.value)

def test_get_all_portfolios(db_session):
    portfolios = portfolio_service.get_all_portfolios()
    assert len(portfolios) >= 2
    names = [p.name for p in portfolios]
    assert "Portfolio 1" in names
    assert "Portfolio 2" in names

def test_get_all_portfolios_db_failure(db_session, monkeypatch):
    def failing_query(_):
        raise Exception("Database connection error")
    monkeypatch.setattr(db_session, 'query', failing_query)
    with pytest.raises(Exception) as e:
        portfolio_service.get_all_portfolios()
    assert "Failed to retrieve portfolios due to error: Database connection error" in str(e.value)

def test_get_portfolio_by_id(setup, db_session):
    portfolio = setup["portfolio1"]
    retrieved_portfolio = portfolio_service.get_portfolio_by_id(portfolio.id)
    assert retrieved_portfolio is not None
    assert retrieved_portfolio.name == "Portfolio 1"
    assert retrieved_portfolio.description == "First portfolio"

def test_get_portfolio_by_id_db_failure(db_session, monkeypatch):
    def failing_get_session(_):
        raise Exception("Database connection error")
    monkeypatch.setattr(db_session, "query", failing_get_session)
    with pytest.raises(Exception) as e:
        portfolio_service.get_portfolio_by_id(1)
    assert "Failed to retrieve portfolio due to error: Database connection error" in str(e.value)

def test_get_portfolio_by_invalid_id(db_session):
    invalid_id = 9999
    assert portfolio_service.get_portfolio_by_id(invalid_id) is None

def test_create_portfolio(setup, db_session):
    user = setup["user"]
    user_portfolios_before = portfolio_service.get_portfolios_by_user(user)
    assert len(user_portfolios_before) == 2
    portfolio_service.create_portfolio("Test Portfolio", "A test portfolio", user)
    user_portfolios_after = portfolio_service.get_portfolios_by_user(user)
    assert len(user_portfolios_after) == 3
    assert user_portfolios_after[-1].name == "Test Portfolio"
    assert user_portfolios_after[-1].description == "A test portfolio"

def test_create_portfolio_invalid_input():
    user = User(username="testuser", firstname="Test", lastname="User", balance=1000.0)
    with pytest.raises(portfolio_service.UnsupportedPortfolioOperationError):
        portfolio_service.create_portfolio("", "A test portfolio", user)
    with pytest.raises(portfolio_service.UnsupportedPortfolioOperationError):
        portfolio_service.create_portfolio("Test Portfolio", "", user)

def test_create_portfolio_db_failure(db_session, monkeypatch):
    def failing_query(_):
        raise Exception("Database connection error")
    monkeypatch.setattr(db_session, 'add', failing_query)
    with pytest.raises(Exception) as e:
        portfolio_service.create_portfolio("Fail Portfolio", "This should fail", User())
    assert "Failed to create portfolio due to error: Database connection error" in str(e.value)
        
def test_delete_portfolio(setup, db_session):
    user = setup["user"]
    portfolio = Portfolio(name="To Be Deleted", description="This portfolio will be deleted", user=user)
    db_session.add(portfolio)
    db_session.commit()
    portfolio_service.delete_portfolio(portfolio.id)
    deleted_portfolio = db_session.query(Portfolio).filter_by(id=portfolio.id).one_or_none()
    assert deleted_portfolio is None

def test_delete_portfolio_invalid_id(db_session):
    with pytest.raises(Exception):
        portfolio_service.delete_portfolio(9999)

def test_get_portfolio_security(setup, db_session):
    portfolio = setup["portfolio1"]
    security = portfolio_service.get_portfolio_security(portfolio.id, "testuser")
    assert security is not None
    assert security.username == "testuser"
    assert security.role == "manager"

def test_get_portfolio_security_invalid_portfolio_id(db_session):
    with pytest.raises(portfolio_service.UnsupportedPortfolioOperationError) as e:
        portfolio_service.get_portfolio_security(9999, "testuser")

def test_get_portfolio_security_invalid_username(setup, db_session):
    portfolio = setup["portfolio1"]
    with pytest.raises(portfolio_service.UnsupportedPortfolioOperationError) as e:
        portfolio_service.get_portfolio_security(portfolio.id, "invaliduser")

def test_get_portfolio_security_db_failure(db_session, monkeypatch):
    def failing_query(_):
        raise Exception("Database connection error")
    monkeypatch.setattr(db_session, 'query', failing_query)
    with pytest.raises(Exception) as e:
        portfolio_service.get_portfolio_security(1, "testuser")
    assert "Failed to retrieve portfolio security due to error: Database connection error" in str(e.value)

def test_create_portfolio_security(setup, db_session):
    user = setup["user"]
    portfolio = setup["portfolio2"]
    viewer = setup["viewer"]
    
    portfolio_service.create_portfolio_security(portfolio.id, viewer.username, "viewer", user.username)
    security = portfolio_service.get_portfolio_security(portfolio.id, viewer.username)
    assert security is not None
    assert security.username == viewer.username
    assert security.role == "viewer"

def test_create_portfolio_security_invalid_portfolio_id(db_session):
    with pytest.raises(portfolio_service.UnsupportedPortfolioOperationError) as e:
        portfolio_service.create_portfolio_security(9999, "testuser", "viewer", "testuser")

def test_create_portfolio_security_invalid_username(setup, db_session):
    portfolio = setup["portfolio2"]
    with pytest.raises(portfolio_service.UnsupportedPortfolioOperationError) as e:
        portfolio_service.create_portfolio_security(portfolio.id, "invaliduser", "viewer", "testuser")

def test_create_portfolio_security_invalid_role(setup, db_session):
    portfolio = setup["portfolio2"]
    with pytest.raises(portfolio_service.UnsupportedPortfolioOperationError) as e:
        portfolio_service.create_portfolio_security(portfolio.id, "testuser", "invalidrole", "testuser")

def test_remove_portfolio_security(setup, db_session):
    portfolio = setup["portfolio1"]
    portfolio_service.remove_portfolio_security(portfolio.id, "testuser", "testuser")
    security = db_session.query(PortfolioSecurity).filter_by(portfolio_id=portfolio.id, username="testuser").one_or_none()
    assert security is None

def test_remove_portfolio_security_invalid_portfolio_id(db_session):
    with pytest.raises(portfolio_service.UnsupportedPortfolioOperationError) as e:
        portfolio_service.remove_portfolio_security(9999, "testuser", "testuser")

def test_remove_portfolio_security_invalid_username(setup, db_session):
    portfolio = setup["portfolio1"]
    with pytest.raises(portfolio_service.UnsupportedPortfolioOperationError) as e:
        portfolio_service.remove_portfolio_security(portfolio.id, "invaliduser", "testuser")

def test_remove_portfolio_security_no_permission(setup, db_session):
    portfolio = setup["portfolio1"]
    viewer = setup["viewer"]
    with pytest.raises(portfolio_service.UnsupportedPortfolioOperationError) as e:
        portfolio_service.remove_portfolio_security(portfolio.id, "testuser", viewer.username)

def test_remove_portfolio_security_db_failure(db_session, monkeypatch):
    def failing_query(_):
        raise Exception("Database connection error")
    monkeypatch.setattr(db_session, 'query', failing_query)
    with pytest.raises(Exception) as e:
        portfolio_service.remove_portfolio_security(1, "testuser", "testuser")
    assert "Failed to retrieve portfolio due to error: Database connection error" in str(e.value)