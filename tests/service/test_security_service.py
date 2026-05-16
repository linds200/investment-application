import pytest

from app.models import Portfolio, User
from app.service.portfolio_service import create_portfolio
from app.service.security_service import SecurityOperationError, get_all_securities, get_security_by_ticker
from app.service.user_service import create_user


def test_get_security_by_ticker(db_session):
    security = get_security_by_ticker("AAPL")
    assert security is not None
    assert security.ticker == "AAPL"
    assert security.price == 150.00

def test_get_all_securities(db_session):
    securities = get_all_securities()
    assert securities is not None
    assert len(securities) == 3
    tickers = [sec.ticker for sec in securities]
    assert "AAPL" in tickers
    assert "GOOGL" in tickers
    assert "MSFT" in tickers

def test_exception_from_get_all_securities(db_session, monkeypatch):
    def mock_query_failure(_):
        raise Exception("Database connection error")
    monkeypatch.setattr(db_session, 'query', mock_query_failure)
    with pytest.raises(SecurityOperationError) as e:
        get_all_securities()
    assert "Failed to retrieve securities due to error: Database connection error" in str(e.value)