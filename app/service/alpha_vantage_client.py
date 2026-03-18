from dataclasses import dataclass
from time import sleep

import requests
from flask import current_app

class AlphaVantageError(Exception):
    pass

@dataclass
class SecurityQuote:
    ticker: str
    date: str
    price: float
    issuer: str | None
    
    def __to_dict__(self):
        return {
            'ticker': self.ticker,
            'date': self.date,
            'price': self.price,
            'issuer': self.issuer
        }

def _get_api_key() -> str:
    """A private helper function that retrieves the Alpha Vantage API key from the application configuration."""
    api_key = current_app.config.get('ALPHAVANTAGE_API_KEY')
    if not api_key:
        raise AlphaVantageError("Alpha Vantage API key is not set. Please set it in the environment variable 'ALPHAVANTAGE_API_KEY' or in the .env file.")
    return api_key

def get_cache():
    from app import cache
    return cache

def get_company_name(ticker: str) -> str | None:
    """Queries the Alpha Vantage API and returns the issuer name associated with the given ticker symbol. 
    Returns None if the ticker is not found."""
    
    #first check cache
    cache = get_cache()
    cache_key = f"company_name:{ticker}"
    cached_name = cache.get(cache_key)
    if cached_name is not None:
        current_app.logger.debug(f"Cache hit for company name of ticker '{ticker}': '{cached_name}'.")
        return cached_name

    api_key = _get_api_key()
    url = 'https://www.alphavantage.co/query'
    params = {'function': 'SYMBOL_SEARCH', 'keywords': ticker, 'apikey': api_key}
    
    try:
        current_app.logger.debug(f"Requesting company name for ticker '{ticker}' from Alpha Vantage API.")
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        best_matches = data.get('bestMatches', [])
        if not best_matches:
            raise AlphaVantageError(f"No matches found for ticker '{ticker}' in Alpha Vantage API.")
        
        #find the best match that exactly matches the ticker symbol
        for match in best_matches:
            if match.get('01. symbol', '').upper() == ticker.upper():
                company_name = match.get('02. name')
                current_app.logger.debug(f"Found company name '{company_name}' for ticker '{ticker}'.")
                cache.set(cache_key, company_name)
                return company_name
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving company name for ticker '{ticker}': {str(e)}")
        raise e

def get_price_data(ticker: str) -> dict | None:
    """Retrieves the most recent available price data for a given ticker. Returns a dictionary with price fields 
    (e.g., open, high, low, close, volume). Returns None if data is unavailable."""
    
    #first check cache
    cache = get_cache()
    cache_key = f"price_data:{ticker}"
    cached_price = cache.get(cache_key)
    if cached_price is not None:
        current_app.logger.debug(f"Cache hit for price data of ticker '{ticker}': {cached_price}.")
        return cached_price
    
    api_key = _get_api_key()
    url = 'https://www.alphavantage.co/query'
    params = {'function': 'GLOBAL_QUOTE', 'symbol': ticker, 'apikey': api_key}
    
    try:
        current_app.logger.debug(f"Requesting price data for ticker '{ticker}' from Alpha Vantage API.")
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        global_quote = data.get('Global Quote')
        if not global_quote:
            raise AlphaVantageError(f"No price data found for ticker '{ticker}' in Alpha Vantage API.")

        price = global_quote.get('05. price')
        if not price or price == '0.00':
            raise AlphaVantageError(f"Price data for ticker '{ticker}' is unavailable or zero in Alpha Vantage API.")

        date = global_quote.get('07. latest trading day')
        if not date:
            raise AlphaVantageError(f"No date information found for ticker '{ticker}' in Alpha Vantage API.")
    
        
        result = {'price': price, 'date': date}
        current_app.logger.debug(f"Retrieved price data for ticker '{ticker}': price={price}, date={date}.")
        cache.set(cache_key, result)
        return result 
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving price data for ticker '{ticker}': {str(e)}")
        raise e


def get_quote(ticker: str) -> SecurityQuote | None:
    """A convenience function that calls get_company_name and get_price_data internally and returns a SecurityQuote 
    dataclass instance, or None if the ticker cannot be resolved."""
    company_name = get_company_name(ticker)
    if not company_name:
        return None
    sleep(1)
    price_data = get_price_data(ticker)
    if not price_data:
        return None
    
    return SecurityQuote(
        ticker=ticker,
        date=price_data.get('date', ''),
        price=price_data.get('price', ''),
        issuer=company_name
    )