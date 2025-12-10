from pathlib import Path

def get_safe_path(path: Path, max_attempts: int = 999) -> Path:
    """
    Return a non-conflicting path by appending _01, _02, ... before the suffix.
    Preserves the original stem/suffix for readability.
    """
    path = Path(path)
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix

    for idx in range(1, max_attempts + 1):
        candidate = path.with_name(f"{stem}_{idx:02d}{suffix}")
        if not candidate.exists():
            return candidate

    # Fallback: timestamp-based name if all attempts exhausted
    return path.with_name(f"{stem}_safe{suffix}")
