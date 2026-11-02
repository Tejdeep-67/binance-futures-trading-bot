from decimal import Decimal, ROUND_DOWN
from typing import Dict, Optional, Tuple

from bot.exceptions import ValidationError
from bot.logging_config import setup_logger

logger = setup_logger()


def get_symbol_filters(client, symbol: str) -> Dict[str, Decimal]:
    """
    Reads the trading rules for one symbol from /fapi/v1/exchangeInfo.
    Binance rejects orders whose quantity/price don't match these
    (error -1111 "Precision is over the maximum defined for this asset").
    """
    info = client.futures_exchange_info()
    match = next((s for s in info.get("symbols", []) if s["symbol"] == symbol), None)
    if match is None:
        raise ValidationError(f"Symbol {symbol} is not listed on the Futures Testnet.")
    if match.get("status") != "TRADING":
        raise ValidationError(f"Symbol {symbol} is not trading right now (status: {match.get('status')}).")

    rules = {}
    for f in match.get("filters", []):
        if f["filterType"] == "PRICE_FILTER":
            rules["tickSize"] = Decimal(f["tickSize"])
            rules["minPrice"] = Decimal(f["minPrice"])
            rules["maxPrice"] = Decimal(f["maxPrice"])
        elif f["filterType"] == "LOT_SIZE":
            rules["stepSize"] = Decimal(f["stepSize"])
            rules["minQty"] = Decimal(f["minQty"])
            rules["maxQty"] = Decimal(f["maxQty"])
        elif f["filterType"] == "MARKET_LOT_SIZE":
            rules["marketStepSize"] = Decimal(f["stepSize"])
            rules["marketMinQty"] = Decimal(f["minQty"])
            rules["marketMaxQty"] = Decimal(f["maxQty"])
        elif f["filterType"] == "MIN_NOTIONAL":
            rules["minNotional"] = Decimal(f["notional"])
    return rules


def round_down_to_step(value, step: Decimal) -> Decimal:
    """Floors value to a multiple of step (0.0012345 with step 0.001 -> 0.001)."""
    value = Decimal(str(value))
    if not step:
        return value
    return (value / step).to_integral_value(rounding=ROUND_DOWN) * step


def to_api_string(value: Decimal) -> str:
    """
    Plain decimal string for the API. str(0.00001) in Python is '1e-05',
    which Binance can't parse, so always format without exponent.
    """
    text = format(value.normalize(), "f")
    return text if text != "-0" else "0"


def apply_symbol_filters(
    order_type: str,
    quantity: float,
    price: Optional[float],
    rules: Dict[str, Decimal],
    mark_price: Optional[float] = None,
) -> Tuple[str, Optional[str]]:
    """
    Rounds quantity/price to the symbol's step and tick size and checks the
    min/max limits. Returns (quantity, price) as strings ready for the API.
    """
    is_market = order_type == "MARKET"
    step = rules.get("marketStepSize" if is_market else "stepSize") or rules.get("stepSize")
    min_qty = rules.get("marketMinQty" if is_market else "minQty") or rules.get("minQty")
    max_qty = rules.get("marketMaxQty" if is_market else "maxQty") or rules.get("maxQty")

    qty = round_down_to_step(quantity, step) if step else Decimal(str(quantity))
    if qty != Decimal(str(quantity)):
        logger.warning(f"Quantity {quantity} rounded down to {to_api_string(qty)} (step size {step})")

    if min_qty is not None and qty < min_qty:
        raise ValidationError(f"Quantity is below the minimum of {to_api_string(min_qty)} for this symbol.")
    if max_qty is not None and qty > max_qty:
        raise ValidationError(f"Quantity is above the maximum of {to_api_string(max_qty)} for this symbol.")

    price_str = None
    ref_price = None
    if price is not None and not is_market:
        tick = rules.get("tickSize")
        px = round_down_to_step(price, tick) if tick else Decimal(str(price))
        if px != Decimal(str(price)):
            logger.warning(f"Price {price} rounded down to {to_api_string(px)} (tick size {tick})")
        if "minPrice" in rules and px < rules["minPrice"]:
            raise ValidationError(f"Price is below the minimum of {to_api_string(rules['minPrice'])}.")
        if rules.get("maxPrice") and px > rules["maxPrice"]:
            raise ValidationError(f"Price is above the maximum of {to_api_string(rules['maxPrice'])}.")
        price_str = to_api_string(px)
        ref_price = px
    elif mark_price is not None:
        ref_price = Decimal(str(mark_price))

    min_notional = rules.get("minNotional")
    if min_notional is not None and ref_price is not None and qty * ref_price < min_notional:
        raise ValidationError(
            f"Order value {to_api_string(qty * ref_price)} USDT is below the minimum of "
            f"{to_api_string(min_notional)} USDT. Increase the quantity."
        )

    return to_api_string(qty), price_str
