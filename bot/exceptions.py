class TradingBotError(Exception):
    """Base exception for the trading bot."""
    pass

class ValidationError(TradingBotError):
    """Exception raised for invalid user input."""
    pass

class APIError(TradingBotError):
    """Exception raised for Binance API errors."""
    pass

class NetworkError(TradingBotError):
    """Exception raised for network or connection issues."""
    pass
