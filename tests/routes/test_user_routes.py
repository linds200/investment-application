import pytest
from pydantic import ValidationError

from app import cache
from app.db import db
from app.models import User
from app.routes.user_routes import CreateUserRequestSchema, UpdateBalanceRequestSchema

class FakeValidator:
    def __init__(self, username: str = "admin"):
        self.username = username

    def _claims(self):
        return {
            "sub": "123",
            "username": self.username,
            "cognito:username": self.username,
            "token_use": "access",
        }

    def validate_token(self, token: str):
        return self._claims()

    def validate(self, token: str):
        return self._claims()

class DummyObj:
    def __init__(self, data: dict):
        self.data = data

    def __to_dict__(self):
        return self.data


@pytest.fixture(autouse=True)
def setup_validator_and_user(client):
    app = client.application
    app.config["COGNITO_VALIDATOR"] = FakeValidator("admin")

    with app.app_context():
        cache.clear()
        admin = db.session.query(User).filter_by(username="admin").one_or_none()
        if not admin:
            db.session.add(
                User(username="admin", firstname="Admin", lastname="User", balance=1000.0)
            )
            db.session.commit()


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

# Schema tests

def test_create_user_request_schema():
    data = {
        'username': 'testuser',
        'password': 'securepassword12345678901234567890',
        'firstname': 'Test',
        'lastname': 'User',
        'balance': 1000.0,
    }
    schema = CreateUserRequestSchema(**data)
    assert schema.username == data['username']
    assert schema.password == data['password']
    assert schema.firstname == data['firstname']
    assert schema.lastname == data['lastname']
    assert schema.balance == data['balance']


def test_create_user_request_schema_invalid():
    with pytest.raises(ValidationError):
        data = {
            'username': 'testuser',
            'password': 'short',  # Invalid password (too short)
            'firstname': 'Test',
            'lastname': 'User',
            'balance': 1000.0,
        }
        CreateUserRequestSchema(**data)


def test_create_user_request_schema_extra_field():
    with pytest.raises(ValidationError):
        data = {
            'username': 'testuser',
            'password': 'securepassword12345678901234567890',
            'firstname': 'Test',
            'lastname': 'User',
            'balance': 1000.0,
            'extra_field': 'This field is not defined in the schema',  # Extra field
        }
        CreateUserRequestSchema(**data)


def test_create_user_request_schema_invalid_balance():
    with pytest.raises(ValidationError):
        data = {
            'username': 'testuser',
            'password': 'securepassword12345678901234567890',
            'firstname': 'Test',
            'lastname': 'User',
            'balance': -100.0,  # Invalid balance (negative)
        }
        CreateUserRequestSchema(**data)


def test_update_balance_request_schema():
    data = {
        'username': 'testuser',
        'balance': 1500.0,
    }
    schema = UpdateBalanceRequestSchema(**data)
    assert schema.username == data['username']
    assert schema.balance == data['balance']


def test_update_balance_request_schema_invalid_balance():
    with pytest.raises(ValidationError):
        data = {
            'username': 'testuser',
            'balance': -500.0,  # Invalid balance (negative)
        }
        UpdateBalanceRequestSchema(**data)

# Route tests

def test_get_all_users_success(client, setup):
    response = client.get(
        "/users/",
        headers={"Authorization": "Bearer fake.token.value"},
    )
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_get_user_by_username_success(client, setup, monkeypatch):
    monkeypatch.setattr(
        "app.routes.user_routes.user_service.get_user_by_username",
        lambda username: DummyObj(
            {"username": username, "firstname": "Test", "lastname": "User", "balance": 500.0}
        ),
    )

    response = client.get(
        f"/users/{setup['username']}",
        headers={"Authorization": "Bearer fake.token.value"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["username"] == setup["username"]
    assert data["firstname"] == "Test"
    assert data["lastname"] == "User"


def test_get_user_by_username_not_found(client, monkeypatch):
    monkeypatch.setattr(
        "app.routes.user_routes.user_service.get_user_by_username",
        lambda username: None,
    )

    response = client.get(
        "/users/missing_user",
        headers={"Authorization": "Bearer fake.token.value"},
    )
    assert response.status_code == 404
    assert response.get_json()["error"] == "User missing_user not found"


def test_create_user_success(client, monkeypatch):
    monkeypatch.setattr(
        "app.routes.user_routes.user_service.create_user",
        lambda username, firstname, lastname, balance: None,
    )

    response = client.post(
        "/users/",
        headers={"Authorization": "Bearer fake.token.value"},
        json={
            "username": "new_user",
            "password": "x" * 30,
            "firstname": "New",
            "lastname": "User",
            "balance": 100.0,
        },
    )
    assert response.status_code == 201
    assert response.get_json()["message"] == "User new_user created successfully"


def test_create_user_missing_field(client):
    response = client.post(
        "/users/",
        headers={"Authorization": "Bearer fake.token.value"},
        json={
            "username": "new_user",
            "password": "x" * 30,
            "firstname": "New",
            "balance": 100.0,
        },
    )
    assert response.status_code == 422
    assert "error" in response.get_json()


def test_delete_user_success(client, setup, monkeypatch):
    monkeypatch.setattr(
        "app.routes.user_routes.user_service.delete_user",
        lambda username: None,
    )

    response = client.delete(
        f"/users/{setup['username']}",
        headers={"Authorization": "Bearer fake.token.value"},
    )
    assert response.status_code == 200
    assert response.get_json()["message"] == f"User {setup['username']} deleted successfully"

def test_update_user_balance_success(client, setup, monkeypatch):
    monkeypatch.setattr(
        "app.routes.user_routes.user_service.update_user_balance",
        lambda username, new_balance: None,
    )

    response = client.put(
        "/users/update-balance",
        headers={"Authorization": "Bearer fake.token.value"},
        json={
            "username": setup["username"],
            "balance": 200.0,
        },
    )
    assert response.status_code == 200
    assert response.get_json()["message"] == "User balance updated successfully"


def test_update_user_balance_invlalid_balance(client, setup):
    response = client.put(
        "/users/update-balance",
        headers={"Authorization": "Bearer fake.token.value"},
        json={
            "username": setup["username"],
            "balance": -50.0,  # Invalid balance (negative)
        },
    )
    assert response.status_code == 422