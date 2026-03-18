import datetime 
import logging
import sys
import uuid
from logging.handlers import RotatingFileHandler
from zoneinfo import ZoneInfo

from flask import Flask, jsonify, g, request
from flask_caching import Cache
from pydantic import ValidationError

from app.auth import CognitoTokenValidator
from app.db import db
from app.routes import portfolio_bp, security_bp, trade_bp, user_bp
from app.common.response_schema import ErrorResponse 
from app.service.portfolio_service import UnsupportedPortfolioOperationError, PortfolioOperationError
from app.service.security_service import SecurityOperationError
from app.service.trade_service import TradeExecutionException, InsufficientFundsError
from app.service.transaction_service import TransactionOperationError
from app.service.user_service import UserOperationError
class RequestIDFilter(logging.Filter):
    def filter(self, record):
        record.request_id = getattr(g, 'request_id', 'N/A')
        return True

cache = Cache()

def create_app(config):
    try:
        app = Flask(__name__)
        app.config.from_object(config)
        
        # configure and register the cache object
        app.config['CACHE_TYPE'] = 'SimpleCache'
        app.config['CACHE_DEFAULT_TIMEOUT'] = 300
        
        cache.init_app(app)
        
        token_validator = CognitoTokenValidator(
            region=app.config['CONFIG_REGION'], 
            user_pool_id=app.config['CONFIG_POOL_ID'], 
            client_id=app.config['CONFIG_CLIENT_ID'],
            domain=app.config['CONFIG_DOMAIN']
        )
        app.config['COGNITO_VALIDATOR'] = token_validator

        # configure the logging pattern for this application
        with app.app_context():
            if app.debug or app.testing:
                handler = logging.StreamHandler(sys.stdout)
                handler.setLevel(logging.DEBUG)
            else:
                handler = RotatingFileHandler('app.log', maxBytes=1000000, backupCount=10)
                handler.setLevel(logging.INFO)

            formatter = logging.Formatter(
                '%(asctime)s %(levelname)s [%(request_id)s]: %(message)s (in %(module)s:%(lineno)d)'
            )
            
            handler.setFormatter(formatter)
            handler.addFilter(RequestIDFilter())
            app.logger.handlers.clear()
            app.logger.addHandler(handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('Starting app...')
        
        @app.before_request
        def before_request():
            g.request_id = str(uuid.uuid4())
            g.start_time = datetime.datetime.now(ZoneInfo('America/New_York'))
            app.logger.info(f"New request ({g.request_id}): @{request.method} {request.host}{request.path}")
            
        @app.after_request
        def after_request(response):
            g.end_time = datetime.datetime.now(ZoneInfo('America/New_York'))
            duration = g.end_time - g.start_time
            app.logger.info(f"Request with ID {g.request_id} completed in {duration} seconds.")
            return response
        
        @app.errorhandler(Exception)
        def handle_exception(error):
            db.session.rollback()
            error = ErrorResponse(error=str(error), request_id=g.request_id)
            return jsonify(error.model_dump()), 500
        
        @app.errorhandler(ValidationError)
        def handle_validation_error(error):
            # Extract first error message for simplicity
            first_error = error.errors()[0]
            error_message = f"{first_error['loc'][0]}: {first_error['msg']}"
            return jsonify({'error': error_message, 'code': 422}), 422
        
        @app.errorhandler(UnsupportedPortfolioOperationError)
        def handle_unsupported_portfolio_operation_error(error):
            status_code = getattr(error, 'code', 404)
            return jsonify({'error': str(error)}), status_code
        
        @app.errorhandler(PortfolioOperationError)
        def handle_portfolio_operation_error(error):
            status_code = getattr(error, 'code', 500)
            return jsonify({'error': str(error), 'code': status_code}), status_code
        
        @app.errorhandler(SecurityOperationError)
        def handle_security_exception(error):
            status_code = getattr(error, 'code', 403)
            return jsonify({'error': str(error), 'code': status_code}), status_code
        
        @app.errorhandler(TradeExecutionException)
        def handle_trade_execution_exception(error):
            status_code = getattr(error, 'code', 500)
            return jsonify({'error': str(error), 'code': status_code}), status_code
        
        @app.errorhandler(InsufficientFundsError)
        def handle_insufficient_funds_error(error):
            status_code = getattr(error, 'code', 400)
            return jsonify({'error': str(error), 'code': status_code}), status_code
        
        @app.errorhandler(TransactionOperationError)
        def handle_transaction_operation_error(error):
            status_code = getattr(error, 'code', 500)
            return jsonify({'error': str(error), 'code': status_code}), status_code
        
        @app.errorhandler(UserOperationError)
        def handle_unsupported_user_operation_error(error):
            status_code = getattr(error, 'code', 400)
            return jsonify({'error': str(error), 'code': status_code}), status_code
        
        # register extensions
        db.init_app(app)

        # register blueprints
        app.register_blueprint(user_bp, url_prefix='/users')
        app.register_blueprint(portfolio_bp, url_prefix='/portfolios')
        app.register_blueprint(security_bp, url_prefix='/securities')
        app.register_blueprint(trade_bp, url_prefix='/trades')

        return app
    except Exception as e:
        print(f'Error creating app: {e}')
        raise
