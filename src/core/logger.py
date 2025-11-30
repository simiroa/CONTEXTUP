import logging
import sys
from pathlib import Path

def setup_logger(name: str = "context_menu", log_file: str = "debug.log", level=logging.DEBUG):
    """
    Sets up a logger that writes to a file and stderr.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create handlers
    # File handler
    log_path = Path(log_file)
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(level)
    
    # Console handler (stderr)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    
    # Create formatters and add it to handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to the logger
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
    return logger
