from flask import Blueprint, jsonify, request, g
from pydantic import BaseModel, ConfigDict, Field

from app.auth import requires_auth
from app.common.response_schema import ErrorResponse
from app.db import db
from app.models import PortfolioSecurity
from app.service import trade_service, portfolio_service

class ExecutePurchaseOrderRequestSchema(BaseModel):
    portfolio_id: int = Field(..., description='ID of the portfolio to which the purchase will be added')
    ticker: str = Field(..., max_length=10, description='Stock ticker symbol of the security being purchased')
    quantity: int = Field(..., gt=0, description='Number of shares to purchase')
    
    model_config = ConfigDict(extra='forbid')

class LiquidateInvestmentRequestSchema(BaseModel):
    portfolio_id: int = Field(..., description='ID of the portfolio from which the investment will be liquidated')
    ticker: str = Field(..., max_length=10, description='Stock ticker symbol of the security being sold')
    quantity: int = Field(..., gt=0, description='Number of shares to sell')
    
    model_config = ConfigDict(extra='forbid')


trade_bp = Blueprint('trade', __name__)

def _caller_username():
    return g.user["username"] if isinstance(g.user, dict) else g.user


def _can_trade(portfolio, username: str) -> bool:
    if portfolio.owner == username:
        return True
    portfolio_security = (
        db.session.query(PortfolioSecurity)
        .filter_by(portfolio_id=portfolio.id, username=username)
        .one_or_none()
    )
    return bool(portfolio_security and str(portfolio_security.role).lower() == 'manager')


@trade_bp.route('/buy', methods=['POST'])
@requires_auth
def execute_purchase_order():
    req_data = ExecutePurchaseOrderRequestSchema(**request.json)
    portfolio = portfolio_service.get_portfolio_by_id(req_data.portfolio_id)
    if portfolio is None:
        return jsonify(ErrorResponse(error=f'Portfolio with id {req_data.portfolio_id} does not exist', request_id=g.request_id).model_dump()), 404

    caller_username = _caller_username()
    if not _can_trade(portfolio, caller_username):
        return jsonify(ErrorResponse(error=f'User {caller_username} does not have permission to trade on portfolio {req_data.portfolio_id}', request_id=g.request_id).model_dump()), 403

    trade_service.execute_purchase_order(
        portfolio_id=req_data.portfolio_id,
        ticker=req_data.ticker,
        quantity=req_data.quantity,
    )
    db.session.commit()
    return jsonify({'message': 'Purchase order executed successfully'}), 201

@trade_bp.route('/sell', methods=['POST'])
@requires_auth
def liquidate_investment():
    req_data = LiquidateInvestmentRequestSchema(**request.json)
    portfolio = portfolio_service.get_portfolio_by_id(req_data.portfolio_id)
    if portfolio is None:
        return jsonify(ErrorResponse(error=f'Portfolio with id {req_data.portfolio_id} does not exist', request_id=g.request_id).model_dump()), 404

    caller_username = _caller_username()
    if not _can_trade(portfolio, caller_username):
        return jsonify(ErrorResponse(error=f'User {caller_username} does not have permission to trade on portfolio {req_data.portfolio_id}', request_id=g.request_id).model_dump()), 403

    trade_service.liquidate_investment(
        portfolio_id=req_data.portfolio_id,
        ticker=req_data.ticker,
        quantity=req_data.quantity
    )
    db.session.commit()
    return jsonify({'message': 'Investment liquidated successfully'}), 200
