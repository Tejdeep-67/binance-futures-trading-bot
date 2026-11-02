from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from bot.exceptions import ValidationError
from bot.filters import apply_symbol_filters, get_symbol_filters, round_down_to_step, to_api_string

# trimmed copy of what /fapi/v1/exchangeInfo returns for BTCUSDT on the testnet
EXCHANGE_INFO = {
    "symbols": [
        {
            "symbol": "BTCUSDT",
            "status": "TRADING",
            "filters": [
                {"filterType": "PRICE_FILTER", "tickSize": "0.10", "minPrice": "261.10", "maxPrice": "809484"},
                {"filterType": "LOT_SIZE", "stepSize": "0.001", "minQty": "0.001", "maxQty": "1000"},
                {"filterType": "MARKET_LOT_SIZE", "stepSize": "0.001", "minQty": "0.001", "maxQty": "120"},
                {"filterType": "MIN_NOTIONAL", "notional": "100"},
            ],
        },
        {"symbol": "OLDUSDT", "status": "SETTLING", "filters": []},
    ]
}


@pytest.fixture
def rules():
    client = MagicMock()
    client.futures_exchange_info.return_value = EXCHANGE_INFO
    return get_symbol_filters(client, "BTCUSDT")


def test_reads_filters(rules):
    assert rules["tickSize"] == Decimal("0.10")
    assert rules["stepSize"] == Decimal("0.001")
    assert rules["marketMaxQty"] == Decimal("120")
    assert rules["minNotional"] == Decimal("100")


def test_unknown_symbol():
    client = MagicMock()
    client.futures_exchange_info.return_value = EXCHANGE_INFO
    with pytest.raises(ValidationError, match="not listed"):
        get_symbol_filters(client, "DOGEUSDT")


def test_symbol_not_trading():
    client = MagicMock()
    client.futures_exchange_info.return_value = EXCHANGE_INFO
    with pytest.raises(ValidationError, match="not trading"):
        get_symbol_filters(client, "OLDUSDT")


def test_round_down_to_step():
    assert round_down_to_step(0.0129, Decimal("0.001")) == Decimal("0.012")
    assert round_down_to_step(65000.17, Decimal("0.10")) == Decimal("65000.1")
    # float noise: 0.1 + 0.2 = 0.30000000000000004
    assert round_down_to_step(0.1 + 0.2, Decimal("0.001")) == Decimal("0.3")


def test_api_string_never_uses_exponent():
    assert to_api_string(Decimal("0.00001")) == "0.00001"
    assert to_api_string(Decimal("1E+2")) == "100"
    assert to_api_string(Decimal("65000.10")) == "65000.1"


def test_limit_order_rounded(rules):
    qty, price = apply_symbol_filters("LIMIT", 0.0157, 65000.17, rules)
    assert (qty, price) == ("0.015", "65000.1")


def test_market_order_has_no_price(rules):
    qty, price = apply_symbol_filters("MARKET", 0.002, None, rules, mark_price=65000)
    assert qty == "0.002"
    assert price is None


def test_quantity_below_min(rules):
    with pytest.raises(ValidationError, match="below the minimum"):
        apply_symbol_filters("LIMIT", 0.0004, 65000, rules)


def test_market_quantity_above_market_max(rules):
    with pytest.raises(ValidationError, match="above the maximum"):
        apply_symbol_filters("MARKET", 150, None, rules, mark_price=65000)


def test_price_below_min_price(rules):
    with pytest.raises(ValidationError, match="Price is below"):
        apply_symbol_filters("LIMIT", 0.01, 100, rules)


def test_min_notional_checked_for_limit(rules):
    # 0.001 * 65000 = 65 USDT < 100
    with pytest.raises(ValidationError, match="Order value"):
        apply_symbol_filters("LIMIT", 0.001, 65000, rules)


def test_min_notional_uses_mark_price_for_market(rules):
    with pytest.raises(ValidationError, match="Order value"):
        apply_symbol_filters("MARKET", 0.001, None, rules, mark_price=65000)
