from flask import Blueprint, jsonify, request

from app.db import db
from app.service import trade_service

trade_bp = Blueprint('trade', __name__)


@trade_bp.route('/buy', methods=['POST'])
def execute_purchase_order():
    req_data = request.get_json()
    trade_service.execute_purchase_order(
        portfolio_id=req_data['portfolio_id'],
        ticker=req_data['ticker'],
        quantity=req_data['quantity'],
    )
    db.session.commit()
    return jsonify({'message': 'Purchase order executed successfully'}), 201


@trade_bp.route('/sell', methods=['POST'])
def liquidate_investment():
    req_data = request.get_json()
    trade_service.liquidate_investment(
        portfolio_id=req_data['portfolio_id'],
        ticker=req_data['ticker'],
        quantity=req_data['quantity'],
        sale_price=req_data['sale_price'],
    )
    db.session.commit()
    return jsonify({'message': 'Investment liquidated successfully'}), 200
