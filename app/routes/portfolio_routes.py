from typing import Literal, Optional

from flask import Blueprint, current_app, g, jsonify, request
from pydantic import BaseModel, ConfigDict, Field

from app.auth import requires_auth
from app.common.response_schema import ErrorResponse
from app.db import db
import app.service.portfolio_service as portfolio_service
import app.service.transaction_service as transaction_service
import app.service.user_service as user_service

class CreatePortfolioRequestSchema(BaseModel):
    name: str = Field(..., max_length=30, description='Portfolio name')
    description: Optional[str] = Field(None, max_length=500, description='Portfolio description')
    
    model_config = ConfigDict(extra='forbid')
class PortfolioSecurityRequestSchema(BaseModel):
    username: str = Field(..., max_length=30, description='Username of the user to be added to the portfolio')
    role: Literal['viewer', 'manager'] = Field(..., description='Role of the user in the portfolio (viewer or manager)')
    
    model_config = ConfigDict(extra='forbid')

portfolio_bp = Blueprint('portfolio', __name__)


@portfolio_bp.route('/', methods=['GET'])
@requires_auth
def get_all_portfolios():
    portfolios = portfolio_service.get_all_portfolios()
    return jsonify([portfolio.__to_dict__() for portfolio in portfolios]), 200



@portfolio_bp.route('/<int:portfolio_id>', methods=['GET'])
@requires_auth
def get_portfolio(portfolio_id):
    caller_username = g.user['username']
    current_app.logger.info(f'Received request to get portfolio {portfolio_id} by user {caller_username}')
    portfolio = portfolio_service.get_portfolio_by_id(portfolio_id)
    if portfolio is None:
        return jsonify(ErrorResponse(error=f'Portfolio with id {portfolio_id} does not exist', request_id=g.request_id).model_dump()), 404
    viewers = [security.username for security in portfolio.portfolio_securities if security.role == 'viewer']
    managers = [security.username for security in portfolio.portfolio_securities if security.role == 'manager']
    if caller_username != portfolio.owner and caller_username not in viewers and caller_username not in managers:
        return jsonify(ErrorResponse(error=f'User {caller_username} does not have permission to view portfolio {portfolio_id}', request_id=g.request_id).model_dump()), 403
    return jsonify(portfolio.__to_dict__()), 200



@portfolio_bp.route('/user/<username>', methods=['GET'])
@requires_auth
def get_portfolios_by_user(username):
    user = user_service.get_user_by_username(username)
    if user is None:
        return jsonify(ErrorResponse(error=f'User {username} not found', request_id=g.request_id).model_dump()), 404
    portfolios = portfolio_service.get_portfolios_by_user(user)
    return jsonify([portfolio.__to_dict__() for portfolio in portfolios]), 200



@portfolio_bp.route('/', methods=['POST'])
@requires_auth
def create_portfolio():
    current_app.logger.info(f'Received request to create portfolio by user {g.user["username"]}')
    req_data = CreatePortfolioRequestSchema(**request.json)
    username = g.user['username']
    user = user_service.get_user_by_username(username)
    if user is None:
        return jsonify(ErrorResponse(error=f'User {username} not found', request_id=g.request_id).model_dump()), 404
    portfolio_id = portfolio_service.create_portfolio(
        name=req_data.name,
        description=req_data.description,
        user=user,
    )
    portfolio_service.create_portfolio_security(
        portfolio_id=portfolio_id,
        username=username,
        role='manager',
        caller_username=username
    )
    db.session.commit()
    return jsonify({'message': 'Portfolio created successfully', 'portfolio_id': portfolio_id}), 201



@portfolio_bp.route('/<int:portfolio_id>', methods=['DELETE'])
@requires_auth
def delete_portfolio(portfolio_id):
    caller_username = g.user['username']
    current_app.logger.info(f'Received request to delete portfolio {portfolio_id} by user {caller_username}')
    portfolio = portfolio_service.get_portfolio_by_id(portfolio_id)
    if portfolio is None:
        return jsonify(ErrorResponse(error=f'Portfolio with id {portfolio_id} does not exist', request_id=g.request_id).model_dump()), 404
    managers = [security.username for security in portfolio.portfolio_securities if security.role == 'manager']
    if portfolio.owner != caller_username and caller_username not in managers:
        return jsonify(ErrorResponse(error=f'User {caller_username} does not have permission to delete portfolio {portfolio_id}', request_id=g.request_id).model_dump()), 403
    portfolio_service.delete_portfolio(portfolio_id)
    db.session.commit()
    return jsonify({'message': 'Portfolio deleted successfully'}), 200



@portfolio_bp.route('/<int:portfolio_id>/transactions', methods=['GET'])
@requires_auth
def get_portfolio_transactions(portfolio_id):
    transactions = transaction_service.get_transactions_by_portfolio_id(portfolio_id)
    return jsonify([transaction.__to_dict__() for transaction in transactions]), 200



@portfolio_bp.route('/<int:portfolio_id>/security', methods=['POST'])
@requires_auth
def add_portfolio_security(portfolio_id):
    create_portfolio_security_req = PortfolioSecurityRequestSchema(**request.json)
    caller_username = g.user['username']
    portfolio_service.create_portfolio_security(
        portfolio_id=portfolio_id,
        username=create_portfolio_security_req.username,
        role=create_portfolio_security_req.role,
        caller_username=caller_username,
    )
    return jsonify({'message': f'User {create_portfolio_security_req.username} added to portfolio {portfolio_id} with role {create_portfolio_security_req.role} successfully.'}), 201



@portfolio_bp.route('/<int:portfolio_id>/security', methods=['DELETE'])
@requires_auth
def delete_portfolio_security(portfolio_id):
    requested_username = request.args.get('username')
    if not requested_username:
        return jsonify({'error': 'Missing required query parameter: username'}), 400
    caller_username = g.user['username']
    portfolio_service.remove_portfolio_security(
        portfolio_id=portfolio_id,
        username=requested_username,
        caller_username=caller_username,
    )
    return jsonify({'message': f'User {requested_username} role removed from portfolio {portfolio_id} successfully.'}), 200



@portfolio_bp.route('/<int:portfolio_id>/security', methods=['GET'])
@requires_auth
def get_portfolio_security(portfolio_id):
    requested_username = request.args.get('username')
    if not requested_username:
        return jsonify({'error': 'Missing required query parameter: username'}), 400
    security = portfolio_service.get_portfolio_security(portfolio_id, requested_username)
    if security is None:
        return jsonify({'error': f'Portfolio security for portfolio {portfolio_id} not found'}), 404
    return jsonify(security.__to_dict__()), 200