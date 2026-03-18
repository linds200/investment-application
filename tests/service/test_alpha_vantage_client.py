import pytest

from app.service.alpha_vantage_client import AlphaVantageError, get_company_name, get_cache, get_price_data
from app import cache
@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()

def test_get_company_name_success(app, mock_alpha_vantage_response, monkeypatch):
    def mock_requests_get(*_, **__):
        return mock_alpha_vantage_response({'bestMatches': [{'01. symbol': 'MSFT','02. name': 'Microsoft Inc.',}]})
    
    monkeypatch.setattr('app.service.alpha_vantage_client.requests.get', mock_requests_get)
    company_name = get_company_name('MSFT')
    assert company_name == 'Microsoft Inc.'

def test_get_company_name_from_cache(app, monkeypatch):
    from app import cache
    cache.set('company_name:MSFT', 'Microsoft Inc.')
    
    total_requests = 0
    
    def request_counter(*_, **__):
        nonlocal total_requests
        total_requests += 1
        return total_requests

    monkeypatch.setattr('app.service.alpha_vantage_client.requests.get', request_counter)
    company_name = get_company_name('MSFT')
    assert company_name == 'Microsoft Inc.'
    assert total_requests == 0

def test_get_company_name_no_cache(app, mock_alpha_vantage_response, monkeypatch):
    total_requests = 0
    
    def request_counter(*_, **__):
        nonlocal total_requests
        total_requests += 1
        return mock_alpha_vantage_response({'bestMatches': [{'01. symbol': 'MSFT','02. name': 'Microsoft Inc.',}]})
    
    monkeypatch.setattr('app.service.alpha_vantage_client.requests.get', request_counter)
    
    company_name = get_company_name('MSFT')
    assert company_name == 'Microsoft Inc.'
    assert total_requests == 1

def test_missing_api_key(app, monkeypatch):    
    monkeypatch.setitem(app.config, 'ALPHAVANTAGE_API_KEY', None)
    
    with pytest.raises(AlphaVantageError) as e:
        get_company_name('AAPL')
    
    assert str(e.value) == "Alpha Vantage API key is not set. Please set it in the environment variable 'ALPHAVANTAGE_API_KEY' or in the .env file."

def test_invalid_ticker(app, mock_alpha_vantage_response, monkeypatch):
    def mock_requests_get(*_, **__):
        return mock_alpha_vantage_response({'bestMatches': []})
    
    monkeypatch.setattr('app.service.alpha_vantage_client.requests.get', mock_requests_get)
    
    with pytest.raises(AlphaVantageError) as e:
        get_company_name('INVALID')
    
    assert str(e.value) == "No matches found for ticker 'INVALID' in Alpha Vantage API."

def test_get_price_data_success(app, mock_alpha_vantage_response, monkeypatch):
    def mock_requests_get(*_, **__):
        return mock_alpha_vantage_response({
            "Global Quote": {
                "01. symbol": "AAPL",
                "02. open": "150.00",
                "03. high": "155.00",
                "04. low": "149.00",
                "05. price": "152.00",
                "06. volume": "1000000",
                "07. latest trading day": "2021-10-01",
                "08. previous close": "148.00",
                "09. change": "4.00",
                "10. change percent": "2.70%"
            }
        })
    
    monkeypatch.setattr('app.service.alpha_vantage_client.requests.get', mock_requests_get)
    price_data = get_price_data('AAPL')
    assert price_data == {'price': '152.00', 'date': '2021-10-01'}

def test_get_price_data_from_cache(app, monkeypatch):
    from app import cache
    cache.set('price_data:AAPL', {'price': '152.00', 'date': '2021-10-01'})
    
    total_requests = 0
    
    def request_counter(*_, **__):
        nonlocal total_requests
        total_requests += 1
        return total_requests

    monkeypatch.setattr('app.service.alpha_vantage_client.requests.get', request_counter)
    price_data = get_price_data('AAPL')
    assert price_data == {'price': '152.00', 'date': '2021-10-01'}
    assert total_requests == 0

def test_get_price_data_no_cache(app, mock_alpha_vantage_response, monkeypatch):
    total_requests = 0
    
    def request_counter(*_, **__):
        nonlocal total_requests
        total_requests += 1
        return mock_alpha_vantage_response({
            "Global Quote": {
                "01. symbol": "AAPL",
                "02. open": "150.00",
                "03. high": "155.00",
                "04. low": "149.00",
                "05. price": "152.00",
                "06. volume": "1000000",
                "07. latest trading day": "2021-10-01",
                "08. previous close": "148.00",
                "09. change": "4.00",
                "10. change percent": "2.70%"
            }
        })
    
    monkeypatch.setattr('app.service.alpha_vantage_client.requests.get', request_counter)
    
    price_data = get_price_data('AAPL')
    assert price_data == {'price': '152.00', 'date': '2021-10-01'}
    assert total_requests == 1

def test_get_price_data_invalid_ticker(app, mock_alpha_vantage_response, monkeypatch):
    def mock_requests_get(*_, **__):
        return mock_alpha_vantage_response({"Global Quote": {}})
    
    monkeypatch.setattr('app.service.alpha_vantage_client.requests.get', mock_requests_get)
    
    with pytest.raises(AlphaVantageError) as e:
        get_price_data('INVALID')
    
    assert str(e.value) == "No price data found for ticker 'INVALID' in Alpha Vantage API."

def test_get_price_data_api_error(app, mock_alpha_vantage_response, monkeypatch):
    def mock_requests_get(*_, **__):
        return mock_alpha_vantage_response({"Error Message": "Invalid API call."})
    
    monkeypatch.setattr('app.service.alpha_vantage_client.requests.get', mock_requests_get)
    
    with pytest.raises(AlphaVantageError) as e:
        get_price_data('AAPL')
    
    assert str(e.value) == "No price data found for ticker 'AAPL' in Alpha Vantage API."

def test_get_company_name_api_error(app, mock_alpha_vantage_response, monkeypatch):
    def mock_requests_get(*_, **__):
        return mock_alpha_vantage_response({"Error Message": "Invalid API call."})
    
    monkeypatch.setattr('app.service.alpha_vantage_client.requests.get', mock_requests_get)
    
    with pytest.raises(AlphaVantageError) as e:
        get_company_name('AAPL')
    
    assert str(e.value) == "No matches found for ticker 'AAPL' in Alpha Vantage API."

def test_company_name_invalid_ticker_no_matches(app, mock_alpha_vantage_response, monkeypatch):
    def mock_requests_get(*_, **__):
        return mock_alpha_vantage_response({'bestMatches': []})
    
    monkeypatch.setattr('app.service.alpha_vantage_client.requests.get', mock_requests_get)
    
    with pytest.raises(AlphaVantageError) as e:
        get_company_name('INVALID')
    
    assert str(e.value) == "No matches found for ticker 'INVALID' in Alpha Vantage API."