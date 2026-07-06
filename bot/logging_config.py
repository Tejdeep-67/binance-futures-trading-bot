import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger() -> logging.Logger:
    """
    Configures and returns the application logger.
    Logs are written to logs/trading_bot.log with a rotating file handler.
    """
    logger = logging.getLogger("trading_bot")
    
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, "trading_bot.log")

    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    
    return logger
