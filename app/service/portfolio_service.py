from typing import List

from app.db import db
from app.models import Portfolio, User, PortfolioSecurity
from app.service import user_service


class UnsupportedPortfolioOperationError(Exception):
    def __init__(self, message: str, code: int = 400):
        super().__init__(message)
        self.code = code

class PortfolioOperationError(Exception):
    def __init__(self, message: str, code: int = 500):
        super().__init__(message)
        self.code = code

def create_portfolio(name: str, description: str, user: User) -> int:
    if not name or not description or not user:
        raise UnsupportedPortfolioOperationError(
            f'Invalid input[name:{name}, description: {description}, user: {user}]. Please try again.', 400
        )
    portfolio = Portfolio(name=name, description=description, user=user)
    try:
        db.session.add(portfolio)
        db.session.flush()
        return portfolio.id
    except Exception as e:
        db.session.rollback()
        raise PortfolioOperationError(f'Failed to create portfolio due to error: {str(e)}', 500)


def get_portfolios_by_user(user: User) -> List[Portfolio]:
    try:
        portfolios = db.session.query(Portfolio).filter_by(owner=user.username).all()
        return portfolios
    except Exception as e:
        db.session.rollback()
        raise PortfolioOperationError(f'Failed to retrieve portfolios due to error: {str(e)}', 500)


def get_all_portfolios() -> List[Portfolio]:
    try:
        portfolios = db.session.query(Portfolio).all()
        return portfolios
    except Exception as e:
        db.session.rollback()
        raise PortfolioOperationError(f'Failed to retrieve portfolios due to error: {str(e)}', 500)


def get_portfolio_by_id(portfolio_id: int) -> Portfolio | None:
    try:
        portfolio = db.session.query(Portfolio).filter_by(id=portfolio_id).one_or_none()
        return portfolio
    except Exception as e:
        db.session.rollback()
        raise PortfolioOperationError(f'Failed to retrieve portfolio due to error: {str(e)}', 500)


def delete_portfolio(portfolio_id: int):
    try:
        portfolio = db.session.query(Portfolio).filter_by(id=portfolio_id).one_or_none()
        if not portfolio:
            raise UnsupportedPortfolioOperationError(f'Portfolio with id {portfolio_id} does not exist', 404)
        db.session.delete(portfolio)
        db.session.flush()
    except UnsupportedPortfolioOperationError:
        raise
    except Exception as e:
        db.session.rollback()
        raise PortfolioOperationError(f'Failed to delete portfolio due to error: {str(e)}', 500)

def create_portfolio_security(portfolio_id: int, username: str, role: str, caller_username: str):
    try:
        portfolio = get_portfolio_by_id(portfolio_id)
        if not portfolio:
            raise UnsupportedPortfolioOperationError(f'Portfolio with id {portfolio_id} does not exist', 404)
        caller_user = user_service.get_user_by_username(caller_username)
        if portfolio.owner != caller_user.username:
            raise UnsupportedPortfolioOperationError(f'User {caller_user.username} does not have permission to add security to portfolio {portfolio_id}', 403)
        if not role or role not in ['manager', 'viewer']:
            raise UnsupportedPortfolioOperationError(f'Invalid role {role}. Role must be either "manager" or "viewer"', 400)
        user = user_service.get_user_by_username(username)
        if not user:
            raise UnsupportedPortfolioOperationError(f'User with username {username} does not exist', 404)
        portfolio_security = PortfolioSecurity(portfolio_id=portfolio_id, username=username, role=role)
        db.session.add(portfolio_security)
        db.session.flush()
    except UnsupportedPortfolioOperationError:
        raise
    except Exception as e:
        db.session.rollback()
        raise PortfolioOperationError(f'Failed to create portfolio security due to error: {str(e)}', 500)

def remove_portfolio_security(portfolio_id: int, username: str, caller_username: str):
    try:
        portfolio = get_portfolio_by_id(portfolio_id)
        if not portfolio:
            raise UnsupportedPortfolioOperationError(f'Portfolio with id {portfolio_id} does not exist', 404)
        caller_user = user_service.get_user_by_username(caller_username)
        if portfolio.owner != caller_user.username:
            raise UnsupportedPortfolioOperationError(f'User {caller_user.username} does not have permission to remove role from portfolio {portfolio_id}', 403)
        portfolio_security = db.session.query(PortfolioSecurity).filter_by(portfolio_id=portfolio_id, username=username).one_or_none()
        if not portfolio_security:
            raise UnsupportedPortfolioOperationError(f'User {username} does not have a role in portfolio {portfolio_id}', 404)
        db.session.delete(portfolio_security)
        db.session.flush()
    except UnsupportedPortfolioOperationError:
        raise
    except Exception as e:
        db.session.rollback()
        raise PortfolioOperationError(f'Failed to remove portfolio security due to error: {str(e)}', 500)

def get_portfolio_security(portfolio_id: int, username: str) -> PortfolioSecurity | None:
    try:
        if not portfolio_id:
            raise UnsupportedPortfolioOperationError(f'Invalid portfolio id {portfolio_id}', 400)
        if not username:
            raise UnsupportedPortfolioOperationError(f'Invalid username {username}', 400)
        portfolio_security = db.session.query(PortfolioSecurity).filter_by(portfolio_id=portfolio_id, username=username).one_or_none()
        if not portfolio_security:
            raise UnsupportedPortfolioOperationError(f'User {username} does not have a role in portfolio {portfolio_id}', 404)
        return portfolio_security
    except UnsupportedPortfolioOperationError:
        raise
    except Exception as e:
        db.session.rollback()
        raise PortfolioOperationError(f'Failed to retrieve portfolio security due to error: {str(e)}', 500)