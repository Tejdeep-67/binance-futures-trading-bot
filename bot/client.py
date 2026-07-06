import os
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
from dotenv import load_dotenv

from bot.exceptions import APIError, NetworkError
from bot.logging_config import setup_logger

logger = setup_logger()

def get_binance_client() -> Client:
    """
    Initializes and returns the Binance client configured for the Futures Testnet.
    Credentials are read from environment variables.
    """
    load_dotenv()

    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_SECRET_KEY")

    if not api_key or not api_secret:
        logger.error("Binance API credentials missing from environment.")
        raise APIError("BINANCE_API_KEY and BINANCE_SECRET_KEY must be set in .env file.")

    try:
        client = Client(api_key, api_secret, testnet=True)
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Binance client: {e}", exc_info=True)
        raise APIError("Failed to initialize Binance client. Check credentials and connection.")

def handle_api_errors(func):
    """
    Decorator to handle Binance API and network exceptions gracefully.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BinanceAPIException as e:
            logger.error(f"Binance API error: {e.status_code} - {e.message}")
            raise APIError(f"Binance API returned an error: {e.message}")
        except BinanceRequestException as e:
            logger.error(f"Binance Network/Request error: {e}")
            raise NetworkError("A network error occurred while connecting to Binance.")
        except Exception as e:
            logger.error(f"Unexpected error in API call: {e}", exc_info=True)
            raise APIError("An unexpected error occurred during the API request.")
    return wrapper
