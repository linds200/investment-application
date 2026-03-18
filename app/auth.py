from functools import wraps
from typing import Dict

import requests
from flask import current_app, g, jsonify, request
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTClaimsError, JWTError

from app.db import db
from app.service import user_service
from app.service.cognito_client import get_user_info
from app.common.response_schema import ErrorResponse

class CognitoTokenValidator:
    def __init__(self, region: str, user_pool_id: str, client_id: str, domain: str):
        self.region = region
        self.user_pool_id = user_pool_id
        self.client_id = client_id
        self.domain = domain
        self.issuer = f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}"
        self.jwks_url = f"{self.issuer}/.well-known/jwks.json"
        self.__jwks = None

    def _get_jwks(self) -> Dict:
        if self.__jwks is None:
            response = requests.get(self.jwks_url)
            response.raise_for_status()
            self.__jwks = response.json()
        return self.__jwks

    def _get_signing_key(self, token: str) -> Dict:
        try:
            header = jwt.get_unverified_header(token)
            kid = header.get('kid')
            if not kid:
                return None
            jwks = self._get_jwks()
            for key in jwks.get('keys', []):
                if key.get('kid') == kid:
                    return key
            return None
        except JWTError:
            return None
    
    def validate_token(self, token: str) -> Dict:
        signing_key = self._get_signing_key(token)
        if not signing_key:
            raise Exception("Unable to find signing key for token.")
        
        try:
            claims = jwt.decode(
                token,
                signing_key,
                algorithms=['RS256'],
                audience=self.client_id,
                issuer=self.issuer,
                options = {'verify_signature': True, 'verify_exp': True, 'verify_aud': True, 'verify_iss': True})

            if claims.get('token_use') != 'access':
                raise Exception(f"Invalid token use: {claims.get('token_use')}.")
            return claims
        except ExpiredSignatureError as e:
            raise Exception("Token has expired.")
        except JWTClaimsError as e:
            raise Exception("Invalid token claims.")
        except JWTError as e:
            raise Exception(f"Token validation failed: {str(e)}")

def get_token_from_header() -> str:
    auth_header = request.headers.get('Authorization', '').strip()
    if not auth_header:
        return None

    scheme, _, token = auth_header.partition(' ')
    if scheme.lower() != 'bearer' or not token.strip():
        return None

    return token.strip()

def requires_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_header()
        if not token:
            return jsonify(ErrorResponse(error='Missing authentication token', request_id='').model_dump()), 403
        
        validator = current_app.config.get('COGNITO_VALIDATOR')
        if not validator:
            return jsonify(ErrorResponse(error='Missing cognito token validator in the app configuration.', request_id='').model_dump()), 500
        
        try:
            from app import cache
            claims = validator.validate_token(token)
            g.user = {'user_id': claims.get('sub'), 'username': claims.get('username'), 'claims': claims}
            
            if cache.get('pre_request_all_users') is None:
                users = user_service.get_all_users()
                cache.set('pre_request_all_users', users, timeout=60)
            users = cache.get('pre_request_all_users')
            caller_username = g.user['username']
            caller_user = next((u for u in users if u.username == caller_username), None)
            try:
                if not caller_user:
                    user_info = get_user_info(token)
                    username = user_info.get('username')
                    firstname = user_info.get('attributes', {}).get('given_name', '')
                    lastname = user_info.get('attributes', {}).get('family_name', '')
                    user_service.create_user(username, firstname, lastname, 1000.0)
                    db.session.commit()
                    users = user_service.get_all_users()
                    cache.set('pre_request_all_users', users, timeout=60)
            except Exception as e:
                current_app.logger.error(f"Failed to add new user in the database: {str(e)}")
                return jsonify(ErrorResponse(error='Failed to add new user in the database.', request_id=g.request_id).model_dump()), 500
            
        except Exception as e:
            return jsonify(ErrorResponse(error=f'Token validation failed: {str(e)}', request_id='').model_dump()), 403
        
        return f(*args, **kwargs)
    return decorated_function