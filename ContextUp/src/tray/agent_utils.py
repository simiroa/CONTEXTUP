"""
Tray Agent Utilities
Process management and logging setup.
"""
import os
import sys
import subprocess
import logging
from pathlib import Path

from core.paths import LOGS_DIR
from core.logger import setup_logger

logger = setup_logger("tray_utils")

# File paths for IPC and process management
PID_FILE = LOGS_DIR / "tray_agent.pid"
HANDSHAKE_FILE = LOGS_DIR / "tray_info.json"
LOG_FILE = LOGS_DIR / "tray_agent.log"


def kill_pid(pid: int):
    """Terminate a process by PID using taskkill."""
    try:
        subprocess.run(
            f"taskkill /PID {pid} /F", 
            shell=True, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )
    except Exception:
        pass


def pre_kill_existing():
    """
    Kill any existing tray agent instance before starting a new one.
    Uses PID file as primary mechanism.
    """
    my_pid = os.getpid()
    
    # Check PID file
    if PID_FILE.exists():
        try:
            old_pid = int(PID_FILE.read_text().strip())
            if old_pid != my_pid:
                kill_pid(old_pid)
        except Exception:
            pass
        
        try:
            PID_FILE.unlink()
        except Exception:
            pass


def setup_file_logging():
    """Configure file-based logging for tray agent."""
    try:
        LOG_FILE.parent.mkdir(exist_ok=True, parents=True)
        fh = logging.FileHandler(LOG_FILE, encoding='utf-8')
        fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(fh)
        logger.setLevel(logging.DEBUG)
    except Exception as e:
        logger.warning(f"Failed to setup file logging: {e}")


def write_pid():
    """Write current process PID to file."""
    try:
        PID_FILE.parent.mkdir(exist_ok=True, parents=True)
        PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
    except Exception as e:
        logger.warning(f"PID write failed: {e}")


def cleanup_files():
    """Remove PID and handshake files on exit."""
    try:
        if PID_FILE.exists():
            PID_FILE.unlink()
        if HANDSHAKE_FILE.exists():
            HANDSHAKE_FILE.unlink()
    except Exception:
        pass
