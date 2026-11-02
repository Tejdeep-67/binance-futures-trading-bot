# Binance Futures Testnet Trading Bot

A small Python command-line tool that places MARKET and LIMIT orders on the **Binance USDT-M Futures Testnet**. I built it to learn how a real exchange API works: API keys, request signing, exchange trading rules, and handling errors properly. It only talks to the testnet, so no real money is involved.

## What it does

- Places MARKET and LIMIT orders, BUY or SELL, on USDT-M futures pairs like BTCUSDT
- Checks the input before calling the API (symbol format, side, type, quantity, price)
- Reads the symbol's trading rules from the exchange (tick size, step size, min/max quantity, minimum order value) and rounds the quantity/price so Binance doesn't reject the order with a precision error
- Syncs with the futures server clock so signed requests don't fail with `-1021 Timestamp outside of recvWindow`
- Shows clear error messages in the terminal (missing keys, insufficient margin, no internet) and writes the details to `logs/trading_bot.log`

## Project structure

```
bot/
  client.py          # creates the testnet client, time sync, error handling decorator
  filters.py         # exchange filters: rounding to step/tick size, min qty, min notional
  orders.py          # builds the order params and sends the order
  validators.py      # input checks before any API call
  exceptions.py      # ValidationError / APIError / NetworkError
  logging_config.py  # rotating log file in logs/
tests/               # pytest tests, the Binance client is mocked
cli.py               # Typer CLI entry point
```

## Setup

You need Python 3.10+ and a Futures Testnet account.

1. Log in at https://testnet.binancefuture.com and create an API key (this is separate from your normal Binance account and from the spot testnet).
2. Install:

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and put your testnet keys in it:

```env
BINANCE_API_KEY=your_testnet_api_key_here
BINANCE_SECRET_KEY=your_testnet_secret_key_here
```

`.env` is in `.gitignore`, so the keys never get committed.

## Usage

```bash
python cli.py --help

# market buy 0.002 BTC
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.002

# limit sell, stays open until filled or cancelled (GTC)
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.002 --price 120000

# short options work too
python cli.py -s ETHUSDT -S BUY -t LIMIT -q 0.05 -p 2500
```

Example output for a limit order (your order ID will be different):

```
      ORDER SUMMARY
┌──────────┬─────────┐
│   Symbol │ BTCUSDT │
│     Side │ SELL    │
│     Type │ LIMIT   │
│ Quantity │ 0.002   │
│    Price │ 120000  │
└──────────┴─────────┘
Submitting order...

Success!
Order ID: 4071223389
Status: NEW
Quantity Sent: 0.002
Executed Quantity: 0
```

Note: Binance has a minimum order value on futures (for BTCUSDT on the testnet it was 50 USDT when I checked), so very small quantities get rejected before the order is sent.

## How a request works

1. `validators.py` checks the arguments.
2. `client.py` loads the keys from `.env`, creates a python-binance `Client(testnet=True)` and asks the futures server for its time to work out the clock offset.
3. `filters.py` downloads `exchangeInfo`, finds the symbol and rounds the quantity down to the step size and the price to the tick size. Values are sent as plain strings (Python prints `0.00001` as `1e-05`, which the API doesn't accept).
4. `orders.py` builds the params (LIMIT orders get `timeInForce=GTC`) and calls `futures_create_order`. python-binance adds the `timestamp` and signs the query string with HMAC-SHA256 using the secret key.
5. Errors from Binance, the network or my own checks are turned into one of three exceptions and printed as a short message.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

The tests don't need keys or internet. They mock the Binance client and check the validators, the rounding rules, the order params, the error handling, and that the request sent over HTTP has the right timestamp and HMAC signature.

## Limitations

- Testnet only, and only MARKET and LIMIT orders (no stop orders, no cancelling, no position view yet).
- One-way position mode is assumed (no `positionSide` for hedge mode).
- Leverage and margin type are whatever is set on the testnet account.
- The testnet sometimes resets balances or has thin order books, so fills can look odd.

## Ideas for next

- cancel / list open orders and show positions
- STOP_MARKET and TAKE_PROFIT orders
- set leverage from the CLI
