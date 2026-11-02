import hashlib
import hmac
from unittest.mock import MagicMock, patch
from urllib.parse import urlencode

import pytest
import requests
from binance.client import Client
from binance.exceptions import BinanceAPIException

from bot.exceptions import APIError, NetworkError
from bot.orders import build_order_params, place_order
from tests.test_filters import EXCHANGE_INFO


def test_market_params():
    params = build_order_params("btcusdt", "buy", "market", "0.002")
    assert params == {"symbol": "BTCUSDT", "side": "BUY", "type": "MARKET", "quantity": "0.002"}


def test_limit_params_have_price_and_time_in_force():
    params = build_order_params("BTCUSDT", "SELL", "LIMIT", "0.002", "70000.1")
    assert params["price"] == "70000.1"
    assert params["timeInForce"] == "GTC"


def fake_client():
    client = MagicMock()
    client.futures_exchange_info.return_value = EXCHANGE_INFO
    client.futures_mark_price.return_value = {"markPrice": "65000"}
    client.futures_create_order.return_value = {"orderId": 42, "status": "NEW", "origQty": "0.002"}
    return client


def test_place_market_order_sends_rounded_params():
    client = fake_client()
    with patch("bot.orders.get_binance_client", return_value=client):
        resp = place_order("BTCUSDT", "BUY", "MARKET", 0.0025)
    assert resp["orderId"] == 42
    client.futures_create_order.assert_called_once_with(
        symbol="BTCUSDT", side="BUY", type="MARKET", quantity="0.002"
    )


def test_place_limit_order():
    client = fake_client()
    with patch("bot.orders.get_binance_client", return_value=client):
        place_order("BTCUSDT", "SELL", "LIMIT", 0.002, 70000.15)
    client.futures_create_order.assert_called_once_with(
        symbol="BTCUSDT", side="SELL", type="LIMIT", quantity="0.002", price="70000.1", timeInForce="GTC"
    )


def test_binance_error_becomes_api_error():
    client = fake_client()
    resp = MagicMock(status_code=400, text='{"code":-2019,"msg":"Margin is insufficient."}')
    client.futures_create_order.side_effect = BinanceAPIException(resp, 400, resp.text)
    with patch("bot.orders.get_binance_client", return_value=client):
        with pytest.raises(APIError, match="Margin is insufficient"):
            place_order("BTCUSDT", "BUY", "MARKET", 0.002)


def test_connection_error_becomes_network_error():
    client = fake_client()
    client.futures_create_order.side_effect = requests.exceptions.ConnectionError("dns failed")
    with patch("bot.orders.get_binance_client", return_value=client):
        with pytest.raises(NetworkError):
            place_order("BTCUSDT", "BUY", "MARKET", 0.002)


def test_missing_keys_message_is_kept(monkeypatch):
    monkeypatch.delenv("BINANCE_API_KEY", raising=False)
    monkeypatch.delenv("BINANCE_SECRET_KEY", raising=False)
    with patch("bot.client.load_dotenv"):
        with pytest.raises(APIError, match="must be set"):
            place_order("BTCUSDT", "BUY", "MARKET", 0.002)


def test_request_is_signed_with_hmac_sha256():
    """
    Mock the HTTP session and check what python-binance actually sends:
    a timestamp (with our clock offset) and an HMAC-SHA256 signature of the
    query string made with the secret key.
    """
    secret = "test-secret"
    client = Client("test-key", secret, testnet=True, ping=False)
    client.timestamp_offset = -1000

    fake_resp = MagicMock(status_code=200, text='{"orderId": 1}')
    fake_resp.json.return_value = {"orderId": 1}
    client.session = MagicMock()
    client.session.post.return_value = fake_resp
    client.session.headers = {}

    params = build_order_params("BTCUSDT", "BUY", "LIMIT", "0.002", "65000.1")
    with patch("time.time", return_value=1_700_000_000.0):
        client.futures_create_order(**params)

    url = client.session.post.call_args.args[0]
    sent = client.session.post.call_args.kwargs["data"]
    assert url.startswith("https://testnet.binancefuture.com/fapi/v1/order")

    sent = dict(sent)
    assert sent["timestamp"] == str(1_700_000_000_000 - 1000)
    signature = sent.pop("signature")
    query = urlencode(sorted(sent.items()))
    expected = hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()
    assert signature == expected
