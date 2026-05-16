from flask import Blueprint, jsonify

from app.auth import requires_auth
import app.service.alpha_vantage_client as alpha_vantage_client
import app.service.transaction_service as transaction_service


security_bp = Blueprint('security', __name__)


@security_bp.route('/<ticker>', methods=['GET'])
@requires_auth
def get_security(ticker):
    ticker_quote = alpha_vantage_client.get_quote(ticker)
    if ticker_quote is None:
        return jsonify({'error': f'No data found for ticker {ticker}'}), 404
    return jsonify(ticker_quote.__to_dict__()), 200


@security_bp.route('/<ticker>/transactions', methods=['GET'])
@requires_auth
def get_security_transactions(ticker):
    transactions = transaction_service.get_transactions_by_ticker(ticker)
    return jsonify([transaction.__to_dict__() for transaction in transactions]), 200