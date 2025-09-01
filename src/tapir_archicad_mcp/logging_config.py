import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path.home() / ".tapir_mcp" / "logs"
LOG_FILE = LOG_DIR / "tapir_mcp_server.log"


def set_debug_lvl_for_modules() -> None:
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("mcp").setLevel(logging.WARNING)
    logging.getLogger("multiconn_archicad").setLevel(logging.INFO)
    logging.getLogger("faiss").setLevel(logging.INFO)
    logging.getLogger("sentence_transformers").setLevel(logging.INFO)


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
    set_debug_lvl_for_modules()

    # --- File Handler ---
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(log_formatter)

    # --- Console Handler ---
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(log_formatter)

    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logging.info(f"Logging initialized. Persistent logs will be stored in: {LOG_FILE}")