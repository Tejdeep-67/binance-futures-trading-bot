from typing import Optional
from bot.exceptions import ValidationError
from bot.logging_config import setup_logger

logger = setup_logger()

def validate_order_input(symbol: str, side: str, order_type: str, quantity: float, price: Optional[float] = None) -> None:
    """
    Validates user input before sending an API request.
    Raises ValidationError if any condition fails.
    """
    if not symbol or not isinstance(symbol, str) or symbol.strip() == "":
        logger.error("Validation failed: Symbol cannot be empty")
        raise ValidationError("Symbol cannot be empty.")

    if side.upper() not in ["BUY", "SELL"]:
        logger.error(f"Validation failed: Invalid side '{side}'")
        raise ValidationError("Side must be BUY or SELL.")

    if order_type.upper() not in ["MARKET", "LIMIT"]:
        logger.error(f"Validation failed: Invalid order type '{order_type}'")
        raise ValidationError("Type must be MARKET or LIMIT.")

    if quantity <= 0:
        logger.error(f"Validation failed: Quantity {quantity} is not greater than zero")
        raise ValidationError("Quantity must be greater than zero.")

    if order_type.upper() == "LIMIT":
        if price is None:
            logger.error("Validation failed: Price is required for LIMIT orders")
            raise ValidationError("LIMIT orders require a price.")
        if price <= 0:
            logger.error(f"Validation failed: Price {price} is not greater than zero")
            raise ValidationError("Price must be greater than zero.")
