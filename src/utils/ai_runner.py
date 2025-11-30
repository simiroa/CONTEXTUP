"""
Utility to run AI scripts in Conda environment.
"""
import subprocess
from pathlib import Path

def get_conda_env_info():
    """Get Conda environment information."""
    # Use absolute path based on this file's location
    script_dir = Path(__file__).parent.parent / "scripts" / "ai_standalone"
    info_file = script_dir / "env_info.txt"
    
    # Fallback: hardcoded path
    if not info_file.exists():
        info_file = Path(r"C:\Users\HG\Documents\HG_context_v2\src\scripts\ai_standalone\env_info.txt")
    
    if not info_file.exists():
        raise FileNotFoundError(
            f"Conda environment not set up. Run: python tools/setup_ai_conda.py\n"
            f"Expected location: {info_file}"
        )
    
    info = {}
    with open(info_file, 'r') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                info[key] = value
    
    return info

def run_ai_script(script_name, *args, **kwargs):
    """
    Run AI script in Conda environment.
    
    Args:
        script_name: Name of script in ai_standalone/
        *args: Arguments to pass to script
        **kwargs: Additional options
    """
    try:
        env_info = get_conda_env_info()
        python_exe = env_info['PYTHON_EXE']
        
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
