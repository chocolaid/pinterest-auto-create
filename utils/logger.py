import logging
import os
import sys
from datetime import datetime

def setup_logger(name, log_level=logging.INFO, log_to_file=True, log_to_console=True):
    """Set up and configure a logger
    
    Args:
        name (str): Logger name
        log_level (int): Logging level
        log_to_file (bool): Whether to log to a file
        log_to_console (bool): Whether to log to the console
        
    Returns:
        logging.Logger: The configured logger
    """
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add file handler if requested
    if log_to_file:
        log_file = os.path.join(logs_dir, f"{name}_{datetime.now().strftime('%Y-%m-%d')}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Add console handler if requested
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger 