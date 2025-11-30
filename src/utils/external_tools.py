"""
Helper utilities for locating external tools.
"""
from pathlib import Path

from core.settings import load_settings

def _get_tools_root():
    """Get the tools directory root."""
    current_dir = Path(__file__).parent.parent.parent
    return current_dir / "tools"

def get_mayo():
    """Get path to mayo-conv.exe."""
    settings = load_settings()
    if settings.get("MAYO_PATH") and Path(settings["MAYO_PATH"]).exists():
        return settings["MAYO_PATH"]

    mayo_path = _get_tools_root() / "mayo" / "mayo-conv.exe"
    if mayo_path.exists():
        return str(mayo_path)
    raise FileNotFoundError(f"Mayo not found at {mayo_path}")

def get_blender():
    """Get path to blender.exe."""
    settings = load_settings()
    if settings.get("BLENDER_PATH") and Path(settings["BLENDER_PATH"]).exists():
        return settings["BLENDER_PATH"]

    blender_root = _get_tools_root() / "blender"
    
    # Search for blender.exe recursively
    for blender_exe in blender_root.rglob("blender.exe"):
        return str(blender_exe)
    
    raise FileNotFoundError(f"Blender not found in {blender_root}")

def get_quadwild():
    """Get path to quadwild.exe."""
    quadwild_path = _get_tools_root() / "quadwild" / "quadwild.exe"
    if quadwild_path.exists():
        return str(quadwild_path)
    raise FileNotFoundError(f"QuadWild not found at {quadwild_path}")

def get_realesrgan():
    """Get path to realesrgan-ncnn-vulkan.exe."""
    realesrgan_path = _get_tools_root() / "realesrgan" / "realesrgan-ncnn-vulkan.exe"
    if realesrgan_path.exists():
        return str(realesrgan_path)
    raise FileNotFoundError(f"RealESRGAN not found at {realesrgan_path}")

def get_ffmpeg():
    """Get path to ffmpeg.exe."""
    settings = load_settings()
    if settings.get("FFMPEG_PATH") and Path(settings["FFMPEG_PATH"]).exists():
        return settings["FFMPEG_PATH"]

    # Check tools/ffmpeg/bin/ffmpeg.exe
    ffmpeg_path = _get_tools_root() / "ffmpeg" / "bin" / "ffmpeg.exe"
    if ffmpeg_path.exists():
        return str(ffmpeg_path)
    
    # Check tools/ffmpeg/ffmpeg.exe
    ffmpeg_path = _get_tools_root() / "ffmpeg" / "ffmpeg.exe"
    if ffmpeg_path.exists():
        return str(ffmpeg_path)
        
    # Fallback to system path
    return "ffmpeg"
