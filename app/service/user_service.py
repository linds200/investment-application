from typing import List

from sqlalchemy.exc import IntegrityError

from app.db import db
from app.models.User import User

class UnsupportedUserOperationError(Exception):
    def __init__(self, message: str, code: int = 400):
        super().__init__(message)
        self.code = code
class UserOperationError(Exception):
    def __init__(self, message: str, code: int = 500):
        super().__init__(message)
        self.code = code


def get_user_by_username(username: str) -> User | None:
    try:
        if not username:
            raise UnsupportedUserOperationError('Username cannot be empty', 400)
        return db.session.query(User).filter_by(username=username).one_or_none()
    except Exception as e:
        db.session.rollback()
        raise UserOperationError(f'Failed to retrieve user due to error: {str(e)}', 500)


def get_all_users() -> List[User]:
    try:
        users = db.session.query(User).all()
        return users
    except Exception as e:
        db.session.rollback()
        raise UserOperationError(f'Failed to retrieve users due to error: {str(e)}', 500)


def update_user_balance(username: str, new_balance: float):
    try:
        user = db.session.query(User).filter_by(username=username).one_or_none()
        if not user:
            raise UnsupportedUserOperationError(f'User with username {username} does not exist', 400)
        user.balance = new_balance
        db.session.flush()
    except Exception as e:
        db.session.rollback()
        raise UserOperationError(f'Failed to update user balance due to error: {str(e)}', 500)


def create_user(username: str, firstname: str, lastname: str, balance: float):
    try:
        existing_user = db.session.query(User).filter_by(username=username).one_or_none()
        if existing_user:
            raise UnsupportedUserOperationError(f'User with username {username} already exists', 400)
        db.session.add(
            User(
                username=username,
                firstname=firstname,
                lastname=lastname,
                balance=balance,
            )
        )
        db.session.flush()
    except Exception as e:
        db.session.rollback()
        raise UserOperationError(f'Failed to create user due to error: {str(e)}', 500)


def delete_user(username: str):
    if username == 'admin':
        raise UnsupportedUserOperationError('Cannot delete admin user', 400)
    if not username:
        raise UnsupportedUserOperationError('Username cannot be empty', 400)
    try:
        user = db.session.query(User).filter_by(username=username).one_or_none()
        if not user:
            raise UnsupportedUserOperationError(f'User with username {username} does not exist', 400)
        db.session.delete(user)
        db.session.flush()
    except IntegrityError:
        raise UnsupportedUserOperationError(f'Cannot delete user {username} due to existing dependencies', 400)
    except Exception as e:
        db.session.rollback()
        raise UserOperationError(f'Failed to delete user due to error: {str(e)}', 500)
