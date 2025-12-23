"""
Centralized path definitions for ContextUp.
Encapsulates directory logic to ensure consistency across modules.
"""
from pathlib import Path
import os
import sys

# Define Project Root (ContextUp/)
# src/utils/paths.py -> src/utils -> src -> ContextUp
CURRENT_DIR = Path(__file__).resolve().parent
SRC_DIR = CURRENT_DIR.parent
PROJECT_ROOT = SRC_DIR.parent

# Resources
RESOURCES_DIR = SRC_DIR / "resources"
AI_MODELS_DIR = RESOURCES_DIR / "ai_models"
BIN_DIR = RESOURCES_DIR / "bin"

# Standard Model Directories
MARIGOLD_DIR = AI_MODELS_DIR / "marigold"
REMBG_DIR = AI_MODELS_DIR / "u2net" # Rembg uses u2net folder name usually, or we enforce it
OCR_DIR = AI_MODELS_DIR / "rapidocr"
WHISPER_DIR = AI_MODELS_DIR / "whisper"
DEMUCS_DIR = AI_MODELS_DIR / "demucs"

def ensure_dirs():
    """Ensure all critical directories exist."""
    RESOURCES_DIR.mkdir(parents=True, exist_ok=True)
    AI_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    BIN_DIR.mkdir(parents=True, exist_ok=True)

# Auto-ensure on import
ensure_dirs()
