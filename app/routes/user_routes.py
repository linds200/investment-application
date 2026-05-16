from flask import Blueprint, jsonify, request
from pydantic import BaseModel, ConfigDict, Field

from app.auth import requires_auth
from app.db import db
import app.service.transaction_service as transaction_service
import app.service.user_service as user_service

class CreateUserRequestSchema(BaseModel):
    username: str = Field(..., max_length=30, description='Unique username for the user')
    password: str = Field(..., min_length=30, description='Password for the user (min 6 characters)')
    firstname: str = Field(..., max_length=30, description='First name of the user')
    lastname: str = Field(..., max_length=30, description='Last name of the user')
    balance: float = Field(..., ge=0, description='Initial account balance for the user')
    
    model_config = ConfigDict(extra='forbid')

class UpdateBalanceRequestSchema(BaseModel):
    username: str = Field(..., max_length=30, description='Username of the user to update')
    balance: float = Field(..., ge=0, description='New account balance for the user')
    
    model_config = ConfigDict(extra='forbid')


user_bp = Blueprint('user', __name__)


@user_bp.route('/', methods=['GET'])
@requires_auth
def get_users():
    users = user_service.get_all_users()
    return jsonify([user.__to_dict__() for user in users]), 200


@user_bp.route('/<username>', methods=['GET'])
@requires_auth
def get_user(username):
    user = user_service.get_user_by_username(username)
    if user is None:
        return jsonify({'error': f'User {username} not found'}), 404
    return jsonify(user.__to_dict__()), 200


@user_bp.route('/', methods=['POST'])
@requires_auth
def create_user():
    req_data = CreateUserRequestSchema(**request.get_json())
    username = req_data.username
    firstname = req_data.firstname
    lastname = req_data.lastname
    balance = req_data.balance
    user_service.create_user(
        username=username, firstname=firstname, lastname=lastname, balance=balance
    )
    db.session.commit()
    return jsonify({'message': f'User {username} created successfully'}), 201


@user_bp.route('/update-balance', methods=['PUT'])
@requires_auth
def update_balance():
    req_data = UpdateBalanceRequestSchema(**request.get_json())
    username = req_data.username
    new_balance = req_data.balance
    user_service.update_user_balance(username=username, new_balance=new_balance)
    db.session.commit()
    return jsonify({'message': 'User balance updated successfully'}), 200


@user_bp.route('/<username>', methods=['DELETE'])
@requires_auth
def delete_user(username):
    user_service.delete_user(username)
    db.session.commit()
    return jsonify({'message': f'User {username} deleted successfully'}), 200


@user_bp.route('/<username>/transactions', methods=['GET'])
@requires_auth
def get_user_transactions(username):
    transactions = transaction_service.get_transactions_by_user(username)
    return jsonify([transaction.__to_dict__() for transaction in transactions]), 200