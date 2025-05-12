import logging

# Configure the logging settings
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

def log_info(message):
    logging.info(message)

def log_warning(message):
    logging.warning(message)

def log_error(message):
    logging.error(message)

def log_debug(message):
    logging.debug(message)

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name"""
    logger = logging.getLogger(name)
    return logger

# Example usage in other modules:
# logger = get_logger(__name__)
# logger.info("This is an info message")