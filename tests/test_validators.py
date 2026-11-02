import pytest

from bot.exceptions import ValidationError
from bot.validators import validate_order_input


def test_valid_market_order_passes():
    validate_order_input("BTCUSDT", "BUY", "MARKET", 0.001)


def test_valid_limit_order_passes_lowercase():
    validate_order_input("ethusdt", "sell", "limit", 0.01, 3000)


@pytest.mark.parametrize("symbol", ["", "   ", "BTC-USDT", "BTCBUSD", "BTC"])
def test_bad_symbols_rejected(symbol):
    with pytest.raises(ValidationError):
        validate_order_input(symbol, "BUY", "MARKET", 0.001)


def test_bad_side_rejected():
    with pytest.raises(ValidationError, match="BUY or SELL"):
        validate_order_input("BTCUSDT", "HOLD", "MARKET", 0.001)


def test_unsupported_type_rejected():
    with pytest.raises(ValidationError, match="MARKET or LIMIT"):
        validate_order_input("BTCUSDT", "BUY", "STOP", 0.001)


@pytest.mark.parametrize("qty", [0, -1])
def test_quantity_must_be_positive(qty):
    with pytest.raises(ValidationError, match="Quantity"):
        validate_order_input("BTCUSDT", "BUY", "MARKET", qty)


def test_limit_needs_price():
    with pytest.raises(ValidationError, match="require a price"):
        validate_order_input("BTCUSDT", "BUY", "LIMIT", 0.001)


def test_limit_price_must_be_positive():
    with pytest.raises(ValidationError, match="Price"):
        validate_order_input("BTCUSDT", "BUY", "LIMIT", 0.001, -5)
