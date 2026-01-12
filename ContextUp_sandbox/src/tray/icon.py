"""
Tray Icon Builder
Loads or generates the tray icon image.
"""
from pathlib import Path
from PIL import Image, ImageDraw

from core.paths import ASSETS_DIR
from core.logger import setup_logger

logger = setup_logger("tray_icon")


def build_icon_image() -> Image.Image:
    """
    Load the main ContextUp icon for tray.
    Falls back to a generated icon if file not found.
    """
    try:
        # Load ContextUp.ico - single source of truth
        icon_path = ASSETS_DIR / "icons" / "ContextUp.ico"
        if icon_path.exists():
            img = Image.open(icon_path)
            # Resize for tray (typically 64x64 or 32x32)
            img = img.resize((64, 64), Image.Resampling.LANCZOS)
            return img
    except Exception as e:
        logger.warning(f"Failed to load ContextUp.ico: {e}")
    
    # Fallback: Generate a simple icon if file not found
    return _generate_fallback_icon()


def _generate_fallback_icon(size: int = 64) -> Image.Image:
    """Generate a simple fallback tray icon."""
    img = Image.new("RGBA", (size, size), (52, 152, 219, 255))  # Blue background
    dc = ImageDraw.Draw(img)
    # Draw a simple white square in center
    margin = size // 4
    dc.rectangle((margin, margin, size - margin, size - margin), fill=(255, 255, 255, 255))
    return img
