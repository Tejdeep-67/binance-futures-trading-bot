from typing import Dict, Any, Optional

from bot.client import get_binance_client, handle_api_errors
from bot.logging_config import setup_logger

logger = setup_logger()

@handle_api_errors
def place_order(symbol: str, side: str, order_type: str, quantity: float, price: Optional[float] = None) -> Dict[str, Any]:
    """
    Submits an order to the Binance Futures Testnet.
    
    Returns a dictionary containing response data.
    """
    client = get_binance_client()
    
    symbol = symbol.upper()
    side = side.upper()
    order_type = order_type.upper()

    params = {
        "symbol": symbol,
        "side": side,
        "type": order_type,
        "quantity": quantity,
    }

    if order_type == "LIMIT":
        params["price"] = price
        params["timeInForce"] = "GTC"

    logger.info(f"Submitting {order_type} {side} order for {symbol} | Quantity: {quantity} | Price: {price}")
    logger.debug(f"API Request params: {params}")

    response = client.futures_create_order(**params)
    
    logger.debug(f"API Response: {response}")
    logger.info(f"Order successfully submitted. Order ID: {response.get('orderId')}")

    return response
