import functools
import os
import time

import requests
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
from dotenv import load_dotenv

from bot.exceptions import APIError, NetworkError, TradingBotError
from bot.logging_config import setup_logger

logger = setup_logger()

def sync_time(client: Client) -> None:
    """
    Signed requests fail with -1021 (timestamp outside recvWindow) when the PC
    clock is a few seconds off, which happens a lot on Windows. So ask the
    futures server for its time once and let python-binance apply the offset.
    """
    server_time = client.futures_time()["serverTime"]
    client.timestamp_offset = server_time - int(time.time() * 1000)
    logger.debug(f"Clock offset vs Binance futures server: {client.timestamp_offset} ms")


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
        # ping=False: the default ping goes to the *spot* testnet, which we don't use
        client = Client(api_key, api_secret, testnet=True, ping=False)
        sync_time(client)
        return client
    except requests.exceptions.RequestException as e:
        logger.error(f"Could not reach Binance Futures Testnet: {e}")
        raise NetworkError("Could not reach the Binance Futures Testnet. Check your internet connection.")
    except Exception as e:
        logger.error(f"Failed to initialize Binance client: {e}", exc_info=True)
        raise APIError("Failed to initialize Binance client. Check credentials and connection.")

def handle_api_errors(func):
    """
    Decorator to handle Binance API and network exceptions gracefully.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except TradingBotError:
            # already a clean message (e.g. missing keys, bad quantity) - don't hide it
            raise
        except BinanceAPIException as e:
            logger.error(f"Binance API error: {e.status_code} - {e.message}")
            raise APIError(f"Binance API returned an error: {e.message}")
        except BinanceRequestException as e:
            logger.error(f"Binance Network/Request error: {e}")
            raise NetworkError("A network error occurred while connecting to Binance.")
        except requests.exceptions.RequestException as e:
            # timeouts / DNS / connection refused come from requests, not python-binance
            logger.error(f"Network error: {e}")
            raise NetworkError("Could not reach the Binance Futures Testnet. Check your internet connection.")
        except Exception as e:
            logger.error(f"Unexpected error in API call: {e}", exc_info=True)
            raise APIError("An unexpected error occurred during the API request.")
    return wrapper
