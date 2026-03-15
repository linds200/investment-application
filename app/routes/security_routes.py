from flask import Blueprint, jsonify

import app.service.security_service as security_service
import app.service.transaction_service as transaction_service

security_bp = Blueprint('security', __name__)


@security_bp.route('/', methods=['GET'])
def get_all_securities():
    securities = security_service.get_all_securities()
    return jsonify([security.__to_dict__() for security in securities]), 200


@security_bp.route('/<ticker>', methods=['GET'])
def get_security(ticker):
    security = security_service.get_security_by_ticker(ticker)
    if security is None:
        return jsonify({'error': f'Security {ticker} not found'}), 404
    return jsonify(security.__to_dict__()), 200


@security_bp.route('/<ticker>/transactions', methods=['GET'])
def get_security_transactions(ticker):
    transactions = transaction_service.get_transactions_by_ticker(ticker)
    return jsonify([transaction.__to_dict__() for transaction in transactions]), 200
