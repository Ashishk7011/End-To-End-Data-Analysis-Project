import logging
import os
from datetime import datetime


def get_logger(name: str, log_file_name: str = None, level=logging.INFO):
    """
    Creates and returns a logger instance with a custom file name.

    Args:
        name (str): Name of the logger (usually __name__)
        log_file_name (str): Custom log file name (optional)
        level: Logging level

    Returns:
        logger object
    """

    # Create logs directory
    logs_dir = os.path.join(os.getcwd(), "logs", datetime.now().strftime("%m_%d_%Y_%H_%M_%S"))
    os.makedirs(logs_dir, exist_ok=True)

    # Default filename if not provided
    if log_file_name is None:
        log_file_name = datetime.now().strftime("%m_%d_%Y_%H_%M_%S") + ".log"

    log_file_path = os.path.join(logs_dir, log_file_name)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers
    if not logger.handlers:
        file_handler = logging.FileHandler(log_file_path)
        formatter = logging.Formatter(
            "[ %(asctime)s ] %(lineno)d %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

    return logger