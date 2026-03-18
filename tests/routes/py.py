import pytest
from pydantic import ValidationError

from app import cache
from app.db import db
from app.models import User
from app.routes.user_routes import CreateUserRequestSchema


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


class DummyObj:
    def __init__(self, data: dict):
        self.data = data

    def __to_dict__(self):
        return self.data


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
            admin = User(username="admin", firstname="Admin", lastname="User", balance=1000.0)
            db.session.add(admin)

        test_user = db.session.get(User, "test_user")
        if not test_user:
            test_user = User(username="test_user", firstname="Test", lastname="User", balance=500.0)
            db.session.add(test_user)

        db.session.commit()

    yield {"username": "test_user"}

    with app.app_context():
        db.session.query(User).filter(User.username.in_(["test_user"])).delete()
        db.session.commit()


def test_create_user_request_schema_valid():
    data = {
        "username": "new_user",
        "password": "x" * 30,
        "firstname": "New",
        "lastname": "User",
        "balance": 100.0,
    }
    schema = CreateUserRequestSchema(**data)
    assert schema.username == data["username"]


def test_create_user_request_schema_invalid_password():
    with pytest.raises(ValidationError):
        CreateUserRequestSchema(
            username="new_user",
            password="short",
            firstname="New",
            lastname="User",
            balance=100.0,
        )


def test_create_user_request_schema_extra_field():
    with pytest.raises(ValidationError):
        CreateUserRequestSchema(
            username="new_user",
            password="x" * 30,
            firstname="New",
            lastname="User",
            balance=100.0,
            extra_field="not-allowed",
        )


