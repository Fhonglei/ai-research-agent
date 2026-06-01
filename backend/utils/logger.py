import logging
import sys
from pathlib import Path
from datetime import datetime


LOG_DIR = Path(__file__).resolve().parent.parent / "logs"


def setup_logger(name: str = "ai_research_agent") -> logging.Logger:
    """
    Set up and return a logger that writes to both console and file.

    Log files are stored in the backend/logs/ directory with a timestamp-based
    filename. Console output uses a simplified format for readability.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers if logger is reconfigured
    if logger.handlers:
        logger.handlers.clear()

    # File handler — detailed format with timestamps
    log_filename = LOG_DIR / f'backend_{datetime.now().strftime("%Y%m%d")}.log'
    file_handler = logging.FileHandler(str(log_filename), encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler — concise format for terminal output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()
