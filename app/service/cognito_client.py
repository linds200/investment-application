
import requests
from flask import current_app, json

class CognitoClientError(Exception):
    pass

def get_user_info(access_token: str):
    try:
        current_app.logger.info("Fetching user info from Cognito...")
        region = current_app.config.get('CONFIG_REGION')
        url = f'https://cognito-idp.{region}.amazonaws.com/'
        headers = {
            'Content-Type': 'application/x-amz-json-1.1',
            'X-Amz-Target': 'AWSCognitoIdentityProviderService.GetUser'
        }
        body = {'AccessToken': access_token}
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        data = response.json()
        attributes = {attr['Name']: attr['Value'] for attr in data.get('UserAttributes', [])}
        username = data['Username']
        current_app.logger.info(f"Successfully retrieved user info for {username}.")
        return {'username': username, 'attributes': attributes}
    except Exception as e:
        current_app.logger.error(f"Failed to get user info: {str(e)}")
        raise CognitoClientError(f"Failed to get user info: {str(e)}")
