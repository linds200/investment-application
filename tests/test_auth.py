import pytest
from jose.exceptions import ExpiredSignatureError, JWTError

from app import cache
from app.db import db
from app.models import User


class FakeValidator:
    def __init__(self, behavior: str = "valid"):
        self.behavior = behavior

    def validate_token(self, token: str):
        if self.behavior == "expired":
            raise ExpiredSignatureError("Token expired")
        if self.behavior == "invalid":
            raise JWTError("Invalid signature")

        return {
            "sub": "123",
            "username": "admin",
            "given_name": "Admin",
            "family_name": "User",
        }


@pytest.fixture(autouse=True)
def test_state(app):
    with app.app_context():
        cache.clear()
        if not db.session.get(User, "admin"):
            db.session.add(User(username="admin", firstname="Admin", lastname="User", balance=1000.00))
            db.session.commit()


def test_protected_route_no_token(client):
    response = client.get("/portfolios/")
    assert response.status_code == 403


def test_protected_route_expired_token(app, client):
    app.config["COGNITO_VALIDATOR"] = FakeValidator("expired")

    response = client.get(
        "/portfolios/",
        headers={"Authorization": "Bearer fake.token.value"},
    )

    assert response.status_code == 403
    assert "Token validation failed" in response.get_json()["error"]


def test_protected_route_invalid_signature(app, client):
    app.config["COGNITO_VALIDATOR"] = FakeValidator("invalid")

    response = client.get(
        "/portfolios/",
        headers={"Authorization": "Bearer fake.token.value"},
    )

    assert response.status_code == 403
    assert "Token validation failed" in response.get_json()["error"]


def test_protected_route_valid_token(app, client):
    app.config["COGNITO_VALIDATOR"] = FakeValidator("valid")

    response = client.get(
        "/portfolios/",
        headers={"Authorization": "Bearer fake.token.value"},
    )
    
    assert response.status_code == 200