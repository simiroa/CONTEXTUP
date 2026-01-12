"""
Internationalization (i18n) Module for ContextUp.

Provides a simple, centralized system for loading and accessing localized strings.
Usage:
    from utils.i18n import t, get_language, set_language
    
    # Get a translated string
    label_text = t("common.cancel")  # Returns "취소" in Korean, "Cancel" in English
    
    # With placeholders
    status_text = t("image_convert_gui.convert_n_files", count=5)  # "5개 파일 변환"
"""
import json
from pathlib import Path
from functools import lru_cache
from typing import Optional, Any
from core.paths import SETTINGS_FILE

# Path to i18n directory relative to this file
I18N_DIR = Path(__file__).parent.parent.parent / "config" / "i18n"
DEFAULT_LANGUAGE = "en"

# Global state
_current_language = DEFAULT_LANGUAGE
_strings: dict = {}


def _get_config_dir() -> Path:
    """Get config directory path."""
    return Path(__file__).parent.parent.parent / "config"


def _load_settings_language() -> str:
    """Load language setting from settings.json, default to 'en'."""
    try:
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
                return settings.get("LANGUAGE", DEFAULT_LANGUAGE)
    except Exception:
        pass
    return DEFAULT_LANGUAGE


@lru_cache(maxsize=4)
def _load_language_file(lang: str) -> dict:
    """Load and cache a language file."""
    path = I18N_DIR / f"{lang}.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _init():
    """Initialize the i18n system."""
    global _current_language, _strings
    
    _current_language = _load_settings_language()
    
    # Load English as fallback
    _strings = _load_language_file(DEFAULT_LANGUAGE)
    
    # Overlay with selected language if different
    if _current_language != DEFAULT_LANGUAGE:
        lang_strings = _load_language_file(_current_language)
        _merge_dicts(_strings, lang_strings)


def _merge_dicts(base: dict, overlay: dict):
    """Recursively merge overlay into base."""
    for key, value in overlay.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _merge_dicts(base[key], value)
        else:
            base[key] = value


def get_language() -> str:
    """Get the current language code."""
    return _current_language


def set_language(lang: str):
    """
    Set the current language and reload strings.
    
    Args:
        lang: Language code (e.g., 'en', 'ko')
    """
    global _current_language
    
    # Clear cache
    _load_language_file.cache_clear()
    
    _current_language = lang
    _init()


def get_available_languages() -> list[dict]:
    """
    Get list of available languages.
    
    Returns:
        List of dicts with 'code' and 'name' keys
    """
    languages = []
    for path in I18N_DIR.glob("*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                meta = data.get("_meta", {})
                languages.append({
                    "code": path.stem,
                    "name": meta.get("name", path.stem),
                    "description": meta.get("description", "")
                })
        except Exception:
            pass
    return languages


def t(key: str, default: Optional[str] = None, **kwargs: Any) -> str:
    """
    Get a translated string.
    
    Args:
        key: Dot-separated key path (e.g., "common.cancel", "image_convert_gui.title")
        default: Default value if key not found (defaults to key itself)
        **kwargs: Placeholder values for string formatting
        
    Returns:
        Translated string with placeholders filled in
        
    Example:
        t("common.cancel")  # "Cancel" or "취소"
        t("video_convert_gui.converted_result", success=5, total=10)  # "Converted 5/10 files."
    """
    # Ensure initialized
    if not _strings:
        _init()
    
    # Navigate the nested structure
    parts = key.split(".")
    value = _strings
    
    for part in parts:
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            # Key not found, return default
            return default if default is not None else key
    
    if not isinstance(value, str):
        return default if default is not None else key
    
    # Format with kwargs if provided
    if kwargs:
        try:
            # Support both {key} and {count} style placeholders
            return value.format(**kwargs)
        except (KeyError, ValueError):
            return value
    
    return value


# Alias for convenience
_ = t


# Initialize on module load
_init()


if __name__ == "__main__":
    # Test the i18n system
    print(f"Current language: {get_language()}")
    print(f"Available languages: {get_available_languages()}")
    print()
    
    # Test translations
    print("Testing English (default):")
    print(f"  common.cancel: {t('common.cancel')}")
    print(f"  common.success: {t('common.success')}")
    
    print()
    print("Testing with placeholders:")
    print(f"  convert_n_files: {t('image_convert_gui.convert_n_files', count=5)}")
    print(f"  converted_result: {t('video_convert_gui.converted_result', success=3, total=5)}")
    
    print()
    print("Testing Korean:")
    set_language("ko")
    print(f"  common.cancel: {t('common.cancel')}")
    print(f"  features.ai.marigold_pbr: {t('features.ai.marigold_pbr')}")

def get_localized_name(name_str: str) -> str:
    """
    Parses a name string in the format "English Name (Korean Name)"
    and returns the appropriate name based on the current language.
    
    Args:
        name_str: The name string, e.g., "ai_text_lab (AI 텍스트 연구소)"
        
    Returns:
        The localized name.
    """
    import re
    # Check for "Name (Bilingual Name)" pattern
    # Only split if the text in parentheses contains non-ASCII characters (e.g., Korean)
    match = re.match(r"^(.*?)\s*\((.*[^\x00-\x7F].*)\)$", name_str.strip())
    
    if match:
        eng_name = match.group(1).strip()
        kor_name = match.group(2).strip()
        
        if get_language() == "ko":
            return kor_name
        return eng_name
        
    return name_str
