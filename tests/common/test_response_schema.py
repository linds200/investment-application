import pytest
from pydantic import ValidationError

from app.common.response_schema import ErrorResponse

def test_error_response_schema():
    data = {
        'error': 'An error occurred',
        'request_id': '12345',
    }
    schema = ErrorResponse(**data)
    assert schema.error == data['error']
    assert schema.request_id == data['request_id']

def test_error_response_schema_invalid():
    with pytest.raises(ValidationError):
        data = {
            'error': 'An error occurred',
            'request_id': '12345',
            'extra_field': 'This field is not defined in the schema',  # Extra field
        }
        ErrorResponse(**data)

def test_error_response_schema_missing_required():
    with pytest.raises(ValidationError):
        data = {
            'error': 'An error occurred',
        }
        ErrorResponse(**data)
