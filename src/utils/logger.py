import logging
import sys
from logging.handlers import RotatingFileHandler

import colorlog


def create_logger(
    level=logging.INFO,
    log_file="System.log",
    max_bytes=10 * 1024 * 1024,
    backup_count=5,
):
    logger = logging.getLogger()
    logger.setLevel(level)
    log_config = {
        "DEBUG": {"level": 10, "color": "purple"},
        "INFO": {"level": 20, "color": "green"},
        "WARNING": {"level": 30, "color": "yellow"},
        "ERROR": {"level": 40, "color": "red"},
    }
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s[%(asctime)-15s] [%(levelname)8s]%(reset)s: %(message)s",
        log_colors={key: conf["color"] for key, conf in log_config.items()},
    )

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)

    # File Handler with Rotation
    file_formatter = logging.Formatter("[%(asctime)-15s] [%(levelname)8s]: %(message)s")
    file_handler = RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count
    )
    file_handler.setFormatter(file_formatter)

    logger.handlers.clear()
    logger.addHandler(sh)
    logger.addHandler(file_handler)

    return logger


logger = create_logger()
