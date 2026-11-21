import logging
import os
from logging.handlers import RotatingFileHandler
def setup_logger():

    os.makedirs("logs", exist_ok=True)

    logger = logging.getLogger("ROV")
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    file_handler = RotatingFileHandler(
        "logs/rov.log",
        maxBytes=1_000_000,
        backupCount=3
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
