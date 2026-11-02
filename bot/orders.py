from typing import Dict, Any, Optional

from bot.client import get_binance_client, handle_api_errors
from bot.filters import get_symbol_filters, apply_symbol_filters
from bot.logging_config import setup_logger

logger = setup_logger()


def build_order_params(symbol: str, side: str, order_type: str, quantity: str, price: Optional[str] = None) -> Dict[str, Any]:
    """
    Builds the request body for POST /fapi/v1/order.
    quantity and price should already be rounded strings (see bot/filters.py).
    """
    params = {
        "symbol": symbol.upper(),
        "side": side.upper(),
        "type": order_type.upper(),
        "quantity": quantity,
    }

    if params["type"] == "LIMIT":
        # LIMIT orders are rejected without timeInForce. GTC = stays open until filled/cancelled
        params["price"] = price
        params["timeInForce"] = "GTC"

    return params


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

    rules = get_symbol_filters(client, symbol)
    mark_price = None
    if order_type == "MARKET":
        # needed to check the min order value (notional) for market orders
        mark_price = float(client.futures_mark_price(symbol=symbol)["markPrice"])

    qty_str, price_str = apply_symbol_filters(order_type, quantity, price, rules, mark_price)
    params = build_order_params(symbol, side, order_type, qty_str, price_str)

    logger.info(f"Submitting {order_type} {side} order for {symbol} | Quantity: {qty_str} | Price: {price_str}")
    logger.debug(f"API Request params: {params}")

    response = client.futures_create_order(**params)

    logger.debug(f"API Response: {response}")
    logger.info(f"Order successfully submitted. Order ID: {response.get('orderId')}")

    return response
