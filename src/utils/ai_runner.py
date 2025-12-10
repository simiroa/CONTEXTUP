"""
Utility to run AI scripts using the embedded Python environment.
"""
import subprocess
import sys
from pathlib import Path

def _find_python():
    """
    Prefer the embedded python at tools/python/python.exe,
    then fallback to config.settings.PYTHON_PATH, then current interpreter.
    """
    project_root = Path(__file__).parents[2]
    embedded = project_root / "tools" / "python" / "python.exe"
    if embedded.exists():
        return embedded

    try:
        from core.settings import load_settings
        settings = load_settings()
        custom = settings.get("PYTHON_PATH")
        if custom and Path(custom).exists():
            return Path(custom)
    except Exception:
        pass

    return Path(sys.executable)

def run_ai_script(script_name, *args, **kwargs):
    """
    Run AI script in the embedded/system Python environment.
    
    Args:
        script_name: Name of script in ai_standalone/
        *args: Arguments to pass to script
        **kwargs: Additional options
    """
    try:
        python_exe = _find_python()
        
        # Use absolute path for script
        script_dir = Path(__file__).parent.parent / "scripts" / "ai_standalone"
        script_path = script_dir / script_name
        
        # Fallback: hardcoded path
        if not script_path.exists():
            script_path = Path(r"C:\Users\HG\Documents\HG_context_v2\src\scripts\ai_standalone") / script_name
        
        if not script_path.exists():
            raise FileNotFoundError(f"AI script not found: {script_path}")
        
        # Build command
        cmd = [python_exe, str(script_path)] + list(args)
        
        # Run command
        # We capture both stdout and stderr
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(Path(__file__).parents[2]), # Project root
            encoding='utf-8',
            errors='replace'
        )
        
        stdout, stderr = process.communicate()
        
        # Check exit code first
        if process.returncode == 0:
            # Success!
            # Even if there is stderr (warnings), we consider it a success if return code is 0
            return True, stdout
        else:
            # Failure
            # If return code is non-zero, stderr likely contains the error
            return False, stderr if stderr else "Unknown error occurred"

    except FileNotFoundError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)
