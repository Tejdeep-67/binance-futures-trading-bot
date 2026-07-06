# Binance Futures Testnet Trading Bot

A professional command-line Python application for interacting with the Binance Futures Testnet (USDT-M Futures). It allows users to place MARKET and LIMIT orders through the Binance API with robust validation, clean architecture, and structured logging.

## Features

- **Order Placement**: Place MARKET and LIMIT orders.
- **Support for sides**: BUY and SELL.
- **Robust Validation**: Extensive input validation before hitting the API.
- **CLI Interface**: Built with Typer and Rich for a colored, professional terminal experience.
- **Structured Logging**: Logs all actions (startup, requests, responses, and errors) to a rotating file in the `logs` directory without exposing technical stack traces to the user.
- **Error Handling**: Graceful error handling for API, network, and validation errors.

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # Package initializer
│   ├── client.py            # API client initialization and request handling
│   ├── exceptions.py        # Custom exceptions
│   ├── logging_config.py    # Structured logging setup
│   ├── orders.py            # Business logic for orders
│   └── validators.py        # Input validation logic
├── logs/
│   └── trading_bot.log      # Application logs
├── .env.example             # Environment variable template
├── .gitignore               # Ignored files
├── cli.py                   # Typer CLI application entry point
├── requirements.txt         # Project dependencies
└── README.md                # Project documentation
```

## Installation

### Prerequisites
- Python 3.11+
- A Binance Testnet account with generated API Keys.

### Virtual Environment Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
2. Activate the virtual environment:
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

### Requirements Installation

Install the required packages using pip:
```bash
pip install -r requirements.txt
```

### Environment Variable Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and fill in your Binance Futures Testnet credentials:
   ```env
   BINANCE_API_KEY=your_testnet_api_key_here
   BINANCE_SECRET_KEY=your_testnet_secret_key_here
   ```

## Running Examples

You can run the application using the CLI entry point `cli.py`.

### Market Order Example

Place a Market Buy order for BTCUSDT:
```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

### Limit Order Example

Place a Limit Sell order for BTCUSDT at a specific price:
```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 120000
```

### Expected Output

```
====================================
ORDER SUMMARY
====================================
Symbol     : BTCUSDT
Side       : BUY
Type       : MARKET
Quantity   : 0.001
====================================
Submitting order...

Success!
Order ID: 123456789
Status: NEW
Executed Quantity: 0.0
Average Price: 0.0
```

## Logging Information

All events are logged in the `logs/trading_bot.log` file.
Logs capture:
- Application startup
- Incoming CLI request and validated inputs
- API request parameters
- API responses (Order success, Order ID, etc.)
- Errors (Network failures, Invalid inputs, API rejections like "Insufficient margin")

The logger uses a Rotating File Handler to keep log size manageable. Users will not see ugly stack traces in the console; they are recorded in the logs.

## Assumptions
- The application currently interacts **exclusively** with the Binance Futures Testnet (`testnet.binancefuture.com`).
- Assumes the trading pair follows standard Binance naming (e.g., `BTCUSDT`).

## Troubleshooting
- **APIError (Unauthorized/Invalid API Key)**: Double-check your `.env` file credentials. Ensure you created keys on the *Futures Testnet* specifically, not the spot testnet or mainnet.
- **ValidationError**: Make sure your `quantity` and `price` values are greater than zero, and the `side`/`type` are correctly capitalized (or left to the CLI to auto-capitalize).
