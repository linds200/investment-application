import pytest
from pydantic import ValidationError

from app.routes.portfolio_routes import CreatePortfolioRequestSchema, PortfolioSecurityRequestSchema
from app import cache
from app.db import db
from app.models import PortfolioSecurity, User, Portfolio
from tests.conftest import client

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

@pytest.fixture()
def setup(app):
    """Seed test data for route tests."""
    with app.app_context():
        # get or create admin user
        user = db.session.get(User, "admin")
        if not user:
            user = User(username="admin", firstname="Admin", lastname="User", balance=1000.0)
            db.session.add(user)

        # get or create otheruser
        other_user = db.session.get(User, "otheruser")
        if not other_user:
            other_user = User(username="otheruser", firstname="Other", lastname="User", balance=500.0)
            db.session.add(other_user)
        db.session.commit()

        portfolio = Portfolio(name="Admin Portfolio", description="Test", owner="admin")
        db.session.add(portfolio)
        db.session.flush()

        security = PortfolioSecurity(
            portfolio_id=portfolio.id,
            username="admin",
            role="manager",
        )
        db.session.add(security)
        db.session.commit()

        portfolio_id = portfolio.id

    yield {"portfolio_id": portfolio_id}

    with app.app_context():
        db.session.query(PortfolioSecurity).delete()
        db.session.query(Portfolio).delete()
        db.session.query(User).filter(User.username.in_(["admin", "otheruser"])).delete()
        db.session.commit()

# Schema tests

def test_portfolio_schema_request():
    data = {
        'name': 'Test Portfolio',
        'description': 'This is a test portfolio',
    }
    schema = CreatePortfolioRequestSchema(**data)
    assert schema.name == data['name']
    assert schema.description == data['description']


def test_portfolio_schema_request_invalid():
    with pytest.raises(ValidationError):
        data = {
            'name': 'Test Portfolio',
            'description': 'This is a test portfolio',
            'extra_field': 'This field is not defined in the schema',
        }
        CreatePortfolioRequestSchema(**data)


def test_portfolio_schema_request_missing_required():
    with pytest.raises(ValidationError):
        data = {
            'description': 'This is a test portfolio',
        }
        CreatePortfolioRequestSchema(**data)


def test_portfolio_schema_request_invalid_name():
    with pytest.raises(ValidationError):
        data = {
            'name': 'x' * 31,  # Exceeds max_length of 30
            'description': 'This is a test portfolio',
        }
        CreatePortfolioRequestSchema(**data)


def test_portfolio_security_request_schema():
    data = {
        'username': 'testuser',
        'role': 'viewer',
    }
    schema = PortfolioSecurityRequestSchema(**data)
    assert schema.username == data['username']
    assert schema.role == data['role']


def test_portfolio_security_request_schema_invalid_role():
    with pytest.raises(ValidationError):
        data = {
            'username': 'testuser',
            'role': 'invalid_role',  # Invalid role
        }
        PortfolioSecurityRequestSchema(**data)


def test_portfolio_security_request_schema_extra_field():
    with pytest.raises(ValidationError):
        data = {
            'username': 'testuser',
            'role': 'viewer',
            'extra_field': 'This field is not defined in the schema',  # Extra field
        }
        PortfolioSecurityRequestSchema(**data)


def test_portfolio_security_request_schema_invalid_username():
    with pytest.raises(ValidationError):
        data = {
            'username': 'x' * 31,  # Exceeds max_length of 30
            'role': 'viewer',
        }
        PortfolioSecurityRequestSchema(**data)

# Route tests

def test_get_portfolios_returns_list(client, setup):
    response = client.get(
        "/portfolios/",
        headers={"Authorization": "Bearer fake.token.value"},
    )
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)
    assert len(response.get_json()) > 0


def test_get_portfolios_contains_created_portfolio(client, setup):
    response = client.get(
        "/portfolios/",
        headers={"Authorization": "Bearer fake.token.value"},
    )
    assert response.status_code == 200
    names = [p["name"] for p in response.get_json()]
    assert "Admin Portfolio" in names


def test_get_portfolio_by_id_success(client, setup):
    portfolio_id = setup["portfolio_id"]
    response = client.get(
        f"/portfolios/{portfolio_id}",
        headers={"Authorization": "Bearer fake.token.value"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == portfolio_id
    assert data["name"] == "Admin Portfolio"


def test_get_portfolio_by_id_not_found(client, setup):
    response = client.get(
        "/portfolios/9999",
        headers={"Authorization": "Bearer fake.token.value"},
    )
    assert response.status_code == 404
    assert response.get_json()["error"] == "Portfolio with id 9999 does not exist"


def test_get_portfolio_by_id_no_permission(client, setup, app):
    # set token user to someone with no access
    app.config["COGNITO_VALIDATOR"] = FakeValidator("otheruser")
    portfolio_id = setup["portfolio_id"]
    response = client.get(
        f"/portfolios/{portfolio_id}",
        headers={"Authorization": "Bearer fake.token.value"},
    )
    assert response.status_code == 403
    assert response.get_json()["error"] == f'User otheruser does not have permission to view portfolio {portfolio_id}'


def test_get_portfolios_by_user_returns_list(client, setup):
    response = client.get(
        "/portfolios/user/admin",
        headers={"Authorization": "Bearer fake.token.value"},
    )
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_get_portfolios_by_user_not_found(client, setup):
    response = client.get(
        "/portfolios/user/nonexistentuser",
        headers={"Authorization": "Bearer fake.token.value"},
    )
    assert response.status_code == 404
    assert response.get_json()["error"] == "User nonexistentuser not found"


def test_create_portfolio_success(client, setup):
    response = client.post(
        "/portfolios/",
        headers={"Authorization": "Bearer fake.token.value"},
        json={"name": "New Portfolio", "description": "Created in test"},
    )
    assert response.status_code == 201
    assert response.get_json()["message"] == "Portfolio created successfully"


def test_create_portfolio_returns_portfolio_id(client, setup):
    response = client.post(
        "/portfolios/",
        headers={"Authorization": "Bearer fake.token.value"},
        json={"name": "My Portfolio", "description": "Test description"},
    )
    assert response.status_code == 201
    data = response.get_json()
    #route returns: {"message": "Portfolio created successfully", "portfolio_id": <id>}
    assert "portfolio_id" in data
    assert data["message"] == "Portfolio created successfully"


def test_create_portfolio_missing_name(client, setup):
    response = client.post(
        "/portfolios/",
        headers={"Authorization": "Bearer fake.token.value"},
        json={"description": "Missing name"},
    )
    assert response.status_code == 422
    assert "name" in response.get_json()["error"]
    assert "Field required" in response.get_json()["error"]
    

def test_create_portfolio_extra_field(client, setup):
    response = client.post(
        "/portfolios/",
        headers={"Authorization": "Bearer fake.token.value"},
        json={"name": "Test", "description": "Test", "extra_field": "bad"},
    )
    assert response.status_code == 422
    assert "extra_field" in response.get_json()["error"]


def test_delete_portfolio_success(client, setup):
    # create a portfolio first
    create_response = client.post(
        "/portfolios/",
        headers={"Authorization": "Bearer fake.token.value"},
        json={"name": "To Delete", "description": "Will be deleted"},
    )
    assert create_response.status_code == 201
    portfolio_id = create_response.get_json()["portfolio_id"]

    response = client.delete(
        f"/portfolios/{portfolio_id}",
        headers={"Authorization": "Bearer fake.token.value"},
    )
    assert response.status_code == 200
    assert response.get_json()["message"] == "Portfolio deleted successfully"


def test_delete_portfolio_not_found(client, setup):
    response = client.delete(
        "/portfolios/9999",
        headers={"Authorization": "Bearer fake.token.value"},
    )
    assert response.status_code == 404
    assert "does not exist" in response.get_json()["error"]


def test_delete_portfolio_not_owner(client, setup, app):
    app.config["COGNITO_VALIDATOR"] = FakeValidator("otheruser")
    portfolio_id = setup["portfolio_id"]
    response = client.delete(
        f"/portfolios/{portfolio_id}",
        headers={"Authorization": "Bearer fake.token.value"},
    )
    assert response.status_code == 403
    assert "does not have permission" in response.get_json()["error"]


def test_get_portfolio_transactions_returns_list(client, setup):
    portfolio_id = setup["portfolio_id"]
    response = client.get(
        f"/portfolios/{portfolio_id}/transactions",
        headers={"Authorization": "Bearer fake.token.value"},
    )
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_add_portfolio_security_success(client, setup):
    portfolio_id = setup["portfolio_id"]
    response = client.post(
        f"/portfolios/{portfolio_id}/security",
        headers={"Authorization": "Bearer fake.token.value"},
        json={"username": "otheruser", "role": "viewer"},
    )
    assert response.status_code == 201
    assert "added to portfolio" in response.get_json()["message"]


def test_add_portfolio_security_invalid_role(client, setup):
    portfolio_id = setup["portfolio_id"]
    response = client.post(
        f"/portfolios/{portfolio_id}/security",
        headers={"Authorization": "Bearer fake.token.value"},
        json={"username": "otheruser", "role": "superadmin"},
    )
    assert response.status_code == 422
    assert "role" in response.get_json()["error"]


def test_add_portfolio_security_invalid_portfolio(client, setup):
    response = client.post(
        "/portfolios/9999/security",
        headers={"Authorization": "Bearer fake.token.value"},
        json={"username": "otheruser", "role": "viewer"},
    )
    assert response.status_code == 404
    assert "does not exist" in response.get_json()["error"]


def test_remove_portfolio_security_success(client, setup):
    portfolio_id = setup["portfolio_id"]

    # add first
    client.post(
        f"/portfolios/{portfolio_id}/security",
        headers={"Authorization": "Bearer fake.token.value"},
        json={"username": "otheruser", "role": "viewer"},
    )

    # then remove
    response = client.delete(
        f"/portfolios/{portfolio_id}/security?username=otheruser",
        headers={"Authorization": "Bearer fake.token.value"},
    )
    assert response.status_code == 200
    assert "removed from portfolio" in response.get_json()["message"]


def test_remove_portfolio_security_missing_username(client, setup):
    portfolio_id = setup["portfolio_id"]
    response = client.delete(
        f"/portfolios/{portfolio_id}/security",
        headers={"Authorization": "Bearer fake.token.value"},
    )
    assert response.status_code == 400
    assert "Missing required query parameter" in response.get_json()["error"]


def test_get_portfolio_security_success(client, setup):
    portfolio_id = setup["portfolio_id"]
    response = client.get(
        f"/portfolios/{portfolio_id}/security?username=admin",
        headers={"Authorization": "Bearer fake.token.value"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["portfolio_id"] == portfolio_id
    assert data["username"] == "admin"
    assert data["role"] == "manager"


def test_get_portfolio_security_missing_username(client, setup):
    portfolio_id = setup["portfolio_id"]
    response = client.get(
        f"/portfolios/{portfolio_id}/security",
        headers={"Authorization": "Bearer fake.token.value"},
    )
    assert response.status_code == 400
    assert "Missing required query parameter" in response.get_json()["error"]
    assert response.status_code == 400


def test_get_portfolio_security_not_found(client, setup):
    portfolio_id = setup["portfolio_id"]
    response = client.get(
        f"/portfolios/{portfolio_id}/security?username=otheruser",
        headers={"Authorization": "Bearer fake.token.value"},
    )
    assert response.status_code == 404
    assert "does not have a role" in response.get_json()["error"]

def test_manager_cannot_delete_portfolio(client, setup, app):
    # set token user to manager
    app.config["COGNITO_VALIDATOR"] = FakeValidator("otheruser")
    portfolio_id = setup["portfolio_id"]
    response = client.delete(
        f"/portfolios/{portfolio_id}",
        headers={"Authorization": "Bearer fake.token.value"},
    )
    assert response.status_code == 403
    assert "does not have permission" in response.get_json()["error"]