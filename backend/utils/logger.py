import logging
from logging.handlers import RotatingFileHandler
import os

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)


def setup_logger():

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    # ================= CONSOLE =================

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # ================= APP LOG =================

    app_log = RotatingFileHandler(
        os.path.join(LOG_DIR, "app.log"),
        maxBytes=5_000_000,
        backupCount=5
    )
    app_log.setFormatter(formatter)

    # ================= ERROR LOG =================

    error_log = RotatingFileHandler(
        os.path.join(LOG_DIR, "error.log"),
        maxBytes=5_000_000,
        backupCount=5
    )
    error_log.setLevel(logging.ERROR)
    error_log.setFormatter(formatter)

    # ================= ADD =================

    logger.handlers.clear()
    logger.addHandler(console_handler)
    logger.addHandler(app_log)
    logger.addHandler(error_log)

    return logger
