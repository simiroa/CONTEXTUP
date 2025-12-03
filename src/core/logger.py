import logging
import os
import sys
from pathlib import Path
from datetime import datetime

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LOG_FILE = PROJECT_ROOT / "debug.log"

# Log Levels
LEVEL_MAP = {
    "Debug (All)": logging.DEBUG,
    "Minimal (Errors Only)": logging.ERROR,
    "Disabled": 100  # Higher than CRITICAL
}

def setup_logger(log_level_str="Debug (All)"):
    """
    Sets up the global logger based on the provided string level.
    """
    level = LEVEL_MAP.get(log_level_str, logging.DEBUG)
    
    # Create logger
    logger = logging.getLogger("ContextUp")
    logger.setLevel(logging.DEBUG) # Capture all, handlers will filter
    
    # Clear existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
        
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # File Handler (if not disabled)
    if level < 100:
        try:
            file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Failed to setup file logging: {e}")

    # Console Handler (Always Debug for dev, or match file?)
    # For now, let's keep console output for immediate feedback if running in terminal
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO) # Keep console clean
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# Global instance (can be re-configured)
# Default to Debug until settings load
logger = setup_logger()

def log_execution(tool_name, args=None):
    """Helper to log tool execution start."""
    msg = f"Executing: {tool_name}"
    if args:
        msg += f" | Args: {args}"
    logger.info(msg)

def log_error(tool_name, error):
    """Helper to log errors."""
    logger.error(f"Error in {tool_name}: {error}", exc_info=True)
