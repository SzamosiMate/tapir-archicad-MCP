import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path.home() / ".tapir_mcp" / "logs"
LOG_FILE = LOG_DIR / "tapir_mcp_server.log"


def setup_logging():
    """
    Configures the root logger to output to both the console and a rotating file.
    This should be called once at the beginning of the application's lifecycle.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    log_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # --- File Handler ---
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5
    )
    file_handler.setFormatter(log_formatter)

    # --- Console Handler ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)

    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logging.info(f"Logging initialized. Persistent logs will be stored in: {LOG_FILE}")