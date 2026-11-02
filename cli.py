import typer
from rich.console import Console
from rich.table import Table
from typing import Optional

from bot.orders import place_order
from bot.validators import validate_order_input
from bot.exceptions import TradingBotError
from bot.logging_config import setup_logger

app = typer.Typer(help="Binance Futures Testnet Trading Bot CLI")
console = Console()
logger = setup_logger()

def display_summary(symbol: str, side: str, order_type: str, quantity: float, price: Optional[float]):
    table = Table(title="ORDER SUMMARY", show_header=False, show_lines=True)
    table.add_column("Property", style="cyan", justify="right")
    table.add_column("Value", style="magenta")
    
    table.add_row("Symbol", symbol.upper())
    table.add_row("Side", side.upper())
    table.add_row("Type", order_type.upper())
    table.add_row("Quantity", str(quantity))
    if order_type.upper() == "LIMIT":
        table.add_row("Price", str(price))
    
    console.print(table)
    console.print("[bold yellow]Submitting order...[/bold yellow]")

@app.command()
def place_order_cmd(
    symbol: str = typer.Option(..., "--symbol", "-s", help="Trading symbol (e.g., BTCUSDT)"),
    side: str = typer.Option(..., "--side", "-S", help="Order side: BUY or SELL"),
    order_type: str = typer.Option(..., "--type", "-t", help="Order type: MARKET or LIMIT"),
    quantity: float = typer.Option(..., "--quantity", "-q", help="Order quantity"),
    price: Optional[float] = typer.Option(None, "--price", "-p", help="Order price (Required for LIMIT)"),
):
    """
    Place a new order on Binance Futures Testnet.
    """
    logger.info("Application startup - Incoming CLI request")
    
    try:
        validate_order_input(symbol, side, order_type, quantity, price)
        logger.info("Input validated successfully.")

        if order_type.upper() == "MARKET" and price is not None:
            console.print("[yellow]Note: --price is ignored for MARKET orders.[/yellow]")
            price = None
        
        display_summary(symbol, side, order_type, quantity, price)
        
        response = place_order(symbol, side, order_type, quantity, price)
        
        console.print("\n[bold green]Success![/bold green]")
        console.print(f"[bold]Order ID:[/bold] {response.get('orderId')}")
        console.print(f"[bold]Status:[/bold] {response.get('status')}")
        console.print(f"[bold]Quantity Sent:[/bold] {response.get('origQty', quantity)}")
        console.print(f"[bold]Executed Quantity:[/bold] {response.get('executedQty', 0)}")
        avg_price = response.get('avgPrice')
        # a new LIMIT order comes back with avgPrice "0.00", no point showing that
        if avg_price and float(avg_price) > 0:
            console.print(f"[bold]Average Price:[/bold] {avg_price}")
        
    except TradingBotError as e:
        console.print("\n[bold red]Order failed[/bold red]")
        console.print(f"[red]Reason:[/red] {str(e)}")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        console.print("\n[bold red]An unexpected error occurred[/bold red]")
        console.print("[red]Please check the logs for details.[/red]")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
