from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import pytest
from sqlalchemy.orm import scoped_session

from app import create_app
from app.config import get_config
from app.db import db
from app.models import Security, User

@pytest.fixture(scope='session')
def app():
    test_config = get_config('test')
    app = create_app(test_config)
    with app.app_context():
        db.create_all()
        _populate_database()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='function')
def client(app):
    return app.test_client()

@pytest.fixture(scope='function')
def db_session(app, monkeypatch):
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()
        
        test_session = scoped_session(db.session.session_factory)
        test_session.configure(bind=connection)
        
        def mock_commit():
            test_session.flush()
        
        monkeypatch.setattr(db, 'session', test_session)
        monkeypatch.setattr(test_session, 'commit', mock_commit)
        monkeypatch.setattr(test_session, 'close', lambda: None)
        
        yield test_session
        
        test_session.remove()
        transaction.rollback()
        connection.close()

@pytest.fixture(scope='function')
def mock_alpha_vantage_response():
    def _create_mock(response_data: dict):
        class MockResponse:
            def raise_for_status(self):
                pass
            
            def json(self):
                return response_data
            
        return MockResponse()
    return _create_mock

def _populate_database():
    try:
        admin_user = User(username='admin', firstname='Admin', lastname='User', balance=1000.00)
        db.session.add(admin_user)

        securities = [
            Security(ticker='AAPL', issuer='Apple Inc.', price=150.00),
            Security(ticker='GOOGL', issuer='Alphabet Inc.', price=2800.00),
            Security(ticker='MSFT', issuer='Microsoft Corp.', price=300.00),
        ]
        db.session.add_all(securities)
    except Exception:
        db.session.rollback()
    finally:
        db.session.commit()